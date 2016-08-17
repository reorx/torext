.PHONY: build coverage

build:
	@python setup.py build

test:
	@nosetests -v

lint:
	@flake8 terminal tests

coverage:
	@rm -f .coverage
	@nosetests --with-coverage --cover-package=torext

clean: clean-build clean-pyc

clean-build:
	@rm -rf build/
	@rm -rf dist/
	@rm -rf *.egg-info

clean-pyc:
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +

publish:
	python setup.py sdist bdist_wheel upload
