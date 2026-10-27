#include <cassert>
#include <future>
#include <chrono>
#include "video_core/renderer_vulkan/translation_job_match.h"
struct Job { int hw_stage, sw_stage, runtime_info, start; std::shared_future<void> done; };
int main() {
    std::promise<void> needed, unrelated;
    auto pending=unrelated.get_future().share();
    Job jobs[] = {{1,2,3,4,needed.get_future().share()},
                  {1,5,3,4,pending},
                  {1,2,6,4,pending}};
    needed.set_value();
    unsigned waits=0;
    for (auto& job: jobs) {
        if (Vulkan::MatchesTranslationRequest(job,1,2,3,4)) {
            assert(job.done.wait_for(std::chrono::milliseconds(100)) == std::future_status::ready);
            ++waits;
        }
    }
    assert(waits==1);
    assert(jobs[1].done.wait_for(std::chrono::milliseconds(0)) == std::future_status::timeout);
}
