import config from '../../../api/analysis-config.json'
import type { OrdinalScale } from '../domain/ordinalScale'

// Tests derive their data from the same definition file as the API.
const nine = structuredClone(config.escala) as OrdinalScale
const five = structuredClone(nine)
const indices = [0, 2, 4, 6, 8]
const keys = ['polo_B_forte', 'polo_B_moderado', 'sem_posicao', 'polo_A_moderado', 'polo_A_forte']
five.id = 'ordinal_5_v1'
five.niveis = indices.map((index, offset) => ({ ...nine.niveis[index], chave: keys[offset], codigo: offset - 2, rotulo: keys[offset].replaceAll('_', ' '), valor: offset / 4 }))
five.rubricas_por_eixo = Object.fromEntries(Object.entries(nine.rubricas_por_eixo).map(([axis, rubrics]) => [axis, Object.fromEntries(indices.map((index, offset) => [keys[offset], rubrics[nine.niveis[index].chave]]))])) as OrdinalScale['rubricas_por_eixo']
export const scaleFixtures: OrdinalScale[] = [five, nine]
