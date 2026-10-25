"""Native iOS build configuration (Thread 08).

Pins the parts of the iOS build that can be checked without an Apple
toolchain: the vcpkg triplet, the iOS dependency manifest, the CMake preset,
the generated Info.plist and the CMake/CI wiring. Compiling and linking the
device binary is verified by .github/workflows/desktop-ios.yml on macos-15;
this module keeps the configuration itself from drifting.

No game data, Apple SDK or network access is needed.
"""

import json
import re
import unittest
import xml.etree.ElementTree as ElementTree
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TRIPLET = (REPO / "triplets/arm64-ios.cmake").read_text()
MANIFEST = json.loads((REPO / "vcpkg-ios.json").read_text())
VCPKG_MANIFEST = json.loads((REPO / "vcpkg.json").read_text())
PRESETS = json.loads((REPO / "CMakePresets.json").read_text())
CMAKE = (REPO / "CMakeLists.txt").read_text()
PLIST_TEMPLATE = (REPO / "ios/Info.plist.in").read_text()
WORKFLOW = (REPO / ".github/workflows/desktop-ios.yml").read_text()

IOS_DEPLOYMENT_TARGET = "15.0"


def triplet_value(name: str) -> str:
    match = re.search(rf"set\((?:{name})\s+([^)]+)\)", TRIPLET)
    return match.group(1).strip() if match else ""


def configured_plist() -> dict:
    """Apply the configure_file() substitutions CMakeLists.txt declares."""
    values = {
        "IMPACTO_IOS_BUNDLE_IDENTIFIER": "com.committeeofzero.impacto",
        "IMPACTO_IOS_VERSION": "0.10.8",
        "IMPACTO_IOS_BUILD_VERSION": "0.10.8",
        "IMPACTO_IOS_SUPPORTED_PLATFORM": "iPhoneOS",
        "IMPACTO_IOS_DEPLOYMENT_TARGET": IOS_DEPLOYMENT_TARGET,
    }
    text = PLIST_TEMPLATE
    for key, value in values.items():
        text = text.replace(f"@{key}@", value)
    return parse_plist(text)


def parse_plist(text: str) -> dict:
    """Minimal plist reader for the dict/array/string/true element types."""

    def convert(node):
        if node.tag == "dict":
            children = list(node)
            return {children[i].text: convert(children[i + 1])
                    for i in range(0, len(children), 2)}
        if node.tag == "array":
            return [convert(child) for child in node]
        if node.tag == "true":
            return True
        if node.tag == "false":
            return False
        return (node.text or "").strip()

    root = ElementTree.fromstring(text)
    return convert(root.find("dict"))


def preset(name: str, key: str) -> dict:
    return next(p for p in PRESETS[key] if p["name"] == name)


class IosTriplet(unittest.TestCase):
    def test_device_arm64_static(self):
        self.assertEqual(triplet_value("VCPKG_TARGET_ARCHITECTURE"), "arm64")
        self.assertEqual(triplet_value("VCPKG_LIBRARY_LINKAGE"), "static")
        self.assertEqual(triplet_value("VCPKG_CMAKE_SYSTEM_NAME"), "iOS")

    def test_pins_device_sdk_and_minimum_os(self):
        # vcpkg's community arm64-ios triplet sets neither, and without the
        # sysroot the ports can be built against the macOS SDK.
        self.assertEqual(triplet_value("VCPKG_OSX_SYSROOT"), "iphoneos")
        self.assertEqual(triplet_value("VCPKG_OSX_ARCHITECTURES"), "arm64")
        self.assertEqual(triplet_value("VCPKG_OSX_DEPLOYMENT_TARGET").strip('"'),
                         IOS_DEPLOYMENT_TARGET)


class IosManifest(unittest.TestCase):
    def test_same_pinned_baseline_as_desktop(self):
        self.assertEqual(MANIFEST["builtin-baseline"], VCPKG_MANIFEST["builtin-baseline"])

    def test_no_desktop_only_dependencies(self):
        names = {d if isinstance(d, str) else d["name"] for d in MANIFEST["dependencies"]}
        # ffmpeg/avcpp are disabled in CMake, libass needs glib/fontconfig,
        # OpenAL and Vulkan are iOS integration decisions, not build ones.
        for excluded in ("ffmpeg", "avcpp", "libass", "openal-soft", "vulkan"):
            self.assertNotIn(excluded, names)

    def test_engine_dependencies_present(self):
        names = {d if isinstance(d, str) else d["name"] for d in MANIFEST["dependencies"]}
        required = {
            "sdl3", "libogg", "libvorbis", "zlib", "libwebp", "fmt", "glm",
            "pugixml", "utfcpp", "concurrentqueue", "readerwriterqueue",
            "unordered-dense", "boost-circular-buffer", "toml11", "freetype",
            "harfbuzz",
        }
        self.assertEqual(required - names, set())

    def test_sdl3_override_matches_desktop(self):
        overrides = {o["name"]: o["version"] for o in MANIFEST["overrides"]}
        desktop = {o["name"]: o["version"] for o in VCPKG_MANIFEST["overrides"]}
        self.assertEqual(overrides["sdl3"], desktop["sdl3"])

    def test_sdl3_without_vulkan_feature(self):
        sdl3 = next(d for d in MANIFEST["dependencies"] if isinstance(d, dict))
        self.assertEqual(sdl3["name"], "sdl3")
        self.assertNotIn("features", sdl3)


class IosPreset(unittest.TestCase):
    def setUp(self):
        self.configure = preset("ci-release-ios", "configurePresets")
        self.build = preset("ci-release-ios", "buildPresets")

    def test_targets_the_device_sdk(self):
        variables = self.configure["cacheVariables"]
        self.assertEqual(variables["CMAKE_SYSTEM_NAME"], "iOS")
        self.assertEqual(variables["CMAKE_OSX_ARCHITECTURES"], "arm64")
        self.assertEqual(variables["CMAKE_OSX_SYSROOT"], "iphoneos")
        self.assertEqual(variables["CMAKE_OSX_DEPLOYMENT_TARGET"], IOS_DEPLOYMENT_TARGET)

    def test_uses_the_ios_triplet_and_manifest(self):
        variables = self.configure["cacheVariables"]
        self.assertEqual(variables["VCPKG_TARGET_TRIPLET"], "arm64-ios")
        self.assertEqual(variables["VCPKG_MANIFEST_FILE"], "${sourceDir}/vcpkg-ios.json")
        # the triplet overlay is inherited from ci-release
        self.assertIn("ci-release", self.configure["inherits"])
        self.assertIn("triplets", preset("ci-release", "configurePresets")
                      ["cacheVariables"]["VCPKG_OVERLAY_TRIPLETS"])

    def test_disables_features_the_first_ios_build_cannot_link(self):
        variables = self.configure["cacheVariables"]
        for feature in ("IMPACTO_DISABLE_FFMPEG", "IMPACTO_DISABLE_OPENAL",
                        "IMPACTO_DISABLE_LIBASS", "IMPACTO_DISABLE_VULKAN"):
            self.assertEqual(variables.get(feature), "ON", feature)

    def test_build_preset_installs_into_its_own_directory(self):
        self.assertEqual(self.build["configurePreset"], "ci-release-ios")
        self.assertEqual(self.build["targets"], ["install"])
        # binaryDir/installDir come from the inherited ci-release preset
        base = preset("ci-release", "configurePresets")
        self.assertEqual(base["binaryDir"], "ci-build/${presetName}")
        self.assertEqual(base["installDir"], "release/${presetName}")


class IosInfoPlist(unittest.TestCase):
    def setUp(self):
        self.plist = configured_plist()

    def value(self, key):
        self.assertIn(key, self.plist)
        return self.plist[key]

    def test_has_no_unsubstituted_variables(self):
        self.assertNotIn("@", json.dumps(self.plist))

    def test_bundle_identity(self):
        self.assertEqual(self.value("CFBundleExecutable"), "Impacto")
        self.assertEqual(self.value("CFBundleIdentifier"),
                         "com.committeeofzero.impacto")
        self.assertEqual(self.value("CFBundleSupportedPlatforms"), ["iPhoneOS"])
        self.assertEqual(self.value("MinimumOSVersion"), IOS_DEPLOYMENT_TARGET)

    def test_launch_screen_and_full_screen(self):
        # Without UILaunchScreen iOS renders in a compatibility letterbox.
        self.assertEqual(self.value("UILaunchScreen"), {})
        self.assertTrue(self.value("UIRequiresFullScreen"))

    def test_landscape_only(self):
        self.assertEqual(self.value("UISupportedInterfaceOrientations"),
                         ["UIInterfaceOrientationLandscapeLeft",
                          "UIInterfaceOrientationLandscapeRight"])

    def test_base_path_is_the_app_bundle(self):
        # src/main.cpp chdirs to SDL_GetBasePath(); the assets are copied to
        # the .app root, not to a Resources/ subdirectory.
        self.assertEqual(self.value("SDL_FILESYSTEM_BASE_DIR_TYPE"), "bundle")


class IosCMakeWiring(unittest.TestCase):
    def test_detects_ios_before_the_project_declaration(self):
        project = CMAKE.index('project("impacto"')
        detection = CMAKE.index('CMAKE_SYSTEM_NAME STREQUAL "iOS"')
        self.assertLess(detection, project)

    def test_keeps_a_macos_deployment_target_default(self):
        # An unconditional 11.0 would override the iOS preset's 15.0.
        self.assertIn("if(APPLE AND NOT CMAKE_OSX_DEPLOYMENT_TARGET)", CMAKE)

    def test_links_the_opengl_es_framework_instead_of_find_opengl(self):
        self.assertIn("find_library(OPENGLES_FRAMEWORK OpenGLES REQUIRED)", CMAKE)
        self.assertIn("if (NOT IMPACTO_IOS)\n        find_package(OpenGL", CMAKE)

    def test_generates_the_bundle_info_plist(self):
        self.assertIn('"${CMAKE_CURRENT_SOURCE_DIR}/ios/Info.plist.in"', CMAKE)
        self.assertIn('MACOSX_BUNDLE_INFO_PLIST "${PROJECT_BINARY_DIR}/ios/Info.plist"', CMAKE)

    def test_copies_engine_assets_to_the_bundle_root(self):
        block = CMAKE[CMAKE.index("if (IMPACTO_IOS)\n    # A UIKit app bundle"):]
        for asset in ("profiles", "src/shaders", "resources", "gamedefinitions.lua",
                      "basepaths.lua"):
            self.assertIn(asset, block)
        self.assertIn('"$<TARGET_FILE_DIR:impacto>"', block)

    def test_installs_assets_inside_the_bundle_only(self):
        self.assertIn("elseif(IMPACTO_IOS)\n    install(TARGETS impacto BUNDLE DESTINATION .)",
                      CMAKE)
        self.assertIn("if (NOT ANDROID AND NOT IMPACTO_IOS)", CMAKE)

    def test_ios_builds_without_audio_video_and_subtitles(self):
        block = CMAKE[CMAKE.index("if (IMPACTO_IOS)\n    # Everything links"):]
        for feature in ("IMPACTO_DISABLE_VULKAN", "IMPACTO_DISABLE_DX9",
                        "IMPACTO_DISABLE_FFMPEG", "IMPACTO_DISABLE_OPENAL",
                        "IMPACTO_DISABLE_LIBASS", "BUILD_SHARED_LIBS OFF"):
            self.assertIn(feature, block)


    def test_links_the_ios_frameworks_sdl_does_not_export(self):
        block = CMAKE[CMAKE.index("if (IMPACTO_IOS)\n    # SDL's static CMake package"):]
        for framework in ("Foundation", "UIKit", "AVFoundation", "AudioToolbox",
                          "GameController", "Metal", "OpenGLES"):
            self.assertIn(f'"-framework {framework}"', block)


class IosWorkflow(unittest.TestCase):
    def test_runs_on_an_apple_silicon_macos_runner(self):
        self.assertIn("runs-on: macos-15", WORKFLOW)

    def test_builds_the_install_target_with_the_ios_preset(self):
        self.assertIn("cmake --preset ci-release-ios", WORKFLOW)
        self.assertIn("cmake --build --preset ci-release-ios", WORKFLOW)

    def test_proves_the_binary_is_an_ios_arm64_build(self):
        self.assertIn("vtool -show-build", WORKFLOW)
        self.assertIn('grep -q "platform IOS"', WORKFLOW)
        self.assertIn("lipo -info", WORKFLOW)

    def test_uploads_an_unsigned_app_artifact(self):
        self.assertIn("ditto -c -k --sequesterRsrc --keepParent", WORKFLOW)
        self.assertIn("impacto-ios-arm64-unsigned-", WORKFLOW)
        self.assertIn("actions/upload-artifact@v7", WORKFLOW)

    def test_uses_no_repository_secrets(self):
        self.assertNotIn("secrets.", WORKFLOW)

    def test_signing_documentation_exists(self):
        self.assertTrue((REPO / "docs/ios-build.md").is_file())


if __name__ == "__main__":
    unittest.main()
