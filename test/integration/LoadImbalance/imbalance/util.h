#ifndef UTIL_H
#define UTIL_H

typedef void (*Fn) ();

void get_func_ptr(void (**func)(), int i);

#endif