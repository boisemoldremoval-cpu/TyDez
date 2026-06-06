#!/usr/bin/env python3
"""
Generate the 5-minute "Love Your Neighbor" film with Veo (see STORY_5MIN.md).

TyGuy shots are image-seeded from tyguy_seed.png; parable / modern shots are
text-prompted from the character bible. Veo generates each character's voice,
SFX, and the backgrounds described in the prompt.

    export GEMINI_API_KEY=...
    python3 veo_story.py 1 2 3 4 5          # generate specific shots
    python3 veo_story.py --act 1            # generate an act (1..5)
    python3 veo_story.py                    # ALL 39 shots (big spend!)
    # then: python3 assemble_3d.py shot1.mp4 ... shot39.mp4 --out love_your_neighbor.mp4

Set VEO_MODEL=veo-3.0-fast-generate-001 to use the cheaper/faster model.
"""

import os
import sys
import time

from google import genai
from google.genai import types

MODEL = os.environ.get("VEO_MODEL", "veo-3.0-generate-001")
SEED_IMG = "tyguy_seed.png"

STYLE = (" Pixar/Disney-style 3D animation, cinematic lighting, warm vibrant colors, "
         "high detail, family-friendly. No subtitles, no on-screen text.")
NEG = ("subtitles, captions, on-screen text, watermark, distorted face, extra fingers, "
       "extra limbs, flat 2D, hand-drawn, low quality, blurry, deformed, violence, blood")

TY = ("The 3D cartoon young man in a royal-blue hoodie with a white 'T' (same character "
      "as the starting image)")
KIDS = ("four happy 3D cartoon kids (Mia with a brown side-ponytail and coral top, Leo "
        "with glasses and a green shirt, Aisha wearing a purple hijab top, Sam with curly "
        "hair and a yellow shirt) sitting on a rug")
ROOM = "a cozy colorful kids' Bible-club room with books, a rug, and a bright banner"
ROAD = "a sunny dusty ancient desert road to Jericho with rocks and sparse trees"

# (prompt, seed_with_tyguy_image)
SHOTS = [
    # ACT 1
    (f"{TY} waves warmly to camera in {ROOM} with {KIDS}; he says, \"Hey friends! Welcome to Bible Club!\" cheerful music.{STYLE}", True),
    (f"{TY} holds up a Bible with a warm smile in {ROOM}; he says, \"Today's big question: who is my neighbor?\"{STYLE}", True),
    (f"Close-up of the curious 3D cartoon kids on the rug; Leo (glasses, green shirt) raises his hand and asks, \"Everybody nearby?\"{STYLE}", False),
    (f"{TY} kneels to the kids' level, gentle, and says, \"Let me tell you a story Jesus told...\"{STYLE}", True),
    (f"A magical storybook opens, glowing pages turning, the club room dissolving into {ROAD}; gentle whoosh, sparkles.{STYLE}", False),
    # ACT 2 — parable
    (f"A kind traveler in a tan tunic walks along {ROAD}, humming happily, carrying a small bag. Warm adventurous music.{STYLE}", False),
    (f"Two rough hooded robbers suddenly jump out from behind rocks on {ROAD}, startling the traveler; tense music, no violence shown.{STYLE}", False),
    (f"Aftermath on {ROAD}: the traveler sits slumped and hurt at the roadside, his bag empty, the robbers gone. Soft sad music.{STYLE}", False),
    (f"Wide lonely shot of {ROAD}; the hurt traveler weakly raises a hand for help. Lonely music.{STYLE}", False),
    (f"A priest in fine white-and-gold robes walks up {ROAD}, looking important.{STYLE}", False),
    (f"The priest notices the hurt man, looks away, and crosses to the far side of {ROAD}, passing by.{STYLE}", False),
    (f"Close-up: the hurt traveler's hopeful face falls as the priest walks away on {ROAD}.{STYLE}", False),
    (f"A Levite in a blue temple robe approaches along {ROAD}, busy and self-important.{STYLE}", False),
    (f"The Levite glances at the hurt man, hesitates, then hurries past on {ROAD}.{STYLE}", False),
    (f"The hurt traveler sits alone again on {ROAD}, head lowered. Lonely gentle music.{STYLE}", False),
    (f"A humble Samaritan in a striped robe leads a small donkey along {ROAD}, sees the hurt man, and stops with a concerned, kind face.{STYLE}", False),
    (f"The Samaritan kneels beside the hurt traveler with compassion on {ROAD} and says, \"Don't worry, I've got you.\" tender music.{STYLE}", False),
    (f"The Samaritan gently bandages the traveler's arm with cloth on {ROAD}, caring and careful. Warm music.{STYLE}", False),
    (f"The Samaritan carefully helps the traveler up onto the small donkey on {ROAD}.{STYLE}", False),
    (f"The Samaritan walks beside the donkey carrying the traveler down {ROAD} toward an inn at dusk; warm hopeful music.{STYLE}", False),
    (f"They arrive at a cozy ancient roadside inn at dusk; a friendly innkeeper in an apron greets them at the door. Warm music.{STYLE}", False),
    (f"Inside the warm inn, the Samaritan helps the traveler lie down on a comfortable bed to rest.{STYLE}", False),
    (f"The Samaritan hands the innkeeper a few gold coins and says, \"Take care of him; I'll repay any more.\"{STYLE}", False),
    (f"The innkeeper nods kindly inside the cozy inn while the rescued traveler rests gratefully.{STYLE}", False),
    (f"At golden hour outside the inn, the Samaritan waves goodbye warmly and continues on his way down the road.{STYLE}", False),
    (f"Magical storybook pages turn back, glowing sparkles, dissolving from the road back into {ROOM}.{STYLE}", False),
    # ACT 3
    (f"{TY} sits with the kids in {ROOM}, gentle smile, and asks, \"So... who was the real neighbor?\"{STYLE}", True),
    (f"The 3D cartoon kids think; Aisha (purple hijab) lights up and says, \"The one who stopped to help!\"{STYLE}", False),
    (f"{TY} nods proudly in {ROOM} and says, \"Exactly! Not the important ones, the kind one.\"{STYLE}", True),
    (f"{TY} sincere in {ROOM}, says, \"Jesus said: go, and do likewise.\" soft inspirational music.{STYLE}", True),
    (f"Close-up of the kids nodding, inspired and smiling, in {ROOM}.{STYLE}", False),
    (f"{TY} warm in {ROOM} says, \"Being a neighbor means helping anyone who needs it.\"{STYLE}", True),
    # ACT 4 — modern application
    (f"A 3D cartoon girl with a brown side-ponytail (Mia) helps a classmate pick up dropped books in a sunny schoolyard; cheerful music.{STYLE}", False),
    (f"A 3D cartoon boy with glasses (Leo) shares half his lunch with another kid who has none; both smile warmly. Heartwarming music.{STYLE}", False),
    (f"A 3D cartoon girl in a purple hijab (Aisha) warmly invites a lonely new kid to join the group playing in a park.{STYLE}", False),
    (f"A 3D cartoon boy with curly hair (Sam) helps a kind elderly neighbor carry grocery bags; she smiles gratefully.{STYLE}", False),
    (f"The four happy 3D cartoon kids together outdoors give a joyful group high-five; uplifting music.{STYLE}", False),
    # ACT 5
    (f"{TY} with the kids in {ROOM}, warm and sincere, says, \"Love your neighbor as yourself. Mark twelve, thirty-one.\" gentle music.{STYLE}", True),
    (f"{TY} gives an enthusiastic thumbs-up, bright brand-blue background with golden sparkles and floating crosses, and says, \"Be kind, have fun, and be you! See you next time at Bible Club!\"{STYLE}", True),
]

ACTS = {1: range(1, 6), 2: range(6, 27), 3: range(27, 33), 4: range(33, 38), 5: range(38, 40)}


def main():
    args = sys.argv[1:]
    aspect = "9:16" if "--vertical" in args else "16:9"
    args = [a for a in args if a != "--vertical"]
    if "--act" in args:
        i = args.index("--act")
        which = list(ACTS[int(args[i + 1])])
        del args[i:i + 2]
    elif args:
        which = [int(a) for a in args]
    else:
        which = list(range(1, len(SHOTS) + 1))

    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        print("ERROR: set GEMINI_API_KEY")
        raise SystemExit(1)
    client = genai.Client(api_key=key)

    seed = None
    if os.path.exists(SEED_IMG):
        with open(SEED_IMG, "rb") as f:
            seed = types.Image(image_bytes=f.read(), mime_type="image/png")

    for n in which:
        prompt, use_seed = SHOTS[n - 1]
        out = f"shot{n}.mp4"
        print(f"[shot {n}/{len(SHOTS)}] {'seeded' if use_seed else 'text'} ({aspect})")
        kwargs = dict(model=MODEL, prompt=prompt,
                      config=types.GenerateVideosConfig(aspect_ratio=aspect,
                                                        number_of_videos=1,
                                                        negative_prompt=NEG))
        if use_seed and seed is not None:
            kwargs["image"] = seed
        op = client.models.generate_videos(**kwargs)
        t0 = time.time()
        while not op.done:
            time.sleep(10)
            op = client.operations.get(op)
        client.files.download(file=op.response.generated_videos[0].video)
        op.response.generated_videos[0].video.save(out)
        print(f"  saved {out}  ({time.time()-t0:.0f}s)")
    print("Done. Assemble with: python3 assemble_3d.py " +
          " ".join(f"shot{n}.mp4" for n in range(1, len(SHOTS) + 1)) +
          " --out love_your_neighbor.mp4")


if __name__ == "__main__":
    main()
