import { Link } from 'react-router-dom'
import AxisBar from '../../components/AxisBar'
import { axisOrder } from '../../domain/axes'
import type { Profile } from '../../storage/localProfile'
import styles from '@8values/shared/styles/Cards.module.css'
import IdeologyMatch from '../../components/IdeologyMatch'
import { downloadProfile } from '@8values/shared/profile'
import ExtensionTransfer from './ExtensionTransfer'
import ConfirmAction from '@8values/shared/components/ConfirmAction'

export default function ResultPage({ profile, stored, onDelete }: { profile: Profile | null; stored: boolean; onDelete: () => void }) {
  if (!profile) return <main className="narrow flow"><h1>Meu resultado</h1><p>Você ainda não concluiu o teste neste navegador.</p><Link className="button" to="/teste">Fazer meu teste</Link></main>
  return <main className="narrow flow"><div className="eyebrow">Meu resultado</div><h1>Seus quatro eixos</h1>
    <p className="muted">Os valores mostram sua posição em cada par de polos. O complemento de cada eixo soma 100.</p>
    {stored ? <p className="notice" role="status">Salvo somente neste navegador. Limpar os dados do site também remove este resultado.</p> : <p className="notice" role="status">Resultado em memória. Ele será perdido ao fechar ou recarregar esta página.</p>}
    <section className={styles.card} aria-labelledby="result-axes-heading"><h2 id="result-axes-heading" className="srOnly">Pontuação por eixo</h2>{axisOrder.map(axis => <AxisBar key={axis} axis={axis} score={profile.scores[axis]} />)}</section>
    <IdeologyMatch scores={profile.scores} source="test" />
    <ExtensionTransfer key={JSON.stringify(profile)} profile={profile} />
    <button className="secondary" onClick={() => downloadProfile(profile)}>Baixar resultado</button>
    <p className="muted small">O arquivo em formato JSON contém apenas os quatro resultados agregados e a versão do questionário. Você pode importá-lo na extensão.</p>
    <div className="actions"><Link className="button" to="/analise">Analisar um texto</Link><Link className="button secondary" to="/teste">Refazer teste</Link><ConfirmAction label="Apagar meus dados locais" title="Apagar os dados deste site?"
      description="Seu resultado, as respostas do teste, o rascunho de texto e o histórico de análises deste site serão apagados. Arquivos baixados, o perfil da extensão e relatos já enviados serão mantidos. Esta ação não pode ser desfeita."
      confirmLabel="Sim, apagar dados do site" onConfirm={onDelete} /></div>
    <p className="muted small">Apagar os dados locais não remove relatos já enviados e armazenados no servidor.</p>
    <p className="muted small">Os percentuais descrevem suas respostas ao questionário e não são um diagnóstico político.</p>
  </main>
}
