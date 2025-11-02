import csv
import os
from pathlib import Path

import httpx
from fire import Fire

def download_images():
    """Download all template images from templates.csv into the images folder."""
    # Create images directory if it doesn't exist
    images_dir = Path("images")
    images_dir.mkdir(exist_ok=True)

    # Read the CSV file
    csv_path = Path("templates.csv")
    if not csv_path.exists():
        print(f"Error: {csv_path} not found")
        return

    downloaded = 0
    skipped = 0
    failed = 0

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            image_url = row.get("image_url", "").strip()
            template_id = row.get("id", "").strip()

            if not image_url:
                skipped += 1
                continue

            # Determine filename - use ID if available, otherwise derive from URL
            if template_id:
                # Get file extension from URL
                ext = os.path.splitext(image_url)[1] or ".jpg"
                filename = f"{template_id}{ext}"
            else:
                # Fallback: use last part of URL
                filename = os.path.basename(image_url) or "image.jpg"

            filepath = images_dir / filename

            # Skip if already downloaded
            if filepath.exists():
                skipped += 1
                continue

            # Download the image
            try:
                response = httpx.get(image_url, timeout=30)
                response.raise_for_status()

                with open(filepath, "wb") as img_file:
                    img_file.write(response.content)

                downloaded += 1
                print(f"Downloaded: {filename}")
            except Exception as e:
                failed += 1
                print(f"Failed to download {image_url}: {e}")

    print(
        f"\nDownload complete: {downloaded} downloaded, {skipped} skipped, {failed} failed"
    )


if __name__ == "__main__":
    Fire()
