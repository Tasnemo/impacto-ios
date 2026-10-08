#pragma once

#include <optional>
#include <vector>

#include "../../../spritesheet.h"

namespace Impacto {
namespace Profile {
namespace SGHD {
namespace TitleMenu {

// One main-menu entry. Bounds is the hit box in design coordinates (and the
// top-left of its sprite); ChoiceId is written to SW_TITLECUR on confirm.
struct Item {
  int ChoiceId = 0;
  bool Enabled = false;
  RectF Bounds;
  std::optional<Sprite> NormalSprite;
  std::optional<Sprite> SelectedSprite;
};

inline int MainMenuMode = 3;
inline std::vector<Item> Items;
inline std::optional<Sprite> CursorSprite;
inline glm::vec2 CursorOffset{0.0f};

void Configure();

}  // namespace TitleMenu
}  // namespace SGHD
}  // namespace Profile
}  // namespace Impacto
