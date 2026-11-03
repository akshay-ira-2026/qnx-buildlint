"""Lint rules for QNX buildfiles. Each finding: line, level, code, message, hint."""
from dataclasses import dataclass
import os, re
from .parser import parse

@dataclass
class Finding:
    line: int
    level: str
    code: str
    message: str
    hint: str = ""
    def __str__(self):
        h = f"\n    hint: {self.hint}" if self.hint else ""
        return f"{self.line}: {self.level} {self.code} {self.message}{h}"

KNOWN_ATTRS = {"virtual","search","prefix","type","perms","uid","gid","dperms","+script","script",
 "data","code","physical","image","ram","rom","compress","keeplinked","autolink","module","chain",
 "filter","followlink","pagesize","linker","optional","newpath","mtime","dupignore","bigendian","+compress",
 "-optional","+optional","attr","uip","cd","pri","+keeplinked","+raw","raw","hostname","sym","+sym"}
PERMS_RE = re.compile(r"^(0?[0-7]{3,4}|[ugoa]*[+-=][rwxst]+(,[ugoa]*[+-=][rwxst]+)*)$")
STARTUP_HINTS = ("startup-", "procnto")

def lint(text, search_dirs=None, check_host=False):
    entries, errors = parse(text)
    out = [Finding(n, "error", "E001", m) for n, m in errors]
    seen = {}
    has_virtual = False
    has_procnto = False
    has_script = False
    for e in entries:
        for k in e.attrs:
            if k not in KNOWN_ATTRS and k.lstrip("+-") not in KNOWN_ATTRS:
                out.append(Finding(e.line, "warning", "W101", f"unknown attribute '{k}'",
                                   "check spelling against the mkifs attribute list"))
        if "virtual" in e.attrs:
            has_virtual = True
            v = str(e.attrs["virtual"])
            if "," not in v:
                out.append(Finding(e.line, "error", "E102", f"virtual={v} lacks the boot type (cpu,boot-type)",
                                   "e.g. [virtual=aarch64le,elf] or [virtual=x86_64,multiboot]"))
        for pk in ("perms", "dperms"):
            if pk in e.attrs and not PERMS_RE.match(str(e.attrs[pk])):
                out.append(Finding(e.line, "error", "E103", f"{pk}={e.attrs[pk]} is not a valid mode",
                                   "use octal like 0755 or symbolic like u+x"))
        for idk in ("uid", "gid"):
            if idk in e.attrs and not str(e.attrs[idk]).lstrip("*").isdigit():
                out.append(Finding(e.line, "warning", "W104", f"{idk}={e.attrs[idk]} is not numeric",
                                   "mkifs expects a numeric id"))
        if e.kind in ("file", "inline", "link", "dir") and e.target:
            if e.target in seen and e.kind != "dir":
                out.append(Finding(e.line, "error", "E201",
                                   f"'{e.target}' already defined on line {seen[e.target]}",
                                   "the later entry silently wins in the image"))
            seen.setdefault(e.target, e.line)
            if any(e.target.split("/")[-1].startswith(p) for p in STARTUP_HINTS):
                if "procnto" in e.target: has_procnto = True
            if e.target.endswith("procnto-smp-instr") or e.host.endswith("procnto-smp-instr"):
                has_procnto = True
        if e.kind == "inline":
            if e.attrs.get("script") or e.attrs.get("+script"):
                has_script = True
                out += _lint_script(e)
            if not e.body.strip():
                out.append(Finding(e.line, "warning", "W202", f"inline file '{e.target}' is empty"))
            if e.target.endswith(".sh") or e.body.startswith("#!"):
                if not str(e.attrs.get("perms", "")).endswith(("5", "7")):
                    out.append(Finding(e.line, "warning", "W203", f"script '{e.target}' may not be executable",
                                       "add [perms=0755]"))
        if e.kind == "link" and not e.host:
            out.append(Finding(e.line, "error", "E204", f"link '{e.target}' has no target"))
        if check_host and e.kind == "file" and e.host and not e.host.startswith("/proc"):
            if not _find_host(e.host, search_dirs or []) and not e.attrs.get("optional"):
                out.append(Finding(e.line, "error", "E301", f"host file '{e.host}' not found in search path",
                                   "set [search=...] or MKIFS_PATH, or mark [+optional]"))
    for e in entries:
        if e.kind in ("file","link") and "procnto" in (e.target + e.host):
            has_procnto = True
        if e.kind == "inline" and "procnto" in e.body:
            has_procnto = True
    if has_virtual and not has_procnto:
        out.append(Finding(1, "error", "E401", "bootable image (virtual=) has no procnto kernel",
                           "add procnto-smp-instr after the startup-* line"))
    if has_virtual and not has_script:
        out.append(Finding(1, "warning", "W402", "bootable image has no [+script] startup script",
                           "add [+script] .script = { ... } to start drivers and a shell"))
    return sorted(out, key=lambda f: (f.line, f.code))

def _lint_script(e):
    out = []
    started = set()
    for off, l in enumerate(e.body.splitlines(), start=1):
        s = l.strip()
        if not s or s.startswith("#"):
            continue
        ln = e.line + off
        if s.startswith("waitfor"):
            parts = s.split()
            if len(parts) < 2:
                out.append(Finding(ln, "error", "E501", "waitfor needs a path"))
            elif len(parts) == 2:
                out.append(Finding(ln, "info", "I502", f"waitfor {parts[1]} has no timeout",
                                   "add seconds, e.g. 'waitfor /dev/sd0 5', so boot doesn't hang"))
        if re.match(r"^(devc-|devb-|io-sock|devs-|pipe|slogger2|random)", s.split()[0] if s.split() else ""):
            started.add(s.split()[0])
            if not s.rstrip().endswith("&") and s.split()[0].startswith(("devb-","io-sock","slogger2","pipe","random")):
                out.append(Finding(ln, "info", "I503", f"'{s.split()[0]}' runs in the foreground",
                                   "resource managers usually daemonise themselves; check it returns"))
    return out

def _find_host(host, dirs):
    if os.path.isabs(host):
        return os.path.exists(host)
    env = os.environ.get("MKIFS_PATH", "")
    for d in list(dirs) + [p for p in env.split(":") if p]:
        if os.path.exists(os.path.join(d, host)):
            return True
    return False
