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
echo "null" > gol.ipcg
cgmerge gol.ipcg main.ipcg SerialGoL.ipcg 2>&1 > /dev/null
cp gol.ipcg $PWD/../../../../../extern/install/pgis/bin/gol_ct.ipcg
cd ../..

cd gol

echo -e "\n----- Running Pira -----\n"

# use runtime folder for extrap files
if [[ -z "${XDG_DATA_HOME}" ]]; then
  pira_dir=$HOME/.local/share/pira
else
  pira_dir=$XDG_DATA_HOME/pira
fi
echo -e "Using ${pira_dir} for runtime files\n"

sed -i "s|CUBES_FOLDER|${pira_dir}/gol_cubes|g" $testDir/gol_config.json

python3 ../../../../pira.py --config-version 2 --tape ../gol.tp $testDir/gol_config.json

pirafailed=$?

rm -rf ${pira_dir}/piraII
rm -rf ${pira_dir}/gol_cubes-*
cd $testDir
rm -rf gol

exit $pirafailed
