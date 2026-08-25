import os

from google import genai


def generate_gemini_text(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY must be configured.")
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"), contents=prompt)
    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")
    return response.text


def generate_gemini_contents(contents: list[dict[str, object]], system_instruction: str) -> str:
    """Gemini user/model 이력이 포함된 멀티턴 답변을 생성합니다."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY must be configured.")
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
        contents=contents,
        config={"temperature": 0.3, "max_output_tokens": 600, "system_instruction": system_instruction},
    )
    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")
    return response.text
