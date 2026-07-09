#!/usr/bin/env python3
"""
Лексическое богатство АВТОРОВ вопросов ЧГК, по аналогии с исследованием
рэперов Ильи Иноземцева (rap.inozemtsev.lol).

Методология (1:1 со stand-up research, наши правки):
  - Корпус автора = тексты всех его вопросов (поле `text` + `comment`),
    только КИРИЛЛИЧЕСКИЕ токены, в хронологическом порядке.
  - Токенизация razdel, лемматизация pymorphy3.
  - Метрика: число УНИКАЛЬНЫХ ЛЕММ в первых WINDOW словах корпуса.
  - Корпус < WINDOW слов => «бледный круг» (метрика на меньшем окне, ниже надёжность).

Дедуп по глобальному id вопроса (один вопрос может лежать в нескольких пакетах).
Со-авторские вопросы засчитываются каждому из перечисленных авторов.
"""
import json, glob, re, collections, os, sys, time

PACKS_DIR = "/Users/imangulov/Downloads/Quiz Packs/packs"
OUT = os.path.join(os.path.dirname(__file__), "..", "report.json")
WINDOW = 25000          # окно метрики (как у Иноземцева)
DISPLAY_FLOOR = 10000   # кого вообще показываем (слов в корпусе)

CYR = re.compile(r"[а-яёА-ЯЁ]+")

def tokens(q):
    txt = (q.get("text", "") or "") + "\n" + (q.get("comment", "") or "")
    return [w.lower() for w in CYR.findall(txt)]

def datekey(q, pack):
    # хронология «карьеры» автора: когда вопрос сыгран/опубликован
    for src in (q.get("endDate"), q.get("pubDate"), pack.get("endDate"),
                pack.get("startDate"), pack.get("pubDate")):
        if src:
            return src
    return "9999-99-99"

def main():
    files = sorted(glob.glob(os.path.join(PACKS_DIR, "*.json")))
    print(f"packs: {len(files)}", flush=True)

    # ---------- PASS 1: подсчёт слов на автора (для отбора отображаемых) ----------
    t0 = time.time()
    wc = collections.Counter()
    gender = {}
    seen = set()
    for i, fn in enumerate(files):
        try:
            d = json.load(open(fn))
        except Exception:
            continue
        for tour in d.get("tours", []):
            for q in tour.get("questions", []):
                qid = q.get("id")
                if qid in seen:
                    continue
                seen.add(qid)
                n = len(tokens(q))
                for a in q.get("authors", []):
                    nm = a.get("name", "?")
                    wc[nm] += n
                    gender[nm] = a.get("gender", "")
        if i % 1000 == 0:
            print(f"  pass1 {i}/{len(files)}", flush=True)
    qualifiers = {nm for nm, c in wc.items() if c >= DISPLAY_FLOOR}
    print(f"pass1 done in {time.time()-t0:.0f}s | authors={len(wc)} "
          f"| >= {DISPLAY_FLOOR}w -> {len(qualifiers)}", flush=True)

    # ---------- PASS 2: собрать токены отображаемых авторов в порядке дат ----------
    t0 = time.time()
    # author -> list of (datekey, qid, [tokens])
    corpus = collections.defaultdict(list)
    qcount = collections.Counter()
    solo_q = collections.Counter()
    seen = set()
    for i, fn in enumerate(files):
        try:
            d = json.load(open(fn))
        except Exception:
            continue
        for tour in d.get("tours", []):
            for q in tour.get("questions", []):
                qid = q.get("id")
                if qid in seen:
                    continue
                seen.add(qid)
                authors = q.get("authors", [])
                if not any(a.get("name") in qualifiers for a in authors):
                    continue
                toks = tokens(q)
                dk = datekey(q, d)
                solo = len(authors) == 1
                for a in authors:
                    nm = a.get("name", "?")
                    if nm in qualifiers:
                        corpus[nm].append((dk, qid, toks))
                        qcount[nm] += 1
                        if solo:
                            solo_q[nm] += 1
        if i % 1000 == 0:
            print(f"  pass2 {i}/{len(files)}", flush=True)
    print(f"pass2 done in {time.time()-t0:.0f}s | collected {len(corpus)} authors",
          flush=True)

    # ---------- лемматизация первых WINDOW слов ----------
    import pymorphy3
    morph = pymorphy3.MorphAnalyzer()
    cache = {}
    def lemma(w):
        v = cache.get(w)
        if v is None:
            v = morph.parse(w)[0].normal_form
            cache[w] = v
        return v

    t0 = time.time()
    rows = []
    for j, (nm, items) in enumerate(sorted(corpus.items(),
                                           key=lambda kv: -wc[kv[0]])):
        items.sort(key=lambda x: (x[0], x[1]))  # по дате, затем id
        stream = []
        for _, _, toks in items:
            stream.extend(toks)
            if len(stream) >= WINDOW:
                break
        window_words = min(len(stream), WINDOW)
        win = stream[:WINDOW]
        lemmas = set()
        for w in win:
            lemmas.add(lemma(w))
        rows.append({
            "name": nm,
            "gender": gender.get(nm, ""),
            "total_words": wc[nm],
            "total_questions": qcount[nm],
            "solo_questions": solo_q[nm],
            "window_words": window_words,
            "unique_lemmas": len(lemmas),
            "reliable": window_words >= WINDOW,
            # плотность лексики: уникальные леммы на 1000 слов окна
            "lemmas_per_1k": round(len(lemmas) / window_words * 1000, 1),
        })
        if j % 25 == 0:
            print(f"  lemmatize {j}/{len(corpus)} cache={len(cache)}", flush=True)
    print(f"lemmatize done in {time.time()-t0:.0f}s | cache={len(cache)}", flush=True)

    rows.sort(key=lambda r: -r["unique_lemmas"])
    reliable = [r for r in rows if r["reliable"]]
    med = sorted(r["unique_lemmas"] for r in reliable)
    median = med[len(med)//2] if med else 0

    report = {
        "meta": {
            "window": WINDOW,
            "display_floor": DISPLAY_FLOOR,
            "total_authors": len(wc),
            "total_questions": len(seen),
            "displayed": len(rows),
            "reliable": len(reliable),
            "median_reliable_lemmas": median,
        },
        "authors": rows,
    }
    with open(OUT, "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print(f"\nwrote {OUT}")
    print(f"reliable authors (>= {WINDOW}w): {len(reliable)} | median lemmas: {median}")
    print("TOP 15:")
    for r in rows[:15]:
        flag = "" if r["reliable"] else "  (pale)"
        print(f"  {r['unique_lemmas']:>6}  {r['total_questions']:>5}q  {r['name']}{flag}")

if __name__ == "__main__":
    main()
