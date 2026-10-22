import { createRoot } from 'react-dom/client'
import ExtensionApp from './ExtensionApp'
import '@8values/shared/styles/base.css'
import './panel.css'

createRoot(document.getElementById('root')!).render(<ExtensionApp />)
