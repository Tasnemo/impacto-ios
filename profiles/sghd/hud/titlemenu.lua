root.TitleMenu = {
    -- No SG title menu implementation exists yet; the CHLCC one needs members
    -- (DelusionADVPosition ...) that do not apply to STEINS;GATE.
    Type = TitleMenuType.None,
    DrawType = DrawComponentType.SystemMenu,
    PressToStartPos = { X = 108, Y = 892.5 },
    PressToStartAnimDurationIn = 0.5,
    PressToStartAnimDurationOut = 0.5,
    PressToStartSprite = "TitleMenuPressToStart",
    IntroBackgroundSprite = "TitleMenuIntroBackground",
    BackgroundSprite = "TitleMenuBackground",
    DelusionADVUnderSprite = "DelusionADVUnder", -- "DelusionADVUnderEnglish" with the TLed assets, "DelusionADVUnder" with the original ones
    DelusionADVUnderX = 117, --74 with the TLed assets, 78 with the original ones
    DelusionADVUnderY = 591, --396 with the TLed assets, 394 with the original ones
    DelusionADVSprite = "DelusionADV", -- "DelusionADVEnglish" with the TLed assets, "DelusionADV" with the original ones
    DelusionADVX = 78, --74 with the TLed assets, 78 with the original ones
    DelusionADVY = 394, --396 with the TLed assets, 394 with the original ones
    SeiraUnderSprite = "SeiraUnder",
    SeiraUnderX = 1099.5,
    SeiraUnderY = 0,
    SeiraSprite = "Seira",
    SeiraX = 1092,
    SeiraY = -70.5,
    CHLogoSprite = "CHLogo",
    CHLogoX = 91.5,
    CHLogoY = 418.5,
    LCCLogoUnderSprite = "LCCLogoUnder",
    LCCLogoUnderX = 361.5,
    LCCLogoUnderY = 490.5,
    ChuLeftLogoSprite = "ChuLeftLogo",
    ChuLeftLogoX = 529.5,
    ChuLeftLogoY = 504,
    ChuRightLogoSprite = "ChuRightLogo",
    ChuRightLogoX = 750,
    ChuRightLogoY = 474,
    LoveLogoSprite = "LoveLogo",
    LoveLogoX = 352.5, --231 with the TLed assets, 235 with the original ones
    LoveLogoY = 504, --335 with the TLed assets, 336 with the original ones
    StarLogoSprite = "StarLogo",
    StarLogoX = 697.5,
    StarLogoY = 474,
    ExclMarkLogoSprite = "ExclMarkLogo",
    ExclMarkLogoX = 921,
    ExclMarkLogoY = 474,
    CopyrightTextSprite = "CopyrightText",
    CopyrightTextX = 108,
    CopyrightTextY = 1012.5,
    SpinningCircleSprite = "SpinningCircle",
    SpinningCircleX = 915.75,
    SpinningCircleY = -428.25,
    SpinningCircleAnimationDuration = 15,
    ItemHighlightSprite = "TitleMenuItemHighlight",
    ItemHighlightOffsetX = 109.5,
    ItemHighlightOffsetY = 10.5,
    ItemPadding = 60,
    ItemYBase = 103.5,
    ItemFadeInDuration = 0.3,
    ItemFadeOutDuration = 0.6,
    SecondaryItemFadeInDuration = 0.2,
    SecondaryItemFadeOutDuration = 0.2,
    PrimaryFadeInDuration = 0.3,
    PrimaryFadeOutDuration = 0.3,
    SecondaryFadeInDuration = 0.512,
    SecondaryFadeOutDuration = 0.512,
    ItemHyperUpLine = "TitleMenuItemHyperUpLine",
    ItemSuperUpLine = "TitleMenuItemSuperUpLine",
    ItemUpLine = "TitleMenuItemUpLine",
    ItemStraightLine = "TitleMenuItemStraightLine",
    ItemDownLine = "TitleMenuItemDownLine",
    ItemSuperDownLine = "TitleMenuItemSuperDownLine",
    ItemLoadQuickSprite = "TitleMenuItemLoadQuick",
    SecondaryItemX = 480,
    ItemLoadY = 163.5,
    ItemLoadQuickY = 124.5,
    ItemLoadSprite = "TitleMenuItemLoad",
    ItemLoadQuickHighlightedSprite = "TitleMenuItemLoadQuickHighlighted",
    ItemLoadHighlightedSprite = "TitleMenuItemLoadHighlighted",
    SecondaryItemHighlightSprite = "TitleMenuSecondaryItemHighlight",
    ItemClearListY = 106.5,
    ItemCGLibraryY = 145.5,
    ItemSoundLibraryY = 184.5,
    ItemMovieLibraryY = 223.5,
    ItemTipsY = 262.5,
    ItemTrophyY = 301.5,
    ItemConfigY = 244.5,
    ItemSystemSaveY = 283.5,
    SecondaryItemHighlightX = 429,
    SecondaryMenuPaddingY = 39,
    SecondaryMenuLoadOffsetY = 114,
    SecondaryMenuLineX = 361.5,
    SecondaryMenuLoadLineY = 139.5,
    SecondaryMenuLoadQuickLineY = 178.5,
    SecondaryMenuExtraClearY = 121.5,
    SecondaryMenuExtraCGY = 107,
    SecondaryMenuExtraSoundY = 199.5,
    SecondaryMenuExtraMovieY = 238.5,
    SecondaryMenuExtraTipsY = 238.5,
    SecondaryMenuExtraTrophyY = 238.5,
    SecondaryMenuSystemConfigY = 259.5,
    SecondaryMenuSystemSaveY = 298.5,
    MenuEntriesNum = 14,
    MenuEntriesSprites = {},
    MenuEntriesHighlightedSprites = {},
    LineNum = 6,
    LineEntriesSprites = {}
};

for i = 0, 3 do
    root.Sprites["TitleMenuEntry" .. i] = {
        Sheet = "Title",
        Bounds = {
            X = 1726.5,
            Y = 151.5 + i * 25,
            Width = 282,
            Height = 34.5
        }
    };
    root.TitleMenu.MenuEntriesSprites[#root.TitleMenu.MenuEntriesSprites + 1] = "TitleMenuEntry" .. i;
end

for i = 0, 9 do
    root.Sprites["TitleMenuEntry" .. (i + 4)] = {
        Sheet = "Title",
        Bounds = {
            X = 2053.5,
            Y = 1026 + i * 22,
            Width = 324,
            Height = 30
        }
    };
    root.TitleMenu.MenuEntriesSprites[#root.TitleMenu.MenuEntriesSprites + 1] = "TitleMenuEntry" .. (i + 4);
end

for i = 0, 3 do
    root.Sprites["TitleMenuEntryHighlighted" .. i] = {
        Sheet = "Title",
        Bounds = {
            X = 1726.5,
            Y = 1.5 + i * 25,
            Width = 282,
            Height = 34.5
        }
    };
    root.TitleMenu.MenuEntriesHighlightedSprites[#root.TitleMenu.MenuEntriesHighlightedSprites + 1] = "TitleMenuEntryHighlighted" .. i;
end

for i = 0, 9 do
    root.Sprites["TitleMenuEntryHighlighted" .. (i + 4)] = {
        Sheet = "Title",
        Bounds = {
            X = 1726.5,
            Y = 1026 + i * 22,
            Width = 324,
            Height = 30
        }
    };
    root.TitleMenu.MenuEntriesHighlightedSprites[#root.TitleMenu.MenuEntriesHighlightedSprites + 1] = "TitleMenuEntryHighlighted" .. (i + 4);
end

root.Sprites["TitleMenuPressToStart"] = {
    Sheet = "Title",
    Bounds = { X = 1.5, Y = 1381.5, Width = 469.5, Height = 42 },
};

root.Sprites["DelusionADVUnder"] = {
    Sheet = "Title",
    Bounds = { X = 2794.5, Y = 1158, Width = 244.5, Height = 40.5 },
};

root.Sprites["DelusionADVUnderEnglish"] = {
    Sheet = "Title",
    Bounds = { X = 2793, Y = 1177.5, Width = 235.5, Height = 55.5 },
};

root.Sprites["DelusionADV"] = {
    Sheet = "Title",
    Bounds = { X = 2794.5, Y = 1092, Width = 244.5, Height = 40.5 },
};

root.Sprites["DelusionADVEnglish"] = {
    Sheet = "Title",
    Bounds = { X = 2793, Y = 1101, Width = 229.5, Height = 49.5 },
};

root.Sprites["SeiraUnder"] = {
    Sheet = "Title",
    Bounds = { X = 832.5, Y = 1.5, Width = 891, Height = 1152 },
};

root.Sprites["Seira"] = {
    Sheet = "Title",
    Bounds = { X = 1.5, Y = 1.5, Width = 828, Height = 1152 },
};

root.Sprites["CHLogo"] = {
    Sheet = "Title",
    Bounds = { X = 1.5, Y = 1156.5, Width = 891, Height = 172.5 },
};

root.Sprites["LCCLogoUnder"] = {
    Sheet = "Title",
    Bounds = { X = 895.5, Y = 1156.5, Width = 693, Height = 183 },
};

root.Sprites["ChuLeftLogo"] = {
    Sheet = "Title",
    Bounds = { X = 724.5, Y = 1372.5, Width = 204, Height = 162 },
};

root.Sprites["ChuRightLogo"] = {
    Sheet = "Title",
    Bounds = { X = 1039.5, Y = 1342.5, Width = 204, Height = 192 },
};

root.Sprites["LoveLogo"] = {
    Sheet = "Title",
    Bounds = { X = 511.5, Y = 1372.5, Width = 210, Height = 162 },
};

root.Sprites["StarLogo"] = {
    Sheet = "Title",
    Bounds = { X = 931.5, Y = 1342.5, Width = 105, Height = 192 },
};

root.Sprites["ExclMarkLogo"] = {
    Sheet = "Title",
    Bounds = { X = 1246.5, Y = 1342.5, Width = 123, Height = 192 },
};

root.Sprites["CopyrightText"] = {
    Sheet = "Title",
    Bounds = { X = 289.5, Y = 1336.5, Width = 570, Height = 36 },
};

root.Sprites["SpinningCircle"] = {
    Sheet = "Title",
    Bounds = { X = 2049, Y = 1.5, Width = 1021.5, Height = 1021.5 },
};

root.Sprites["TitleMenuIntroBackground"] = {
    Sheet = "TitleBg1",
    Bounds = { X = 0, Y = 0, Width = 1920, Height = 1080 },
};

root.Sprites["TitleMenuBackground"] = {
    Sheet = "TitleBg2",
    Bounds = { X = 0, Y = 0, Width = 1920, Height = 1080 },
};

root.Sprites["TitleMenuItemHighlight"] = {
    Sheet = "Title",
    Bounds = { X = 1372.5, Y = 1426.5, Width = 366, Height = 54 },
};

root.Sprites["TitleMenuItemHyperUpLine"] = {
    Sheet = "Title",
    Bounds = { X = 2707.5, Y = 1029, Width = 76.5, Height = 120 },
};

root.Sprites["TitleMenuItemSuperUpLine"] = {
    Sheet = "Title",
    Bounds = { X = 2707.5, Y = 1164, Width = 76.5, Height = 81 },
};

root.Sprites["TitleMenuItemUpLine"] = {
    Sheet = "Title",
    Bounds = { X = 2707.5, Y = 1267.5, Width = 76.5, Height = 42 },
};

root.Sprites["TitleMenuItemStraightLine"] = {
    Sheet = "Title",
    Bounds = { X = 2707.5, Y = 1332, Width = 76.5, Height = 3 },
};

root.Sprites["TitleMenuItemDownLine"] = {
    Sheet = "Title",
    Bounds = { X = 2707.5, Y = 1365, Width = 76.5, Height = 42 },
};

root.Sprites["TitleMenuItemSuperDownLine"] = {
    Sheet = "Title",
    Bounds = { X = 2707.5, Y = 1438.5, Width = 76.5, Height = 81 },
};

root.TitleMenu.LineEntriesSprites[#root.TitleMenu.LineEntriesSprites + 1] = "TitleMenuItemHyperUpLine";
root.TitleMenu.LineEntriesSprites[#root.TitleMenu.LineEntriesSprites + 1] = "TitleMenuItemSuperUpLine";
root.TitleMenu.LineEntriesSprites[#root.TitleMenu.LineEntriesSprites + 1] = "TitleMenuItemUpLine";
root.TitleMenu.LineEntriesSprites[#root.TitleMenu.LineEntriesSprites + 1] = "TitleMenuItemStraightLine";
root.TitleMenu.LineEntriesSprites[#root.TitleMenu.LineEntriesSprites + 1] = "TitleMenuItemDownLine";
root.TitleMenu.LineEntriesSprites[#root.TitleMenu.LineEntriesSprites + 1] = "TitleMenuItemSuperDownLine";

root.Sprites["TitleMenuItemLoadQuick"] = {
    Sheet = "Title",
    Bounds = { X = 2053.5, Y = 1026, Width = 324, Height = 30 },
};

root.Sprites["TitleMenuItemLoad"] = {
    Sheet = "Title",
    Bounds = { X = 2053.5, Y = 1059, Width = 324, Height = 30 },
};

root.Sprites["TitleMenuItemLoadQuickHighlighted"] = {
    Sheet = "Title",
    Bounds = { X = 1726.5, Y = 1026, Width = 324, Height = 30 },
};

root.Sprites["TitleMenuItemLoadHighlighted"] = {
    Sheet = "Title",
    Bounds = { X = 1726.5, Y = 1059, Width = 324, Height = 30 },
};

root.Sprites["TitleMenuSecondaryItemHighlight"] = {
    Sheet = "Title",
    Bounds = { X = 1372.5, Y = 1483.5, Width = 427.5, Height = 51 },
};
