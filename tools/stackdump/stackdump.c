// Prints, for every thread of a process, its instruction pointer and the values on its stack that
// point into a loaded module (likely return addresses), as module+offset.
// Usage: stackdump <pid> [stack qwords to scan, default 256]
#include <windows.h>
#include <psapi.h>
#include <stdio.h>
#include <stdlib.h>
#include <tlhelp32.h>

typedef struct {
    ULONG_PTR base, end;
    char name[64];
} Module;

static Module modules[512];
static int module_count;

static const Module* find_module(ULONG_PTR address) {
    for (int i = 0; i < module_count; ++i)
        if (address >= modules[i].base && address < modules[i].end) return &modules[i];
    return NULL;
}

static void print_address(ULONG_PTR address) {
    const Module* m = find_module(address);
    if (m) printf("%s+0x%llx", m->name, (unsigned long long)(address - m->base));
    else printf("0x%llx", (unsigned long long)address);
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    DWORD pid = (DWORD)strtoul(argv[1], NULL, 10);
    int depth = argc > 2 ? atoi(argv[2]) : 256;
    HANDLE process = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, FALSE, pid);
    if (!process) { printf("OpenProcess failed %lu\n", GetLastError()); return 1; }
    HMODULE handles[512];
    DWORD needed;
    if (EnumProcessModulesEx(process, handles, sizeof(handles), &needed, LIST_MODULES_ALL)) {
        for (DWORD i = 0; i < needed / sizeof(HMODULE) && module_count < 512; ++i) {
            MODULEINFO info;
            if (!GetModuleInformation(process, handles[i], &info, sizeof(info))) continue;
            Module* m = &modules[module_count++];
            m->base = (ULONG_PTR)info.lpBaseOfDll;
            m->end = m->base + info.SizeOfImage;
            GetModuleBaseNameA(process, handles[i], m->name, sizeof(m->name));
        }
    }
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
    THREADENTRY32 entry = {sizeof(entry)};
    ULONG_PTR* stack = malloc(sizeof(ULONG_PTR) * depth);
    for (BOOL ok = Thread32First(snapshot, &entry); ok; ok = Thread32Next(snapshot, &entry)) {
        if (entry.th32OwnerProcessID != pid) continue;
        HANDLE thread = OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT | THREAD_QUERY_INFORMATION, FALSE, entry.th32ThreadID);
        if (!thread) continue;
        PWSTR description = NULL;
        SuspendThread(thread);
        CONTEXT context = {0};
        context.ContextFlags = CONTEXT_CONTROL | CONTEXT_INTEGER;
        if (GetThreadContext(thread, &context)) {
            printf("thread %lu", entry.th32ThreadID);
            if (SUCCEEDED(GetThreadDescription(thread, &description)) && description && description[0]) printf(" \"%ls\"", description);
            printf(" r12=%llx r13=%llx r14=%llx r15=%llx rbx=%llx: rip=", (unsigned long long)context.R12, (unsigned long long)context.R13, (unsigned long long)context.R14, (unsigned long long)context.R15, (unsigned long long)context.Rbx);
            print_address(context.Rip);
            printf("\n");
            SIZE_T read = 0;
            ReadProcessMemory(process, (LPCVOID)context.Rsp, stack, sizeof(ULONG_PTR) * depth, &read);
            int shown = 0;
            for (SIZE_T i = 0; i < read / sizeof(ULONG_PTR) && shown < 24; ++i) {
                const Module* m = find_module(stack[i]);
                if (!m) continue;
                printf("    ");
                print_address(stack[i]);
                printf("\n");
                ++shown;
            }
        }
        if (description) LocalFree(description);
        ResumeThread(thread);
        CloseHandle(thread);
    }
    return 0;
}
