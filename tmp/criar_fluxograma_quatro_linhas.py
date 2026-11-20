from pathlib import Path

helper_path = Path(__file__).with_name('criar_fluxograma_padrao_referencia.py')
exec(compile(helper_path.read_text(encoding='utf-8').split("label(370,22,")[0], str(helper_path), 'exec'))

S, W, H = 2, 1800, 1710
im = Image.new('RGB', (W*S,H*S), 'white')
draw = ImageDraw.Draw(im)
fonts = {}
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W*S}" height="{H*S}" viewBox="0 0 {W} {H}">', '<rect width="100%" height="100%" fill="white"/>']

def box(x,y,w,h,value,size=20):
    rectangle(x,y,w,h,YELLOW,r=12)
    assert len(words(value,size,w-24))*size*1.22 <= h-14, value
    label(x+w/2,y+h/2,value,size,w-24)

label(900,28,'Caminho da classificação — quatro eixos em linhas separadas',28,1700)
label(900,64,'textos_pequenos_008 · execução 20261112T010422966692Z',17,1700,color='#666666')
circle(900,100,7)
label(855,100,'Início',16,60)
edge([(900,107),(900,130)])
box(680,130,440,55,'Recebe o texto de entrada',21)
note(45,110,570,150,'TEXTO COMPLETO\n“'+data['original']['texto']+'”',18)
edge([(615,157),(680,157)],False,True)
edge([(900,185),(900,225)])
box(680,225,440,55,'Segmenta o texto em um único trecho',20)
note(1190,215,510,75,'1 trecho · 160 caracteres · 46 tokens',19)
edge([(1120,252),(1190,252)],False,True)
edge([(900,280),(900,320)])
box(680,320,440,65,'Classifica os quatro eixos com JEV\njev-1.13.0 · regra: polo_primeiro',20)

ys=[545,805,1065,1325]
edge([(900,385),(900,412),(35,412),(35,ys[-1])],False)
label(1200,412,'Cada linha mostra o caminho observado em um eixo',17,900,color='#666666')
axes=[
    ('economic','ECONÔMICO','Igualdade ↔ Mercado'),
    ('diplomatic','DIPLOMÁTICO','Globo ↔ Nação'),
    ('state','ESTATAL','Liberdade ↔ Autoridade'),
    ('society','SOCIAL','Progresso ↔ Tradição'),
]
for cy,(axis,name,poles) in zip(ys,axes):
    rectangle(65,cy-110,1670,220,'white','#d4d4d4',7)
    edge([(35,cy),(85,cy)])
    box(85,cy-50,250,100,name+'\n'+poles,19)
    edge([(335,cy),(380,cy)])
    if axis in ('economic','society'):
        initial='JEV: irrelevante\nSem evidência no eixo.\nMargem de relevância: 1,00.'
    elif axis=='diplomatic':
        initial='JEV: relevante\nNação moderado · nível −2\nPolo B: 0,99\nSuporte da intensidade: 0,404.'
    else:
        initial='JEV: relevante\nSem posição · nível 0\nMargem de relevância: 0,40\nMargem entre grupos: 0,17.'
    note(380,cy-80,270,160,initial,18)
    edge([(650,cy),(693,cy)])
    polygon([(705,cy-12),(717,cy),(705,cy+12),(693,cy)],INK)
    label(705,cy-39,'Reavaliar?',17,120)
    edge([(717,cy),(770,cy)])
    label(745,cy+26,'Sim' if record['motivos_fallback'][axis] else 'Não',17,70)
    if axis in ('economic','society'):
        box(770,cy-70,270,140,'Manter decisão do JEV\nNenhum gatilho registrado.\nSem reavaliação pelo LLM.',18)
        edge([(1040,cy),(1420,cy)])
    elif axis=='diplomatic':
        box(770,cy-85,270,170,'LLM: sabia-4\nIntensidade ambígua:\n0,404 < limiar 0,50.\nConfirma o nível −2.',18)
        edge([(1040,cy),(1080,cy)])
        note(1080,cy-90,300,180,'VERIFICAÇÃO DA EVIDÊNCIA\nCitação presente no texto.\nParecer JEV: sustenta.\nConfiança semântica: 0,98.\n“...recusando subordinação”',17)
        edge([(1380,cy),(1420,cy)])
    else:
        box(770,cy-85,270,170,'LLM: sabia-4\nRelevância ambígua:\n0,40 < limiar 0,60.\nDireção ambígua:\n0,17 < limiar 0,20.\nConsidera irrelevante.',17)
        edge([(1040,cy),(1420,cy)])
    if axis=='diplomatic':
        final='Nação — moderado\nNível −2 · origem: LLM'
    else:
        final='Sem evidência\nSem nível e sem pontuação\nOrigem: '+('LLM' if axis=='state' else 'JEV')
    box(1420,cy-65,290,130,final,19)
    edge([(1710,cy),(1760,cy)],False)

edge([(1760,ys[0]),(1760,1470),(900,1470),(900,1510)])
box(210,1510,1380,100,'RESULTADO FINAL EXPLORATÓRIO\nDiplomático: Globo 25% / Nação 75% · Rótulo por faixa: “Patriota”\nEconômico, estatal e social: sem evidência disponível.',22)
edge([(900,1610),(900,1630)])
circle(900,1640,10,'white',INK)
circle(900,1640,7)
label(938,1640,'Fim',16,45)
label(900,1677,'Base: um único trecho. Percentuais representam a escala ordinal; não são probabilidades.',17,1700,color='#666666')
label(900,1700,'Fonte: resultado.json, decisoes.csv e evidencias.csv da execução indicada.',14,1700,color='#666666')
svg.append('</svg>')
stem='fluxograma_classificacao_quatro_eixos_em_linhas'
if (DEST/f'{stem}.png').exists() or (DEST/f'{stem}.svg').exists():
    index=2
    while (DEST/f'{stem}_v{index}.png').exists() or (DEST/f'{stem}_v{index}.svg').exists():
        index+=1
    stem=f'{stem}_v{index}'
im.save(DEST/f'{stem}.png',dpi=(300,300))
(DEST/f'{stem}.svg').write_text('\n'.join(svg),encoding='utf-8')
print(DEST/f'{stem}.png')
print(DEST/f'{stem}.svg')
