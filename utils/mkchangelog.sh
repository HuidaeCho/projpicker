#!/bin/sh
if [ "$1" = "-w" ]; then
	file=../projpicker/ChangeLog.md
	hash='[`%h`](https://github.com/HuidaeCho/projpicker/commit/%h)'
else
	file=/dev/stdout
	hash='%h'
fi

exclude=""
for i in COPYING README.md setup.py data deploy docs guis tests utils; do
	exclude="$exclude :(exclude)../$i"
done
(
echo "# Change log"
echo
git log --pretty="* $hash %d %s %cd" --decorate=full $exclude |
sed '
/(HEAD/{
	s/^\(.*\) (HEAD.*HEAD) \(.* \(\([^ ]\+ \)\{5\}[^ ]\+\)\)$/## HEAD\n\3\n\n\1 \2/
}
/(tag: refs\/tags/{
	s/^\(.*(tag: refs\/tags\/\([^)]*\)).* \(\([^ ]\+ \)\{5\}[^ ]\+\)\)$/\n## \2\n\3\n\n\1/
}
s/\( [^ ]\+\)\{6\}$//
s/_/\\_/g
'
) > $file
