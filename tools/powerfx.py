"""powerfx: static checks of the Power Fx formulas in a canvas app's .pa.yaml source (docs/standards/powerfx-validation.md).

WHAT IT PROVES, AND WHAT IT DOES NOT. Two layers:

  1. SYNTAX, by Microsoft's own parser (Microsoft.PowerFx.Core, shipped inside the Power Platform CLI), called through
     tools/fxparse.ps1 with PowerShell 7. When pac or pwsh is missing, the stdlib parser below decides instead, and the
     report says so.
  2. MEANING, by the analyser below: function names and argument counts (from Microsoft's engine and the canvas formula
     reference, tools/powerfx-functions.json), behaviour functions outside behaviour properties, names that resolve to
     nothing, control properties, enumeration members, literal types, list columns (schemas/*.csv), Patch, delegation and
     indexes, variables, flow calls and acceptance-criteria comments.

Neither layer binds types the way Power Apps Studio does. A formula that passes here can still be refused by Studio
(a type mismatch inside an expression, a column on a list that was never imported, a connector that was never added)
or misbehave at run time. Passing means "no known defect found statically", never "error-free": the app must still be
opened in Studio (App checker: Formulas, Accessibility, Performance) and its acceptance checks walked.

USE
    import powerfx
    result = powerfx.check_app(app_name, {"Src/scrHome.pa.yaml": text, ...}, props_for=..., datasources=[...])
    for f in result.findings: print(f.severity, f.code, f.where(), f.message)

    uv run tools/powerfx.py --selftest            parse every formula of samples/powerapp and the canvas apps; cross-check parsers
    uv run tools/powerfx.py --refresh-functions   regenerate the 'core' part of tools/powerfx-functions.json from pac's engine
The project-level entry point is `uv run tools/pp.py fx` (and `pp.py build`, which runs the same checks).
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
CATALOGUE_PATH = ROOT / "tools" / "powerfx-functions.json"
FXPARSE = ROOT / "tools" / "fxparse.ps1"


# =========================================================================== YAML (the Source Code layout subset)

class Scalar:
    """A YAML scalar with the 1-based line its text starts on (for a block scalar, its first content line)."""
    __slots__ = ("text", "line", "style")

    def __init__(self, text: str, line: int, style: str) -> None:
        self.text, self.line, self.style = text, line, style


class YMap(dict):
    """A mapping that remembers the line of each key."""
    def __init__(self) -> None:
        super().__init__()
        self.lines: dict[str, int] = {}


_KEY = re.compile(r"""^(\s*)(?:'((?:[^']|'')*)'|"((?:[^"\\]|\\.)*)"|([^\s#'"\-][^:#]*?|-[^\s:#][^:#]*?))\s*:(?:\s+(.*?))?\s*$""")


class _Yaml:
    """Reads the mapping/sequence/scalar subset Studio writes (pa.yaml). Not a general YAML parser: anchors, tags, flow
    collections and complex keys are not needed by the format and are not supported. Syntax faults are reported by
    pp.py's PA1001 lint; this reader is tolerant and only recovers the formulas."""

    def __init__(self, text: str) -> None:
        self.lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        self.n = len(self.lines)
        self.i = 0

    @staticmethod
    def ind(s: str) -> int:
        return len(s) - len(s.lstrip(" "))

    def skip(self) -> None:
        while self.i < self.n and (not self.lines[self.i].strip() or self.lines[self.i].lstrip().startswith("#")):
            self.i += 1

    def node(self, min_indent: int):
        self.skip()
        if self.i >= self.n:
            return None
        line = self.lines[self.i]
        ind = self.ind(line)
        if ind < min_indent:
            return None
        if line.lstrip().startswith("- ") or line.strip() == "-":
            return self.seq(ind)
        return self.map(ind)

    def seq(self, ind: int) -> list:
        out = []
        while True:
            self.skip()
            if self.i >= self.n:
                break
            line = self.lines[self.i]
            if self.ind(line) != ind or not (line.lstrip().startswith("- ") or line.strip() == "-"):
                break
            rest = line[ind + 2:]
            if _KEY.match(" " * (ind + 2) + rest):
                self.lines[self.i] = " " * (ind + 2) + rest  # "- key: v" is a mapping at ind + 2
                out.append(self.map(ind + 2))
            else:
                out.append(self.scalar(rest.strip(), ind))
        return out

    def map(self, ind: int) -> YMap:
        out = YMap()
        while True:
            self.skip()
            if self.i >= self.n:
                break
            line = self.lines[self.i]
            li = self.ind(line)
            if li < ind:
                break
            if li > ind:  # stray deeper line: not ours (a YAML error the PA1001 lint reports)
                self.i += 1
                continue
            m = _KEY.match(line)
            if not m:
                break
            key = m.group(2).replace("''", "'") if m.group(2) is not None else (m.group(3) if m.group(3) is not None else m.group(4).strip())
            rest = m.group(5)
            out.lines[key] = self.i + 1
            if rest is None or rest == "" or rest.startswith("#"):
                self.i += 1
                self.skip()
                if self.i < self.n and self.ind(self.lines[self.i]) > ind:
                    out[key] = self.node(ind + 1)
                elif self.i < self.n and self.ind(self.lines[self.i]) == ind and self.lines[self.i].lstrip().startswith("- "):
                    out[key] = self.seq(ind)
                else:
                    out[key] = None
            else:
                out[key] = self.scalar(rest, ind)
        return out

    def scalar(self, rest: str, ind: int) -> Scalar:
        start = self.i + 1
        if rest[:1] in "|>" and re.match(r"^[|>][+-]?\d?\s*(#.*)?$", rest):
            head = rest.split("#")[0].strip()
            self.i += 1
            body = []
            while self.i < self.n and (not self.lines[self.i].strip() or self.ind(self.lines[self.i]) > ind):
                body.append(self.lines[self.i])
                self.i += 1
            content = [ln for ln in body if ln.strip()]
            bi = min((self.ind(ln) for ln in content), default=0)
            first = next((k for k, ln in enumerate(body) if ln.strip()), 0)
            rows = [ln[bi:] if ln.strip() else "" for ln in body]
            if head.startswith(">"):
                text = re.sub(r"(?<!\n)\n(?!\n)", " ", "\n".join(rows))
            else:
                text = "\n".join(rows)
            if "+" not in head:
                text = text.rstrip("\n") + ("" if "-" in head else "\n")
            return Scalar(text, start + 1 + first, "block")
        if rest.startswith("'") or rest.startswith('"'):
            q = rest[0]
            buf, j, line_text, parts = [], 1, rest, []
            while True:
                while j < len(line_text):
                    c = line_text[j]
                    if q == "'" and c == "'":
                        if j + 1 < len(line_text) and line_text[j + 1] == "'":
                            buf.append("'")
                            j += 2
                            continue
                        self.i += 1
                        return Scalar("".join(parts) + "".join(buf), start, "single")
                    if q == '"' and c == "\\" and j + 1 < len(line_text):
                        esc = line_text[j + 1]
                        buf.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\", "/": "/"}.get(esc, esc))
                        j += 2
                        continue
                    if q == '"' and c == '"':
                        self.i += 1
                        return Scalar("".join(parts) + "".join(buf), start, "double")
                    buf.append(c)
                    j += 1
                # The quoted scalar continues on the next line (folded: a line break is a space, a blank line a newline).
                self.i += 1
                if self.i >= self.n:
                    return Scalar("".join(parts) + "".join(buf), start, "single" if q == "'" else "double")
                nxt = self.lines[self.i]
                parts.append("".join(buf).rstrip(" ") + ("\n" if not nxt.strip() else " "))
                buf, line_text, j = [], nxt.strip(), 0
        # Plain scalar: " #" starts a YAML comment, so it is not part of the value (a formula that needs it must be quoted).
        cut = re.search(r"\s#", rest)
        text = (rest[:cut.start()] if cut else rest).rstrip()
        self.i += 1
        while self.i < self.n and self.lines[self.i].strip() and self.ind(self.lines[self.i]) > ind \
                and not self.lines[self.i].lstrip().startswith("#"):
            more = self.lines[self.i].strip()
            cut = re.search(r"\s#", more)
            text += " " + (more[:cut.start()] if cut else more).rstrip()
            self.i += 1
        return Scalar(text, start, "plain")


def load_yaml(text: str):
    return _Yaml(text).node(0)


# =========================================================================== tokenizer

class FxSyntaxError(Exception):
    def __init__(self, message: str, pos: int) -> None:
        super().__init__(message)
        self.message, self.pos = message, pos


class Tok:
    __slots__ = ("k", "v", "s", "e")

    def __init__(self, k: str, v, s: int, e: int) -> None:
        self.k, self.v, self.s, self.e = k, v, s, e

    def __repr__(self) -> str:
        return f"{self.k}:{self.v!r}"


_NUM = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")
_OPS2 = ("<>", "<=", ">=", "&&", "||", ":=")
_OPS1 = set("+-*/^%&=<>!.,;:(){}[]@")


def tokenize(src: str, base: int = 0):
    """Tokens and comments of a formula. Positions are offsets into `src` plus `base`."""
    toks, comments, i, n = [], [], 0, len(src)
    while i < n:
        c = src[i]
        if c.isspace():
            i += 1
            continue
        if src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            comments.append(Tok("comment", src[i + 2:j], base + i, base + j))
            i = j
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            if j < 0:
                raise FxSyntaxError("a /* comment is not closed with */", base + i)
            comments.append(Tok("comment", src[i + 2:j], base + i, base + j + 2))
            i = j + 2
            continue
        if c == '"':
            j, buf = i + 1, []
            while True:
                if j >= n:
                    raise FxSyntaxError("a text string is not closed with \"", base + i)
                if src[j] == '"':
                    if j + 1 < n and src[j + 1] == '"':
                        buf.append('"')
                        j += 2
                        continue
                    break
                buf.append(src[j])
                j += 1
            toks.append(Tok("str", "".join(buf), base + i, base + j + 1))
            i = j + 1
            continue
        if c == "$" and i + 1 < n and src[i + 1] == '"':
            parts, j = _interpolated(src, i + 2, base)
            toks.append(Tok("istr", parts, base + i, base + j))
            i = j
            continue
        if c == "'":
            j, buf = i + 1, []
            while True:
                if j >= n:
                    raise FxSyntaxError("a quoted name is not closed with '", base + i)
                if src[j] == "'":
                    if j + 1 < n and src[j + 1] == "'":
                        buf.append("'")
                        j += 2
                        continue
                    break
                buf.append(src[j])
                j += 1
            toks.append(Tok("qid", "".join(buf), base + i, base + j + 1))
            i = j + 1
            continue
        if c.isdigit() or (c == "." and i + 1 < n and src[i + 1].isdigit()):
            m = _NUM.match(src, i)
            toks.append(Tok("num", m.group(0), base + i, base + m.end()))
            i = m.end()
            continue
        if c.isalpha() or c == "_":
            j = i + 1
            while j < n and (src[j].isalnum() or src[j] == "_"):
                j += 1
            toks.append(Tok("id", src[i:j], base + i, base + j))
            i = j
            continue
        two = src[i:i + 2]
        if two in _OPS2:
            toks.append(Tok("op", two, base + i, base + i + 2))
            i += 2
            continue
        if c in _OPS1:
            toks.append(Tok("op", c, base + i, base + i + 1))
            i += 1
            continue
        if c in "“”‘’":
            raise FxSyntaxError(f"a curly quote ({c}) is not a Power Fx quote: use \" for text and ' for names", base + i)
        raise FxSyntaxError(f"unexpected character {c!r}", base + i)
    toks.append(Tok("eof", None, base + n, base + n))
    return toks, comments


def _interpolated(src: str, i: int, base: int):
    """Parts of $"...": ('t', text) and ('e', expression source, absolute offset). Returns (parts, index after the closing quote)."""
    parts, buf, n = [], [], len(src)
    while True:
        if i >= n:
            raise FxSyntaxError("an interpolated string $\"...\" is not closed", base + i)
        c = src[i]
        if c == '"':
            if i + 1 < n and src[i + 1] == '"':
                buf.append('"')
                i += 2
                continue
            if buf:
                parts.append(("t", "".join(buf)))
            return parts, i + 1
        if c == "{" and src.startswith("{{", i):
            buf.append("{")
            i += 2
            continue
        if c == "}" and src.startswith("}}", i):
            buf.append("}")
            i += 2
            continue
        if c == "{":
            if buf:
                parts.append(("t", "".join(buf)))
                buf = []
            j, depth = i + 1, 1
            while j < n and depth:
                if src[j] == '"':  # skip a nested string (and a nested interpolated one)
                    j += 1
                    while j < n and not (src[j] == '"' and not src.startswith('""', j)):
                        j += 2 if src.startswith('""', j) else 1
                elif src[j] == "'":
                    j += 1
                    while j < n and src[j] != "'":
                        j += 1
                elif src[j] == "{":
                    depth += 1
                elif src[j] == "}":
                    depth -= 1
                    if not depth:
                        break
                j += 1
            if depth:
                raise FxSyntaxError("a { in an interpolated string is not closed", base + i)
            parts.append(("e", src[i + 1:j], base + i + 1))
            i = j + 1
            continue
        buf.append(c)
        i += 1


# =========================================================================== parser

class Node:
    """An expression node. k: num str bool istr name member call rec tbl un bin chain block as disamb index pct empty."""

    def __init__(self, k: str, s: int, e: int, **kw) -> None:
        self.k, self.s, self.e = k, s, e
        self.__dict__.update(kw)

    def __repr__(self) -> str:
        return f"<{self.k} {self.s}-{self.e}>"


BIN_PREC = {"||": 1, "Or": 1, "&&": 2, "And": 2, "=": 3, "<>": 3, "<": 3, ">": 3, "<=": 3, ">=": 3, "in": 3, "exactin": 3,
            "&": 4, "+": 5, "-": 5, "*": 6, "/": 6, "^": 7}
_CLOSERS = {")", "}", "]", ","}


class Parser:
    def __init__(self, src: str, base: int = 0) -> None:
        self.src, self.base = src, base
        self.toks, self.comments = tokenize(src, base)
        self.strings: list[Tok] = [t for t in self.toks if t.k in ("str", "istr")]
        self.i = 0

    # -- token helpers
    def peek(self, k: int = 0) -> Tok:
        return self.toks[min(self.i + k, len(self.toks) - 1)]

    def next(self) -> Tok:
        t = self.toks[self.i]
        self.i = min(self.i + 1, len(self.toks) - 1)
        return t

    def is_op(self, v: str, k: int = 0) -> bool:
        t = self.peek(k)
        return t.k == "op" and t.v == v

    def expect_op(self, v: str) -> Tok:
        t = self.peek()
        if not (t.k == "op" and t.v == v):
            raise FxSyntaxError(f"expected '{v}' but found {self.describe(t)}", t.s)
        return self.next()

    @staticmethod
    def describe(t: Tok) -> str:
        return "the end of the formula" if t.k == "eof" else f"'{t.v}'" if t.k in ("op", "id", "num") else t.k

    def at_closer(self) -> bool:
        t = self.peek()
        return t.k == "eof" or (t.k == "op" and t.v in _CLOSERS)

    # -- grammar
    def formula(self) -> Node:
        node = self.chain()
        t = self.peek()
        if t.k != "eof":
            raise FxSyntaxError(f"unexpected {self.describe(t)}", t.s)
        return node

    def chain(self) -> Node:
        if self.at_closer():
            t = self.peek()
            return Node("empty", t.s, t.s)
        items = [self.expr()]
        while self.is_op(";"):
            self.next()
            if self.at_closer():
                break
            items.append(self.expr())
        return items[0] if len(items) == 1 else Node("chain", items[0].s, items[-1].e, items=items)

    def binop(self) -> str | None:
        t = self.peek()
        if t.k == "op" and t.v in BIN_PREC:
            return t.v
        if t.k == "id" and t.v in ("And", "Or", "in", "exactin"):
            return t.v
        return None

    def expr(self, minp: int = 1) -> Node:
        left = self.unary()
        while True:
            op = self.binop()
            if not op or BIN_PREC[op] < minp:
                return left
            self.next()
            right = self.expr(BIN_PREC[op] + 1)
            left = Node("bin", left.s, right.e, op=op, l=left, r=right)

    def unary(self) -> Node:
        t = self.peek()
        if (t.k == "op" and t.v in ("-", "+", "!")) or (t.k == "id" and t.v == "Not" and not self.is_op("(", 1)):
            self.next()
            x = self.unary()
            return Node("un", t.s, x.e, op=t.v, x=x)
        return self.postfix()

    def postfix(self) -> Node:
        x = self.primary()
        while True:
            t = self.peek()
            if t.k == "op" and t.v == ".":
                self.next()
                m = self.next()
                if m.k not in ("id", "qid"):
                    raise FxSyntaxError(f"expected a name after '.' but found {self.describe(m)}", m.s)
                x = Node("member", x.s, m.e, obj=x, name=m.v)
            elif t.k == "op" and t.v == "(":
                if x.k not in ("name", "member") or getattr(x, "paren", False):
                    raise FxSyntaxError("only a function name can be followed by '('", t.s)
                args, end = self.args()
                x = Node("call", x.s, end, head=x, args=args)
            elif t.k == "op" and t.v == "%":
                self.next()
                x = Node("pct", x.s, t.e, x=x)
            elif t.k == "op" and t.v == "[" and self.is_op("@", 1):
                self.next()
                self.next()
                m = self.next()
                if m.k not in ("id", "qid"):
                    raise FxSyntaxError("expected a name after '[@'", m.s)
                end = self.expect_op("]").e
                x = Node("index", x.s, end, obj=x, name=m.v)
            else:
                return x

    def args(self):
        self.expect_op("(")
        out = []
        if self.is_op(")"):
            return out, self.next().e
        while True:
            if self.is_op(",") or self.is_op(")"):
                raise FxSyntaxError("an argument is missing", self.peek().s)
            a = self.chain()
            t = self.peek()
            if t.k == "id" and t.v == "As":
                self.next()
                m = self.next()
                if m.k not in ("id", "qid"):
                    raise FxSyntaxError("expected a name after As", m.s)
                a = Node("as", a.s, m.e, x=a, name=m.v)
            out.append(a)
            t = self.next()
            if t.k == "op" and t.v == ")":
                return out, t.e
            if not (t.k == "op" and t.v == ","):
                raise FxSyntaxError(f"expected ',' or ')' but found {self.describe(t)}", t.s)

    def primary(self) -> Node:
        t = self.next()
        if t.k == "num":
            return Node("num", t.s, t.e, v=float(t.v) if any(c in t.v for c in ".eE") else int(t.v))
        if t.k == "str":
            return Node("str", t.s, t.e, v=t.v)
        if t.k == "istr":
            parts = []
            for p in t.v:
                if p[0] == "t":
                    parts.append(p[1])
                else:
                    sub = Parser(p[1], p[2])
                    self.comments += sub.comments
                    self.strings += sub.strings
                    parts.append(sub.formula())
            return Node("istr", t.s, t.e, parts=parts)
        if t.k == "id":
            if t.v in ("true", "false"):
                return Node("bool", t.s, t.e, v=t.v == "true")
            return Node("name", t.s, t.e, v=t.v, quoted=False)
        if t.k == "qid":
            return Node("name", t.s, t.e, v=t.v, quoted=True)
        if t.k == "op" and t.v == "(":
            inner = self.chain()
            end = self.expect_op(")").e
            inner.paren = True
            return inner if inner.k != "empty" else Node("empty", t.s, end)
        if t.k == "op" and t.v == "{":
            fields = []
            if self.is_op("}"):
                return Node("rec", t.s, self.next().e, fields=fields)
            while True:
                f = self.next()
                if f.k not in ("id", "qid"):
                    raise FxSyntaxError(f"expected a field name in a record but found {self.describe(f)}", f.s)
                self.expect_op(":")
                fields.append((f.v, self.expr(), f.s))
                c = self.next()
                if c.k == "op" and c.v == "}":
                    return Node("rec", t.s, c.e, fields=fields)
                if not (c.k == "op" and c.v == ","):
                    raise FxSyntaxError(f"expected ',' or '}}' in a record but found {self.describe(c)}", c.s)
        if t.k == "op" and t.v == "[":
            if self.is_op("@"):
                self.next()
                m = self.next()
                if m.k not in ("id", "qid"):
                    raise FxSyntaxError("expected a name after '[@'", m.s)
                return Node("disamb", t.s, self.expect_op("]").e, v=m.v)
            items = []
            if self.is_op("]"):
                return Node("tbl", t.s, self.next().e, items=items)
            while True:
                items.append(self.expr())
                c = self.next()
                if c.k == "op" and c.v == "]":
                    return Node("tbl", t.s, c.e, items=items)
                if not (c.k == "op" and c.v == ","):
                    raise FxSyntaxError(f"expected ',' or ']' in a table but found {self.describe(c)}", c.s)
        raise FxSyntaxError(f"unexpected {self.describe(t)}", t.s)

    # -- App.Formulas: named formulas and user-defined functions
    def named_formulas(self) -> list[dict]:
        out = []
        while self.peek().k != "eof":
            t = self.next()
            if t.k not in ("id", "qid"):
                raise FxSyntaxError(f"expected a formula name but found {self.describe(t)}", t.s)
            entry = {"name": t.v, "start": t.s, "udf": False, "params": [], "returns": None, "behavior": False}
            if self.is_op("("):
                entry["udf"] = True
                self.next()
                while not self.is_op(")"):
                    p = self.next()
                    if p.k not in ("id", "qid"):
                        raise FxSyntaxError("expected a parameter name", p.s)
                    self.expect_op(":")
                    self.postfix()
                    entry["params"].append(p.v)
                    if not self.is_op(")"):
                        self.expect_op(",")
                self.next()
                self.expect_op(":")
                rt = self.postfix()
                entry["returns"] = rt.v if rt.k == "name" else None
            op = self.next()
            if not (op.k == "op" and op.v in ("=", ":=")):
                raise FxSyntaxError(f"expected '=' after the formula name {t.v} but found {self.describe(op)}", op.s)
            entry["type_def"] = op.v == ":="
            body_start = self.peek().s
            if entry["udf"] and self.is_op("{") and self._is_block(entry["returns"]):
                self.next()
                body = self.chain()
                end = self.expect_op("}").e
                body = Node("block", body_start, end, items=[body])
                entry["behavior"] = True
            else:
                body = self.expr()
            entry["body"], entry["body_span"] = body, (body_start, body.e)
            out.append(entry)
            if self.is_op(";"):
                self.next()
            elif self.peek().k != "eof":
                raise FxSyntaxError(f"expected ';' after the named formula {t.v} but found {self.describe(self.peek())}", self.peek().s)
        return out

    def _is_block(self, returns: str | None) -> bool:
        a, b = self.peek(1), self.peek(2)
        if a.k == "op" and a.v == "}":
            return returns == "Void"
        return not (a.k in ("id", "qid") and b.k == "op" and b.v == ":")


def parse(src: str, base: int = 0) -> tuple[Node, Parser]:
    p = Parser(src, base)
    return p.formula(), p


def children(n: Node) -> list[Node]:
    k = n.k
    if k == "member" or k == "index":
        return [n.obj]
    if k == "call":
        return ([n.head.obj] if n.head.k == "member" else []) + list(n.args)
    if k == "rec":
        return [v for _, v, _ in n.fields]
    if k in ("tbl", "chain", "block"):
        return list(n.items)
    if k in ("un", "as", "pct"):
        return [n.x]
    if k == "bin":
        return [n.l, n.r]
    if k == "istr":
        return [p for p in n.parts if isinstance(p, Node)]
    return []


def walk(n: Node, anc: tuple = ()):
    """(node, ancestors) for every node, depth first; ancestors are (parent, index in children)."""
    yield n, anc
    for i, c in enumerate(children(n)):
        yield from walk(c, anc + ((n, i),))


def call_name(n: Node) -> str | None:
    return n.head.v if n.k == "call" and n.head.k == "name" else None


# =========================================================================== catalogue and app facts

_CATALOGUE = None


def catalogue() -> dict:
    """{'functions': {name: (min, max, source)}, 'namespaces': {ns: {name: (min, max)}}, 'behavior': set}"""
    global _CATALOGUE
    if _CATALOGUE is None:
        raw = json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))
        funcs = {}
        for f in raw["core"]["functions"]:
            funcs[f["name"]] = (f["min"], f["max"], "Microsoft.PowerFx.Core")
        for f in raw["canvas"]["functions"]:
            funcs.setdefault(f["name"], (f["min"], f["max"], "canvas formula reference"))
        ns = {k: {f["name"]: (f["min"], f["max"]) for f in v} for k, v in raw.get("namespaces", {}).items()}
        _CATALOGUE = {"functions": funcs, "namespaces": ns, "behavior": set(raw["behavior"])}
    return _CATALOGUE


# Enumerations whose members this check knows completely (from the canvas function and control references). An unknown
# member is an error. Other enumerations (Color, Font, Icon, ErrorKind, ...) are recognised but their members are not checked.
STRICT_ENUMS = {
    "NotificationType": {"Error", "Information", "Success", "Warning"},
    "ScreenTransition": {"Cover", "CoverRight", "Fade", "None", "UnCover", "UnCoverRight"},
    "DisplayMode": {"Disabled", "Edit", "View"},
    "SortOrder": {"Ascending", "Descending"},
    "Align": {"Center", "Justify", "Left", "Right"},
    "VerticalAlign": {"Bottom", "Middle", "Top"},
    "FontWeight": {"Bold", "Lighter", "Normal", "Semibold"},
    "LayoutDirection": {"Horizontal", "Vertical"},
    "LayoutOverflow": {"Hidden", "Scroll"},
    "LayoutAlignItems": {"Center", "End", "Start", "Stretch"},
    "AlignInContainer": {"Center", "End", "SetByContainer", "Start", "Stretch"},
    "DropShadow": {"Bold", "ExtraBold", "Light", "None", "Regular", "Semilight"},
    "TextMode": {"MultiLine", "Password", "SingleLine"},
    "Live": {"Assertive", "Off", "Polite"},
    "FormMode": {"Edit", "New", "View"},
    "BorderStyle": {"Dashed", "Dotted", "None", "Solid"},
    "DateTimeZone": {"Local", "UTC"},
    "TimeUnit": {"Days", "Hours", "Milliseconds", "Minutes", "Months", "Quarters", "Seconds", "Years"},
    "RemoveFlags": {"All"},
    "LaunchTarget": {"New", "Replace"},
}
OTHER_ENUMS = {
    "Color", "Font", "Icon", "TextRole", "LayoutJustifyContent", "TextFormat", "Overflow", "ImagePosition", "StartOfWeek", "ErrorKind",
    "ErrorSeverity", "JSONFormat", "MatchOptions", "Match", "Transition", "Direction", "ScreenSize", "Layout", "PenMode", "DataSourceInfo",
    "RecordInfo", "DateTimeFormat", "TraceSeverity", "TraceOptions", "VirtualKeyboardMode", "TeamsTheme", "PDFPaperSize", "ImageRotation",
    "ListItemTemplate", "GridStyle", "Zoom", "SelectedState", "BarcodeType", "MapStyle", "Themes", "TextPosition", "LabelPosition",
    "AppearanceType", "CameraOrientation", "ScanMode", "FormPattern",
}
# Names Power Apps provides: named operators, signals, host objects, the theme.
OBJECTS = {"Self", "Parent", "ThisItem", "ThisRecord", "App", "Host", "Location", "Acceleration", "Compass", "Connection",
           "PowerAppsTheme", "Screen", "Calendar", "Clock", "Dataverse"}
# Properties whose value has one type. A literal of another type there is a defect Studio reports or coerces badly.
ENUM_PROPS = {"DisplayMode": "DisplayMode", "Align": "Align", "VerticalAlign": "VerticalAlign", "FontWeight": "FontWeight",
              "LayoutDirection": "LayoutDirection", "LayoutAlignItems": "LayoutAlignItems", "LayoutOverflowX": "LayoutOverflow",
              "LayoutOverflowY": "LayoutOverflow", "AlignInContainer": "AlignInContainer", "DropShadow": "DropShadow", "Live": "Live",
              "BorderStyle": "BorderStyle"}
NUMBER_PROPS = {"X", "Y", "Width", "Height", "Size", "BorderThickness", "FocusedBorderThickness", "PaddingTop", "PaddingBottom",
                "PaddingLeft", "PaddingRight", "RadiusTopLeft", "RadiusTopRight", "RadiusBottomLeft", "RadiusBottomRight", "LayoutGap",
                "TemplateSize", "TemplatePadding", "FillPortions", "TabIndex", "LayoutMinWidth", "LayoutMinHeight", "LayoutMaxWidth",
                "LayoutMaxHeight", "MaxLength", "LineHeight", "Transparency"}
BOOLEAN_PROPS = {"Visible", "AutoHeight", "Wrap", "Italic", "Underline", "Strikethrough", "ShowScrollbar", "Reset", "Clear",
                 "EnableSpellCheck", "ShowNavigation", "Checked"}
TEXT_PROPS = {"Text", "HintText", "Tooltip", "AccessibleLabel", "Placeholder"}

# Functions whose arguments from the given index on are evaluated per record of the first argument (record scope): bare
# names there may be that table's columns.
SCOPE_FUNCS = {"Filter": 1, "LookUp": 1, "Search": 2, "Sort": 1, "SortByColumns": 1, "AddColumns": 1, "DropColumns": 1,
               "ShowColumns": 1, "RenameColumns": 1, "ForAll": 1, "Sum": 1, "Average": 1, "Max": 1, "Min": 1, "StdevP": 1, "VarP": 1,
               "Concat": 1, "CountIf": 1, "RemoveIf": 1, "UpdateIf": 1, "GroupBy": 1, "Ungroup": 1, "Distinct": 1}
SCALAR_OR_TABLE = {"Sum", "Average", "Max", "Min", "StdevP", "VarP"}
FORM_FUNCS = {"SubmitForm", "ResetForm", "NewForm", "EditForm", "ViewForm"}
WRITE_FUNCS = {"Patch", "Collect", "Update", "UpdateIf", "Remove", "RemoveIf"}
DELEGABLE_WRAPPERS = {"Filter", "Sort", "SortByColumns"}
# Run in the app, over at most the data row limit (500 by default, 2,000 at most), when given a SharePoint list.
APP_SIDE_ON_LIST = {"Sum", "Average", "Max", "Min", "StdevP", "VarP", "CountIf", "CountA", "Count", "CountRows", "Distinct", "GroupBy",
                    "ForAll", "Last", "LastN", "Concat", "Shuffle"}
# A column wrapped in one of these inside Filter/LookUp cannot be sent to SharePoint (docs/standards/dev-standards.md §5).
NOT_DELEGABLE_ON_COLUMN = {"Len", "Lower", "Upper", "Proper", "Left", "Right", "Mid", "Trim", "TrimEnds", "Text", "Value", "Year",
                           "Month", "Day", "Hour", "Minute", "Weekday", "DateValue", "DateTimeValue", "TimeValue", "Find", "Substitute",
                           "Replace", "EndsWith", "IsMatch", "Match", "Concatenate", "Round", "RoundUp", "RoundDown", "Int", "Abs",
                           "DateDiff", "DateAdd", "Coalesce", "Search"}
SUPPRESSIBLE = {"FX-DELEG", "FX-INDEX", "FX-ERRHANDLING", "FX-TEXT", "FX-UNUSED"}
SP_SYSTEM = {  # SharePoint columns every list has: (type, read-only, indexed)
    "ID": ("Counter", True, True), "Title": ("Text", False, False), "Created": ("DateTime", True, False),
    "Modified": ("DateTime", True, False), "Author": ("User", True, False), "Editor": ("User", True, False),
    "Attachments": ("Attachments", False, False),
}
AC_STRICT = re.compile(r"\bAC-[A-Z0-9]{2,10}-\d{2,3}\.\d+\b")
AC_NO_CHECK = re.compile(r"\bAC-[A-Z0-9]{2,10}-\d{2,3}\b(?!\.\d)")
AC_LOOSE = re.compile(r"\bAC[-_ ][A-Za-z0-9]+[-_][A-Za-z0-9.]+")


class Column:
    __slots__ = ("name", "display", "type", "required", "indexed", "readonly", "choices", "has_default")

    def __init__(self, name, display, type_, required=False, indexed=False, readonly=False, choices=None, has_default=False):
        self.name, self.display, self.type, self.required, self.indexed = name, display, type_, required, indexed
        self.readonly, self.choices, self.has_default = readonly, choices, has_default


class ListSchema:
    def __init__(self, name: str, columns: list[Column]) -> None:
        self.name = name
        self.columns = {c.name: c for c in columns}
        self.by_display = {c.display: c for c in columns if c.display}

    def col(self, name: str) -> Column | None:
        return self.columns.get(name) or self.by_display.get(name)


def load_schemas(folder: Path) -> dict[str, ListSchema]:
    """schemas/<List>.csv, line 1 `ListSchema={"schemaXmlList": [...]}`, parsed with an XML parser."""
    out = {}
    for csv in sorted(folder.glob("*.csv")) if folder.exists() else []:
        try:
            first = csv.read_text(encoding="utf-8-sig").split("\n")[0]
            xmls = json.loads(first[len("ListSchema="):])["schemaXmlList"]
        except (ValueError, KeyError, OSError):
            continue
        cols = [Column(k, k, t, False, ix, ro) for k, (t, ro, ix) in SP_SYSTEM.items()]
        for x in xmls:
            try:
                f = ET.fromstring(x)
            except ET.ParseError:
                continue
            name = f.get("Name") or f.get("StaticName")
            if not name:
                continue
            choices = [c.text or "" for c in f.iter("CHOICE")] or None
            col = Column(name, f.get("DisplayName") or name, f.get("Type", "Text"), f.get("Required", "").upper() == "TRUE",
                         f.get("Indexed", "").upper() == "TRUE", f.get("ReadOnly", "").upper() == "TRUE" or f.get("Type") == "Calculated",
                         choices, f.find("Default") is not None)
            cols = [c for c in cols if c.name != name] + [col]
        out[csv.stem] = ListSchema(csv.stem, cols)
    return out


def load_flows(folder: Path) -> dict[str, dict]:
    """Flows in the solution source: display name -> {'kind', 'params' (None = unknown), 'required'}."""
    out = {}
    for data in sorted(folder.glob("*.json.data.xml")) if folder.exists() else []:
        text = data.read_text(encoding="utf-8-sig", errors="replace")
        m = re.search(r'<Workflow[^>]*\sName="([^"]+)"', text)
        if not m:
            continue
        info = {"kind": None, "params": None, "required": []}
        jf = data.with_name(data.name[: -len(".data.xml")])
        try:
            flow = json.loads(jf.read_text(encoding="utf-8-sig"))
            for trig in flow.get("properties", {}).get("definition", {}).get("triggers", {}).values():
                info["kind"] = trig.get("kind") or trig.get("type")
                if trig.get("type") == "Request" and trig.get("kind") in ("PowerAppV2", "Button"):
                    schema = (trig.get("inputs") or {}).get("schema") or {}
                    info["params"] = list((schema.get("properties") or {}).keys())
                    info["required"] = list(schema.get("required") or [])
        except (OSError, ValueError):
            pass
        out[m.group(1)] = info
    return out


def list_prefix() -> str | None:
    card = ROOT / "PROJECT.md"
    if not card.exists():
        return None
    m = re.search(r"^\|\s*List prefix\s*\|\s*`?([A-Za-z][A-Za-z0-9]*)`?\s*\|", card.read_text(encoding="utf-8-sig"), re.M)
    return m.group(1) if m else None


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


# =========================================================================== Microsoft's parser (pac's Microsoft.PowerFx.Core)

_OFFICIAL_CACHE: dict[str, dict] = {}


def find_powerfx_dll() -> Path | None:
    import os
    env = os.environ.get("PP_POWERFX_DLL")
    if env and Path(env).exists():
        return Path(env)
    roots = []
    pac = shutil.which("pac")
    if pac:
        roots.append(Path(pac).resolve().parent / ".store")
    roots.append(Path.home() / ".dotnet" / "tools" / ".store")
    if os.environ.get("LOCALAPPDATA"):
        roots.append(Path(os.environ["LOCALAPPDATA"]) / "Microsoft" / "PowerAppsCLI")
    found = []
    for r in roots:
        if r.exists():
            found += list(r.glob("**/Microsoft.PowerFx.Core.dll"))
    found = [f for f in found if "resources" not in f.name]

    def version(p: Path):
        return [int(x) if x.isdigit() else 0 for part in p.parts for x in re.findall(r"\d+", part)][:12]
    return max(found, key=version) if found else None


def official_parse(items: list[tuple[str, str, bool]]) -> tuple[dict | None, str]:
    """Parse [(id, text, behavior)] with Microsoft's parser. Returns ({id: {'ok', 'errors'}}, version) or (None, reason)."""
    dll = find_powerfx_dll()
    if not dll:
        return None, "Microsoft.PowerFx.Core.dll not found (it ships with pac; set PP_POWERFX_DLL to point at it)"
    pwsh = shutil.which("pwsh")
    if not pwsh:
        return None, "PowerShell 7 (pwsh) not found"
    out, todo = {}, []
    for id_, text, beh in items:
        key = hashlib.sha1(f"{beh}\x00{text}".encode()).hexdigest()
        if key in _OFFICIAL_CACHE:
            out[id_] = _OFFICIAL_CACHE[key]
        else:
            todo.append((id_, text, beh, key))
    version = _OFFICIAL_CACHE.get("__version__", {}).get("v", "")
    if todo:
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = Path(tmp) / "in.json", Path(tmp) / "out.json"
            src.write_text(json.dumps([{"id": k, "text": t, "behavior": b} for _, t, b, k in todo]), encoding="utf-8")
            try:
                proc = subprocess.run([pwsh, "-NoProfile", "-NonInteractive", "-File", str(FXPARSE), "-Dll", str(dll), "-In", str(src),
                                       "-Out", str(dst)], capture_output=True, text=True, errors="replace", timeout=300)
            except (OSError, subprocess.TimeoutExpired) as e:
                return None, f"pwsh failed: {e}"
            if proc.returncode != 0 or not dst.exists():
                last = ((proc.stderr or proc.stdout).strip().splitlines() or [""])[-1][:200]
                return None, f"pwsh could not load Microsoft's parser (pwsh and pac on different .NET versions?) {last}".rstrip()
            res = json.loads(dst.read_text(encoding="utf-8-sig"))
        version = res.get("version", "")
        _OFFICIAL_CACHE["__version__"] = {"v": version}
        by_key = {r["id"]: r for r in res.get("results", [])}
        for id_, _, _, key in todo:
            r = by_key.get(key, {"ok": True, "errors": []})
            _OFFICIAL_CACHE[key] = r
            out[id_] = r
    return out, version


# =========================================================================== findings

class Finding:
    __slots__ = ("severity", "code", "file", "line", "owner", "prop", "message")

    def __init__(self, severity, code, file, line, owner, prop, message):
        self.severity, self.code, self.file, self.line, self.owner, self.prop, self.message = severity, code, file, line, owner, prop, message

    def where(self) -> str:
        loc = f"{self.file} line {self.line}" if self.line else self.file
        return f"{loc} {self.owner}.{self.prop}" if self.prop else f"{loc} {self.owner}" if self.owner else loc

    def text(self) -> str:
        return f"{self.where()}: {self.message} [{self.code}]"


class Formula:
    """One property formula."""

    def __init__(self, file, owner, ctype, prop, scalar, screen, ancestors, kind):
        self.file, self.owner, self.ctype, self.prop, self.scalar = file, owner, ctype, prop, scalar
        self.screen, self.ancestors, self.kind = screen, ancestors, kind  # ancestors: [(name, ctype)] outermost first
        raw = scalar.text if scalar else ""
        lead = len(raw) - len(raw.lstrip())
        self.has_eq = raw.lstrip().startswith("=")
        self.src = raw.lstrip()[1:] if self.has_eq else raw
        self.offset = lead + (1 if self.has_eq else 0)
        self.raw = raw
        self.behavior = (prop.startswith("On") and prop[2:3].isupper()) or prop == "OnStart"
        self.ast: Node | None = None
        self.parser: Parser | None = None
        self.entries: list[dict] = []  # App.Formulas
        self.id = f"{file}|{owner}|{prop}"

    def line_at(self, pos: int) -> int:
        if not self.scalar:
            return 0
        if self.scalar.style == "block":
            return self.scalar.line + self.raw[: self.offset + max(0, pos)].count("\n")
        return self.scalar.line


class Result:
    def __init__(self) -> None:
        self.findings: list[Finding] = []
        self.suppressed: list[tuple[Finding, str]] = []
        self.stats = {"formulas": 0, "official": 0, "calls": 0, "names": 0, "unverified_scope": 0, "connector_calls": 0,
                      "delegation_sites": 0, "writes": 0}
        self.official_version = ""
        self.official_reason = ""

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "warning"]


# =========================================================================== the analysis

def extract(yaml_texts: dict[str, str]) -> tuple[list[Formula], dict, dict, list]:
    """Every property formula, the controls {name: info}, the screens {name: file} and structural problems."""
    formulas, controls, screens, problems = [], {}, {}, []

    def add_props(file, owner, ctype, props, screen, ancestors, kind):
        if not isinstance(props, dict):
            return
        for prop, val in props.items():
            if isinstance(val, Scalar):
                formulas.append(Formula(file, owner, ctype, prop, val, screen, ancestors, kind))
            elif val is None:
                formulas.append(Formula(file, owner, ctype, prop, Scalar("", props.lines.get(prop, 0), "plain"), screen, ancestors, kind))

    def walk_children(file, items, screen, ancestors):
        for item in items or []:
            if not isinstance(item, dict):
                continue
            for name, body in item.items():
                if not isinstance(body, dict):
                    continue
                ctl = body.get("Control")
                ctype = ctl.text if isinstance(ctl, Scalar) else None
                line = item.lines.get(name, 0) if isinstance(item, YMap) else 0
                if name in controls and controls[name]["screen"] != screen:
                    problems.append(("FX-DUPNAME", file, line, name,
                                     f"control name '{name}' is also used on {controls[name]['screen']} ({controls[name]['file']} line "
                                     f"{controls[name]['line']}). Control names are unique across the whole app (PA2110)"))
                variant = body.get("Variant")
                controls.setdefault(name, {"ctype": ctype, "screen": screen, "file": file, "line": line,
                                           "variant": variant.text if isinstance(variant, Scalar) else None,
                                           "ancestors": list(ancestors), "props": set((body.get("Properties") or {}).keys())})
                add_props(file, name, ctype, body.get("Properties"), screen, ancestors, "control")
                walk_children(file, body.get("Children"), screen, ancestors + [(name, ctype)])

    for file, text in sorted(yaml_texts.items()):
        if not file.endswith(".pa.yaml") or file.endswith("_EditorState.pa.yaml"):
            continue
        doc = load_yaml(text)
        if not isinstance(doc, dict):
            continue
        app = doc.get("App")
        if isinstance(app, dict):
            add_props(file, "App", None, app.get("Properties"), None, [], "app")
        for group in ("Screens", "ComponentDefinitions"):
            for sname, body in (doc.get(group) or {}).items() if isinstance(doc.get(group), dict) else []:
                if not isinstance(body, dict):
                    continue
                screens[sname] = {"file": file, "component": group == "ComponentDefinitions",
                                  "custom": set((body.get("CustomProperties") or {}).keys()) if isinstance(body.get("CustomProperties"), dict) else set()}
                add_props(file, sname, None, body.get("Properties"), sname, [], "screen")
                walk_children(file, body.get("Children"), sname, [])
    return formulas, controls, screens, problems


class Analyzer:
    def __init__(self, app: str, yaml_texts: dict[str, str], props_for=None, screen_props=None, datasources=None, schemas=None,
                 flows=None, prefix=None, release=False, use_official=True, child_props=None) -> None:
        self.app = app
        self.yaml_texts = yaml_texts
        self.props_for = props_for or (lambda ctype: None)
        self.screen_props = set(screen_props or ())
        self.child_props = set(child_props or ())
        self.flows_used: set[str] = set()
        self.datasources = set(datasources or ())
        self.schemas = schemas if schemas is not None else load_schemas(ROOT / "schemas")
        self.flows = flows if flows is not None else load_flows(ROOT / "solution" / "src" / "Workflows")
        self.prefix = prefix if prefix is not None else list_prefix()
        self.release = release
        self.use_official = use_official
        self.cat = catalogue()
        self.r = Result()
        self.globals: dict[str, list] = {}       # Set(name, value): [(formula, literal kind)]
        self.ctx: dict[str, dict[str, list]] = {}  # screen -> context variable -> [(formula, literal kind)]
        self.collections: dict[str, list] = {}
        self.reads: set[str] = set()
        self.named: dict[str, dict] = {}
        self.udfs: dict[str, dict] = {}
        self.has_onerror = False
        self.f: Formula | None = None  # the formula being analysed

    # -- reporting
    def add(self, severity, code, message, pos=None, f: Formula | None = None, file=None, line=None, owner=None, prop=None):
        f = f or self.f
        if f is not None:
            file, line, owner, prop = f.file, (f.line_at(pos) if pos is not None else (f.scalar.line if f.scalar else 0)), f.owner, f.prop
        self.r.findings.append(Finding(severity, code, file or "", line or 0, owner or "", prop or "", message))

    # -- structure checks (each one cost a round in Studio on a delivered project)
    def _structure_checks(self, f: Formula) -> None:
        src = f.src or ""
        # FX-OVERLAY: a control placed from an overlay's panel (X or Y names the panel's X, Y, Width or Height) must be shown by that overlay's variable too.
        # Without its own Visible it is drawn on every screen state, over the content (PA-T41).
        if f.kind == "control" and f.prop in ("X", "Y") and f.screen:
            me = self.controls.get(f.owner)
            if me is not None and "Visible" not in me["props"]:
                for m in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\.(?:X|Y|Width|Height)\b", src):
                    ref = self.controls.get(m.group(1))
                    if ref is not None and ref["screen"] == f.screen and m.group(1) != f.owner and "Visible" in ref["props"]:
                        self.add("error", "FX-OVERLAY", f"'{f.owner}' is placed from '{m.group(1)}', which is shown and hidden, but has no Visible of its own: it would show "
                                 f"on top of every screen state. Give it the same Visible as '{m.group(1)}' (PA-T41)", f=f)
                        break
        # FX-SVG: Text(x, "0.##") leaves a trailing separator ("30."), which is not an SVG number: the shape is not drawn (PA-T40)
        if "<svg" in src and re.search(r'Text\([^()]*(?:\([^()]*\))?[^()]*,\s*"[0#]*\.#+"\s*\)', src):
            self.add("error", "FX-SVG", "an SVG built with Text(x, \"0.##\"): a whole number comes out as \"30.\", which is not an SVG number, so the shape is not drawn. "
                     "Use Substitute(Text(Round(x, 2)), \",\", \".\") (PA-T40)", f=f)
        # FX-NAME: the table behind a SharePoint item's Attachments has the columns Id, DisplayName, Value and AbsoluteUri, not Name (PA-T42)
        if re.search(r"\.Attachments\s*,\s*\{[^{}]*:\s*(?:ThisRecord\.)?Name\s*[,}]", src):
            self.add("error", "FX-NAME", "'Name' isn't a column of an Attachments table: its columns are Id, DisplayName, Value and AbsoluteUri (PA-T42)", f=f)

    # -- driver
    def run(self) -> Result:
        formulas, self.controls, self.screens, problems = extract(self.yaml_texts)
        for code, file, line, owner, msg in problems:
            self.add("error", code, msg, file=file, line=line, owner=owner, prop="")
        self.formulas = formulas
        self.r.stats["formulas"] = len(formulas)
        for f in formulas:
            self._structure_checks(f)
        self.has_onerror = any(f.kind == "app" and f.prop == "OnError" and f.src.strip() for f in formulas)
        self._parse_all()
        for f in formulas:
            if f.ast is not None or f.entries:
                self._collect(f)
        for f in formulas:
            self.f = f
            if f.prop == "Formulas" and f.kind == "app":
                for e in f.entries:
                    if not e.get("bad") and not e.get("type_def"):  # a type definition's body names types, not values
                        self._analyse(e["body"], f, entry=e)
            elif f.ast is not None:
                self._analyse(f.ast, f)
            self._comments(f)
        self.f = None
        self._variables()
        self._apply_suppressions()
        return self.r

    def _parse_all(self) -> None:
        jobs, entry_of = [], {}
        for f in self.formulas:
            self.f = f
            if not f.has_eq and f.raw.strip():
                self.add("error", "FX-YAML", "the value does not start with '=': every property value in .pa.yaml is a Power Fx formula "
                                             "(write =\"text\" for text, =12 for a number)")
                continue
            if f.kind == "app" and f.prop == "Formulas":
                # Microsoft's parser takes one expression, so each named formula's body goes to it on its own.
                try:
                    p = Parser(f.src)
                    f.entries = p.named_formulas()
                    f.parser = p
                except FxSyntaxError as e:
                    self.add("error", "FX-SYNTAX", f"App.Formulas: {e.message} (stdlib parser)", pos=e.pos)
                    for m in re.finditer(r"(?m)^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:\(|:?=)", f.src):
                        self.named.setdefault(m.group(1), {"name": m.group(1)})  # keep the names, so screens don't cascade errors
                    continue
                for e in f.entries:
                    (self.udfs if e["udf"] else self.named)[e["name"]] = e
                    if not e.get("type_def"):
                        s, t = e["body_span"]
                        jobs.append((f"{f.id}|{e['name']}", f.src[s:t], e["behavior"], f, s))
                        entry_of[f"{f.id}|{e['name']}"] = e
                continue
            try:
                f.ast, f.parser = parse(f.src)
            except FxSyntaxError as e:
                f.ast = None
                f.syntax_error = e
            jobs.append((f.id, f.src, f.behavior, f, 0))
        official = None
        if self.use_official and jobs:
            official, info = official_parse([(j[0], j[1], j[2]) for j in jobs])
            if official is None:
                self.r.official_reason = info
            else:
                self.r.official_version = info
        confirmed = set()
        for id_, text, beh, f, base in jobs:
            self.f = f
            mine = getattr(f, "syntax_error", None)
            if official is not None and id_ in official:
                if f.id not in confirmed:
                    confirmed.add(f.id)
                    self.r.stats["official"] += 1
                res = official[id_]
                if not res["ok"]:
                    e = res["errors"][0] if res["errors"] else {"message": "syntax error", "start": 0}
                    more = f" (+{len(res['errors']) - 1} more)" if len(res["errors"]) > 1 else ""
                    hint = ""
                    if not beh and re.search(r";", text) and "operator" in e["message"].lower():
                        hint = ". A ';' chains actions, which only behaviour properties (On...) may do"
                    self.add("error", "FX-SYNTAX", f"Microsoft's Power Fx parser: {e['message']}{more}{hint}", pos=base + (e.get("start") or 0))
                    if id_ in entry_of:
                        entry_of[id_]["bad"] = True  # this named formula is not analysed; the others still are
                    else:
                        f.ast = None
                elif mine is not None:
                    self.add("warning", "FX-PARSER", f"Microsoft's parser accepts this formula but the stdlib analyser cannot read it "
                                                     f"({mine.message}); its names, functions and data use were NOT checked")
            elif mine is not None:
                self.add("error", "FX-SYNTAX", f"{mine.message} (stdlib parser; Microsoft's parser was not available to confirm)", pos=mine.pos)
            elif not beh and f.ast is not None and self._has_chain(f.ast) and f.prop != "Formulas":
                self.add("error", "FX-SYNTAX", "';' chains actions, which only behaviour properties (On...) may do")

    @staticmethod
    def _has_chain(n: Node) -> bool:
        return any(x.k == "chain" for x, _ in walk(n))

    # -- pass 1: what the app defines
    def _collect(self, f: Formula) -> None:
        roots = [e["body"] for e in f.entries] if f.entries else [f.ast]
        for root in roots:
            for n, _ in walk(root):
                name = call_name(n)
                if not name or not n.args:
                    continue
                a0 = n.args[0]
                if name == "Set" and a0.k == "name":
                    self.globals.setdefault(a0.v, []).append((f, lit_kind(n.args[1]) if len(n.args) > 1 else None, n.s))
                elif name == "UpdateContext" and a0.k == "rec" and f.screen:
                    for fname, val, _ in a0.fields:
                        self.ctx.setdefault(f.screen, {}).setdefault(fname, []).append((f, lit_kind(val), n.s))
                elif name == "Navigate" and len(n.args) >= 3 and a0.k == "name" and n.args[2].k == "rec":
                    for fname, val, _ in n.args[2].fields:
                        self.ctx.setdefault(a0.v, {}).setdefault(fname, []).append((f, lit_kind(val), n.s))
                elif name in ("Collect", "ClearCollect", "LoadData") and a0.k == "name" and not self._is_datasource(a0.v):
                    self.collections.setdefault(a0.v, []).append((f, n.s))

    def _is_datasource(self, name: str) -> bool:
        return name in self.schemas or name in self.datasources or name in self.flows

    # -- pass 2: every formula
    def _analyse(self, root: Node, f: Formula, entry: dict | None = None) -> None:
        if entry is not None:
            scope = Scope(None, names=set(entry["params"]))
            behavior = entry["behavior"]
        else:
            scope, behavior = Scope(None), f.behavior
        self.f = f
        self.behavior = behavior
        self.entry = entry
        self.res(root, scope)
        self._data(root)
        if entry is None:
            self._literal_types(root)
            self._token_discipline(root)

    # ---- names
    def lookup(self, name: str, scope: "Scope"):
        """What a bare name is: (kind, info) or None."""
        hit = scope.find(name)
        if hit:
            return hit
        if name in OBJECTS:
            return ("object", name)
        f = self.f
        if name in ("FirstError", "AllErrors") and f and f.prop == "OnError":
            return ("object", name)  # App.OnError sees the error it handles
        if f and f.screen and name in self.ctx.get(f.screen, {}):
            return ("ctxvar", name)
        if name in self.globals:
            return ("global", name)
        if name in self.collections:
            return ("collection", name)
        if name in self.named:
            return ("named", name)
        if name in self.controls:
            return ("control", name)
        if name in self.screens:
            return ("screen", name)
        if name in self.schemas:
            return ("list", name)
        if name in self.datasources:
            return ("datasource", name)
        if name in self.flows:
            return ("flow", name)
        if name in STRICT_ENUMS or name in OTHER_ENUMS or name in self.cat["namespaces"]:
            return ("enum", name)
        return None

    def unknown_name(self, n: Node, scope: "Scope", name: str) -> None:
        if scope.is_open():
            self.r.stats["unverified_scope"] += 1
            return
        known = set(self.globals) | set(self.collections) | set(self.named) | set(self.controls) | set(self.screens) | \
            set(self.schemas) | set(self.datasources) | OBJECTS | set(STRICT_ENUMS) | OTHER_ENUMS | \
            set(self.ctx.get(self.f.screen, {}) if self.f.screen else {}) | {"true", "false"}
        ci = [k for k in known if k.lower() == name.lower()]
        if ci:
            self.add("error", "FX-NAME", f"'{name}' is not defined; names are case-sensitive: did you mean '{ci[0]}'?", n.s)
            return
        if self.prefix and re.fullmatch(rf"{re.escape(self.prefix)}_[A-Za-z0-9]+", name):
            self.add("error", "FX-SCHEMA", f"the formula names the list '{name}' but there is no schemas/{name}.csv (PA-T27)", n.s)
            return
        other = [s for s, v in self.ctx.items() if name in v and s != self.f.screen]
        hint = f". It is a context variable of {', '.join(sorted(other))}: context variables belong to one screen (use Set for a global)" if other else \
            ": not a control, screen, variable, collection, named formula, list in schemas/, data source, flow or enumeration"
        self.add("error", "FX-NAME", f"'{name}' is not defined{hint}", n.s)

    def res(self, n: Node, scope: "Scope") -> None:
        k = n.k
        if k == "name":
            self.r.stats["names"] += 1
            hit = self.lookup(n.v, scope)
            if hit is None:
                self.unknown_name(n, scope, n.v)
                return
            self.reads.add(n.v)
            if n.v == "ThisItem" and hit[0] == "object" and not self._in_item_container():
                self.add("error", "FX-THISITEM", "ThisItem is only defined inside a gallery or a form (this control is in neither)", n.s)
            return
        if k == "disamb":
            self.reads.add(n.v)
            if n.v not in self.globals and n.v not in self.collections and not self._is_datasource(n.v):
                self.add("error", "FX-NAME", f"[@{n.v}] names no global variable, collection or data source", n.s)
            return
        if k == "member":
            self.res_member(n, scope)
            return
        if k == "call":
            self.res_call(n, scope)
            return
        for c in children(n):
            self.res(c, scope)

    def _in_item_container(self) -> bool:
        """ThisItem exists inside a gallery or form, and in the item properties of a list control (ItemDisplayText of a dropdown)."""
        def item_type(ct):
            base = (ct or "").split("@")[0].split("/")[-1]
            return base in ("Gallery", "Form", "ModernForm", "FormViewer", "DataTable", "ModernTable", "Table") or "DataCard" in base \
                or any(w in base for w in ("Dropdown", "DropDown", "Combobox", "ComboBox", "ListBox", "Radio"))
        return item_type(self.f.ctype) or any(item_type(ct) for _, ct in self.f.ancestors)

    def _props_of_control(self, ctype: str | None):
        return self.props_for(ctype) if ctype else None

    def res_member(self, n: Node, scope: "Scope") -> None:
        obj, prop = n.obj, n.name
        if obj.k != "name":
            self.res(obj, scope)
            return
        self.r.stats["names"] += 1
        hit = self.lookup(obj.v, scope)
        if hit is None:
            self.unknown_name(obj, scope, obj.v)
            return
        self.reads.add(obj.v)
        kind, info = hit
        if kind == "control":
            c = self.controls[obj.v]
            self._check_control_prop(n, obj.v, c["ctype"], prop, c)
        elif kind == "object" and obj.v == "Self":
            if self.f.kind == "control":
                self._check_control_prop(n, self.f.owner, self.f.ctype, prop, self.controls.get(self.f.owner))
        elif kind == "object" and obj.v == "Parent":
            if self.f.kind == "control":
                if self.f.ancestors:
                    pname, pctype = self.f.ancestors[-1]
                    self._check_control_prop(n, pname, pctype, prop, self.controls.get(pname))
                elif self.screen_props and prop not in self.screen_props and not self.screens.get(self.f.screen, {}).get("component"):
                    self.add("error", "FX-CTRLPROP", f"Parent here is the screen {self.f.screen}, which has no property '{prop}'", n.s)
        elif kind == "object" and obj.v == "ThisItem":
            if not self._in_item_container():
                self.add("error", "FX-THISITEM", "ThisItem is only defined inside a gallery or a form (this control is in neither)", obj.s)
            lst = self._gallery_list()
            if lst and not self.schemas[lst].col(prop):
                self.add("error", "FX-SCHEMA", f"ThisItem.{prop}: the gallery shows {lst}, which has no column '{prop}' in schemas/{lst}.csv", n.s)
        elif kind == "enum" and obj.v == "ErrorKind" and prop in ("EditPermission", "CreatePermission", "DeletePermission"):
            self.add("error", "FX-ENUM", f"ErrorKind.{prop} is not recognised by Studio ('Name isn't valid', PA-T33): test FirstError.Message instead "
                                         "(ReadPermission is recognised)", n.s)
        elif kind == "enum" and obj.v in STRICT_ENUMS and prop not in STRICT_ENUMS[obj.v]:
            self.add("error", "FX-ENUM", f"{obj.v}.{prop} is not a member of {obj.v} ({', '.join(sorted(STRICT_ENUMS[obj.v]))})", n.s)
        elif kind == "list":
            if not self.schemas[obj.v].col(prop):
                self.add("error", "FX-SCHEMA", f"{obj.v}.{prop}: no column '{prop}' in schemas/{obj.v}.csv", n.s)
        elif kind == "alias" and info:
            if not self.schemas[info].col(prop):
                self.add("error", "FX-SCHEMA", f"{obj.v}.{prop}: no column '{prop}' in schemas/{info}.csv", n.s)
        elif kind == "object" and obj.v == "ThisRecord":
            lst = scope.list_name()
            if lst and not self.schemas[lst].col(prop):
                self.add("error", "FX-SCHEMA", f"ThisRecord.{prop}: no column '{prop}' in schemas/{lst}.csv", n.s)

    def _check_control_prop(self, n: Node, name: str, ctype: str | None, prop: str, info: dict | None) -> None:
        if ctype is None and info is None:
            return
        props = self._props_of_control(ctype)
        if props is None:
            return
        extra = self.child_props | (info or {}).get("props", set())
        if prop not in props and prop not in extra:
            close = [p for p in props if p.lower() == prop.lower()]
            hint = f": did you mean '{close[0]}'?" if close else ""
            self.add("error", "FX-CTRLPROP", f"{name}.{prop}: {ctype} has no property '{prop}'{hint} (Studio's control template)", n.s)

    def _gallery_list(self) -> str | None:
        """The list a gallery (or form) around this control shows, when its Items/DataSource is that list, filtered or sorted."""
        for name, ct in reversed(self.f.ancestors):
            base = (ct or "").split("@")[0].split("/")[-1]
            if base not in ("Gallery", "Form"):
                continue
            f = next((x for x in self.formulas if x.owner == name and x.prop in ("Items", "DataSource")), None)
            if f is None or f.ast is None:
                return None
            return self.base_list(f.ast)
        return None

    def base_list(self, n: Node) -> str | None:
        if n.k == "name" and n.v in self.schemas:
            return n.v
        if n.k == "as":
            return self.base_list(n.x)
        if n.k == "call" and call_name(n) in DELEGABLE_WRAPPERS and n.args:
            return self.base_list(n.args[0])
        return None

    # ---- calls
    def res_call(self, n: Node, scope: "Scope") -> None:
        self.r.stats["calls"] += 1
        head, args = n.head, n.args
        if head.k == "member":
            self._member_call(n, scope)
            for a in args:
                self.res(a, scope)
            return
        fname = head.v
        cat = self.cat["functions"]
        if fname in self.udfs:
            u = self.udfs[fname]
            if len(args) != len(u["params"]):
                self.add("error", "FX-ARITY", f"{fname} is defined in App.Formulas with {len(u['params'])} parameter(s) but is given {len(args)}", n.s)
            if u["behavior"] and not self.behavior:
                self.add("error", "FX-BEHAVIOR", f"{fname} is a behaviour function (its body is {{...}}): only behaviour properties (On...) may call it", n.s)
        elif fname in cat:
            lo, hi, src = cat[fname]
            if len(args) < lo or (hi is not None and len(args) > hi):
                want = f"{lo}" if lo == hi else f"{lo} or more" if hi is None else f"{lo} to {hi}"
                self.add("error", "FX-ARITY", f"{fname} takes {want} argument(s), given {len(args)} ({src})", n.s)
            if fname in self.cat["behavior"] and not self.behavior:
                where = "a named formula" if self.entry is not None else f"{self.f.prop}, which is not a behaviour property"
                self.add("error", "FX-BEHAVIOR", f"{fname} changes app state, so it may only be used in a behaviour property (On...), not in {where}", n.s)
        else:
            near = [k for k in list(cat) + list(self.udfs) if k.lower() == fname.lower()]
            hint = f": names are case-sensitive, did you mean {near[0]}?" if near else \
                " (not in Microsoft's Power Fx library, the canvas formula reference, or this app's App.Formulas)"
            self.add("error", "FX-FUNC", f"'{fname}' is an unknown function{hint}", n.s)
        self._call_rules(n, fname, scope)
        # Arguments, with record scope where the function gives one.
        sf = SCOPE_FUNCS.get(fname)
        if fname in SCALAR_OR_TABLE and args and not _maybe_table(args[0]):
            sf = None
        if fname == "IfError" and len(args) >= 2:
            self.res(args[0], scope)
            err_scope = Scope(scope, names={"FirstError", "AllErrors"})  # the fallbacks see the error that was caught
            for a in args[1:]:
                self.res(a, err_scope)
            return
        if fname == "With" and len(args) == 2:
            self.res(args[0], scope)
            fields = {fn for fn, _, _ in args[0].fields} if args[0].k == "rec" else set()
            self.res(args[1], Scope(scope, names=fields, open_=args[0].k != "rec"))
            return
        if fname == "Set" and args and args[0].k == "name":
            for a in args[1:]:  # the variable being set is not a read of it
                self.res(a, scope)
            return
        if sf is not None and len(args) > sf:
            for a in args[:sf]:
                self.res(a, scope)
            a0 = args[0]
            alias = a0.name if a0.k == "as" else None
            lst = self.base_list(a0)
            cols = self.schemas[lst] if lst else None
            inner = Scope(scope, names=set(), alias=alias, alias_list=lst, columns=cols, open_=cols is None)
            for a in args[sf:]:
                if fname in ("SortByColumns", "Search", "DropColumns", "ShowColumns", "RenameColumns", "GroupBy", "Ungroup", "AddColumns") \
                        and a.k == "name" and not cols:
                    continue  # a column name given as an identifier (newer syntax); its table is not a known list
                self.res(a, inner)
            return
        for a in args:
            self.res(a, scope)

    def _member_call(self, n: Node, scope: "Scope") -> None:
        head, args = n.head, n.args
        obj, m = head.obj, head.name
        if obj.k != "name":
            self.res(obj, scope)
            return
        if m == "Run":
            self.reads.add(obj.v)
            flow = obj.v if obj.v in self.flows else next((k for k in self.flows if _norm(k) == _norm(obj.v)), None)
            if not self.behavior:
                self.add("error", "FX-BEHAVIOR", f"'{obj.v}'.Run starts a flow, which only behaviour properties (On...) may do", n.s)
            if flow is None:
                if obj.v in self.datasources:
                    return
                self.add("error", "FX-FLOW", f"a formula calls the flow '{obj.v}', which is not in solution/src/Workflows", n.s)
                return
            self.flows_used.add(flow)
            info = self.flows[flow]
            if info["params"] is not None:
                if len(args) < len(info["required"]) or len(args) > len(info["params"]):
                    self.add("error", "FX-FLOW", f"'{flow}'.Run is given {len(args)} argument(s); its Power Apps (V2) trigger takes "
                                                 f"{len(info['required'])} required and {len(info['params'])} in all", n.s)
            return
        if obj.v in self.cat["namespaces"]:
            fns = self.cat["namespaces"][obj.v]
            if m not in fns:
                self.add("error", "FX-FUNC", f"{obj.v}.{m} is not a function of {obj.v} ({', '.join(sorted(fns))})", n.s)
            else:
                lo, hi = fns[m]
                if len(args) < lo or (hi is not None and len(args) > hi):
                    self.add("error", "FX-ARITY", f"{obj.v}.{m} takes {lo} argument(s), given {len(args)}", n.s)
            return
        hit = self.lookup(obj.v, scope)
        if hit and hit[0] in ("datasource", "list"):
            self.r.stats["connector_calls"] += 1
            return
        if hit is None and scope.is_open():
            return
        self.r.stats["connector_calls"] += 1
        self.add("warning", "FX-NAME", f"{obj.v}.{m}(...): '{obj.v}' is not a data source this check knows (not in the app's "
                                       "References/DataSources.json). If it is a connector, add it in Studio; until then the formula is an error there", n.s)

    def _call_rules(self, n: Node, fname: str, scope: "Scope") -> None:
        a = n.args
        if not a:
            return
        a0 = a[0]
        if fname in SCOPE_FUNCS and call_name(a0) == "Split":  # PA-T38: Studio does not call Split's column 'Result'
            for arg in a[1:]:
                for sub, _ in walk(arg):
                    if sub.k == "name" and sub.v == "Result":
                        self.add("error", "FX-NAME", "'Result' is not Split's column name in Studio (PA-T38): test the text with `in` against the Split table, or read the column as Value", sub.s)
        if fname == "Set":
            if a0.k != "name":
                self.add("error", "FX-VAR", "Set's first argument must be a variable name", a0.s)
            else:
                clash = "named formula" if a0.v in self.named else "control" if a0.v in self.controls else "screen" if a0.v in self.screens \
                    else "list" if a0.v in self.schemas else None
                if clash:
                    self.add("error", "FX-VAR", f"Set({a0.v}, ...): '{a0.v}' is a {clash}, not a variable", a0.s)
        elif fname == "UpdateContext" and a0.k != "rec":
            self.add("error", "FX-VAR", "UpdateContext takes a record: UpdateContext({locName: value})", a0.s)
        elif fname in ("Collect", "ClearCollect", "Clear") and a0.k not in ("name", "disamb"):
            self.add("error", "FX-VAR", f"{fname}'s first argument must be a collection or data source name", a0.s)
        elif fname == "Navigate":
            if self.f is not None and self.f.prop in ("OnVisible", "OnStart"):
                self.add("error", "FX-NAV", f"Navigate cannot be used in {self.f.prop}: Studio refuses it because it would always navigate away from "
                                                 "the screen (PA-T30). Show a message instead, or navigate from a control's OnSelect", n.s)
            if a0.k == "name":
                hit = self.lookup(a0.v, scope)
                if hit and hit[0] not in ("screen", "global", "ctxvar", "named", "alias", "scope", "field"):
                    self.add("error", "FX-NAME", f"Navigate({a0.v}, ...): '{a0.v}' is a {hit[0]}, not a screen", a0.s)
            if len(a) > 1:
                self._expect_enum(a[1], "ScreenTransition", "Navigate's second argument")
            if len(a) > 2 and a[2].k != "rec":
                self.add("error", "FX-VAR", "Navigate's third argument is a record of context variables: {locName: value}", a[2].s)
        elif fname in ("ShowColumns", "DropColumns") and any(x.k == "str" for x in a[1:]):
            self.add("error", "FX-ARG", f"{fname} takes column names as identifiers, not text: {fname}(Table, Title, Name). Studio answers 'Expected identifier name' "
                                        "and 'has some invalid arguments' (PA-T33)", n.s)
        elif fname == "IfError" and len(a) >= 2:
            kind = {"ClearCollect": "table", "Collect": "table", "Filter": "table", "SortByColumns": "table", "ForAll": "table", "Notify": "boolean", "Set": "boolean", "Reset": "boolean", "SetFocus": "boolean", "Navigate": "boolean"}

            def last_kind(x):
                if x.k == "chain":
                    x = x.items[-1]
                return kind.get(call_name(x) or "") if x.k == "call" else ("boolean" if x.k == "lit" and getattr(x, "v", None) in (True, False, "true", "false") else None)
            v, fb = last_kind(a0), last_kind(a[1])
            if v and fb and v != fb:
                self.add("error", "FX-TYPE", f"IfError: the protected formula ends in a {v} but the fallback ends in a {fb}; Studio refuses the mix "
                                             f"('Invalid argument type ({fb.title()}). Expecting a {v.title()} value', PA-T31). End the protected chain with ; true", n.s)
        elif fname == "Back" and a:
            self._expect_enum(a0, "ScreenTransition", "Back's argument")
        elif fname == "Notify" and len(a) > 1:
            self._expect_enum(a[1], "NotificationType", "Notify's second argument")
        elif fname == "Sort" and len(a) > 2:
            self._expect_enum(a[2], "SortOrder", "Sort's third argument")
        elif fname == "SortByColumns":
            for x in a[2::2]:
                self._expect_enum(x, "SortOrder", "a SortByColumns order")
        elif fname in FORM_FUNCS and a0.k == "name":
            c = self.controls.get(a0.v)
            if c is None:
                return
            base = (c["ctype"] or "").split("@")[0].split("/")[-1]
            if "Form" not in base:
                self.add("error", "FX-NAME", f"{fname}({a0.v}): '{a0.v}' is a {c['ctype']}, not a form", a0.s)
            elif fname == "SubmitForm" and "OnFailure" not in c["props"] and not self.has_onerror:
                self.add("warning", "FX-ERRHANDLING", f"SubmitForm({a0.v}): the form has no OnFailure, so a failed save shows nothing "
                                                      "(dev-standards §5)", a0.s)
        elif fname in ("Reset", "SetFocus") and a0.k == "name":
            hit = self.lookup(a0.v, scope)
            if hit and hit[0] not in ("control", "alias", "scope", "field"):
                self.add("error", "FX-NAME", f"{fname}({a0.v}): '{a0.v}' is a {hit[0]}, not a control", a0.s)
        elif fname in ("Refresh", "Revert") and a0.k == "name":
            if a0.v in self.collections or a0.v in self.globals:
                self.add("error", "FX-NAME", f"{fname}({a0.v}): '{a0.v}' is a {'collection' if a0.v in self.collections else 'variable'}; "
                                             f"{fname} takes a data source", a0.s)

    def _expect_enum(self, x: Node, enum: str, what: str) -> None:
        if x.k in ("str", "num", "bool"):
            self.add("error", "FX-ENUM", f"{what} must be a {enum} value ({enum}.{sorted(STRICT_ENUMS[enum])[0]}), not a literal", x.s)
        elif x.k == "member" and x.obj.k == "name" and x.obj.v in STRICT_ENUMS and x.obj.v != enum:
            self.add("error", "FX-ENUM", f"{what} must be a {enum} value, not {x.obj.v}.{x.name}", x.s)

    # ---- data: writes and delegation
    def _data(self, root: Node) -> None:
        text_has_errors = "Errors(" in self.f.src
        for n, anc in walk(root):
            fname = call_name(n)
            if not fname or not n.args:
                continue
            a0 = n.args[0]
            if fname in WRITE_FUNCS and a0.k == "name" and self._is_datasource(a0.v) and a0.v not in self.collections:
                self.r.stats["writes"] += 1
                if a0.v in self.schemas:
                    self._write(n, fname, self.schemas[a0.v])
                guarded = any(call_name(p) == "IfError" and i == 0 for p, i in anc) or text_has_errors or self.has_onerror
                if not guarded:
                    self.add("warning", "FX-ERRHANDLING", f"{fname}({a0.v}, ...) is not inside IfError(...) and nothing reads Errors({a0.v}): "
                                                          "a failed save is silent (dev-standards §5, STD-PERM)", n.s)
            lst = self.base_list(a0)
            if not lst:
                continue
            if fname == "Search" and a0.k == "name":
                self.r.stats["delegation_sites"] += 1
                self.add("error", "FX-DELEG", f"Search({lst}, ...) is not delegable to SharePoint: only the first 500 items (data row "
                                              "limit) are searched. Filter with StartsWith on an indexed column (PA-T14)", n.s)
            elif fname in ("Filter", "LookUp"):
                self.r.stats["delegation_sites"] += 1
                for pred in n.args[1:2] if fname == "LookUp" else n.args[1:]:
                    self._predicate(pred, self.schemas[lst], a0.name if a0.k == "as" else None)
            elif fname == "Sort" and len(n.args) > 1 and a0.k in ("name", "as"):
                self.r.stats["delegation_sites"] += 1
                key = n.args[1]
                col = self._colref(key, self.schemas[lst], a0.name if a0.k == "as" else None)
                if col is None:
                    self.add("error", "FX-DELEG", f"Sort({lst}, <formula>) sorts by a formula, which SharePoint cannot do: sort by a column "
                                                  "(SortByColumns) (PA-T14)", key.s)
                else:
                    self._indexed(col, lst, key.s, "sorts by")
            elif fname == "SortByColumns":
                self.r.stats["delegation_sites"] += 1
                for x in n.args[1::2]:
                    cname = x.v if x.k in ("str", "name") else None
                    if cname is None:
                        continue
                    col = self.schemas[lst].col(cname)
                    if col is None:
                        self.add("error", "FX-SCHEMA", f"SortByColumns({lst}, \"{cname}\"): no column '{cname}' in schemas/{lst}.csv", x.s)
                    else:
                        self._indexed(col, lst, x.s, "sorts by")
            elif fname in APP_SIDE_ON_LIST:
                self.r.stats["delegation_sites"] += 1
                self.add("warning", "FX-DELEG", f"{fname}({lst}, ...) runs in the app over at most the data row limit (500 by default), "
                                                "not over the whole list: right only while the list stays that small (PA-T14)", n.s)

    def _colref(self, n: Node, schema: ListSchema, alias: str | None) -> Column | None:
        if n.k == "name":
            return schema.col(n.v)  # in record scope a column hides a variable of the same name ([@name] reaches the variable)
        if n.k == "member" and n.obj.k == "name" and (n.obj.v == "ThisRecord" or (alias and n.obj.v == alias)):
            return schema.col(n.name)
        return None

    def _column_refs(self, root: Node, schema: ListSchema, alias: str | None):
        """(column, node, ancestors) for each column of `schema` used in `root`, not descending into nested record scopes."""
        def rec(n, anc):
            col = self._colref(n, schema, alias)
            if col is not None:
                yield col, n, anc
                return
            nm = call_name(n)
            if nm in SCOPE_FUNCS and n.k == "call":
                kids = n.args[:SCOPE_FUNCS[nm]]
                for i, c in enumerate(kids):
                    yield from rec(c, anc + ((n, i),))
                return
            for i, c in enumerate(children(n)):
                yield from rec(c, anc + ((n, i),))
        yield from rec(root, ())

    def _predicate(self, pred: Node, schema: ListSchema, alias: str | None) -> None:
        seen = set()
        for col, node, anc in self._column_refs(pred, schema, alias):
            # Walk up past member access (Status.Value, Author.Email) and logical operators to the operation that uses the column.
            k = len(anc) - 1
            while k >= 0 and anc[k][0].k == "member":
                k -= 1
            verdict = None
            while k >= 0:
                p, i = anc[k]
                pn = call_name(p)
                if p.k == "bin" and p.op in ("&&", "||", "And", "Or"):
                    k -= 1
                    continue
                if p.k == "un" or pn in ("And", "Or", "Not"):
                    k -= 1
                    continue
                if p.k == "call" and pn == "StartsWith":
                    verdict = None if i == 0 else ("error", "StartsWith(<text>, <column>) is not delegable: the column must be the first argument")
                elif p.k == "call" and pn == "IsBlank":
                    verdict = ("warning", f"IsBlank({col.name}) may not be delegable to SharePoint: confirm Studio shows no delegation "
                                          f"warning, or compare with Blank()")
                elif p.k == "call" and pn in NOT_DELEGABLE_ON_COLUMN:
                    verdict = ("error", f"{pn}({col.name}) inside Filter/LookUp is evaluated in the app, not by SharePoint: only the first "
                                        f"500 items are filtered (PA-T14)")
                elif p.k == "call" and pn:
                    verdict = ("warning", f"{pn}(...) applied to the column {col.name} may not be delegable: confirm in Studio (PA-T14)")
                elif p.k == "bin" and p.op in ("in", "exactin"):
                    verdict = ("error", f"'{p.op}' with the column {col.name} is not delegable to SharePoint: only the first 500 items are "
                                        "filtered. Use = or StartsWith on an indexed column (PA-T14)")
                elif p.k == "bin" and p.op in ("=", "<>", "<", ">", "<=", ">="):
                    other = p.r if i == 0 else p.l
                    if any(True for _ in self._column_refs(other, schema, alias)):
                        verdict = ("warning", f"a comparison between two columns ({col.name}) is not delegable to SharePoint (PA-T14)")
                elif p.k == "bin":
                    verdict = ("warning", f"'{p.op}' on the column {col.name} inside Filter/LookUp may not be delegable (PA-T14)")
                break
            if verdict:
                self.add(verdict[0], "FX-DELEG", verdict[1], node.s)
            if col.type == "Note":
                self.add("error", "FX-DELEG", f"{col.name} is a multi-line text (Note) column: SharePoint cannot filter on it (T-10)", node.s)
            elif col.type == "Calculated":
                self.add("error", "FX-DELEG", f"{col.name} is a calculated column: SharePoint cannot filter on it (PA-T14)", node.s)
            elif col.type in ("User", "UserMulti", "MultiChoice", "LookupMulti"):
                self.add("warning", "FX-DELEG", f"{col.name} is a {col.type} column: filtering on it may not be delegable; dev-standards §5 "
                                                "says don't (store an indexed Text or Number copy)", node.s)
            if col.name not in seen:
                seen.add(col.name)
                self._indexed(col, schema.name, node.s, "filters on")

    def _indexed(self, col: Column, lst: str, pos: int, verb: str) -> None:
        if not col.indexed and col.name != "ID":
            self.add("error", "FX-INDEX", f"the formula {verb} {lst}.{col.name}, which is not indexed in schemas/{lst}.csv: past 5,000 "
                                          f"items the query fails (L5, T-1, T-9). Add Indexed=\"TRUE\"", pos)

    def _write(self, n: Node, fname: str, schema: ListSchema) -> None:
        args = n.args
        creating, changes = False, []
        if fname == "Patch" and len(args) >= 2:
            base = args[1]
            if call_name(base) == "Defaults":
                creating = True
                if base.args and base.args[0].k == "name" and base.args[0].v != schema.name:
                    self.add("error", "FX-PATCH", f"Patch({schema.name}, Defaults({base.args[0].v}), ...): the defaults come from another data "
                                                  "source", base.s)
            changes = args[2:] if len(args) > 2 or base.k != "rec" else [base]
        elif fname == "Collect":
            creating, changes = True, args[1:]
        elif fname == "Update" and len(args) > 2:
            changes = [args[2]]
        elif fname == "UpdateIf":
            changes = args[2::2]
        set_cols = set()
        literal_only = bool(changes)
        for rec in changes:
            if rec.k != "rec":
                literal_only = False
                continue
            for field, val, pos in rec.fields:
                col = schema.col(field)
                if col is None:
                    self.add("error", "FX-SCHEMA", f"{fname} writes '{field}' on {schema.name}, which is not in schemas/{schema.name}.csv (add "
                                                   "the column, run the importer, refresh the data source in Studio: PA-T27)", pos)
                    continue
                set_cols.add(col.name)
                if col.readonly:
                    self.add("error", "FX-PATCH", f"{fname} writes {schema.name}.{col.name}, which is read-only ({col.type}): SharePoint "
                                                  "rejects the save", pos)
                    continue
                self._value_type(val, col, schema.name, fname)
        if creating and literal_only:
            missing = [c.name for c in schema.columns.values() if c.required and not c.has_default and not c.readonly and c.name not in set_cols]
            if missing:
                self.add("warning", "FX-PATCH", f"{fname} creates an item in {schema.name} without the required column(s) "
                                                f"{', '.join(missing)}: SharePoint rejects it", n.s)

    def _value_type(self, val: Node, col: Column, lst: str, fname: str) -> None:
        kind = lit_kind(val)
        if kind is None or kind == "blank":
            return
        t, where = col.type, f"{fname} writes {lst}.{col.name}"
        bad = None
        if t in ("Choice",):
            if kind != "rec":
                bad = f"{where} ({t}) with a {kind}: a Choice column takes a record, {{Value: \"...\"}}"
            else:
                v = next((x for fn, x, _ in val.fields if fn == "Value"), None)
                if v is not None and v.k == "str" and col.choices and v.v not in col.choices:
                    bad = f"{where}: '{v.v}' is not one of its choices ({', '.join(col.choices)}) (T-11)"
        elif t in ("MultiChoice", "UserMulti", "LookupMulti"):
            if kind != "tbl":
                bad = f"{where} ({t}) with a {kind}: it takes a table of records"
        elif t == "User":
            if kind != "rec":
                bad = f"{where} (Person) with a {kind}: it takes a person record ({{Claims: \"i:0#.f|membership|\" & ..., ...}})"
        elif t in ("Number", "Currency", "Integer", "Counter"):
            if kind in ("bool", "rec", "tbl") or (kind == "str" and not (val.k == "str" and re.fullmatch(r"\s*-?\d+(\.\d+)?\s*", val.v))):
                bad = f"{where} ({t}) with a {kind}"
        elif t == "Boolean":
            if kind in ("str", "rec", "tbl"):
                bad = f"{where} (Yes/No) with a {kind}: use true or false"
        elif t == "DateTime":
            if kind in ("num", "bool", "rec", "tbl"):
                bad = f"{where} (Date) with a {kind}"
            elif kind == "str":
                self.add("warning", "FX-PATCH", f"{where} (Date) with text: convert it (DateValue/DateTimeValue) so the format is not "
                                                "left to the user's locale", val.s)
        elif t in ("Text", "Note", "URL"):
            if kind in ("rec", "tbl"):
                bad = f"{where} ({t}) with a {kind}"
        if bad:
            self.add("error", "FX-PATCH", bad, val.s)

    # ---- property literal types and token discipline (D11)
    def _literal_types(self, root: Node) -> None:
        prop, kind = self.f.prop, lit_kind(root)
        if prop == "Default" and (self.f.ctype or "").startswith("ModernDropdown") and root.k in ("name", "member", "str", "num"):
            self.add("error", "FX-TYPE", "the Default of a modern dropdown is a record from its Items, not text: Default: =LookUp(Items, Value = x) (PA-T34)", root.s)
        if self.f.kind not in ("control", "screen") or kind is None or kind == "blank":
            return
        if kind == "str" and root.k != "str":
            kind = "text expression"  # $"..." or a & b: text, but not a literal whose content can be read
        if prop in ENUM_PROPS:
            enum = ENUM_PROPS[prop]
            if kind in ("str", "num", "bool", "rec", "tbl"):
                self.add("error", "FX-TYPE", f"{prop} takes a {enum} value ({enum}.{sorted(STRICT_ENUMS[enum])[0]}), not a {kind}", root.s)
            return
        if prop.endswith("Color") or prop.endswith("Fill") or prop == "Fill":
            if kind in ("str", "num", "bool", "rec", "tbl"):
                self.add("error", "FX-TYPE", f"{prop} takes a colour (a token from App.Formulas), not a {kind}", root.s)
        elif prop in NUMBER_PROPS:
            if kind in ("bool", "rec", "tbl") or (kind == "str" and not re.fullmatch(r"\s*-?\d+(\.\d+)?\s*", root.v)):
                self.add("error", "FX-TYPE", f"{prop} takes a number, not a {kind}", root.s)
            elif kind == "str":
                self.add("warning", "FX-TYPE", f"{prop} takes a number: write ={root.v.strip()} without quotes", root.s)
        elif prop in BOOLEAN_PROPS:
            if kind in ("rec", "tbl") or (kind == "str" and root.v.strip().lower() not in ("true", "false")):
                self.add("error", "FX-TYPE", f"{prop} takes true or false, not a {kind}", root.s)
            elif kind in ("str", "num"):
                self.add("warning", "FX-TYPE", f"{prop} takes true or false: write it without quotes", root.s)
        elif prop == "Items" and kind in ("str", "num", "bool"):
            self.add("error", "FX-TYPE", f"Items takes a table, not a {kind}", root.s)
        elif prop in TEXT_PROPS and kind in ("rec", "tbl"):
            self.add("error", "FX-TYPE", f"{prop} takes text, not a {kind}", root.s)
        if prop in TEXT_PROPS and kind == "str":
            v = root.v
            if v == '"':
                self.add("warning", "FX-TEXT", "the text is a single \" character: =\"\"\"\" shows a quote mark; an empty text is =\"\"", root.s)
            elif self._looks_like_formula(v):
                self.add("warning", "FX-TEXT", f"\"{v[:50]}\" is shown as this text, not evaluated: remove the quotes to make it a formula", root.s)

    def _looks_like_formula(self, v: str) -> bool:
        """True when a text literal's content parses as Power Fx and calls a known function or reads a known name's property:
        `="User().FullName"` shows the words, not the name."""
        v = v.strip()
        if v.startswith("="):
            v = v[1:]
        if not re.search(r"[(.]", v) or " " in v.split("(")[0]:
            return False
        try:
            node, _ = parse(v)
        except FxSyntaxError:
            return False
        for n, _ in walk(node):
            if call_name(n) in self.cat["functions"] or call_name(n) in self.udfs:
                return True
            if n.k == "member" and n.obj.k == "name" and (n.obj.v in OBJECTS or n.obj.v in self.controls or n.obj.v in self.named):
                return True
        return False

    def _token_discipline(self, root: Node) -> None:
        if self.f.kind == "app" or self.f.file.endswith("App.pa.yaml"):
            return
        for n, _ in walk(root):
            if call_name(n) in ("RGBA", "ColorValue"):
                self.add("error", "FX-TOKEN", f"{call_name(n)}(...) on a screen: colours are design tokens from App.Formulas only (D11)", n.s)

    # ---- comments: acceptance criteria and suppressions
    def _comments(self, f: Formula) -> None:
        self.f = f
        p = f.parser
        if p is None:
            return
        f.ignores = []
        for c in p.comments:
            text = c.v
            m = re.search(r"\bfx-ignore\s+(FX-[A-Z]+)\b\s*(.*)", text)
            if m:
                code, reason = m.group(1), m.group(2).strip(" -")
                if code not in SUPPRESSIBLE:
                    self.add("error", "FX-IGNORE", f"fx-ignore {code}: only {', '.join(sorted(SUPPRESSIBLE))} may be suppressed", c.s)
                elif len(reason.split()) < 3:
                    self.add("error", "FX-IGNORE", f"fx-ignore {code} needs a reason of a few words (who agreed, and why)", c.s)
                else:
                    f.ignores.append((code, reason))
            if "TODO(AC" in text:
                self.add("error" if self.release else "warning", "FX-AC", f"stub left by /scaffold: {text.strip()[:60]}", c.s)
            for m in AC_NO_CHECK.finditer(text):
                self.add("warning", "FX-AC", f"{m.group(0)} has no check number: cite the check it implements, {m.group(0)}.1 (dev-standards §9)", c.s)
            for m in AC_LOOSE.finditer(text):
                if not AC_STRICT.match(m.group(0)) and not AC_NO_CHECK.match(m.group(0)):
                    self.add("warning", "FX-AC", f"'{m.group(0)}' is not an acceptance criterion ID (AC-<PROJECT>-NN.n), so the traceability check "
                                                 "cannot see it", c.s)
        for s in p.strings:
            txt = s.v if s.k == "str" else "".join(x[1] for x in s.v if x[0] == "t")
            if AC_STRICT.search(txt) or AC_NO_CHECK.search(txt):
                self.add("error", "FX-AC", "an acceptance-criterion ID is inside a text string, so users see it: put the // comment after the "
                                           "closing quote (and inside YAML quotes, if any)", s.s)
        empty = (f.ast is not None and f.ast.k == "empty") or (f.prop == "Formulas" and not f.entries)
        if empty and p.comments and f.prop != "Formulas":
            self.add("error" if f.behavior else "warning", "FX-AC",
                     "the whole formula is a comment, so it " + ("does nothing when it runs" if f.behavior else "gives a blank value") +
                     ": a // comment runs to the end of the line, so it goes after the formula", p.comments[0].s)
        if self.release:
            for n, _ in walk(f.ast) if f.ast is not None else []:
                if n.k == "name" and re.match(r"Mock[A-Z]|MockState$", n.v):
                    self.add("error", "FX-AC", f"mock data '{n.v}' is still used at release (/functionality-dev replaces it)", n.s)

    # ---- variables
    def _variables(self) -> None:
        for name, sets in sorted(self.globals.items()):
            kinds = {k for _, k, _ in sets if k not in (None, "blank")}
            if len(kinds) > 1:
                where = "; ".join(f"{f.owner}.{f.prop} sets {k}" for f, k, _ in sets if k not in (None, "blank"))
                f0, _, pos = sets[0]
                self.add("error", "FX-VAR", f"the global variable {name} is given different types ({where}): a variable has one type", pos, f=f0)
            if name not in self.reads:
                f0, _, pos = sets[0]
                self.add("warning", "FX-UNUSED", f"the global variable {name} is set but never read", pos, f=f0)
            if any(name in v for v in self.ctx.values()):
                f0, _, pos = sets[0]
                self.add("warning", "FX-VAR", f"{name} is both a global variable (Set) and a context variable (UpdateContext/Navigate): "
                                              "on that screen the context variable hides the global one", pos, f=f0)
            if name in self.collections:
                f0, _, pos = sets[0]
                self.add("error", "FX-VAR", f"{name} is both a variable (Set) and a collection (Collect/ClearCollect)", pos, f=f0)
        for screen, vars_ in sorted(self.ctx.items()):
            if screen not in self.screens:
                f0, _, pos = next(iter(vars_.values()))[0]
                self.add("error", "FX-NAME", f"Navigate({screen}, ...): there is no screen '{screen}'", pos, f=f0)
                continue
            for name, sets in sorted(vars_.items()):
                kinds = {k for _, k, _ in sets if k not in (None, "blank")}
                if len(kinds) > 1:
                    f0, _, pos = sets[0]
                    self.add("error", "FX-VAR", f"the context variable {name} on {screen} is given different types ({', '.join(sorted(kinds))})",
                             pos, f=f0)

    def _apply_suppressions(self) -> None:
        by_formula = {}
        for f in self.formulas:
            for code, reason in getattr(f, "ignores", []):
                by_formula.setdefault((f.file, f.owner, f.prop), []).append((code, reason))
        kept = []
        for fd in self.r.findings:
            rules = by_formula.get((fd.file, fd.owner, fd.prop), [])
            hit = next((reason for code, reason in rules if code == fd.code), None)
            if hit is not None:
                self.r.suppressed.append((fd, hit))
            else:
                kept.append(fd)
        self.r.findings = kept


class Scope:
    def __init__(self, parent: "Scope | None", names=None, columns: ListSchema | None = None, open_=False, alias=None, alias_list=None):
        self.parent, self.names, self.columns, self.open, self.alias, self.alias_list = parent, set(names or ()), columns, open_, alias, alias_list

    def find(self, name: str):
        s = self
        while s is not None:
            if s.alias and name == s.alias:
                return ("alias", s.alias_list)
            if name in s.names:
                return ("scope", name)
            if s.columns is not None and s.columns.col(name):
                return ("column", s.columns.name)
            s = s.parent
        return None

    def is_open(self) -> bool:
        s = self
        while s is not None:
            if s.open:
                return True
            s = s.parent
        return False

    def list_name(self) -> str | None:
        s = self
        while s is not None:
            if s.columns is not None:
                return s.columns.name
            s = s.parent
        return None


def lit_kind(n: Node) -> str | None:
    """The type of a literal value: num str bool rec tbl color blank, or None for any other expression."""
    if n.k == "num" or (n.k == "un" and n.op == "-" and n.x.k == "num"):
        return "num"
    if n.k in ("str", "istr"):
        return "str"
    if n.k == "bool":
        return "bool"
    if n.k == "rec":
        return "rec"
    if n.k == "tbl":
        return "tbl"
    if call_name(n) in ("RGBA", "ColorValue", "ColorFade"):
        return "color"
    if call_name(n) == "Blank":
        return "blank"
    if n.k == "bin" and n.op == "&":
        return "str"
    return None


def _maybe_table(n: Node) -> bool:
    if n.k in ("num", "str", "bool", "un", "bin", "pct", "istr"):
        return False
    if n.k == "member" and n.obj.k == "name" and n.obj.v in ("Self", "Parent"):
        return False
    return True


def check_app(app: str, yaml_texts: dict[str, str], **kw) -> Result:
    a = Analyzer(app, yaml_texts, **kw)
    res = a.run()
    res.flows_used = sorted(a.flows_used)
    return res


# =========================================================================== command line

def _selftest() -> int:
    """Every formula of the Studio-built sample app must parse with the stdlib parser AND with Microsoft's (when present), and the
    analyser must find no syntax, function, arity, behaviour, control-property or enumeration error in it: Studio opened it."""
    sys.path.insert(0, str(ROOT / "tools"))
    import pp  # noqa: E402
    bad = 0
    for label, folder in [("samples/powerapp", ROOT / "samples" / "powerapp")] + \
            [(a["source"], ROOT / a["source"]) for a in pp.load_config()["canvasApps"]]:
        texts = {f"Src/{p.name}": p.read_text(encoding="utf-8-sig") for p in sorted((folder / "Src").glob("*.pa.yaml"))}
        templates, datasources = pp.app_references(folder)
        kw = pp.formula_check_args(templates, datasources)
        if label.startswith("samples"):
            kw.update(schemas={}, flows={}, prefix=None)
        res = check_app(label, texts, **kw)
        studio_kinds = {"FX-SYNTAX", "FX-FUNC", "FX-ARITY", "FX-BEHAVIOR", "FX-CTRLPROP", "FX-ENUM", "FX-PARSER", "FX-NAME", "FX-THISITEM"}
        wrong = [f for f in res.findings if f.code in studio_kinds and label.startswith("samples")]
        print(f"{label}: {res.stats['formulas']} formulas, {res.stats['official']} confirmed by Microsoft's parser "
              f"{res.official_version or '(not available: ' + res.official_reason + ')'}; {len(res.errors)} error(s), {len(res.warnings)} warning(s)")
        by_code: dict[str, int] = {}
        for f in res.findings:
            by_code[f"{f.severity} {f.code}"] = by_code.get(f"{f.severity} {f.code}", 0) + 1
        if by_code:
            print("  by rule: " + ", ".join(f"{k} x{v}" for k, v in sorted(by_code.items())))
        for f in res.findings:
            if f in wrong or not label.startswith("samples") or "-v" in sys.argv:
                print(f"  {'FAIL' if f in wrong else f.severity.upper():5} {f.text()}")
        bad += len(wrong)
    print("OK" if not bad else f"{bad} finding(s) on a Studio-built app: the checker is wrong, fix it")
    return 1 if bad else 0


def _refresh_functions() -> int:
    dll, pwsh = find_powerfx_dll(), shutil.which("pwsh")
    if not dll or not pwsh:
        print("needs pac (Microsoft.PowerFx.Core.dll) and PowerShell 7 (pwsh)")
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "f.json"
        subprocess.run([pwsh, "-NoProfile", "-NonInteractive", "-File", str(FXPARSE), "-Dll", str(dll), "-DumpFunctions", "-Out", str(out)], check=True)
        dump = json.loads(out.read_text(encoding="utf-8-sig"))
    cat = json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))
    ns_names = {f["name"] for v in cat["namespaces"].values() for f in v}
    canvas = {f["name"] for f in cat["canvas"]["functions"]}
    cat["core"] = {"source": f"Microsoft.PowerFx.Core {dump['version']} + Interpreter mutation functions, from {dll.parent}",
                   "functions": [f for f in dump["functions"] if f["name"] not in ns_names]}
    clash = canvas & {f["name"] for f in cat["core"]["functions"]}
    if clash:
        cat["canvas"]["functions"] = [f for f in cat["canvas"]["functions"] if f["name"] not in clash]
        print(f"now in the engine, removed from 'canvas': {', '.join(sorted(clash))}")
    CATALOGUE_PATH.write_text(json.dumps(cat, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(cat['core']['functions'])} functions from Microsoft.PowerFx.Core {dump['version']}")
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    if "--refresh-functions" in sys.argv:
        sys.exit(_refresh_functions())
    print(__doc__)
