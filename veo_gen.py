#!/usr/bin/env python3
"""
Generate the TyGuy 3D shots directly with Google Veo (google-genai SDK), then
assemble with assemble_3d.py.

Requires a Google AI (Gemini) API key WITH VEO ACCESS:
    export GEMINI_API_KEY=...        # never commit this
    python3 veo_gen.py               # all 8 shots -> shot1.mp4..shot8.mp4
    python3 veo_gen.py 2             # just shot 2 (cheap test)
    python3 veo_gen.py --vertical 1 4 8

NOTE: Veo is a paid API (~ a few dollars per ~8s clip). This will spend credits
on the key you provide. Generation is async; each clip can take 1-3 minutes.
"""

import os
import sys
import time

from google import genai
from google.genai import types

MODEL = os.environ.get("VEO_MODEL", "veo-3.0-generate-001")

CHAR_TY = (
    "TyGuy, a friendly upbeat young man, late 20s, warm tan skin, short dark-brown "
    "spiky quiff hair with faded sides, light stubble, big genuine smile, expressive "
    "brown eyes; wearing a royal-blue pullover hoodie with a bold white 'T' on the chest "
    "and white drawstrings, black joggers, royal-blue high-top sneakers with white soles. "
    "Appealing Pixar-style 3D character, slightly caricatured, very expressive."
)
CHAR_MIA = (
    "Mia, a shy 9-year-old girl, fair skin, brown hair in a side ponytail, big expressive "
    "eyes, coral-pink top, blue jeans, white sneakers; Pixar-style 3D."
)
STYLE = (
    " Pixar/Disney-style 3D animation, cinematic three-point lighting, soft global "
    "illumination, subsurface-scattering skin, shallow depth of field, warm vibrant colors, "
    "volumetric sunlight, high-detail studio render, family-friendly. No subtitles, no on-screen text."
)
NEG = ("subtitles, captions, on-screen text, watermark, logo, distorted face, extra fingers, "
       "extra limbs, flat 2D, hand-drawn, low quality, blurry, deformed")

SHOTS = [
    f"{CHAR_MIA} Wide establishing shot of a sunny cheerful schoolyard with grass, a leafy tree "
    f"and a friendly school building; Mia sits alone on a bench, shoulders slumped, looking down "
    f"sadly. Slow cinematic dolly-in. Ambient playground sounds; soft mellow piano.{STYLE}",
    f"{CHAR_MIA} Two cheerful kids walk past Mia chatting and laughing, not noticing her; Mia "
    f"lowers her head. Medium tracking shot. Kids laughing, footsteps; wistful score.{STYLE}",
    f"{CHAR_TY} TyGuy notices a lonely girl sitting alone across the schoolyard; his grin softens "
    f"to a caring expression. Over-the-shoulder then push-in on his kind face. He says warmly, "
    f"\"Hey there! Are you new here?\" gentle hopeful music.{STYLE}",
    f"{CHAR_TY} {CHAR_MIA} TyGuy walks over and crouches to the girl's eye level by the bench, "
    f"smiling warmly with an open friendly gesture; Mia looks up hopeful. Smooth two-shot, slight arc. "
    f"He says cheerfully, \"Hi, I'm Ty! Come hang out with us!\" uplifting music.{STYLE}",
    f"{CHAR_MIA} Mia breaks into a big joyful smile, eyes bright, cheeks blushing, a happy little "
    f"bounce. Medium close-up push-in, warm bokeh sparkles. She says brightly, \"Really? Thank you!\" "
    f"warm heartfelt music.{STYLE}",
    f"{CHAR_TY} {CHAR_MIA} TyGuy and Mia walk side by side toward a small group of welcoming kids, "
    f"both smiling. Tracking shot, slight low angle, golden light. Warm triumphant music. "
    f"Narrator: \"One small kindness changed her whole day.\"{STYLE}",
    f"{CHAR_TY} TyGuy stands in soft heavenly light with gentle golden sparkles and subtle glowing "
    f"cross motifs, hand on heart, sincere expression to camera. Slow reverent push-in. He says, "
    f"\"Be kind to one another, tender-hearted, forgiving one another.\" soft inspirational strings.{STYLE}",
    f"{CHAR_TY} TyGuy faces camera, enthusiastic thumbs-up and big grin, energetic pose; bright "
    f"brand-blue background with golden sparkle accents and floating golden crosses. Dynamic zoom-in. "
    f"He says energetically, \"Be kind, have fun, and be you!\" upbeat playful sting.{STYLE}",
]


def main():
    args = sys.argv[1:]
    aspect = "9:16" if "--vertical" in args else "16:9"
    args = [a for a in args if a != "--vertical"]
    which = [int(a) for a in args] if args else list(range(1, len(SHOTS) + 1))

    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        print("ERROR: set GEMINI_API_KEY (Google AI key with Veo access).")
        raise SystemExit(1)
    client = genai.Client(api_key=key)

    for n in which:
        prompt = SHOTS[n - 1]
        out = f"shot{n}.mp4"
        print(f"[shot {n}] generating ({aspect})...")
        op = client.models.generate_videos(
            model=MODEL, prompt=prompt,
            config=types.GenerateVideosConfig(aspect_ratio=aspect,
                                              number_of_videos=1,
                                              negative_prompt=NEG),
        )
        t0 = time.time()
        while not op.done:
            time.sleep(10)
            op = client.operations.get(op)
            print(f"  ...{time.time()-t0:.0f}s")
        vids = op.response.generated_videos
        client.files.download(file=vids[0].video)
        vids[0].video.save(out)
        print(f"  saved {out}")
    print("Done. Now: python3 assemble_3d.py " +
          " ".join(f"shot{n}.mp4" for n in which))


if __name__ == "__main__":
    main()
