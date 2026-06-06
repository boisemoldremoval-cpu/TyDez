# TyGuy's Bible Club — "Love Your Neighbor" (≈5 min, 3D / Veo)

A Christian cartoon for kids: **TyGuy teaches a group of children the parable of
the Good Samaritan**, then they apply it today. Core verse: **Mark 12:31 — "Love
your neighbor as yourself."** (parable from **Luke 10:25–37**).

Format: ~38 Veo shots of ~8s each = ~5:00. Veo generates each character's voice
+ SFX; I add a music bed and continuity. TyGuy shots are image-seeded from his art.

---

## CHARACTER BIBLE (keep wording consistent in every prompt)

- **TyGuy** *(image-seeded from tyguy_seed.png)* — friendly young man, tan skin,
  dark spiky quiff, light stubble, royal-blue hoodie with white "T", black joggers,
  blue high-top sneakers. Warm, energetic teacher. Pixar-style 3D.
- **The Kids (TyGuy's class):** Mia (girl, brown side-ponytail, coral top), Leo
  (boy, glasses, green shirt), Aisha (girl, hijab, purple top), Sam (boy, curly
  hair, yellow shirt). Ages ~8–10, Pixar-style 3D.
- **Parable cast (ancient Bible-times, robes & sandals, dusty desert road):**
  Traveler (kind man in a tan tunic), 2 Robbers (rough, hooded), Priest (fine
  white-and-gold robe), Levite (blue temple robe), **Samaritan** (humble striped
  robe, the hero), Innkeeper (apron). A small donkey.

Global style suffix: *Pixar/Disney-style 3D animation, cinematic lighting, warm
vibrant colors, high detail, family-friendly. No subtitles, no on-screen text.*
Negative: *subtitles, text, watermark, distorted faces, extra fingers, flat 2D, low quality.*

---

## ACT 1 — Bible Club Begins (≈40s, shots 1–5)
1. TyGuy waves to a cozy, colorful kids' club room (rug, books, a "Bible Club"
   banner); the four kids sit on a rug. TyGuy: *"Hey friends! Welcome to Bible Club!"*
2. TyGuy holds up a Bible, warm smile. *"Today's big question: who is my neighbor?"*
3. Close on the curious kids; Leo raises his hand. Leo: *"Everybody nearby?"*
4. TyGuy gently. *"Let me tell you a story Jesus told..."*
5. Storybook transition — pages turn, the room dissolves into a sunny ancient road.

## ACT 2 — The Good Samaritan (≈170s, shots 6–26)
6. A kind Traveler in a tan tunic walks a dusty desert road to Jericho, humming.
7. Two rough hooded Robbers leap out from the rocks. (No violence shown — cut on approach.)
8. Aftermath: the Traveler lies hurt on the roadside, the robbers gone, his bag emptied.
9. Wide lonely road; the hurt man weakly raises a hand. Soft sad music.
10. A Priest in fine white-and-gold robes walks up the road.
11. The Priest sees the hurt man, looks away, and crosses to the far side. Passes by.
12. The hurt man's hopeful face falls as the Priest leaves.
13. A Levite in a blue temple robe approaches, busy and important.
14. The Levite glances at the hurt man, hesitates, then hurries past too.
15. The hurt man alone again, head lowered. Lonely music.
16. A humble Samaritan leads a small donkey up the road, sees the man — concerned.
17. The Samaritan kneels beside him with compassion. Samaritan: *"Don't worry — I've got you."*
18. The Samaritan gently bandages the man's wounds (wrapping cloth, pouring oil).
19. The Samaritan carefully lifts him onto the donkey.
20. They travel together down the road toward an inn at dusk; warm hopeful music.
21. They arrive at a cozy inn; the Innkeeper greets them at the door.
22. The Samaritan helps the man inside to a comfortable bed.
23. The Samaritan hands the Innkeeper coins. Samaritan: *"Take care of him; I'll repay any more."*
24. The Innkeeper nods kindly; the rescued man rests, grateful.
25. The Samaritan waves goodbye warmly and continues on his way at golden hour.
26. Storybook pages turn back — dissolve to TyGuy's club room.

## ACT 3 — Who Was the Neighbor? (≈45s, shots 27–32)
27. TyGuy back in the club room with the kids, gentle smile. *"So... who was the real neighbor?"*
28. The kids think; Aisha lights up. Aisha: *"The one who stopped to help!"*
29. TyGuy nods proudly. *"Exactly! Not the important ones — the kind one."*
30. TyGuy, sincere. *"Jesus said: 'Go, and do likewise.'"*
31. Close on the kids nodding, inspired.
32. TyGuy: *"Being a neighbor means helping anyone who needs it."*

## ACT 4 — Doing Likewise Today (≈45s, shots 33–37)
33. Mia helps a classmate who dropped their books in a sunny schoolyard.
34. Leo shares his lunch with a kid who has none, both smiling.
35. Aisha invites a lonely new kid to join the group at play.
36. Sam helps an elderly neighbor carry groceries; she smiles warmly.
37. The four kids together, joyful, giving a group high-five.

## ACT 5 — Closing Blessing (≈20s, shots 38–39)
38. TyGuy with the kids, warm. *"Love your neighbor as yourself. Mark twelve, thirty-one."*
39. TyGuy gives a big thumbs-up; bright brand-blue, golden sparkles & crosses.
    *"Be kind, have fun, and be you! See you next time at Bible Club!"*

---

## Production notes
- **Voices/audio:** Veo voices each character per clip; I add a gentle music bed and
  light scene-to-scene level matching. Optional: a consistent Piper narrator over the
  parable for storytelling glue.
- **Consistency:** TyGuy = image-seeded every appearance. For the parable cast & kids,
  I lock the character-bible wording; if any drift, I regenerate that shot (optionally
  seeding from a generated reference frame).
- **Assembly:** `assemble_3d.py shot1.mp4 … shot39.mp4 --out love_your_neighbor.mp4`.
