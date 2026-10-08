root.SystemMenu = {
    Type = SystemMenuType.RNE,
    DrawType = DrawComponentType.SystemMenu,
    Background = {
        DurationIn = 0.75,
        DurationOut = 1.0,
        Sprite = "SystemMenuBackground",
        Seed = 0,
        Rows = 7,
        Columns = 12,
        CenterY = 1.05,
        VanishingPointX = 0.99,
        Depth = 2,
        MaxAngle = 3.141592653 / 2  -- pi / 2
    },
    ButtonBackgroundSprite = "SystemMenuButtonBackground",
    SkyBackgroundSprite = "SystemMenuSkyBackground",
    SkyArrowSprite = "SystemMenuSkyArrow",
    SkyTextSprite = "SystemMenuSkyText",
    ButtonPromptsSprite = "SystemMenuButtonPrompts",
    SkyBackgroundBeginX = -120,
    SkyBackgroundY = 0,
    SkyTextBeginX = 430.5,
    SkyTextY = 103.5,
    ButtonBackgroundStartX = 1885.5,
    ButtonBackgroundX = 0,
    ButtonBackgroundY = 1021.5,
    ButtonBackgroundTargetWidth = 1414.5,
    ButtonBackgroundSprStartX = 2248.5,
    MenuEntriesSprites = {},
    MenuEntriesHighlightedSprites = {},
    MenuEntriesNum = 8,
    MenuEntriesHNum = 8,
    MenuEntriesX = 0,
    MenuEntriesXSkew = 30,
    MenuEntriesXOffset = 150,
    MenuEntriesFirstY = 330,
    MenuEntriesYPadding = 75,
    MenuEntriesTargetWidth = 625.5,
    SkyInStartProgress = 0.285,
    SkyOutStartProgress = 0.715,
    SkyMoveDurationIn = 0.415,
    SkyMoveDurationOut = 0.415,
    EntriesMoveDurationIn = 0.4,
    EntriesMoveDurationOut = 0.4,
    HighlightDurationIn = 0.15,
    HighlightDurationOut = 0.15,
};

for i = 0, 7 do
    root.Sprites["SystemMenuEntry" .. i] = {
        Sheet = "Data",
        Bounds = {
            X = 1446,
            Y = 444 + i * 38,
            Width = root.SystemMenu.MenuEntriesTargetWidth,
            Height = 39
        },
        BaseScale = { X = 1280 / 960, Y = 720 / 544 }
    };
    root.SystemMenu.MenuEntriesSprites[#root.SystemMenu.MenuEntriesSprites + 1] = "SystemMenuEntry" .. i;
end

for i = 0, 7 do
    root.Sprites["SystemMenuEntryHighlighted" .. i] = {
        Sheet = "Data",
        Bounds = {
            X = 1446,
            Y = 3 + i * 38,
            Width = root.SystemMenu.MenuEntriesTargetWidth,
            Height = 39
        },
        BaseScale = { X = 1280 / 960, Y = 720 / 544 }
    };
    root.SystemMenu.MenuEntriesHighlightedSprites[#root.SystemMenu.MenuEntriesHighlightedSprites + 1] = "SystemMenuEntryHighlighted" .. i;
end

root.Sprites["SystemMenuBackground"] = {
    Sheet = "Menu",
    Bounds = { X = 0, Y = 1632, Width = 2880, Height = 1620 },
};

root.Sprites["SystemMenuButtonBackground"] = {
    Sheet = "Menu",
    Bounds = { X = root.SystemMenu.ButtonBackgroundSprStartX, Y = 1462.5, Width = 0, Height = 45 },
    BaseScale = { X = 1280 / 960, Y = 720 / 544 }
};

root.Sprites["SystemMenuSkyBackground"] = {
    Sheet = "Data",
    Bounds = { X = 2074.5, Y = 801, Width = 627, Height = 135 },
    BaseScale = { X = 1280 / 960, Y = 720 / 544 }
};

root.Sprites["SystemMenuSkyArrow"] = {
    Sheet = "Data",
    Bounds = { X = 2703, Y = 801, Width = 105, Height = 135 },
    BaseScale = { X = 1280 / 960, Y = 720 / 544 }
};

root.Sprites["SystemMenuSkyText"] = {
    Sheet = "Data",
    Bounds = { X = 2812.5, Y = 880.5, Width = 178.5, Height = 45 },
    BaseScale = { X = 1280 / 960, Y = 720 / 544 }
};

root.Sprites["SystemMenuButtonPrompts"] = {
    Sheet = "Menu",
    Bounds = { X = 1846.5, Y = 792, Width = 600, Height = 31.5 },
    BaseScale = { X = 1280 / 960, Y = 720 / 544 }
};