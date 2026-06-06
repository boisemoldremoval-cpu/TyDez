#!/usr/bin/env python3
"""
Generate Pixar-style 3D TyGuy shots with Google Veo (google-genai SDK), seeded
from his real character art via image-to-video for tight consistency.

    export GEMINI_API_KEY=...                 # never commit
    python3 veo_gen.py --image tyguy_seed.png 1          # one seeded test shot
    python3 veo_gen.py --image tyguy_seed.png            # all hosted shots
    python3 veo_gen.py --vertical --image tyguy_seed.png 1 6

Then: python3 assemble_3d.py shot1.mp4 ... --out tyguy_pixar.mp4

NOTE: Veo is paid (~a few $ per ~8s clip); generation is async (1-3 min each).
"""

import os
import sys
import time

from google import genai
from google.genai import types

MODEL = os.environ.get("VEO_MODEL", "veo-3.0-generate-001")

STYLE = (" Pixar/Disney-style 3D animation, same character design as the starting "
         "image, cinematic lighting, vibrant colors, high detail, family-friendly. "
         "No subtitles, no on-screen text.")

# TyGuy-hosted kindness lesson; each shot is seeded with his reference image so
# he stays perfectly on-model. He talks to camera (Veo generates his voice).
SHOTS = [
    "The 3D cartoon young man waves cheerfully at the camera with a big friendly "
    "smile and says, \"Hey friends! It's TyGuy!\" Bright brand-blue background with "
    "golden sparkles. Upbeat happy music." + STYLE,
    "The 3D cartoon young man points at the camera with an energetic grin and says, "
    "\"Today, let's talk about being kind!\" Brand-blue background, golden sparkles, "
    "playful music." + STYLE,
    "The 3D cartoon young man tilts his head with a thoughtful, caring expression, "
    "hand near his chin, and says, \"Ever see someone sitting all alone?\" Soft "
    "gentle music, brand-blue background." + STYLE,
    "The 3D cartoon young man places his hand on his heart with a warm sincere smile "
    "and says, \"The Bible tells us to love our neighbor.\" Soft heavenly light, "
    "subtle glowing golden crosses, inspirational music." + STYLE,
    "The 3D cartoon young man gestures welcomingly with both hands, encouraging and "
    "upbeat, and says, \"So say hi, share a smile, and include them!\" Bright "
    "brand-blue background, golden sparkles, uplifting music." + STYLE,
    "The 3D cartoon young man gives an enthusiastic double thumbs-up with a huge grin "
    "and says, \"Be kind, have fun, and be you!\" Bright brand-blue background with "
    "floating golden crosses and sparkle accents, triumphant playful sting." + STYLE,
]
NEG = ("subtitles, captions, on-screen text, watermark, distorted face, extra fingers, "
       "extra limbs, flat 2D, hand-drawn, low quality, blurry, deformed, different character")


def main():
    args = sys.argv[1:]
    aspect = "9:16" if "--vertical" in args else "16:9"
    args = [a for a in args if a != "--vertical"]
    image_path = None
    if "--image" in args:
        i = args.index("--image")
        image_path = args[i + 1]
        del args[i:i + 2]
    which = [int(a) for a in args] if args else list(range(1, len(SHOTS) + 1))

    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        print("ERROR: set GEMINI_API_KEY (Google AI key with Veo access).")
        raise SystemExit(1)
    client = genai.Client(api_key=key)

    seed_img = None
    if image_path:
        with open(image_path, "rb") as f:
            data = f.read()
        mime = "image/png" if image_path.lower().endswith("png") else "image/jpeg"
        seed_img = types.Image(image_bytes=data, mime_type=mime)
        print(f"seeding image-to-video from {image_path}")

    for n in which:
        out = f"shot{n}.mp4"
        print(f"[shot {n}] generating ({aspect})...")
        kwargs = dict(model=MODEL, prompt=SHOTS[n - 1],
                      config=types.GenerateVideosConfig(aspect_ratio=aspect,
                                                        number_of_videos=1,
                                                        negative_prompt=NEG))
        if seed_img is not None:
            kwargs["image"] = seed_img
        op = client.models.generate_videos(**kwargs)
        t0 = time.time()
        while not op.done:
            time.sleep(10)
            op = client.operations.get(op)
            print(f"  ...{time.time()-t0:.0f}s")
        client.files.download(file=op.response.generated_videos[0].video)
        op.response.generated_videos[0].video.save(out)
        print(f"  saved {out}")
    print("Done. Next: python3 assemble_3d.py " +
          " ".join(f"shot{n}.mp4" for n in which) + " --out tyguy_pixar.mp4")


if __name__ == "__main__":
    main()
