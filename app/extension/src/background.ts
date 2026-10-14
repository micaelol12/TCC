import { captureKey, isCapture, makeCapture, MENU_ID, sessionKey } from './platform/selection'
import { registerProfileTransfer } from './platform/profileTransfer'
import { isLabBuild } from '@8values/shared/domain/experimentConfig'

declare const __WEB_BASE_URL__: string
registerProfileTransfer(__WEB_BASE_URL__)

// Register synchronously on each worker start; only installation creates the menu.
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({ id: MENU_ID, title: isLabBuild ? 'Analisar com 8values Lab' : 'Analisar com 8values', contexts: ['selection'], documentUrlPatterns: ['http://*/*', 'https://*/*'] })
  })
  void chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true })
  void chrome.storage.local.setAccessLevel({ accessLevel: 'TRUSTED_CONTEXTS' })
})
let writes: Promise<void> = Promise.resolve()
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId !== MENU_ID || !tab?.id || tab.windowId === undefined) return
  // Preserve the user gesture: do not await storage before opening.
  void chrome.sidePanel.open({ windowId: tab.windowId }).catch(() => { /* the toolbar action can reopen the panel */ })
  const capture = makeCapture(info.selectionText ?? '', tab.windowId, tab.id, info.frameUrl ?? info.pageUrl)
  writes = writes.catch(() => undefined).then(async () => {
    try {
      const key = captureKey(capture.windowId)
      const previous = (await chrome.storage.session.get(key))[key]
      capture.createdAt = Math.max(capture.createdAt, (isCapture(previous) ? previous.createdAt : 0) + 1)
      await chrome.storage.session.set({ [key]: capture })
    }
    catch { await chrome.runtime.sendMessage({ type: 'capture-storage-failed', windowId: capture.windowId, capture }).catch(() => undefined) }
  })
})
chrome.windows.onRemoved.addListener(windowId => {
  writes = writes.catch(() => undefined).then(async () => {
    await chrome.storage.session.remove([captureKey(windowId), sessionKey(windowId)])
  })
})
