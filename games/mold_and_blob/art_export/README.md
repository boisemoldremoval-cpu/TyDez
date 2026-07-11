# art_export — source art for AI redraws

High-resolution (10x) renders of every Mold & Blob asset on a **transparent
background**, plus two full-scene mockups. Hand these to an image model
(ChatGPT / DALL·E / etc.) to redraw them at higher quality, then drop the
results back in.

| File | What it is |
|------|-----------|
| `sprite_tyguy.png` | TyGuy — the mold-removal hero (hard hat + backpack sprayer) |
| `sprite_blob.png` | Blob — the companion (follow form) |
| `sprite_mold.png` | A mold patch (the enemy) |
| `sprite_trampoline.png` | Blob transformed into a trampoline |
| `sprite_bridge.png` | Blob transformed into a bridge |
| `sprite_ladder.png` | Blob transformed into a ladder |
| `sprite_door_open.png` / `sprite_door_closed.png` | Exit door (cleared / not cleared) |
| `scene_gameplay.png` / `scene_menu.png` | Full 960x640 mockups for overall art direction |

## Palette (match these hexes)

`#56D6A5` brand green · `#288C68` dark green · `#68D6AA` blob · `#7EAC52` mold
green · `#486A2E` mold dark · `#EAC8A8` skin · `#D2B060` door · `#101816` outline.

## Redraw prompt (per sprite)

> Redraw this game sprite at higher quality. Keep the same silhouette,
> proportions, and pose, and the same green palette. Clean polished 2D game art
> with smooth shading and soft rim light. Transparent background, PNG, no text,
> no drop shadow. Style: friendly modern cartoon platformer.

Ask for transparent PNGs with the subject centered at roughly the same
width:height as the source so they line up with the game's positions. The game
currently draws its art in code; sprite-image loading can be added so these
PNGs replace the drawn shapes.
