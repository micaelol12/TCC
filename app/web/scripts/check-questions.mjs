import { createHash } from 'node:crypto'
import { readFileSync } from 'node:fs'

const content = readFileSync(new URL('../src/data/questions.json', import.meta.url))
const scoring = readFileSync(new URL('../src/domain/quizScoring.ts', import.meta.url), 'utf8')
const hash = createHash('sha256').update(content).digest('hex')
if (!scoring.includes(`QUESTION_HASH = '${hash}'`)) {
  throw new Error('questions.json mudou. Revise o instrumento e atualize QUESTION_HASH antes de compilar.')
}
console.log(`Questionário verificado: ${JSON.parse(content).length} perguntas, SHA-256 ${hash}`)
