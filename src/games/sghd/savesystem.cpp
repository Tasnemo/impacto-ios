#include "savesystem.h"
#include "phone.h"

#include "../../io/physicalfilestream.h"
#include "../../log.h"
#include "../../mem.h"
#include "../../profile/data/savesystem.h"
#include "../../profile/scriptvars.h"
#include "../../profile/vm.h"
#include "../../util.h"
#include "../../vm/thread.h"
#include "../../vm/vm.h"

#include <algorithm>
#include <bit>
#include <cstring>
#include <memory>
#include <utility>

namespace Impacto {
namespace SGHD {

using namespace Impacto::Vm;
using namespace Impacto::Profile::SaveSystem;
using namespace Impacto::Profile::ScriptVars;

static constexpr char Magic[8] = {'I', 'M', 'P', 'S', 'G', 'H', 'D', '\0'};

// (start, length) pairs from the profile, clamped to the backing arrays
template <size_t N>
static std::vector<std::pair<size_t, size_t>> Ranges(
    std::vector<uint32_t> const& flat) {
  std::vector<std::pair<size_t, size_t>> out;
  for (size_t i = 0; i + 1 < flat.size(); i += 2) {
    size_t const start = std::min<size_t>(flat[i], N);
    out.emplace_back(start, std::min<size_t>(flat[i + 1], N - start));
  }
  return out;
}

static Sc3VmThread* MainThread() {
  const int threadId = ScrWork[SW_MAINTHDP] & 0x7FFFFFFF;
  if (threadId <= 0 || threadId >= MaxThreads) return nullptr;
  return &ThreadPool[threadId];
}

SaveSystem::SaveSystem() {
  for (int i = 0; i < MaxSaveEntries; i++) {
    FullSaveEntries[i] = &FullEntries[i];
    QuickSaveEntries[i] = &QuickEntries[i];
  }
}

SaveFileEntry* SaveSystem::Entry(SaveType type, int id) {
  return const_cast<SaveFileEntry*>(std::as_const(*this).Entry(type, id));
}

SaveFileEntry const* SaveSystem::Entry(SaveType type, int id) const {
  if (type == SaveType::Full && id >= 0 && id < MaxFullSaves)
    return &FullEntries[id];
  if (type == SaveType::Quick && id >= 0 && id < MaxQuickSaves)
    return &QuickEntries[QuickSaveRecentSortedId[id]];
  ImpLog(LogLevel::Error, LogChannel::IO, "Invalid save slot {:d}:{:d}\n",
         (int)type, id);
  return nullptr;
}

void SaveSystem::InitializeSystemData() {
  ReadLines.clear();
  SystemFlagWorkData.clear();
  SystemScrWorkData.clear();
  HasSystemData = false;
}

void SaveSystem::SaveSystemData() {
  SystemFlagWorkData.clear();
  SystemScrWorkData.clear();
  for (auto const& [start, length] :
       Ranges<FlagWorkSize>(SystemFlagWorkRanges)) {
    SystemFlagWorkData.insert(SystemFlagWorkData.end(),
                              FlagWork.begin() + start,
                              FlagWork.begin() + start + length);
  }
  for (auto const& [start, length] : Ranges<ScrWorkSize>(SystemScrWorkRanges)) {
    SystemScrWorkData.insert(SystemScrWorkData.end(), ScrWork.begin() + start,
                             ScrWork.begin() + start + length);
  }
  HasSystemData = true;
}

SaveError SaveSystem::LoadSystemData() {
  if (!HasSystemData) return SaveError::NotFound;
  auto flags = SystemFlagWorkData.begin();
  for (auto const& [start, length] :
       Ranges<FlagWorkSize>(SystemFlagWorkRanges)) {
    if (SystemFlagWorkData.end() - flags < (ptrdiff_t)length) break;
    std::copy_n(flags, length, FlagWork.begin() + start);
    flags += length;
  }
  auto values = SystemScrWorkData.begin();
  for (auto const& [start, length] : Ranges<ScrWorkSize>(SystemScrWorkRanges)) {
    if (SystemScrWorkData.end() - values < (ptrdiff_t)length) break;
    std::copy_n(values, length, ScrWork.begin() + start);
    values += length;
  }
  return SaveError::OK;
}

void SaveSystem::SaveMemory() {
  SaveFileEntry& entry = WorkingEntry;
  entry = SaveFileEntry{};
  entry.Status = 1;
  entry.SaveDate = CurrentDateTime();
  entry.PlayTime = ScrWork[SW_PLAYTIME];
  entry.SwTitle = ScrWork[SW_TITLE];
  entry.CheckpointId = CheckpointId;

  for (auto const& [start, length] : Ranges<FlagWorkSize>(FlagWorkRanges)) {
    entry.FlagWorkData.insert(entry.FlagWorkData.end(),
                              FlagWork.begin() + start,
                              FlagWork.begin() + start + length);
  }
  for (auto const& [start, length] : Ranges<ScrWorkSize>(ScrWorkRanges)) {
    entry.ScrWorkData.insert(entry.ScrWorkData.end(), ScrWork.begin() + start,
                             ScrWork.begin() + start + length);
  }
  entry.PhoneItemBits.assign(Phone::ItemBits.begin(), Phone::ItemBits.end());

  Sc3VmThread const* thd = MainThread();
  if (thd == nullptr) {
    ImpLog(LogLevel::Warning, LogChannel::IO,
           "SaveMemory: SW_MAINTHDP does not name a script thread; saving "
           "variables only\n");
    return;
  }
  entry.MainThreadExecPriority = thd->ExecPriority;
  entry.MainThreadGroupId = thd->GroupId;
  entry.MainThreadWaitCounter = thd->WaitCounter;
  entry.MainThreadScriptParam = thd->ScriptParam;
  entry.MainThreadScriptBufferId = thd->ScriptBufferId;
  entry.MainThreadIp = thd->IpOffset;
  entry.MainThreadLoopCounter = thd->LoopCounter;
  entry.MainThreadLoopLabelNum = thd->LoopLabelNum;
  entry.MainThreadCallStackDepth = thd->CallStackDepth;
  // Return addresses and return ids share storage; copy it verbatim.
  static_assert(sizeof(thd->ReturnAddresses) ==
                sizeof(entry.MainThreadReturnAddresses));
  std::memcpy(entry.MainThreadReturnAddresses.data(), thd->ReturnAddresses,
              sizeof(thd->ReturnAddresses));
  std::copy(std::begin(thd->ReturnScriptBufferIds),
            std::end(thd->ReturnScriptBufferIds),
            entry.MainThreadReturnBufIds.begin());
  std::copy(std::begin(thd->Variables), std::end(thd->Variables),
            entry.MainThreadVariables.begin());
  entry.MainThreadDialoguePageId = thd->DialoguePageId;
}

void SaveSystem::LoadEntry(SaveType type, int id) {
  SaveFileEntry const* entry = Entry(type, id);
  if (entry != nullptr) WorkingEntry = *entry;
}

void SaveSystem::LoadMemoryNew(LoadProcess process) {
  // InstLoadData forwards every sub-type; only 0 (Vars) and 1 (Thread) load.
  if (process != LoadProcess::Vars && process != LoadProcess::Thread) return;
  SaveFileEntry const& entry = WorkingEntry;
  if (entry.Status == 0) {
    ImpLog(LogLevel::Error, LogChannel::IO,
           "Failed to load entry: save is empty\n");
    return;
  }

  if (process == LoadProcess::Vars) {
    ScrWork[SW_PLAYTIME] = entry.PlayTime;
    ScrWork[SW_TITLE] = entry.SwTitle;
    CheckpointId = entry.CheckpointId;

    auto flags = entry.FlagWorkData.begin();
    for (auto const& [start, length] : Ranges<FlagWorkSize>(FlagWorkRanges)) {
      std::copy_n(flags, length, FlagWork.begin() + start);
      flags += length;
    }
    auto values = entry.ScrWorkData.begin();
    for (auto const& [start, length] : Ranges<ScrWorkSize>(ScrWorkRanges)) {
      std::copy_n(values, length, ScrWork.begin() + start);
      values += length;
    }
    Phone::ItemBits.fill(0);
    std::copy_n(entry.PhoneItemBits.begin(),
                std::min(entry.PhoneItemBits.size(), Phone::ItemBits.size()),
                Phone::ItemBits.begin());
    return;
  }

  Sc3VmThread* thd = MainThread();
  if (thd == nullptr) {
    ImpLog(LogLevel::Error, LogChannel::IO,
           "LoadMemory: SW_MAINTHDP does not name a script thread\n");
    return;
  }
  thd->ExecPriority = entry.MainThreadExecPriority;
  thd->GroupId = entry.MainThreadGroupId;
  thd->WaitCounter = entry.MainThreadWaitCounter;
  thd->ScriptParam = entry.MainThreadScriptParam;
  thd->ScriptBufferId = entry.MainThreadScriptBufferId;
  thd->IpOffset = entry.MainThreadIp;
  thd->LoopCounter = entry.MainThreadLoopCounter;
  thd->LoopLabelNum = (uint16_t)entry.MainThreadLoopLabelNum;
  thd->CallStackDepth = entry.MainThreadCallStackDepth;
  std::memcpy(thd->ReturnAddresses, entry.MainThreadReturnAddresses.data(),
              sizeof(thd->ReturnAddresses));
  std::copy(entry.MainThreadReturnBufIds.begin(),
            entry.MainThreadReturnBufIds.end(),
            std::begin(thd->ReturnScriptBufferIds));
  std::copy(entry.MainThreadVariables.begin(), entry.MainThreadVariables.end(),
            std::begin(thd->Variables));
  thd->DialoguePageId = entry.MainThreadDialoguePageId;
}

void SaveSystem::FlushWorkingSaveEntry(SaveType type, int id,
                                       int autoSaveType) {
  SaveFileEntry* entry = Entry(type, id);
  if (entry == nullptr || WorkingEntry.Status == 0 ||
      (entry->Flags & WriteProtect))
    return;
  uint8_t const flags = entry->Flags;
  *entry = WorkingEntry;
  entry->Flags = flags;
  entry->SaveDate = CurrentDateTime();
  if (type == SaveType::Quick) {
    entry->SaveType = autoSaveType;
    UpdateQuickSaveRecentSortedId(id);
  }
}

// --- file I/O --------------------------------------------------------------

static void WriteU32(Io::Stream* s, uint32_t v) { Io::WriteLE<uint32_t>(s, v); }
static uint32_t ReadU32(Io::Stream* s) { return Io::ReadLE<uint32_t>(s); }

static void WriteRanges(Io::Stream* s, std::vector<uint32_t> const& flat) {
  WriteU32(s, (uint32_t)flat.size());
  for (uint32_t v : flat) WriteU32(s, v);
}

static void WriteEntry(Io::Stream* s, SaveFileEntry const& e) {
  Io::WriteLE<uint8_t>(s, e.Status);
  if (e.Status == 0) return;
  WriteU32(s, e.PlayTime);
  WriteU32(s, e.SwTitle);
  Io::WriteLE<uint8_t>(s, e.Flags);
  WriteU32(s, e.SaveType);
  for (int v : {e.SaveDate.tm_year, e.SaveDate.tm_mon, e.SaveDate.tm_mday,
                e.SaveDate.tm_hour, e.SaveDate.tm_min, e.SaveDate.tm_sec})
    Io::WriteLE<int32_t>(s, v);
  WriteU32(s, e.CheckpointId);
  for (uint32_t v :
       {e.MainThreadExecPriority, e.MainThreadGroupId, e.MainThreadWaitCounter,
        e.MainThreadScriptParam, e.MainThreadScriptBufferId, e.MainThreadIp,
        e.MainThreadLoopCounter, e.MainThreadLoopLabelNum,
        e.MainThreadCallStackDepth})
    WriteU32(s, v);
  for (uint32_t v : e.MainThreadReturnAddresses) WriteU32(s, v);
  for (uint32_t v : e.MainThreadReturnBufIds) WriteU32(s, v);
  for (int v : e.MainThreadVariables) Io::WriteLE<int32_t>(s, v);
  WriteU32(s, e.MainThreadDialoguePageId);
  WriteU32(s, (uint32_t)e.FlagWorkData.size());
  Io::WriteArrayLE<uint8_t>(e.FlagWorkData.data(), s, e.FlagWorkData.size());
  WriteU32(s, (uint32_t)e.ScrWorkData.size());
  Io::WriteArrayLE<int32_t>(e.ScrWorkData.data(), s, e.ScrWorkData.size());
  WriteU32(s, (uint32_t)e.PhoneItemBits.size());
  Io::WriteArrayLE<uint8_t>(e.PhoneItemBits.data(), s, e.PhoneItemBits.size());
}

static void ReadEntry(Io::Stream* s, SaveFileEntry& e, uint32_t version) {
  e = SaveFileEntry{};
  e.Status = Io::ReadLE<uint8_t>(s);
  if (e.Status == 0) return;
  e.PlayTime = ReadU32(s);
  e.SwTitle = ReadU32(s);
  e.Flags = Io::ReadLE<uint8_t>(s);
  e.SaveType = ReadU32(s);
  for (int* v : {&e.SaveDate.tm_year, &e.SaveDate.tm_mon, &e.SaveDate.tm_mday,
                 &e.SaveDate.tm_hour, &e.SaveDate.tm_min, &e.SaveDate.tm_sec})
    *v = Io::ReadLE<int32_t>(s);
  e.CheckpointId = ReadU32(s);
  for (uint32_t* v :
       {&e.MainThreadExecPriority, &e.MainThreadGroupId,
        &e.MainThreadWaitCounter, &e.MainThreadScriptParam,
        &e.MainThreadScriptBufferId, &e.MainThreadIp, &e.MainThreadLoopCounter,
        &e.MainThreadLoopLabelNum, &e.MainThreadCallStackDepth})
    *v = ReadU32(s);
  for (uint32_t& v : e.MainThreadReturnAddresses) v = ReadU32(s);
  for (uint32_t& v : e.MainThreadReturnBufIds) v = ReadU32(s);
  for (int& v : e.MainThreadVariables) v = Io::ReadLE<int32_t>(s);
  e.MainThreadDialoguePageId = ReadU32(s);
  e.FlagWorkData.resize(ReadU32(s));
  Io::ReadArrayLE<uint8_t>(e.FlagWorkData.data(), s, e.FlagWorkData.size());
  e.ScrWorkData.resize(ReadU32(s));
  Io::ReadArrayLE<int32_t>(e.ScrWorkData.data(), s, e.ScrWorkData.size());
  if (version >= 2) {
    e.PhoneItemBits.resize(ReadU32(s));
    Io::ReadArrayLE<uint8_t>(e.PhoneItemBits.data(), s, e.PhoneItemBits.size());
  }
}

SaveError SaveSystem::WriteSaveFile() {
  using CF = Io::PhysicalFileStream::CreateFlagsMode;
  Io::Stream* raw;
  IoError err = Io::PhysicalFileStream::Create(
      SaveFilePath, &raw,
      CF::CREATE | CF::CREATE_DIRS | CF::WRITE | CF::TRUNCATE);
  if (err != IoError_OK) {
    ImpLog(LogLevel::Error, LogChannel::IO,
           "Failed to open save file {:s} for writing\n", SaveFilePath);
    return SaveError::Failed;
  }
  std::unique_ptr<Io::Stream> s(raw);

  Io::WriteArrayLE<char>(Magic, s.get(), sizeof(Magic));
  WriteU32(s.get(), SaveFormatVersion);
  WriteU32(s.get(), MaxFullSaves);
  WriteU32(s.get(), MaxQuickSaves);
  WriteRanges(s.get(), FlagWorkRanges);
  WriteRanges(s.get(), ScrWorkRanges);

  WriteU32(s.get(), (uint32_t)ReadLines.size());
  for (auto const& [scriptId, bits] : ReadLines) {
    WriteU32(s.get(), scriptId);
    WriteU32(s.get(), (uint32_t)bits.size());
    Io::WriteArrayLE<uint8_t>(bits.data(), s.get(), bits.size());
  }

  Io::WriteArrayLE<uint8_t>(QuickSaveRecentSortedId.data(), s.get(),
                            QuickSaveRecentSortedId.size());

  // format 2: global variables
  WriteRanges(s.get(), SystemFlagWorkRanges);
  WriteRanges(s.get(), SystemScrWorkRanges);
  Io::WriteLE<uint8_t>(s.get(), HasSystemData ? 1 : 0);
  WriteU32(s.get(), (uint32_t)SystemFlagWorkData.size());
  Io::WriteArrayLE<uint8_t>(SystemFlagWorkData.data(), s.get(),
                            SystemFlagWorkData.size());
  WriteU32(s.get(), (uint32_t)SystemScrWorkData.size());
  Io::WriteArrayLE<int32_t>(SystemScrWorkData.data(), s.get(),
                            SystemScrWorkData.size());

  for (SaveFileEntry const& e : FullEntries) WriteEntry(s.get(), e);
  for (SaveFileEntry const& e : QuickEntries) WriteEntry(s.get(), e);
  return SaveError::OK;
}

SaveError SaveSystem::CheckSaveFile() const {
  switch (Io::PathExists(SaveFilePath)) {
    case IoError_OK:
      return SaveError::OK;
    case IoError_NotFound:
      return SaveError::NotFound;
    default:
      return SaveError::Failed;
  }
}

SaveError SaveSystem::MountSaveFile(std::vector<QueuedTexture>&) {
  Io::Stream* raw;
  IoError err = Io::PhysicalFileStream::Create(SaveFilePath, &raw);
  if (err == IoError_NotFound) return SaveError::NotFound;
  if (err != IoError_OK) return SaveError::Corrupted;
  std::unique_ptr<Io::Stream> s(raw);

  char magic[sizeof(Magic)];
  Io::ReadArrayLE<char>(magic, s.get(), sizeof(magic));
  uint32_t version = 0;
  if (std::memcmp(magic, Magic, sizeof(Magic)) != 0 ||
      (version = ReadU32(s.get())) < 1 || version > SaveFormatVersion ||
      ReadU32(s.get()) != MaxFullSaves || ReadU32(s.get()) != MaxQuickSaves) {
    ImpLog(LogLevel::Error, LogChannel::IO,
           "{:s} is not an impacto SGHD save (version {:d})\n", SaveFilePath,
           SaveFormatVersion);
    return SaveError::Corrupted;
  }
  for (std::vector<uint32_t> const* expected :
       {&FlagWorkRanges, &ScrWorkRanges}) {
    std::vector<uint32_t> stored(ReadU32(s.get()));
    for (uint32_t& v : stored) v = ReadU32(s.get());
    if (stored != *expected) {
      ImpLog(LogLevel::Error, LogChannel::IO,
             "Save file variable ranges differ from the profile; not "
             "loading {:s}\n",
             SaveFilePath);
      return SaveError::Corrupted;
    }
  }

  ReadLines.clear();
  for (uint32_t n = ReadU32(s.get()); n > 0; n--) {
    uint32_t const scriptId = ReadU32(s.get());
    std::vector<uint8_t>& bits = ReadLines[scriptId];
    bits.resize(ReadU32(s.get()));
    Io::ReadArrayLE<uint8_t>(bits.data(), s.get(), bits.size());
  }

  Io::ReadArrayLE<uint8_t>(QuickSaveRecentSortedId.data(), s.get(),
                           QuickSaveRecentSortedId.size());

  SystemFlagWorkData.clear();
  SystemScrWorkData.clear();
  HasSystemData = false;
  if (version >= 2) {
    std::vector<uint32_t> storedFlags(ReadU32(s.get()));
    for (uint32_t& v : storedFlags) v = ReadU32(s.get());
    std::vector<uint32_t> storedScr(ReadU32(s.get()));
    for (uint32_t& v : storedScr) v = ReadU32(s.get());
    bool const present = Io::ReadLE<uint8_t>(s.get()) != 0;
    std::vector<uint8_t> flags(ReadU32(s.get()));
    Io::ReadArrayLE<uint8_t>(flags.data(), s.get(), flags.size());
    std::vector<int> values(ReadU32(s.get()));
    Io::ReadArrayLE<int32_t>(values.data(), s.get(), values.size());
    if (storedFlags == SystemFlagWorkRanges &&
        storedScr == SystemScrWorkRanges) {
      SystemFlagWorkData = std::move(flags);
      SystemScrWorkData = std::move(values);
      HasSystemData = present;
    } else {
      ImpLog(LogLevel::Warning, LogChannel::IO,
             "Save file system-data ranges differ from the profile; "
             "ignoring its global variables\n");
    }
  }

  for (SaveFileEntry& e : FullEntries) ReadEntry(s.get(), e, version);
  for (SaveFileEntry& e : QuickEntries) ReadEntry(s.get(), e, version);
  return SaveError::OK;
}

// --- read-line bitmap -------------------------------------------------------

void SaveSystem::SetLineRead(size_t scriptId, size_t lineId) {
  std::vector<uint8_t>& bits = ReadLines[(uint32_t)scriptId];
  if (bits.size() <= lineId / 8) bits.resize(lineId / 8 + 1);
  bits[lineId / 8] |= Flbit[lineId % 8];
}

bool SaveSystem::IsLineRead(size_t scriptId, size_t lineId) const {
  auto it = ReadLines.find((uint32_t)scriptId);
  if (it == ReadLines.end() || it->second.size() <= lineId / 8) return false;
  return it->second[lineId / 8] & Flbit[lineId % 8];
}

void SaveSystem::GetReadMessagesCount(int* totalMessageCount,
                                      int* readMessageCount) const {
  // Total line counts per script are unknown for SGHD.
  *totalMessageCount = 0;
  *readMessageCount = 0;
  for (auto const& [scriptId, bits] : ReadLines)
    for (uint8_t byte : bits) *readMessageCount += std::popcount(byte);
}

// --- per-slot accessors ------------------------------------------------------

uint32_t SaveSystem::GetSavePlayTime(SaveType type, int id) const {
  auto const* e = Entry(type, id);
  return e ? e->PlayTime : 0;
}

uint8_t SaveSystem::GetSaveFlags(SaveType type, int id) const {
  auto const* e = Entry(type, id);
  return e ? e->Flags : 0;
}

void SaveSystem::SetSaveFlags(SaveType type, int id, uint8_t flags) {
  if (auto* e = Entry(type, id)) e->Flags = flags;
}

tm const& SaveSystem::GetSaveDate(SaveType type, int id) const {
  static tm const empty{};
  auto const* e = Entry(type, id);
  return e ? e->SaveDate : empty;
}

uint8_t SaveSystem::GetSaveStatus(SaveType type, int id) const {
  auto const* e = Entry(type, id);
  return e ? e->Status : 0;
}

int SaveSystem::GetSaveTitle(SaveType type, int id) const {
  auto const* e = Entry(type, id);
  return e ? e->SwTitle : 0;
}

Sprite& SaveSystem::GetSaveThumbnail(SaveType type, int id) {
  SaveFileEntry* e = Entry(type, id);
  return e ? e->SaveThumbnail : WorkingEntry.SaveThumbnail;
}

}  // namespace SGHD
}  // namespace Impacto
