import { readdirSync, readFileSync, mkdirSync, writeFileSync } from 'node:fs'
import { deflateRawSync } from 'node:zlib'
import { crc32 } from './binary.mjs'

const root = new URL('../dist/', import.meta.url)
const manifest = JSON.parse(readFileSync(new URL('manifest.json', root), 'utf8'))
const localApi = manifest.host_permissions.some(host => /localhost|127\.0\.0\.1/.test(host))
function files(directory, prefix = '') {
  return readdirSync(directory, { withFileTypes: true }).flatMap(file => file.isDirectory() ? files(new URL(`${file.name}/`, directory), `${prefix}${file.name}/`) : [`${prefix}${file.name}`]).sort()
}
const entries = files(root)
const records = [], central = []
let offset = 0
for (const path of entries) {
  const name = Buffer.from(path), content = readFileSync(new URL(path, root)), compressed = deflateRawSync(content), crc = crc32(content)
  const header = Buffer.alloc(30); header.writeUInt32LE(0x04034b50); header.writeUInt16LE(20, 4); header.writeUInt16LE(0x0800, 6); header.writeUInt16LE(8, 8); header.writeUInt16LE(0x21, 12)
  header.writeUInt32LE(crc, 14); header.writeUInt32LE(compressed.length, 18); header.writeUInt32LE(content.length, 22); header.writeUInt16LE(name.length, 26)
  records.push(header, name, compressed)
  const directory = Buffer.alloc(46); directory.writeUInt32LE(0x02014b50); directory.writeUInt16LE(20, 4); directory.writeUInt16LE(20, 6); directory.writeUInt16LE(0x0800, 8); directory.writeUInt16LE(8, 10); directory.writeUInt16LE(0x21, 14)
  directory.writeUInt32LE(crc, 16); directory.writeUInt32LE(compressed.length, 20); directory.writeUInt32LE(content.length, 24); directory.writeUInt16LE(name.length, 28); directory.writeUInt32LE(offset, 42)
  central.push(directory, name); offset += header.length + name.length + compressed.length
}
const directory = Buffer.concat(central), end = Buffer.alloc(22)
end.writeUInt32LE(0x06054b50); end.writeUInt16LE(entries.length, 8); end.writeUInt16LE(entries.length, 10); end.writeUInt32LE(directory.length, 12); end.writeUInt32LE(offset, 16)
const output = new URL(`../artifacts/8values-extension-${manifest.version}-${localApi ? 'local' : 'production'}.zip`, import.meta.url)
mkdirSync(new URL('../artifacts/', import.meta.url), { recursive: true })
writeFileSync(output, Buffer.concat([...records, directory, end]))
console.log(`Pacote criado: ${decodeURIComponent(output.pathname)} (${entries.length} arquivos)`)
