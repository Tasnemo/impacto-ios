"""Runtime probes: drive a real impacto binary with synthetic SGHD fixtures.

These probes reproduce the Thread 03 findings without any commercial game
data.  They are skipped unless ``IMPACTO_BIN`` points at a built ``impacto``
executable (run from its own directory so ``resources/`` resolves).

Environment the probes need:

* a display: a private ``Xvfb`` is started when ``DISPLAY`` is unset;
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
# 0.3 s 440 Hz mono Ogg Vorbis, generated with ffmpeg (no game audio)
SYNTHETIC_OGG = Path(__file__).resolve().parent / "fixtures" / "synthetic_tone.ogg"

# SYSTEM_US sprite sheet ids referenced by profiles/sgps3/sprites.lua
SYSTEM_SHEET_IDS = (6, 7, 8, 10, 19, 20, 21)
# system.mpk entries profiles/sghd/sprites.lua loads, with their Steam names
# (fixtures/sghd_steam_evidence.json); ScriptHandled sheets are not loaded
SGHD_SYSTEM_SHEETS = {2: "BACKLOG.DDS", 6: "DATA01.DDS", 9: "FONT.PNG",
                      30: "TITLE_CHIP.DDS"}
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


def tiny_dds(width: int = 64, height: int = 64) -> bytes:
    """DXT5 DDS (all-zero blocks), the format family src/texture/ddsloader.cpp reads."""
    header = bytearray(128)
    header[:4] = b"DDS "
    struct.pack_into("<7I", header, 4, 124, 0x1007, height, width, width * height, 0, 1)
    struct.pack_into("<II4s", header, 76, 32, 0x4, b"DXT5")
    struct.pack_into("<I", header, 108, 0x1000)  # DDSCAPS_TEXTURE (required by the loader)
    return bytes(header) + bytes(width * height)


def bink2_movie(frames: int = 1) -> bytes:
    """Smallest file FFmpeg's bink demuxer accepts as Bink 2 ('KB2j'): one
    64x64 video stream, no audio. FFmpeg reports its codec as "none" ("Bink 2
    video is not implemented"), exactly like the Steam .bk2 files."""
    header_len = 48 + 4 * frames
    frame = b"\0" * 16
    size = header_len + len(frame) * frames
    out = bytearray(b"KB2j")
    out += struct.pack("<IIII", size - 8, frames, len(frame), 0)
    out += struct.pack("<IIII", 64, 64, 30, 1)    # width, height, fps num/den
    out += struct.pack("<III", 0, 0, 0)           # flags, audio tracks, rev-j field
    for i in range(frames):                       # frame index, keyframe bit on #0
        out += struct.pack("<I", (header_len + i * len(frame)) | (1 if i == 0 else 0))
    out += frame * frames
    assert len(out) == size
    return bytes(out)


def movie_script(status: int) -> bytes:
    """PlayMovie (01 22: playMode 0, playView 0, playNo 0, cancel 0), then
    MovieMain type 0 (waits while SF_MOVIEPLAY is set), then exit status."""
    b = fx.ScxBuilder()
    b.add_label(fx.ins(0x01, 0x22, fx.u8(0), fx.u8(0), fx.expr(0), fx.expr(0))
                + fx.ins(0x01, 0x23, fx.u8(0))
                + fx.sghd_assign_scrwork(HARNESS_EXIT_CODE_SCRWORK, status)
                + fx.sghd_end_of_script())
    return b.build()


def audio_script(status: int) -> bytes:
    """PlayBgm (00 21 loop 0, track 1; track 0 equals the initial
    SW_BGMREQNO and is skipped by InstBGMplay), PlaySoundEffect (00 23
    channel 0, type 0, effect 0, loop 0), PlayVoice (00 37 channel 0, file 0,
    loop 0)."""
    E = fx.expr
    b = fx.ScxBuilder()
    b.add_label(fx.ins(0x00, 0x21, fx.u8(0), E(1))
                + fx.ins(0x00, 0x23, fx.u8(0), fx.u8(0), E(0), E(0))
                + fx.ins(0x00, 0x37, fx.u8(0), E(0), E(0))
                + fx.sghd_assign_scrwork(HARNESS_EXIT_CODE_SCRWORK, status)
                + fx.sghd_end_of_script())
    return b.build()


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
    # profiles/sghd-harness: asset-free, only the script archive
    "sghd-harness": {"SCRIPT": "script.mpk"},
    # sghd-harness plus a "movie" folder and Ogg audio archives (probe-only)
    "sghd-harness-media": {"SCRIPT": "script.mpk", "BGM": "bgm.mpk",
                           "SE": "se.mpk", "VOICE": "voice.mpk"},
}
GAMEDATA_DIR = {"sghd-harness": "sghd", "sghd-harness-media": "sghd"}
# games that run from the committed profiles/ and gamedefinitions.lua
UNPATCHED = ("sghd", "sghd-harness", "sghd-harness-media")


def wavtable(count_le: int = 2) -> bytes:
    """Synthetic Steam-style WAVTABLE.DAT: little-endian u16 count, u16 0,
    count x (u16 data index, u16 length*6), then 4 lip-sync bytes per index."""
    toc = b"".join(struct.pack("<HH", i, 6 * (i + 1)) for i in range(2))
    return struct.pack("<HH", count_le, 0) + toc + bytes(range(8))


def write_gamedata(root: Path, game: str = "sgps3",
                   script: bytes | None = None,
                   wavtable_data: bytes | None = None) -> None:
    gd = root / "gamedata" / GAMEDATA_DIR.get(game, game)
    gd.mkdir(parents=True)
    png = tiny_png()
    for mount, name in ARCHIVES[game].items():
        if mount == "SYSTEM_US" and game == "sghd":
            files = [fx.MpkFile(i, n, tiny_dds() if n.endswith(".DDS") else png)
                     for i, n in SGHD_SYSTEM_SHEETS.items()]
            files.append(fx.MpkFile(31, "WAVTABLE.DAT", wavtable_data or wavtable()))
        elif mount == "SYSTEM_US":
            files = [fx.MpkFile(i, f"sheet{i}.png", png) for i in SYSTEM_SHEET_IDS]
        elif game == "sghd-harness-media" and mount in ("BGM", "SE", "VOICE"):
            # Steam audio archives hold .ogg entries; a generated Vorbis tone
            files = [fx.MpkFile(i, f"{mount}00{i}.ogg", SYNTHETIC_OGG.read_bytes())
                     for i in (0, 1)]
        elif mount == "SCRIPT":
            files = [fx.MpkFile(2, "probe.scx", script or probe_script())]
        else:
            files = [fx.MpkFile(0, "empty.bin", b"\0" * 16)]
        (gd / name).write_bytes(fx.build_mpk(files))
    if game == "sghd-harness-media":
        (gd / "movie").mkdir()
        (gd / "movie" / "op.bk2").write_bytes(bink2_movie())


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


def write_config(root: Path, game: str = "sgps3",
                 saves: Path | None = None) -> None:
    """basepaths + game definitions.

    sgps3 is not registered upstream, so the probe writes its own definition
    and a patched profile copy.  sghd must work from the committed files
    unmodified: profiles/ and gamedefinitions.lua are used straight from the
    repository.
    """
    saves = saves or root / "saves"
    saves.mkdir(exist_ok=True)
    profiles = PROFILES if game in UNPATCHED else root / "profiles"
    (root / "basepaths.lua").write_text(f"""root.BasePaths = {{
  RootInstallDir = "./",
  RootGamedataDir = "{root}/gamedata",
  RootProfilesDir = "{profiles}",
  RootPatchesDir = "./patches",
  RootSavesDir = "{saves}",
}};
""")
    if game in UNPATCHED:
        shutil.copy(REPO / "gamedefinitions.lua", root / "gamedefs.lua")
        if game == "sghd-harness-media":
            (root / "harness-movie.lua").write_text(
                "include(root.BasePaths.RootProfilesDir .. '/sghd-harness/game.lua');\n"
                'for _, m in ipairs({"bgm", "se", "voice"}) do\n'
                '  root.Vfs.Mounts[m] = {root.BasePaths.RootGamedataDir .. "/sghd/" .. m .. ".mpk"};\n'
                'end\n'
                'root.Vfs.Mounts["movie"] = {root.BasePaths.RootGamedataDir .. "/sghd/movie"};\n')
            with (root / "gamedefs.lua").open("a") as f:
                f.write(f"""
root.GameDefinitions["sghd-harness-media"] = {{
  Hidden = true, Name = "sghd harness + media mounts", LauncherOrderId = 99,
  GameProfile = "{root}/harness-movie.lua",
}};
""")
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

_XVFB: subprocess.Popen | None = None
_XVFB_DISPLAY = ""


def shared_xvfb_display() -> str:
    """Start one Xvfb for all probes in this process.

    One server per test process instead of xvfb-run per engine run: xvfb-run
    sporadically failed its temp-dir cleanup and replaced the engine's exit
    status with its own (5), and on timeout only xvfb-run, not the engine,
    was killed."""
    global _XVFB, _XVFB_DISPLAY
    if _XVFB is None:
        import atexit
        r, w = os.pipe()
        _XVFB = subprocess.Popen(
            ["Xvfb", "-displayfd", str(w), "-screen", "0", "1280x1024x24",
             "-nolisten", "tcp"], pass_fds=(w,),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.close(w)
        with os.fdopen(r) as f:
            _XVFB_DISPLAY = ":" + f.readline().strip()
        atexit.register(_XVFB.terminate)
    return _XVFB_DISPLAY


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
              game: str = "sgps3", script: bytes | None = None,
              saves: Path | None = None,
              env_extra: dict | None = None,
              wavtable_data: bytes | None = None) -> ProbeResult:
    binary = Path(os.environ["IMPACTO_BIN"]).resolve()
    root = Path(tempfile.mkdtemp(prefix="impacto-probe-"))
    try:
        write_gamedata(root, game, script, wavtable_data)
        if game == "sgps3":
            write_profiles(root, use_return_ids)
        write_config(root, game, saves)
        log = root / "impacto.log"
        cmd = [str(binary), "-g", game,
               "-bp", str(root / "basepaths.lua"),
               "-gc", str(root / "gamedefs.lua"),
               "-uc", str(root / "user.toml"),
               "-ll", "Trace", "-lf", str(log)]
        env = dict(os.environ, ALSOFT_DRIVERS="null", LIBGL_ALWAYS_SOFTWARE="1")
        env.update(env_extra or {})
        if not env.get("DISPLAY"):
            env["DISPLAY"] = shared_xvfb_display()
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

    def test_steam_sheet_ids_load_as_png_and_dds(self):
        # sprites.lua points at the Steam system.mpk ids; DDS (DXT5) and PNG
        # sheets both decode, ScriptHandled sheets are never opened
        # (the fixture's other archives hold zero-filled dummies, so a later
        # non-sheet texture load logs "No loader"; only sheets matter here)
        self.assertNotIn("texture could not be imported", self.probe.log)
        self.assertNotIn("Could not open spritesheet", self.probe.log)
        self.assertNotIn("magic 0x44445320", self.probe.log)  # 'DDS ' rejected

    def test_vm_starts_without_profile_patches(self):
        self.assertIn("Initializing SC3 virtual machine", self.probe.log)
        self.assertNotIn("Expected member", self.probe.log)

    def test_plain_dialogue_box_configured(self):
        # Thread 06: the Steam profile uses the generic PlainDialogueBox
        # (ADVBox sprite + two-piece nametag); no per-game box is needed
        self.assertNotIn("Dialogue box is not implemented", self.probe.log)
        self.assertNotIn("defaulting to Void", self.probe.log)

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


HARNESS_EXIT_CODE_SCRWORK = 4000  # profiles/sghd-harness/game.lua


def exit_status_script(status: int) -> bytes:
    b = fx.ScxBuilder()
    b.add_label(fx.sghd_assign_scrwork(HARNESS_EXIT_CODE_SCRWORK, status)
                + fx.sghd_nop() + fx.sghd_end_of_script())
    return b.build()


@unittest.skipUnless(os.environ.get("IMPACTO_BIN"),
                     "set IMPACTO_BIN=/path/to/impacto to run runtime probes")
class SghdHarnessRuntimeProbe(unittest.TestCase):
    """Thread 04 Task 3: profiles/sghd-harness needs only script.mpk, runs
    the real VM and exits by itself with a script-controlled status."""

    @classmethod
    def setUpClass(cls):
        cls.blob = fx.sghd_task2_fixture()
        cls.task2 = run_probe(game="sghd-harness", script=cls.blob,
                              seconds=30.0)
        cls.status = run_probe(game="sghd-harness",
                               script=exit_status_script(7), seconds=30.0)

    def test_exits_by_itself_with_status_zero(self):
        self.assertEqual(self.task2.returncode, 0, self.task2.log[-2000:])
        self.assertIn("All script threads ended; exiting with status 0",
                      self.task2.log)

    def test_needs_no_sprites_fonts_or_other_archives(self):
        self.assertNotIn("spritesheet", self.task2.log.lower())
        self.assertNotIn("Expected member", self.task2.log)
        self.assertEqual(self.task2.log.count('" as MPK'), 1)

    def test_task2_fixture_trace_matches_reference(self):
        self.assertEqual(self.task2.vm_trace(), fx.sghd_reference_trace(self.blob))

    def test_exit_status_comes_from_scrwork(self):
        self.assertEqual(self.status.returncode, 7, self.status.log[-2000:])
        self.assertEqual([op for _, op in self.status.vm_trace()],
                         ["00:5f", "00:00"])


@unittest.skipUnless(os.environ.get("IMPACTO_BIN"),
                     "set IMPACTO_BIN=/path/to/impacto to run runtime probes")
class SghdMovieSkipProbe(unittest.TestCase):
    """Thread 05 (Task 8, M2): the Steam movies are Bink 2, which FFmpeg
    cannot decode. A movie that cannot be opened or decoded must be skipped:
    the script continues past MovieMain and the engine does not crash.
    Before the fix the Bink 2 case started playback without a video stream
    and the reader thread dereferenced it."""

    @classmethod
    def setUpClass(cls):
        cls.unmounted = run_probe(game="sghd-harness", script=movie_script(31),
                                  seconds=30.0)
        cls.bink2 = run_probe(game="sghd-harness-media", script=movie_script(32),
                              seconds=30.0)

    def test_unmounted_movie_is_skipped(self):
        self.assertEqual(self.unmounted.returncode, 31, self.unmounted.log[-2000:])
        self.assertIn("Failed to open movie for playback", self.unmounted.log)

    def test_bink2_movie_is_skipped_without_crash(self):
        self.assertEqual(self.bink2.returncode, 32,
                         self.bink2.stdout[-1500:] + self.bink2.log[-2500:])
        self.assertIn("as filesystem folder archive", self.bink2.log)
        self.assertIn("Unsupported codec: FFmpeg codec id 0", self.bink2.log)
        self.assertIn("No decodable video stream", self.bink2.log)
        self.assertIn("Movie 0 could not be played; skipping it", self.bink2.log)
        self.assertEqual([op for _, op in self.bink2.vm_trace()],
                         ["01:22", "01:23", "00:00"])


@unittest.skipUnless(os.environ.get("IMPACTO_BIN"),
                     "set IMPACTO_BIN=/path/to/impacto to run runtime probes")
class SghdOggAudioProbe(unittest.TestCase):
    """Thread 05 (Task 8, M3 groundwork): the Steam bgm/se/voice archives
    contain .ogg entries. BGM, SE and voice instructions decode Ogg Vorbis
    from MPK archives through impacto's Vorbis stream. Only proves the
    container/codec path with a synthetic tone; the real files' codec is
    confirmed by tools/sghd_census.py --assets."""

    @classmethod
    def setUpClass(cls):
        cls.audio = run_probe(game="sghd-harness-media", script=audio_script(33),
                            seconds=30.0)
        cls.no_device = run_probe(game="sghd-harness-media", script=audio_script(34),
                                  seconds=30.0, env_extra={"ALSOFT_DRIVERS": "no-such-driver"})

    def test_no_audio_device_continues_silently(self):
        # L4: an OpenAL driver list with no usable device (as on a machine
        # without sound hardware) used to segfault in Audio::AudioUpdate
        self.assertEqual(self.no_device.returncode, 34,
                         self.no_device.stdout[-1500:] + self.no_device.log[-2000:])
        self.assertIn("Could not create OpenAL device", self.no_device.log)
        self.assertIn("continuing without sound", self.no_device.log)

    def test_three_vorbis_streams_and_clean_exit(self):
        self.assertEqual(self.audio.returncode, 33, self.audio.log[-2500:])
        self.assertEqual(self.audio.log.count("Creating Vorbis stream"), 3, self.audio.log[-2500:])
        self.assertNotIn("No audio decoder found", self.audio.log)
        for name in ("bgm.mpk", "se.mpk", "voice.mpk"):
            self.assertIn(f'{name}" as MPK', self.audio.log)


def parse_sghd_save(blob: bytes) -> dict:
    """Parse the fork-native save file (docs/sghd-save-format.md)."""
    pos = 0

    def take(fmt):
        nonlocal pos
        vals = struct.unpack_from("<" + fmt, blob, pos)
        pos += struct.calcsize("<" + fmt)
        return vals if len(vals) > 1 else vals[0]

    out = {"magic": blob[:8]}
    pos = 8
    out["version"], out["full"], out["quick"] = take("III")
    out["flag_ranges"] = list(take("I" * take("I")) or ())
    out["scr_ranges"] = list(take("I" * take("I")) or ())
    out["read_lines"] = {}
    for _ in range(take("I")):
        script_id, n = take("II")
        out["read_lines"][script_id] = blob[pos:pos + n]
        pos += n
    pos += 48  # quick-save recency order
    if out["version"] >= 2:
        out["sys_flag_ranges"] = list(take("I" * take("I")) or ())
        out["sys_scr_ranges"] = list(take("I" * take("I")) or ())
        out["sys_present"] = take("B")
        n = take("I")
        out["sys_flags"] = blob[pos:pos + n]
        pos += n
        n = take("I")
        out["sys_scr"] = list(struct.unpack_from(f"<{n}i", blob, pos))
        pos += 4 * n
    entries = []
    for _ in range(out["full"] + out["quick"]):
        status = take("B")
        if not status:
            entries.append(None)
            continue
        e = {}
        e["play_time"], e["title"] = take("II")
        e["flags"] = take("B")
        e["save_type"] = take("I")
        e["date"] = take("6i")
        e["checkpoint"] = take("I")
        (e["exec_priority"], e["group"], e["wait"], e["script_param"],
         e["buffer"], e["ip"], e["loop_counter"], e["loop_label"],
         e["depth"]) = take("9I")
        e["returns"] = take("8I")
        e["return_buffers"] = take("8I")
        e["variables"] = take("16i")
        e["dialogue_page"] = take("I")
        n = take("I")
        e["flag_data"] = blob[pos:pos + n]
        pos += n
        n = take("I")
        e["scr_data"] = list(struct.unpack_from(f"<{n}i", blob, pos))
        pos += 4 * n
        if out["version"] >= 2:
            n = take("I")
            e["phone"] = blob[pos:pos + n]
            pos += n
        entries.append(e)
    assert pos == len(blob), (pos, len(blob))
    out["entries"] = entries
    return out


SW_SAVEFILENO_SGHD = 2123  # profiles/sghd/scriptvars.lua


@unittest.skipUnless(os.environ.get("IMPACTO_BIN"),
                     "set IMPACTO_BIN=/path/to/impacto to run runtime probes")
class SghdSaveRoundTripProbe(unittest.TestCase):
    """Thread 04 Task 4: run to a save point, save to full slot 79, quit;
    start a new process, load slot 79 and continue the main thread at the
    saved address with the saved call stack (fork-native format)."""

    @classmethod
    def setUpClass(cls):
        T = fx.SAVE_TEST
        cls.saves = Path(tempfile.mkdtemp(prefix="impacto-saves-"))
        save_blob, cls.resume = fx.sghd_save_test_script(False, SW_SAVEFILENO_SGHD)
        load_blob, resume2 = fx.sghd_save_test_script(True, SW_SAVEFILENO_SGHD)
        assert cls.resume == resume2 and len(save_blob) == len(load_blob)
        cls.save_run = run_probe(game="sghd-harness", script=save_blob,
                                 seconds=30.0, saves=cls.saves)
        save_file = cls.saves / "sghd" / "impacto-sghd.sav"
        cls.file = save_file.read_bytes() if save_file.exists() else b""
        cls.load_run = run_probe(game="sghd-harness", script=load_blob,
                                 seconds=30.0, saves=cls.saves)
        cls.call_end = (fx.scx_label_address(save_blob, 1)
                        + save_blob[fx.scx_label_address(save_blob, 1):]
                        .index(fx.sghd_call(4, 0)) + 6)
        # the Assign after the Call is not traced; the End that follows is
        cls.end_after_call = cls.call_end + len(
            fx.sghd_add_scrwork(T["exit_scr"], 100))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.saves, ignore_errors=True)

    def test_save_run_completes(self):
        self.assertEqual(self.save_run.returncode, 110, self.save_run.stdout[-2000:] + self.save_run.log[-1500:])

    def test_save_file_contents(self):
        T = fx.SAVE_TEST
        self.assertTrue(self.file, "save file was not written")
        s = parse_sghd_save(self.file)
        self.assertEqual((s["magic"], s["version"], s["full"], s["quick"]),
                         (b"IMPSGHD\0", 2, 80, 48))
        self.assertEqual(s["flag_ranges"], [50, 50, 300, 100])
        self.assertEqual(s["scr_ranges"], [300, 300, 2300, 1300])
        e = s["entries"][T["slot"]]
        self.assertIsNotNone(e, "full slot 79 empty")
        self.assertEqual(sum(x is not None for x in s["entries"][:80]), 1)
        self.assertEqual(e["ip"], self.resume)
        self.assertEqual((e["group"], e["buffer"], e["depth"]), (4, 0, 1))
        self.assertEqual(e["returns"][0] & 0xFFFF, 0, "return id 0")
        self.assertEqual(e["return_buffers"][0], 0)
        self.assertEqual(e["scr_data"][300 + T["saved_scr"] - 2300], T["saved_value"])
        self.assertEqual(len(e["scr_data"]), 1600)
        byte, bit = divmod(T["saved_flag"], 8)
        self.assertTrue(e["flag_data"][50 + byte - 300] & (1 << bit))
        self.assertEqual(s["read_lines"].get(T["script_id"], b"")[:1], b"\x01")
        self.assertEqual((s["sys_flag_ranges"], s["sys_scr_ranges"]),
                         ([100, 50, 460, 40], [600, 400]))
        self.assertEqual(s["sys_present"], 1)
        byte, bit = divmod(T["system_flag"], 8)
        self.assertTrue(s["sys_flags"][50 + byte - 460] & (1 << bit))
        self.assertEqual(s["sys_scr"][T["system_scr"] - 600], T["saved_value"])
        self.assertEqual(len(e["phone"]), 1024)
        self.assertEqual(e["phone"][T["phone_item"]], 1 << T["phone_bit"])
        self.assertEqual(sum(e["phone"]), 1 << T["phone_bit"])

    def test_load_run_restores_state_and_call_stack(self):
        # 42 = all three checks passed in the restored subroutine,
        # +100 = the restored Return reached the instruction after the Call
        self.assertEqual(self.load_run.returncode, 142, self.load_run.log[-3000:])

    def test_load_run_resumes_at_saved_address(self):
        addrs = [a for a, _ in self.load_run.vm_trace()]
        self.assertIn(self.resume, addrs)
        after = addrs[addrs.index(self.resume):]
        self.assertEqual(after[-1], self.end_after_call,
                         "restored Return continues right after the Call")


def voice_table_script() -> bytes:
    """00 31 (voice/lip-sync table load) of system id 31, Nop, End."""
    b = fx.ScxBuilder()
    b.add_label(fx.ins(0x00, 0x31, fx.expr(31)) + fx.sghd_nop()
                + fx.sghd_end_of_script())
    return b.build()


@unittest.skipUnless(os.environ.get("IMPACTO_BIN"),
                     "set IMPACTO_BIN=/path/to/impacto to run runtime probes")
class SghdVoiceTableProbe(unittest.TestCase):
    """Thread 06: Steam WAVTABLE.DAT is little-endian (census: b0 38 00 00 =
    14512 = voice.mpk entries). The sghd profile reads it as such; a table
    whose count does not fit is refused instead of crashing."""

    @classmethod
    def setUpClass(cls):
        cls.good = run_probe(game="sghd", script=voice_table_script())
        # what the Steam file looks like to a big-endian reader: 0xb038 entries
        cls.bad = run_probe(game="sghd", script=voice_table_script(),
                            wavtable_data=struct.pack(">H", 0xB038) + bytes(14))

    @staticmethod
    def ops(probe):
        # 00 31 re-executes while the table loads asynchronously
        ops = [op for _, op in probe.vm_trace()]
        return [op for i, op in enumerate(ops) if i == 0 or op != ops[i - 1]]

    def test_little_endian_table_loads(self):
        ops = self.ops(self.good)
        self.assertEqual(ops[:3], ["00:31", "00:5f", "00:00"], self.good.log[-2000:])
        self.assertNotIn("Voice table", self.good.log)

    def test_oversized_count_is_refused_not_fatal(self):
        self.assertIn("lip sync disabled", self.bad.log)
        ops = self.ops(self.bad)
        self.assertEqual(ops[:3], ["00:31", "00:5f", "00:00"], self.bad.log[-2000:])


@unittest.skipUnless(os.environ.get("IMPACTO_BIN"),
                     "set IMPACTO_BIN=/path/to/impacto to run runtime probes")
class SghdPhoneProbe(unittest.TestCase):
    """Thread 06: phone item bits set/clear/branch (10 37 types 0x00-0x03),
    10 3A as one expression and 10 37 type 0x1E without arguments."""

    @classmethod
    def setUpClass(cls):
        cls.probe = run_probe(game="sghd-harness",
                            script=fx.sghd_phone_test_script(), seconds=30.0)

    def test_branches(self):
        self.assertEqual(self.probe.returncode, 42,
                         self.probe.stdout[-1500:] + self.probe.log[-2500:])

    def test_no_desync_or_unknown_subtype(self):
        self.assertNotIn("unknown SGHD subtype", self.probe.log)
        self.assertNotIn("is not part of the SGHD instruction set", self.probe.log)
        self.assertIn("STUB instruction Unk103A(args: 63, 64, 65, 66, 67, 128)",
                      self.probe.log)


def main(argv: list[str]) -> int:
    if not os.environ.get("IMPACTO_BIN"):
        print("IMPACTO_BIN not set; nothing to do", file=sys.stderr)
        return 2
    if argv:
        # run an SCX file through the asset-free harness
        r = run_probe(game="sghd-harness", script=Path(argv[0]).read_bytes(),
                      seconds=float(argv[1]) if len(argv) > 1 else 30.0)
        trace = r.vm_trace()
        print(f"== sghd-harness {argv[0]}: exit={r.returncode}, {len(trace)} VM steps")
        for addr, op in trace[-20:]:
            print(f"   0x{addr:02x} {op}")
        for line in r.log.splitlines():
            if line.startswith(("ERROR", "CRITICAL", "WARN")):
                print("  ", line)
        return 0
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
    sys.exit(main(sys.argv[1:]))
