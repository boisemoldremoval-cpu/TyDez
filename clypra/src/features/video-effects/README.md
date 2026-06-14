# Video Effects System

## Architecture Overview

The Video Effects system distinguishes between three fundamentally different types of "effects":

### 1. **Overlay Assets** (Data-Driven)

Actual media files that are composited over video:

- **Examples**: `smoke.mov`, `fire.mov`, `light_leak.webm`, `dust.mp4`
- **Storage**: Video/image files on CDN
- **Usage**: Downloaded and played as video overlays
- **Similar to**: Stickers, but for video clips

### 2. **Effect Presets** (Behavior-Driven)

JSON definitions that tell the renderer how to transform frames:

- **Examples**: Camera shake, blur, VHS, glitch, RGB split
- **Storage**: JSON configurations
- **Usage**: Algorithmic transformations applied at render time
- **Similar to**: CSS filters, but more powerful

### 3. **Transitions** (Behavior-Driven)

JSON definitions for blending between two clips:

- **Examples**: Fade, zoom in, wipe left, dissolve
- **Storage**: JSON configurations
- **Usage**: Applied between clip boundaries
- **Similar to**: Premiere/Final Cut transitions

---

## Why This Distinction Matters

**Most "video effects" people think of are NOT video files.**

When users in CapCut select:

- ❌ Camera Shake → **NOT a video file** (it's algorithmic)
- ❌ Zoom In → **NOT a video file** (it's a transform)
- ❌ VHS Effect → **NOT a video file** (it's shaders/filters)
- ❌ Blur → **NOT a video file** (it's a filter)
- ✅ Smoke Overlay → **IS a video file** (`smoke.mov`)
- ✅ Fire Effect → **IS a video file** (`fire.webm`)

If you tried to build a marketplace by uploading `.prproj` or `.aep` files, you'd be stuck reverse-engineering proprietary formats.

---

## File Structure

```
src/features/video-effects/
├── types.ts                    # TypeScript type definitions
├── api/
│   └── clypraApi.ts           # API client for fetching effects
├── store/
│   └── videoEffectsStore.ts   # Zustand store for state management
├── renderers/
│   ├── EffectRenderer.ts      # Applies behavior-driven effects
│   └── TransitionRenderer.ts  # Applies behavior-driven transitions
├── index.ts                    # Public exports
└── README.md                   # This file
```

---

## Usage Examples

### 1. Fetching Overlays (Actual Video Files)

```typescript
import { VideoEffectsApi, useOverlays } from "@/features/video-effects";

// In a component
function OverlayPicker() {
  const { overlays, loading, error } = useOverlays("particle");

  // overlays = [
  //   {
  //     id: "smoke_001",
  //     name: "Smoke Rising",
  //     type: "overlay",
  //     url: "https://cdn.clypra.com/overlays/smoke_001.webm",
  //     duration: 5.0,
  //     hasAlpha: true,
  //     ...
  //   }
  // ]
}

// Download an overlay for use
const overlay = await VideoEffectsApi.getOverlay("particle", "smoke_001");
const videoURL = await VideoEffectsApi.getOverlayObjectURL(overlay);

// Use videoURL in a <video> element or timeline
```

### 2. Applying Effects (Behavior-Driven)

```typescript
import { EffectRenderer, VideoEffectsApi } from "@/features/video-effects";

// Fetch effect definition
const shake = await VideoEffectsApi.getEffect("camera", "shake_strong");
// shake = {
//   id: "shake_strong",
//   type: "effect",
//   renderer: "shake",
//   params: { intensity: 80, frequency: 15 }
// }

// Apply at render time
const canvas = document.createElement("canvas");
const ctx = canvas.getContext("2d");

// Draw video frame to canvas
ctx.drawImage(videoFrame, 0, 0);

// Apply effect
EffectRenderer.apply(
  ctx,
  shake.renderer, // "shake"
  shake.params, // { intensity: 80, frequency: 15 }
  0.8, // intensity multiplier (0-1)
  currentTime, // for animated effects
);
```

### 3. Applying Transitions

```typescript
import { TransitionRenderer, VideoEffectsApi } from "@/features/video-effects";

// Fetch transition definition
const zoom = await VideoEffectsApi.getTransition("zoom", "zoom_in");
// zoom = {
//   id: "zoom_in",
//   type: "transition",
//   renderer: "zoom_in",
//   params: { scale: 1.3, easing: "ease-out" }
// }

// Apply during transition
const fromFrame = // Canvas with outgoing frame
const toFrame = // Canvas with incoming frame
const progress = 0.5; // 0 = start, 1 = end

TransitionRenderer.render(
  ctx,
  fromFrame,
  toFrame,
  zoom.renderer,
  zoom.params,
  progress
);
```

---

## API Endpoints

The Clypra API should provide these endpoints:

### Manifest

```
GET /video-effects/manifest
```

Returns categories and featured items.

### By Category

```
GET /video-effects/overlay/:category      # Particle, Light, Atmospheric, etc.
GET /video-effects/effect/:category       # Camera, Color, Distortion, etc.
GET /video-effects/transition/:category   # Basic, Slide, Zoom, Creative, etc.
```

### Individual Items

```
GET /video-effects/overlay/:category/:id
GET /video-effects/effect/:category/:id
GET /video-effects/transition/:category/:id
```

### Search

```
GET /video-effects/search?q=smoke&type=overlay
```

---

## Integrating with Timeline

### Adding Overlays to Timeline

```typescript
import { useVideoEffectsStore } from "@/features/video-effects";

function applyOverlayToClip(clipId: string, overlay: OverlayAsset) {
  const clip = timelineStore.getClip(clipId);

  // Download the overlay video
  const objectURL = await useVideoEffectsStore.getState().downloadOverlay(overlay);

  // Add as an overlay property on the clip
  timelineStore.updateClip(clipId, {
    overlays: [
      ...(clip.overlays || []),
      {
        id: generateId(),
        effectId: overlay.id,
        type: "overlay",
        url: objectURL,
        x: 0,
        y: 0,
        width: clip.width,
        height: clip.height,
        rotation: 0,
        opacity: 0.7,
        blendMode: overlay.recommended.blendMode || "screen",
        startTime: 0,
        duration: overlay.duration,
        loop: overlay.loopable,
      },
    ],
  });
}
```

### Adding Effects to Clips

```typescript
function applyEffectToClip(clipId: string, effect: EffectPreset) {
  const clip = timelineStore.getClip(clipId);

  timelineStore.updateClip(clipId, {
    effects: [
      ...(clip.effects || []),
      {
        id: generateId(),
        effectId: effect.id,
        type: "effect",
        renderer: effect.renderer,
        params: effect.params,
        startTime: 0,
        duration: clip.duration,
        intensity: effect.intensity.default,
      },
    ],
  });
}
```

### Adding Transitions Between Clips

```typescript
function addTransitionBetweenClips(fromClipId: string, toClipId: string, transition: TransitionPreset) {
  timelineStore.addTransition({
    id: generateId(),
    transitionId: transition.id,
    type: "transition",
    renderer: transition.renderer,
    params: transition.params,
    duration: transition.duration.default,
    fromClipId,
    toClipId,
    alignment: "center",
  });
}
```

---

## Rendering Pipeline Integration

### At Render Time

```typescript
import { EffectRenderer, TransitionRenderer } from "@/features/video-effects";
import { AppliedEffect, AppliedTransition } from "@/features/video-effects";

function renderFrame(clip: Clip, time: number): HTMLCanvasElement {
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d")!;

  // 1. Draw base frame
  ctx.drawImage(getVideoFrame(clip, time), 0, 0);

  // 2. Draw overlays
  clip.overlays?.forEach((overlay) => {
    const overlayFrame = getOverlayFrame(overlay, time);
    ctx.save();
    ctx.globalAlpha = overlay.opacity;
    ctx.globalCompositeOperation = overlay.blendMode;
    ctx.translate(overlay.x, overlay.y);
    ctx.rotate((overlay.rotation * Math.PI) / 180);
    ctx.drawImage(overlayFrame, 0, 0, overlay.width, overlay.height);
    ctx.restore();
  });

  // 3. Apply effects
  clip.effects?.forEach((effect) => {
    if (isEffectActiveAt(effect, time)) {
      EffectRenderer.apply(ctx, effect.renderer, effect.params, effect.intensity, time - effect.startTime);
    }
  });

  return canvas;
}
```

---

## Free Content Sources

### For Overlays (Actual Files)

You can populate Clypra with free overlay assets from:

**Filmstocks (Free Section)**

- Smoke, fire, dust, light leaks
- Download as MOV/WebM with alpha
- https://filmstocks.wondershare.com/free-effects.html

**Videezy**

- Free motion graphics overlays
- Light leaks, bokeh, particles
- https://www.videezy.com/free-video/overlay

**Mixkit**

- Free video assets
- Light effects, particles
- https://mixkit.co/free-stock-video/

**FootageCrate**

- VFX elements (explosions, smoke, fire)
- Free with attribution
- https://footagecrate.com/

### For Effects & Transitions (JSON Definitions)

You **define these yourself** based on what your renderer supports:

```json
{
  "id": "shake_strong",
  "name": "Strong Shake",
  "type": "effect",
  "renderer": "shake",
  "params": {
    "intensity": 80,
    "frequency": 15
  }
}
```

No external files needed - just JSON configs.

---

## Next Steps

### 1. Backend Implementation

Create these API endpoints in your Clypra Worker:

```typescript
// cloudflare-worker/src/routes/video-effects.ts
export async function handleVideoEffects(request: Request) {
  const url = new URL(request.url);
  const path = url.pathname;

  // GET /video-effects/manifest
  if (path === "/video-effects/manifest") {
    return getManifest();
  }

  // GET /video-effects/:type/:category
  if (path.match(/^\/video-effects\/(overlay|effect|transition)\/[\w-]+$/)) {
    const [_, type, category] = path.split("/").slice(2);
    return getItemsByCategory(type, category);
  }

  // ... etc
}
```

### 2. Populate with Free Content

1. Download free overlays from Videezy/Filmstocks
2. Upload to R2/CDN
3. Create JSON manifest:

```json
{
  "id": "smoke_001",
  "name": "Rising Smoke",
  "type": "overlay",
  "category": "atmospheric",
  "url": "https://cdn.clypra.com/overlays/smoke_001.webm",
  "thumbnail": "https://cdn.clypra.com/thumbs/smoke_001.jpg",
  "duration": 5.0,
  "width": 1920,
  "height": 1080,
  "hasAlpha": true,
  "fileFormat": "webm",
  "loopable": true,
  "tags": ["smoke", "fog", "atmospheric"]
}
```

### 3. UI Components

Create picker components:

- `OverlayPicker.tsx` - Browse and apply overlays
- `EffectPicker.tsx` - Browse and apply effects
- `TransitionPicker.tsx` - Browse and apply transitions

---

## Key Takeaways

✅ **Overlays** = Real video files you upload  
✅ **Effects** = JSON that tells your renderer what to do  
✅ **Transitions** = JSON that tells your renderer how to blend

❌ **Don't** try to import Premiere templates  
❌ **Don't** treat effects as video files  
❌ **Don't** reverse-engineer proprietary formats

✅ **Do** own your effect engine  
✅ **Do** distribute JSON definitions  
✅ **Do** provide overlay assets as downloadable files

This architecture scales across web, desktop, and mobile because the renderer is yours and the definitions are portable JSON.
