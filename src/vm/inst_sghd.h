#pragma once

#include "vm.h"

// Handlers specific to the STEINS;GATE Steam release (InstructionSet::SGHD).
// Argument layouts follow the CommitteeOfZero/sc3ntist SGHD disassembler
// (reference only). Unless stated otherwise a handler only consumes its
// arguments and logs a stub message once: correct byte consumption, not
// verified game semantics. See docs/steins-gate-blockers.md.

namespace Impacto {

namespace Vm {

// Slots the SGHD compiler never emits: advance past the opcode and log an
// error instead of spinning forever like InstDummy.
VmInstruction(InstUnknownSGHD);
// 00 52, 00 5F, 10 12 (no arguments), 10 40/10 41 (Win32 window opcodes).
VmInstruction(InstNopSGHD);
// 00 4B WaitForSomething004B (no arguments, semantics unknown).
VmInstruction(InstStubSGHD);
// 00 35, 00 41, 01 08, 01 0A, 10 1A, 10 3F: one byte argument.
VmInstruction(InstByteArgStubSGHD);

VmInstruction(InstUnk004CSGHD);
VmInstruction(InstSystemMesSGHD);
VmInstruction(InstUselessJumpSGHD);
VmInstruction(InstUseless0053SGHD);
VmInstruction(InstCallIfFlag);
VmInstruction(InstCallFarIfFlag);
VmInstruction(InstUnk0058SGHD);
VmInstruction(InstUnk0059SGHD);
VmInstruction(InstUnk0106SGHD);
VmInstruction(InstUnk0107SGHD);
VmInstruction(InstCheckpointSGHD);
VmInstruction(InstEncyclopediaSGHD);
VmInstruction(InstPhoneSGHD);

}  // namespace Vm

}  // namespace Impacto
