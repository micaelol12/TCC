import type { Analysis, AxisResult } from '../../api/analysisApi'
import { AXES } from '../../domain/axes'
import type { ScaleLevel } from '../../domain/ordinalScale'
import LevelDistribution from './LevelDistribution'
import styles from '../../styles/Evidence.module.css'

export default function FinalLevelDistribution({ analysis, result, levels }: { analysis: Analysis; result: AxisResult; levels: ScaleLevel[] }) {
  if (!result.valid_chunks) return <div className={styles.empty}><strong>Sem distribuição final</strong><p>{result.status === 'no_evidence' ? 'Os trechos foram considerados sem relevância para este eixo, por isso não receberam níveis para compor o resultado.' : 'Nenhum trecho recebeu uma estimativa válida para compor a distribuição deste eixo.'}</p></div>
  const counts = Object.fromEntries(levels.map(level => [level.chave, analysis.escala ? result.level_counts_by_key?.[level.chave] ?? 0 : result.level_counts[level.chave as keyof typeof result.level_counts] ?? 0]))
  return <>
    <div className={styles.sectionHeading}><h5>Percentual de trechos por nível</h5><span className={styles.caption}>{result.valid_chunks} válidos de {result.total_chunks}</span></div>
    <p className={styles.help}>Níveis finais usados no resultado, após eventuais revisões pelo LLM. As porcentagens e barras mostram a proporção de cada nível entre os trechos válidos do eixo.</p>
    <LevelDistribution axis={result.axis} levels={levels} values={counts} unit="count" total={result.valid_chunks} label={`Distribuição final de ${AXES[result.axis].title}`} />
    <p className={styles.caption}>Trechos sem estimativa válida ficam fora desta contagem. O nível sem posição é uma classificação válida e não equivale a uma estimativa ausente.</p>
    {result.ci95 && <p className={styles.help}>Intervalo entre trechos (95%): {result.ci95[0].toLocaleString('pt-BR', { maximumFractionDigits: 1 })}–{result.ci95[1].toLocaleString('pt-BR', { maximumFractionDigits: 1 })}. Não representa probabilidade de acerto.</p>}
  </>
}
