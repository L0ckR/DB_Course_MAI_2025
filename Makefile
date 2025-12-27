LATEX ?= xelatex
TEX_SRC := docs/report.tex
PDF_OUT := docs/report.pdf

.PHONY: report clean

report:
	$(LATEX) -interaction=nonstopmode -halt-on-error -output-directory=docs $(TEX_SRC)
	$(LATEX) -interaction=nonstopmode -halt-on-error -output-directory=docs $(TEX_SRC)

clean:
	$(RM) docs/*.aux docs/*.log docs/*.out docs/*.toc docs/*.pdf
