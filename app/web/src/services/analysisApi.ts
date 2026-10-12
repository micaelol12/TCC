import type { Axis } from '../domain/axes'

export type Mode = 'low' | 'medium' | 'high'
export type AxisResult = {
  axis: Axis; pole_a: number | null; pole_b: number | null;
  status: 'estimated' | 'no_evidence' | 'abstained'; coverage: number;
  valid_chunks: number; total_chunks: number; sufficient_evidence: boolean;
  level_counts: { minus2: number; minus1: number; zero: number; plus1: number; plus2: number };
  ci95: [number, number] | null; methods_used: ('jev' | 'llm')[];
  reason_codes: string[]; evidence: { chunk_index: number; quote: string; verified: true }[]
}
export type Analysis = {
  schema_version: string; pipeline_version: string; processing_level: Mode;
  models_used: string[]; axes: AxisResult[]; chunks: { index: number; text: string }[];
  logical_calls: { jev: number; llm: number }; warnings: string[]
}
export type Capabilities = { max_chars: number; max_tokens: number; max_chunks: number; modes: Record<Mode, boolean>; timeout_seconds: number }

export async function getCapabilities(): Promise<Capabilities> {
  const response = await fetch('/api/capabilities', { cache: 'no-store' })
  if (!response.ok) throw new Error('Não foi possível consultar a API.')
  return response.json()
}

export async function analyze(text: string, processingLevel: Mode, signal: AbortSignal): Promise<Analysis> {
  const response = await fetch('/api/analyze', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, processing_level: processingLevel }), signal,
  })
  if (!response.ok) {
    const messages: Record<number, string> = { 413: 'Texto acima do limite.', 422: 'Entrada inválida.', 429: 'Limite de uso atingido. Tente mais tarde.', 503: 'Modo indisponível no servidor.', 504: 'A análise excedeu o tempo disponível.' }
    throw new Error(messages[response.status] ?? 'Falha na análise. Tente novamente.')
  }
  return response.json()
}
