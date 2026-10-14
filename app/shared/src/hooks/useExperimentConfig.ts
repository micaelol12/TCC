import { useEffect, useRef, useState } from 'react'
import type { Capabilities } from '../api/analysisApi'
import { configError, importPreset, isLabBuild, modelReady, type ExperimentConfig } from '../domain/experimentConfig'

export function useExperimentConfig(caps: Capabilities | null, scope: string, mode: 'low' | 'medium' | 'high' = 'medium') {
  const available = isLabBuild && caps?.environment === 'lab' && caps.experimental?.enabled === true ? caps.experimental : null
  const [config, setConfig] = useState<ExperimentConfig | null>(null)
  const [notice, setNotice] = useState('')
  const loaded = useRef(false)
  const key = `8values-lab-preset-v1:${scope}`
  useEffect(() => {
    if (!available || loaded.current) return
    loaded.current = true
    let next = { ...available.defaults }
    try {
      const raw = localStorage.getItem(key)
      if (raw) next = importPreset(JSON.parse(raw), available)
    } catch { setNotice('A configuração salva não está disponível nesta API. Os padrões foram restaurados.') }
    setConfig(next)
  }, [available, key])
  const error = available ? configError(config, available) || (mode !== 'low' && config && !modelReady(available, config.llm_model) ? 'Cadastre a chave do provedor selecionado na aba API keys ou escolha um modelo com chave configurada.' : '') : ''
  return { available, config, setConfig, notice, setNotice, storageKey: key, error,
    requestConfig: available && config && !error ? { ...config } : undefined,
    blocked: !!available && !!error }
}
