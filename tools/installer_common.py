"""Verified DRTC Korean loader installer; standard library + vendored pefile."""
from pathlib import Path, PurePosixPath
import ctypes, datetime, hashlib, json, os, re, shutil, struct, sys, uuid

sys.dont_write_bytecode = True

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'vendor'))
import pefile

ORIGINAL_EXE = 'aba4ff1b8ea669b8831d4085c8703c46bdb98e80ddaf35f02bad111637cea105'
PATCHED_EXE = '454833646ec28a7fffb46cb5bf8dcf16faf7a967915dc3404860141d11035f36'
STATE_FILE = '.drtc_ko_install.json'
LOCK_FILE = '.drtc_ko_install.lock'
BACKUP_MANIFEST = 'installation_manifest.json'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def safe_relative(value):
    p = PurePosixPath(value.replace('\\', '/'))
    if p.is_absolute() or not p.parts or '..' in p.parts:
        raise ValueError(f'Unsafe relative path: {value!r}')
    for part in p.parts:
        if re.search(r'[<>:"|?*\x00-\x1f]', part) or part.endswith((' ', '.')):
            raise ValueError(f'Unsafe Windows path: {value!r}')
        if part.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL', *('COM'+str(i) for i in range(1,10)), *('LPT'+str(i) for i in range(1,10))}:
            raise ValueError(f'Reserved Windows name: {value!r}')
    return p.as_posix()


def is_link(path):
    st = path.lstat()
    return path.is_symlink() or bool(getattr(st, 'st_file_attributes', 0) & 0x400)


def target(root, relative):
    """Resolve before every operation; refuse links/junctions and escaping paths."""
    relative = safe_relative(relative)
    raw = root / relative
    current = raw
    while current != root:
        if (current.exists() or current.is_symlink()) and is_link(current):
            raise ValueError(f'Reparse point/symlink is not supported: {current}')
        current = current.parent
    resolved = raw.resolve()
    if resolved == root or not resolved.is_relative_to(root):
        raise ValueError(f'Target escapes its declared root: {raw}')
    return resolved


def game_root(path):
    root = Path(path).expanduser().resolve(strict=True)
    if root == Path(root.anchor) or not root.is_dir() or not (root/'prog.exe').is_file():
        raise ValueError('Game root must be the folder containing prog.exe.')
    if is_link(root):
        raise ValueError('Game root must not be a reparse point/symlink.')
    return root


def tree(root):
    """Full regular-file and directory inventory; never follows a junction."""
    files, directories = {}, []
    for directory, dirnames, filenames in os.walk(root, followlinks=False):
        base = Path(directory)
        for name in dirnames:
            p = base/name
            if is_link(p):
                raise ValueError(f'Reparse point/symlink in tree: {p}')
            directories.append(p.relative_to(root).as_posix())
        for name in filenames:
            p = base/name
            if is_link(p) or not p.is_file():
                raise ValueError(f'Non-regular file in tree: {p}')
            relative = safe_relative(p.relative_to(root).as_posix())
            files[relative] = {'sha256': file_sha(p), 'size': p.stat().st_size}
    return dict(sorted(files.items())), sorted(directories)


def validate_hash(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise ValueError('Malformed SHA-256 in manifest.')


def assert_not_running(root):
    """Read process executable paths, without UI control or launching the game."""
    if os.name == 'nt':
        return _assert_not_running_windows(root)
    if sys.platform.startswith('linux'):
        return _assert_not_running_linux(root, Path('/proc'))
    raise ValueError('This installer requires Windows or Linux (Steam Deck + Proton).')


def _wine_argument_path(argument):
    """Map a Proton/Wine command-line path to a host path when it is unambiguous."""
    if argument.startswith('/'):
        return Path(argument)
    if re.match(r'[Zz]:[\\/]', argument):
        return Path('/'+argument[3:].replace('\\', '/'))
    return None


def _assert_not_running_linux(root, proc):
    """Proton runs prog.exe under Wine; find it in /proc command lines."""
    expected = target(root, 'prog.exe')
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            arguments = (entry/'cmdline').read_bytes().split(b'\0')
        except OSError:
            continue  # exited while scanning, or not ours to read
        for raw in arguments:
            argument = raw.decode('utf-8', 'surrogateescape')
            if re.split(r'[\\/]', argument)[-1].lower() != 'prog.exe':
                continue
            host = _wine_argument_path(argument)
            if host is None:
                raise ValueError(f'A prog.exe is running (PID {entry.name}) and its folder cannot be verified; close it first.')
            try:
                folder = host.parent.resolve()
            except OSError:
                continue
            if folder == expected.parent:  # Wine file names are case-insensitive
                raise ValueError(f'The target game is running (PID {entry.name}); close it first.')


def _assert_not_running_windows(root):
    from ctypes import wintypes as w
    class ProcessEntry(ctypes.Structure):
        _fields_ = [('dwSize',w.DWORD),('cntUsage',w.DWORD),('th32ProcessID',w.DWORD),
                    ('th32DefaultHeapID',ctypes.c_size_t),('th32ModuleID',w.DWORD),
                    ('cntThreads',w.DWORD),('th32ParentProcessID',w.DWORD),
                    ('pcPriClassBase',w.LONG),('dwFlags',w.DWORD),('szExeFile',w.WCHAR*260)]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes=[w.DWORD,w.DWORD];kernel.CreateToolhelp32Snapshot.restype=w.HANDLE
    kernel.Process32FirstW.argtypes=[w.HANDLE,ctypes.POINTER(ProcessEntry)];kernel.Process32FirstW.restype=w.BOOL
    kernel.Process32NextW.argtypes=[w.HANDLE,ctypes.POINTER(ProcessEntry)];kernel.Process32NextW.restype=w.BOOL
    kernel.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];kernel.OpenProcess.restype=w.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,ctypes.POINTER(w.DWORD)];kernel.QueryFullProcessImageNameW.restype=w.BOOL
    kernel.CloseHandle.argtypes=[w.HANDLE];kernel.CloseHandle.restype=w.BOOL
    snapshot=kernel.CreateToolhelp32Snapshot(2,0)
    if snapshot == ctypes.c_void_p(-1).value:
        raise OSError(ctypes.get_last_error(), 'Cannot enumerate running processes.')
    try:
        entry=ProcessEntry();entry.dwSize=ctypes.sizeof(entry)
        more=kernel.Process32FirstW(snapshot,ctypes.byref(entry))
        while more:
            if entry.szExeFile.lower() == 'prog.exe':
                process=kernel.OpenProcess(0x1000,False,entry.th32ProcessID)
                if not process:
                    raise ValueError('Cannot inspect a running prog.exe; close it before installing/removing.')
                try:
                    size=w.DWORD(32768);buffer=ctypes.create_unicode_buffer(size.value)
                    if not kernel.QueryFullProcessImageNameW(process,0,buffer,ctypes.byref(size)):
                        raise ValueError('Cannot inspect a running prog.exe; close it first.')
                    if Path(buffer.value).resolve() == target(root,'prog.exe'):
                        raise ValueError(f'The target game is running (PID {entry.th32ProcessID}); close it first.')
                finally:
                    kernel.CloseHandle(process)
            more=kernel.Process32NextW(snapshot,ctypes.byref(entry))
    finally:
        kernel.CloseHandle(snapshot)


def patch_bytes(before):
    """Identical PE transformation to the inspected and tested loader_patch.py."""
    if sha(before) != ORIGINAL_EXE:
        raise ValueError('Unsupported prog.exe SHA-256; no patch is applied.')
    pe=pefile.PE(data=before)
    if pe.FILE_HEADER.Machine != 0x14c or pe.OPTIONAL_HEADER.DllCharacteristics & 0x40:
        raise ValueError('Requires the verified non-ASLR x86 executable.')
    align=lambda n,a:(n+a-1)//a*a
    base=pe.OPTIONAL_HEADER.ImageBase
    iat={entry.name:entry.address for imp in pe.DIRECTORY_ENTRY_IMPORT for entry in imp.imports}
    old_entry=pe.OPTIONAL_HEADER.AddressOfEntryPoint
    rva=align(pe.OPTIONAL_HEADER.SizeOfImage,pe.OPTIONAL_HEADER.SectionAlignment)
    va=base+rva
    stub=(b'\x9c\x60\x68'+struct.pack('<I',va+31)+b'\xff\x15'+struct.pack('<I',iat[b'LoadLibraryA'])
          +b'\x68'+struct.pack('<I',350)+b'\xff\x15'+struct.pack('<I',iat[b'Sleep'])
          +b'\x61\x9d\xe9'+struct.pack('<i',base+old_entry-(va+31)))
    if len(stub)!=31:raise ValueError('Unexpected startup stub size.')
    payload=stub+b'dr2c-gadget.dll\0'
    raw_start=align(len(before),pe.OPTIONAL_HEADER.FileAlignment)
    raw_size=align(len(payload),pe.OPTIONAL_HEADER.FileAlignment)
    header=pe.sections[-1].get_file_offset()+40
    if header+40>pe.OPTIONAL_HEADER.SizeOfHeaders or any(before[header:header+40]):
        raise ValueError('No unused PE section header.')
    after=bytearray(before)
    after[header:header+40]=struct.pack('<8sIIIIIIHHI',b'.dr2c\0\0\0',len(payload),rva,raw_size,raw_start,0,0,0,0,0x60000020)
    struct.pack_into('<H',after,pe.FILE_HEADER.get_field_absolute_offset('NumberOfSections'),pe.FILE_HEADER.NumberOfSections+1)
    for key,value in [('AddressOfEntryPoint',rva),('SizeOfImage',align(rva+len(payload),pe.OPTIONAL_HEADER.SectionAlignment)),('SizeOfCode',pe.OPTIONAL_HEADER.SizeOfCode+raw_size)]:
        struct.pack_into('<I',after,pe.OPTIONAL_HEADER.get_field_absolute_offset(key),value)
    after.extend(b'\0'*(raw_start-len(after)));after.extend(payload+b'\0'*(raw_size-len(payload)))
    struct.pack_into('<I',after,pe.OPTIONAL_HEADER.get_field_absolute_offset('CheckSum'),pefile.PE(data=bytes(after)).generate_checksum())
    if sha(after)!=PATCHED_EXE:
        raise ValueError('Generated executable differs from the tested patch; no write is allowed.')
    return bytes(after)


def read_json(path):
    return json.loads(path.read_text('utf-8'))


def json_bytes(value):
    return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')


def write_installation_record(root,record_path,record):
    """Keep a discoverable installation record, including incomplete rollbacks."""
    atomic_write(record_path,json_bytes(record))
    state={'schema':1,'installation_id':record['installation_id'],
           'game_root':str(root),'backup_root':record['backup_root'],
           'manifest_sha256':file_sha(record_path)}
    atomic_write(target(root,STATE_FILE),json_bytes(state))


def atomic_write(path,data):
    temp=path.parent/('.drtc-ko-'+uuid.uuid4().hex+'.tmp')
    try:
        with temp.open('xb') as f:
            f.write(data);f.flush();os.fsync(f.fileno())
        os.replace(temp,path)
    finally:
        if temp.exists():temp.unlink()


def make_parents(root,path,created):
    missing=[];current=path.parent
    while current!=root and not current.exists():
        missing.append(current);current=current.parent
    for directory in reversed(missing):
        target(root,directory.relative_to(root).as_posix()).mkdir()
        created.add(directory.relative_to(root).as_posix())


def remove_empty_dirs(root,directories):
    for rel in sorted(set(directories),key=lambda x:len(PurePosixPath(x).parts),reverse=True):
        p=target(root,rel)
        if p.exists():
            try:p.rmdir()
            except OSError:
                if any(p.iterdir()):continue
                raise


def acquire_lock(root,token):
    path=target(root,LOCK_FILE)
    with path.open('xb') as f:f.write(token.encode('ascii'))


def release_lock(root,token):
    path=target(root,LOCK_FILE)
    if path.exists() and path.read_text('ascii')==token:path.unlink()


def load_payload(payload_root):
    root=Path(payload_root).resolve(strict=True)
    manifest=read_json(root/'manifest.json')
    if manifest.get('schema')!=1 or manifest.get('game_build')!='24936165' or manifest.get('original_exe_sha256')!=ORIGINAL_EXE:
        raise ValueError('Unsupported/malformed payload manifest.')
    expected=manifest.get('source_sha256',{})
    if len(expected)!=562:raise ValueError('Expected 562 verified English scripts.')
    shipped=read_json(Path(__file__).resolve().parent.parent/'data/expected_source.json')
    if expected!=shipped.get('source_sha256'):
        raise ValueError('Payload source hashes differ from the shipped supported-build inventory.')
    for rel,h in expected.items():
        if not safe_relative(rel).startswith('deathforth/') or not rel.endswith('.df'):
            raise ValueError('Unexpected source-script path.')
        validate_hash(h)
    entries=manifest.get('files',[]);names=set()
    for entry in entries:
        rel=safe_relative(entry['target']);src=safe_relative(entry['source'])
        if rel.casefold() in names:raise ValueError('Duplicate payload target.')
        names.add(rel.casefold());validate_hash(entry['sha256'])
        if rel in {'prog.exe',STATE_FILE,LOCK_FILE,'steam_appid.txt'} or rel.startswith('deathforth/'):
            raise ValueError(f'Forbidden payload target: {rel}')
        if not (src.startswith('loader/') or src.startswith('DRTC_KO/')):
            raise ValueError('Payload source must be loader/ or DRTC_KO/.')
        if src.startswith('loader/') and rel!=src[len('loader/'):]:
            raise ValueError('Loader file layout must preserve its relative paths.')
        if src.startswith('DRTC_KO/') and rel!='mods/'+src:
            raise ValueError('Korean resources must install only into mods/DRTC_KO/.')
        p=target(root,src)
        if not p.is_file() or file_sha(p)!=entry['sha256']:
            raise ValueError(f'Payload file SHA-256 mismatch: {src}')
    if not {'dr2c-gadget.dll','dr2c-gadget.config','mods/dr2c-mod-loader/index.js','mods/drtc_ko/package.json'}<=names:
        raise ValueError('Required loader/Korean mod payload files are missing.')
    return root,manifest


def preflight(game,payload_root,backup_root=None):
    root=game_root(game);assert_not_running(root)
    if target(root,STATE_FILE).exists() or target(root,LOCK_FILE).exists():
        raise ValueError('An installation record or operation lock already exists.')
    payload,definition=load_payload(payload_root)
    if payload==root or payload.is_relative_to(root) or root.is_relative_to(payload):
        raise ValueError('Payload and game folders must not overlap.')
    original=target(root,'prog.exe').read_bytes();patched=patch_bytes(original)
    for rel,expected in definition['source_sha256'].items():
        p=target(root,rel)
        if not p.is_file() or file_sha(p)!=expected:
            raise ValueError(f'Unsupported/modified English script: {rel}')
    snapshot,dirs=tree(root)
    stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup=(Path(backup_root) if backup_root else root.parent/(root.name+'_KO_backup_'+stamp)).resolve()
    if backup.exists():raise ValueError('Backup root must be a new, nonexistent folder.')
    if backup==root or backup.is_relative_to(root) or root.is_relative_to(backup):
        raise ValueError('Backup and game roots must not overlap.')
    if backup==payload or backup.is_relative_to(payload) or payload.is_relative_to(backup):
        raise ValueError('Backup and payload roots must not overlap.')
    changes=[]
    for entry in definition['files']:
        rel=entry['target'];path=target(root,rel)
        if path.exists() and not path.is_file():raise ValueError(f'Target is not a regular file: {rel}')
        old=snapshot.get(rel,{}).get('sha256')
        if old!=entry['sha256']:
            changes.append({'path':rel,'original_sha256':old,'installed_sha256':entry['sha256'],'payload_source':entry['source']})
    changes.append({'path':'prog.exe','original_sha256':ORIGINAL_EXE,'installed_sha256':PATCHED_EXE,'payload_source':None})
    return root,payload,backup,definition,snapshot,dirs,changes,patched


def install(game,payload_root,backup_root=None,apply=False,_fail_after=None):
    root,payload,backup,definition,snapshot,dirs,changes,patched=preflight(game,payload_root,backup_root)
    result={'mode':'install','apply':apply,'game_root':str(root),'backup_root':str(backup),'game_build':definition['game_build'],
            'original_files':len(snapshot),'original_bytes':sum(v['size'] for v in snapshot.values()),
            'changed_files':sum(c['original_sha256'] is not None for c in changes),'added_files':sum(c['original_sha256'] is None for c in changes),
            'patched_exe_sha256':PATCHED_EXE}
    if not apply:return result
    backup.mkdir(parents=True,exist_ok=False)
    original_root=backup/'original';original_root.mkdir()
    for rel in dirs:target(original_root,rel).mkdir(parents=True,exist_ok=True)
    for rel in snapshot:
        dest=target(original_root,rel);dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(target(root,rel),dest)
    copied,copied_dirs=tree(original_root)
    if copied!=snapshot or copied_dirs!=dirs:
        raise ValueError(f'Full backup verification failed; game unchanged. Inspect {backup}')
    if tree(root)!=(snapshot,dirs):
        raise ValueError(f'Game changed while copying the backup; game unchanged by installer. Backup: {backup}')
    assert_not_running(root)
    token=uuid.uuid4().hex;created=set();applied=[]
    record={'schema':1,'status':'prepared','installation_id':token,'created_at':datetime.datetime.now().astimezone().isoformat(),
            'game_root':str(root),'backup_root':str(backup),'game_build':definition['game_build'],'original_files':snapshot,
            'original_directories':dirs,'changes':changes,'created_directories':[],'payload_manifest_sha256':file_sha(payload/'manifest.json')}
    record_path=backup/BACKUP_MANIFEST;atomic_write(record_path,json_bytes(record))
    acquire_lock(root,token)
    try:
        for change in changes:
            path=target(root,change['path'])
            current=file_sha(path) if path.is_file() else None
            if current!=change['original_sha256']:raise ValueError(f'Concurrent modification: {change["path"]}')
            make_parents(root,path,created)
            data=patched if change['path']=='prog.exe' else target(payload,change['payload_source']).read_bytes()
            if sha(data)!=change['installed_sha256']:raise ValueError('Payload changed during installation.')
            if change['path']=='prog.exe':assert_not_running(root)
            # Register before replacing: Ctrl+C can arrive after os.replace
            # succeeds but before the caller receives its return value.
            applied.append(change);atomic_write(path,data)
            if file_sha(path)!=change['installed_sha256']:raise ValueError('Installed file verification failed.')
            if _fail_after is not None and len(applied)>=_fail_after:raise OSError('Injected test failure')
        record['status']='installed';record['created_directories']=sorted(created)
        write_installation_record(root,record_path,record)
        result.update({'status':'installed','backup_verified':True,'manifest':str(record_path)})
        return result
    except (Exception,KeyboardInterrupt) as error:
        failures=[]
        for change in reversed(applied):
            try:
                path=target(root,change['path'])
                current=file_sha(path) if path.is_file() else None
                if current==change['original_sha256']:continue
                if current!=change['installed_sha256']:
                    raise ValueError('Changed externally during rollback; preserved for manual review.')
                if change['original_sha256'] is None:path.unlink()
                else:atomic_write(path,target(original_root,change['path']).read_bytes())
            except (Exception,KeyboardInterrupt) as rollback_error:failures.append(f'{change["path"]}: {rollback_error}')
        try:remove_empty_dirs(root,created)
        except (Exception,KeyboardInterrupt) as directory_error:failures.append(str(directory_error))
        record.update({'status':'rollback-incomplete' if failures else 'rolled-back','created_directories':sorted(created),
                       'error':str(error),'rollback_errors':failures})
        if failures:
            write_installation_record(root,record_path,record)
        else:
            atomic_write(record_path,json_bytes(record))
            state_path=target(root,STATE_FILE)
            if state_path.exists():
                if read_json(state_path).get('installation_id')!=token:
                    raise ValueError('Installation state changed externally; preserved.') from error
                state_path.unlink()
        raise ValueError(f'Installation failed: {error}. Rollback: {record["status"]}. Backup: {backup}. '+ '; '.join(failures)) from error
    finally:
        release_lock(root,token)


def uninstall(game,apply=False,_fail_after=None):
    root=game_root(game);assert_not_running(root)
    if target(root,LOCK_FILE).exists():raise ValueError('An operation lock already exists.')
    state_path=target(root,STATE_FILE)
    if not state_path.is_file():raise ValueError('No Korean patch installation record in this game folder.')
    state=json.loads(state_path.read_bytes())
    if state.get('schema')!=1 or Path(state['game_root']).resolve()!=root:raise ValueError('Installation root does not match the record.')
    backup=Path(state['backup_root']).resolve(strict=True)
    if backup==root or backup.is_relative_to(root) or root.is_relative_to(backup):raise ValueError('Unsafe backup root in record.')
    record_path=backup/BACKUP_MANIFEST
    if file_sha(record_path)!=state['manifest_sha256']:raise ValueError('Backup installation manifest changed.')
    record=read_json(record_path)
    prior_status=record.get('status')
    if prior_status not in {'installed','rollback-incomplete'} or record.get('installation_id')!=state['installation_id']:
        raise ValueError('Invalid installation record state.')
    original_root=backup/'original'
    if tree(original_root)!=(record['original_files'],record['original_directories']):
        raise ValueError('Full original backup hash/directory verification failed.')
    originals={};actions=[]
    for change in record['changes']:
        path=target(root,change['path']);validate_hash(change['installed_sha256'])
        current=file_sha(path) if path.is_file() else None
        if current is None and change['original_sha256'] is None:continue
        if prior_status=='rollback-incomplete' and current==change['original_sha256']:continue
        if current!=change['installed_sha256']:
            raise ValueError(f'Installed file was modified or removed; removal refused: {change["path"]}')
        if change['original_sha256'] is not None:
            validate_hash(change['original_sha256'])
            if file_sha(target(original_root,change['path']))!=change['original_sha256']:
                raise ValueError('Restoration file hash mismatch.')
        originals[change['path']]=path.read_bytes();actions.append(change)
    result={'mode':'uninstall','apply':apply,'game_root':str(root),'backup_root':str(backup),
            'restore_files':sum(c['original_sha256'] is not None for c in actions),'remove_added_files':sum(c['original_sha256'] is None for c in actions)}
    if not apply:return result
    token=uuid.uuid4().hex;applied=[];created=set()
    assert_not_running(root);acquire_lock(root,token)
    try:
        for change in reversed(actions):
            path=target(root,change['path'])
            if not path.is_file() or file_sha(path)!=change['installed_sha256']:
                raise ValueError(f'Concurrent modification: {change["path"]}')
            applied.append(change)
            if change['original_sha256'] is None:path.unlink()
            else:atomic_write(path,target(original_root,change['path']).read_bytes())
            if _fail_after is not None and len(applied)>=_fail_after:raise OSError('Injected test failure')
        # Directory cleanup can fail too; keep the installed record until it
        # has succeeded so the exception handler can restore a retryable state.
        remove_empty_dirs(root,record['created_directories'])
        record['status']='uninstalled';record['removed_at']=datetime.datetime.now().astimezone().isoformat()
        atomic_write(record_path,json_bytes(record))
        state_path.unlink()
        result['status']='uninstalled';return result
    except (Exception,KeyboardInterrupt) as error:
        failures=[]
        for change in reversed(applied):
            try:
                path=target(root,change['path'])
                expected=change['original_sha256'];current=file_sha(path) if path.is_file() else None
                if current==change['installed_sha256']:continue
                if current!=expected:raise ValueError('Changed externally during rollback; preserved.')
                make_parents(root,path,created);atomic_write(path,originals[change['path']])
            except (Exception,KeyboardInterrupt) as rollback_error:failures.append(f'{change["path"]}: {rollback_error}')
        record['status']='rollback-incomplete' if failures else prior_status
        record.pop('removed_at',None)
        record['error']=str(error);record['rollback_errors']=failures
        write_installation_record(root,record_path,record)
        raise ValueError(f'Removal failed: {error}; rollback errors: {failures}; backup: {backup}') from error
    finally:
        release_lock(root,token)

