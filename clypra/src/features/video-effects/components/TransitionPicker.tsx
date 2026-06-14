/**
 * Transition Picker Component
 * Displays a grid of transitions between clips
 * Follows the same design pattern as Text Effects and Stickers
 */

import React, { useState, useEffect, useMemo } from "react";
import { Search, Sparkles, Loader2, AlertCircle } from "lucide-react";
import { useVideoEffectsStore } from "../store/videoEffectsStore";
import type { TransitionPreset } from "../types";

const TRANSITION_CATEGORIES = ["All", "Fade", "Slide", "Wipe", "Zoom", "Dissolve", "Creative"];

interface TransitionPickerProps {
  onSelect: (transition: TransitionPreset) => void;
}

export function TransitionPicker({ onSelect }: TransitionPickerProps) {
  const [activeCategory, setActiveCategory] = useState("All");
  const [searchQuery, setSearchQuery] = useState("");

  const { transitions, loading, error, fetchTransitions } = useVideoEffectsStore();

  useEffect(() => {
    if (activeCategory !== "All") {
      fetchTransitions(activeCategory.toLowerCase());
    }
  }, [activeCategory, fetchTransitions]);

  const filteredTransitions = useMemo(() => {
    let filtered = activeCategory === "All" ? transitions : transitions.filter((t) => t.category.toLowerCase() === activeCategory.toLowerCase());

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter((t) => t.name.toLowerCase().includes(query) || t.category.toLowerCase().includes(query));
    }

    return filtered;
  }, [transitions, activeCategory, searchQuery]);

  return (
    <div className="flex flex-col h-full">
      {/* Category tabs */}
      <div className="relative shrink-0 border-b border-border/40 bg-surface/5">
        <div className="absolute left-0 top-0 bottom-0 w-3 bg-linear-to-l to-surface from-transparent pointer-events-none z-10" />
        <div className="flex overflow-x-auto gap-2 p-1 whitespace-nowrap" style={{ scrollbarWidth: "none" }}>
          {TRANSITION_CATEGORIES.map((cat) => (
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
          <input type="text" placeholder="Search transitions..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="w-full bg-surface-raised border border-border rounded-lg pl-9 pr-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-accent" />
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto scrollbar-thin p-1">
        {loading && (
          <div className="flex items-center justify-center gap-2 py-10 text-xs text-text-muted">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading transitions...
          </div>
        )}

        {!loading && error && (
          <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-3 text-xs text-red-300 flex items-start gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {!loading && !error && filteredTransitions.length === 0 && (
          <div className="flex flex-col items-center justify-center h-40 gap-1 text-xs text-text-muted">
            <p>No matching transitions found</p>
            <p className="opacity-60">Try another category or search</p>
          </div>
        )}

        {!loading && !error && filteredTransitions.length > 0 && (
          <div className="grid grid-cols-3 gap-1.5">
            {filteredTransitions.map((transition) => (
              <TransitionCard key={transition.id} transition={transition} onSelect={onSelect} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Transition Card Component
const TransitionCard: React.FC<{ transition: TransitionPreset; onSelect: (transition: TransitionPreset) => void }> = ({ transition, onSelect }) => {
  const [isHovered, setIsHovered] = useState(false);

  // Get icon for transition type
  const getTransitionIcon = (name: string) => {
    if (name.toLowerCase().includes("fade")) return "🌅";
    if (name.toLowerCase().includes("slide")) return "↔️";
    if (name.toLowerCase().includes("wipe")) return "↔️";
    if (name.toLowerCase().includes("zoom")) return "🔍";
    if (name.toLowerCase().includes("dissolve")) return "🌫️";
    return "🔄";
  };

  return (
    <div className="group relative aspect-square bg-surface-raised hover:bg-surface-raised/60 rounded-lg overflow-hidden transition-all border border-border hover:border-accent/30 cursor-pointer" onClick={() => onSelect(transition)} onMouseEnter={() => setIsHovered(true)} onMouseLeave={() => setIsHovered(false)}>
      {/* Premium Badge */}
      {transition.isPremium && (
        <div className="absolute top-2 left-2 z-10">
          <div className="bg-linear-to-r from-purple-500 to-pink-500 rounded-full p-1">
            <Sparkles className="w-3 h-3 text-white" />
          </div>
        </div>
      )}

      {/* Duration Badge */}
      {transition.duration && <div className="absolute top-2 right-2 z-10 bg-black/80 text-white text-[10px] px-1.5 py-0.5 rounded">{typeof transition.duration === "number" ? transition.duration.toFixed(1) : transition.duration.default}s</div>}

      {/* Thumbnail */}
      {transition.thumbnailUrl ? (
        <img src={transition.thumbnailUrl} alt={transition.name} className="w-full h-full object-cover" />
      ) : (
        <div className="w-full h-full flex items-center justify-center bg-linear-to-r from-accent/20 via-accent/10 to-accent/20">
          <span className="text-4xl opacity-40">{getTransitionIcon(transition.name)}</span>
        </div>
      )}

      {/* Name Overlay on Hover */}
      <div className={`absolute inset-x-0 bottom-0 bg-linear-to-t from-black/80 to-transparent p-2 transition-opacity ${isHovered ? "opacity-100" : "opacity-0"}`}>
        <p className="text-xs font-semibold text-white truncate">{transition.name}</p>
        {transition.easing && <p className="text-[10px] text-white/60">{transition.easing}</p>}
      </div>

      {/* Hover Overlay */}
      <div className="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors pointer-events-none" />
    </div>
  );
};
