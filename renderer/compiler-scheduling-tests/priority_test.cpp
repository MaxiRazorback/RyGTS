#include <atomic>
#include <cassert>
#include <future>
#include <memory>
#include <thread>
#include <vector>
#include "video_core/renderer_vulkan/build_queue.h"
int main() {
    using namespace std::chrono_literals;
    Vulkan::BuildQueue queue{1,1};
    std::promise<void> entered,release;
    auto gate=release.get_future().share();
    std::vector<int> order;
    std::atomic<unsigned> compilations{};
    auto claimed=std::make_shared<std::atomic<bool>>(false);
    auto owned=std::make_shared<int>(77);
    std::weak_ptr<int> lifetime=owned;
    std::promise<void> drained;
    std::jthread worker([&](std::stop_token stop) {
        Vulkan::BuildQueue::Job job; bool background;
        while(queue.Pop(job,background,stop)) {
            job();
            if(background) queue.FinishedBackground(); else queue.FinishedForeground();
            job={};
        }
    });
    queue.Push([&] {entered.set_value(); gate.wait();},Vulkan::BuildQueue::Kind::Normal);
    assert(entered.get_future().wait_for(2s)==std::future_status::ready);
    for(int i=0;i<64;++i) queue.Push([&,i] {order.push_back(i);},Vulkan::BuildQueue::Kind::Normal);
    auto required=[&,claimed,owned] {
        if(!claimed->exchange(true)) { assert(*owned==77); ++compilations; order.push_back(77); }
    };
    queue.Push(std::move(required),Vulkan::BuildQueue::Kind::Normal);
    queue.Push([&,claimed,owned] {
        if(!claimed->exchange(true)) {assert(*owned==77); ++compilations; order.push_back(77);}
    },Vulkan::BuildQueue::Kind::Urgent);
    owned.reset();
    assert(!lifetime.expired());
    queue.Push([&] {drained.set_value();},Vulkan::BuildQueue::Kind::Normal);
    release.set_value();
    assert(drained.get_future().wait_for(2s)==std::future_status::ready);
    worker.request_stop(); queue.NotifyAll(); worker.join();
    assert(order.size()==65 && order.front()==77 && compilations==1);
    assert(lifetime.expired());
}
