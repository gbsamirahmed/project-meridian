"""Owned storage, immutable evidence and explicit unapproved resource profiles."""
from contextlib import contextmanager
from dataclasses import dataclass, asdict
import hashlib
import json
import os
from pathlib import Path
import time

from accounting import GeometryAccount, AccountingLimit


def encode(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n'


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for body in iter(lambda:stream.read(1048576),b''):h.update(body)
    return h.hexdigest()


@dataclass(frozen=True)
class Budget:
    """Every caller supplies a profile; construction grants no execution approval."""
    final: int
    stored: int
    written: int
    extracted: int
    loaded: int
    stitched: int
    temporary: int
    scratch: int
    working: int
    seconds: float
    receipt_reserve: int=65536

    def __post_init__(self):
        if any(v<=0 for v in asdict(self).values()):raise ValueError('Positive explicit limits required')
        if any(not isinstance(v,int) or isinstance(v,bool) for k,v in asdict(self).items() if k!='seconds'):
            raise ValueError('Count and byte ceilings must be integers')
        if self.receipt_reserve>=self.scratch:raise ValueError('Receipt reserve consumes scratch budget')

    @property
    def sha256(self):return hashlib.sha256(encode(asdict(self))).hexdigest()


class StageStore:
    """Byte reconciliation includes the entire owning root, not just new files.

    Immutable entries are verified before processing and at publication. New files
    must be created through this store. No unregistered writer is accepted.
    """
    def __init__(self,root,execution,budget,inventory,*,written,work=None,elapsed=0.,memory_reader=None,
                 external_receipt=None):
        self.root=Path(root).resolve();self.execution=Path(execution).resolve()
        if not self.execution.is_relative_to(self.root) or self.execution==self.root:
            raise ValueError('Execution must be an owned child of the budget root')
        if self.execution.exists():raise ValueError('Fresh execution required')
        self.budget=budget;self.started=time.monotonic();self.prior_elapsed=elapsed
        self.memory_reader=memory_reader;self.peak_memory=0;self.peak_bytes=0
        self.worker_ceiling=min(budget.working,int(os.environ.get('MERIDIAN_GUARD_MEMBER_BYTES',budget.working)))
        self.observed_generated_peak=0
        self.max_window_samples=0
        self.geometry=GeometryAccount(budget.written,budget.temporary,
            {'extracted':budget.extracted,'loaded':budget.loaded,'stitched':budget.stitched},
            budget.stored,budget.final)
        self.geometry.written=written;self.geometry.processing=dict(work or {})
        if any(stage not in self.geometry.work_limits or count<0 or count>self.geometry.work_limits[stage]
               for stage,count in self.geometry.processing.items()):
            raise AccountingLimit('Inherited stage-work limit')
        self.registry={};self.poisoned=False
        self.external_receipt=str(self.safe_path(external_receipt)) if external_receipt else None
        for entry in inventory:
            path=self.safe_path(self.root/entry['path'])
            if str(path) in self.registry:raise ValueError('Duplicate inventory path')
            if path.stat().st_size!=entry['bytes'] or digest(path)!=entry['sha256']:
                raise ValueError('Immutable evidence changed: '+entry['path'])
            role=entry.get('role','control');vertices=entry.get('vertices',0)
            self.geometry.seed_file(path,vertices,role)
            self.registry[str(path)]={'bytes':entry['bytes'],'sha256':entry['sha256'],
                'immutable':True,'role':role,'vertices':vertices,'disposable':False}
        self.reconcile();self.check()
        self.execution.mkdir()

    def safe_path(self,path):
        path=Path(path)
        # Reject junctions/symlinks before resolution, including any ancestor.
        for part in (path,*path.parents):
            if part.exists() and (part.is_symlink() or getattr(part.stat(),'st_file_attributes',0)&0x400):
                raise ValueError('Reparse points are outside the owned-storage contract')
            if part==self.root:break
        path=path.resolve()
        if not path.is_relative_to(self.root):raise ValueError('Path outside budget root')
        return path

    def reconcile(self):
        observed={str(self.safe_path(p)):p.stat().st_size for p in self.root.rglob('*') if p.is_file()}
        external={self.external_receipt} if self.external_receipt else set()
        if set(observed)-external!=set(self.registry):
            self.poisoned=True;raise AccountingLimit('Unregistered or missing budget-root file')
        for path,size in observed.items():
            if path==self.external_receipt:
                if size>self.budget.receipt_reserve//2:raise AccountingLimit('Controller receipt exceeded reserved allowance')
                continue
            if self.registry[path]['bytes']!=size:
                self.poisoned=True;raise AccountingLimit('Unexpected file length')
        self.bytes=sum(observed.values());self.peak_bytes=max(self.peak_bytes,self.bytes)
        if self.bytes>self.budget.scratch:raise AccountingLimit('Whole-directory scratch limit')
        return self.bytes

    def check(self,*,reserve_bytes=0,add_bytes=0):
        if self.poisoned:raise AccountingLimit('Unreconciled storage')
        self.geometry.check()
        if self.prior_elapsed+time.monotonic()-self.started>=self.budget.seconds:
            raise AccountingLimit('Shared active-execution time limit')
        if self.memory_reader:
            current,peak=self.memory_reader();self.peak_memory=max(self.peak_memory,peak)
            if peak>self.worker_ceiling or current+reserve_bytes>self.worker_ceiling:
                raise AccountingLimit('Worker memory/preflight limit')
        self.reconcile()
        if self.bytes+add_bytes+self.budget.receipt_reserve>self.budget.scratch:
            raise AccountingLimit('Scratch reservation refused')

    def open_geometry(self,path,role='intermediate',disposable=False):
        self.check();path=self.safe_path(path)
        if not path.is_relative_to(self.execution):raise ValueError('Cannot create outside fresh execution')
        path.parent.mkdir(parents=True,exist_ok=True)
        stream=path.open('xb')
        self.registry[str(path)]={'bytes':0,'immutable':False,'role':role,'vertices':0,
            'disposable':disposable}
        self.geometry.files[str(path)]={'bytes':0,'role':role,'vertices':0,'immutable':False}
        return stream

    def append(self,stream,record,vertices=0):
        self.check(reserve_bytes=vertices*256+8192)
        path=self.safe_path(stream.name);entry=self.registry[str(path)]
        if entry['immutable']:raise AccountingLimit('Historical file is immutable')
        with self.workspace(vertices*2):
            body=encode(record);self.check(add_bytes=len(body))
            try:self.geometry.append(stream,body,vertices,entry['role'])
            except BaseException:
                if self.geometry.poisoned:
                    entry['bytes']=path.stat().st_size;self.poisoned=True
                raise
        entry['bytes']+=len(body);entry['vertices']+=vertices
        self.reconcile()

    def atomic_json(self,path,value,*,emergency=False):
        path=self.safe_path(path)
        if not path.is_relative_to(self.execution):raise ValueError('Receipt must be owned')
        previous=self.registry.get(str(path))
        if previous and previous['immutable']:raise ValueError('Cannot replace immutable receipt')
        body=encode(value)
        if emergency:
            if len(body)>self.budget.receipt_reserve//2:raise AccountingLimit('Emergency receipt too large')
            # An external kill can leave a partial registered file. Observe its
            # bytes, but never publish successful counters from a poisoned store.
            size=sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file())
            if size+len(body)>self.budget.scratch:raise AccountingLimit('No safe emergency receipt space')
        else:self.check(add_bytes=len(body))
        temporary=path.with_name(path.name+'.pending')
        if temporary.exists():raise AccountingLimit('Incomplete receipt transaction retained')
        path.parent.mkdir(parents=True,exist_ok=True)
        self.registry[str(temporary)]={'bytes':0,'immutable':False,'role':'control','vertices':0,'disposable':False}
        try:
            with temporary.open('xb') as stream:
                if stream.write(body)!=len(body):raise OSError('Short receipt write')
                stream.flush();os.fsync(stream.fileno())
            self.registry[str(temporary)]['bytes']=len(body)
            os.replace(temporary,path)
            self.registry[str(path)]=self.registry.pop(str(temporary))
            self.reconcile()
        except BaseException:
            if temporary.exists():self.registry[str(temporary)]['bytes']=temporary.stat().st_size
            raise

    def retire(self,path,*,expected_hash,receipt):
        self.check();path=self.safe_path(path);entry=self.registry[str(path)]
        if entry['immutable'] or not entry['disposable'] or not path.is_relative_to(self.execution):
            raise ValueError('Only explicitly disposable fresh geometry may be retired')
        if digest(path)!=expected_hash:raise ValueError('Disposable geometry changed after verification')
        # Durable successful comparison precedes deletion. A failed atomic update
        # leaves the previous receipt and geometry; retirement is not attempted.
        self.atomic_json(receipt,{'state':'verified-before-retirement','path':str(path.relative_to(self.root)),
            'sha256':expected_hash,'vertices':entry['vertices']})
        path.unlink();self.geometry.release_deleted(path);del self.registry[str(path)]
        self.reconcile()
        self.atomic_json(receipt,{'state':'retired','path':str(path.relative_to(self.root)),
            'sha256':expected_hash,'vertices':entry['vertices']})

    @contextmanager
    def workspace(self,count,*,bytes_per_coordinate=256):
        self.check(reserve_bytes=count*bytes_per_coordinate)
        with self.geometry.temporary(count):yield

    def generation_reservation(self,quads):
        # At most two contour segments/four endpoint coordinates per valid quad.
        # This is intentionally conservative; no silent smaller source window.
        return self.workspace(4*quads,bytes_per_coordinate=32)

    def observe_generated(self,count):
        self.observed_generated_peak=max(self.observed_generated_peak,count)
        if count>self.geometry.workspace:raise AccountingLimit('Native contour allocation exceeded reservation')

    def level_records(self,path):
        path=self.safe_path(path);count=self.registry[str(path)]['vertices']
        self.geometry.processed('loaded',count)
        records=[]
        with path.open('rb') as stream:
            for body in stream:
                if len(body)>2_000_000:raise AccountingLimit('Record size limit')
                records.append(json.loads(body))
        if sum(len(r['coordinates']) for r in records)!=count:
            raise ValueError('Registered geometry count mismatch')
        return records

    def snapshot(self):
        return {'geometry':self.geometry.snapshot(),'storageBytes':self.bytes,
            'peakStorageBytes':self.peak_bytes,'workerPeakBytes':self.peak_memory,
            'activeElapsedSeconds':self.prior_elapsed+time.monotonic()-self.started,
            'profileSha256':self.budget.sha256,'effectiveWorkerCeilingBytes':self.worker_ceiling,
            'observedGeneratedCoordinatePeak':self.observed_generated_peak,
            'poisoned':self.poisoned or self.geometry.poisoned}

    def sealed_inventory(self,exclude=()):
        self.reconcile();excluded={str(Path(p).resolve()) for p in exclude}
        return [{'path':str(Path(path).relative_to(self.root)).replace('\\','/'),
            'bytes':entry['bytes'],'sha256':digest(path),'role':entry['role'],'vertices':entry['vertices']}
            for path,entry in sorted(self.registry.items()) if path not in excluded]

    def verify_immutable(self):
        self.reconcile()
        for path,entry in self.registry.items():
            if entry['immutable'] and digest(path)!=entry['sha256']:
                raise ValueError('Immutable evidence changed')
