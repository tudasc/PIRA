#include <mpi.h>

#include "lib.h"
#include "util.h"

#include <stdio.h>
#include <unistd.h>
#include <stddef.h>

void function_pointer_test() {
    void (*r)() = NULL;

    get_func_ptr(&r, 0);

    r();
}


/**
 * Main function
 */
int main(int argc, char** argv ) {
    MPI_Init( &argc, &argv );

    int myrank, nprocs;
    MPI_Comm_rank( MPI_COMM_WORLD, &myrank );
    MPI_Comm_size( MPI_COMM_WORLD, &nprocs );

    // function pointer test
    function_pointer_test();
    // Fn func = get_func_ptr(0);
    // func();

    // print_mpi_info(myrank, nprocs);

    // imbalance detection test
    test(myrank);

    printf("%d is done.\n", myrank);

    MPI_Barrier(MPI_COMM_WORLD);

    MPI_Finalize();

    return 0;
}



