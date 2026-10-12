"""Bounded read-only contour investigation; cannot launch the genuine driver."""
import argparse
from pathlib import Path
import sys
from worker_supervision import supervise

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--python',type=Path,required=True)
    parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    args.output.mkdir(exist_ok=False)
    result = supervise([str(args.python),'-B',str(Path(__file__).with_name('retained_checks.py')),
        '--data-root',str(args.data_root),'--output',str(args.output/'checks')],
        args.output/'supervision.json',seconds=60)
    print(result)
    sys.exit(0 if result['success'] else 1)
