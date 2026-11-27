import type { Profile } from '@8values/shared/profile'
import ConfirmAction from '@8values/shared/components/ConfirmAction'
import { WEB_BASE_URL } from '../../config'

type ExtensionProfileSettingsProps = {
  profile: Profile | null
  ready: boolean
  busy: boolean
  error: string
  onImport: (file?: File) => Promise<void>
  onDelete: () => Promise<void>
}

/** Apresenta o perfil de comparação e os controles de importação e exclusão local. */
export default function ExtensionProfileSettings({ profile, ready, busy, error, onImport, onDelete }: ExtensionProfileSettingsProps) {
  return <section className="profileSettings" aria-label="Perfil pessoal"><h2>Meu perfil local</h2><p className="muted small">No site, abra “Meu resultado” e clique em “Usar resultado na extensão”. A comparação será atualizada aqui automaticamente.</p>
          <a className="button secondary" href={`${WEB_BASE_URL}/resultado`} target="_blank" rel="noreferrer">Abrir meu resultado no site</a>
          <p className="muted small">O perfil fica salvo nesta extensão até você apagá-lo.</p>
          {profile && <><p role="status" className="small">Perfil salvo localmente nesta extensão.</p><ConfirmAction label="Apagar perfil" title="Apagar o perfil desta extensão?" description="Seu resultado do teste será removido desta extensão. As análises e o resultado salvo no site serão mantidos. Para comparar novamente, envie ou importe seu resultado do teste."
            confirmLabel="Sim, apagar perfil" disabled={busy} onConfirm={onDelete} /></>}
          <label htmlFor="profile-file">Importar resultado do teste</label><input id="profile-file" type="file" accept="application/json,.json" disabled={busy || !ready} onChange={e => { void onImport(e.target.files?.[0]); e.target.value = '' }} />
          <p className="muted small">Selecione o arquivo obtido em “Baixar resultado”, na página “Meu resultado” do site.</p>
          {error && <p className="error" role="alert">{error}</p>}
        </section>
}
