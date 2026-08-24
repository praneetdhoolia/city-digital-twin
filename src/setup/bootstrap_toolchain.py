#!/usr/bin/env python
"""Fetch and pin the model toolchain.

The build and run stack needs things this repository does not carry and cannot
regenerate: a JVM, the pt2matsim converter, and - for explicit corridor
signals (issue #73) - the MATSim signals contrib with its dependency tree.
Everything lands under `.tools/` (gitignored) and every component is pinned by
version **and** by sha256, so a rebuilt toolchain is the same toolchain.

    JDK        Eclipse Temurin 25 - pt2matsim 26.6's pom sets <release>25</release>,
               so a 21 JDK will not load its classes.
    pt2matsim  the published *shaded* jar. It carries MATSim and every transitive
               dependency and declares PublicTransitMapper as its Main-Class, so
               neither Maven nor a build step is required for the DEFAULT run
               stack. It embeds org.matsim:matsim 2027.0-2026w25 (verified from
               its own Maven metadata, DECISIONS.md 9.73).
    maven      Apache Maven, used for ONE job: resolving the signals run stack.
    run stack  org.matsim:matsim + org.matsim.contrib:signals at EXACTLY the
               version the shaded jar embeds, plus their transitive closure,
               copied into `.tools/run-stack/lib`. The signals contrib is not in
               the shaded jar, and a contrib must not share a classpath with it
               (9.73) - so signal-enabled runs use this stack and nothing else
               does. Every resolved jar's sha256 is recorded in toolchain.json.

SUMO was REMOVED from this toolchain on the 9.74 descope (issue #72): MATSim
is the single simulator, and no completed run ever consumed a SUMO artefact.
A stale `.tools/sumo-venv` from an earlier bootstrap is inert and may be
deleted by hand.

Writes `.tools/toolchain.json`: version, source URL, sha256 and retrieval date
for each component - the provenance record for the tools, mirroring what
`data/raw/provenance_*.json` does for the data. Changing any pin is a
toolchain change: re-run, re-hash and record it in DECISIONS.md 14.

Usage:
    python src/setup/bootstrap_toolchain.py            # fetch what is missing
    python src/setup/bootstrap_toolchain.py --verify   # check digests, fetch nothing
    python src/setup/bootstrap_toolchain.py --run-stack  # also build the signals run stack
"""
import os
import sys
import glob
import json
import shutil
import hashlib
import zipfile
import datetime
import argparse
import subprocess
import urllib.request

TOOLS = '.tools'

# ---------------------------------------------------------------------------
# Pins. Changing any of these is a toolchain change: re-run, re-hash and record
# it in DECISIONS.md 14 - a different jar can move a result.
# ---------------------------------------------------------------------------
JDK_VERSION = '25.0.4+7'
JDK_URL = ('https://github.com/adoptium/temurin25-binaries/releases/download/'
           'jdk-25.0.4%2B7/OpenJDK25U-jdk_x64_windows_hotspot_25.0.4_7.zip')
JDK_SHA256 = '7caab7db43bf4b94a2e6252c699e70d90084f9aa7c943cd3414761fd540937ae'
JDK_DIRNAME = 'jdk-25.0.4+7'

PT2MATSIM_VERSION = '26.6'
PT2MATSIM_URL = ('https://repo.matsim.org/repository/matsim/org/matsim/pt2matsim/'
                 '26.6/pt2matsim-26.6-shaded.jar')

MAVEN_VERSION = '3.9.9'
MAVEN_URL = ('https://repo1.maven.org/maven2/org/apache/maven/apache-maven/'
             '%s/apache-maven-%s-bin.zip' % (MAVEN_VERSION, MAVEN_VERSION))
MAVEN_SHA256 = '4ec3f26fb1a692473aea0235c300bd20f0f9fe741947c82c1234cefd76ac3a3c'

# The signals run stack matches the MATSim the shaded jar embeds, EXACTLY:
# 9.73 verified 2027.0-2026w25 from the jar's own pom.properties, and a contrib
# from any other train would put two MATSim versions one classpath apart.
MATSIM_STACK_VERSION = '2027.0-2026w25'

LICENCES = {
    'jdk': 'GPLv2 with Classpath Exception (Eclipse Temurin)',
    'pt2matsim': 'GPL-2.0 (pt2matsim); bundles MATSim, GPL-2.0',
    'maven': 'Apache-2.0 (Apache Maven)',
    'run-stack': 'GPL-2.0 (MATSim, signals contrib) + transitive dependencies, '
                 'each under its own licence',
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def download(url, dest, expect=None):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest) and (expect is None or sha256(dest) == expect):
        print('   cached  %s' % os.path.basename(dest))
        return sha256(dest)
    print('   fetch   %s' % url)
    tmp = dest + '.part'
    with urllib.request.urlopen(url, timeout=300) as r, open(tmp, 'wb') as f:
        shutil.copyfileobj(r, f, 1 << 20)
    got = sha256(tmp)
    if expect and got != expect:
        os.remove(tmp)
        raise SystemExit('digest mismatch for %s\n  expected %s\n  got      %s'
                         % (url, expect, got))
    os.replace(tmp, dest)
    print('   ok      %s  %.1f MB  sha256=%s' % (os.path.basename(dest),
                                                 os.path.getsize(dest) / 1e6, got[:16]))
    return got


def jdk_archive():
    return os.path.join(TOOLS, 'dl', JDK_URL.split('/')[-1])


def install_jdk():
    home = os.path.join(TOOLS, 'jdk')
    digest = download(JDK_URL, jdk_archive(), JDK_SHA256)
    if not java_path():
        print('   unpack  JDK %s' % JDK_VERSION)
        stage = os.path.join(TOOLS, '_jdk_stage')
        shutil.rmtree(stage, ignore_errors=True)
        with zipfile.ZipFile(jdk_archive()) as z:
            z.extractall(stage)
        src = os.path.join(stage, JDK_DIRNAME)
        if not os.path.isdir(src):
            cands = [d for d in sorted(os.listdir(stage))
                     if os.path.isdir(os.path.join(stage, d))]
            src = os.path.join(stage, cands[0])
        shutil.rmtree(home, ignore_errors=True)
        shutil.move(src, home)
        shutil.rmtree(stage, ignore_errors=True)
    return dict(component='jdk', version=JDK_VERSION, url=JDK_URL, sha256=digest,
                home=home.replace('\\', '/'), licence=LICENCES['jdk'])


def install_pt2matsim():
    jar = os.path.join(TOOLS, 'jars', 'pt2matsim-%s-shaded.jar' % PT2MATSIM_VERSION)
    digest = download(PT2MATSIM_URL, jar)
    return dict(component='pt2matsim', version=PT2MATSIM_VERSION, url=PT2MATSIM_URL,
                sha256=digest, jar=jar.replace('\\', '/'), licence=LICENCES['pt2matsim'])


def maven_archive():
    return os.path.join(TOOLS, 'dl', MAVEN_URL.split('/')[-1])


def maven_path():
    for cand in (os.path.join(TOOLS, 'maven', 'bin', 'mvn.cmd'),
                 os.path.join(TOOLS, 'maven', 'bin', 'mvn')):
        if os.path.exists(cand):
            return cand
    return ''


def install_maven():
    home = os.path.join(TOOLS, 'maven')
    digest = download(MAVEN_URL, maven_archive(), MAVEN_SHA256)
    if not maven_path():
        print('   unpack  Maven %s' % MAVEN_VERSION)
        stage = os.path.join(TOOLS, '_maven_stage')
        shutil.rmtree(stage, ignore_errors=True)
        with zipfile.ZipFile(maven_archive()) as z:
            z.extractall(stage)
        cands = [d for d in sorted(os.listdir(stage))
                 if os.path.isdir(os.path.join(stage, d))]
        shutil.rmtree(home, ignore_errors=True)
        shutil.move(os.path.join(stage, cands[0]), home)
        shutil.rmtree(stage, ignore_errors=True)
    return dict(component='maven', version=MAVEN_VERSION, url=MAVEN_URL,
                sha256=digest, home=home.replace('\\', '/'),
                licence=LICENCES['maven'])


RUN_STACK_POM = os.path.join('src', 'java', 'run-stack-pom.xml')
RUN_STACK_LIB = os.path.join(TOOLS, 'run-stack', 'lib')


def run_stack_jars():
    return sorted(glob.glob(os.path.join(RUN_STACK_LIB, '*.jar')))


def build_run_stack():
    """Resolve the signals run stack with the pinned Maven and record it.

    One Maven invocation, one job: copy `org.matsim:matsim` +
    `org.matsim.contrib:signals` at MATSIM_STACK_VERSION and their transitive
    runtime closure into `.tools/run-stack/lib`. Every jar's sha256 goes into
    toolchain.json, so --verify can re-hash the whole stack without touching
    the network. The local Maven repository is kept inside `.tools/` so the
    user's own ~/.m2 is never involved (isolation, and reproducibility from a
    clone).
    """
    mvn = maven_path()
    if not mvn:
        raise SystemExit('maven missing - run without flags first')
    if not os.path.exists(RUN_STACK_POM):
        raise SystemExit('no %s - the run-stack pom is committed; restore it'
                         % RUN_STACK_POM)
    os.makedirs(RUN_STACK_LIB, exist_ok=True)
    env = dict(os.environ)
    env['JAVA_HOME'] = os.path.abspath(os.path.join(TOOLS, 'jdk'))
    repo_local = os.path.abspath(os.path.join(TOOLS, 'run-stack', 'm2'))
    out_dir = os.path.abspath(RUN_STACK_LIB)
    print('   mvn     dependency:copy-dependencies (matsim %s + signals)'
          % MATSIM_STACK_VERSION)
    cmd = [mvn, '-B', '-q', '-f', RUN_STACK_POM,
           '-Dmaven.repo.local=%s' % repo_local,
           '-DoutputDirectory=%s' % out_dir,
           '-DincludeScope=runtime',
           'dependency:copy-dependencies']
    out = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if out.returncode != 0:
        print(out.stdout[-4000:] if out.stdout else '')
        print(out.stderr[-4000:] if out.stderr else '')
        raise SystemExit('maven dependency resolution FAILED')
    jars = run_stack_jars()
    if not jars:
        raise SystemExit('run stack resolved no jars - check %s' % RUN_STACK_POM)
    digest_index = {os.path.basename(j): sha256(j) for j in jars}
    agg = hashlib.sha256()
    for name in sorted(digest_index):
        agg.update(name.encode('utf-8'))
        agg.update(digest_index[name].encode('utf-8'))
    print('   ok      %d jars -> %s  stack sha256=%s'
          % (len(jars), RUN_STACK_LIB, agg.hexdigest()[:16]))
    return dict(component='run-stack', version=MATSIM_STACK_VERSION,
                url='https://repo.matsim.org/repository/matsim/ (via %s)'
                    % RUN_STACK_POM,
                sha256=agg.hexdigest(), lib=RUN_STACK_LIB.replace('\\', '/'),
                jar_count=len(jars), jars=digest_index,
                licence=LICENCES['run-stack'])


JAVA_SRC = os.path.join('src', 'java')
JAVA_SIGNALS_SRC = os.path.join('src', 'java_signals')
CLASSES = os.path.join(TOOLS, 'classes')
CLASSES_SIGNALS = os.path.join(TOOLS, 'classes-signals')


def javac_path():
    for cand in (os.path.join(TOOLS, 'jdk', 'bin', 'javac.exe'),
                 os.path.join(TOOLS, 'jdk', 'bin', 'javac')):
        if os.path.exists(cand):
            return cand
    return None


def compile_java():
    """Compile the project's MATSim entry point against the pinned jar.

    `run_matsim.py` runs `citysim.CitysimControler`, not the stock MATSim
    Controler, because two bindings differ: ride availability (DECISIONS.md 9.11)
    and the ride travel time that issue #28 fixed. The source is committed;
    `.tools/` is not. Until this step existed the classes were built by hand, so
    a fresh checkout had the source, the jar and no way to run - the classpath
    would simply lack the main class. Compiling here, with the pinned javac
    against the pinned jar, is what makes a run reproducible from a clone.
    """
    javac = javac_path()
    jar = pt2matsim_jar()
    if not javac or not jar:
        print('\nskip javac: toolchain incomplete (javac=%s jar=%s)' % (javac, jar))
        return False
    srcs = sorted(glob.glob(os.path.join(JAVA_SRC, '*', '*.java')))
    if not srcs:
        print('\nno java sources under %s' % JAVA_SRC)
        return False
    os.makedirs(CLASSES, exist_ok=True)
    cmd = [javac, '-cp', jar, '-d', CLASSES] + srcs
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        print('\njavac FAILED\n%s' % (out.stderr or out.stdout))
        raise SystemExit(1)
    print('\njavac      %d source(s) -> %s' % (len(srcs), CLASSES))
    for src in srcs:
        print('             %s' % src.replace('\\', '/'))
    return True


def compile_java_signals():
    """Compile the signal-enabled entry point against the RUN STACK.

    `src/java_signals/` holds the classes that import the signals contrib
    (issue #73). They CANNOT compile against the shaded jar - the contrib is
    not in it, and must not share a classpath with it (9.73) - so they compile
    against `.tools/run-stack/lib` together with the base `src/java/` sources,
    into their own class directory. A checkout without the run stack skips
    this quietly: the default (non-signal) harness never needs it.
    """
    javac = javac_path()
    jars = run_stack_jars()
    if not javac or not jars:
        print('skip javac (signals): run stack not built '
              '(python src/setup/bootstrap_toolchain.py --run-stack)')
        return False
    srcs = sorted(glob.glob(os.path.join(JAVA_SRC, '*', '*.java'))
                  + glob.glob(os.path.join(JAVA_SIGNALS_SRC, '*', '*.java')))
    signal_srcs = [s for s in srcs if s.startswith(JAVA_SIGNALS_SRC)]
    if not signal_srcs:
        print('no java sources under %s' % JAVA_SIGNALS_SRC)
        return False
    os.makedirs(CLASSES_SIGNALS, exist_ok=True)
    cp = os.pathsep.join(jars)
    cmd = [javac, '-cp', cp, '-d', CLASSES_SIGNALS] + srcs
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        print('\njavac (signals) FAILED\n%s' % (out.stderr or out.stdout))
        raise SystemExit(1)
    print('javac      %d source(s) -> %s (signals stack)'
          % (len(srcs), CLASSES_SIGNALS))
    return True


def java_path():
    for cand in (os.path.join(TOOLS, 'jdk', 'bin', 'java.exe'),
                 os.path.join(TOOLS, 'jdk', 'bin', 'java')):
        if os.path.exists(cand):
            return cand
    return ''


def pt2matsim_jar():
    p = os.path.join(TOOLS, 'jars', 'pt2matsim-%s-shaded.jar' % PT2MATSIM_VERSION)
    return p if os.path.exists(p) else ''


def load_manifest():
    p = os.path.join(TOOLS, 'toolchain.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None


def require():
    """Return (java, jar) or exit with instructions."""
    j, p = java_path(), pt2matsim_jar()
    if not (j and p):
        raise SystemExit(
            'toolchain incomplete (java=%s pt2matsim=%s)\n'
            'run: python src/setup/bootstrap_toolchain.py' % (bool(j), bool(p)))
    return j, p


def _verify_run_stack(component):
    """Re-hash every recorded run-stack jar; True when all match."""
    recorded = component.get('jars') or {}
    bad = 0
    for name, want in sorted(recorded.items()):
        path = os.path.join(RUN_STACK_LIB, name)
        if not os.path.exists(path):
            print('  MISSING  run-stack %s' % name)
            bad += 1
        elif sha256(path) != want:
            print('  MISMATCH run-stack %s' % name)
            bad += 1
    extra = set(os.path.basename(j) for j in run_stack_jars()) - set(recorded)
    for name in sorted(extra):
        print('  EXTRA    run-stack %s (not in the recorded stack)' % name)
        bad += 1
    print('  %-8s %-9s %d jar(s)' % ('ok' if not bad else 'FAILED',
                                     'run-stack', len(recorded)))
    return bad


def verify():
    man = load_manifest()
    if not man:
        print('no .tools/toolchain.json - run without --verify first')
        return 1
    bad = 0
    has_run_stack = False
    for c in man['components']:
        if c['component'] == 'run-stack':
            has_run_stack = True
            bad += _verify_run_stack(c)
            continue
        target = {'jdk': jdk_archive(),
                  'pt2matsim': c.get('jar'),
                  'maven': maven_archive()}.get(c['component'])
        if not target or not os.path.exists(target):
            print('  MISSING  %-9s %s' % (c['component'], target))
            bad += 1
            continue
        got = sha256(target)
        ok = got == c['sha256']
        print('  %-8s %-9s %s' % ('ok' if ok else 'MISMATCH', c['component'], got[:16]))
        bad += 0 if ok else 1
    # The custom controler is part of the toolchain a run depends on, and its
    # classes live under the gitignored .tools/. Recompiling here keeps --verify
    # an honest statement that this checkout can actually run.
    if not bad:
        compile_java()
        if has_run_stack:
            compile_java_signals()
    print('toolchain %s' % ('OK' if not bad else 'FAILED'))
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--verify', action='store_true',
                    help='check recorded digests, download nothing')
    ap.add_argument('--run-stack', action='store_true',
                    help='also resolve the signals run stack (Maven, one-off '
                         '~300 MB; needed only for signal-enabled runs, #73)')
    a = ap.parse_args()
    if a.verify:
        raise SystemExit(verify())

    os.makedirs(TOOLS, exist_ok=True)
    comps = []
    print('JDK:')
    comps.append(install_jdk())
    print('pt2matsim:')
    comps.append(install_pt2matsim())
    print('Maven:')
    comps.append(install_maven())
    if a.run_stack:
        print('signals run stack:')
        comps.append(build_run_stack())
    else:
        # keep an already-built stack's record rather than dropping it
        prior = load_manifest()
        for c in (prior or {}).get('components', []):
            if c['component'] == 'run-stack' and run_stack_jars():
                comps.append(c)

    man = dict(
        purpose='model toolchain (network build + run stacks)',
        retrieved=datetime.date.today().isoformat(),
        platform=sys.platform,
        components=comps)
    with open(os.path.join(TOOLS, 'toolchain.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(man, f, indent=2)
        f.write('\n')

    compile_java()
    if any(c['component'] == 'run-stack' for c in comps):
        compile_java_signals()

    print('\njava       %s' % java_path())
    print('pt2matsim  %s' % pt2matsim_jar())
    print('maven      %s' % maven_path())
    print('run stack  %s (%d jars)' % (RUN_STACK_LIB, len(run_stack_jars())))
    for cmd in ([java_path(), '-version'],):
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            line = (out.stdout or out.stderr).strip().splitlines()[0]
            print('\n$ %s\n%s' % (' '.join(cmd), line))
        except Exception as e:
            print('could not run %s (%s)' % (cmd[0], e))


if __name__ == '__main__':
    main()
