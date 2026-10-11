#include "inst_movie.h"

#include "inst_macros.inc"

#include <math.h>
#include <array>
#include <string>
#include <string_view>

#include "expression.h"
#include "../game.h"
#include "../log.h"
#include "../mem.h"
#include "../profile/scriptvars.h"
#include "../profile/vm.h"
#include "../profile/game.h"
#include "../video/videosystem.h"
#include "interface/input.h"

namespace Impacto {

namespace Vm {

using namespace Impacto::Profile::ScriptVars;

// Original English Steam Game.exe indexes movies in this order. These are
// filename stems only, not movie data. Derived from its 38-entry name table.
// Never place original BK2s or locally converted video in this repository.
static constexpr std::array<std::string_view, 38> SghdMovieStems = {
    "ar",  // 0
    "ending_c",  // 1
    "ending_f",  // 2
    "ending_m",  // 3
    "ending_r",  // 4
    "ending_s",  // 5
    "imv001",  // 6
    "imv002",  // 7
    "imv003",  // 8
    "imv004",  // 9
    "imv005",  // 10
    "imv006",  // 11
    "imv007",  // 12
    "imv008",  // 13
    "imv009",  // 14
    "imv010",  // 15
    "imv018",  // 16
    "imv023",  // 17
    "imv027",  // 18
    "imv034",  // 19
    "imv034b",  // 20
    "imv036",  // 21
    "imv037",  // 22
    "imv038",  // 23
    "imv039",  // 24
    "imv041",  // 25
    "imv042",  // 26
    "imv043",  // 27
    "imv047",  // 28
    "imv049",  // 29
    "imv050",  // 30
    "imv051",  // 31
    "op",  // 32
    "op2",  // 33
    "prologue01",  // 34
    "prologue02",  // 35
    "timeleapbg",  // 36
    "title",  // 37
};

// Converted videos remain entirely on the owner's local machine, in
// gamedata/sghd/movie-converted/*.mp4. Use NAME lookups instead of folder
// ordinal IDs (FSFolderArchive sorts files, so missing conversions otherwise
// shift script movie IDs). Legacy SGHD harness tests may mount a Bink 2
// .bk2 by name; FFmpeg will safely reject it as unsupported.
static IoError OpenMovieStream(int movieId, Io::Stream** stream) {
  if (Profile::Vm::GameInstructionSet != InstructionSet::SGHD)
    return Io::VfsOpen("movie", movieId, stream);

  if (movieId < 0 ||
      static_cast<size_t>(movieId) >= SghdMovieStems.size()) {
    ImpLog(LogLevel::Error, LogChannel::Video,
           "Unknown SGHD movie ID {:d}; skipping movie\n", movieId);
    return IoError_NotFound;
  }
  std::string stem(SghdMovieStems[movieId]);
  IoError err = Io::VfsOpen("movie", stem + ".mp4", stream);
  if (err != IoError_OK)
    err = Io::VfsOpen("movie", stem + ".bk2", stream);
  if (err != IoError_OK)
    ImpLog(LogLevel::Warning, LogChannel::Video,
           "SGHD movie ID {:d} ({:s}) has no local converted MP4; "
           "skipping movie\n", movieId, stem);
  return err;
}


// Missing or undecodable movies must not inherit another movie's wait flags.
static void ResetFailedMovieState(uint8_t channel) {
  SetFlag(SF_MOVIEPLAY + channel, false);
  SetFlag(SF_MOVIE_DRAWWAIT + channel, false);
  SetFlag(SF_MOVIELOADPLAYFL + channel, false);
  SetFlag(SF_MOVIECANCEL + channel, false);
  ScrWork[SW_MOVIE_PLAYNO + 20 * channel] = 0xffff;
  ScrWork[SW_MOVIE_LOADNO + 20 * channel] = 0xffff;
}

VmInstruction(InstPlayMovie) {
  StartInstruction;
  PopUint8(playMode);

  int playView;
  if (playMode == 99) {  // PlayMovieRecover - used when loading a save file
    // playMode of the video at save time
    playMode = static_cast<uint8_t>(ExpressionEval(thread));
    playView = ExpressionEval(thread);
  } else {
    playView = *thread->GetIp();
    thread->IpOffset++;
  }

  PopExpression(playNo);
  PopExpression(movCancelFlag);

  if (+Profile::Game::GameFeatures & +GameFeature::Video) {
    const uint8_t channel = (playMode / 20) == 0 ? 0 : 1;
    Io::Stream* stream;
    auto err = OpenMovieStream(playNo, &stream);
    if (err != IoError_OK) {
      ResetFailedMovieState(channel);
      ImpLog(LogLevel::Error, LogChannel::Video,
             "Failed to open movie for playback: IO error {}\n", err);
      return;
    }

    Video::Players[channel]->CancelFlag = movCancelFlag;
    Video::Players[channel]->CancelWaitTime = 0;
    SetFlag(SF_MOVIEFL + channel, movCancelFlag);
    ScrWork[SW_MOVIE_PLAYNO + 20 * channel] = playNo;
    ScrWork[SW_MOVIE_PLAYMODE + 20 * channel] = playMode + 20 * channel;
    ScrWork[SW_MOVIE_PLAYVIEW + 20 * channel] = playView;
    ScrWork[SW_MOVIE_LOADNO + 20 * channel] = 0xffff;

    int flags = 0;
    if (playMode >= 8) {
      playMode -= 8;
      flags |= 4;
    }
    switch (playMode) {
      case 0:
        flags |= 0b10;
        break;
      case 1:
        flags |= 0b1;
        break;
      case 2:
        flags |= 0b1010;
        break;
      case 3:
        flags |= 0b1001;
        break;
      case 4:
        flags |= 0b100000;
        break;
      case 5:
        flags |= 0b101000;
        break;
      default:
        break;
    }

    if (Video::Players[channel]->IsPlaying) Video::Players[channel]->Stop();
    Video::Players[channel]->Play(stream, flags & 8, flags & 4);
    if (!Video::Players[channel]->IsPlaying) {
      // Undecodable stream (e.g. Bink 2): nothing would ever clear
      // SF_MOVIEPLAY, so MovieMain would wait forever. Skip the movie like a
      // failed open does.
      ImpLog(LogLevel::Error, LogChannel::Video,
             "Movie {:d} could not be played; skipping it\n", playNo);
      ResetFailedMovieState(channel);
      return;
    }

    SetFlag(SF_MOVIE_DRAWWAIT + channel, true);
    SetFlag(SF_MOVIEPLAY + channel, true);
    SetFlag(SF_MOVIECANCEL + channel, false);
  }

  BlockThread;
  ImpLogSlow(LogLevel::Warning, LogChannel::VMStub,
             "STUB instruction PlayMovie(playMode: {:d}, playView: {:d}, "
             "playNo: {:d}, movCancelFlag: {:d})\n",
             playMode, playView, playNo, movCancelFlag);
}

static void PlayMovieOldCommon(Sc3VmThread* thread, uint8_t instType) {
  StartInstruction;
  PopUint8(playMode);

  int playView;
  if (playMode == 99) {  // PlayMovieRecover - used when loading a save file
    // playMode of the video at save time
    playMode = static_cast<uint8_t>(ExpressionEval(thread));
    playView = ExpressionEval(thread);
  } else {
    playView = *thread->GetIp();
    thread->IpOffset++;
  }

  PopExpression(playNo);
  PopExpression(movCancelFlag);

  if (+Profile::Game::GameFeatures & +GameFeature::Video) {
    const uint8_t channel = (playMode / 20) == 0 ? 0 : 1;
    Io::Stream* stream;
    auto err = OpenMovieStream(playNo, &stream);
    if (err != IoError_OK) {
      if (Profile::Vm::GameInstructionSet == InstructionSet::SGHD)
        ResetFailedMovieState(channel);
      ImpLog(LogLevel::Error, LogChannel::Video,
             "Failed to open movie for playback: IO error {}\n", err);
      return;
    }

    Video::Players[channel]->CancelFlag = movCancelFlag;
    Video::Players[channel]->CancelWaitTime = 0;
    SetFlag(SF_MOVIEFL + channel, movCancelFlag);
    ScrWork[SW_MOVIE_PLAYNO + 20 * channel] = playNo + (1000 * (instType == 2));
    ScrWork[SW_MOVIE_PLAYMODE + 20 * channel] = playMode + 20 * channel;
    ScrWork[SW_MOVIE_PLAYVIEW + 20 * channel] = playView;
    ScrWork[SW_MOVIE_LOADNO + 20 * channel] = 0xffff;

    if (Video::Players[channel]->IsPlaying) Video::Players[channel]->Stop();
    Video::Players[channel]->Play(stream, playMode == 5, playMode == 5);
    if (!Video::Players[channel]->IsPlaying) {
      ImpLog(LogLevel::Error, LogChannel::Video,
             "Movie {:d} could not be played; skipping it\n", playNo);
      if (Profile::Vm::GameInstructionSet == InstructionSet::SGHD)
        ResetFailedMovieState(channel);
      return;
    }

    SetFlag(SF_MOVIE_DRAWWAIT + channel, true);
    SetFlag(SF_MOVIEPLAY + channel, true);
    SetFlag(SF_MOVIECANCEL + channel, false);
  }

  BlockThread;
  ImpLogSlow(LogLevel::Warning, LogChannel::VMStub,
             "STUB instruction PlayMovieOld(playMode: {:d}, playView: {:d}, "
             "playNo: {:d}, movCancelFlag: {:d})\n",
             playMode, playView, playNo, movCancelFlag);
}

VmInstruction(InstPlayMovieOld) { PlayMovieOldCommon(thread, 1); }
VmInstruction(InstPlayMovieOld2) { PlayMovieOldCommon(thread, 2); }

VmInstruction(InstMovie) {
  StartInstruction;
  PopUint8(type);
  switch (type) {
    case 0: {  // Restart
      ImpLogSlow(LogLevel::Warning, LogChannel::VMStub,
                 "STUB instruction Movie(type: Restart)\n");
    } break;
    case 1: {  // Pause
      ImpLogSlow(LogLevel::Warning, LogChannel::VMStub,
                 "STUB instruction Movie(type: Pause)\n");
    } break;
  }
}
VmInstruction(InstMovieMain) {
  using namespace Video;
  StartInstruction;

  const bool videoEnabled = +Profile::Game::GameFeatures & +GameFeature::Video;

  PopUint8(type);
  const uint8_t playerId = type < 20 ? 0 : 1;
  VideoPlayer& player = *Players[playerId];

  switch (type) {
    case 0: {
      if (!videoEnabled) {
        SetFlag(SF_MOVIELOADPLAYFL + playerId, false);
        SetFlag(SF_MOVIE_DRAWWAIT + playerId, false);
        ScrWork[SW_MOVIE_PLAYNO + playerId * 20] = 0xffff;
        ScrWork[SW_MOVIE_LOADNO + playerId * 20] = 0xffff;
        break;
      }

      if (GetFlag(SF_MOVIEPLAY + playerId) && player.CancelWaitTime != 0) {
        player.CancelWaitTime++;
        if (player.CancelWaitTime < 8) {
          ResetInstruction;
          BlockThread;
          return;
        }

        SetFlag(SF_MOVIEPLAY + playerId, false);
        SetFlag(SF_MOVIECANCEL + playerId, true);
        player.CancelWaitTime = 0;
        BlockThread;
      }

      if (!player.CancelFlag ||
          !Interface::GetControlState(Interface::ControlType::MovieCancel)) {
        if (GetFlag(SF_MOVIEPLAY + playerId)) {
          ResetInstruction;
          BlockThread;
        } else {
          player.Stop();

          SetFlag(SF_MOVIELOADPLAYFL + playerId, false);
          SetFlag(SF_MOVIE_DRAWWAIT + playerId, false);
          ScrWork[SW_MOVIE_PLAYNO + playerId * 20] = 0xffff;
          ScrWork[SW_MOVIE_LOADNO + playerId * 20] = 0xffff;
        }

      } else {
        player.CancelWaitTime++;
        player.CancelFlag = false;

        ResetInstruction;
        BlockThread;
      }
    } break;

    case 1:
    case 21: {
      thread->ScriptParam = GetFlag(SF_MOVIEPLAY + playerId);
    } break;

    case 2:
    case 22: {  // Stop
      if (videoEnabled) player.Stop();

      SetFlag(SF_MOVIEPLAY + playerId, false);
      SetFlag(SF_MOVIELOADPLAYFL + playerId, false);
      SetFlag(SF_MOVIE_DRAWWAIT + playerId, false);
      ScrWork[SW_MOVIE_PLAYNO + playerId * 20] = 0xffff;
      ScrWork[SW_MOVIE_LOADNO + playerId * 20] = 0xffff;
    } break;

    case 3:
    case 23: {  // StopWait
      if (player.CancelFlag &&
          Interface::GetControlState(Interface::ControlType::MovieCancel)) {
        SetFlag(SF_MOVIEPLAY + playerId, false);
        SetFlag(SF_MOVIECANCEL + playerId, true);
        BlockThread;
      }

      if (!GetFlag(SF_MOVIEPLAY + playerId)) {
        if (videoEnabled) player.Stop();

        SetFlag(SF_MOVIELOADPLAYFL + playerId, false);
        ScrWork[SW_MOVIE_PLAYNO + playerId * 20] = 0xffff;
        ScrWork[SW_MOVIE_LOADNO + playerId * 20] = 0xffff;
      }
    } break;

    case 4:
    case 24: {
      if (videoEnabled && !player.IsPlaying) {
        ResetInstruction;
        BlockThread;
      } else {
        // TODO: Set frame numbers
      }
    } break;

    case 20: {
      if (!videoEnabled) {
        SetFlag(SF_MOVIEPLAY + playerId, false);
        SetFlag(SF_MOVIECANCEL + playerId, false);
        ScrWork[SW_MOVIE_PLAYNO + playerId * 20] = 0xffff;
        ScrWork[SW_MOVIE_LOADNO + playerId * 20] = 0xffff;
        break;
      }

      if (player.CancelFlag &&
          Interface::GetControlState(Interface::ControlType::MovieCancel)) {
        SetFlag(SF_MOVIEPLAY + playerId, true);
        SetFlag(SF_MOVIECANCEL + playerId, true);
        BlockThread;
      }

      if (!GetFlag(SF_MOVIEPLAY + playerId)) {
        player.Stop();
        ScrWork[SW_MOVIE_PLAYNO + playerId * 20] = 0xffff;
        ScrWork[SW_MOVIE_LOADNO + playerId * 20] = 0xffff;
      } else {
        ResetInstruction;
        BlockThread;
      }
    } break;
  }
}
VmInstruction(InstLoadMovie) {
  StartInstruction;
  PopExpression(arg1);
  ScrWork[SW_MOVIE_LOADNO] = arg1 + 1000;
  ImpLogSlow(LogLevel::Warning, LogChannel::VMStub,
             "STUB instruction LoadMovie(arg1: {:d})\n", arg1);
}
VmInstruction(InstPlayMovieMemory) {
  StartInstruction;
  PopUint8(playMode);
  if (playMode == 99) {
    PopExpression(playModeEx);
    PopExpression(playView);
    PopExpression(movCancelFlag);
    ImpLogSlow(LogLevel::Warning, LogChannel::VMStub,
               "STUB instruction PlayMovie(playMode: {:d}, playModeEx: {:d}, "
               "playView: {:d}, movCancelFlag: {:d})\n",
               playMode, playModeEx, playView, movCancelFlag);

  } else {
    PopUint8(playView);
    PopExpression(movCancelFlag);
    ImpLogSlow(LogLevel::Warning, LogChannel::VMStub,
               "STUB instruction PlayMovie(playMode: {:d}, playView: {:d}, "
               "movCancelFlag: {:d})\n",
               playMode, playView, movCancelFlag);
  }
}
VmInstruction(InstSFDpause) {
  StartInstruction;
  PopUint8(paused);
  ImpLogSlow(LogLevel::Warning, LogChannel::VMStub,
             "STUB instruction SFDpause(paused: {:d})\n", paused);
}

}  // namespace Vm

}  // namespace Impacto
