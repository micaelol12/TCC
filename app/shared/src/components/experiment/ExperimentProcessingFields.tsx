import { configLabels } from '../../domain/experimentConfig'
import { sameContent } from '../../domain/ordinalScale'
import type { ExperimentFieldProps } from './experimentFieldTypes'
import ExperimentNumericFields from './ExperimentNumericFields'
import ExperimentModelFields from './ExperimentModelFields'

/** Edita escala, segmentação e regras JEV conforme o modo de processamento. */
export default function ExperimentProcessingFields({ capabilities, config, mode, busy, onChange }: ExperimentFieldProps) {
  return <fieldset disabled={busy}><legend>Parâmetros da próxima análise</legend><div className="experimentFields">
      <div><label htmlFor="lab-chunk_strategy">{configLabels.chunk_strategy}</label>
        <select id="lab-chunk_strategy" value={config.chunk_strategy ?? 'tokens'} aria-describedby="help-chunk_strategy" onChange={e => onChange({ ...config, chunk_strategy: e.target.value as 'sentencas' | 'tokens' })}>
          <option value="sentencas">Sentenças · preservar frases inteiras</option><option value="tokens">Tokens · corte por tamanho</option>
        </select><small id="help-chunk_strategy" className="muted">Corresponde a preparacao_e_exibicao.chunks.estrategia no pipeline. Em sentenças, os tokens por trecho são um alvo: uma frase longa pode ultrapassá-lo sem ser cortada.</small>
      </div>
      <div><label htmlFor="lab-regra_decisao">{configLabels.regra_decisao}</label>
        <select id="lab-regra_decisao" value={config.regra_decisao ?? 'nivel'} disabled={mode === 'high'} aria-describedby="help-regra_decisao" onChange={e => onChange({ ...config, regra_decisao: e.target.value as 'nivel' | 'polo_primeiro' })}>
          <option value="nivel">Nível mais provável · atual</option><option value="polo_primeiro">Polo primeiro · experimental</option>
        </select><small id="help-regra_decisao" className="muted">{mode === 'high' ? 'Não se aplica à classificação com LLM.' : 'Polo primeiro soma os níveis de Globo/Nação (ou os polos do eixo), escolhe o grupo e depois a intensidade. Reaproveita a resposta do JEV; exige avaliação experimental.'}</small>
      </div>
      <div><label htmlFor="lab-primitiva_polaridade">{configLabels.primitiva_polaridade}</label>
        <select id="lab-primitiva_polaridade" value={config.primitiva_polaridade ?? 'score'} disabled={mode === 'high'} aria-describedby="help-primitiva_polaridade" onChange={e => onChange({ ...config, primitiva_polaridade: e.target.value as 'score' | 'choice' })}>
          <option value="score">Score · níveis ordenados</option><option value="choice">Choice · escolha entre níveis</option>
        </select><small id="help-primitiva_polaridade" className="muted">{mode === 'high' ? 'Não se aplica ao modo alto, que classifica com LLM.' : 'Escolhe como o JEV classifica a posição na escala. A relevância continua usando Choice.'}</small>
      </div>
      {!!capabilities.scales?.length && <div><label htmlFor="lab-escala">Escala ordinal</label><select id="lab-escala" value={capabilities.scales.findIndex(s => sameContent(s, config.escala))} onChange={e => onChange({ ...config, escala: structuredClone(capabilities.scales![Number(e.target.value)]) })}>
        {!capabilities.scales.some(s => sameContent(s, config.escala)) && <option value={-1}>{config.escala?.id ?? 'Selecione uma escala'}</option>}
        {capabilities.scales.map((s, i) => <option key={`${s.id}-${i}`} value={i}>{s.niveis.length} níveis · {s.id} · v{s.versao}</option>)}
      </select><small className="muted">A mesma escala será usada pelo JEV, LLM e cálculo do índice.</small></div>}
      <ExperimentNumericFields capabilities={capabilities} config={config} mode={mode} busy={busy} onChange={onChange} />
      <ExperimentModelFields capabilities={capabilities} config={config} mode={mode} busy={busy} onChange={onChange} />
    </div></fieldset>
}
