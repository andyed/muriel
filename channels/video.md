# Video — Product Demos, GIFs, Recorded Talks

Scripted screen recordings with tooltip overlays for YouTube/social. ffmpeg for trim/concat/burn. `desktop-control` MCP for mouse choreography. AppleScript for menu automation.

Part of the [muriel](../muriel.md) skill — see the top-level index for mission, universal rules, and channel map.

## Tools available

| Tool | What it does | How to invoke |
|------|-------------|---------------|
| `desktop-control` MCP | Move mouse, click, key combos, screenshots | `mcp__desktop-control__move_mouse`, `__click`, `__key_combo` |
| App-specific skill | Switch modes or toggle features in the app being demoed via AppleScript menus | `/<app> mode <name>` (project-specific) |
| AppleScript (direct) | Any macOS UI automation — menu clicks, window focus, keystrokes | `osascript -e '...'` |
| macOS screen recording | Capture video | User starts with `Cmd+Shift+5`, agent controls the app |
| ffmpeg (homebrew-ffmpeg tap) | Trim, burn captions, add music, encode | Hard-burn via `subtitles` filter (libass) |

## Workflow

1. **Write a tooltip manifest** — JSON array of `{start, end, text}` objects
2. **Script the choreography** — `desktop-control` moves the mouse on timed coordinates; AppleScript switches modes
3. **User records** with `Cmd+Shift+5` while agent drives the app
4. **Post-process**: `burn-tooltips.sh manifest.json raw.mov output.mp4`
   - Generates SRT from manifest
   - Burns captions via ffmpeg `subtitles` filter (Helvetica 24px, white, black outline)
   - Trims with `-ss` / `-t` flags
   - Drops audio with `-an` when needed
   - H.264 CRF 22, faststart for YouTube

## ffmpeg setup

The default `brew install ffmpeg` lacks `drawtext`/`subtitles` filters. Install the full version:
```bash
brew uninstall ffmpeg
brew tap homebrew-ffmpeg/ffmpeg
brew install homebrew-ffmpeg/ffmpeg/ffmpeg
```
This includes freetype, libass, fontconfig — enables `drawtext`, `subtitles`, and `ass` filters.

## Tooltip burn script

A `burn-tooltips.sh` script (see your app repo or [`muriel/tools/`](../tools/)) — two modes:
```bash
# SRT only (no ffmpeg needed)
burn-tooltips.sh tooltips.json output.srt

# Full pipeline: trim + burn + optional music
burn-tooltips.sh tooltips.json raw.mov output.mp4 [music.mp3]
```

Uses `subtitles` filter (libass) for hard-burn. Falls back to soft-sub mux if drawtext unavailable. Music mixed at 15% volume.

## Lessons learned

- **Trim first, caption second** — tooltip timecodes are relative to the trimmed video, not the raw recording. Use `-ss` to skip dead intro before the filter chain.
- **Drop audio with `-an`** — screen recordings capture system audio, dogs barking, etc.
- **macOS filenames have Unicode spaces** — `PM` in screen recording filenames uses a narrow no-break space (U+202F). Use glob matching, not exact strings.
- **Excalidraw: skip hand-drawn** — use `roughness: 0`, `fontFamily: 2` (Helvetica), `fillStyle: "solid"`. The hand-drawn aesthetic reads as fake, not charming.
- **SRT for YouTube** — even with hard-burned captions, upload the SRT too. YouTube auto-translates it.

## ffmpeg editing recipes

Standalone operations for cutting, joining, and splitting video outside the tooltip pipeline.

```bash
# Cut segment (fast, keyframe-aligned)
ffmpeg -ss 00:00:10 -to 00:00:30 -i input.mp4 -c copy output.mp4

# Cut segment (precise, re-encodes)
ffmpeg -ss 00:00:10 -i input.mp4 -t 20 -c:v libx264 -c:a aac output.mp4

# Last N seconds
ffmpeg -sseof -30 -i input.mp4 -c copy output.mp4

# Concatenate via file list (recommended — works across codecs)
# list.txt contains: file 'clip1.mp4'\nfile 'clip2.mp4'\nfile 'clip3.mp4'
ffmpeg -f concat -safe 0 -i list.txt -c copy output.mp4

# Concatenate with re-encode (when codecs differ)
ffmpeg -f concat -safe 0 -i list.txt -c:v libx264 -c:a aac output.mp4

# Split into fixed-length segments
ffmpeg -i input.mp4 -c copy -f segment -segment_time 60 -reset_timestamps 1 output_%03d.mp4
```

**`-c copy` vs re-encode:** `-c copy` is instant but cuts on keyframes (may be off by a few frames). Add `-c:v libx264 -c:a aac` for frame-accurate cuts at the cost of speed. `-ss` before `-i` is faster; after `-i` is more precise.

## Design doc

See [`docs/PERMUTE.md`](docs/PERMUTE.md) for the infographic aspiration: Tufte, Bertin, Gestalt, CRAP, semantic zoom, small multiples, linked displays.

## Anti-patterns

- **Don't capture with system audio on** unless narration is intentional. Dogs bark, notifications ding, system alerts leak into shipped reels.
- **Don't burn subtitles in the default SRT font.** Use the brand's typography so captions feel authored, not tacked on.
- **Don't edit at 30 fps then upload at 60** (or vice versa). Match the recording's frame rate or re-encode deliberately.
- **Don't ship a demo whose first 3 seconds don't hook attention.** The opening frame is most of the commitment decision.
