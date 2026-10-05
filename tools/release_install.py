"""Build translated resources locally, then use the verified backup installer."""
import argparse,json,shutil,sys,tempfile
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


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root',type=Path,required=True)
    parser.add_argument('--loader-root',type=Path,required=True,help='Unmodified, user-downloaded V202.0 loader folder.')
    parser.add_argument('--backup-root',type=Path,help='New nonexistent directory; defaults to a timestamped game sibling.')
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--apply',action='store_true',help='Install after a verified full backup.')
    mode.add_argument('--check','--dry-run',dest='check',action='store_true',help='Validate and build in temporary storage; game unchanged (default).')
    args=parser.parse_args()
    try:print(json.dumps(install_local(args.game_root,args.loader_root,args.backup_root,args.apply),ensure_ascii=False,indent=2))
    except Exception as error:print('ERROR: '+str(error),file=sys.stderr);return 1
    return 0
