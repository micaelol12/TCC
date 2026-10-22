import { mkdirSync, writeFileSync } from 'node:fs'
import { deflateSync } from 'node:zlib'
import { crc32 } from './binary.mjs'

const glyph = ['01110', '11011', '11011', '01110', '11011', '11011', '01110']
function chunk(type, bytes) {
  const name = Buffer.from(type)
  const length = Buffer.alloc(4); length.writeUInt32BE(bytes.length)
  const crc = Buffer.alloc(4); crc.writeUInt32BE(crc32(Buffer.concat([name, bytes])))
  return Buffer.concat([length, name, bytes, crc])
}
const directory = new URL('../public/icons/', import.meta.url)
mkdirSync(directory, { recursive: true })
for (const size of [16, 48, 128]) {
  const pixels = Buffer.alloc(size * (1 + size * 4))
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const index = y * (1 + size * 4) + 1 + x * 4
    const gx = Math.floor((x / size - .265) / .47 * 5)
    const gy = Math.floor((y / size - .17) / .66 * 7)
    const white = gx >= 0 && gx < 5 && gy >= 0 && gy < 7 && glyph[gy][gx] === '1'
    const radius = size * .18
    const dx = Math.max(radius - x, 0, x - (size - radius - 1))
    const dy = Math.max(radius - y, 0, y - (size - radius - 1))
    pixels.set(white ? [255, 255, 255, 255] : [37, 36, 32, dx * dx + dy * dy > radius * radius ? 0 : 255], index)
  }
  const header = Buffer.alloc(13); header.writeUInt32BE(size, 0); header.writeUInt32BE(size, 4); header[8] = 8; header[9] = 6
  const png = Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]), chunk('IHDR', header), chunk('IDAT', deflateSync(pixels)), chunk('IEND', Buffer.alloc(0))])
  writeFileSync(new URL(`${size}.png`, directory), png)
}
