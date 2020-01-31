#!/usr/bin/env bash

echo "Downloading the external dependencies"


scriptdir="$( cd "$(dirname "$0")" ; pwd -P )"
exttardir=$scriptdir/../extern/tars
extsourcedir=$scriptdir/../extern/src
extinstalldir=$scriptdir/../extern/install

ls $exttardir > /dev/null

if [ $? -ne 0 ]; then
	mkdir $exttardir
fi

cd $exttardir
#cd $extsourcedir

echo "Getting PIRA call graph collector utility tool"
wget https://github.com/jplehr/CGCollector/archive/cgc-v0.1.1.tar.gz
tar xzf cgc-v0.1.1.tar.gz
mv CGCollector-cgc-v0.1.1/* $extsourcedir/cgcollector

cd $exttardir
#cd $extsourcedir

echo "Getting Score-P in PIRA version"
wget https://github.com/jplehr/score-p-v6/archive/scorep-mod-v0.1.tar.gz
tar xzf scorep-mod-v0.1.tar.gz
mv score-p-v6-scorep-mod-v0.1/* $extsourcedir/scorep-mod

cd $exttardir
#cd $extsourcedir

echo "Getting PIRA LLVM-instrumentation plugin"
wget https://github.com/jplehr/llvm-instrumentation/archive/instrumentation-v0.1.tar.gz
tar xzf instrumentation-v0.1.tar.gz
mv llvm-instrumentation-instrumentation-v0.1/* $extsourcedir/llvm-instrumenter

cd $exttardir
#cd $extsourcedir

echo "Getting PIRA PGIS analysis engine"
wget https://github.com/jplehr/PGIS/archive/pgis-v0.1.1.tar.gz
tar xzf pgis-v0.1.1.tar.gz
mv PGIS-pgis-v0.1.1/* $extsourcedir/PGIS

