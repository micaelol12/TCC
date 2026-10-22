import assert from 'node:assert/strict'
import { existsSync, readdirSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { inflateRawSync } from 'node:zlib'

function files(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap(item => item.isDirectory() ? files(resolve(directory, item.name)) : [resolve(directory, item.name)])
}
const sentinels = ['lab-test-typesafe-secret-UNIQUE', 'lab-test-maritaca-secret-UNIQUE', 'lab-test-gemini-secret-UNIQUE']
for (const directory of ['web/dist-lab', 'extension/dist-lab']) {
  assert(existsSync(directory), `Build ausente: ${directory}`)
  for (const file of files(directory)) {
    const data = readFileSync(file).toString('utf8')
    assert(!sentinels.some(secret => data.includes(secret)), 'Credencial fictícia encontrada no build.')
    assert(!/\.env(?:\.|$)/.test(file), 'Arquivo de ambiente encontrado no build.')
  }
}
const manifest = JSON.parse(readFileSync('extension/dist-lab/manifest.json', 'utf8'))
assert.equal(manifest.name, '8values Lab')
assert(manifest.host_permissions.every(host => /^https?:\/\/(127\.0\.0\.1|localhost)\//.test(host)))
const zipPath = `extension/artifacts/8values-extension-${manifest.version}-lab.zip`
assert(existsSync(zipPath), 'ZIP Lab ausente.')
const zip = readFileSync(zipPath)
let cursor = 0, entries = 0
while (zip.readUInt32LE(cursor) === 0x04034b50) {
  const size = zip.readUInt32LE(cursor + 18), nameLength = zip.readUInt16LE(cursor + 26), extraLength = zip.readUInt16LE(cursor + 28)
  const name = zip.subarray(cursor + 30, cursor + 30 + nameLength).toString('utf8')
  assert(!/(^|\/)\.env/.test(name), 'Arquivo de ambiente encontrado no ZIP.')
  const start = cursor + 30 + nameLength + extraLength
  const content = inflateRawSync(zip.subarray(start, start + size)).toString('utf8')
  assert(!sentinels.some(secret => content.includes(secret)), 'Credencial fictícia encontrada no ZIP.')
  cursor = start + size; entries++
}
console.log(`Artefatos Lab verificados; ${entries} entradas no ZIP, sem credenciais fictícias ou arquivos de ambiente.`)
