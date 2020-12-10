#
# File: run.sh
# License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
# Description: Runs the game of life integration test
#

# The test directory where the top-level files reside
testDir=$PWD
export TEST_DIR=$testDir

echo -e "[ -- ## testDir == $testDir ## -- ]"

export PATH=$PWD/../bear/install/bin:$PATH
echo $PATH

# Export all the Pira tools for the integration test
cd $testDir/../../../resources
. setup_paths.sh
cd $testDir
echo $PATH

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
mkdir $PWD/../../../extern/install/pgis/bin/out

# Download the target application
stat amg20130624.tgz
if [ $? -ne 0 ]; then
  wget https://computing.llnl.gov/projects/co-design/download/amg2013.tgz
fi
tar xzf amg2013.tgz
cd AMG2013

# XXX The clang version we use is built w/o OMP support, therefore, remove OMP flags
sed -i "s/-fopenmp//" Makefile.include
sed -i "s/-DHYPRE_USING_OPENMP//" Makefile.include


echo -e "\n----- Build AMG2013 / build call graph -----"
# Builds the compile_commands.json file
bear make CC="OMPI_CC=clang mpicc"
# Now cgcollector can read the compile_commands.json file, to retrieve the commands required
for f in $(find . -name "*.c"); do
	echo "Processing $f"
	cgc $f
done
# Build the full whole-program call-graph
echo "null" > amg.ipcg # create empty json file
find . -name "*.ipcg" -exec cgmerge amg.ipcg amg.ipcg {} + 2>&1 > ../cgcollector.log # merge all ipcg files into amg.ipcg
# Move the CG to where PIRA expects it
echo $PWD
cp amg.ipcg $PWD/../../../../extern/install/pgis/bin/amg_ct_mpi.ipcg
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

python3 ../../../pira.py --config-version 2 --iterations 2 --repetitions 2 --extrap-dir ${pira_dir}/piraII --extrap-prefix t --tape ../amg.tp $testDir/amg_config.json

pirafailed=$?

rm -rf ${pira_dir}/piraII
rm -rf ${pira_dir}/amg_cubes-*
cd $testDir
rm -rf AMG2013

exit $pirafailed
