from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

out = Path(__file__).resolve().parents[1] / 'output' / 'figuras'
out.mkdir(parents=True, exist_ok=True)
request = {
    'model': 'jev-1.13.0',
    'state': 'Defendemos a tributação progressiva.',
    'questions': {
        'posicao': {
            'type': 'choice',
            'instructions': 'Qual a posição sobre essa tributação?',
            'criteria': {
                'apoia': 'Defende a medida.',
                'rejeita': 'Rejeita a medida.',
                'sem_posicao': 'Não expressa posição.'
            }
        }
    }
}
response = {
    'model': 'jev-1.13.0',
    'answers': {
        'posicao': {
            'type': 'choice',
            'choice': 'apoia',
            'confidence': 0.85,
            'probabilities': {
                'apoia': 0.90,
                'rejeita': 0.06,
                'sem_posicao': 0.04
            }
        }
    }
}
assert abs(sum(response['answers']['posicao']['probabilities'].values()) - 1) < 1e-12
plt.rcParams.update({'font.family': 'DejaVu Sans', 'svg.fonttype': 'none'})
fig = plt.figure(figsize=(17, 8.5), facecolor='white')
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')
ink, accent = '#172B3A', '#185B73'
ax.text(.035, .952, 'Exemplo de requisição e resposta do JEV', color=ink, fontsize=23, weight='bold', va='top')
ax.text(.035, .898, 'Classificação da posição expressa em um trecho por meio de uma pergunta Choice', color='#526371', fontsize=13, va='top')

def panel(x, width, title, subtitle, payload):
    ax.add_patch(FancyBboxPatch((x, .16), width, .66, boxstyle='round,pad=0.009,rounding_size=0.012', linewidth=1.1, edgecolor='#CBD4DB', facecolor='#F7F9FB'))
    ax.text(x+.017, .788, title, color=accent, fontsize=15, weight='bold', va='top')
    ax.text(x+.017, .75, subtitle, color='#526371', fontsize=10.5, va='top')
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    ax.text(x+.017, .705, text, color=ink, fontsize=10.8, fontfamily='DejaVu Sans Mono', linespacing=1.35, va='top')

panel(.035, .445, 'REQUISIÇÃO', 'Corpo JSON · POST /v1/systemone', request)
panel(.60, .365, 'RESPOSTA', 'Campos selecionados · valores fictícios', response)
ax.add_patch(FancyArrowPatch((.492, .50), (.585, .50), arrowstyle='-|>', mutation_scale=20, linewidth=1.8, color=accent))
ax.text(.538, .553, 'JEV', ha='center', va='center', color=accent, fontsize=15, weight='bold')
ax.text(.538, .445, 'avaliação', ha='center', va='center', color='#526371', fontsize=10)
ax.text(.035, .10, 'Fonte: elaboração própria, com base na documentação da TypeSafe (Choice).', color=ink, fontsize=11, va='top')
ax.text(.035, .065, 'Exemplo didático: a resposta foi construída para ilustrar a interface; não representa uma chamada executada à API.', color='#526371', fontsize=10.5, va='top')
fig.savefig(out / 'requisicao_resposta_jev.svg', bbox_inches='tight', facecolor='white')
fig.savefig(out / 'requisicao_resposta_jev.png', dpi=180, bbox_inches='tight', facecolor='white')
print(out / 'requisicao_resposta_jev.png')
