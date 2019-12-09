#
# File: run.sh
# License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
# Description: Runs the game of life integration test
#

testDir=$PWD
export TEST_DIR=$testDir

# We need to be able to generate a compile_commands.json library
git clone https://github.com/rizsotto/Bear.git bear
cd bear
mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=../install ..
make all
make install

cd ..
export PATH=$PWD/install/bin:$PATH
echo $PATH
cd ..

# Export all the Pira tools for the integration test
export LD_LIBRARY_PATH=$PWD/../../../extern/install/scorep/lib:$PWD/../../../extern/install/extrap/lib:$PWD/../../../extern/install/pgis/lib:$PWD/../../../extern/install/cgcollector/lib:$LD_LIBRARY_PATH
export PATH=$PWD/../../../extern/install/pgis/bin:$PWD/../../../extern/install/cgcollector/bin:$PATH
echo $PATH

mkdir $PWD/../../../extern/install/pgis/bin/out

# Download the target application
git clone https://github.com/jplehr/GameOfLife gol

cd gol/serial_non_template
bear make gol
cgcollector main.cpp
cgcollector SerialGoL.cpp
cgmerge gol.ipcg main.ipcg SerialGoL.ipcg
cp gol.ipcg $PWD/../../../../../extern/install/pgis/bin/ct-gol.ipcg
cd ../..


export PATH=$PWD/../../../extern/install/scorep/bin:$PATH

which pgis_pira
which cgcollector
which scorep

cd gol

echo -e "------ PATH -----\n"
echo $PATH
echo -e "------ LD_LIBRARY_PATH -----\n"
echo $LD_LIBRARY_PATH

python3 ../../../../pira.py --version 2 --extrap-dir /tmp/piraII --extrap-prefix t --tape ./gol.tp $testDir/gol-config.json

pirafailed=$?

rm -rf /tmp/piraII
cd $testDir
rm -rf gol
rm -rf bear

exit $pirafailed
