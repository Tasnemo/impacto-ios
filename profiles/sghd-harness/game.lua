-- Asset-free VM harness for the STEINS;GATE Steam profile (Thread 04 Task 3).
--
-- Loads the complete sghd profile, then removes every dependency on game
-- data: all spritesheets become ScriptHandled (registered with the renderer,
-- never read from an archive) and only script.mpk is mounted. The real SC3 VM
-- and the sghd UI configuration run unchanged, so synthetic SCX fixtures can
-- run in CI. Not a playable game profile; nothing is drawn.
--
-- Fixture contract: <gamedata>/sghd/script.mpk containing the start script
-- (profiles/sghd/vm.lua; label 0 is the entry point). The process exits once
-- every script thread has ended, with exit status ScrWork[4000].

include(root.BasePaths.RootProfilesDir .. '/sghd/game.lua');

root.WindowName = "STEINS;GATE VM harness";

for _, sheet in pairs(root.SpriteSheets) do
    sheet.ScriptHandled = true;
end

root.Vfs = {
    Mounts = {
        ["script"] = {root.BasePaths.RootGamedataDir .. "/sghd/script.mpk"},
    }
};

root.Vm.ExitWhenThreadsEnd = true;
root.Vm.ExitCodeScrWork = 4000;
