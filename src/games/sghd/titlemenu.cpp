#include "titlemenu.h"

#include "../../inputsystem.h"
#include "../../mem.h"
#include "../../profile/games/sghd/titlemenu.h"
#include "../../profile/scriptvars.h"
#include "../../profile/game.h"
#include "../../profile/fonts.h"
#include "../../renderer/renderer.h"
#include "../../text/text.h"
#include "../../vm/interface/input.h"

#include <array>
#include <cstdint>

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

// The original Steam title is assembled from TITLE_CHIP.DDS and a Bink 2
// animated movie. The owner's reference screenshots confirm the atlas
// backdrop and menu chip locations; the movie is not yet supported.
static void DrawFallbackText(const char* text, glm::vec2 center,
                             float fontSize, uint32_t color) {
  auto const fontIt = Profile::Fonts.find("Default");
  if (fontIt == Profile::Fonts.end() || !fontIt->second) return;
  Fonts::Font* font = fontIt->second;
  auto const glyphs = TextLayoutPlainString(
      text, *font, fontSize, {color, 0x101827}, 1.0f, center,
      TextAlignment::Center);
  font->DrawProcessedText(glyphs, 1.0f, Fonts::RendererOutlineMode::Full);
}

void TitleMenu::Render() {
  if (State != Shown) return;

  float const w = Profile::Game::DesignWidth;
  float const h = Profile::Game::DesignHeight;

  // TITLE_CHIP.DDS region 0,0,1920,1080 is the real Steam backdrop:
  // grid, logo, ornamental gears and copyright are already embedded.
  if (PreviewBackgroundSprite) {
    Renderer->DrawSprite(*PreviewBackgroundSprite, RectF(0, 0, w, h));
  } else {
    // Visible only when the Steam texture isn't present.
    Renderer->DrawQuad(RectF(0, 0, w, h),
                       glm::vec4(0.025f, 0.04f, 0.075f, 1.0f));
    DrawFallbackText("STEINS;GATE", {w * 0.5f, h * 0.3f},
                     82.0f, 0xF5F5EF);
  }

  if (!InMainMenu) {
    // Reference Steam screenshot: a small, muted prompt above the logo,
    // not a full-width dialog or a compatibility-preview banner.
    DrawFallbackText("Press Enter", {w * 0.508f, h * 0.586f},
                     35.0f, 0xB8A7A0);
    return;
  }

  constexpr std::array<const char*, 5> labels{
      "START", "LOAD", "EXTRA", "CONFIG", "HELP"};

  for (size_t i = 0; i < Items.size(); ++i) {
    Item const& item = Items[i];
    RectF const& bounds = item.Bounds;
    bool const selected = (int)i == Cursor && item.Enabled;

    // The reference Steam screenshot has a thin orange stripe beside every
    // menu chip, not a thick border around the selected item's rectangle.
    Renderer->DrawQuad(
        RectF(bounds.X + 4.0f, bounds.Y + 4.0f, 8.0f, 46.0f),
        selected ? glm::vec4(1.0f, 0.43f, 0.06f, 1.0f)
                 : glm::vec4(0.96f, 0.39f, 0.05f, 0.97f));

    // The owner's side-by-side screenshots established that the right-hand
    // column of atlas crops contains dark text on pale chips, matching the
    // Steam title. The left column appeared white on gold in Round 8.
    std::optional<Sprite> const& sprite =
        item.SelectedSprite ? item.SelectedSprite : item.NormalSprite;
    if (sprite) {
      // Keep hitboxes at their measured positions; offset only the art so
      // its left edge follows the orange stripe, like the Steam version.
      Renderer->DrawSprite(
          *sprite, bounds.GetPos() + glm::vec2(20.0f, 0.0f));
    } else if (i < labels.size()) {
      // No duplicate text when the native Steam chips are available.
      DrawFallbackText(labels[i],
                       {bounds.X + bounds.Width * 0.5f, bounds.Y},
                       34.0f, item.Enabled ? 0xFFFFFF : 0xB9C2CF);
    }

    if (selected && CursorSprite)
      Renderer->DrawSprite(*CursorSprite,
                           bounds.GetPos() + CursorOffset);
  }

  // Reference Steam menu shows a compact key legend at lower left.
  // (Its original tiny controller icons are not yet mapped.)
  DrawFallbackText("SELECT    ENTER    BACK",
                   {w * 0.165f, h - 67.0f}, 20.0f, 0xFFFFFF);
}

}  // namespace SGHD
}  // namespace UI
}  // namespace Impacto
