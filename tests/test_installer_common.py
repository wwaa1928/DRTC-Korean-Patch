"""Filesystem transaction regressions; no game files or Windows process APIs."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import installer_common as common


class TransactionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)
        self.game=self.base/'game';self.game.mkdir()
        self.backup=self.base/'backup'
        self.original_exe=b'original executable fixture'
        self.installed_exe=b'installed executable fixture'
        (self.game/'prog.exe').write_bytes(self.original_exe)
        self.changes=[
            {'path':'mods/ko.txt','original_sha256':None,
             'installed_sha256':common.sha(b'translated fixture'),'payload_source':'DRTC_KO/ko.txt'},
            {'path':'prog.exe','original_sha256':common.sha(self.original_exe),
             'installed_sha256':common.sha(self.installed_exe),'payload_source':None}]
        self.addCleanup(patch.stopall)
        patch.object(common,'assert_not_running').start()

    def install(self,**kwargs):
        payload=self.base/'payload'
        payload.mkdir(exist_ok=True)
        (payload/'DRTC_KO').mkdir(exist_ok=True)
        (payload/'DRTC_KO/ko.txt').write_bytes(b'translated fixture')
        (payload/'manifest.json').write_text('{}')
        snapshot,dirs=common.tree(self.game)
        prepared=(self.game,payload,self.backup,{'game_build':'24936165'},
                  snapshot,dirs,self.changes,self.installed_exe)
        with patch.object(common,'preflight',return_value=prepared):
            return common.install(self.game,payload,apply=True,**kwargs)

    def record(self):
        state=common.read_json(self.game/common.STATE_FILE)
        path=self.backup/common.BACKUP_MANIFEST
        self.assertEqual(state['manifest_sha256'],common.file_sha(path))
        return common.read_json(path)

    def assert_installed(self):
        self.assertEqual((self.game/'prog.exe').read_bytes(),self.installed_exe)
        self.assertEqual((self.game/'mods/ko.txt').read_bytes(),b'translated fixture')
        self.assertEqual(self.record()['status'],'installed')
        self.assertFalse((self.game/common.LOCK_FILE).exists())

    def interrupt_once(self,after):
        write=common.atomic_write
        fired=False
        def replacement(path,data):
            nonlocal fired
            if path==self.game/'prog.exe' and not fired:
                fired=True
                if after:write(path,data)
                raise KeyboardInterrupt('Ctrl+C fixture')
            return write(path,data)
        return patch.object(common,'atomic_write',side_effect=replacement)

    def test_install_interrupt_before_replace(self):
        self.check_install_interrupt(False)

    def test_install_interrupt_after_replace(self):
        self.check_install_interrupt(True)

    def check_install_interrupt(self,after):
        with self.interrupt_once(after),self.assertRaises(ValueError):self.install()
        self.assertEqual((self.game/'prog.exe').read_bytes(),self.original_exe)
        self.assertFalse((self.game/'mods').exists())
        self.assertFalse((self.game/common.STATE_FILE).exists())
        self.assertFalse((self.game/common.LOCK_FILE).exists())
        self.assertEqual(common.read_json(self.backup/common.BACKUP_MANIFEST)['status'],'rolled-back')

    def test_install_incomplete_rollback_can_be_removed(self):
        write=common.atomic_write
        calls=0
        def fail(path,data):
            nonlocal calls
            if path==self.game/'prog.exe':
                calls+=1
                if calls==1:
                    write(path,data)
                    raise KeyboardInterrupt('Ctrl+C fixture')
                raise PermissionError('Locked executable fixture')
            return write(path,data)
        with patch.object(common,'atomic_write',side_effect=fail),self.assertRaises(ValueError):self.install()
        self.assertEqual(self.record()['status'],'rollback-incomplete')
        result=common.uninstall(self.game,apply=True)
        self.assertEqual(result['status'],'uninstalled')
        self.assertEqual((self.game/'prog.exe').read_bytes(),self.original_exe)
        self.assertFalse((self.game/common.STATE_FILE).exists())

    def test_uninstall_interrupt_before_replace(self):
        self.check_uninstall_interrupt(False)

    def test_uninstall_interrupt_after_replace(self):
        self.check_uninstall_interrupt(True)

    def check_uninstall_interrupt(self,after):
        self.install()
        with self.interrupt_once(after),self.assertRaises(ValueError):common.uninstall(self.game,apply=True)
        self.assert_installed()
        self.assertEqual(common.uninstall(self.game,apply=True)['status'],'uninstalled')

    def test_uninstall_interrupt_after_unlink(self):
        self.install()
        unlink=Path.unlink
        fired=False
        def interrupted(path,*args,**kwargs):
            nonlocal fired
            unlink(path,*args,**kwargs)
            if path==self.game/'mods/ko.txt' and not fired:
                fired=True
                raise KeyboardInterrupt('Ctrl+C fixture')
        with patch.object(Path,'unlink',interrupted),self.assertRaises(ValueError):common.uninstall(self.game,apply=True)
        self.assert_installed()

    def test_cleanup_error_restores_retryable_installation(self):
        self.install()
        with patch.object(common,'remove_empty_dirs',side_effect=OSError('Locked directory fixture')),self.assertRaises(ValueError):
            common.uninstall(self.game,apply=True)
        self.assert_installed()

    def make_incomplete_removal(self):
        self.install()
        write=common.atomic_write
        calls=0
        def fail(path,data):
            nonlocal calls
            if path==self.game/'prog.exe':
                calls+=1
                if calls==2:raise PermissionError('Locked executable fixture')
            return write(path,data)
        with patch.object(common,'atomic_write',side_effect=fail),patch.object(common,'remove_empty_dirs',side_effect=OSError('Locked directory fixture')),self.assertRaises(ValueError):
            common.uninstall(self.game,apply=True)
        self.assertEqual(self.record()['status'],'rollback-incomplete')

    def test_incomplete_removal_can_finish_without_touching_other_files(self):
        self.make_incomplete_removal()
        (self.game/'user-save.txt').write_bytes(b'new player progress')
        before=common.tree(self.game)
        common.uninstall(self.game,apply=False)
        self.assertEqual(common.tree(self.game),before)
        self.assertEqual(common.uninstall(self.game,apply=True)['status'],'uninstalled')
        self.assertEqual((self.game/'prog.exe').read_bytes(),self.original_exe)
        self.assertFalse((self.game/'mods').exists())
        self.assertEqual((self.game/'user-save.txt').read_bytes(),b'new player progress')

    def test_recovery_refuses_external_changes(self):
        self.make_incomplete_removal()
        (self.game/'mods/ko.txt').write_bytes(b'user changes')
        before=common.tree(self.game)
        with self.assertRaisesRegex(ValueError,'modified or removed'):common.uninstall(self.game,apply=True)
        self.assertEqual(common.tree(self.game),before)

    def test_installed_record_still_refuses_unexpected_original_exe(self):
        self.install()
        (self.game/'prog.exe').write_bytes(self.original_exe)
        with self.assertRaisesRegex(ValueError,'modified or removed'):common.uninstall(self.game,apply=True)

    def test_interrupt_after_final_state_unlink_restores_record(self):
        self.install()
        unlink=Path.unlink
        fired=False
        def interrupted(path,*args,**kwargs):
            nonlocal fired
            unlink(path,*args,**kwargs)
            if path==self.game/common.STATE_FILE and not fired:
                fired=True
                raise KeyboardInterrupt('Ctrl+C fixture')
        with patch.object(Path,'unlink',interrupted),self.assertRaises(ValueError):common.uninstall(self.game,apply=True)
        self.assert_installed()

    def test_normal_install_and_uninstall(self):
        self.install();self.assert_installed()
        self.assertEqual(common.uninstall(self.game,apply=True)['status'],'uninstalled')
        self.assertEqual((self.game/'prog.exe').read_bytes(),self.original_exe)
        self.assertFalse((self.game/common.STATE_FILE).exists())
        self.assertFalse((self.game/common.LOCK_FILE).exists())
        self.assertFalse((self.game/'mods').exists())

    def test_ordinary_error_rollback(self):
        self.install()
        with self.assertRaises(ValueError):common.uninstall(self.game,apply=True,_fail_after=1)
        self.assert_installed()


if __name__=='__main__':unittest.main()
