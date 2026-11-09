"""Bind upgrade planning to the same local state that tam-deploy checks."""
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from test_cli import load


class BaselineIdentity(unittest.TestCase):
    def test_baseline_digest_covers_pin_receipt_and_active_generation(self):
        host = load('host')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = root / 'consumer'
            host_dir = config / 'hosts/fixture'
            (host_dir / 'state').mkdir(parents=True)
            (host_dir / 'host.json').write_text(json.dumps({'hostname': 'fixture', 'username': 'alex', 'system': 'x86_64-linux'}))
            assembly = 'a' * 40
            pin = host_dir / 'state/assembly'
            pin.write_text(assembly + '\n')
            state = root / 'state'
            deployment = state / 'tamlinux/deploy.json'
            deployment.parent.mkdir(parents=True)
            deployment.write_text(json.dumps({'packages': assembly, 'generation': '/nix/store/old'}))
            generation = root / 'generation'
            generation.mkdir()
            profile = state / 'nix/profiles/home-manager'
            profile.parent.mkdir(parents=True)
            profile.symlink_to(generation)
            with mock.patch.dict(os.environ, {'XDG_STATE_HOME': str(state)}), \
                 mock.patch.object(host.socket, 'gethostname', return_value='fixture'), \
                 mock.patch.object(host.getpass, 'getuser', return_value='alex'), \
                 mock.patch.object(host.os, 'uname', return_value=SimpleNamespace(machine='x86_64')), \
                 mock.patch.object(host, 'native_package', return_value=None):
                identity = {'assembly': assembly, 'generation': str(generation),
                            'pinSha256': hashlib.sha256(pin.read_bytes()).hexdigest(),
                            'receiptSha256': hashlib.sha256(deployment.read_bytes()).hexdigest()}
                expected = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
                self.assertEqual(host.local_profile(config)['baselineToken'], expected)
                deployment.write_text(deployment.read_text() + '\n')
                self.assertNotEqual(host.local_profile(config)['baselineToken'], expected)
                pin.unlink()
                (config / 'flake.lock').write_text('{}')
                self.assertIsNotNone(host.local_profile(config)['baselineToken'])


if __name__ == '__main__':
    unittest.main()
