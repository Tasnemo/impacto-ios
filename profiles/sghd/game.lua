

root.LayerCount = 100;
root.GameFeatures = GameFeature.Sc3VirtualMachine | GameFeature.Renderer2D | GameFeature.Input | GameFeature.Audio | GameFeature.Video;
root.DesignWidth = 1280;
root.DesignHeight = 720;

root.WindowName = "STEINS;GATE";
-- sghd: English Steam release (MAGES. 2016 PC port). Derived from profiles/sgps3,
-- which stays frozen for the PS3 build. See docs/steins-gate-compatibility.md.
-- No SG-specific icon/cursor resources yet (L3): reuse the engine icon and
-- the generic cursors already shipped in resources/.
root.WindowIconPath = "resources/common/icons/icon.png";
root.CursorArrowPath = "resources/chlcc/icondata/cursor_arrow.png";
root.CursorPointerPath = "resources/chlcc/icondata/cursor_pointer.png";

root.CharaIsMvl = false;
root.LayFileBigEndian = true;
root.LayFileTexXMultiplier = 2048;
root.LayFileTexYMultiplier = 1024;

root.Vm = {
    StartScript = 2, -- placeholder until the Steam script.mpk listing is known (Task 5)
    StartScriptBuffer = 0,
    GameInstructionSet = InstructionSet.SGHD,
    -- SGHD Call/CallFar/CallIfFlag/CallFarIfFlag carry a u16 return-address id
    UseReturnIds = true,

    ScrWorkChaStructSize = 20,
    ScrWorkChaOffsetStructSize = 10,
    ScrWorkBgStructSize = 20,
    ScrWorkBgOffsetStructSize = 10,
};

include(root.BasePaths.RootProfilesDir .. '/common/scriptinput.lua');
include(root.BasePaths.RootProfilesDir .. '/common/scriptvars.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/scriptvars.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/savedata.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/tipssystem.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/vfs.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/sprites.lua');
include(root.BasePaths.RootProfilesDir .. '/common/animation.lua');
include(root.BasePaths.RootProfilesDir .. '/common/achievementnotification.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/charset.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/font.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/dialogue.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/hud/saveicon.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/hud/loadingdisplay.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/hud/datedisplay.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/hud/titlemenu.lua');
--include(root.BasePaths.RootProfilesDir .. '/sghd/hud/systemmenu.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/hud/backlogmenu.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/hud/sysmesboxdisplay.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/hud/selectiondisplay.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/hud/tipsmenu.lua');
include(root.BasePaths.RootProfilesDir .. '/sghd/hud/tipsnotification.lua');
