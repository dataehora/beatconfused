"""Tiny S-expression reader/writer for KiCad files (stdlib only).

Nodes are Python lists; atoms are str. Quoted strings are kept as Q
instances so they are written back quoted.
"""


class Q(str):
    """A quoted string atom."""


def parse(text):
    stack, cur, i, n = [], [], 0, len(text)
    while i < n:
        c = text[i]
        if c == "(":
            stack.append(cur)
            cur = []
            i += 1
        elif c == ")":
            done = cur
            cur = stack.pop()
            cur.append(done)
            i += 1
        elif c == '"':
            j, buf = i + 1, []
            while text[j] != '"':
                if text[j] == "\\":
                    j += 1
                    buf.append({"n": "\n", "t": "\t"}.get(text[j], text[j]))
                else:
                    buf.append(text[j])
                j += 1
            cur.append(Q("".join(buf)))
            i = j + 1
        elif c in " \t\r\n":
            i += 1
        else:
            j = i
            while j < n and text[j] not in ' \t\r\n()"':
                j += 1
            cur.append(text[i:j])
            i = j
    return cur[0]


def quote(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def dump(node, indent=0):
    if not isinstance(node, list):
        return quote(node) if isinstance(node, Q) else node
    if all(not isinstance(x, list) for x in node):
        return "(" + " ".join(dump(x) for x in node) + ")"
    pad = "\t" * (indent + 1)
    head = [dump(x) for x in node if not isinstance(x, list)]
    out = "(" + " ".join(head)
    for x in node:
        if isinstance(x, list):
            out += "\n" + pad + dump(x, indent + 1)
    return out + "\n" + "\t" * indent + ")"


def find(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def first(node, key):
    r = find(node, key)
    return r[0] if r else None
