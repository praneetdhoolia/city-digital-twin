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
import time

# An arm is a JVM in the tens of GB; VS Code's language server sits under
# 1 GB. A classifier for reading a process list, not a model value.
ARM_RSS_KB = 2_000_000

_SYNCHRONIZE = 0x00100000
_WAIT_TIMEOUT = 0x102
_WAIT_OBJECT_0 = 0x0
# OpenProcess's answer for a pid no process holds; every other failure
# (ERROR_ACCESS_DENIED = 5 above all) means a process IS there
_ERROR_INVALID_PARAMETER = 87

ALIVE, DEAD, UNKNOWN = 'alive', 'dead', 'unknown'


def _kernel32():
    import ctypes                                         # noqa: PLC0415
    return ctypes.WinDLL('kernel32', use_last_error=True), ctypes


def pid_state(pid):
    """'alive', 'dead' or 'unknown' for this pid. Never signals it.

    An OpenProcess failure used to read as dead (fifteenth report), and
    `--stop` then recorded `died` - which a warm start accepts - for a
    process that merely refused the handle. Only ERROR_INVALID_PARAMETER
    means no process holds the pid; access denied means one does and says
    nothing more, so it is 'unknown', and no caller may read it as dead.
    """
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return DEAD
    if pid <= 0:
        return DEAD
    if os.name == 'nt':
        try:
            k32, ctypes = _kernel32()
            handle = k32.OpenProcess(_SYNCHRONIZE, 0, pid)
            if not handle:
                err = ctypes.get_last_error()
                return DEAD if err == _ERROR_INVALID_PARAMETER else UNKNOWN
            try:
                # WAIT_TIMEOUT: still running; WAIT_OBJECT_0: signalled (exited)
                rc = k32.WaitForSingleObject(handle, 0)
            finally:
                k32.CloseHandle(handle)
        except (OSError, AttributeError):
            return UNKNOWN
        if rc == _WAIT_TIMEOUT:
            return ALIVE
        return DEAD if rc == _WAIT_OBJECT_0 else UNKNOWN
    try:
        os.kill(pid, 0)
        return ALIVE
    except PermissionError:
        return UNKNOWN          # EPERM: a process exists, owned by another user
    except OSError:
        return DEAD


def pid_alive(pid):
    """Is this pid a live process? Never signals it. UNKNOWN IS NOT DEAD.

    Every caller that asks this acts on a death (reconciles a run, trims its
    directory, closes it out), so a pid the kernel will not describe is
    treated as the live process it may be - the rule `arm_running` states for
    a process list it cannot read (#66).
    """
    return pid_state(pid) != DEAD


def boot_time():
    """The epoch second the host last booted; None when it cannot be told."""
    try:
        if os.name == 'nt':
            import ctypes                                 # noqa: PLC0415
            k32 = ctypes.windll.kernel32
            k32.GetTickCount64.restype = ctypes.c_ulonglong
            return time.time() - k32.GetTickCount64() / 1000.0
        with open('/proc/stat', encoding='ascii') as fh:
            for line in fh:
                if line.startswith('btime '):
                    return float(line.split()[1])
    except (OSError, AttributeError, ValueError):
        pass
    return None


def card_pid_alive(card, key):
    """Is the process a run card records under `key` still THAT process?

    A pid outlives nothing: after a reboot the number is handed to whatever
    starts next. F36's arm 0 died when Windows Update rebooted the host at
    iteration 238 (24 September 2026); its card's pids then named nothing,
    but on another boot they could have named anything - and `run.py --stop`
    runs `taskkill /F /T` on them. A host booted after the card's `started`
    cannot be running any process the card recorded, so every pid on it is
    dead whatever the number now names.
    """
    return card_pid_state(card, key) != DEAD


def card_pid_state(card, key):
    """`pid_state` of the pid a run card records under `key`, reboot-aware."""
    pid = (card or {}).get(key)
    if not pid:
        return DEAD
    try:
        started = time.mktime(time.strptime(card.get('started') or '',
                                            '%Y-%m-%dT%H:%M:%S'))
    except (TypeError, ValueError):
        started = None
    booted = boot_time()
    if started is not None and booted is not None and booted > started:
        return DEAD
    return pid_state(pid)


_REBOOT_KEYS = (
    r'SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired',
    r'SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending')
_UPDATE_UX = r'SOFTWARE\Microsoft\WindowsUpdate\UX\Settings'


def restart_pending():
    """Has the OS staged a restart it will force? None off Windows."""
    if os.name != 'nt':
        return None
    import winreg                                          # noqa: PLC0415
    for key in _REBOOT_KEYS:
        try:
            winreg.CloseKey(winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key))
            return True
        except OSError:
            continue
    return False


def updates_paused_until():
    """The epoch second Windows Update's pause expires; 0 when not paused, None off Windows.

    Windows Update restarted this host at 04:30 on 24 September 2026, half an
    hour after its active hours ended, and killed F36's arm 0 at iteration
    237 of 250; active hours cannot span more than 18 h and an arm runs
    25-42 h, so only a pause covers one.
    """
    if os.name != 'nt':
        return None
    import winreg                                          # noqa: PLC0415
    try:
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _UPDATE_UX)
    except OSError:
        return 0
    ends = []
    try:
        for name in ('PauseUpdatesExpiryTime', 'PauseQualityUpdatesEndTime'):
            try:
                ends.append(winreg.QueryValueEx(k, name)[0])
            except OSError:
                continue
    finally:
        winreg.CloseKey(k)
    import calendar                                        # noqa: PLC0415
    best = 0
    for v in ends:
        # stored as UTC ('2026-10-02T11:28:39Z'); timegm reads it as UTC, where
        # mktime would apply the local daylight-saving rule to it
        try:
            t = calendar.timegm(time.strptime(str(v)[:19], '%Y-%m-%dT%H:%M:%S'))
        except ValueError:
            continue
        best = max(best, t)
    return best


def _cpu_times():
    """(busy, total) CPU seconds-ish counters for the whole host, or None."""
    try:
        import psutil                                      # noqa: PLC0415
        t = psutil.cpu_times()
        total = float(sum(t))
        return total - float(getattr(t, 'idle', 0.0)), total
    except Exception:                                      # noqa: BLE001
        pass
    if os.name != 'nt':
        return None
    try:
        k32, ctypes = _kernel32()
        idle, kern, user = (ctypes.c_ulonglong(), ctypes.c_ulonglong(),
                            ctypes.c_ulonglong())
        if not k32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kern),
                                  ctypes.byref(user)):
            return None
        # kernel time INCLUDES idle time on Windows
        total = float(kern.value + user.value)
        return total - float(idle.value), total
    except Exception:                                      # noqa: BLE001
        return None


def _memory():
    """(free, total) physical memory in bytes, or None."""
    try:
        import psutil                                      # noqa: PLC0415
        vm = psutil.virtual_memory()
        return float(vm.available), float(vm.total)
    except Exception:                                      # noqa: BLE001
        pass
    if os.name != 'nt':
        return None
    try:
        k32, ctypes = _kernel32()

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [('dwLength', ctypes.c_ulong),
                        ('dwMemoryLoad', ctypes.c_ulong),
                        ('ullTotalPhys', ctypes.c_ulonglong),
                        ('ullAvailPhys', ctypes.c_ulonglong),
                        ('ullTotalPageFile', ctypes.c_ulonglong),
                        ('ullAvailPageFile', ctypes.c_ulonglong),
                        ('ullTotalVirtual', ctypes.c_ulonglong),
                        ('ullAvailVirtual', ctypes.c_ulonglong),
                        ('ullAvailExtendedVirtual', ctypes.c_ulonglong)]
        st = MEMORYSTATUSEX()
        st.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if not k32.GlobalMemoryStatusEx(ctypes.byref(st)):
            return None
        return float(st.ullAvailPhys), float(st.ullTotalPhys)
    except Exception:                                      # noqa: BLE001
        return None


def _process_cpu():
    """{pid: (name, cumulative CPU seconds)} for every process; None without psutil.

    The top other process is recorded only where it is cheap: psutil reads
    the whole table in one pass. Without it nothing is spawned for it.
    """
    try:
        import psutil                                      # noqa: PLC0415
    except ImportError:
        return None
    out = {}
    try:
        for p in psutil.process_iter(['pid', 'name', 'cpu_times']):
            t = p.info.get('cpu_times')
            if t is None:
                continue
            out[p.info['pid']] = (p.info.get('name') or '?',
                                  float(t.user + t.system))
    except Exception:                                      # noqa: BLE001
        return None
    return out


def host_load(prev=None, exclude_pids=()):
    """What the host was doing, for a progress write (fifteenth report).

    Returns (doc, sample). `doc` carries the host's CPU busy % over the span
    since `prev` (the `sample` a previous call returned - the digest's own
    interval, so a slow iteration is read against the load across it), free
    and total RAM, and - where psutil makes it cheap - the process other than
    `exclude_pids` (the run's own harness and JVM) that used most CPU over the
    same span. With no `prev` the CPU figure is None: one reading of a
    cumulative counter is not a rate. Instrumentation: never raises.
    """
    cpu = _cpu_times()
    procs_now = _process_cpu()
    # stamped AFTER the process scan, which walks ~370 processes and takes
    # seconds under load: stamped before it, the window was measured short and
    # one sample read blender.exe at 25.13 cores on a 24-core host and the
    # outside-the-run CPU at 110.9 % (aborted_20261008T144829_250it_25pct,
    # 16:25); every figure below is also clamped to what the host can hold
    now = time.time()
    sample = dict(at=now, cpu=cpu, procs=procs_now)
    doc = dict(at=time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(now)),
               cpu_pct=None, other_cpu_pct=None, span_s=None, ram_free_gb=None,
               ram_total_gb=None, top_other_process=None)
    mem = _memory()
    if mem:
        doc['ram_free_gb'] = round(mem[0] / 2 ** 30, 2)
        doc['ram_total_gb'] = round(mem[1] / 2 ** 30, 2)
    if prev and prev.get('cpu') and cpu:
        busy = cpu[0] - prev['cpu'][0]
        total = cpu[1] - prev['cpu'][1]
        if total > 0:
            doc['cpu_pct'] = round(100.0 * max(0.0, busy) / total, 1)
        doc['span_s'] = round(now - prev['at'], 1)
    if prev and prev.get('procs') and procs_now and now > prev['at']:
        skip = {int(p) for p in exclude_pids if p}
        skip.add(os.getpid())
        best = None
        # the CPU OUTSIDE the run: the whole-host figure above includes the
        # run's own JVM, so a 16-thread mobsim on 24 cores reads 70-90 % by
        # itself and a bar on it refuses every real probe (the first launch
        # under 9.220's pricing rule); what prices the host rather than the
        # build is what everything ELSE used over the same span
        other_secs = 0.0
        ncores = os.cpu_count() or 1
        for pid, (name, secs) in procs_now.items():
            if pid in skip or pid == 0 or pid not in prev['procs']:
                continue
            used = secs - prev['procs'][pid][1]
            if used > 0:
                other_secs += used
            if best is None or used > best[2]:
                best = (pid, name, used)
        doc['other_cpu_pct'] = round(min(100.0, 100.0 * other_secs / ((now - prev['at']) * ncores)), 1)
        if best is not None and best[2] > 0:
            # CPU seconds per wall second: 1.0 is one logical core busy
            doc['top_other_process'] = dict(
                pid=best[0], name=best[1],
                cores=round(min(float(os.cpu_count() or 1), best[2] / (now - prev['at'])), 2))
    return doc, sample


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
