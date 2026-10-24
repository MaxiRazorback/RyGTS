#include "ryty_gpu/native/menu_snapshot_session.h"
#include <cassert>
#include <thread>
#include <cstdio>
int main() {
    Native::MenuSnapshotSession session;
    assert(session.Idle());
    session.Begin(); // Idle replay starts without a project script read.
    assert(!session.Idle());
    auto old = session.Ending();
    session.Begin(); // Restart/replacement while an older end is in flight.
    session.End(old);
    assert(!session.Idle());
    session.End(session.Ending());
    assert(session.Idle());
    for (int i=0; i<1000; ++i) {
        session.Begin();
        old=session.Ending();
        std::thread a([&] { session.End(old); });
        std::thread b([&] { session.Begin(); });
        a.join(); b.join();
        assert(!session.Idle());
        session.End(session.Ending());
        assert(session.Idle());
    }
    std::puts("PASS: replay start, repeated starts, stale end and concurrent replacement");
}

