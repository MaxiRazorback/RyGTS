#include <windows.h>
#include <array>
#include <atomic>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <thread>

static bool module_available = true;
static bool register_available = true;
static bool unregister_available = true;
static bool registration_succeeds = true;
static bool make_context_writable = false;
static std::atomic<unsigned> module_references{0}, registrations{0}, releases{0};
static std::uint64_t expected_address = 0, expected_size = 0;
static const void* untouched_object = nullptr;
static const void* untouched_context = nullptr;

static void Check(bool value, const char* message) {
    if (!value) { std::fprintf(stderr, "FAIL: %s\n", message); std::abort(); }
}

static int MockRegister(std::uint64_t address, std::uint64_t size) {
    Check(address == expected_address && size == expected_size, "register exact range");
    if (untouched_object) {
        const auto* bytes = static_cast<const unsigned char*>(untouched_object);
        for (unsigned i = 0; i < 256; ++i) Check(bytes[i] == 0xa5, "object written before registration");
    }
    if (untouched_context) {
        const auto* bytes = static_cast<const unsigned char*>(untouched_context);
        for (unsigned i = 0; i < size; ++i) Check(bytes[i] == 0x37, "context written before registration");
    }
    ++registrations;
    if (registration_succeeds && make_context_writable) {
        DWORD old = 0;
        Check(VirtualProtect(reinterpret_cast<void*>(address), size, PAGE_READWRITE, &old) != 0,
              "make context writable during registration");
    }
    return registration_succeeds ? 1 : 0;
}

static void MockUnregister(std::uint64_t address, std::uint64_t size) {
    Check(address == expected_address && size == expected_size, "unregister exact range");
    ++releases;
}

static BOOL WINAPI MockGetModuleHandleExA(DWORD flags, LPCSTR name, HMODULE* module) {
    Check(flags == 0 && std::strcmp(name, "libSceVideoOut.prx") == 0, "hold loaded renderer reference");
    if (!module_available) return FALSE;
    *module = reinterpret_cast<HMODULE>(std::uintptr_t{1});
    ++module_references;
    return TRUE;
}

static FARPROC WINAPI MockGetProcAddress(HMODULE, LPCSTR name) {
    if (std::strcmp(name, "RytyGpuRegisterCpuStack") == 0)
        return register_available ? reinterpret_cast<FARPROC>(&MockRegister) : nullptr;
    if (std::strcmp(name, "RytyGpuUnregisterCpuStack") == 0)
        return unregister_available ? reinterpret_cast<FARPROC>(&MockUnregister) : nullptr;
    Check(false, "unexpected renderer export");
    return nullptr;
}

static BOOL WINAPI MockFreeLibrary(HMODULE) {
    Check(module_references.fetch_sub(1) != 0, "module reference released once");
    return TRUE;
}

// Exercise the real lifecycle and stack-switch implementation while controlling only
// the renderer DLL boundary. No production DLL or running game is loaded by this test.
#define GetModuleHandleExA MockGetModuleHandleExA
#define GetProcAddress MockGetProcAddress
#define FreeLibrary MockFreeLibrary
#include "../Export.cpp"
#undef GetModuleHandleExA
#undef GetProcAddress
#undef FreeLibrary

static FiberObject* current_object = nullptr;
static bool race_mode = false;
static std::atomic<bool> race_body_entered{false}, race_finalize_done{false};
static void APS5_VABI Body(std::uint64_t, std::uint64_t) {
    volatile unsigned char frame[0x31000];
    for (unsigned i = 0; i < sizeof(frame); i += 4096) frame[i] = 0x55;
    if (race_mode) {
        race_body_entered.store(true, std::memory_order_release);
        while (!race_finalize_done.load(std::memory_order_acquire)) std::this_thread::yield();
    }
    const auto before = releases.load();
    Check(sceFiberFinalize(current_object) == SCE_FIBER_ERROR_STATE, "running finalize rejected");
    Check(releases == before, "running finalize retains registration");
    sceFiberReturnToThread(0x55, nullptr);
    std::abort();
}

int main() {
    alignas(16) std::array<unsigned char, 256> object, second;
    auto* fiber = reinterpret_cast<FiberObject*>(object.data());
    auto* other = reinterpret_cast<FiberObject*>(second.data());
    constexpr std::uint64_t size = 1 << 20;
    auto* context = static_cast<unsigned char*>(VirtualAlloc(nullptr, size, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE));
    Check(context != nullptr, "allocate context");
    expected_address = reinterpret_cast<std::uint64_t>(context);
    expected_size = size;
    auto reset = [&] { object.fill(0xa5); std::memset(context, 0x37, size); };
    auto initialize = [&] { return _sceFiberInitializeImpl_nid_postfix(fiber, "ownership", Body, 0, context, size, nullptr, 0); };
    auto unchanged = [&] {
        for (auto byte : object) Check(byte == 0xa5, "failed initialize changed object");
        for (unsigned i = 0; i < size; ++i) Check(context[i] == 0x37, "failed initialize changed context");
        Check(module_references == 0, "failed initialize leaked module reference");
    };

    reset();
    module_available = false;
    Check(initialize() == SCE_FIBER_ERROR_STATE, "absent renderer fails closed"); unchanged();
    module_available = true; register_available = false;
    Check(initialize() == SCE_FIBER_ERROR_STATE, "missing register fails closed"); unchanged();
    register_available = true; unregister_available = false;
    Check(initialize() == SCE_FIBER_ERROR_STATE, "missing release fails closed"); unchanged();
    Check(registrations == 0, "paired exports resolved before acquisition");
    unregister_available = true; registration_succeeds = false;
    Check(initialize() == SCE_FIBER_ERROR_STATE, "registration failure fails closed"); unchanged();
    Check(releases == 0, "failed registration not released");
    registration_succeeds = true;
    Check(_sceFiberInitializeImpl_nid_postfix(fiber, nullptr, Body, 0, context, size, nullptr, 0) == SCE_FIBER_ERROR_NULL,
          "invalid initialize rejected"); unchanged();
    const auto before_overflow = registrations.load();
    Check(_sceFiberInitializeImpl_nid_postfix(fiber, "overflow", Body, 0,
          reinterpret_cast<void*>(UINTPTR_MAX - 15), 512, nullptr, 0) == SCE_FIBER_ERROR_RANGE,
          "context end overflow rejected"); unchanged();
    Check(registrations == before_overflow, "overflow rejected before registration");

    untouched_object = object.data(); untouched_context = context;
    make_context_writable = true;
    DWORD old = 0;
    Check(VirtualProtect(context, size, PAGE_READONLY, &old) != 0, "protect reused context");
    Check(sceFiberStartContextSizeCheck(0) == SCE_OK, "enable initial context fill");
    Check(initialize() == SCE_OK, "register before protected context fill");
    untouched_object = nullptr; untouched_context = nullptr;
    make_context_writable = false;
    Check(module_references == 1, "hold module for fiber lifetime");
    const auto before_reinit = registrations.load();
    Check(initialize() == SCE_FIBER_ERROR_STATE && registrations == before_reinit, "live reinitialize keeps one registration");
    current_object = fiber;
    std::uint64_t result = 0;
    Check(sceFiberRun_nid_postfix(fiber, 0, &result) == SCE_OK && result == 0x55, "large frame and return");
    Check(sceFiberFinalize(fiber) == SCE_OK && module_references == 0, "suspended finalize releases");
    const auto after_finalize = releases.load();
    Check(sceFiberFinalize(fiber) == SCE_FIBER_ERROR_INVALID && releases == after_finalize, "double finalize does not release twice");
    Check(sceFiberStopContextSizeCheck() == SCE_OK, "disable context fill");

    reset(); second.fill(0xa5);
    Check(initialize() == SCE_OK, "initialize after valid finalize");
    Check(_sceFiberInitializeImpl_nid_postfix(other, "duplicate", Body, 0, context, size, nullptr, 0) == SCE_OK,
          "distinct objects register duplicate exact range");
    Check(module_references == 2, "duplicate lifetime references");
    Check(sceFiberFinalize(fiber) == SCE_OK && module_references == 1, "first duplicate release");
    Check(sceFiberFinalize(other) == SCE_OK && module_references == 0, "last duplicate release");

    reset(); second.fill(0xa5);
    Check(initialize() == SCE_OK, "base overlap registration");
    expected_address += 4096; expected_size -= 4096;
    Check(_sceFiberInitializeImpl_nid_postfix(other, "overlap", Body, 0, context + 4096, size - 4096, nullptr, 0) == SCE_OK,
          "overlapping registration passed to renderer");
    Check(sceFiberFinalize(other) == SCE_OK, "overlap released with exact original bounds");
    expected_address -= 4096; expected_size += 4096;
    Check(sceFiberFinalize(fiber) == SCE_OK, "base overlap released");

    reset(); expected_address += 16; expected_size -= 32;
    Check(_sceFiberInitializeImpl_nid_postfix(fiber, "partial pages", Body, 0, context + 16, size - 32, nullptr, 0) == SCE_OK,
          "16-byte aligned partial-page context accepted");
    Check(sceFiberFinalize(fiber) == SCE_OK, "partial-page context released with exact original bounds");
    expected_address -= 16; expected_size += 32;

    for (unsigned i = 0; i < 128; ++i) {
        object.fill(0xa5);
        Check(initialize() == SCE_OK, "race initialize");
        race_mode = true;
        race_body_entered.store(false, std::memory_order_relaxed);
        race_finalize_done.store(false, std::memory_order_relaxed);
        std::atomic<bool> go{false}; int resumed = 1, finalized = 1; std::uint64_t transferred = 0;
        std::thread resume([&] { while (!go.load(std::memory_order_acquire)) {} resumed = sceFiberRun_nid_postfix(fiber, 0, &transferred); });
        std::thread finalize([&] {
            while (!go.load(std::memory_order_acquire)) {}
            finalized = sceFiberFinalize(fiber);
            race_finalize_done.store(true, std::memory_order_release);
        });
        go.store(true, std::memory_order_release);
        resume.join(); finalize.join();
        race_mode = false;
        Check((resumed == SCE_OK) != (finalized == SCE_OK), "public run and finalize cannot both acquire ownership");
        if (resumed == SCE_OK) {
            Check(race_body_entered && transferred == 0x55, "public run executes and returns on winning thread");
            Check(finalized == SCE_FIBER_ERROR_STATE && module_references == 1, "winning resumer retains ownership");
            Check(sceFiberFinalize(fiber) == SCE_OK, "release after race winner suspends");
        } else {
            Check(resumed == SCE_FIBER_ERROR_STATE || resumed == SCE_FIBER_ERROR_INVALID, "losing public run rejects finalized fiber");
            Check(!race_body_entered, "finalize winner prevents public run from entering context");
        }
        Check(module_references == 0, "race registration released exactly once");
    }
    Check(VirtualFree(context, 0, MEM_RELEASE) != 0, "free context");
    std::puts("PASS: real Fiber lifecycle, VirtualProtect ordering, large frames and finalization race; renderer DLL callbacks mocked (native integration not tested)");
}
