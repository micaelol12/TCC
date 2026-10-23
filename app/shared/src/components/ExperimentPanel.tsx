import { useState } from 'react'
import { evidenceFields, configLabels, exportPreset, importPreset, numericFields, modelReady, modelProvider, type ExperimentConfig, type ExperimentCapabilities } from '../domain/experimentConfig'
import type { Mode } from '../api/analysisApi'
import type { createAnalysisClient } from '../api/analysisApi'
import LabApiKeys from './LabApiKeys'
import { sameContent } from '../domain/ordinalScale'

const help = {
  chunk_tokens: 'Trechos menores podem aumentar as chamadas e ultrapassar o limite de trechos.',
  relevance_margin_min: 'No modo médio, margens menores que este valor encaminham o eixo ao LLM.',
  level_confidence_min: 'No modo médio, níveis com confiança menor são revisados pelo LLM.',
  direction_margin_min: 'No modo médio, direções ambíguas são revisadas pelo LLM.',
  min_valid_chunks: 'Muda a indicação de evidência suficiente; a média dos eixos é a mesma.',
  bootstrap_samples: 'Mais reamostragens refinam o intervalo entre trechos e exigem mais processamento.',
  bootstrap_seed: 'Reproduz o bootstrap. As respostas dos provedores ainda podem variar.',
}
export default function ExperimentPanel({ caps, config, onChange, mode, busy, error, storageKey, notice, onNotice, client, onKeysUpdated }: {
  caps: ExperimentCapabilities; config: ExperimentConfig | null; onChange: (config: ExperimentConfig) => void;
  mode: Mode; busy: boolean; error: string; storageKey: string; notice: string; onNotice: (value: string) => void;
  client: ReturnType<typeof createAnalysisClient>; onKeysUpdated: () => Promise<void>
}) {
  const [fileError, setFileError] = useState('')
  const [tab, setTab] = useState<'parameters' | 'keys'>('parameters')
  if (!config) return <p role="status">Carregando a configuração Lab…</p>
  const changed = [...numericFields, ...evidenceFields, 'jev_model', 'llm_model', 'escala'].filter(name => !sameContent(config[name as keyof ExperimentConfig], caps.defaults[name as keyof ExperimentConfig]))
  async function importFile(file?: File) {
    if (!file) return
    setFileError('')
    try {
      if (file.size > 200000) throw new Error('Arquivo acima do limite de 200 KB.')
      onChange(importPreset(JSON.parse(await file.text()), caps)); onNotice('Configuração importada para a próxima análise.')
    } catch (err) { setFileError(err instanceof Error ? err.message : 'Não foi possível importar.') }
  }
  function save() {
    try { localStorage.setItem(storageKey, JSON.stringify(exportPreset(config!))); onNotice('Configuração salva neste navegador.') }
    catch { setFileError('Não foi possível salvar a configuração neste navegador.') }
  }
  function download() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(exportPreset(config!), null, 2)], { type: 'application/json' }))
    const link = document.createElement('a'); link.href = url; link.download = '8values-lab-config.json'; link.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  }
  return <section className="experimentPanel" aria-label="Configuração da análise">
    <h3>Configuração da análise · Lab</h3>
    <div role="tablist" aria-label="Configuração Lab"><button id="lab-tab-parameters" role="tab" aria-selected={tab === 'parameters'} aria-controls="lab-parameters" className={tab === 'parameters' ? '' : 'secondary'} disabled={busy} onClick={() => setTab('parameters')}>Parâmetros</button><button id="lab-tab-keys" role="tab" aria-selected={tab === 'keys'} aria-controls="lab-keys" className={tab === 'keys' ? '' : 'secondary'} disabled={busy} onClick={() => setTab('keys')}>API keys</button></div>
    <div id="lab-keys" role="tabpanel" aria-labelledby="lab-tab-keys" hidden={tab !== 'keys'}><LabApiKeys client={client} caps={caps} busy={busy} onUpdated={onKeysUpdated} /></div>
    <div id="lab-parameters" role="tabpanel" aria-labelledby="lab-tab-parameters" hidden={tab !== 'parameters'}>
    <p className="small muted">Suas chaves nesta sessão: TypeSafe {caps.providers.typesafe ? 'configurado' : 'ausente'} · Maritaca {caps.providers.maritaca ? 'configurado' : 'ausente'} · Gemini {caps.providers.gemini ? 'configurado' : 'ausente'}. Cadastre suas chaves na aba API keys para liberar os modos e modelos.</p>
    <fieldset disabled={busy}><legend>Parâmetros da próxima análise</legend><div className="experimentFields">
      {!!caps.scales?.length && <div><label htmlFor="lab-escala">Escala ordinal</label><select id="lab-escala" value={caps.scales.findIndex(s => sameContent(s, config.escala))} onChange={e => onChange({ ...config, escala: structuredClone(caps.scales![Number(e.target.value)]) })}>
        {!caps.scales.some(s => sameContent(s, config.escala)) && <option value={-1}>{config.escala?.id ?? 'Selecione uma escala'}</option>}
        {caps.scales.map((s, i) => <option key={`${s.id}-${i}`} value={i}>{s.niveis.length} níveis · {s.id} · v{s.versao}</option>)}
      </select><small className="muted">A mesma escala será usada pelo JEV, LLM e cálculo do índice.</small></div>}
      {numericFields.map(name => {
        const inactive = mode === 'high' && ['relevance_margin_min', 'level_confidence_min', 'direction_margin_min'].includes(name)
        return <div key={name}><label htmlFor={`lab-${name}`}>{configLabels[name]}</label>
          <input id={`lab-${name}`} type="number" min={caps.ranges[name].min} max={caps.ranges[name].max} step={caps.ranges[name].step}
            value={Number.isFinite(config[name]) ? config[name] : ''} disabled={inactive} onChange={e => onChange({ ...config, [name]: e.target.value === '' ? NaN : Number(e.target.value) })} aria-describedby={`help-${name}`} />
          <small id={`help-${name}`} className="muted">{inactive ? 'Não se aplica ao modo alto.' : help[name]}</small></div>
      })}
      {(['jev', 'llm'] as const).map(provider => {
        const name = `${provider}_model` as 'jev_model' | 'llm_model'
        return <div key={name}><label htmlFor={`lab-${name}`}>{configLabels[name]}</label><select id={`lab-${name}`} value={config[name]} disabled={provider === 'jev' && mode === 'high' && !config.semantic_evidence_check} aria-describedby={`help-${name}`} onChange={e => onChange({ ...config, [name]: e.target.value })}>
          {!caps.allowed_models[provider].includes(config[name]) && <option value={config[name]}>Modelo indisponível</option>}
          {caps.allowed_models[provider].map(model => <option key={model} value={model}>{model}{provider === 'llm' ? ` · ${modelProvider(caps, model) === 'gemini' ? 'Gemini' : 'Maritaca'}${modelReady(caps, model) ? '' : ' · chave ausente'}` : ''}</option>)}</select>
          <small id={`help-${name}`} className="muted">{provider === 'llm'
            ? mode === 'low' ? 'O modo baixo usa apenas JEV. O modelo LLM escolhido será usado nos modos médio e alto.'
              : modelReady(caps, config.llm_model) ? 'Modelo usado nos modos médio e alto.' : 'Cadastre a chave deste provedor na aba API keys para analisar com este modelo.'
            : mode === 'high' && !config.semantic_evidence_check ? 'Não se aplica ao modo alto sem checagem semântica.' : 'Modelo JEV usado para classificação e checagem de evidências.'}</small></div>
      })}
    </div></fieldset>
    <fieldset disabled={busy}><legend>Evidências experimentais</legend>
      <label><input id="lab-semantic_evidence_check" type="checkbox" checked={config.semantic_evidence_check ?? false} onChange={e => onChange({ ...config, semantic_evidence_check: e.target.checked })} /> Verificar apoio semântico da citação</label>
      <p className="small muted">O JEV avalia se a citação sustenta, contradiz ou não comprova a posição e sua intensidade. O parecer fica registrado e não altera a pontuação. Exige TypeSafe também no modo alto.</p>
      <label><input id="lab-jev_evidence_search" type="checkbox" checked={config.jev_evidence_search ?? false} disabled={mode === 'high'} onChange={e => onChange({ ...config, jev_evidence_search: e.target.checked })} /> Buscar citações do JEV por ID</label>
      <p className="small muted">Nos modos baixo e médio, procura uma passagem original para cada decisão final do JEV. Só apresenta a citação quando o teste de existência passa. A média continua usando todos os trechos válidos.</p>
      <label htmlFor="lab-evidence_existence_min">Limiar de existência de evidência</label>
      <input id="lab-evidence_existence_min" type="number" min="0" max="1" step="0.01" value={Number.isFinite(config.evidence_existence_min ?? 0.7) ? (config.evidence_existence_min ?? 0.7) : ''} disabled={!config.jev_evidence_search || mode === 'high'} onChange={e => onChange({ ...config, evidence_existence_min: e.target.value === '' ? NaN : Number(e.target.value) })} />
      <p className="small muted">Até duas chamadas JEV adicionais por trecho com as duas opções ativas. Confiança do modelo não é probabilidade de acerto.</p>
    </fieldset>
    <p className="small">{changed.length ? `Alterações: ${changed.map(name => `${configLabels[name as keyof ExperimentConfig]} = ${name === 'escala' ? config.escala?.id : config[name as keyof ExperimentConfig]}`).join('; ')}.` : 'Usando os padrões desta API.'}</p>
    {error && <p className="error" role="alert">{error}</p>}
    <div className="actions"><button className="secondary" disabled={busy} onClick={() => { onChange({ ...caps.defaults }); setFileError(''); onNotice('Padrões restaurados para a próxima análise.') }}>Restaurar padrões</button><button className="secondary" disabled={busy || !!error} onClick={save}>Salvar configuração</button><button className="secondary" disabled={busy || !!error} onClick={download}>Exportar JSON</button></div>
    <label htmlFor="lab-import">Importar configuração JSON</label><input id="lab-import" type="file" accept="application/json,.json" disabled={busy} onChange={e => { void importFile(e.target.files?.[0]); e.target.value = '' }} />
    {fileError && <p className="error" role="alert">{fileError}</p>}{notice && <p className="small" role="status">{notice}</p>}
    </div>
  </section>
}
