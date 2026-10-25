#include <cassert>
#include <future>
#include <memory>
#include <stdexcept>
#include <thread>
#include <vector>
#include "video_core/renderer_vulkan/build_queue.h"

int main() {
    using namespace std::chrono_literals;
    const auto caller = std::this_thread::get_id();
    std::atomic<int> running{}, peak{};
    std::weak_ptr<int> queued_lifetime;
    {
        Vulkan::BuildQueue queue{2, 1};
        std::vector<std::jthread> workers;
        for (int i = 0; i < 4; ++i) workers.emplace_back([&](std::stop_token stop) {
            Vulkan::BuildQueue::Job job;
            bool background;
            while (queue.Pop(job, background, stop)) {
                job();
                if (background) queue.FinishedBackground(); else queue.FinishedForeground();
                job = {};
            }
        });
        std::vector<std::future<int>> done;
        for (int i = 0; i < 40; ++i) {
            auto owned = std::make_shared<int>(i);
            auto task = std::make_shared<std::packaged_task<int()>>([&, owned] {
                assert(std::this_thread::get_id() != caller);
                int n = ++running;
                int old = peak.load();
                while (n > old && !peak.compare_exchange_weak(old, n)) {}
                std::this_thread::sleep_for(1ms);
                --running;
                if (*owned == 17) throw std::runtime_error("compiler failure");
                return *owned;
            });
            done.push_back(task->get_future());
            queue.Push([task] { (*task)(); }, Vulkan::BuildQueue::Kind::Urgent);
        }
        int failures = 0;
        for (int i = 0; i < 40; ++i) {
            assert(done[i].wait_for(5s) == std::future_status::ready);
            try { assert(done[i].get() == i); }
            catch (const std::runtime_error&) { assert(i == 17); ++failures; }
        }
        assert(failures == 1 && peak <= 2 && running == 0);
        // Queued work owns its inputs; stopping/joining workers and destroying the queue
        // must release jobs that never ran, without detached access to cache resources.
        queue.PauseBackground(Vulkan::BuildQueue::Clock::now() + 1h);
        auto owned = std::make_shared<int>(42);
        queued_lifetime = owned;
        queue.Push([owned] { assert(false); }, Vulkan::BuildQueue::Kind::Background);
        owned.reset();
        assert(!queued_lifetime.expired());
        for (auto& worker : workers) worker.request_stop();
        queue.NotifyAll();
        workers.clear();
    }
    assert(queued_lifetime.expired());
}
