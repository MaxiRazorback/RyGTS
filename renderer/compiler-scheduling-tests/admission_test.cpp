#include <cassert>
#include <future>
#include <thread>
#include <vector>
#include "video_core/renderer_vulkan/build_queue.h"
int main() {
 using namespace std::chrono_literals;
 Vulkan::BuildQueue q{3,1};
 std::promise<void> release, a,b,light,third;
 auto gate=release.get_future().share();
 q.Push([&]{a.set_value();gate.wait();},Vulkan::BuildQueue::Kind::Normal,true);
 q.Push([&]{b.set_value();gate.wait();},Vulkan::BuildQueue::Kind::Normal,true);
 std::vector<std::jthread> workers;
 for(int i=0;i<3;++i)workers.emplace_back([&](std::stop_token stop){
  Vulkan::BuildQueue::Job job;bool bg=false,heavy=false;
  while(q.Pop(job,bg,stop,&heavy)){job();if(bg)q.FinishedBackground(heavy);else q.FinishedForeground(heavy);}
 });
 assert(a.get_future().wait_for(2s)==std::future_status::ready);
 assert(b.get_future().wait_for(2s)==std::future_status::ready);
 auto third_done=third.get_future();
 q.Push([&]{third.set_value();},Vulkan::BuildQueue::Kind::Urgent,true);
 q.Push([&]{light.set_value();},Vulkan::BuildQueue::Kind::Normal);
 assert(light.get_future().wait_for(2s)==std::future_status::ready);
 assert(third_done.wait_for(20ms)==std::future_status::timeout);
 release.set_value();
 assert(third_done.wait_for(2s)==std::future_status::ready);
 for(auto& t:workers)t.request_stop();q.NotifyAll();
}
