#!/usr/bin/env python3
"""Asset-free Linux launcher and CLI checks; run under xvfb-run."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


def main():
    executable = Path(sys.argv[1]).resolve(strict=True)
    env = dict(os.environ, SDL_VIDEO_DRIVER="x11", LIBGL_ALWAYS_SOFTWARE="1")
    with tempfile.TemporaryDirectory(prefix="impacto-smoke-") as temporary:
        config = str(Path(temporary) / "userconfig.toml")
        result = subprocess.run(
            [str(executable), "-g"], env=env, capture_output=True,
            text=True, timeout=15,
        )
        output = result.stdout + result.stderr
        print(output, end="")
        assert result.returncode == 1, f"CLI exit: {result.returncode}"
        assert "Invalid number of arguments" in output
        print("PASS: missing CLI parameter rejected (exit 1)")

        # A fresh config avoids selecting a user's game. Do not pass -g:
        # all upstream game/viewer profiles need commercial assets.
        with tempfile.TemporaryFile(mode="w+") as log:
            process = subprocess.Popen(
                [str(executable), "-ll", "Debug", "-uc", config],
                env=env, stdout=log, stderr=subprocess.STDOUT,
            )
            try:
                time.sleep(5)
                assert process.poll() is None, "Launcher exited before shutdown"
                # SDL translates SIGTERM to its normal quit event.
                process.terminate()
                assert process.wait(timeout=15) == 0, "Launcher exit was not 0"
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                log.seek(0)
                output = log.read()
                print(output, end="")
        for marker in ("Lua profile execute success", "Creating window",
                       "Window size (screen coords):", "Bye!"):
            assert marker in output, f"Missing startup/shutdown marker: {marker}"
        assert "[Fatal]" not in output and "[Error]" not in output
        print("PASS: asset-free launcher stayed alive for 5s and quit cleanly (exit 0)")


if __name__ == "__main__":
    main()
