#include <cstdint>
#include <cstddef>
#include "SceTypes.hpp"
#include "prx/libSceCommonDialog/CommonDialog.hpp"
#include "prx/libc/include/General.hpp"

static bool g_initialized = false;

extern "C" {

#define COMMON_DIALOG_COMPAT(symbol) int APS5_VABI symbol() { return 0; }
COMMON_DIALOG_COMPAT(_ZNK3sce16CommonDialogUtil6Server10isCloseReqEv)
COMMON_DIALOG_COMPAT(_ZN3sce16CommonDialogUtil6ClientD1Ev)
COMMON_DIALOG_COMPAT(_ZN3sce16CommonDialogUtil6ServerC2EPKcmmis)
COMMON_DIALOG_COMPAT(_ZNK3sce16CommonDialogUtil6Client9getResultEv)
COMMON_DIALOG_COMPAT(_ZNK3sce16CommonDialogUtil6Client8isFinishEv)
COMMON_DIALOG_COMPAT(_ZN3sce16CommonDialogUtil6ServerD0Ev)
COMMON_DIALOG_COMPAT(_ZN3sce16CommonDialogUtil6ServerC2EPKcmis)
COMMON_DIALOG_COMPAT(_ZNK3sce16CommonDialogUtil6Client14getClientStateEv)
COMMON_DIALOG_COMPAT(_ZN3sce16CommonDialogUtil6Client15launchCmnDialogEv)
COMMON_DIALOG_COMPAT(_ZN3sce16CommonDialogUtil6Server6setRunEPvm)
COMMON_DIALOG_COMPAT(_ZN3sce16CommonDialogUtil6ClientD0Ev)
COMMON_DIALOG_COMPAT(_ZN3sce16CommonDialogUtil6ServerD1Ev)
COMMON_DIALOG_COMPAT(_ZN3sce16CommonDialogUtil6Server9setResultEi)
COMMON_DIALOG_COMPAT(_ZN3sce16CommonDialogUtil6Server13setFinishDataEPvm)
COMMON_DIALOG_COMPAT(_ZNK3sce16CommonDialogUtil6Client10isCloseReqEv)
COMMON_DIALOG_COMPAT(_ZN3sce16CommonDialogUtil6Server9setFinishEv)
COMMON_DIALOG_COMPAT(_ZNK3sce16CommonDialogUtil6Server9getUserIdEv)
COMMON_DIALOG_COMPAT(_ZNK3sce16CommonDialogUtil6Client8getAppIdEv)
COMMON_DIALOG_COMPAT(_ZNK3sce16CommonDialogUtil6Server10getVersionERj)
COMMON_DIALOG_COMPAT(_ZNK3sce16CommonDialogUtil6Server14getServerStateEv)
COMMON_DIALOG_COMPAT(_ZN3sce16CommonDialogUtil6Client13openCmnDialogEPvm)
COMMON_DIALOG_COMPAT(_ZN3sce16CommonDialogUtil6Client11updateStateEv)
COMMON_DIALOG_COMPAT(_ZN3sce16CommonDialogUtil6ServerD2Ev)
COMMON_DIALOG_COMPAT(_ZNK3sce16CommonDialogUtil6Server9isSetDataEv)
#undef COMMON_DIALOG_COMPAT

int APS5_VABI _ZN3sce16CommonDialogUtil6Client11closeModuleEv() {
 return 0;
}

int APS5_VABI _ZN3sce16CommonDialogUtil12getSelfAppIdEv() {
 return 0;
}

int APS5_VABI _ZN3sce16CommonDialogUtil6ClientD2Ev() {
 return 0;
}

int APS5_VABI _ZNK3sce16CommonDialogUtil6Client13getFinishDataEPvm() {
 return 0;
}

int APS5_VABI _ZNK3sce16CommonDialogUtil6Client19isInitializedStatusEv() {
 return 0;
}

int APS5_VABI sceCommonDialogInitialize(void) {
 if (g_initialized) {
  return COMMON_DIALOG_ERROR_ALREADY_INITIALIZED;
 }
 g_initialized = true;
 return COMMON_DIALOG_OK;
}

bool APS5_VABI sceCommonDialogIsUsed(void) {
 return false;
}

}
