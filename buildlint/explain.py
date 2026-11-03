"""Turn a buildfile into a plain-English map of what the image will contain."""
from .parser import parse

def explain(text):
    entries, _ = parse(text)
    lines, defaults = [], {}
    for e in entries:
        if e.kind == "defaults":
            defaults.update(e.attrs)
            if "virtual" in e.attrs:
                cpu, _, boot = str(e.attrs["virtual"]).partition(",")
                lines.append(f"line {e.line}: bootable image for {cpu}, boot format {boot or '?'}")
            else:
                lines.append(f"line {e.line}: defaults now {dict(defaults)}")
        elif e.kind == "inline" and "virtual" in e.attrs:
            cpu, _, boot = str(e.attrs["virtual"]).partition(",")
            k = "kernel" if "procnto" in e.body else "no kernel"
            lines.append(f"line {e.line}: bootable image for {cpu}, boot format {boot or '?'}, bootstrap {e.target} ({k})")
        elif e.kind == "inline":
            what = "startup script" if (e.attrs.get("script") or e.attrs.get("+script")) else "inline file"
            lines.append(f"line {e.line}: {what} {e.target} ({len(e.body.splitlines())} lines)")
        elif e.kind == "link":
            lines.append(f"line {e.line}: symlink {e.target} -> {e.host}")
        elif e.kind == "dir":
            lines.append(f"line {e.line}: directory {e.target}")
        else:
            src = e.host if e.host != e.target else "search path"
            perms = e.attrs.get("perms") or defaults.get("perms")
            lines.append(f"line {e.line}: file {e.target} from {src}" + (f", perms {perms}" if perms else ""))
    return "\n".join(lines)
