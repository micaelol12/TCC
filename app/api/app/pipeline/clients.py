"""Provider clients are created only for the selected mode."""
from .domain import criar_questoes_eixo, criar_rubrica_polaridade_ordinal
from .rubrics import AXIS_SPECS
from ..polarity import CONTEXTO_POSICAO_POLITICA


def jev_client(api_key: str, model: str):
    from typesafe_sdk import AsyncTypeSafeClient
    return AsyncTypeSafeClient(api_key=api_key, model=model)


def jev_questions(escala=None, primitiva_polaridade="score", contexto_posicao_politica=CONTEXTO_POSICAO_POLITICA):
    from typesafe_sdk import Choice, Score
    if primitiva_polaridade not in {"score", "choice"}:
        raise ValueError("primitiva_polaridade deve ser score ou choice.")
    questions = {}
    for axis in AXIS_SPECS:
        questions[f"{axis}_relevancia"] = Choice(**criar_questoes_eixo(axis, contexto_posicao_politica=contexto_posicao_politica))
        rubric = criar_rubrica_polaridade_ordinal(axis, escala=escala, contexto_posicao_politica=contexto_posicao_politica)
        questions[f"{axis}_polaridade"] = (
            Score(instructions=rubric["instructions"], criteria=list(rubric["niveis"].values()))
            if primitiva_polaridade == "score" else
            Choice(instructions=rubric["instructions"], criteria=dict(rubric["niveis"]))
        )
    return questions


def llm_client(api_key: str, timeout: int):
    from openai import AsyncOpenAI
    return AsyncOpenAI(api_key=api_key, base_url="https://chat.maritaca.ai/api", timeout=timeout, max_retries=0)


def gemini_client(api_key: str, timeout: int):
    from .gemini import GeminiClient
    return GeminiClient(api_key, timeout)
