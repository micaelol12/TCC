"""Adaptador REST Gemini para o contrato de saída estruturada do pipeline."""
from types import SimpleNamespace
from urllib.parse import quote

import httpx


def generation_payload(prompt, instructions, response_schema):
    """Monta a requisição Gemini com instruções e esquema de resposta JSON."""
    return {
        "systemInstruction": {"parts": [{"text": instructions}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseJsonSchema": response_schema.model_json_schema(),
        },
    }


def response_content(response_data):
    """Extrai o texto útil da primeira candidata e rejeita respostas interrompidas."""
    candidates = response_data.get("candidates", [])

    if not candidates or candidates[0].get("finishReason") not in (None, "STOP"):
        raise ValueError("Resposta Gemini ausente ou interrompida.")

    content_parts = candidates[0].get("content", {}).get("parts", [])

    return "".join(part.get("text", "") for part in content_parts if not part.get("thought"))


class GeminiClient:
    def __init__(self, api_key: str, timeout: int, transport=None):
        """Configura o cliente HTTP e expõe a interface de saída estruturada usada pelo pipeline."""
        self.client = httpx.AsyncClient(
            base_url="https://generativelanguage.googleapis.com/v1beta/",
            headers={"x-goog-api-key": api_key}, timeout=timeout, transport=transport,
        )
        self.responses = self

    async def parse(self, *, model, input, instructions, text_format):
        """Envia a geração ao Gemini e valida o JSON retornado com o modelo Pydantic solicitado."""
        response = await self.client.post(
            f'models/{quote(model, safe="")}:generateContent',
            json=generation_payload(input, instructions, text_format),
        )
        response.raise_for_status()
        response_data = response.json()
        parsed_answer = text_format.model_validate_json(response_content(response_data))

        return SimpleNamespace(output_parsed=parsed_answer, model=response_data.get("modelVersion") or model)

    async def close(self):
        """Libera as conexões HTTP do adaptador após o processamento."""
        await self.client.aclose()
