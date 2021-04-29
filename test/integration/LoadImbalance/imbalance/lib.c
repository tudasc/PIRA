#include "lib.h"

#include <mpi.h>
#include <unistd.h>
#include <stdio.h>

/*
 * Prints information about MPI environment
 */
void print_mpi_info(int myrank, int nprocs) {

    if(myrank == 0) { // only once
        printf("Size: %d\n", nprocs);
    }

    MPI_Barrier(MPI_COMM_WORLD);

    printf("My Rank: %d\n", myrank);
}

/**
 * This function is load imbalanced on purpose.
 */
void imbalanced(int myrank) {
    // do some heavy work
    int i = 0;
    i++;
    i++;
    i--;
    i+=42;
    i*=2;
    i=0;

    if(myrank % 2 == 0) {
        sleep(1);
    } else {
        sleep(2);
    }
}

/**
 * Perfectly balanced - as all things should be.
 */
void balanced() {
    // do some heavy work
    int i = 0;
    i++;
    i++;
    i--;
    i+=42;
    i*=2;
    i=0;

    // wait for some time
    sleep(1);
}

void test(int myrank) {
    MPI_Barrier(MPI_COMM_WORLD);

    balanced();
    imbalanced(myrank);

    MPI_Barrier(MPI_COMM_WORLD);
}

void func1() {
    sleep(1);
    printf("Running func1\n");
}

void func2() {
    sleep(1);
    printf("Running func2\n");
}