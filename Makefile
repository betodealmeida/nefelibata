venv: venv/.touchfile

venv/.touchfile: setup.cfg
	test -d venv || python3 -m venv venv
	. venv/bin/activate
	pip install -e '.[testing]'
	touch venv/.touchfile

test: venv
	pytest --cov=src/nefelibata -vv tests/ --doctest-modules src/nefelibata

clean:
	rm -rf venv

spellcheck:
	codespell -S "*.json" src/nefelibata docs/*rst tests templates

check:
	pre-commit run --all-files
