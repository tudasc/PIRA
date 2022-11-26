#include "util.h"
#include "lib.h"

#include <stddef.h>

void get_func_ptr(void (**func)(), int i) {
    void (*r)() = NULL;

    switch (i) {
        case 0: r = func1; break;
        default: r = func2;
    }

    *func = r;
}