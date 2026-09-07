"""The mechanical half of the code redundancy / quality / efficiency pass.

Reads every tracked Python and Java file (`git ls-files`, so results/, .tools/
and caches are never counted) and writes OUT_DIR/code_metrics.json. Nothing
here is a judgement: it is the list of places a reviewer must look, each with
a file and a line, so the report's code findings start from an inventory that
was measured rather than remembered. No third-party package is needed - the
Python side is `ast`, the Java side is regex plus brace matching.

    python .claude/skills/project-report/scripts/collect_code_metrics.py OUT_DIR

What it collects
  per file      lines, code lines, functions, classes, docstring coverage,
                longest function, max cyclomatic complexity, max nesting
  long/complex  every function over LONG_FUNCTION lines or COMPLEX_FUNCTION
                branches, with file:line
  redundancy    duplicated blocks (DUP_WINDOW normalised lines repeated in two
                places), top-level names defined in more than one file,
                top-level definitions referenced nowhere but their own file,
                modules under src/ that nothing imports and that have no main
  efficiency    nested loops three deep, pandas row iteration / concat-in-loop,
                subprocess in a loop, re.compile inside a function body
  determinism   wall-clock reads and unseeded randomness in the build and
                extraction layers (the layers whose output must be regenerable)
  hygiene       unused imports, bare excepts, swallowed exceptions, print in
                library code, sys.path edits, TODO markers, literal mode lists
  java          methods, longest method, unseeded Random, synchronized blocks,
                static mutable fields, System.out, empty catch, listener
                methods present (where per-iteration cost lives)
  tests         test functions, and which src modules a unit test imports

Thresholds are named constants at the top so the report can quote them.
"""
from __future__ import annotations

import ast
import collections
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

LONG_FUNCTION = 150        # lines; the project's own reviewer threshold
COMPLEX_FUNCTION = 15      # branch points
DEEP_NESTING = 5           # nested blocks
DUP_WINDOW = 6             # consecutive normalised lines
DUP_MIN_CHARS = 120        # a window shorter than this is boilerplate, not duplication
BUILD_LAYERS = ("/build/", "/extract/", "src/registry/")   # regenerable-output layers
MODE_NAMES = {"car", "ride", "walk", "bike", "motorbike", "taxi", "bus", "light_rail", "tram",
              "heavy_rail", "rail", "ferry", "truck", "freight_train", "pt"}
WALL_CLOCK = re.compile(r"\b(datetime\.now|datetime\.utcnow|date\.today|time\.time|time\.perf_counter|time\.monotonic)\s*\(")
RANDOM_USE = re.compile(r"\b(random\.(random|randint|choice|choices|shuffle|sample|uniform|gauss)|np\.random\.(rand|randn|randint|choice|shuffle|permutation|uniform|normal))\s*\(")
SEED_CALL = re.compile(r"\b(random\.seed|np\.random\.seed|default_rng|RandomState|Random\()")
SKIP_UNREFERENCED = {"main", "setUp", "tearDown", "__init__"}


def sh(args: list[str]) -> str:
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(args)} -> rc={r.returncode}: {r.stderr[:300]}")
    return r.stdout


def tracked(root: Path, suffix: str) -> list[str]:
    return [f for f in sh(["git", "ls-files"]).split("\n") if f.endswith(suffix)]


# ----------------------------------------------------------------------------- python

class _Visitor(ast.NodeVisitor):
    """Per-function complexity, nesting, and the efficiency markers."""

    BRANCH = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With, ast.AsyncWith,
              ast.ExceptHandler, ast.IfExp, ast.comprehension, ast.BoolOp, ast.Match)
    BLOCK = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With, ast.AsyncWith, ast.FunctionDef,
             ast.AsyncFunctionDef, ast.ClassDef)

    def __init__(self, rel: str):
        self.rel = rel
        self.functions = []          # dict(name, line, end, lines, complexity, nesting, documented)
        self.nested_loops = []       # (line, depth)
        self.pandas_flags = []       # (line, what)
        self.subprocess_in_loop = [] # line
        self.recompile_in_function = []
        self.bare_except = []
        self.swallowed = []
        self._loop_depth = 0
        self._loop_lines = []
        self._in_function = 0

    def _complexity(self, node) -> int:
        n = 1
        for sub in ast.walk(node):
            if isinstance(sub, self.BRANCH):
                n += 1
        return n

    def _nesting(self, node, depth=0) -> int:
        best = depth
        for child in ast.iter_child_nodes(node):
            d = depth + 1 if isinstance(child, self.BLOCK) else depth
            best = max(best, self._nesting(child, d))
        return best

    def visit_FunctionDef(self, node):
        end = getattr(node, "end_lineno", node.lineno)
        self.functions.append(dict(name=node.name, line=node.lineno, lines=end - node.lineno + 1,
                                   complexity=self._complexity(node), nesting=self._nesting(node),
                                   documented=ast.get_docstring(node) is not None))
        self._in_function += 1
        self.generic_visit(node)
        self._in_function -= 1

    visit_AsyncFunctionDef = visit_FunctionDef

    def _loop(self, node):
        self._loop_depth += 1
        if self._loop_depth >= 3:
            self.nested_loops.append((node.lineno, self._loop_depth))
        self.generic_visit(node)
        self._loop_depth -= 1

    visit_For = visit_AsyncFor = visit_While = _loop

    def visit_Call(self, node):
        name = _call_name(node)
        if name.endswith(".iterrows") or name.endswith(".itertuples"):
            self.pandas_flags.append((node.lineno, name.split(".")[-1]))
        elif name.endswith(".append") and self._loop_depth and _looks_like_dataframe(node):
            self.pandas_flags.append((node.lineno, "DataFrame.append in loop"))
        elif name in ("pd.concat", "pandas.concat") and self._loop_depth:
            self.pandas_flags.append((node.lineno, "concat in loop"))
        elif name.endswith(".apply") and any(isinstance(a, ast.Lambda) for a in node.args):
            self.pandas_flags.append((node.lineno, "apply(lambda)"))
        elif name.startswith("subprocess.") and self._loop_depth:
            self.subprocess_in_loop.append(node.lineno)
        elif name == "re.compile" and self._in_function:
            self.recompile_in_function.append(node.lineno)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        if node.type is None:
            self.bare_except.append(node.lineno)
        body = node.body
        if len(body) == 1 and isinstance(body[0], (ast.Pass, ast.Continue)):
            self.swallowed.append(node.lineno)
        self.generic_visit(node)


def _call_name(node: ast.Call) -> str:
    f = node.func
    parts = []
    while isinstance(f, ast.Attribute):
        parts.append(f.attr)
        f = f.value
    if isinstance(f, ast.Name):
        parts.append(f.id)
    return ".".join(reversed(parts))


def _looks_like_dataframe(node: ast.Call) -> bool:
    f = node.func
    return isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and re.search(r"df|frame|table", f.value.id, re.I) is not None


def _unused_imports(tree: ast.AST, text: str) -> list[tuple[int, str]]:
    imported = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                imported[(a.asname or a.name).split(".")[0]] = node.lineno
        elif isinstance(node, ast.ImportFrom):
            if node.module == "__future__":
                continue
            for a in node.names:
                if a.name != "*":
                    imported[a.asname or a.name] = node.lineno
    used = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used.add(node.id)
        elif isinstance(node, ast.Attribute):
            base = node
            while isinstance(base, ast.Attribute):
                base = base.value
            if isinstance(base, ast.Name):
                used.add(base.id)
    exported = set(re.findall(r"__all__\s*=\s*\[([^\]]*)\]", text))
    out = []
    for name, line in imported.items():
        if name in used or any(name in e for e in exported):
            continue
        # a name used only inside a string (doctest, __all__, typing comment) still counts as referenced
        if re.search(r"\b%s\b" % re.escape(name), text.replace(text.splitlines()[line - 1], "", 1)):
            continue
        out.append((line, name))
    return out


def _normalise(line: str) -> str:
    s = line.strip()
    if not s or s.startswith("#"):
        return ""
    s = re.sub(r"#.*$", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def python_pass(root: Path, files: list[str]) -> dict:
    per_file = []
    long_functions, complex_functions, deep_functions = [], [], []
    unused_imports, bare_excepts, swallowed, prints, syspath, todos = [], [], [], [], [], []
    nested_loops, pandas_flags, subprocess_in_loop, recompile = [], [], [], []
    wall_clock, unseeded_random, mode_lists = [], [], []
    windows = collections.defaultdict(list)     # hash -> [(file, line)]
    top_defs = collections.defaultdict(list)    # name -> [file]
    def_sites = {}                              # (file, name) -> line
    tokens_by_file = {}
    imports_by_file = {}
    mains = set()
    for rel in files:
        p = root / rel
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(text)
        except (OSError, SyntaxError) as e:
            per_file.append(dict(file=rel, error=str(e)[:120]))
            continue
        lines = text.splitlines()
        code_lines = sum(1 for l in lines if _normalise(l))
        v = _Visitor(rel)
        v.visit(tree)
        classes = sum(isinstance(n, ast.ClassDef) for n in ast.walk(tree))
        documented = sum(f["documented"] for f in v.functions)
        longest = max(v.functions, key=lambda f: f["lines"], default=None)
        per_file.append(dict(
            file=rel, lines=len(lines), code_lines=code_lines, functions=len(v.functions), classes=classes,
            docstring_coverage=round(documented / len(v.functions), 2) if v.functions else None,
            module_docstring=ast.get_docstring(tree) is not None,
            longest_function=(longest["name"], longest["lines"], longest["line"]) if longest else None,
            max_complexity=max((f["complexity"] for f in v.functions), default=0),
            max_nesting=max((f["nesting"] for f in v.functions), default=0),
        ))
        for f in v.functions:
            if f["lines"] > LONG_FUNCTION:
                long_functions.append(dict(file=rel, line=f["line"], name=f["name"], lines=f["lines"]))
            if f["complexity"] > COMPLEX_FUNCTION:
                complex_functions.append(dict(file=rel, line=f["line"], name=f["name"], complexity=f["complexity"]))
            if f["nesting"] > DEEP_NESTING:
                deep_functions.append(dict(file=rel, line=f["line"], name=f["name"], nesting=f["nesting"]))
        unused_imports += [dict(file=rel, line=l, name=n) for l, n in _unused_imports(tree, text)]
        bare_excepts += [dict(file=rel, line=l) for l in v.bare_except]
        swallowed += [dict(file=rel, line=l) for l in v.swallowed]
        nested_loops += [dict(file=rel, line=l, depth=d) for l, d in v.nested_loops]
        pandas_flags += [dict(file=rel, line=l, what=w) for l, w in v.pandas_flags]
        subprocess_in_loop += [dict(file=rel, line=l) for l in v.subprocess_in_loop]
        recompile += [dict(file=rel, line=l) for l in v.recompile_in_function]
        is_script = "__name__" in text and "__main__" in text
        if is_script:
            mains.add(rel)
        in_build = any(k in "/" + rel for k in BUILD_LAYERS)
        has_seed = SEED_CALL.search(text) is not None
        for i, l in enumerate(lines, 1):
            s = l.strip()
            if re.match(r"print\s*\(", s) and not is_script and not rel.startswith("tests/"):
                prints.append(dict(file=rel, line=i))
            if "sys.path.insert" in s or "sys.path.append" in s:
                syspath.append(dict(file=rel, line=i))
            if re.search(r"\b(TODO|FIXME|XXX|HACK)\b", s):
                todos.append(dict(file=rel, line=i, text=s[:100]))
            if in_build and WALL_CLOCK.search(s):
                wall_clock.append(dict(file=rel, line=i, text=s[:100]))
            if in_build and RANDOM_USE.search(s) and not has_seed:
                unseeded_random.append(dict(file=rel, line=i, text=s[:100]))
            found = set(re.findall(r"['\"](%s)['\"]" % "|".join(sorted(MODE_NAMES)), s))
            if len(found) >= 3 and rel.startswith("src/"):
                mode_lists.append(dict(file=rel, line=i, modes=sorted(found)))
        # duplicated blocks
        norm = [(i + 1, _normalise(l)) for i, l in enumerate(lines)]
        norm = [(i, s) for i, s in norm if s]
        for k in range(len(norm) - DUP_WINDOW + 1):
            block = norm[k:k + DUP_WINDOW]
            joined = "\n".join(s for _, s in block)
            if len(joined) < DUP_MIN_CHARS or joined.count("import ") >= 3:
                continue
            windows[hashlib.sha1(joined.encode()).hexdigest()[:16]].append((rel, block[0][0]))
        # top-level names, references, imports
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                top_defs[node.name].append(rel)
                def_sites[(rel, node.name)] = node.lineno
        tokens_by_file[rel] = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text))
        mods = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods.add(node.module.split(".")[0])
        imports_by_file[rel] = mods

    # duplicated blocks -> pairs of files, counted once per distinct window
    pair_counts = collections.Counter()
    examples = {}
    for h, sites in windows.items():
        distinct = sorted(set(sites))
        if len(distinct) < 2:
            continue
        for a in range(len(distinct)):
            for b in range(a + 1, len(distinct)):
                key = (distinct[a][0], distinct[b][0])
                pair_counts[key] += 1
                examples.setdefault(key, (distinct[a], distinct[b]))
    duplicates = [dict(files=list(k), windows=n, example=[f"{examples[k][0][0]}:{examples[k][0][1]}", f"{examples[k][1][0]}:{examples[k][1][1]}"])
                  for k, n in pair_counts.most_common(60)]
    within_file = sum(1 for h, sites in windows.items() if len(set(sites)) >= 2 and len({s[0] for s in sites}) == 1)

    # same-named top-level definitions in more than one file
    same_name = [dict(name=n, files=sorted(set(fs))) for n, fs in top_defs.items()
                 if len(set(fs)) > 1 and not n.startswith("_") and n not in SKIP_UNREFERENCED and not n.startswith("test_")]
    same_name.sort(key=lambda d: -len(d["files"]))

    # top-level definitions no other file mentions: dead if their own file never uses them either,
    # module-local otherwise (a public name that could be private, or a helper duplicated elsewhere)
    unreferenced, module_local = [], 0
    for (rel, name), line in def_sites.items():
        if name.startswith("_") or name in SKIP_UNREFERENCED or name.startswith("test_") or rel.startswith("tests/"):
            continue
        if not any(name in toks for f, toks in tokens_by_file.items() if f != rel):
            self_uses = len(re.findall(r"\b%s\b" % re.escape(name), (root / rel).read_text(encoding="utf-8", errors="ignore"))) - 1
            if self_uses == 0:
                unreferenced.append(dict(file=rel, line=line, name=name))
            else:
                module_local += 1
    unreferenced.sort(key=lambda d: d["file"])

    # modules under src/ that no file imports and that have no main
    module_names = {Path(f).stem: f for f in files if f.startswith("src/")}
    imported_anywhere = set().union(*imports_by_file.values()) if imports_by_file else set()
    dead_modules = sorted(f for stem, f in module_names.items() if stem not in imported_anywhere and f not in mains and stem != "__init__")

    fn_total = sum(f.get("functions", 0) for f in per_file)
    return dict(
        thresholds=dict(long_function_lines=LONG_FUNCTION, complex_function_branches=COMPLEX_FUNCTION,
                        deep_nesting=DEEP_NESTING, duplicate_window_lines=DUP_WINDOW),
        summary=dict(files=len(files), lines=sum(f.get("lines", 0) for f in per_file),
                     code_lines=sum(f.get("code_lines", 0) for f in per_file), functions=fn_total,
                     classes=sum(f.get("classes", 0) for f in per_file),
                     modules_with_docstring=sum(1 for f in per_file if f.get("module_docstring")),
                     long_functions=len(long_functions), complex_functions=len(complex_functions),
                     deep_functions=len(deep_functions), unused_imports=len(unused_imports),
                     bare_excepts=len(bare_excepts), swallowed_exceptions=len(swallowed),
                     duplicate_file_pairs=len(duplicates), duplicate_windows_within_a_file=within_file,
                     same_name_definitions=len(same_name), unreferenced_definitions=len(unreferenced),
                     module_local_public_definitions=module_local,
                     dead_modules=len(dead_modules), nested_loops_3deep=len(nested_loops),
                     pandas_flags=len(pandas_flags), wall_clock_in_build_layers=len(wall_clock),
                     unseeded_random_in_build_layers=len(unseeded_random), literal_mode_lists=len(mode_lists),
                     todo_markers=len(todos), sys_path_edits=len(syspath), prints_in_library_code=len(prints)),
        files=sorted(per_file, key=lambda f: -f.get("lines", 0)),
        long_functions=sorted(long_functions, key=lambda d: -d["lines"]),
        complex_functions=sorted(complex_functions, key=lambda d: -d["complexity"]),
        deep_functions=sorted(deep_functions, key=lambda d: -d["nesting"]),
        duplicate_blocks=duplicates, same_name_definitions=same_name[:80], unreferenced_definitions=unreferenced[:150],
        dead_modules=dead_modules, nested_loops=nested_loops, pandas_flags=pandas_flags,
        subprocess_in_loop=subprocess_in_loop, re_compile_in_function=recompile,
        wall_clock_in_build_layers=wall_clock, unseeded_random_in_build_layers=unseeded_random,
        literal_mode_lists=mode_lists, unused_imports=unused_imports, bare_excepts=bare_excepts,
        swallowed_exceptions=swallowed, prints_in_library_code=prints[:100], sys_path_edits=syspath, todo_markers=todos,
    )


# ----------------------------------------------------------------------------- java

JAVA_METHOD = re.compile(r"^\s*(?:public|private|protected|static|final|synchronized|abstract|default|\s)*[\w<>\[\],\s?]+\s+(\w+)\s*\([^;{)]*\)\s*(?:throws [\w.,\s]+)?\s*\{", re.M)
LISTENER_METHODS = ("notifyIterationStarts", "notifyIterationEnds", "notifyBeforeMobsim", "notifyAfterMobsim",
                    "notifyReplanning", "notifyScoring", "notifyStartup", "notifyShutdown", "handleEvent", "reset",
                    "doSimStep", "onPrepareSim", "afterSim")


def _method_length(text: str, start: int) -> int:
    depth = 0
    i = text.index("{", start)
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text.count("\n", start, j) + 1
    return text.count("\n", start) + 1


def java_pass(root: Path, files: list[str]) -> dict:
    per_file, long_methods, flags = [], [], collections.defaultdict(list)
    for rel in files:
        text = (root / rel).read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()
        methods = []
        for m in JAVA_METHOD.finditer(text):
            name = m.group(1)
            if name in ("if", "for", "while", "switch", "catch", "synchronized", "return", "new", "else", "try"):
                continue
            line = text.count("\n", 0, m.start()) + 1
            length = _method_length(text, m.start())
            methods.append((name, line, length))
            if length > LONG_FUNCTION:
                long_methods.append(dict(file=rel, line=line, name=name, lines=length))
        listeners = sorted({n for n, _, _ in methods if n in LISTENER_METHODS})
        for i, l in enumerate(lines, 1):
            s = l.strip()
            if "new Random(" in s:
                flags["unseeded_random" if re.search(r"new Random\(\s*\)", s) else "seeded_random"].append(f"{rel}:{i}")
            if re.search(r"\bsynchronized\b", s):
                flags["synchronized"].append(f"{rel}:{i}")
            if re.search(r"\bstatic\b(?!.*\bfinal\b).*\b(Map|List|Set|HashMap|ArrayList|HashSet|\[\])\b.*[;=]", s) and "(" not in s.split("=")[0]:
                flags["static_mutable_field"].append(f"{rel}:{i}")
            if "System.out." in s or "System.err." in s:
                flags["system_out"].append(f"{rel}:{i}")
            if "printStackTrace" in s:
                flags["print_stack_trace"].append(f"{rel}:{i}")
            if re.search(r"catch\s*\([^)]*\)\s*\{\s*\}", s):
                flags["empty_catch"].append(f"{rel}:{i}")
            if re.search(r"\b(TODO|FIXME|XXX|HACK)\b", s):
                flags["todo"].append(f"{rel}:{i}")
            if re.search(r"Id\.create(Person|Link|Vehicle|Node)?Id\(.*\+", s):
                flags["id_string_concat"].append(f"{rel}:{i}")
            if re.search(r"\.split\(|String\.format\(|\+ \"", s) and any(k in text[max(0, text.find(l) - 800):text.find(l)] for k in ("handleEvent", "doSimStep")):
                flags["string_work_near_event_handler"].append(f"{rel}:{i}")
        per_file.append(dict(file=rel, lines=len(lines), methods=len(methods),
                             longest_method=max(methods, key=lambda m: m[2], default=None), listeners=listeners,
                             injects=text.count("@Inject"), event_handler=("EventHandler" in text or "handleEvent(" in text)))
    return dict(summary=dict(files=len(files), lines=sum(f["lines"] for f in per_file), methods=sum(f["methods"] for f in per_file),
                             long_methods=len(long_methods), **{k: len(v) for k, v in flags.items()}),
                files=sorted(per_file, key=lambda f: -f["lines"]), long_methods=sorted(long_methods, key=lambda d: -d["lines"]),
                flags={k: v[:80] for k, v in flags.items()})


# ----------------------------------------------------------------------------- tests

def tests_pass(root: Path, py_files: list[str]) -> dict:
    test_files = [f for f in py_files if f.startswith("tests/")]
    src_stems = {Path(f).stem for f in py_files if f.startswith("src/")}
    covered = collections.defaultdict(list)
    n_tests = 0
    for rel in test_files:
        text = (root / rel).read_text(encoding="utf-8", errors="ignore")
        n_tests += len(re.findall(r"^\s*def test_", text, re.M))
        for m in re.finditer(r"^\s*(?:from|import)\s+([\w.]+)", text, re.M):
            stem = m.group(1).split(".")[-1]
            if stem in src_stems:
                covered[stem].append(rel)
    return dict(test_files=len(test_files), test_functions=n_tests,
                src_modules=len(src_stems), src_modules_imported_by_a_test=len(covered),
                uncovered_src_modules=sorted(src_stems - set(covered)), covered=dict(covered))


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    out_dir = Path(argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    root = Path(sh(["git", "rev-parse", "--show-toplevel"]).strip())
    os.chdir(root)
    py = tracked(root, ".py")
    java = tracked(root, ".java")
    print(f"python: {len(py)} files, java: {len(java)} files", flush=True)
    m = dict(head=sh(["git", "rev-parse", "--short", "HEAD"]).strip(), python=python_pass(root, py),
             java=java_pass(root, java), tests=tests_pass(root, py))
    (out_dir / "code_metrics.json").write_text(json.dumps(m, indent=1, default=str), encoding="utf-8")
    s = m["python"]["summary"]
    print(f"wrote {out_dir / 'code_metrics.json'}: {s['lines']} py lines, {s['long_functions']} long functions, "
          f"{s['duplicate_file_pairs']} duplicate pairs, {s['unreferenced_definitions']} unreferenced defs, "
          f"{m['java']['summary']['lines']} java lines")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
