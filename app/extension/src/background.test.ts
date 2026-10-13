import { afterEach, expect, test, vi } from 'vitest'
import { captureKey, MENU_ID } from './platform/selection'
afterEach(() => { vi.unstubAllGlobals(); vi.resetModules() })
test('abre painel no gesto antes de ler storage, preserva seleção e serializa cliques rápidos', async () => {
  const events: string[] = []
  let click: (info: { menuItemId: string; selectionText: string; pageUrl: string }, tab: { id: number; windowId: number }) => void
  const data: Record<string, unknown> = {}
  const set = vi.fn(async (value: Record<string, unknown>) => { events.push('set'); Object.assign(data, value) })
  const get = vi.fn(async (key: string) => { events.push('get'); return { [key]: data[key] } })
  vi.stubGlobal('chrome', {
    runtime: { onInstalled: { addListener: vi.fn() }, sendMessage: vi.fn().mockResolvedValue(undefined) },
    contextMenus: { onClicked: { addListener: (fn: typeof click) => { click = fn } } },
    windows: { onRemoved: { addListener: vi.fn() } },
    sidePanel: { open: vi.fn(async () => { events.push('open') }) },
    storage: { session: { get, set } },
  })
  await import('./background')
  click!({ menuItemId: MENU_ID, selectionText: 'ação\ncom acento', pageUrl: 'https://example.org/path?secret=1' }, { id: 4, windowId: 2 })
  click!({ menuItemId: MENU_ID, selectionText: 'Segundo', pageUrl: 'https://other.org/#token' }, { id: 5, windowId: 3 })
  expect(events).toEqual(['open', 'open'])
  await vi.waitFor(() => expect(set).toHaveBeenCalledTimes(2))
  expect(data[captureKey(2)]).toMatchObject({ text: 'ação\ncom acento', source: 'example.org', windowId: 2 })
  expect(data[captureKey(3)]).toMatchObject({ text: 'Segundo', source: 'other.org', windowId: 3 })
  expect(JSON.stringify(data)).not.toContain('secret')
})
