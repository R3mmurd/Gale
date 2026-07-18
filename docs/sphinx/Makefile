# Minimal makefile for Sphinx documentation.
#
# Guide pages under source/examples/ and the API reference under
# source/api/ are generated, not committed: `prepare` regenerates them
# from ../examples/*.rst (this repo's existing example guides,
# stripped of their "back to README" backlink, which doesn't resolve
# from a standalone doc site) and from the gale package's docstrings,
# so they always match the checked-out commit.

SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SPHINXAPIDOC  ?= sphinx-apidoc
SOURCEDIR     = source
BUILDDIR      = build
EXAMPLESDIR   = ../examples
GALEPKG       = ../../gale

.PHONY: help clean prepare html

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

clean:
	rm -rf "$(BUILDDIR)" "$(SOURCEDIR)/examples" "$(SOURCEDIR)/api"

prepare:
	mkdir -p "$(SOURCEDIR)/examples"
	rm -f "$(SOURCEDIR)"/examples/*.rst
	for f in "$(EXAMPLESDIR)"/*.rst; do \
		tail -n +2 "$$f" > "$(SOURCEDIR)/examples/$$(basename "$$f")"; \
	done
	$(SPHINXAPIDOC) -o "$(SOURCEDIR)/api" "$(GALEPKG)" --separate --module-first -f
	rm -f "$(SOURCEDIR)/api/modules.rst"

html: prepare
	@$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) $(O)
