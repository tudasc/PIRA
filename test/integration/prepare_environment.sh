#
# File: prepare_environment.sh
# License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
# Description: Sets up the environment for PIRA's integration tests
#

testDir=$PWD
export TEST_DIR=$testDir

# We need to be able to generate a compile_commands.json library
echo -e "\n----- Getting and building bear (v 2.4.2) -----"
wget https://github.com/rizsotto/Bear/archive/2.4.2.tar.gz
tar xzf 2.4.2.tar.gz
mv Bear-2.4.2 bear
cd bear
mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=../install .. 2>&1 > /dev/null
make all 2>&1 > /dev/null
make install 2>&1 > /dev/null

cd ..
export PATH=$PWD/install/bin:$PATH
echo $PATH
cd ..

# XXX Currently required from PGIS
mkdir $PWD/../../extern/install/pgis/bin/out

