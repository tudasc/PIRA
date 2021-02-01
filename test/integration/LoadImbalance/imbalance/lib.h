#ifndef LIB_H
#define LIB_H

// General
void print_mpi_info(int myrank, int nprocs);


// imbalance detection test
void imbalanced(int myrank);

void balanced();

void test(int myrank);


// function pointer test
void func1();
void func2();

#endif