"""Process liveness, asked once and answered the same way everywhere.

Two questions the harness asks of the operating system, each of which used
to be answered by its own copy: is this pid alive (`run_matsim`,
`results_store`, `run_failure` - three copies, one with a different return
test), and is a MATSim arm up (`session_gate` inlined the 2 GB classifier
that `bootstrap_toolchain` named). A Windows-handle fix applied to one copy
left the others (eighth project report, 11 September 2026, area 2; the
STRUCTURAL ledger in `check_hardcoding.py` records the inlined-vs-named split
as "the wrong lesson"). Both answers live here and nowhere else.

Neither function signals a process. On Windows `os.kill(pid, 0)` TERMINATES
the process (os.kill there wraps TerminateProcess and the CTRL events), so
liveness is asked of the kernel handle.
"""
import os
import re
import subprocess

# An arm is a JVM in the tens of GB; VS Code's language server sits under
# 1 GB. A classifier for reading a process list, not a model value.
ARM_RSS_KB = 2_000_000

_SYNCHRONIZE = 0x00100000
_WAIT_TIMEOUT = 0x102


def pid_alive(pid):
    """Is this pid a live process? Never signals it."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    if os.name == 'nt':
        import ctypes                                     # noqa: PLC0415
        k32 = ctypes.windll.kernel32
        handle = k32.OpenProcess(_SYNCHRONIZE, 0, pid)
        if not handle:
            return False
        try:
            # WAIT_TIMEOUT means still running; 0 means signalled (exited)
            return k32.WaitForSingleObject(handle, 0) == _WAIT_TIMEOUT
        finally:
            k32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def arm_running(threshold_kb=ARM_RSS_KB, timeout=30):
    """Descriptions of every JVM big enough to be an arm; None when it cannot be told.

    None is NOT "idle": every caller treats unknown as busy, because the one
    time this was got wrong the compile ran under a live arm (#66).
    """
    try:
        if os.name == 'nt':
            out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq java.exe',
                                  '/FO', 'CSV'], capture_output=True,
                                 text=True, timeout=timeout)
            if out.returncode != 0:
                return None
            big = []
            for line in (out.stdout or '').splitlines()[1:]:
                cells = [c.strip('"') for c in line.split('","')]
                if len(cells) >= 5:
                    kb = int(re.sub(r'[^\d]', '', cells[4]) or 0)
                    if kb > threshold_kb:
                        big.append('pid %s (%d MB)' % (cells[1], kb // 1024))
            return big
        out = subprocess.run(['ps', '-eo', 'pid,rss,comm'], capture_output=True,
                             text=True, timeout=timeout)
        if out.returncode != 0:
            return None
        big = []
        for line in (out.stdout or '').splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 3 and 'java' in parts[2] \
                    and int(parts[1]) > threshold_kb:
                big.append('pid %s (%d MB)' % (parts[0], int(parts[1]) // 1024))
        return big
    except Exception:                                          # noqa: BLE001
        return None
