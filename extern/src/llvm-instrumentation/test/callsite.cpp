// RUN: clang++ -Xclang -load -Xclang ../build/lib/instrumentationlib.so -mllvm --score-p-filter=callsite.cfg -S -emit-llvm -o - %s | FileCheck %s
//

// CHECK-LABEL: define dso_local i32 @_Z1av()
// CHECK-NOT: call void @__cyg_profile_func_enter
// CHECK-NOT: call void @__cyg_profile_func_exit
int a() {
  int b = 3;
  return b;
}

// CHECK-LABEL: define dso_local i32 @_Z1cv()
// CHECK: call void @__cyg_profile_func_enter
// CHECK: call i32 @_Z1av()
// CHECK: call void @__cyg_profile_func_exit
int c() {
  int some_var = 2;
  a();
  return 7;
}

// CHECK-LABEL: define dso_local void @_Z3foov()
// CHECK-NOT: call void @__cyg_profile_func_enter
// CHECK-NOT: call void @__cyg_profile_func_exit
void foo() {}

// CHECK-LABEL: define dso_local i32 @main(
// CHECK: store i32 %argc
// CHECK: store i8** %argv
int main(int argc, char **argv) { return 0; }
