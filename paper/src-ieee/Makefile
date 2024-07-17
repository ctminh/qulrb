TEX = latexmk -g -pdf -bibtex
MAIN = main

.PHONY : default clean

default :	
	${TEX} ${MAIN}

clean:
	-rm -f *.aux *.log *.nav *.out *.snm *.toc *.vrb *.auxlock ${MAIN}.pdf *.synctex.gz *.run.xml *.bbl *.bcf *.blg *.lof *.fdb_latexmk *.fls *.cb *.cb2
	-rm -f *.bak *.~ *.dvi
