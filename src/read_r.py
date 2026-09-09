"""Small, fail-closed XDR reader for the pinned Complete Journey v2 files.

Supports only the vector/pairlist types used by these files. Not a general R
interpreter; never executes serialized code. Format: R Internals section 1.8.
"""
import bz2, gzip, lzma, struct
from pathlib import Path
import numpy as np
import pandas as pd

class Node:
    def __init__(self, value=None, attrs=None):
        self.value, self.attrs = value, attrs or {}

class Reader:
    def __init__(self, data):
        self.data, self.pos, self.refs = data, 0, []
    def take(self, n):
        if n < 0 or self.pos+n > len(self.data): raise ValueError('Invalid length')
        b=self.data[self.pos:self.pos+n]; self.pos+=n; return b
    def integer(self): return struct.unpack('>i', self.take(4))[0]
    def obj(self):
        flags=self.integer(); typ=flags & 255
        attr=bool(flags & 512); tag=bool(flags & 1024)
        if typ in (0,254): return None
        if typ==255:
            i=flags >> 8
            return self.refs[(i or self.integer())-1]
        if typ==1:
            n=self.obj(); self.refs.append(n); return n
        if typ==2:
            a=self.obj() if attr else None
            t=self.obj() if tag else None
            car=self.obj(); cdr=self.obj()
            return (t,car,cdr)
        if typ==9:
            n=self.integer()
            return None if n==-1 else self.take(n).decode('utf-8' if flags & (8<<12) else 'latin1')
        if typ in (10,13,14):
            n=self.integer(); dt='>f8' if typ==14 else '>i4'
            v=np.frombuffer(self.take(n*np.dtype(dt).itemsize),dtype=dt).astype('float64' if typ==14 else 'int64')
        elif typ in (16,19): v=[self.obj() for _ in range(self.integer())]
        else: raise ValueError(f'Unsupported R type {typ} at {self.pos-4}')
        return Node(v, pairs(self.obj()) if attr else {})

def pairs(p):
    d={}
    while p is not None:
        t,v,p=p; d[t]=v.value if isinstance(v,Node) else v
    return d

def read_frame(path):
    b=Path(path).read_bytes()
    if b[:2]==b'\x1f\x8b': b=gzip.decompress(b)
    elif b[:3]==b'BZh': b=bz2.decompress(b)
    elif b[:6]==b'\xfd7zXZ\x00': b=lzma.decompress(b)
    workspace=b.startswith(b'RDX')
    if workspace: b=b.split(b'\n',1)[1]
    r=Reader(b)
    if r.take(2)!=b'X\n': raise ValueError('Only XDR is supported')
    ver=r.integer(); r.integer();r.integer()
    if ver==3: r.take(r.integer())
    elif ver!=2: raise ValueError('Unsupported version')
    obj=r.obj()
    if workspace: obj=obj[1]
    assert r.pos==len(b), 'Trailing bytes'
    out={}
    for name,col in zip(obj.attrs['names'],obj.value):
        v=col.value; classes=col.attrs.get('class',[])
        if 'factor' in classes:
            levels=col.attrs['levels'];v=[levels[i-1] if i>0 else None for i in v]
        elif 'POSIXct' in classes:
            v=pd.to_datetime(v,unit='s',utc=True).tz_convert('America/New_York').tz_localize(None)
        elif 'Date' in classes: v=pd.to_datetime(v,unit='D',origin='unix')
        out[name]=v
    return pd.DataFrame(out)

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    for f in sorted((root/'data/raw').glob('*.rd*')):
        df=read_frame(f); print(f.name,df.shape,df.head(2).to_dict('records'),flush=True)
        df.to_csv(root/'data/raw'/f'{f.stem}.csv.gz',index=False)
