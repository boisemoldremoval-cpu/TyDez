/**
 * Video Effects Store
 *
 * Manages state for:
 * - Overlays (actual video files)
 * - Effects (behavior definitions)
 * - Transitions (animation definitions)
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { VideoEffectManifest, VideoEffectItem, OverlayAsset, EffectPreset, TransitionPreset, VideoEffectCategory, EffectCategory } from "../types";
import { VideoEffectsApi } from "../api/clypraApi";

interface VideoEffectsState {
  // Manifest
  manifest: VideoEffectManifest | null;
  manifestLoading: boolean;
  manifestError: string | null;

  // Categories
  categories: Record<string, VideoEffectItem[]>;
  categoryLoading: Record<string, boolean>;
  categoryErrors: Record<string, string | null>;

  // Downloaded overlays (Object URLs)
  overlayURLs: Map<string, string>;

  // User favorites (persisted)
  favorites: Set<string>;

  // Actions
  loadManifest: () => Promise<void>;
  loadCategory: (type: EffectCategory, category: string) => Promise<void>;
  downloadOverlay: (overlay: OverlayAsset) => Promise<string>;
  preloadOverlays: (overlays: OverlayAsset[]) => Promise<void>;
  search: (query: string, type?: EffectCategory) => Promise<VideoEffectItem[]>;

  // Favorites
  addFavorite: (id: string) => void;
  removeFavorite: (id: string) => void;
  toggleFavorite: (id: string) => void;
  isFavorite: (id: string) => boolean;

  // Cache management
  clearCache: () => void;
  clearOverlayCache: () => void;
  getCacheStats: () => ReturnType<typeof VideoEffectsApi.getCacheStats>;
}

export const useVideoEffectsStore = create<VideoEffectsState>()(
  persist(
    (set, get) => ({
      // Initial state
      manifest: null,
      manifestLoading: false,
      manifestError: null,
      categories: {},
      categoryLoading: {},
      categoryErrors: {},
      overlayURLs: new Map(),
      favorites: new Set(),

      // Load manifest
      loadManifest: async () => {
        const state = get();

        // Skip if already loaded or loading
        if (state.manifest || state.manifestLoading) {
          return;
        }

        set({ manifestLoading: true, manifestError: null });

        try {
          const manifest = await VideoEffectsApi.getManifest();
          set({
            manifest,
            manifestLoading: false,
            manifestError: null,
          });
        } catch (error) {
          const message = error instanceof Error ? error.message : "Failed to load manifest";
          set({
            manifestLoading: false,
            manifestError: message,
          });
          throw error;
        }
      },

      // Load category items
      loadCategory: async (type: EffectCategory, category: string) => {
        const cacheKey = `${type}:${category}`;
        const state = get();

        // Skip if already loaded or loading
        if (state.categories[cacheKey] || state.categoryLoading[cacheKey]) {
          return;
        }

        set((state) => ({
          categoryLoading: { ...state.categoryLoading, [cacheKey]: true },
          categoryErrors: { ...state.categoryErrors, [cacheKey]: null },
        }));

        try {
          const items = await VideoEffectsApi.getItemsByCategory(type, category);

          set((state) => ({
            categories: { ...state.categories, [cacheKey]: items },
            categoryLoading: { ...state.categoryLoading, [cacheKey]: false },
            categoryErrors: { ...state.categoryErrors, [cacheKey]: null },
          }));
        } catch (error) {
          const message = error instanceof Error ? error.message : "Failed to load category";

          set((state) => ({
            categoryLoading: { ...state.categoryLoading, [cacheKey]: false },
            categoryErrors: { ...state.categoryErrors, [cacheKey]: message },
          }));

          throw error;
        }
      },

      // Download overlay asset
      downloadOverlay: async (overlay: OverlayAsset): Promise<string> => {
        const state = get();

        // Return cached URL if available
        if (state.overlayURLs.has(overlay.id)) {
          return state.overlayURLs.get(overlay.id)!;
        }

        try {
          const objectURL = await VideoEffectsApi.getOverlayObjectURL(overlay);

          set((state) => {
            const newURLs = new Map(state.overlayURLs);
            newURLs.set(overlay.id, objectURL);
            return { overlayURLs: newURLs };
          });

          return objectURL;
        } catch (error) {
          console.error(`Failed to download overlay "${overlay.name}":`, error);
          throw error;
        }
      },

      // Preload multiple overlays
      preloadOverlays: async (overlays: OverlayAsset[]): Promise<void> => {
        await Promise.all(
          overlays.map((overlay) =>
            get()
              .downloadOverlay(overlay)
              .catch((error) => {
                console.warn(`Failed to preload overlay "${overlay.name}":`, error);
              }),
          ),
        );
      },

      // Search
      search: async (query: string, type?: EffectCategory): Promise<VideoEffectItem[]> => {
        try {
          return await VideoEffectsApi.search(query, type);
        } catch (error) {
          console.error("Search failed:", error);
          return [];
        }
      },

      // Favorites
      addFavorite: (id: string) => {
        set((state) => {
          const newFavorites = new Set(state.favorites);
          newFavorites.add(id);
          return { favorites: newFavorites };
        });
      },

      removeFavorite: (id: string) => {
        set((state) => {
          const newFavorites = new Set(state.favorites);
          newFavorites.delete(id);
          return { favorites: newFavorites };
        });
      },

      toggleFavorite: (id: string) => {
        const state = get();
        if (state.favorites.has(id)) {
          state.removeFavorite(id);
        } else {
          state.addFavorite(id);
        }
      },

      isFavorite: (id: string): boolean => {
        return get().favorites.has(id);
      },

      // Cache management
      clearCache: () => {
        const state = get();

        // Revoke all Object URLs
        state.overlayURLs.forEach((url) => {
          URL.revokeObjectURL(url);
        });

        // Clear API cache
        VideoEffectsApi.clearLocalCache();

        // Reset state
        set({
          manifest: null,
          manifestError: null,
          categories: {},
          categoryLoading: {},
          categoryErrors: {},
          overlayURLs: new Map(),
        });
      },

      clearOverlayCache: () => {
        const state = get();

        // Revoke all Object URLs
        state.overlayURLs.forEach((url) => {
          URL.revokeObjectURL(url);
        });

        // Clear API overlay cache
        VideoEffectsApi.clearOverlayCache();

        // Reset overlay URLs
        set({ overlayURLs: new Map() });
      },

      getCacheStats: () => {
        return VideoEffectsApi.getCacheStats();
      },
    }),
    {
      name: "clypra-video-effects-store",
      partialize: (state) => ({
        // Only persist favorites
        favorites: Array.from(state.favorites),
      }),
      merge: (persistedState: any, currentState) => ({
        ...currentState,
        favorites: new Set(persistedState?.favorites || []),
      }),
    },
  ),
);

// ============================================================================
// HELPER HOOKS
// ============================================================================

/**
 * Hook to get overlays for a category
 */
export function useOverlays(category: string) {
  const store = useVideoEffectsStore();
  const cacheKey = `overlay:${category}`;

  React.useEffect(() => {
    store.loadCategory("overlay", category);
  }, [category]);

  return {
    overlays: (store.categories[cacheKey] || []) as OverlayAsset[],
    loading: store.categoryLoading[cacheKey] || false,
    error: store.categoryErrors[cacheKey] || null,
  };
}

/**
 * Hook to get effects for a category
 */
export function useEffects(category: string) {
  const store = useVideoEffectsStore();
  const cacheKey = `effect:${category}`;

  React.useEffect(() => {
    store.loadCategory("effect", category);
  }, [category]);

  return {
    effects: (store.categories[cacheKey] || []) as EffectPreset[],
    loading: store.categoryLoading[cacheKey] || false,
    error: store.categoryErrors[cacheKey] || null,
  };
}

/**
 * Hook to get transitions for a category
 */
export function useTransitions(category: string) {
  const store = useVideoEffectsStore();
  const cacheKey = `transition:${category}`;

  React.useEffect(() => {
    store.loadCategory("transition", category);
  }, [category]);

  return {
    transitions: (store.categories[cacheKey] || []) as TransitionPreset[],
    loading: store.categoryLoading[cacheKey] || false,
    error: store.categoryErrors[cacheKey] || null,
  };
}

/**
 * Hook to get manifest
 */
export function useManifest() {
  const store = useVideoEffectsStore();

  React.useEffect(() => {
    store.loadManifest();
  }, []);

  return {
    manifest: store.manifest,
    loading: store.manifestLoading,
    error: store.manifestError,
  };
}

// Add React import for hooks
import React from "react";
