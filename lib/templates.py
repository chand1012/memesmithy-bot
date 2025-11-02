import csv
import random
from pathlib import Path
from typing import Optional

from PIL import Image
from pydantic import BaseModel, Field


class Template(BaseModel):
    """Pydantic model representing a meme template."""

    id: str = Field(..., description="Unique identifier for the template")
    name: str = Field(..., description="Name of the template")
    description: str = Field(default="", description="Description of the template")
    image_url: str = Field(default="", description="URL to the template image")
    width: Optional[int] = Field(
        default=None, description="Width of the template image"
    )
    height: Optional[int] = Field(
        default=None, description="Height of the template image"
    )
    prompt: str = Field(
        default="", description="Prompt/instructions for using the template"
    )
    boxes: str = Field(
        default="", description="JSON string representing text box positions"
    )
    public: bool = Field(default=True, description="Whether the template is public")
    created_by: Optional[str] = Field(
        default=None, description="Creator of the template"
    )
    created_at: Optional[str] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[str] = Field(default=None, description="Last update timestamp")
    deleted_at: Optional[str] = Field(default=None, description="Deletion timestamp")

    class Config:
        """Pydantic config."""

        frozen = True  # Make the model immutable


def get_template_by_id(
    template_id: str, csv_path: Path = Path("templates.csv")
) -> Optional[Template]:
    """
    Get a template by its ID from the templates CSV file.

    Args:
        template_id: The ID of the template to retrieve
        csv_path: Path to the templates CSV file (default: templates.csv)

    Returns:
        Template object if found, None otherwise
    """
    if not csv_path.exists():
        return None

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("id", "").strip() == template_id.strip():
                return _parse_template_row(row)

    return None


def get_image_by_template_id(
    template_id: str, images_dir: Path = Path("images")
) -> Optional[Image.Image]:
    """
    Get an image by its template ID from the images folder.
    """
    if not images_dir.exists():
        return None

    return Image.open(images_dir / f"{template_id}.jpg")


def get_all_templates(csv_path: Path = Path("templates.csv")) -> list[Template]:
    """
    Get all templates from the templates CSV file.

    Args:
        csv_path: Path to the templates CSV file (default: templates.csv)

    Returns:
        List of Template objects
    """
    if not csv_path.exists():
        return []

    templates = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Only include templates with valid ID and name
            if row.get("id") and row.get("name"):
                template = _parse_template_row(row)
                if template:
                    templates.append(template)

    return templates


def get_random_template(csv_path: Path = Path("templates.csv")) -> Optional[Template]:
    """
    Get a random template from the templates CSV file.

    Args:
        csv_path: Path to the templates CSV file (default: templates.csv)

    Returns:
        Random Template object if templates exist, None otherwise
    """
    templates = get_all_templates(csv_path)
    if not templates:
        return None

    return random.choice(templates)


def search_templates(
    keyword: str, max_results: int = 10, csv_path: Path = Path("templates.csv")
) -> list[Template]:
    """
    Search for templates by keyword in name and description fields.

    Args:
        keyword: Search keyword (case-insensitive)
        max_results: Maximum number of results to return (default: 10)
        csv_path: Path to the templates CSV file (default: templates.csv)

    Returns:
        List of Template objects matching the keyword, sorted by relevance (max_results items)
    """
    if not keyword:
        return []

    templates = get_all_templates(csv_path)
    if not templates:
        return []

    keyword_lower = keyword.lower()

    # Score each template based on match quality
    scored_templates = []
    for template in templates:
        score = 0
        name_lower = template.name.lower()
        desc_lower = (template.description or "").lower()

        # Exact name match gets highest score
        if keyword_lower == name_lower:
            score += 100
        # Name contains keyword
        elif keyword_lower in name_lower:
            score += 50
        # Description contains keyword
        if keyword_lower in desc_lower:
            score += 10
        # Check if keyword words appear in name
        keyword_words = keyword_lower.split()
        for word in keyword_words:
            if word in name_lower:
                score += 20
            elif word in desc_lower:
                score += 5

        if score > 0:
            scored_templates.append((score, template))

    # Sort by score (descending) and return top results
    scored_templates.sort(key=lambda x: x[0], reverse=True)
    return [template for _, template in scored_templates[:max_results]]


def _parse_template_row(row: dict) -> Optional[Template]:
    """
    Parse a CSV row into a Template Pydantic model.

    Args:
        row: Dictionary representing a CSV row

    Returns:
        Template object if valid, None otherwise
    """
    try:
        # Parse width and height as integers
        width = None
        height = None
        if row.get("width"):
            try:
                width = int(row["width"])
            except (ValueError, TypeError):
                pass
        if row.get("height"):
            try:
                height = int(row["height"])
            except (ValueError, TypeError):
                pass

        # Parse public as boolean
        public = True
        public_str = row.get("public", "").strip().lower()
        if public_str in ("false", "0", "no", ""):
            public = False

        return Template(
            id=row.get("id", "").strip(),
            name=row.get("name", "").strip(),
            description=row.get("description", "").strip(),
            image_url=row.get("image_url", "").strip(),
            width=width,
            height=height,
            prompt=row.get("prompt", "").strip(),
            boxes=row.get("boxes", "").strip(),
            public=public,
            created_by=row.get("created_by", "").strip() or None,
            created_at=row.get("created_at", "").strip() or None,
            updated_at=row.get("updated_at", "").strip() or None,
            deleted_at=row.get("deleted_at", "").strip() or None,
        )
    except Exception:
        return None
