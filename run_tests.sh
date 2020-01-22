echo "Running the PIRA tests"

didfail=0

export PYTHONPATH=$PWD:$PYTHONPATH
# This seems to be specific to my machine...
export PATH=~/.local/bin:$PATH

cd test/unit
for i in `find . -iname "*.py"`; do 
	echo "Running $i"; 
  pytest --cov=lib --cov-append $i; 
	if [ $? -ne 0 ]; then 
		let didfail=$didfail+1; 
	fi ; 
done
  coverage combine
cd ../..

exit $didfail
