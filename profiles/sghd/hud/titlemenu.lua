-- STEINS;GATE (Steam) has no engine-side title menu implementation yet
-- (TitleMenuType.None: nothing below is drawn). Thread 07 removed the
-- CHAOS;HEAD Love Chu Chu title sprites (heroine art, logos, delusion
-- prompts, menu entries) inherited through sgps3: none matches a region of
-- the Steam TITLE_CHIP.DDS (owner report). The loader still requires the
-- press-to-start members; the sprite is an empty placeholder, not artwork.
root.TitleMenu = {
    Type = TitleMenuType.None,
    DrawType = DrawComponentType.SystemMenu,
    MenuEntriesNum = 0,
    PressToStartPos = { X = 0, Y = 0 },
    PressToStartAnimDurationIn = 0.5,
    PressToStartAnimDurationOut = 0.5,
    PressToStartSprite = "TitleMenuPressToStart",
};

root.Sprites["TitleMenuPressToStart"] = {
    Sheet = "Title",
    Bounds = { X = 0, Y = 0, Width = 0, Height = 0 },
};
