"""Adaptadores de dados existentes; R3/R4 em METODOLOGIA.md.

Não coleta tweets nem inventa textos a partir de IDs; exige hidratação existente.
"""
import csv
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import zipfile

import numpy as np

from .protocolo import connected_groups, digest, validate_corpus, write_json

TARGETS = {"bo": "Jair Bolsonaro", "lu": "Luiz Inácio Lula da Silva", "cl": "hidroxicloroquina",
           "co": "vacina Sinovac", "gl": "Rede Globo", "ig": "igreja"}

BRMORAL_TARGETS = {
    "gay-marriage": "casamento entre pessoas do mesmo sexo",
    "gun-control": "legalização do porte de armas",
    "abortion": "legalização do aborto", "death-penalty": "pena de morte",
    "drugs": "legalização das drogas", "criminal-age": "redução da maioridade penal",
    "racial-quotas": "cotas raciais", "church-tax": "isenção de impostos para igrejas",
}


def import_brmoral(archive, output, seed=42):
    """R9/README v5.10: opiniões por tema, sem usar ideologia do autor.

    Santos e Paraboni (2019), §3.1, DOI 10.26615/978-954-452-056-4_123:
    0/1 contra, 2/3 neutro, 4/5 favor. Exclui neutros, textos/escores ausentes;
    confere st.* contra s.*. Adaptação R4: componentes autor/duplicata em
    64/16/20 por grupos, semente fixa, sem otimizar distribuição ou resultados.
    """
    with zipfile.ZipFile(archive) as z:
        names = [n for n in z.namelist() if n.endswith('.csv')]
        if len(names) != 1:
            raise ValueError('Esperado exatamente um CSV BRmoral')
        records = list(csv.DictReader(io.StringIO(z.read(names[0]).decode('cp1252')), delimiter=';'))
    rows, exclusions, seen = [], Counter(), set()
    for record in records:
        author = record['sid'].strip()
        if not author or author in seen:
            raise ValueError('Autor ausente/duplicado')
        seen.add(author)
        for topic, target in BRMORAL_TARGETS.items():
            text, score = record['t.' + topic].strip(), record['s.' + topic].strip()
            if not text or text.lower() == 'na' or score.lower() == 'na':
                exclusions['missing_text_or_score'] += 1
                continue
            if score not in {'0', '1', '2', '3', '4', '5'}:
                raise ValueError('Escore desconhecido')
            label = 'against' if int(score) < 2 else 'neutral' if int(score) < 4 else 'for'
            if record['st.' + topic] != label:
                raise ValueError('Classe e escore discordam')
            if label == 'neutral':
                exclusions['neutral'] += 1
                continue
            rows.append({'id': f'{author}:{topic}', 'author_id': author, 'text': text,
                         'target': target, 'label': 'favor' if label == 'for' else label,
                         'label_source': 'corpus_publico'})
    groups = connected_groups(rows)
    unique = sorted(set(groups))
    if len(unique) < 5:
        raise ValueError('Poucos componentes para três partições')
    shuffled = np.random.default_rng(seed).permutation(unique)
    ntest, ndev = max(1, round(.2 * len(unique))), max(1, round(.16 * len(unique)))
    test, dev = set(shuffled[:ntest]), set(shuffled[ntest:ntest + ndev])
    rows = [{**r, 'family_id': g, 'split': 'test' if g in test else 'dev' if g in dev else 'train'}
            for r, g in zip(rows, groups)]
    meta = {'name': 'BRmoral', 'version': '5.10-sept2019', 'license': 'CC-BY-4.0',
            'source': 'https://ivandreparaboni.wixsite.com/research/downloads',
            'annotation_unit': 'text_target', 'author_ids_unavailable': False,
            'label_definition': 's=0/1 against; s=4/5 favor; st verified; s=2/3 excluded',
            'split_policy': '64/16/20 train/dev/test by connected author/duplicate components',
            'seed': seed, 'participants': len(records), 'exclusions': dict(exclusions),
            'archive_sha256': hashlib.sha256(Path(archive).read_bytes()).hexdigest(),
            'target_mapping': BRMORAL_TARGETS, 'groups': len(unique),
            'largest_group': max(Counter(groups).values())}
    audit = validate_corpus(rows, meta)
    audit['distribution'] = dict(Counter(f"{r['split']}|{r['target']}|{r['label']}" for r in rows))
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'corpus.jsonl').write_text('\n'.join(json.dumps(r, ensure_ascii=False) for r in rows) + '\n', encoding='utf-8')
    write_json(output / 'corpus.meta.json', meta)
    write_json(output / 'audit.json', audit)
    return audit


def split_development(rows, seed=42, fraction=.2):
    """R4: separa componentes de treino para dev sem mover o teste oficial.

    Falha em colisões globais com teste, não as elimina silenciosamente. Não
    otimiza a divisão por resultados; proporção aproximada por grupos.
    """
    if not 0 < fraction < 1:
        raise ValueError("Fração de desenvolvimento inválida")
    if any(r["split"] not in {"train", "test"} for r in rows):
        raise ValueError("Entrada deve conter apenas treino/teste oficiais")
    groups = connected_groups(rows)
    sets = {}
    for row, g in zip(rows, groups):
        sets.setdefault(g, set()).add(row["split"])
    if any(len(v) > 1 for v in sets.values()):
        raise ValueError("Componentes compartilhados com teste oficial; registrar e definir novo protocolo")
    available = sorted(g for g, s in sets.items() if s == {"train"})
    if len(available) < 2:
        raise ValueError("Treino precisa de pelo menos dois grupos")
    rng = np.random.default_rng(seed)
    shuffled = rng.permutation(available)
    count = max(1, min(len(available) - 1, round(len(available) * fraction)))
    dev = set(shuffled[:count])
    return [{**r, "split": "dev" if g in dev else r["split"], "family_id": g} for r, g in zip(rows, groups)]


def import_ustancebr(archive, hydrated, output, seed=42):
    """R3/R4 + README oficial UstanceBR r3: join exato de IDs, for -> favor.

    hydrated é JSONL com id/text/author_id. Ausências são contadas como perda de
    hidratação; não cria gabarito novo. A seleção perdida limita o benchmark.
    """
    texts = {}
    for line in Path(hydrated).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        key = str(row["id"]).lstrip("_")
        if key in texts:
            raise ValueError("ID de hidratação duplicado")
        if not row.get("author_id") or not row.get("text", "").strip():
            raise ValueError("Texto e autoria são necessários para particionar sem vazamento")
        texts[key] = row
    rows, missing, counts = [], [], {}
    with zipfile.ZipFile(archive) as z:
        for path in sorted(z.namelist()):
            name = Path(path).name
            if not name.startswith("r3_") or not name.endswith("_ids.csv"):
                continue
            _, topic, split, _ = name.split("_")
            if topic not in TARGETS or split not in {"train", "test"}:
                raise ValueError(f"Arquivo não reconhecido: {name}")
            table = list(csv.DictReader(io.StringIO(z.read(path).decode("utf-8-sig")), delimiter=";"))
            counts[name] = len(table)
            for record in table:
                key = record["Tweet_ID"].lstrip("_")
                if record["Polarity"] not in {"for", "against"}:
                    raise ValueError("Rótulo desconhecido; documentar exclusão antes de importar")
                if key not in texts:
                    missing.append({"id": key, "target": topic, "split": split})
                    continue
                text = texts[key]
                rows.append({"id": f"{topic}:{key}", "text": text["text"], "author_id": str(text["author_id"]),
                             "target": TARGETS[topic], "label": "favor" if record["Polarity"] == "for" else "against",
                             "split": split, "label_source": "corpus_publico"})
    rows = split_development(rows, seed)
    metadata = {"name": "UstanceBR", "version": "r3_hydrated_subset", "license": "CC-BY-4.0",
                "source": "https://drive.google.com/drive/folders/1qThfcIe0HjwVbsDVgkot-AqgnXoJdB0K",
                "annotation_unit": "text_target", "label_definition": "for -> favor; against -> against",
                "split_policy": "teste r3 preservado; 20% dos componentes do treino para dev",
                "seed": seed, "author_ids_unavailable": False, "source_counts": counts,
                "hydration_missing": len(missing), "hydration_sha256": digest(texts)}
    audit = validate_corpus(rows, metadata)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output / "corpus.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    write_json(output / "corpus.meta.json", metadata)
    write_json(output / "audit.json", {**audit, "missing": missing})
    return audit
