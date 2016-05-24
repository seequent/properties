
.PHONY: install publish test

install:
    python setup.py install

publish:
    python setup.py sdist upload

test:
    nosetests
