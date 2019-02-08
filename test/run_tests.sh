echo "Running the PIRA tests"

for i in `find . -iname "*.py"`; do python3 $i; done