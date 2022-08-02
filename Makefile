### Defensive settings for make:
#     https://tech.davis-hansson.com/p/make/
SHELL:=bash
.ONESHELL:
.SHELLFLAGS:=-xeu -o pipefail -O inherit_errexit -c
.SILENT:
.DELETE_ON_ERROR:
MAKEFLAGS+=--warn-undefined-variables
MAKEFLAGS+=--no-builtin-rules

CURRENT_USER=$$(whoami)

# We like colors
# From: https://coderwall.com/p/izxssa/colored-makefile-for-golang-projects
RED=`tput setaf 1`
GREEN=`tput setaf 2`
RESET=`tput sgr0`
YELLOW=`tput setaf 3`

PLONE5=5.2.7
PLONE6=6.0.0a4

PACKAGE_NAME=kitconcept.contentcreator
PACKAGE_PATH=src/
CHECK_PATH=$(PACKAGE_PATH) setup.py

CODE_QUALITY_VERSION=1.0.1
LINT=docker run --rm -v "$(PWD)":/github/workspace plone/code-quality:${CODE_QUALITY_VERSION} check
FORMAT=docker run --rm -v "${PWD}":/github/workspace plone/code-quality:${CODE_QUALITY_VERSION} format

# Add the following 'help' target to your Makefile
# And add help text after each target name starting with '\#\#'
.PHONY: help
help: ## This help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

bin/pip:
	@echo "$(GREEN)==> Setup Virtual Env$(RESET)"
	python3 -m venv .
	bin/pip install -U pip wheel

.PHONY: build-plone-5.2
build-plone-5.2: bin/pip ## Build Plone 5.2
	@echo "$(GREEN)==> Build with Plone 5.2$(RESET)"
	bin/pip install Plone plone.app.testing -c https://dist.plone.org/release/$(PLONE5)/constraints.txt
	bin/pip install -e ".[test]"
	bin/mkwsgiinstance -d . -u admin:admin

.PHONY: build-plone-6.0
build-plone-6.0: bin/pip ## Build Plone 6.0
	@echo "$(GREEN)==> Build with Plone 6.0$(RESET)"
	bin/pip install Plone plone.app.testing -c https://dist.plone.org/release/$(PLONE6)/constraints.txt
	bin/pip install -e ".[test]"
	bin/mkwsgiinstance -d . -u admin:admin

.PHONY: build
build: build-plone-6.0 ## Build Plone 6.0

.PHONY: clean
clean: ## Remove old virtualenv and creates a new one
	@echo "$(RED)==> Cleaning environment and build$(RESET)"
	rm -rf bin lib lib64 include share etc var inituser pyvenv.cfg .installed.cfg

.PHONY: format
format:  ## Format the codebase according to our standards
	$(FORMAT) "${PACKAGE_PATH}"
	sudo chown -R ${CURRENT_USER}: *

.PHONY: lint
lint: lint-isort lint-black lint-flake8 lint-zpretty lint-pyroma ## check code style

.PHONY: lint-black
lint-black: ## validate black formating
	$(LINT) black "$(CHECK_PATH)"

.PHONY: lint-flake8
lint-flake8: ## validate black formating
	$(LINT) flake8 "$(CHECK_PATH)"

.PHONY: lint-isort
lint-isort: ## validate using isort
	$(LINT) isort "$(CHECK_PATH)"

.PHONY: lint-zpretty
lint-zpretty: ## validate ZCML/XML using zpretty
	$(LINT) zpretty "$(PACKAGE_PATH)"

.PHONY: lint-pyroma
lint-pyroma: ## validate using pyroma
	$(LINT) pyroma ./

.PHONY: test
test: ## run tests
	PYTHONWARNINGS=ignore ./bin/zope-testrunner --auto-color --auto-progress --test-path $(PACKAGE_PATH)

.PHONY: start
start: ## Start a Plone instance on localhost:8080
	PYTHONWARNINGS=ignore ./bin/runwsgi etc/zope.ini
