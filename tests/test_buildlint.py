import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from buildlint import lint, parse
from buildlint.explain import explain
H = os.path.dirname(__file__)
read = lambda n: open(os.path.join(H, "fixtures", n)).read()

def codes(t): return {f.code for f in lint(t)}

def test_good_has_no_errors():
    f = lint(read("good.build"))
    assert not [x for x in f if x.level == "error"], f

def test_good_parses_inline_and_link():
    e, err = parse(read("good.build"))
    kinds = [x.kind for x in e]
    assert "inline" in kinds and "link" in kinds and not err

def test_bad_catches_everything():
    c = codes(read("bad.build"))
    for want in ["E001", "E102", "E103", "W101", "W104", "E201", "E401", "W402"]:
        assert want in c, (want, c)

def test_waitfor_without_timeout():
    t = "[+script] .script = {\nwaitfor /dev/sd0\n}\n"
    assert "I502" in codes(t)

def test_explain_lists_symlink():
    out = explain(read("good.build"))
    assert "symlink /bin/sh -> /proc/boot/ksh" in out and "aarch64le" in out

def test_cli_exit_codes(tmp_path=None):
    from buildlint.__main__ import main
    assert main([os.path.join(H, "fixtures", "good.build")]) == 0
    assert main([os.path.join(H, "fixtures", "bad.build")]) == 1

def test_check_host(tmp_path=None):
    import tempfile
    d = tempfile.mkdtemp(); open(os.path.join(d, "ksh"), "w").close()
    t = "[perms=0755] ksh\nmissing-bin\n"
    f = lint(t, [d], check_host=True)
    assert [x.code for x in f] == ["E301"] and f[0].line == 2
