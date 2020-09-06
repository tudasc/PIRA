//===- EntryExitInstrumenter.cpp - Function Entry/Exit Instrumentation ----===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//
//
// This version is shipped as part of the PIRA project
// 
// Modifications 2019 - 2020
//
// Jan-Patrick Lehr
// Jonas Rickert
//
//

#include "llvm/Analysis/GlobalsModRef.h"
#include "llvm/IR/DebugInfoMetadata.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/LegacyPassManager.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/Type.h"
#include "llvm/Pass.h"
#include "llvm/Support/CommandLine.h"
#include "llvm/Support/FileSystem.h"
#include "llvm/Transforms/IPO/PassManagerBuilder.h"
#include "llvm/Transforms/Utils.h"
#include "llvm/Transforms/Utils/EntryExitInstrumenter.h"

#include <fstream>
#include <iostream>
#include <string>
#include <string_view>
#include <unordered_set>

using namespace llvm;

cl::opt<std::string> WhitelistFile("filter-list", cl::desc("Input file w/ mangled names"), cl::value_desc("filename"));
cl::opt<std::string> ConfigFileScoreP("score-p-filter", cl::desc("Score-P filter"), cl::value_desc("filename"));

static void insertCall(Function &CurFn, StringRef Func, Instruction *InsertionPt, DebugLoc DL) {
  Module &M = *InsertionPt->getParent()->getParent()->getParent();
  LLVMContext &C = InsertionPt->getParent()->getContext();

  if (Func == "mcount" || Func == ".mcount" || Func == "llvm.arm.gnu.eabi.mcount" || Func == "\01_mcount" ||
      Func == "\01mcount" || Func == "__mcount" || Func == "_mcount" || Func == "__cyg_profile_func_enter_bare") {
    FunctionCallee Fn = M.getOrInsertFunction(Func, Type::getVoidTy(C));
    CallInst *Call = CallInst::Create(Fn, "", InsertionPt);
    Call->setDebugLoc(DL);
    return;
  }

  if (Func == "__cyg_profile_func_enter" || Func == "__cyg_profile_func_exit") {
    Type *ArgTypes[] = {Type::getInt8PtrTy(C), Type::getInt8PtrTy(C)};

    FunctionCallee Fn = M.getOrInsertFunction(Func, FunctionType::get(Type::getVoidTy(C), ArgTypes, false));

    Instruction *RetAddr =
        CallInst::Create(Intrinsic::getDeclaration(&M, Intrinsic::returnaddress),
                         ArrayRef<Value *>(ConstantInt::get(Type::getInt32Ty(C), 0)), "", InsertionPt);
    RetAddr->setDebugLoc(DL);

    Value *Args[] = {ConstantExpr::getBitCast(&CurFn, Type::getInt8PtrTy(C)), RetAddr};

    CallInst *Call = CallInst::Create(Fn, ArrayRef<Value *>(Args), "", InsertionPt);
    Call->setDebugLoc(DL);
    return;
  }

  // We only know how to call a fixed set of instrumentation functions, because
  // they all expect different arguments, etc.
  report_fatal_error(Twine("Unknown instrumentation function: '") + Func + "'");
}

static bool instrumentFunction(Function &F, bool PostInlining) {
  StringRef EntryAttr = PostInlining ? "instrument-function-entry-inlined" : "instrument-function-entry";

  StringRef ExitAttr = PostInlining ? "instrument-function-exit-inlined" : "instrument-function-exit";

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

static bool instrumentateCallSites(Function &F, const std::unordered_set<std::string> &CallsToInstrument,
                                   bool PostInlining) {
  StringRef CallSiteEntryFunc = "__cyg_profile_func_enter";
  StringRef CallSiteExitFunc = "__cyg_profile_func_exit";

  bool Changed = false;
  for (BasicBlock &BB : F) {
    for (Instruction &I : BB) {
      if (auto *Call = dyn_cast<CallInst>(&I)) {
        if (auto *CalledFunc = Call->getCalledFunction()) {
          if (CallsToInstrument.find(CalledFunc->getName().str()) != CallsToInstrument.end()) {
            if (!CallSiteEntryFunc.empty()) {
              std::cerr << "[LLVMInstrumentor] [DEBUG]: Inserting Call Site Entry Instrumentation" << std::endl;
              DebugLoc DL = Call->getDebugLoc();
              insertCall(*CalledFunc, CallSiteEntryFunc, Call, DL);
              Changed = true;
            }
            if (!CallSiteExitFunc.empty()) {
              std::cerr << "[LLVMInstrumentor] [DEBUG]: Inserting Call Site Exit Instrumentation" << std::endl;
              if (Call->isMustTailCall()) {
                std::cerr << "[LLVMInstrumentor] [Error]: Can not insert call site instrumentation in function "
                          << Call->getName().str() << " because is is declared as \"must tail call\"" << std::endl;
                exit(-1);
              }
              DebugLoc DL = Call->getDebugLoc();
              insertCall(*CalledFunc, CallSiteExitFunc, Call->getNextNode(), DL);
              Changed = true;
            }
          }
        }
      } else if (auto *Invoke = dyn_cast<InvokeInst>(&I)) {
        if (auto *CalledFunc = Invoke->getCalledFunction()) {
          if (CallsToInstrument.find(CalledFunc->getName().str()) != CallsToInstrument.end()) {
            if (!CallSiteEntryFunc.empty()) {
              std::cerr << "[LLVMInstrumentor] [DEBUG]: Inserting Call Site Entry Instrumentation" << std::endl;
              DebugLoc DL = Invoke->getDebugLoc();
              insertCall(*CalledFunc, CallSiteEntryFunc, Invoke, DL);
              Changed = true;
            }
            if (!CallSiteExitFunc.empty()) {
              std::cerr << "[LLVMInstrumentor] [DEBUG]: Inserting Call Site Exit Instrumentation" << std::endl;
              DebugLoc DL = Invoke->getDebugLoc();
              auto IP = &*Invoke->getNormalDest()->getFirstInsertionPt();
              insertCall(*CalledFunc, CallSiteExitFunc, IP, DL);
              Changed = true;
            }
          }
        }
      }
    }
  }
  return Changed;
}

namespace {

struct FilteringEntryExitInstrumenter : public FunctionPass {
  static char ID;
  FilteringEntryExitInstrumenter() : FunctionPass(ID) {
    // initializeEntryExitInstrumenterPass(*PassRegistry::getPassRegistry());
    if (!WhitelistFile.empty()) {
      if (!sys::fs::exists(WhitelistFile.c_str())) {
        std::cerr << "[LLVMInstrumentor] [Error]: Filter file (" << WhitelistFile.c_str() << ") does not exist."
                  << std::endl;
        exit(-1);
      } else {
        std::ifstream filter(WhitelistFile.c_str());
        for (std::string in; std::getline(filter, in);) {
          filterList.insert(in);
        }
      }
    }

    if (!ConfigFileScoreP.empty()) {
      if (!sys::fs::exists(ConfigFileScoreP.c_str())) {
        std::cerr << "[LLVMInstrumentor] [Error]: Filter file (" << WhitelistFile.c_str() << ") does not exist."
                  << std::endl;
        exit(-1);
      } else {
        std::ifstream filter(ConfigFileScoreP.c_str());
        std::string linebuffer;
        std::string_view linebuffer_view;

        enum class ParserState {
          Normal /*Content without special meaning*/,
          Block /*Func filter block*/,
          Include /*include directive that has no item yet*/,
          IncludeFinished /*include directive that can be finished*/,
        };

        /// Returns the next token in the filter file as the parameter out.
        /// Skips all whitespace and comments, returns false if no token exists
        auto get_next_token = [&filter, &linebuffer, &linebuffer_view](std::string_view &out, ParserState state) {
          const std::string whitespace = " \t\r";
          auto first_not_whitespace = linebuffer_view.find_first_not_of(whitespace);
          while (first_not_whitespace == std::string_view::npos || linebuffer_view[first_not_whitespace] == '#') {
            if (!std::getline(filter, linebuffer)) {
              if (state != ParserState::Normal) {
                std::cerr << "[LLVMInstrumentor] [Error]: Unexpected ending "
                             "in filter file."
                          << std::endl;
                exit(-1);
              }
              return false;
            }
            linebuffer_view = linebuffer;
            first_not_whitespace = linebuffer_view.find_first_not_of(whitespace);
          }
          // Skip whitespace and commets
          linebuffer_view.remove_prefix(first_not_whitespace);
          auto endtoken = linebuffer_view.find_first_of(" \t\r#");
          if (endtoken == std::string_view::npos) {
            endtoken = linebuffer_view.length();
          }
          out = std::string_view(linebuffer_view.data(), endtoken);
          // std::cerr << "Token: \"" << out << "\"" << std::endl;
          linebuffer_view.remove_prefix(endtoken);
          return true;
        };

        auto parser_error = [](std::string_view token) {
          std::cerr << "[LLVMInstrumentor] [Error]: Unexpected token \"" << token << "\" in filter file." << std::endl;
          exit(-1);
        };

        ParserState state = ParserState::Normal;

        std::string_view token;
        while (state == ParserState::IncludeFinished || get_next_token(token, state)) {
          if (token == "SCOREP_REGION_NAMES_BEGIN") {
            if (state == ParserState::Normal) {
              state = ParserState::Block;
            } else {
              parser_error(token);
            }
          } else if (token == "SCOREP_REGION_NAMES_END") {
            if (state == ParserState::Block || state == ParserState::IncludeFinished) {
              state = ParserState::Normal;
            } else {
              parser_error(token);
            }
          } else if (token == "INCLUDE") {
            if (state == ParserState::Block || state == ParserState::IncludeFinished) {
              state = ParserState::Include;
            } else {
              parser_error(token);
            }
          } else {
            if (state != ParserState::Include) {
              parser_error(token);
            }
            // Helper function to parse a function name. sets token to the next token
            auto get_func_name = [&]() {
              // Function to check if a string contains an unsupported wildcard
              auto warn_unsupported_wildcard = [](const std::string &name) {
                const auto start_wildcard = name.find_first_of("*?[]");
                if (start_wildcard != std::string::npos) {
                  std::cerr << "[LLVMInstrumentor] [Warning]: Unsupported "
                               "wildcard in \""
                            << name << "\"" << std::endl;
                }
              };

              std::string prev_token(token);
              // Look ahead one token to check if we need to handle a mangeled name
              get_next_token(token, state);
              if (token != "MANGLED") {
                warn_unsupported_wildcard(prev_token);
                return prev_token;
              } else {
                // Skip MANGLED keyword
                get_next_token(token, state);
                prev_token = token;
                get_next_token(token, state);
                warn_unsupported_wildcard(prev_token);
                return prev_token;
              }
            };
            const auto fname = get_func_name();
            if (token == "->") {
              get_next_token(token, state);
              const auto called_function = get_func_name();
              const auto csli = callSiteList.find(fname);
              if (csli != callSiteList.end()) {
                csli->second.insert(called_function);
              } else {
                std::unordered_set<std::string> called_func_set;
                called_func_set.insert(called_function);
                callSiteList.insert({fname, called_func_set});
              }
            } else {
              filterList.insert(fname);
            }
            state = ParserState::IncludeFinished;
          }
        }
        if (state != ParserState::Normal) {
          std::cerr << "[LLVMInstrumentor] [Error]: Unexpected ending "
                       "in filter file."
                    << std::endl;
          exit(-1);
        }
      }
    }
  }
  void getAnalysisUsage(AnalysisUsage &AU) const override { AU.addPreserved<GlobalsAAWrapperPass>(); }
  bool isFiltered(Function &F) const { return filterList.find(F.getName().str()) != filterList.end(); }
  bool runOnFunction(Function &F) override {
    bool changed = false;
    if (isFiltered(F)) {
      std::cerr << "[LLVMInstrumentor] [DEBUG]: Running on " + F.getName().str() << std::endl;
      changed = ::instrumentFunction(F, false);
    }
    const auto c = callSiteList.find(F.getName());
    if (c != callSiteList.end()) {
      std::cerr << "[LLVMInstrumentor] [DEBUG]: Running call site instrumentation on " + F.getName().str() << std::endl;
      changed = ::instrumentateCallSites(F, c->second, false) || changed;
    }
    return changed;
  }
  StringRef getPassName() const override { return "Filtering Entry Exit Instrumentation"; }

  std::unordered_set<std::string> filterList;  // whitelist filter
  std::unordered_map<std::string, std::unordered_set<std::string>>
      callSiteList;  // List of all call sites that should be instrumented
};
char FilteringEntryExitInstrumenter::ID = 0;

struct FilteringPostInlineEntryExitInstrumenter : public FunctionPass {
  static char ID;
  FilteringPostInlineEntryExitInstrumenter() : FunctionPass(ID) {
    // initializePostInlineEntryExitInstrumenterPass(
    //*PassRegistry::getPassRegistry());
  }
  void getAnalysisUsage(AnalysisUsage &AU) const override { AU.addPreserved<GlobalsAAWrapperPass>(); }
  bool runOnFunction(Function &F) override { return ::instrumentFunction(F, true); }
};
char FilteringPostInlineEntryExitInstrumenter::ID = 0;
}  // namespace

static void registerFilteringEEInstrumenter(const PassManagerBuilder &b, llvm::legacy::PassManagerBase &PM) {
  PM.add(new FilteringEntryExitInstrumenter());
}

static RegisterStandardPasses RegisterFilteringEEINstrumenter(PassManagerBuilder::EP_EarlyAsPossible,
                                                              registerFilteringEEInstrumenter);
