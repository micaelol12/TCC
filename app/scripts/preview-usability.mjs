import { createServer } from 'node:http'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const report = resolve('test-results/usability/index.html')
const server = createServer((request, response) => {
  if (request.url !== '/' && request.url !== '/index.html') { response.writeHead(404); response.end(); return }
  try {
    response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' })
    response.end(readFileSync(report))
  } catch { response.writeHead(404); response.end('Execute npm run test:usability para gerar o painel de casos.') }
})
server.listen(5188, '127.0.0.1', () => console.log('Casos de teste: http://127.0.0.1:5188/'))
server.on('error', error => { console.error(`Não foi possível abrir o painel: ${error.message}`); process.exitCode = 1 })
