import argparse, json, sys
from .rules import lint
from .explain import explain

def main(argv=None):
    ap = argparse.ArgumentParser(prog="buildlint", description="Lint and explain QNX OS 8.0 image buildfiles")
    ap.add_argument("buildfile")
    ap.add_argument("--search", action="append", default=[], help="host search dir (like mkifs -r)")
    ap.add_argument("--check-host", action="store_true", help="verify host files exist")
    ap.add_argument("--explain", action="store_true", help="print what the image will contain")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    text = open(a.buildfile, encoding="utf-8").read()
    if a.explain:
        print(explain(text)); return 0
    f = lint(text, a.search, a.check_host)
    if a.json:
        print(json.dumps([x.__dict__ for x in f], indent=2))
    else:
        for x in f: print(f"{a.buildfile}:{x}")
        print(f"{sum(x.level=='error' for x in f)} errors, {sum(x.level=='warning' for x in f)} warnings")
    return 1 if any(x.level == "error" for x in f) else 0

if __name__ == "__main__":
    sys.exit(main())
