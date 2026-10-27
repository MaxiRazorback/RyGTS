#include <cstdint>
#include <cstddef>
#include "SceTypes.hpp"
#include "prx/libc/include/General.hpp"
#include "prx/libSceHttp/src/HttpErrors.hpp"
#include <atomic>

// No network is emulated: contexts, templates and requests can be created, but any request
// that would touch the network fails with the library's network error.
static std::atomic<int> g_nextHandle{1};

extern "C" {

int APS5_VABI sceHttpParseResponseHeader() {
    return ERROR_NETWORK;
}

int APS5_VABI sceHttpAbortRequest(int request_id) {
    (void)request_id;
    return 0;
}

int APS5_VABI sceHttpGetMemoryPoolStats(int http_ctx_id, void* stats) {
    (void)http_ctx_id;
    (void)stats;
    return 0;
}

int APS5_VABI sceHttpAddRequestHeader(int id, const char* name, const char* value, uint32_t mode) {
    (void)id;
    (void)name;
    (void)value;
    (void)mode;
    return 0;
}

int APS5_VABI sceHttpCreateConnection(int tmpl_id, const char* server_name, const char* scheme, uint16_t port, int enable_keep_alive) {
    (void)tmpl_id;
    (void)server_name;
    (void)scheme;
    (void)port;
    (void)enable_keep_alive;
    return g_nextHandle.fetch_add(1, std::memory_order_relaxed);
}

int APS5_VABI sceHttpCreateConnectionWithURL(int tmpl_id, const char* url, int enable_keep_alive) {
    (void)tmpl_id;
    (void)url;
    (void)enable_keep_alive;
    return g_nextHandle.fetch_add(1, std::memory_order_relaxed);
}

int APS5_VABI sceHttpCreateEpoll(int http_ctx_id, HttpEpollHandle* eh) {
    (void)http_ctx_id;
    if (!eh) return ERROR_INVALID_VALUE;
    *eh = new HttpEpoll{};
    return 0;
}

int APS5_VABI sceHttpCreateRequest(int conn_id, int method, const char* path, uint64_t content_length) {
    (void)conn_id;
    (void)method;
    (void)path;
    (void)content_length;
    return g_nextHandle.fetch_add(1, std::memory_order_relaxed);
}

int APS5_VABI sceHttpCreateRequest2(int conn_id, const char* method, const char* path,
                                   uint64_t content_length) {
    (void)conn_id;
    (void)method;
    (void)path;
    (void)content_length;
    return g_nextHandle.fetch_add(1, std::memory_order_relaxed);
}

int APS5_VABI sceHttpCreateRequestWithURL2(int conn_id, const char* method, const char* url, uint64_t content_length) {
    (void)conn_id;
    (void)method;
    (void)url;
    (void)content_length;
    return g_nextHandle.fetch_add(1, std::memory_order_relaxed);
}

int APS5_VABI sceHttpCreateTemplate(int http_ctx_id, const char* user_agent, int http_ver, int is_auto_proxy_conf) {
    (void)http_ctx_id;
    (void)user_agent;
    (void)http_ver;
    (void)is_auto_proxy_conf;
    return g_nextHandle.fetch_add(1, std::memory_order_relaxed);
}

int APS5_VABI sceHttpDeleteConnection(int conn_id) {
    (void)conn_id;
    return 0;
}

int APS5_VABI sceHttpDeleteRequest(int req_id) {
    (void)req_id;
    return 0;
}

int APS5_VABI sceHttpDeleteTemplate(int tmpl_id) {
    (void)tmpl_id;
    return 0;
}

int APS5_VABI sceHttpDestroyEpoll(int http_ctx_id, HttpEpollHandle eh) {
    (void)http_ctx_id;
    delete eh;
    return 0;
}

int APS5_VABI sceHttpGetAllResponseHeaders(int request_id, char** header, size_t* header_size) {
    (void)request_id;
    (void)header;
    (void)header_size;
    return ERROR_NETWORK;
}

int APS5_VABI sceHttpGetResponseContentLength(int request_id, int* result, uint64_t* content_length) {
    (void)request_id;
    (void)result;
    (void)content_length;
    return ERROR_NETWORK;
}

int APS5_VABI sceHttpGetStatusCode(int request_id, int* status_code) {
    (void)request_id;
    (void)status_code;
    return ERROR_NETWORK;
}

int APS5_VABI sceHttpInit_nid_postfix(int memid, int ssl_ctx_id, uint64_t pool_size) {
    (void)memid;
    (void)ssl_ctx_id;
    (void)pool_size;
    return g_nextHandle.fetch_add(1, std::memory_order_relaxed);
}

int APS5_VABI sceHttpsDisableOption(int id, uint32_t ssl_flags) {
    (void)id;
    (void)ssl_flags;
    return 0;
}

int APS5_VABI sceHttpSendRequest(int request_id, const void* post_data, size_t size) {
    (void)request_id;
    (void)post_data;
    (void)size;
    return ERROR_NETWORK;
}

int APS5_VABI sceHttpSetAuthEnabled(int id, int enable) {
    (void)id;
    (void)enable;
    return 0;
}

int APS5_VABI sceHttpSetAutoRedirect(int id, int enable) {
    (void)id;
    (void)enable;
    return 0;
}

int APS5_VABI sceHttpSetConnectTimeOut(int id, uint32_t usec) {
    (void)id;
    (void)usec;
    return 0;
}

int APS5_VABI sceHttpSetEpoll(int id, HttpEpollHandle eh, void* user_arg) {
    (void)id;
    (void)eh;
    (void)user_arg;
    return 0;
}

int APS5_VABI sceHttpSetNonblock(int id, int enable) {
    (void)id;
    (void)enable;
    return 0;
}

int APS5_VABI sceHttpSetRecvTimeOut(int id, uint32_t usec) {
    (void)id;
    (void)usec;
    return 0;
}

int APS5_VABI sceHttpSetRequestContentLength(int request_id, uint64_t content_length) {
    (void)request_id;
    (void)content_length;
    return 0;
}

int APS5_VABI sceHttpSetResolveRetry(int id, int32_t retry) {
    (void)id;
    (void)retry;
    return 0;
}

int APS5_VABI sceHttpSetResolveTimeOut(int id, uint32_t usec) {
    (void)id;
    (void)usec;
    return 0;
}

int APS5_VABI sceHttpSetSendTimeOut(int id, uint32_t usec) {
    (void)id;
    (void)usec;
    return 0;
}

int APS5_VABI sceHttpsSetMinSslVersion(int id, uint32_t ssl_version) {
    (void)id;
    (void)ssl_version;
    return 0;
}

int APS5_VABI sceHttpsSetSslCallback(int id, HttpsCallback cbfunc, void* user_arg) {
    (void)id;
    (void)cbfunc;
    (void)user_arg;
    return 0;
}

int APS5_VABI sceHttpTerm_nid_postfix(int http_ctx_id) {
    (void)http_ctx_id;
    return 0;
}

int APS5_VABI sceHttpUnsetEpoll(int id) {
    (void)id;
    return 0;
}

int APS5_VABI sceHttpWaitRequest(HttpEpollHandle eh, HttpNBEvent* nbev, int maxevents, int timeout) {
    (void)eh;
    (void)nbev;
    (void)maxevents;
    (void)timeout;
    return ERROR_NETWORK;
}

int APS5_VABI sceHttpCreateRequestWithURL(int conn_id, int method, const char* url, uint64_t content_length) {
    (void)conn_id;
    (void)method;
    (void)url;
    (void)content_length;
    return g_nextHandle.fetch_add(1, std::memory_order_relaxed);
}

int APS5_VABI sceHttpReadData(int request_id, void* data, size_t size) {
    (void)request_id;
    (void)data;
    (void)size;
    return ERROR_NETWORK;
}

int APS5_VABI sceHttpSetChunkedTransferEnabled(int id, int enable) {
    (void)id;
    (void)enable;
    return 0;
}

}

// Remaining HTTP APIs report network unavailable; no PSN transport is emulated.
extern "C" {
int APS5_VABI sceHttp2AbortRequest() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2AddCookie() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2AddRequestHeader() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2AuthCacheFlush() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2CookieExport() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2CookieFlush() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2CookieImport() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2CreateCookieBox() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2CreateRequestWithURL() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2CreateTemplate() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2DeleteCookieBox() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2DeleteRequest() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2DeleteTemplate() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2GetAllResponseHeaders() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2GetAllTrailingHeaders() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2GetAuthEnabled() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2GetAutoRedirect() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2GetCookie() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2GetCookieBox() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2GetCookieStats() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2GetMemoryPoolStats() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2GetResponseContentLength() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2GetStatusCode() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2Init() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2ReadData() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2ReadDataAsync() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2RedirectCacheFlush() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2RemoveRequestHeader() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2SendRequest() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2SendRequestAsync() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2SetAuthEnabled() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2SetAuthInfoCallback() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2SetAutoRedirect() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2SetConnectionWaitTimeOut() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2SetConnectTimeOut() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2SetCookieBox() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2SetCookieMaxNum() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2SetCookieMaxNumPerDomain() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2SetCookieMaxSize() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2SetCookieRecvCallback() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2SetCookieSendCallback() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2SetInflateGZIPEnabled() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2SetMinSslVersion() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2SetPreSendCallback() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2SetRecvTimeOut() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2SetRedirectCallback() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2SetRequestContentLength() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2SetRequestNoContentLength() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2SetResolveRetry() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2SetResolveTimeOut() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2SetSendTimeOut() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2SetSslCallback() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2SetTimeOut() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2SslDisableOption() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2SslEnableOption() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2Term() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2WaitAsync() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2WebSocketClose() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2WebSocketCloseAsync() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2WebSocketCreateRequest() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2WebSocketSendDataMessage() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2WebSocketSendDataMessageAsync() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2WebSocketSendTextMessage() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2WebSocketSendTextMessageAsync() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2WebSocketSetPingInterval() { return ERROR_NETWORK; }
int APS5_VABI sceHttp2WebSocketSetPingTimeout() { return ERROR_NETWORK; }
int APS5_VABI sceHttpAbortRequestForce() { return ERROR_NETWORK; }
int APS5_VABI sceHttpAbortWaitRequest() { return ERROR_NETWORK; }
int APS5_VABI sceHttpAddCookie() { return ERROR_NETWORK; }
int APS5_VABI sceHttpAddQuery() { return ERROR_NETWORK; }
int APS5_VABI sceHttpAddRequestHeaderRaw() { return ERROR_NETWORK; }
int APS5_VABI sceHttpAuthCacheExport() { return ERROR_NETWORK; }
int APS5_VABI sceHttpAuthCacheFlush() { return ERROR_NETWORK; }
int APS5_VABI sceHttpAuthCacheImport() { return ERROR_NETWORK; }
int APS5_VABI sceHttpCacheClear() { return ERROR_NETWORK; }
int APS5_VABI sceHttpCacheClearAll() { return ERROR_NETWORK; }
int APS5_VABI sceHttpCacheCompleteRequest() { return ERROR_NETWORK; }
int APS5_VABI sceHttpCacheCreateRequest() { return ERROR_NETWORK; }
int APS5_VABI sceHttpCacheCreateRequestWithTag() { return ERROR_NETWORK; }
int APS5_VABI sceHttpCacheDeleteRequest() { return ERROR_NETWORK; }
int APS5_VABI sceHttpCacheInit() { return ERROR_NETWORK; }
int APS5_VABI sceHttpCacheReadData() { return ERROR_NETWORK; }
int APS5_VABI sceHttpCacheRedirectedConnectionEnabled() { return ERROR_NETWORK; }
int APS5_VABI sceHttpCacheRetrieve() { return ERROR_NETWORK; }
int APS5_VABI sceHttpCacheRetrieveWithMemoryPool() { return ERROR_NETWORK; }
int APS5_VABI sceHttpCacheRevalidate() { return ERROR_NETWORK; }
int APS5_VABI sceHttpCacheRevalidateWithMemoryPool() { return ERROR_NETWORK; }
int APS5_VABI sceHttpCacheSetCacheSharing() { return ERROR_NETWORK; }
int APS5_VABI sceHttpCacheSetData() { return ERROR_NETWORK; }
int APS5_VABI sceHttpCacheSetQuota() { return ERROR_NETWORK; }
int APS5_VABI sceHttpCacheSetResponseHeader() { return ERROR_NETWORK; }
int APS5_VABI sceHttpCacheSystemClearAll() { return ERROR_NETWORK; }
int APS5_VABI sceHttpCacheSystemInit() { return ERROR_NETWORK; }
int APS5_VABI sceHttpCacheSystemSendStatistics() { return ERROR_NETWORK; }
int APS5_VABI sceHttpCacheSystemShutdown() { return ERROR_NETWORK; }
int APS5_VABI sceHttpCacheSystemTerm() { return ERROR_NETWORK; }
int APS5_VABI sceHttpCacheTerm() { return ERROR_NETWORK; }
int APS5_VABI sceHttpCookieExport() { return ERROR_NETWORK; }
int APS5_VABI sceHttpCookieFlush() { return ERROR_NETWORK; }
int APS5_VABI sceHttpCookieImport() { return ERROR_NETWORK; }
int APS5_VABI sceHttpDbgEnableProfile() { return ERROR_NETWORK; }
int APS5_VABI sceHttpDbgGetConnectionStat() { return ERROR_NETWORK; }
int APS5_VABI sceHttpDbgGetRequestStat() { return ERROR_NETWORK; }
int APS5_VABI sceHttpDbgSetPrintf() { return ERROR_NETWORK; }
int APS5_VABI sceHttpDbgShowConnectionStat() { return ERROR_NETWORK; }
int APS5_VABI sceHttpDbgShowMemoryPoolStat() { return ERROR_NETWORK; }
int APS5_VABI sceHttpDbgShowRequestStat() { return ERROR_NETWORK; }
int APS5_VABI sceHttpDbgShowStat() { return ERROR_NETWORK; }
int APS5_VABI sceHttpGetAcceptEncodingGZIPEnabled() { return ERROR_NETWORK; }
int APS5_VABI sceHttpGetAuthEnabled() { return ERROR_NETWORK; }
int APS5_VABI sceHttpGetAutoRedirect() { return ERROR_NETWORK; }
int APS5_VABI sceHttpGetConnectionStat() { return ERROR_NETWORK; }
int APS5_VABI sceHttpGetCookie() { return ERROR_NETWORK; }
int APS5_VABI sceHttpGetCookieEnabled() { return ERROR_NETWORK; }
int APS5_VABI sceHttpGetCookieStats() { return ERROR_NETWORK; }
int APS5_VABI sceHttpGetEpoll() { return ERROR_NETWORK; }
int APS5_VABI sceHttpGetEpollId() { return ERROR_NETWORK; }
int APS5_VABI sceHttpGetLastErrno() { return ERROR_NETWORK; }
int APS5_VABI sceHttpGetNonblock() { return ERROR_NETWORK; }
int APS5_VABI sceHttpGetRegisteredCtxIds() { return ERROR_NETWORK; }
int APS5_VABI sceHttpInit() { return ERROR_NETWORK; }
int APS5_VABI sceHttpParseStatusLine() { return ERROR_NETWORK; }
int APS5_VABI sceHttpRedirectCacheFlush() { return ERROR_NETWORK; }
int APS5_VABI sceHttpRemoveRequestHeader() { return ERROR_NETWORK; }
int APS5_VABI sceHttpRequestGetAllHeaders() { return ERROR_NETWORK; }
int APS5_VABI sceHttpsDisableOptionPrivate() { return ERROR_NETWORK; }
int APS5_VABI sceHttpsEnableOption() { return ERROR_NETWORK; }
int APS5_VABI sceHttpsEnableOptionPrivate() { return ERROR_NETWORK; }
int APS5_VABI sceHttpSetAcceptEncodingGZIPEnabled() { return ERROR_NETWORK; }
int APS5_VABI sceHttpSetAuthInfoCallback() { return ERROR_NETWORK; }
int APS5_VABI sceHttpSetCookieEnabled() { return ERROR_NETWORK; }
int APS5_VABI sceHttpSetCookieMaxNum() { return ERROR_NETWORK; }
int APS5_VABI sceHttpSetCookieMaxNumPerDomain() { return ERROR_NETWORK; }
int APS5_VABI sceHttpSetCookieMaxSize() { return ERROR_NETWORK; }
int APS5_VABI sceHttpSetCookieRecvCallback() { return ERROR_NETWORK; }
int APS5_VABI sceHttpSetCookieSendCallback() { return ERROR_NETWORK; }
int APS5_VABI sceHttpSetCookieTotalMaxSize() { return ERROR_NETWORK; }
int APS5_VABI sceHttpSetDefaultAcceptEncodingGZIPEnabled() { return ERROR_NETWORK; }
int APS5_VABI sceHttpSetDelayBuildRequestEnabled() { return ERROR_NETWORK; }
int APS5_VABI sceHttpSetEpollId() { return ERROR_NETWORK; }
int APS5_VABI sceHttpSetHttp09Enabled() { return ERROR_NETWORK; }
int APS5_VABI sceHttpSetInflateGZIPEnabled() { return ERROR_NETWORK; }
int APS5_VABI sceHttpSetPolicyOption() { return ERROR_NETWORK; }
int APS5_VABI sceHttpSetPriorityOption() { return ERROR_NETWORK; }
int APS5_VABI sceHttpSetProxy() { return ERROR_NETWORK; }
int APS5_VABI sceHttpSetRecvBlockSize() { return ERROR_NETWORK; }
int APS5_VABI sceHttpSetRedirectCallback() { return ERROR_NETWORK; }
int APS5_VABI sceHttpSetRequestStatusCallback() { return ERROR_NETWORK; }
int APS5_VABI sceHttpSetResponseHeaderMaxSize() { return ERROR_NETWORK; }
int APS5_VABI sceHttpSetSocketCreationCallback() { return ERROR_NETWORK; }
int APS5_VABI sceHttpsFreeCaList() { return ERROR_NETWORK; }
int APS5_VABI sceHttpsGetCaList() { return ERROR_NETWORK; }
int APS5_VABI sceHttpsGetSslError() { return ERROR_NETWORK; }
int APS5_VABI sceHttpsLoadCert() { return ERROR_NETWORK; }
int APS5_VABI sceHttpsSetSslVersion() { return ERROR_NETWORK; }
int APS5_VABI sceHttpsUnloadCert() { return ERROR_NETWORK; }
int APS5_VABI sceHttpTerm() { return ERROR_NETWORK; }
int APS5_VABI sceHttpTryGetNonblock() { return ERROR_NETWORK; }
int APS5_VABI sceHttpTrySetNonblock() { return ERROR_NETWORK; }
int APS5_VABI sceHttpUriCopy() { return ERROR_NETWORK; }
int APS5_VABI sceHttpUriMerge() { return ERROR_NETWORK; }
int APS5_VABI sceHttpUriSweepPath() { return ERROR_NETWORK; }
int APS5_VABI sceHttpUriUnescape() { return ERROR_NETWORK; }
}

