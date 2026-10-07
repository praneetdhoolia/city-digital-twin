"""Split a long main() into named stage functions along marker comments,
mechanically: each stage becomes a function taking the names it reads from
the preamble and returning what a later stage reads back.

    python split_stages.py <file> <func> <stage_name>=<start_line>:<end_line> ...

The stage bodies are moved verbatim (dedented by 4), the call replaces them
in place. Names a stage READS before binding them, that the preamble or an
earlier stage bound, become its parameters; names a stage binds that a LATER
stage or the tail reads before binding them are returned by the stage and
bound at the call site, so state crosses a stage boundary in the open.

The analysis is of names in the function's own scope, in evaluation order.
Splitting the Mumbai builders (8 October 2026) met three ways a textual walk
of the tree got that wrong, each a NameError or an UnboundLocalError in the
split output and corrected by hand: `persons = persons.sort_values(...)` was
read as a binding before a read because the target sits left of the value;
`from x import y` bound nothing, so a stage reading `y` got no parameter; and
the arguments of a lambda and the targets of a comprehension were taken for
the function's own names, so a preamble's loop variable `r` leaked into a
stage's parameters and returns through a later `key=lambda r: ...`. `events`
below yields (name, is_load) in the order the interpreter meets them and
keeps a nested scope's bindings inside it: only what a lambda, a def, a class
body or a comprehension reads FROM the function reaches the function's list.
"""
import ast, sys, re
NL = chr(10)


def events(nodes):
    """(name, is_load) for every name these statements read or bind in the
    enclosing function's scope, in evaluation order."""
    out = []
    for n in nodes:
        _walk(n, out)
    return out


def assigned(ev):
    return {n for n, load in ev if not load}


def used(ev):
    return {n for n, load in ev if load}


def first_use_before_assign(ev, name):
    """True when `name` is read before it is bound: the value read is the one
    the function held when these statements began."""
    for n, load in ev:
        if n == name:
            return load
    return False


_COMPREHENSIONS = (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)
_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)
_MATCH_BINDERS = tuple(getattr(ast, k) for k in ('MatchAs', 'MatchStar', 'MatchMapping')
                       if hasattr(ast, k))


def _walk(node, out):
    if isinstance(node, ast.Name):
        if isinstance(node.ctx, ast.Load):
            out.append((node.id, True))
        elif isinstance(node.ctx, ast.Store):
            out.append((node.id, False))
    elif isinstance(node, ast.Assign):
        _walk(node.value, out)                   # the value first, then the targets
        for t in node.targets:
            _walk(t, out)
    elif isinstance(node, ast.AugAssign):
        _walk(node.value, out)
        if isinstance(node.target, ast.Name):
            out.append((node.target.id, True))   # `x += 1` reads x before binding it
        _walk(node.target, out)
    elif isinstance(node, ast.AnnAssign):
        if node.value is not None:
            _walk(node.value, out)
        _walk(node.target, out)
    elif isinstance(node, ast.NamedExpr):
        _walk(node.value, out)
        _walk(node.target, out)
    elif isinstance(node, (ast.For, ast.AsyncFor)):
        _walk(node.iter, out)                    # the iterable, then the target, then the body
        _walk(node.target, out)
        for s in node.body + node.orelse:
            _walk(s, out)
    elif isinstance(node, (ast.With, ast.AsyncWith)):
        for item in node.items:
            _walk(item.context_expr, out)
            if item.optional_vars is not None:
                _walk(item.optional_vars, out)
        for s in node.body:
            _walk(s, out)
    elif isinstance(node, ast.ExceptHandler):
        if node.type is not None:
            _walk(node.type, out)
        if node.name:
            out.append((node.name, False))
        for s in node.body:
            _walk(s, out)
    elif isinstance(node, (ast.Import, ast.ImportFrom)):
        for alias in node.names:                 # an import binds a name like any assignment
            if alias.name != '*':
                out.append(((alias.asname or alias.name).split('.')[0], False))
    elif isinstance(node, _SCOPES):
        for d in getattr(node, 'decorator_list', []):
            _walk(d, out)
        if isinstance(node, ast.ClassDef):
            for e in node.bases + [k.value for k in node.keywords]:
                _walk(e, out)
        else:
            _walk_arguments(node.args, out)      # defaults and annotations are evaluated here
            if getattr(node, 'returns', None) is not None:
                _walk(node.returns, out)
        out.extend((n, True) for n in _free_names(node))
        if not isinstance(node, ast.Lambda):
            out.append((node.name, False))
    elif isinstance(node, _COMPREHENSIONS):
        _comprehension(node, out)
    elif _MATCH_BINDERS and isinstance(node, _MATCH_BINDERS):
        pattern = getattr(node, 'pattern', None)
        if pattern is not None:
            _walk(pattern, out)
        for p in getattr(node, 'patterns', []):
            _walk(p, out)
        name = getattr(node, 'name', None) or getattr(node, 'rest', None)
        if name:
            out.append((name, False))
    else:
        for child in ast.iter_child_nodes(node):
            _walk(child, out)


def _walk_arguments(args, out):
    """A def's or lambda's defaults and annotations, evaluated where it is
    defined - in the function's scope, not the nested one's."""
    for d in args.defaults + [d for d in args.kw_defaults if d is not None]:
        _walk(d, out)
    for a in _every_arg(args):
        if a.annotation is not None:
            _walk(a.annotation, out)


def _every_arg(args):
    return (args.posonlyargs + args.args + args.kwonlyargs
            + [a for a in (args.vararg, args.kwarg) if a is not None])


def _free_names(node):
    """The names a nested scope (a def, a lambda, a class body) reads from
    the function around it: what its body loads and neither its arguments
    nor its own bindings supply, in first-read order."""
    inner = []
    bound = set()
    args = getattr(node, 'args', None)
    if args is not None:
        bound = {a.arg for a in _every_arg(args)}
    body = node.body if isinstance(node.body, list) else [node.body]
    for s in body:
        _walk(s, inner)
    bound |= {n for n, load in inner if not load}
    free = []
    for n, load in inner:
        if load and n not in bound and n not in free:
            free.append(n)
    return free


def _comprehension(node, out):
    """A comprehension is its own scope: its targets bind inside it and never
    reach the function. Its first iterable is evaluated in the function's
    scope; what its element, its conditions and its later iterables read
    beyond its own targets is read from the function."""
    inner = []
    gens = node.generators
    _walk(gens[0].iter, out)
    for i, g in enumerate(gens):
        if i:
            _walk(g.iter, inner)
        _walk(g.target, inner)
        for cond in g.ifs:
            _walk(cond, inner)
    if isinstance(node, ast.DictComp):
        _walk(node.key, inner)
        _walk(node.value, inner)
    else:
        _walk(node.elt, inner)
    bound = {n for n, load in inner if not load}
    out.extend((n, True) for n, load in inner if load and n not in bound)



def main():

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
    pre_ev = events(pre)
    stage_ev = [events(nodes) for nodes in stage_nodes]
    tail_ev = events(tail)
    for i, ((name, a, b), ev) in enumerate(zip(stages, stage_ev)):
        avail = assigned(pre_ev) | fn_args
        for j in range(i):
            avail |= assigned(stage_ev[j])
        # what the stage reads before binding, of what the function held
        need = {n for n in used(ev) if n in avail and first_use_before_assign(ev, n)}
        # a stage's own bindings that a later stage or the tail reads before
        # binding are RETURNED by the stage and bound at the call site - a
        # preamble name a stage re-binds (`persons = persons.sort_values()`)
        # as much as a name the stage introduces
        crossing = set()
        later_ev = [e for j in range(i + 1, len(stages)) for e in stage_ev[j]]
        for later in (later_ev, tail_ev):
            for n in assigned(ev):
                if first_use_before_assign(later, n):
                    crossing.add(n)
        # a crossing name the function already held is passed in as well as
        # returned, so a stage that re-binds it on one branch only still has
        # a value to hand back on the other
        need |= crossing & avail
        params.append(sorted(need))
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



if __name__ == '__main__':
    main()
