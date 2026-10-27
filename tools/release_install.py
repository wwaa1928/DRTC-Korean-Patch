"""Build translated resources locally, then use the verified backup installer."""
import argparse,base64,json,shutil,sys,tempfile,zlib
from pathlib import Path
from . import installer_common as common
from build_ko import build_local,verified_loader,RELEASE_ROOT


def prepare_payload(game,loader,payload):
    loader,files=verified_loader(loader)
    record=build_local(game,loader,payload/'DRTC_KO')
    entries=[]
    for rel,expected in files.items():
        dest=common.target(payload,'loader/'+rel)
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(common.target(loader,rel),dest)
        if common.file_sha(dest)!=expected:raise ValueError('Loader changed during preparation.')
        entries.append({'source':'loader/'+rel,'target':rel,'sha256':expected})
    for path in sorted((payload/'DRTC_KO').rglob('*')):
        if path.is_file():
            rel=path.relative_to(payload).as_posix()
            entries.append({'source':rel,'target':'mods/'+rel,'sha256':common.file_sha(path)})
    expected=common.read_json(RELEASE_ROOT/'data/expected_source.json')
    manifest={'schema':1,'game_build':'24936165','original_exe_sha256':common.ORIGINAL_EXE,
        'patched_exe_sha256':common.PATCHED_EXE,'source_sha256':expected['source_sha256'],'files':entries}
    (payload/'manifest.json').write_bytes(common.json_bytes(manifest))
    return record


def install_local(game,loader,backup=None,apply=False):
    root=common.game_root(game)
    common.assert_not_running(root)
    if common.target(root,common.STATE_FILE).exists() or common.target(root,common.LOCK_FILE).exists():
        raise ValueError('Remove the existing Korean patch before installing this version.')
    common.patch_bytes(common.target(root,'prog.exe').read_bytes())
    loader,_=verified_loader(loader)
    if root==loader or loader.is_relative_to(root) or root.is_relative_to(loader):
        raise ValueError('Download the loader into a separate folder outside the game.')
    if backup is not None:
        backup=Path(backup).resolve()
        for protected in (RELEASE_ROOT,loader):
            if backup==protected or backup.is_relative_to(protected) or protected.is_relative_to(backup):
                raise ValueError('Backup must not overlap the release or loader folder.')
    temp_base=Path(tempfile.gettempdir()).resolve()
    if any(temp_base==p or temp_base.is_relative_to(p) for p in (root,loader,RELEASE_ROOT)):
        raise ValueError('Temporary storage must be outside the game, loader, and release folder.')
    with tempfile.TemporaryDirectory(prefix='drtc-ko-install-') as folder:
        payload=Path(folder)/'payload'
        record=prepare_payload(root,loader,payload)
        result=common.install(root,payload,backup,apply)
        result['build']={k:record[k] for k in ('source_df_hashes_verified','translated_script_entries',
            'replaced_literal_occurrences','generated_df_files','native_po_entries_applied','empty_sentinel_entries')}
        return result


_ART=(
    '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'
    '/dsvbf86/Qs5LTwe')


class _Art(argparse.Action):
    def __call__(self,parser,*_):
        print(zlib.decompress(base64.b64decode(_ART)).decode('utf-8'));parser.exit()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root',type=Path,required=True)
    parser.add_argument('--loader-root',type=Path,required=True,help='Unmodified, user-downloaded V202.0 loader folder.')
    parser.add_argument('--backup-root',type=Path,help='New nonexistent directory; defaults to a timestamped game sibling.')
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--apply',action='store_true',help='Install after a verified full backup.')
    mode.add_argument('--check','--dry-run',dest='check',action='store_true',help='Validate and build in temporary storage; game unchanged (default).')
    parser.add_argument('--wait',action=_Art,nargs=0,help='???')
    args=parser.parse_args()
    try:print(json.dumps(install_local(args.game_root,args.loader_root,args.backup_root,args.apply),ensure_ascii=False,indent=2))
    except Exception as error:print('ERROR: '+str(error),file=sys.stderr);return 1
    return 0
