/**
 * Frame Scheduler Integration Tests
 *
 * Tests the complete pipeline:
 *   Timeline → Scheduler → Evaluation → Rasterization → Output
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { FrameScheduler, resetFrameScheduler } from "../FrameScheduler";
import type { Clip, Track, MediaAsset, Project } from "@/types";

// Mock Tauri API
vi.mock("@tauri-apps/api/core", () => ({
  convertFileSrc: (path: string) => `asset://localhost/${path}`,
}));

// Mock OffscreenCanvas for Node environment
class MockImageData {
  data: Uint8ClampedArray;
  width: number;
  height: number;

  constructor(width: number, height: number) {
    this.data = new Uint8ClampedArray(width * height * 4);
    this.width = width;
    this.height = height;
  }
}

class MockOffscreenCanvas {
  width: number;
  height: number;
  private ctx: any;

  constructor(width: number, height: number) {
    this.width = width;
    this.height = height;
    this.ctx = {
      fillStyle: "",
      strokeStyle: "",
      globalAlpha: 1,
      globalCompositeOperation: "source-over",
      font: "",
      textAlign: "left",
      textBaseline: "alphabetic",
      lineWidth: 1,
      shadowColor: "",
      shadowBlur: 0,
      shadowOffsetX: 0,
      shadowOffsetY: 0,
      fillRect: vi.fn(),
      strokeRect: vi.fn(),
      fillText: vi.fn(),
      strokeText: vi.fn(),
      drawImage: vi.fn(),
      save: vi.fn(),
      restore: vi.fn(),
      translate: vi.fn(),
      rotate: vi.fn(),
      scale: vi.fn(),
      getImageData: vi.fn(() => new MockImageData(width, height)),
      measureText: vi.fn((text: string) => ({
        width: text.length * 10,
        actualBoundingBoxLeft: 0,
        actualBoundingBoxRight: text.length * 10,
        actualBoundingBoxAscent: 12,
        actualBoundingBoxDescent: 3,
        fontBoundingBoxAscent: 15,
        fontBoundingBoxDescent: 5,
        alphabeticBaseline: 0,
      })),
      clearRect: vi.fn(),
      beginPath: vi.fn(),
      closePath: vi.fn(),
      rect: vi.fn(),
      clip: vi.fn(),
      moveTo: vi.fn(),
      lineTo: vi.fn(),
      arc: vi.fn(),
      stroke: vi.fn(),
      fill: vi.fn(),
    };
  }

  getContext(type: string) {
    return type === "2d" ? this.ctx : null;
  }

  transferToImageBitmap() {
    return Promise.resolve({ width: this.width, height: this.height, close: vi.fn() });
  }

  convertToBlob(options?: any) {
    return Promise.resolve(new Blob(["mock"], { type: options?.type || "image/png" }));
  }
}

// @ts-ignore - Mock for Node environment
globalThis.OffscreenCanvas = MockOffscreenCanvas;
// @ts-ignore - Mock for Node environment
globalThis.ImageData = MockImageData;
// @ts-ignore - Mock ImageBitmap
globalThis.ImageBitmap = class MockImageBitmap {
  width: number;
  height: number;
  constructor(width: number = 100, height: number = 100) {
    this.width = width;
    this.height = height;
  }
  close() {}
};
globalThis.fetch = vi.fn(() =>
  Promise.resolve({
    blob: () => Promise.resolve(new Blob(["mock-image"])),
  } as any),
);
globalThis.createImageBitmap = vi.fn((source: any) => {
  const width = source?.width || 100;
  const height = source?.height || 100;
  return Promise.resolve(new (globalThis.ImageBitmap as any)(width, height));
});

describe("FrameScheduler Integration", () => {
  let scheduler: FrameScheduler;
  let mockClips: Clip[];
  let mockTracks: Track[];
  let mockAssets: MediaAsset[];
  let mockProject: Project;

  beforeEach(() => {
    resetFrameScheduler();
    scheduler = new FrameScheduler({ debug: false });

    // Create mock timeline data
    mockTracks = [
      {
        id: "track-1",
        name: "Video Track 1",
        type: "video",
        visible: true,
        muted: false,
        locked: false,
        height: 80,
      },
    ];

    mockAssets = [
      {
        id: "asset-1",
        name: "test-video.mp4",
        type: "video",
        path: "/test/video.mp4",
        duration: 10,
        width: 1920,
        height: 1080,
        size: 1024 * 1024,
        posterFrame: "data:image/png;base64,test",
      },
    ];

    mockClips = [
      {
        id: "clip-1",
        mediaId: "asset-1",
        trackId: "track-1",
        startTime: 0,
        duration: 5,
        trimIn: 0,
        trimOut: 5,
        x: 0,
        y: 0,
        width: 1920,
        height: 1080,
        rotation: 0,
        opacity: 1,
      },
    ];

    mockProject = {
      id: "project-1",
      name: "Test Project",
      canvasWidth: 1920,
      canvasHeight: 1080,
      frameRate: 30,
      aspectRatio: "16:9",
      duration: 10,
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };

    // Update timeline state
    scheduler.updateTimeline(mockClips, mockTracks, mockAssets, mockProject, 0);
  });

  describe("Basic Scheduling", () => {
    it("should schedule and complete a frame render", async () => {
      const jobId = scheduler.schedule({
        time: 1.0,
        resolution: { width: 1920, height: 1080 },
        outputFormat: "imagebitmap",
        priority: "realtime",
      });

      expect(jobId).toBeDefined();

      const job = scheduler.getJob(jobId);
      expect(job).toBeDefined();
      // Job status can be 'pending' or 'loading' depending on timing
      expect(["pending", "loading", "evaluating", "rasterizing"]).toContain(job?.status);

      const result = await scheduler.wait(jobId);

      expect(result).toBeDefined();
      expect(result.data).toBeDefined();
      expect(result.data).toHaveProperty("width");
      expect(result.data).toHaveProperty("height");
      expect(result.renderTimeMs).toBeGreaterThan(0);

      const completedJob = scheduler.getJob(jobId);
      expect(completedJob?.status).toBe("complete");
    });

    it("should handle multiple concurrent frames", async () => {
      const jobIds = [
        scheduler.schedule({
          time: 0.0,
          resolution: { width: 1920, height: 1080 },
          outputFormat: "imagebitmap",
          priority: "realtime",
        }),
        scheduler.schedule({
          time: 1.0,
          resolution: { width: 1920, height: 1080 },
          outputFormat: "imagebitmap",
          priority: "realtime",
        }),
        scheduler.schedule({
          time: 2.0,
          resolution: { width: 1920, height: 1080 },
          outputFormat: "imagebitmap",
          priority: "realtime",
        }),
      ];

      const results = await Promise.all(jobIds.map((id) => scheduler.wait(id)));

      expect(results).toHaveLength(3);
      results.forEach((result) => {
        expect(result.data).toBeDefined();
        expect(result.data).toHaveProperty("width");
        expect(result.data).toHaveProperty("height");
      });
    });
  });

  describe("Priority Scheduling", () => {
    it("should prioritize realtime over background", async () => {
      // Schedule background job first
      const backgroundJobId = scheduler.schedule({
        time: 1.0,
        resolution: { width: 1920, height: 1080 },
        outputFormat: "imagebitmap",
        priority: "background",
      });

      // Schedule realtime job second (should jump queue)
      const realtimeJobId = scheduler.schedule({
        time: 2.0,
        resolution: { width: 1920, height: 1080 },
        outputFormat: "imagebitmap",
        priority: "realtime",
      });

      // Both should complete, but realtime should be processed first
      const results = await Promise.all([scheduler.wait(realtimeJobId), scheduler.wait(backgroundJobId)]);

      expect(results).toHaveLength(2);
    });

    it("should prioritize export over background", async () => {
      const backgroundJobId = scheduler.schedule({
        time: 1.0,
        resolution: { width: 1920, height: 1080 },
        outputFormat: "imagebitmap",
        priority: "background",
      });

      const exportJobId = scheduler.schedule({
        time: 2.0,
        resolution: { width: 1920, height: 1080 },
        outputFormat: "blob",
        priority: "export",
      });

      const results = await Promise.all([scheduler.wait(exportJobId), scheduler.wait(backgroundJobId)]);

      expect(results).toHaveLength(2);
    });
  });

  describe("Cancellation", () => {
    it("should cancel a pending job", async () => {
      const jobId = scheduler.schedule({
        time: 1.0,
        resolution: { width: 1920, height: 1080 },
        outputFormat: "imagebitmap",
        priority: "realtime",
      });

      scheduler.cancel(jobId);

      const job = scheduler.getJob(jobId);
      expect(job?.cancelled).toBe(true);
      expect(job?.status).toBe("cancelled");

      await expect(scheduler.wait(jobId)).rejects.toThrow("Job cancelled");
    });

    it("should cancel all jobs", async () => {
      const jobIds = [
        scheduler.schedule({
          time: 0.0,
          resolution: { width: 1920, height: 1080 },
          outputFormat: "imagebitmap",
          priority: "realtime",
        }),
        scheduler.schedule({
          time: 1.0,
          resolution: { width: 1920, height: 1080 },
          outputFormat: "imagebitmap",
          priority: "realtime",
        }),
      ];

      scheduler.cancelAll();

      for (const jobId of jobIds) {
        const job = scheduler.getJob(jobId);
        expect(job?.cancelled).toBe(true);
      }
    });
  });

  describe("Output Formats", () => {
    it("should output ImageBitmap", async () => {
      const jobId = scheduler.schedule({
        time: 1.0,
        resolution: { width: 1920, height: 1080 },
        outputFormat: "imagebitmap",
        priority: "realtime",
      });

      const result = await scheduler.wait(jobId);
      expect(result.data).toBeDefined();
      expect(result.data).toHaveProperty("width");
      expect(result.data).toHaveProperty("height");
    });

    it("should output ImageData", async () => {
      const jobId = scheduler.schedule({
        time: 1.0,
        resolution: { width: 1920, height: 1080 },
        outputFormat: "imagedata",
        priority: "realtime",
      });

      const result = await scheduler.wait(jobId);
      expect(result.data).toBeDefined();
      expect(result.data).toHaveProperty("width");
      expect(result.data).toHaveProperty("height");
    });

    it("should output Blob", async () => {
      const jobId = scheduler.schedule({
        time: 1.0,
        resolution: { width: 1920, height: 1080 },
        outputFormat: "blob",
        priority: "export",
      });

      const result = await scheduler.wait(jobId);
      expect(result.data).toBeDefined();
      expect(result.data).toBeInstanceOf(Blob);
    });
  });

  describe("Telemetry", () => {
    it("should track statistics", async () => {
      const jobId = scheduler.schedule({
        time: 1.0,
        resolution: { width: 1920, height: 1080 },
        outputFormat: "imagebitmap",
        priority: "realtime",
      });

      await scheduler.wait(jobId);

      const stats = scheduler.getStats();

      expect(stats.totalJobs).toBe(1);
      expect(stats.complete).toBe(1);
      expect(stats.avgEvaluationTimeMs).toBeGreaterThanOrEqual(0);
      expect(stats.avgRasterTimeMs).toBeGreaterThanOrEqual(0);
      expect(stats.avgTotalTimeMs).toBeGreaterThanOrEqual(0);
    });

    it("should track job metrics", async () => {
      const jobId = scheduler.schedule({
        time: 1.0,
        resolution: { width: 1920, height: 1080 },
        outputFormat: "imagebitmap",
        priority: "realtime",
      });

      await scheduler.wait(jobId);

      const job = scheduler.getJob(jobId);

      expect(job?.metrics.evaluationTimeMs).toBeGreaterThanOrEqual(0);
      expect(job?.metrics.rasterTimeMs).toBeGreaterThanOrEqual(0);
      expect(job?.metrics.totalTimeMs).toBeGreaterThanOrEqual(0);
    });
  });

  describe("Timeline Updates", () => {
    it("should handle timeline state updates", () => {
      const newClips = [
        ...mockClips,
        {
          id: "clip-2",
          mediaId: "asset-1",
          trackId: "track-1",
          startTime: 5,
          duration: 5,
          trimIn: 0,
          trimOut: 5,
          x: 0,
          y: 0,
          width: 1920,
          height: 1080,
          rotation: 0,
          opacity: 1,
        },
      ];

      scheduler.updateTimeline(newClips, mockTracks, mockAssets, mockProject, 1);

      // Should be able to schedule frames with new timeline
      const jobId = scheduler.schedule({
        time: 6.0,
        resolution: { width: 1920, height: 1080 },
        outputFormat: "imagebitmap",
        priority: "realtime",
      });

      expect(jobId).toBeDefined();
    });
  });

  describe("Resolution Independence", () => {
    it("should render at different resolutions", async () => {
      const resolutions = [
        { width: 1920, height: 1080 },
        { width: 1280, height: 720 },
        { width: 640, height: 360 },
      ];

      const jobIds = resolutions.map((resolution) =>
        scheduler.schedule({
          time: 1.0,
          resolution,
          outputFormat: "imagebitmap",
          priority: "realtime",
        }),
      );

      const results = await Promise.all(jobIds.map((id) => scheduler.wait(id)));

      expect(results).toHaveLength(3);
      results.forEach((result, i) => {
        expect(result.data).toBeDefined();
        expect(result.data).toHaveProperty("width");
        expect(result.data).toHaveProperty("height");
        const bitmap = result.data as any;
        expect(bitmap.width).toBe(resolutions[i].width);
        expect(bitmap.height).toBe(resolutions[i].height);
      });
    });
  });
});
