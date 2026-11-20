from pathlib import Path
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[2]
src = ROOT/'output/resultados_tcc.md'
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.top_margin = sec.bottom_margin = Cm(2)
sec.left_margin = sec.right_margin = Cm(2)

normal = doc.styles['Normal']
normal.font.name = 'Times New Roman'
normal.font.size = Pt(11)
normal.font.color.rgb = RGBColor(0,0,0)
fmt = normal.paragraph_format
fmt.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
fmt.first_line_indent = Cm(.8)
fmt.space_after = Pt(5)
fmt.line_spacing = 1.08
fmt.widow_control = True
for name in ['Title','Heading 1','Heading 2']:
    s=doc.styles[name]
    s.font.name='Times New Roman'
    s.font.color.rgb=RGBColor(0,0,0)
    s.font.size=Pt(11)
    s.font.bold=True
    s.paragraph_format.first_line_indent=Cm(0)
    s.paragraph_format.space_before=Pt(10 if name!='Title' else 0)
    s.paragraph_format.space_after=Pt(7)
    s.paragraph_format.keep_with_next=True
    s.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.LEFT
doc.styles['Title'].font.size=Pt(12)
for style in doc.styles:
    for border in list(style.element.iter(qn('w:pBdr'))):
        border.getparent().remove(border)
for name in ['Normal','Title','Heading 1','Heading 2']:
    rpr=doc.styles[name].element.get_or_add_rPr()
    fonts=rpr.find(qn('w:rFonts'))
    if fonts is not None:
        for key in list(fonts.attrib):
            if key.endswith('Theme'): del fonts.attrib[key]
        for key in ['ascii','hAnsi','eastAsia','cs']: fonts.set(qn('w:'+key),'Times New Roman')

def add_table(lines):
    rows = [[c.strip() for c in l.strip().strip('|').split('|')] for l in lines]
    rows = [r for r in rows if not all(set(c)<=set('-: ') for c in r)]
    table = doc.add_table(rows=len(rows), cols=len(rows[0]))
    table.autofit=False
    widths = {6:[2.15,2.0,2.65,2.45,3.85,3.9], 3:([10.0,2.6,4.4] if 'Conteúdo' in rows[0][0] else [8.1,4.45,4.45])}[len(rows[0])]
    for column,width in zip(table.columns,widths): column.width=Cm(width)
    pr=table._tbl.tblPr
    borders=OxmlElement('w:tblBorders')
    for edge in ['top','left','bottom','right','insideH','insideV']:
        el=OxmlElement('w:'+edge);el.set(qn('w:val'),'single');el.set(qn('w:sz'),'4');el.set(qn('w:color'),'666666');borders.append(el)
    pr.append(borders)
    for i,values in enumerate(rows):
        trpr=table.rows[i]._tr.get_or_add_trPr()
        no_split=OxmlElement('w:cantSplit');trpr.append(no_split)
        if i==0:
            repeat=OxmlElement('w:tblHeader');trpr.append(repeat)
        for j,value in enumerate(values):
            cell=table.cell(i,j);cell.width=Cm(widths[j])
            p=cell.paragraphs[0]
            p.paragraph_format.first_line_indent=Cm(0)
            p.paragraph_format.space_before=Pt(3)
            p.paragraph_format.space_after=Pt(3)
            p.paragraph_format.line_spacing=1
            p.paragraph_format.keep_with_next=(i<len(rows)-1)
            p.alignment=WD_ALIGN_PARAGRAPH.LEFT if j==0 else WD_ALIGN_PARAGRAPH.CENTER
            run=p.add_run(value);run.font.size=Pt(9.5);run.bold=(i==0)
            if i==0:
                shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'E8E8E8');cell._tc.get_or_add_tcPr().append(shade)
            cell.vertical_alignment=1
    return table

lines=src.read_text(encoding='utf-8').splitlines()
i=0
while i<len(lines):
    line=lines[i].strip()
    if not line: i+=1; continue
    if line.startswith('|'):
        block=[]
        while i<len(lines) and lines[i].strip().startswith('|'):
            block.append(lines[i]);i+=1
        add_table(block)
        continue
    if line.startswith('# '):
        p=doc.add_paragraph(line[2:],style='Title')
    elif line.startswith('## '):
        p=doc.add_paragraph(line[3:],style='Heading 1')
    elif line.startswith('Tabela '):
        p=doc.add_paragraph(line)
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent=Cm(0)
        p.paragraph_format.keep_with_next=True
        p.paragraph_format.space_before=Pt(5)
        p.paragraph_format.space_after=Pt(4)
        p.runs[0].font.size=Pt(10)
    elif line.startswith(('Fonte:','Nota:')):
        p=doc.add_paragraph(line)
        p.paragraph_format.first_line_indent=Cm(0)
        p.paragraph_format.line_spacing=1
        p.paragraph_format.space_after=Pt(6)
        p.runs[0].font.size=Pt(9)
    else:
        doc.add_paragraph(line)
    i+=1

doc.core_properties.title='Resultados da análise de textos políticos'
doc.core_properties.subject='Seção de resultados do TCC'
doc.core_properties.author=''
doc.core_properties.keywords='8values, resultados, JEV, Sabiá'
out=ROOT/'output/resultados_tcc.docx'
doc.save(out)
print(out)
print('Palavras aproximadas:',len(src.read_text(encoding='utf-8').split()))
