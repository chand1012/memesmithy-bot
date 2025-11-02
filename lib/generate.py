import os
from typing import Optional

from groq import Groq
from pydantic import BaseModel
from dotenv import load_dotenv

from lib.templates import get_template_by_id

load_dotenv()

system_prompt = " ".join(
    [
        "You are a masterful meme maker.",
        "You are given a prompt and a template.",
        "You need to generate captions for the template.",
        "The captions should be in the same language as the prompt.",
        "Should be short, not wordy or verbose. Less than 5 words is ideal.",
    ]
)

model = "openai/gpt-oss-20b"

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY is not set")

groq = Groq(api_key=groq_api_key)


class GeneratedCaptions(BaseModel):
    text1: str
    text2: Optional[str] = None
    text3: Optional[str] = None
    text4: Optional[str] = None
    text5: Optional[str] = None
    text6: Optional[str] = None
    text7: Optional[str] = None
    text8: Optional[str] = None
    text9: Optional[str] = None
    text10: Optional[str] = None


def generate_captions(template_id: str, prompt: str) -> dict[str, str | None]:
    template = get_template_by_id(template_id)
    if not template:
        raise ValueError(f"Template with ID {template_id} not found")

    response = groq.chat.completions.create(
        model=model,
        temperature=0.5,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": template.prompt + prompt},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "generated_captions",
                "schema": GeneratedCaptions.model_json_schema(),
            },
        },
    )

    generated_captions = GeneratedCaptions.model_validate_json(
        response.choices[0].message.content
    )
    return generated_captions.model_dump()
