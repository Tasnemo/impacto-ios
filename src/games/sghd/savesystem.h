#pragma once

#include "../../data/savesystem.h"

#include <array>
#include <map>
#include <vector>

namespace Impacto {
namespace SGHD {

using namespace Impacto::SaveSystem;

// Fork-native save format for the STEINS;GATE Steam profile (Thread 04 Task
// 4). This is NOT the Steam SAVEDATA.DAT layout, which is undocumented; the
// file only round-trips impacto's own VM state. Layout: see
// docs/sghd-save-format.md.

constexpr int MaxFullSaves = 80;
constexpr int MaxQuickSaves = 48;
constexpr uint32_t SaveFormatVersion = 1;

class SaveFileEntry : public SaveFileEntryBase {
 public:
  uint32_t CheckpointId = 0;
  uint32_t MainThreadLoopLabelNum = 0;
  std::vector<uint8_t> FlagWorkData;  // concatenated FlagWorkRanges
  std::vector<int> ScrWorkData;       // concatenated ScrWorkRanges
};

class SaveSystem : public SaveSystemBase {
 public:
  SaveSystem();

  SaveError CheckSaveFile() const override;
  SaveError MountSaveFile(std::vector<QueuedTexture>& textures) override;

  void SaveMemory() override;
  void LoadEntry(SaveType type, int id) override;
  void LoadMemoryNew(LoadProcess process) override;
  void FlushWorkingSaveEntry(SaveType type, int id, int autoSaveType) override;

  void SaveSystemData() override {}
  SaveError LoadSystemData() override { return SaveError::OK; }
  void InitializeSystemData() override;

  void SaveThumbnailData() override {}
  SaveError WriteSaveFile() override;
  uint32_t GetSavePlayTime(SaveType type, int id) const override;
  uint8_t GetSaveFlags(SaveType type, int id) const override;
  void SetSaveFlags(SaveType type, int id, uint8_t flags) override;
  tm const& GetSaveDate(SaveType type, int id) const override;
  uint8_t GetSaveStatus(SaveType type, int id) const override;
  int GetSaveTitle(SaveType type, int id) const override;

  // Tips, CGs and BGM unlocks are not persisted yet.
  uint32_t GetTipStatus(size_t) const override { return 0; }
  void SetTipStatus(size_t, bool, bool, bool) override {}
  void GetViewedEVsCount(int* total, int* viewed) const override {
    *total = 0;
    *viewed = 0;
  }
  void GetEVStatus(int, int* total, int* viewed) const override {
    *total = 0;
    *viewed = 0;
  }
  void SetEVStatus(int) override {}
  bool GetEVVariationIsUnlocked(size_t, size_t) const override { return false; }
  bool GetBgmFlag(int) const override { return false; }
  void SetBgmFlag(int, bool) override {}

  void SetLineRead(size_t scriptId, size_t lineId) override;
  bool IsLineRead(size_t scriptId, size_t lineId) const override;
  void GetReadMessagesCount(int* totalMessageCount,
                            int* readMessageCount) const override;

  void SetCheckpointId(int id) override { CheckpointId = id; }
  Sprite& GetSaveThumbnail(SaveType type, int id) override;

 private:
  SaveFileEntry* Entry(SaveType type, int id);
  SaveFileEntry const* Entry(SaveType type, int id) const;

  std::array<SaveFileEntry, MaxFullSaves> FullEntries;
  std::array<SaveFileEntry, MaxQuickSaves> QuickEntries;
  SaveFileEntry WorkingEntry;
  uint32_t CheckpointId = 0;
  // script id -> bitmap of read line ids
  std::map<uint32_t, std::vector<uint8_t>> ReadLines;
};

}  // namespace SGHD
}  // namespace Impacto
