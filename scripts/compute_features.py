#!/usr/bin/env python3
"""Считает «фишки» поверх корпуса ЧГК и пишет данные для страниц сайта.

Дополняет report.json:
  sig_style : топ-10 «слов-маркеров» (нарицательные, weighted log-odds vs корпус)
  sig_theme : топ-10 «тем» (имена/фамилии/гео/организации)
  kindred   : 3 родственных автора (косинус tf-idf по лексике)
Пишет:
  coauthors.json : граф соавторства (ВСЕ авторы, рёбра по силе связи)
  years.json     : слово / имя / гео-слово года + «как менялась метода»
  cliches.json   : зачины вопросов и заезженные обороты

Метод — weighted log-odds с приором Дирихле (Monroe, Colaresi & Quinn 2008).
Тяжёлые агрегаты кэшируются в scripts/_raw.pkl (пересчёт: --fresh).
"""
import json, glob, re, math, os, collections, time, pickle, sys

PACKS_DIR = "/Users/imangulov/Downloads/Quiz Packs/packs"
HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
PKL = os.path.join(HERE, "_raw.pkl")
CYR = re.compile(r"[а-яёА-ЯЁ]+")
# --- чистка текста: снимаем знаки ударения (U+0301/U+0300) ДО токенизации,
#     иначе «Дека́рт» рвётся на «дека»+«рт». Точечно, чтобы не разрушить ё/й. ---
_STRESS = str.maketrans("", "", "̀́́͂")
_STRESS_TBL = dict.fromkeys([0x0300, 0x0301, 0x0341, 0x0342, 0x00B4, 0x02CA], None)
def destress(s):
    return s.translate(_STRESS_TBL)
# --- детект языка: буквы і ї є ґ ў есть в бел/укр и отсутствуют в русском.
#     Русский вопрос про обувь «гэта» их не содержит -> не пострадает. ---
_OTHER = set("іїєґўІЇЄҐЎ")
_CYR_ALL = re.compile("[а-яёіїєґўА-ЯЁІЇЄҐЎ]")
def is_nonrussian(t):
    L = _CYR_ALL.findall(t)
    if len(L) < 20:
        return False
    return sum(1 for c in t if c in _OTHER) / len(L) > 0.03

STOP = set("""и в во не что он на я с со как а то все всё она так его но да ты к у же вы за бы
по только ее её мне было вот от меня еще ещё нет о из ему теперь когда даже ну вдруг ли если уже или
ни быть был него до вас нибудь опять уж вам ведь там потом себя ничего ей может они тут где есть
надо ней для мы тебя их чем была сам чтоб без будто чего раз тоже себе под будет ж кто этот того
потому этого какой совсем ним здесь этом один почти мой тем чтобы нее сейчас были куда зачем всех
никогда можно при наконец два об другой хоть после над больше тот через эти нас про всего них какая
много разве три эту моя впрочем свою этой перед иногда лучше чуть том нельзя такой им более всегда
конечно всю между это свой которых который которые также этих весь эта наш свои мочь стать самый этими
как-то также""".split())

# форматно-жаргонные слова ЧГК — исключаем из «слова года» и «слов-маркеров»
META = set("""слово вопрос замена заменить цитата икс игрек зет материал раздаточный раздатка чтец
знаток ответ буква ведущий статья википедия журнал герой альфа бета гамма пропуск пропустить
воспроизвести прослушать обсуждение дуплет блиц тур редактор автор команда назвать название поэтому
внимание многоточие пример изображение картинка фотография рисунок аудио видео текст строка символ
знак логотип аббревиатура пара пропущенный некоторый пропуская гласный согласный слог фрагмент
раунд альф альфа бета гамма дельта омега зет назва гэта пытанна больша льшуя кова знатокиада
викторович кс кса ксу ксом ксов ксова ксовый иксовый икснуть иксов иксом икса
сайт отрывок эпизод сцена глава персонаж фильм роман книга рассказ повесть пьеса предложение
фраза выражение пауза алфавит раскрутка тёзка тезка речь бланк секунда минута перевод оригинал
вариант версия надпись подпись реплика заголовок абзац строчка строка тори анекдот эпиграмма
песня стихотворение стих кадр сюжет монолог диалог
бескрылка синхрон очко кавычка подсказка энциклопедия словарь газета журнал происхождение
четверостишие швец юзер хаус зачёт зачет апелляция комментарий формулировка
аллюзия отточие список заметка однофамилец героиня реминисценция определение цитирование""".split())

# --- по итогам LLM-аудита лемм (5 агентов) ---
# УДАЛИТЬ: обрывки/косвенные формы фамилий, бренды-не-места, нерусское, отчества.
AUDIT_BLOCK = set("""
брюоля вувузел ниал паол первыя ский ство солт хокк шефнера
авив айрес анджелес буэнос амундсена бреннана бухвальда буссенара буссенары брукса бэнкса бэтмена
бёлля бёрка бёрнэма бритиша венгера гардиана гиннесса голдинга гомера гриффина гениса готэма даррелла
дорь ермол кастр ксеп конференц карризя кизя запахулья киевск левандовск
смитя суиня тиффаня сэмюэла старра стеллера синделара трумена уорнера формана хаггарда хайнлайна
хеллера хилла хитчинга шпицвега эрдмана экслера фоллетта финнегана энтерпрайза эрнаня чатланина
тайгера фрая шишковы фанфиковы физико чёрно шизгар юнайтед
людея майорк мисим мобь накамур невад немецк нной обуд паппеть паризя португальск сатося сатрапеть сваровск
гугл икеа телеграм ютуба яндекс сяомь майкрософт твиттер фейсбук онли
сергеевич александрович алибабаевич анатолиевич андреевич аркадиевич борисович василиевич георгиевич
иванович ильич иоаннович исаевич ефимович кузьмич михаилович николаевич осипович петрович
""".split())
META |= AUDIT_BLOCK
# ПЕРЕКЛАССИФИЦИРОВАТЬ в нарицательные (pymorphy ошибочно пометил как имя/гео/орг):
# так годные слова уедут в «стиль», а не пропадут.
FORCE_COMMON = set("""
авторка афорист блэкджек бодибилдинг бондиана вампирша васаби великое аэс гэс ввс
душнил камео катана коан каббалиста квнщиковы
стендап стэндап хард фэйк фанфик хюгге эмодзь эмси
словенский сталинградский стамбульский тегеранский техасский украинский фарерский чикагский шотландский эстонский
майка марка метамфетамин нии нунчак октиллион плюсик сабля
""".split())

import pymorphy3
morph = pymorphy3.MorphAnalyzer()
_lemma, _kind, _pos = {}, {}, {}
def lemma(w):
    v = _lemma.get(w)
    if v is None:
        p = morph.parse(w)[0]  # не из словаря -> оставляем слово (иначе pymorphy выдумывает лемму)
        v = p.normal_form if p.is_known else w; _lemma[w] = v
    return v
def kind(lm):
    if lm in FORCE_COMMON:
        return "none"
    k = _kind.get(lm)
    if k is None:
        t = morph.parse(lm)[0].tag
        # Patr (отчество) -> отдельная категория "patr": не имя, не тема, не стиль
        k = ("surn" if "Surn" in t else "name" if "Name" in t
             else "patr" if "Patr" in t
             else "geo" if "Geox" in t else "org" if "Orgn" in t else "none")
        _kind[lm] = k
    return k
def pos(lm):
    p = _pos.get(lm)
    if p is None:
        p = morph.parse(lm)[0].tag.POS or ""; _pos[lm] = p
    return p

def texts(q):
    return (q.get("text", "") or ""), (q.get("comment", "") or "")
def year_of(q, pack):
    for src in (q.get("endDate"), q.get("pubDate"), pack.get("endDate"),
                pack.get("startDate"), pack.get("pubDate")):
        if src and len(src) >= 4 and src[:4].isdigit():
            y = int(src[:4])
            if 1989 <= y <= 2026: return y
    return None


def build_raw(disp_names):
    files = sorted(glob.glob(os.path.join(PACKS_DIR, "*.json")))
    print(f"packs={len(files)}", flush=True)
    global_lemma = collections.Counter()
    author_lemma = collections.defaultdict(collections.Counter)
    coauthor = collections.Counter()
    node_name, node_q = {}, collections.Counter()
    opener2 = collections.Counter(); opener3 = collections.Counter(); opener4 = collections.Counter()
    trigram = collections.Counter()
    year_lemma = collections.defaultdict(collections.Counter); year_tot = collections.Counter()
    seen = set(); skipped_lang = 0
    t0 = time.time()
    for i, fn in enumerate(files):
        try: d = json.load(open(fn))
        except Exception: continue
        for tour in d.get("tours", []):
            for q in tour.get("questions", []):
                qid = q.get("id")
                if qid in seen: continue
                seen.add(qid)
                text, comment = texts(q)
                text = destress(text); comment = destress(comment)
                if is_nonrussian(text + " " + comment):
                    skipped_lang += 1; continue   # белорусский/украинский вопрос
                toks = [w.lower() for w in CYR.findall(text + "\n" + comment)]
                # каждая лемма учитывается НЕ БОЛЕЕ ОДНОГО РАЗА на вопрос
                # (иначе «гек ×100» в одном вопросе раздувает частоту)
                uniq = {lemma(t) for t in toks}
                global_lemma.update(uniq)
                y = year_of(q, d)
                if y is not None:
                    year_lemma[y].update(uniq); year_tot[y] += len(uniq)
                ids = sorted({a["id"] for a in q.get("authors", []) if a.get("id")})
                for a in q.get("authors", []):
                    if a.get("id"):
                        node_name[a["id"]] = a.get("name", "?"); node_q[a["id"]] += 1
                    if a.get("name") in disp_names:
                        author_lemma[a["name"]].update(uniq)
                for x in range(len(ids)):
                    for z in range(x + 1, len(ids)):
                        coauthor[(ids[x], ids[z])] += 1
                tt = [w.lower() for w in CYR.findall(text)]
                if len(tt) >= 2: opener2[" ".join(tt[:2])] += 1
                if len(tt) >= 3: opener3[" ".join(tt[:3])] += 1
                if len(tt) >= 4: opener4[" ".join(tt[:4])] += 1
                for k in range(len(tt) - 2):
                    trigram[(tt[k], tt[k+1], tt[k+2])] += 1
        if len(trigram) > 4_000_000:
            trigram = collections.Counter({k: v for k, v in trigram.items() if v >= 3})
        if i % 1500 == 0:
            print(f"  pass {i}/{len(files)} cache={len(_lemma)}", flush=True)
    def topn(c, n, j=" "):
        return [{"phrase": (j.join(k) if isinstance(k, tuple) else k), "count": v}
                for k, v in c.most_common(n)]
    raw = {
        "global_lemma": global_lemma, "N": sum(global_lemma.values()),
        "author_lemma": dict(author_lemma),
        "year_lemma": {y: c for y, c in year_lemma.items()}, "year_tot": dict(year_tot),
        "coauthor": coauthor, "node_name": node_name, "node_q": node_q,
        "cliche": {"openers2": topn(opener2, 25), "openers3": topn(opener3, 25),
                   "openers4": topn(opener4, 20), "trigrams": topn(trigram, 40),
                   "questions": len(seen) - skipped_lang},
    }
    print(f"raw built {time.time()-t0:.0f}s | tokens={raw['N']} vocab={len(global_lemma)} "
          f"| skipped non-russian={skipped_lang}", flush=True)
    with open(PKL, "wb") as f: pickle.dump(raw, f)
    return raw


A0 = 1000.0
def emit(raw):
    G = raw["global_lemma"]; N = raw["N"]
    author_lemma = raw["author_lemma"]
    report = json.load(open(os.path.join(ROOT, "report.json")))
    displayed = {a["name"]: a for a in report["authors"]}

    def logodds(cnt_i, n_i, min_i=3):
        out = []
        for w, yi in cnt_i.items():
            if yi < min_i: continue
            gw = G[w]; yj = max(gw - yi, 0); aw = A0 * gw / N; nj = N - n_i
            delta = (math.log((yi + aw) / (n_i + A0 - yi - aw))
                     - math.log((yj + aw) / (nj + A0 - yj - aw)))
            var = 1.0 / (yi + aw) + 1.0 / (yj + aw)
            out.append((w, delta / math.sqrt(var), yi, gw))
        out.sort(key=lambda x: -x[1]); return out

    author_df = collections.Counter()
    for c in author_lemma.values():
        for w in c: author_df[w] += 1
    Nd = len(author_lemma)
    # «стилевой отпечаток» автора = вектор положительных z (weighted log-odds) по
    # нарицательным словам, которыми он ВЫДЕЛЯЕТСЯ. Косинус таких отпечатков даёт
    # «пишут в одной манере», а не «оба много писали»: плодовитые авторы больше
    # не выпадают в соседи всем подряд, т.к. сравниваем характерность, а не объём.
    def fingerprint(c, n_i):
        v = {}
        for w, z, yi, gw in logodds(c, n_i, min_i=3):
            if z <= 1.0: break                      # отсортировано по убыванию z
            if kind(w) != "none" or w in STOP or w in META or len(w) <= 2: continue
            if author_df[w] < 2: continue           # слово должно встречаться не у одного
            v[w] = z
            if len(v) >= 120: break
        return v, (math.sqrt(sum(x * x for x in v.values())) or 1.0)
    FP = {nm: fingerprint(c, sum(c.values())) for nm, c in author_lemma.items()}
    def kindred(nm):
        vi, ni = FP[nm]; sims = []
        for nm2, (vj, nj) in FP.items():
            if nm2 == nm or not vj: continue
            a, b = (vi, vj) if len(vi) < len(vj) else (vj, vi)
            dot = sum(val * b.get(w, 0.0) for w, val in a.items())
            if dot > 0:
                sims.append((nm2, dot / (ni * nj)))
        sims.sort(key=lambda x: -x[1])
        return [{"name": s[0], "pid": displayed[s[0]]["pid"], "sim": round(s[1], 3)}
                for s in sims[:3]]

    for nm, a in displayed.items():
        c = author_lemma.get(nm, collections.Counter()); n_i = sum(c.values())
        style, theme = [], []
        for w, z, yi, gw in logodds(c, n_i):
            it = {"lemma": w, "z": round(z, 2), "count": yi, "others": author_df[w]-1}
            k = kind(w)
            if w in STOP or w in META or len(w) <= 2:
                continue
            if k == "none":
                if len(style) < 10: style.append(it)
            elif k in ("surn", "name", "geo", "org"):
                if len(theme) < 10: it["kind"] = k; theme.append(it)
            if len(style) >= 10 and len(theme) >= 10: break
        a["sig_style"] = style; a["sig_theme"] = theme; a["kindred"] = kindred(nm)
    json.dump(report, open(os.path.join(ROOT, "report.json"), "w"),
              ensure_ascii=False, separators=(",", ":"))
    print("report.json updated (signatures/kindred)")

    # ---- граф соавторства ----
    coauthor = raw["coauthor"]; node_name = raw["node_name"]; node_q = raw["node_q"]
    edges_all = [(a, b, w) for (a, b), w in coauthor.items() if w >= 2]
    wmin = 2
    for cand in range(2, 60):
        nn = {x for a, b, w in edges_all if w >= cand for x in (a, b)}
        if len(nn) <= 520: wmin = cand; break
    edges = [(a, b, w) for a, b, w in edges_all if w >= wmin]
    deg = collections.Counter()
    for a, b, w in edges: deg[a] += w; deg[b] += w
    nodeset = {x for a, b, w in edges for x in (a, b)}
    nodes = [{"id": i, "name": node_name.get(i, "?"), "pid": i, "q": node_q[i], "deg": deg[i]}
             for i in nodeset]
    # топ «у кого больше всего связей» — по ВСЕМ парам соавторства (любой вес)
    partners = collections.defaultdict(set); joint = collections.Counter()
    for (a, b), wt in coauthor.items():
        partners[a].add(b); partners[b].add(a); joint[a] += wt; joint[b] += wt
    top_conn = sorted(partners, key=lambda i: (-len(partners[i]), -joint[i]))[:30]
    top_connected = [{"name": node_name.get(i, "?"), "pid": i,
                      "partners": len(partners[i]), "joint": joint[i], "q": node_q[i]}
                     for i in top_conn]
    json.dump({"meta": {"wmin": wmin, "nodes": len(nodes), "edges": len(edges),
                        "total_pairs": len(coauthor),
                        "total_authors": len({x for p in coauthor for x in p})},
               "nodes": nodes, "edges": [{"a": a, "b": b, "w": w} for a, b, w in edges],
               "top_connected": top_connected},
              open(os.path.join(ROOT, "coauthors.json"), "w"),
              ensure_ascii=False, separators=(",", ":"))
    print(f"coauthors.json: wmin={wmin} nodes={len(nodes)} edges={len(edges)}")

    # ---- годы: слово / имя / гео года + эволюция методы ----
    year_lemma = raw["year_lemma"]; year_tot = raw["year_tot"]
    def yrank(y, mode, min_c):
        cnt = year_lemma[y]; ny = year_tot[y]; rows = []
        for w, yi in cnt.items():
            if yi < min_c or len(w) < 4: continue
            k = kind(w)
            if mode == "word" and not (k == "none" and pos(w) == "NOUN"
                                       and w not in STOP and w not in META): continue
            if w in META or w in STOP: continue
            if mode == "name" and k not in ("surn", "name"): continue
            if mode == "geo" and k != "geo": continue
            if mode in ("name", "geo") and (G[w] < 40): continue
            if mode == "word" and G[w] < 25: continue
            gw = G[w]; yj = max(gw - yi, 0); aw = A0 * gw / N
            delta = (math.log((yi+aw)/(ny+A0-yi-aw)) - math.log((yj+aw)/(N-ny+A0-yj-aw)))
            var = 1.0/(yi+aw) + 1.0/(yj+aw)
            rows.append((w, delta/math.sqrt(var), yi))
        rows.sort(key=lambda x: -x[1]); return rows
    years_out = []
    for y in sorted(year_lemma):
        if year_tot[y] < 40000: continue
        def one(mode, mc):
            r = yrank(y, mode, mc)
            return {"lemma": r[0][0], "z": round(r[0][1], 2), "count": r[0][2]} if r else None
        years_out.append({
            "year": y, "tokens": year_tot[y],
            "word": one("word", 8), "name": one("name", 8), "geo": one("geo", 6),
            "top5": [{"lemma": w, "z": round(z, 2), "count": c} for w, z, c in yrank(y, "word", 8)[:5]],
        })
    json.dump({"years": years_out}, open(os.path.join(ROOT, "years.json"), "w"),
              ensure_ascii=False, separators=(",", ":"))
    print(f"years.json: {len(years_out)} years")

    json.dump({"meta": {"questions": raw["cliche"]["questions"]},
               **{k: raw["cliche"][k] for k in ("openers2", "openers3", "openers4", "trigrams")}},
              open(os.path.join(ROOT, "cliches.json"), "w"),
              ensure_ascii=False, separators=(",", ":"))
    print("cliches.json written")

    json.dump({"meta_words": sorted(META), "stop_words": sorted(STOP)},
              open(os.path.join(ROOT, "stoplist.json"), "w"),
              ensure_ascii=False, separators=(",", ":"))
    print(f"stoplist.json written (meta={len(META)} stop={len(STOP)})")

    print("\n=== Борис Бурда ===")
    b = displayed.get("Борис Бурда")
    print(" style:", [x["lemma"] for x in b["sig_style"]])
    print(" theme:", [x["lemma"] for x in b["sig_theme"]])
    print(" kindred:", [x["name"] for x in b["kindred"]])
    print("=== слово / имя / гео года ===")
    for yo in years_out:
        w = yo["word"]["lemma"] if yo["word"] else "-"
        nmn = yo["name"]["lemma"] if yo["name"] else "-"
        g = yo["geo"]["lemma"] if yo["geo"] else "-"
        print(f"  {yo['year']}: {w:14} имя={nmn:12} гео={g}")


def main():
    report = json.load(open(os.path.join(ROOT, "report.json")))
    disp_names = {a["name"] for a in report["authors"]}
    if "--fresh" in sys.argv or not os.path.exists(PKL):
        raw = build_raw(disp_names)
    else:
        print("loading cached _raw.pkl (use --fresh to recompute)")
        raw = pickle.load(open(PKL, "rb"))
    emit(raw)

if __name__ == "__main__":
    main()
