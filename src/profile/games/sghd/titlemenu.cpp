#include "titlemenu.h"

#include "../../profile_internal.h"
#include "../../../game.h"
#include "../../../log.h"
#include "../../../ui/ui.h"
#include "../../../games/sghd/titlemenu.h"

namespace Impacto {
namespace Profile {
namespace SGHD {
namespace TitleMenu {

// Reads the members of root.TitleMenu (already pushed by
// Profile::TitleMenu::Configure). Item sprites and the cursor sprite are
// optional: they stay unset until the TITLE_CHIP.DDS regions are named.
void Configure() {
  MainMenuMode = EnsureGetMember<int>("MainMenuMode");
  auto const ids = EnsureGetMember<std::vector<int>>("ItemChoiceIds");
  auto const enabled = EnsureGetMember<std::vector<int>>("ItemEnabled");
  auto const bounds = EnsureGetMember<std::vector<RectF>>("ItemBounds");
  auto const sprites = TryGetMember<std::vector<Sprite>>("ItemSprites")
                           .value_or(std::vector<Sprite>{});
  auto const selected = TryGetMember<std::vector<Sprite>>("ItemSelectedSprites")
                            .value_or(std::vector<Sprite>{});
  if (enabled.size() != ids.size() || bounds.size() != ids.size() ||
      (!sprites.empty() && sprites.size() != ids.size()) ||
      (!selected.empty() && selected.size() != ids.size())) {
    ImpLog(LogLevel::Fatal, LogChannel::Profile,
           "TitleMenu: item arrays must have the same length\n");
    Game::Shutdown();
  }

  Items.clear();
  for (size_t i = 0; i < ids.size(); i++) {
    Item item;
    item.ChoiceId = ids[i];
    item.Enabled = enabled[i] != 0;
    item.Bounds = bounds[i];
    if (!sprites.empty()) item.NormalSprite = sprites[i];
    if (!selected.empty()) item.SelectedSprite = selected[i];
    Items.push_back(item);
  }
  PreviewBackgroundSprite = TryGetMember<Sprite>("PreviewBackgroundSprite");
  CursorSprite = TryGetMember<Sprite>("CursorSprite");
  CursorOffset =
      TryGetMember<glm::vec2>("CursorOffset").value_or(glm::vec2(0.0f));

  auto drawType = EnsureGetMember<Game::DrawComponentType>("DrawType");
  UI::TitleMenuPtr = new UI::SGHD::TitleMenu();
  UI::Menus[drawType].push_back(UI::TitleMenuPtr);
}

}  // namespace TitleMenu
}  // namespace SGHD
}  // namespace Profile
}  // namespace Impacto
