import importlib.util
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import unittest

spec=importlib.util.spec_from_file_location('refresh',Path(__file__).resolve().parents[1]/'refresh.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class BrowserRefresh(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.profile=self.root/'profile';self.profile.mkdir()
        self.command=self.root/'browser';self.log=self.root/'invoked'
        self.command.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > '+str(self.log)+'\n')
        self.command.chmod(0o755)

    def live_profile(self):
        self.lock=self.profile/'SingletonLock';self.lock.symlink_to(socket.gethostname()+'-'+str(os.getpid()))
        self.endpoint=socket.socket(socket.AF_UNIX);self.addCleanup(self.endpoint.close)
        self.endpoint.bind(str(self.profile/'SingletonSocket'))

    def test_closed_browser_is_never_started(self):
        self.assertEqual(m.refresh(self.command,self.profile),'not-running')
        self.assertFalse(self.log.exists())

    def test_existing_default_profile_receives_refresh_arguments(self):
        self.live_profile()
        self.assertEqual(m.refresh(self.command,self.profile),'refreshed')
        self.assertEqual(self.log.read_text().splitlines(),['--refresh-platform-policy','--no-startup-window'])

    def test_stale_or_remote_lock_is_not_a_running_profile(self):
        self.live_profile()
        for value in ['remote-host-2',socket.gethostname()+'-999999999',socket.gethostname()+'-0']:
            self.lock.unlink();self.lock.symlink_to(value)
            self.assertEqual(m.refresh(self.command,self.profile),'not-running')
        self.assertFalse(self.log.exists())

    def test_hung_invocation_is_bounded_and_existing_process_survives(self):
        self.live_profile()
        self.command.write_text('#!/bin/sh\nexec sleep 60\n')
        start=time.monotonic()
        self.assertEqual(m.refresh(self.command,self.profile,timeout=.1),'timeout')
        self.assertLess(time.monotonic()-start,3)
        self.assertTrue(m.running_profile(self.profile))

    def test_missing_socket_does_not_start_a_browser(self):
        (self.profile/'SingletonLock').symlink_to(socket.gethostname()+'-'+str(os.getpid()))
        self.assertEqual(m.refresh(self.command,self.profile),'not-running')
        self.assertFalse(self.log.exists())
