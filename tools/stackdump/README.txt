stackdump: prints every thread of a process with its instruction pointer and the module
addresses found on its stack. The renderer runs tools\stackdump.exe (next to GTSport.exe) when a
shader build or the GPU stays stuck, writing user\log\stuck-stacks.txt or gpu-stuck-stacks.txt.

Build (MSYS2 ucrt64): gcc -O2 -o stackdump.exe stackdump.c -lpsapi
