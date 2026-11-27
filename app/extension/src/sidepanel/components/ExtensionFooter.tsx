import { API_BASE_URL } from '../../config'

export default function ExtensionFooter() {
  return <footer className="panelFooter"><span>Projeto acadêmico · baseado no <a href="https://8values.github.io/" target="_blank" rel="noreferrer">8values</a></span><details><summary>Conexão e dados</summary><p>Selecionar texto não o envia. A análise envia o trecho revisado aos serviços indicados no modo escolhido. Perfil, domínio de origem e histórico não fazem parte do envio. A retenção dos serviços externos depende de suas políticas.</p><p>Ao confirmar um relato, o trecho, a análise e o comentário opcional são armazenados no servidor para posterior avaliação. Limpar os dados locais não apaga os relatos enviados.</p><details><summary>Endereço técnico do serviço</summary><p>{API_BASE_URL}</p></details></details></footer>
}
