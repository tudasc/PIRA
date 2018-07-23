def get_method():
  return {'passive': True, 'active': False}


def passive(benchmark, **kwargs):
  invoc_str = 'make arch=Linux_Serial CXX=clang++ INSTRUMENTATION="-finstrument-functions -finstrument-functions-whitelist-inputfile=/home/j_lehr/all_repos/gh-jplehr-pgoe/out/instrumented-test_run-hpcg30.txt"'
  invoc_str += ' && clang++  -DHPCG_NO_MPI -DHPCG_NO_OPENMP -I./src -I./src/Linux_Serial  -fomit-frame-pointer -O3 -funroll-loops -W -Wall -pedantic -finstrument-functions -finstrument-functions-whitelist-inputfile=/home/j_lehr/all_repos/gh-sachinmanawadi-pgoe/out/instrumented-test_run-hpcg30.txt src/main.o src/CG.o src/CG_ref.o src/TestCG.o src/ComputeResidual.o src/ExchangeHalo.o src/GenerateGeometry.o src/GenerateProblem.o src/GenerateProblem_ref.o src/CheckProblem.o src/MixedBaseCounter.o src/OptimizeProblem.o src/ReadHpcgDat.o src/ReportResults.o src/SetupHalo.o src/SetupHalo_ref.o src/TestSymmetry.o src/TestNorms.o src/WriteProblem.o src/YAML_Doc.o src/YAML_Element.o src/ComputeDotProduct.o src/ComputeDotProduct_ref.o src/mytimer.o src/ComputeOptimalShapeXYZ.o src/ComputeSPMV.o src/ComputeSPMV_ref.o src/ComputeSYMGS.o src/ComputeSYMGS_ref.o src/ComputeWAXPBY.o src/ComputeWAXPBY_ref.o src/ComputeMG_ref.o src/ComputeMG.o src/ComputeProlongation_ref.o src/ComputeRestriction_ref.o src/CheckAspectRatio.o src/GenerateCoarseProblem.o src/init.o src/finalize.o .scorep_init.o -o bin/test_run-xhpcg `scorep-config --nomemory --ldflags` `scorep-config --nomemory --libs` -lscorep_adapter_memory_event_cxx_L64 -lscorep_adapter_memory_mgmt -lscorep_alloc_metric'
  return invoc_str


def active(benchmark, **kwargs):
  pass
