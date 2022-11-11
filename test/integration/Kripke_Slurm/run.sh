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

export CXX_COMPILER_WRAPPER=${TEST_DIR}/cxx-wrapper.sh

# XXX Currently required by PGIS
mkdir $PWD/../../../extern/install/metacg/bin/out

# Download the target application
stat Kripke
if [ $? -ne 0 ]; then
  git clone git@github.com:LLNL/Kripke.git
fi
cd Kripke
git checkout v1.2.4
git submodule update --init
git clean -dxf

echo -e "\n----- Build Kripke / build call graph -----"
export LULESH_CXXFLAGS="-DUSE_MPI=1 -O3 -g -I. -Wno-unknown-pragmas -Wall"

# Configure
mkdir build
cd build
export CXX_WRAP="clang++"
cmake -DENABLE_MPI=ON -Wno-dev -DCMAKE_CXX_COMPILER=${CXX_COMPILER_WRAPPER} .. || exit 1

# Initial build
# Builds the compile_commands.json file
bear make -j || exit 1

cd ..

# CGCollection
# Now cgcollector can read the compile_commands.json file, to retrieve the commands required
cp build/compile_commands.json .
# for f in $(cat build/compile_commands.json | jq  -r 'map(.directory + "/" + .file) | .[]'  | grep '\.cpp'); do
for f in $(find ./src -type f -iname "*.cpp" ); do
	echo "Processing $f"
	cgc $f >/dev/null 2>&1
done

# Build the full whole-program call-graph
echo "null" > kripke.mcg # create empty json file
find . -name "*.ipcg" -exec cgmerge kripke.mcg kripke.mcg {} + 2>&1 > ../cgmerge.log # merge all ipcg files into kripke.mcg

# Move the CG to where PIRA expects it
cp kripke.mcg $PWD/../../../../extern/install/metacg/bin/kripke_ct.mcg
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

python3 ../../../pira.py --config-version 2 --slurm-config ${testDir}/batchsystem.json --iterations 4 --repetitions 1 --tape kripke.tp $testDir/kripke_config.json
pirafailed=$?

#rm -rf ${pira_dir}/piraII
#rm -rf ${pira_dir}/lulesh_cubes-*
cd $testDir
../check.py ../../../extern/install/metacg/bin/out expected_instrumentation.json kripke_ct || exit 1

exit $pirafailed
