import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from PIL import Image, ImageDraw, ImageFont

from lib.templates import get_template_by_id


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    """
    Wrap text to fit within a maximum width using the given font.

    Args:
        text: Text to wrap
        font: PIL ImageFont to use for measuring text
        max_width: Maximum width in pixels

    Returns:
        List of text lines that fit within max_width
    """
    words = text.split()
    lines = []
    line = ""

    for word in words:
        test_line = line + " " + word if line else word
        bbox = font.getbbox(test_line)
        line_width = bbox[2] - bbox[0]

        if line_width <= max_width:
            line = test_line
        else:
            if line:
                lines.append(line)
            line = word

    if line:
        lines.append(line)

    return lines


def get_line_height(font: ImageFont.FreeTypeFont) -> int:
    """
    Get the line height for a given font.

    Args:
        font: PIL ImageFont

    Returns:
        Line height in pixels
    """
    ascent, descent = font.getmetrics()
    return ascent + descent


def get_max_font_size_and_wrapped_text(
    text: str, font_path: str, max_width: int, max_height: int
) -> tuple[int, List[str]]:
    """
    Find the maximum font size that fits text within box dimensions and return wrapped text.

    Args:
        text: Text to fit
        font_path: Path to font file
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels

    Returns:
        Tuple of (best_font_size, wrapped_text_lines)
    """
    min_size = 1
    max_size = 1000  # Arbitrary upper limit
    best_size = min_size
    best_lines = []

    # Binary search for the largest size that fits within the box
    while min_size <= max_size:
        fontsize = (min_size + max_size) // 2
        font = ImageFont.truetype(font_path, fontsize)

        # Ensure no single word exceeds max_width
        words = text.split()
        max_word_width = max(
            font.getbbox(word)[2] - font.getbbox(word)[0] for word in words
        )
        if max_word_width > max_width:
            max_size = fontsize - 1
            continue

        lines = wrap_text(text, font, max_width)
        line_height = get_line_height(font)
        total_height = line_height * len(lines)

        if total_height <= max_height:
            best_size = fontsize
            best_lines = lines
            min_size = fontsize + 1
        else:
            max_size = fontsize - 1

    return best_size, best_lines


def _find_image_file(template_id: str, images_dir: Path) -> Optional[Path]:
    """
    Find image file by template ID, trying multiple extensions.

    Args:
        template_id: Template ID
        images_dir: Directory containing images

    Returns:
        Path to image file if found, None otherwise
    """
    if not images_dir.exists():
        return None

    # Try common image extensions
    image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
    for ext in image_extensions:
        potential_path = images_dir / f"{template_id}{ext}"
        if potential_path.exists():
            return potential_path

    return None


def generate_meme_image(
    template_id: str,
    texts: Union[List[str], Dict[str, str]],
    watermark: Optional[str] = None,
    images_dir: Path = Path("images"),
    fonts_dir: Path = Path("fonts"),
    csv_path: Path = Path("templates.csv"),
) -> Image.Image:
    """
    Generate a meme image by adding text to a template's boxes.

    Args:
        template_id: ID of the template to use
        texts: Text to fill in boxes - can be a list (ordered by box index) or
               a dict (with keys matching box order or named keys like "text1", "text2")
        watermark: Optional watermark text to add at bottom-left
        images_dir: Directory containing template images (default: images)
        fonts_dir: Directory containing font files (default: fonts)
        csv_path: Path to templates CSV file (default: templates.csv)

    Returns:
        PIL Image with text captions added

    Raises:
        ValueError: If template not found, image not found, font not found, or invalid input
        FileNotFoundError: If required directories or files don't exist
    """
    # Load template
    template = get_template_by_id(template_id, csv_path)
    if not template:
        raise ValueError(f"Template with ID '{template_id}' not found")

    # Parse boxes JSON
    try:
        boxes_data = json.loads(template.boxes) if template.boxes else []
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid boxes JSON in template: {e}")

    if not boxes_data:
        raise ValueError(f"Template '{template_id}' has no boxes defined")

    # Load image - try multiple extensions
    image_path = _find_image_file(template_id, images_dir)
    if not image_path:
        raise FileNotFoundError(
            f"Image file for template '{template_id}' not found in {images_dir}"
        )

    image = Image.open(image_path)
    if image.format not in ("PNG", "JPEG", "JPG"):
        raise ValueError(f"Unsupported image format: {image.format}")

    # Convert to RGBA for transparency support
    input_format = image.format
    image = image.convert("RGBA")
    image.format = input_format

    # Normalize texts input to a list
    if isinstance(texts, dict):
        # If dict has numeric string keys, convert to list
        text_list = []
        keys = sorted(
            texts.keys(), key=lambda k: (int(k) if k.isdigit() else float("inf"), k)
        )
        for key in keys:
            if isinstance(key, str) and key.isdigit():
                idx = int(key)
                # Pad list if needed
                while len(text_list) <= idx:
                    text_list.append("")
                text_list[idx] = texts[key]
            else:
                # Named keys - try to match order or append
                text_list.append(texts[key])
        texts = text_list
    elif isinstance(texts, list):
        texts = texts.copy()

    # Process each box
    for i, box_data in enumerate[list[dict[str, Any]]](boxes_data):
        if i >= len(texts):
            continue  # Skip boxes without corresponding text

        text = texts[i]
        if not text:
            continue  # Skip empty text

        # Extract box properties with defaults
        x = box_data.get("x", 0)
        y = box_data.get("y", 0)
        w = box_data.get("w", 0)
        h = box_data.get("h", 0)
        font_name = box_data.get("font", "arial").lower()
        fontsize = box_data.get("fontsize")
        color = box_data.get("color")
        border = box_data.get("border")

        # Validate font
        if font_name not in ["arial", "impact"]:
            raise ValueError(
                f"Unsupported font '{font_name}'. Use 'arial' or 'impact'."
            )

        # Load font file
        font_path = fonts_dir / f"{font_name}.ttf"
        if not font_path.exists():
            raise FileNotFoundError(f"Font file not found: {font_path}")

        # Handle font sizing
        if fontsize is None:
            # Auto-size to fit box
            fontsize, lines = get_max_font_size_and_wrapped_text(
                text, str(font_path), w, h
            )
            font = ImageFont.truetype(str(font_path), fontsize)
        else:
            # Use specified font size
            font = ImageFont.truetype(str(font_path), fontsize)
            lines = wrap_text(text, font, w)

            # Validate text fits
            line_height = get_line_height(font)
            total_height = line_height * len(lines)
            if total_height > h:
                raise ValueError(
                    f"Text exceeds box height at fontsize {fontsize} for box {i}"
                )

        # Set default colors based on font
        fill_color = color if color else ("black" if font_name == "arial" else "white")
        stroke_color = (
            border if border else ("black" if font_name == "impact" else None)
        )

        # Determine stroke width
        stroke_width = (
            max(1, fontsize // 15) if stroke_color and stroke_color != fill_color else 0
        )

        # Calculate total text height
        line_height = get_line_height(font)
        total_text_height = line_height * len(lines)

        # Calculate starting y to center text vertically
        current_y = y + (h - total_text_height) // 2

        # Draw each line
        draw = ImageDraw.Draw(image)
        for line in lines:
            # Calculate the width of the line
            line_width = font.getbbox(line)[2] - font.getbbox(line)[0]

            # Calculate x to center the line within the box
            line_x = x + (w - line_width) // 2

            draw.text(
                (line_x, current_y),
                line,
                font=font,
                fill=fill_color,
                stroke_width=stroke_width,
                stroke_fill=stroke_color,
            )

            current_y += line_height

    # Add watermark if provided
    if watermark:
        # Create a transparent overlay
        overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)

        watermark_text = watermark
        desired_text_height = image.height * 0.03  # 3% of the image height
        font_name = "arial"
        font_path = fonts_dir / f"{font_name}.ttf"

        if not font_path.exists():
            raise FileNotFoundError(f"Font file not found: {font_path}")

        # Find the font size that makes the text height approximately desired_text_height
        font_size = 1
        font = None
        while True:
            font = ImageFont.truetype(str(font_path), font_size)
            bbox = font.getbbox(watermark_text)
            text_height = bbox[3] - bbox[1]
            if text_height >= desired_text_height:
                break
            font_size += 1

        position = (
            round(image.width * 0.02),
            image.height - text_height - round(image.height * 0.02),
        )  # Bottom-left corner with padding

        # Set fill and stroke colors with 50% opacity
        fill_color = (255, 255, 255, 128)  # White with 50% opacity
        stroke_color = (0, 0, 0, 128)  # Black with 50% opacity

        # Draw the watermark on the overlay
        draw.text(
            position,
            watermark_text,
            font=font,
            fill=fill_color,
            stroke_width=3,
            stroke_fill=stroke_color,
        )

        # Composite the overlay onto the original image
        image = Image.alpha_composite(image.convert("RGBA"), overlay)

    return image
