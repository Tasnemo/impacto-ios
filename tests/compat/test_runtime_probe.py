"""Runtime probes: drive a real impacto binary with synthetic SGHD fixtures.

These probes reproduce the Thread 03 findings without any commercial game
data.  They are skipped unless ``IMPACTO_BIN`` points at a built ``impacto``
executable (run from its own directory so ``resources/`` resolves).

Environment the probes need:

* a display: ``xvfb-run`` is used automatically when present;
* an audio backend that never fails: ``ALSOFT_DRIVERS=null`` is exported
  because impacto segfaults in ``Audio::AudioUpdate`` when OpenAL has no
  device (observed under gdb, see docs/steins-gate-compatibility.md);
* software GL is fine (``LIBGL_ALWAYS_SOFTWARE=1`` is exported).

Each probe builds a throwaway tree::

    <tmp>/gamedata/sgps3/*.CPK   MPK v2.0 archives (sc3fixtures.build_mpk)
    <tmp>/profiles/              copy of profiles/ with minimal patches
    <tmp>/gamedefs.lua           registers ``sgps3`` (stock file lacks it)
    <tmp>/basepaths.lua          points impacto at the tree above

and runs ``impacto -g sgps3`` for a few seconds with Trace logging, then
inspects the log.  Expected outcomes (all verified against the Thread 02
ubuntu24 build on 2026-10-08):

* ``UseReturnIds = false`` (stock sgps3 profile): after ``Call`` the
  ``Return`` lands on the 2-byte return id and executes opcode 00:00
  (``End``) instead of the ``Nop`` that follows the call;
* ``UseReturnIds = true``: control flow is right but the ``Nop`` (00:5F,
  an ``InstDummy`` slot in the sgps3 table) never advances the IP, so the
  VM spins on the same address until the timeout.

Run directly for a human-readable report::

    IMPACTO_BIN=/path/to/impacto python3 tests/compat/test_runtime_probe.py
"""

from __future__ import annotations

import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sc3fixtures as fx  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
PROFILES = REPO / "profiles"

# SYSTEM_US sprite sheet ids referenced by profiles/sgps3/sprites.lua
SYSTEM_SHEET_IDS = (6, 7, 8, 10, 19, 20, 21)
MOUNTS = ("SCRIPT", "SYSTEM_US", "BGM", "SE", "VOICE", "BG", "CHARA",
          "MASK", "MOVIE")


# --------------------------------------------------------------------------
# fixture tree
# --------------------------------------------------------------------------

def tiny_png(width: int = 64, height: int = 64) -> bytes:
    """Opaque magenta RGBA PNG, written by hand so no imaging library is needed."""
    def chunk(tag: bytes, body: bytes) -> bytes:
        return (struct.pack(">I", len(body)) + tag + body
                + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF))

    row = b"\x00" + b"\xff\x00\xff\xff" * width
    raw = row * height
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b""))


def probe_script() -> bytes:
    """Label 0: Assign; SetFlag; Call label1 (ret 0); Nop; End.  Label 1: Assign; Return."""
    b = fx.ScxBuilder()
    main = (fx.sghd_assign(1)
            + fx.sghd_set_flag(1770)
            + fx.sghd_call(1, 0)
            + fx.sghd_nop()
            + fx.sghd_end_of_script())
    sub = fx.sghd_assign(2) + fx.sghd_return()
    b.add_label(main)
    b.add_label(sub)
    # return id 0 -> label 0, byte offset of the Nop (right after the Call)
    call_end = len(fx.sghd_assign(1) + fx.sghd_set_flag(1770) + fx.sghd_call(1, 0))
    b.add_return(0, call_end)
    return b.build()


# Archive file names per game id (profiles/<game>/vfs.lua)
ARCHIVES = {
    "sgps3": {m: f"{m}.CPK" for m in MOUNTS},
    "sghd": {"SCRIPT": "script.mpk", "SYSTEM_US": "system.mpk",
             "BGM": "bgm.mpk", "SE": "se.mpk", "VOICE": "voice.mpk",
             "BG": "bg.mpk", "CHARA": "chara.mpk", "MASK": "mask.mpk"},
}


def write_gamedata(root: Path, game: str = "sgps3",
                   script: bytes | None = None) -> None:
    gd = root / "gamedata" / game
    gd.mkdir(parents=True)
    png = tiny_png()
    for mount, name in ARCHIVES[game].items():
        if mount == "SYSTEM_US":
            files = [fx.MpkFile(i, f"sheet{i}.png", png) for i in SYSTEM_SHEET_IDS]
        elif mount == "SCRIPT":
            files = [fx.MpkFile(2, "probe.scx", script or probe_script())]
        else:
            files = [fx.MpkFile(0, "empty.bin", b"\0" * 16)]
        (gd / name).write_bytes(fx.build_mpk(files))


def write_profiles(root: Path, use_return_ids: bool) -> None:
    """Copy profiles/ and apply the minimal patches needed to reach the VM.

    The stock sgps3 profile predates members that the current CHLCC-type
    HUD code requires (LoadingStar*, DelusionADVPosition ...); without the
    patches impacto aborts with "Expected member ..." before the VM runs.
    """
    dst = root / "profiles"
    shutil.copytree(PROFILES, dst)
    game = dst / "sgps3" / "game.lua"
    text = game.read_text()
    assert "UseReturnIds = false" in text, "sgps3 profile changed; update probe"
    text = text.replace("UseReturnIds = false",
                        f"UseReturnIds = {'true' if use_return_ids else 'false'}")
    game.write_text(text)

    sysmes = dst / "sgps3" / "hud" / "sysmesboxdisplay.lua"
    sysmes.write_text(sysmes.read_text() + """
-- test_runtime_probe patch: members required by src/profile/games/chlcc/sysmesbox.cpp
root.Sprites[name .. "LoadingStar"] = { Sheet = sheet, Bounds = { X = 0, Y = 0, Width = 8, Height = 8 } };
root.SysMesBoxDisplay.LoadingStar = name .. "LoadingStar";
root.SysMesBoxDisplay.LoadingStarsPosition = { X = 580, Y = 357 };
root.SysMesBoxDisplay.LoadingStarsFadeDuration = 0.533;
""")

    title = dst / "sgps3" / "hud" / "titlemenu.lua"
    ttext = title.read_text()
    assert "Type = TitleMenuType.CHLCC" in ttext, "sgps3 titlemenu changed; update probe"
    title.write_text(ttext.replace("Type = TitleMenuType.CHLCC",
                                   "Type = TitleMenuType.None"))


def write_config(root: Path, game: str = "sgps3") -> None:
    """basepaths + game definitions.

    sgps3 is not registered upstream, so the probe writes its own definition
    and a patched profile copy.  sghd must work from the committed files
    unmodified: profiles/ and gamedefinitions.lua are used straight from the
    repository.
    """
    (root / "saves").mkdir()
    profiles = PROFILES if game == "sghd" else root / "profiles"
    (root / "basepaths.lua").write_text(f"""root.BasePaths = {{
  RootInstallDir = "./",
  RootGamedataDir = "{root}/gamedata",
  RootProfilesDir = "{profiles}",
  RootPatchesDir = "./patches",
  RootSavesDir = "{root}/saves",
}};
""")
    if game == "sghd":
        shutil.copy(REPO / "gamedefinitions.lua", root / "gamedefs.lua")
        return
    (root / "gamedefs.lua").write_text("""root.GameDefinitions = {
  sgps3 = {
    Name = "STEINS;GATE (sgps3 runtime probe)",
    LauncherOrderId = 0,
    GameProfile = root.BasePaths.RootProfilesDir .. "/sgps3/game.lua",
  },
};
""")


# --------------------------------------------------------------------------
# running impacto
# --------------------------------------------------------------------------

class ProbeResult:
    def __init__(self, returncode: int, log: str, stdout: str):
        self.returncode = returncode
        self.log = log
        self.stdout = stdout

    def vm_trace(self) -> list[tuple[int, str]]:
        """(address, 'gg:oo') for every executed instruction, in order."""
        return [(int(a, 16), op) for a, op in
                re.findall(r"Address: (0x[0-9a-f]+) Opcode: ([0-9a-f]{2}:[0-9a-f]{2})",
                           self.log)]


def run_probe(use_return_ids: bool = False, seconds: float = 4.0,
              game: str = "sgps3", script: bytes | None = None) -> ProbeResult:
    binary = Path(os.environ["IMPACTO_BIN"]).resolve()
    root = Path(tempfile.mkdtemp(prefix="impacto-probe-"))
    try:
        write_gamedata(root, game, script)
        if game == "sgps3":
            write_profiles(root, use_return_ids)
        write_config(root, game)
        log = root / "impacto.log"
        cmd = [str(binary), "-g", game,
               "-bp", str(root / "basepaths.lua"),
               "-gc", str(root / "gamedefs.lua"),
               "-uc", str(root / "user.toml"),
               "-ll", "Trace", "-lf", str(log)]
        if shutil.which("xvfb-run") and not os.environ.get("DISPLAY"):
            cmd = ["xvfb-run", "-a"] + cmd
        env = dict(os.environ, ALSOFT_DRIVERS="null", LIBGL_ALWAYS_SOFTWARE="1")
        env.setdefault("SDL_VIDEO_DRIVER", "x11")
        try:
            proc = subprocess.run(cmd, cwd=binary.parent, env=env,
                                  capture_output=True, text=True,
                                  timeout=seconds)
            rc, out = proc.returncode, proc.stdout + proc.stderr
        except subprocess.TimeoutExpired as e:
            rc, out = 124, (e.stdout or b"").decode(errors="replace")
        return ProbeResult(rc, log.read_text(errors="replace") if log.exists() else "", out)
    finally:
        shutil.rmtree(root, ignore_errors=True)


# --------------------------------------------------------------------------
# tests
# --------------------------------------------------------------------------

@unittest.skipUnless(os.environ.get("IMPACTO_BIN"),
                     "set IMPACTO_BIN=/path/to/impacto to run runtime probes")
class SgPs3RuntimeProbe(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock = run_probe(use_return_ids=False)
        cls.retids = run_probe(use_return_ids=True)

    def test_all_nine_mounts_are_tried_as_mpk(self):
        for mount in MOUNTS:
            self.assertIn(f'{mount}.CPK" as MPK', self.stock.log, mount)
        self.assertNotIn("Could not open spritesheet", self.stock.log)

    def test_vm_starts_with_stock_profile_once_hud_members_are_patched(self):
        self.assertIn("Initializing SC3 virtual machine", self.stock.log)
        self.assertNotIn("Expected member", self.stock.log)

    def test_stock_profile_return_lands_on_return_id_bytes(self):
        # The VM only logs non-0xFE opcodes, so Assign (FE ..) is invisible and
        # the trace is SetFlag(00:12) Call(00:0b) Return(00:0e) ...
        # impacto's Call without UseReturnIds is 2 bytes shorter than the SGHD
        # encoding (no return id), so the saved return address points at the
        # return-id bytes "00 00" == End.  The Nop (00:5f) never runs.
        trace = self.stock.vm_trace()
        ops = [op for _, op in trace]
        self.assertEqual(ops[:3], ["00:12", "00:0b", "00:0e"], trace[:4])
        self.assertEqual(ops[3], "00:00", trace[:4])
        self.assertEqual(trace[3][0], trace[1][0] + 4, "End executed at Call+4 (the return id)")
        self.assertNotIn("00:5f", ops)

    def test_return_ids_true_then_dummy_nop_spins_forever(self):
        trace = self.retids.vm_trace()
        ops = [op for _, op in trace]
        self.assertEqual(ops[:3], ["00:12", "00:0b", "00:0e"], trace[:4])
        self.assertEqual(trace[3][0], trace[1][0] + 6, "Return resumes right after the Call")
        spins = [a for a, op in trace if op == "00:5f"]
        self.assertGreater(len(spins), 1000, "InstDummy should re-execute every VM tick")
        self.assertEqual(len(set(spins)), 1, "IP never advances past the Dummy slot")
        self.assertEqual(self.retids.returncode, 124, "engine must be killed by the timeout")


@unittest.skipUnless(os.environ.get("IMPACTO_BIN"),
                     "set IMPACTO_BIN=/path/to/impacto to run runtime probes")
class SghdRuntimeProbe(unittest.TestCase):
    """The committed sghd profile, unpatched, against the same fixture."""

    @classmethod
    def setUpClass(cls):
        cls.probe = run_probe(game="sghd")

    def test_all_archives_are_mounted_as_mpk(self):
        for name in ARCHIVES["sghd"].values():
            self.assertIn(f'{name}" as MPK', self.probe.log, name)
        self.assertNotIn("Could not open spritesheet", self.probe.log)

    def test_vm_starts_without_profile_patches(self):
        self.assertIn("Initializing SC3 virtual machine", self.probe.log)
        self.assertNotIn("Expected member", self.probe.log)

    def test_return_resumes_right_after_call(self):
        trace = self.probe.vm_trace()
        ops = [op for _, op in trace]
        self.assertEqual(ops[:3], ["00:12", "00:0b", "00:0e"], trace[:4])
        self.assertEqual(trace[3][0], trace[1][0] + 6,
                         "Return resumes at Call+6 (UseReturnIds = true)")
        # Task 2: the SGHD Nop advances, then End stops the thread (the
        # sgps3 table's InstDummy spun on 00:5f forever).
        self.assertEqual(ops[3:], ["00:5f", "00:00"], trace)


@unittest.skipUnless(os.environ.get("IMPACTO_BIN"),
                     "set IMPACTO_BIN=/path/to/impacto to run runtime probes")
class SghdTask2RuntimeProbe(unittest.TestCase):
    """All 37 previously broken opcodes through the real VM (sghd profile).

    impacto's executed addresses must equal the reference SGHD trace
    instruction by instruction: any byte-consumption error shifts every
    later address."""

    @classmethod
    def setUpClass(cls):
        cls.blob = fx.sghd_task2_fixture()
        cls.probe = run_probe(game="sghd", script=cls.blob, seconds=6.0)

    def test_vm_trace_matches_reference_trace(self):
        expected = fx.sghd_reference_trace(self.blob)
        self.assertEqual(self.probe.vm_trace(), expected)

    def test_no_crash_recovery_or_unknown_opcode(self):
        for needle in ("Thread CRASH", "not part of the SGHD instruction set",
                       "unknown SGHD", "Expected member", "call stack"):
            self.assertNotIn(needle, self.probe.log, needle)

    def test_stub_instructions_are_reported(self):
        # unverified semantics are logged, not silently ignored
        for needle in ("STUB instruction Phone(type: 0x14)",
                       "STUB instruction Checkpoint(type: 0)",
                       "STUB instruction SystemMes(mode: 0xc)"):
            self.assertIn(needle, self.probe.log, needle)


def main() -> int:
    if not os.environ.get("IMPACTO_BIN"):
        print("IMPACTO_BIN not set; nothing to do", file=sys.stderr)
        return 2
    for label, flag in (("UseReturnIds=false", False), ("UseReturnIds=true", True)):
        r = run_probe(flag)
        trace = r.vm_trace()
        print(f"== {label}: exit={r.returncode}, {len(trace)} VM steps")
        for addr, op in trace[:8]:
            print(f"   0x{addr:02x} {op}")
        if len(trace) > 8:
            last = trace[-1]
            print(f"   ... last: 0x{last[0]:02x} {last[1]} (repeated "
                  f"{sum(1 for a, _ in trace if a == last[0])}x)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
