echo "Running Python formatting and linting"

didfail=0

export PYTHONPATH=$PWD:$PYTHONPATH
# This seems to be specific to my machine...
export PATH=~/.local/bin:$PATH

# files and directories to be checked by pylint
locations=(
	./pira.py
	./lib
	./test/integration/check.py
)

# First check for formatting then lint
for i in $(find ${locations[@]} -iname "*.py"); do
	testName=$(echo "$i" | awk -F . '{print substr($2,2)}')

  echo "Formatting check for $i -> $testName";
  python -m yapf -q $i 
  if [ $? -ne 0 ]; then
    echo "Formatting check failed for $i"
    exit 1
  fi

	echo "Running $i -> $testName";
	python -m pylint -E $i
	if [ $? -ne 0 ]; then 
		let didfail=$didfail+1; 
	fi ; 
done

echo "Failed tests: $didfail"

exit $didfail
