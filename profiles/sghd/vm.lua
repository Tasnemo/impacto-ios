-- VM settings shared by profiles/sghd and profiles/sghd-harness.
root.Vm = {
    StartScript = 2, -- script.mpk id 2 = _STARTUP_WIN.SCX (Steam evidence)
    StartScriptBuffer = 0,
    GameInstructionSet = InstructionSet.SGHD,
    -- SGHD Call/CallFar/CallIfFlag/CallFarIfFlag carry a u16 return-address id
    UseReturnIds = true,

    ScrWorkChaStructSize = 20,
    ScrWorkChaOffsetStructSize = 10,
    ScrWorkBgStructSize = 20,
    ScrWorkBgOffsetStructSize = 10,

    -- Bring-up diagnostic: log where a script thread has waited this long.
    StallReportSeconds = 5,
};
