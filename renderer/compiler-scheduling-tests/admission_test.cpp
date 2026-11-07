#include <atomic>
#include <cassert>
#include <future>
#include <thread>
#include <vector>
#include "video_core/renderer_vulkan/build_queue.h"
int main() {
 using namespace std::chrono_literals;
 Vulkan::BuildQueue q{3,1};
 std::promise<void> release,a,b,light,urgent;
 auto gate=release.get_future().share();
 auto b_done=b.get_future();auto urgent_done=urgent.get_future();
 std::atomic<unsigned> active{};
 auto heavy=[&](std::promise<void>& started,bool block){
  assert(active.fetch_add(1)==0);started.set_value();if(block)gate.wait();
  assert(active.fetch_sub(1)==1);
 };
 q.Push([&]{heavy(a,true);},Vulkan::BuildQueue::Kind::Normal,true);
 q.Push([&]{heavy(b,false);},Vulkan::BuildQueue::Kind::Normal,true);
 std::vector<std::jthread> workers;
 for(int i=0;i<3;++i)workers.emplace_back([&](std::stop_token stop){
  Vulkan::BuildQueue::Job job;bool bg=false,is_heavy=false;
  while(q.Pop(job,bg,stop,&is_heavy)){
   job();if(bg)q.FinishedBackground(is_heavy);else q.FinishedForeground(is_heavy);
  }
 });
 assert(a.get_future().wait_for(2s)==std::future_status::ready);
 assert(b_done.wait_for(20ms)==std::future_status::timeout);
 q.Push([&]{heavy(urgent,false);},Vulkan::BuildQueue::Kind::Urgent,true);
 q.Push([&]{light.set_value();},Vulkan::BuildQueue::Kind::Normal);
 assert(light.get_future().wait_for(2s)==std::future_status::ready);
 assert(urgent_done.wait_for(20ms)==std::future_status::timeout);
 release.set_value();
 assert(urgent_done.wait_for(2s)==std::future_status::ready);
 assert(b_done.wait_for(2s)==std::future_status::ready);
 for(auto& t:workers)t.request_stop();q.NotifyAll();
}
