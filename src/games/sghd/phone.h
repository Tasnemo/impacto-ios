#pragma once

#include <array>
#include <cstdint>

namespace Impacto {
namespace SGHD {
namespace Phone {

// Per-item attribute bits driven by 10 37 sub-types 0x00-0x03 in the Steam
// scripts (docs/phone-protocol.md). An "item" is the expression argument
// (ids up to ~650 in the census; mails/contacts, exact meaning unknown); the
// byte argument selects one of bits 0-4. Inferred semantics (Thread 06):
//   0x00 B E    set bit B of item E
//   0x01 B E    clear bit B of item E
//   0x02 B E L  jump to L if bit B of item E is set
//   0x03 B E L  jump to L if bit B of item E is clear
// The engine-side store is fork-native (saved per slot,
// docs/sghd-save-format.md); where the Steam executable keeps these bits is
// unknown.
constexpr int ItemCount = 1024;
inline std::array<uint8_t, ItemCount> ItemBits{};

inline bool ValidItem(int item, int bit) {
  return item >= 0 && item < ItemCount && bit >= 0 && bit < 8;
}

}  // namespace Phone
}  // namespace SGHD
}  // namespace Impacto
