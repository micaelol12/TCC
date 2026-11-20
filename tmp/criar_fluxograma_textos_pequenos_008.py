from pathlib import Path
import json
import math
from html import escape
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'runs/testes_textos/20261112T010422966692Z/textos_pequenos_008'
data = json.loads((DEST / 'resultado.json').read_text(encoding='utf-8'))
record = data['registros'][0]
W, H = 2480, 2620
im = Image.new('RGB', (W, H), '#ffffff')
draw = ImageDraw.Draw(im)
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
       '<rect width="100%" height="100%" fill="white"/>']
INK, MUTED, LINE = '#172b40', '#52687b', '#9aaebf'
BLUE, BLUE_BG = '#265c96', '#eef5fc'
AMBER, AMBER_BG = '#986019', '#fff7e8'
GREEN, GREEN_BG = '#16705e', '#eaf7f2'
GRAY_BG = '#f3f6f8'
fonts = {}

def font(size, bold=False):
    key = size, bold
    if key not in fonts:
        fonts[key] = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf' if bold else 'C:/Windows/Fonts/segoeui.ttf', size)
    return fonts[key]

def text(x, y, value, size=30, color=INK, bold=False, center=True):
    f = font(size, bold)
    width = draw.textlength(value, font=f)
    draw.text((x-width/2 if center else x, y), value, font=f, fill=color)
    # SVG baseline corresponds to the font ascender used by Pillow.
    ascent = f.getmetrics()[0]
    svg.append(f'<text x="{x}" y="{y+ascent}" text-anchor="{"middle" if center else "start"}" font-family="Segoe UI, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{escape(value)}</text>')

def wrap(value, size, max_width, bold=False):
    lines = []
    for paragraph in value.split('\n'):
        current = ''
        for word in paragraph.split():
            proposed = f'{current} {word}'.strip()
            if draw.textlength(proposed, font=font(size, bold)) > max_width and current:
                lines.append(current)
                current = word
            else:
                current = proposed
        lines.append(current)
    return lines

def paragraph(x, y, value, size=30, max_width=460, color=INK, bold=False, center=True, line_height=None):
    lines = wrap(value, size, max_width, bold)
    step = line_height or round(size * 1.34)
    for i, line in enumerate(lines):
        text(x, y+i*step, line, size, color, bold, center)
    return len(lines)*step

def rect(x, y, w, h, fill, stroke=LINE, radius=22, line_width=2):
    draw.rounded_rectangle((x, y, x+w, y+h), radius=radius, fill=fill, outline=stroke, width=line_width)
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="{line_width}"/>')

def card(cx, y, w, h, title, body='', fill=GRAY_BG, stroke=LINE, title_color=INK, body_size=29):
    rect(cx-w/2, y, w, h, fill, stroke)
    title_lines = wrap(title, 32, w-38, True)
    body_lines = wrap(body, body_size, w-42) if body else []
    total = len(title_lines)*43 + (14 if body else 0) + len(body_lines)*round(body_size*1.34)
    assert total <= h-12, (title, total, h)
    ty = y+(h-total)/2
    for line in title_lines:
        text(cx, ty, line, 32, title_color, True)
        ty += 43
    if body:
        ty += 14
        for line in body_lines:
            text(cx, ty, line, body_size, MUTED)
            ty += round(body_size*1.34)

def line(points, color=LINE, width=4, arrow=False):
    draw.line(points, fill=color, width=width, joint='curve')
    svg.append(f'<polyline points="{" ".join(f"{x},{y}" for x,y in points)}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"/>')
    if arrow:
        x, y = points[-1]
        px, py = points[-2]
        ang = math.atan2(y-py, x-px)
        tri = [(x,y), (x-16*math.cos(ang-.48), y-16*math.sin(ang-.48)), (x-16*math.cos(ang+.48), y-16*math.sin(ang+.48))]
        draw.polygon(tri, fill=color)
        svg.append(f'<polygon points="{" ".join(f"{a},{b}" for a,b in tri)}" fill="{color}"/>')

def diamond(cx, y, w=450, h=190):
    pts = [(cx,y), (cx+w/2,y+h/2), (cx,y+h), (cx-w/2,y+h/2)]
    draw.polygon(pts, fill=AMBER_BG)
    draw.line(pts+[pts[0]], fill=AMBER, width=3)
    svg.append(f'<polygon points="{" ".join(f"{x},{yy}" for x,yy in pts)}" fill="{AMBER_BG}" stroke="{AMBER}" stroke-width="3"/>')
    text(cx, y+48, 'Há gatilho de', 30, AMBER, True)
    text(cx, y+91, 'reavaliação?', 30, AMBER, True)

text(100, 52, 'Caminho da classificação', 64, bold=True, center=False)
text(100, 137, 'textos_pequenos_008  •  execução 20261112T010422966692Z', 29, MUTED, center=False)
rect(100, 202, 2280, 180, BLUE_BG, '#c7d9eb')
text(1240, 218, 'TEXTO DE ENTRADA', 26, BLUE, True)
paragraph(1240, 268, '“'+data['original']['texto']+'”', 33, 2140)

line([(1240,382),(1240,430)], arrow=True)
card(1240,430,1120,110,'Segmentação','1 trecho  •  160 caracteres  •  46 tokens', BLUE_BG, '#c7d9eb', BLUE)
line([(1240,540),(1240,585)], arrow=True)
card(1240,585,1420,110,'Classificação inicial pelo JEV','jev-1.13.0  •  quatro eixos  •  regra: polo_primeiro', BLUE_BG, '#c7d9eb', BLUE)

centers = [355,945,1535,2125]
line([(1240,695),(1240,740)])
line([(centers[0],740),(centers[-1],740)])
axes = [('economic','ECONÔMICO','Igualdade ↔ Mercado'),('diplomatic','DIPLOMÁTICO','Globo ↔ Nação'),('state','ESTATAL','Liberdade ↔ Autoridade'),('society','SOCIAL','Progresso ↔ Tradição')]
for cx,(axis,title,poles) in zip(centers,axes):
    line([(cx,740),(cx,785)], arrow=True)
    card(cx,785,530,110,title,poles,BLUE_BG,'#c7d9eb',BLUE,28)
    line([(cx,895),(cx,935)], arrow=True)
    d = record['eixos_jev'][axis]
    if axis in ('economic','society'):
        title,body = 'JEV: irrelevante','Sem evidência no eixo.\nMargem de relevância: 1,00.'
    elif axis == 'diplomatic':
        title,body = 'JEV: Nação moderado','Relevante  •  nível −2\nPolo B: 0,99\nSuporte da intensidade: 0,404.'
    else:
        title,body = 'JEV: sem posição','Relevante  •  nível 0\nMargem de relevância: 0,40\nMargem entre grupos: 0,17.'
    card(cx,935,530,220,title,body,body_size=28)
    line([(cx,1155),(cx,1190)], arrow=True)
    diamond(cx,1190)
    line([(cx,1380),(cx,1465)], color=AMBER if record['motivos_fallback'][axis] else LINE, arrow=True)
    text(cx+45,1400,'SIM' if record['motivos_fallback'][axis] else 'NÃO',26,AMBER if record['motivos_fallback'][axis] else MUTED,True)
    if axis in ('economic','society'):
        card(cx,1465,530,220,'Manter decisão do JEV','Nenhum gatilho registrado.\nSem reavaliação pelo LLM.',body_size=29)
        line([(cx,1685),(cx,2070)],arrow=True)
    elif axis == 'diplomatic':
        card(cx,1465,530,220,'LLM: confirma nível −2','sabia-4\nIntensidade ambígua:\n0,404 < limiar 0,50.',AMBER_BG,AMBER,AMBER,29)
        line([(cx,1685),(cx,1740)],arrow=True)
        card(cx,1740,530,275,'Verificar evidência','Citação presente no texto.\nParecer JEV: sustenta.\nConfiança semântica: 0,98.\n“...recusando subordinação”',GREEN_BG,GREEN,GREEN,28)
        line([(cx,2015),(cx,2070)],arrow=True)
    else:
        card(cx,1465,530,220,'LLM: irrelevante','sabia-4\nRelevância: 0,40 < 0,60.\nDireção: 0,17 < 0,20.',AMBER_BG,AMBER,AMBER,29)
        line([(cx,1685),(cx,2070)],arrow=True)
    final=record['eixos'][axis]
    if final['relevante']:
        card(cx,2070,530,145,'Nação — moderado','Nível −2  •  origem: LLM',GREEN_BG,GREEN,GREEN,28)
    else:
        card(cx,2070,530,145,'Sem evidência','Sem nível e sem pontuação',body_size=28)
    line([(cx,2215),(cx,2260)])

line([(centers[0],2260),(centers[-1],2260)])
line([(1240,2260),(1240,2305)],color=GREEN,arrow=True)
rect(100,2305,2280,180,GREEN_BG,GREEN)
text(1240,2323,'RESULTADO FINAL EXPLORATÓRIO',29,GREEN,True)
text(1240,2372,'Diplomático: Globo 25%  /  Nação 75%  •  Rótulo por faixa: “Patriota”',37,GREEN,True)
text(1240,2428,'Econômico, estatal e social: sem evidência disponível.',30,MUTED)
text(100,2510,'Base: um único trecho. Percentuais representam a escala ordinal; não são probabilidades.',27,MUTED,center=False)
text(100,2554,'Fonte: resultado.json, decisoes.csv e evidencias.csv da execução indicada.',25,MUTED,center=False)

svg.append('</svg>')
stem='fluxograma_classificacao'
if (DEST/f'{stem}.png').exists() or (DEST/f'{stem}.svg').exists():
    version=2
    while (DEST/f'{stem}_v{version}.png').exists() or (DEST/f'{stem}_v{version}.svg').exists():
        version+=1
    stem=f'{stem}_v{version}'
im.save(DEST/f'{stem}.png',dpi=(300,300))
(DEST/f'{stem}.svg').write_text('\n'.join(svg),encoding='utf-8')
print(json.dumps({'png':str(DEST/f'{stem}.png'),'svg':str(DEST/f'{stem}.svg'),'size':[W,H]},ensure_ascii=False))
