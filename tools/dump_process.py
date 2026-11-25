"""Saves a running process to a minidump with its full memory, as the emulator needs it (dbghelp's
MiniDumpWriteDump, with the streams x64dbg's `minidump` command writes).

    python tools/dump_process.py PID app.dmp

Run it with a Python of the process's architecture: a 32-bit process dumped by a 64-bit Python gives a
WoW64 dump (the 64-bit view of the process), which the emulator does not load.
"""
import ctypes
import msvcrt
import sys
from ctypes import wintypes

# MiniDumpWithFullMemory | WithHandleData | WithUnloadedModules | WithFullMemoryInfo | WithThreadInfo:
# what dumpulator reads (the memory info list among others)
MINIDUMP_TYPE = 0x2 | 0x4 | 0x20 | 0x800 | 0x1000
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
PROCESS_DUP_HANDLE = 0x0040


def dump_process(pid: int, path: str):
    """Writes a full minidump of the process `pid` to `path`."""
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    dbghelp = ctypes.WinDLL("dbghelp", use_last_error=True)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    dbghelp.MiniDumpWriteDump.restype = wintypes.BOOL
    dbghelp.MiniDumpWriteDump.argtypes = (wintypes.HANDLE, wintypes.DWORD, wintypes.HANDLE, ctypes.c_int,
                                          ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)
    process = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ | PROCESS_DUP_HANDLE, False, pid)
    if not process:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        with open(path, "wb") as f:
            handle = msvcrt.get_osfhandle(f.fileno())
            if not dbghelp.MiniDumpWriteDump(process, pid, handle, MINIDUMP_TYPE, None, None, None):
                raise ctypes.WinError(ctypes.get_last_error())
    finally:
        kernel32.CloseHandle(process)


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__.strip())
        return 2
    dump_process(int(sys.argv[1], 0), sys.argv[2])
    print(f"saved process {sys.argv[1]} to {sys.argv[2]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
