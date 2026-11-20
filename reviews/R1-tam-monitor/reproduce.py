#!/usr/bin/env python3
"""Diagnostic reproductions for the accompanying review; no real display writes.

Build commands/tam-monitor with `make check` first. Requires its link-time
fixtures, a C compiler, and pkg-config metadata for libtam-display-session.
Results describe observations; they are not automatic pass/fail verdicts.
Temporary fixtures are compiled outside the checkout and removed on exit.
"""

import argparse
from contextlib import contextmanager
import importlib.util
import json
import os
from pathlib import Path
import pty
import select
import shlex
import signal
import socket
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[2]
CMD = ROOT / "commands/tam-monitor"
PREVIEW = CMD / "build/tam-monitor-preview-fixture"


def run(argv, env=None, timeout=6):
    return subprocess.run([str(x) for x in argv], env=env, text=True,
                          capture_output=True, timeout=timeout)


def result(p):
    return {"exit": p.returncode, "stdout": p.stdout.strip(),
            "stderr": p.stderr.strip()}


def emit(case, **values):
    print(json.dumps({"case": case, **values}, sort_keys=True), flush=True)


@contextmanager
def setup():
    with tempfile.TemporaryDirectory(prefix="tm-review-", dir="/tmp") as tmp:
        directory = Path(tmp)
        log = directory / "actions"
        log.touch()
        env = dict(os.environ)
        # Do not inherit fixture flags or selection overrides from an earlier run.
        for key in list(env):
            if key.startswith("TAM_MONITOR_"):
                del env[key]
        env.update(TAM_MONITOR_RUNTIME_DIR=str(directory),
                   TAM_MONITOR_FIXTURE_LOG=str(log),
                   TAM_MONITOR_FIXTURE_VERBOSE="1")
        shell = directory / "shell.py"
        shell.write_text(f"#!{sys.executable}\nimport time\ntime.sleep(3)\n")
        shell.chmod(0o755)
        env["TAM_MONITOR_SHELL"] = str(shell)
        yield directory, log, env


def actions(log):
    return [line.split()[0] for line in log.read_text().splitlines()]


@contextmanager
def owner(exe, directory, log, env, *args):
    p = subprocess.Popen([str(exe), *args], env=env, text=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        deadline = time.monotonic() + 3
        while not (directory / "vt2.sock").exists():
            if p.poll() is not None:
                raise RuntimeError(f"Supervisor exited before listen: {p.communicate()}")
            if time.monotonic() >= deadline:
                raise TimeoutError("Fixture supervisor did not listen within 3 seconds")
            time.sleep(0.01)
        yield p
    finally:
        if p.poll() is None:
            p.send_signal(signal.SIGCONT)
            p.terminate()
        try:
            p.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            # Only these hardware-free fixture processes may be killed here.
            # The record identifies this owner's recovery child, not a live owner.
            for line in log.read_text().splitlines():
                action, pid = line.split()
                if action == "acquire":
                    try:
                        os.kill(int(pid), signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    break
            p.kill()
            p.communicate(timeout=5)
            raise RuntimeError("Fixture teardown timed out; inspect this case")


def extended_fixture(directory):
    """Keep production objects intact; change only a temporary link-time fixture."""
    source = (CMD / "tests/native-preview-fixture.c").read_text()
    marker = "enum tam_display_result __wrap_tam_display_state_blank"
    at = source.index(marker)
    tail = source[at:]
    old = 'flag("TAM_MONITOR_FIXTURE_COMMIT_FAIL")'
    if old not in tail:
        raise RuntimeError("Baseline fixture changed: adapt R3 injection before running")
    source = source[:at] + tail.replace(old, 'flag("TAM_MONITOR_FIXTURE_BLANK_FAIL")', 1)
    source += r'''
#include "native-hw.h"
int __wrap_tam_monitor_discover(bool probe, struct tam_monitor_info *m,
    size_t max, size_t *n, char *err, size_t cap)
{
    (void)probe; (void)err; (void)cap;
    if (max < 2) return -1;
    memset(m, 0, 2 * sizeof(*m)); *n = 2;
    strcpy(m[0].id, "card1-DP-1"); strcpy(m[0].connector, "DP-1");
    strcpy(m[1].id, "card1-HDMI-A-1"); strcpy(m[1].connector, "HDMI-A-1");
    for (int i = 0; i < 2; ++i) {
        m[i].card = 1; m[i].brightness = -1;
        strcpy(m[i].connection, "connected");
    }
    return 0;
}
'''
    fixture = directory / "fixture.c"
    fixture.write_text(source)
    makefile = (CMD / "Makefile").read_text().splitlines()
    wraps = next(line.split("=", 1)[1].split() for line in makefile
                 if line.startswith("PREVIEW_WRAPS ="))
    wraps.append("tam_monitor_discover")
    sources = next(line.split("=", 1)[1].split() for line in makefile
                   if line.startswith("NATIVE_SRCS ="))
    objects = [CMD / "build" / (Path(name).stem + ".o") for name in sources]
    flags = shlex.split(subprocess.check_output(
        ["pkg-config", "--cflags", "--libs", "libtam-display-session"], text=True))
    exe = directory / "review-fixture"
    subprocess.run([*shlex.split(os.environ.get("CC", "cc")), "-g", f"-I{CMD}",
                    *map(str, objects), str(fixture), *flags, "-lm",
                    *[f"-Wl,--wrap={name}" for name in wraps], "-o", str(exe)],
                   check=True)
    return exe


def r1():
    with setup() as (directory, log, env):
        env["TAM_MONITOR_FIXTURE_MAP_FAIL"] = "1"
        p = run([PREVIEW, "keep", "DP-1", "--card", "1", "--seconds", "1", "--json"], env)
        emit("R1", **result(p), actions=actions(log))


def r2():
    with setup() as (directory, log, env):
        with owner(PREVIEW, directory, log, env, "keep", "DP-1", "--shell"):
            p = run([PREVIEW, "keep", "HDMI-A-1", "--card", "63", "--json"], env)
            emit("R2", **result(p), actions=actions(log))


def r3():
    with setup() as (directory, log, env):
        exe = extended_fixture(directory)
        env["TAM_MONITOR_FIXTURE_BLANK_FAIL"] = "1"
        with owner(exe, directory, log, env, "keep", "DP-1", "--shell") as p:
            # Make the target active before the failing request. Count restoration
            # only after that request, since real WAKE can itself restore baseline.
            wake = run([exe, "wake", "--monitor", "HDMI-A-1", "--json"], env)
            if wake.returncode:
                raise RuntimeError(f"R3 prerequisite wake failed: {result(wake)}")
            before = len(actions(log))
            request = run([exe, "blank", "--monitor", "HDMI-A-1", "--json"], env)
            time.sleep(0.2)
            emit("R3", request=result(request), owner_alive=p.poll() is None,
                 actions_after_request=actions(log)[before:])
            out, err = p.communicate(timeout=5)
            emit("R3-final", exit=p.returncode, stdout=out.strip(), stderr=err.strip(),
                 actions=actions(log))


def r4():
    with setup() as (directory, log, env):
        start = time.monotonic()
        with owner(PREVIEW, directory, log, env,
                   "keep", "DP-1", "--seconds", "1", "--json") as p:
            with socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET) as client:
                client.settimeout(3)
                client.connect(str(directory / "vt2.sock"))
                # Deliberately send nothing. The independent deadline must win.
                out, err = p.communicate(timeout=4)
            emit("R4", elapsed_seconds=round(time.monotonic() - start, 3),
                 exit=p.returncode, stdout=out.strip(), stderr=err.strip())


@contextmanager
def hardware():
    spec = importlib.util.spec_from_file_location("monitor_review_tests", CMD / "tests/test_monitor.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fixture = module.HardwareTests()
    fixture.setUp()
    try:
        fixture.connector()
        yield fixture
    finally:
        fixture.doCleanups()


def r5():
    with hardware() as h:
        helper = h.bin_dir / "tam-brightness-display-ddc"
        helper.write_text("#!/bin/sh\nexec 1>&- 2>&-\nsleep 1.2\n")
        helper.chmod(0o755)
        start = time.monotonic()
        p = h.run_mon("brightness", "DP-1", TAM_MONITOR_FIXTURE_TOOL_TIMEOUT_MS="100")
        emit("R5", elapsed_seconds=round(time.monotonic() - start, 3), **result(p))


def r6():
    with setup() as (directory, log, env):
        exe = extended_fixture(directory)
        with owner(PREVIEW, directory, log, env, "keep", "HDMI-A-1", "--shell"):
            master, slave = pty.openpty()
            tui = None
            try:
                tui = subprocess.Popen([str(exe)], env=env, stdin=slave, stdout=slave, stderr=slave)
                deadline = time.monotonic() + 2
                output = b""
                while b"Ready" not in output:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not select.select([master], [], [], remaining)[0]:
                        raise TimeoutError("TUI did not render Ready")
                    output += os.read(master, 8192)
                os.write(master, b"xxq")
                tui.wait(timeout=3)
                emit("R6", tui_exit=tui.returncode, actions=actions(log))
            finally:
                if tui is not None and tui.poll() is None:
                    tui.terminate()
                    try:
                        tui.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        tui.kill()
                        tui.wait(timeout=2)
                os.close(master)
                os.close(slave)


def r7():
    with hardware() as h:
        for value in ("4294967297", "-4294967295"):
            h.clear_calls()
            p = h.run_mon("brightness", "DP-1", value)
            emit("R7", input=value, **result(p), helper_calls=h.calls())


def r8():
    with setup() as (directory, log, env):
        longdir = directory / ("x" * 100)
        longdir.mkdir(mode=0o700)
        marker = directory / "shell-started"
        Path(env["TAM_MONITOR_SHELL"]).write_text(
            f"#!{sys.executable}\nfrom pathlib import Path\nPath({str(marker)!r}).touch()\n")
        env["TAM_MONITOR_RUNTIME_DIR"] = str(longdir)
        p = run([PREVIEW, "keep", "DP-1", "--shell", "--json"], env)
        emit("R8", **result(p), shell_started=marker.exists(),
             socket_created=(longdir / "vt2.sock").exists(), actions=actions(log))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=[f"R{i}" for i in range(1, 9)])
    args = parser.parse_args()
    for path in (PREVIEW, CMD / "build/tam-monitor-fixture"):
        if not path.is_file():
            parser.error("Run make check in commands/tam-monitor first; fixtures are missing")
    # Python test imports must not leave __pycache__ in the checkout.
    sys.dont_write_bytecode = True
    selected = [int(args.case[1:])] if args.case else range(1, 9)
    for number in selected:
        globals()[f"r{number}"]()


if __name__ == "__main__":
    main()
