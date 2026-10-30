"""Seeds realistic portfolio-grade sample images into the platform library."""

import shutil
from pathlib import Path
from PIL import Image

from backend.storage import StorageManager
from backend.local_editor import apply_preset_filter
from backend.config import SAMPLES_DIR, BASE_DIR

# 5 New Curated High-Aesthetic Portfolio Assets
SOURCE_IMAGES = [
    {
        "filename": "studio_fashion_portrait.jpg",
        "title": "High-Fashion Editorial Portrait",
        "caption": "An elegant, striking studio fashion portrait of a young woman with natural makeup, subtle freckles, and warm rim lighting against a neutral slate backdrop.",
        "tags": ["portrait", "fashion", "editorial", "studio", "woman", "lighting", "aesthetic", "model", "beauty", "sharp"],
        "objects": ["fashion model", "linen blouse", "earrings", "studio backdrop", "softbox lighting"],
        "dominant_colors": ["Warm Amber", "Charcoal Slate", "Porcelain Ivory", "Soft Terracotta"],
        "sample_edit": ("noir_monochrome", "preset", "High-contrast fine-art noir black and white transformation")
    },
    {
        "filename": "cyberpunk_neon_city.jpg",
        "title": "Cyberpunk Tokyo Night Rain",
        "caption": "A futuristic neon-drenched metropolis street at night with glowing electric cyan and magenta signs reflecting across rain-slick asphalt pavements.",
        "tags": ["cyberpunk", "neon", "tokyo", "city", "night", "street", "reflections", "rain", "futuristic", "sci-fi"],
        "objects": ["neon signs", "skyscrapers", "wet street", "crosswalk", "street lights", "pedestrians"],
        "dominant_colors": ["Electric Cyan", "Neon Magenta", "Deep Midnight Blue", "Obsidian Black"],
        "sample_edit": ("cyberpunk_neon", "preset", "Amplify cyberpunk neon reflections and atmospheric glow")
    },
    {
        "filename": "alpine_mountain_sunset.jpg",
        "title": "Alpine Lake Golden Hour Reflection",
        "caption": "A majestic alpine mountain range bathed in radiant 2800K golden hour sunlight, with dramatic rugged peaks perfectly mirrored in a crystal-clear mountain lake.",
        "tags": ["mountain", "sunset", "golden hour", "lake", "reflection", "nature", "landscape", "alpine", "trees", "wilderness"],
        "objects": ["mountain peaks", "alpine lake", "pine forest", "golden sunlight", "cloud formations"],
        "dominant_colors": ["Golden Orange", "Deep Emerald", "Cobalt Blue", "Granite Gray"],
        "sample_edit": ("golden_hour", "preset", "Intensify golden hour warmth and radiant sunset highlights")
    },
    {
        "filename": "playful_dog_nature.jpg",
        "title": "Golden Retriever Adventure in Meadow",
        "caption": "A joyful golden retriever sitting alert in a sun-dappled wild grass meadow, with soft afternoon sunlight illuminating its golden fur and a blurred forest background.",
        "tags": ["dog", "golden retriever", "pet", "animal", "meadow", "grass", "happy", "sunlight", "outdoor", "canine"],
        "objects": ["golden retriever", "collar", "wild meadow grass", "forest trees", "sun flare"],
        "dominant_colors": ["Warm Gold", "Meadow Green", "Sunlight Yellow", "Earthy Brown"],
        "sample_edit": ("watercolor_art", "preset", "Convert to delicate fluid watercolor artwork")
    },
    {
        "filename": "minimalist_coffee_workspace.jpg",
        "title": "Architectural Creator Workspace",
        "caption": "A minimalist aesthetic desk setup featuring a MacBook, an artisanal ceramic coffee mug, wireless mouse, and a notebook on a clean oak wood surface with natural morning daylight.",
        "tags": ["workspace", "minimalist", "coffee", "laptop", "desk", "technology", "aesthetic", "clean", "office", "productivity"],
        "objects": ["laptop", "ceramic coffee mug", "notebook", "wireless mouse", "wooden desk"],
        "dominant_colors": ["Natural Oak", "Espresso Brown", "Clean White", "Matte Gray"],
        "sample_edit": ("vintage_film", "preset", "Apply vintage 1970s analog 35mm film grading")
    }
]


def seed_library(clear_existing: bool = True):
    storage = StorageManager()
    if clear_existing:
        print("Clearing previous sample images to avoid duplicates...")
        for existing in storage.get_all_images():
            storage.delete_image(existing["id"])

    print("Seeding sample portfolio images...")

    for item in SOURCE_IMAGES:
        dest_sample = SAMPLES_DIR / item["filename"]

        if dest_sample.exists():
            target_image_path = dest_sample
        else:
            print(f"Skipping missing sample for {item['filename']}")
            continue

        # Open image and add to storage manager
        with Image.open(target_image_path) as img:
            record = storage.add_original_image(
                pil_image=img,
                filename=item["filename"],
                title=item["title"],
                caption=item["caption"],
                tags=item["tags"],
                objects=item["objects"],
                dominant_colors=item["dominant_colors"]
            )
            print(f"Added original image: {record['title']} (ID: {record['id']})")

            # Apply sample edit to populate version history
            if "sample_edit" in item:
                preset_key, edit_type, prompt_desc = item["sample_edit"]
                edited_pil = apply_preset_filter(img, preset_key)
                updated_record = storage.add_version(
                    image_id=record["id"],
                    edited_image=edited_pil,
                    prompt=prompt_desc,
                    edit_type=edit_type,
                    model_used=f"Smart Vision Engine ({preset_key})",
                    notes=f"Sample visual transformation ({preset_key})"
                )
                print(f"  -> Added version v1: {prompt_desc}")

    print("Seeding complete! Metadata and versions generated.")


if __name__ == "__main__":
    seed_library()
