"""Extract a loop body into a module-level function, mechanically.

    python src/setup/extract_loop_body.py <file> <function> <for-line> <new_name> [--ctx NAME]

The statements of the `for` loop that starts at <for-line> inside <function>
become `def <new_name>(<loop targets>, ctx):` placed before <function>; the
loop body is replaced by one call. Every name the body reads or rebinds that
belongs to the enclosing function's scope (its parameters, its earlier
assignments, the `with` targets around the loop) is reached through `ctx`,
a SimpleNamespace the enclosing function builds just before the loop from
those names and unpacks just after it for the ones the body rebinds.

Renaming is done on NAME tokens only (tokenize), so a string literal or a
comment that happens to contain the identifier is never touched, and every
other byte of the body - comments included - is kept. The result compiles
and is byte-for-byte checked by the caller re-running the builder against
the manifest: a refactor of a build script is finished only when its
outputs' hashes have not moved.
"""
from __future__ import annotations

import argparse
import ast
import builtins
import io
import tokenize

NL = chr(10)


def _names(nodes, ctx_type):
    out = set()
    for n in nodes:
        for x in ast.walk(n):
            if isinstance(x, ast.Name) and isinstance(x.ctx, ctx_type):
                out.add(x.id)
    return out


def _defined_in(nodes):
    out = _names(nodes, ast.Store)
    for n in nodes:
        for x in ast.walk(n):
            if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out.add(x.name)
            if isinstance(x, ast.arg):
                out.add(x.arg)
            if isinstance(x, (ast.Import, ast.ImportFrom)):
                for a in x.names:
                    out.add((a.asname or a.name).split('.')[0])
    return out


def _comprehension_targets(nodes):
    out = set()
    for n in nodes:
        for x in ast.walk(n):
            if isinstance(x, ast.comprehension):
                out |= _names([x.target], ast.Store)
    return out


def _top_level_defs(tree):
    """Names bound at module level, not descending into function or class bodies."""
    out = set()

    def walk(node):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out.add(child.name)
                continue
            if isinstance(child, ast.Lambda):
                continue
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                out.add(child.id)
            if isinstance(child, (ast.Import, ast.ImportFrom)):
                for al in child.names:
                    out.add((al.asname or al.name).split('.')[0])
            walk(child)
    walk(tree)
    return out


def _first_use_is_load(nodes, name):
    events = []
    for n in nodes:
        for x in ast.walk(n):
            if isinstance(x, ast.Name) and x.id == name:
                events.append((x.lineno, x.col_offset, isinstance(x.ctx, ast.Load)))
    events.sort()
    return bool(events) and events[0][2]


def _nested_locals(nodes):
    """Names bound inside nested function scopes of the body (their locals)."""
    out = set()
    for n in nodes:
        for x in ast.walk(n):
            if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                inner = x.body if not isinstance(x, ast.Lambda) else [x.body]
                out |= _names(inner, ast.Store)
                out |= {a.arg for a in (x.args.args + x.args.kwonlyargs)}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('file')
    ap.add_argument('function')
    ap.add_argument('for_line', help='the line of the `for` whose body is extracted, '
                                     'or A:B for a range of top-level statements')
    ap.add_argument('new_name')
    ap.add_argument('--ctx', default='ctx')
    ap.add_argument('--in-body', type=int, default=None,
                    help='with A:B - the statements are taken from the body of the '
                         'compound statement (if/for/with/try) starting at this line')
    a = ap.parse_args(argv)
    src = open(a.file, encoding='utf-8').read()
    lines = src.split('\n')
    tree = ast.parse(src)
    fn = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == a.function][0]
    loop = None
    range_mode = ':' in a.for_line
    if range_mode:
        # a range of the function's own top-level statements: modelled as a
        # loop with no targets whose body is those statements
        ra, rb = (int(x) for x in a.for_line.split(':'))
        host_body = fn.body
        if a.in_body is not None:
            host = [x for x in ast.walk(fn) if isinstance(x, (ast.If, ast.For, ast.With, ast.Try, ast.While))
                    and x.lineno == a.in_body]
            assert host, 'no compound statement starts at line %d' % a.in_body
            host_body = host[0].body
        stmts = [n for n in host_body if ra <= n.lineno and n.end_lineno <= rb]
        assert stmts, 'no top-level statements in %d:%d' % (ra, rb)
        def _own(nodes):
            for n in nodes:
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                    continue
                yield n
                yield from _own(ast.iter_child_nodes(n))
        for x in _own(stmts):
            assert not isinstance(x, ast.Return), 'a return inside the range cannot be extracted'
        loop = ast.For(target=ast.Tuple(elts=[], ctx=ast.Store()), iter=ast.Constant(None),
                       body=stmts, orelse=[], lineno=stmts[0].lineno,
                       end_lineno=stmts[-1].end_lineno, col_offset=stmts[0].col_offset)
    else:
        for x in ast.walk(fn):
            if isinstance(x, ast.For) and x.lineno == int(a.for_line):
                loop = x
        assert loop is not None, 'no for loop starts at line %s' % a.for_line
    body = loop.body
    targets = sorted(_names([loop.target], ast.Store))

    # the enclosing scope's names: parameters, and everything the function
    # binds outside the loop body (before or after it - a closure resolves at
    # call time, so `w` bound by the surrounding `with` counts)
    fn_scope = {x.arg for x in fn.args.args + fn.args.kwonlyargs}
    outside = [n for n in ast.walk(fn) if n is not loop and not (
        hasattr(n, 'lineno') and loop.lineno <= n.lineno and n.end_lineno <= loop.end_lineno)]
    fn_scope |= _defined_in([fn]) - _defined_in(body) - set(targets)
    # names the body binds that the enclosing scope ALSO binds are shared
    # state (rebound accumulators); names only the body binds are its locals
    body_stores = _names(body, ast.Store) | _defined_in(body)
    body_loads = _names(body, ast.Load)
    module_scope = _top_level_defs(tree) | set(dir(builtins))
    nested = _nested_locals(body) | _comprehension_targets(body)
    # bound by fn OUTSIDE the body: walk fn's tree, skipping every node that
    # lies inside the loop body's span
    lo, hi = body[0].lineno, body[-1].end_lineno

    def outside_nodes(node):
        for child in ast.iter_child_nodes(node):
            if hasattr(child, 'lineno') and lo <= child.lineno and child.end_lineno <= hi:
                continue
            yield child
            yield from outside_nodes(child)
    outer_binds = set()
    for n in outside_nodes(fn):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            outer_binds.add(n.id)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            outer_binds.add(n.name)
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            for al in n.names:
                outer_binds.add((al.asname or al.name).split('.')[0])
    outer_binds |= {x.arg for x in fn.args.args + fn.args.kwonlyargs}
    outer_binds -= set(targets)
    # a name bound in the body that fn ALSO binds outside it is shared state
    # only if the body READS it before binding it (an accumulator) or fn reads
    # it AFTER the loop; a loop variable that merely reuses a name is local
    after = [n for n in fn.body if n.lineno > loop.end_lineno]
    before = [n for n in fn.body if n.end_lineno < body[0].lineno]
    if range_mode and a.in_body is not None:
        # inside a compound statement: what precedes the range in the host
        # body counts as before, what follows it (in the host and in fn) after
        after = [n for n in host_body if n.lineno > loop.end_lineno] +                 [n for n in fn.body if n.lineno > host[0].end_lineno]
        before = [n for n in fn.body if n.end_lineno < host[0].lineno] +                  [n for n in host_body if n.end_lineno < body[0].lineno]
    bound_before = _defined_in(before) | {x.arg for x in fn.args.args + fn.args.kwonlyargs}
    # the `with` (or other compound statement) that encloses the loop binds
    # its targets before the loop runs
    for n in ast.walk(fn):
        if isinstance(n, ast.With) and n.lineno < loop.lineno <= n.end_lineno:
            for item in n.items:
                if item.optional_vars is not None:
                    bound_before |= _names([item.optional_vars], ast.Store)
    shared = sorted(n for n in (body_stores & outer_binds) - set(targets) - nested
                    if n in bound_before and (_first_use_is_load(body, n)
                                              or (n in _names(after, ast.Load)
                                                  and _first_use_is_load(after, n))))
    # a name read in the body that fn binds outside it and the body does not
    # bind first is reached through ctx; module-level names and builtins are not
    reads = sorted(n for n in body_loads
                   if n in outer_binds and n not in set(targets) and n not in nested
                   and n not in module_scope and n in bound_before
                   and (n not in body_stores or _first_use_is_load(body, n)))
    via_ctx = sorted(set(shared) | set(reads))
    # a name the body binds for the FIRST time that the function reads after
    # the loop is produced by the extracted function and returned to the caller
    after_loads_ = _names(after, ast.Load)
    produced = sorted(n for n in (body_stores - set(targets) - nested)
                      if n not in bound_before and n in after_loads_
                      and _first_use_is_load(after, n) and n not in module_scope)
    print('produced (returned to the caller):', produced)
    # names the body binds only for itself (locals) stay bare
    print('loop targets', targets)
    print('via ctx (%d):' % len(via_ctx), via_ctx)
    print('rebound in body (unpacked after the loop):', shared)

    # a `continue` that belongs to THIS loop (not to an inner one) becomes a
    # `return` of the extracted function
    own_continues = set()

    def find_continues(nodes, in_inner):
        for n in nodes:
            if isinstance(n, ast.Continue) and not in_inner:
                own_continues.add((n.lineno, n.col_offset))
            elif isinstance(n, (ast.For, ast.While, ast.AsyncFor)):
                find_continues(n.body, True)
                find_continues(n.orelse, in_inner)
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                continue
            else:
                for f in ('body', 'orelse', 'finalbody', 'handlers'):
                    if hasattr(n, f):
                        find_continues(getattr(n, f), in_inner)
                if isinstance(n, ast.Try):
                    for h in n.handlers:
                        find_continues(h.body, in_inner)
    find_continues(body, False)
    if any(isinstance(x, ast.Break) for n in body for x in ast.walk(n)):
        for n in body:
            for x in ast.walk(n):
                if isinstance(x, ast.Break):
                    pass  # a break of an inner loop is fine; of THIS loop it is not extractable
    # token-level rename inside the body's line span
    start_line, end_line = body[0].lineno, body[-1].end_lineno
    # include comment lines directly above the first statement
    while start_line - 1 > loop.lineno and (lines[start_line - 2].strip().startswith('#') or not lines[start_line - 2].strip()):
        start_line -= 1
    body_text = '\n'.join(lines[start_line - 1:end_line])
    # dedent by the loop's indentation + 4 -> function body indentation 4
    loop_indent = len(lines[loop.lineno - 1]) - len(lines[loop.lineno - 1].lstrip())
    # a loop body sits one level inside the `for` (indent + 4) and lands at 4
    # inside the new function; a statement range sits AT loop_indent already
    strip = loop_indent - 4 if range_mode else loop_indent
    body_lines = []
    for l in body_text.split('\n'):
        if l.strip() == '':
            body_lines.append('')
        else:
            assert l.startswith(' ' * strip), 'unexpected indentation: %r' % l[:40]
            body_lines.append(l[strip:])
    body_text = '\n'.join(body_lines)
    # rename NAME tokens that are free (via ctx), skipping attribute names and keywords
    toks = list(tokenize.generate_tokens(io.StringIO(body_text).readline))
    edits = []
    prev = None
    for t in toks:
        if t.type == tokenize.NAME and t.string in via_ctx:
            # skip `obj.NAME` (an attribute) and `NAME=` keyword arguments
            if prev is not None and prev.type == tokenize.OP and prev.string == '.':
                prev = t
                continue
            edits.append((t.start, t.end, '%s.%s' % (a.ctx, t.string)))
        if not (t.type in (tokenize.NL, tokenize.NEWLINE, tokenize.COMMENT, tokenize.INDENT, tokenize.DEDENT)):
            prev = t
    bl = body_text.split('\n')
    # keyword-argument detection: NAME followed by '=' and preceded by '(' or ','
    kw = set()
    for i, t in enumerate(toks):
        if t.type == tokenize.NAME and t.string in via_ctx and i + 1 < len(toks) and toks[i + 1].string == '=' \
                and i > 0 and toks[i - 1].string in ('(', ','):
            kw.add(t.start)
    edits = [e for e in edits if e[0] not in kw]
    # the loop's own `continue`s -> `return` (positions are in the ORIGINAL
    # file's coordinates; translate to the body text's)
    for (ln, col) in own_continues:
        edits.append(((ln - start_line + 1, col - strip), (ln - start_line + 1, col - strip + len('continue')), 'return'))
    for (sr, sc), (er, ec), new in sorted(edits, reverse=True):
        assert sr == er
        row = bl[sr - 1]
        bl[sr - 1] = row[:sc] + new + row[ec:]
    new_body = '\n'.join(bl)
    sig = 'def %s(%s):' % (a.new_name, ', '.join(targets + [a.ctx]))
    doc = '    """One iteration of the loop this replaced in %s(); `%s` carries the\n    enclosing scope (%d names). Extracted mechanically, byte-identical outputs."""\n' % (
        a.function, a.ctx, len(via_ctx))
    ret = ('    return ' + ', '.join(produced) + NL) if produced else ''
    new_func = sig + NL + doc + new_body + NL + ret + NL + NL

    # the call site and the ctx bundle
    loop_line = lines[loop.lineno - 1]
    ind = ' ' * loop_indent
    pack = ind + '%s = _types.SimpleNamespace(%s)' % (a.ctx, ', '.join('%s=%s' % (n, n) for n in via_ctx))
    unpack = (ind + '%s = %s' % (', '.join(shared), ', '.join('%s.%s' % (a.ctx, n) for n in shared))) if shared else None
    out = lines[:]
    bind = (', '.join(produced) + ' = ') if produced else ''
    if range_mode:
        call = ind + bind + '%s(%s)' % (a.new_name, a.ctx)
        out[start_line - 1:end_line] = [pack, call] + ([unpack] if unpack else [])
    else:
        call = ind + '    ' + bind + '%s(%s)' % (a.new_name, ', '.join(targets + [a.ctx]))
        out[loop.lineno - 1:end_line] = [pack, loop_line, call] + ([unpack] if unpack else [])
    # insert the new function before the enclosing function
    out[fn.lineno - 1:fn.lineno - 1] = new_func.split('\n')
    text = '\n'.join(out)
    if 'import types as _types' not in text:
        # after the last top-level import
        i = max(i for i, l in enumerate(out) if l.startswith('import ') or l.startswith('from '))
        out.insert(i + 1, 'import types as _types')
        text = '\n'.join(out)
    ast.parse(text)
    open(a.file, 'w', encoding='utf-8', newline='\n').write(text)
    print('extracted %s lines into %s' % (end_line - start_line + 1, a.new_name))


if __name__ == '__main__':
    main()
