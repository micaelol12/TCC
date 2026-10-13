import { expect, test } from 'vitest'
import { extensionConfig } from './buildConfig'
test('deriva URL, permissão e origem da mesma configuração', () => {
  expect(extensionConfig('development', {})).toEqual({ apiBase: 'http://127.0.0.1:8000', webBase: 'http://127.0.0.1:5173', hostPermission: 'http://127.0.0.1/*' })
  expect(extensionConfig('production', { VITE_API_BASE_URL: 'https://api.example.org/' }).hostPermission).toBe('https://api.example.org/*')
})
test.each(['', 'http://api.example.org', 'https://localhost:8000', 'https://user:password@api.example.org', 'https://api.example.org/path', 'https://api.example.org?token=secret'])('produção recusa endereço inválido %s', url => {
  expect(() => extensionConfig('production', { VITE_API_BASE_URL: url })).toThrow()
})
