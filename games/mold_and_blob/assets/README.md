# assets — drop-in art for Mold & Blob

Put **transparent-background PNGs** with any of these exact names in this folder
and the game uses them automatically (menu + gameplay). Anything missing falls
back to the built-in vector art, so you can add them one at a time.

| Filename | Replaces | Framing tips |
|----------|----------|--------------|
| `tyguy.png` | The player character | Full body, **facing right**, centered, feet near the bottom. The game mirrors it when walking left. |
| `blob.png` | The companion (follow form) | Centered, roughly square. |
| `mold.png` | A mold patch | Centered, roughly square, fills most of the frame. |
| `trampoline.png` | Blob → trampoline | Wide, horizontal. |
| `bridge.png` | Blob → bridge | Long horizontal plank. |
| `ladder.png` | Blob → ladder | Tall vertical. |
| `door_open.png` | Exit door (level cleared) | Portrait, ~0.85 wide:tall. |
| `door_closed.png` | Exit door (not cleared) | Same size as `door_open`. |
| `background.png` | The whole background | 3:2 landscape (960x640-ish or larger). |
| `platform.png` | The ground/platform texture | Wide tile; it's stretched per platform. |

**Must be transparent PNGs** (the subject cut out). If your render has a solid
background, run it through a background remover first, or ask the image model to
output a transparent/plain-white background. See
`../CHATGPT_3D_PROMPTS.md` for prompts that produce game-ready, transparent
sprites in a consistent 3D style.

Higher resolution is better — the game renders at 2x and scales art down, so
1024px+ per sprite looks crisp.
