#! /usr/bin/env bash
#"""
# File: build_submodules.sh
# License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
# Description: Helper script to build the git submodules useed in PIRA.
#"""

scriptdir="$( cd "$(dirname "$0")" ; pwd -P )"
extsourcedir=$scriptdir/../extern/src

function check_directory_or_file_exists {
	dir_to_check=$1
	(stat $dir_to_check 2>&1)>/dev/null

	if [ $? -ne 0 ]; then
		return 1
	fi
	return 0
}

function remove_if_exists {
  dir_to_remove=$1

  check_directory_or_file_exists $dir_to_remove

  if [ $? -eq 0 ]; then
	  echo "Removing $dir_to_remove"
    rm -rdf $dir_to_remove
  fi
}


remove_if_exists $extsourcedir/llvm-instrumenter/build
remove_if_exists $extsourcedir/scorep-mod/scorep-build
remove_if_exists $extsourcedir/cgcollector/build
remove_if_exists $extsourcedir/extrap/extrap-3.0/build
remove_if_exists $extsourcedir/PGIS/build


