import type { Analysis, AnalysisEntry } from './analysisApi'

export const REPORT_NOTICE_VERSION = '1'
export const REPORT_NOTICE = 'O trecho analisado e a análise gerada serão enviados e armazenados em nosso banco de dados para posterior avaliação pela equipe responsável. Se você escrever um comentário, ele também será armazenado.'
export const REPORT_COMMENT_LIMIT = 2000
export type ReportRequest = {
  submission_id: string; text: string; analysis: Analysis; comment: string;
  client: 'web' | 'extension'; storage_consent: true; notice_version: '1'
}
export type ReportResponse = { report_id: string; received_at: string; status: 'pending' }
export type ReportClient = ReturnType<typeof createReportClient>

export function buildReport(entry: AnalysisEntry<number | string>, client: ReportRequest['client'], comment: string, submissionId: string): ReportRequest {
  // Explicit allowlist: source URL/domain, title, profile and history never enter this payload.
  return { submission_id: submissionId, text: entry.text, analysis: entry.analysis, comment, client, storage_consent: true, notice_version: REPORT_NOTICE_VERSION }
}

export function createReportClient(baseUrl = '', fetcher: typeof fetch = (...args) => fetch(...args)) {
  const base = baseUrl.replace(/\/$/, '')
  return {
    async report(payload: ReportRequest, signal?: AbortSignal): Promise<ReportResponse> {
      if (payload.storage_consent !== true) throw new Error('Confirme o envio e o armazenamento para continuar.')
      const controller = new AbortController()
      const abort = () => controller.abort()
      signal?.addEventListener('abort', abort, { once: true })
      if (signal?.aborted) abort()
      let timedOut = false
      const timer = setTimeout(() => { timedOut = true; controller.abort() }, 15000)
      try {
        const response = await fetcher(`${base}/api/reports`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'omit', cache: 'no-store',
          body: JSON.stringify(payload), signal: controller.signal,
        })
        if (!response.ok) {
          const messages: Record<number, string> = {
            409: 'O identificador deste report já foi utilizado com outros dados.',
            413: 'O report está acima do limite de tamanho.',
            422: 'Os dados do report são inválidos. Confira a análise e a confirmação de armazenamento.',
            429: 'Limite de reports atingido. Tente mais tarde.',
            503: 'Não foi possível armazenar o report. Tente novamente.',
          }
          throw new Error(messages[response.status] ?? 'Não foi possível confirmar o armazenamento do report. Tente novamente.')
        }
        const data: unknown = await response.json()
        if (!data || typeof data !== 'object' || !('report_id' in data) || typeof data.report_id !== 'string' ||
          !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(data.report_id) ||
          !('received_at' in data) || typeof data.received_at !== 'string' || !Number.isFinite(Date.parse(data.received_at)) ||
          !('status' in data) || data.status !== 'pending') throw new Error('Não foi possível confirmar o armazenamento do report. Tente novamente.')
        return data as ReportResponse
      } catch (err) {
        if (timedOut) throw new Error('O prazo de envio terminou sem confirmação. Tente novamente para verificar o armazenamento.')
        if (err instanceof TypeError) throw new Error('Falha de conexão. Tente novamente para verificar o armazenamento do report.')
        throw err
      } finally { clearTimeout(timer); signal?.removeEventListener('abort', abort) }
    },
  }
}
