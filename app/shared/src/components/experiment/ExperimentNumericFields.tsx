import { configLabels, numericFields, type ExperimentConfig, type NumericField } from '../../domain/experimentConfig'
import type { ExperimentFieldProps } from './experimentFieldTypes'

const numericFieldHelp = {
  chunk_tokens: 'Trechos menores podem aumentar as chamadas e ultrapassar o limite de trechos.',
  relevance_margin_min: 'No modo médio, margens menores que este valor encaminham o eixo ao LLM.',
  level_confidence_min: 'No modo médio, níveis com confiança menor são revisados pelo LLM.',
  direction_margin_min: 'No modo médio, direções ambíguas são revisadas pelo LLM.',
  min_valid_chunks: 'Muda a indicação de evidência suficiente; a média dos eixos é a mesma.',
  bootstrap_samples: 'Mais reamostragens refinam o intervalo entre trechos e exigem mais processamento.',
  bootstrap_seed: 'Reproduz o bootstrap. As respostas dos provedores ainda podem variar.',
}

/** Ajusta a explicação do parâmetro ao modo e à regra de decisão selecionados. */
function getNumericFieldHelp(fieldName: NumericField, config: ExperimentConfig, inactive: boolean): string {
  if (inactive) return 'Não se aplica ao modo alto.'
  if (config.regra_decisao === 'polo_primeiro') {
    if (fieldName === 'level_confidence_min') return 'No modo médio, revisa intensidades com suporte condicional abaixo deste limiar. Não é probabilidade de acerto.'
    if (fieldName === 'direction_margin_min') return 'Compara o grupo vencedor com o segundo, incluindo sem posição. No modo médio, margem menor aciona o LLM.'
  }

  return numericFieldHelp[fieldName]
}

/** Edita parâmetros numéricos dentro dos intervalos anunciados pela API. */
export default function ExperimentNumericFields({ capabilities, config, mode, onChange }: ExperimentFieldProps) {
  return <>{numericFields.map(name => {
    const inactive = mode === 'high' && ['relevance_margin_min', 'level_confidence_min', 'direction_margin_min'].includes(name)

    return <div key={name}><label htmlFor={`lab-${name}`}>{configLabels[name]}</label>
      <input id={`lab-${name}`} type="number" min={capabilities.ranges[name].min} max={capabilities.ranges[name].max} step={capabilities.ranges[name].step}
        value={Number.isFinite(config[name]) ? config[name] : ''} disabled={inactive} onChange={e => onChange({ ...config, [name]: e.target.value === '' ? NaN : Number(e.target.value) })} aria-describedby={`help-${name}`} />
      <small id={`help-${name}`} className="muted">{getNumericFieldHelp(name, config, inactive)}</small></div>
  })}</>
}
