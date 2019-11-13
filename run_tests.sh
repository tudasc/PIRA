echo "Running the PIRA tests"
didfail=0
cd test
for i in `find . -iname "*.py"`; do echo "Running $i"; python3 $i; if [ $? -ne 0 ]; then let didfail=$didfail+1; fi ; done
cd ..

exit $didfail
