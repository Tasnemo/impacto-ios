#pragma once

#include "../../data/savesystem.h"
#include <string>
#include <optional>

namespace Impacto {
namespace Profile {
namespace SaveSystem {

int constexpr MaxAlbumEntries = 200;
int constexpr MaxAlbumSubEntries = 15;
int constexpr MaxCGSprites = 4;

inline Impacto::SaveSystem::SaveDataType Type =
    Impacto::SaveSystem::SaveDataType::None;

inline std::string SaveFilePath;
inline std::optional<std::string> ThumbnailFilePath;
inline std::vector<uint32_t> StoryScriptIDs;
// Flattened (start, length) pairs of FlagWork bytes / ScrWork entries that a
// save stores (SaveDataType::SGHD).
inline std::vector<uint32_t> FlagWorkRanges;
inline std::vector<uint32_t> ScrWorkRanges;
// Same, for the global (system) data saved once per file (SGHD, optional).
inline std::vector<uint32_t> SystemFlagWorkRanges;
inline std::vector<uint32_t> SystemScrWorkRanges;
inline std::vector<Impacto::SaveSystem::ScriptMessageDataPair>
    ScriptMessageData;
inline uint16_t AlbumEvData[MaxAlbumEntries][MaxAlbumSubEntries];
inline uint16_t AlbumData[MaxAlbumEntries][MaxAlbumSubEntries][MaxCGSprites];

struct AddedLinesDataStruct {
  size_t BitFieldOffset;
  size_t AddedLinesPerScript;
};
inline std::optional<AddedLinesDataStruct> AddedLinesData;

std::vector<std::pair<size_t, size_t>> GetEquivalentLines(size_t scriptId,
                                                          size_t lineId);

void Configure();

}  // namespace SaveSystem
}  // namespace Profile
}  // namespace Impacto