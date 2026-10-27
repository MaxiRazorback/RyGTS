#include <cstdint>
#include <cstddef>
#include "SceTypes.hpp"
#include "prx/libc/include/General.hpp"
#include "prx/libkernel/AppMetadata/include/AppMetadata.hpp"
#include <algorithm>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <stdexcept>
#include <string>

static constexpr int SCE_APP_CONTENT_ERROR_PARAMETER = static_cast<int>(0x80D90002);
static constexpr uint32_t APPPARAM_ID_SKU_FLAG = 1;
static constexpr int32_t SKU_FLAG_FULL = 3;

static constexpr char TEMPORARY_MOUNT_POINT[] = "/temp0";
static constexpr char DOWNLOAD_MOUNT_POINT[] = "/download0";
static constexpr uint32_t TEMPORARY_DATA_OPTION_FORMAT = 1;

static std::filesystem::path TemporaryDirectory(const AppContentMountPoint* mount_point) {
    if (!mount_point || std::strncmp(mount_point->data, TEMPORARY_MOUNT_POINT, sizeof(mount_point->data)) != 0) APS5_INVALID_ARG_EX;
    return ResolvePath_nid_no_patch(TEMPORARY_MOUNT_POINT);
}

static void ClearDirectory(const std::filesystem::path& directory) {
    for (const auto& entry : std::filesystem::directory_iterator(directory)) std::filesystem::remove_all(entry.path());
}

extern "C" {

int APS5_VABI sceAppContentAddcontMount(uint32_t service_label, const NpUnifiedEntitlementLabel* entitlement_label, AppContentMountPoint* mount_point) {
 (void)service_label;
 (void)entitlement_label;
 (void)mount_point;
 NotImplemented_nid_no_patch(__func__);
 return 0;
}

int APS5_VABI sceAppContentAddcontUnmount(const AppContentMountPoint* mount_point) {
 (void)mount_point;
 NotImplemented_nid_no_patch(__func__);
 return 0;
}

int APS5_VABI sceAppContentGetAddcontDownloadProgress() {
    return 0;
}

int APS5_VABI sceAppContentAddcontEnqueueDownload() {
    return SCE_APP_CONTENT_ERROR_PARAMETER;
}

// No add-on content is installed, so the list is always empty.
int APS5_VABI sceAppContentGetAddcontInfoList(uint32_t service_label, void* list, uint32_t list_num, uint32_t* hit_num) {
    (void)service_label;
    (void)list;
    (void)list_num;
    if (!hit_num) return SCE_APP_CONTENT_ERROR_PARAMETER;
    *hit_num = 0;
    return 0;
}

int APS5_VABI sceAppContentAppParamGetInt(uint32_t param_id, int32_t* value) {
    if (!value) return SCE_APP_CONTENT_ERROR_PARAMETER;
    switch (param_id) {
    case APPPARAM_ID_SKU_FLAG:
        *value = SKU_FLAG_FULL;
        return 0;
    case 2: case 3: case 4: case 5:
        *value = 0;
        return 0;
    default:
        return SCE_APP_CONTENT_ERROR_PARAMETER;
    }
}

int APS5_VABI sceAppContentDownloadDataGetAvailableSpaceKb(const AppContentMountPoint* mount_point, size_t* available_space_kb) {
    static bool traced = false;
    if (!traced) {
        traced = true;
        std::fprintf(stderr, "[APPCONTENT] download data space: mount point %s\n", mount_point ? mount_point->data : "(null)");
    }
    if (!available_space_kb) return SCE_APP_CONTENT_ERROR_PARAMETER;
    if (!mount_point || std::strncmp(mount_point->data, DOWNLOAD_MOUNT_POINT, sizeof(mount_point->data)) != 0) APS5_INVALID_ARG_EX;
    const std::uint64_t quotaKb = GetAppDownloadDataSizeMiB_nid_postfix() * 1024u;
    if (quotaKb == 0) throw std::logic_error(std::string(__func__) + ": the title declares no download data");
    const auto directory = ResolvePath_nid_no_patch(DOWNLOAD_MOUNT_POINT);
    std::filesystem::create_directories(directory);
    std::uint64_t usedKb = 0;
    for (const auto& entry : std::filesystem::recursive_directory_iterator(directory)) {
        if (entry.is_regular_file()) usedKb += (entry.file_size() + 1023u) / 1024u;
    }
    const std::uint64_t hostKb = std::filesystem::space(directory).available / 1024u;
    *available_space_kb = static_cast<size_t>(std::min(quotaKb - std::min(quotaKb, usedKb), hostKb));
    std::fprintf(stderr, "[APPCONTENT] download data space: %zu KiB free of %llu KiB\n", *available_space_kb, static_cast<unsigned long long>(quotaKb));
    return 0;
}

int APS5_VABI sceAppContentInitialize(const AppContentInitParam* init_param, AppContentBootParam* boot_param) {
    (void)init_param;
    if (!boot_param) return SCE_APP_CONTENT_ERROR_PARAMETER;
    std::memset(boot_param, 0, sizeof(*boot_param));
    // On a PS4, /download0 is mounted before the title starts whenever it declares download data,
    // and titles open files there without asking about it first.
    if (GetAppDownloadDataSizeMiB_nid_postfix() != 0) {
        std::filesystem::create_directories(ResolvePath_nid_no_patch(DOWNLOAD_MOUNT_POINT));
    }
    return 0;
}

int APS5_VABI sceAppContentTemporaryDataFormat(const AppContentMountPoint* mount_point) {
    ClearDirectory(TemporaryDirectory(mount_point));
    return 0;
}

int APS5_VABI sceAppContentTemporaryDataGetAvailableSpaceKb(const AppContentMountPoint* mount_point, size_t* available_space_kb) {
    if (!available_space_kb) return SCE_APP_CONTENT_ERROR_PARAMETER;
    *available_space_kb = static_cast<size_t>(std::filesystem::space(TemporaryDirectory(mount_point)).available / 1024);
    std::fprintf(stderr, "[APPCONTENT] temporary data space: %zu KiB free\n", *available_space_kb);
    return 0;
}

int APS5_VABI sceAppContentTemporaryDataMount2(uint32_t option, AppContentMountPoint* mount_point) {
    if (!mount_point) return SCE_APP_CONTENT_ERROR_PARAMETER;
    if (option > TEMPORARY_DATA_OPTION_FORMAT) throw std::invalid_argument(std::string(__func__) + ": unknown option " + std::to_string(option));
    std::memset(mount_point->data, 0, sizeof(mount_point->data));
    std::memcpy(mount_point->data, TEMPORARY_MOUNT_POINT, sizeof(TEMPORARY_MOUNT_POINT));
    const auto directory = TemporaryDirectory(mount_point);
    std::filesystem::create_directories(directory);
    if (option == TEMPORARY_DATA_OPTION_FORMAT) ClearDirectory(directory);
    return 0;
}

}

// Offline no-add-on-content compatibility exports.
extern "C" {
int APS5_VABI sceAppContentAddcontDelete() { return SCE_APP_CONTENT_ERROR_PARAMETER; }
int APS5_VABI sceAppContentAddcontEnqueueDownloadByEntitlementId() { return SCE_APP_CONTENT_ERROR_PARAMETER; }
int APS5_VABI sceAppContentAddcontEnqueueDownloadSp() { return SCE_APP_CONTENT_ERROR_PARAMETER; }
int APS5_VABI sceAppContentAddcontMountByEntitlementId() { return SCE_APP_CONTENT_ERROR_PARAMETER; }
int APS5_VABI sceAppContentAddcontShrink() { return SCE_APP_CONTENT_ERROR_PARAMETER; }
int APS5_VABI sceAppContentAppParamGetString() { return SCE_APP_CONTENT_ERROR_PARAMETER; }
int APS5_VABI sceAppContentDownload0Expand() { return SCE_APP_CONTENT_ERROR_PARAMETER; }
int APS5_VABI sceAppContentDownload0Shrink() { return SCE_APP_CONTENT_ERROR_PARAMETER; }
int APS5_VABI sceAppContentDownload1Expand() { return SCE_APP_CONTENT_ERROR_PARAMETER; }
int APS5_VABI sceAppContentDownload1Shrink() { return SCE_APP_CONTENT_ERROR_PARAMETER; }
int APS5_VABI sceAppContentDownloadDataFormat() { return SCE_APP_CONTENT_ERROR_PARAMETER; }
int APS5_VABI sceAppContentGetAddcontInfo() { return SCE_APP_CONTENT_ERROR_PARAMETER; }
int APS5_VABI sceAppContentGetAddcontInfoByEntitlementId() { return SCE_APP_CONTENT_ERROR_PARAMETER; }
int APS5_VABI sceAppContentGetAddcontInfoListByIroTag() { return SCE_APP_CONTENT_ERROR_PARAMETER; }
int APS5_VABI sceAppContentGetDownloadedStoreCountry() { return SCE_APP_CONTENT_ERROR_PARAMETER; }
int APS5_VABI sceAppContentGetEntitlementKey() { return SCE_APP_CONTENT_ERROR_PARAMETER; }
int APS5_VABI sceAppContentGetPftFlag() { return SCE_APP_CONTENT_ERROR_PARAMETER; }
int APS5_VABI sceAppContentGetRegion() { return SCE_APP_CONTENT_ERROR_PARAMETER; }
int APS5_VABI sceAppContentRequestPatchInstall() { return SCE_APP_CONTENT_ERROR_PARAMETER; }
int APS5_VABI sceAppContentSmallSharedDataFormat() { return SCE_APP_CONTENT_ERROR_PARAMETER; }
int APS5_VABI sceAppContentSmallSharedDataGetAvailableSpaceKb() { return SCE_APP_CONTENT_ERROR_PARAMETER; }
int APS5_VABI sceAppContentSmallSharedDataMount() { return SCE_APP_CONTENT_ERROR_PARAMETER; }
int APS5_VABI sceAppContentSmallSharedDataUnmount() { return SCE_APP_CONTENT_ERROR_PARAMETER; }
int APS5_VABI sceAppContentTemporaryDataMount() { return SCE_APP_CONTENT_ERROR_PARAMETER; }
int APS5_VABI sceAppContentTemporaryDataUnmount() { return SCE_APP_CONTENT_ERROR_PARAMETER; }
}

