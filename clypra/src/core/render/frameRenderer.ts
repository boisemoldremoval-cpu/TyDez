/**
 * Single-Frame Renderer
 *
 * High-level API for frame export.
 * Delegates to rasterizer for actual pixel generation.
 *
 * Architecture:
 *   EvaluatedScene → rasterizeScene() → RasterFrame → Blob/ImageData
 */

import type { EvaluatedScene } from "../evaluation/types";
import { rasterizeScene, type RasterTarget } from "./rasterizer";

/**
 * Frame render options.
 */
export interface RenderFrameOptions {
  /** Output width in pixels */
  width: number;

  /** Output height in pixels */
  height: number;

  /** Background color (default: black) */
  backgroundColor?: string;

  /** Image format for output */
  format?: "imagebitmap" | "imagedata" | "blob";

  /** Quality for blob output (0-1, JPEG/WebP only) */
  quality?: number;

  /** MIME type for blob output */
  mimeType?: "image/png" | "image/jpeg" | "image/webp";
}

/**
 * Frame render result.
 */
export interface RenderFrameResult {
  /** Rendered frame data */
  data: ImageBitmap | ImageData | Blob;

  /** Output format */
  format: "imagebitmap" | "imagedata" | "blob";

  /** Render time in milliseconds */
  renderTimeMs: number;

  /** Canvas dimensions */
  width: number;
  height: number;
}

/**
 * Render a single frame from an evaluated scene.
 *
 * This delegates to rasterizeScene() for pixel generation.
 *
 * @param scene - Evaluated scene to render
 * @param options - Render options
 * @returns Rendered frame
 */
export async function renderFrame(scene: EvaluatedScene, options: RenderFrameOptions): Promise<RenderFrameResult> {
  const startTime = performance.now();

  const { width, height, backgroundColor = "#000000", format = "imagebitmap", quality = 0.92, mimeType = "image/png" } = options;

  // Rasterize scene
  const rasterTarget: RasterTarget = {
    width,
    height,
    backgroundColor,
  };

  const rasterFrame = await rasterizeScene(scene, rasterTarget);

  // Convert to requested format
  let data: ImageBitmap | ImageData | Blob;

  switch (format) {
    case "imagebitmap":
      if (rasterFrame.canvas instanceof OffscreenCanvas) {
        data = await rasterFrame.canvas.transferToImageBitmap();
      } else {
        // For HTMLCanvasElement, create ImageBitmap from canvas
        data = await createImageBitmap(rasterFrame.canvas);
      }
      break;

    case "imagedata":
      data = rasterFrame.ctx.getImageData(0, 0, width, height);
      break;

    case "blob":
      if (rasterFrame.canvas instanceof OffscreenCanvas) {
        data = await rasterFrame.canvas.convertToBlob({ type: mimeType, quality });
      } else {
        // For HTMLCanvasElement, use toBlob
        data = await new Promise<Blob>((resolve, reject) => {
          (rasterFrame.canvas as HTMLCanvasElement).toBlob(
            (blob) => {
              if (blob) resolve(blob);
              else reject(new Error("Failed to create blob"));
            },
            mimeType,
            quality,
          );
        });
      }
      break;

    default:
      throw new Error(`Unsupported format: ${format}`);
  }

  const renderTimeMs = performance.now() - startTime;

  return {
    data,
    format,
    renderTimeMs,
    width,
    height,
  };
}

/**
 * Render frame to PNG blob (convenience function).
 */
export async function renderFrameToPNG(scene: EvaluatedScene, width: number, height: number): Promise<Blob> {
  const result = await renderFrame(scene, {
    width,
    height,
    format: "blob",
    mimeType: "image/png",
  });

  if (!(result.data instanceof Blob)) {
    throw new Error("Expected Blob output");
  }

  return result.data;
}

/**
 * Render frame to JPEG blob (convenience function).
 */
export async function renderFrameToJPEG(scene: EvaluatedScene, width: number, height: number, quality: number = 0.92): Promise<Blob> {
  const result = await renderFrame(scene, {
    width,
    height,
    format: "blob",
    mimeType: "image/jpeg",
    quality,
  });

  if (!(result.data instanceof Blob)) {
    throw new Error("Expected Blob output");
  }

  return result.data;
}

/**
 * Render frame to ImageData (for pixel manipulation).
 */
export async function renderFrameToImageData(scene: EvaluatedScene, width: number, height: number): Promise<ImageData> {
  const result = await renderFrame(scene, {
    width,
    height,
    format: "imagedata",
  });

  if (!(result.data instanceof ImageData)) {
    throw new Error("Expected ImageData output");
  }

  return result.data;
}
