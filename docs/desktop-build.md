# Reproducible desktop build

Thread 02, 2026-10-08. Target: Linux x86-64. This builds the existing engine,
not an iOS port or a STEINS;GATE compatibility implementation. Observed results
and failure evidence are in [desktop-test-results.md](desktop-test-results.md).

## Configuration and dependency ownership

Use upstream CMake/Ninja preset `ci-release`, with target and host triplets both
`x64-linux-ci`. It builds Release shared dependencies and preserves the default
OpenGL, Vulkan, ImGui, OpenAL, FFmpeg and libass features. DX9 is already disabled
by upstream on Unix. Do not set `IMPACTO_DISABLE_*` to `OFF`: some upstream checks
test whether the variable is **defined**, rather than its truth value.

- CMake: **3.31.10** (upstream requires at least 3.28).
- GCC/libstdc++: **13 or newer**; local Ubuntu build uses **13.3.0**. Debian 12's
  default GCC 12.2 fails in OpenAL Soft on missing `<format>`; use the container
  below rather than changing engine/dependency functionality.
- vcpkg checkout and manifest baseline: `62159a45e18f3a9ac0548628dcaf74fcb60c6ff9`.
- SDL3 **3.4.0**, OpenAL Soft **1.25.1**, FFmpeg **7.1.2#5** are manifest overrides.
- Other dependency versions come from that baseline; avcpp uses the existing
  `portfiles/avcpp` overlay. The full resolved list is in the configure log.
- CMake FetchContent: LibAtrac9 is pinned to
  `efca2e3af35562a09a9bb6deed90e45b4b824dc4` (formerly moving `master`);
  magic_enum already uses `591b64351ea8442f8b8fa044ff335d6943e8e6e0`;
  ImGui retains upstream tag `v1.92.9b-docking`, resolving to
  `b48d1afbe8ee8b238e2961dc363a949dd7304e23` during this build.
- System libraries supply Linux display/audio/device interfaces; vcpkg supplies
  the engine libraries. Mono/NuGet are **not required** by this workflow.

This is a pinned-source build recipe, not a claim of bit-identical binaries:
distribution security updates, runner images, compiler patches and the ImGui
tag can change. Record toolchain versions when reproducing it.

## Reproduce natively on Ubuntu 24.04

Start from a clean checkout of this branch (see [handoff.md](handoff.md)). Do not
place commercial data under the source tree: upstream's desktop install command
copies `resources/` recursively. No commercial assets are needed for these checks.
Allow several GB of disk and at least 8 GB RAM. Limit engine compilation to two
jobs; compiling all translation units concurrently can exhaust an orb's memory.

Run from the repository root in Bash:

```bash
sudo bash .github/scripts/install-desktop-deps.sh

# Use an external tools directory, not a vendored dependency checkout.
export IMPACTO_TOOLS="$HOME/.local/share/impacto-tools"
mkdir -p "$IMPACTO_TOOLS"
python3 -m venv "$IMPACTO_TOOLS/cmake"
"$IMPACTO_TOOLS/cmake/bin/pip" install cmake==3.31.10
export PATH="$IMPACTO_TOOLS/cmake/bin:$PATH"

export VCPKG_ROOT="$IMPACTO_TOOLS/vcpkg"
git clone https://github.com/microsoft/vcpkg.git "$VCPKG_ROOT"
git -C "$VCPKG_ROOT" checkout 62159a45e18f3a9ac0548628dcaf74fcb60c6ff9
"$VCPKG_ROOT/bootstrap-vcpkg.sh" -disableMetrics

export VCPKG_MAX_CONCURRENCY=4
export CMAKE_BUILD_PARALLEL_LEVEL=2
export VCPKG_BINARY_SOURCES=clear  # proves no private binary feed is required
mkdir -p ci-build/logs
set -o pipefail  # do not let tee hide compiler/test failures
cmake --preset ci-release \
  -DVCPKG_TARGET_TRIPLET=x64-linux-ci \
  -DVCPKG_HOST_TRIPLET=x64-linux-ci 2>&1 | tee ci-build/logs/configure.log
cmake --build --preset ci-release 2>&1 | tee ci-build/logs/build.log
ctest --test-dir ci-build/ci-release --output-on-failure \
  2>&1 | tee ci-build/logs/ctest.log
xvfb-run -a python3 .github/scripts/desktop-smoke.py \
  release/ci-release/impacto 2>&1 | tee ci-build/logs/smoke.log
```

For an existing tools checkout, verify the pinned commit instead of cloning into
an existing directory. Repeat configure/build after source edits; do not change
compilers in an existing CMake build directory.

Optional local vcpkg binary caching, without credentials:

```bash
mkdir -p "$HOME/.cache/impacto-vcpkg"
export VCPKG_BINARY_SOURCES="clear;files,$HOME/.cache/impacto-vcpkg,readwrite"
```

The installed executable is `release/ci-release/impacto`, next to `lib/`,
`profiles/`, `resources/`, `shaders/`, `basepaths.lua` and `gamedefinitions.lua`.
Run the **installed executable**, not the build-tree binary: desktop startup
changes its working directory to the executable directory and expects these
files there. Keep the complete installed directory together when moving it.

## Reproduce in a Debian-based orb using Ubuntu Docker

The orb's native GCC 12 build failed; the Ubuntu image provides GCC 13 without
replacing the host's system libraries. Docker is already installed in this orb.
If its daemon is not running, the following **orb-only** command starts a
supervised local daemon (no published port is needed):

```bash
amp orb service start desktop-docker --command \
  'sudo dockerd --storage-driver=vfs --iptables=false --bridge=none --ip-forward=false --ip-masq=false'
```

On a normal Linux machine use its existing Docker daemon. Build a tools image;
only the two named files enter the Docker build context, never game data:

```bash
tar -c docker/desktop.Dockerfile .github/scripts/install-desktop-deps.sh | \
  sudo docker build --network=host -t impacto-desktop:ubuntu24 \
    -f docker/desktop.Dockerfile -
```

Clone/bootstrap the same pinned vcpkg checkout as above. The Dockerfile pins the
tested Ubuntu image digest and CMake, but apt package security updates still move.
Keep the native GCC 12 build directory separate; this command uses
`ci-build/ubuntu24` and `release/ubuntu24`:

```bash
sudo docker run --rm --network=host \
  -v "$PWD:$PWD" -w "$PWD" -v "$VCPKG_ROOT:/opt/vcpkg" \
  -e VCPKG_ROOT=/opt/vcpkg -e VCPKG_MAX_CONCURRENCY=4 \
  -e VCPKG_BINARY_SOURCES=clear impacto-desktop:ubuntu24 bash -c '
    set -euo pipefail
    mkdir -p ci-build/logs
    cmake --preset ci-release -B ci-build/ubuntu24 \
      -DCMAKE_INSTALL_PREFIX="$PWD/release/ubuntu24" \
      -DVCPKG_TARGET_TRIPLET=x64-linux-ci \
      -DVCPKG_HOST_TRIPLET=x64-linux-ci 2>&1 | tee ci-build/logs/configure-ubuntu24.log
    cmake --build ci-build/ubuntu24 --target install --parallel 2 \
      2>&1 | tee ci-build/logs/build-ubuntu24.log
    ctest --test-dir ci-build/ubuntu24 --output-on-failure \
      2>&1 | tee ci-build/logs/ctest-ubuntu24.log
    xvfb-run -a python3 .github/scripts/desktop-smoke.py release/ubuntu24/impacto \
      2>&1 | tee ci-build/logs/smoke-ubuntu24.log
  '
```

Container-created build files are root-owned; they are generated, gitignored
outputs, not source edits. Run the Ubuntu binary **inside Ubuntu** (as above),
not directly on Debian 12: newer glibc/libstdc++ may be required. Do not run
simultaneous builds sharing one writable vcpkg checkout.

## Runtime scope

On a real Linux desktop, run
`./release/ci-release/impacto -lf /tmp/impacto.log -ll Debug`. Desktop console
logging is off by default; read the explicit log file. Without
game data the launcher is the intended asset-free state. This engine has **no
`--help` handler**; unknown arguments are ignored, so `--help` is not a CLI test.

The smoke script tests malformed `-g` rejection, then runs a fresh-config launcher
under Xvfb with Mesa software OpenGL for five seconds. It requests SDL's normal
quit via SIGTERM and requires exit 0 and startup/shutdown log markers. It fails on
early exit or shutdown timeout. This proves neither actual audio output nor
hardware acceleration, video decoding, VM execution, saves or game playability.
SDL's dummy video driver is unsuitable because it cannot provide OpenGL.

Viewer profiles are **not** asset-free: `characterviewer` inherits CHLCC and the
model viewers inherit RNE/DaSH. Real profile initialization needs legally obtained
data arranged according to [upstream setup](../doc/getting_started.md). Steam
STEINS;GATE still has no `sghd` profile; that investigation belongs to Thread 03.

## GitHub Actions

`.github/workflows/desktop.yml` builds on Ubuntu 24.04, on pushes to the desktop
branch or integration branches, pull requests, and manual dispatch. It runs the
same dependency installer, pinned configure/build, CTest discovery and smoke
script. `actions/cache` stores a vcpkg **files** binary cache keyed by platform,
vcpkg commit, manifests, overlay ports and triplets; a miss builds from source.
Compiler ABI hashes remain vcpkg's responsibility. No CoZ credentials or NuGet
feed is used. Build/test logs are uploaded even after failure.

The inherited `.github/workflows/impacto.yml` remains unchanged. It still depends
on the CoZ feed for its multi-platform jobs and is not this fork's desktop
baseline. Windows, macOS, Android and iOS are not verified by the new Linux job.
