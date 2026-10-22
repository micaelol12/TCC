"""Gemini REST adapter exposing the structured parse contract used by the pipeline."""
from types import SimpleNamespace
from urllib.parse import quote
import httpx


class GeminiClient:
    def __init__(self, api_key: str, timeout: int, transport=None):
        self.client = httpx.AsyncClient(base_url='https://generativelanguage.googleapis.com/v1beta/',
            headers={'x-goog-api-key': api_key}, timeout=timeout, transport=transport)
        self.responses = self

    async def parse(self, *, model, input, instructions, text_format):
        response = await self.client.post(f'models/{quote(model, safe="")}:generateContent', json={
            'systemInstruction': {'parts': [{'text': instructions}]},
            'contents': [{'role': 'user', 'parts': [{'text': input}]}],
            'generationConfig': {'responseMimeType': 'application/json', 'responseJsonSchema': text_format.model_json_schema()},
        })
        response.raise_for_status()
        data = response.json()
        candidates = data.get('candidates', [])
        if not candidates or candidates[0].get('finishReason') not in (None, 'STOP'):
            raise ValueError('Resposta Gemini ausente ou interrompida.')
        content = ''.join(part.get('text', '') for part in candidates[0].get('content', {}).get('parts', []) if not part.get('thought'))
        parsed = text_format.model_validate_json(content)
        return SimpleNamespace(output_parsed=parsed, model=data.get('modelVersion') or model)

    async def close(self):
        await self.client.aclose()
