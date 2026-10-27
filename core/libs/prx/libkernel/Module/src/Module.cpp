#include <cstdint>
#include <cstddef>
#include <cstring>
#include <cstdio>
#include <mutex>
#ifdef _WIN32
#include <windows.h>
#endif
#include "SceTypes.hpp"
#include "prx/libc/include/General.hpp"
#include "prx/libkernel/DirectMemory/DirectMemory.hpp"
#include "prx/libkernel/KernelErrors.hpp"

extern "C" {
void* APS5_VABI dlopen_nid_postfix(const char* path, int flags);
void* APS5_VABI dlsym_nid_postfix(void* handle, const char* name);
int APS5_VABI dlclose_nid_postfix(void* handle);
}

namespace {
constexpr int kRtldNow = 2;
}

extern "C" {

int APS5_VABI sceKernelDlsym(KernelModule handle, const char* symbol, void** addr) {
 if (!symbol || !addr) return SCE_KERNEL_ERROR_EFAULT;
 void* found = dlsym_nid_postfix(reinterpret_cast<void*>(static_cast<intptr_t>(handle)), symbol);
 if (!found) return SCE_KERNEL_ERROR_ESRCH;
 *addr = found;
 return 0;
}

// The guest libunwind (firmware libc) finds a module's DWARF unwind tables through this; without it
// every C++ throw in the game crashes ("Unsupported .eh_frame_hdr version"). Converted modules are PE
// images whose .ehmeta section starts with the RVA of the original .eh_frame_hdr.
int APS5_VABI sceKernelGetModuleInfoForUnwind(uint64_t addr, int flags, ModuleInfoForUnwind* info) {
 (void)flags;
 if (!info) return SCE_KERNEL_ERROR_EFAULT;
#ifdef _WIN32
 MEMORY_BASIC_INFORMATION memory{};
 if (!VirtualQuery(reinterpret_cast<void*>(addr), &memory, sizeof(memory)) || memory.Type != MEM_IMAGE)
  return SCE_KERNEL_ERROR_ESRCH;
 const auto* base = static_cast<const std::uint8_t*>(memory.AllocationBase);
 {
  // The frames C++ exceptions unwind through (each address once, the first 256), to find where
  // the game throws.
  static std::mutex mutex;
  static std::uint64_t seen[256];
  static unsigned count = 0;
  std::scoped_lock lock{mutex};
  bool known = false;
  for (unsigned i = 0; i < count; ++i) known |= seen[i] == addr;
  if (!known && count < 256) {
   seen[count++] = addr;
   char module[MAX_PATH] = {};
   GetModuleFileNameA(reinterpret_cast<HMODULE>(const_cast<std::uint8_t*>(base)), module, sizeof(module) - 1);
   const char* name = std::strrchr(module, '\\');
   std::fprintf(stderr, "[unwind] %s+0x%llx\n", name ? name + 1 : module,
                static_cast<unsigned long long>(addr - reinterpret_cast<std::uint64_t>(base)));
  }
 }
 const auto* dos = reinterpret_cast<const IMAGE_DOS_HEADER*>(base);
 if (dos->e_magic != IMAGE_DOS_SIGNATURE) return SCE_KERNEL_ERROR_ESRCH;
 const auto* nt = reinterpret_cast<const IMAGE_NT_HEADERS64*>(base + dos->e_lfanew);
 if (nt->Signature != IMAGE_NT_SIGNATURE) return SCE_KERNEL_ERROR_ESRCH;
 const auto* sections = IMAGE_FIRST_SECTION(nt);
 const std::uint8_t* header = nullptr;
 for (unsigned i = 0; i < nt->FileHeader.NumberOfSections; ++i) {
  if (std::memcmp(sections[i].Name, ".ehmeta", 8) == 0) {
   std::uint32_t rva = 0;
   std::memcpy(&rva, base + sections[i].VirtualAddress, sizeof(rva));
   header = base + rva;
  }
 }
 // eh_frame_ptr: pcrel sdata4 (0x1b) or udata4/sdata4 absolute (0x03/0x0b)
 if (!header || header[0] != 1) return SCE_KERNEL_ERROR_ESRCH;
 std::int32_t frame_ptr = 0;
 std::memcpy(&frame_ptr, header + 4, sizeof(frame_ptr));
 std::uint64_t frame = 0;
 if (header[1] == 0x1b) frame = reinterpret_cast<std::uint64_t>(header + 4) + static_cast<std::int64_t>(frame_ptr);
 else if (header[1] == 0x03) frame = static_cast<std::uint32_t>(frame_ptr);
 else if (header[1] == 0x0b) frame = static_cast<std::uint64_t>(static_cast<std::int64_t>(frame_ptr));
 else return SCE_KERNEL_ERROR_ESRCH;
 std::uint64_t frame_size = 0;
 for (unsigned i = 0; i < nt->FileHeader.NumberOfSections; ++i) {
  const auto start = reinterpret_cast<std::uint64_t>(base) + sections[i].VirtualAddress;
  const auto end = start + sections[i].Misc.VirtualSize;
  if (frame >= start && frame < end) frame_size = end - frame;
 }
 std::memset(info, 0, sizeof(*info));
 info->st_size = sizeof(ModuleInfoForUnwind);
 GetModuleFileNameA(reinterpret_cast<HMODULE>(const_cast<std::uint8_t*>(base)), info->name, sizeof(info->name) - 1);
 info->eh_frame_hdr_addr = reinterpret_cast<std::uint64_t>(header);
 info->eh_frame_addr = frame;
 info->eh_frame_size = frame_size;
 info->seg0_addr = reinterpret_cast<std::uint64_t>(base);
 info->seg0_size = nt->OptionalHeader.SizeOfImage;
 return 0;
#else
 (void)addr;
 NotImplemented_nid_no_patch(__func__);
 return 0;
#endif
}

int APS5_VABI sceKernelGetModuleInfoFromAddr(uint64_t addr, int n, ModuleInfo* r) {
 (void)addr;
 (void)n;
 (void)r;
 NotImplemented_nid_no_patch(__func__);
 return 0;
}

KernelModule APS5_VABI sceKernelLoadStartModule(const char* module_file_name, size_t args, const void* argp, uint32_t flags, const KernelLoadModuleOpt* opt, int* res) {
 (void)args;
 (void)argp;
 (void)flags;
 (void)opt;
 if (res) *res = 0;
 if (!module_file_name) return static_cast<KernelModule>(SCE_KERNEL_ERROR_EFAULT);
 void* handle = dlopen_nid_postfix(module_file_name, kRtldNow);
 if (!handle) return static_cast<KernelModule>(SCE_KERNEL_ERROR_ENOENT);
 return static_cast<KernelModule>(reinterpret_cast<intptr_t>(handle));
}

int APS5_VABI sceKernelStopUnloadModule(KernelModule handle, size_t args, const void* argp, uint32_t flags, const KernelUnloadModuleOpt* opt, int* res) {
 (void)args;
 (void)argp;
 (void)flags;
 (void)opt;
 if (res) *res = 0;
 return dlclose_nid_postfix(reinterpret_cast<void*>(static_cast<intptr_t>(handle))) == 0 ? 0 : SCE_KERNEL_ERROR_ESRCH;
}

}

extern "C" {

int APS5_VABI __elf_phdr_match_addr_nid_postfix(ModuleInfo* module, std::uint64_t address) {
    (void)module;
    (void)address;
    NotImplemented_nid_no_patch(__func__);
    return 0;
}

// unknown signature
std::int32_t APS5_VABI sceKernelInternalMemoryGetModuleSegmentInfo_nid_postfix(void* result) {
    (void)result;
    NotImplemented_nid_no_patch(__func__);
    return 0;
}

}
