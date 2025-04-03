from typing import List
import json
import base64

import httpx
from supabase import create_client
from smolagents import tool
from openai import OpenAI
import easyocr
import cv2
import numpy as np

from src.lib.env import SUPABASE_URL, SUPABASE_KEY, JINA_API_KEY, OPENAI_API_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)
reader = easyocr.Reader(['en'])

# supabase UUIDs of good examples
GOOD_TEMPLATE_EXAMPLES = [
    "dfb0ece2-b853-4352-aa26-41bd746f5341",
    "ceaa1ad8-a6b5-40cd-b1b0-a1171ccac227",
    "52e485a3-3d99-4df9-9adf-5fcfe7626226",
    "07dcb5d2-c43c-41da-8737-1684dc889c66",
    "4aac3c03-c8ab-49a3-9118-05334a1c9f09"
]


@tool
def get_template_examples() -> List[dict]:
    """Get a list of good template examples"""
    templates = supabase.table("templates").select(
        "*").in_("id", GOOD_TEMPLATE_EXAMPLES).execute()
    return templates.data


@tool
def get_page_content(url: str) -> str:
    """
    Get the contents of a webpage as Markdown.

    Args:
        url: The URL of the webpage to get the contents of.

    Returns:
        The contents of the webpage as Markdown.
    """
    headers = {
        "X-With-Images-Summary": "true",
    }

    if JINA_API_KEY:
        headers["Authorization"] = f"Bearer {JINA_API_KEY}"

    req_url = f'https://r.jina.ai/{url}'
    response = httpx.get(req_url, headers=headers)
    response.raise_for_status()
    return response.text


@tool
def get_image_text(image_url: str) -> List[str]:
    '''
    Given the URL of an image, responds with a detailed description of the texts found on that image.

    Args:
        image_url: The URL of the image to describe.

    Returns:
        A list of texts found on the image.
    '''

    resp = httpx.get(image_url)
    resp.raise_for_status()

    base64_image = base64.b64encode(resp.content).decode('utf-8')

    chat_response = client.responses.create(
        model="gpt-4o",
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Given a meme, identify the number of text boxes that were added by the user after the fact to make the meme. Do not include text boxes that were subtitles, or probably originally included with the image. All text that users add should be in Impact or Arial, so only identify text in those fonts. Output these texts in the order they appear, left to right, top to bottom. Output as JSON in the following format: `{\"texts\": [\"text 1\", ...]}`. If there are no text boxes, return an empty list. Also don't include any text that may be a watermark or logo."
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{base64_image}"
                    }
                ]
            },
        ],
        text={
            "format": {
                "type": "json_object"
            }
        },
        reasoning={},
        tools=[],
        temperature=0.5,
        max_output_tokens=2048,
        top_p=1,
        store=False
    )

    try:
        texts: List[str] = json.loads(
            chat_response.output[0].content[0].text)['texts']
        # if any of the texts contain "imgflip" or "memesmithy", remove them
        texts = [text for text in texts if "imgflip" not in text.lower(
        ) and "memesmithy" not in text.lower()]
        return texts
    except Exception as e:
        raise Exception(f"Error parsing image description: {e}")


@tool
def get_str_bounding_box(image_url: str, input_text: str) -> tuple[int, int, int, int]:
    """
    Given the URL of an image and a string, returns the bounding box of the string in the image.
    Handles cases where the text might be split across multiple lines or split on spaces,
    and also handles repeated words by considering spatial relationships.

    Args:
        image_url: The URL of the image to get the bounding box of.
        input_text: The string to get the bounding box of.

    Returns:
        A tuple of the bounding box of the string in the image. (x, y, w, h)
    """

    resp = httpx.get(image_url)
    resp.raise_for_status()

    image = cv2.imdecode(np.frombuffer(
        resp.content, np.uint8), cv2.IMREAD_COLOR)

    results = reader.readtext(image)

    # Clean the input text for comparison
    input_text_clean = input_text.strip().lower()
    input_words = input_text_clean.split()

    # First try exact match
    for (bbox, text, prob) in results:
        text_clean = text.strip().lower()
        if text_clean == input_text_clean:
            # Exact match found
            (x, y, w, h) = (bbox[0][0], bbox[0][1], bbox[2]
                            [0] - bbox[0][0], bbox[2][1] - bbox[0][1])
            return (int(x), int(y), int(w), int(h))

    # If no exact match, we need to find the best combination of text segments
    # that match our input text

    # First, collect all text segments with their bounding boxes
    text_segments = []
    for (bbox, text, prob) in results:
        text_clean = text.strip().lower()
        # Calculate center point of the bounding box
        center_x = (bbox[0][0] + bbox[2][0]) / 2
        center_y = (bbox[0][1] + bbox[2][1]) / 2
        text_segments.append({
            'text': text_clean,
            'bbox': bbox,
            'center_x': center_x,
            'center_y': center_y
        })

    # Sort text segments by y-coordinate (top to bottom)
    text_segments.sort(key=lambda x: x['center_y'])

    # Function to calculate distance between two text segments
    def segment_distance(seg1, seg2):
        return ((seg1['center_x'] - seg2['center_x'])**2 +
                (seg1['center_y'] - seg2['center_y'])**2)**0.5

    # Function to check if a sequence of text segments matches our input text
    def segments_match_input(segments):
        combined_text = ' '.join(seg['text'] for seg in segments)
        # Check if all words from input are in the combined text
        for word in input_words:
            if word not in combined_text:
                return False
        return True

    # Function to get bounding box for a sequence of segments
    def get_combined_bbox(segments):
        if not segments:
            return None

        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')

        for seg in segments:
            bbox = seg['bbox']
            min_x = min(min_x, bbox[0][0])
            min_y = min(min_y, bbox[0][1])
            max_x = max(max_x, bbox[2][0])
            max_y = max(max_y, bbox[2][1])

        width = max_x - min_x
        height = max_y - min_y

        return (int(min_x), int(min_y), int(width), int(height))

    # Try to find the best sequence of text segments that match our input
    best_match = None
    best_score = float('inf')

    # Try different window sizes (number of consecutive segments)
    for window_size in range(1, min(len(text_segments) + 1, 10)):
        # Slide the window through all possible positions
        for i in range(len(text_segments) - window_size + 1):
            window = text_segments[i:i+window_size]

            # Check if this window matches our input text
            if segments_match_input(window):
                # Calculate a score based on how well the segments match the input
                # Lower score is better
                combined_text = ' '.join(seg['text'] for seg in window)

                # Count how many words from input are in the combined text
                word_count = sum(
                    1 for word in input_words if word in combined_text)

                # Calculate average distance between consecutive segments
                total_distance = 0
                for j in range(len(window) - 1):
                    total_distance += segment_distance(window[j], window[j+1])
                avg_distance = total_distance / \
                    (len(window) - 1) if len(window) > 1 else 0

                # Score is based on word count and average distance
                # We want to maximize word count and minimize distance
                score = -word_count + avg_distance / 100

                if score < best_score:
                    best_score = score
                    best_match = window

    # If we found a match, return its bounding box
    if best_match:
        return get_combined_bbox(best_match)

    # If we still haven't found a match, try a more aggressive approach
    # Look for any text segments that contain any of the words from the input text
    matching_boxes = []
    for (bbox, text, prob) in results:
        text_clean = text.strip().lower()
        # Check if this text segment is part of our input text
        if any(word in text_clean for word in input_words) or any(text_clean in word for word in input_words):
            matching_boxes.append(bbox)

    if matching_boxes:
        # Find the min x, min y, max x, max y across all boxes
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')

        for bbox in matching_boxes:
            min_x = min(min_x, bbox[0][0])
            min_y = min(min_y, bbox[0][1])
            max_x = max(max_x, bbox[2][0])
            max_y = max(max_y, bbox[2][1])

        # Calculate width and height
        width = max_x - min_x
        height = max_y - min_y

        return (int(min_x), int(min_y), int(width), int(height))

    raise Exception(f"Text not found in image: {input_text}")
