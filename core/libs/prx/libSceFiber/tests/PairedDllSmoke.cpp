#include <windows.h>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>

using Entry = void (__attribute__((sysv_abi))*)(std::uint64_t, std::uint64_t);
using Initialize = int (__attribute__((sysv_abi))*)(void*, const char*, Entry, std::uint64_t, void*, std::uint64_t, const void*, std::uint32_t);
using Finalize = int (__attribute__((sysv_abi))*)(void*);
using Run = int (__attribute__((sysv_abi))*)(void*, std::uint64_t, std::uint64_t*);
using Return = int (__attribute__((sysv_abi))*)(std::uint64_t, std::uint64_t*);
using Register = int (*)(std::uint64_t, std::uint64_t);
using Unregister = void (*)(std::uint64_t, std::uint64_t);
static Finalize finalize_fiber = nullptr;
static Return return_to_thread = nullptr;
static void* running_object = nullptr;
static constexpr int StateError = static_cast<int>(0x80590006);

static void Check(bool value, const char* message) {
    if (!value) { std::fprintf(stderr, "FAIL: %s (Win32 error %lu)\n", message, GetLastError()); std::abort(); }
}

static void __attribute__((sysv_abi, noinline)) Body(std::uint64_t, std::uint64_t) {
    volatile unsigned char frame[0x31000];
    for (unsigned i = 0; i < sizeof(frame); i += 4096) frame[i] = 0x37;
    Check(finalize_fiber(running_object) == StateError, "actual running finalize rejected");
    return_to_thread(0x55, nullptr);
    std::abort();
}

int main(int argc, char** argv) {
    Check(argc == 3, "usage: paired_smoke <staged libSceFiber.prx> <staged libSceVideoOut.prx>");
    Check(GetModuleHandleA("libSceVideoOut.prx") == nullptr, "isolated process starts without renderer");
    const auto fiber = LoadLibraryExA(argv[1], nullptr, LOAD_WITH_ALTERED_SEARCH_PATH);
    Check(fiber != nullptr, "load actual patched Fiber DLL");
    // NIDs are checked against the staged DLL's export RVAs and COFF symbol table.
    const auto initialize = reinterpret_cast<Initialize>(GetProcAddress(fiber, "hVYD7Ou2pCQ"));
    finalize_fiber = reinterpret_cast<Finalize>(GetProcAddress(fiber, "JeNX5F-NzQU"));
    const auto run = reinterpret_cast<Run>(GetProcAddress(fiber, "a0LLrZWac0M"));
    return_to_thread = reinterpret_cast<Return>(GetProcAddress(fiber, "B0ZX2hx9DMw"));
    Check(initialize && finalize_fiber && run && return_to_thread, "resolve actual patched Fiber NIDs");
    alignas(16) unsigned char object[256];
    std::memset(object, 0xa5, sizeof(object));
    constexpr std::uint64_t size = 1 << 20;
    auto* context = static_cast<unsigned char*>(VirtualAlloc(nullptr, size, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE));
    Check(context != nullptr, "allocate CPU stack context");
    std::memset(context, 0x37, size);
    Check(initialize(object, "before renderer load", Body, 0, context + 16, size - 32, nullptr, 0) == StateError,
          "actual missing renderer fails closed");
    for (auto byte : object) Check(byte == 0xa5, "failed actual init leaves object untouched");
    for (unsigned i = 0; i < size; ++i) Check(context[i] == 0x37, "failed actual init leaves context untouched");

    // DllMain sees an ordinary host executable (no .gtcode). No renderer creation,
    // Vulkan instance/device, guest startup or game code is requested by this smoke.
    const auto renderer = LoadLibraryExA(argv[2], nullptr, LOAD_WITH_ALTERED_SEARCH_PATH);
    Check(renderer != nullptr, "load actual native DLL before renderer initialization");
    const auto acquire = reinterpret_cast<Register>(GetProcAddress(renderer, "RytyGpuRegisterCpuStack"));
    const auto release = reinterpret_cast<Unregister>(GetProcAddress(renderer, "RytyGpuUnregisterCpuStack"));
    Check(acquire && release, "resolve actual paired host C ABI exports");
    Check(acquire(0, 0) == 0, "actual registration rejects invalid range");
    const auto address = reinterpret_cast<std::uint64_t>(context + 16);
    Check(acquire(address, size - 32) == 1, "static registry accepts partial pages before singleton");
    Check(acquire(address, size - 32) == 1, "static registry accepts exact duplicate before singleton");
    Check(acquire(address + 16, size - 64) == 1, "static registry accepts overlap before singleton");
    release(address + 16, size - 64);
    release(address, size - 32);
    release(address, size - 32);
    Check(initialize(object, "actual paired hooks", Body, 0, context + 16, size - 32, nullptr, 0) == 0,
          "actual Fiber registers context before singleton");
    Check(initialize(object, "live reinit", Body, 0, context + 16, size - 32, nullptr, 0) == StateError,
          "actual live reinit rejected");
    Check(FreeLibrary(renderer) != 0, "drop caller renderer reference");
    Check(GetModuleHandleA("libSceVideoOut.prx") != nullptr, "Fiber registration holds renderer DLL lifetime");
    running_object = object;
    std::uint64_t result = 0;
    Check(run(object, 0, &result) == 0 && result == 0x55, "actual DLL large-frame fiber execution");
    Check(finalize_fiber(object) == 0, "actual successful finalize unregisters context");
    Check(GetModuleHandleA("libSceVideoOut.prx") == nullptr, "actual finalize releases renderer DLL reference");
    Check(VirtualFree(context, 0, MEM_RELEASE) != 0, "release CPU stack context");
    Check(FreeLibrary(fiber) != 0, "release actual Fiber DLL");
    std::puts("PASS: actual patched Fiber/native DLL C ABI and pre-renderer-init lifetime smoke; no GPU/mirror integration tested");
}
