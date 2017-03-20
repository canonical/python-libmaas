<h1>Releasing a new version of <em>python-libmaas</em></h1>

1. Clean and test:

        make clean
        make test

1. If you didn't `make clean` just now, do it! Without it the [PyPI][]
   uploads may be built incorrectly.

1. Bump version in ``setup.py``, merge to _master_.

1. Tag _master_:

        git tag --sign ${version} --message "Release ${version}."
        git push origin --tags

1. Build and push docs to [GitHub][docs]:

        make docs-to-github

1. Build and push source and wheel to [PyPI][]:

        make upload


[docs]: http://maas.github.io/python-libmaas/
[pypi]: https://pypi.python.org/pypi/python-libmaas
