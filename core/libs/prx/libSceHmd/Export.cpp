#include "Hmd.hpp"

#include <atomic>

namespace {

std::atomic<bool> initialized{false};

std::int32_t Initialize(const Hmd::InitializeParam* param) {
    if (initialized.load()) return Hmd::AlreadyInitialized;
    if (!param) return Hmd::ParameterNull;
    if (param->reserved0) return Hmd::UnsupportedFeature;
    return initialized.exchange(true) ? Hmd::AlreadyInitialized : 0;
}

}

extern "C" {

std::int32_t APS5_VABI sceHmdInternalMmapGetSensorCalibrationData(void* data, std::uint32_t* size) {
    (void)data;
    if (size) *size = 0;
    return Hmd::DeviceDisconnected;
}

std::int32_t APS5_VABI sceHmdInternalGetPUVersion(std::uint32_t* version) {
    if (version) *version = 0;
    return Hmd::DeviceDisconnected;
}

std::int32_t APS5_VABI sceHmdInternalGetDeviceInformation(Hmd::DeviceInformation* info) {
    if (!info) return Hmd::ParameterNull;
    *info = {};
    info->status = Hmd::DeviceStatus::NotDetected;
    info->userId = -1;
    return 0;
}

std::int32_t APS5_VABI sceHmdInternalMmapGetCount(std::uint32_t* count) {
    if (count) *count = 0;
    return 0;
}

std::int32_t APS5_VABI sceHmdInternalResetLedForVrTracker() {
    return Hmd::DeviceDisconnected;
}

std::int32_t APS5_VABI sceHmdInternalSetUserType(std::int32_t userType) {
    (void)userType;
    return Hmd::DeviceDisconnected;
}

std::int32_t APS5_VABI sceHmdInternalGetHmuSerialNumber(char* serial) {
    if (serial) *serial = '\0';
    return Hmd::DeviceDisconnected;
}

std::int32_t APS5_VABI sceHmdInternalGetEyeStatus(Hmd::DeviceStatus* status) {
    if (status) *status = Hmd::DeviceStatus::NotDetected;
    return Hmd::DeviceDisconnected;
}

std::int32_t APS5_VABI sceHmdGetInertialSensorData(std::int32_t handle, void* data) {
    (void)handle;
    (void)data;
    return Hmd::DeviceDisconnected;
}

std::int32_t APS5_VABI sceHmdGetFieldOfView(std::int32_t handle, void* field_of_view) {
    (void)handle;
    (void)field_of_view;
    return Hmd::DeviceDisconnected;
}

std::int32_t APS5_VABI sceHmdInitialize(const Hmd::InitializeParam* param) {
    return Initialize(param);
}

std::int32_t APS5_VABI sceHmdInitialize315(const Hmd::InitializeParam* param) {
    return Initialize(param);
}

std::int32_t APS5_VABI sceHmdTerminate() {
    return initialized.exchange(false) ? 0 : Hmd::NotInitialized;
}

std::int32_t APS5_VABI sceHmdOpen(std::int32_t userId, std::int32_t type, std::int32_t index,
                                Hmd::OpenParam* param) {
    if (!initialized.load()) return Hmd::NotInitialized;
    if (type != 0 || index != 0 || param || userId == -1 || userId == 0xff)
        return Hmd::ParameterInvalid;
    return Hmd::DeviceDisconnected;
}

std::int32_t APS5_VABI sceHmdClose(std::int32_t handle) {
    (void)handle;
    return initialized.load() ? Hmd::InvalidHandle : Hmd::NotInitialized;
}

std::int32_t APS5_VABI sceHmdGetDeviceInformation(Hmd::DeviceInformation* info) {
    if (!info) return Hmd::ParameterNull;
    if (!initialized.load()) return Hmd::NotInitialized;
    *info = {};
    info->status = Hmd::DeviceStatus::NotDetected;
    info->userId = -1;
    return 0;
}

std::int32_t APS5_VABI sceHmdGetDeviceInformationByHandle(std::int32_t handle,
                                                        Hmd::DeviceInformation* info) {
    (void)handle;
    (void)info;
    return initialized.load() ? Hmd::InvalidHandle : Hmd::NotInitialized;
}

std::int32_t APS5_VABI sceHmdInternalGetDeviceStatus(Hmd::DeviceStatus* status) {
    if (!status) return Hmd::ParameterNull;
    *status = Hmd::DeviceStatus::NotDetected;
    return 0;
}

// GT Sport imports this reprojection entry point even when no headset is present.
std::int32_t APS5_VABI sceHmdReprojectionSetOutputMinColor() {
    return 0;
}

std::int32_t APS5_VABI sceHmdInternalMmapIsConnect() {
    return 0;
}

}

// HMD compatibility exports for unavailable headset hardware.
extern "C" {
int APS5_VABI sceHmd2Close() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2GazeGetCalibrationData() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2GazeGetCalibrationDataMaxSize() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2GazeGetResult() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2GazeGetResultForFoveatedRendering() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2GetDeviceInformation() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2GetDeviceInformationByHandle() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2GetFieldOfView() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2GetFieldOfViewWithoutHandle() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2Initialize() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2Open() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2ReprojectionBeginFrame() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2ReprojectionClearUserEventEnd() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2ReprojectionClearUserEventStart() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2ReprojectionDisableMirroring() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2ReprojectionDisableVrMode() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2ReprojectionEnableMirroring() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2ReprojectionEnableVrMode() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2ReprojectionGetCurrentOutput() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2ReprojectionGetMirroringDisplayBufferSizeAlign() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2ReprojectionGetMirroringWorkMemorySizeAlign() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2ReprojectionGetPredictedDisplayTime() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2ReprojectionGetStatus() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2ReprojectionInitialize() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2ReprojectionQueryBufferSizeAlign() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2ReprojectionQueryDisplayBufferSizeAlign() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2ReprojectionSetAllowPositionalReprojection() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2ReprojectionSetMirroringOption() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2ReprojectionSetParam() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2ReprojectionSetParamWithBuffer() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2ReprojectionSetRenderConfig() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2ReprojectionSetTiming() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2ReprojectionSetUserEventEnd() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2ReprojectionSetUserEventStart() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2ReprojectionTerminate() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2SetVibration() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmd2Terminate() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdDistortionGet2dVrCommand() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdDistortionGetCompoundEyeCorrectionCommand() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdDistortionGetCorrectionCommand() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdDistortionGetWideNearCorrectionCommand() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdDistortionGetWorkMemoryAlign() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdDistortionGetWorkMemorySize() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdDistortionInitialize() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdDistortionSetOutputMinColor() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdFillDistortionBuffer() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdGet2dDistortionMap() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdGet2DEyeOffset() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdGet2dVrCommand() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdGetAssyError() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdGetDistortionCorrectionCommand() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdGetDistortionCorrectionCommand2d() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdGetDistortionCorrectionCommandApprox() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdGetDistortionMap() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdGetDistortionParams() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdGetDistortionWorkMemoryAlign() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdGetDistortionWorkMemoryAlignFor2d() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdGetDistortionWorkMemorySize() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdGetDistortionWorkMemorySizeFor2d() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdGetEyeStatus() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdGetFieldOfView2d() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdGetFieldOfViewApprox() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdGetViewStatus() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdGetWideNearDistortionCorrectionCommand() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternal3dAudioClose() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternal3dAudioOpen() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternal3dAudioSendData() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalAnotherScreenClose() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalAnotherScreenGetAudioStatus() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalAnotherScreenGetFadeState() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalAnotherScreenGetVideoStatus() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalAnotherScreenOpen() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalAnotherScreenSendAudio() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalAnotherScreenSendVideo() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalAnotherScreenSetFadeAndSwitch() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalBindDeviceWithUserId() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalCheckDeviceModelMk3() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalCheckS3dPassModeAvailable() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalCrashReportCancel() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalCrashReportClose() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalCrashReportOpen() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalCrashReportReadData() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalCrashReportReadDataSize() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalCreateSharedMemory() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalDfuCheckAfterPvt() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalDfuCheckPartialUpdateAvailable() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalDfuClose() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalDfuGetStatus() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalDfuOpen() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalDfuReset() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalDfuSend() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalDfuSendSize() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalDfuSetMode() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalDfuStart() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalEventInitialize() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalGetBrightness() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalGetCrashDumpInfo() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalGetDebugMode() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalGetDebugSocialScreenMode() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalGetDebugTextMode() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalGetDefaultLedData() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalGetDemoMode() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalGetDeviceInformationByHandle() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalGetHmuOpticalParam() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalGetHmuPowerStatusForDebug() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalGetIPD() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalGetIpdSettingEnableForSystemService() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalGetPuBuildNumber() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalGetPuPositionParam() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalGetPuRevision() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalGetPUSerialNumber() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalGetRequiredPUPVersion() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalGetSensorCalibrationData() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalGetStatusReport() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalGetTv4kCapability() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalGetVirtualDisplayDepth() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalGetVirtualDisplayHeight() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalGetVirtualDisplaySize() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalGetVr2dData() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalIsCommonDlgMiniAppVr2d() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalIsCommonDlgVr2d() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalIsGameVr2d() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalIsMiniAppVr2d() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalMapSharedMemory() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalMirroringModeSetAspect() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalMirroringModeSetAspectDebug() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalMmapGetModeId() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalPushVr2dData() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalRegisterEventCallback() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalResetInertialSensor() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalResetLedForVsh() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSeparateModeClose() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSeparateModeGetAudioStatus() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSeparateModeGetVideoStatus() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSeparateModeOpen() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSeparateModeSendAudio() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSeparateModeSendVideo() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSetBrightness() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSetCrashReportCommand() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSetDebugGpo() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSetDebugMode() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSetDebugSocialScreenMode() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSetDebugTextMode() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSetDefaultLedData() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSetDemoMode() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSetDeviceConnection() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSetForcedCrash() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSetHmuPowerControl() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSetHmuPowerControlForDebug() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSetIPD() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSetIpdSettingEnableForSystemService() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSetIPDSettingEnableForSystemService() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSetLedOn() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSetM2LedBrightness() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSetM2LedOn() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSetPortConnection() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSetPortStatus() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSetS3dPassMode() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSetSidetone() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSetVirtualDisplayDepth() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSetVirtualDisplayHeight() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSetVirtualDisplaySize() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSetVRMode() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSocialScreenGetFadeState() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSocialScreenSetFadeAndSwitch() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdInternalSocialScreenSetOutput() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionAddDisplayBuffer() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionClearUserEventEnd() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionClearUserEventStart() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionDebugGetLastInfo() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionDebugGetLastInfoMultilayer() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionFinalize() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionFinalizeCapture() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionInitialize() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionInitializeCapture() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionQueryGarlicBuffAlign() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionQueryGarlicBuffSize() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionQueryOnionBuffAlign() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionQueryOnionBuffSize() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionSetCallback() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionSetDisplayBuffers() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionSetUserEventEnd() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionSetUserEventStart() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionSetUserEventToFinish() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionSetUserEventToStart() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionStart() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionStart2dVr() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionStartCapture() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionStartCompoundEye() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionStartLiveCapture() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionStartMultilayer() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionStartMultilayer2() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionStartWideNear() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionStartWideNearWithOverlay() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionStartWithOverlay() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionStop() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionStopCapture() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionStopLiveCapture() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionUnsetCallback() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdReprojectionUnsetDisplayBuffers() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdSetupDialogClose() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdSetupDialogGetResult() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdSetupDialogGetStatus() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdSetupDialogInitialize() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdSetupDialogOpen() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdSetupDialogTerminate() { return Hmd::DeviceDisconnected; }
int APS5_VABI sceHmdSetupDialogUpdateStatus() { return Hmd::DeviceDisconnected; }
}

