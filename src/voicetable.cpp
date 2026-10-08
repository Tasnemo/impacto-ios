#include "voicetable.h"

#include "io/io.h"
#include "io/vfs.h"
#include "log.h"
#include "profile/game.h"

namespace Impacto {
bool VoiceTable::LoadSync(uint32_t id) {
  Io::Stream* stream;
  int64_t err = Io::VfsOpen("system", id, &stream);
  if (err != IoError_OK) return false;

  const bool le = Profile::Game::VoiceTableLittleEndian;
  const auto readU16 = [stream, le]() {
    return le ? Io::ReadLE<uint16_t>(stream) : Io::ReadBE<uint16_t>(stream);
  };

  VoiceFileCount = readU16();
  readU16();

  const int64_t endToc = 4 * (int64_t)VoiceFileCount + 4;
  if (endToc > stream->Meta.Size) {
    ImpLog(LogLevel::Error, LogChannel::General,
           "Voice table {:d}: {:d} entries do not fit in {:d} bytes (wrong "
           "byte order?); lip sync disabled\n",
           id, VoiceFileCount, stream->Meta.Size);
    VoiceFileCount = 0;
    delete stream;
    return false;
  }

  for (size_t i = 0; i < VoiceFileCount; ++i) {
    uint16_t dataIndex = readU16();
    uint16_t voiceLengthSecTimes6 = Io::ReadLE<uint16_t>(stream);
    VoiceMeta voiceMeta{dataIndex, voiceLengthSecTimes6};
    TableOfContents[i] = voiceMeta;
  }

  LipSyncData.resize(stream->Meta.Size - stream->Position);
  stream->Read(LipSyncData.data(), LipSyncData.size());

  delete stream;
  return true;
}

uint8_t VoiceTable::GetVoiceData(uint32_t id, size_t index) const {
  const auto it = TableOfContents.find(id);
  if (it == TableOfContents.end()) return 0;
  const size_t offset = it->second.DataIndex * 4 + index;
  return offset < LipSyncData.size() ? LipSyncData[offset] : 0;
}

void VoiceTable::UnloadSync() {
  VoiceFileCount = 0;
  TableOfContents.clear();
  LipSyncData.resize(0);
}

void VoiceTable::MainThreadOnLoad(bool result) {}

}  // namespace Impacto