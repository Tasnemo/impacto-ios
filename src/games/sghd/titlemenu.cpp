#include "titlemenu.h"

#include "../../inputsystem.h"
#include "../../mem.h"
#include "../../profile/games/sghd/titlemenu.h"
#include "../../profile/scriptvars.h"
#include "../../profile/game.h"
#include "../../profile/fonts.h"
#include "../../renderer/renderer.h"
#include "../../text/text.h"

#include <algorithm>
#include <array>
#include <cstdint>
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

// The original Steam title is assembled from TITLE_CHIP.DDS regions and a
// Bink 2 movie. Until those assets are mapped, render an honest, navigable
// fallback instead of making the functioning title protocol invisible.
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

  bool const hasMenuArtwork =
      !Items.empty() &&
      std::all_of(Items.begin(), Items.end(),
                  [](Item const& item) { return item.NormalSprite.has_value(); });

  if (!hasMenuArtwork) {
    float const w = Profile::Game::DesignWidth;
    float const h = Profile::Game::DesignHeight;
    Renderer->DrawQuad(RectF(0.0f, 0.0f, w, h),
                       glm::vec4(0.025f, 0.04f, 0.075f, 1.0f));
    Renderer->DrawQuad(RectF(0.0f, h * 0.22f, w, 3.0f),
                       glm::vec4(0.78f, 0.36f, 0.16f, 1.0f));
    Renderer->DrawQuad(RectF(w * 0.08f, h * 0.32f, 6.0f, h * 0.34f),
                       glm::vec4(0.78f, 0.36f, 0.16f, 1.0f));

    DrawFallbackText("STEINS;GATE", {w * 0.5f, h * 0.31f},
                     82.0f, 0xF5F5EF);
    DrawFallbackText("COMPATIBILITY PREVIEW", {w * 0.5f, h * 0.42f},
                     29.0f, 0xBFC9D8);

    if (!InMainMenu) {
      Renderer->DrawQuad(RectF(w * 0.27f, h * 0.7f, w * 0.46f, 80.0f),
                         glm::vec4(0.3f, 0.16f, 0.1f, 0.92f));
      DrawFallbackText("PRESS ENTER OR CLICK TO START",
                       {w * 0.5f, h * 0.71f}, 31.0f, 0xFFFFFF);
    } else {
      constexpr std::array<const char*, 5> labels{
          "START", "LOAD", "EXTRA", "CONFIG", "HELP"};
      for (size_t i = 0; i < Items.size(); ++i) {
        Item const& item = Items[i];
        bool const selected = (int)i == Cursor && item.Enabled;
        RectF const& bounds = item.Bounds;
        Renderer->DrawQuad(
            RectF(bounds.X - 20.0f, bounds.Y - 10.0f,
                  bounds.Width + 40.0f, bounds.Height + 20.0f),
            selected ? glm::vec4(0.78f, 0.36f, 0.16f, 0.95f)
                     : glm::vec4(0.12f, 0.17f, 0.24f, 0.85f));
        if (i < labels.size()) {
          DrawFallbackText(labels[i],
                           {bounds.X + bounds.Width * 0.5f, bounds.Y + 1.0f},
                           35.0f,
                           !item.Enabled ? 0x8290A0
                                         : selected ? 0xFFFFFF : 0xE8ECF1);
        }
      }
      DrawFallbackText("ENTER OR CLICK TO SELECT",
                       {w * 0.5f, h * 0.9f}, 26.0f, 0xBFC9D8);
    }
    return;
  }

  if (!InMainMenu) return;
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
