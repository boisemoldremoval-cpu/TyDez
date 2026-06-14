/**
 * Overlay Picker Component
 * Displays a grid of video overlay assets
 * Follows the same design pattern as Text Effects and Stickers
 */

import React, { useState, useEffect, useMemo } from "react";
import { Search, Sparkles, Loader2, AlertCircle, Play } from "lucide-react";
import { useVideoEffectsStore } from "../store/videoEffectsStore";
import type { OverlayAsset } from "../types";

const OVERLAY_CATEGORIES = ["All", "Particles", "Light Leaks", "Bokeh", "Film", "Weather", "Abstract"];

interface OverlayPickerProps {
  onSelect: (overlay: OverlayAsset) => void;
}

export function OverlayPicker({ onSelect }: OverlayPickerProps) {
  const [activeCategory, setActiveCategory] = useState("All");
  const [searchQuery, setSearchQuery] = useState("");

  const { overlays, loading, error, fetchOverlays } = useVideoEffectsStore();

  useEffect(() => {
    if (activeCategory !== "All") {
      fetchOverlays(activeCategory.toLowerCase());
    }
  }, [activeCategory, fetchOverlays]);

  const filteredOverlays = useMemo(() => {
    let filtered = activeCategory === "All" ? overlays : overlays.filter((o) => o.category.toLowerCase() === activeCategory.toLowerCase());

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter((o) => o.name.toLowerCase().includes(query) || o.category.toLowerCase().includes(query) || o.tags?.some((tag) => tag.toLowerCase().includes(query)));
    }

    return filtered;
  }, [overlays, activeCategory, searchQuery]);

  return (
    <div className="flex flex-col h-full">
      {/* Category tabs */}
      <div className="relative shrink-0 border-b border-border/40 bg-surface/5">
        <div className="absolute left-0 top-0 bottom-0 w-3 bg-linear-to-l to-surface from-transparent pointer-events-none z-10" />
        <div className="flex overflow-x-auto gap-2 p-1 whitespace-nowrap" style={{ scrollbarWidth: "none" }}>
          {OVERLAY_CATEGORIES.map((cat) => (
            <button key={cat} onClick={() => setActiveCategory(cat)} className={`px-2 py-1 text-xs font-medium rounded-sm transition-colors cursor-pointer hover:bg-accent/10 hover:text-accent ${activeCategory === cat ? "bg-accent/10 text-accent" : "text-text-muted"}`}>
              {cat}
            </button>
          ))}
        </div>
        <div className="absolute right-0 top-0 bottom-0 w-3 bg-linear-to-l from-surface to-transparent pointer-events-none z-10" />
      </div>

      {/* Search Bar */}
      <div className="p-1 border-b border-border">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input type="text" placeholder="Search overlays..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="w-full bg-surface-raised border border-border rounded-lg pl-9 pr-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-accent" />
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto scrollbar-thin p-1">
        {loading && (
          <div className="flex items-center justify-center gap-2 py-10 text-xs text-text-muted">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading overlays...
          </div>
        )}

        {!loading && error && (
          <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-3 text-xs text-red-300 flex items-start gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {!loading && !error && filteredOverlays.length === 0 && (
          <div className="flex flex-col items-center justify-center h-40 gap-1 text-xs text-text-muted">
            <p>No matching overlays found</p>
            <p className="opacity-60">Try another category or search</p>
          </div>
        )}

        {!loading && !error && filteredOverlays.length > 0 && (
          <div className="grid grid-cols-3 gap-1.5">
            {filteredOverlays.map((overlay) => (
              <OverlayCard key={overlay.id} overlay={overlay} onSelect={onSelect} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Overlay Card Component
const OverlayCard: React.FC<{ overlay: OverlayAsset; onSelect: (overlay: OverlayAsset) => void }> = ({ overlay, onSelect }) => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div className="group relative aspect-square bg-surface-raised hover:bg-surface-raised/60 rounded-lg overflow-hidden transition-all border border-border hover:border-accent/30 cursor-pointer" onClick={() => onSelect(overlay)} onMouseEnter={() => setIsHovered(true)} onMouseLeave={() => setIsHovered(false)}>
      {/* Premium Badge */}
      {overlay.isPremium && (
        <div className="absolute top-2 left-2 z-10">
          <div className="bg-linear-to-r from-purple-500 to-pink-500 rounded-full p-1">
            <Sparkles className="w-3 h-3 text-white" />
          </div>
        </div>
      )}

      {/* Duration Badge */}
      {overlay.duration && <div className="absolute top-2 right-2 z-10 bg-black/80 text-white text-[10px] px-1.5 py-0.5 rounded">{overlay.duration.toFixed(1)}s</div>}

      {/* Thumbnail */}
      {overlay.thumbnailUrl ? (
        <img src={overlay.thumbnailUrl} alt={overlay.name} className="w-full h-full object-cover" />
      ) : (
        <div className="w-full h-full flex items-center justify-center bg-linear-to-br from-accent/20 to-accent/5">
          <span className="text-4xl opacity-40">🎬</span>
        </div>
      )}

      {/* Play Icon on Hover */}
      {isHovered && (
        <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
          <Play className="w-8 h-8 text-white fill-white" />
        </div>
      )}

      {/* Name Overlay on Hover */}
      <div className={`absolute inset-x-0 bottom-0 bg-linear-to-t from-black/80 to-transparent p-2 transition-opacity ${isHovered ? "opacity-100" : "opacity-0"}`}>
        <p className="text-xs font-semibold text-white truncate">{overlay.name}</p>
        {overlay.fileSize && <p className="text-[10px] text-white/60">{(overlay.fileSize / 1024 / 1024).toFixed(1)}MB</p>}
      </div>

      {/* Hover Overlay */}
      <div className="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors pointer-events-none" />
    </div>
  );
};
