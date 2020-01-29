echo "Running the PIRA tests"

tester=''

command -v pytest
if [ $? -eq 1 ]; then
  echo -e "[PIRA]: No pytest found.\n"
else
  tester=pytest
fi

command -v pytest-3
if [ $? -eq 1 ]; then
  echo -e "[PIRA]: No pytest-3 found.\n"
else
  tester=pytest-3
fi

if [ -z $tester ]; then
  exit -1
fi

didfail=0

export PYTHONPATH=$PWD:$PYTHONPATH
# This seems to be specific to my machine...
export PATH=~/.local/bin:$PATH

cd test/unit
for i in `find . -iname "*.py"`; do 
	echo "Running $i"; 
  $tester --cov=lib --cov-append $i; 
	if [ $? -ne 0 ]; then 
		let didfail=$didfail+1; 
	fi ; 
done
  coverage combine
cd ../..

exit $didfail
