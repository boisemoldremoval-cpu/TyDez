/**
 * Apply overlay to a clip
 */

import { useVideoEffectsStore } from "../store/videoEffectsStore";
import { useTimelineStore } from "@/store/timelineStore";
import type { OverlayAsset, ClipOverlay } from "../types";
import { generateId } from "@/lib/utils/id";

export async function applyOverlayToClip(clipId: string, overlay: OverlayAsset): Promise<void> {
  const timelineStore = useTimelineStore.getState();
  const effectsStore = useVideoEffectsStore.getState();

  // Get the clip
  const clip = timelineStore.clips.find((c) => c.id === clipId);
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

export async function removeOverlayFromClip(clipId: string, overlayId: string): Promise<void> {
  const timelineStore = useTimelineStore.getState();
  const clip = timelineStore.clips.find((c) => c.id === clipId);

  if (!clip || !clip.overlays) {
    return;
  }

  timelineStore.updateClip(clipId, {
    overlays: clip.overlays.filter((o) => o.id !== overlayId),
  });
}

export function updateClipOverlay(clipId: string, overlayId: string, updates: Partial<ClipOverlay>): void {
  const timelineStore = useTimelineStore.getState();
  const clip = timelineStore.clips.find((c) => c.id === clipId);

  if (!clip || !clip.overlays) {
    return;
  }

  timelineStore.updateClip(clipId, {
    overlays: clip.overlays.map((o) => (o.id === overlayId ? { ...o, ...updates } : o)),
  });
}
