import { createHash } from 'node:crypto'
import { readFileSync } from 'node:fs'

// Canonical LF bytes keep the instrument hash stable in Windows checkouts.
const content = readFileSync(new URL('../../shared/src/data/questions.json', import.meta.url), 'utf8').replaceAll('\r\n', '\n')
const scoring = readFileSync(new URL('../../shared/src/domain/quizScoring.ts', import.meta.url), 'utf8')
const hash = createHash('sha256').update(content).digest('hex')
if (!scoring.includes(`QUESTION_HASH = '${hash}'`)) {
  throw new Error('questions.json mudou. Revise o instrumento e atualize QUESTION_HASH antes de compilar.')
}
console.log(`Questionário verificado: ${JSON.parse(content).length} perguntas, SHA-256 ${hash}`)
