import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import QuizPage from './features/quiz/QuizPage'
import ResultPage from './features/quiz/ResultPage'
import AnalysisPage from './features/analysis/AnalysisPage'
import type { Profile } from './storage/localProfile'
import { PROFILE_KEY, readProfile, removeLocalData } from './storage/localProfile'
import { clearAnalysisHistory } from './features/analysis/analysisHistory'
import { isLabBuild } from '@8values/shared/domain/experimentConfig'

export default function App() {
  const [profile, setProfile] = useState<Profile | null>(() => readProfile())
  const [stored, setStored] = useState(() => readProfile() !== null)
  const navigate = useNavigate()
  const location = useLocation()
  const contentRef = useRef<HTMLDivElement>(null)
  const initialRoute = useRef(true)
  useEffect(() => { if (isLabBuild) document.title = '8values Lab · versão de teste' }, [])
  useEffect(() => {
    const sync = (event: StorageEvent) => {
      if (event.key === PROFILE_KEY || event.key === null) { const current = readProfile(); setProfile(current); setStored(current !== null) }
    }
    window.addEventListener('storage', sync)
    return () => window.removeEventListener('storage', sync)
  }, [])
  useEffect(() => {
    if (initialRoute.current) { initialRoute.current = false; return }
    window.scrollTo(0, 0)
    contentRef.current?.focus({ preventScroll: true })
  }, [location.pathname])
  function clear() { removeLocalData(); clearAnalysisHistory(); setProfile(null); setStored(false); navigate('/') }
  return <>
    <a className="skipLink" href="#main-content">Pular para o conteúdo</a>
    <header className="siteHeader"><Link to="/" className="brand"><span className="brandMark">8</span><span>valores<span className="brandPlus">+ textos</span></span></Link><nav aria-label="Navegação principal"><NavLink to="/teste">Teste</NavLink><NavLink to="/resultado">Meu resultado</NavLink><NavLink to="/analise">Analisar texto</NavLink></nav></header>
    <div id="main-content" ref={contentRef} tabIndex={-1} role="region" aria-label="Conteúdo principal"><Routes>
      <Route path="/" element={<main className="home"><div className="homeHero"><div className="eyebrow">POLÍTICA · LEITURA CRÍTICA · QUATRO EIXOS</div><h1>Conheça seus valores e compare com as posições presentes em um texto.</h1><p>Responda ao questionário 8values, analise textos políticos e veja as diferenças eixo por eixo, com limites e evidências à vista.</p><div className="actions"><Link className="button" to="/teste">Fazer meu teste</Link>{profile && <Link className="button secondary" to="/analise">Continuar para análises</Link>}<Link className="button quiet" to="/analise">Analisar sem teste</Link></div><p className="privacyNote">Seu teste é calculado neste navegador. Os textos enviados para análise são processados por serviços externos.</p></div><div className="homeCards"><div><span>01</span><h2>Responda</h2><p>70 perguntas, cinco alternativas e revisão antes de concluir.</p></div><div><span>02</span><h2>Analise</h2><p>Envie um texto por vez e escolha entre três modos de processamento.</p></div><div><span>03</span><h2>Compare</h2><p>Veja diferenças nos quatro eixos, sem um índice global de compatibilidade.</p></div></div></main>} />
      <Route path="/teste" element={<QuizPage onComplete={(next, saved) => { setProfile(next); setStored(saved) }} />} />
      <Route path="/resultado" element={<ResultPage profile={profile} stored={stored} onDelete={clear} />} />
      <Route path="/analise" element={<AnalysisPage profile={profile} />} />
      <Route path="*" element={<main className="narrow flow"><h1>Página não encontrada</h1><Link to="/">Voltar ao início</Link></main>} />
    </Routes></div>
    <footer><span>8values + textos · projeto acadêmico · baseado no <a href="https://8values.github.io/">8values original</a></span><span>Resultados descritivos, sem diagnóstico político.</span></footer>
  </>
}
