#!/usr/bin/env bash
#
# File: run.sh
# License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
# Description: Runs the game of life integration test
#

# The test directory where the top-level files reside
testDir=$PWD
export TEST_DIR=$testDir

echo -e "[ -- ## testDir == $testDir ## -- ]"

export PATH=$PWD/../jq:$PATH
# Export all the Pira tools for the integration test
cd $testDir/../../../resources
. setup_paths.sh
cd $testDir

echo -e "\n------ PATH -----"
echo $PATH
echo -e "\n------ LD_LIBRARY_PATH -----"
echo $LD_LIBRARY_PATH
echo -e "\n------ Which tools -----"
which pgis_pira
which cgcollector
which scorep
which wrap.py

# XXX Currently required by PGIS
mkdir $PWD/../../../extern/install/metacg/bin/out

# Download the target application
stat LULESH
if [ $? -ne 0 ]; then
  git clone https://github.com/LLNL/LULESH.git
fi
cd LULESH
git checkout 3e01c40
git clean -dxf

echo -e "\n----- Build LULESG / build call graph -----"
export LULESH_CXXFLAGS="-DUSE_MPI=1 -O3 -g -I. -Wno-unknown-pragmas -Wall"
# Builds the compile_commands.json file
bear make CXX="mpicxx" CXXFLAGS="$LULESH_CXXFLAGS" -j
# Now cgcollector can read the compile_commands.json file, to retrieve the commands required
for f in $(cat compile_commands.json | jq  -r 'map(.directory + "/" + .file) | .[]'  | grep '\.cc'); do
	echo "Processing $f"
	cgc $f >/dev/null 2>&1
done
# Build the full whole-program call-graph
echo "null" > lulesh.mcg # create empty json file
find . -name "*.ipcg" -exec cgmerge lulesh.mcg lulesh.mcg {} + 2>&1 > ../cgcollector.log # merge all ipcg files into lulesh.mcg
# Move the CG to where PIRA expects it
echo $PWD
cp lulesh.mcg $PWD/../../../../extern/install/metacg/bin/lulesh_ct.mcg
cd ..


echo -e "\n----- Running Pira -----\n"

# use runtime folder for extrap files
if [[ -z "${XDG_DATA_HOME}" ]]; then
  pira_dir=$HOME/.local/share/pira
else
  pira_dir=$XDG_DATA_HOME/pira
fi
export PIRA_DIR=$pira_dir
echo -e "Using ${pira_dir} for runtime files\n"

python3 ../../../pira.py --config-version 2 --iterations 10 --repetitions 1 --lide --tape lulesh.tp --analysis-parameters $testDir/parameters.json $testDir/lulesh_config.json

pirafailed=$?

#rm -rf ${pira_dir}/piraII
#rm -rf ${pira_dir}/lulesh_cubes-*
cd $testDir
#rm -rf LULESH
../check.py ../../../extern/install/metacg/bin/out expected_instrumentation.json lulesh_ct || exit 1

exit $pirafailed
