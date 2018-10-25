@echo off

pdflatex %1
biber %1
pdflatex %1
pdflatex %1
::pdflatex %1.tex
::pdflatex %1.tex

del %1.aux
del %1.bbl
del %1.blg
del %1.dvi
::del %1.log
del %1.nav
del %1.out
del %1.ps
del %1.snm
del %1.toc