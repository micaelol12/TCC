from pathlib import Path
from html import escape
import math
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent
W, H, S = 1520, 1790, 2
INK, YELLOW = '#363636', '#ffdb43'
img = Image.new('RGB', (W*S, H*S), 'white')
draw = ImageDraw.Draw(img)
font_path = 'C:/Windows/Fonts/arial.ttf'
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
       '<title>Diagrama de atividades: análise híbrida de textos e comparação com o teste 8values</title>',
       '<rect width="100%" height="100%" fill="white"/>']
root = ET.Element('mxfile', host='app.diagrams.net')
diagram = ET.SubElement(root, 'diagram', name='Código atual - modo híbrido', id='fluxo-teste')
model = ET.SubElement(diagram, 'mxGraphModel', dx=str(W), dy=str(H), grid='1', gridSize='10', page='1', pageWidth=str(W), pageHeight=str(H), pageScale='1')
cells = ET.SubElement(model, 'root')
ET.SubElement(cells, 'mxCell', id='0')
ET.SubElement(cells, 'mxCell', id='1', parent='0')
counter = 1

def cell(value, style, x, y, w, h):
    global counter
    counter += 1
    c = ET.SubElement(cells, 'mxCell', id=str(counter), value=value, style=style, vertex='1', parent='1')
    ET.SubElement(c, 'mxGeometry', x=str(x), y=str(y), width=str(w), height=str(h), **{'as': 'geometry'})
    return c

def text(x, y, lines, size=24):
    if isinstance(lines, str):
        lines = [lines]
    font = ImageFont.truetype(font_path, size*S)
    lh = size*1.23
    top = y-(len(lines)-1)*lh/2
    for i, line in enumerate(lines):
        cy = top+i*lh
        draw.text((x*S, cy*S), line, font=font, fill=INK, anchor='mm')
        svg.append(f'<text x="{x}" y="{cy}" dominant-baseline="central" text-anchor="middle" font-family="Arial, sans-serif" font-size="{size}" fill="{INK}">{escape(line)}</text>')

def label(x, y, lines, width=360, size=23):
    text(x, y, lines, size)
    n = 1 if isinstance(lines, str) else len(lines)
    cell('<br>'.join([lines] if isinstance(lines, str) else lines),
         f'text;html=1;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;strokeColor=none;fillColor=none;fontFamily=Arial;fontSize={size};fontColor={INK};',
         x-width/2, y-n*size*1.23/2, width, n*size*1.23)

def action(x, y, w, h, lines):
    font = ImageFont.truetype(font_path, 24*S)
    assert all(font.getlength(line)/S <= w-28 for line in lines), lines
    assert len(lines)*24*1.23 <= h-12, lines
    draw.rounded_rectangle((x*S,y*S,(x+w)*S,(y+h)*S), radius=18*S, fill=YELLOW)
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{YELLOW}"/>')
    text(x+w/2,y+h/2,lines)
    cell('<br>'.join(lines),f'rounded=1;arcSize=22;whiteSpace=wrap;html=1;fillColor={YELLOW};strokeColor=none;fontColor={INK};fontFamily=Arial;fontSize=24;',x,y,w,h)

def note(x, y, w, h, lines, target, side='right'):
    font = ImageFont.truetype(font_path, 21*S)
    assert all(font.getlength(line)/S <= w-24 for line in lines), lines
    assert len(lines)*21*1.23 <= h-10, lines
    fill = '#fff4ad'
    fold = 17
    pts = [(x,y),(x+w-fold,y),(x+w,y+fold),(x+w,y+h),(x,y+h)]
    source = (x+w,y+h/2) if side=='right' else (x+w/2,y+h)
    # A note association has no arrow: it annotates an activity, not a flow.
    ax,ay=source; bx,by=target
    length=math.hypot(bx-ax,by-ay)
    for start in range(0,int(length),10):
        end=min(start+4,length)
        draw.line(((ax+(bx-ax)*start/length)*S,(ay+(by-ay)*start/length)*S,
                   (ax+(bx-ax)*end/length)*S,(ay+(by-ay)*end/length)*S),fill='#777777',width=S)
    svg.append(f'<line x1="{ax}" y1="{ay}" x2="{bx}" y2="{by}" stroke="#777777" stroke-dasharray="4 6"/>')
    global counter
    counter+=1
    c=ET.SubElement(cells,'mxCell',id=str(counter),style='edgeStyle=none;endArrow=none;dashed=1;strokeColor=#777777;',edge='1',parent='1')
    g=ET.SubElement(c,'mxGeometry',relative='1',**{'as':'geometry'})
    ET.SubElement(g,'mxPoint',x=str(ax),y=str(ay),**{'as':'sourcePoint'})
    ET.SubElement(g,'mxPoint',x=str(bx),y=str(by),**{'as':'targetPoint'})
    draw.polygon([(a*S,b*S) for a,b in pts],fill=fill)
    draw.line(((x+w-fold)*S,y*S,(x+w-fold)*S,(y+fold)*S,(x+w)*S,(y+fold)*S),fill='#d6c668',width=S)
    svg.append(f'<polygon points="{" ".join(f"{a},{b}" for a,b in pts)}" fill="{fill}"/>')
    svg.append(f'<polyline points="{x+w-fold},{y} {x+w-fold},{y+fold} {x+w},{y+fold}" fill="none" stroke="#d6c668"/>')
    text(x+w/2,y+h/2,lines,21)
    cell('<br>'.join(lines),f'shape=note;size=17;whiteSpace=wrap;html=1;fillColor={fill};strokeColor=none;fontFamily=Arial;fontSize=21;fontColor={INK};',x,y,w,h)

def diamond(x,y,r=20):
    pts=[(x,y-r),(x+r,y),(x,y+r),(x-r,y)]
    draw.polygon([(a*S,b*S) for a,b in pts], fill=INK)
    svg.append(f'<polygon points="{" ".join(f"{a},{b}" for a,b in pts)}" fill="{INK}"/>')
    cell('',f'rhombus;fillColor={INK};strokeColor={INK};',x-r,y-r,2*r,2*r)

def terminal(x,y,final=False):
    r=16
    if final:
        draw.ellipse(((x-r-6)*S,(y-r-6)*S,(x+r+6)*S,(y+r+6)*S),outline=INK,width=2*S)
        svg.append(f'<circle cx="{x}" cy="{y}" r="22" fill="white" stroke="{INK}" stroke-width="2"/>')
    draw.ellipse(((x-r)*S,(y-r)*S,(x+r)*S,(y+r)*S),fill=INK)
    svg.append(f'<circle cx="{x}" cy="{y}" r="16" fill="{INK}"/>')
    cell('',f'{"shape=endState" if final else "ellipse"};fillColor={INK};strokeColor={INK};',x-(22 if final else r),y-(22 if final else r),44 if final else 32,44 if final else 32)

def edge(points):
    draw.line([(x*S,y*S) for x,y in points],fill=INK,width=2*S)
    x,y=points[-1]; a,b=points[-2]
    ang=math.atan2(y-b,x-a)
    arrow=[(x,y),(x-12*math.cos(ang)+5*math.sin(ang),y-12*math.sin(ang)-5*math.cos(ang)),(x-12*math.cos(ang)-5*math.sin(ang),y-12*math.sin(ang)+5*math.cos(ang))]
    draw.polygon([(a*S,b*S) for a,b in arrow],fill=INK)
    svg.append(f'<polyline points="{" ".join(f"{a},{b}" for a,b in points)}" fill="none" stroke="{INK}" stroke-width="2"/>')
    svg.append(f'<polygon points="{" ".join(f"{a},{b}" for a,b in arrow)}" fill="{INK}"/>')
    global counter
    counter += 1
    c=ET.SubElement(cells,'mxCell',id=str(counter),style=f'edgeStyle=none;rounded=0;html=1;endArrow=block;endFill=1;strokeWidth=2;strokeColor={INK};',edge='1',parent='1')
    g=ET.SubElement(c,'mxGeometry',relative='1',**{'as':'geometry'})
    ET.SubElement(g,'mxPoint',x=str(points[0][0]),y=str(points[0][1]),**{'as':'sourcePoint'})
    ET.SubElement(g,'mxPoint',x=str(x),y=str(y),**{'as':'targetPoint'})
    if len(points)>2:
        arr=ET.SubElement(g,'Array',**{'as':'points'})
        for a,b in points[1:-1]: ET.SubElement(arr,'mxPoint',x=str(a),y=str(b))

# This diagram describes the existing medium/hybrid mode, not a proposed
# relevance-first implementation. Each chunk follows the framed subflow.
label(760,35,'Análise híbrida de textos e comparação com o teste 8values',1450,28)
label(760,75,'Modo com revisão (medium) — fluxo funcional do código atual',1400,22)

# Visually group the per-chunk subactivity, including concurrent execution.
draw.rounded_rectangle((30*S,355*S,1480*S,915*S),radius=12*S,outline='#aaaaaa',width=S)
svg.append('<rect x="30" y="355" width="1450" height="560" rx="12" fill="none" stroke="#aaaaaa"/>')
cell('', 'rounded=1;arcSize=4;fillColor=none;strokeColor=#aaaaaa;',30,355,1450,560)
label(1195,380,'Para cada trecho (em paralelo)',530,22)

# Connectors precede activities to keep their ends clean.
edge([(650,141),(650,165)])
edge([(650,241),(650,275)])
edge([(650,351),(650,430)])
edge([(650,530),(650,595)])
edge([(670,615),(1010,615)])
edge([(650,635),(650,805)])
edge([(1215,665),(1215,845),(850,845)])
edge([(650,885),(650,975)])
edge([(650,1069),(650,1120)])
edge([(650,1200),(650,1260)])
edge([(670,1280),(1010,1280)])
edge([(1420,1280),(1448,1280)])
edge([(650,1300),(650,1380)])
edge([(650,1474),(650,1550)])
edge([(650,1634),(650,1708)])

terminal(650,125)
label(585,125,'Início',100)
action(450,165,400,76,['Recebe o texto do usuário'])
action(450,275,400,76,['Divide o texto em trechos'])
action(450,430,400,100,['Avalia relevância e polaridade','dos quatro eixos com JEV'])
note(65,410,330,130,['TypeSafe · jev-1.13.0','Uma chamada por trecho,','com as duas perguntas','para cada eixo.'],(450,480))
diamond(650,615)
label(305,615,['Há eixos com baixa','confiança ou falha?'],460)
label(825,592,'Sim',75)
label(690,675,'Não',75)
action(1010,565,410,100,['Revisa relevância e polaridade','dos eixos sinalizados com LLM'])
note(1020,410,400,120,['Maritaca · Sabiá 4 (padrão)','Substitui as duas decisões;','os demais eixos mantêm JEV.'],(1215,565),side='bottom')
action(450,805,400,80,['Busca e verifica evidências','conforme a configuração'])
note(65,795,330,100,['Auditoria com JEV,','quando habilitada.','Não altera as pontuações.'],(450,845))
label(900,940,'Após concluir todos os trechos',460,22)
action(450,975,400,94,['Agrega as pontuações válidas','pela média de cada eixo'])
note(45,975,350,120,['Somente relevância confirmada','e nível válido (escala 0–100).','Sem valores: sem estimativa.'],(450,1022))
action(450,1120,400,80,['Apresenta a análise por eixo'])
diamond(650,1280)
label(300,1280,['Resultado do teste','8values disponível?'],440)
label(825,1257,'Não',75)
label(690,1340,'Sim',75)
action(1010,1233,410,94,['Oferece adicionar o resultado','do teste 8values'])
terminal(1470,1280,True)
label(1470,1328,'Fim',80)
action(450,1380,400,94,['Compara o texto e o teste','nos eixos com estimativa'])
note(40,1370,355,120,['Diferença de pontuação','por eixo, na escala 0–100.','Demais eixos: sem base','para comparar.'],(450,1427))
action(450,1550,400,84,['Apresenta o resultado','da comparação ao usuário'])
terminal(650,1730,True)
label(710,1730,'Fim',80)

svg.append('</svg>')
(OUT/'diagrama_teste_corrigido.svg').write_text('\n'.join(svg),encoding='utf-8')
img.save(OUT/'diagrama_teste_corrigido.png',dpi=(240,240))
ET.indent(root)
ET.ElementTree(root).write(OUT/'diagrama_teste_corrigido.drawio',encoding='utf-8',xml_declaration=True)
print('Gerados: PNG, SVG e drawio.')
