"""Linux/Proton running-game detection against a fake /proc tree."""
from pathlib import Path
import tempfile
import unittest

from tools import installer_common as common


class LinuxProcessTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name).resolve()
        self.game=self.base/'Death Road to Canada';self.game.mkdir()
        (self.game/'prog.exe').write_bytes(b'fixture')
        self.proc=self.base/'proc';self.proc.mkdir()
        (self.proc/'self').mkdir()

    def process(self,pid,*arguments):
        folder=self.proc/str(pid);folder.mkdir()
        (folder/'cmdline').write_bytes(b'\0'.join(a.encode() for a in arguments)+b'\0')

    def check(self):
        common._assert_not_running_linux(self.game,self.proc)

    def test_unrelated_processes_pass(self):
        self.process(10,'/usr/bin/steam','-silent')
        self.process(11,str(self.base/'Other Game'/'prog.exe'))
        (self.proc/'12').mkdir()  # exited: no cmdline left
        self.check()

    def test_proton_launcher_unix_path_is_detected(self):
        self.process(20,'python3','/proton','waitforexitandrun',str(self.game/'prog.exe'))
        with self.assertRaisesRegex(ValueError,'target game is running'):self.check()

    def test_wine_z_drive_path_is_detected(self):
        self.process(30,'Z:'+str(self.game/'PROG.EXE').replace('/','\\'))
        with self.assertRaisesRegex(ValueError,'target game is running'):self.check()

    def test_unmappable_wine_path_refuses(self):
        self.process(40,'C:\\Games\\prog.exe')
        with self.assertRaisesRegex(ValueError,'cannot be verified'):self.check()


if __name__=='__main__':unittest.main()
