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
if [ $? -ne 0 ]; then
	echo "[PIRA] Configuring LLVM-Instrumenter failed."
	exit 1
fi

make -j $parallel_jobs
if [ $? -ne 0 ]; then
	echo "[PIRA] Building LLVM-Instrumenter failed."
	exit 1
fi

# Score-P modified version
echo "[PIRA] Configuring and building Score-P"
cd $extsourcedir/scorep-mod

bash set_instrumenter_directory.sh $extsourcedir/llvm-instrumenter/build/lib

# TODO We should check whether a cube / scorep install was found and if so, bail out, to know exactly which scorep/cube we get.
aclocalversion=$( aclocal --version | grep 1.13 )
if [ -z "$aclocalversion" ]; then
	echo "aclocal available in wrong version. Guessing to autoreconf."
	autoreconf -ivf
	cd ./vendor/cubelib
	autoreconf -ivf
	cd ./build-frontend
	autoreconf -ivf
	cd ../../cubew
	autoreconf -ivf
	cd ./build-backend
	autoreconf -ivf
	cd ../build-frontend
	autoreconf -ivf
	cd $extsourcedir/scorep-mod
fi

rm -rf scorep-build
mkdir scorep-build && cd scorep-build
../configure --prefix=$extinstalldir/scorep --disable-gcc-plugin "$add_flags"
if [ $? -ne 0 ]; then
	echo "[PIRA] Configuring Score-P failed."
	exit 1
fi
make -j $parallel_jobs
if [ $? -ne 0 ]; then
	echo "[PIRA] Building Score-P failed."
	exit 1
fi
make install
echo "[PIRA] Adding PIRA Score-P to PATH for subsequent tool chain components."
export PATH=$extinstalldir/scorep/bin:$PATH

# Extra-P (https://www.scalasca.org/software/extra-p/download.html)
echo "[PIRA] Building Extra-P (for PIRA II modeling)"
echo "[PIRA] Getting prerequisites ..."
pip3 install --user PyQt5
pip3 install --user matplotlib
if [ $? -ne 0 ]; then
	echo "[PIRA] Installting Extra-P dependencies failed."
	exit 1
fi

mkdir -p $extsourcedir/extrap
cd $extsourcedir/extrap

# TODO check if extra-p is already there, if so, no download / no build?
if [ ! -f "extrap-3.0.tar.gz" ]; then
    echo "[PIRA] Downloading and building Extra-P"
    wget http://apps.fz-juelich.de/scalasca/releases/extra-p/extrap-3.0.tar.gz
fi
tar xzf extrap-3.0.tar.gz
cd ./extrap-3.0
rm -rf build
mkdir build && cd build
# On my Ubuntu machine, the locate command is available, on the CentOS machine it wasn't
# TODO This should be done just a little less fragile
command -v locate "/Python.h"
if [ $? -eq 1 ]; then
	pythonheader=$(dirname $(which python))/../include/python3.7m
else
	pythonlocation=$(locate "/Python.h" | grep "python3.")
	if [ -z $pythonlocation ]; then
	  pythonheader=$(dirname $(which python))/../include/python3.7m
	else
    pythonheader=$(dirname $pythonlocation)
	fi
fi
echo "[PIRA] Found Python.h at " $pythonheader
../configure --prefix=$extinstalldir/extrap CPPFLAGS=-I$pythonheader
if [ $? -ne 0 ]; then
	echo "[PIRA] Configuring Extra-P failed."
	exit 1
fi
make -j $parallel_jobs
if [ $? -ne 0 ]; then
	echo "[PIRA] Building Extra-P failed."
	exit 1
fi
make install

# CXX Opts
echo "[PIRA] Getting cxxopts library"
cd $extsourcedir
if [ ! -d "$extsourcedir/cxxopts" ]; then
    git clone https://github.com/jarro2783/cxxopts cxxopts
fi
cd cxxopts
echo "[PIRA] Select release branch 2_1 for cxxopts."
git checkout 2_1

# JSON library
echo "[PIRA] Getting json library"
cd $extsourcedir
if [ ! -d "$extsourcedir/json" ]; then
    git clone https://github.com/nlohmann/json json
fi

echo "[PIRA] Building PGIS analysis engine"
cd $extsourcedir/PGIS

git checkout devel

rm -rf build
mkdir build && cd build
cmake -DCUBE_INCLUDE=$extinstalldir/scorep/include/cubelib -DCUBE_LIB=$extinstalldir/scorep/lib -DCXXOPTS_INCLUDE=$extsourcedir/cxxopts -DJSON_INCLUDE=$extsourcedir/json/single_include -DEXTRAP_INCLUDE=$extsourcedir/extrap/extrap-3.0/include -DEXTRAP_LIB=$extinstalldir/extrap/lib -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=$extinstalldir/pgis ..
if [ $? -ne 0 ]; then
	echo "[PIRA] Configuring PGIS failed."
	exit 1
fi

make -j $parallel_jobs
if [ $? -ne 0 ]; then
	echo "[PIRA] Building PGIS failed."
	exit 1
fi
make install

# CGCollector / merge tool
echo "[PIRA] Not yet ready to be built, thus skipping CGCollector"
cd $extsourcedir/cgcollector

## TODO Remove when merged
git checkout devel

rm -rf build
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=$extinstalldir/cgcollector -DJSON_INCLUDE_PATH=$extsourcedir/json/single_include ..
if [ $? -ne 0 ]; then
	echo "[PIRA] Configuring CGCollector failed."
	exit 1
fi

make -j $parallel_jobs
if [ $? -ne 0 ]; then
	echo "[PIRA] Building CGCollector failed."
	exit 1
fi
make install

cd $scriptdir
