# Integration Guide: Video Effects in Clypra Timeline

This guide shows how to integrate the video effects system into your timeline editor.

---

## Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│                    User Workflow                            │
├─────────────────────────────────────────────────────────────┤
│  1. Select clip on timeline                                 │
│  2. Open effects panel                                      │
│  3. Choose overlay/effect/transition                        │
│  4. Adjust parameters                                       │
│  5. Render with effects applied                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 1: Add Effects Panel to UI

Create an effects panel in your editor:

```tsx
// src/components/editor/EffectsPanel.tsx
import React, { useState } from "react";
import { OverlayPicker } from "@/features/video-effects/components/OverlayPicker";
import { EffectPicker } from "@/features/video-effects/components/EffectPicker";
import { TransitionPicker } from "@/features/video-effects/components/TransitionPicker";

type EffectTab = "overlays" | "effects" | "transitions";

export function EffectsPanel() {
  const [activeTab, setActiveTab] = useState<EffectTab>("overlays");

  return (
    <div className="h-full flex flex-col bg-zinc-950">
      {/* Tabs */}
      <div className="flex border-b border-zinc-800">
        <button
          onClick={() => setActiveTab("overlays")}
          className={`
            flex-1 px-4 py-3 text-sm font-medium
            ${activeTab === "overlays" ? "text-blue-500 border-b-2 border-blue-500" : "text-zinc-400 hover:text-zinc-200"}
          `}
        >
          Overlays
        </button>
        <button
          onClick={() => setActiveTab("effects")}
          className={`
            flex-1 px-4 py-3 text-sm font-medium
            ${activeTab === "effects" ? "text-blue-500 border-b-2 border-blue-500" : "text-zinc-400 hover:text-zinc-200"}
          `}
        >
          Effects
        </button>
        <button
          onClick={() => setActiveTab("transitions")}
          className={`
            flex-1 px-4 py-3 text-sm font-medium
            ${activeTab === "transitions" ? "text-blue-500 border-b-2 border-blue-500" : "text-zinc-400 hover:text-zinc-200"}
          `}
        >
          Transitions
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === "overlays" && <OverlayPicker onSelect={handleOverlaySelect} />}
        {activeTab === "effects" && <EffectPicker onSelect={handleEffectSelect} />}
        {activeTab === "transitions" && <TransitionPicker onSelect={handleTransitionSelect} />}
      </div>
    </div>
  );

  function handleOverlaySelect(overlay: OverlayAsset) {
    // Implementation in Step 2
  }

  function handleEffectSelect(effect: EffectPreset) {
    // Implementation in Step 3
  }

  function handleTransitionSelect(transition: TransitionPreset) {
    // Implementation in Step 4
  }
}
```

---

## Step 2: Apply Overlays to Clips

```tsx
// src/lib/effects/applyOverlay.ts
import { useVideoEffectsStore } from "@/features/video-effects";
import { useTimelineStore } from "@/store/timelineStore";
import { OverlayAsset, ClipOverlay } from "@/features/video-effects";
import { generateId } from "@/lib/id";

export async function applyOverlayToClip(clipId: string, overlay: OverlayAsset): Promise<void> {
  const timelineStore = useTimelineStore.getState();
  const effectsStore = useVideoEffectsStore.getState();

  // Get the clip
  const clip = timelineStore.getClipById(clipId);
  if (!clip) {
    throw new Error("Clip not found");
  }

  // Download the overlay video file
  const objectURL = await effectsStore.downloadOverlay(overlay);

  // Create overlay data
  const clipOverlay: ClipOverlay = {
    id: generateId(),
    effectId: overlay.id,
    type: "overlay",
    url: objectURL,

    // Default transform (fullscreen)
    x: 0,
    y: 0,
    width: clip.width,
    height: clip.height,
    rotation: 0,

    // Default appearance
    opacity: overlay.recommended.opacity || 0.7,
    blendMode: overlay.recommended.blendMode || "screen",

    // Timing
    startTime: 0, // Start of clip
    duration: Math.min(overlay.duration, clip.duration),
    loop: overlay.loopable,
  };

  // Add to clip
  timelineStore.updateClip(clipId, {
    overlays: [...(clip.overlays || []), clipOverlay],
  });
}
```

Usage:

```tsx
function handleOverlaySelect(overlay: OverlayAsset) {
  const selectedClipId = uiStore.getState().selectedClipId;
  if (!selectedClipId) {
    toast.error("Please select a clip first");
    return;
  }

  applyOverlayToClip(selectedClipId, overlay);
  toast.success(`Applied ${overlay.name}`);
}
```

---

## Step 3: Apply Effects to Clips

```tsx
// src/lib/effects/applyEffect.ts
import { useTimelineStore } from "@/store/timelineStore";
import { EffectPreset, ClipEffect } from "@/features/video-effects";
import { generateId } from "@/lib/id";

export function applyEffectToClip(clipId: string, effect: EffectPreset): void {
  const timelineStore = useTimelineStore.getState();

  // Get the clip
  const clip = timelineStore.getClipById(clipId);
  if (!clip) {
    throw new Error("Clip not found");
  }

  // Create effect data
  const clipEffect: ClipEffect = {
    id: generateId(),
    effectId: effect.id,
    type: "effect",
    renderer: effect.renderer,
    params: { ...effect.params },

    // Timing
    startTime: 0, // Start of clip
    duration: clip.duration,

    // Intensity
    intensity: effect.intensity.default / 100, // Convert to 0-1
  };

  // Add to clip
  timelineStore.updateClip(clipId, {
    effects: [...(clip.effects || []), clipEffect],
  });
}
```

Usage:

```tsx
function handleEffectSelect(effect: EffectPreset) {
  const selectedClipId = uiStore.getState().selectedClipId;
  if (!selectedClipId) {
    toast.error("Please select a clip first");
    return;
  }

  applyEffectToClip(selectedClipId, effect);
  toast.success(`Applied ${effect.name}`);
}
```

---

## Step 4: Apply Transitions Between Clips

```tsx
// src/lib/effects/applyTransition.ts
import { useTimelineStore } from "@/store/timelineStore";
import { TransitionPreset } from "@/features/video-effects";
import { generateId } from "@/lib/id";

export function applyTransitionBetweenClips(fromClipId: string, toClipId: string, transition: TransitionPreset): void {
  const timelineStore = useTimelineStore.getState();

  // Validate clips exist and are adjacent
  const fromClip = timelineStore.getClipById(fromClipId);
  const toClip = timelineStore.getClipById(toClipId);

  if (!fromClip || !toClip) {
    throw new Error("Clips not found");
  }

  // Check if clips are on the same track
  if (fromClip.trackId !== toClip.trackId) {
    throw new Error("Clips must be on the same track");
  }

  // Check if clips are adjacent
  const fromEnd = fromClip.startTime + fromClip.duration;
  const gap = toClip.startTime - fromEnd;

  if (gap > 0.1) {
    throw new Error("Clips must be adjacent (no gap)");
  }

  // Create transition
  const transitionData = {
    id: generateId(),
    transitionId: transition.id,
    type: "transition" as const,
    renderer: transition.renderer,
    params: { ...transition.params },
    duration: transition.duration.default,
    fromClipId,
    toClipId,
    alignment: "center" as const,
  };

  // Add to timeline
  timelineStore.addTransition(transitionData);
}
```

Usage:

```tsx
function handleTransitionSelect(transition: TransitionPreset) {
  const selectedClipIds = uiStore.getState().selectedClipIds;

  if (selectedClipIds.length !== 2) {
    toast.error("Please select exactly 2 adjacent clips");
    return;
  }

  try {
    applyTransitionBetweenClips(selectedClipIds[0], selectedClipIds[1], transition);
    toast.success(`Applied ${transition.name}`);
  } catch (error) {
    toast.error(error.message);
  }
}
```

---

## Step 5: Render Frames with Effects

Update your render pipeline to apply effects:

```tsx
// src/lib/renderEngine/frameRenderer.ts
import { EffectRenderer, TransitionRenderer } from "@/features/video-effects";
import { Clip, ClipOverlay, ClipEffect } from "@/types";

export class FrameRenderer {
  /**
   * Render a clip frame with all overlays and effects applied
   */
  async renderClipFrame(clip: Clip, time: number, canvas: HTMLCanvasElement): Promise<void> {
    const ctx = canvas.getContext("2d")!;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 1. Draw base video frame
    const baseFrame = await this.getVideoFrame(clip, time);
    ctx.drawImage(baseFrame, 0, 0, canvas.width, canvas.height);

    // 2. Draw overlays (actual video files)
    if (clip.overlays) {
      for (const overlay of clip.overlays) {
        if (this.isOverlayActiveAt(overlay, time)) {
          await this.renderOverlay(ctx, overlay, time);
        }
      }
    }

    // 3. Apply effects (behavior-driven)
    if (clip.effects) {
      for (const effect of clip.effects) {
        if (this.isEffectActiveAt(effect, time)) {
          this.renderEffect(ctx, effect, time);
        }
      }
    }
  }

  /**
   * Render an overlay on the canvas
   */
  private async renderOverlay(ctx: CanvasRenderingContext2D, overlay: ClipOverlay, time: number): Promise<void> {
    const overlayTime = time - overlay.startTime;
    let adjustedTime = overlayTime;

    // Handle looping
    if (overlay.loop) {
      const overlayDuration = overlay.duration;
      adjustedTime = overlayTime % overlayDuration;
    }

    // Get overlay frame
    const overlayFrame = await this.getOverlayFrame(overlay.url, adjustedTime);

    // Apply transform and blend
    ctx.save();
    ctx.globalAlpha = overlay.opacity;
    ctx.globalCompositeOperation = this.getBlendMode(overlay.blendMode);

    ctx.translate(overlay.x, overlay.y);
    ctx.rotate((overlay.rotation * Math.PI) / 180);
    ctx.drawImage(overlayFrame, 0, 0, overlay.width, overlay.height);

    ctx.restore();
  }

  /**
   * Apply an effect to the canvas
   */
  private renderEffect(ctx: CanvasRenderingContext2D, effect: ClipEffect, time: number): void {
    const effectTime = time - effect.startTime;

    // Get intensity (with keyframe support)
    const intensity = this.getEffectIntensity(effect, effectTime);

    // Apply the effect
    EffectRenderer.apply(ctx, effect.renderer, effect.params, intensity, effectTime);
  }

  /**
   * Render a transition between two clips
   */
  async renderTransition(fromClip: Clip, toClip: Clip, transition: AppliedTransition, progress: number, canvas: HTMLCanvasElement): Promise<void> {
    const ctx = canvas.getContext("2d")!;

    // Get frames
    const fromTime = fromClip.duration - transition.duration * (1 - progress);
    const toTime = transition.duration * progress;

    const fromFrame = await this.getVideoFrame(fromClip, fromTime);
    const toFrame = await this.getVideoFrame(toClip, toTime);

    // Apply transition
    TransitionRenderer.render(ctx, fromFrame, toFrame, transition.renderer, transition.params, progress);
  }

  // Helper methods
  private isOverlayActiveAt(overlay: ClipOverlay, time: number): boolean {
    return time >= overlay.startTime && time < overlay.startTime + overlay.duration;
  }

  private isEffectActiveAt(effect: ClipEffect, time: number): boolean {
    return time >= effect.startTime && time < effect.startTime + effect.duration;
  }

  private getEffectIntensity(effect: ClipEffect, time: number): number {
    // If no keyframes, use constant intensity
    if (!effect.keyframes || effect.keyframes.length === 0) {
      return effect.intensity;
    }

    // Find surrounding keyframes and interpolate
    // ... keyframe interpolation logic
    return effect.intensity;
  }

  private getBlendMode(mode: string): GlobalCompositeOperation {
    const modes: Record<string, GlobalCompositeOperation> = {
      normal: "source-over",
      multiply: "multiply",
      screen: "screen",
      overlay: "overlay",
      darken: "darken",
      lighten: "lighten",
      "color-dodge": "color-dodge",
      "color-burn": "color-burn",
      "hard-light": "hard-light",
      "soft-light": "soft-light",
      difference: "difference",
      exclusion: "exclusion",
    };
    return modes[mode] || "source-over";
  }

  private async getVideoFrame(clip: Clip, time: number): Promise<HTMLCanvasElement> {
    // Your existing video frame extraction logic
    // ...
  }

  private async getOverlayFrame(url: string, time: number): Promise<HTMLCanvasElement> {
    // Create video element for overlay
    const video = document.createElement("video");
    video.src = url;
    video.currentTime = time;

    await new Promise((resolve) => {
      video.onseeked = resolve;
    });

    // Draw to canvas
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d")!;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);

    return canvas;
  }
}
```

---

## Step 6: Export with Effects

Update your export pipeline:

```tsx
// src/lib/videoExport.ts
export async function exportVideoWithEffects(project: Project, outputPath: string, onProgress?: (progress: number) => void): Promise<void> {
  const frameRenderer = new FrameRenderer();
  const fps = project.frameRate;
  const totalFrames = Math.ceil(project.duration * fps);

  for (let frame = 0; frame < totalFrames; frame++) {
    const time = frame / fps;

    // Get all clips active at this time
    const activeClips = getActiveClipsAt(time);

    // Render each clip with effects
    for (const clip of activeClips) {
      await frameRenderer.renderClipFrame(clip, time, canvas);
    }

    // Check for transitions
    const transition = getTransitionAt(time);
    if (transition) {
      await frameRenderer.renderTransition(transition.fromClip, transition.toClip, transition, transition.progress, canvas);
    }

    // Write frame to output
    await writeFrame(canvas, outputPath, frame);

    // Update progress
    onProgress?.(frame / totalFrames);
  }
}
```

---

## Step 7: Add Effect Controls

Create a panel to adjust effect parameters:

```tsx
// src/components/editor/EffectControls.tsx
export function EffectControls({ clipId }: { clipId: string }) {
  const clip = useTimelineStore((state) => state.clips.find((c) => c.id === clipId));

  if (!clip || !clip.effects || clip.effects.length === 0) {
    return <div className="p-4 text-zinc-500">No effects applied</div>;
  }

  return (
    <div className="p-4 space-y-4">
      {clip.effects.map((effect) => (
        <EffectControl key={effect.id} clipId={clipId} effect={effect} />
      ))}
    </div>
  );
}

function EffectControl({ clipId, effect }: { clipId: string; effect: ClipEffect }) {
  const updateEffect = useTimelineStore((state) => state.updateClipEffect);

  return (
    <div className="bg-zinc-900 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-medium text-white">{effect.renderer}</h4>
        <button onClick={() => removeEffect(clipId, effect.id)} className="text-red-500 hover:text-red-400">
          Remove
        </button>
      </div>

      {/* Intensity Slider */}
      <div>
        <label className="text-xs text-zinc-400">Intensity</label>
        <input
          type="range"
          min="0"
          max="100"
          value={effect.intensity * 100}
          onChange={(e) => {
            updateEffect(clipId, effect.id, {
              intensity: Number(e.target.value) / 100,
            });
          }}
          className="w-full"
        />
        <div className="text-right text-xs text-zinc-500 mt-1">{Math.round(effect.intensity * 100)}%</div>
      </div>

      {/* Parameter Controls */}
      {Object.entries(effect.params).map(([key, value]) => (
        <div key={key} className="mt-3">
          <label className="text-xs text-zinc-400">{key}</label>
          <input
            type="range"
            min="0"
            max="100"
            value={value}
            onChange={(e) => {
              updateEffect(clipId, effect.id, {
                params: {
                  ...effect.params,
                  [key]: Number(e.target.value),
                },
              });
            }}
            className="w-full"
          />
        </div>
      ))}
    </div>
  );
}
```

---

## Complete Integration Checklist

- [ ] Add effects panel to editor UI
- [ ] Implement overlay application
- [ ] Implement effect application
- [ ] Implement transition application
- [ ] Update frame renderer to apply effects
- [ ] Update export pipeline to include effects
- [ ] Add effect controls for parameter adjustment
- [ ] Add effect preview in timeline
- [ ] Add effect indicators on clips
- [ ] Test rendering performance
- [ ] Test export with effects
- [ ] Add keyboard shortcuts for effects
- [ ] Add effect presets/favorites
- [ ] Document effects workflow for users

---

## Performance Tips

1. **Cache overlay videos**: Download once, reuse many times
2. **Use Web Workers**: Render effects in background threads
3. **GPU acceleration**: Use WebGL for complex effects
4. **Lazy load**: Only load effect definitions when needed
5. **Debounce previews**: Don't re-render on every parameter change
6. **Progressive rendering**: Show low-res preview while rendering

---

## Next Steps

1. Implement the backend API endpoints (see BACKEND.md)
2. Populate with free overlay content
3. Test each effect renderer
4. Optimize rendering performance
5. Add more effects and transitions
6. Build effect marketplace UI
7. Add user-generated content support
