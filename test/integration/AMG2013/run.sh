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
  wget https://asc.llnl.gov/CORAL-benchmarks/Throughput/amg20130624.tgz
fi
tar xzf amg20130624.tgz
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
find . -name "*.ipcg" -exec cgmerge amg.ipcg {} + 2>&1 > ../cgcollector.log
# Move the CG to where PIRA expects it
echo $PWD
cp amg.ipcg $PWD/../../../../extern/install/pgis/bin/amg_ct_mpi.ipcg
cd ..


echo -e "\n----- Running Pira -----\n"

python3 ../../../pira.py --version 2 --iterations 2 --repetitions 2 --extrap-dir /tmp/piraII --extrap-prefix t --tape ../amg.tp $testDir/amg_config.json

pirafailed=$?

rm -rf /tmp/piraII
rm -r /tmp/pira-*
cd $testDir
rm -rf AMG2013

exit $pirafailed
