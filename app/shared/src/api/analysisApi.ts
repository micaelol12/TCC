import { isLabBuild, type ExperimentConfig } from '../domain/experimentConfig'
import { sameContent } from '../domain/ordinalScale'
import type { Analysis, Capabilities, LabProvider, Mode } from './analysisContracts'
import { isAnalysis, isCapabilities } from './analysisValidation'
import { createLabSession, type LabSessionStorage } from './labSession'

export type * from './analysisContracts'
export type { LabSessionStorage } from './labSession'
export { modes, modeLabels, modeDescriptions, recipients, configuredRecipients } from './analysisModes'
export { isAnalysis, isCapabilities } from './analysisValidation'

export class AnalysisTimeoutError extends Error {
  constructor() {
    super('A análise excedeu o tempo de espera. O texto foi preservado.')
    this.name = 'AnalysisTimeoutError'
  }
}

function analysisErrorMessage(status: number): string {
  const messages: Record<number, string> = {
    401: isLabBuild ? 'Sessão de chaves expirada. Atualize a conexão e cadastre novamente na aba API keys.' : 'O serviço de análise está com um problema de acesso. Verifique a conexão ou avise a equipe responsável.',
    403: isLabBuild ? 'Configuração experimental indisponível nesta API. Atualize a conexão.' : 'Este serviço não permite a análise solicitada. Verifique a conexão ou avise a equipe responsável.',
    413: isLabBuild ? 'Texto acima do limite. No Lab, aumente os tokens por trecho ou reduza o texto.' : 'O texto excede a capacidade de uma análise. Reduza o texto e tente novamente, mesmo que ele esteja dentro do limite de caracteres.',
    422: isLabBuild ? 'Entrada ou configuração inválida. Atualize a conexão e confira os parâmetros.' : 'Não foi possível analisar o conteúdo enviado. Confira o texto, verifique os modos disponíveis e tente novamente.',
    429: 'Limite de uso atingido. Tente mais tarde.',
    503: 'Este modo está indisponível. Verifique a conexão e escolha outro modo disponível ou tente mais tarde.',
    504: 'A análise excedeu o tempo disponível. Tente novamente com um texto menor.',
  }
  return messages[status] ?? 'Falha na análise. Tente novamente.'
}

function validateAnalysisResponse(data: unknown, processingLevel: Mode, requestedConfig?: ExperimentConfig): Analysis {
  if (!isAnalysis(data) || data.processing_level !== processingLevel) {
    throw new Error('A API retornou uma análise inválida.')
  }
  if (requestedConfig) {
    const effectiveConfig = data.effective_config
    const configMatches = effectiveConfig && Object.keys(requestedConfig).every(name =>
      sameContent(effectiveConfig[name as keyof ExperimentConfig], requestedConfig[name as keyof ExperimentConfig]))
    if (data.environment !== 'lab' || !configMatches) {
      throw new Error('A API não confirmou a configuração experimental utilizada.')
    }
  }
  return data
}

export function createAnalysisClient(baseUrl = '', fetcher: typeof fetch = (...args) => fetch(...args), labClient: 'web' | 'extension' = 'web', sessionStore?: LabSessionStorage) {
  const apiBaseUrl = baseUrl.replace(/\/$/, '')
  const session = createLabSession(apiBaseUrl, labClient, sessionStore)

  async function updateLabKey(provider: LabProvider, apiKey?: string) {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 10000)
    try {
      const response = await fetcher(`${apiBaseUrl}/api/lab/api-keys${apiKey === undefined ? `/${provider}` : ''}`, {
        method: apiKey === undefined ? 'DELETE' : 'POST', headers: { ...await session.buildHeaders(), 'Content-Type': 'application/json' },
        body: apiKey === undefined ? undefined : JSON.stringify({ provider, api_key: apiKey }), signal: controller.signal, cache: 'no-store', credentials: 'omit',
      })
      if (response.status === 401) {
        await session.saveToken('')
        throw new Error('Sessão expirada. Tente cadastrar a chave novamente.')
      }
      if (!response.ok) throw new Error('Não foi possível atualizar a chave. Confira o formato e a conexão com a API Lab.')
      const data = await response.json()
      if (typeof data.session_token !== 'string' || !/^[A-Za-z0-9_-]{40,100}$/.test(data.session_token)) throw new Error('Resposta inválida da API Lab.')
      await session.saveToken(data.session_token)
    } finally {
      clearTimeout(timer)
    }
  }
  return {
    saveLabKey: (provider: LabProvider, apiKey: string) => updateLabKey(provider, apiKey),
    removeLabKey: (provider: LabProvider) => updateLabKey(provider),
    async clearLabSession() {
      const controller = new AbortController()
      const timer = setTimeout(() => controller.abort(), 10000)
      try {
        const response = await fetcher(`${apiBaseUrl}/api/lab/session`, { method: 'DELETE', headers: await session.buildHeaders(), cache: 'no-store', credentials: 'omit', signal: controller.signal })
        if (!response.ok) throw new Error('Não foi possível encerrar a sessão de chaves.')
        await session.saveToken('')
      } finally {
        clearTimeout(timer)
      }
    },
    async getCapabilities(signal?: AbortSignal): Promise<Capabilities> {
      const controller = new AbortController()
      const abort = () => controller.abort()
      signal?.addEventListener('abort', abort, { once: true })
      if (signal?.aborted) abort()
      const timer = setTimeout(abort, 10000)
      try {
        let response = await fetcher(`${apiBaseUrl}/api/capabilities`, { headers: await session.buildHeaders(), cache: 'no-store', credentials: 'omit', signal: controller.signal })
        if (response.status === 401 && await session.readToken()) {
          await session.saveToken('')
          response = await fetcher(`${apiBaseUrl}/api/capabilities`, {
            headers: await session.buildHeaders(), cache: 'no-store', credentials: 'omit', signal: controller.signal,
          })
        }
        if (!response.ok) throw new Error('Não foi possível consultar a API.')
        const data: unknown = await response.json()
        if (!isCapabilities(data)) throw new Error('A API retornou capacidades inválidas.')
        return data
      } finally {
        clearTimeout(timer)
        signal?.removeEventListener('abort', abort)
      }
    },
    async analyze(text: string, processingLevel: Mode, signal: AbortSignal, timeoutSeconds = 120, experimentConfig?: ExperimentConfig): Promise<Analysis> {
      const controller = new AbortController()
      let timedOut = false
      const abort = () => controller.abort()
      signal.addEventListener('abort', abort, { once: true })
      if (signal.aborted) abort()
      const timer = setTimeout(() => {
        timedOut = true
        controller.abort()
      }, (timeoutSeconds + 15) * 1000)
      try {
        const response = await fetcher(`${apiBaseUrl}/api/analyze`, {
          method: 'POST', headers: { 'Content-Type': 'application/json', ...await session.buildHeaders() }, credentials: 'omit', cache: 'no-store',
          body: JSON.stringify({ text, processing_level: processingLevel, ...(experimentConfig ? { experiment_config: experimentConfig } : {}) }), signal: controller.signal,
        })
        if (!response.ok) {
          if (response.status === 401) await session.saveToken('')
          throw new Error(analysisErrorMessage(response.status))
        }
        const data: unknown = await response.json()
        return validateAnalysisResponse(data, processingLevel, experimentConfig)
      } catch (error) {
        if (timedOut) throw new AnalysisTimeoutError()
        if (error instanceof TypeError) throw new Error('Falha de conexão com o serviço de análise. Verifique sua conexão e tente novamente. O texto foi preservado.')
        throw error
      } finally {
        clearTimeout(timer)
        signal.removeEventListener('abort', abort)
      }
    },
  }
}
