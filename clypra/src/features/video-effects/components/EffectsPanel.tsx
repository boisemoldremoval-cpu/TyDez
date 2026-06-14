/**
 * Main Effects Panel Component
 * Combines Overlays, Effects, and Transitions into a single tabbed interface
 * Following the same design pattern as Text and Stickers tabs
 */

import React, { useState } from "react";
import { OverlayPicker } from "./OverlayPicker";
import { EffectPicker } from "./EffectPicker";
import { TransitionPicker } from "./TransitionPicker";
import type { OverlayAsset, EffectPreset, TransitionPreset } from "../types";
import { useTimelineStore } from "@/store/timelineStore";
import { useUIStore } from "@/store/uiStore";
import { Button } from "@/components/ui/Button";
import { AlertCircle } from "lucide-react";

type EffectTab = "overlays" | "effects" | "transitions";

export function EffectsPanel() {
  const [activeTab, setActiveTab] = useState<EffectTab>("effects");
  const selectedClipIds = useUIStore((state) => state.selectedClipIds);

  const handleOverlaySelect = async (overlay: OverlayAsset) => {
    if (!selectedClipIds || selectedClipIds.length === 0) {
      // Show toast or notification
      console.warn("No clip selected");
      return;
    }

    const { applyOverlayToClip } = await import("../utils/applyOverlay");
    await applyOverlayToClip(selectedClipIds[0], overlay);
  };

  const handleEffectSelect = (effect: EffectPreset) => {
    if (!selectedClipIds || selectedClipIds.length === 0) {
      console.warn("No clip selected");
      return;
    }

    const { applyEffectToClip } = await import("../utils/applyEffect");
    applyEffectToClip(selectedClipIds[0], effect);
  };

  const handleTransitionSelect = (transition: TransitionPreset) => {
    if (!selectedClipIds || selectedClipIds.length !== 2) {
      console.warn("Select exactly 2 adjacent clips");
      return;
    }

    const { applyTransitionBetweenClips } = await import("../utils/applyTransition");
    try {
      applyTransitionBetweenClips(selectedClipIds[0], selectedClipIds[1], transition);
    } catch (error) {
      console.error("Failed to apply transition:", error);
    }
  };

  const hasClipSelected = selectedClipIds && selectedClipIds.length > 0;
  const hasTwoClipsSelected = selectedClipIds && selectedClipIds.length === 2;

  return (
    <div className="flex-1 min-h-0 flex flex-col overflow-hidden bg-surface/5 select-none">
      {/* Top Header Control Navigation Row */}
      <div className="flex items-center gap-2 p-1 border-b border-border/50 shrink-0 bg-surface/10">
        <div className="grow overflow-x-auto flex items-center gap-2 pb-0.5 whitespace-nowrap" style={{ scrollbarWidth: "none" }}>
          <button onClick={() => setActiveTab("effects")} className={`px-2 py-0.5 rounded-sm text-xs font-semibold transition-all cursor-pointer ${activeTab === "effects" ? "bg-accent text-white" : "text-text-muted hover:text-text-primary hover:bg-surface-raised/40"}`}>
            Effects
          </button>
          <button onClick={() => setActiveTab("overlays")} className={`px-2 py-0.5 rounded-sm text-xs font-semibold transition-all cursor-pointer ${activeTab === "overlays" ? "bg-accent text-white" : "text-text-muted hover:text-text-primary hover:bg-surface-raised/40"}`}>
            Overlays
          </button>
          <button onClick={() => setActiveTab("transitions")} className={`px-2 py-0.5 rounded-sm text-xs font-semibold transition-all cursor-pointer ${activeTab === "transitions" ? "bg-accent text-white" : "text-text-muted hover:text-text-primary hover:bg-surface-raised/40"}`}>
            Transitions
          </button>
        </div>
      </div>

      {/* Selection Hint */}
      {!hasClipSelected && activeTab !== "transitions" && (
        <div className="flex items-start gap-2 p-2.5 bg-yellow-500/10 border-b border-yellow-500/25 text-xs text-yellow-200 leading-normal">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>Select a clip on the timeline to apply {activeTab}</span>
        </div>
      )}

      {!hasTwoClipsSelected && activeTab === "transitions" && (
        <div className="flex items-start gap-2 p-2.5 bg-yellow-500/10 border-b border-yellow-500/25 text-xs text-yellow-200 leading-normal">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>Select exactly 2 adjacent clips on the timeline to apply transitions</span>
        </div>
      )}

      {/* Tab Content */}
      <div className="grow overflow-y-auto scrollbar-thin">
        {activeTab === "overlays" && <OverlayPicker onSelect={handleOverlaySelect} />}
        {activeTab === "effects" && <EffectPicker onSelect={handleEffectSelect} />}
        {activeTab === "transitions" && <TransitionPicker onSelect={handleTransitionSelect} />}
      </div>
    </div>
  );
}
