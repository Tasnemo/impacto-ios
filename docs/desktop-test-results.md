# Desktop test results — Thread 02

Date: 2026-10-08 UTC. No proprietary game data was present, downloaded or committed.
Reproduction commands: [desktop-build.md](desktop-build.md). Source baseline:
Thread 01 commit `b468d4fb60314344a1c3b66096b263427b87d4c6`, already on
`origin/master` at thread startup. The handoff's earlier “not merged” statement
was stale. Engine `src/`, profiles and resources remain unchanged in Thread 02.

## Local environment and observed results

Host: Debian 12 x86-64 Amp orb, 4 CPUs, 7.8 GiB RAM, no swap. Successful build:
Ubuntu 24.04.5 container, GCC/G++ **13.3.0-6ubuntu2~24.04.1**, CMake **3.31.10**,
Ninja **1.11.1**, NASM **2.16.01**, vcpkg tool
**2026-02-21-82f3841f4f91e8389b7c7ddf61e6733683b2f67b**. vcpkg uses its downloaded
Ninja 1.13.2 for some ports. Mesa **25.2.8**, llvmpipe LLVM **20.1.2**; no hardware
acceleration. Exact versions and complete output: [logs](threads/02-logs/).

| Check | Actual result |
|---|---|
| Native Debian 12 GCC 12.2 configure/build | **Failed** while building OpenAL Soft: missing `<format>`; not an engine defect |
| Ubuntu configure, default `ci-release` features, both triplets `x64-linux-ci` | **Passed**, all 67 vcpkg packages built without any binary cache |
| `cmake --build ci-build/ubuntu24 --target install --parallel 2` | **Passed**, 403 build/install steps, exit 0 |
| `ctest --test-dir ci-build/ubuntu24 --output-on-failure` | **No tests found**; exit 0 does not establish test coverage |
| CLI smoke (`-lf <temp-log> -g`) | **Passed**, expected exit 1 and `Invalid number of arguments` |
| Launcher smoke (no `-g`, fresh config, Xvfb, software GL) | **Passed**, five seconds alive, SIGTERM → SDL quit → exit 0 |
| Installed tree copied to a fresh temporary directory | **Passed**, both smoke checks again; no missing `ldd` libraries |
| Reconfigure/incremental build | **Passed**; reconfigure relinked engine, subsequent build reported `ninja: no work to do.` |
| Harness negative control: remove `basepaths.lua` in disposable install copy | **Failed as expected**; harness rejects early launcher exit |
| `actionlint` 1.7.7 on `desktop.yml`, Bash syntax, Python compile, `git diff --check` | **Passed** |

There is no upstream first-party automated suite: no `enable_testing`, `add_test`
or CTest registration in the engine CMake project. Dependency projects' internal
tests are not an engine test suite and were not separately run.

## GitHub CI verification

[Run 37733016683](https://github.com/Tasnemo/impacto-ios/actions/runs/37733016683)
**passed** on commit
[a97fb46c](https://github.com/Tasnemo/impacto-ios/commit/a97fb46cdc890a8e7ca746264f5331b985b9733e),
Ubuntu 24.04.5/GCC 13.3. The job took **23m32s** with a cold cache. Configure,
compile/install, CTest discovery, CLI and launcher smoke checks, log upload and
vcpkg cache save all succeeded. CTest still reported no tests. CI toolchain and
smoke output are retained as `02-logs/ci-*.txt`; full build/configure output is
available in that run's diagnostic artifact. Cache restoration on a later warm
run was not tested. The final report commit changes documentation only and uses
`[skip ci]`; the tested code/workflow is unchanged from the linked commit.

GitHub emitted a nonfatal Node 20 deprecation annotation for `actions/cache@v4`,
which ran under Node 24 successfully. No tests were skipped to obtain green CI.

## Actual compiler and runtime output

From [build-ubuntu24.txt](threads/02-logs/build-ubuntu24.txt):

```text
[400/403] Linking C shared library _deps/libatrac9-build/libatrac9.so
[402/403] Linking CXX executable impacto
```

One upstream ImGui warning remains (`imgui.h:2369`, GCC `-Wstringop-overflow`),
in its separate dependency target. Engine warning settings were not weakened;
`IMPACTO_WARNINGS=ON` and the engine's warnings-as-errors remain enabled. CMake
also warns about LibAtrac9's missing `PUBLIC_HEADER DESTINATION`. Neither blocked
the build/install. These were not expanded into unrelated dependency fixes.

From [smoke-ubuntu24.txt](threads/02-logs/smoke-ubuntu24.txt):

```text
CRITICAL: [2026-10-08 05:37:51][General] Invalid number of arguments
PASS: missing CLI parameter rejected (exit 1)
INFO: [2026-10-08 05:37:51][General] Creating window
INFO: [2026-10-08 05:37:51][General] Trying to create desktop GL context
DEBUG: [2026-10-08 05:37:51][General] Window size (screen coords): 1280 x 720
DEBUG: [2026-10-08 05:37:51][Render] Compiling shader "Sprite"
DEBUG: [2026-10-08 05:37:51][General] Drawable size (pixels): 1280 x 720 (4x MSAA requested, render scale 1.000000)
INFO: [2026-10-08 05:37:56][General] Bye!
PASS: asset-free launcher stayed alive for 5s and quit cleanly (exit 0)
```

The expected CLI CRITICAL message belongs to a separate negative-input process.
The launcher process had no ERROR/CRITICAL log entries. It loaded both Lua config
files, wrote a fresh user config, created GL context/window, compiled shaders,
submitted textures and ran its launcher loop. Shutdown was an intentional SDL
quit event, not an accepted timeout/crash.

## Failures encountered and their resolutions

1. **GCC 12 standard library is too old for pinned OpenAL Soft.** Actual output:
   `common/alformat.hpp:28:10: fatal error: format: No such file or directory`.
   Full compiler invocation: [openal-gcc12-failed.txt](threads/02-logs/openal-gcc12-failed.txt).
   Later CMake messages about Ninja/compiler not being set followed the failed
   vcpkg install; Ninja was installed. Resolution: Ubuntu 24.04/GCC 13 container,
   matching upstream CI. No downgrades, dependency patches or engine rewrites.
2. **First CI smoke harness expected disabled console logging.**
   [Run 37730643328](https://github.com/Tasnemo/impacto-ios/actions/runs/37730643328)
   compiled and installed successfully, found no CTest tests, then failed the
   expected-log assertion. `GetDefaultLogToConsole()` returns false on desktop.
   Resolution: use existing `-lf` and inspect the engine's file log, including
   actual SDL `ERROR:`/`CRITICAL:` severity prefixes. No engine logging change.
3. A manual repeat-build invocation omitted the `/opt/vcpkg` bind mount and
   failed CMake regeneration. Restoring the mount fixed it; both subsequent
   incremental builds returned `ninja: no work to do.` The reproduction command
   includes the mount. This was an invocation error, not a source/build fix.

## What this does not establish

- No original game profile was started; no game assets were loaded. The upstream
  viewer profiles require game data too. Launcher initialization is not complete
  game-profile initialization.
- Audio output, video decode, VM execution, text/gameplay fidelity, phone/mail,
  saves, branches and endings remain **untested**. Steam SG still has no profile.
- Vulkan compiled but was not launched. Only software OpenGL was exercised.
- No iOS work, simulator/device testing, Windows or macOS builds occurred.
- Relocation worked in the same Ubuntu environment, not on arbitrary Linux
  distributions. The Ubuntu executable is not claimed to run on Debian 12.
- This is reproducible build procedure/source selection, not bit-for-bit output
  reproducibility or proof of STEINS;GATE compatibility.
