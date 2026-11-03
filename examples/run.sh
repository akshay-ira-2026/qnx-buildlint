#!/bin/sh
python3 -m buildlint tests/fixtures/good.build
python3 -m buildlint tests/fixtures/bad.build || true
python3 -m buildlint --explain tests/fixtures/good.build
