import sys
from . import study

if __name__=='__main__':
    stage=sys.argv[1]
    if stage=='_worker':study.worker(sys.argv[2])
    elif stage=='init':study.initialize()
    elif stage=='structural':study.structural()
    elif stage=='probes':study.probes()
    elif stage=='A':study.stage_a()
    elif stage=='expand':study.expand()
    else:raise ValueError('STAGE')
