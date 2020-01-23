// RUN: clang++ -Xclang -load -Xclang ../build/lib/instrumentationlib.so -S -emit-llvm -o - %s | FileCheck %s
//
// CHECK-LABEL: define dso_local void @_Z3foov()
// CHECK: ret
void foo() {
}

// CHECK-LABEL: define dso_local i32 @main(
// CHECK: store i32 %argc
// CHECK: store i8** %argv
// CHECK: ret
int main(int argc, char **argv) {
  return 0;
}
