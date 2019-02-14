echo "Running the PIRA tests"
cd test
for i in `find . -iname "*.py"`; do echo "Running $i"; python3 $i; done
cd ..
