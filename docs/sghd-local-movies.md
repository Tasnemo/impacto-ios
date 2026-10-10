# Local-only Steam movie playback (original English STEINS;GATE)

**Original and converted Steam videos must never be committed to GitHub.**
This feature uses files from the owner's own legally installed Steam copy.
It does not bundle a Bink 2 decoder or game footage.

## Why the original BK2 folder does not work

The Steam release has 38 Bink 2 movies stored as loose `.bk2` files in
`USRDIR/movie/1920x1080`. FFmpeg can recognize but **cannot decode** their
video stream. Copying the originals to `gamedata/sghd/movie` is not enough.

The movie script instructions name numeric IDs. Steam `Game.exe` has a
38-entry movie-name table. The engine now resolves SGHD movie IDs to
the corresponding local **`.mp4` filename**, rather than relying on
alphabetical directory position. The folder may contain only some of the
38 converted files; missing movies continue to skip as before.

## Minimal visual test: convert the title movie

1. Use the official RAD Video Tools for Windows:
   https://www.radgametools.com/bnkdown.htm
2. Open the original `USRDIR/movie/1920x1080/title.bk2` using RAD.
   Select **Convert a file**, choose **MP4** as output type, and output a
   file called `title.mp4`. The RAD Video Tools offer MP4 output through
   Windows Media Foundation, but verify that this specific Steam file
   actually converts and that audio is intact.
3. Place the converted file in your local Impacto test installation:

   `t8/gamedata/sghd/movie-converted/title.mp4`

   Create the `movie-converted` directory if necessary. Use the filename
   in lowercase; on Linux, file lookups are case-sensitive.
4. **Only after installing a Windows executable built from the movie PR:**
   run from the `t8` test directory:

   ```bash
   ./impacto.exe -g sghd -uc ./round13-config.toml -ll Debug -lf round13-1.log
   ```

   A config can be prepared by copying a prior config into
   `round13-config.toml`. Do not override existing local saves by
   accident. Test the title movie and then START. Close the process before
   sharing its log.
5. If RAD cannot decode or export this title BK2, **stop at that step** and
   report the error; this is a conversion-path blocker, not an Impacto bug.

The `movie-converted` folder should contain **MP4s only** named using the
*original BK2's stem*, e.g. `title.mp4`, `op.mp4`,
`prologue01.mp4`. No archive packing, numeric prefix, placeholder files,
or bulk conversion is required.

## Testing and safety

- Keep your original `.bk2` files unchanged in the Steam installation.
- Conversion output is private, local, and user-generated.
- The public GitHub PR contains code, filenames, documentation and synthetic
  test fixtures only; neither Steam footage nor converted videos.
- Unit/CI compile success does **not** establish A/V sync or a successful
  gameplay transition; review it on the owner's Windows machine.
- The existing synthetic malformed-Bink regression probe still verifies
  graceful handling of unsupported `.bk2` files.
