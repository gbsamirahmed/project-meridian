"""Explicit geometry counters; the historical cap still means cumulative writes."""
from contextlib import contextmanager
import os


class AccountingLimit(RuntimeError):
    pass


class GeometryAccount:
    """Logical coordinate counts, not a substitute for process-memory measurements.

    Released staging never refunds the cumulative-write allowance. Unknown partial
    writes poison the ledger; no subsequent operation may claim a successful run.
    """
    def __init__(self, write_limit=2_000_000, temporary_limit=100_000, work_limits=None,
                 persistent_limit=2_000_000, final_limit=2_000_000):
        self.write_limit = write_limit
        self.temporary_limit = temporary_limit
        self.persistent_limit, self.final_limit = persistent_limit, final_limit
        self.written = self.attempted = self.rejected = self.rolled_back = 0
        self.workspace = self.workspace_peak = self.persistent_peak = 0
        self.files = {}
        self.processing = {}
        self.work_limits = work_limits or {}
        self.role_writes = {role:0 for role in ('final','intermediate','control','diagnostic')}
        self.poisoned = False

    def check(self, count=0):
        if self.poisoned:
            raise AccountingLimit('Unreconciled partial write; ledger is unusable')
        if count < 0 or not isinstance(count, int):
            raise ValueError('Vertex counts must be non-negative integers')
        if self.written + count > self.write_limit:
            raise AccountingLimit('Cumulative vertex-write limit')

    @contextmanager
    def temporary(self, count):
        self.check()
        if count < 0 or self.workspace + count > self.temporary_limit:
            raise AccountingLimit('Simultaneously held temporary geometry limit')
        self.workspace += count
        self.workspace_peak = max(self.workspace_peak, self.workspace)
        try:
            yield
        finally:
            self.workspace -= count

    def processed(self, stage, count):
        """Stage-specific work counters; repeated reads are intentionally counted."""
        self.check()
        if count < 0 or not isinstance(count,int): raise ValueError('Invalid work count')
        if self.processing.get(stage,0)+count > self.work_limits.get(stage,float('inf')):
            raise AccountingLimit('Cumulative stage-work limit: '+stage)
        self.processing[stage] = self.processing.get(stage,0) + count

    def seed_file(self, path, count, role):
        """Register verified immutable evidence; never resets cumulative charges.

        The caller verifies provenance/hashes first. This method records geometry
        counts/bytes only and refuses duplicate registration or an exceeded cap.
        """
        self.check()
        if count < 0 or role not in self.role_writes: raise ValueError('Invalid seed')
        path = os.path.realpath(path)
        if path in self.files: raise AccountingLimit('Duplicate evidence registration')
        self._storage_check(count,role)
        self.files[path] = {'vertices':count,'role':role,'bytes':os.path.getsize(path),'immutable':True}
        self.persistent_peak = max(self.persistent_peak,sum(item['vertices'] for item in self.files.values()))

    def _storage_check(self,count,role):
        if sum(item['vertices'] for item in self.files.values())+count > self.persistent_limit:
            raise AccountingLimit('Simultaneously stored geometry limit')
        if role == 'final' and sum(item['vertices'] for item in self.files.values()
                                  if item['role'] == 'final')+count > self.final_limit:
            raise AccountingLimit('Canonical final geometry limit')

    def append(self, stream, body, count, role='intermediate'):
        if role not in ('final', 'intermediate', 'control', 'diagnostic'):
            raise ValueError('Unknown geometry role')
        self.check()
        if count < 0 or not isinstance(count,int): raise ValueError('Invalid vertex count')
        self.attempted += count
        try:
            self.check(count)
            self._storage_check(count,role)
        except AccountingLimit:
            self.rejected += count
            raise
        path = os.path.realpath(stream.name)
        old = os.fstat(stream.fileno()).st_size
        if path not in self.files and old:
            raise AccountingLimit('Existing geometry must be inventoried, not guessed')
        entry = self.files.setdefault(path, {'vertices': 0, 'role': role, 'bytes': old,'immutable':False})
        if entry['immutable']: raise AccountingLimit('Immutable evidence cannot be appended')
        if entry['role'] != role or entry['bytes'] != old:
            self.poisoned = True
            raise AccountingLimit('File role or byte inventory changed unexpectedly')
        stream.seek(0, 2)
        try:
            if stream.write(body) != len(body):
                raise OSError('Short geometry write')
            stream.flush()
            if os.fstat(stream.fileno()).st_size != old + len(body):
                raise OSError('Geometry byte count mismatch')
        except BaseException:
            try:
                stream.seek(old)
                stream.truncate(old)
                stream.flush()
                if os.fstat(stream.fileno()).st_size != old:
                    raise OSError('Rollback byte count mismatch')
                self.rolled_back += count
            except BaseException:
                self.poisoned = True
            raise
        entry['vertices'] += count
        entry['bytes'] += len(body)
        self.written += count
        self.role_writes[role] += count
        self.persistent_peak = max(self.persistent_peak,
                                   sum(item['vertices'] for item in self.files.values()))

    def release_deleted(self, path):
        """Only callers owning disposable files may delete them; never deletes data."""
        self.check()
        path = os.path.realpath(path)
        if self.files[path]['immutable']: raise AccountingLimit('Immutable evidence cannot be released')
        if os.path.exists(path):
            raise AccountingLimit('Cannot release geometry that still exists')
        del self.files[path]

    def snapshot(self):
        roles = {role: sum(item['vertices'] for item in self.files.values() if item['role'] == role)
                 for role in ('final', 'intermediate', 'control', 'diagnostic')}
        return {'cumulativeAttemptedVertices': self.attempted,
                'cumulativeWrittenVertices': self.written, 'rejectedVertices': self.rejected,
                'cumulativeWrittenVerticesByRole':self.role_writes.copy(),
                'unclassifiedInitialWrittenVertices':self.written-sum(self.role_writes.values()),
                'rolledBackVertices': self.rolled_back, 'persistentVerticesByRole': roles,
                'peakPersistentVertices': self.persistent_peak,
                'temporaryVertices': self.workspace, 'peakTemporaryVertices': self.workspace_peak,
                'processingVerticesByStage': dict(sorted(self.processing.items())),
                'unreconciledPartialWrite': self.poisoned}
