import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import QuizPage from './features/quiz/QuizPage'
import HomePage from './features/home/HomePage'
import ResultPage from './features/quiz/ResultPage'
import AnalysisPage from './features/analysis/AnalysisPage'
import type { Profile } from './storage/localProfile'
import { PROFILE_KEY, readProfile, removeLocalData } from './storage/localProfile'
import { clearAnalysisHistory } from './features/analysis/analysisHistory'
import { clearAnalysisDraft } from './features/analysis/analysisDraft'
import { isLabBuild } from '@8values/shared/domain/experimentConfig'

/** Organiza as rotas e mantém o perfil compartilhado entre as páginas do site. */
export default function App() {
  const [profile, setProfile] = useState<Profile | null>(() => readProfile())
  const [stored, setStored] = useState(() => readProfile() !== null)
  const navigate = useNavigate()
  const location = useLocation()
  const contentRef = useRef<HTMLDivElement>(null)
  const initialRoute = useRef(true)
  useEffect(() => { if (isLabBuild) document.title = '8values Lab · versão de teste' }, [])
  useEffect(() => {
    /** Sincroniza o perfil quando outra aba altera ou remove os dados locais. */
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
  /** Apaga rascunho, histórico e perfil antes de limpar o estado e voltar ao início. */
  function clearSiteData() {
    try { clearAnalysisDraft(); clearAnalysisHistory(); removeLocalData(true) }
    catch { throw new Error('Não foi possível apagar todos os dados do site. Verifique as permissões de armazenamento do navegador e tente novamente.') }
    setProfile(null); setStored(false); navigate('/')
  }
  return <>
    <a className="skipLink" href="#main-content">Pular para o conteúdo</a>
    <header className="siteHeader"><Link to="/" className="brand"><span className="brandMark">8</span><span>valores<span className="brandPlus">+ textos</span></span></Link><nav aria-label="Navegação principal"><NavLink to="/teste">Teste</NavLink><NavLink to="/resultado">Meu resultado</NavLink><NavLink to="/analise">Analisar texto</NavLink></nav></header>
    <div id="main-content" ref={contentRef} tabIndex={-1} role="region" aria-label="Conteúdo principal"><Routes>
      <Route path="/" element={<HomePage hasProfile={profile !== null} />} />
      <Route path="/teste" element={<QuizPage onComplete={(next, saved) => { setProfile(next); setStored(saved) }} />} />
      <Route path="/resultado" element={<ResultPage profile={profile} stored={stored} onDelete={clearSiteData} />} />
      <Route path="/analise" element={<AnalysisPage profile={profile} />} />
      <Route path="*" element={<main className="narrow flow"><h1>Página não encontrada</h1><Link to="/">Voltar ao início</Link></main>} />
    </Routes></div>
    <footer><span>8values + textos · projeto acadêmico · baseado no <a href="https://8values.github.io/">8values original</a></span><span>Resultados descritivos, sem diagnóstico político.</span></footer>
  </>
}
