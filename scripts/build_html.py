#!/usr/bin/env python3
"""Собирает self-contained index.html (тема Pac-Man) с вшитыми данными report.json.

Дизайн-референс: bergside/awesome-design-skills -> skills/pacman
Токены: surface #000, maze/primary #2A3FE5, secondary/pink #F4B9B0,
success #16A34A, warning #D97706, danger #DC2626. Шрифты: Press Start 2P
(латинский лого + цифры; кириллицу не поддерживает), Space Mono / JetBrains Mono
(кириллический текст). Пакмен-жёлтый #FFD400 — герой-акцент (сам Pac-Man).
"""
import json, os

HERE = os.path.dirname(__file__)
report = json.load(open(os.path.join(HERE, "..", "report.json")))
DATA = json.dumps(report, ensure_ascii=False, separators=(",", ":"))

HTML = r"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CHGK LEXICON — словарь авторов вопросов ЧГК</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Space+Mono:wght@400;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
  :root{
    --surface:#000000; --panel:#0a0d1a; --maze:#2A3FE5; --maze-dim:#1a1f4d;
    --pac:#FFD400; --pink:#F4B9B0; --red:#DC2626; --orange:#D97706;
    --green:#16A34A; --inky:#37c6ff; --text:#F5F7FA; --muted:#8b93a7;
    --pellet:#3a4470;
    --pixel:'Press Start 2P',monospace;
    --mono:'Space Mono','JetBrains Mono',ui-monospace,Menlo,monospace;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--surface);color:var(--text);font-family:var(--mono);
    font-size:14px;line-height:1.55;
    background-image:radial-gradient(var(--maze-dim) 1px,transparent 1px);
    background-size:22px 22px;background-position:0 0}
  .wrap{max-width:980px;margin:0 auto;padding:30px 18px 90px}

  .logo{font-family:var(--pixel);color:var(--pac);font-size:26px;line-height:1.35;
    letter-spacing:1px;margin:0 0 14px;text-shadow:3px 3px 0 var(--maze)}
  .logo .ghost{color:var(--pink)}
  .sub{color:var(--text);margin:0 0 6px;max-width:720px}
  .sub b{color:var(--pac)}
  .credit{color:var(--muted);font-size:12px;margin:0 0 22px}
  .credit a{color:var(--inky)}

  .stats{display:flex;flex-wrap:wrap;gap:12px;margin:0 0 24px}
  .stat{background:var(--panel);border:3px solid var(--maze);border-radius:8px;
    padding:12px 16px;min-width:140px;box-shadow:4px 4px 0 var(--maze-dim)}
  .stat .n{font-family:var(--pixel);font-size:20px;color:var(--pac);
    font-variant-numeric:tabular-nums}
  .stat .l{color:var(--muted);font-size:11px;text-transform:uppercase;
    letter-spacing:.08em;margin-top:8px}

  .controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:0 0 14px;
    position:sticky;top:0;background:var(--surface);padding:12px 0;z-index:5;
    border-bottom:2px dotted var(--maze)}
  input[type=search],select,label.tgl{font-family:var(--mono);font-size:13px;
    background:var(--panel);border:2px solid var(--maze);color:var(--text);
    border-radius:6px;padding:10px 12px}
  input[type=search]{flex:1;min-width:200px}
  input[type=search]::placeholder{color:var(--muted)}
  select,label.tgl{cursor:pointer}
  label.tgl{display:flex;align-items:center;gap:8px;user-select:none}
  input:focus-visible,select:focus-visible,label.tgl:focus-within{
    outline:3px solid var(--pac);outline-offset:2px}
  accent-color:var(--pac);
  input[type=checkbox]{accent-color:var(--pac);width:16px;height:16px}

  .legend{display:flex;flex-wrap:wrap;gap:18px;color:var(--muted);font-size:12px;margin:6px 0 8px}
  .legend span{display:flex;align-items:center;gap:7px}
  .dot{width:11px;height:11px;border-radius:3px 3px 5px 5px;display:inline-block}
  .dot.HE{background:var(--inky)} .dot.SHE{background:var(--pink)} .dot.U{background:var(--muted)}

  .row{display:grid;grid-template-columns:44px 1fr;gap:12px;align-items:center;
    padding:9px 0;border-bottom:1px dotted var(--maze-dim)}
  .rank{font-family:var(--pixel);color:var(--maze);text-align:right;font-size:11px;
    font-variant-numeric:tabular-nums}
  .barcell{position:relative}
  .top{display:flex;justify-content:space-between;align-items:baseline;gap:10px;margin-bottom:6px}
  .name{font-weight:700;font-size:15px}
  .name .dot{margin-right:8px;vertical-align:middle}
  .val{font-family:var(--pixel);font-size:13px;color:var(--pac);
    font-variant-numeric:tabular-nums;white-space:nowrap}
  .val small{font-family:var(--mono);color:var(--muted);font-weight:400;margin-left:8px;
    font-size:11px}

  /* pac-man bar: коридор из пеллет + жёлтый съеденный путь + munching pacman */
  .track{position:relative;height:18px;border-radius:9px;
    background:radial-gradient(circle,var(--pellet) 2px,transparent 2.4px);
    background-size:14px 18px;background-position:8px center}
  .fill{position:absolute;left:0;top:50%;transform:translateY(-50%);height:5px;
    border-radius:3px;background:linear-gradient(90deg,#8a7400,var(--pac));min-width:2px}
  .pac{position:absolute;top:50%;width:18px;height:18px;transform:translate(-50%,-50%);
    background:var(--pac);border-radius:50%;
    clip-path:polygon(100% 32%,8% 4%,8% 96%,100% 68%)}
  @media (prefers-reduced-motion:no-preference){
    .pac{animation:chomp .45s steps(1,jump-none) infinite alternate}
  }
  @keyframes chomp{
    from{clip-path:polygon(100% 30%,8% 4%,8% 96%,100% 70%)}
    to{clip-path:polygon(100% 48%,8% 4%,8% 96%,100% 52%)}
  }
  .meta2{color:var(--muted);font-size:11.5px;margin-top:6px}

  .pale .fill{background:linear-gradient(90deg,#2a2f45,#5b6480)}
  .pale .pac{background:var(--muted);animation:none}
  .pale .name,.pale .val{color:var(--muted)}
  .pale .rank{color:var(--maze-dim)}

  .foot{color:var(--muted);font-size:12.5px;margin-top:38px;border-top:2px dotted var(--maze);
    padding-top:20px}
  .foot a{color:var(--inky)}
  mark{background:var(--pac);color:#000;border-radius:3px;padding:0 2px}
</style>
</head>
<body>
<div class="wrap">
  <h1 class="logo">CHGK <span class="ghost">LEXICON</span></h1>
  <p class="sub">У кого из авторов вопросов <b>«Что? Где? Когда?»</b> богаче словарный
  запас. Метрика: число <b>уникальных лемм в первых 25&nbsp;000 словах</b> корпуса автора
  (тексты и комментарии его вопросов), лемматизация pymorphy3, только кириллица.</p>
  <p class="credit">Подход — по мотивам исследования рэперов
  <a href="https://rap.inozemtsev.lol/" target="_blank" rel="noopener">rap.inozemtsev.lol</a>.
  Дизайн — тема Pac-Man (bergside/awesome-design-skills).</p>

  <div class="stats" id="stats"></div>

  <div class="controls">
    <input type="search" id="q" placeholder="ПОИСК АВТОРА…" autocomplete="off" aria-label="Поиск автора">
    <select id="sort" aria-label="Сортировка">
      <option value="unique_lemmas">по богатству словаря</option>
      <option value="lemmas_per_1k">по плотности (лемм / 1000 слов)</option>
      <option value="total_questions">по числу вопросов</option>
      <option value="total_words">по объёму корпуса</option>
    </select>
    <label class="tgl"><input type="checkbox" id="pale"> показать &lt;25k</label>
  </div>
  <div class="legend">
    <span><i class="dot HE"></i> автор-мужчина</span>
    <span><i class="dot SHE"></i> автор-женщина</span>
    <span><i class="dot U"></i> не указан</span>
    <span>бледный = корпус меньше 25&nbsp;000 слов</span>
  </div>

  <div id="list"></div>

  <div class="foot">
    <p>Метрика измеряет разнообразие словаря, а не «ум» или качество вопросов: у прозаичных
    формулировок и у авторов с большим числом коротких вопросов метрика естественно выше.
    Со-авторские вопросы засчитываются каждому соавтору. Порог отображения — 10&nbsp;000 слов.</p>
    <p>Данные: дамп базы вопросов ЧГК (gotquestions / db.chgk.info).</p>
  </div>
</div>

<script>
const REPORT = __DATA__;
const A = REPORT.authors, M = REPORT.meta;
const fmt = n => n.toLocaleString('ru-RU');

document.getElementById('stats').innerHTML = [
  ['надёжных авторов', fmt(M.reliable)],
  ['медиана словаря', fmt(M.median_reliable_lemmas)],
  ['всего авторов', fmt(M.total_authors)],
  ['всего вопросов', fmt(M.total_questions)],
].map(([l,n])=>`<div class="stat"><div class="n">${n}</div><div class="l">${l}</div></div>`).join('');

const qEl=document.getElementById('q'), sortEl=document.getElementById('sort'), paleEl=document.getElementById('pale');
function esc(s){return s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
function hi(name,q){ if(!q) return esc(name);
  const i=name.toLowerCase().indexOf(q.toLowerCase());
  if(i<0) return esc(name);
  return esc(name.slice(0,i))+'<mark>'+esc(name.slice(i,i+q.length))+'</mark>'+esc(name.slice(i+q.length)); }
function gclass(g){ return g==='HE'?'HE':(g==='SHE'?'SHE':'U'); }

function render(){
  const q=qEl.value.trim(), key=sortEl.value, showPale=paleEl.checked;
  let rows=A.filter(r=>(showPale||r.reliable));
  if(q) rows=rows.filter(r=>r.name.toLowerCase().includes(q.toLowerCase()));
  rows.sort((a,b)=>b[key]-a[key]);
  const max=Math.max(1,...rows.map(r=>r[key]));
  const unit = key==='lemmas_per_1k' ? 'лемм/1k' : (key==='total_questions'?'вопр.':(key==='total_words'?'слов':'лемм'));
  document.getElementById('list').innerHTML = rows.map((r,i)=>{
    const w=Math.max(3,r[key]/max*100);
    const sub = `${fmt(r.total_questions)} вопр. · ${fmt(r.total_words)} слов · ${r.lemmas_per_1k} лемм/1k`;
    return `<div class="row ${r.reliable?'':'pale'}">
      <div class="rank">${i+1}</div>
      <div class="barcell">
        <div class="top">
          <div class="name"><span class="dot ${gclass(r.gender)}"></span>${hi(r.name,q)}</div>
          <div class="val">${fmt(r[key])}<small>${unit}</small></div>
        </div>
        <div class="track">
          <div class="fill" style="width:${w}%"></div>
          <div class="pac" style="left:${w}%"></div>
        </div>
        <div class="meta2">${sub}</div>
      </div>
    </div>`;
  }).join('') || '<p style="color:var(--muted);padding:20px 0">GAME OVER — ничего не найдено.</p>';
}
qEl.oninput=render; sortEl.onchange=render; paleEl.onchange=render;
render();
</script>
</body>
</html>
"""

out = os.path.join(HERE, "..", "index.html")
with open(out, "w") as f:
    f.write(HTML.replace("__DATA__", DATA))
print("wrote", out, f"({len(HTML)+len(DATA)} bytes, {len(report['authors'])} authors)")
