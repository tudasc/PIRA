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
	
	# According to https://unix.stackexchange.com/questions/590694/posix-compliant-way-to-redirect-stdout-and-stderr-to-a-file
	# This is also POSIC compliant
	stat $dir_to_check >/dev/null 2>&1

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

if [ -z "$1" ] || [ "llvm-instrumentation" == "$1" ]; then
	echo "Testing llvm-instrumentation"
  remove_if_exists $extsourcedir/llvm-instrumentation/build
fi

if [ -z "$1" ] || [ "scorep" == "$1" ]; then
	echo "Testing scorep"
  remove_if_exists $extsourcedir/scorep-mod/scorep-build
fi

if [ -z "$1" ] || [ "cgcollector" == "$1" ]; then
	echo "Testing cgcollector"
  remove_if_exists $extsourcedir/metacg/cgcollector/build
fi

if [ -z "$1" ] || [ "extrap" == "$1" ]; then
	echo "Testing extrap"
  remove_if_exists $extsourcedir/extrap/extrap-3.0/build
fi

if [ -z "$1" ] || [ "pgis" == "$1" ]; then
	echo "Testing pgis"
  remove_if_exists $extsourcedir/metacg/pgis/build
fi

