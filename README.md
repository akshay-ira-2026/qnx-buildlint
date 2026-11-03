# buildlint: catch QNX image buildfile mistakes before mkifs does

QNX Global Hackathon 2026 entry, Developer Tooling category.

A QNX OS 8.0 image is described by a buildfile that `mkifs` turns into a bootable image. A typo there
(a missing kernel, a bad `perms=`, an unclosed inline block, a `waitfor` with no timeout) usually shows up
only as an image that will not boot. `buildlint` is a host tool that reads the buildfile first and tells you,
line by line, what is wrong and how to fix it, and can print a plain-English map of what the image will contain.

## Use
```
pip install .
buildlint my.build                 # lint, exit 1 on errors
buildlint --check-host --search $QNX_TARGET/aarch64le/boot/sys my.build
buildlint --explain my.build       # what goes into the image
buildlint --json my.build          # for CI
```

## Checks
- E001 broken syntax (unclosed `[` or inline `{`)
- E102 `virtual=` without a boot format
- E103 invalid `perms=` / `dperms=`
- E201 the same target defined twice (the later one silently wins)
- E204 symlink with no target
- E301 host file missing from the search path
- E401 bootable image with no `procnto` kernel
- W101 unknown attribute, W104 non-numeric uid/gid
- W202 empty inline file, W203 script that is not executable
- W402 bootable image with no `[+script]`
- I502 `waitfor` without a timeout, I503 resource manager in the foreground

## Demo
`examples/run.sh` lints a good Raspberry Pi 4 buildfile, a broken one, and explains the good one.

## Tests
`python3 -m pytest tests` (7 tests).

## Licence
Apache-2.0
