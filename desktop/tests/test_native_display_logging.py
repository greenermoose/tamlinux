"""Compile the production emission sink; no compositor, DRM or journal access."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HEADER = ROOT / 'native/providers/display/DisplayLog.hpp'


@unittest.skipUnless(shutil.which('c++'), 'C++ compiler required')
class DisplayLoggingTests(unittest.TestCase):
    def test_clocks_severity_bounds_and_file_visibility(self):
        with tempfile.TemporaryDirectory() as directory:
            d = Path(directory)
            source = d / 'probe.cpp'
            source.write_text(r'''
#include "DisplayLog.hpp"
#include <filesystem>
#include <thread>
#include <chrono>
int main(int argc, char** argv) {
    Tamlinux::CDisplayLog log;
    if (!log.open(argv[1])) return 1;
    log.write("hyprland", 7, "hidden-debug");
    log.write("aquamarine", 7, "hidden-backend-debug");
    if (!log.write("hyprland", 3, "ordinary-error")) return 2;
    if (!std::filesystem::file_size(argv[1])) return 3;
    std::this_thread::sleep_for(std::chrono::milliseconds(20));
    log.write("aquamarine", 3, "backend-error output=TEST crtc=0");
    log.write("aquamarine", 6, "connector-transition output=TEST", true);
    log.write("hyprland", 4, "one\ntwo\rthree\tend");
    log.write("hyprland", 4, std::string(8000, 'x'));
    return 0;
}
''')
            binary = d / 'probe'
            subprocess.run(['c++', '-std=c++23', '-pthread', '-I'+str(HEADER.parent),
                            str(source), '-o', str(binary)], check=True, capture_output=True)
            file = d / 'native.log'
            result = subprocess.run([str(binary), str(file)], check=True, capture_output=True, text=True)
            stream = result.stdout.splitlines()
            retained = file.read_text().splitlines()
            self.assertEqual(len(stream), 5)
            self.assertEqual([re.sub(r'^<\d>', '', line) for line in stream], retained)
            self.assertTrue(all(len(line.encode()) < 4096 for line in stream))
            self.assertNotIn('hidden', result.stdout)
            mono = [int(re.search(r'monotonic_ns=(\d+)', line)[1]) for line in stream]
            self.assertEqual(mono, sorted(mono))
            self.assertGreaterEqual(mono[1]-mono[0], 10_000_000)
            self.assertIn('one two three end', retained[3])
            self.assertTrue(retained[-1].endswith('[truncated]'))
            target = d / 'protected.log'
            target.write_text('untouched')
            link = d / 'linked.log'
            link.symlink_to(target)
            refused = subprocess.run([str(binary), str(link)], capture_output=True, text=True)
            self.assertEqual(refused.returncode, 1)
            self.assertEqual(target.read_text(), 'untouched')
            self.assertTrue(all(re.search(r'wall_ns=\d+ monotonic_ns=\d+ component=\w+ severity=\d pid=\d+', line) for line in retained))

    def test_native_patch_embeds_the_exact_tested_sink(self):
        patch = (HEADER.parent / 'hyprland-output-workspace-logging.patch').read_text()
        embedded = patch.split('+++ b/src/debug/log/DisplayLog.hpp\n', 1)[1].split('--- ', 1)[0]
        lines = embedded.splitlines(keepends=True)[1:]
        self.assertEqual(''.join(line[1:] for line in lines if line.startswith('+')), HEADER.read_text())
