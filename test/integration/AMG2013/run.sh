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

# XXX Currently required from PGIS
mkdir $PWD/../../../extern/install/metacg/bin/out

# Download the target application
stat amg2013_0.tgz
if [ $? -ne 0 ]; then
  wget https://asc.llnl.gov/sites/asc/files/2021-01/amg2013_0.tgz
fi
tar xzf amg2013_0.tgz
cd AMG2013

# XXX The clang version we use is built w/o OMP support, therefore, remove OMP flags
sed -i "s/-fopenmp//" Makefile.include
sed -i "s/-DHYPRE_USING_OPENMP//" Makefile.include


echo -e "\n----- Build AMG2013 / build call graph -----"
# Builds the compile_commands.json file
bear make CC="OMPI_CC=clang mpicc" -j
# Now cgcollector can read the compile_commands.json file, to retrieve the commands required
for f in $(cat compile_commands.json | jq  -r 'map(.directory + "/" + .file) | .[]'  | grep '\.c'); do
	echo "Processing $f"
	cgc $f >/dev/null 2>&1
done
# Build the full whole-program call-graph
echo "null" > amg.ipcg # create empty json file
find . -name "*.ipcg" -exec cgmerge amg.ipcg amg.ipcg {} + 2>&1 > ../cgcollector.log # merge all ipcg files into amg.ipcg
# Move the CG to where PIRA expects it
echo $PWD
cp amg.ipcg $PWD/../../../../extern/install/metacg/bin/amg_ct_mpi.mcg
cd ..


echo -e "\n----- Running Pira -----\n"

# use runtime folder for extrap files
if [[ -z "${XDG_DATA_HOME}" ]]; then
  pira_dir=$HOME/.local/share/pira
else
  pira_dir=$XDG_DATA_HOME/pira
fi
echo -e "Using ${pira_dir} for runtime files\n"

sed -i "s|CUBES_FOLDER|${pira_dir}/amg_cubes|g" $testDir/amg_config.json

python3 ../../../pira.py --config-version 2 --iterations 2 --repetitions 2 --extrap-dir ${pira_dir}/piraII --extrap-prefix t --tape ../amg.tp --analysis-parameters $testDir/parameters.json $testDir/amg_config.json

pirafailed=$?

#rm -rf ${pira_dir}/piraII
#rm -rf ${pira_dir}/amg_cubes-*
cd $testDir
#rm -rf AMG2013

exit $pirafailed
