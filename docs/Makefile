# Makefile for Sphinx documentation

# You can set these variables to customize the behavior of Sphinx
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SOURCEDIR     = source
BUILDDIR      = _build

# Build the HTML output of your documentation
html:
	$(SPHINXBUILD) -M html $(SOURCEDIR) $(BUILDDIR) $(SPHINXOPTS)

# Build the LaTeX output of your documentation
latex:
	$(SPHINXBUILD) -M latex $(SOURCEDIR) $(BUILDDIR) $(SPHINXOPTS)

# Build the PDF output of your documentation
pdf:
	$(SPHINXBUILD) -M latexpdf $(SOURCEDIR) $(BUILDDIR) $(SPHINXOPTS)

# Build the epub output of your documentation
epub:
	$(SPHINXBUILD) -M epub $(SOURCEDIR) $(BUILDDIR) $(SPHINXOPTS)

# Clean the build directory
clean:
	rm -rf $(BUILDDIR)/*

.PHONY: help clean html latex pdf epub

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  html      to build the HTML output of the documentation"
	@echo "  latex     to build the LaTeX output of the documentation"
	@echo "  pdf       to build the PDF output of the documentation"
	@echo "  epub      to build the epub output of the documentation"
	@echo "  clean     to clean the build directory"
