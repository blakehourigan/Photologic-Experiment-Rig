#/bin/bash

rm control-software-guide.log control-software-guide.aux control-software-guide.out control-software-guide.pdf

pdflatex control-software-guide.tex 
pdflatex control-software-guide.tex 
pdflatex control-software-guide.tex 

firefox control-software-guide.pdf



