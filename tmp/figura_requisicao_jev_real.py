from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

out = Path(__file__).resolve().parents[1] / 'output' / 'figuras'
out.mkdir(parents=True, exist_ok=True)
request = {
    'model': 'jev-preview',
    'state': {'state': 'Defendemos a tributação progressiva.'},
    'questions': {
        'posicao_tributacao': {
            'type': 'choice',
            'instructions': 'Qual posição o trecho expressa em relação à tributação progressiva?',
            'criteria': {
                'apoia': 'Defende a medida',
                'rejeita': 'Rejeita a medida',
                'sem_posicao': 'Não expressa posição'
            }
        }
    }
}
response = {
    'model': 'jev-1.14.0',
    'answers': {
        'posicao_tributacao': {
            'type': 'choice',
            'choice': 'apoia',
            'confidence': 1.0,
            'probabilities': {'apoia': 1.0, 'rejeita': 0.0, 'sem_posicao': 0.0}
        }
    },
    'usage': {'input_tokens': 364, 'output_tokens': 49}
}
request_text = json.dumps(request, ensure_ascii=False, indent=2)
# Break only between a JSON key and its string value; preserve valid JSON.
request_text = request_text.replace(
    '"instructions": "Qual', '"instructions":\n        "Qual')
assert json.loads(request_text) == request
response_text = json.dumps(response, ensure_ascii=False, indent=2)
for name, data in [('requisicao_jev_real.json', request), ('resposta_jev_real.json', response)]:
    (out / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

plt.rcParams.update({'font.family': 'DejaVu Sans', 'svg.fonttype': 'none'})
fig = plt.figure(figsize=(16, 8), facecolor='white')
ink, accent = '#172B3A', '#185B73'
code_style = dict(fontsize=11.5, fontfamily='DejaVu Sans Mono', linespacing=1.3)

def measure(text, **style):
    item = fig.text(0, 0, text, **style)
    fig.canvas.draw()
    bounds = item.get_window_extent(fig.canvas.get_renderer())
    item.remove()
    return bounds.width / fig.dpi, bounds.height / fig.dpi

pad, gap, margin = .16, .22, .025
header_height = measure('REQUISIÇÃO', fontsize=14, weight='bold')[1]
sizes = [measure(code, **code_style) for code in (request_text, response_text)]
widths = [width + 2 * pad for width, _ in sizes]
heights = [height + header_height + .13 + 2 * pad for _, height in sizes]
canvas_width = sum(widths) + gap + 2 * margin
canvas_height = max(heights) + 2 * margin
fig.set_size_inches(canvas_width, canvas_height)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, canvas_width)
ax.set_ylim(0, canvas_height)
ax.axis('off')

def panel(x, width, height, title, code):
    top = canvas_height - margin
    ax.add_patch(FancyBboxPatch(
        (x, top-height), width, height,
        boxstyle='round,pad=0,rounding_size=0.06',
        linewidth=1, edgecolor='#CBD4DB', facecolor='#F7F9FB'))
    ax.text(x+pad, top-pad, title, color=accent, fontsize=14, weight='bold', va='top')
    ax.text(x+pad, top-pad-header_height-.13, code, color=ink, va='top', **code_style)

panel(margin, widths[0], heights[0], 'REQUISIÇÃO', request_text)
panel(margin+widths[0]+gap, widths[1], heights[1], 'RESPOSTA', response_text)
for ext in ['svg', 'png']:
    fig.savefig(out / f'requisicao_resposta_jev_real.{ext}', dpi=200, bbox_inches='tight', facecolor='white')
print(out / 'requisicao_resposta_jev_real.png')
