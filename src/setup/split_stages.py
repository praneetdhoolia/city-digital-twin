"""Split a long main() into named stage functions along marker comments,
mechanically: each stage becomes a function taking the names it reads from
the preamble and returning nothing (the shared accumulators are passed in).

    python split_stages.py <file> <func> <stage_name>=<start_line>:<end_line> ...

The stage bodies are moved verbatim (dedented by 4), the call replaces them
in place. Names a stage READS that the preamble ASSIGNED become parameters;
names a stage assigns that a LATER stage reads abort the split (state that
crosses a stage boundary is a design question, not a mechanical one) unless
they are re-assigned in the later stage before use (loop variables).
"""
import ast, sys, re
NL = chr(10)

path, func = sys.argv[1], sys.argv[2]
stages = []
for spec in sys.argv[3:]:
    name, rng = spec.split('=')
    a, b = rng.split(':')
    stages.append((name, int(a), int(b)))
src = open(path, encoding='utf-8').read()
lines = src.split('\n')
tree = ast.parse(src)
fn = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == func][0]


def assigned(nodes):
    out = set()
    for n in nodes:
        for x in ast.walk(n):
            if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store):
                out.add(x.id)
            if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out.add(x.name)
            if isinstance(x, ast.arg):
                out.add(x.arg)
    return out


def used(nodes):
    out = set()
    for n in nodes:
        for x in ast.walk(n):
            if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load):
                out.add(x.id)
    return out


def comprehension_targets(nodes):
    out = set()
    for n in nodes:
        for x in ast.walk(n):
            if isinstance(x, ast.comprehension):
                for t in ast.walk(x.target):
                    if isinstance(t, ast.Name):
                        out.add(t.id)
    return out


def first_use_before_assign(nodes, name):
    """True when `name` is loaded in these nodes before any store of it.
    A comprehension's own target is bound before its body whatever the
    source order says, so it never counts as a use before assignment."""
    if name in comprehension_targets(nodes):
        return False
    events = []
    for n in nodes:
        for x in ast.walk(n):
            if isinstance(x, ast.Name) and x.id == name:
                events.append((x.lineno, x.col_offset, isinstance(x.ctx, ast.Load)))
    events.sort()
    return bool(events) and events[0][2]


body = fn.body
pre_end = stages[0][1]
pre = [n for n in body if n.end_lineno < pre_end]
stage_nodes = [[n for n in body if a <= n.lineno and n.end_lineno <= b] for _, a, b in stages]
for (name, a, b), nodes in zip(stages, stage_nodes):
    assert nodes, 'stage %s has no statements' % name
    assert nodes[0].lineno == a or nodes[0].lineno <= a + 20, (name, nodes[0].lineno, a)

params = []
returns = []
fn_args = {a.arg for a in fn.args.args + fn.args.kwonlyargs}
tail = [n for n in body if n.lineno > stages[-1][2]]
for i, ((name, a, b), nodes) in enumerate(zip(stages, stage_nodes)):
    reads = used(nodes)
    avail = assigned(pre) | fn_args
    for j in range(i):
        avail |= assigned(stage_nodes[j])
    need = sorted(n for n in reads if n in avail and n not in assigned(nodes)
                  or (n in avail and n in assigned(nodes) and first_use_before_assign(nodes, n)))
    # a stage's own assignments that a later stage or the tail reads before
    # assigning are RETURNED by the stage and bound at the call site
    crossing = set()
    later_all = [n for j in range(i + 1, len(stages)) for n in stage_nodes[j]]
    for later in (later_all, tail):
        for n in assigned(nodes):
            if n in used(later) and first_use_before_assign(later, n)                     and n not in assigned(pre) and n not in fn_args:
                crossing.add(n)
    params.append(need)
    returns.append(sorted(crossing))

# build the new source: stage functions inserted before `def func`, bodies replaced by calls
new_funcs = []
replacements = []
for (name, a, b), nodes, need, ret in zip(stages, stage_nodes, params, returns):
    start, end = nodes[0].lineno, nodes[-1].end_lineno
    # include any comment lines immediately above the first statement back to `a`
    while start - 1 >= a and (lines[start - 2].strip().startswith('#') or not lines[start - 2].strip()):
        start -= 1
    block = lines[start - 1:end]
    dedented = block   # the body keeps main()'s indentation inside its own def
    sig = 'def %s(%s):' % (name, ', '.join(need))
    ret_line = ('    return ' + ', '.join(ret) + NL) if ret else ''
    new_funcs.append(sig + NL + NL.join(dedented) + NL + ret_line + NL)
    call = '%s(%s)' % (name, ', '.join(need))
    if ret:
        call = ', '.join(ret) + ' = ' + call
    replacements.append((start, end, '    ' + call))

out = lines[:]
for start, end, call in sorted(replacements, reverse=True):
    out[start - 1:end] = [call]
fn_line = fn.lineno
# the decorator-free def line; insert the stage functions before it (and before its docstring is irrelevant)
insert_at = fn_line - 1
out[insert_at:insert_at] = ['\n'.join(new_funcs)]
open(path, 'w', encoding='utf-8', newline='\n').write('\n'.join(out))
ast.parse('\n'.join(out))
print('split %s.%s into %s; params %s; returns %s' % (path, func, [s[0] for s in stages], params, returns))
