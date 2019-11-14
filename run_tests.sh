echo "Running the PIRA tests"
export PYTHONPATH=$PWD:$PYTHONPATH
cd test/unit
for i in `find . -iname "*.py"`; do echo "Running $i"; python3 $i; done
cd ..
