from pathlib import Path

# Reuse only the drawing helpers, before the previous diagram's layout starts.
helper_path = Path(__file__).with_name('criar_fluxograma_padrao_referencia.py')
helpers = helper_path.read_text(encoding='utf-8').split("label(370,22,")[0]
exec(compile(helpers, str(helper_path), 'exec'))

S, W, H = 3, 1100, 1450
im = Image.new('RGB', (W*S,H*S), 'white')
draw = ImageDraw.Draw(im)
fonts = {}
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W*S}" height="{H*S}" viewBox="0 0 {W} {H}">', '<rect width="100%" height="100%" fill="white"/>']

def box(x,y,w,h,value,size=16):
    rectangle(x,y,w,h,YELLOW,r=10)
    assert len(words(value,size,w-26))*size*1.22 <= h-12, value
    label(x+w/2,y+h/2,value,size,w-26)

def memo(x,y,w,h,value,size=14):
    note(x,y,w,h,value,size)

label(550,25,'Caminho da classificação — textos_pequenos_008',22,1050)
label(550,56,'Execução 20261112T010422966692Z',13,1000,color='#666666')
circle(520,89,7)
label(482,89,'Início',13,48)
edge([(520,96),(520,120)])
box(390,120,260,60,'Recebe o texto de entrada')
memo(20,110,320,155,'TEXTO COMPLETO\n“'+data['original']['texto']+'”',14)
edge([(340,150),(390,150)],False,True)
edge([(520,180),(520,230)])
box(390,230,260,60,'Segmenta o texto\nResultado: um único trecho')
memo(20,280,320,55,'1 trecho · 160 caracteres · 46 tokens',14)
edge([(340,307),(365,307),(365,260),(390,260)],False,True)

rectangle(10,350,1080,705,'white','#d4d4d4',6)
label(920,366,'Classificação por eixo no trecho',13,320)
edge([(520,290),(520,390)])
box(390,390,260,85,'Avalia os quatro eixos\nJEV: jev-1.13.0\nRegra: polo_primeiro',15)
memo(20,390,320,190,'ECONÔMICO · Igualdade ↔ Mercado\nJEV: irrelevante; sem evidência.\nMargem de relevância: 1,00.\n\nSOCIAL · Progresso ↔ Tradição\nJEV: irrelevante; sem evidência.\nMargem de relevância: 1,00.',14)
edge([(340,432),(390,432)],False,True)
memo(740,390,320,215,'DIPLOMÁTICO · Globo ↔ Nação\nJEV: relevante; Nação moderado.\nNível −2; polo B: 0,99.\nSuporte da intensidade: 0,404.\n\nESTATAL · Liberdade ↔ Autoridade\nJEV: relevante; sem posição; nível 0.\nMargem de relevância: 0,40.\nMargem entre grupos: 0,17.',14)
edge([(650,432),(740,432)],False,True)

edge([(520,475),(520,641)])
polygon([(520,641),(529,650),(520,659),(511,650)],INK)
label(294,650,'Há gatilho de reavaliação?',15,300)
edge([(529,650),(740,650)])
label(634,633,'Sim',13,60)
box(740,620,320,65,'Reavalia os eixos sinalizados\nLLM: sabia-4',16)
memo(740,727,320,205,'DIPLOMÁTICO\nIntensidade ambígua:\n0,404 < limiar 0,50.\nLLM confirma o nível −2.\n\nESTATAL\nRelevância ambígua: 0,40 < 0,60.\nDireção ambígua: 0,17 < 0,20.\nLLM considera irrelevante.',14)
edge([(900,685),(900,727)],False,True)
edge([(1060,652),(1075,652),(1075,987),(650,987)])

edge([(520,659),(520,955)])
label(549,687,'Não',13,45)
memo(20,730,320,115,'ECONÔMICO E SOCIAL\nNenhum gatilho registrado.\nManter decisão do JEV.\nSem reavaliação pelo LLM.',14)
edge([(340,787),(520,787)],False,True)
box(390,955,260,65,'Verifica a evidência\ndo eixo diplomático',16)
memo(20,925,320,115,'Citação presente no texto.\nParecer JEV: sustenta.\nConfiança semântica: 0,98.\n“...recusando subordinação”',14)
edge([(340,987),(390,987)],False,True)

edge([(520,1020),(520,1130)])
box(390,1130,260,75,'Consolida a classificação\nfinal dos quatro eixos',16)
memo(20,1100,320,150,'ECONÔMICO, ESTATAL E SOCIAL\nSem evidência disponível.\nSem nível e sem pontuação.\n\nOrigem: JEV para econômico e social; LLM para estatal.',14)
edge([(340,1167),(390,1167)],False,True)
memo(740,1090,320,175,'DIPLOMÁTICO\nNação — moderado; nível −2.\nOrigem: LLM.\n\nGlobo: 25% · Nação: 75%.\nRótulo exploratório por faixa:\n“Patriota”.',14)
edge([(650,1167),(740,1167)],False,True)
edge([(520,1205),(520,1280)])
circle(520,1290,10,'white',INK)
circle(520,1290,7)
label(556,1290,'Fim',13,45)

memo(205,1330,690,65,'Base: um único trecho. Percentuais representam a escala ordinal; não são probabilidades.\nResultado final e rótulo por faixa são exploratórios.',14)
label(550,1421,'Fonte: resultado.json, decisoes.csv e evidencias.csv da execução indicada.',12,1060,color='#666666')
svg.append('</svg>')
stem='fluxograma_classificacao_dados_completos_layout_amarelo'
if (DEST/f'{stem}.png').exists() or (DEST/f'{stem}.svg').exists():
    index=2
    while (DEST/f'{stem}_v{index}.png').exists() or (DEST/f'{stem}_v{index}.svg').exists():
        index+=1
    stem=f'{stem}_v{index}'
im.save(DEST/f'{stem}.png',dpi=(300,300))
(DEST/f'{stem}.svg').write_text('\n'.join(svg),encoding='utf-8')
print(DEST/f'{stem}.png')
print(DEST/f'{stem}.svg')
