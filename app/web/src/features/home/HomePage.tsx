import { Link } from 'react-router-dom'

export default function HomePage({ hasProfile }: { hasProfile: boolean }) {
  return <main className="home">
    <div className="homeHero"><div className="eyebrow">POLÍTICA · LEITURA CRÍTICA · QUATRO EIXOS</div><h1>Conheça seus valores e compare com as posições presentes em um texto.</h1><p>Responda ao questionário 8values, analise textos políticos e veja as diferenças eixo por eixo, com limites e evidências à vista.</p>
      <div className="actions"><Link className="button" to="/teste">Fazer meu teste</Link>{hasProfile && <Link className="button secondary" to="/analise">Continuar para análises</Link>}<Link className="button quiet" to="/analise">Analisar sem teste</Link></div>
      <p className="privacyNote">Seu teste é calculado neste navegador. Os textos enviados para análise são processados por serviços externos.</p></div>
    <div className="homeCards"><div><span>01</span><h2>Responda</h2><p>70 perguntas, cinco alternativas e revisão antes de concluir.</p></div><div><span>02</span><h2>Analise</h2><p>Envie um texto por vez e escolha entre três modos de processamento.</p></div><div><span>03</span><h2>Compare</h2><p>Veja diferenças nos quatro eixos.</p></div></div>
  </main>
}
