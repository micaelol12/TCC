import type { Analysis, JevDiagnostic } from '../../api/analysisApi'
import { AXES, type Axis } from '../../domain/axes'
import type { ScaleLevel } from '../../domain/ordinalScale'
import LevelDistribution from './LevelDistribution'
import { formatLevelName, formatLevelCode, formatProbability } from './evidenceFormatting'
import styles from '../../styles/Evidence.module.css'

/** Apresenta probabilidades e decisões iniciais do JEV para o trecho selecionado. */
export default function JevModelDiagnostic({ diagnostic, analysis, axis, levels }: { diagnostic: JevDiagnostic; analysis: Analysis; axis: Axis; levels: ScaleLevel[] }) {
  const threshold = analysis.effective_config?.level_confidence_min
  const checksIntensity = diagnostic.relevante && diagnostic.regra_decisao === 'polo_primeiro' && (diagnostic.grupo_mais_provavel === 'A' || diagnostic.grupo_mais_provavel === 'B')
  const selected = levels.find(level => level.codigo === diagnostic.nivel)

  return <div className={styles.diagnostic}>
    {!diagnostic.relevante && <div className={styles.statusNotice}><strong>Trecho sem relevância neste eixo</strong><p>A avaliação inicial do JEV considerou este trecho sem relevância para o eixo {AXES[axis].title.toLocaleLowerCase('pt-BR')}.</p></div>}
    <dl className={styles.facts}>
      <div><dt>Regra de decisão</dt><dd>{diagnostic.regra_decisao === 'polo_primeiro' ? 'Polo primeiro (experimental)' : 'Nível mais provável'}</dd></div>
      <div><dt>Nível selecionado pelo JEV</dt><dd>{selected ? formatLevelName(selected, axis) : 'Indeterminado'}</dd></div>
      <div><dt>Nível mais provável global</dt><dd>{diagnostic.nivel_jev_bruto === null ? 'Empate' : formatLevelCode(diagnostic.nivel_jev_bruto)}</dd></div>
      <div><dt>Certeza do JEV (confiança do nível)</dt><dd>{formatProbability(diagnostic.confianca_nivel)}</dd></div>
      {diagnostic.probabilidade_nivel_condicional !== null && <div><dt>Suporte do nível dentro do polo</dt><dd>{formatProbability(diagnostic.probabilidade_nivel_condicional)}</dd></div>}
    </dl>
    {diagnostic.desempate_intensidade && <p className="notice small">Houve empate entre intensidades do mesmo polo. Foi selecionada a menor intensidade ({selected?.rotulo ?? diagnostic.nivel}); a intensidade permanece incerta.</p>}
    {checksIntensity && <p className="notice small">No modo Polo primeiro, a intensidade é avaliada pelo suporte dentro do polo, diferente da confiança do nível.
      {threshold !== undefined && ` Limiar desta execução: ${formatProbability(threshold)}.`}
      {diagnostic.probabilidade_nivel_condicional === null ? ' Intensidade incerta: houve empate, sem uma intensidade única selecionada.'
        : threshold === undefined ? ' O limiar não foi registrado nesta análise.'
          : diagnostic.probabilidade_nivel_condicional < threshold ? ` Intensidade incerta: o suporte de ${formatProbability(diagnostic.probabilidade_nivel_condicional)} ficou abaixo do limiar.`
            : ` O suporte atingiu o limiar.${diagnostic.desempate_intensidade ? ' A intensidade continua incerta pelo empate.' : ''}`}
    </p>}
    <h5>Distribuição dos polos · JEV</h5>
    <dl className={styles.poleValues}>{(['A', 'C', 'B'] as const).map(pole => <div key={pole}><dt>{pole === 'A' ? AXES[axis].a : pole === 'B' ? AXES[axis].b : 'Sem posição'}</dt><dd>{formatProbability(diagnostic.probabilities_abc[pole])}</dd></div>)}</dl>
    <h5>Distribuição dos níveis · JEV</h5>
    <LevelDistribution axis={axis} levels={levels} values={diagnostic.probabilities_nivel} unit="probability" label={`Distribuição dos níveis JEV de ${AXES[axis].title}`} />
    <p className={styles.caption}>O suporte dentro do polo é a probabilidade do nível dividida pela probabilidade total do polo. Essas medidas não representam probabilidade de acerto.</p>
  </div>
}
