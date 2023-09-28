SOURCE_FILES := $(shell find plugins tests -type f -name '*.py')
MARKDOWN_FILES := README.md
COLLECTION_FILES := $(SOURCE_FILES) galaxy.yml meta/runtime.yml

all: build

build:
	mkdir build
	ansible-galaxy collection build --output-path build/colin_nolan-rpi.tar.gz

lint: lint-code lint-markdown

lint-code:
	black --check $(SOURCE_FILES)
	isort --check $(SOURCE_FILES)

lint-markdown:
	mdformat --check $(MARKDOWN_FILES)

format: format-code format-markdown
fmt: format

format-code:
	black $(SOURCE_FILES)
	isort $(SOURCE_FILES)

format-markdown:
	mdformat $(MARKDOWN_FILES)	

test:
	pytest -v

.PHONY: all build lint lint-code lint-markdown format fmt format-code format-markdown test
