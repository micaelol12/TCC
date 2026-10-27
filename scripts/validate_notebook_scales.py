"""Demonstrações locais: nenhuma credencial ou inferência remota."""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tcc_lib.notebook_pipeline import carregar_pipeline_notebook


async def validar():
    ns = carregar_pipeline_notebook()
    s5, s9 = ns['ESCALA_5_NIVEIS'], ns['ESCALA_9_NIVEIS']
    d7 = s9.model_dump(mode='json')
    d7['id'] = 'ordinal_7_diagnostico'
    d7['niveis'] = [n for n in d7['niveis'] if abs(n['codigo']) != 1]
    for i, n in enumerate(d7['niveis']): n['valor'] = i / 6
    for eixo in d7['rubricas_por_eixo']:
        d7['rubricas_por_eixo'][eixo] = {n['chave']: d7['rubricas_por_eixo'][eixo][n['chave']] for n in d7['niveis']}
    s7 = ns['validar_escala'](d7)
    texto = 'Vamos ampliar o benefício das famílias de baixa renda.'
    for escala in (s5, s9, s7):
        for primitiva in ('score', 'choice'):
            for index, nivel in enumerate(escala.niveis):
                probs = {str(i) if primitiva == 'score' else n.chave: int(i == index) for i, n in enumerate(escala.niveis)}
                d = ns['_normalizar_polaridade_ordinal']({'probabilities': probs, 'confidence': .95}, True, primitiva, escala)
                assert d['nivel'] == nivel.codigo and d['valor_0_100'] == 100 * nivel.valor
                assert d['classe'] == (nivel.polo or 'C')
                assert d['p_polo_A'] == int(nivel.polo == 'A')
                assert d['p_polo_B'] == int(nivel.polo == 'B')
        class Jev:
            async def system_one(self, **kwargs):
                return {'answers': {k: v for e in ns['AXIS_SPECS'] for k, v in {
                    f'{e}_relevancia': {'choice': 'A', 'probabilities': {'A': .9, 'B': .1}},
                    f'{e}_polaridade': {'probabilities': {str(i): int(i == len(escala.niveis)-1) for i in range(len(escala.niveis))}, 'confidence': .99}}.items()}}
        pipeline = ns['CascataJevLLM2Polos'](Jev(), None, ns['AXIS_SPECS'], escala=escala, usar_fallback=False)
        registro = await pipeline.classificar(texto)
        assert registro['escala_hash'] == escala.hash
        resumo = ns['resumir_documento']([registro])
        assert list(resumo['índice A']) == [100] * 4
        if '--html' in sys.argv:
            target = Path(__file__).resolve().parents[1] / 'app/test-results/scales'
            target.mkdir(parents=True, exist_ok=True)
            data = ns['criar_dados_fluxograma']([registro], resumo, contexto={'nome': f'SIMULAÇÃO {escala.id}'}, rubricas=pipeline.rubricas)
            (target / f'{escala.id}.html').write_text(ns['renderizar_fluxograma'](data), encoding='utf-8')
        schema = ns['_esquema_resposta'](['economic'], escala)
        for codigo in [n.codigo for n in escala.niveis]:
            schema.model_validate({'eixos': [{'eixo': 'economic', 'relevante': True, 'nivel': codigo, 'evidencia': texto}]})
        print(f'{escala.id}: {len(escala.niveis)} níveis, Score/Choice/LLM/cascata/agregação OK ({escala.hash[:12]})')
    return ns


if __name__ == '__main__': asyncio.run(validar())
