/**
 * Apply effect to a clip
 */

import { useTimelineStore } from "@/store/timelineStore";
import type { EffectPreset, ClipEffect } from "../types";
import { generateId } from "@/lib/utils/id";

export function applyEffectToClip(clipId: string, effect: EffectPreset): void {
  const timelineStore = useTimelineStore.getState();

  // Get the clip
  const clip = timelineStore.clips.find((c) => c.id === clipId);
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

export function removeEffectFromClip(clipId: string, effectId: string): void {
  const timelineStore = useTimelineStore.getState();
  const clip = timelineStore.clips.find((c) => c.id === clipId);

  if (!clip || !clip.effects) {
    return;
  }

  timelineStore.updateClip(clipId, {
    effects: clip.effects.filter((e) => e.id !== effectId),
  });
}

export function updateClipEffect(clipId: string, effectId: string, updates: Partial<ClipEffect>): void {
  const timelineStore = useTimelineStore.getState();
  const clip = timelineStore.clips.find((c) => c.id === clipId);

  if (!clip || !clip.effects) {
    return;
  }

  timelineStore.updateClip(clipId, {
    effects: clip.effects.map((e) => (e.id === effectId ? { ...e, ...updates } : e)),
  });
}

export function toggleEffectEnabled(clipId: string, effectId: string): void {
  const timelineStore = useTimelineStore.getState();
  const clip = timelineStore.clips.find((c) => c.id === clipId);

  if (!clip || !clip.effects) {
    return;
  }

  timelineStore.updateClip(clipId, {
    effects: clip.effects.map((e) => (e.id === effectId ? { ...e, intensity: e.intensity === 0 ? 1 : 0 } : e)),
  });
}
