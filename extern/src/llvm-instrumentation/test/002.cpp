// RUN: clang++ -Xclang -load -Xclang ../build/lib/instrumentationlib.so -S -emit-llvm -o - %s | FileCheck %s
// XFAIL: *
void foo() {
}

int main(int argc, char **argv) {
  return 0;
}
