#include "inst_sghd.h"

#include "inst_macros.inc"

#include <string>
#include <unordered_set>

#include "expression.h"
#include "../log.h"
#include "../mem.h"
#include "../profile/scriptvars.h"
#include "../profile/vm.h"
#include "../games/sghd/phone.h"

namespace Impacto {

namespace Vm {

using namespace Impacto::Profile::ScriptVars;

// Log each distinct stub (instruction + subtype) once per run. Not
// ImpLogSlow: Release builds must still report which unverified SGHD
// instructions a real script reaches (Thread 04 Task 5 input).
static void StubOnce(const std::string& name, const std::string& args = "") {
  static std::unordered_set<std::string> seen;
  if (!seen.insert(name).second) return;
  ImpLog(LogLevel::Warning, LogChannel::VMStub,
         "STUB instruction {:s}({:s}) [SGHD, logged once]\n", name, args);
}

VmInstruction(InstUnknownSGHD) {
  StartInstruction;
  uint8_t const group = _oldIp[0] & 0x7F;
  uint8_t const opcode = _oldIp[1];
  static std::unordered_set<uint16_t> seen;
  if (seen.insert((uint16_t)(group << 8 | opcode)).second) {
    ImpLog(LogLevel::Error, LogChannel::VM,
           "Opcode {:02x}:{:02x} is not part of the SGHD instruction set; "
           "skipping 2 bytes (stream may desync). Address: {:#0x} "
           "ScriptBuffer: {:d}\n",
           group, opcode, thread->IpOffset - 2, thread->ScriptBufferId);
  }
}

VmInstruction(InstNopSGHD) { StartInstruction; }

VmInstruction(InstStubSGHD) {
  StartInstruction;
  StubOnce(fmt::format("Unk{:02X}{:02X}", _oldIp[0] & 0x7F, _oldIp[1]));
}

VmInstruction(InstByteArgStubSGHD) {
  StartInstruction;
  PopUint8(arg);
  StubOnce(fmt::format("Unk{:02X}{:02X}", _oldIp[0] & 0x7F, _oldIp[1]),
           fmt::format("arg: {:d}", arg));
}

VmInstruction(InstUnk004CSGHD) {
  StartInstruction;
  PopUint8(type);
  int arg = 0;
  if (type == 0) arg = ExpressionEval(thread);
  StubOnce(fmt::format("Unk004C(type: {:d})", type),
           fmt::format("arg: {:d}", arg));
}

// 00 43. SGHD modes 0A-11 have the same argument shapes as impacto's
// SystemMes modes 0-7 (0C: expression, 0D/0E: string id), but the mapping
// is unverified, so nothing is shown yet.
VmInstruction(InstSystemMesSGHD) {
  StartInstruction;
  PopUint8(mode);
  int arg = 0;
  switch (mode) {
    case 0x02:
    case 0x0C:
      arg = ExpressionEval(thread);
      break;
    case 0x03:
    case 0x04:
    case 0x0D:
    case 0x0E: {
      PopUint16(stringId);
      arg = stringId;
    } break;
    case 0x00:
    case 0x01:
    case 0x05:
    case 0x06:
    case 0x07:
    case 0x0A:
    case 0x0B:
    case 0x0F:
    case 0x10:
    case 0x11:
      break;
    default:
      ImpLog(LogLevel::Error, LogChannel::VM,
             "SystemMes: unknown SGHD mode {:#x}\n", mode);
      return;
  }
  StubOnce(fmt::format("SystemMes(mode: {:#x})", mode),
           fmt::format("arg: {:d}", arg));
}

// 00 50 "UselessJump": condition byte, then 0, 2 or 3 local labels. The
// branch is not taken (sc3ntist and the Steam build treat it as inert).
VmInstruction(InstUselessJumpSGHD) {
  StartInstruction;
  PopUint8(condition);
  int labels = 0;
  if (condition == 0 || condition == 2) labels = 2;
  if (condition == 3) labels = 3;
  thread->IpOffset += 2 * labels;
  StubOnce(fmt::format("UselessJump(condition: {:d})", condition));
}

VmInstruction(InstUseless0053SGHD) {
  StartInstruction;
  PopUint8(arg1);
  PopExpression(arg2);
  PopUint16(label);
  StubOnce("Useless0053", fmt::format("arg1: {:d}, arg2: {:d}, label: {:d}",
                                      arg1, arg2, label));
}

static void PushCall(Sc3VmThread* thread, uint16_t retNum) {
  if (Profile::Vm::UseReturnIds) {
    thread->ReturnIds[thread->CallStackDepth] = retNum;
  } else {
    thread->ReturnAddresses[thread->CallStackDepth] = thread->IpOffset;
  }
  thread->ReturnScriptBufferIds[thread->CallStackDepth++] =
      thread->ScriptBufferId;
}

// 00 54: condition byte, flag expression, local label, return-address id.
// Calls the label when the flag's state equals the condition, the same
// test InstFlagOnJump and InstReturnIfFlag use.
VmInstruction(InstCallIfFlag) {
  StartInstruction;
  PopUint8(condition);
  PopExpression(flagId);
  PopLocalLabel(labelAdr);
  PopUint16(retNum);
  if (GetFlag(flagId) != (bool)condition) return;
  if (thread->CallStackDepth == MaxCallStackDepth) {
    ImpLog(LogLevel::Error, LogChannel::VM,
           "CallIfFlag error, call stack overflow.\n");
    return;
  }
  PushCall(thread, retNum);
  thread->IpOffset = labelAdr;
}

// 00 56: condition byte, flag expression, far label (script buffer
// expression + label id), return-address id. The far label is only resolved
// when the call is taken, because the target buffer may not be loaded.
VmInstruction(InstCallFarIfFlag) {
  StartInstruction;
  PopUint8(condition);
  PopExpression(flagId);
  PopExpression(scriptBufferId);
  PopUint16(labelNum);
  PopUint16(retNum);
  if (GetFlag(flagId) != (bool)condition) return;
  if (thread->CallStackDepth == MaxCallStackDepth) {
    ImpLog(LogLevel::Error, LogChannel::VM,
           "CallFarIfFlag error, call stack overflow.\n");
    return;
  }
  PushCall(thread, retNum);
  thread->IpOffset = ScriptGetLabelAddress(scriptBufferId, labelNum);
  thread->ScriptBufferId = scriptBufferId;
}

VmInstruction(InstUnk0058SGHD) {
  StartInstruction;
  PopUint8(type);
  int const count = (type == 2 || type == 3) ? 4 : 1;
  for (int i = 0; i < count; i++) ExpressionEval(thread);
  PopUint16(label);
  StubOnce(fmt::format("Unk0058(type: {:d})", type),
           fmt::format("label: {:d}", label));
}

VmInstruction(InstUnk0059SGHD) {
  StartInstruction;
  PopUint8(arg1);
  PopExpression(arg2);
  PopExpression(arg3);
  PopUint16(label);
  StubOnce("Unk0059", fmt::format("arg1: {:d}, arg2: {:d}, arg3: {:d}, "
                                  "label: {:d}",
                                  arg1, arg2, arg3, label));
}

VmInstruction(InstUnk0106SGHD) {
  StartInstruction;
  PopUint8(type);
  switch (type) {
    case 0: {
      PopExpression(arg1);
      PopExpression(arg2);
      StubOnce("Unk0106NoStore",
               fmt::format("arg1: {:d}, arg2: {:d}", arg1, arg2));
    } break;
    case 1: {
      PopExpression(dest);
      PopExpression(arg1);
      PopExpression(arg2);
      StubOnce("Unk0106Store", fmt::format("dest: {:d}, arg1: {:d}, arg2: {:d}",
                                           dest, arg1, arg2));
    } break;
    default:
      ImpLog(LogLevel::Error, LogChannel::VM,
             "Unk0106: unknown SGHD type {:d}\n", type);
      break;
  }
}

VmInstruction(InstUnk0107SGHD) {
  StartInstruction;
  PopExpression(arg1);
  PopExpression(arg2);
  PopExpression(unused);
  StubOnce("Unk0107", fmt::format("arg1: {:d}, arg2: {:d}", arg1, arg2));
}

// 01 09 GroupCheckpoint. Checkpoint ids are not used yet (M5).
VmInstruction(InstCheckpointSGHD) {
  StartInstruction;
  PopUint8(type);
  int checkpointId = -1;
  int arg = 0;
  switch (type) {
    case 0: {
      PopUint16(id);
      checkpointId = id;
    } break;
    case 1: {
      PopUint16(id);
      checkpointId = id;
      arg = ExpressionEval(thread);
    } break;
    case 2:
      arg = ExpressionEval(thread);
      break;
    default:
      break;
  }
  StubOnce(fmt::format("Checkpoint(type: {:d})", type),
           fmt::format("checkpointId: {:d}, arg: {:d}", checkpointId, arg));
}

// 10 27: type byte, tip expression, flag expression when type == 1.
// sc3ntist calls type 0 "OpenTip"; unlocking tips needs real tips data, so
// it is not wired to the tips system until it can be verified.
VmInstruction(InstEncyclopediaSGHD) {
  StartInstruction;
  PopUint8(type);
  PopExpression(tip);
  int flag = -1;
  if (type == 1) flag = ExpressionEval(thread);
  StubOnce(fmt::format("Encyclopedia(type: {:d})", type),
           fmt::format("tip: {:d}, flag: {:d}", tip, flag));
}

// 10 37 phone. Consumes every subtype the SGHD compiler emits; the phone
// itself is Thread 04 Task 7 (H1).
VmInstruction(InstPhoneSGHD) {
  StartInstruction;
  PopUint8(type);
  std::string args;
  switch (type) {
    case 0x00:
    case 0x01: {
      // set / clear item attribute bit (games/sghd/phone.h)
      PopUint8(bit);
      PopExpression(item);
      if (!SGHD::Phone::ValidItem(item, bit)) {
        ImpLog(LogLevel::Error, LogChannel::VM,
               "Phone: item {:d} bit {:d} out of range\n", item, bit);
        return;
      }
      uint8_t& bits = SGHD::Phone::ItemBits[item];
      if (type == 0x00)
        bits |= (uint8_t)(1u << bit);
      else
        bits &= (uint8_t) ~(1u << bit);
      ImpLog(LogLevel::Debug, LogChannel::VM,
             "Phone: item {:d} bit {:d} {:s}\n", item, bit,
             type == 0x00 ? "set" : "cleared");
      return;
    }
    case 0x02:
    case 0x03: {
      // jump if item attribute bit set (0x02) / clear (0x03)
      PopUint8(bit);
      PopExpression(item);
      PopUint16(labelNum);
      if (type == 0x03) {
        // Kept from InstPhoneSG (sgps3) for parity.
        ScrWork[SW_PHONE_DISP_CT] = GetFlag(SF_Phone_Open) ? 20 : 0;
      }
      if (!SGHD::Phone::ValidItem(item, bit)) {
        ImpLog(LogLevel::Error, LogChannel::VM,
               "Phone: item {:d} bit {:d} out of range\n", item, bit);
        return;
      }
      bool const isSet = (SGHD::Phone::ItemBits[item] >> bit) & 1;
      if (isSet == (type == 0x02)) {
        thread->IpOffset =
            ScriptGetLabelAddress(thread->ScriptBufferId, labelNum);
      }
      return;
    }
    case 0x04:
      thread->IpOffset += 6 * 2;  // six local labels
      break;
    case 0x0F:
    case 0x10:
    case 0x1A: {
      PopExpression(arg1);
      args = fmt::format("arg1: {:d}", arg1);
    } break;
    case 0x12: {
      PopExpression(arg1);
      PopExpression(arg2);
      args = fmt::format("arg1: {:d}, arg2: {:d}", arg1, arg2);
    } break;
    case 0x14:
    case 0x15: {
      PopExpression(arg1);
      PopExpression(arg2);
      PopExpression(arg3);
      PopExpression(arg4);
      args = fmt::format("arg1: {:d}, arg2: {:d}, arg3: {:d}, arg4: {:d}", arg1,
                         arg2, arg3, arg4);
    } break;
    case 0x05:
    case 0x06:
    case 0x07:
    case 0x08:
    case 0x09:
    case 0x0A:
    case 0x11:
    case 0x13:
    case 0x16:
    case 0x17:
    case 0x18:
    case 0x19:
    case 0x1E:  // no arguments (census: _SYSTEM.SCX, next instruction at +3)
      break;
    default:
      ImpLog(LogLevel::Error, LogChannel::VM,
             "Phone: unknown SGHD subtype {:#x}\n", type);
      return;
  }
  StubOnce(fmt::format("Phone(type: {:#x})", type), args);
}

VmInstruction(InstUnk103ASGHD) {
  StartInstruction;
  PopExpression(arg1);
  PopExpression(arg2);
  PopExpression(arg3);
  PopExpression(arg4);
  PopExpression(arg5);
  PopExpression(arg6);
  StubOnce("Unk103A", fmt::format("args: {:d}, {:d}, {:d}, {:d}, {:d}, {:d}",
                                  arg1, arg2, arg3, arg4, arg5, arg6));
}

}  // namespace Vm

}  // namespace Impacto
