# iOS device (arm64) triplet for impacto (Thread 08).
#
# Static linkage matches the other console/mobile triplets: an iOS app links
# one binary, so every vcpkg dependency has to be a static library. The
# overlay shadows vcpkg's community arm64-ios triplet to pin the SDK and the
# minimum iOS version instead of relying on the port defaults.
set(VCPKG_TARGET_ARCHITECTURE arm64)
set(VCPKG_CRT_LINKAGE dynamic)
set(VCPKG_LIBRARY_LINKAGE static)

set(VCPKG_CMAKE_SYSTEM_NAME iOS)
set(VCPKG_OSX_SYSROOT iphoneos)
set(VCPKG_OSX_ARCHITECTURES arm64)
set(VCPKG_OSX_DEPLOYMENT_TARGET "15.0")
set(VCPKG_BUILD_TYPE release)
