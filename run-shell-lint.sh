#! //usr/bin/env bash
echo "Running Shell lint"

didfail=0



for i in $(find ./test/integration -iname "*.sh"); do
  testName=$(echo "$i" | awk -F . '{print substr($2,2)}')
  echo "Running $i -> $testName";

  if [[ $(grep -e '/home/*' -c "$i") -ne 0 ]]; then
    echo "Detected paths refering to /home"
    didfail=$((didfail+1))
  fi

  if [[ "$(shellcheck -S error "$i")"  -ne 0 ]]; then
    didfail=$((didfail+1))
  fi
done

for i in $(find ./resources -iname "*.sh"); do
  testName=$(echo "$i" | awk -F . '{print substr($2,2)}')
  echo "Running $i -> $testName";
 
  if [[ $(grep -e '/home/*' -c "$i") -ne 0 ]]; then
    echo "Detected paths refering to /home"
    didfail=$((didfail+1))
  fi

  shellcheck -S error "$i"
  if [[ "$(shellcheck -S error "$i")" -ne 0 ]]; then
    didfail=$((didfail+1))
  fi
done

echo "Failed tests: $didfail"

exit $didfail
