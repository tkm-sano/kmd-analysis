import argparse
from kmd_toc.pipeline.route_pairs import build_pipeline

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--parent',required=True);p.add_argument('--output',required=True);p.add_argument('--scenarios',nargs='+',default=['S1','S2','S3']);p.add_argument('--process-workers',type=int,default=0);p.add_argument('--port',type=int,default=5000);a=p.parse_args()
    build_pipeline(a.parent,a.output,a.scenarios,a.process_workers,a.port)
