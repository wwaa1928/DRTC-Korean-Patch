"""Ensure technical strings stay unchanged in generated script resources."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
import polib

import build_ko


def run_build(base,code,entries,source_hashes=None):
    """Build test.df from code and (msgid, msgstr) entries. Return the build record and the generated text."""
    source=base/'source';(source/'deathforth').mkdir(parents=True)
    rel='deathforth/test.df'
    (source/rel).write_bytes(code)
    summary=base/'summary.json'
    summary.write_text(json.dumps({'source_sha256':{rel:source_hashes or hashlib.sha256(code).hexdigest()}}),encoding='utf-8')
    po=polib.POFile()
    for msgid,msgstr in entries:
        po.append(polib.POEntry(msgctxt=rel,msgid=msgid,msgstr=msgstr))
    po_path=base/'test.po';po.save(str(po_path))
    # A synthetic atlas isolates classification from real font coverage.
    atlas=base/'font.png';Image.new('RGBA',(3072,3072),(255,255,255,255)).save(atlas)
    language=base/'lang.json'
    language.write_text(json.dumps({'string_literal':{'en':{}}}),encoding='utf-8')
    result=build_ko.build(source,None,summary,[po_path],atlas,language,base/'output')
    return result,(base/'output/assets/dr2c'/rel).read_text(encoding='utf-8')


class BuildClassificationTests(unittest.TestCase):
    def test_comparison_and_conversion_strings_are_not_replaced(self):
        with tempfile.TemporaryDirectory() as folder:
            code=b': check-foo "Foo" $= if 1 else 0 then ;\n"Convert" str>\n"Greeting" print\n'
            entries=[('Foo','\ud478'),('Convert','\ubcc0\ud658'),('Greeting','\uc778\uc0ac')]
            result,generated=run_build(Path(folder),code,entries)
            self.assertIn('"Foo" $=',generated)
            self.assertIn('"Convert" str>',generated)
            self.assertIn('"\uc778\uc0ac" print',generated)
            self.assertEqual(result['translated_script_entries'],1)
            self.assertEqual({row['source'] for row in result['ignored_translations']},{'Foo','Convert'})


class SourceVariantTests(unittest.TestCase):
    """The Linux perkdef.df is the second listed hash and lacks some Windows lines."""
    code=b'"Greeting" print\n'
    entries=[('Greeting','\uc778\uc0ac'),('Windows only','\uc708\ub3c4\uc6b0')]

    def test_variant_source_keeps_lines_it_lacks_in_english(self):
        with tempfile.TemporaryDirectory() as folder:
            result,generated=run_build(Path(folder),self.code,self.entries,['0'*64,hashlib.sha256(self.code).hexdigest()])
            self.assertEqual(generated,'"\uc778\uc0ac" print\n')
            self.assertEqual([(r['source'],r['reason']) for r in result['ignored_translations']],
                             [('Windows only','not in this game version')])

    def test_primary_source_refuses_unknown_lines(self):
        with tempfile.TemporaryDirectory() as folder,self.assertRaisesRegex(ValueError,'Unknown or technical source'):
            run_build(Path(folder),self.code,self.entries)


class LoaderVerificationTests(unittest.TestCase):
    def test_compatible_language_files_return_the_verified_digest(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            loader = root / 'loader'
            relative = 'mods/dr2c-mod-loader/assets/lang.json'
            path = loader / relative
            path.parent.mkdir(parents=True)
            variants = [b'V204.0 language file', b'V202.0 language file']
            hashes = [hashlib.sha256(value).hexdigest() for value in variants]
            data = root / 'data'
            data.mkdir()
            (data / 'loader_files.json').write_text(json.dumps({'files': {relative: hashes}}), encoding='utf-8')
            with patch.object(build_ko, 'RELEASE_ROOT', root), patch.object(build_ko, 'LOADER_PATHS', {relative}):
                for value, digest in zip(variants, hashes):
                    path.write_bytes(value)
                    self.assertEqual(build_ko.verified_loader(loader), (loader.resolve(), {relative: digest}))
                path.write_bytes(b'modified language file')
                with self.assertRaisesRegex(ValueError, 'Loader SHA-256 mismatch'):
                    build_ko.verified_loader(loader)


if __name__=='__main__':unittest.main()
