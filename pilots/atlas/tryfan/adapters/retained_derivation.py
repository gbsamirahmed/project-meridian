"""Read-only locator bridge to the unchanged scientific sampler (not a new method)."""
import hashlib,importlib.util,json,sys
from pathlib import Path
payload=json.load(sys.stdin)
spec=importlib.util.spec_from_file_location('frozen_sampler',Path(__file__).resolve().parents[4]/'scripts/atlas/qualified-query-proof/retained_inputs.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
# Lexical virtual root keeps frozen meridian-data aliases stable after physical relocation.
virtual=Path(payload['dataRoot'])/'__atlas_registered_read_view__'
if 'meridian-private' in str(virtual).lower():raise ValueError('Private paths prohibited')
bindings=payload['bindings'];read=Path.read_bytes;is_file=Path.is_file;text=Path.read_text

def bound(p):
    try:alias=p.relative_to(virtual).as_posix()
    except ValueError:return None
    if alias not in bindings:raise ValueError('Sampler requested unregistered artifact: '+alias)
    return bindings[alias]

def bytes_registered(p):
    b=bound(p)
    if b is None:return read(p)
    path=Path(b['path'])
    if 'meridian-private' in str(path).lower():raise ValueError('Private paths prohibited')
    data=read(path)
    if len(data)!=b['bytes'] or hashlib.sha256(data).hexdigest()!=b['sha256']:raise ValueError('Registered artifact integrity mismatch')
    return data

def file_registered(p):
    b=bound(p)
    return is_file(Path(b['path'])) if b is not None else is_file(p)
def text_registered(p,*args,**kwargs):
    if bound(p) is None:return text(p,*args,**kwargs)
    return bytes_registered(p).decode(kwargs.get('encoding') or (args[0] if args else 'utf-8'))
Path.read_bytes=bytes_registered;Path.is_file=file_registered;Path.read_text=text_registered
try:result=m.samples(virtual,payload['requests'])
finally:Path.read_bytes=read;Path.is_file=is_file;Path.read_text=text
print(json.dumps(result,sort_keys=True,allow_nan=False))
