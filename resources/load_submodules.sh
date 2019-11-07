#! /usr/bin/env bash
#"""
# File: load_submodules.sh
# License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
# Description: Helper script to build the git submodules useed in PIRA.
#"""

scriptdir="$( cd "$(dirname "$0")" ; pwd -P )"

echo "Adding PIRA Score-P to PATH:"
export PATH=$scriptdir/../extern/install/scorep/bin:$PATH
echo $PATH
