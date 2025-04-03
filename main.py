import fire
import nextcord
from nextcord.ext import commands
import httpx
import cv2
import numpy as np
import os

from src.agents.tools import get_image_text, get_str_bounding_box
from src.cogs.generator import Generator
from src.lib.env import DISCORD_TOKEN


def init_bot():
    intents = nextcord.Intents.default()
    bot = commands.Bot(command_prefix="!", intents=intents)
    bot.add_cog(Generator(bot))
    bot.run(DISCORD_TOKEN)


def describe_img(image_url: str):
    # Download the image
    resp = httpx.get(image_url)
    resp.raise_for_status()

    # Convert to OpenCV format
    image = cv2.imdecode(np.frombuffer(
        resp.content, np.uint8), cv2.IMREAD_COLOR)

    # Get text and bounding boxes
    texts = get_image_text(image_url)
    boxes: list[tuple] = [get_str_bounding_box(
        image_url, text) for text in texts]

    # post process the boxes. If there are overlapping boxes,
    # make them non-overlapping with a 5 pixel gap
    new_boxes = []
    for box in boxes:
        
        

    # draw the boxes on the image
    for i, box in enumerate(new_boxes):
        cv2.rectangle(
            image, (box[0], box[1]), (box[0] + box[2], box[1] + box[3]), (0, 255, 0), 2)
        cv2.putText(image, texts[i], (box[0], box[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)

    # Save the output image
    output_path = os.path.join('output', 'detected_text.jpg')
    cv2.imwrite(output_path, image)
    print(f"Output image saved to: {output_path}")


if __name__ == "__main__":
    fire.Fire({
        "bot": init_bot,
        "get_image_text": describe_img,
    })
