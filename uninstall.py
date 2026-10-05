"""Restore modified files and remove only verified patch-added files."""
import argparse,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
from tools.installer_common import uninstall

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game-root',type=Path,required=True)
    mode=p.add_mutually_exclusive_group()
    mode.add_argument('--apply',action='store_true')
    mode.add_argument('--check','--dry-run',dest='check',action='store_true',help='Read-only preflight (default).')
    a=p.parse_args()
    try:print(json.dumps(uninstall(a.game_root,a.apply),ensure_ascii=False,indent=2))
    except Exception as error:print('ERROR: '+str(error),file=sys.stderr);return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
