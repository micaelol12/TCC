import { configLabels, modelProvider, modelReady } from '../../domain/experimentConfig'
import type { ExperimentFieldProps } from './experimentFieldTypes'

/** Explica a disponibilidade e o papel do modelo conforme o provedor e o modo de análise. */
function getModelHelp(provider: 'jev' | 'llm', { config, capabilities, mode }: ExperimentFieldProps): string {
  if (provider === 'llm') {
    if (mode === 'low') return 'O modo baixo usa apenas JEV. O modelo LLM escolhido será usado nos modos médio e alto.'
    return modelReady(capabilities, config.llm_model)
      ? 'Modelo usado nos modos médio e alto.'
      : 'Cadastre a chave deste provedor na aba API keys para analisar com este modelo.'
  }
  return mode === 'high' && !config.semantic_evidence_check
    ? 'Não se aplica ao modo alto sem checagem semântica.'
    : 'Modelo JEV usado para classificação e checagem de evidências.'
}

/** Exibe os modelos permitidos e a disponibilidade das chaves de seus provedores. */
export default function ExperimentModelFields(props: ExperimentFieldProps) {
  const { capabilities, config, mode, onChange } = props
  return <>{(['jev', 'llm'] as const).map(provider => {
    const name = `${provider}_model` as 'jev_model' | 'llm_model'
    return <div key={name}><label htmlFor={`lab-${name}`}>{configLabels[name]}</label><select id={`lab-${name}`} value={config[name]} disabled={provider === 'jev' && mode === 'high' && !config.semantic_evidence_check} aria-describedby={`help-${name}`} onChange={e => onChange({ ...config, [name]: e.target.value })}>
      {!capabilities.allowed_models[provider].includes(config[name]) && <option value={config[name]}>Modelo indisponível</option>}
      {capabilities.allowed_models[provider].map(model => <option key={model} value={model}>{model}{provider === 'llm' ? ` · ${modelProvider(capabilities, model) === 'gemini' ? 'Gemini' : 'Maritaca'}${modelReady(capabilities, model) ? '' : ' · chave ausente'}` : ''}</option>)}</select>
      <small id={`help-${name}`} className="muted">{getModelHelp(provider, props)}</small></div>
  })}</>
}
