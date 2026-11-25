# Changelog

The emulator follows the versions of [Fathom](https://github.com/EGKrb/Fathom): version X.Y.Z is the
`emulator` folder of Fathom X.Y.Z. Its history before this repository is in
[Fathom's changelog](https://github.com/EGKrb/Fathom/blob/main/CHANGELOG.md).

## [1.9.0] - 2026-11-25

First release as a repository of its own: the emulator of Fathom 1.9.0 (commit `4965e46b`).

- dumpulator with Fathom's changes: Windows system calls and exceptions, threads interleaved as on a
  multiprocessor with virtual time, DLL loading, console, registry and files (an overlay over the
  host), windows drawn to images, simulated network, child and simultaneous processes, COM, GDI+,
  OpenGL, Direct3D 9 to 12 (DXBC and DXIL shaders of every stage, ray tracing with intersection
  shaders, RayQuery and local root signatures, mesh and amplification shaders, work graphs, shader
  model 6.9), AVX / AVX2 / FMA / BMI.
- `fathom_emu.py`: `info`, `call`, `run`, `script`, `setup`; x64dbg traces of the emulated code.
- New here: `tools/dump_process.py` (a full minidump of a running process), `hosts/build.ps1` (builds
  `emulator_host` for x64 and x86), `tests/test_call.py` (end to end, on a dump of a running
  process, 64-bit or 32-bit), GitHub Actions on dumps of 64-bit and 32-bit processes.

[1.9.0]: https://github.com/EGKrb/fathom-emulator/releases/tag/v1.9.0
