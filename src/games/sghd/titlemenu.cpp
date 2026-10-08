#include "titlemenu.h"

#include "../../inputsystem.h"
#include "../../mem.h"
#include "../../profile/games/sghd/titlemenu.h"
#include "../../profile/scriptvars.h"
#include "../../renderer/renderer.h"
#include "../../vm/interface/input.h"

namespace Impacto {
namespace UI {
namespace SGHD {

using namespace Impacto::Profile::SGHD::TitleMenu;
using namespace Impacto::Profile::ScriptVars;
using namespace Impacto::Vm::Interface;

void TitleMenu::Show() {
  if (State == Hidden) State = Shown;
}

void TitleMenu::Hide() {
  if (State == Shown) State = Hidden;
}

void TitleMenu::Update(float dt) {
  if (GetFlag(SF_TITLEMODE)) {
    Show();
  } else {
    Hide();
  }
  if (PollFramesLeft <= 0) return;
  PollFramesLeft--;
  bool const mainMenu = ScrWork[SW_TITLEMODE] == MainMenuMode;
  InMainMenu = mainMenu;
  if (Pending) return;
  if (std::optional<int> choice = ReadInput(mainMenu))
    Pending = Decision{mainMenu, *choice};
}

void TitleMenu::ResetCursor() {
  Pending.reset();
  Cursor = 0;
  while (Cursor < (int)Items.size() - 1 && !Items[Cursor].Enabled) Cursor++;
}

std::optional<int> TitleMenu::Poll(bool mainMenuMode) {
  PollFramesLeft = PollFrames;
  if (!Pending) return std::nullopt;
  Decision const decision = *Pending;
  Pending.reset();
  // a confirm latched in the other phase belongs to a poll that has ended
  if (decision.MainMenu != mainMenuMode) return std::nullopt;
  return decision.Choice;
}

void TitleMenu::MoveCursor(int direction) {
  int const count = (int)Items.size();
  for (int step = 1; step < count; step++) {
    int const next = Cursor + direction * step;
    if (next < 0 || next >= count) return;
    if (Items[next].Enabled) {
      Cursor = next;
      return;
    }
  }
}

std::optional<int> TitleMenu::ReadInput(bool mainMenuMode) {
  bool const confirm = (PADinputButtonWentDown & PAD1A) != 0;
  bool const click = (PADinputMouseWentDown & PAD1A) != 0;

  if (!mainMenuMode) {
    if (confirm || click) return -1;
    return std::nullopt;
  }

  if (Items.empty()) return std::nullopt;
  if (PADinputButtonRepeatDown & PAD1DOWN) MoveCursor(1);
  if (PADinputButtonRepeatDown & PAD1UP) MoveCursor(-1);

  std::optional<int> hovered;
  for (int i = 0; i < (int)Items.size(); i++) {
    if (Items[i].Enabled && Items[i].Bounds.ContainsPoint(Input::CurMousePos))
      hovered = i;
  }
  if (hovered && Input::CurMousePos != Input::PrevMousePos) Cursor = *hovered;

  if (click && hovered) {
    Cursor = *hovered;
    return Items[Cursor].ChoiceId;
  }
  if (confirm && Items[Cursor].Enabled) return Items[Cursor].ChoiceId;
  return std::nullopt;
}

void TitleMenu::Render() {
  if (State != Shown || !InMainMenu) return;
  for (int i = 0; i < (int)Items.size(); i++) {
    Item const& item = Items[i];
    std::optional<Sprite> const& sprite = i == Cursor && item.SelectedSprite
                                              ? item.SelectedSprite
                                              : item.NormalSprite;
    if (sprite) Renderer->DrawSprite(*sprite, item.Bounds.GetPos());
    if (i == Cursor && CursorSprite)
      Renderer->DrawSprite(*CursorSprite, item.Bounds.GetPos() + CursorOffset);
  }
}

}  // namespace SGHD
}  // namespace UI
}  // namespace Impacto
