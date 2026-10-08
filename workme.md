# impacto-ios

**A native, fully offline iOS port of Committee of Zero's impacto engine, initially targeting the original English Steam release of STEINS;GATE.**

Repository: https://github.com/Tasnemo/impacto-ios

Upstream engine: https://github.com/CommitteeOfZero/impacto

---

# 1. Project Mission

The purpose of this repository is to adapt the existing open-source impacto visual novel engine to run natively on iOS.

The first target is the **original English Steam release of STEINS;GATE**, not STEINS;GATE ELITE or the PlayStation 3 release.

The eventual application must:

- Run natively on modern iPhones.
- Function completely offline.
- Preserve the original game's artwork, dialogue, voice acting, music, and mechanics.
- Support phone triggers and all branching routes.
- Support reliable saves and loading.
- Support all endings.
- Load assets from a legitimate Steam installation.
- Require no Steam, Crunchyroll, or cloud authentication.
- Support personal sideloading.
- Be developed without requiring the developer to own a Mac.

This is an **engine-porting and compatibility project**, not a new visual novel engine.

Preserve impacto's existing C++ implementation wherever practical.

Do not rewrite working engine components in Swift or Objective-C++ simply because the destination platform is iOS.

Use native Apple technologies where technically appropriate.

---

# 2. Authoritative Repository Context

## Repository

https://github.com/Tasnemo/impacto-ios

Current integration branch: `master`.

The repository is currently public.

Commercial game assets, derivative script dumps, certificates, credentials, and signing secrets must never be committed.

## Historical Work

### Thread 01 — Architecture Investigation

**Completed.**

Established:

- impacto's C++20 architecture.
- Lua game profile system.
- Script VM and opcode tables.
- Virtual filesystem.
- Audio/video pipelines.
- Renderer abstraction.
- Existing Android GLES3 implementation.
- iOS port feasibility.
- Initial STEINS;GATE compatibility blockers.

### Thread 02 — Desktop Build

**Completed and merged into master.**

Established:

- Ubuntu 24.04/GCC 13 build.
- Pinned dependency toolchain.
- Reproducible CMake/Ninja configuration.
- Working impacto executable.
- Asset-free launcher smoke tests.
- GitHub Actions desktop build workflow.
- Build logs and reproduction instructions.

Do not rebuild this infrastructure from scratch.

### Thread 03 — STEINS;GATE Compatibility Investigation

**Investigation completed on branch `phase-02-steins-compatibility`.**

The next agent must verify that this branch has been merged into `master` before beginning implementation.

If it has not been merged, use the documented Thread 03 commit/branch and prepare integration without discarding its work.

Thread 03 produced:

- Compatibility investigation.
- Verified synthetic runtime probes.
- Prioritized blocker list.
- Opcode analysis.
- Implementation plan.
- Asset-free unit tests.
- CI test integration.
- Windows Steam-validation instructions.

The investigation identified several major problems.

**Missing Steam game profile**

The existing `sgps3` profile targets the PS3 version and is not directly suitable for Steam.

**Outdated profile configuration**

The PS3 profile references outdated UI configurations and fails during initialization.

**Broken call/return behavior**

The existing configuration does not correctly handle the return IDs required by the Steam instruction layout.

**VM infinite loops**

Sixteen opcode slots map to dummy handlers capable of leaving the VM stuck in an execution loop.

**Instruction layout mismatches**

Twenty-one instruction argument layouts require correction or verification.

**Incomplete game mechanics**

Phone, mail, saves, dialogue UI, and video compatibility require further implementation.

These findings are already documented.

**Do not repeat Thread 03's broad reverse-engineering investigation.**

Read and reuse the existing evidence.

---

# 3. Required Reading

Before beginning any development task, read:

1. `workme.md`
2. `docs/handoff.md`
3. `docs/roadmap.md`
4. Relevant implementation documentation
5. Relevant source code and tests

For STEINS;GATE compatibility work, also read:

- `docs/architecture.md`
- `docs/decisions.md`
- `docs/steins-gate-compatibility.md`
- `docs/steins-gate-blockers.md`
- `docs/thread-04-implementation-plan.md`
- `docs/compatibility-matrix.md`
- `tests/compat/README.md`

These files may reside on the Thread 03 branch until integration is complete.

Use the latest committed documentation.

If documentation conflicts with source code or test results, investigate the discrepancy.

Do not blindly trust outdated reports.

Do not read every source file merely to establish context.

Use targeted inspection based on the assigned subsystem.

---

# 4. Core Development Philosophy

## 4.1 Minimize Agent Usage

Amp agent usage is a limited resource.

The project has comparatively more Orb compute available.

Agent reasoning and Orb execution are separate resources.

Unused Orb compute does not convert into agent reasoning allowance.

The objective is to **use AI reasoning only when it adds meaningful engineering value**.

Avoid spending expensive agent usage on repetitive operations.

### Agent Responsibilities

Use Amp agents for:

- Understanding unfamiliar code.
- Designing implementation approaches.
- Writing new engine functionality.
- Investigating unexpected behavior.
- Resolving difficult failures.
- Reviewing code.
- Making architectural decisions.
- Reverse-engineering undocumented features.

### Orb Responsibilities

Use Orb terminal execution for:

- Compiling.
- Rebuilding.
- Running tests.
- Executing scripts.
- Inspecting file headers.
- Generating opcode inventories.
- Comparing instruction tables.
- Running regression suites.
- Capturing logs.
- Running deterministic experiments.
- Generating test reports.
- Performing performance measurements.

Prefer writing a reusable script once over repeatedly asking Amp to perform the same operation.

## 4.2 Default to Medium Reasoning

The overall complexity of the project is not justification for using Ultra on every thread.

Each task should use the minimum sufficient reasoning intensity.

| Amp Mode | Default Purpose |
|---|---|
| Low | Documentation, simple maintenance, straightforward isolated edits |
| Medium | Default implementation, testing, CI, bounded investigations |
| High | Complex implementation, difficult debugging, substantial subsystem decisions |
| Ultra | Exceptional reverse engineering and unresolved architectural problems |

**Medium is the default for new implementation threads.**

High is used when there is concrete evidence that Medium is insufficient.

Ultra is reserved for difficult questions that High cannot resolve reliably.

Do not choose Ultra merely because the project involves an emulator, interpreter, or iOS port.

## 4.3 Escalation by Evidence

Begin a task at Medium unless the task has an established reason to use another mode.

After an implementation attempt, evaluate:

1. Does it compile?
2. Do relevant tests pass?
3. Does runtime behavior match expectations?
4. Are changes isolated and maintainable?
5. Are there unresolved technical assumptions?

If the implementation passes its defined acceptance criteria, proceed normally.

If it fails:

1. Execute existing diagnostic scripts.
2. Identify the smallest failing case.
3. Capture the relevant error.
4. Determine whether the problem is mechanical or conceptual.
5. Attempt an isolated correction at the current intensity.
6. Escalate only if the blocker genuinely requires deeper reasoning.

### Medium to High

Escalate when:

- Repeated focused attempts fail.
- A subsystem has complex state interactions.
- A bug cannot be isolated using existing tests.
- The implementation requires nontrivial architectural judgment.

### High to Ultra

Escalate when:

- Required instruction semantics remain undocumented.
- Reverse engineering cannot proceed from known evidence.
- Competing architectures require a substantial technical decision.
- Existing documentation is insufficient and source behavior is fundamentally ambiguous.

Do not escalate simply because a compiler reports many errors.

Do not escalate for ordinary dependency installation or CI configuration issues.

## 4.4 Escalation Requires a Handoff

Amp reasoning intensity is fixed per thread.

To change intensity:

1. Stop at a coherent checkpoint.
2. Preserve verified code.
3. Record failing tests.
4. Update `docs/handoff.md`.
5. Commit and push.
6. Start a new thread.
7. Select the appropriate intensity.
8. Read the committed handoff.

Do not assume a new thread shares the previous thread's conversation history.

---

# 5. Orb-First Execution

## 5.1 Existing Build Infrastructure

The established development environment uses:

- Ubuntu 24.04.
- GCC 13.
- CMake.
- Ninja.
- vcpkg.
- The existing impacto CMake configuration.
- Xvfb/Mesa for headless launcher tests.

Relevant instructions:

- `docs/desktop-build.md`
- `docs/desktop-test-results.md`

Reuse pinned dependencies and existing build directories wherever available.

New Orb environments may not retain previous build outputs.

When state is missing, reproduce the documented environment through scripts.

Do not manually rediscover dependencies.

## 5.2 Incremental Builds

When changing a small amount of C++ code:

- Prefer incremental compilation.
- Do not rebuild unchanged dependencies.
- Reuse the existing build preset.
- Avoid deleting working caches.
- Capture build failures to logs.

Full clean builds are appropriate when required to validate reproducibility or investigate build-system problems.

## 5.3 Reusable Tools

Maintain reusable scripts under existing appropriate repository directories.

Potential interfaces include:

```text
tools/
  sg-inspect/
  sg-asset-pack/

tests/
  compat/
  runtime/
  fixtures/
```

These are organizational suggestions, not instructions to create empty directories.

Use scripts for:

- Archive analysis.
- Opcode analysis.
- Script fixture generation.
- VM regression testing.
- Save-state round-trip testing.
- Automated desktop launches.
- Asset validation.
- iOS packaging.

Avoid creating duplicate functionality when an existing script already performs the task.

## 5.4 Diagnostic Reporting

For expensive or lengthy automated operations, generate:

- A short summary.
- Complete raw logs.
- Exit status.
- Relevant error messages.
- Environment information.
- Git commit hash.

Prefer reading the summary first.

Inspect raw logs only when necessary.

Do not paste enormous successful build logs back into the agent context.

## 5.5 Long-Running Operations

Compilation and test execution should run autonomously through the Orb terminal or CI.

Agents should avoid repeatedly polling a process when doing so offers no useful additional information.

Use a single supervised command or script where possible.

Do not run unnecessary long-lived background services for one-shot tests.

---

# 6. Mandatory Testing Rules

## 6.1 Preserve Thread 03 Tests

Thread 03 introduced `tests/compat/`.

The tests include:

- SC3 decoding tests.
- Opcode table audits.
- Synthetic fixtures.
- Runtime probes.
- Regression checks.

These tests are now part of the project's engineering foundation.

Do not delete them merely because they expose problems in the existing engine.

## 6.2 Baseline Test Commands

For applicable desktop compatibility tasks, execute:

```bash
python3 -m unittest discover -s tests/compat -v
```

For runtime probes, use the environment and commands documented in:

```text
tests/compat/README.md
docs/desktop-build.md
```

The Thread 03 handoff documents a working binary probe command:

```bash
IMPACTO_BIN=release/ubuntu24/impacto \
python3 -m unittest tests.compat.test_runtime_probe -v
```

This must run within the documented environment, including any required Xvfb/OpenAL setup.

In a headless environment, the existing tests use:

```bash
ALSOFT_DRIVERS=null
```

This avoids a known no-audio-device crash.

Do not assume that the command above works outside its required environment.

## 6.3 Existing Tests May Assert Known Bugs

Some Thread 03 runtime probes intentionally verify that the current engine fails in a specific way.

When fixing such a bug:

1. Preserve the test case.
2. Change its expectation to the correct behavior.
3. Verify the corrected result.
4. Ensure the previous failure no longer occurs.
5. Record the transition.

Do not leave a test that expects a known bug after the bug is fixed.

Do not remove regression coverage.

## 6.4 Test Quality

Tests must verify behavior, not simply implementation details.

Examples of meaningful assertions:

- `Call` returns to the correct instruction.
- `ReturnIfFlag` follows the expected branch.
- An unsupported instruction does not hang the VM.
- An instruction consumes the correct number of bytes.
- A save restores VM state accurately.
- A phone reply changes the correct story flags.

A successful compilation does not prove gameplay compatibility.

Synthetic fixture success does not prove real Steam compatibility.

Simulator success does not prove physical iPhone compatibility.

Record these distinctions explicitly.

---

# 7. Development Roadmap

The original Threads 01–03 remain historical milestones.

Future development should use smaller, bounded threads.

Each thread must have a specific acceptance gate.

The exact number of threads may grow as new evidence emerges.

## Phase A — Desktop Compatibility Foundation

| Thread | Objective | Default Mode |
|---|---|---|
| 04A | Steam profile and correct VM initialization | Medium |
| 04B | Opcode handling and instruction layouts | Medium |
| 04C | Asset-free VM harness | Medium |
| 04D | Save-state foundation | Medium |

## Phase B — Actual Steam Gameplay

| Thread | Objective | Default Mode |
|---|---|---|
| 05A | First Steam asset boot | Medium |
| 05B | Dialogue, charset, and UI | Medium |
| 06A | Phone/mail behavior investigation | Medium → High if needed |
| 06B | Phone/mail state implementation | Medium / High |
| 06C | Phone/mail interface | Medium |
| 07A | Complete save/load integration | Medium |
| 07B | Movie and audio compatibility | Medium |
| 07C | Representative desktop gameplay test | Medium |

## Phase C — Native iOS Port

| Thread | Objective | Default Mode |
|---|---|---|
| 08A | iOS ARM64 toolchain and dependencies | Medium |
| 08B | Minimal native iOS app | Medium |
| 08C | Signing and sideloading workflow | Medium |
| 09A | Existing GLES3 renderer feasibility | Medium |
| 09B | iOS rendering integration | Medium / High |
| 10A | Audio and video integration | Medium |
| 10B | Touch and phone controls | Medium |
| 10C | Asset import, storage, and lifecycle | Medium |

## Phase D — Complete iPhone Gameplay

| Thread | Objective | Default Mode |
|---|---|---|
| 11A | Steam asset integration on iPhone | Medium |
| 11B | Desktop/iOS gameplay parity | Medium |
| 11C | Physical-device compatibility fixes | Medium / High |
| 12A | Full-route regression testing | Medium |
| 12B | Offline reliability | Medium |
| 12C | Performance and release documentation | Low / Medium |

These labels describe milestones.

They do not require opening a new agent thread for every small task.

A single Medium thread may complete multiple closely related tasks if the scope remains clear and tests are passing.

Stop when the task changes substantially or further reasoning requires a different intensity.

---

# 8. Thread 04A — Steam Profile Initialization

**Default Mode: MEDIUM**

## Objective

Implement the first task from `docs/thread-04-implementation-plan.md`.

Add support for a Steam-specific `sghd` profile.

## Required Work

- Register `sghd` in `gamedefinitions.lua`.
- Create `profiles/sghd/`.
- Preserve `profiles/sgps3/`.
- Add `InstructionSet::SGHD`.
- Add the initial `opcodetables_sghd.h`.
- Configure the correct archive mounts.
- Enable `UseReturnIds`.
- Resolve initial profile configuration failures.
- Reach VM initialization with synthetic fixtures.

## Important Findings

The old PS3 profile is not a reliable Steam implementation.

Do not patch `sgps3` in place.

The existing code needs to consume return IDs correctly.

Use Thread 03's runtime probes to verify behavior.

## Acceptance Criteria

- Synthetic profile initialization succeeds.
- No outdated HUD member abort.
- Correct return-address handling.
- Existing PS3 profile behavior preserved.
- Appropriate unit and runtime tests pass.
- Changes committed and documented.

## Opening Prompt

Read `workme.md`, `docs/handoff.md`, `docs/thread-04-implementation-plan.md`, and `tests/compat/README.md`.

Execute Thread 04A only.

Implement the Steam-specific `sghd` profile and reach VM initialization using the existing synthetic fixtures.

Enable correct return-ID handling.

Preserve the PS3 profile and upstream compatibility.

Use existing Orb build infrastructure and automated tests.

Do not investigate the entire repository again.

Do not implement unrelated opcode semantics, phone systems, saves, or iOS functionality.

Commit verified changes, update the handoff, and stop.

---

# 9. Thread 04B — Opcode Compatibility

**Default Mode: MEDIUM**

**Escalate to HIGH for genuinely ambiguous VM behavior.**

## Objective

Fix the known opcode handling and argument-layout problems.

## Existing Evidence

Thread 03 identified:

- Sixteen dummy opcode slots.
- Twenty-one argument-layout mismatches.
- Broken conditional call/return behavior.
- Potential infinite execution loops.

These findings are documented in:

- `docs/steins-gate-blockers.md`
- `docs/thread-04-implementation-plan.md`
- `tests/compat/fixtures/`

## Required Work

- Correct relevant opcode mappings.
- Implement known missing control-flow behavior.
- Consume instruction arguments correctly.
- Prevent infinite loops.
- Add SGHD-specific behavior where required.
- Preserve other instruction sets.
- Log unsupported semantics accurately.

Do not treat an instruction as implemented merely because the handler advances the instruction pointer.

Distinguish correct parsing from correct instruction behavior.

## Orb Automation

Use automated opcode audits and synthetic VM fixtures.

Avoid manual inspection of the same opcode table repeatedly.

## Acceptance Criteria

- Known dummy-slot hazards addressed.
- Relevant argument layouts consume the correct bytes.
- Control-flow fixtures pass.
- No infinite loops in the tested cases.
- Existing instruction sets remain unaffected.
- Regression suite passes.

## Opening Prompt

Read the current handoff, opcode gap fixtures, compatibility backlog, and Thread 04 implementation plan.

Execute Thread 04B only.

Fix the verified SGHD opcode-table and instruction-layout problems.

Use the existing compatibility tests.

Extend the tests to demonstrate correct VM execution.

Do not implement speculative opcode semantics.

Keep engine changes specific to SGHD where possible.

Use Orb scripts for repeated builds and tests.

Commit verified changes and hand off.

---

# 10. Thread 04C — Asset-Free VM Harness

**Default Mode: MEDIUM**

## Objective

Make STEINS;GATE VM regression tests independent of commercial assets.

## Required Work

Implement a dedicated harness profile or equivalent test mode.

It should support:

- Synthetic scripts.
- Minimal configuration.
- No commercial spritesheets.
- No proprietary audio.
- Deterministic VM execution.
- Explicit test termination.
- Exit-code reporting.
- Log capture.

The harness must execute the actual engine VM.

Do not create an entirely independent interpreter that can pass while impacto remains broken.

## Acceptance Criteria

- Tests execute through the real VM.
- No commercial game files required.
- Reproducible locally.
- Reproducible in GitHub Actions.
- Clear pass/fail behavior.

## Opening Prompt

Read `workme.md`, `docs/handoff.md`, and Task 3 in `docs/thread-04-implementation-plan.md`.

Execute Thread 04C only.

Create an asset-free SGHD VM testing harness using the real impacto interpreter.

Integrate it with existing compatibility tests and CI.

Do not implement new gameplay features.

Use reusable scripts and minimize repeated agent interaction.

Commit verified work and update the handoff.

---

# 11. Thread 04D — Save-State Foundation

**Default Mode: MEDIUM**

## Objective

Implement the basic SGHD save-state adapter.

## Required Work

Persist and restore:

- Script position.
- VM thread state.
- Call stack.
- Return IDs.
- FlagWork.
- ScrWork.
- Read-line state.
- Relevant engine configuration.

Use an internal save format initially.

Compatibility with Steam's original save files is optional.

Do not misrepresent a fork-native format as Steam-compatible.

## Testing

Create deterministic serialization tests.

Verify that execution resumes correctly after loading.

## Acceptance Criteria

- Save/reload round trip passes.
- VM state is restored correctly.
- Regression tests verify continuation behavior.
- No dependence on proprietary assets.

## Opening Prompt

Read the current handoff and Task 4 of the Thread 04 implementation plan.

Execute Thread 04D only.

Implement the minimal SGHD save-state adapter.

Use existing impacto save infrastructure.

Create deterministic serialization and state-restoration tests.

Do not implement the Steam save-file format unless its structure has been verified.

Commit, document, and stop.

---

# 12. Thread 05 — Real Steam Boot and Dialogue

**Default Mode: MEDIUM**

## Objective

Run the original Steam game's assets and display the first dialogue.

This milestone depends on access to evidence from the developer's legitimate Windows installation.

## Required Work

- Inspect real MPK headers.
- Verify archive versions.
- Identify resource IDs.
- Identify startup scripts.
- Map required spritesheets.
- Load the game profile.
- Implement the required dialogue box.
- Support the correct charset.
- Display original dialogue.

## Asset Policy

Keep commercial assets out of GitHub and public CI.

Use Windows-local inspection tools.

Share only information necessary for compatibility analysis.

Do not fabricate gameplay success when actual files are unavailable.

## Acceptance Criteria

A real Steam gameplay sequence begins and displays original dialogue.

If this cannot be tested, document the precise blocker.

## Opening Prompt

Read the latest handoff, current SGHD profile, compatibility matrix, and Windows asset-inspection procedure.

Execute the next bounded Thread 05 task.

Use actual Steam asset evidence where available.

Implement only the missing resource and dialogue functionality necessary to reach the first dialogue.

Reuse existing engine systems.

Do not begin phone mechanics or iOS work.

Commit verified changes and hand off.

---

# 13. Thread 06 — Phone and Mail Mechanics

**Default Mode: MEDIUM**

**HIGH or ULTRA only when justified by unresolved semantics.**

## Objective

Implement the phone-trigger mechanics central to STEINS;GATE.

## Required Work

- Investigate observed phone/mail instruction usage.
- Implement phone state.
- Implement message events.
- Implement reply choices.
- Implement conditional branching.
- Connect phone state to save/load.
- Implement the required interface.
- Preserve original game behavior.

## Test Strategy

Develop synthetic phone-event sequences.

Verify resulting flags and script transitions.

Use local Steam script evidence when necessary.

## Escalation

If actual phone instruction semantics cannot be inferred:

1. Isolate the specific instruction.
2. Preserve its argument layout.
3. Record relevant script context.
4. Write a minimal failing test.
5. Escalate only that question.

Do not escalate the entire subsystem without a concrete blocker.

## Acceptance Criteria

Phone-event tests pass.

At least one real branching phone interaction is verified when legitimate game files are available.

## Opening Prompt

Read the current handoff, phone-related blocker documentation, and relevant script evidence.

Execute the next bounded Thread 06 task.

Implement or test one well-defined portion of the STEINS;GATE phone/mail system.

Use synthetic event sequences and automated VM tests.

Do not guess undocumented behavior.

Escalate only precise unresolved semantics.

Commit verified changes and hand off.

---

# 14. Thread 07 — Complete Desktop Gameplay Foundation

**Default Mode: MEDIUM**

## Objective

Establish reliable representative gameplay on desktop before undertaking substantial iOS integration.

## Required Work

- Complete save/load integration.
- Correct audio instruction behavior.
- Verify movie formats.
- Implement a practical video strategy.
- Verify chapter transitions.
- Verify branching behavior.
- Resolve critical script execution blockers.

## Video Strategy

Inspect actual Steam video signatures before selecting a solution.

If the original files use unsupported Bink 2:

- Investigate legitimate Windows-local conversion.
- Consider supported alternative codecs.
- Preserve original content fidelity.
- Avoid unnecessary proprietary decoder development.

Do not assume that all movie files share the same format.

## Desktop Gameplay Gate

Demonstrate:

1. Game startup.
2. Original dialogue.
3. Phone interaction.
4. Route-affecting choice.
5. Save.
6. Load.
7. Correct story continuation.

Use automated tests where practical.

The desktop implementation does not need all endings complete before an independent minimal iOS feasibility experiment, but important unknowns must remain documented.

## Opening Prompt

Read the latest handoff and outstanding desktop compatibility blockers.

Execute the next bounded Thread 07 task.

Implement missing save, media, or gameplay progression behavior.

Use the existing test harness and Orb automation.

Prioritize a representative end-to-end desktop gameplay sequence.

Do not claim full compatibility based on partial progression.

Commit, update results, and stop.

---

# 15. Thread 08 — Native iOS ARM64 Build

**Default Mode: MEDIUM**

## Objective

Compile the existing impacto engine into a minimal native iOS application.

## Development Constraints

- Developer uses Windows.
- Mac ownership is not required.
- GitHub Actions macOS runners provide Apple build tooling.
- Physical device installation requires separate signing.
- Commercial game files are not included in CI.

## Required Work

- Verify ARM64 dependency builds.
- Configure CMake for iOS.
- Implement the minimal SDL3 iOS application shell.
- Configure app resources.
- Establish a reproducible macOS build workflow.
- Produce appropriate application artifacts.
- Document signing and installation.

## Acceptance Criteria

iOS ARM64 build succeeds.

Application packaging is reproducible.

Real-device installation is verified separately.

## Opening Prompt

Read the latest handoff and the current desktop implementation.

Execute the next bounded Thread 08 task.

Establish native iOS ARM64 compilation and a minimal impacto-based application shell.

Use GitHub Actions macOS runners.

Preserve the C++ engine.

Do not begin a Metal rewrite.

Document actual compilation and signing status.

Commit verified work and stop.

---

# 16. Thread 09 — iOS Rendering

**Default Mode: MEDIUM**

## Objective

Reuse impacto's rendering infrastructure on iOS wherever possible.

## Preferred Approach

Investigate the existing GLES3 renderer first.

Verify whether it is usable with the chosen iOS SDK and device target.

OpenGL ES is deprecated, so do not assume its long-term viability.

If unsuitable, evaluate:

- ANGLE-on-Metal.
- Native Metal implementation.
- Metal-cpp.
- MoltenVK with existing Vulkan support.

Choose based on actual compatibility and implementation cost.

Do not implement multiple full rendering backends unnecessarily.

## Acceptance Criteria

Representative scenes render correctly.

Original aspect ratio, textures, transparency, text, and transitions work.

Automated screenshot comparisons are encouraged.

## Opening Prompt

Read the renderer architecture documentation and latest iOS handoff.

Execute the next bounded Thread 09 task.

Validate reuse of impacto's GLES3 renderer before implementing alternatives.

Use simulator and CI testing where practical.

Preserve rendering correctness.

Commit tested changes and document device compatibility.

---

# 17. Thread 10 — iOS Platform Integration

**Default Mode: MEDIUM**

## Objective

Implement the platform services required for gameplay.

## Required Work

- Audio output.
- Video playback.
- Touch input.
- Phone interaction mapping.
- Files app import.
- Local save storage.
- Application suspension.
- Foreground restoration.
- Audio interruption handling.
- Memory-pressure handling.

Reuse existing impacto logic.

Keep Apple-specific code isolated.

## Acceptance Criteria

The app can render, play audio, accept input, import test resources, preserve state, and resume normally.

Physical-device behavior must be validated separately.

## Opening Prompt

Read the latest handoff and existing iOS implementation.

Execute the next bounded Thread 10 task.

Implement one isolated iOS platform integration feature.

Reuse existing impacto systems.

Add automated tests where possible.

Use Orb and CI execution instead of repeated manual agent-driven testing.

Commit verified changes and hand off.

---

# 18. Thread 11 — STEINS;GATE on iPhone

**Default Mode: MEDIUM**

## Objective

Run the original English Steam STEINS;GATE release through the native iOS application.

## Required Work

- Import legitimate game data.
- Load the game profile.
- Display dialogue.
- Play voice and music.
- Execute phone events.
- Support branching.
- Support saves.
- Play video.
- Preserve gameplay behavior.

## Validation

Automate platform-neutral tests.

Use CI for build and simulator verification.

Provide explicit manual tests for the user's physical iPhone.

Do not claim device success without observed results.

## Acceptance Criteria

A representative gameplay sequence works on the physical iPhone.

All remaining incompatibilities are recorded.

## Opening Prompt

Read the latest handoff and desktop/iOS compatibility documentation.

Execute the next bounded Thread 11 task.

Integrate STEINS;GATE with the iOS version of impacto.

Preserve identical game logic between desktop and iOS.

Use automated parity tests where possible.

Provide exact physical-device test steps for anything CI cannot validate.

Commit tested changes and hand off.

---

# 19. Thread 12 — Complete Gameplay and Release

**Default Mode: LOW or MEDIUM**

**HIGH for difficult regressions.**

## Objective

Deliver a reliable, fully offline, personally sideloadable application.

## Required Work

- Verify all story routes.
- Verify all endings.
- Test phone-trigger progression.
- Verify saves and loading.
- Test media playback.
- Test offline launches.
- Test device restart.
- Test suspension/resume.
- Investigate memory problems.
- Profile performance.
- Prepare signing documentation.
- Prepare installation instructions.
- Document tested iOS versions.

## Performance Policy

Measure before optimizing.

Do not rewrite engine subsystems based solely on theoretical performance concerns.

## Offline Requirements

The installed application must run without:

- Steam authentication.
- Crunchyroll authentication.
- Internet connectivity.
- Cloud streaming.
- Remote game services.

Signing expiration and renewal are separate operational considerations.

## Acceptance Criteria

All endings are reachable.

Offline functionality is verified.

The application can be rebuilt and sideloaded using documented instructions.

## Opening Prompt

Read the latest handoff, compatibility matrix, and physical-device test results.

Execute the next bounded Thread 12 task.

Use automated regression suites and CI wherever possible.

Verify routes, offline reliability, save behavior, and release readiness.

Escalate only difficult regressions.

Document actual results, known limitations, and supported iOS versions.

Commit verified work and stop.

---

# 20. Git Workflow

The repository currently uses `master` as its integration branch.

Use focused feature branches for substantial changes.

Before beginning work:

1. Check the current branch.
2. Check `git status`.
3. Fetch the latest remote commits.
4. Identify the intended base commit.
5. Verify prerequisite work is integrated or explicitly available.

Do not overwrite another thread's unmerged work.

At completion:

1. Run applicable tests.
2. Commit changes.
3. Push the branch.
4. Make changes reviewable.
5. Integrate validated work into `master` when authorized.
6. Update the handoff.
7. Stop.

Do not claim work is integrated merely because it exists on a feature branch.

Do not force-push over another agent's work.

---

# 21. Handoff Requirements

Every development thread must update:

`docs/handoff.md`

Use the following structure:

```markdown
# Project Handoff

## Current Milestone
What task was completed?

## Repository State
Branch, commit, and merge status.

## Completed Work
What was implemented?

## Verification
What tests ran and passed?

## Failed or Skipped Tests
What did not pass or could not run?

## Known Limitations
What remains broken or unverified?

## Reproducible Commands
How can the next thread repeat the tests?

## Relevant Logs
Where are the useful diagnostic files?

## Architectural Decisions
What changed and why?

## Open Questions
What remains unresolved?

## Next Milestone
The smallest useful next task.

## Recommended Mode
Low / Medium / High / Ultra.
```

Also maintain relevant entries in:

- `docs/roadmap.md`
- `docs/compatibility-matrix.md`
- `docs/steins-gate-blockers.md`
- `docs/decisions.md`
- `docs/threads/`

Keep documentation synchronized with actual repository state.

---

# 22. Commercial Asset Policy

The developer owns the original English Steam release of STEINS;GATE.

The project may use legally obtained local game files for personal compatibility testing.

Never commit:

- Steam game archives.
- Original scripts or substantial derivative script dumps.
- Original audio files.
- Original video files.
- Proprietary fonts or artwork.
- Authentication credentials.
- Apple signing secrets.

Prefer Windows-local extraction and validation tools.

Synthetic fixtures are appropriate for automated public CI.

Do not download pirated game data.

---

# 23. Engineering Quality Rules

## No Unsupported Claims

Distinguish:

- Verified.
- Source-level.
- Externally reported.
- Unknown.
- Failed.

Do not claim that a feature works without corresponding evidence.

## No Unnecessary Rewrites

Preserve impacto's architecture.

Keep changes additive and maintainable where practical.

## No Speculative Implementations

Do not implement unknown behavior merely because a similarly named instruction exists.

Use tests and source evidence.

## No Endless Investigations

A thread should answer the questions necessary for its assigned milestone.

Do not explore unrelated subsystems without a clear reason.

## No Repeated Mechanical Work

Use scripts for deterministic operations.

Do not spend repeated agent calls generating the same report.

## No Silent Test Weakening

Do not delete, skip, or weaken tests merely to produce green results.

If an expected-failure test becomes a passing regression, document the change.

## No Unbounded Scope Expansion

Do not automatically implement adjacent major features when the assigned milestone is complete.

Record them for future threads.

## No Artificial Over-Splitting

Do not open separate threads for tiny tasks that fit naturally into an existing bounded implementation.

Thread boundaries exist to preserve clarity and manage reasoning intensity, not to maximize thread count.

---

# 24. Final Definition of Done

The project is complete when:

1. impacto runs natively on iOS ARM64.
2. The original English Steam STEINS;GATE release is playable.
3. Original dialogue, graphics, voice acting, music, and required video function correctly.
4. Phone triggers and branching mechanics work.
5. Saves and loading are reliable.
6. All endings are reachable.
7. Game data can be imported from a legitimate Steam installation.
8. The application runs without internet access or third-party authentication.
9. The app can be built using reproducible cloud workflows.
10. The app can be personally signed and sideloaded from a Windows-based development workflow.
11. The implementation remains maintainable and based on impacto's existing engine architecture.
12. Actual compatibility is supported by tests and physical-device evidence.

---

# 25. Final Agent Directive

**This repository is the source of truth.**

Before acting:

- Read the latest handoff.
- Identify the current milestone.
- Read relevant tests and implementation plans.
- Reuse prior findings.
- Select the smallest useful scope.

While working:

- Prefer Medium reasoning.
- Use Orb compute for deterministic execution.
- Implement rather than endlessly investigate.
- Add tests for new behavior.
- Preserve existing cross-platform functionality.
- Escalate only when supported by evidence.

Before finishing:

- Run tests.
- Record failures.
- Commit.
- Push.
- Update the handoff.
- Stop.

**The development philosophy is simple:**

**Medium implements. Automated tests evaluate. High solves difficult blockers. Ultra handles exceptional uncertainty. Orbs execute repeatable work.**

The goal is not to spend the largest amount of reasoning on every task.

The goal is to build a working, thoroughly tested, offline STEINS;GATE port efficiently.

**Preserve the engine. Reuse the evidence. Automate the execution. Finish the game.**
