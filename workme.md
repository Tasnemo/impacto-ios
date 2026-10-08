# impacto-ios

**Porting Committee of Zero's impacto engine to iOS, with the original English Steam release of STEINS;GATE as the first target game.**

## Project Mission

The purpose of `impacto-ios` is to create a native, fully offline iOS port of the open-source [impacto](https://github.com/CommitteeOfZero/impacto) visual novel engine.

The initial target is the original English Steam release of **STEINS;GATE**, not STEINS;GATE ELITE.

The final application should:

- Run directly on modern iPhones.
- Preserve the original game's artwork, dialogue, voice acting, audio, and mechanics.
- Support phone triggers, branching paths, saves, and all endings.
- Function without Steam, Crunchyroll, cloud streaming, or internet access.
- Load game assets from a legitimate Steam installation.
- Be installable through personal sideloading.
- Be developed without requiring the developer to own a Mac.

This is an **engine-porting and compatibility project**, not an effort to recreate the game or independently develop a new visual novel engine.

The primary engineering approach is to preserve impacto's C++ implementation and introduce iOS-specific functionality where required.

Swift, Objective-C++, Metal, Metal-cpp, UIKit, SwiftUI, and other native Apple technologies may be used when technically appropriate.

## Important: Upstream Compatibility Is Incomplete

impacto is an experimental reimplementation of the MAGES. visual novel engine.

Its current development status does not establish full compatibility with the original English Steam release of STEINS;GATE.

The project therefore has two distinct objectives:

1. Establish and improve STEINS;GATE compatibility within impacto on desktop.
2. Port impacto to iOS and reproduce that compatibility on iPhone hardware.

The first objective must be investigated before significant iOS implementation work begins.

Do not assume an existing PC engine implementation can fully execute STEINS;GATE simply because it supports some related games or resource formats.

## Technical Architecture

The proposed architecture is:

```text
+--------------------------------------+
|          Native iOS App              |
|  UIKit / SwiftUI / App Lifecycle      |
|  File Import / Device Integration    |
+--------------------------------------+
                  |
                  v
+--------------------------------------+
|         iOS Platform Layer           |
|  C++ / Objective-C++ / Swift          |
|  Graphics / Audio / Input / Storage   |
+--------------------------------------+
                  |
                  v
+--------------------------------------+
|          impacto C++ Engine          |
|  Script Execution / Resource Loading |
|  Game Logic / State / Save System     |
+--------------------------------------+
                  |
                  v
+--------------------------------------+
|          Original Game Data          |
|  Steam Assets / Scripts / Audio       |
+--------------------------------------+
```

This is a conceptual architecture, not a requirement to introduce unnecessary abstraction layers.

### Language and Performance Policy

Do not rewrite impacto in Swift merely because iOS is an Apple platform.

C++ compiles natively for iOS ARM64.

Choose implementation technologies based on:

- Platform compatibility
- Maintainability
- Existing code reuse
- Memory efficiency
- Cache locality
- Rendering performance
- Dependency requirements
- Measured runtime behavior

Existing C++ functionality should normally be preserved.

Rewrites or replacements are permitted when supported by a clear technical justification.

The graphics backend should be selected after inspecting impacto's existing OpenGL implementation and abstractions.

Do not immediately commit to a complete Metal rewrite.

Investigate existing platform backends and potential reuse first.

## Target Platforms

### Desktop Development

Use Linux or Windows for upstream testing and STEINS;GATE compatibility development.

### iOS

- Architecture: ARM64
- Initial physical-device target: iOS 26.6.2, as reported by the developer
- Proposed minimum deployment target: iOS 18.0, subject to investigation
- Future iOS versions: supported wherever technically possible
- Distribution: personal sideloading
- App Store publication: not required

Verify the precise SDK and operating-system compatibility rather than assuming a reported version is supported.

Do not hardcode compatibility to one iOS release.

Use supported Apple APIs and availability checks where necessary.

Future iOS releases must be tested before compatibility is claimed.

## Development Infrastructure

The developer uses Windows and primarily works through the Amp Code website.

Infrastructure:

| Component | Purpose |
|---|---|
| Amp Code | Development agent |
| Amp Cloud Orbs | Remote coding and Linux tests |
| GitHub | Persistent source code |
| GitHub Actions Linux | Desktop build and regression tests |
| GitHub Actions macOS | Native iOS builds |
| Windows laptop | Steam installation and local asset preparation |
| Physical iPhone | Runtime and installation testing |

Commercial game assets must not be committed to GitHub.

A cloud macOS build does not automatically solve Apple code signing or device installation.

These requirements must be investigated and implemented separately.

---

# Development Execution Strategy

## Read This Section Before Starting Any Work

**This project must be executed through separate, milestone-focused Amp Code threads.**

Each thread has:

- A specific objective
- A recommended reasoning intensity
- Required input documentation
- Defined implementation responsibilities
- Verification requirements
- Required deliverables
- A completion checkpoint

The threads share a GitHub repository, not an assumed conversation history.

Each thread must be capable of starting independently with the committed repository files.

Do not require the user to copy conversation transcripts between threads.

Do not assume a new thread knows what happened in an earlier thread.

## Amp Reasoning Intensities

Amp reasoning intensity should be selected separately for each new thread.

| Mode | Intended Use |
|---|---|
| Ultra | Architecture, complex reverse engineering, major design decisions |
| High | Difficult implementation and debugging |
| Medium | Well-defined implementation tasks, build fixes, CI |
| Low | Documentation, simple isolated changes |

Do not use Ultra indefinitely.

Use the lowest mode appropriate for the engineering difficulty, escalating to a fresh higher-mode thread when necessary.

### Thread Intensity Changes

The agent mode is fixed for a thread.

To change reasoning intensity:

1. Complete or pause the current work at a coherent checkpoint.
2. Commit all validated work.
3. Update the project handoff documents.
4. Push the changes to GitHub.
5. Start a new Amp thread in the same project.
6. Select the new mode before sending its first message.
7. Instruct the agent to read the repository and continue from the documented state.

Do not assume uncommitted files in one Orb exist in a newly created Orb.

The next agent must use the appropriate committed branch or merged repository state.

Amp's native thread referencing and Handoff features may be used as supplementary context, but the project must never depend on them for correctness.

## Git Workflow

Use a private GitHub repository.

The `main` branch should contain the latest validated project state.

Each substantial thread should work on a focused branch, such as:

```text
phase-00-upstream-analysis
phase-01-desktop-baseline
phase-02-steins-compatibility
phase-03-ios-feasibility
phase-04-ios-rendering
```

When the assigned milestone is complete:

1. Run the required tests.
2. Document the results.
3. Commit the changes.
4. Push the branch.
5. Open a pull request or otherwise make the changes reviewable.
6. Merge validated work into the integration branch.
7. Ensure the next thread starts from that updated state.

Never create a new development thread assuming changes from a previous unmerged branch are already present.

Do not commit proprietary game files, signing credentials, or other secrets.

## Permanent Context Files

Maintain:

```text
README.md
docs/
  architecture.md
  compatibility-matrix.md
  decisions.md
  roadmap.md
  handoff.md
  test-results.md
  blockers.md
  threads/
    01-upstream-investigation.md
    02-desktop-baseline.md
    03-desktop-compatibility.md
    ...
```

Not every file needs to be populated immediately.

Create them as the project progresses.

### Handoff Requirements

At the end of each thread, update `docs/handoff.md` with:

```markdown
# Project Handoff

## Current Milestone
What phase has been reached?

## Repository State
Branch, commit, and merged changes.

## Completed Work
What was actually implemented?

## Verification
Which tests ran, and what were their results?

## Known Failures
What is broken or incomplete?

## Architectural Decisions
What decisions were made and why?

## Open Questions
What remains unknown?

## Next Thread
Which thread should run next?

## Recommended Mode
Low / Medium / High / Ultra

## Next Objective
Specific actionable work to perform.
```

Each thread must also produce a more detailed report in `docs/threads/`.

The handoff is not a narrative summary of the conversation. It is a technical description of the repository's actual state.

### Universal Thread Startup Procedure

Every new development thread must:

1. Inspect the checked-out branch and recent Git commits.
2. Read `README.md`.
3. Read `docs/handoff.md`, if present.
4. Read relevant architecture and compatibility documents.
5. Inspect any relevant source code.
6. Verify that prior deliverables actually exist.
7. Check whether previous changes were committed and merged.
8. Identify the current technical blockers.
9. Execute only its assigned milestone.

If documentation disagrees with the source code, investigate the discrepancy rather than assuming the documentation is correct.

### Universal Thread Completion Procedure

Every thread must:

1. Run appropriate tests.
2. Record actual results.
3. Distinguish verified functionality from untested assumptions.
4. Commit changes.
5. Push its branch.
6. Prepare its work for integration.
7. Update `docs/handoff.md`.
8. Update the relevant thread report.
9. Identify the next milestone.

Do not claim physical iPhone testing if only cloud compilation was performed.

Do not proceed to the next milestone automatically unless explicitly instructed.

---

# Sequential Amp Thread Plan

The following threads are the planned execution sequence.

The sequence is conditional: later implementation stages must not proceed blindly if an earlier feasibility gate fails.

Some stages may require additional debugging threads.

The purpose of the sequence is to maintain clear responsibilities rather than artificially restrict how many threads a phase may require.

## Thread 01 — Upstream Architecture and Feasibility

**Mode: ULTRA**

**Type: Research and architecture**

### Objective

Investigate impacto's architecture, existing platform implementations, and STEINS;GATE compatibility.

No significant iOS implementation should occur during this thread.

### Responsibilities

- Clone and inspect the official impacto repository.
- Identify its principal engine subsystems.
- Study its build system.
- Identify existing supported platforms.
- Investigate Android and macOS platform code.
- Examine rendering, audio, input, and filesystem implementations.
- Inspect the official compatibility tracker.
- Determine existing STEINS;GATE support.
- Compare support for the original English Steam release against other releases.
- Study relevant Committee of Zero tools and documentation.
- Identify major technical blockers.
- Evaluate whether impacto remains a sensible foundation.

### Required Deliverables

- Architecture report
- Dependency analysis
- Existing platform comparison
- STEINS;GATE compatibility assessment
- Initial risk assessment
- Desktop testing plan
- Handoff report

### Opening Prompt

> Read README.md and execute Thread 01 only.
>
> Perform a thorough technical investigation of Committee of Zero's impacto engine.
>
> Establish the current level of compatibility with the original English Steam release of STEINS;GATE.
>
> Inspect the upstream architecture, platform implementations, dependencies, script execution, and graphics system.
>
> Do not assume that the game is already playable.
>
> Produce evidence-based reports referencing actual source files and documentation.
>
> Identify the major blockers to desktop compatibility and an eventual iOS port.
>
> Do not implement iOS support.
>
> Commit your reports and update docs/handoff.md.
>
> Stop after Thread 01.

### Exit Criteria

The architecture, current compatibility, and likely implementation difficulty are sufficiently understood to begin desktop testing.

**If the investigation reveals an architectural blocker, stop and report it instead of continuing automatically.**

---

## Thread 02 — Reproducible Desktop Build

**Mode: HIGH**

**Type: Implementation and verification**

### Objective

Build and run the existing impacto engine on a supported desktop platform.

### Responsibilities

- Read Thread 01 findings.
- Clone and configure the required dependencies.
- Establish a reproducible Linux or Windows build.
- Resolve build issues.
- Run upstream tests.
- Confirm engine startup.
- Document compiler and dependency requirements.
- Create desktop CI tests.

### Required Deliverables

- Working desktop build configuration
- Reproducible setup instructions
- CI workflow
- Build logs
- Initial runtime report
- Updated handoff

### Opening Prompt

> Read README.md, docs/handoff.md, and the Thread 01 reports.
>
> Execute Thread 02 only.
>
> Establish a reproducible desktop build of impacto.
>
> Do not modify engine functionality unless necessary to resolve verified build defects.
>
> Add appropriate CI coverage and document all required dependencies.
>
> Confirm actual execution rather than reporting compilation alone.
>
> Commit verified changes, update the handoff, and stop.

### Exit Criteria

The engine builds reproducibly and executes successfully in a supported desktop environment.

---

## Thread 03 — STEINS;GATE Desktop Compatibility

**Mode: ULTRA**

**Type: Compatibility investigation and implementation planning**

### Objective

Determine exactly what prevents the original English Steam release from running fully in impacto.

### Responsibilities

- Compare required Steam assets with supported resource formats.
- Inspect script parsing and execution.
- Identify missing script operations.
- Investigate phone-trigger support.
- Evaluate save/load behavior.
- Identify unsupported media or rendering features.
- Develop minimal reproducible compatibility tests.
- Use the real game files when securely available.
- Document all observed behavior.

### Compatibility Matrix

Track:

| Feature | Status |
|---|---|
| Startup | Unknown |
| Original archives | Unknown |
| Script loading | Unknown |
| English dialogue | Unknown |
| Sprites and backgrounds | Unknown |
| Audio | Unknown |
| Video | Unknown |
| Phone triggers | Unknown |
| Save/load | Unknown |
| Branching routes | Unknown |
| All endings | Unknown |

Statuses must be updated only using actual evidence.

### Opening Prompt

> Read README.md, docs/handoff.md, and the desktop build reports.
>
> Execute Thread 03 only.
>
> Investigate the actual compatibility of the original English Steam release of STEINS;GATE with impacto.
>
> Identify missing engine operations, unsupported assets, script incompatibilities, and incomplete game functionality.
>
> Build focused tests where practical.
>
> Do not confuse the existence of resource parsing tools with full engine compatibility.
>
> Produce a detailed compatibility matrix and prioritized implementation backlog.
>
> Commit findings, update the handoff, and stop.

### Exit Criteria

All major compatibility blockers are understood well enough to estimate and organize the remaining work.

---

## Thread 04 — STEINS;GATE Desktop Implementation

**Mode: HIGH**

**Type: Engine implementation**

### Objective

Implement missing desktop functionality necessary to execute STEINS;GATE correctly.

### Responsibilities

- Follow the compatibility backlog established in Thread 03.
- Reuse existing impacto components.
- Implement missing script behavior.
- Repair incompatible resource handling.
- Address game-specific rendering or media behavior.
- Preserve original branching mechanics.
- Implement or repair phone-trigger functionality.
- Validate save/load behavior.
- Add regression tests.

This is potentially a large phase.

Do not attempt to solve every compatibility problem in a single oversized conversation.

If substantial work remains, create additional focused High-mode threads for individual subsystems.

### Opening Prompt

> Read README.md, docs/handoff.md, and the compatibility backlog.
>
> Execute the next prioritized portion of Thread 04.
>
> Implement the highest-priority verified compatibility blockers for STEINS;GATE within impacto.
>
> Preserve upstream architecture wherever practical.
>
> Add regression tests for every resolved engine defect.
>
> Do not begin iOS porting work.
>
> Complete a coherent subset of the compatibility backlog, commit it, update the handoff, and stop.
>
> If significant compatibility work remains, recommend a follow-up Thread 04 implementation task rather than claiming the whole phase is complete.

### Exit Criteria

Preferred: complete STEINS;GATE desktop compatibility.

Minimum gate for proceeding to iOS implementation:

- Game startup works.
- Dialogue executes.
- Core assets render.
- Audio playback works.
- A phone-trigger interaction functions.
- Save/load works.
- A representative segment of the game is playable.

If full desktop compatibility is incomplete, document exactly what remains.

---

## Thread 05 — iOS Architecture and Build Feasibility

**Mode: ULTRA**

**Type: Platform architecture**

### Objective

Design the smallest maintainable iOS implementation based on the actual state of impacto.

### Responsibilities

- Review all desktop compatibility changes.
- Identify platform-independent engine components.
- Examine rendering dependencies.
- Investigate Metal, Metal-cpp, and translation alternatives.
- Evaluate audio/video library compatibility.
- Determine the required native application shell.
- Establish filesystem integration strategy.
- Identify iOS-specific toolchain requirements.
- Investigate signing and Windows-based installation.
- Define the minimum deployment target.
- Assess compatibility with current iOS releases.

### Opening Prompt

> Read README.md, docs/handoff.md, and the current engine architecture documents.
>
> Execute Thread 05 only.
>
> Design the smallest viable native iOS port of impacto.
>
> Preserve the existing C++ engine.
>
> Evaluate Swift, Objective-C++, Metal, Metal-cpp, and compatible cross-platform dependencies based on technical merit.
>
> Do not immediately rewrite the rendering engine.
>
> Produce a detailed implementation plan covering build tooling, rendering, audio, input, filesystem, lifecycle, and sideloading.
>
> Document tradeoffs and evidence.
>
> Commit the architecture documents, update the handoff, and stop.

### Exit Criteria

A defensible iOS architecture has been selected, with major dependencies and blockers identified.

---

## Thread 06 — Minimal iOS Build and Sideloading

**Mode: HIGH**

**Type: Toolchain and device integration**

### Objective

Compile an impacto-derived iOS app and establish a repeatable installation path.

### Responsibilities

- Configure an iOS ARM64 build.
- Create a minimal application entry point.
- Integrate essential engine initialization.
- Set up GitHub Actions macOS builds.
- Package the application.
- Document signing and provisioning.
- Establish a Windows-compatible sideloading procedure.
- Prepare diagnostic logging.

A minimal app displaying test content is sufficient.

### Opening Prompt

> Read README.md, docs/handoff.md, and the iOS architecture report.
>
> Execute Thread 06 only.
>
> Implement the minimum impacto-based native iOS application and automated GitHub Actions build.
>
> Ensure the output can be packaged for signing and installation.
>
> Investigate a practical Windows-based sideloading procedure.
>
> Do not claim real-device success without evidence from the developer's iPhone.
>
> Commit verified code and update the handoff.
>
> Stop after documenting the current build and installation status.

### Exit Criteria

An iOS application compiles, can be validly signed, and is confirmed to launch on physical iPhone hardware.

If the device validation has not yet occurred, mark the milestone incomplete.

---

## Thread 07 — iOS Rendering Backend

**Mode: HIGH**

**Type: Graphics implementation**

### Objective

Make impacto's renderer functional on iOS.

### Responsibilities

- Implement the renderer selected in Thread 05.
- Preserve original rendering logic where practical.
- Support texture loading.
- Implement sprite composition and transparency.
- Support dialogue rendering.
- Implement necessary scene transitions.
- Preserve aspect ratio.
- Test memory behavior.
- Add graphics regression tests.

Do not introduce unnecessary optimization before obtaining correct output.

### Opening Prompt

> Read README.md, docs/handoff.md, and the chosen rendering architecture.
>
> Execute Thread 07 only.
>
> Implement the iOS rendering backend for impacto.
>
> Prioritize correctness and reuse of existing engine code.
>
> Verify rendering using distributable test assets.
>
> Keep graphics changes isolated from game-specific compatibility logic.
>
> Document any unverified device behavior.
>
> Commit code and test results, update the handoff, and stop.

### Exit Criteria

The iOS engine correctly renders representative visual novel scenes.

---

## Thread 08 — iOS Audio, Input, and Lifecycle

**Mode: HIGH**

**Type: Platform integration**

### Objective

Implement the remaining platform-dependent features necessary for gameplay.

### Responsibilities

- Adapt audio playback.
- Integrate video playback.
- Implement touch input translation.
- Adapt filesystem access.
- Support local game-data importing.
- Handle application suspension and restoration.
- Handle audio interruptions.
- Verify persistent storage.
- Test resource cleanup and memory behavior.

### Opening Prompt

> Read README.md, docs/handoff.md, and the platform architecture documents.
>
> Execute Thread 08 only.
>
> Implement the remaining iOS platform systems required by impacto, including audio, video, input, filesystem integration, and application lifecycle management.
>
> Preserve existing game logic and interfaces.
>
> Test each subsystem independently before integration.
>
> Document actual verification results.
>
> Commit verified changes, update the handoff, and stop.

### Exit Criteria

The port can render, play audio, accept touch input, read local resources, and handle normal iOS application lifecycle events.

---

## Thread 09 — STEINS;GATE iOS Integration

**Mode: HIGH**

**Type: Full-game integration**

### Objective

Run the desktop-compatible STEINS;GATE implementation on iOS.

### Responsibilities

- Import original game data.
- Validate resource loading.
- Confirm dialogue and script execution.
- Verify scene transitions.
- Test audio and video.
- Test phone-trigger mechanics.
- Validate saves.
- Compare desktop and iOS behavior.
- Investigate platform-specific regressions.

Do not rewrite game logic for iOS where existing desktop functionality can be reused.

### Opening Prompt

> Read README.md, docs/handoff.md, and the latest STEINS;GATE compatibility matrix.
>
> Execute Thread 09.
>
> Integrate the desktop-compatible STEINS;GATE implementation with the native iOS engine.
>
> Preserve the original game scripts, assets, branching logic, and phone-trigger mechanics.
>
> Identify differences between desktop and iOS behavior.
>
> Resolve verified platform-specific regressions.
>
> Work incrementally and add regression tests.
>
> Commit verified work and update the handoff.
>
> If complete compatibility requires additional threads, document the remaining tasks instead of claiming completion.

### Exit Criteria

The original game executes correctly on iPhone, including its core mechanics.

Full-game completion must be validated separately.

---

## Thread 10 — Optimization, Offline Testing, and Release

**Mode: MEDIUM**

**Type: Testing, performance, and release engineering**

### Objective

Produce a reliable, maintainable, personally sideloadable release.

### Responsibilities

- Profile CPU and GPU performance.
- Investigate memory usage.
- Optimize asset loading and texture caching.
- Validate original visual fidelity.
- Refine touch controls.
- Test all routes and endings.
- Verify save/load.
- Test airplane-mode startup.
- Test force-close and restart.
- Test device restart.
- Validate signing renewal and application updates.
- Document reproducible release builds.

Escalate isolated complex performance or engine defects into new High-mode threads rather than attempting major architectural work in Medium.

### Opening Prompt

> Read README.md, docs/handoff.md, the compatibility matrix, and all current release test results.
>
> Execute Thread 10.
>
> Audit the iOS port for correctness, offline reliability, memory efficiency, usability, and release readiness.
>
> Prioritize verified defects and measurable performance problems.
>
> Confirm that the app does not require Steam, Crunchyroll, or network authentication.
>
> Do not claim complete game compatibility without documented testing of all routes and endings.
>
> Prepare release instructions, signing documentation, test results, and a final compatibility report.
>
> Commit validated changes and update the handoff.

### Exit Criteria

A reproducible, signed, sideloadable application runs the original STEINS;GATE offline with the required functionality.

---

# Handling Failed Milestones

Not every milestone will succeed in one thread.

If a task remains incomplete, do not automatically proceed to the next numbered thread.

Instead:

1. Record the precise blocker.
2. Preserve verified progress.
3. Commit and push the current state.
4. Update the handoff.
5. Create a focused continuation thread.
6. Select its reasoning intensity based on the remaining difficulty.
7. Continue until the necessary gate is met.

Example:

```text
Thread 04 — High
    |
    +-- Phone triggers remain broken
    |
    v
Thread 04A — Ultra
    |
    +-- Investigate script state machine
    |
    v
Thread 04B — High
    |
    +-- Implement and test correction
    |
    v
Thread 05 — Ultra
```

There is no requirement to force a complex milestone into a single agent conversation.

## When to Escalate Intensity

Use a new Ultra thread when:

- An architectural assumption is invalidated.
- Reverse engineering exposes undocumented behavior.
- Several subsystems interact in unexpected ways.
- A major compatibility issue cannot be isolated.
- A design decision could require extensive rework.

Use High for implementing the chosen solution.

Use Medium for bounded build fixes and routine validation.

Do not restart a thread merely because an individual compiler error occurs.

Thread changes should correspond to meaningful changes in scope or reasoning requirements.

---

# Repository Context Is Authoritative

Amp threads may have different conversational contexts and may run in separate cloud environments.

Therefore, the authoritative project state is:

1. Committed source code
2. Automated test results
3. Compatibility matrix
4. Architecture and decision records
5. Handoff document
6. Current implementation backlog

A previous Amp thread's conversation is supplementary information, not the required source of truth.

If a new agent cannot understand what to do from the repository alone, the previous handoff is incomplete.

## General Agent Rules

Every agent must:

- Inspect before implementing.
- Preserve existing functionality.
- Avoid unnecessary rewrites.
- Document architectural decisions.
- Run relevant tests.
- Report failures accurately.
- Avoid publishing commercial assets.
- Avoid committing credentials.
- Verify source-level claims.
- Distinguish compilation from runtime success.
- Distinguish partial compatibility from full game completion.
- Keep changes reviewable.
- Update project documentation.
- Leave a usable handoff.

---

# Commercial Game Assets

This repository must not redistribute STEINS;GATE's commercial assets.

Users must supply files from a legitimately obtained installation.

The intended workflow is:

1. Install STEINS;GATE through Steam on Windows.
2. Execute a local asset validation or packaging tool.
3. Transfer required resources to the iPhone.
4. Import files into the app's local storage.
5. Run the game through impacto.

Do not add game assets to public or private Git repositories unnecessarily.

Avoid sending entire commercial installations to third-party cloud environments when local validation is sufficient.

Use legally distributable samples for CI wherever possible.

---

# Final Acceptance Criteria

- [ ] impacto builds reproducibly on desktop.
- [ ] STEINS;GATE's actual desktop compatibility is documented.
- [ ] The original English Steam release is playable through impacto.
- [ ] The engine builds for iOS ARM64.
- [ ] The application launches on an iPhone.
- [ ] Original graphics render correctly.
- [ ] Audio and video playback function.
- [ ] Touch controls work.
- [ ] Game data imports successfully.
- [ ] Phone triggers function correctly.
- [ ] Save/load persists correctly.
- [ ] All story routes and endings work.
- [ ] The app launches without an internet connection.
- [ ] The app works after a force-close and restart.
- [ ] The app can be signed and installed from a Windows-based workflow.
- [ ] The build is reproducible through GitHub Actions.
- [ ] Significant upstream modifications are documented.
- [ ] Repository documentation supports independent development threads.

## Definition of Done

The project is complete when the original English Steam release of STEINS;GATE can be played from beginning to end through impacto on a modern iPhone, offline, with its original content and game mechanics intact.

The resulting implementation should remain a maintainable iOS port of impacto, allowing other compatible visual novels to be supported in the future.

**Prove desktop compatibility. Port the engine. Integrate the game. Play offline.**

---

# References and Attribution

- [Committee of Zero — impacto](https://github.com/CommitteeOfZero/impacto)
- [Committee of Zero — sc3tools](https://github.com/CommitteeOfZero/sc3tools)
- [Committee of Zero — MAGES. Engine Compendium](https://github.com/CommitteeOfZero/compendium)
- [Amp Documentation](https://ampcode.com/docs)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

impacto is developed by Committee of Zero.

This project must preserve the upstream license and all relevant third-party notices.

STEINS;GATE and its commercial assets remain the intellectual property of their respective rights holders.

This project is not affiliated with Committee of Zero or the game's rights holders.
