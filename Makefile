pyenv: .python-version

.python-version: setup.cfg
	if [ -z "`pyenv virtualenvs | grep nefelibata`" ]; then\
	    pyenv virtualenv nefelibata;\
	fi
	if [ ! -f .python-version ]; then\
	    pyenv local nefelibata;\
	fi
	pip install -e '.[testing]'
	touch .python-version

test: pyenv
	pytest --cov=src/nefelibata -vv tests/ --doctest-modules src/nefelibata

clean:
	pyenv virtualenv-delete nefelibata

spellcheck:
	codespell -S "*.json" src/nefelibata docs/*rst tests templates

requirements.txt: .python-version
	pip install --upgrade pip
	pip-compile --no-annotate

check:
	pre-commit run --all-files
