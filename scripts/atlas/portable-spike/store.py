"""Owned, single-writer directory experiment. No downloads or scientific publication."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import tempfile
import time
from reader import Reader, ReadError, require
from verification import manifest_at, bounded_bytes, json_value, digest, MAX_BYTES, Snapshot

STORE_SCHEMA = 'atlas-projection-store-spike/v1'
READY_SCHEMA = 'atlas-projection-ready-spike/v1'
SELECTION_SCHEMA = 'atlas-projection-selection-spike/v1'
MAX_STORE = 512 * 1024 * 1024

def record(path, value, hook=None):
    """Same-directory replace is the process-visible record commit; no directory fsync claim."""
    raw = (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode('utf-8')
    fd, temporary = tempfile.mkstemp(prefix='.record-', dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        event(hook,'record-written:'+path.name)
        os.replace(temporary,path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)

def event(hook, name):
    if hook: hook(name)

class Store:
    @staticmethod
    def create(root):
        root = Path(root).absolute()
        require(not root.exists(), 'store-owned', 'Initialise a new owned store; existing paths are not adopted.')
        root.mkdir(parents=True)
        for name in ['staging','packages','ready']: (root/name).mkdir()
        record(root/'store.json', {'schema':STORE_SCHEMA})
        return Store(root)

    def __init__(self, root):
        self.root = Path(root).absolute()
        try:
            for path in [self.root] + [self.root/n for n in ['staging','packages','ready']]:
                require(path.is_dir() and not path.is_symlink() and not path.is_junction(), 'store-owned', 'Store directories must be owned ordinary directories.')
            require(json_value(bounded_bytes(self.root/'store.json',4096)) == {'schema':STORE_SCHEMA}, 'store-incompatible', 'Invalid owned store marker.')
        except (OSError,ValueError) as e: raise ReadError('store-unavailable','Owned store is unavailable.') from e

    def package(self, identifier):
        require(digest(identifier), 'store-identity', 'Exact package SHA256 required.')
        return self.root/'packages'/identifier

    def selected(self):
        try:
            data = json_value(bounded_bytes(self.root/'selection.json',4096))
            require(set(data) == {'schema','projectionIdentity'} and data['schema'] == SELECTION_SCHEMA and digest(data['projectionIdentity']),
                    'store-selection', 'Invalid selection; no fallback.')
            return data['projectionIdentity']
        except (OSError,ValueError,TypeError) as e: raise ReadError('store-selection','Selection is missing or malformed; explicitly select a ready package.') from e

    def receipt(self, identifier):
        package = self.package(identifier)
        try:
            r = json_value(bounded_bytes(self.root/'ready'/(identifier+'.json'),4096))
            require(set(r) == {'schema','projectionIdentity','manifestSha256','profile','generations'}
                    and r['schema'] == READY_SCHEMA and r['projectionIdentity'] == identifier and digest(r['manifestSha256']),
                    'store-ready', 'Invalid ready receipt.')
            raw = bounded_bytes(package/'manifest.json',65536)
            require(hashlib.sha256(raw).hexdigest() == r['manifestSha256'], 'store-ready', 'Ready manifest changed.')
            m = manifest_at(package,identifier)
            require(r['profile'] == m['profile'] and r['generations'] == sorted(m['pins']), 'store-ready', 'Ready compatibility differs.')
            return r
        except (OSError,ValueError,TypeError) as e: raise ReadError('store-ready','Package is not completely ready.') from e

    def open(self, generation, identifier=None):
        identifier = self.selected() if identifier is None else identifier
        self.receipt(identifier)
        return Reader(self.package(identifier), generation, identifier)

    def select(self, identifier, hook=None):
        receipt = self.receipt(identifier)
        # A ready marker alone cannot substitute for reopening/complete verification.
        with self.open(receipt['generations'][0], identifier): pass
        event(hook,'before-select')
        record(self.root/'selection.json', {'schema':SELECTION_SCHEMA,'projectionIdentity':identifier},hook)
        event(hook,'after-select')

    def install(self, source, expected, hook=None, select=True):
        source = Path(source).absolute(); self.package(expected)
        start = time.perf_counter()
        try:
            m = manifest_at(source,expected)
            required_bytes = sum(s['bytes'] for s in m['files'].values()) + (source/'manifest.json').stat().st_size
            occupied = sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file())
            require(occupied + required_bytes <= MAX_STORE, 'store-budget', 'Owned store exceeds 512 MiB experiment bound; explicitly delete obsolete/staged copies.')
            stage = Path(tempfile.mkdtemp(prefix='candidate-',dir=self.root/'staging'))
            for name in ['manifest.json'] + sorted(m['files']):
                seal = m['files'].get(name)
                raw = bounded_bytes(source/name,MAX_BYTES if seal else 65536,seal)
                with (stage/name).open('xb') as stream:
                    for offset in range(0,len(raw),1024*1024):
                        stream.write(raw[offset:offset+1024*1024])
                        event(hook,'staging-write:'+name)
                    stream.flush(); os.fsync(stream.fileno())
                event(hook,'staged-member:'+name)
            staged = time.perf_counter()
            event(hook,'before-verify')
            snapshot = Snapshot(stage,expected); snapshot.close()
            verified = time.perf_counter()
            package = self.package(expected)
            if package.exists():
                # Never overwrite an immutable identity directory, including a corrupt one.
                existing = Snapshot(package,expected); existing.close()
                shutil.rmtree(stage)
            else: os.rename(stage,package)
            event(hook,'before-final-verify')
            final_start = time.perf_counter()
            final = Snapshot(package,expected); final.close()
            final_ms = (time.perf_counter()-final_start)*1000
            event(hook,'before-ready')
            receipt = {'schema':READY_SCHEMA,'projectionIdentity':expected,'manifestSha256':hashlib.sha256((package/'manifest.json').read_bytes()).hexdigest(),
                       'profile':m['profile'],'generations':sorted(m['pins'])}
            record(self.root/'ready'/(expected+'.json'),receipt,hook)
            event(hook,'after-ready')
            ready = time.perf_counter()
            if select: self.select(expected,hook)
            return {'projectionIdentity':expected,'bytes':required_bytes,'stagingMs':(staged-start)*1000,
                    'verificationMs':(verified-staged)*1000,'finalVerificationMs':final_ms,'readyPublicationMs':(ready-verified)*1000-final_ms,'selectionMs':(time.perf_counter()-ready)*1000,'totalMs':(time.perf_counter()-start)*1000}
        except OSError as e:
            # Owned abandoned stages remain inspectable and unready; selection is untouched before commit.
            raise ReadError('store-write','Installation write failed; inspect owned staging and retain the last ready selection.') from e

    def delete(self, identifier, hook=None):
        package = self.package(identifier)
        # Malformed selection must be resolved explicitly, never assumed to be another package.
        if (self.root/'selection.json').exists() and self.selected() == identifier:
            (self.root/'selection.json').unlink()
        event(hook,'delete-selection-cleared')
        (self.root/'ready'/(identifier+'.json')).unlink(missing_ok=True)
        event(hook,'delete-ready-cleared')
        if package.exists():
            require(not package.is_symlink() and not package.is_junction(), 'store-owned', 'Refuse linked package deletion.')
            shutil.rmtree(package)

    def discard_stage(self, name):
        require(isinstance(name,str) and name.startswith('candidate-') and Path(name).name == name and '/' not in name and '\\' not in name,
                'store-owned','Only a named owned candidate may be discarded.')
        stage = self.root/'staging'/name
        require(stage.is_dir() and not stage.is_symlink() and not stage.is_junction(), 'store-owned','Refuse non-owned stage deletion.')
        shutil.rmtree(stage)

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('operation',choices=['init','install','select','open','delete','discard-stage'])
    parser.add_argument('--store',required=True); parser.add_argument('--projection'); parser.add_argument('--identity'); parser.add_argument('--generation'); parser.add_argument('--stage')
    args = parser.parse_args()
    try:
        if args.operation == 'init': Store.create(args.store); result = {'status':'initialised'}
        else:
            store = Store(args.store)
            if args.operation == 'install':
                require(bool(args.projection), 'store-request', 'Install requires --projection and exact --identity.')
                result = store.install(args.projection,args.identity)
            elif args.operation == 'select': store.select(args.identity); result = {'status':'selected','projectionIdentity':args.identity}
            elif args.operation == 'delete': store.delete(args.identity); result = {'status':'deleted','projectionIdentity':args.identity}
            elif args.operation == 'discard-stage': store.discard_stage(args.stage); result = {'status':'discarded','stage':args.stage}
            else:
                require(bool(args.generation), 'store-request', 'Open requires an exact --generation.')
                with store.open(args.generation,args.identity) as reader:
                    result = {'status':'opened','generation':reader.generation,'projectionIdentity':reader.manifest['projectionIdentity'],'records':len(reader.records)}
        print(json.dumps(result)); return 0
    except (ReadError,OSError,ValueError) as e:
        print(json.dumps({'status':'error','code':e.code if isinstance(e,ReadError) else 'store-unavailable','message':str(e) if isinstance(e,ReadError) else 'Check the explicit owned store and request.'})); return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
