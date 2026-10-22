"""Gera o dataset sintético de tool-calling (determinístico, sem rede, sem dados de terceiros).

Anti-leakage por construção:
  * as ENTIDADES (cidade, assunto, caminho, operandos) são particionadas em
    train/val/test ANTES de gerar os pedidos — nenhuma entidade aparece em dois splits;
  * o último template de cada ferramenta (`HOLDOUT_TEMPLATE`) só existe no test —
    mede generalização para uma formulação nunca vista;
  * `validation.validate_dataset` verifica tudo isso depois e falha se algo vazar.

Uso:  python -m model_adaptation.datasets.prepare_dataset --seed 0
"""
from __future__ import annotations

import argparse
import hashlib
import random
from typing import Any, Dict, List, Tuple

from model_adaptation.common import DATA_DIR, canonical_target, write_json
from model_adaptation.datasets.validation import validate_dataset

# ---------------------------------------------------------------- entidades
CITIES = [
    "Curitiba", "Recife", "Salvador", "Fortaleza", "Manaus", "Belém", "Goiânia", "Campinas",
    "Santos", "Florianópolis", "Porto Alegre", "Belo Horizonte", "Vitória", "Natal", "Maceió",
    "João Pessoa", "Cuiabá", "Campo Grande", "Aracaju", "Teresina", "São Luís", "Palmas",
    "Londrina", "Joinville", "Uberlândia", "Ribeirão Preto", "Sorocaba", "Niterói", "Petrópolis",
    "Blumenau", "Caxias do Sul", "Pelotas", "Maringá", "Juiz de Fora", "Anápolis", "Macapá",
    "Boa Vista", "Rio Branco", "Porto Velho", "Foz do Iguaçu",
]
TOPICS = [
    "energia solar", "computação quântica", "reforma tributária", "mercado de carbono",
    "vacinas de mRNA", "carros elétricos", "inteligência artificial generativa", "fusão nuclear",
    "hidrogênio verde", "cibersegurança bancária", "agricultura de precisão", "6G",
    "baterias de estado sólido", "Pix parcelado", "open finance", "robôs humanoides",
    "edição genética CRISPR", "telescópio James Webb", "satélites Starlink", "criptografia pós-quântica",
    "internet das coisas", "impressão 3D de casas", "dessalinização da água", "reciclagem de baterias",
    "turismo espacial", "blockchain na saúde", "drones de entrega", "realidade aumentada",
    "microeletrônica no Brasil", "biocombustíveis", "smart grids", "metaverso corporativo",
    "visão computacional industrial", "LGPD e dados pessoais", "computação neuromórfica", "bioplásticos",
    "ensino híbrido", "telemedicina", "cidades inteligentes", "mobilidade urbana sustentável",
]
DIRS = ["docs", "data", "relatorios", "notas", "projetos/alfa", "projetos/beta", "backup", "entrada"]
STEMS = ["resumo", "relatorio", "ata", "plano", "orcamento", "cronograma", "metricas", "contrato",
         "analise", "proposta"]
EXTS = ["md", "txt", "csv", "json"]

NONE_PROMPTS = [
    "Olá, tudo bem?", "Bom dia!", "Boa tarde, como vai?", "Boa noite!", "Oi, pessoal!", "E aí, beleza?",
    "Tudo certo por aí?", "Fala comigo!", "Alô, tem alguém aí?", "Opa, de volta por aqui.",
    "Salve!", "Oi de novo.", "Obrigado pela ajuda!", "Valeu, ajudou bastante.", "Muito obrigado!",
    "Agradeço a atenção.", "Brigadão!", "Isso resolveu, obrigado.", "Perfeito, era isso mesmo.",
    "Show de bola, obrigado.", "Quem é você?", "Qual é o seu nome?", "O que você consegue fazer?",
    "Você é uma pessoa de verdade?", "Quem te criou?", "Como você funciona?", "Você fala português?",
    "Você aprende com as conversas?", "Conta uma piada.", "Me diz uma curiosidade qualquer.",
    "Fala algo motivador.", "Escreve um haicai sobre o mar.", "Inventa um nome para um gato.",
    "Me dá uma frase de efeito.", "Recomenda um passatempo.", "Você prefere café ou chá?",
    "Qual sua cor favorita?", "Gosta de música?", "Acha que vai dar tudo certo?",
    "Estou meio cansado hoje.", "Que dia complicado!", "Hoje o dia foi puxado.",
    "Estou animado com o fim de semana.", "Preciso de uma pausa.", "Sem ideias para o almoço, e você?",
    "Vamos conversar um pouco?", "Pode me ouvir um instante?", "Só passei para dizer oi.",
    "Tchau, até logo!", "Até amanhã!", "Falou, valeu!", "Boa semana para você!", "Descanse bem!",
    "Nos falamos depois.", "Preciso sair agora, tchau.", "Foi um prazer conversar.", "Cuide-se!",
    "Estou só testando, pode ignorar.", "Testando, um, dois, três.", "Isso é só um teste de conversa.",
]

# ---------------------------------------------------------------- templates
# O ÚLTIMO template de cada lista é o HOLDOUT (aparece só no test).
CALC_TEMPLATES = [
    "Quanto é {a} {opw} {b}?",
    "Calcule {a} {opw} {b}",
    "Me diz o resultado de {a} {sym} {b}",
    "Faz a conta: {a}{sym}{b}",
    "Preciso saber quanto dá {a} {opw} {b}, pode calcular?",
]
WEATHER_TEMPLATES = [
    "Como está o tempo em {city}?",
    "Qual a previsão do tempo para {city} hoje?",
    "Está chovendo em {city} agora?",
    "Me fala a temperatura em {city}",
    "Vou viajar para {city} amanhã, como está o clima por lá?",
]
SEARCH_TEMPLATES = [
    "Pesquise na web sobre {topic}",
    "Procure informações sobre {topic}",
    "Busque notícias recentes de {topic}",
    "Quero saber mais sobre {topic}, pode pesquisar?",
    "Dá uma olhada na internet: o que há de novo em {topic}?",
]
FILE_TEMPLATES = [
    "Leia o arquivo {path}",
    "Abra {path} e me mostre o conteúdo",
    "O que está escrito em {path}?",
    "Mostre o conteúdo do arquivo {path}",
    "Preciso do texto que está salvo em {path}, pode ler?",
]
OPS = [("+", "mais"), ("-", "menos"), ("*", "vezes"), ("/", "dividido por")]

SPLIT_SIZES = {
    "train": {"calculator": 120, "weather_api": 100, "web_search": 100, "file_reader": 100, "none": 40},
    "val": {"calculator": 15, "weather_api": 12, "web_search": 12, "file_reader": 12, "none": 6},
    "test": {"calculator": 30, "weather_api": 24, "web_search": 24, "file_reader": 24, "none": 12},
}
FRACTIONS = {"train": 0.70, "val": 0.10, "test": 0.20}


def _all_paths() -> List[str]:
    return [f"{d}/{s}_{n:02d}.{e}" for d in DIRS for s in STEMS[:5] for n, e in [(1, EXTS[0]), (2, EXTS[1]), (3, EXTS[2]), (4, EXTS[3])]][:200]


def _partition(items: List[str], rng: random.Random) -> Dict[str, List[str]]:
    items = sorted(items)
    rng.shuffle(items)
    n = len(items)
    n_train, n_val = int(n * FRACTIONS["train"]), max(1, int(n * FRACTIONS["val"]))
    return {"train": items[:n_train], "val": items[n_train:n_train + n_val], "test": items[n_train + n_val:]}


def _bucket(a: int, op: str, b: int) -> str:
    """Partição determinística dos operandos (independe da seed → sem vazamento entre seeds)."""
    h = int(hashlib.sha256(f"{a}|{op}|{b}".encode()).hexdigest(), 16) % 10
    return "train" if h < 7 else ("val" if h == 7 else "test")


def _templates_for(split: str, templates: List[str]) -> List[Tuple[int, str]]:
    idx = list(enumerate(templates))
    return idx if split == "test" else idx[:-1]


def _make_record(split: str, n: int, tool: str, args: Dict[str, Any], prompt: str, template_id: int) -> Dict[str, Any]:
    return {
        "id": f"{split}-{n:04d}", "split": split, "prompt": prompt, "tool": tool, "args": args,
        "target": canonical_target(tool, args), "template_id": template_id,
    }


def build(seed: int = 0) -> Dict[str, List[Dict[str, Any]]]:
    rng = random.Random(seed)
    cities = _partition(CITIES, rng)
    topics = _partition(TOPICS, rng)
    paths = _partition(_all_paths(), rng)
    nones = _partition(NONE_PROMPTS, rng)
    out: Dict[str, List[Dict[str, Any]]] = {}

    for split, counts in SPLIT_SIZES.items():
        records: List[Dict[str, Any]] = []
        seen = set()

        def add(tool: str, args: Dict[str, Any], prompt: str, tid: int) -> bool:
            if prompt in seen:
                return False
            seen.add(prompt)
            records.append(_make_record(split, len(records), tool, args, prompt, tid))
            return True

        def holdout_quota(count: int) -> int:
            return count // 3 if split == "test" else 0

        for tool, count in counts.items():
            made, tries = 0, 0
            tmpls = {"calculator": CALC_TEMPLATES, "weather_api": WEATHER_TEMPLATES,
                     "web_search": SEARCH_TEMPLATES, "file_reader": FILE_TEMPLATES}.get(tool)
            hq = holdout_quota(count) if tmpls else 0
            while made < count:
                tries += 1
                if tries > 20000:
                    raise RuntimeError(f"não consegui gerar {count} exemplos únicos de {tool} em {split}")
                if tool == "none":
                    prompt = rng.choice(nones[split])
                    made += add("none", {}, prompt, -1)
                    continue
                if split == "test" and made < hq:
                    tid = len(tmpls) - 1                      # força o template holdout
                elif split == "test":
                    tid = rng.randrange(len(tmpls) - 1)
                else:
                    tid = rng.randrange(len(tmpls) - 1)
                tmpl = tmpls[tid]
                if tool == "calculator":
                    a, b = rng.randint(2, 999), rng.randint(2, 99)
                    sym, opw = OPS[rng.randrange(len(OPS))]
                    if _bucket(a, sym, b) != split:
                        continue
                    args = {"expression": f"{a}{sym}{b}"}
                    made += add(tool, args, tmpl.format(a=a, b=b, sym=sym, opw=opw), tid)
                elif tool == "weather_api":
                    city = rng.choice(cities[split])
                    made += add(tool, {"city": city}, tmpl.format(city=city), tid)
                elif tool == "web_search":
                    topic = rng.choice(topics[split])
                    made += add(tool, {"query": topic}, tmpl.format(topic=topic), tid)
                else:
                    path = rng.choice(paths[split])
                    made += add(tool, {"path": path}, tmpl.format(path=path), tid)
        rng.shuffle(records)
        for i, r in enumerate(records):
            r["id"] = f"{split}-{i:04d}"
        out[split] = records
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=str(DATA_DIR))
    ns = ap.parse_args(argv)
    splits = build(ns.seed)
    report = validate_dataset(splits)
    from pathlib import Path
    out = Path(ns.out)
    out.mkdir(parents=True, exist_ok=True)
    import json
    for name, rows in splits.items():
        with open(out / f"{name}.jsonl", "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    report["seed"] = ns.seed
    write_json(out / "validation_report.json", report)
    print(f"dataset seed={ns.seed} ok={report['ok']} sizes={report['sizes']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
