PYTHON := python3.5

# ---

develop: bin/python setup.py
	bin/python setup.py develop

dist: bin/python setup.py README
	bin/python setup.py egg_info sdist

upload: bin/python setup.py README
	bin/python setup.py egg_info sdist upload

test: bin/tox
	@bin/tox

clean:
	$(RM) -r bin build dist include lib local share
	find . -name '*.py[co]' -print0 | xargs -r0 $(RM) -r
	find . -name '__pycache__' -print0 | xargs -r0 $(RM) -r
	find . -name '*.egg' -print0 | xargs -r0 $(RM) -r
	find . -name '*.egg-info' -print0 | xargs -r0 $(RM) -r
	find . -name '*~' -print0 | xargs -r0 $(RM)
	$(RM) -r .eggs .tox .coverage TAGS tags

# ---

README: README.md
	pandoc --from markdown --to rst --output $@ $^

docs: bin/mkdocs
	bin/mkdocs build --config-file doc.yaml --clean --strict

# ---

bin/tox: bin/pip
	bin/pip install --quiet --ignore-installed tox

bin/python bin/pip:
	virtualenv --python=$(PYTHON) --quiet $(CURDIR)

bin/mkdocs: bin/pip
	bin/pip install --quiet --ignore-installed "mkdocs >= 0.14.0"

# ---

.PHONY: develop dist docs test clean
