import { useState } from 'react'
import { evidenceFields, configLabels, numericFields, type ExperimentConfig, type ExperimentCapabilities } from '../domain/experimentConfig'
import type { Mode } from '../api/analysisApi'
import type { createAnalysisClient } from '../api/analysisApi'
import LabApiKeys from './LabApiKeys'
import { sameContent } from '../domain/ordinalScale'
import ExperimentProcessingFields from './experiment/ExperimentProcessingFields'
import ExperimentEvidenceFields from './experiment/ExperimentEvidenceFields'
import ExperimentPresetControls from './experiment/ExperimentPresetControls'
import HelperText from './HelperText'
import Button from './Button'

/** Organiza os campos de configuração Lab, presets e chaves disponíveis antes do envio. */
export default function ExperimentPanel({ capabilities, config, onChange, mode, busy, error, notice, onNotice, client, onKeysUpdated, collapsible = false }: {
  capabilities: ExperimentCapabilities; config: ExperimentConfig | null; onChange: (config: ExperimentConfig) => void;
  mode: Mode; busy: boolean; error: string; notice: string; onNotice: (value: string) => void;
  client: ReturnType<typeof createAnalysisClient>; onKeysUpdated: () => Promise<void>; collapsible?: boolean
}) {
  const [tab, setTab] = useState<'parameters' | 'keys'>('parameters')
  if (!config) return <p role="status">Carregando a configuração Lab…</p>
  const changed = [...numericFields, ...evidenceFields, 'contexto_posicao_politica', 'jev_model', 'llm_model', 'escala', 'primitiva_polaridade', 'regra_decisao', 'chunk_strategy'].filter(name => !sameContent(config[name as keyof ExperimentConfig], capabilities.defaults[name as keyof ExperimentConfig]))
  const panel = <section className="experimentPanel" aria-label="Configuração da análise">
    {!collapsible && <h3>Configuração da análise · Lab</h3>}
    <div role="tablist" aria-label="Configuração Lab"><Button id="lab-tab-parameters" role="tab" aria-selected={tab === 'parameters'} aria-controls="lab-parameters" variant={tab === 'parameters' ? 'primary' : 'secondary'} disabled={busy} onClick={() => setTab('parameters')}>Parâmetros</Button><Button id="lab-tab-keys" role="tab" aria-selected={tab === 'keys'} aria-controls="lab-keys" variant={tab === 'keys' ? 'primary' : 'secondary'} disabled={busy} onClick={() => setTab('keys')}>API keys</Button></div>
    <div id="lab-keys" role="tabpanel" aria-labelledby="lab-tab-keys" hidden={tab !== 'keys'}><LabApiKeys client={client} caps={capabilities} busy={busy} onUpdated={onKeysUpdated} /></div>
    <div id="lab-parameters" role="tabpanel" aria-labelledby="lab-tab-parameters" hidden={tab !== 'parameters'}>
    <HelperText>Suas chaves nesta sessão: TypeSafe {capabilities.providers.typesafe ? 'configurado' : 'ausente'} · Maritaca {capabilities.providers.maritaca ? 'configurado' : 'ausente'} · Gemini {capabilities.providers.gemini ? 'configurado' : 'ausente'}. Cadastre suas chaves na aba API keys para liberar os modos e modelos.</HelperText>
    <ExperimentProcessingFields capabilities={capabilities} config={config} mode={mode} busy={busy} onChange={onChange} />
    <fieldset disabled={busy}><legend>{configLabels.contexto_posicao_politica}</legend>
      <label htmlFor="lab-contexto_posicao_politica">Instruções de contexto</label>
      <textarea id="lab-contexto_posicao_politica" rows={8} value={config.contexto_posicao_politica ?? capabilities.defaults.contexto_posicao_politica ?? ''} aria-describedby="help-contexto_posicao_politica" onChange={e => onChange({ ...config, contexto_posicao_politica: e.target.value })} />
      <HelperText id="help-contexto_posicao_politica">Define como interpretar posições, descrições, citações e críticas. Usado pelo JEV, pelo LLM e na checagem de evidências, junto às rubricas da escala. Aceita até 20.000 caracteres e acompanha o JSON exportado.</HelperText>
    </fieldset>
    <ExperimentEvidenceFields capabilities={capabilities} config={config} mode={mode} busy={busy} onChange={onChange} />
    <p className="small">{changed.length ? `Alterações: ${changed.map(name => `${configLabels[name as keyof ExperimentConfig]} = ${name === 'contexto_posicao_politica' ? 'alterado' : name === 'escala' ? config.escala?.id : config[name as keyof ExperimentConfig]}`).join('; ')}.` : 'Usando os padrões desta API.'}</p>
    {error && <p className="error" role="alert">{error}</p>}
    <HelperText>As alterações válidas são salvas automaticamente neste navegador. Ao reabrir, a última configuração salva será restaurada.</HelperText>
    <ExperimentPresetControls capabilities={capabilities} config={config} busy={busy} error={error} notice={notice} onNotice={onNotice} onChange={onChange} />
    </div>
  </section>

  return collapsible ? <details className="experimentDisclosure">
    <summary><span>Configuração da análise <small>Parâmetros e API keys{error ? ' · Verifique a configuração' : changed.length ? ` · ${changed.length} alterações` : ' · Padrões da API'}</small></span><span className="configChevron" aria-hidden="true">⌄</span></summary>
    {panel}
  </details> : panel
}
