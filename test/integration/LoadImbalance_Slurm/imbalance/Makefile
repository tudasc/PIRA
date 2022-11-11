all: imbalance

imbalance: lib util
	$(CC) -O0 main.c -ggdb -L. -l:libtest.so -l:libutil.so -o imbalance-dynamic.out
	$(CC) -O0 main.c -ggdb -rdynamic -L. -l:libtest.a -l:libutil.a -o imbalance-static.out

lib:
	$(CC) -O0 -ggdb -c -Wall -fpic lib.c -o lib.o
	$(CC) -O0 -ggdb -shared -o libtest.so lib.o
	ar rcs libtest.a lib.o

util:
	$(CC) -O0 -ggdb -c -Wall -fpic util.c -o util.o
	$(CC) -O0 -ggdb -shared -o libutil.so util.o
	ar rcs libutil.a util.o

clean:
	rm -f *.out *.o *.so *.a
