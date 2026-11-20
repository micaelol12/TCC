from pathlib import Path
from html import escape
import math
import json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'runs/testes_textos/20261112T010422966692Z/textos_pequenos_008'
data = json.loads((DEST / 'resultado.json').read_text(encoding='utf-8'))
record = data['registros'][0]
assert record['eixos']['diplomatic']['nivel'] == -2
assert not any(record['eixos'][k]['relevante'] for k in ('economic', 'state', 'society'))

S, W, H = 4, 740, 960
im = Image.new('RGB', (W*S, H*S), 'white')
draw = ImageDraw.Draw(im)
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W*S}" height="{H*S}" viewBox="0 0 {W} {H}">', '<rect width="100%" height="100%" fill="white"/>']
YELLOW, NOTE, INK, GRAY = '#ffde3b', '#fff4a8', '#383838', '#777777'
fonts = {}

def font(size):
    if size not in fonts:
        fonts[size] = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', round(size*S))
    return fonts[size]

def words(value, size, width):
    lines = []
    for p in value.split('\n'):
        line = ''
        for word in p.split():
            trial = (line+' '+word).strip()
            if draw.textlength(trial, font=font(size))/S > width and line:
                lines.append(line)
                line = word
            else:
                line = trial
        lines.append(line)
    return lines

def label(cx, cy, value, size=12, width=200, color=INK):
    lines = words(value, size, width)
    step = size*1.22
    top = cy-len(lines)*step/2
    for i, line in enumerate(lines):
        tw = draw.textlength(line, font=font(size))
        # Use ascender positioning consistently in the PNG and editable SVG.
        asc = font(size).getmetrics()[0]/S
        baseline = top + i*step + size
        draw.text((cx*S-tw/2, (baseline-asc)*S), line, font=font(size), fill=color)
        svg.append(f'<text x="{cx}" y="{baseline}" text-anchor="middle" font-family="Arial, sans-serif" font-size="{size}" fill="{color}">{escape(line)}</text>')

def rectangle(x,y,w,h,fill='white',stroke=None,r=0):
    draw.rounded_rectangle((x*S,y*S,(x+w)*S,(y+h)*S), radius=r*S, fill=fill, outline=stroke, width=round(S*1.3))
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke or "none"}" stroke-width="1.3"/>')

def polygon(points,fill,stroke=None):
    draw.polygon([(round(x*S),round(y*S)) for x,y in points],fill=fill)
    if stroke:
        draw.line([(round(x*S),round(y*S)) for x,y in points+[points[0]]],fill=stroke,width=S)
    svg.append(f'<polygon points="{" ".join(f"{x},{y}" for x,y in points)}" fill="{fill}" stroke="{stroke or "none"}"/>')

def edge(points,arrow=True,dotted=False,color=GRAY):
    if dotted:
        for a,b in zip(points,points[1:]):
            length=math.dist(a,b)
            for p in range(0,round(length),5):
                q=min(p+2,length)
                draw.line([(S*(a[0]+(b[0]-a[0])*p/length),S*(a[1]+(b[1]-a[1])*p/length)),(S*(a[0]+(b[0]-a[0])*q/length),S*(a[1]+(b[1]-a[1])*q/length))],fill='#b9b9b9',width=3)
    else:
        draw.line([(x*S,y*S) for x,y in points],fill=color,width=4)
    svg.append(f'<polyline points="{" ".join(f"{x},{y}" for x,y in points)}" fill="none" stroke="{"#b9b9b9" if dotted else color}" stroke-width="1" {"stroke-dasharray="+chr(34)+"2 3"+chr(34) if dotted else ""}/>')
    if arrow:
        x,y=points[-1]
        a,b=points[-2]
        ang=math.atan2(y-b,x-a)
        polygon([(x,y),(x-6*math.cos(ang-.4),y-6*math.sin(ang-.4)),(x-6*math.cos(ang+.4),y-6*math.sin(ang+.4))],color)

def process(x,y,w,h,value):
    rectangle(x,y,w,h,YELLOW,r=9)
    lines=words(value,12,w-20)
    assert len(lines)*12*1.22 <= h-10, value
    label(x+w/2,y+h/2,value,12,w-20)

def note(x,y,w,h,value,size=10.8):
    fold=9
    polygon([(x,y),(x+w-fold,y),(x+w,y+fold),(x+w,y+h),(x,y+h)],NOTE)
    polygon([(x+w-fold,y),(x+w-fold,y+fold),(x+w,y+fold)],'#eee4a0')
    lines=words(value,size,w-16)
    assert len(lines)*size*1.22 <= h-10, (value,lines)
    label(x+w/2,y+h/2,value,size,w-16)

def circle(cx,cy,r,fill=INK,outline=None):
    draw.ellipse(((cx-r)*S,(cy-r)*S,(cx+r)*S,(cy+r)*S),fill=fill,outline=outline,width=3)
    svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{outline or "none"}"/>')

label(370,22,'Classificação — textos_pequenos_008',18,700)
circle(315,60,7)
label(281,60,'Início',11,45)
edge([(315,67),(315,90)])
process(210,90,210,46,'Recebe o texto do usuário')
note(26,82,170,105,'Texto sobre pressão norte-americana, soberania e recusa de subordinação.\n160 caracteres · 46 tokens.')
edge([(196,112),(210,112)],False,True)
edge([(315,136),(315,165)])
process(210,165,210,46,'Divide o texto em trechos\nResultado: um único trecho')

rectangle(12,235,714,385,'white','#d4d4d4',5)
label(600,248,'Para cada trecho (em paralelo)',10.5,235)
edge([(315,211),(315,275)])
process(210,275,210,60,'Avalia relevância e polaridade\ndos quatro eixos com JEV')
note(26,265,170,112,'TypeSafe · jev-1.13.0\nEconômico e social: irrelevantes.\nDiplomático: Nação moderado.\nEstatal: sem posição.')
edge([(196,305),(210,305)],False,True)
note(490,267,216,115,'Maritaca · sabia-4\nDiplomático: intensidade ambígua; mantém nível −2.\nEstatal: relevância e direção ambíguas; torna irrelevante.\nDemais eixos mantêm o JEV.')
edge([(598,382),(598,395)],False,True)

edge([(315,335),(315,416)])
polygon([(315,416),(324,425),(315,434),(306,425)],INK)
label(123,425,'Há eixos com baixa\nconfiança ou falha?',11.5,180)
edge([(324,425),(490,425)])
label(405,412,'Sim',11,45)
process(490,395,216,60,'Revisa relevância e polaridade\ndos eixos sinalizados com LLM')
edge([(315,434),(315,555)])
label(337,458,'Não',11,38)
process(210,555,210,55,'Busca e verifica evidências\nconforme a configuração')
edge([(598,455),(598,582),(420,582)])
note(26,540,170,70,'Auditoria com JEV: sustenta.\nConfiança semântica: 0,98.\nCitação presente no texto.')
edge([(196,575),(210,575)],False,True)

edge([(315,610),(315,675)])
label(437,645,'Após concluir o trecho',10.5,190)
process(210,675,210,55,'Agrega as pontuações válidas\npela média de cada eixo')
note(26,667,170,84,'Somente relevância confirmada e nível válido (escala 0–100).\nSem evidência: sem estimativa.')
edge([(196,705),(210,705)],False,True)
edge([(315,730),(315,790)])
process(210,790,210,60,'Apresenta a classificação\nfinal por eixo')
note(490,759,216,122,'Resultado exploratório\nDiplomático: Nação moderado (−2).\nGlobo: 25% · Nação: 75%.\nRótulo por faixa: Patriota.\nEconômico, estatal e social: sem evidência.')
edge([(420,820),(490,820)],False,True)
edge([(315,850),(315,891)])
circle(315,900,10,'white',INK)
circle(315,900,7)
label(346,900,'Fim',11,40)
label(370,936,'Fonte: resultado.json · Base: um trecho · Percentuais da escala ordinal',10,700,color='#666666')

svg.append('</svg>')
stem='fluxograma_classificacao_padrao_referencia'
if (DEST/f'{stem}.png').exists():
    index=2
    while (DEST/f'{stem}_v{index}.png').exists():
        index+=1
    stem=f'{stem}_v{index}'
im.save(DEST/f'{stem}.png',dpi=(300,300))
(DEST/f'{stem}.svg').write_text('\n'.join(svg),encoding='utf-8')
print(DEST/f'{stem}.png')
print(DEST/f'{stem}.svg')
