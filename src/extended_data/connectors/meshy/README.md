# Meshy SDK

Modular Python package for generating game assets via Meshy API.

## Features

- **All Endpoints**: Text-to-3D, Text-to-Texture, Image-to-3D
- **Rate Limiting**: Automatic 429 handling with exponential backoff
- **Type Safety**: Pydantic models for all API types
- **Job Orchestration**: High-level `AssetGenerator` for game asset workflows
- **Auto-Download**: Fetches GLB models, PBR textures, thumbnails
- **Metadata**: JSON manifests for ECS integration

## Quick Start

```python
from tools.meshy import AssetGenerator, otter_player_spec

# Generate player character
generator = AssetGenerator(output_root="client/public")
manifest = generator.generate_model(otter_player_spec(), wait=True)

print(f"Model: {manifest.model_path}")
print(f"Textures: {manifest.texture_paths}")
```

## CLI Usage

```bash
python3 scripts/generate_assets.py
```

Generates 6 core assets:
- Player otter
- 2 NPC otters
- Bass fish
- Cattail reeds
- Wooden dock

Assets output to `client/public/models/` with manifests.

## API

### Client

```python
from tools.meshy import MeshyClient, Text3DRequest, ArtStyle

client = MeshyClient()  # Uses MESHY_API_KEY env var

# Create task
task_id = client.create_text_to_3d(Text3DRequest(
    prompt="anthropomorphic otter character",
    art_style=ArtStyle.REALISTIC,
    target_polycount=15000,
    enable_pbr=True
))

# Poll until complete
result = client.poll_until_complete(task_id, task_type="text-to-3d")
client.download_file(result.model_urls.glb, "output.glb")
```

### Asset Generator

```python
from tools.meshy import AssetGenerator, GameAssetSpec, AssetIntent, ArtStyle

spec = GameAssetSpec(
    intent=AssetIntent.CREATURE_PREY,
    description="realistic marsh frog, green skin, sitting pose",
    art_style=ArtStyle.REALISTIC,
    target_polycount=5000,
    output_path="models/creatures"
)

generator = AssetGenerator()
manifest = generator.generate_model(spec, wait=True)
```

### Preset Specs

Pre-configured specs for common assets:

- `otter_player_spec()` - Player character
- `otter_npc_male_spec()` - Male NPC
- `otter_npc_female_spec()` - Female NPC
- `fish_bass_spec()` - Bass fish
- `cattail_reeds_spec()` - Marsh vegetation
- `wooden_dock_spec()` - Dock structure

## Dependencies

- `httpx` - HTTP client
- `tenacity` - Retry logic
- `pydantic` - Type validation
