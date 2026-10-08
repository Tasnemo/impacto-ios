

root.LayerCount = 100;
root.GameFeatures = GameFeature.Sc3VirtualMachine | GameFeature.Renderer2D | GameFeature.Input | GameFeature.Audio | GameFeature.Video;
-- Steam assets are 1080p (full-screen masks BLOGMASK/TIPSMASK.DDS are
-- 1920x1080, LAY vertices are 1080p pixels); script coordinates stay 720p
-- and impacto scales them by DesignWidth/1280 (as for cclcc/mo8).
root.DesignWidth = 1920;
root.DesignHeight = 1080;

root.WindowName = "STEINS;GATE";
-- sghd: English Steam release (MAGES. 2016 PC port). Derived from profiles/sgps3,
-- which stays frozen for the PS3 build. See docs/steins-gate-compatibility.md.
-- No SG-specific icon/cursor resources yet (L3): reuse the engine icon and
-- the generic cursors already shipped in resources/.
root.WindowIconPath = "resources/common/icons/icon.png";
root.CursorArrowPath = "resources/chlcc/icondata/cursor_arrow.png";
root.CursorPointerPath = "resources/chlcc/icondata/cursor_pointer.png";

root.CharaIsMvl = false;
-- Steam LAY: little-endian, texture coordinates already in pixels, plus one
-- trailing byte per vertex that impacto ignores (Thread 06 census).
root.LayFileBigEndian = false;
root.LayFileTexXMultiplier = 1;
root.LayFileTexYMultiplier = 1;
-- system.mpk WAVTABLE.DAT (lip sync, loaded by 00 31) starts b0 38 00 00:
-- little-endian 14512 = the voice.mpk entry count (Thread 06 census).
root.VoiceTableLittleEndian = true;

include(root.BasePaths.RootProfilesDir .. '/sghd/vm.lua');

include(root.BasePaths.RootProfilesDir .. '/common/scriptinput.lua');
include(root.BasePaths.RootProfilesDir .. '/common/scriptvars.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/scriptvars.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/savedata.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/tipssystem.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/vfs.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/sprites.lua');
include(root.BasePaths.RootProfilesDir .. '/common/animation.lua');
include(root.BasePaths.RootProfilesDir .. '/common/achievementnotification.lua');
include(root.BasePaths.RootProfilesDir .. '/common/charset.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/charset.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/font.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/dialogue.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/hud/saveicon.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/hud/loadingdisplay.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/hud/datedisplay.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/hud/titlemenu.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/hud/backlogmenu.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/hud/sysmesboxdisplay.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/hud/selectiondisplay.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/hud/tipsmenu.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/hud/tipsnotification.lua');
