echo "Running Python lint"

didfail=0

export PYTHONPATH=$PWD:$PYTHONPATH
# This seems to be specific to my machine...
export PATH=~/.local/bin:$PATH


for i in `find ./lib -iname "*.py"`; do
	testName=$(echo "$i" | awk -F . '{print substr($2,2)}')
	echo "Running $i -> $testName";
	python -m pylint -E $i
	if [ $? -ne 0 ]; then 
		let didfail=$didfail+1; 
	fi ; 
done

echo "Failed tests: $didfail"

exit $didfail
