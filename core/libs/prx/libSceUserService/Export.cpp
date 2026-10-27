#include <cstddef>
#include <cstdint>
#include "SceTypes.hpp"
#include "prx/libc/include/General.hpp"
#include <atomic>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <string>
#include "prx/libSceUserService/UserService.hpp"
#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace {

std::size_t Utf8PrefixLength(const char* text, std::size_t max_bytes) {
 const std::size_t length = std::strlen(text);
 std::size_t offset = 0;
 while (offset < length && offset < max_bytes) {
  const unsigned char lead = static_cast<unsigned char>(text[offset]);
  std::size_t width = 1;
  if ((lead & 0xe0) == 0xc0) width = 2;
  else if ((lead & 0xf0) == 0xe0) width = 3;
  else if ((lead & 0xf8) == 0xf0) width = 4;
  if (offset + width > length || offset + width > max_bytes) break;
  bool valid = true;
  for (std::size_t i = 1; i < width; ++i) {
   if ((static_cast<unsigned char>(text[offset + i]) & 0xc0) != 0x80) {
    valid = false;
    break;
   }
  }
  offset += valid ? width : 1;
 }
 return offset;
}

// The GT Sport config next to the game's exe (user/custom_configs/CUSA03220.json) as text.
std::string ReadGameConfig() {
#ifdef _WIN32
 char exe[MAX_PATH] = {};
 const DWORD length = GetModuleFileNameA(nullptr, exe, MAX_PATH);
 if (length == 0 || length >= MAX_PATH) return {};
 std::string path(exe, length);
 path = path.substr(0, path.find_last_of("\\/") + 1) + "user/custom_configs/CUSA03220.json";
#else
 const std::string path = "user/custom_configs/CUSA03220.json";
#endif
 std::FILE* file = std::fopen(path.c_str(), "rb");
 if (file == nullptr) return {};
 std::string text;
 char chunk[4096];
 while (const std::size_t n = std::fread(chunk, 1, sizeof(chunk), file)) text.append(chunk, n);
 std::fclose(file);
 return text;
}

void AppendUtf8(std::string& out, std::uint32_t code) {
 if (code < 0x80) {
  out += static_cast<char>(code);
 } else if (code < 0x800) {
  out += static_cast<char>(0xc0 | code >> 6);
  out += static_cast<char>(0x80 | (code & 0x3f));
 } else if (code < 0x10000) {
  out += static_cast<char>(0xe0 | code >> 12);
  out += static_cast<char>(0x80 | (code >> 6 & 0x3f));
  out += static_cast<char>(0x80 | (code & 0x3f));
 } else {
  out += static_cast<char>(0xf0 | code >> 18);
  out += static_cast<char>(0x80 | (code >> 12 & 0x3f));
  out += static_cast<char>(0x80 | (code >> 6 & 0x3f));
  out += static_cast<char>(0x80 | (code & 0x3f));
 }
}

// General.player_names (the launcher's Controller ports window): "name 1,name 2", a JSON string.
// Empty entries (or no setting) keep the default names.
std::string ConfiguredPlayerName(int slot) {
 const std::string text = ReadGameConfig();
 std::size_t at = text.find("\"player_names\"");
 if (at == std::string::npos) return {};
 at = text.find(':', at);
 if (at == std::string::npos) return {};
 at = text.find('"', at);
 if (at == std::string::npos) return {};
 std::string value;
 for (++at; at < text.size() && text[at] != '"'; ++at) {
  if (text[at] != '\\' || at + 1 >= text.size()) {
   value += text[at];
   continue;
  }
  const char escaped = text[++at];
  if (escaped == 'u' && at + 4 < text.size()) {
   std::uint32_t code = static_cast<std::uint32_t>(std::strtoul(text.substr(at + 1, 4).c_str(), nullptr, 16));
   at += 4;
   // A surrogate pair: \uD8xx\uDCxx.
   if (code >= 0xd800 && code < 0xdc00 && at + 6 < text.size() && text[at + 1] == '\\' && text[at + 2] == 'u') {
    const auto low = static_cast<std::uint32_t>(std::strtoul(text.substr(at + 3, 4).c_str(), nullptr, 16));
    if (low >= 0xdc00 && low < 0xe000) {
     code = 0x10000 + ((code - 0xd800) << 10) + (low - 0xdc00);
     at += 6;
    }
   }
   AppendUtf8(value, code);
  } else {
   value += escaped == 'n' ? '\n' : escaped == 't' ? '\t' : escaped;
  }
 }
 std::size_t start = 0;
 for (int i = 0; i < slot; ++i) {
  start = value.find(',', start);
  if (start == std::string::npos) return {};
  ++start;
 }
 std::string name = value.substr(start, value.find(',', start) - start);
 const auto first = name.find_first_not_of(' ');
 if (first == std::string::npos) return {};
 return name.substr(first, name.find_last_not_of(' ') - first + 1);
}

std::string ConfiguredUserName() {
 const std::string configured = ConfiguredPlayerName(0);
 if (!configured.empty()) return configured;
#ifdef _WIN32
 const wchar_t* configured_name = _wgetenv(L"RYGT_USER_NAME");
 if (configured_name == nullptr || configured_name[0] == L'\0') return "Player";
 const int byte_count = WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, configured_name, -1, nullptr, 0, nullptr, nullptr);
 if (byte_count <= 1) return "Player";
 std::string result(static_cast<std::size_t>(byte_count), '\0');
 if (WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, configured_name, -1, result.data(), byte_count, nullptr, nullptr) != byte_count)
  return "Player";
 result.resize(static_cast<std::size_t>(byte_count - 1));
 return result;
#else
 const char* configured_name = std::getenv(USER_SERVICE_USER_NAME_ENV);
 return configured_name == nullptr || configured_name[0] == '\0' ? "Player" : configured_name;
#endif
}

}

namespace {

// GT Sport's Split Screen is for 2 players (the input bridge reports up to 4; 3 and 4 are ignored).
constexpr int MAX_PLAYERS = 2;
// Players logged in (bit N = player N+1, user id 0x10000000 + N). Player 1 always is; player 2
// logs in while a controller is assigned to them (UserServiceSetPlayers, from the input bridge).
std::atomic<std::uint32_t> g_players{1};
std::atomic<std::uint32_t> g_reported{0};

int SlotOf(int user_id) {
 const int slot = user_id - USER_SERVICE_INITIAL_USER_ID;
 return slot >= 0 && slot < MAX_PLAYERS && (g_players.load() >> slot & 1u) != 0 ? slot : -1;
}

bool Valid(int user_id) {
 return SlotOf(user_id) >= 0;
}

}

extern "C" {

int APS5_VABI sceUserServiceIsLoggedIn() {
    return 0;
}

int APS5_VABI sceUserServiceGetUserColor(int user_id, void* color) {
    (void)user_id;
    (void)color;
    return 0;
}

void UserServiceSetPlayers_nid_postfix(std::uint32_t mask) {
 g_players.store((mask | 1u) & ((1u << MAX_PLAYERS) - 1u));
}

int APS5_VABI sceUserServiceGetAccessibilityChatTranscription(int user_id, int32_t* chat_transcription) {
 if (chat_transcription == nullptr || !Valid(user_id)) {
  return USER_SERVICE_ERROR_INVALID_ARGUMENT;
 }
 *chat_transcription = 0;
 return USER_SERVICE_OK;
}

int APS5_VABI sceUserServiceGetAccessibilityPressAndHoldDelay(int user_id, int32_t* press_and_hold_delay) {
 if (press_and_hold_delay == nullptr || !Valid(user_id)) {
  return USER_SERVICE_ERROR_INVALID_ARGUMENT;
 }
 *press_and_hold_delay = 0;
 return USER_SERVICE_OK;
}

int APS5_VABI sceUserServiceGetAccessibilityTriggerEffect(int user_id, int32_t* trigger_effect) {
 if (trigger_effect == nullptr || !Valid(user_id)) {
  return USER_SERVICE_ERROR_INVALID_ARGUMENT;
 }
 *trigger_effect = 0;
 return USER_SERVICE_OK;
}

int APS5_VABI sceUserServiceGetAccessibilityVibration(int user_id, int32_t* vibration) {
 if (vibration == nullptr || !Valid(user_id)) {
  return USER_SERVICE_ERROR_INVALID_ARGUMENT;
 }
 *vibration = 0;
 return USER_SERVICE_OK;
}

int APS5_VABI sceUserServiceGetAccessibilityZoomEnabled(int user_id, int32_t* zoom_enabled) {
 if (zoom_enabled == nullptr || !Valid(user_id)) {
  return USER_SERVICE_ERROR_INVALID_ARGUMENT;
 }
 *zoom_enabled = 0;
 return USER_SERVICE_OK;
}

int APS5_VABI sceUserServiceGetAgeLevel(int user_id, uint32_t* age_level) {
 (void)user_id;
 (void)age_level;
 NotImplemented_nid_no_patch(__func__);
 return 0;
}

// Player 1 is reported as logging in first; player 2 logs in and out as their controller comes
// and goes.
int APS5_VABI sceUserServiceGetEvent(SceUserServiceEvent* event) {
 if (event == nullptr) {
  return USER_SERVICE_ERROR_INVALID_ARGUMENT;
 }
 constexpr std::uint32_t EventTypeLogin = 0;
 constexpr std::uint32_t EventTypeLogout = 1;
 const std::uint32_t players = g_players.load();
 std::uint32_t reported = g_reported.load();
 for (int slot = 0; slot < MAX_PLAYERS; ++slot) {
  const std::uint32_t bit = 1u << slot;
  if ((players & bit) == (reported & bit)) continue;
  if (!g_reported.compare_exchange_strong(reported, reported ^ bit)) return USER_SERVICE_ERROR_NO_EVENT;
  event->event_type = (players & bit) != 0 ? EventTypeLogin : EventTypeLogout;
  event->user_id = USER_SERVICE_INITIAL_USER_ID + slot;
  return USER_SERVICE_OK;
 }
 return USER_SERVICE_ERROR_NO_EVENT;
}

int APS5_VABI sceUserServiceGetGamePresets(int user_id, UserServiceGamePresets* presets) {
 // System-wide game presets (difficulty, view inversion, subtitles, audio language) of the user's
 // profile. A fresh console has none set: every field is 0, "not specified", and the title falls
 // back to its own defaults. this_size is the caller's.
 if (presets == nullptr || !Valid(user_id)) {
  return USER_SERVICE_ERROR_INVALID_ARGUMENT;
 }
 presets->difficulty = 0;
 presets->priority = 0;
 presets->invert_vertical_view_for_1st_person_view = 0;
 presets->invert_horizontal_view_for_1st_person_view = 0;
 presets->invert_vertical_view_for_3rd_person_view = 0;
 presets->invert_horizontal_view_for_3rd_person_view = 0;
 presets->display_sub_titles = 0;
 presets->audio_language = 0;
 return USER_SERVICE_OK;
}

int APS5_VABI sceUserServiceGetInitialUser(int* user_id) {
 if (user_id == nullptr) {
  return USER_SERVICE_ERROR_INVALID_ARGUMENT;
 }
 *user_id = USER_SERVICE_INITIAL_USER_ID;
 return USER_SERVICE_OK;
}

int APS5_VABI sceUserServiceGetLoginUserIdList(UserServiceLoginUserIdList* user_id_list) {
 if (user_id_list == nullptr) {
  return USER_SERVICE_ERROR_INVALID_ARGUMENT;
 }
 const std::uint32_t players = g_players.load();
 int n = 0;
 for (int slot = 0; slot < MAX_PLAYERS; ++slot) {
  if ((players >> slot & 1u) != 0) user_id_list->user_id[n++] = USER_SERVICE_INITIAL_USER_ID + slot;
 }
 while (n < static_cast<int>(sizeof(user_id_list->user_id) / sizeof(user_id_list->user_id[0])))
  user_id_list->user_id[n++] = USER_SERVICE_USER_ID_INVALID;
 return USER_SERVICE_OK;
}

int APS5_VABI sceUserServiceGetUserName(int user_id, char* name, size_t size) {
 if (name == nullptr || !Valid(user_id)) {
  return USER_SERVICE_ERROR_INVALID_ARGUMENT;
 }
 if (size < USER_SERVICE_MAX_USER_NAME_LENGTH + 1) {
  return USER_SERVICE_ERROR_BUFFER_TOO_SHORT;
 }
 if (SlotOf(user_id) == 0) {
  // Player 1: the name from the launcher, else RYGT_USER_NAME, else "Player".
  const std::string configured_name = ConfiguredUserName();
  const size_t name_length = Utf8PrefixLength(configured_name.c_str(), USER_SERVICE_MAX_USER_NAME_LENGTH);
  std::memcpy(name, configured_name.c_str(), name_length);
  name[name_length] = '\0';
 } else {
  // Player 2: the name from the launcher, else "Player 2". Cut to 16 bytes on a UTF-8 boundary.
  const std::string configured_name = ConfiguredPlayerName(SlotOf(user_id));
  if (configured_name.empty()) {
   std::snprintf(name, size, "Player %d", SlotOf(user_id) + 1);
  } else {
   const size_t name_length = Utf8PrefixLength(configured_name.c_str(), USER_SERVICE_MAX_USER_NAME_LENGTH);
   std::memcpy(name, configured_name.c_str(), name_length);
   name[name_length] = '\0';
  }
 }
 return USER_SERVICE_OK;
}

int APS5_VABI sceUserServiceGetUserNumber(int user_id, int32_t* number) {
 if (number == nullptr || !Valid(user_id)) {
  return USER_SERVICE_ERROR_INVALID_ARGUMENT;
 }
 *number = SlotOf(user_id) + 1;
 return USER_SERVICE_OK;
}

int APS5_VABI sceUserServiceInitialize(const void* params) {
 (void)params;
 return USER_SERVICE_OK;
}

int APS5_VABI sceUserServiceInitialize2(void) {
 return USER_SERVICE_OK;
}

int APS5_VABI sceUserServiceTerminate(void) {
 return USER_SERVICE_OK;
}

// No PSN account exists, so the platform privacy setting reports the feature as not permitted.
int APS5_VABI sceUserServiceGetPlatformPrivacyWs1(int32_t user_id, int32_t* value) {
    (void)user_id;
    if (!value) return USER_SERVICE_ERROR_INVALID_ARGUMENT;
    *value = 0;
    return 0;
}

}
