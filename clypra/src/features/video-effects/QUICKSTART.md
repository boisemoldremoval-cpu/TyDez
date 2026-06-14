# Quick Start Guide

Get the video effects system running in 30 minutes.

---

## Step 1: Backend Setup (15 min)

### Create KV Entries

```typescript
// Add to your Cloudflare Worker KV
await KV.put(
  "video-effects:manifest",
  JSON.stringify({
    version: "1.0.0",
    categories: [
      {
        id: "particle",
        name: "Particle Effects",
        type: "overlay",
        description: "Smoke, fire, and particle overlays",
        thumbnail: "https://cdn.clypra.com/thumbs/particle.jpg",
        itemCount: 2,
      },
      {
        id: "camera",
        name: "Camera Effects",
        type: "effect",
        description: "Camera shake, zoom, and movement",
        thumbnail: "https://cdn.clypra.com/thumbs/camera.jpg",
        itemCount: 2,
      },
      {
        id: "basic",
        name: "Basic Transitions",
        type: "transition",
        description: "Fade, dissolve, and cuts",
        thumbnail: "https://cdn.clypra.com/thumbs/basic.jpg",
        itemCount: 2,
      },
    ],
    featured: [],
  }),
);

// Add some sample overlays
await KV.put(
  "video-effects:overlay:particle",
  JSON.stringify([
    {
      id: "smoke_001",
      name: "Rising Smoke",
      type: "overlay",
      category: "particle",
      description: "Realistic smoke rising effect",
      thumbnail: "https://cdn.clypra.com/thumbs/smoke.jpg",
      url: "https://cdn.clypra.com/overlays/smoke.webm",
      duration: 5.0,
      width: 1920,
      height: 1080,
      hasAlpha: true,
      fileFormat: "webm",
      fileSize: 2457600,
      tags: ["smoke", "fog", "atmospheric"],
      isPremium: false,
      blendMode: "screen",
      loopable: true,
      recommended: {
        opacity: 0.7,
        blendMode: "screen",
        placement: "fullscreen",
      },
    },
  ]),
);

// Add some sample effects
await KV.put(
  "video-effects:effect:camera",
  JSON.stringify([
    {
      id: "shake_strong",
      name: "Strong Shake",
      type: "effect",
      category: "camera",
      description: "Intense camera shake",
      thumbnail: "https://cdn.clypra.com/thumbs/shake.jpg",
      renderer: "shake",
      params: {
        intensity: 80,
        frequency: 15,
      },
      tags: ["shake", "camera", "handheld"],
      isPremium: false,
      intensity: {
        min: 0,
        max: 100,
        default: 80,
        step: 1,
      },
    },
  ]),
);

// Add some sample transitions
await KV.put(
  "video-effects:transition:basic",
  JSON.stringify([
    {
      id: "fade",
      name: "Fade",
      type: "transition",
      category: "basic",
      description: "Classic crossfade",
      thumbnail: "https://cdn.clypra.com/thumbs/fade.jpg",
      renderer: "fade",
      params: {
        easing: "ease-in-out",
      },
      tags: ["fade", "crossfade", "basic"],
      isPremium: false,
      duration: {
        min: 0.1,
        max: 3.0,
        default: 0.5,
        step: 0.1,
      },
      easing: "ease-in-out",
    },
  ]),
);
```

### Add API Routes

Add to your Cloudflare Worker:

```typescript
// workers/src/index.ts
import { VideoEffectsApi } from "./video-effects";

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Video effects routes
    if (url.pathname.startsWith("/video-effects")) {
      return VideoEffectsApi.handle(request, env);
    }

    // ... other routes
  },
};
```

```typescript
// workers/src/video-effects.ts
export class VideoEffectsApi {
  static async handle(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    // GET /video-effects/manifest
    if (path === "/video-effects/manifest") {
      const manifest = await env.KV.get("video-effects:manifest", "json");
      return new Response(JSON.stringify(manifest), {
        headers: {
          "Content-Type": "application/json",
          "Cache-Control": "public, max-age=3600",
        },
      });
    }

    // GET /video-effects/:type/:category
    const categoryMatch = path.match(/^\/video-effects\/(overlay|effect|transition)\/([\w-]+)$/);
    if (categoryMatch) {
      const [, type, category] = categoryMatch;
      const key = `video-effects:${type}:${category}`;
      const items = await env.KV.get(key, "json");
      return new Response(JSON.stringify(items || []), {
        headers: {
          "Content-Type": "application/json",
          "Cache-Control": "public, max-age=3600",
        },
      });
    }

    return new Response("Not found", { status: 404 });
  }
}
```

---

## Step 2: Frontend Setup (10 min)

### Test the API

```typescript
// Test in browser console or a test file
import { VideoEffectsApi } from "@/features/video-effects";

// Test manifest
const manifest = await VideoEffectsApi.getManifest();
console.log("Manifest:", manifest);

// Test overlays
const overlays = await VideoEffectsApi.getOverlays("particle");
console.log("Overlays:", overlays);

// Test effects
const effects = await VideoEffectsApi.getEffects("camera");
console.log("Effects:", effects);

// Test transitions
const transitions = await VideoEffectsApi.getTransitions("basic");
console.log("Transitions:", transitions);
```

### Add to UI

```tsx
// src/App.tsx or your main editor component
import { EffectsPanel } from "@/features/video-effects/components/EffectsPanel";

function Editor() {
  return (
    <div className="flex h-screen">
      {/* Your existing editor */}
      <div className="flex-1">{/* Timeline, preview, etc. */}</div>

      {/* New effects panel */}
      <div className="w-80 border-l border-zinc-800">
        <EffectsPanel />
      </div>
    </div>
  );
}
```

---

## Step 3: Test It (5 min)

### 1. Test Overlay Picker

```tsx
import { OverlayPicker } from "@/features/video-effects/components";

<OverlayPicker
  onSelect={(overlay) => {
    console.log("Selected overlay:", overlay);
    // Later: apply to clip
  }}
/>;
```

### 2. Test Effect Picker

```tsx
import { EffectPicker } from "@/features/video-effects/components";

<EffectPicker
  onSelect={(effect) => {
    console.log("Selected effect:", effect);
    // Later: apply to clip
  }}
/>;
```

### 3. Test Transition Picker

```tsx
import { TransitionPicker } from "@/features/video-effects/components";

<TransitionPicker
  onSelect={(transition) => {
    console.log("Selected transition:", transition);
    // Later: apply between clips
  }}
/>;
```

---

## What You Should See

✅ Effects panel with three tabs: Overlays, Effects, Transitions  
✅ Category tabs for each type  
✅ Grid of effect cards with thumbnails  
✅ Click to select (console logs for now)  
✅ No errors in console

---

## Common Issues

### API Not Working

**Problem**: Can't fetch manifest  
**Solution**: Check CORS headers in Worker

```typescript
headers: {
  'Content-Type': 'application/json',
  'Access-Control-Allow-Origin': '*',  // Add this
}
```

### Thumbnails Not Loading

**Problem**: 404 on thumbnail URLs  
**Solution**: Use placeholder images initially

```typescript
thumbnail: "https://via.placeholder.com/320x180/1a1a1a/666666?text=Smoke";
```

### Effects Not Rendering

**Problem**: Applied effect but nothing happens  
**Solution**: Rendering comes later! For now, just test selection.

---

## Next: Full Integration

Once you can select effects, proceed to:

1. **Apply to Clips**: [INTEGRATION.md](./INTEGRATION.md) - Step 2
2. **Render Effects**: [INTEGRATION.md](./INTEGRATION.md) - Step 5
3. **Export with Effects**: [INTEGRATION.md](./INTEGRATION.md) - Step 6

---

## Quick Reference

### Import What You Need

```typescript
// Types
import type { OverlayAsset, EffectPreset, TransitionPreset } from "@/features/video-effects";

// API
import { VideoEffectsApi } from "@/features/video-effects";

// Store hooks
import { useManifest, useOverlays, useEffects, useTransitions } from "@/features/video-effects";

// Renderers
import { EffectRenderer, TransitionRenderer } from "@/features/video-effects";

// Components
import { OverlayPicker, EffectPicker, TransitionPicker } from "@/features/video-effects/components";
```

### Fetch Data

```typescript
// Get everything
const { manifest, loading } = useManifest();

// Get by category
const { overlays } = useOverlays("particle");
const { effects } = useEffects("camera");
const { transitions } = useTransitions("basic");

// Download overlay
const store = useVideoEffectsStore();
const objectURL = await store.downloadOverlay(overlay);
```

### Apply to Clips

```typescript
// Apply overlay (video file)
clip.overlays.push({
  id: generateId(),
  effectId: overlay.id,
  url: objectURL,
  opacity: 0.7,
  blendMode: "screen",
  // ... more properties
});

// Apply effect (behavior)
clip.effects.push({
  id: generateId(),
  effectId: effect.id,
  renderer: "shake",
  params: { intensity: 80 },
  // ... more properties
});
```

### Render

```typescript
// At render time
EffectRenderer.apply(ctx, "shake", { intensity: 80 }, 0.8, time);
TransitionRenderer.render(ctx, fromFrame, toFrame, "fade", {}, 0.5);
```

---

## That's It!

You now have:

- ✅ Backend serving effect data
- ✅ Frontend fetching and displaying effects
- ✅ UI for browsing and selecting effects

**Next steps**: Integrate with your timeline and render pipeline. See [INTEGRATION.md](./INTEGRATION.md) for details.

---

## Need Help?

- 📖 [README.md](./README.md) - Full architecture
- 🔧 [INTEGRATION.md](./INTEGRATION.md) - Timeline integration
- 🚀 [BACKEND.md](./BACKEND.md) - Backend setup
- 📦 [SUMMARY.md](./SUMMARY.md) - Complete overview
