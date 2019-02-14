echo "Running the PIRA tests"

for i in `find . -iname "*.py"`; do echo "Running $i"; python3 $i; done
