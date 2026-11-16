import argparse
from kmd_toc.pipeline.roads import build_inputs

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--graph-dir',default='/tmp/kmd-osrm-graph');p.add_argument('--rootfs',default='/tmp/kmd-osrm527');a=p.parse_args()
    build_inputs(a.output,a.graph_dir,a.rootfs)
