#include <cstdint>
#include <cstddef>
#include <mutex>
#include <set>
#include <stdexcept>
#include <string>
#include "SceTypes.hpp"
#include "prx/libc/include/General.hpp"

#ifdef _WIN32
#include <windows.h>
#endif

namespace {

// RyGT: the shadGT renderer (libSceVideoOut.prx) has the on-screen keyboard (sceImeOpen's inline
// keyboard, drawn with ImGui) and exports these functions by NID. When it is there, every call
// goes to it; otherwise the stubs below answer as before.
template <typename Fn>
Fn Renderer(const char* nid) {
#ifdef _WIN32
    if (HMODULE renderer = GetModuleHandleA("libSceVideoOut.prx")) {
        return reinterpret_cast<Fn>(GetProcAddress(renderer, nid));
    }
#endif
    return nullptr;
}

std::mutex g_keyboardMutex;
std::set<int32_t> g_openKeyboards;

}

extern "C" {

int APS5_VABI sceImeClose_nid_postfix(void) {
 if (static const auto f = Renderer<int(APS5_VABI*)()>("TmVP8LzcFcY"); f) return f();
 NotImplemented_nid_no_patch(__func__);
 return 0;
}

int APS5_VABI sceImeGetPanelSize(const Param* param, uint32_t* width, uint32_t* height) {
 if (static const auto f = Renderer<int(APS5_VABI*)(const Param*, uint32_t*, uint32_t*)>("ziPDcIjO0Vk"); f) return f(param, width, height);
 (void)param;
 (void)width;
 (void)height;
 NotImplemented_nid_no_patch(__func__);
 return 0;
}

int APS5_VABI sceImeKeyboardClose(int32_t user_id) {
 if (static const auto f = Renderer<int(APS5_VABI*)(int32_t)>("PMVehSlfZ94"); f) return f(user_id);
 std::lock_guard lock(g_keyboardMutex);
 if (g_openKeyboards.erase(user_id) == 0) throw std::logic_error("sceImeKeyboardClose: keyboard not open for user " + std::to_string(user_id));
 return 0;
}

int APS5_VABI sceImeKeyboardGetInfo(uint32_t resource_id, KeyboardInfo* info) {
 if (static const auto f = Renderer<int(APS5_VABI*)(uint32_t, KeyboardInfo*)>("VkqLPArfFdc"); f) return f(resource_id, info);
 (void)resource_id;
 (void)info;
 NotImplemented_nid_no_patch(__func__);
 return 0;
}

int APS5_VABI sceImeKeyboardGetResourceId(int32_t user_id, KeyboardResourceIdArray* resource_ids) {
 if (static const auto f = Renderer<int(APS5_VABI*)(int32_t, KeyboardResourceIdArray*)>("dKadqZFgKKQ"); f) return f(user_id, resource_ids);
 (void)user_id;
 (void)resource_ids;
 NotImplemented_nid_no_patch(__func__);
 return 0;
}

int APS5_VABI sceImeKeyboardOpen(int32_t user_id, const KeyboardParam* param) {
 if (static const auto f = Renderer<int(APS5_VABI*)(int32_t, const KeyboardParam*)>("eaFXjfJv3xs"); f) return f(user_id, param);
 if (!param) APS5_INVALID_ARG_EX;
 std::lock_guard lock(g_keyboardMutex);
 if (!g_openKeyboards.insert(user_id).second) throw std::logic_error("sceImeKeyboardOpen: keyboard already open for user " + std::to_string(user_id));
 return 0;
}

int APS5_VABI sceImeKeyboardSetMode(int32_t user_id, uint32_t mode) {
 if (static const auto f = Renderer<int(APS5_VABI*)(int32_t, uint32_t)>("ua+13Hk9kKs"); f) return f(user_id, mode);
 (void)user_id;
 (void)mode;
 NotImplemented_nid_no_patch(__func__);
 return 0;
}

int APS5_VABI sceImeOpen_nid_postfix(const Param* param, const ExtendedParam* extended) {
 if (static const auto f = Renderer<int(APS5_VABI*)(const Param*, const ExtendedParam*)>("RPydv-Jr1bc"); f) return f(param, extended);
 (void)param;
 (void)extended;
 NotImplemented_nid_no_patch(__func__);
 return 0;
}

void APS5_VABI sceImeParamInit(Param* param) {
 if (static const auto f = Renderer<void(APS5_VABI*)(Param*)>("WmYDzdC4EHI"); f) { f(param); return; }
 (void)param;
 NotImplemented_nid_no_patch(__func__);
}

int APS5_VABI sceImeSetCaret(const Caret* caret) {
 if (static const auto f = Renderer<int(APS5_VABI*)(const Caret*)>("WLxUN2WMim8"); f) return f(caret);
 (void)caret;
 NotImplemented_nid_no_patch(__func__);
 return 0;
}

int APS5_VABI sceImeSetText(const char16_t* text, uint32_t length) {
 if (static const auto f = Renderer<int(APS5_VABI*)(const char16_t*, uint32_t)>("ieCNrVrzKd4"); f) return f(text, length);
 (void)text;
 (void)length;
 NotImplemented_nid_no_patch(__func__);
 return 0;
}

int APS5_VABI sceImeSetTextGeometry(TextAreaMode mode, const TextGeometry* geometry) {
 if (static const auto f = Renderer<int(APS5_VABI*)(TextAreaMode, const TextGeometry*)>("TXYHFRuL8UY"); f) return f(mode, geometry);
 (void)mode;
 (void)geometry;
 NotImplemented_nid_no_patch(__func__);
 return 0;
}

int APS5_VABI sceImeUpdate(EventHandler handler) {
 if (static const auto f = Renderer<int(APS5_VABI*)(EventHandler)>("-4GCfYdNF1s"); f) return f(handler);
 if (!handler) APS5_INVALID_ARG_EX;
 return 0;
}

}
