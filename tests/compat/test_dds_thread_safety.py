"""Static regression guards for the DDS loader's per-image decoder state.

Profile::LoadSpritesheets uses std::async: multiple TextureLoadDDS calls can
execute simultaneously. These checks catch reintroduction of shared mutable
file metadata and loss of short-read failure propagation. They do not replace
a compiled concurrency test or owner-side Steam validation.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DDS = ROOT / "src/texture/ddsloader.cpp"
SPRITES = ROOT / "src/profile/sprites.cpp"


class DdsThreadSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code = DDS.read_text(encoding="utf-8-sig")

    def test_decoder_has_per_load_state(self):
        self.assertIn("struct DdsDecodeState {", self.code)
        self.assertRegex(
            self.code,
            r"bool TextureLoadDDS\([^)]*\) \{\s*DdsDecodeState state\{\};",
        )
        self.assertIn("const DdsDecodeState& state", self.code)
        for name in ("m_dds", "m_nchans", "m_Bpp", "m_redL", "m_greenR"):
            with self.subTest(name=name):
                self.assertNotRegex(self.code, rf"\b{name}\b")
        self.assertIn("state.dds.width", self.code)
        self.assertIn("state.dds.height", self.code)

    def test_compressed_reads_are_exact_and_failures_propagate(self):
        self.assertIn("stream->Read(tmp.data(), static_cast<int64_t>(tmp.size())) !=", self.code)
        self.assertIn("return internal_readimg(stream,", self.code)
        self.assertIn("state.dds.height, state.dds.depth, state)", self.code)

    def test_parallel_loads_remain_enabled(self):
        self.assertIn(
            "std::async(std::launch::async, LoadTexture",
            SPRITES.read_text(encoding="utf-8-sig"),
        )

    def test_zero_alpha_is_not_divided_by(self):
        self.assertIn("if (dst[k + 3] == 0)", self.code)


if __name__ == "__main__":
    unittest.main()
