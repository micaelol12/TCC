"""Provider clients are created only for the selected mode."""
from .rubrics import AXIS_SPECS, criar_questoes_eixo, criar_rubrica_polaridade_ordinal
from ..analysis_defaults import CONTEXTO_POSICAO_POLITICA


def jev_client(api_key: str, model: str):
    """Instancia o cliente assíncrono TypeSafe com o modelo escolhido para a análise."""
    from typesafe_sdk import AsyncTypeSafeClient
    return AsyncTypeSafeClient(api_key=api_key, model=model)


def jev_questions(escala=None, primitiva_polaridade="score", contexto_posicao_politica=CONTEXTO_POSICAO_POLITICA, axis_specs=AXIS_SPECS):
    """Monta as perguntas de relevância e polaridade para os quatro eixos."""
    from typesafe_sdk import Choice

    if primitiva_polaridade not in {"score", "choice"}:
        raise ValueError("primitiva_polaridade deve ser score ou choice.")

    questions = {}

    for axis in AXIS_SPECS:
        # Relevância e polaridade são perguntas separadas, enviadas juntas.
        questions[f"{axis}_relevancia"] = Choice(**criar_questoes_eixo(axis, axis_specs=axis_specs, contexto_posicao_politica=contexto_posicao_politica))

        rubric = criar_rubrica_polaridade_ordinal(axis, axis_specs=axis_specs, escala=escala, contexto_posicao_politica=contexto_posicao_politica)

        # Score usa índices de uma lista; Choice usa as chaves dos níveis.
        questions[f"{axis}_polaridade"] = polarity_question(rubric, primitiva_polaridade)

    return questions


def polarity_question(rubric, primitive):
    """Representa a rubrica ordinal usando a primitiva Score ou Choice configurada."""
    from typesafe_sdk import Choice, Score

    if primitive == "score":
        return Score(instructions=rubric["instructions"], criteria=list(rubric["niveis"].values()))
    return Choice(instructions=rubric["instructions"], criteria=dict(rubric["niveis"]))


def llm_client(api_key: str, timeout: int):
    """Configura o cliente Maritaca; as novas tentativas ficam a cargo do pipeline."""
    from openai import AsyncOpenAI

    # O SDK OpenAI acessa o endpoint compatível da Maritaca. As tentativas
    # adicionais são controladas em ask_llm(), sem retries internos do SDK.
    return AsyncOpenAI(api_key=api_key, base_url="https://chat.maritaca.ai/api", timeout=timeout, max_retries=0)


def gemini_client(api_key: str, timeout: int):
    """Cria o adaptador Gemini com a chave e o prazo desta análise."""
    from .gemini import GeminiClient
    return GeminiClient(api_key, timeout)
