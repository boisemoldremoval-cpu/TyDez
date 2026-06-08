#!/usr/bin/env python3
"""
Generate the Pixar-style 3D "Block Tower" scene with Google Veo, seeded from
TyGuy's real character art (image-to-video) so he stays perfectly on-model.

This is the 3D counterpart of make_blocks_clip.py and recreates the reference
clip: TyGuy joyfully builds a colorful toy-block castle in a sunny, flowery
park; another boy storms over and kicks it down; TyGuy reacts, hurt.

    pip install google-genai
    export GEMINI_API_KEY=...                       # Google AI key with Veo access
    python3 veo_blocks.py                            # one ~8s seeded shot -> shotB1.mp4
    python3 veo_blocks.py --two                      # build + kick as two shots
    python3 veo_blocks.py --vertical                 # 9:16 for shorts/reels

Then (for --two): python3 assemble_3d.py shotB1.mp4 shotB2.mp4 --out blocks_pixar.mp4

NOTE: Veo is paid (~a few $ per ~8s clip); generation is async (1-3 min each).
Set VEO_MODEL=veo-3.0-fast-generate-001 for the cheaper/faster model.
"""

import os
import sys
import time

from google import genai
from google.genai import types

MODEL = os.environ.get("VEO_MODEL", "veo-3.0-generate-001")
SEED_IMG = "tyguy_seed.png"

STYLE = (" Pixar/Disney-style 3D animation, same character design as the starting "
         "image, cinematic lighting, warm vibrant colors, shallow depth of field, "
         "high detail, family-friendly. No subtitles, no on-screen text.")
NEG = ("subtitles, captions, on-screen text, watermark, distorted face, extra fingers, "
       "extra limbs, flat 2D, hand-drawn, low quality, blurry, deformed, different "
       "character, violence, blood")

TY = ("The same 3D cartoon boy from the starting image (royal-blue hoodie with a white "
      "'T', dark spiky hair)")
SETTING = ("a sunny green park meadow full of colorful flowers, leafy trees and a bright "
           "blue sky")
OTHER = ("another 3D cartoon boy with messy auburn hair, a green t-shirt and grey shorts")

# Single ~8s shot that captures the whole beat.
ONE = (
    f"{TY} kneels happily in {SETTING}, carefully stacking bright red, blue, yellow and "
    f"green toy building blocks into a little castle tower, smiling with delight. Then "
    f"{OTHER} storms in from the side and kicks the tower, sending the colorful blocks "
    f"tumbling and scattering across the grass. {TY}'s face falls in shock and sadness "
    f"while the other boy stands with arms crossed, scowling. Gentle storybook music that "
    f"turns dismayed; soft outdoor ambience; no dialogue." + STYLE
)

# Two-shot version for a fuller ~16s cut.
TWO = [
    (f"{TY} kneels in {SETTING}, joyfully and carefully stacking bright red, blue, yellow "
     f"and green toy building blocks into a tall little castle tower, beaming with pride. "
     f"Warm cheerful storybook music, soft birdsong, gentle camera push-in. No dialogue."
     + STYLE),
    (f"In {SETTING}, {OTHER} storms up to a colorful toy-block castle and kicks it over, "
     f"the blocks tumbling and scattering across the grass; {TY} kneeling nearby gasps, "
     f"his face falling to hurt sadness, while the other boy stands with arms crossed, "
     f"scowling. Music turns dismayed; soft thud and clatter; no dialogue." + STYLE),
]


def _gen(client, prompt, seed, aspect, out):
    print(f"[{out}] generating ({aspect})...")
    kwargs = dict(model=MODEL, prompt=prompt,
                  config=types.GenerateVideosConfig(aspect_ratio=aspect,
                                                    number_of_videos=1,
                                                    negative_prompt=NEG))
    if seed is not None:
        kwargs["image"] = seed
    op = client.models.generate_videos(**kwargs)
    t0 = time.time()
    while not op.done:
        time.sleep(10)
        op = client.operations.get(op)
        print(f"  ...{time.time()-t0:.0f}s")
    if getattr(op, "error", None):
        print(f"  !! ERROR: {op.error}")
        return False
    resp = op.response
    vids = getattr(resp, "generated_videos", None) if resp else None
    if not vids:
        cnt = getattr(resp, "rai_media_filtered_count", None)
        reasons = getattr(resp, "rai_media_filtered_reasons", None)
        print(f"  !! NO video (content-filtered). count={cnt} reasons={reasons}")
        return False
    client.files.download(file=vids[0].video)
    vids[0].video.save(out)
    print(f"  saved {out}  ({time.time()-t0:.0f}s)")
    return True


def main():
    args = sys.argv[1:]
    aspect = "9:16" if "--vertical" in args else "16:9"
    two = "--two" in args

    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        print("ERROR: set GEMINI_API_KEY (Google AI key with Veo access).")
        raise SystemExit(1)
    client = genai.Client(api_key=key)

    seed = None
    if os.path.exists(SEED_IMG):
        with open(SEED_IMG, "rb") as f:
            seed = types.Image(image_bytes=f.read(), mime_type="image/png")
        print(f"seeding image-to-video from {SEED_IMG}")

    if two:
        ok = all(_gen(client, p, seed, aspect, f"shotB{i+1}.mp4")
                 for i, p in enumerate(TWO))
        if ok:
            print("Done. Assemble: python3 assemble_3d.py shotB1.mp4 shotB2.mp4 "
                  "--out blocks_pixar.mp4")
    else:
        _gen(client, ONE, seed, aspect, "shotB1.mp4")
        print("Done -> shotB1.mp4")


if __name__ == "__main__":
    main()
