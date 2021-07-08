#!/bin/sh
exclude=""
for i in COPYING README.md setup.py data deploy docs guis tests utils; do
	exclude="$exclude :(exclude)../$i"
done
(
echo "# Change log"
git log --pretty="* [%h](https://github.com/HuidaeCho/projpicker/commit/%h) %d %s %cd" --decorate=full $exclude |
sed '
/(HEAD/{
	s/^\(.*\) (HEAD.*HEAD) \(.* \(\([^ ]\+ \)\{5\}[^ ]\+\)\)$/\n## HEAD\n\3\n\n\1 \2/
}
/(tag: refs\/tags/{
	s/^\(.*(tag: refs\/tags\/\([^)]*\)).* \(\([^ ]\+ \)\{5\}[^ ]\+\)\)$/\n## \2\n\3\n\n\1/
}
s/\( [^ ]\+\)\{6\}$//
s/_/\\_/g
'
) > ../projpicker/ChangeLog.md
