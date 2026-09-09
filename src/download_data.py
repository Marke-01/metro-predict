"""Download exact checksum-verified public source files when originals are absent."""
from pathlib import Path
import urllib.request,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def run():
    raw=ROOT/'data/raw'
    for item in json.loads((raw/'manifest.json').read_text()):
        f=raw/item['file']
        b=f.read_bytes() if f.exists() else urllib.request.urlopen(item['url'],timeout=120).read()
        if hashlib.sha256(b).hexdigest()!=item['sha256']:raise ValueError('Source changed: '+item['file'])
        if not f.exists():f.write_bytes(b)
        print('Verified',item['file'])
if __name__=='__main__':run()
