#!/usr/bin/env python3
"""Фирменные СЛОВОСОЧЕТАНИЯ автора (word би-/три-граммы) -> дополняет report.json.

Для каждого отображаемого автора считаем weighted log-odds по словесным биграммам
и триграммам (форма слов, кириллица) против всего корпуса и берём топ распределённых.
Добавляет поля sig_bi (топ-8) и sig_tri (топ-6).

Те же фиксы: снятие ударений, отсев бел/укр, каждый н-грамм учитывается 1 раз на вопрос.
"""
import json, glob, os, sys, math, collections
HERE = os.path.dirname(__file__); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
from compute_features import destress, is_nonrussian, CYR, STOP, META  # noqa

PACKS_DIR = "/Users/imangulov/Downloads/Quiz Packs/packs"
A0 = 1000.0
BORING = STOP | META

def boring_ngram(ng):
    # скучно, если ВСЕ токены служебные/жаргон, или есть слишком короткий токен
    return all(t in BORING for t in ng) or any(len(t) < 3 for t in ng)

def main():
    report = json.load(open(os.path.join(ROOT, "report.json")))
    disp = {a["name"] for a in report["authors"]}
    gbi = collections.Counter(); gtri = collections.Counter()
    abi = collections.defaultdict(collections.Counter)
    atri = collections.defaultdict(collections.Counter)
    seen = set()
    files = sorted(glob.glob(os.path.join(PACKS_DIR, "*.json")))
    print(f"packs={len(files)}", flush=True)
    for k, fn in enumerate(files):
        try: d = json.load(open(fn))
        except Exception: continue
        for tour in d.get("tours", []):
            for q in tour.get("questions", []):
                qid = q.get("id")
                if qid in seen: continue
                seen.add(qid)
                txt = destress((q.get("text", "") or "") + "\n" + (q.get("comment", "") or ""))
                if is_nonrussian(txt): continue
                who = [a.get("name") for a in q.get("authors", []) if a.get("name") in disp]
                if not who: continue
                t = [w.lower() for w in CYR.findall(txt)]
                # уникальные н-граммы в пределах вопроса (без спама повторов)
                bi = set(zip(t, t[1:]))
                tri = set(zip(t, t[1:], t[2:]))
                bi = {g for g in bi if not boring_ngram(g)}
                tri = {g for g in tri if not boring_ngram(g)}
                gbi.update(bi); gtri.update(tri)
                for nm in who:
                    abi[nm].update(bi); atri[nm].update(tri)
        if len(gbi) > 6_000_000:
            gbi = collections.Counter({x: c for x, c in gbi.items() if c >= 2})
        if len(gtri) > 6_000_000:
            gtri = collections.Counter({x: c for x, c in gtri.items() if c >= 2})
        if k % 1500 == 0:
            print(f"  read {k}/{len(files)} gbi={len(gbi)} gtri={len(gtri)}", flush=True)
    Nbi = sum(gbi.values()); Ntri = sum(gtri.values())
    print(f"collected: bi_vocab={len(gbi)} tri_vocab={len(gtri)}", flush=True)

    def logodds(cnt, G, N, n_i, min_i, topn):
        out = []
        for ng, yi in cnt.items():
            if yi < min_i: continue
            gw = G.get(ng, yi)
            yj = max(gw - yi, 0); aw = A0 * gw / N; nj = N - n_i
            if n_i + A0 - yi - aw <= 0 or nj + A0 - yj - aw <= 0: continue
            delta = (math.log((yi + aw) / (n_i + A0 - yi - aw))
                     - math.log((yj + aw) / (nj + A0 - yj - aw)))
            var = 1.0 / (yi + aw) + 1.0 / (yj + aw)
            out.append((ng, delta / math.sqrt(var), yi))
        out.sort(key=lambda x: -x[1])
        return [{"phrase": " ".join(ng), "z": round(z, 2), "count": c}
                for ng, z, c in out[:topn]]

    for a in report["authors"]:
        nm = a["name"]
        cbi, ctri = abi.get(nm, {}), atri.get(nm, {})
        a["sig_bi"] = logodds(cbi, gbi, Nbi, sum(cbi.values()) or 1, 3, 8)
        a["sig_tri"] = logodds(ctri, gtri, Ntri, sum(ctri.values()) or 1, 2, 6)
    json.dump(report, open(os.path.join(ROOT, "report.json"), "w"),
              ensure_ascii=False, separators=(",", ":"))
    print("report.json updated with sig_bi/sig_tri", flush=True)
    b = next((a for a in report["authors"] if a["name"] == "Борис Бурда"), None)
    if b:
        print("Бурда bi :", [x["phrase"] for x in b["sig_bi"]])
        print("Бурда tri:", [x["phrase"] for x in b["sig_tri"]])

if __name__ == "__main__":
    main()
