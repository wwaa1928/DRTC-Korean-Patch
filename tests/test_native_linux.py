"""Native Linux install payload: game executable, Frida gadget and file layout, without game files."""
import json
import lzma
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import installer_common as common
from tools import release_install

LOADER_ASSETS = 'mods/dr2c-mod-loader/assets/'


class NativeLinuxTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.game = self.base/'game'; self.game.mkdir()
        (self.game/'prog-linux').write_bytes(b'linux executable fixture')
        self.addCleanup(patch.stopall)
        patch.object(common, 'LINUX_EXE_SHA256', common.sha(b'linux executable fixture')).start()

    def test_executable_accepts_pinned_prog_linux_without_patch(self):
        self.assertEqual(common.executable(self.game), (b'linux executable fixture', None))
        (self.game/'prog-linux').write_bytes(b'other build')
        with self.assertRaisesRegex(ValueError, 'Unsupported prog-linux'):
            common.executable(self.game)

    def test_gadget_from_xz_is_decompressed_and_verified(self):
        gadget = self.base/'gadget.so.xz'
        gadget.write_bytes(lzma.compress(b'gadget fixture'))
        with patch.object(release_install, 'GADGET_XZ_SHA256', common.file_sha(gadget)), \
             patch.object(release_install, 'GADGET_SHA256', common.sha(b'gadget fixture')):
            self.assertEqual(release_install.linux_gadget(gadget), b'gadget fixture')
            gadget.write_bytes(b'other file')
            with self.assertRaisesRegex(ValueError, 'Frida gadget SHA-256 mismatch'):
                release_install.linux_gadget(gadget)

    def test_payload_puts_korean_assets_in_loader_folder(self):
        """Installs lang.json to mods/DRTC_KO and over the loader's lang.json, and the .so instead of the .dll."""
        loader = self.base/'loader'
        files = {}
        for rel in ('dr2c-gadget.dll', 'dr2c-gadget.config', 'mods/dr2c-mod-loader/index.js', LOADER_ASSETS+'lang.json'):
            (loader/rel).parent.mkdir(parents=True, exist_ok=True)
            (loader/rel).write_bytes(rel.encode())
            files[rel] = common.sha(rel.encode())

        def build(game, loader, output):
            for rel in ('package.json', 'assets/lang.json'):
                (output/rel).parent.mkdir(parents=True, exist_ok=True)
                (output/rel).write_bytes(b'Korean '+rel.encode())
            return {}

        payload = self.base/'payload'
        with patch.object(release_install, 'verified_loader', return_value=(loader, files)), \
             patch.object(release_install, 'build_local', side_effect=build), \
             patch.object(release_install, 'linux_gadget', return_value=b'gadget fixture'), \
             patch.object(release_install, 'GADGET_SHA256', common.sha(b'gadget fixture')):
            release_install.prepare_payload(self.game, loader, payload)
            _, manifest = common.load_payload(payload)
        targets = {entry['target']: entry['source'] for entry in manifest['files']}
        self.assertEqual(targets, {
            'mods/DRTC_KO/package.json': 'DRTC_KO/package.json',
            'mods/DRTC_KO/assets/lang.json': 'DRTC_KO/assets/lang.json',
            LOADER_ASSETS+'lang.json': 'DRTC_KO/assets/lang.json',
            'dr2c-gadget.config': 'loader/dr2c-gadget.config',
            'mods/dr2c-mod-loader/index.js': 'loader/mods/dr2c-mod-loader/index.js',
            'dr2c-gadget.so': 'loader/dr2c-gadget.so'})
        self.assertEqual(manifest['original_exe_sha256'], common.LINUX_EXE_SHA256)

    def test_payload_refuses_other_korean_files_in_loader_folder(self):
        payload = self.base/'payload'; (payload/'DRTC_KO').mkdir(parents=True)
        (payload/'DRTC_KO/index.js').write_bytes(b'fixture')
        shipped = common.read_json(Path(common.__file__).resolve().parent.parent/'data/expected_source.json')
        manifest = {'schema': 1, 'game_build': shipped['game_build'], 'original_exe_sha256': common.LINUX_EXE_SHA256,
                    'source_sha256': shipped['source_sha256'],
                    'files': [{'source': 'DRTC_KO/index.js', 'target': 'mods/dr2c-mod-loader/index.js', 'sha256': common.sha(b'fixture')}]}
        (payload/'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Korean resources must install only'):
            common.load_payload(payload)


if __name__ == '__main__': unittest.main()
