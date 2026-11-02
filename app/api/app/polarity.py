"""Contrato autoritativo de escala ordinal."""
import hashlib
import json
import math
from types import MappingProxyType
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, field_serializer, field_validator, model_validator

EIXOS_ESCALA = ("economic", "diplomatic", "state", "society")


class PoloEixo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: StrictStr = Field(min_length=1)
    label: StrictStr = Field(min_length=1)
    description: StrictStr = Field(min_length=1)

    @field_validator('*')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Definição de polo vazia.')
        return value


class DefinicaoEixo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    effect: StrictStr = Field(min_length=1)
    name: StrictStr = Field(min_length=1)
    topic: StrictStr = Field(min_length=1)
    poles: dict[Literal['A', 'B'], PoloEixo]
    note: StrictStr = Field(min_length=1)

    @field_validator('effect', 'name', 'topic', 'note')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Definição de eixo vazia.')
        return value

    @model_validator(mode='after')
    def poles_complete(self):
        if set(self.poles) != {'A', 'B'}:
            raise ValueError('Cada eixo exige os polos A e B.')
        object.__setattr__(self, 'poles', MappingProxyType(dict(self.poles)))
        return self

    @field_serializer('poles')
    def serialize_poles(self, value):
        return {key: pole.model_dump(mode='json') for key, pole in value.items()}


class NivelEscala(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    chave: StrictStr = Field(min_length=1)
    codigo: StrictInt
    rotulo: StrictStr = Field(min_length=1)
    polo: Literal["A", "B"] | None
    valor: float = Field(strict=True, ge=0, le=1, allow_inf_nan=False)

    @model_validator(mode="after")
    def textos(self):
        if not self.chave.strip() or not self.rotulo.strip():
            raise ValueError("Chave e rótulo devem estar preenchidos.")
        return self


class AncoraEscala(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    situacao: StrictStr = Field(min_length=1)
    exemplos: tuple[StrictStr, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def textos(self):
        if not self.situacao.strip() or any(not x.strip() for x in self.exemplos):
            raise ValueError("Âncoras exigem situação e exemplos preenchidos.")
        return self


class EscalaOrdinal(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: StrictStr = Field(min_length=1)
    versao: StrictInt = Field(ge=1)
    niveis: tuple[NivelEscala, ...]
    rubricas_por_eixo: dict[str, dict[str, AncoraEscala]]

    @model_validator(mode="after")
    def contrato(self):
        n = len(self.niveis)
        if not self.id.strip() or n < 3 or n % 2 != 1:
            raise ValueError("Escala bipolar exige quantidade ímpar de ao menos três níveis.")
        if len({x.chave for x in self.niveis}) != n or len({x.codigo for x in self.niveis}) != n:
            raise ValueError("Chaves e códigos devem ser únicos.")
        valores = [x.valor for x in self.niveis]
        if valores[0] != 0 or valores[-1] != 1 or valores[n // 2] != .5 or any(a >= b for a, b in zip(valores, valores[1:])):
            raise ValueError("Valores devem crescer de 0 a 1, com centro 0,5.")
        if [x.polo for x in self.niveis] != ["B"] * (n // 2) + [None] + ["A"] * (n // 2):
            raise ValueError("Esperados polos B, um centro, e polos A, nesta ordem.")
        if set(self.rubricas_por_eixo) != set(EIXOS_ESCALA):
            raise ValueError("Rubricas devem cobrir exatamente os quatro eixos.")
        for rubrica in self.rubricas_por_eixo.values():
            if set(rubrica) != {x.chave for x in self.niveis}:
                raise ValueError("Rubricas devem corresponder exatamente às chaves dos níveis.")
        object.__setattr__(self, "rubricas_por_eixo", MappingProxyType({
            eixo: MappingProxyType(dict(rubrica)) for eixo, rubrica in self.rubricas_por_eixo.items()}))
        return self

    @field_serializer("niveis")
    def serializar_niveis(self, value):
        return [n.model_dump(mode="json") for n in value]

    @field_serializer("rubricas_por_eixo")
    def serializar_rubricas(self, value):
        return {e: {k: a.model_dump(mode="json") for k, a in r.items()} for e, r in value.items()}

    @property
    def hash(self):
        canonical = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @property
    def por_codigo(self):
        return {x.codigo: x for x in self.niveis}

    @property
    def por_chave(self):
        return {x.chave: x for x in self.niveis}

    @property
    def centro(self):
        return next(x for x in self.niveis if x.polo is None)


def validar_escala(escala):
    """Reconstrói uma cópia imutável; nunca mantém referências ao dicionário de entrada."""
    return EscalaOrdinal.model_validate(escala.model_dump(mode="json") if isinstance(escala, BaseModel) else escala)


def valor_nivel(nivel, escala):
    if type(nivel) is not int or nivel not in escala.por_codigo:
        raise ValueError("Código não pertence à escala desta execução.")
    return 100.0 * escala.por_codigo[nivel].valor


def classe_nivel(nivel, escala):
    return "C" if nivel is None else escala.por_codigo[nivel].polo or "C"


PolarityLevel = Literal[-4, -3, -2, -1, 0, 1, 2, 3, 4]
COUNT_KEYS = {-4: "minus4", -3: "minus3", -2: "minus2", -1: "minus1", 0: "zero",
              1: "plus1", 2: "plus2", 3: "plus3", 4: "plus4"}
def level_score(level, escala):
    return valor_nivel(level, validar_escala(escala))
