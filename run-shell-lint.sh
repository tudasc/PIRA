#! //usr/bin/env bash
echo "Running Shell lint"

didfail=0


for i in $(find ./test/integration -iname "*.sh"); do
	testName=$(echo "$i" | awk -F . '{print substr($2,2)}')
	echo "Running $i -> $testName";
  shellcheck -S error $i
	if [ $? -ne 0 ]; then 
		let didfail=$didfail+1; 
	fi ; 
done

for i in $(find ./resources -iname "*.sh"); do
	testName=$(echo "$i" | awk -F . '{print substr($2,2)}')
	echo "Running $i -> $testName";
  shellcheck -S error $i
	if [ $? -ne 0 ]; then 
		let didfail=$didfail+1; 
	fi ; 
done

echo "Failed tests: $didfail"

exit $didfail
