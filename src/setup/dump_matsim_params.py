"""Write down every parameter the pinned MATSim exposes, and its default.

`config/schema/matsim_defaults.json` is that dump. It exists because a
DECLARED value can be silently voided by an UNDECLARED one:
`RUN.travel_time.analysed_modes` was declared `["car"]`, swept, rendered into
the reference and proven to reach the config - and meant nothing, because
`travelTimeCalculator.filterModes` was never emitted and its framework default
of `false` tells MATSim to ignore `analyzedModes` altogether. Every check this
repository had asks whether a declared field reaches the model. None could ask
what an UNDECLARED parameter was deciding beside it.

This dump is the other half. `src/registry/check_matsim_defaults.py` reads it
and reports, for every config group the model writes into, the parameters it
does NOT set - each one a value the framework is choosing.

It needs the toolchain (`.tools/jdk`, `.tools/run-stack/lib`), so it is a
generation step like the toolchain itself, not a CI check: the dump is
committed and CI reads the committed file. The MATSim version is recorded in
it, so a toolchain change - which is a model change (CLAUDE.md) - shows up as
a dump that no longer matches.

    python src/setup/dump_matsim_params.py            # rewrite the dump
    python src/setup/dump_matsim_params.py --check    # is it current?
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(REPO, '.tools')
OUT = os.path.join(REPO, 'config', 'schema', 'matsim_defaults.json')

JAVA_SRC = r'''
import java.util.Map;
import java.util.TreeMap;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigGroup;
import org.matsim.core.config.ConfigUtils;

/** Prints every group's parameters and their defaults as JSON. */
public final class DumpMatsimParams {
    public static void main(final String[] args) {
        final Config config = ConfigUtils.createConfig();
        final Map<String, ConfigGroup> modules =
                new TreeMap<>(config.getModules());
        final StringBuilder out = new StringBuilder("{\n");
        boolean firstGroup = true;
        for (final Map.Entry<String, ConfigGroup> e : modules.entrySet()) {
            Map<String, String> params;
            try {
                params = new TreeMap<>(e.getValue().getParams());
            } catch (final RuntimeException ex) {
                // a group that refuses to render its own defaults says so
                params = new TreeMap<>();
                params.put("__unrenderable__", ex.getClass().getSimpleName());
            }
            if (!firstGroup) {
                out.append(",\n");
            }
            firstGroup = false;
            out.append("  ").append(quote(e.getKey())).append(": {\n");
            boolean firstParam = true;
            for (final Map.Entry<String, String> p : params.entrySet()) {
                if (!firstParam) {
                    out.append(",\n");
                }
                firstParam = false;
                out.append("    ").append(quote(p.getKey())).append(": ")
                   .append(quote(p.getValue()));
            }
            out.append(firstParam ? "" : "\n").append("  }");
        }
        out.append("\n}\n");
        System.out.println("---BEGIN-JSON---");
        System.out.println(out);
    }

    private static String quote(final String s) {
        if (s == null) {
            return "null";
        }
        final StringBuilder b = new StringBuilder("\"");
        for (int i = 0; i < s.length(); i++) {
            final char c = s.charAt(i);
            switch (c) {
                case '"': b.append("\\\""); break;
                case '\\': b.append("\\\\"); break;
                case '\n': b.append("\\n"); break;
                case '\r': b.append("\\r"); break;
                case '\t': b.append("\\t"); break;
                default:
                    if (c < 0x20) {
                        b.append(String.format("\\u%04x", (int) c));
                    } else {
                        b.append(c);
                    }
            }
        }
        return b.append('"').toString();
    }
}
'''


def _tool(name: str) -> str:
    for ext in ('.exe', ''):
        cand = os.path.join(TOOLS, 'jdk', 'bin', name + ext)
        if os.path.exists(cand):
            return cand
    return name


def _classpath() -> str:
    jars = sorted(glob.glob(os.path.join(TOOLS, 'run-stack', 'lib', '*.jar')))
    if not jars:
        raise SystemExit(
            'the run stack is not built: no jars under .tools/run-stack/lib.\n'
            'Run: python src/setup/bootstrap_toolchain.py --run-stack')
    return os.pathsep.join(jars)


def _matsim_version() -> str:
    path = os.path.join(TOOLS, 'toolchain.json')
    try:
        with open(path, encoding='utf-8') as fh:
            doc = json.load(fh)
    except (OSError, ValueError):
        return 'unknown'
    for c in doc.get('components', []):
        if c.get('component') == 'run-stack':
            return str(c.get('version') or 'unknown')
    return 'unknown'


def dump() -> dict:
    """Run the dumper against the pinned jars and return the parsed groups."""
    cp = _classpath()
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, 'DumpMatsimParams.java')
        with open(src, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(JAVA_SRC)
        rc = subprocess.run([_tool('javac'), '-cp', cp, '-d', tmp, src],
                            capture_output=True, text=True)
        if rc.returncode != 0:
            raise SystemExit('javac failed:\n%s' % (rc.stderr or rc.stdout))
        rc = subprocess.run([_tool('java'), '-cp', tmp + os.pathsep + cp,
                             'DumpMatsimParams'],
                            capture_output=True, text=True)
        if rc.returncode != 0:
            raise SystemExit('java failed:\n%s' % (rc.stderr or rc.stdout))
    body = rc.stdout.split('---BEGIN-JSON---', 1)
    if len(body) != 2:
        raise SystemExit('the dumper printed no JSON:\n%s' % rc.stdout[-2000:])
    return json.loads(body[1])


def build_document() -> dict:
    return {
        'purpose': ('every parameter the pinned MATSim exposes, with the '
                    'default it takes when nothing sets it. Generated by '
                    'src/setup/dump_matsim_params.py; read by '
                    'src/registry/check_matsim_defaults.py. A parameter here '
                    'that the model does not emit is a value the FRAMEWORK is '
                    'deciding.'),
        'matsim_version': _matsim_version(),
        'groups': dump(),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--check', action='store_true',
                    help='fail if the committed dump is not what the pinned '
                         'toolchain produces')
    args = ap.parse_args(argv)

    doc = build_document()
    text = json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + '\n'

    if args.check:
        try:
            with open(OUT, encoding='utf-8') as fh:
                current = fh.read()
        except OSError:
            print('MISSING %s - run without --check to write it'
                  % os.path.relpath(OUT, REPO))
            return 1
        if current.replace('\r\n', '\n') != text:
            print('STALE %s - the pinned toolchain produces a different '
                  'parameter surface.\nA toolchain change is a model change: '
                  'regenerate it and record the change.'
                  % os.path.relpath(OUT, REPO))
            return 1
        groups = doc['groups']
        print('matsim defaults current: %d group(s), %d parameter(s), '
              'MATSim %s' % (len(groups), sum(len(v) for v in groups.values()),
                             doc['matsim_version']))
        return 0

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)
    groups = doc['groups']
    print('wrote %s - %d group(s), %d parameter(s), MATSim %s'
          % (os.path.relpath(OUT, REPO), len(groups),
             sum(len(v) for v in groups.values()), doc['matsim_version']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
