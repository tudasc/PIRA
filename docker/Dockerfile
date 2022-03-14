FROM ubuntu:20.04

WORKDIR /usr/src

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -y && apt-get upgrade -y && apt-get install -y gcc g++ cmake python3 apt-utils wget gnupg qt5-default git autoconf automake libtool zlib1g-dev zlib1g vim unzip python3-pip python3-pytest python3-pytest-cov openmpi-bin openmpi-common bison flex

RUN wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key| apt-key add - && apt-get install -y libllvm10 llvm-10 llvm-10-dev llvm-10-doc llvm-10-examples llvm-10-runtime clang-10 clang-tools-10 libclang-common-10-dev libclang-10-dev libclang1-10 clang-format-10  clang-tidy-10

RUN ln -s /usr/bin/clang-10 /usr/bin/clang && ln -s /usr/bin/clang++-10 /usr/bin/clang++

RUN mkdir pira
COPY resources pira/resources
COPY extern pira/extern
COPY .gitmodules pira/.gitmodules
COPY .git pira/.git
RUN cd pira && git submodule update --init && cd resources && ./build_submodules.sh $(nproc) --with-mpi=openmpi
RUN cd pira && sed -i "1s/.*/#!\/usr\/bin\/env python3/" ./extern/install/mpiwrap/wrap.py
COPY . pira
