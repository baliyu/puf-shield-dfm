"""Minimal KiCad s-expression reader (KiCad 6 to 10 text files). Returns nested lists; strings keep their text, atoms are plain str."""
import re

_TOKEN = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))')


def parse(text: str):
    stack, cur = [], []
    pos = 0
    n = len(text)
    while pos < n:
        m = _TOKEN.match(text, pos)
        if not m:
            break
        pos = m.end()
        op, cl, qs, atom = m.groups()
        if op:
            stack.append(cur)
            cur = []
        elif cl:
            done = cur
            cur = stack.pop()
            cur.append(done)
        elif qs is not None:
            cur.append(Str(qs.replace('\\"', '"').replace('\\\\', '\\')))
        else:
            cur.append(atom)
    if stack:
        raise ValueError("unbalanced parentheses")
    return cur[0] if len(cur) == 1 else cur


class Str(str):
    """A quoted string from the file (so 'yes' the atom and \"yes\" the string stay distinct)."""


def find_all(node, head):
    return [c for c in node if isinstance(c, list) and c and c[0] == head]


def find(node, head, default=None):
    r = find_all(node, head)
    return r[0] if r else default


def prop(node, name):
    for c in find_all(node, "property"):
        if len(c) > 2 and c[1] == name:
            return str(c[2])
    return None
