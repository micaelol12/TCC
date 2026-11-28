import { useState } from 'react'
import { exportPreset, importPreset, type ExperimentConfig, type ExperimentCapabilities } from '../../domain/experimentConfig'
import Actions from '../Actions'
import Button from '../Button'

type PresetControlsProps = {
  capabilities: ExperimentCapabilities
  config: ExperimentConfig
  busy: boolean
  error: string
  notice: string
  onNotice: (message: string) => void
  onChange: (config: ExperimentConfig) => void
}

/** Reúne importação, exportação e restauração dos parâmetros de uma análise Lab. */
export default function ExperimentPresetControls({ capabilities, config, busy, error, notice, onNotice, onChange }: PresetControlsProps) {
  const [fileError, setFileError] = useState('')

  /** Restringe o tamanho e valida o preset antes de aplicá-lo à próxima análise. */
  async function importPresetFile(file?: File) {
    if (!file) return
    setFileError('')
    try {
      if (file.size > 200000) throw new Error('Arquivo acima do limite de 200 KB.')
      onChange(importPreset(JSON.parse(await file.text()), capabilities))
      onNotice('Configuração importada para a próxima análise.')
    } catch (err) { setFileError(err instanceof Error ? err.message : 'Não foi possível importar.') }
  }

  /** Gera o arquivo JSON versionado da configuração atual e libera a URL temporária. */
  function downloadPreset() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(exportPreset(config), null, 2)], { type: 'application/json' }))
    const link = document.createElement('a')
    link.href = url
    link.download = '8values-lab-config.json'
    link.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  }

  /** Restaura os padrões anunciados pela API e limpa os erros de importação. */
  function restoreDefaults() {
    onChange({ ...capabilities.defaults })
    setFileError('')
    onNotice('Padrões restaurados para a próxima análise.')
  }

  return <><Actions><Button variant="secondary" disabled={busy} onClick={restoreDefaults}>Restaurar padrões</Button><Button variant="secondary" disabled={busy || !!error} onClick={downloadPreset}>Exportar JSON</Button></Actions>
    <label htmlFor="lab-import">Importar configuração JSON</label><input id="lab-import" type="file" accept="application/json,.json" disabled={busy} onChange={e => { void importPresetFile(e.target.files?.[0]); e.target.value = '' }} />
    {fileError && <p className="error" role="alert">{fileError}</p>}{notice && <p className="small" role="status">{notice}</p>}</>
}
