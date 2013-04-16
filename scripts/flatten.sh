#!/usr/local/bin/zsh
for x in `ls *.pdf`
do
  pdftk $x output _$x flatten
done
