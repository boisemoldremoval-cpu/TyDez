import { TemplateCustomization, TextLayer } from "./types";

/**
 * Deep clones any object or array.
 */
function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj));
}

/**
 * Normalizes a hexadecimal color string to Lottie's normalized [r, g, b] format (0.0 to 1.0).
 */
export function hexToLottieColor(hex: string): [number, number, number] {
  let cleanHex = hex.replace("#", "");
  if (cleanHex.length === 3) {
    cleanHex = cleanHex.split("").map((c) => c + c).join("");
  }
  const r = parseInt(cleanHex.substring(0, 2), 16) / 255;
  const g = parseInt(cleanHex.substring(2, 4), 16) / 255;
  const b = parseInt(cleanHex.substring(4, 6), 16) / 255;
  return [
    isNaN(r) ? 1 : r,
    isNaN(g) ? 1 : g,
    isNaN(b) ? 1 : b
  ];
}

/**
 * Truncates text if it exceeds maxCharacters, appending an ellipsis.
 */
function truncateText(text: string, max: number): string {
  if (text.length > max) {
    return text.substring(0, max - 3) + "...";
  }
  return text;
}

/**
 * Mutates text documents inside a Lottie text layer's keyframes.
 */
function updateTextLayerData(layer: any, newText: string) {
  if (layer.t && layer.t.d) {
    const d = layer.t.d;
    if (Array.isArray(d.k)) {
      d.k.forEach((keyframe: any) => {
        if (keyframe && keyframe.s && typeof keyframe.s.t === "string") {
          keyframe.s.t = newText;
        }
      });
    } else if (d.k && d.k.s && typeof d.k.s.t === "string") {
      d.k.s.t = newText;
    }
  }
}

/**
 * Infers layer role and max character limit based on name if no textLayers config is provided.
 */
function inferTextLayerConfig(layerName: string): { role: 'primary' | 'secondary' | 'accent'; max: number } {
  const name = layerName.toLowerCase();
  if (name.includes("secondary") || name.includes("sub") || name.includes("cta") || name.includes("attribution") || name.includes("label")) {
    return { role: "secondary", max: 48 };
  } else if (name.includes("accent") || name.includes("year")) {
    return { role: "accent", max: 24 };
  } else {
    return { role: "primary", max: 32 };
  }
}

/**
 * Injects user customized text into a deep clone of the Lottie JSON data.
 */
export function injectText(
  lottieData: object,
  customization: TemplateCustomization,
  textLayers?: TextLayer[]
): object {
  const clone = deepClone(lottieData) as any;
  if (!clone.layers || !Array.isArray(clone.layers)) {
    return clone;
  }

  clone.layers.forEach((layer: any) => {
    // Check if layer is a text layer (ty: 5)
    if (layer.ty === 5 && layer.nm) {
      const matchedConfig = textLayers?.find((tl) => tl.layerName === layer.nm);
      const config = matchedConfig || inferTextLayerConfig(layer.nm);

      let targetText = "";
      if (config.role === "primary") {
        targetText = customization.primaryText;
      } else if (config.role === "secondary") {
        targetText = customization.secondaryText || "";
      } else if (config.role === "accent") {
        targetText = customization.accentText || "";
      }

      const maxChars = 'maxCharacters' in config ? config.maxCharacters : config.max;
      const truncated = truncateText(targetText, maxChars);
      updateTextLayerData(layer, truncated);
    }
  });

  return clone;
}

/**
 * Traverses shapes recursively to find fill shapes and inject colors.
 */
function injectColorToShapes(shapes: any[], lottieColor: [number, number, number]) {
  shapes.forEach((shape: any) => {
    if (!shape) return;

    // Fill shape is ty: "fl"
    if (shape.ty === "fl" && shape.c) {
      if (Array.isArray(shape.c.k)) {
        if (shape.c.k.length > 0 && typeof shape.c.k[0] === "number") {
          // Static color array: replace r, g, b, optionally keeping alpha
          shape.c.k[0] = lottieColor[0];
          shape.c.k[1] = lottieColor[1];
          shape.c.k[2] = lottieColor[2];
        } else {
          // Keyframed array: loop over keyframes
          shape.c.k.forEach((keyframe: any) => {
            if (keyframe) {
              if (Array.isArray(keyframe.s)) {
                keyframe.s[0] = lottieColor[0];
                keyframe.s[1] = lottieColor[1];
                keyframe.s[2] = lottieColor[2];
              }
              if (Array.isArray(keyframe.e)) {
                keyframe.e[0] = lottieColor[0];
                keyframe.e[1] = lottieColor[1];
                keyframe.e[2] = lottieColor[2];
              }
            }
          });
        }
      }
    }

    // Group shape (ty: "gr") can contain shapes list
    if (shape.ty === "gr" && Array.isArray(shape.it)) {
      injectColorToShapes(shape.it, lottieColor);
    }
  });
}

/**
 * Injects a hexadecimal color into shapes of a specific named layer.
 */
export function injectColor(
  lottieData: object,
  layerName: string,
  hexColor: string
): object {
  const clone = deepClone(lottieData) as any;
  if (!clone.layers || !Array.isArray(clone.layers)) {
    return clone;
  }

  const lottieColor = hexToLottieColor(hexColor);

  clone.layers.forEach((layer: any) => {
    if (layer.nm === layerName && Array.isArray(layer.shapes)) {
      injectColorToShapes(layer.shapes, lottieColor);
    }
  });

  return clone;
}
