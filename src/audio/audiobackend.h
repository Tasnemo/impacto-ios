#pragma once

#include "audiocommon.h"

namespace Impacto {
namespace Audio {

// Set when the configured backend failed to initialise (e.g. no audio
// device): audio and video then use the silent backend for this run only;
// the user's configured backend is left unchanged.
inline bool BackendUnavailable = false;

class AudioBackend {
 public:
  virtual ~AudioBackend() = default;

  virtual bool Init() { return true; };

  virtual bool Reinit() { return true; };

  virtual void Shutdown() {};

  virtual bool DidDeviceChanged() { return false; };

  virtual bool ReopenSupported() { return false; }
};

}  // namespace Audio
}  // namespace Impacto