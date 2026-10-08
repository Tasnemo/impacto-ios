#pragma once

#include <optional>

#include "../../ui/menu.h"

namespace Impacto {
namespace UI {
namespace SGHD {

// STEINS;GATE (Steam) title menu. The scripts drive it through 10 34
// (docs/threads/07c-title-menu.md): type 0/2 initialise, type 1 is called
// while the script polls SF_TITLEEND. In the press-start phase any confirm
// ends it; in the main-menu phase (SW_TITLEMODE == MainMenuMode) confirm
// reports the selected item's choice id, which the script reads from
// SW_TITLECUR. Input is read in Update (every frame) and latched, because
// the scripts only poll every other frame.
class TitleMenu : public Menu {
 public:
  void Show() override;
  void Hide() override;
  void Update(float dt) override;
  void Render() override;

  // 10 34 type 0/2: cursor to the first enabled item, forget any decision.
  void ResetCursor();
  // 10 34 type 1, once per script poll: keeps input processing on for the
  // next PollFrames frames (the scripts poll every other frame: Sleep 1,
  // 10 34 1) and returns a decision latched by Update for this phase:
  // -1 in the press-start phase, the item's ChoiceId in the main menu.
  std::optional<int> Poll(bool mainMenuMode);

  int Cursor = 0;
  static int constexpr PollFrames = 3;

 private:
  struct Decision {
    bool MainMenu;
    int Choice;
  };
  int PollFramesLeft = 0;
  bool InMainMenu = false;
  std::optional<Decision> Pending;

  std::optional<int> ReadInput(bool mainMenuMode);
  void MoveCursor(int direction);
};

}  // namespace SGHD
}  // namespace UI
}  // namespace Impacto
