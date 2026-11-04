from pathlib import Path
import hashlib,ast,json
import pandas as pd
O=Path(__file__).resolve().parents[1]
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
code=[]
for p in sorted((O/'scripts').glob('*.py')):
 ast.parse(p.read_text());code.append(dict(path=str(p.relative_to(O)),sha256=sha(p)))
pd.DataFrame(code).to_csv(O/'CODE_SHA256_MANIFEST.csv',index=False)
outputs=[]
for p in sorted(O.rglob('*')):
 if p.is_file() and p.name!='OUTPUT_SHA256_MANIFEST.csv' and not any(x in p.relative_to(O).parts for x in ['profile','cache','config','matplotlib']):outputs.append(dict(path=str(p.relative_to(O)),bytes=p.stat().st_size,sha256=sha(p)))
pd.DataFrame(outputs).to_csv(O/'OUTPUT_SHA256_MANIFEST.csv',index=False)
assert all(sha(O/x['path'])==x['sha256'] for x in outputs)
print(json.dumps(dict(artifacts=len(outputs),all_output_hashes_verified=True,final=json.loads((O/'evidence/FINAL_RUN.json').read_text())),ensure_ascii=False))
