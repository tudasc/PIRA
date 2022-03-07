echo "Running the PIRA tests"

tester=''

didfail=0

export PYTHONPATH=$PWD:$PYTHONPATH
# This seems to be specific to my machine...
export PATH=~/.local/bin:$PATH

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

cd test/unit
for i in `find . -iname "*.py"`; do
  testName=$(echo "$i" | awk -F . '{print substr($2,2)}')
  echo "Running $i -> $testName"
  $tester --junit-xml=report-${testName}.xml --cov=lib --cov-append $i
  if [ $? -ne 0 ]; then
    didfail=$((didfail+1))
  fi
done
  coverage combine
cd ../..

echo "Failed tests: $didfail"

exit $didfail
