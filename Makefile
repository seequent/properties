PACKAGE_NAME=properties

.PHONY: install publish coverage-run coverage lint lint-tml graph docs tests

install:
	python setup.py install

publish:
	python setup.py sdist upload

docs:
	cd docs && make html

coverage-run:
	nosetests --logging-level=INFO --with-coverage --cover-package=$(PACKAGE_NAME) --cover-html

coverage: coverage-run
	open cover/index.html

lint:
	pylint $(PACKAGE_NAME)

lint-html:
	pylint --output-format=html $(PACKAGE_NAME) > pylint.html

graphs:
	pyreverse -my -A -o pdf -p $(PACKAGE_NAME) $(PACKAGE_NAME)/**.py $(PACKAGE_NAME)/**/**.py

tests:
	nosetests --logging-level=INFO --with-coverage --cover-package=$(PACKAGE_NAME)
	make lint
