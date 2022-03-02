#! /usr/bin/env bash
#"""
# File: load_submodules.sh
# License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
# Description: Helper script to build the git submodules useed in PIRA.
#"""

scriptdir="$1"

if [[ -z "$scriptdir" ]]; then
  scriptdir="$( cd "$(dirname "$0")" ; pwd -P )"
fi

# The upper-case parts are sed'ed while installation
cube_install_dir=/work/home/j_lehr/all_repos/gl-sc-pira/resources/../extern/install/scorep
scorep_install_dir=/work/home/j_lehr/all_repos/gl-sc-pira/resources/../extern/install/scorep
extrap_install_dir=/work/home/j_lehr/all_repos/gl-sc-pira/resources/../extern/install/extrap
metacg_install_dir=/work/home/j_lehr/all_repos/gl-sc-pira/resources/../extern/install/metacg
mpiwrap_install_dir=/work/home/j_lehr/all_repos/gl-sc-pira/resources/../extern/install/mpiwrap
bear_install_dir=/work/home/j_lehr/all_repos/gl-sc-pira/resources/../extern/install/bear

echo -e "Cube installation dir:\t$cube_install_dir"
echo -e "Score-P insitallation dir:\t$scorep_install_dir"
echo -e "Extra-P installation dir:\t$extrap_install_dir"
echo -e "MetaCG installation dir:\t$metacg_install_dir"
echo -e "mpiwrap installation dir:\t$mpiwrap_install_dir"
echo -e "bear installation dir:\t$bear_install_dir"

echo -e "Setting up paths\n"

clangbaseraw="$( cd "$(dirname ""$(which clang)"")" ; pwd -P )"
export CLANG_BASE_PATH="${clangbaseraw/\/bin/}"

export PIRA_DIR="$scriptdir/.."


export PATH=$cube_install_dir/bin:$scorep_install_dir/bin:$extrap_install_dir/bin:$metacg_install_dir/bin:$mpiwrap_install_dir:$bear_install_dir/bin:$PATH
export LD_LIBRARY_PATH=$cube_install_dir/lib:$scorep_install_dir/lib:$extrap_install_dir/lib:$metacg_install_dir/lib:$mpiwrap_install_dir/lib:$bear_install_dir/lib:$LD_LIBRARY_PATH
echo -e "-- PATH --\n" $PATH
echo -e "\n-- LD_LIBRARY_PATH --\n" $LD_LIBRARY_PATH

