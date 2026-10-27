#include <cstdint>
#include <cstddef>
#include <cerrno>
#include "SceTypes.hpp"
#include "prx/libc/include/General.hpp"

extern "C" {

int APS5_VABI sceKernelError() {
    return 0;
}

int APS5_VABI ipmimgr_call() {
    return -ENOSYS;
}

int APS5_VABI get_authinfo() {
    return 0;
}

int APS5_VABI get_self_auth_info() {
    return 0;
}

int APS5_VABI sceKernelGetUtokenUseSoftwagnerForAcmgr() {
    return 0;
}

int APS5_VABI sceKernelGetCompiledSdkVersionByPid() {
    return 0;
}

int APS5_VABI __sys_regmgr_call() {
    return 0;
}

int APS5_VABI sceKernelGetVrCaptureSize() {
    return 0;
}

int APS5_VABI sceKernelPrintBacktraceWithModuleInfo() {
    return 0;
}

int APS5_VABI sceCoredumpAttachMemoryRegion() {
    return 0;
}

int APS5_VABI sceCoredumpWriteUserData() {
 NotImplemented_nid_no_patch(__func__);
 return 0;
}

}

// Coredump interfaces do not write user data in this runtime.
extern "C" {
int APS5_VABI sceKernelGetAppInfo() { return 0; }
int APS5_VABI sceKernelTitleWorkaroundIsEnabled() { return 0; }
int APS5_VABI p9TTq4bLdFU_nid_no_patch_cut() { return 0; }
int APS5_VABI QXFsLON5QWw_nid_no_patch_cut() { return 0; }
int APS5_VABI reTFEla4NQw_nid_no_patch_cut() { return 0; }
int APS5_VABI yxjgDvqUbGQ_nid_no_patch_cut() { return 0; }
int APS5_VABI afLdI6i0lQw_nid_no_patch_cut() { return 0; }
int APS5_VABI txNJzxX6yrA_nid_no_patch_cut() { return 0; }
int APS5_VABI eQnlGJJAFsA_nid_no_patch_cut() { return 0; }
int APS5_VABI sceKernelCloseEventFlag() { return 0; }
int APS5_VABI sceKernelOpenEventFlag() { return 0; }
int APS5_VABI sceKernelGetCpumode() { return 0; }
int APS5_VABI scePthreadGetschedparam() { return 0; }
int APS5_VABI scePthreadSetschedparam() { return 0; }
int APS5_VABI sceCoredumpAttachMemoryRegionAsUserFile() { return 0; }
int APS5_VABI sceCoredumpAttachUserFile() { return 0; }
int APS5_VABI sceCoredumpAttachUserMemoryFile() { return 0; }
int APS5_VABI sceCoredumpConfigDumpMode() { return 0; }
int APS5_VABI sceCoredumpDebugForceCoredumpOnAppClose() { return 0; }
int APS5_VABI sceCoredumpDebugTextOut() { return 0; }
int APS5_VABI sceCoredumpDebugTriggerCoredump() { return 0; }
int APS5_VABI sceCoredumpGetStopInfoCpu() { return 0; }
int APS5_VABI sceCoredumpGetStopInfoGpu() { return 0; }
int APS5_VABI sceCoredumpGetThreadContextInfo() { return 0; }
int APS5_VABI sceCoredumpInternalGetThreadContextInfo() { return 0; }
int APS5_VABI sceCoredumpSetUserDataType() { return 0; }
}

