#! /usr/bin/env bash
#"""
# File: build_submodules.sh
# License: Part of the PIRA project. Licensed under BSD 3 clause license. See LICENSE.txt file at https://github.com/jplehr/pira/LICENSE.txt
# Description: Helper script to build the git submodules useed in PIRA.
#"""

scriptdir="$( cd "$(dirname "$0")" ; pwd -P )"
extsourcedir=$scriptdir/../extern/src
extinstalldir=$scriptdir/../extern/install

# using mpicc for compilation leads to errors in PGIS (for whatever reason)
export CC=gcc
export CXX=g++

allOutputTo=/dev/null


# TODO Make this actually working better!
# Allow configure options (here for Score-P, bc I want to build it w/o MPI)
#add_flags="$2"
add_flags=""

# Which options do we have to provide?
# - Path to cube library
# - Path to cube headers
# - Path to Extra-P installation (lib/include as sub directories)
# - Parallelism used during build
function print_usage {
  echo -e "./build_submodules.sh <OPTS>\n"
  echo -e "  -e\tPath to Extra-P installation"
  echo -e "  -c\tPath to Cube installation"
  echo -e "  -p\tParallel compile jobs"
}

function echo_configuring {
  echo "[PIRA] Configuring $1"
}

function echo_building {
  echo "[PIRA] Building $1"
}

function echo_already_built {
  echo "[PIRA] Already built $1"
}

function echo_processing {
  echo "[PIRA] Processing $1"
}

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

# Get command line parameters
while getopts ":e:c:p:o:h" opt; do
  case $opt in
    e)
      if [ ! -d $OPTARG ]; then
        echo "Extra-P installation directory not valid"
        exit 1
      fi
      extrap_install_dir=$OPTARG
      echo "Setting Extra-P installation to: $extrap_install_dir" >&2
      ;;
    c)
      if [ ! -d $OPTARG ]; then
        echo "Cube installation directory not valid"
        exit 1
      fi
      cube_install_dir=$OPTARG
      echo "Setting Cube installation to: $cube_install_dir" >&2
      ;;
    p)
      parallel_jobs=$OPTARG
      echo "Setting parallel builds to: $parallel_jobs" >&2
      ;;
    o)
      add_flags="$OPTARG"
      echo "Passing additional flags " ${additional_flags}
      ;;
    h)
      print_usage
      exit 0
      ;;
    \?)
      echo "Invalid option -$OPTARG" >&2
      print_usage
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument" >&2
      print_usage
      exit 1
      ;;
  esac
done


# Some sanity check of things that may go wrong.
# This most likely just a list of things that I get wrong all the time
command -v cubelib-config >${allOutputTo} 2>&1
if [ $? -eq 0 ] && [ -z $cube_install_dir ] ; then
  echo "[PIRA]: No cubelib path set (-c) but cubelib-config available in PATH. Please set -c option or strip from PATH."
  echo ""
  exit 1
fi

command -v extrap >${allOutputTo} 2>&1
if [ $? -eq 0 ] && [ -z $extrap_install_dir ] ; then
  echo "[PIRA]: No Extra-P path set (-e) but extrap available in PATH. Please set -e option or strip from PATH."
  echo ""
  exit 1
fi

command -v clang++ >${allOutputTo} 2>&1
if [ $? -eq 1 ]; then
  echo -e "[PIRA]: No Clang found.\nPIRA requires a source build of Clang/LLVM 10.\nNo suitable Clang version found in PATH"
  exit 1
fi

# Very primitive version check to bail out early enough
clangversion=$(clang++ --version | grep 10.0) >${allOutputTo} 2>&1
if [ -z "$clangversion" ]; then
  echo -e "[PIRA] Wrong version of Clang.\nPIRA requires a source build of Clang/LLVM 10.\nNo suitable Clang version found in PATH"
  exit 1
fi


### ====================
## Actual work starts
### =====================

# LLVM Instrumenter
llvm_dir=$extsourcedir/llvm-instrumentation

llvm_component_name="LLVM Instrumentation Plugin"
echo_processing "$llvm_component_name"
cd $llvm_dir || exit 1
check_directory_or_file_exists $llvm_dir/build
if [ $? -ne 0 ]; then
  echo_configuring "$llvm_component_name"
  rm -rf build
  mkdir build && cd build || exit 1

  cmake .. >${allOutputTo} 2>&1
  if [ $? -ne 0 ]; then
    echo "[PIRA] Configuring LLVM-Instrumenter failed."
    exit 1
  fi

  echo_building "$llvm_component_name"
  make -j $parallel_jobs >${allOutputTo} 2>&1
  if [ $? -ne 0 ]; then
    echo "[PIRA] Building LLVM-Instrumenter failed."
    exit 1
  fi
else
  echo_already_built "$llvm_component_name"
fi

# Score-P modified version
scorep_component_name="Score-P 6.0 Modified"
echo_processing "$scorep_component_name"
cd $extsourcedir/scorep-mod || exit 1

check_directory_or_file_exists $extsourcedir/scorep-mod/scorep-build
if [ $? -ne 0 ]; then
  bash set_instrumenter_directory.sh $extsourcedir/llvm-instrumentation/build/lib >${allOutputTo} 2>&1

  # TODO We should check whether a cube / scorep install was found and if so, bail out, to know exactly which scorep/cube we get.
  aclocalversion=$( aclocal --version | grep 1.16 ) >${allOutputTo} 2>&1
  if [ -z "$aclocalversion" ]; then
    echo "[PIRA][Score-P] aclocal available in wrong version. Guessing to autoreconf."
    autoreconf -ivf >${allOutputTo} 2>&1
    cd ./vendor/cubelib || exit 1 >${allOutputTo} 2>&1
    autoreconf -ivf >${allOutputTo} 2>&1
    cd ./build-frontend || exit 1 >${allOutputTo} 2>&1
    autoreconf -ivf >${allOutputTo} 2>&1
    cd ../../cubew || exit 1 >${allOutputTo} 2>&1
    autoreconf -ivf >${allOutputTo} 2>&1
    cd ./build-backend || exit 1 >${allOutputTo} 2>&1
    autoreconf -ivf >${allOutputTo} 2>&1
    cd ../build-frontend || exit 1  >${allOutputTo} 2>&1
    autoreconf -ivf >${allOutputTo} 2>&1
    cd $extsourcedir/scorep-mod || exit 1
  fi

  echo_configuring "$scorep_component_name"
  rm -rf scorep-build
  mkdir scorep-build && cd scorep-build
  if [ -z $cube_install_dir ]; then
    #../configure --prefix=$extinstalldir/scorep --enable-shared --disable-static --disable-gcc-plugin --without-shmem "$add_flags"
    ../configure --prefix=$extinstalldir/scorep --enable-shared --disable-static --disable-gcc-plugin --without-shmem "$add_flags"  >${allOutputTo} 2>&1
    cube_install_dir=$extinstalldir/scorep
  else
    #../configure --prefix=$extinstalldir/scorep --with-cubelib=$cube_install_dir --enable-shared --disable-static --disable-gcc-plugin --without-shmem "$add_flags"
    ../configure --prefix=$extinstalldir/scorep --with-cubelib=$cube_install_dir --enable-shared --disable-static --disable-gcc-plugin --without-shmem "$add_flags" >${allOutputTo} 2>&1
  fi
  if [ $? -ne 0 ]; then
    echo "[PIRA] Configuring Score-P failed."
    exit 1
  fi
  echo_building "$scorep_component_name"
  make -j $parallel_jobs >${allOutputTo} 2>&1
  #make -j $parallel_jobs
  if [ $? -ne 0 ]; then
    echo "[PIRA] Building Score-P failed."
    exit 1
  fi
  make install >${allOutputTo} 2>&1
  scorep_install_dir=$extinstalldir/scorep
else
  echo_already_built "$scorep_component_name"
fi

#echo "[PIRA] Adding PIRA Score-P to PATH for subsequent tool chain components."
#export PATH=$extinstalldir/scorep/bin:$PATH

# Extra-P (https://www.scalasca.org/software/extra-p/download.html)
extrap_component_name="Extra-P"
echo_processing "$extrap_component_name"
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
cd $extsourcedir/extrap || exit 1

if [ -z $extrap_install_dir ]; then
  # TODO check if extra-p is already there, if so, no download / no build?
  if [ ! -f "extrap-3.0.tar.gz" ]; then
    echo "[PIRA] Downloading Extra-P"
    wget http://apps.fz-juelich.de/scalasca/releases/extra-p/extrap-3.0.tar.gz >${allOutputTo} 2>&1
    tar xzf extrap-3.0.tar.gz >${allOutputTo} 2>&1
  fi
  cd ./extrap-3.0 || exit 1

  check_directory_or_file_exists $extsourcedir/extrap/extrap-3.0/build
  if [ $? -ne 0 ]; then
    echo_configuring "$extrap_component_name"
    rm -rf build
    mkdir build && cd build || exit 1
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
  
    ../configure --prefix=$extinstalldir/extrap --with-cube=$cube_install_dir CPPFLAGS=-I$pythonheader >${allOutputTo} 2>&1
    #../configure --prefix=$extinstalldir/extrap --with-cube=$cube_install_dir CPPFLAGS=-I$pythonheader
  
    if [ $? -ne 0 ]; then
      echo "[PIRA] Configuring Extra-P failed."
      exit 1
    fi

		echo_building "$extrap_component_name"
    make -j $parallel_jobs >${allOutputTo} 2>&1  
    if [ $? -ne 0 ]; then
      echo "[PIRA] Building Extra-P failed."
      exit 1
    fi
    
		make install >${allOutputTo} 2>&1
    # Manually add the required headers for Extra-P
    cd .. || exit 1
    mkdir -p $extinstalldir/extrap/include
    cp ./include/*.hpp $extinstalldir/extrap/include
   
		extrap_install_dir=$extinstalldir/extrap
  else
    echo_already_built "$extrap_component_name"
  fi
else
  echo "[PIRA] Using $extrap_install_dir"
fi


# CXX Opts
echo "[PIRA] Getting cxxopts library"
cd $extsourcedir || exit 1
if [ ! -d "$extsourcedir/cxxopts" ]; then
    git clone -b 2_1 --single-branch https://github.com/jarro2783/cxxopts cxxopts >${allOutputTo} 2>&1 
fi

# JSON library
echo "[PIRA] Getting json library"
cd $extsourcedir || exit 1
if [ ! -d "$extsourcedir/json" ]; then
    git clone -b v3.9.1 --depth 1 --single-branch https://github.com/nlohmann/json json >${allOutputTo} 2>&1 
fi

metacg_component_name="MetaCG"
echo_processing "$metacg_component_name"
cd $extsourcedir/metacg || exit 1

check_directory_or_file_exists $extsourcedir/metacg/build
if [ $? -ne 0 ]; then
  echo_configuring "$metacg_component_name"
  cmake -B build -S . -DCMAKE_BUILD_TYPE=Debug \
    -DCMAKE_INSTALL_PREFIX=$extinstalldir/metacg \
    -DCUBE_LIB=$cube_install_dir/lib \
    -DCUBE_INCLUDE=$cube_install_dir/include/cubelib \
    -DEXTRAP_INCLUDE=$extrap_install_dir/include \
    -DEXTRAP_LIB=$extrap_install_dir/lib \
    -DSPDLOG_BUILD_SHARED=ON \
    -DCMAKE_VERBOSE_MAKEFILE:BOOL=ON >${allOutputTo} 2>&1
  if [ $? -ne 0 ]; then
    echo "[PIRA] Configuring MetaCG failed."
    exit 1
  fi

  echo_building "$metacg_component_name"
  cmake --build build --parallel ${parallel_jobs} >${allOutputTo} 2>&1
  if [ $? -ne 0 ]; then
    echo "[PIRA] Building MetaCG failed."
    exit 1
  fi

  cmake --install build >${allOutputTo} 2>&1
  if [ ! -d ${extinstalldir}/metacg/bin/out ]; then
    mkdir -p ${extinstalldir}/metacg/bin/out >${allOutputTo} 2>&1
  fi
  metacg_install_dir=$extinstalldir/metacg
else 
  echo_already_built "$metacg_component_name"
  metacg_install_dir=$extinstalldir/metacg
fi

# Installing LLNL's MPI wrapper generator
cd $extsourcedir || exit 1

check_directory_or_file_exists $extsourcedir/mpiwrap
if [ $? -ne 0 ]; then
  echo "[PIRA] installing mpiwrap"
  rm -r mpiwrap >${allOutputTo} 2>&1
  mkdir mpiwrap && cd mpiwrap || exit 1
  wget https://github.com/LLNL/wrap/archive/master.zip >${allOutputTo} 2>&1
  unzip master.zip >${allOutputTo} 2>&1
  rm -rf $extinstalldir/mpiwrap >${allOutputTo} 2>&1
  mkdir $extinstalldir/mpiwrap
  cp wrap-master/wrap.py $extinstalldir/mpiwrap/wrap.py
  mpiwrap_install_dir=$extinstalldir/mpiwrap
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
  mpiwrap_install_dir=$extinstalldir/mpiwrap
fi


cd $extsourcedir || exit 1
check_directory_or_file_exists $extsourcedir/bear
if [ $? -ne 0 ]; then
  echo "[PIRA] Installing bear"
  rm -rf bear >${allOutputTo} 2>&1
  mkdir bear && cd bear || exit 1
  if [ ! -f 2.4.2.tar.gz ]; then
    echo "[PIRA] Downloading bear release 2.4.2"
    wget https://github.com/rizsotto/Bear/archive/2.4.2.tar.gz >${allOutputTo} 2>&1
    tar xzf 2.4.2.tar.gz >${allOutputTo} 2>&1
    mv Bear-2.4.2 bear >${allOutputTo} 2>&1
    cd bear || exit 1 >${allOutputTo} 2>&1
    mkdir build && cd build || exit 1>${allOutputTo} 2>&1
    cmake -DCMAKE_INSTALL_PREFIX=${extinstalldir}/bear .. >${allOutputTo} 2>&1
    make all >${allOutputTo} 2>&1
    make install >${allOutputTo} 2>&1
    cd .. || exit 1
    bear_install_dir=$extinstalldir/bear
  else
    cd bear || exit 1
  fi
else
  echo "[PIRA] Bear already installed"
  bear_install_dir=$extinstalldir/bear
fi

cd $scriptdir || exit 1


echo -e "\n=== PIRA Installation Summary ==="
echo -e "Cube installation dir:\t\t$cube_install_dir"
echo -e "Score-P installation dir:\t$scorep_install_dir"
echo -e "Extra-P installation dir:\t$extrap_install_dir"
echo -e "MetaCG installation dir:\t$metacg_install_dir"
echo -e "mpiwrap installation dir:\t$mpiwrap_install_dir"
echo -e "bear installation dir:\t\t$bear_install_dir"
echo "==== ----"

echo "[PIRA] sed'ing paths to setup_paths.sh script"
sed -i "s|CUBEINSTALLDIR|${cube_install_dir}|g" "./setup_paths.sh"
sed -i "s|SCOREPINSTALLDIR|${scorep_install_dir}|g" ./setup_paths.sh
sed -i "s|EXTRAPINSTALLDIR|${extrap_install_dir}|g" "./setup_paths.sh"
sed -i "s|METACGINSTALLDIR|${metacg_install_dir}|g" ./setup_paths.sh
sed -i "s|MPIWRAPINSTALLDIR|${mpiwrap_install_dir}|g" ./setup_paths.sh
sed -i "s|BEARINSTALLDIR|${bear_install_dir}|g" ./setup_paths.sh
