local sheet = "Data";
local name = "SysMesBox";

root.SysMesBoxDisplay = {
    Type = SysMesBoxType.CHLCC,
    DrawType = DrawComponentType.SystemMessage,
    BoxX = 0,
    BoxY = 345,
    TextFontSize = 48,
    TextMiddleY = 354,
    TextX = 960,
    TextLineHeight = 51,
    TextMarginY = 21,
    ChoicePadding = 60,
    ChoiceY = 547.5,
    ChoiceXBase = 1020,
    MinMaxMesWidth = 441,
    MinHighlightWidth = 72,
    HighlightBaseWidth = 216,
    HighlightYOffset = 0,
    HighlightXOffset = 0,
    HighlightXBase = 987,
    HighlightXStep = 198,
    HighlightRightPartSpriteWidth = 36,
    AnimationSpeed = 55,
    FadeInDuration = 0.33,
    FadeOutDuration = 0.25
};

root.Sprites[name .. "Box"] = {
    Sheet = sheet,
    Bounds = {
        X = 1150.5,
        Y = 955.5,
        Width = 1920,
        Height = 258
    }
};
root.SysMesBoxDisplay.Box = name .. "Box";

root.Sprites[name .. "BoxDecoration"] = {
    Sheet = sheet,
    Bounds = {
        X = 2074.5,
        Y = 175.5,
        Width = 888,
        Height = 12
    }
};
root.SysMesBoxDisplay.BoxDecoration = name .. "BoxDecoration";

root.Sprites[name .. "SelectionLeftPart"] = {
    Sheet = sheet,
    Bounds = {
        X = 753,
        Y = 76.5,
        Width = 216,
        Height = 57
    }
};
root.SysMesBoxDisplay.SelectionLeftPart = name .. "SelectionLeftPart";

root.Sprites[name .. "SelectionRightPart"] = {
    Sheet = sheet,
    Bounds = {
        X = 951,
        Y = 76.5,
        Width = 36,
        Height = 57
    }
};
root.SysMesBoxDisplay.SelectionRightPart = name .. "SelectionRightPart";

root.Sprites[name .. "SelectionMiddlePart"] = {
    Sheet = sheet,
    Bounds = {
        X = 772.5,
        Y = 76.5,
        Width = 198,
        Height = 57
    }
};
root.SysMesBoxDisplay.SelectionMiddlePart = name .. "SelectionMiddlePart";
-- Members required by src/profile/games/chlcc/sysmesbox.cpp that the PS3
-- profile predates. Bounds are placeholders until the Steam system.mpk sheet
-- layout is known (Task 5).
root.Sprites[name .. "LoadingStar"] = {
    Sheet = sheet,
    Bounds = { X = 0, Y = 0, Width = 12, Height = 12 }
};
root.SysMesBoxDisplay.LoadingStar = name .. "LoadingStar";
root.SysMesBoxDisplay.LoadingStarsPosition = { X = 870, Y = 535.5 };
root.SysMesBoxDisplay.LoadingStarsFadeDuration = 0.533;
