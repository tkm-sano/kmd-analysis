from pathlib import Path
import hashlib,ast,json
import pandas as pd
O=Path(__file__).resolve().parents[1]
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
rows=[]
for p in sorted((O/'scripts').glob('*.py')):
 ast.parse(p.read_text());rows.append(dict(path=str(p.relative_to(O)),sha256=sha(p)))
pd.DataFrame(rows).to_csv(O/'CODE_SHA256_MANIFEST.csv',index=False)
rows=[]
for p in sorted(O.rglob('*')):
 if p.is_file() and p.name!='OUTPUT_SHA256_MANIFEST.csv' and not any(z in p.relative_to(O).parts for z in ['profile','cache','config','matplotlib']):rows.append(dict(path=str(p.relative_to(O)),bytes=p.stat().st_size,sha256=sha(p)))
pd.DataFrame(rows).to_csv(O/'OUTPUT_SHA256_MANIFEST.csv',index=False)
assert all(sha(O/x['path'])==x['sha256'] for x in rows)
print(json.dumps(dict(sealed_outputs=len(rows),all_output_hashes_verified=True,final_run=json.loads((O/'evidence/FINAL_RUN.json').read_text())),ensure_ascii=False))
