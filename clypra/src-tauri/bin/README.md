# FFmpeg / FFprobe sidecars

Tauri bundles these as `externalBin` entries `bin/ffmpeg` and `bin/ffprobe`. For each host triple you ship, place a **real executable** at:

| Binary  | macOS ARM                      | macOS Intel                   | Linux x86_64                       | Linux ARM64                         | Windows x86_64                       | Windows ARM64                         |
| ------- | ------------------------------ | ----------------------------- | ---------------------------------- | ----------------------------------- | ------------------------------------ | ------------------------------------- |
| ffmpeg  | `ffmpeg-aarch64-apple-darwin`  | `ffmpeg-x86_64-apple-darwin`  | `ffmpeg-x86_64-unknown-linux-gnu`  | `ffmpeg-aarch64-unknown-linux-gnu`  | `ffmpeg-x86_64-pc-windows-msvc.exe`  | `ffmpeg-aarch64-pc-windows-msvc.exe`  |
| ffprobe | `ffprobe-aarch64-apple-darwin` | `ffprobe-x86_64-apple-darwin` | `ffprobe-x86_64-unknown-linux-gnu` | `ffprobe-aarch64-unknown-linux-gnu` | `ffprobe-x86_64-pc-windows-msvc.exe` | `ffprobe-aarch64-pc-windows-msvc.exe` |

The repo ships **small shell/batch wrappers** that delegate to `ffmpeg` / `ffprobe` on your `PATH` so `cargo tauri dev` works before you drop in static builds. For distribution, replace each file with a **static** or **framework-linked** build from a trusted source (e.g. your own build from [ffmpeg.org](https://ffmpeg.org/) or a vetted static bundle), then:

```bash
chmod +x src-tauri/bin/ffmpeg-* src-tauri/bin/ffprobe-*
```

## Compliance

FFmpeg is typically LGPL/GPL depending on enabled codecs. Ensure your **LICENSE** / third-party notices match the binaries you ship.

## Code signing & notarization

Sidecar binaries must be signed and stapled with the same workflow as your main app bundle, or macOS Gatekeeper may block them.
