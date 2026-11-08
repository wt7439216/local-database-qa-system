# P5: one command for every engineering gate.
# Windows without `make`: use `powershell -File scripts/check.ps1` instead.
PYTHON ?= python

.PHONY: check check-full build build-plan test lint contract smoke clean activate

check:
	$(PYTHON) -X utf8 scripts/verify_all.py

check-full:
	$(PYTHON) -X utf8 scripts/verify_all.py --full

test:
	$(PYTHON) -B -m unittest discover -v

lint:
	$(PYTHON) -m ruff check core desktop scripts tests

contract:
	$(PYTHON) -X utf8 scripts/export_openapi.py
	$(PYTHON) -X utf8 scripts/capture_contract.py --backend legacy
	$(PYTHON) -X utf8 scripts/capture_contract.py --backend modern

build-plan:
	$(PYTHON) -X utf8 scripts/build.py --plan

build:
	$(PYTHON) -X utf8 scripts/build.py

activate:
	$(PYTHON) -X utf8 scripts/activate_candidate.py --bundle-root runtime/LocalDatabaseQA

smoke:
	$(PYTHON) -X utf8 scripts/startup_smoke.py

clean:
	-$(PYTHON) -c "import shutil,pathlib; [shutil.rmtree(p,ignore_errors=True) for p in (pathlib.Path('.pytest_cache'),pathlib.Path('.ruff_cache'),pathlib.Path('.hypothesis'))]"
