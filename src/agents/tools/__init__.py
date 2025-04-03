from typing import List
import json
import base64

import httpx
from supabase import create_client
from smolagents import tool
from openai import OpenAI

from src.lib.env import SUPABASE_URL, SUPABASE_KEY, JINA_API_KEY, OPENAI_API_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)

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
