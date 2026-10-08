-- VM settings shared by profiles/sghd and profiles/sghd-harness.
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
