#!/bin/sh
(
echo "# Change Log"
git log --tags --pretty="* [%h](https://github.com/HuidaeCho/projpicker/commit/%h) %d %s %cd" --decorate=full ":(exclude)../guis" |
sed '/(tag: refs\/tags/{s`^\(.*(tag: refs/tags/\([^)]*\)).* \(\([^ ]\+ \)\{5\}[^ ]\+\)\)$`\n## \2\n\3\n\n\1`}; s/\( [^ ]\+\)\{6\}$//'
) > ../projpicker/ChangeLog.md
