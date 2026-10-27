#include <cassert>
#include <future>
#include <thread>
#include <vector>
#include "video_core/renderer_vulkan/build_queue.h"

int main() {
    using namespace std::chrono_literals;
    Vulkan::BuildQueue queue{3, 3};
    std::promise<void> entered, release, background, urgent, ordinary;
    auto entered_future = entered.get_future();
    auto background_future = background.get_future();
    auto urgent_future = urgent.get_future();
    auto ordinary_future = ordinary.get_future();
    const auto gate = release.get_future().share();
    queue.Push([&] { entered.set_value(); gate.wait(); }, Vulkan::BuildQueue::Kind::Normal, true);
    std::vector<std::jthread> workers;
    for (int i = 0; i < 3; ++i) {
        workers.emplace_back([&](std::stop_token stop) {
            Vulkan::BuildQueue::Job job;
            bool is_background = false, heavy = false;
            while (queue.Pop(job, is_background, stop, &heavy)) {
                job();
                if (is_background) queue.FinishedBackground(heavy);
                else queue.FinishedForeground(heavy);
            }
        });
    }
    assert(entered_future.wait_for(2s) == std::future_status::ready);
    queue.SetBoost(true);
    queue.Push([&] { background.set_value(); }, Vulkan::BuildQueue::Kind::Background, true);
    queue.Push([&] { urgent.set_value(); }, Vulkan::BuildQueue::Kind::Urgent, true);
    queue.Push([&] { ordinary.set_value(); }, Vulkan::BuildQueue::Kind::Normal);
    assert(ordinary_future.wait_for(2s) == std::future_status::ready);
    assert(background_future.wait_for(30ms) == std::future_status::timeout);
    assert(urgent_future.wait_for(30ms) == std::future_status::timeout);
    release.set_value();
    assert(urgent_future.wait_for(2s) == std::future_status::ready);
    assert(background_future.wait_for(2s) == std::future_status::ready);
    for (auto& thread : workers) thread.request_stop();
    queue.NotifyAll();
}
