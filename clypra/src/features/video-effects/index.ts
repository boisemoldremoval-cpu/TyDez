/**
 * Video Effects Feature Module
 *
 * Provides three categories of video effects:
 * 1. Overlays - Actual video/image files (smoke, fire, light leaks)
 * 2. Effects - Behavior definitions (shake, blur, glitch)
 * 3. Transitions - Animation definitions (zoom, dissolve, wipe)
 */

// Types
export * from "./types";

// API
export { VideoEffectsApi } from "./api/clypraApi";

// Store
export { useVideoEffectsStore, useOverlays, useEffects, useTransitions, useManifest } from "./store/videoEffectsStore";

// Renderers
export { EffectRenderer } from "./renderers/EffectRenderer";
export { TransitionRenderer } from "./renderers/TransitionRenderer";
