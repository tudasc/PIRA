#!/bin/bash

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

mkdir -p /tmp/pira-meta

echo -e "\n------ PATH -----"
echo $PATH
echo -e "\n------ LD_LIBRARY_PATH -----"
echo $LD_LIBRARY_PATH
echo -e "\n------ Which tools -----"
which pgis_pira
which cgcollector
which scorep
which wrap.py


echo -e "\n----- Build Imbalance / build call graph -----"
cd imbalance
echo -e "\n -> Running make clean"
bear make clean
echo -e "\n -> Running bear make"
bear make CC="OMPI_CC=clang mpicc" imbalance 2>&1 > /dev/null
echo -e "\n -> Running cgcollector"
cgc main.c 2>&1 > /dev/null || exit 1
cgc lib.c 2>&1 > /dev/null || exit 1
cgc util.h 2>&1 > /dev/null || exit 1
echo "null" > imbalance.ipcg
cgmerge imbalance.ipcg main.ipcg lib.ipcg util.ipcg || exit 1
cp imbalance.ipcg $PWD/../../../../extern/install/metacg/bin/imbalance_ct.mcg

echo -e "\n----- Running Pira -----\n"

python3 ../../../../pira.py --config-version 2 --iterations 5 --tape ../imbalance.tp --lide --analysis-parameters $testDir/parameters.json $testDir/imbalance_config.json || exit 1

pirafailed=$?
exit $pirafailed
