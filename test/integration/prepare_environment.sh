#!/usr/bin/env bash
#
# File: prepare_environment.sh
# License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/tudasc/pira
# Description: Sets up the environment for PIRA's integration tests
#

testDir=$PWD
export TEST_DIR=$testDir

echo -e "\n----- Getting and building jq (v 1.6) -----"
# Used for extracting info from the compile_commands.json file

if [ ! -d jq ]; then
	echo "Fetching jq release 1.6"
  wget https://github.com/stedolan/jq/releases/download/jq-1.6/jq-linux64
  mkdir jq
  mv jq-linux64 jq/jq
  cd jq
  chmod +x jq
else
  cd jq
fi
export PATH=$PWD:$PATH
echo $PATH
cd ..

