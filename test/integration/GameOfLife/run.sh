#
# File: run.sh
# License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
# Description: Runs the game of life integration test
#

testDir=$PWD
export TEST_DIR=$testDir

# We need to be able to generate a compile_commands.json library
echo -e "\n----- Getting and building bear -----"
git clone https://github.com/rizsotto/Bear.git bear 2>&1 > /dev/null
cd bear
mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=../install .. 2>&1 > /dev/null
make all 2>&1 > /dev/null
make install 2>&1 > /dev/null

cd ..
export PATH=$PWD/install/bin:$PATH
echo $PATH
cd ..

# Export all the Pira tools for the integration test
export LD_LIBRARY_PATH=$PWD/../../../extern/install/scorep/lib:$PWD/../../../extern/install/extrap/lib:$PWD/../../../extern/install/pgis/lib:$PWD/../../../extern/install/cgcollector/lib:$LD_LIBRARY_PATH
export PATH=$PWD/../../../extern/install/pgis/bin:$PWD/../../../extern/install/cgcollector/bin:$PATH
export PATH=$PWD/../../../extern/install/scorep/bin:$PATH
echo $PATH

echo -e "\n------ PATH -----"
echo $PATH
echo -e "\n------ LD_LIBRARY_PATH -----"
echo $LD_LIBRARY_PATH
echo -e "\n------ Which tools -----"
which pgis_pira
which cgcollector
which scorep

# XXX Currently required from PGIS
mkdir $PWD/../../../extern/install/pgis/bin/out

# Download the target application
git clone https://github.com/jplehr/GameOfLife gol 2>&1 > /dev/null

echo -e "\n----- Build GameOfLife / build call graph -----"
cd gol/serial_non_template
bear make gol 2>&1 > /dev/null
cgcollector main.cpp 2>&1 > /dev/null
cgcollector SerialGoL.cpp 2>&1 > /dev/null
cgmerge gol.ipcg main.ipcg SerialGoL.ipcg 2>&1 > /dev/null
cp gol.ipcg $PWD/../../../../../extern/install/pgis/bin/ct-gol.ipcg
cd ../..

cd gol

echo -e "\n----- Running Pira -----\n"

python3 ../../../../pira.py --version 2 --extrap-dir /tmp/piraII --extrap-prefix t --tape ./gol.tp $testDir/gol-config.json

pirafailed=$?

rm -rf /tmp/piraII
cd $testDir
rm -rf gol
rm -rf bear

exit $pirafailed
