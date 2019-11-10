#! /usr/bin/env bash
#"""
# File: build_submodules.sh
# License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
# Description: Helper script to build the git submodules useed in PIRA.
#"""

scriptdir="$( cd "$(dirname "$0")" ; pwd -P )"
extsourcedir=$scriptdir/../extern/src
extinstalldir=$scriptdir/../extern/install

# TODO Make this actually working better!
# Allow configure options (here for Score-P, bc I want to build it w/o MPI)
parallel_jobs="$1"
add_flags="$2"

CC=clang
CXX=clang++

command -v clang++
if [ $? -eq 1 ]; then
  echo -e "[PIRA]: No Clang found.\nPIRA requires a source build of Clang 9.0.\nNo suitable Clang version found in PATH"
  exit -1
fi
# Very primitive version check to bail out early enough
clangversion=$($CXX --version | grep 9.0)
if [ -z "$clangversion" ]; then
  echo -e "[PIRA] Wrong version of Clang.\nPIRA requires a source build of Clang 9.0.\nNo suitable Clang version found in PATH"
  exit -1
fi

# LLVM Instrumenter
echo "[PIRA] Configuring and building LLVM-instrumentation"
cd $extsourcedir/llvm-instrumenter
rm -rf build
mkdir build && cd build
cmake ..
make -j $parallel_jobs

# Score-P modified version
echo "[PIRA] Configuring and building Score-P"
# TODO We should check whether a cube / scorep install was found and if so, bail out, to know exactly which scorep/cube we get.
cd $extsourcedir/scorep-mod
rm -rf scorep-build
mkdir scorep-build && cd scorep-build
../configure --prefix=$extinstalldir/scorep --disable-gcc-plugin "$add_flags"
make -j $parallel_jobs
make install
echo "[PIRA] Adding PIRA Score-P to PATH for subsequent tool chain components."
export PATH=$extinstalldir/scorep/bin:$PATH

# Extra-P (https://www.scalasca.org/software/extra-p/download.html)
echo "[PIRA] Building Extra-P (for PIRA II modeling)"
echo "[PIRA] Getting prerequisites ..."
pip3 install --user PyQt5
pip3 install --user matplotlib

mkdir -p $extsourcedir/extrap
cd $extsourcedir/extrap

# TODO check if extra-p is already there, if so, no download / no build?
if [ ! -f "extrap-3.0.tar.gz" ]; then
    echo "[PIRA] Downloading and building Extra-P"
    wget http://apps.fz-juelich.de/scalasca/releases/extra-p/extrap-3.0.tar.gz
fi
tar xzf extrap-3.0.tar.gz
cd extrap-3.0
rm -rf build
mkdir build && cd build
# On my Ubuntu machine, the locate command is available, on the CentOS machine it wasn't
# TODO This should be done just a little less fragile
command -v locate "/Python.h"
if [ $? -eq 1 ]; then
	pythonheader=$(dirname $(which python))/../include/python3.7m
else
  pythonheader=$(dirname $(locate "/Python.h" | grep "python3."))
fi
echo "[PIRA] Found Python.h at " $pythonheader
../configure --prefix=$extinstalldir/extrap CPPFLAGS=-I$pythonheader
make -j $parallel_jobs
make install

# CXX Opts
echo "[PIRA] Getting cxxopts library"
cd $extsourcedir
if [ ! -d "$extsourcedir/cxxopts" ]; then
    git clone https://github.com/jarro2783/cxxopts cxxopts
fi
cd cxxopts
echo "[PIRA] JP TODO: Select a specific release branch."

# JSON library
echo "[PIRA] Getting json library"
cd $extsourcedir
if [ ! -d "$extsourcedir/json" ]; then
    git clone https://github.com/nlohmann/json json
fi

# CGCollector / merge tool
echo "[PIRA] Not yet ready to be built, thus skipping CGCollector"


