"""Ensure technical strings stay unchanged in generated script resources."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image
import polib

from build_ko import build


class BuildClassificationTests(unittest.TestCase):
    def test_comparison_and_conversion_strings_are_not_replaced(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder)
            source=base/'source';(source/'deathforth').mkdir(parents=True)
            rel='deathforth/test.df'
            code=b': check-foo "Foo" $= if 1 else 0 then ;\n"Convert" str>\n"Greeting" print\n'
            (source/rel).write_bytes(code)
            summary=base/'summary.json'
            summary.write_text(json.dumps({'source_sha256':{rel:hashlib.sha256(code).hexdigest()}}),encoding='utf-8')
            po=polib.POFile()
            for msgid,msgstr in [('Foo','\ud478'),('Convert','\ubcc0\ud658'),('Greeting','\uc778\uc0ac')]:
                po.append(polib.POEntry(msgctxt=rel,msgid=msgid,msgstr=msgstr))
            po_path=base/'test.po';po.save(str(po_path))
            # A synthetic atlas isolates classification from real font coverage.
            atlas=base/'font.png';Image.new('RGBA',(3072,3072),(255,255,255,255)).save(atlas)
            language=base/'lang.json'
            language.write_text(json.dumps({'string_literal':{'en':{}}}),encoding='utf-8')
            result=build(source,None,summary,[po_path],atlas,language,base/'output')
            generated=(base/'output/assets/dr2c'/rel).read_text(encoding='utf-8')
            self.assertIn('"Foo" $=',generated)
            self.assertIn('"Convert" str>',generated)
            self.assertIn('"\uc778\uc0ac" print',generated)
            self.assertEqual(result['translated_script_entries'],1)
            self.assertEqual({row['source'] for row in result['ignored_translations']},{'Foo','Convert'})


if __name__=='__main__':unittest.main()
