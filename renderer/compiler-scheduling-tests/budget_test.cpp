#include "video_core/renderer_vulkan/compiler_worker_budget.h"
using Vulkan::CompilerWorkerBudget;
constexpr bool Check() {
 for(unsigned n=0;n<=1024;++n) {
  auto b=CompilerWorkerBudget::ForLogicalThreads(n);
  if(b.pipeline==0 || b.translation+b.pipeline!=(n>2?n-2:1))return false;
 }
 return CompilerWorkerBudget::ForLogicalThreads(32).pipeline>14 &&
        CompilerWorkerBudget::ForLogicalThreads(4).translation==1;
}
static_assert(Check());
int main() {}
