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

# using mpicc for compilation leads to errors in PGIS (for whatever reason)
export CC=gcc
export CXX=g++

allOutputTo=/dev/null


function check_directory_or_file_exists {
  dir_to_check=$1

	# According to https://unix.stackexchange.com/questions/590694/posix-compliant-way-to-redirect-stdout-and-stderr-to-a-file
	# This is also POSIC compliant
	stat $dir_to_check >${allOutputTo} 2>&1

  if [ $? -ne 0 ]; then
    return 1
  fi
  return 0
}

command -v clang++ >${allOutputTo} 2>&1
if [ $? -eq 1 ]; then
  echo -e "[PIRA]: No Clang found.\nPIRA requires a source build of Clang/LLVM 10.\nNo suitable Clang version found in PATH"
  exit -1
fi
# Very primitive version check to bail out early enough
clangversion=$(clang++ --version | grep 10.0) >${allOutputTo} 2>&1
if [ -z "$clangversion" ]; then
  echo -e "[PIRA] Wrong version of Clang.\nPIRA requires a source build of Clang/LLVM 10.\nNo suitable Clang version found in PATH"
  exit -1
fi

### ====================
## Actual work starts
### =====================

# LLVM Instrumenter
echo "[PIRA] Configuring and building LLVM-instrumentation"
llvm_dir=$extsourcedir/llvm-instrumentation

cd $llvm_dir
check_directory_or_file_exists $llvm_dir/build
if [ $? -ne 0 ]; then
  echo "[PIRA] Rebuilding LLVM-Instrumenter."
  rm -rf build
  mkdir build && cd build

  cmake .. >${allOutputTo} 2>&1 
  if [ $? -ne 0 ]; then
    echo "[PIRA] Configuring LLVM-Instrumenter failed."
    exit 1
  fi
  make -j $parallel_jobs >${allOutputTo} 2>&1 
  if [ $? -ne 0 ]; then
    echo "[PIRA] Building LLVM-Instrumenter failed."
    exit 1
  fi
else
  echo "[PIRA] LLVM-Instrumenter already built."
fi

# Score-P modified version
echo "[PIRA] Configuring and building Score-P"
cd $extsourcedir/scorep-mod

check_directory_or_file_exists $extsourcedir/scorep-mod/scorep-build
if [ $? -ne 0 ]; then
  bash set_instrumenter_directory.sh $extsourcedir/llvm-instrumentation/build/lib >${allOutputTo} 2>&1 

  # TODO We should check whether a cube / scorep install was found and if so, bail out, to know exactly which scorep/cube we get.
  aclocalversion=$( aclocal --version | grep 1.13 ) >${allOutputTo} 2>&1 
  if [ -z "$aclocalversion" ]; then
    echo "[PIRA][Score-P] aclocal available in wrong version. Guessing to autoreconf."
    autoreconf -ivf >${allOutputTo} 2>&1 
  	cd ./vendor/cubelib >${allOutputTo} 2>&1 
  	autoreconf -ivf >${allOutputTo} 2>&1 
  	cd ./build-frontend >${allOutputTo} 2>&1 
  	autoreconf -ivf >${allOutputTo} 2>&1 
  	cd ../../cubew >${allOutputTo} 2>&1 
  	autoreconf -ivf >${allOutputTo} 2>&1 
  	cd ./build-backend >${allOutputTo} 2>&1 
  	autoreconf -ivf >${allOutputTo} 2>&1 
  	cd ../build-frontend  >${allOutputTo} 2>&1 
  	autoreconf -ivf >${allOutputTo} 2>&1 
  	cd $extsourcedir/scorep-mod
  fi
  
  rm -rf scorep-build
  mkdir scorep-build && cd scorep-build
  ../configure --prefix=$extinstalldir/scorep --enable-shared --disable-static --disable-gcc-plugin "$add_flags"  >${allOutputTo} 2>&1 
  if [ $? -ne 0 ]; then
  	echo "[PIRA] Configuring Score-P failed."
  	exit 1
  fi
  make -j $parallel_jobs >${allOutputTo} 2>&1
  if [ $? -ne 0 ]; then
  	echo "[PIRA] Building Score-P failed."
  	exit 1
  fi
  make install >${allOutputTo} 2>&1
else
  echo "[PIRA] Score-P already built."
fi

echo "[PIRA] Adding PIRA Score-P to PATH for subsequent tool chain components."
export PATH=$extinstalldir/scorep/bin:$PATH

# Extra-P (https://www.scalasca.org/software/extra-p/download.html)
echo "[PIRA] Building Extra-P (for PIRA II modeling)"
echo "[PIRA] Getting prerequisites ... (requires Qt 5)"
set MAKEFLAGS=-j$parallel_jobs
python3 -m pip install --user PyQt5 >${allOutputTo} 2>&1
if [ $? -ne 0 ]; then
  echo "[PIRA] Installting Extra-P dependency PyQt5 failed."
  exit 1
fi

python3 -m pip install --user matplotlib >${allOutputTo} 2>&1
if [ $? -ne 0 ]; then
  echo "[PIRA] Installting Extra-P dependency matplotlib failed."
  exit 1
fi

mkdir -p $extsourcedir/extrap
cd $extsourcedir/extrap

# TODO check if extra-p is already there, if so, no download / no build?
if [ ! -f "extrap-3.0.tar.gz" ]; then
  echo "[PIRA] Downloading and building Extra-P"
  wget http://apps.fz-juelich.de/scalasca/releases/extra-p/extrap-3.0.tar.gz >${allOutputTo} 2>&1
  tar xzf extrap-3.0.tar.gz >${allOutputTo} 2>&1
fi
cd ./extrap-3.0

check_directory_or_file_exists $extsourcedir/extrap/extrap-3.0/build
if [ $? -ne 0 ]; then
  echo "[PIRA] Building Extra-P"
  rm -rf build
  mkdir build && cd build
  # On my Ubuntu machine, the locate command is available, on the CentOS machine it wasn't
  # TODO This should be done just a little less fragile
  command -v locate "/Python.h" >${allOutputTo} 2>&1
  if [ $? -eq 1 ]; then
  	pythonheader=$(dirname $(which python3))/../include/python3.8
  else
  	pythonlocation=$(locate "/Python.h" | grep "python3.")
  	if [ -z $pythonlocation ]; then
  	  pythonheader=$(dirname $(which python))/../include/python3.8
  	else
      pythonheader=$(dirname $pythonlocation)
  	fi
  fi
  echo "[PIRA] Found Python.h at " $pythonheader
  ../configure --prefix=$extinstalldir/extrap CPPFLAGS=-I$pythonheader >${allOutputTo} 2>&1 
  if [ $? -ne 0 ]; then
  	echo "[PIRA] Configuring Extra-P failed."
  	exit 1
  fi
  make -j $parallel_jobs >${allOutputTo} 2>&1  
  if [ $? -ne 0 ]; then
  	echo "[PIRA] Building Extra-P failed."
  	exit 1
  fi
  make install >${allOutputTo} 2>&1 
else
  echo "[PIRA] Extra-P already built."
fi

# CXX Opts
echo "[PIRA] Getting cxxopts library"
cd $extsourcedir
if [ ! -d "$extsourcedir/cxxopts" ]; then
    git clone -b 2_1 --single-branch https://github.com/jarro2783/cxxopts cxxopts >${allOutputTo} 2>&1 
fi

# JSON library
echo "[PIRA] Getting json library"
cd $extsourcedir
if [ ! -d "$extsourcedir/json" ]; then
    git clone -b v3.7.3 --single-branch https://github.com/nlohmann/json json >${allOutputTo} 2>&1 
fi

echo "[PIRA] Building PGIS analysis engine"
cd $extsourcedir/metacg

# TODO Remove when merged
stat .git >${allOutputTo} 2>&1 
if [ $? -eq 0 ]; then
	git checkout master
	git pull
fi

cd $extsourcedir/metacg/pgis

check_directory_or_file_exists $extsourcedir/metacg/pgis/build
if [ $? -ne 0 ]; then
  rm -rf build
  mkdir build && cd build
	echo "[PIRA] Configuring PGIS"
  cmake -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DSPDLOG_BUILD_SHARED=ON -DCUBE_INCLUDE=$extinstalldir/scorep/include/cubelib -DCUBE_LIB=$extinstalldir/scorep/lib -DCXXOPTS_INCLUDE=$extsourcedir/cxxopts -DJSON_INCLUDE=$extsourcedir/json/single_include -DEXTRAP_INCLUDE=$extsourcedir/extrap/extrap-3.0/include -DEXTRAP_LIB=$extinstalldir/extrap/lib -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=$extinstalldir/pgis .. >${allOutputTo} 2>&1 
	echo "[PIRA] Configuring PGIS done"
  if [ $? -ne 0 ]; then
    echo "[PIRA] Configuring PGIS failed."
    exit 1
  fi
 
  make -j $parallel_jobs >${allOutputTo} 2>&1 
  if [ $? -ne 0 ]; then
    echo "[PIRA] Building PGIS failed."
    exit 1
  fi
  make install >${allOutputTo} 2>&1 
	mkdir $extinstalldir/pgis/bin/out >${allOutputTo} 2>&1
else
  echo "[PIRA] PGIS already built"
fi

# CGCollector / merge tool
echo "[PIRA] Building CGCollector"
cd $extsourcedir/metacg/cgcollector

check_directory_or_file_exists $extsourcedir/metacg/cgcollector/build
if [ $? -ne 0 ]; then
  rm -rf build
  mkdir build && cd build
  cmake -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=$extinstalldir/cgcollector -DJSON_INCLUDE_PATH=$extsourcedir/json/single_include -DCUBE_INCLUDE=$extinstalldir/scorep/include -DCUBE_LIB=$extinstalldir/scorep/lib ..  >${allOutputTo} 2>&1 
  if [ $? -ne 0 ]; then
    echo "[PIRA] Configuring CGCollector failed."
    exit 1
  fi
 
  make -j $parallel_jobs >${allOutputTo} 2>&1 
  if [ $? -ne 0 ]; then
    echo "[PIRA] Building CGCollector failed."
    exit 1
  fi
  make install >${allOutputTo} 2>&1 
else
  echo "[PIRA] CGCollector already built"
fi

cd $scriptdir

# Installing LLNL's MPI wrapper generator
cd $extsourcedir

check_directory_or_file_exists $extsourcedir/mpiwrap
if [ $? -ne 0 ]; then
  rm -r mpiwrap >${allOutputTo} 2>&1
  mkdir mpiwrap && cd mpiwrap
  wget https://github.com/LLNL/wrap/archive/master.zip >${allOutputTo} 2>&1
  unzip master.zip >${allOutputTo} 2>&1
  rm -rf $extinstalldir/mpiwrap >${allOutputTo} 2>&1
  mkdir $extinstalldir/mpiwrap
  cp wrap-master/wrap.py $extinstalldir/mpiwrap/wrap.py
else
  check_directory_or_file_exists $extinstalldir/mpiwrap
  if [ $? -ne 0 ]; then
    mkdir $extinstalldir/mpiwrap
	fi
  check_directory_or_file_exists $extinstalldir/mpiwrap/wrap.py
  if [ $? -ne 0 ]; then
    cp $extsourcedir/mpiwrap/wrap-master/wrap.py $extinstalldir/mpiwrap/wrap.py
	fi
  echo "[PIRA] mpiwrap already installed"
fi

cd $scriptdir
