echo "Running the PIRA tests"
didfail=0
export PYTHONPATH=$PWD:$PYTHONPATH
cd test/unit
for i in `find . -iname "*.py"`; do echo "Running $i"; python3 $i; if [ $? -ne 0 ]; then let didfail=$didfail+1; fi ; done
cd ../..

exit $didfail
