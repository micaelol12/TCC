import { Link } from 'react-router-dom'
import AxisBar from '../../components/AxisBar'
import { axisOrder } from '../../domain/axes'
import type { Profile } from '../../storage/localProfile'
import styles from '../../components/Cards.module.css'
import IdeologyMatch from '../../components/IdeologyMatch'

export default function ResultPage({ profile, stored, onDelete }: { profile: Profile | null; stored: boolean; onDelete: () => void }) {
  if (!profile) return <main className="narrow flow"><h1>Meu resultado</h1><p>Você ainda não concluiu o teste neste navegador.</p><Link className="button" to="/teste">Fazer meu teste</Link></main>
  return <main className="narrow flow"><div className="eyebrow">Meu resultado</div><h1>Seus quatro eixos</h1>
    <p className="muted">Os valores mostram sua posição em cada par de polos. O complemento de cada eixo soma 100.</p>
    {stored ? <p className="notice" role="status">Salvo somente neste navegador. Limpar os dados do site também remove este resultado.</p> : <p className="notice" role="status">Resultado em memória. Ele será perdido ao fechar ou recarregar esta página.</p>}
    <section className={styles.card} aria-labelledby="result-axes-heading"><h2 id="result-axes-heading" className="srOnly">Pontuação por eixo</h2>{axisOrder.map(axis => <AxisBar key={axis} axis={axis} score={profile.scores[axis]} />)}</section>
    <IdeologyMatch scores={profile.scores} source="test" />
    <div className="actions"><Link className="button" to="/analise">Analisar um texto</Link><Link className="button secondary" to="/teste">Refazer teste</Link><button className="danger" onClick={onDelete}>Apagar meus dados locais</button></div>
    <p className="muted small">Os percentuais descrevem suas respostas ao questionário e não são um diagnóstico político.</p>
  </main>
}
