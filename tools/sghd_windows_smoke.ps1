<#
.SYNOPSIS
  Run a local STEINS;GATE title-to-gameplay smoke test on Windows.
.DESCRIPTION
  Uses only the owner's own game archives and executable. Logs and optional
  screenshots stay local; nothing is sent to GitHub or added to the repo.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\sghd_windows_smoke.ps1 -EngineDir "C:\impacto-testing\t6" -Screenshots
#>
param(
  [Parameter(Mandatory=$true)][string]$EngineDir,
  [int]$TitleWaitSeconds = 9,
  [int]$GameplayWaitSeconds = 25,
  [switch]$Screenshots,
  [switch]$CloseAfter
)
$ErrorActionPreference = "Stop"
$EngineDir = (Resolve-Path -LiteralPath $EngineDir).Path
$exe = Join-Path $EngineDir "impacto.exe"
$assets = Join-Path $EngineDir "gamedata\sghd\script.mpk"
if (!(Test-Path -LiteralPath $exe)) { throw "impacto.exe is missing from EngineDir" }
if (!(Test-Path -LiteralPath $assets)) { throw "Move your own MPKs into gamedata\sghd first" }

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class ImpactoWindow {
  [StructLayout(LayoutKind.Sequential)]
  public struct Rect { public int Left, Top, Right, Bottom; }
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out Rect rect);
}
'@

function Get-MainWindow([System.Diagnostics.Process]$proc) {
  for ($i = 0; $i -lt 100; $i++) {
    $proc.Refresh()
    if ($proc.HasExited) { throw "Impacto exited before opening a window" }
    if ($proc.MainWindowHandle -ne [IntPtr]::Zero) { return $proc.MainWindowHandle }
    Start-Sleep -Milliseconds 250
  }
  throw "No visible title window within 25 seconds"
}

function Send-SafeEnter([IntPtr]$window) {
  [void][ImpactoWindow]::SetForegroundWindow($window)
  Start-Sleep -Milliseconds 200
  if ([ImpactoWindow]::GetForegroundWindow() -ne $window) {
    throw "Windows refused foreground focus: won't type into a different app"
  }
  [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
}

function Capture-Window([IntPtr]$window, [string]$path) {
  $rect = New-Object ImpactoWindow+Rect
  if (![ImpactoWindow]::GetWindowRect($window, [ref]$rect)) { return }
  $width = $rect.Right - $rect.Left
  $height = $rect.Bottom - $rect.Top
  if ($width -le 0 -or $height -le 0) { return }
  $bitmap = New-Object System.Drawing.Bitmap($width, $height)
  $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
  try {
    $graphics.CopyFromScreen($rect.Left, $rect.Top, 0, 0,
                             (New-Object System.Drawing.Size($width, $height)))
    $bitmap.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
  } finally {
    $graphics.Dispose()
    $bitmap.Dispose()
  }
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$outdir = Join-Path $EngineDir ("smoke-local-" + $stamp)
New-Item -ItemType Directory -Path $outdir | Out-Null
$logPath = Join-Path $outdir "impacto.log"
$configPath = Join-Path $outdir "config.toml"
$quote = [char]34
$arguments = "-g sghd -uc $quote$configPath$quote -ll Debug -lf $quote$logPath$quote"
Write-Host "Starting private Windows smoke test. Output: $outdir"
$proc = Start-Process -FilePath $exe -ArgumentList $arguments -WorkingDirectory $EngineDir -PassThru
try {
  $handle = Get-MainWindow $proc
  Start-Sleep -Seconds $TitleWaitSeconds
  $proc.Refresh()
  if ($proc.HasExited) { throw "Impacto exited before title input" }

  if ($Screenshots) { Capture-Window $handle (Join-Path $outdir "01-press-enter.png") }
  Send-SafeEnter $handle
  Start-Sleep -Seconds 2
  if ($Screenshots) { Capture-Window $handle (Join-Path $outdir "02-title-menu.png") }
  Send-SafeEnter $handle
  Start-Sleep -Seconds $GameplayWaitSeconds
  $proc.Refresh()
  if (!$proc.HasExited -and $Screenshots) {
    Capture-Window $handle (Join-Path $outdir "03-gameplay.png")
  }

  $log = if (Test-Path -LiteralPath $logPath) {
    Get-Content -LiteralPath $logPath -Raw
  } else { "" }
  $report = [ordered]@{
    "press_start_accepted" = $log.Contains("TitleMenu: press start")
    "start_selected" = $log.Contains("TitleMenu: main menu choice (SW_TITLECUR = 0)")
    "main_script_loaded" = $log.Contains('Loading script "MAIN00.SCX"')
    "first_scene_loaded" = $log.Contains('Loading script "SG00_01.SCX"')
    "missing_movie_events" = ([regex]::Matches($log, "Failed to open movie for playback")).Count
    "unsupported_background_modes" = ([regex]::Matches($log, "Unknown background fade/render mode")).Count
    "phone_stub_events" = ([regex]::Matches($log, "STUB instruction Phone")).Count
    "process_running_at_end" = !$proc.HasExited
    "exit_code_if_exited" = $(if ($proc.HasExited) { $proc.ExitCode } else { $null })
  }
  $report | ConvertTo-Json | Write-Host
  Write-Host "Private logs and screenshots (if enabled) stay in $outdir"
  if (!$report["first_scene_loaded"]) {
    Write-Warning "Story-scene load not confirmed: do not approve the gameplay change yet"
  }
}
finally {
  if ($CloseAfter -and !$proc.HasExited) {
    [void]$proc.CloseMainWindow()
    if (!$proc.WaitForExit(3000)) { Stop-Process -Id $proc.Id -Force }
  }
}
