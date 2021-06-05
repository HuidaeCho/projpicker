#!/bin/sh
set -e

cleanup() {
	rm -f *.tmp
}
trap cleanup EXIT

cleanup

for script in *.py; do
	outfile=$(echo $script | sed 's/py$/out/')

	echo -n "$script..." | tee -a run.tmp
	python3 $script > test.tmp
	if diff test.tmp $outfile > /dev/null; then
		echo "PASSED" | tee -a run.tmp
	else
		echo "FAILED" | tee -a run.tmp
	fi

	shell=$(sed '/^#shell$/,/^#end$/!d; /^#\(shell\|end\)$/d; s/^# //' $script)
	if [ "$shell" != "" ]; then
		echo -n "shell $script..." | tee -a run.tmp
		eval "$shell" > test.tmp
		if diff test.tmp $outfile > /dev/null; then
			echo "PASSED" | tee -a run.tmp
		else
			echo "FAILED" | tee -a run.tmp
		fi
	fi
done

for infile in *.txt; do
	outfile=$(echo $infile | sed 's/txt$/out/')

	opts=$(sed '/^#opts: /!d; s/^#opts: //' $infile)
	echo -n $opts "-i $infile..." | tee -a run.tmp
	../projpicker/projpicker.py $opts -i $infile > test.tmp
	if diff test.tmp $outfile > /dev/null; then
		echo "PASSED" | tee -a run.tmp
	else
		echo "FAILED" | tee -a run.tmp
	fi

	geoms=$(sed '/^#geoms: /!d; s/^#geoms: //' $infile)
	if [ "$geoms" != "" ]; then
		echo -n $opts "$geoms..." | tee -a run.tmp
		eval "../projpicker/projpicker.py $opts -- $geoms" > test.tmp
		if diff test.tmp $outfile > /dev/null; then
			echo "PASSED" | tee -a run.tmp
		else
			echo "FAILED" | tee -a run.tmp
		fi
	fi

	python=$(sed '/^#python$/,/^#end$/!d; /^#\(python\|end\)$/d; s/^# //' $infile)
	if [ "$python" != "" ]; then
		echo -n "python $infile..." | tee -a run.tmp
		echo "$python" | python3 > test.tmp
		if diff test.tmp $outfile > /dev/null; then
			echo "PASSED" | tee -a run.tmp
		else
			echo "FAILED" | tee -a run.tmp
		fi
	fi
done

passed=$(grep "PASSED$" run.tmp | wc -l)
failed=$(grep "FAILED$" run.tmp | wc -l)

cat<<EOT

PASSED: $passed
FAILED: $failed
EOT
