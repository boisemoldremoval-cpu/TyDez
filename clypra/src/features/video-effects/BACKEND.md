# Backend Implementation Guide

This document provides guidance for implementing the video effects API endpoints.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Cloudflare Worker                        │
│  ┌───────────────────────────────────────────────────────┐ │
│  │                 API Routes                            │ │
│  │  /video-effects/manifest                              │ │
│  │  /video-effects/:type/:category                       │ │
│  │  /video-effects/:type/:category/:id                   │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              KV Store (Metadata)                      │ │
│  │  - Manifest                                           │ │
│  │  - Categories                                         │ │
│  │  - Effect/Transition definitions (JSON)               │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              R2 Storage (Assets)                      │ │
│  │  - Overlay video files (.mov, .webm)                 │ │
│  │  - Thumbnails (.jpg, .png)                           │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## KV Store Structure

### Key: `video-effects:manifest`

```json
{
  "version": "1.0.0",
  "categories": [
    {
      "id": "particle",
      "name": "Particle Effects",
      "type": "overlay",
      "description": "Smoke, fire, dust, and particle effects",
      "thumbnail": "https://cdn.clypra.com/thumbs/category-particle.jpg",
      "itemCount": 15
    },
    {
      "id": "camera",
      "name": "Camera Effects",
      "type": "effect",
      "description": "Shake, zoom, pan, and camera movements",
      "thumbnail": "https://cdn.clypra.com/thumbs/category-camera.jpg",
      "itemCount": 8
    },
    {
      "id": "basic",
      "name": "Basic Transitions",
      "type": "transition",
      "description": "Fade, dissolve, cut",
      "thumbnail": "https://cdn.clypra.com/thumbs/category-basic.jpg",
      "itemCount": 5
    }
  ],
  "featured": ["overlay:particle:smoke_001", "effect:camera:shake_strong", "transition:zoom:zoom_in"]
}
```

### Key: `video-effects:overlay:particle`

```json
[
  {
    "id": "smoke_001",
    "name": "Rising Smoke",
    "type": "overlay",
    "category": "particle",
    "description": "Realistic smoke rising effect with alpha channel",
    "thumbnail": "https://cdn.clypra.com/thumbs/smoke_001.jpg",
    "url": "https://cdn.clypra.com/overlays/smoke_001.webm",
    "duration": 5.0,
    "width": 1920,
    "height": 1080,
    "hasAlpha": true,
    "fileFormat": "webm",
    "fileSize": 2457600,
    "tags": ["smoke", "fog", "atmospheric", "rising"],
    "isPremium": false,
    "blendMode": "screen",
    "loopable": true,
    "recommended": {
      "opacity": 0.7,
      "blendMode": "screen",
      "placement": "fullscreen"
    }
  },
  {
    "id": "fire_001",
    "name": "Fire Burst",
    "type": "overlay",
    "category": "particle",
    "description": "Explosive fire effect with alpha channel",
    "thumbnail": "https://cdn.clypra.com/thumbs/fire_001.jpg",
    "url": "https://cdn.clypra.com/overlays/fire_001.webm",
    "duration": 3.0,
    "width": 1920,
    "height": 1080,
    "hasAlpha": true,
    "fileFormat": "webm",
    "fileSize": 3145728,
    "tags": ["fire", "explosion", "burst", "flame"],
    "isPremium": false,
    "blendMode": "add",
    "loopable": false,
    "recommended": {
      "opacity": 0.8,
      "blendMode": "add",
      "placement": "overlay"
    }
  }
]
```

### Key: `video-effects:effect:camera`

```json
[
  {
    "id": "shake_strong",
    "name": "Strong Shake",
    "type": "effect",
    "category": "camera",
    "description": "Intense camera shake for action scenes",
    "thumbnail": "https://cdn.clypra.com/thumbs/shake_strong.jpg",
    "renderer": "shake",
    "params": {
      "intensity": 80,
      "frequency": 15
    },
    "tags": ["shake", "camera", "movement", "handheld"],
    "isPremium": false,
    "intensity": {
      "min": 0,
      "max": 100,
      "default": 80,
      "step": 1
    }
  },
  {
    "id": "zoom_dramatic",
    "name": "Dramatic Zoom",
    "type": "effect",
    "category": "camera",
    "description": "Slow zoom in for dramatic effect",
    "thumbnail": "https://cdn.clypra.com/thumbs/zoom_dramatic.jpg",
    "renderer": "zoom",
    "params": {
      "scale": 1.3,
      "centerX": 0.5,
      "centerY": 0.5
    },
    "tags": ["zoom", "camera", "dolly", "dramatic"],
    "isPremium": false,
    "intensity": {
      "min": 0,
      "max": 100,
      "default": 70,
      "step": 1
    }
  }
]
```

### Key: `video-effects:transition:basic`

```json
[
  {
    "id": "fade",
    "name": "Fade",
    "type": "transition",
    "category": "basic",
    "description": "Classic crossfade between clips",
    "thumbnail": "https://cdn.clypra.com/thumbs/fade.jpg",
    "renderer": "fade",
    "params": {
      "easing": "ease-in-out"
    },
    "tags": ["fade", "crossfade", "basic", "smooth"],
    "isPremium": false,
    "duration": {
      "min": 0.1,
      "max": 3.0,
      "default": 0.5,
      "step": 0.1
    },
    "easing": "ease-in-out"
  },
  {
    "id": "dissolve",
    "name": "Dissolve",
    "type": "transition",
    "category": "basic",
    "description": "Smooth dissolve between clips",
    "thumbnail": "https://cdn.clypra.com/thumbs/dissolve.jpg",
    "renderer": "dissolve",
    "params": {
      "easing": "linear"
    },
    "tags": ["dissolve", "fade", "basic"],
    "isPremium": false,
    "duration": {
      "min": 0.1,
      "max": 3.0,
      "default": 1.0,
      "step": 0.1
    },
    "easing": "linear"
  }
]
```

---

## API Routes Implementation

### 1. Get Manifest

**Endpoint:** `GET /video-effects/manifest`

```typescript
async function getManifest(env: Env): Promise<Response> {
  const cached = await env.CACHE.match("video-effects:manifest");
  if (cached) {
    return cached;
  }

  const manifest = await env.KV.get("video-effects:manifest", "json");

  if (!manifest) {
    return new Response(JSON.stringify({ error: "Manifest not found" }), {
      status: 404,
      headers: { "Content-Type": "application/json" },
    });
  }

  const response = new Response(JSON.stringify(manifest), {
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "public, max-age=3600", // 1 hour
    },
  });

  await env.CACHE.put("video-effects:manifest", response.clone());
  return response;
}
```

### 2. Get Items by Category

**Endpoint:** `GET /video-effects/:type/:category`

```typescript
async function getItemsByCategory(type: "overlay" | "effect" | "transition", category: string, env: Env): Promise<Response> {
  const cacheKey = `video-effects:${type}:${category}`;
  const cached = await env.CACHE.match(cacheKey);
  if (cached) {
    return cached;
  }

  const items = await env.KV.get(cacheKey, "json");

  if (!items) {
    return new Response(JSON.stringify({ error: `Category not found: ${type}/${category}` }), {
      status: 404,
      headers: { "Content-Type": "application/json" },
    });
  }

  const response = new Response(JSON.stringify(items), {
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "public, max-age=3600",
    },
  });

  await env.CACHE.put(cacheKey, response.clone());
  return response;
}
```

### 3. Get Individual Item

**Endpoint:** `GET /video-effects/:type/:category/:id`

```typescript
async function getItem(type: "overlay" | "effect" | "transition", category: string, id: string, env: Env): Promise<Response> {
  const cacheKey = `video-effects:${type}:${category}:${id}`;
  const cached = await env.CACHE.match(cacheKey);
  if (cached) {
    return cached;
  }

  // Get all items in category
  const items = await env.KV.get(`video-effects:${type}:${category}`, "json");

  if (!items || !Array.isArray(items)) {
    return new Response(JSON.stringify({ error: "Category not found" }), {
      status: 404,
      headers: { "Content-Type": "application/json" },
    });
  }

  const item = items.find((i: any) => i.id === id);

  if (!item) {
    return new Response(JSON.stringify({ error: `Item not found: ${id}` }), {
      status: 404,
      headers: { "Content-Type": "application/json" },
    });
  }

  const response = new Response(JSON.stringify(item), {
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "public, max-age=86400", // 24 hours
    },
  });

  await env.CACHE.put(cacheKey, response.clone());
  return response;
}
```

### 4. Search

**Endpoint:** `GET /video-effects/search?q=smoke&type=overlay`

```typescript
async function search(query: string, type: "overlay" | "effect" | "transition" | undefined, env: Env): Promise<Response> {
  const manifest = await env.KV.get("video-effects:manifest", "json");
  if (!manifest) {
    return new Response(JSON.stringify([]), {
      headers: { "Content-Type": "application/json" },
    });
  }

  const results: any[] = [];
  const categories = manifest.categories.filter((cat: any) => (type ? cat.type === type : true));

  for (const category of categories) {
    const items = await env.KV.get(`video-effects:${category.type}:${category.id}`, "json");

    if (items && Array.isArray(items)) {
      const matches = items.filter((item: any) => item.name.toLowerCase().includes(query.toLowerCase()) || item.description.toLowerCase().includes(query.toLowerCase()) || item.tags?.some((tag: string) => tag.toLowerCase().includes(query.toLowerCase())));

      results.push(...matches);
    }
  }

  return new Response(JSON.stringify(results), {
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "public, max-age=300", // 5 minutes
    },
  });
}
```

---

## R2 Storage Structure

```
clypra-video-effects/
├── overlays/
│   ├── smoke_001.webm          (5MB, 1920x1080, 5s, alpha)
│   ├── fire_001.webm           (3MB, 1920x1080, 3s, alpha)
│   ├── dust_001.webm           (2MB, 1920x1080, 4s, alpha)
│   └── light_leak_001.mov      (4MB, 1920x1080, 6s, alpha)
├── thumbs/
│   ├── smoke_001.jpg           (100KB)
│   ├── fire_001.jpg            (100KB)
│   ├── shake_strong.jpg        (100KB)
│   └── fade.jpg                (100KB)
└── category-thumbs/
    ├── category-particle.jpg   (150KB)
    ├── category-camera.jpg     (150KB)
    └── category-basic.jpg      (150KB)
```

---

## Populating with Free Content

### Script: Upload Overlays

```typescript
import { R2Bucket } from "@cloudflare/workers-types";
import { createReadStream } from "fs";
import { readdir } from "fs/promises";

async function uploadOverlays(r2: R2Bucket, sourceDir: string) {
  const files = await readdir(sourceDir);

  for (const file of files) {
    if (!file.endsWith(".webm") && !file.endsWith(".mov")) continue;

    const stream = createReadStream(`${sourceDir}/${file}`);
    const key = `overlays/${file}`;

    await r2.put(key, stream, {
      httpMetadata: {
        contentType: file.endsWith(".webm") ? "video/webm" : "video/quicktime",
      },
    });

    console.log(`Uploaded: ${key}`);
  }
}
```

### Script: Populate KV

```typescript
async function populateKV(kv: KVNamespace) {
  // 1. Upload manifest
  await kv.put(
    "video-effects:manifest",
    JSON.stringify({
      version: "1.0.0",
      categories: [
        {
          id: "particle",
          name: "Particle Effects",
          type: "overlay",
          description: "Smoke, fire, dust, and particle effects",
          thumbnail: "https://cdn.clypra.com/thumbs/category-particle.jpg",
          itemCount: 2,
        },
        // ... more categories
      ],
      featured: ["overlay:particle:smoke_001"],
    }),
  );

  // 2. Upload overlay items
  await kv.put(
    "video-effects:overlay:particle",
    JSON.stringify([
      {
        id: "smoke_001",
        name: "Rising Smoke",
        type: "overlay",
        category: "particle",
        url: "https://cdn.clypra.com/overlays/smoke_001.webm",
        duration: 5.0,
        width: 1920,
        height: 1080,
        hasAlpha: true,
        fileFormat: "webm",
        loopable: true,
        // ... more properties
      },
    ]),
  );

  // 3. Upload effect presets
  await kv.put(
    "video-effects:effect:camera",
    JSON.stringify([
      {
        id: "shake_strong",
        name: "Strong Shake",
        type: "effect",
        renderer: "shake",
        params: { intensity: 80, frequency: 15 },
        // ... more properties
      },
    ]),
  );

  console.log("KV populated successfully");
}
```

---

## Testing

### Test Manifest

```bash
curl https://clypra-worker-api.abdulkabirmusa.com/video-effects/manifest
```

### Test Category

```bash
curl https://clypra-worker-api.abdulkabirmusa.com/video-effects/overlay/particle
```

### Test Individual Item

```bash
curl https://clypra-worker-api.abdulkabirmusa.com/video-effects/overlay/particle/smoke_001
```

### Test Search

```bash
curl "https://clypra-worker-api.abdulkabirmusa.com/video-effects/search?q=smoke&type=overlay"
```

---

## Deployment Checklist

- [ ] Set up R2 bucket: `clypra-video-effects`
- [ ] Upload overlay video files to R2
- [ ] Upload thumbnails to R2
- [ ] Populate KV with manifest
- [ ] Populate KV with category definitions
- [ ] Deploy Worker with new routes
- [ ] Test all endpoints
- [ ] Configure CDN caching
- [ ] Set up monitoring/analytics
- [ ] Document API for frontend team

---

## Next Steps

1. **Collect Free Content**: Download overlays from Videezy, Filmstocks, Mixkit
2. **Convert to WebM**: Use FFmpeg to convert to WebM with alpha
3. **Generate Thumbnails**: Extract first frame for thumbnails
4. **Upload to R2**: Use upload script
5. **Create Definitions**: Write JSON for effects and transitions
6. **Populate KV**: Run population script
7. **Deploy & Test**: Deploy Worker and test endpoints

---

## Performance Considerations

- **Cache-Control**: Set aggressive caching (1h for manifest, 24h for items)
- **CDN**: Use Cloudflare CDN for R2 assets
- **Compression**: Use Brotli/Gzip for JSON responses
- **Lazy Loading**: Load categories on-demand in frontend
- **Preload**: Preload featured items for faster UX

---

## Cost Estimation

**R2 Storage** (free tier: 10GB)

- 50 overlays × 3MB = 150MB
- Thumbnails = 10MB
- **Total**: ~160MB (well within free tier)

**KV Operations** (free tier: 100k reads/day)

- Manifest: ~1k reads/day
- Categories: ~5k reads/day
- Items: ~10k reads/day
- **Total**: ~16k/day (well within free tier)

**Bandwidth** (free tier: 10GB/month)

- Video downloads: Users download overlays once, then cached
- Estimated: 2GB/month for 1000 users
- **Total**: Well within free tier
