SOURCE_FILES := $(shell find plugins tests -type f -name '*.py')
MARKDOWN_FILES := README.md CHANGELOG.md
COLLECTION_FILES := $(SOURCE_FILES) galaxy.yml meta/runtime.yml
BUILD_DIRECTORY := build
DISTRIBUTABLE := $(BUILD_DIRECTORY)/colin_nolan-rpi.tar.gz

all: build

build: $(DISTRIBUTABLE) 
$(DISTRIBUTABLE): $(COLLECTION_FILES)
	build_directory="$(BUILD_DIRECTORY)/$${RANDOM}$${RANDOM}"; \
	mkdir -p "$${build_directory}"; \
	ansible-galaxy collection build --force --output-path "$${build_directory}"; \
	mv "$${build_directory}"/*.tar.gz "$(DISTRIBUTABLE)"; \
	rm -r "$${build_directory}"

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
