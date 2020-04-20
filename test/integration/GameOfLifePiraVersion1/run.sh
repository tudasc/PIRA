#
# File: run.sh
# License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
# Description: Runs the game of life integration test
#

testDir=$PWD
export TEST_DIR=$testDir

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

# Download the target application
stat PIRA-testing.tar.gz
if [ $? -ne 0 ]; then
  wget https://github.com/jplehr/GameOfLife/archive/PIRA-testing.tar.gz
fi
tar xzf PIRA-testing.tar.gz
mv GameOfLife-PIRA-testing gol

echo -e "\n----- Build GameOfLife / build call graph -----"
cd gol/serial_non_template
bear make gol 2>&1 > /dev/null
cgc main.cpp 2>&1 > /dev/null
cgc SerialGoL.cpp 2>&1 > /dev/null
cgmerge gol.ipcg main.ipcg SerialGoL.ipcg 2>&1 > /dev/null
cp gol.ipcg $PWD/../../../../../extern/install/pgis/bin/gol_ct.ipcg
cd ../..

cd gol

echo -e "\n----- Running Pira -----\n"

python3 ../../../../pira.py --version 2 --tape ../gol.tp $testDir/gol_config.json

pirafailed=$?

rm -rf /tmp/piraII
rm -r /tmp/pira-*
cd $testDir
rm -rf gol

exit $pirafailed
