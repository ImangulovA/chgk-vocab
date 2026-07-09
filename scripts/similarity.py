#!/usr/bin/env python3
"""Близость авторов ЧГК четырьмя способами -> дополняет report.json.

  kindred        — стилевой отпечаток (log-odds z по нарицательным словам); из compute_features.py
  kindred_delta  — Cosine Delta: z-нормированные частоты частотных/служебных слов (стилометрия «манеры»)
  kindred_ngram  — косинус профилей символьных 3-грамм
  kindred_emb    — doc2vec (Paragraph Vectors): локальная нейросеть, обучается на нашем корпусе

Те же фиксы, что и везде: снятие ударений, отсев бел/укр, дедуп леммы на вопрос
(для doc2vec — уникальные леммы вопроса; для delta/ngram — реальные частоты форм).
Локально, без внешних моделей и без обращений к API.
"""
import json, glob, re, os, collections
import numpy as np

PACKS_DIR = "/Users/imangulov/Downloads/Quiz Packs/packs"
HERE = os.path.dirname(__file__); ROOT = os.path.join(HERE, "..")
CYR = re.compile(r"[а-яёА-ЯЁ]+")
_STRESS = dict.fromkeys([0x0300, 0x0301, 0x0341, 0x0342, 0x00B4, 0x02CA], None)
def destress(s): return s.translate(_STRESS)
_OTHER = set("іїєґўІЇЄҐЎ"); _CYR_ALL = re.compile("[а-яёіїєґўА-ЯЁІЇЄҐЎ]")
def nonrus(t):
    L = _CYR_ALL.findall(t)
    return len(L) >= 20 and sum(1 for c in t if c in _OTHER) / len(L) > 0.03

import pymorphy3
morph = pymorphy3.MorphAnalyzer(); _lem = {}
def lemma(w):
    v = _lem.get(w)
    if v is None:
        v = morph.parse(w)[0].normal_form; _lem[w] = v
    return v

MFW_N = 300          # сколько частотных слов для Delta
NGRAM_TOP = 2000     # сколько символьных 3-грамм держим
DOC_CAP = 60000      # ограничение длины документа автора для doc2vec
EMB_DIM = 100

def top3(names, pids, S, i):
    order = np.argsort(-S[i])
    out = []
    for j in order:
        if j == i: continue
        out.append({"name": names[j], "pid": pids[j], "sim": round(float(S[i, j]), 3)})
        if len(out) == 3: break
    return out

def main():
    report = json.load(open(os.path.join(ROOT, "report.json")))
    authors = [a["name"] for a in report["authors"]]
    pid_of = {a["name"]: a["pid"] for a in report["authors"]}
    disp = set(authors)
    aidx = {nm: i for i, nm in enumerate(authors)}
    n = len(authors)
    print(f"authors={n}", flush=True)

    forms = [collections.Counter() for _ in range(n)]   # формы слов (для delta)
    grams = [collections.Counter() for _ in range(n)]   # символьные 3-граммы
    docs = [[] for _ in range(n)]                        # леммы (для doc2vec)
    gform = collections.Counter(); ggram = collections.Counter()
    seen = set()

    files = sorted(glob.glob(os.path.join(PACKS_DIR, "*.json")))
    for k, fn in enumerate(files):
        try: d = json.load(open(fn))
        except Exception: continue
        for tour in d.get("tours", []):
            for q in tour.get("questions", []):
                qid = q.get("id")
                if qid in seen: continue
                seen.add(qid)
                txt = destress((q.get("text", "") or "") + "\n" + (q.get("comment", "") or ""))
                if nonrus(txt): continue
                who = [a.get("name") for a in q.get("authors", []) if a.get("name") in disp]
                if not who: continue
                fs = [w.lower() for w in CYR.findall(txt)]
                lem_uniq = {lemma(w) for w in fs}
                # символьные 3-граммы с границами слова
                g = collections.Counter()
                for w in fs:
                    s = "_" + w + "_"
                    for i in range(len(s) - 2):
                        g[s[i:i+3]] += 1
                fc = collections.Counter(fs)
                gform.update(fc); ggram.update(g)
                for nm in who:
                    a = aidx[nm]
                    forms[a].update(fc); grams[a].update(g)
                    if len(docs[a]) < DOC_CAP:
                        docs[a].extend(lem_uniq)
        if k % 1500 == 0:
            print(f"  read {k}/{len(files)} lemcache={len(_lem)}", flush=True)
    print("corpus collected", flush=True)

    names, pids = authors, [pid_of[a] for a in authors]

    # ---------- Cosine Delta (стилометрия по частотным словам) ----------
    mfw = [w for w, _ in gform.most_common(MFW_N)]
    M = np.zeros((n, len(mfw)))
    for a in range(n):
        tot = sum(forms[a].values()) or 1
        for j, w in enumerate(mfw):
            M[a, j] = forms[a][w] / tot
    mu = M.mean(0); sd = M.std(0) + 1e-9
    Z = (M - mu) / sd                       # z-нормировка по каждому слову (Delta)
    Zn = Z / (np.linalg.norm(Z, axis=1, keepdims=True) + 1e-9)
    S_delta = Zn @ Zn.T
    print("delta done", flush=True)

    # ---------- символьные 3-граммы (косинус tf-idf) ----------
    topg = [g for g, _ in ggram.most_common(NGRAM_TOP)]
    gi = {g: j for j, g in enumerate(topg)}
    df = np.zeros(len(topg))
    G = np.zeros((n, len(topg)))
    for a in range(n):
        tot = sum(grams[a].values()) or 1
        for g, c in grams[a].items():
            j = gi.get(g)
            if j is not None:
                G[a, j] = c / tot
    df = (G > 0).sum(0)
    idf = np.log((n + 1) / (df + 1)) + 1
    G = G * idf
    Gn = G / (np.linalg.norm(G, axis=1, keepdims=True) + 1e-9)
    S_ngram = Gn @ Gn.T
    print("ngram done", flush=True)

    # ---------- doc2vec (локальная нейросеть) ----------
    from gensim.models.doc2vec import Doc2Vec, TaggedDocument
    tagged = [TaggedDocument(docs[a], [a]) for a in range(n)]
    model = Doc2Vec(vector_size=EMB_DIM, min_count=5, epochs=40, dm=1,
                    window=5, negative=5, workers=4, seed=42)
    model.build_vocab(tagged)
    model.train(tagged, total_examples=len(tagged), epochs=model.epochs)
    E = np.array([model.dv[a] for a in range(n)])
    En = E / (np.linalg.norm(E, axis=1, keepdims=True) + 1e-9)
    S_emb = En @ En.T
    print("doc2vec done", flush=True)

    # ---------- запись ----------
    for i, a in enumerate(report["authors"]):
        a["kindred_delta"] = top3(names, pids, S_delta, i)
        a["kindred_ngram"] = top3(names, pids, S_ngram, i)
        a["kindred_emb"] = top3(names, pids, S_emb, i)
    json.dump(report, open(os.path.join(ROOT, "report.json"), "w"),
              ensure_ascii=False, separators=(",", ":"))
    print("report.json updated with kindred_delta/ngram/emb")

    b = aidx.get("Борис Бурда")
    if b is not None:
        print("Бурда  lex:  ", [x["name"] for x in report["authors"][b]["kindred"]])
        print("Бурда  delta:", [x["name"] for x in report["authors"][b]["kindred_delta"]])
        print("Бурда  ngram:", [x["name"] for x in report["authors"][b]["kindred_ngram"]])
        print("Бурда  emb:  ", [x["name"] for x in report["authors"][b]["kindred_emb"]])

if __name__ == "__main__":
    main()
