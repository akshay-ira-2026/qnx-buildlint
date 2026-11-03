"""Parse QNX image buildfiles into entries.

Buildfile grammar (mkifs, simplified):
  [attr attr=val]            -> attributes; alone on a line they become the defaults
  [attr] target=host         -> a file mapping with per-file attributes
  [attr] target={ ... }      -> an inline file (closing brace on its own line)
  target                     -> a host file taken from the search path
  # comment
"""
from dataclasses import dataclass, field
import re, shlex

@dataclass
class Entry:
    line: int
    kind: str            # 'defaults' | 'file' | 'inline' | 'link' | 'dir'
    target: str = ""
    host: str = ""
    attrs: dict = field(default_factory=dict)
    body: str = ""

ATTR_RE = re.compile(r"^\s*\[([^\]]*)\]\s*")

def _attrs(text):
    out = {}
    for tok in shlex.split(text, posix=True):
        neg = tok.startswith("-")
        pos = tok.startswith("+")
        tok = tok.lstrip("+-")
        if "=" in tok:
            k, v = tok.split("=", 1)
            out[k] = v
        else:
            out[tok] = not neg
            _ = pos
    return out

def parse(text):
    entries, errors = [], []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]; n = i + 1
        s = raw.strip()
        i += 1
        if not s or s.startswith("#"):
            continue
        attrs = {}
        while True:
            m = ATTR_RE.match(s)
            if not m:
                break
            try:
                attrs.update(_attrs(m.group(1)))
            except ValueError as e:
                errors.append((n, f"bad attribute list: {e}"))
            s = s[m.end():]
        if s.startswith("[") and "]" not in s:
            errors.append((n, "attribute bracket '[' is never closed"))
            continue
        if not s:
            entries.append(Entry(n, "defaults", attrs=attrs)); continue
        if "=" in s:
            target, host = s.split("=", 1)
            target, host = target.strip(), host.strip()
            if host.startswith("{"):
                body_lines = [host[1:]] if host[1:].strip() else []
                closed = False
                while i < len(lines):
                    l = lines[i]; i += 1
                    if l.strip() == "}":
                        closed = True; break
                    body_lines.append(l)
                if not closed:
                    errors.append((n, f"inline file '{target}' has no closing '}}'"))
                kind = "inline"
                entries.append(Entry(n, kind, target, "", attrs, "\n".join(body_lines)))
            else:
                kind = "link" if attrs.get("type") == "link" else "file"
                entries.append(Entry(n, kind, target, host, attrs))
        else:
            kind = "dir" if attrs.get("type") == "dir" else "file"
            entries.append(Entry(n, kind, s, s, attrs))
    return entries, errors
