// RUN: clang++ -Xclang -load -Xclang ../build/lib/instrumentationlib.so -mllvm --score-p-filter=004.cfg -S -emit-llvm -o - %s | FileCheck %s
//
// CHECK-LABEL: define dso_local void @_Z3foov()
// CHECK: call void @__cyg_profile_func_enter
// CHECK: call void @__cyg_profile_func_exit
void foo() {
}

// CHECK-LABEL: define dso_local i32 @main(
// CHECK: store i32 0, i32* %4
// CHECK: store i32 %0, i32* %5
// CHECK: store i8** %1, i8*** %6
int main(int argc, char **argv) {
  return 0;
}
