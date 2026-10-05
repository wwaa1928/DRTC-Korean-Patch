"""Build a resources-only Korean DRTC mod from verified English source + PO.

Python 3.10+, polib. The game/backup and original PO batches are read-only.
The output folder must be outside the source tree and is never recursively deleted.
"""
from pathlib import Path, PurePosixPath
import argparse, collections, hashlib, json, re, shutil, tempfile, unicodedata
import sys
sys.dont_write_bytecode=True
import polib
from tools.source_lexer import lex_literals, classify_literal
from PIL import Image

FORMAT = re.compile(r"(?<!\d)%(?:\d+\$)?[-+#0']*(?:\d+|\*)?(?:\.(?:\d+|\*))?(?:hh|h|ll|l|j|z|t|L)?[diuoxXfFeEgGaAcspn%]")
PARTICLE = re.compile(r'^(?:은\(는\)|이\(가\)|을\(를\)|와\(과\)|\(으\)로|의|에게|에서|에|은|는|이|가|을|를|와|과|도|만|로|으로|께|한테)')
PRONOUN_TOKEN = re.compile(r'(?<![A-Za-z])E(?:HIS|HE|HIM|HER|SHE)(?![A-Za-z])')
# Fortune prefixes already supply a separator before this dynamically picked tail.
SPACE_SUPPLIED_BY_PREVIOUS = {' die a terrible death!'}


def protected(s):
    return [ord(c) for c in s if ord(c)<32 or 0xe000<=ord(c)<=0xe0ff]


def whitespace_edges(s):
    # Newlines/tabs are independently checked in their exact sequence.
    return re.match(r'^ *',s)[0], re.search(r' *$',s)[0]


def restore_edges(source, translated):
    if source in SPACE_SUPPLIED_BY_PREVIOUS:
        return translated
    start,end=whitespace_edges(source)
    # An intentional Korean particle joins directly to the preceding name.
    if start and not translated.startswith((' ','\t','\r','\n')) and not PARTICLE.match(translated):
        translated=start+translated
    if end and not translated.endswith((' ','\t','\r','\n')):
        translated+=end
    return translated


def check(source, translated, label, atlas, script=True, empty=False):
    errors=[]
    if unicodedata.normalize('NFC',translated)!=translated:
        errors.append('not NFC')
    if script and '"' in translated:
        errors.append('double quote breaks DeathForth literal')
    if not script and translated.count('"')>source.count('"'):
        errors.append('added double quote')
    if FORMAT.findall(source)!=FORMAT.findall(translated) or source.count('%')!=translated.count('%'):
        errors.append('printf placeholder order/type/count changed')
    if protected(source)!=protected(translated):
        errors.append('control/icon/newline/tab sequence changed')
    if PRONOUN_TOKEN.findall(source)!=PRONOUN_TOKEN.findall(translated):
        errors.append('epilogue pronoun replacement tokens changed')
    if not empty:
        original_start,original_end=whitespace_edges(source)
        translated_start,translated_end=whitespace_edges(translated)
        if original_start and not translated_start and source not in SPACE_SUPPLIED_BY_PREVIOUS and not (PARTICLE.match(translated) or translated.startswith(('\t','\r','\n'))):
            errors.append('leading whitespace changed')
        if original_end and not translated.endswith((' ','\t','\r','\n')):
            errors.append('trailing whitespace changed')
    for c in set(translated):
        cp=ord(c)
        if cp<=0x7f or 0xe000<=cp<=0xe0ff:
            continue
        if cp>0xffff:
            errors.append(f'non-BMP character U+{cp:X}')
        elif not atlas.crop(((cp&255)*12,(cp>>8)*12,(cp&255)*12+12,(cp>>8)*12+12)).getchannel('A').getbbox():
            errors.append(f'empty atlas glyph U+{cp:04X}')
    if errors:
        raise ValueError(f'{label}: '+ '; '.join(errors))


def safe_relative(path):
    p=PurePosixPath(path.replace('\\','/'))
    if p.is_absolute() or '..' in p.parts or ':' in path or not p.parts or p.parts[0]!='deathforth' or p.suffix!='.df':
        raise ValueError(f'Unsafe/non-script PO context: {path}')
    return p.as_posix()


def technical_row(row):
    # Inspect the code after the closing quote, not words inside the literal.
    context=row.get('source_context','')
    tail=context.split('"'+row['source']+'"',1)[-1] if '"'+row['source']+'"' in context else ''
    line=(tail.splitlines()[0] if tail.splitlines() else tail).split('"',1)[0].split('//',1)[0]
    return bool(re.search(r'(?:\$anew|\$load|\$picklocid|only-with-door|evaluate|\.name!|\.trait!|\.perk!)(?:\s|$)',line) or
                re.search(r'\b(?:DBG|ABORT)\b',line) or
                re.search(r'(?:^|\s):(?:map|tags|tiles|script[A-Z]|size|off)\s',row['source']) or
                re.search(r'^(?:DBG\b|ABORT(?:[:!]|$)|Oldstats-transfer:|old-total-)|APPLIED ON CHAR',row['source']) or
                row['source'] in {'TRANSIENT','DBG','ABORT'})


def build(source, inventory, summary, po_paths, atlas_path, language_json, output, native_po=None, native_samples=None, do_not_translate=None):
    source,output=source.resolve(strict=True),output.resolve()
    release=Path(__file__).resolve().parent
    for protected_root in (source,release):
        if output==protected_root or output.is_relative_to(protected_root) or protected_root.is_relative_to(output):
            raise ValueError('Output must not overlap the game or release folder.')
    hashes=json.loads(summary.read_text('utf-8'))['source_sha256']
    original={}
    for rel,expected in hashes.items():
        safe_relative(rel)
        b=(source/rel).read_bytes()
        if hashlib.sha256(b).hexdigest()!=expected:
            raise ValueError(f'Source SHA-256 mismatch: {rel}; no output written.')
        original[rel]=b
    if inventory is None:
        quoted_words={m.group(1) for b in original.values() for m in re.finditer(rb'(?m)^[ \t]*:[ \t]+("[^"\s]+)(?=\s|$)',b)}
        rows=[]
        for rel,b in original.items():
            literals,issues=lex_literals(b,quoted_words)
            if issues:raise ValueError(f'Literal lexer warnings: {rel}: {issues}')
            for item in literals:
                start,end=item['start'],item['end']
                rows.append({'id':f'{rel}:{start}','path':rel,'source':item['source'],
                    'byte_start':start,'byte_end':end,
                    'category':classify_literal(item,b[end+1:end+100]),
                    'source_context':b[max(0,item['opening']-100):min(len(b),end+100)].decode('utf-8','replace')})
    else:
        rows=[json.loads(line) for line in inventory.read_text('utf-8').splitlines()]
    index=collections.defaultdict(list)
    for row in rows:
        rel=safe_relative(row['path'])
        b=original[rel]
        if b[row['byte_start']:row['byte_end']]!=row['source'].encode('utf-8'):
            raise ValueError(f'Inventory byte range mismatch: {row["id"]}')
        index[(rel,row['source'])].append(row)
    atlas=Image.open(atlas_path).convert('RGBA')
    if atlas.size!=(3072,3072):
        raise ValueError('Incorrect font atlas size.')
    if do_not_translate is None:
        do_not_translate=Path(__file__).parent/'data/protected_strings.json'
    if not do_not_translate.is_file():
        raise ValueError('Required comparison-identifier block list is missing.')
    compared=set(json.loads(do_not_translate.read_text('utf-8-sig')))
    # The English catalog is also needed when building script-only samples.
    native_catalog=native_po or Path(__file__).parent/'translations/native-ko.po'
    if not native_catalog.is_file():
        raise ValueError('Required native string catalog is missing.')
    native_ids={e.msgid for e in polib.pofile(str(native_catalog)) if not e.obsolete}
    blocked=compared|native_ids
    translations={}
    ignored=[]
    empty_entries=0
    adjusted_edges=[]
    for p in po_paths:
        for e in polib.pofile(str(p)):
            if e.obsolete or not e.msgstr or 'fuzzy' in e.flags:
                continue
            rel=safe_relative(e.msgctxt or '')
            key=(rel,e.msgid)
            if e.msgid in blocked:
                ignored.append({'path':rel,'source':e.msgid,'reason':'comparison/native identifier'})
                continue
            eligible=[x for x in index.get(key,[]) if x['category']=='text-candidate' and not technical_row(x)]
            if index.get(key) and not eligible:
                ignored.append({'path':rel,'source':e.msgid,'reason':'technical literal'})
                continue
            if not eligible:
                raise ValueError(f'Unknown or technical source: {rel}/{e.msgid!r}')
            is_empty=e.msgstr=='<EMPTY>'
            t='' if is_empty else e.msgstr
            if not is_empty and whitespace_edges(e.msgid)!=whitespace_edges(t):
                # Preserve original fragment separators even if a translator omitted them.
                adjusted=restore_edges(e.msgid,t)
                if adjusted!=t:
                    adjusted_edges.append({'path':rel,'source':e.msgid})
                t=adjusted
            check(e.msgid,t,f'{p.name}/{rel}/{e.occurrences}',atlas,empty=is_empty)
            if key in translations and translations[key]!=t:
                raise ValueError(f'Conflicting translations: {key}')
            translations[key]=t
            empty_entries+=int(is_empty)
    changed={}
    replacements=collections.defaultdict(list)
    for key,t in translations.items():
        for row in index[key]:
            if row['category']=='text-candidate' and not technical_row(row):
                replacements[key[0]].append((row['byte_start'],row['byte_end'],t.encode('utf-8')))
    for rel,edits in replacements.items():
        b=original[rel]
        last_start=len(b)+1
        for start,end,t in sorted(edits,reverse=True):
            if end>last_start:
                raise ValueError(f'Overlapping replacements: {rel}')
            b=b[:start]+t+b[end:]
            last_start=start
        b.decode('utf-8')
        if b!=original[rel]:
            changed[rel]=b
    lang=json.loads(language_json.read_text('utf-8-sig'))
    ko=dict(lang['string_literal']['en'])
    applied_native=0
    for key,val in (native_samples or {}).items():
        check(key,val,f'native sample {key!r}',atlas,script=False)
        ko[key]=val
    if native_po:
        for e in polib.pofile(str(native_po)):
            if e.obsolete or not e.msgstr or 'fuzzy' in e.flags:
                continue
            key=e.msgctxt or e.msgid
            t='' if e.msgstr=='<EMPTY>' else e.msgstr
            check(e.msgid,t,f'native {key!r}',atlas,script=False,empty=e.msgstr=='<EMPTY>')
            ko[key]=t
            applied_native+=1
    ko['ko.Language.Name']='한국어'
    ko['ko.Language.Contributors.List']='DRTC Korean Patch contributors'
    lang['string_literal']['ko']=ko
    lang['selected_lang']='ko'
    # Do not overwrite stale generated script assets without detecting them.
    resources=output/'assets/dr2c'
    expected_paths={resources/rel for rel in changed}
    stale=[p for p in (resources/'deathforth').rglob('*.df') if p not in expected_paths]
    if stale:
        raise ValueError(f'Stale generated files present; choose a fresh output folder: {stale}')
    output.mkdir(parents=True,exist_ok=True)
    for rel,b in changed.items():
        p=resources/rel
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(b)
    (output/'assets').mkdir(exist_ok=True)
    (output/'assets/lang.json').write_text(json.dumps(lang,ensure_ascii=False,indent=4),'utf-8')
    # Disable the optional template bridge explicitly; direct .df translations
    # do not use it. This matches the loader's missing-catalog fallback quietly.
    (resources/'i18n').mkdir(parents=True,exist_ok=True)
    (resources/'i18n/ko.json').write_text('null\n','utf-8')
    shutil.copy2(atlas_path,output/'assets/font_ucs2_12x12.png')
    license_file=Path(__file__).parent/'licenses/Galmuri-OFL.txt'
    if license_file.is_file():
        shutil.copy2(license_file,output/'Galmuri-LICENSE.txt')
    manifest={'name':'DRTC_KO','version':'0.2.0','description':'현재 영어 DeathForth 원문에서 생성한 한국어 리소스',
              'author':'DRTC Korean Patch contributors','dr2cRuntime':'resources-only','type':'commonjs','main':'index.js'}
    (output/'package.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),'utf-8')
    (output/'index.js').write_text('// Resource-only package; hooks are supplied by the installed V202.0 loader.\n','utf-8')
    record={'source_df_hashes_verified':len(hashes),'translated_script_entries':len(translations),
            'replaced_literal_occurrences':sum(len(v) for v in replacements.values()),'generated_df_files':len(changed),
            'native_po_entries_applied':applied_native,'blank_or_fuzzy_translations':'keep English',
            'empty_sentinel_entries':empty_entries,'compared_string_block_count':len(compared),
            'native_string_block_count':len(native_ids),'ignored_translations':ignored,
            'whitespace_edges_restored':adjusted_edges,
            'files':[{'path':rel,'source_sha256':hashes[rel],'output_sha256':hashlib.sha256(b).hexdigest()} for rel,b in changed.items()]}
    return record


RELEASE_ROOT=Path(__file__).resolve().parent
LOADER_PATHS={
    'dr2c-gadget.config','dr2c-gadget.dll',
    'mods/dr2c-mod-loader/index.html','mods/dr2c-mod-loader/index.js',
    'mods/dr2c-mod-loader/main.js','mods/dr2c-mod-loader/package.json',
    'mods/dr2c-mod-loader/assets/font_ucs2_12x12.png',
    'mods/dr2c-mod-loader/assets/lang.json',
}


def verified_loader(loader_root):
    from tools.installer_common import target,file_sha,validate_hash,is_link
    root=Path(loader_root).resolve(strict=True)
    if not root.is_dir() or is_link(root):
        raise ValueError('Loader root must be a regular directory.')
    definition=json.loads((RELEASE_ROOT/'data/loader_files.json').read_text('utf-8'))['files']
    if set(definition)!=LOADER_PATHS:
        raise ValueError('Unexpected loader file inventory.')
    for rel,expected in definition.items():
        validate_hash(expected)
        p=target(root,rel)
        if not p.is_file() or file_sha(p)!=expected:
            raise ValueError(f'Loader SHA-256 mismatch or missing file: {rel}; use the unmodified V202.0 loader folder.')
    return root,definition


def merge_hangul(base_path,output):
    with Image.open(base_path) as image:
        base=image.convert('RGBA')
    with Image.open(RELEASE_ROOT/'fonts/hangul_12x12.png') as image:
        overlay=image.convert('RGBA')
    if base.size!=(3072,3072) or overlay.size!=base.size:
        raise ValueError('Incorrect atlas dimensions.')
    for cp in (*range(0xac00,0xd7a4),*range(0x3131,0x318f)):
        x,y=(cp&255)*12,(cp>>8)*12
        # Paste the whole cell, including transparent pixels (e.g. U+3164).
        base.paste(overlay.crop((x,y,x+12,y+12)),(x,y))
    base.save(output)


def build_local(game_root,loader_root,output):
    source=Path(game_root).resolve(strict=True)
    loader,_=verified_loader(loader_root)
    output=Path(output).resolve()
    for root in (source,loader,RELEASE_ROOT):
        if output==root or output.is_relative_to(root) or root.is_relative_to(output):
            raise ValueError('Output must not overlap the game, loader, or release folder.')
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError('Choose a new or empty output folder.')
    temp_base=Path(tempfile.gettempdir()).resolve()
    if any(temp_base==p or temp_base.is_relative_to(p) for p in (source,loader,RELEASE_ROOT)):
        raise ValueError('Temporary storage must be outside the game, loader, and release folder.')
    with tempfile.TemporaryDirectory(prefix='drtc-ko-atlas-') as folder:
        atlas=Path(folder)/'font.png'
        merge_hangul(loader/'mods/dr2c-mod-loader/assets/font_ucs2_12x12.png',atlas)
        return build(source,None,RELEASE_ROOT/'data/expected_source.json',
            [RELEASE_ROOT/'translations'/f'{n:03}.po' for n in range(1,34)],
            atlas,loader/'mods/dr2c-mod-loader/assets/lang.json',output,
            native_po=RELEASE_ROOT/'translations/native-ko.po')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root',type=Path,required=True)
    parser.add_argument('--loader-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True,help='New/empty directory outside the game, loader, and release.')
    args=parser.parse_args()
    try:
        result=build_local(args.game_root,args.loader_root,args.output)
        print(json.dumps({k:v for k,v in result.items() if k not in {'files','ignored_translations','whitespace_edges_restored'}},ensure_ascii=False,indent=2))
    except Exception as error:
        print('ERROR: '+str(error),file=sys.stderr)
        return 1
    return 0


if __name__=='__main__':raise SystemExit(main())

