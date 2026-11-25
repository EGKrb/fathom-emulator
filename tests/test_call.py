"""End-to-end test of the emulator: a full minidump of a running process (a child started for the test, of the
same architecture as this Python), then fathom_emu.py calls lstrlenA("hello") and RtlComputeCrc32 in it and
runs examples/crc_strings.py.

    python tests/test_call.py

Exit code 0 when the results are right. Needs the packages of requirements.txt.
"""
import json
import os
import subprocess
import sys
import tempfile
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMULATOR = os.path.join(ROOT, "fathom_emu.py")
sys.path.insert(0, os.path.join(ROOT, "tools"))
from dump_process import dump_process  # noqa: E402


def emulate(*arguments) -> dict:
    with tempfile.TemporaryDirectory() as folder:
        result = os.path.join(folder, "result.json")
        run = subprocess.run([sys.executable, EMULATOR, "--result", result, *arguments], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=600)
        if not os.path.isfile(result):
            raise RuntimeError(f"fathom_emu.py gave no result:\n{run.stdout}\n{run.stderr}")
        with open(result, encoding="utf-8") as f:
            result = json.load(f)
        if not result.get("ok"):
            print(run.stdout, run.stderr, sep="\n")
        return result


def main() -> int:
    # a process of this architecture that waits: Python itself, sleeping
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(600)"])
    with tempfile.TemporaryDirectory() as folder:
        dump = os.path.join(folder, "child.dmp")
        try:
            dump_process(child.pid, dump)
        finally:
            child.kill()
            child.wait()
        failures = 0
        result = emulate("call", dump, "kernel32!lstrlenA", "str:hello")
        value = int(result.get("return", "-1"), 0)
        print(f"lstrlenA(\"hello\") in the emulator: {value}")
        failures += value != 5
        result = emulate("call", dump, "ntdll!RtlComputeCrc32", "0", "str:hello", "5")
        value = int(result.get("return", "-1"), 0)
        expected = zlib.crc32(b"hello")
        print(f"RtlComputeCrc32(0, \"hello\", 5) in the emulator: {value:#x} (expected {expected:#x})")
        failures += value != expected
        result = emulate("script", dump, os.path.join(ROOT, "examples", "crc_strings.py"), "ntdll!RtlComputeCrc32")
        value = int(result.get("return", "-1"), 0)
        expected = zlib.crc32(b"dumpulator")
        print(f"examples/crc_strings.py in the emulator: {value:#x} (expected {expected:#x})")
        failures += value != expected
    print("OK" if not failures else f"{failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
