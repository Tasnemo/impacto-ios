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

  float const w = Profile::Game::DesignWidth;
  float const h = Profile::Game::DesignHeight;

  // The local Steam sheet has a full-screen opaque region; its exact role
  // has not yet been confirmed. Draw it behind a readable UI for the
  // compatibility preview, and retain the fallback if the region is unset.
  if (PreviewBackgroundSprite) {
    Renderer->DrawSprite(*PreviewBackgroundSprite, RectF(0, 0, w, h));
  } else {
    Renderer->DrawQuad(RectF(0, 0, w, h),
                       glm::vec4(0.025f, 0.04f, 0.075f, 1.0f));
    Renderer->DrawQuad(RectF(0, h * 0.22f, w, 3),
                       glm::vec4(0.78f, 0.36f, 0.16f, 1.0f));
    DrawFallbackText("STEINS;GATE", {w * 0.5f, h * 0.31f},
                     82.0f, 0xF5F5EF);
  }

  if (!InMainMenu) {
    Renderer->DrawQuad(RectF(w * 0.25f, h * 0.7f, w * 0.5f, 84),
                       glm::vec4(0.08f, 0.11f, 0.18f, 0.94f));
    DrawFallbackText("PRESS ENTER OR CLICK TO START",
                     {w * 0.5f, h * 0.72f}, 31.0f, 0xFFFFFF);
  } else {
    // These labels remain authoritative even when the tentative atlas
    // regions are enabled: the positions and selected-state mapping must
    // be visually verified against the original Steam menu.
    constexpr std::array<const char*, 5> labels{
        "START", "LOAD", "EXTRA", "CONFIG", "HELP"};

    for (size_t i = 0; i < Items.size(); ++i) {
      Item const& item = Items[i];
      bool const selected = (int)i == Cursor && item.Enabled;
      RectF const& bounds = item.Bounds;

      std::optional<Sprite> const& sprite =
          selected && item.SelectedSprite ? item.SelectedSprite
                                          : item.NormalSprite;

      if (selected) {
        Renderer->DrawQuad(
            RectF(bounds.X - 6, bounds.Y - 5,
                  bounds.Width + 12, bounds.Height + 10),
            glm::vec4(0.95f, 0.42f, 0.12f, 0.94f));
      }

      if (sprite) {
        Renderer->DrawSprite(*sprite, bounds.GetPos());
      } else {
        Renderer->DrawQuad(
            bounds, item.Enabled ? glm::vec4(0.15f, 0.21f, 0.29f, 0.95f)
                                 : glm::vec4(0.12f, 0.14f, 0.19f, 0.86f));
      }

      // A separate text key for each row makes the preview navigable even
      // if a candidate atlas crop does not contain the expected word.
      if (i < labels.size()) {
        DrawFallbackText(labels[i],
                         {bounds.X - 130.0f, bounds.Y + 7.0f},
                         30.0f, item.Enabled ? 0xFFFFFF : 0xA0AEC0);
      }

      if (selected && CursorSprite)
        Renderer->DrawSprite(*CursorSprite, bounds.GetPos() + CursorOffset);
    }
  }

  Renderer->DrawQuad(RectF(0, h - 42, w, 42),
                     glm::vec4(0.035f, 0.055f, 0.08f, 0.93f));
  DrawFallbackText("WINDOWS COMPATIBILITY PREVIEW",
                   {w * 0.5f, h - 37.0f}, 21.0f, 0xC8D2E0);
}

}  // namespace SGHD
}  // namespace UI
}  // namespace Impacto
