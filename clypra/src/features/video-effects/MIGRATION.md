# Migration Guide: Video Effects System

## Overview

This guide helps you migrate from the old `src/store/videoEffectsStore.ts` to the new `src/features/video-effects/` module.

---

## Key Changes

### Old System (Deprecated)

```typescript
import { useVideoEffectsStore } from "@/store/videoEffectsStore";

// Single store with generic "effects"
const store = useVideoEffectsStore();
await store.loadCategory("camera");
const items = store.categoryItems["camera"];
```

### New System

```typescript
import { useVideoEffectsStore, useOverlays, useEffects, useTransitions } from "@/features/video-effects";

// Specialized stores for each type
const { overlays } = useOverlays("particle"); // Actual video files
const { effects } = useEffects("camera"); // Behavior definitions
const { transitions } = useTransitions("zoom"); // Animation definitions
```

---

## Migration Steps

### Step 1: Identify Effect Types

First, categorize your existing effects:

**Overlays** (actual files):

- Smoke, fire, dust, light leaks
- Lens flares, bokeh, particles
- Any effect that's a video/image file

**Effects** (behaviors):

- Camera shake, zoom, pan
- Blur, glitch, VHS
- RGB split, chromatic aberration
- Any effect that transforms pixels

**Transitions** (animations):

- Fade, dissolve, cut
- Zoom in/out, slide
- Wipe, circle expand
- Any effect between two clips

### Step 2: Update Imports

**Before:**

```typescript
import { useVideoEffectsStore, EffectItem } from "@/store/videoEffectsStore";
```

**After:**

```typescript
import { useVideoEffectsStore, OverlayAsset, EffectPreset, TransitionPreset } from "@/features/video-effects";
```

### Step 3: Update Component Code

**Before:**

```typescript
function EffectsPicker() {
  const store = useVideoEffectsStore();

  useEffect(() => {
    store.loadCategory("camera");
  }, []);

  const items = store.categoryItems["camera"];
  const loading = store.loading["camera"];

  return (
    <div>
      {loading && <Spinner />}
      {items?.map((item) => (
        <EffectCard key={item.id} item={item} />
      ))}
    </div>
  );
}
```

**After:**

```typescript
function EffectsPicker() {
  const { effects, loading, error } = useEffects("camera");

  return (
    <div>
      {loading && <Spinner />}
      {error && <ErrorMessage message={error} />}
      {effects.map((effect) => (
        <EffectCard key={effect.id} effect={effect} />
      ))}
    </div>
  );
}
```

### Step 4: Update Type Definitions

**Before:**

```typescript
interface EffectItem {
  id: string;
  name: string;
  category: string;
  description: string;
  strength?: "Subtle" | "Medium" | "Strong";
  status: "ready" | "soon";
}
```

**After:**

```typescript
// For overlays
interface OverlayAsset {
  id: string;
  name: string;
  type: "overlay";
  category: string;
  url: string; // The actual video file
  duration: number;
  hasAlpha: boolean;
  loopable: boolean;
  // ... more properties
}

// For effects
interface EffectPreset {
  id: string;
  name: string;
  type: "effect";
  renderer: EffectRenderer; // "shake", "blur", etc.
  params: EffectParameters; // { intensity: 80, ... }
  // ... more properties
}

// For transitions
interface TransitionPreset {
  id: string;
  name: string;
  type: "transition";
  renderer: TransitionRenderer; // "fade", "zoom_in", etc.
  params: TransitionParameters;
  // ... more properties
}
```

### Step 5: Update Timeline Integration

**Before:**

```typescript
function applyEffect(clipId: string, effectItem: EffectItem) {
  // Generic effect application
  timelineStore.updateClip(clipId, {
    effect: effectItem,
  });
}
```

**After:**

```typescript
// For overlays (video files)
async function applyOverlay(clipId: string, overlay: OverlayAsset) {
  const objectURL = await useVideoEffectsStore.getState().downloadOverlay(overlay);

  timelineStore.updateClip(clipId, {
    overlays: [
      ...(clip.overlays || []),
      {
        id: generateId(),
        effectId: overlay.id,
        type: "overlay",
        url: objectURL,
        opacity: 0.7,
        blendMode: "screen",
        duration: overlay.duration,
        loop: overlay.loopable,
      },
    ],
  });
}

// For effects (behaviors)
function applyEffect(clipId: string, effect: EffectPreset) {
  timelineStore.updateClip(clipId, {
    effects: [
      ...(clip.effects || []),
      {
        id: generateId(),
        effectId: effect.id,
        type: "effect",
        renderer: effect.renderer,
        params: effect.params,
        intensity: effect.intensity.default,
      },
    ],
  });
}

// For transitions (between clips)
function applyTransition(fromClipId: string, toClipId: string, transition: TransitionPreset) {
  timelineStore.addTransition({
    id: generateId(),
    transitionId: transition.id,
    type: "transition",
    renderer: transition.renderer,
    params: transition.params,
    duration: transition.duration.default,
    fromClipId,
    toClipId,
  });
}
```

### Step 6: Update Rendering

**Before:**

```typescript
// Generic effect rendering (unclear what it does)
function renderFrame(clip: Clip) {
  if (clip.effect) {
    applyEffect(clip.effect);
  }
}
```

**After:**

```typescript
import { EffectRenderer, TransitionRenderer } from "@/features/video-effects";

function renderFrame(clip: Clip, time: number) {
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d")!;

  // Draw base frame
  ctx.drawImage(getVideoFrame(clip, time), 0, 0);

  // Draw overlays (video files)
  clip.overlays?.forEach((overlay) => {
    const overlayFrame = getOverlayFrame(overlay, time);
    ctx.save();
    ctx.globalAlpha = overlay.opacity;
    ctx.globalCompositeOperation = overlay.blendMode;
    ctx.drawImage(overlayFrame, overlay.x, overlay.y, overlay.width, overlay.height);
    ctx.restore();
  });

  // Apply effects (behaviors)
  clip.effects?.forEach((effect) => {
    EffectRenderer.apply(ctx, effect.renderer, effect.params, effect.intensity, time - effect.startTime);
  });

  return canvas;
}
```

---

## API Endpoint Changes

### Old Endpoint Structure

```
GET /effects/:category
```

### New Endpoint Structure

```
GET /video-effects/manifest                    # All categories
GET /video-effects/overlay/:category           # Smoke, fire, etc.
GET /video-effects/effect/:category            # Shake, blur, etc.
GET /video-effects/transition/:category        # Fade, zoom, etc.
GET /video-effects/overlay/:category/:id       # Specific overlay
GET /video-effects/effect/:category/:id        # Specific effect
GET /video-effects/transition/:category/:id    # Specific transition
```

---

## Checklist

- [ ] Identify which effects are overlays vs. effects vs. transitions
- [ ] Update imports from `@/store/videoEffectsStore` to `@/features/video-effects`
- [ ] Replace `useVideoEffectsStore()` with specialized hooks
- [ ] Update type definitions to use new interfaces
- [ ] Update timeline integration to handle three categories
- [ ] Update rendering to use `EffectRenderer` and `TransitionRenderer`
- [ ] Update API calls to use new endpoint structure
- [ ] Test each effect type separately
- [ ] Remove deprecated `@/store/videoEffectsStore` once migration is complete

---

## Backward Compatibility

The old `@/store/videoEffectsStore` has been marked as deprecated but remains functional for backward compatibility. However, new features will only be added to the new system.

**Timeline for Deprecation:**

- **v1.1**: New system introduced, old system marked deprecated
- **v1.2**: Warning messages when using old system
- **v2.0**: Old system removed

---

## Support

If you encounter issues during migration:

1. Check the [README.md](./README.md) for usage examples
2. Review the [types.ts](./types.ts) for type definitions
3. Look at example components in `src/components/editor/effects/`
4. Open an issue on GitHub with the `migration` label

---

## Benefits of New System

✅ **Clear separation** between overlays, effects, and transitions  
✅ **Type safety** with dedicated interfaces  
✅ **Better performance** with specialized stores  
✅ **Easier testing** with modular renderers  
✅ **Scalable** for future effect types  
✅ **Portable** across web, desktop, mobile

The new architecture aligns with how professional video editors (CapCut, Premiere, Final Cut) distinguish between different effect types.
