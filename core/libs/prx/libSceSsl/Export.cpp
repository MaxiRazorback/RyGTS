#include <cstdint>
#include <cstddef>
#include "SceTypes.hpp"
#include "prx/libc/include/General.hpp"
#include <atomic>

// No network is emulated: contexts, templates and requests can be created, but any request
// that would touch the network fails with the library's network error.
static constexpr int ERROR_NETWORK = static_cast<int>(0x80435001);
static std::atomic<int> g_nextHandle{1};

namespace {

constexpr int ERROR_NOT_FOUND = static_cast<int>(0x8095F004);
constexpr int ERROR_INVALID_ARG = static_cast<int>(0x8095177A);

struct SslData {
    char* ptr;
    size_t size;
};

struct SslCaCerts {
    SslData* certs;
    size_t num;
    void* pool;
};

}

extern "C" {

int APS5_VABI sceSslFreeCaCerts(int ssl_ctx_id, void* ca_certs) {
    (void)ssl_ctx_id;
    if (!ca_certs) return ERROR_INVALID_ARG;
    *static_cast<SslCaCerts*>(ca_certs) = {};
    return 0;
}

int APS5_VABI sceSslGetCaCerts(int ssl_ctx_id, void* ca_certs) {
    (void)ssl_ctx_id;
    if (!ca_certs) return ERROR_INVALID_ARG;
    *static_cast<SslCaCerts*>(ca_certs) = {};
    return ERROR_NOT_FOUND;
}

int APS5_VABI sceSslGetMemoryPoolStats() {
    return 0;
}

int APS5_VABI sceSslInit_nid_postfix(uint64_t pool_size) {
    (void)pool_size;
    return g_nextHandle.fetch_add(1, std::memory_order_relaxed);
}

int APS5_VABI sceSslTerm_nid_postfix(int ssl_ctx_id) {
    (void)ssl_ctx_id;
    return 0;
}

int APS5_VABI sceSslClose() {
 NotImplemented_nid_no_patch(__func__);
 return 0;
}

int APS5_VABI sceSslGetSerialNumber() {
 NotImplemented_nid_no_patch(__func__);
 return 0;
}

}

// Offline SSL compatibility exports; network requests are unavailable.
extern "C" {
int APS5_VABI sceSslCheckRecvPending() { return ERROR_NETWORK; }
int APS5_VABI sceSslConnect() { return ERROR_NETWORK; }
int APS5_VABI sceSslCreateConnection() { return ERROR_NETWORK; }
int APS5_VABI sceSslCreateSslConnection() { return ERROR_NETWORK; }
int APS5_VABI sceSslDeleteConnection() { return ERROR_NETWORK; }
int APS5_VABI sceSslDeleteSslConnection() { return ERROR_NETWORK; }
int APS5_VABI sceSslDisableOption() { return ERROR_NETWORK; }
int APS5_VABI sceSslDisableOptionInternal() { return ERROR_NETWORK; }
int APS5_VABI sceSslDisableOptionInternalInsecure() { return ERROR_NETWORK; }
int APS5_VABI sceSslDisableVerifyOption() { return ERROR_NETWORK; }
int APS5_VABI sceSslEnableOption() { return ERROR_NETWORK; }
int APS5_VABI sceSslEnableOptionInternal() { return ERROR_NETWORK; }
int APS5_VABI sceSslEnableVerifyOption() { return ERROR_NETWORK; }
int APS5_VABI sceSslFreeCaList() { return ERROR_NETWORK; }
int APS5_VABI sceSslFreeSslCertName() { return ERROR_NETWORK; }
int APS5_VABI sceSslGetAlpnSelected() { return ERROR_NETWORK; }
int APS5_VABI sceSslGetCaList() { return ERROR_NETWORK; }
int APS5_VABI sceSslGetFingerprint() { return ERROR_NETWORK; }
int APS5_VABI sceSslGetIssuerName() { return ERROR_NETWORK; }
int APS5_VABI sceSslGetNameEntryCount() { return ERROR_NETWORK; }
int APS5_VABI sceSslGetNameEntryInfo() { return ERROR_NETWORK; }
int APS5_VABI sceSslGetNanoSSLModuleId() { return ERROR_NETWORK; }
int APS5_VABI sceSslGetNotAfter() { return ERROR_NETWORK; }
int APS5_VABI sceSslGetNotBefore() { return ERROR_NETWORK; }
int APS5_VABI sceSslGetPeerCert() { return ERROR_NETWORK; }
int APS5_VABI sceSslGetPem() { return ERROR_NETWORK; }
int APS5_VABI sceSslGetSslError() { return ERROR_NETWORK; }
int APS5_VABI sceSslGetSubjectName() { return ERROR_NETWORK; }
int APS5_VABI sceSslInit() { return ERROR_NETWORK; }
int APS5_VABI sceSslLoadCert() { return ERROR_NETWORK; }
int APS5_VABI sceSslLoadRootCACert() { return ERROR_NETWORK; }
int APS5_VABI sceSslRead() { return ERROR_NETWORK; }
int APS5_VABI sceSslRecv() { return ERROR_NETWORK; }
int APS5_VABI sceSslReuseConnection() { return ERROR_NETWORK; }
int APS5_VABI sceSslSend() { return ERROR_NETWORK; }
int APS5_VABI sceSslSetAlpn() { return ERROR_NETWORK; }
int APS5_VABI sceSslSetMinSslVersion() { return ERROR_NETWORK; }
int APS5_VABI sceSslSetSslVersion() { return ERROR_NETWORK; }
int APS5_VABI sceSslSetVerifyCallback() { return ERROR_NETWORK; }
int APS5_VABI sceSslShowMemoryStat() { return ERROR_NETWORK; }
int APS5_VABI sceSslTerm() { return ERROR_NETWORK; }
int APS5_VABI sceSslUnloadCert() { return ERROR_NETWORK; }
int APS5_VABI sceSslWrite() { return ERROR_NETWORK; }
}

