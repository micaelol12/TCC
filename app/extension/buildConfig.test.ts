import { expect, test } from 'vitest'
import { extensionConfig } from './buildConfig'
test('deriva URL, permissão e origem da mesma configuração', () => {
  expect(extensionConfig('development', {})).toEqual({ apiBase: 'http://127.0.0.1:8000', webBase: 'http://127.0.0.1:5173', hostPermission: 'http://127.0.0.1/*', webMatchPattern: 'http://127.0.0.1/*' })
  expect(extensionConfig('production', { VITE_API_BASE_URL: 'https://api.example.org/' }).hostPermission).toBe('https://api.example.org/*')
})
test.each(['', 'http://api.example.org', 'https://localhost:8000', 'https://user:password@api.example.org', 'https://api.example.org/path', 'https://api.example.org?token=secret'])('produção recusa endereço inválido %s', url => {
  expect(() => extensionConfig('production', { VITE_API_BASE_URL: url })).toThrow()
})
test('Lab usa portas próprias e recusa publicação remota ou em produção', () => {
  const lab = extensionConfig('lab', {})
  expect(lab.apiBase).toBe('http://127.0.0.1:8001')
  expect(lab.webBase).toBe('http://127.0.0.1:5174')
  expect(() => extensionConfig('lab', { VITE_API_BASE_URL: 'https://api.example.org' })).toThrow()
  expect(() => extensionConfig('lab', { VITE_WEB_BASE_URL: 'https://web.example.org' })).toThrow()
  expect(() => extensionConfig('production', { VITE_API_BASE_URL: 'https://api.example.org', VITE_APP_VARIANT: 'lab' })).toThrow()
})
