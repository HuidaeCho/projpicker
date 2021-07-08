#!/bin/sh
(
echo "# Change log"
git log --pretty="* [%h](https://github.com/HuidaeCho/projpicker/commit/%h) %d %s %cd" --decorate=full ":(exclude)../guis" |
sed '
/(HEAD/{
	s/^\(.*\) (HEAD.*HEAD) \(.* \(\([^ ]\+ \)\{5\}[^ ]\+\)\)$/\n## HEAD\n\3\n\n\1 \2/
};
/(tag: refs\/tags/{
	s/^\(.*(tag: refs\/tags\/\([^)]*\)).* \(\([^ ]\+ \)\{5\}[^ ]\+\)\)$/\n## \2\n\3\n\n\1/
};
s/\( [^ ]\+\)\{6\}$//
'
) > ../projpicker/ChangeLog.md
