import argparse
from kmd_toc.pipeline.execution import execute

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--method',required=True,choices=['A1','A2','A3','B','C','D']);p.add_argument('--output',required=True);p.add_argument('--primary',choices=['D','W'],default='D');p.add_argument('--other-limit',type=float);p.add_argument('--offset',type=int,default=0);a=p.parse_args()
    r=execute(a.input,a.method,a.output,a.primary,a.other_limit,a.offset);print(r['status'],r['D_km'],r['W_min'],r['T_program_s'],flush=True)
