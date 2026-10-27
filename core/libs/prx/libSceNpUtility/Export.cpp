#include <cstdint>
#include <cstddef>
#include "SceTypes.hpp"
#include "prx/libc/include/General.hpp"

static constexpr int SCE_NP_ERROR_INVALID_ARGUMENT = static_cast<int>(0x80550003);
static constexpr int SCE_NP_ERROR_SIGNED_OUT = static_cast<int>(0x80550006);

extern "C" {

int SceNpUtilityModuleLoaded_nid_no_patch = 1;

int APS5_VABI sceNpBandwidthTestAbort(int context_id) {
    (void)context_id;
    return SCE_NP_ERROR_INVALID_ARGUMENT;
}

int APS5_VABI sceNpBandwidthTestGetStatus(int context_id, int* status) {
    (void)context_id;
    if (status) *status = 0;
    return SCE_NP_ERROR_INVALID_ARGUMENT;
}

int APS5_VABI sceNpBandwidthTestInitStartDownload(const void* param) {
    (void)param;
    return SCE_NP_ERROR_SIGNED_OUT;
}

int APS5_VABI sceNpBandwidthTestInitStartUpload(const void* param) {
    (void)param;
    return SCE_NP_ERROR_SIGNED_OUT;
}

int APS5_VABI sceNpBandwidthTestShutdown(int context_id, void* result) {
    (void)context_id;
    (void)result;
    return SCE_NP_ERROR_INVALID_ARGUMENT;
}

}

// Friend-list dialog compatibility exports; network-backed dialog is offline.
extern "C" {
int APS5_VABI sceNpFriendListDialogClose() { return 0; }
int APS5_VABI sceNpFriendListDialogGetResult() { return 0; }
int APS5_VABI sceNpFriendListDialogGetResultA() { return 0; }
int APS5_VABI sceNpFriendListDialogGetStatus() { return 0; }
int APS5_VABI sceNpFriendListDialogInitialize() { return 0; }
int APS5_VABI sceNpFriendListDialogOpen() { return 0; }
int APS5_VABI sceNpFriendListDialogOpenA() { return 0; }
int APS5_VABI sceNpFriendListDialogTerminate() { return 0; }
int APS5_VABI sceNpFriendListDialogUpdateStatus() { return 0; }
}


// In-game message network service is offline.
extern "C" {
int APS5_VABI sceNpInGameMessageAbortHandle() { return 0; }
int APS5_VABI sceNpInGameMessageCheckCallback() { return 0; }
int APS5_VABI sceNpInGameMessageCreateHandle() { return 0; }
int APS5_VABI sceNpInGameMessageDeleteHandle() { return 0; }
int APS5_VABI sceNpInGameMessageGetMemoryPoolStatistics() { return 0; }
int APS5_VABI sceNpInGameMessageInitialize() { return 0; }
int APS5_VABI sceNpInGameMessagePrepare() { return 0; }
int APS5_VABI sceNpInGameMessagePrepareA() { return 0; }
int APS5_VABI sceNpInGameMessageSendData() { return 0; }
int APS5_VABI sceNpInGameMessageSendDataA() { return 0; }
int APS5_VABI sceNpInGameMessageTerminate() { return 0; }
}


// EULA dialog compatibility exports; online console dialogs are offline.
extern "C" {
int APS5_VABI sceNpEulaDialogCheckVersion() { return 0; }
int APS5_VABI sceNpEulaDialogCheckVersionAbort() { return 0; }
int APS5_VABI sceNpEulaDialogClose() { return 0; }
int APS5_VABI sceNpEulaDialogGetResult() { return 0; }
int APS5_VABI sceNpEulaDialogGetStatus() { return 0; }
int APS5_VABI sceNpEulaDialogInitialize() { return 0; }
int APS5_VABI sceNpEulaDialogOpen() { return 0; }
int APS5_VABI sceNpEulaDialogTerminate() { return 0; }
int APS5_VABI sceNpEulaDialogUpdateStatus() { return 0; }
}

