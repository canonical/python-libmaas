python := python3
snapcraft := SNAPCRAFT_BUILD_INFO=1 /snap/bin/snapcraft

# ---

install-dependencies:
	if [ -x /usr/bin/snap ]; then sudo snap install --classic snapcraft; fi

# ---

develop: bin/python setup.py
	bin/python setup.py develop

dist: bin/python setup.py README
	bin/python setup.py sdist bdist_wheel

upload: bin/python bin/twine setup.py README
	bin/python setup.py sdist bdist_wheel
	bin/twine upload dist/*

test: bin/tox
	@bin/tox

integrate: bin/tox
	@bin/tox -e integrate

format: bin/tox
	@bin/tox -e format,imports

lint: bin/tox
	@bin/tox -e lint,imports

clean:
	$(RM) -r bin build dist include lib local share
	find . -name '*.py[co]' -print0 | xargs -r0 $(RM) -r
	find . -name '__pycache__' -print0 | xargs -r0 $(RM) -r
	find . -name '*.egg' -print0 | xargs -r0 $(RM) -r
	find . -name '*.egg-info' -print0 | xargs -r0 $(RM) -r
	find . -name '*~' -print0 | xargs -r0 $(RM)
	$(RM) -r .eggs .tox .coverage TAGS tags
	$(RM) pip-selfcheck.json

# ---

snap-clean:
	$(snapcraft) clean

snap:
	$(snapcraft)

# ---

README: README.md
	pandoc --from markdown --to rst --output $@ $^

docs: bin/mkdocs
	bin/mkdocs build --config-file doc.yaml --clean --strict

docs-to-github: bin/mkdocs
	bin/mkdocs gh-deploy --config-file doc.yaml --clean

# ---

bin/tox: bin/pip
	bin/pip install --quiet --ignore-installed tox

bin/python bin/pip:
	virtualenv --python=$(python) --quiet $(CURDIR)

bin/mkdocs: bin/pip
	bin/pip install --quiet --ignore-installed "mkdocs >= 0.14.0"

bin/twine: bin/pip
	bin/pip install --quiet --ignore-installed twine

# ---

api-json-raw := $(wildcard maas/client/bones/testing/*.raw.json)
api-json := $(patsubst %.raw.json,%.json,$(api-json-raw))

pretty: $(api-json)

%.json: %.pretty.json
	cp $^ $@

%.pretty.json: %.raw.json
	scripts/prettify-api-desc-doc < $^ > $@

# ---

.PHONY: install-dependencies develop dist docs docs-to-github test integrate lint clean pretty snap snap-clean
