#!/usr/bin/env bash

echo "Downloading the external dependencies"

echo "Running in $PWD"

cp ./public.gitmodules ../.gitmodules
cd ..
git submodule init
git submodule update
cd resources
