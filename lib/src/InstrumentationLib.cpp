//===- EntryExitInstrumenter.cpp - Function Entry/Exit Instrumentation ----===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//
//
// Modifications by JP Lehr 2019

#include "llvm/Transforms/Utils/EntryExitInstrumenter.h"
#include "llvm/Analysis/GlobalsModRef.h"
#include "llvm/IR/DebugInfoMetadata.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/Type.h"
#include "llvm/IR/LegacyPassManager.h"
#include "llvm/Pass.h"
#include "llvm/Support/CommandLine.h"
#include "llvm/Support/FileSystem.h"
#include "llvm/Transforms/Utils.h"
#include "llvm/Transforms/IPO/PassManagerBuilder.h"

#include <iostream>
#include <fstream>
#include <unordered_set>
#include <string>

using namespace llvm;

cl::opt<std::string> WhitelistFile("filter-list", cl::desc("Input file w/ mangled names"), cl::value_desc("filename"));

static void insertCall(Function &CurFn, StringRef Func,
                       Instruction *InsertionPt, DebugLoc DL) {
  Module &M = *InsertionPt->getParent()->getParent()->getParent();
  LLVMContext &C = InsertionPt->getParent()->getContext();

  if (Func == "mcount" ||
      Func == ".mcount" ||
      Func == "llvm.arm.gnu.eabi.mcount" ||
      Func == "\01_mcount" ||
      Func == "\01mcount" ||
      Func == "__mcount" ||
      Func == "_mcount" ||
      Func == "__cyg_profile_func_enter_bare") {
    FunctionCallee Fn = M.getOrInsertFunction(Func, Type::getVoidTy(C));
    CallInst *Call = CallInst::Create(Fn, "", InsertionPt);
    Call->setDebugLoc(DL);
    return;
  }

  if (Func == "__cyg_profile_func_enter" || Func == "__cyg_profile_func_exit") {
    Type *ArgTypes[] = {Type::getInt8PtrTy(C), Type::getInt8PtrTy(C)};

    FunctionCallee Fn = M.getOrInsertFunction(
        Func, FunctionType::get(Type::getVoidTy(C), ArgTypes, false));

    Instruction *RetAddr = CallInst::Create(
        Intrinsic::getDeclaration(&M, Intrinsic::returnaddress),
        ArrayRef<Value *>(ConstantInt::get(Type::getInt32Ty(C), 0)), "",
        InsertionPt);
    RetAddr->setDebugLoc(DL);

    Value *Args[] = {ConstantExpr::getBitCast(&CurFn, Type::getInt8PtrTy(C)),
                     RetAddr};

    CallInst *Call =
        CallInst::Create(Fn, ArrayRef<Value *>(Args), "", InsertionPt);
    Call->setDebugLoc(DL);
    return;
  }

  // We only know how to call a fixed set of instrumentation functions, because
  // they all expect different arguments, etc.
  report_fatal_error(Twine("Unknown instrumentation function: '") + Func + "'");
}

static bool runOnFunction(Function &F, bool PostInlining) {
  StringRef EntryAttr = PostInlining ? "instrument-function-entry-inlined"
                                     : "instrument-function-entry";

  StringRef ExitAttr = PostInlining ? "instrument-function-exit-inlined"
                                    : "instrument-function-exit";

  StringRef EntryFunc = "__cyg_profile_func_enter";
  StringRef ExitFunc = "__cyg_profile_func_exit";

  bool Changed = false;

  // If the attribute is specified, insert instrumentation and then "consume"
  // the attribute so that it's not inserted again if the pass should happen to
  // run later for some reason.

  if (!EntryFunc.empty()) {
    std::cerr << "[LLVMInstrumentor] [DEBUG]: Inserting Entry Instrumentation" << std::endl;
    DebugLoc DL;
    if (auto SP = F.getSubprogram())
      DL = DebugLoc::get(SP->getScopeLine(), 0, SP);

    insertCall(F, EntryFunc, &*F.begin()->getFirstInsertionPt(), DL);
    Changed = true;
    F.removeAttribute(AttributeList::FunctionIndex, EntryAttr);
  }

  if (!ExitFunc.empty()) {
    std::cerr << "[LLVMInstrumentor] [DEBUG]: Inserting Exit Instrumentation" << std::endl;
    for (BasicBlock &BB : F) {
      Instruction *T = BB.getTerminator();
      if (!isa<ReturnInst>(T))
        continue;

      // If T is preceded by a musttail call, that's the real terminator.
      Instruction *Prev = T->getPrevNode();
      if (BitCastInst *BCI = dyn_cast_or_null<BitCastInst>(Prev))
        Prev = BCI->getPrevNode();
      if (CallInst *CI = dyn_cast_or_null<CallInst>(Prev)) {
        if (CI->isMustTailCall())
          T = CI;
      }

      DebugLoc DL;
      if (DebugLoc TerminatorDL = T->getDebugLoc())
        DL = TerminatorDL;
      else if (auto SP = F.getSubprogram())
        DL = DebugLoc::get(0, 0, SP);

      insertCall(F, ExitFunc, T, DL);
      Changed = true;
    }
    F.removeAttribute(AttributeList::FunctionIndex, ExitAttr);
  }

  return Changed;
}

namespace {

  struct FilteringEntryExitInstrumenter : public FunctionPass {
  static char ID;
  FilteringEntryExitInstrumenter() : FunctionPass(ID) {
    //initializeEntryExitInstrumenterPass(*PassRegistry::getPassRegistry());
    if (!WhitelistFile.empty()) {
      if (!sys::fs::exists(WhitelistFile.c_str())) {
        std::cerr << "[LLVMInstrumentor] [Error]: Filter file (" << WhitelistFile.c_str() << ") does not exist." << std::endl;
        exit(-1);
      } else {
        std::ifstream filter(WhitelistFile.c_str());
        for (std::string in; std::getline(filter, in);) {
          filterList.insert(in);
        }
      }
    }
  }
  void getAnalysisUsage(AnalysisUsage &AU) const override {
    AU.addPreserved<GlobalsAAWrapperPass>();
  }
  bool isFiltered(Function &F) const {
    return filterList.find(F.getName().str()) != filterList.end();
  }
  bool runOnFunction(Function &F) override {
    if (isFiltered(F)) {
      std::cerr << "[LLVMInstrumentor] [DEBUG]: Running on " + F.getName().str() << std::endl;
      return ::runOnFunction(F, false);
    }
    return false;
  }
  StringRef getPassName() const override { return "Filtering Entry Exit Instrumentation"; }

  std::unordered_set<std::string> filterList; // whitelist filter
};
char FilteringEntryExitInstrumenter::ID = 0;

struct FilteringPostInlineEntryExitInstrumenter : public FunctionPass {
  static char ID;
  FilteringPostInlineEntryExitInstrumenter() : FunctionPass(ID) {
    //initializePostInlineEntryExitInstrumenterPass(
        //*PassRegistry::getPassRegistry());
  }
  void getAnalysisUsage(AnalysisUsage &AU) const override {
    AU.addPreserved<GlobalsAAWrapperPass>();
  }
  bool runOnFunction(Function &F) override { return ::runOnFunction(F, true); }
};
char FilteringPostInlineEntryExitInstrumenter::ID = 0;
}

static void registerFilteringEEInstrumenter(const PassManagerBuilder &b, llvm::legacy::PassManagerBase &PM) {
  PM.add(new FilteringEntryExitInstrumenter());
}

static RegisterStandardPasses RegisterFilteringEEINstrumenter(PassManagerBuilder::EP_EarlyAsPossible, registerFilteringEEInstrumenter);
