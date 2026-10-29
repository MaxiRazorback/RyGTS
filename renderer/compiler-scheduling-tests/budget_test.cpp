#include "video_core/renderer_vulkan/compiler_worker_budget.h"
using Vulkan::CompilerWorkerBudget;
constexpr bool Check() {
 for (unsigned n=0; n<=1024; ++n) {
  const auto b=CompilerWorkerBudget::ForLogicalThreads(n);
  const auto total=b.translation+b.pipeline;
  if (b.pipeline==0 || total>8 || total==0) return false;
  if (n>2 && total>n/2) return false;
 }
 const auto large=CompilerWorkerBudget::ForLogicalThreads(32);
 return large.pipeline==6 && large.translation==2 &&
        CompilerWorkerBudget::ForLogicalThreads(4).pipeline==1 &&
        CompilerWorkerBudget::HeavyPipelineLimit==1;
}
static_assert(Check());
int main() {}
