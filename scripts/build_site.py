#!/usr/bin/env python3
"""Собирает весь сайт (5 self-contained страниц, тема Pac-Man) из JSON-данных.

Страницы:
  index.html     — рейтинг словаря + раскрытие: слова-маркеры, темы, родственники
  method.html    — популярно про weighted log-odds
  coauthors.html — граф соавторства (canvas force-layout)
  years.html     — слово / имя / гео года + эволюция методы ЧГК
  cliches.html   — зачины вопросов и заезженные обороты
"""
import json, os
HERE = os.path.dirname(__file__); ROOT = os.path.join(HERE, "..")
def load(n): return json.load(open(os.path.join(ROOT, n)))
report = load("report.json"); coauthors = load("coauthors.json")
years = load("years.json"); cliches = load("cliches.json"); stoplist = load("stoplist.json")

NAV = [("index.html", "Рейтинг"), ("years.html", "Слово года"),
       ("coauthors.html", "Соавторы"), ("cliches.html", "Штампы"),
       ("method.html", "Как считаем"), ("pipeline.html", "Кухня")]

CSS = r"""
:root{--maze:#2A3FE5;--pac:#FFD400;--pink:#F4B9B0;
  --pixel:'Press Start 2P',monospace;--mono:'Space Mono','JetBrains Mono',ui-monospace,Menlo,monospace;}
html[data-theme="light"]{--bg:#FBFBF4;--panel:#FFFFFF;--text:#111827;--muted:#5b6472;
  --pellet:#c7cef0;--accent:#2A3FE5;--logo-shadow:#FFD400;--shadow:#dfe2f5;
  --fill1:#E0A800;--fill2:#FFD400;--pac-shadow:rgba(0,0,0,.28);--line:#e3e6f2;--chip:#eef0fb;}
html[data-theme="dark"]{--bg:#000000;--panel:#0a0d1a;--text:#F5F7FA;--muted:#8b93a7;
  --pellet:#3a4470;--accent:#FFD400;--logo-shadow:#2A3FE5;--shadow:#1a1f4d;
  --fill1:#8a7400;--fill2:#FFD400;--pac-shadow:transparent;--line:#1a1f4d;--chip:#141a30;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-family:var(--mono);font-size:14px;
  line-height:1.55;background-image:radial-gradient(var(--pellet) 1px,transparent 1px);
  background-size:22px 22px}
.wrap{max-width:980px;margin:0 auto;padding:22px 18px 90px}
a{color:var(--accent)}
.head{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
.logo{font-family:var(--pixel);color:var(--accent);font-size:22px;line-height:1.35;letter-spacing:1px;
  margin:0;text-shadow:3px 3px 0 var(--logo-shadow);text-decoration:none}
.logo .ghost{color:var(--pink)}
.theme{font-family:var(--pixel);font-size:10px;cursor:pointer;white-space:nowrap;background:var(--panel);
  color:var(--accent);border:2px solid var(--maze);border-radius:6px;padding:9px 10px;box-shadow:3px 3px 0 var(--shadow)}
.theme:focus-visible{outline:3px solid var(--pac);outline-offset:2px}
nav{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 6px}
nav a{font-family:var(--pixel);font-size:10px;text-decoration:none;color:var(--text);
  background:var(--panel);border:2px solid var(--maze);border-radius:6px;padding:8px 10px}
nav a.on{background:var(--maze);color:#fff}
nav a:hover{color:var(--pink)}
.links{display:flex;flex-wrap:wrap;gap:8px 14px;margin:6px 0 16px;font-size:12.5px}
.links a{color:var(--accent);text-decoration:none;font-weight:700;border-bottom:2px dotted var(--maze);padding-bottom:1px}
.links a:hover{color:var(--pink)}
h2{font-family:var(--pixel);font-size:15px;color:var(--accent);margin:26px 0 12px;line-height:1.4}
.lead{color:var(--text);max-width:720px}.lead b{color:var(--accent)}
.muted{color:var(--muted)}
.foot{color:var(--muted);font-size:12.5px;margin-top:38px;border-top:2px dotted var(--maze);padding-top:18px}
.stats{display:flex;flex-wrap:wrap;gap:12px;margin:16px 0 22px}
.stat{background:var(--panel);border:3px solid var(--maze);border-radius:8px;padding:12px 16px;min-width:130px;box-shadow:4px 4px 0 var(--shadow)}
.stat .n{font-family:var(--pixel);font-size:18px;color:var(--accent)}
.stat .l{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.06em;margin-top:8px}
.chip{display:inline-flex;align-items:baseline;gap:6px;background:var(--chip);border:1px solid var(--line);
  border-radius:6px;padding:4px 9px;margin:3px 4px 3px 0;font-size:13px}
.chip b{color:var(--accent)}.chip small{color:var(--muted);font-size:10.5px}
mark{background:var(--pac);color:#000;border-radius:3px;padding:0 2px}
"""

def head(title, active, extra=""):
    nav = "".join(f'<a href="{u}"{" class=\"on\"" if u==active else ""}>{t}</a>' for u, t in NAV)
    return f"""<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Space+Mono:wght@400;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<script>(function(){{var t=localStorage.getItem('chgk-theme')||'light';document.documentElement.setAttribute('data-theme',t);}})();</script>
<style>{CSS}{extra}</style></head><body><div class="wrap">
<div class="head"><a class="logo" href="index.html">CHGK <span class="ghost">LEXICON</span></a>
<button class="theme" id="theme" type="button" aria-label="Переключить тему"></button></div>
<nav>{nav}</nav>
<div class="links"><a href="https://t.me/newezha" target="_blank" rel="noopener">Невежда · @newezha</a>
<a href="https://t.me/tatarchgk" target="_blank" rel="noopener">Тат. школа ЧГК · @tatarchgk</a>
<a href="https://github.com/ImangulovA/chgk-vocab" target="_blank" rel="noopener">GitHub</a></div>
"""

FOOT = """<div class="foot"><p>Данные и профили авторов: база вопросов ЧГК
<a href="https://gotquestions.online/" target="_blank" rel="noopener">gotquestions.online</a>.
Метод «фирменных слов» — weighted log-odds (см. <a href="method.html">Как считаем</a>).
Дизайн — тема Pac-Man.</p></div></div>
<script>
var tb=document.getElementById('theme');
function pt(){var t=document.documentElement.getAttribute('data-theme');tb.textContent=t==='dark'?'☀ LIGHT':'☾ DARK';}
tb.onclick=function(){var c=document.documentElement.getAttribute('data-theme'),n=c==='dark'?'light':'dark';
document.documentElement.setAttribute('data-theme',n);localStorage.setItem('chgk-theme',n);pt();if(window.onThemeChange)window.onThemeChange();};
pt();
</script>
</body></html>"""

def w(name, html):
    open(os.path.join(ROOT, name), "w").write(html)
    print("wrote", name, f"({len(html)//1024} KB)")

# ============================ index.html ============================
def build_index():
    extra = r"""
.controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:0 0 12px;position:sticky;top:0;
  background:var(--bg);padding:12px 0;z-index:5;border-bottom:2px dotted var(--maze)}
input[type=search],select,label.tgl{font-family:var(--mono);font-size:13px;background:var(--panel);
  border:2px solid var(--maze);color:var(--text);border-radius:6px;padding:10px 12px}
input[type=search]{flex:1;min-width:200px}input[type=search]::placeholder{color:var(--muted)}
select,label.tgl{cursor:pointer}label.tgl{display:flex;align-items:center;gap:8px;user-select:none}
input:focus-visible,select:focus-visible{outline:3px solid var(--pac);outline-offset:2px}
input[type=checkbox]{accent-color:var(--maze);width:16px;height:16px}
.btn{font-family:var(--mono);font-size:13px;background:var(--panel);border:2px solid var(--maze);
  color:var(--text);border-radius:6px;padding:10px 12px;cursor:pointer}
.btn:focus-visible{outline:3px solid var(--pac);outline-offset:2px}
.btn.on{background:var(--maze);color:#fff}
.legend{color:var(--muted);font-size:12px;margin:6px 0 8px}
.row{display:grid;grid-template-columns:44px 1fr;gap:12px;align-items:center;padding:9px 0;border-bottom:1px dotted var(--line);cursor:pointer}
.rank{font-family:var(--pixel);color:var(--maze);text-align:right;font-size:11px}
.barcell{position:relative}
.top{display:flex;justify-content:space-between;align-items:baseline;gap:10px;margin-bottom:6px}
.name{font-weight:700;font-size:15px}.name .tw{color:var(--muted);font-weight:400;font-size:12px;margin-left:6px}
.name a{color:inherit;text-decoration:none;border-bottom:1px solid transparent}
.name a:hover{color:var(--accent);border-bottom-color:var(--accent)}
.val{font-family:var(--pixel);font-size:13px;color:var(--accent);white-space:nowrap}
.val small{font-family:var(--mono);color:var(--muted);font-weight:400;margin-left:8px;font-size:11px}
.track{position:relative;height:18px;border-radius:9px;background:radial-gradient(circle,var(--pellet) 2px,transparent 2.4px);background-size:14px 18px;background-position:8px center}
.fill{position:absolute;left:0;top:50%;transform:translateY(-50%);height:5px;border-radius:3px;background:linear-gradient(90deg,var(--fill1),var(--fill2));min-width:2px}
.pac{position:absolute;top:50%;width:18px;height:18px;transform:translate(-50%,-50%);background:var(--pac);border-radius:50%;
  filter:drop-shadow(1px 1px 0 var(--pac-shadow));clip-path:polygon(100% 32%,8% 4%,8% 96%,100% 68%)}
@media (prefers-reduced-motion:no-preference){.pac{animation:chomp .45s steps(1,jump-none) infinite alternate}}
@keyframes chomp{from{clip-path:polygon(100% 30%,8% 4%,8% 96%,100% 70%)}to{clip-path:polygon(100% 48%,8% 4%,8% 96%,100% 52%)}}
.meta2{color:var(--muted);font-size:11.5px;margin-top:6px}
.detail{grid-column:2;padding:4px 0 10px;font-size:13px}
.detail .lab{font-family:var(--pixel);font-size:9px;color:var(--muted);text-transform:uppercase;margin:8px 0 4px}
.pale .fill{background:linear-gradient(90deg,#a9b0c8,#c7cee0)}.pale .pac{background:var(--muted);animation:none;filter:none}
.pale .name,.pale .val{color:var(--muted)}.pale .rank{opacity:.55}
"""
    body = """
<p class="lead">У кого из авторов вопросов <b>«Что? Где? Когда?»</b> богаче словарный запас.
Метрика: число <b>уникальных лемм в первых 25&nbsp;000 словах</b> корпуса автора. Кликните строку,
чтобы увидеть <b>слова-маркеры</b>, <b>темы</b> и <b>родственных авторов</b>. Клик по имени — профиль.</p>
<div class="stats" id="stats"></div>
<div class="controls">
  <input type="search" id="q" placeholder="ПОИСК АВТОРА…" autocomplete="off" aria-label="Поиск автора">
  <select id="sort" aria-label="Сортировка">
    <option value="unique_lemmas">по богатству словаря</option>
    <option value="lemmas_per_1k">по плотности (лемм / 1000 слов)</option>
    <option value="total_questions">по числу вопросов</option>
    <option value="total_words">по объёму корпуса</option>
  </select>
  <select id="sim" aria-label="Способ подсчёта близости" title="Как считать родственных авторов">
    <option value="lex">соседи: по лексике</option>
    <option value="delta">соседи: по манере (Delta)</option>
    <option value="ngram">соседи: по буквосочетаниям</option>
    <option value="emb">соседи: по смыслу (нейросеть)</option>
  </select>
  <label class="tgl"><input type="checkbox" id="pale"> показать &lt;25k</label>
  <button type="button" class="btn" id="expand" aria-expanded="false">Раскрыть все разборы</button>
</div>
<div class="legend">Бледный ряд = корпус меньше 25&nbsp;000 слов. Клик по строке раскрывает разбор (слова-маркеры, темы, родственники), или кнопкой сразу у всех.</div>
<div id="list"></div>
"""
    script = """
<script>
const REPORT=__REPORT__;const A=REPORT.authors,M=REPORT.meta;const fmt=n=>n.toLocaleString('ru-RU');
document.getElementById('stats').innerHTML=[['надёжных',fmt(M.reliable)],['медиана',fmt(M.median_reliable_lemmas)],
['авторов',fmt(M.total_authors)],['вопросов',fmt(M.total_questions)]].map(([l,n])=>
`<div class="stat"><div class="n">${n}</div><div class="l">${l}</div></div>`).join('');
const qEl=q0('q'),sortEl=q0('sort'),paleEl=q0('pale'),expEl=q0('expand'),simEl=q0('sim');function q0(i){return document.getElementById(i);}
let allOpen=false,simMode='lex';
const SIMKEY={lex:'kindred',delta:'kindred_delta',ngram:'kindred_ngram',emb:'kindred_emb'};
const SIMLAB={lex:'по лексике',delta:'по манере (Delta)',ngram:'по буквосочетаниям',emb:'по смыслу (нейросеть)'};
function esc(s){return s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
function hi(n,q){if(!q)return esc(n);const i=n.toLowerCase().indexOf(q.toLowerCase());if(i<0)return esc(n);
return esc(n.slice(0,i))+'<mark>'+esc(n.slice(i,i+q.length))+'</mark>'+esc(n.slice(i+q.length));}
const KIND={surn:'фамилия',name:'имя',geo:'место',org:'организация'};
function detailHtml(r){
  const chip=x=>`<span class="chip"><b>${esc(x.lemma)}</b> <small>×${x.count}${x.others?', ещё у '+x.others:''}</small></span>`;
  const pchip=x=>`<span class="chip"><b>${esc(x.phrase)}</b> <small>×${x.count}</small></span>`;
  const kk=(r[SIMKEY[simMode]]||r.kindred||[]);
  const kin=kk.map(k=>`<a href="https://gotquestions.online/person/${k.pid}" target="_blank" rel="noopener">${esc(k.name)}</a>`).join(' · ');
  return `<div class="detail">
   <div class="lab">Слова-маркеры (стиль)</div>${r.sig_style.map(chip).join('')||'<span class="muted">—</span>'}
   <div class="lab">Темы (о чём чаще пишет)</div>${r.sig_theme.map(chip).join('')||'<span class="muted">—</span>'}
   <div class="lab">Фирменные обороты · 2 слова</div>${(r.sig_bi||[]).map(pchip).join('')||'<span class="muted">—</span>'}
   <div class="lab">Фирменные обороты · 3 слова</div>${(r.sig_tri||[]).map(pchip).join('')||'<span class="muted">—</span>'}
   <div class="lab">Родственные авторы · ${SIMLAB[simMode]}</div>${kin||'<span class="muted">—</span>'}
   <div class="lab" style="margin-top:10px"><a href="method.html">Как это посчитано?</a></div></div>`;
}
let CUR=[];
function render(){
  const q=qEl.value.trim(),key=sortEl.value,sp=paleEl.checked;
  let rows=A.filter(r=>(sp||r.reliable));if(q)rows=rows.filter(r=>r.name.toLowerCase().includes(q.toLowerCase()));
  rows.sort((a,b)=>b[key]-a[key]);CUR=rows;const max=Math.max(1,...rows.map(r=>r[key]));
  const unit=key==='lemmas_per_1k'?'лемм/1k':(key==='total_questions'?'вопр.':(key==='total_words'?'слов':'лемм'));
  q0('list').innerHTML=rows.map((r,i)=>{const wd=Math.max(3,r[key]/max*100);
    const nm=r.pid?`<a href="https://gotquestions.online/person/${r.pid}" target="_blank" rel="noopener">${hi(r.name,q)}</a>`:hi(r.name,q);
    return `<div class="row ${r.reliable?'':'pale'}" data-i="${i}">
      <div class="rank">${i+1}</div>
      <div class="barcell"><div class="top"><div class="name">${nm}</div>
        <div class="val">${fmt(r[key])}<small>${unit}</small></div></div>
        <div class="track"><div class="fill" style="width:${wd}%"></div><div class="pac" style="left:${wd}%"></div></div>
        <div class="meta2">${fmt(r.total_questions)} вопр. · ${fmt(r.total_words)} слов · ${r.lemmas_per_1k} лемм/1k</div>
      </div></div>${allOpen?'<div class="row drow">'+detailHtml(r)+'</div>':''}`;}).join('')||'<p class="muted" style="padding:20px 0">GAME OVER — ничего не найдено.</p>';
}
q0('list').addEventListener('click',e=>{
  if(e.target.closest('a'))return; const row=e.target.closest('.row'); if(!row||row.classList.contains('drow'))return;
  const nx=row.nextElementSibling;
  if(nx&&nx.classList.contains('drow')){nx.remove();return;}
  const r=CUR[+row.dataset.i];const div=document.createElement('div');div.className='row drow';
  div.innerHTML=detailHtml(r);row.after(div);
});
expEl.onclick=()=>{allOpen=!allOpen;expEl.classList.toggle('on',allOpen);
  expEl.setAttribute('aria-expanded',allOpen);
  expEl.textContent=allOpen?'Свернуть все разборы':'Раскрыть все разборы';render();};
simEl.onchange=()=>{simMode=simEl.value;
  if(allOpen){render();return;}
  document.querySelectorAll('.drow').forEach(d=>{const pr=d.previousElementSibling;
    if(pr&&pr.dataset.i!=null) d.innerHTML=detailHtml(CUR[+pr.dataset.i]);});};
qEl.oninput=render;sortEl.onchange=render;paleEl.onchange=render;render();
</script>
"""
    html = head("CHGK Lexicon — словарь авторов вопросов ЧГК", "index.html", extra) + body + FOOT
    html = html.replace("</body></html>", script + "</body></html>")
    w("index.html", html.replace("__REPORT__", json.dumps(report, ensure_ascii=False, separators=(",", ":"))))

# ============================ method.html ============================
def build_method():
    body = """
<h2>Как мы находим «фирменные слова» автора</h2>
<p class="lead">Хочется для каждого автора показать слова, которые звучат <b>именно как он</b>. Наивные
способы не работают:</p>
<p class="lead">• <b>«Самые частые слова»</b> — у всех получится «который», «это», «назвать». Скучно и одинаково.<br>
• <b>«Слова только у него»</b> — это почти всегда опечатки и случайные редкости, а не стиль.</p>
<h2>Идея: сравнить автора со всеми остальными</h2>
<p class="lead">Мы берём, как часто слово встречается <b>у автора</b>, и сравниваем с тем, как часто оно
встречается <b>во всём остальном корпусе</b>. Слово «фирменное», если у автора оно идёт заметно чаще,
чем в среднем по ЧГК. Формально это <b>логарифм отношения шансов</b> (log-odds): насколько сдвинуты
шансы встретить слово у автора против всех прочих.</p>
<h2>Поправка на редкость: приор</h2>
<p class="lead">У редких слов отношение шансов «скачет»: одно-два употребления — и слово будто бы
уникальное. Чтобы этого не было, мы добавляем <b>мягкий приор</b> (метод Monroe, Colaresi &amp; Quinn,
2008, «Fightin' Words»): как будто заранее видели каждое слово чуть-чуть, пропорционально его общей
частоте. Затем делим сдвиг на его погрешность и получаем <b>z-оценку</b>: насколько надёжно слово
отличает автора. Чем выше z, тем «фирменнее».</p>
<div class="stats">
  <div class="stat"><div class="n">z &gt; 3</div><div class="l">уверенный маркер</div></div>
  <div class="stat"><div class="n">×N</div><div class="l">сколько раз у автора</div></div>
  <div class="stat"><div class="n">ещё у K</div><div class="l">у скольких других авторов встречается</div></div>
</div>
<h2>Две колонки: стиль и темы</h2>
<p class="lead">Слова-маркеры мы делим на два вида по грамматике (через морфоанализатор pymorphy3):<br>
• <b>Темы</b> — имена, фамилии, города, организации: <i>о чём</i> автор любит спрашивать
(Плутарх, Тэтчер, Ливерпуль).<br>
• <b>Слова-маркеры</b> — нарицательная лексика: <i>как</i> он пишет (у Бориса Бурды это «каковой»,
«весьма», «совершенно» — его фирменный высокий штиль).</p>
<p class="lead">Тем же методом (log-odds) считаем <b>фирменные обороты</b> — словосочетания из 2 и 3 слов,
характерные для автора (у Бурды «представьте себе», «без труда догадаетесь», «пролетарии всех стран
соединяйтесь»). Общие для всего ЧГК штампы сюда не лезут: они не отличают автора.</p>
<p class="lead muted">Мелочь по чистоте данных: белорусские и украинские вопросы отсеиваем по буквам
і/ї/є/ґ/ў, снимаем знаки ударения перед разбором, а имена/места сверх этого прошли отдельный аудит
(LLM-агенты разметили обрывки, отчества и бренды-не-места, они в стоп-листе).</p>
<h2>Родственные авторы</h2>
<p class="lead">На сайте можно переключать <b>4 способа</b> искать похожих (селектор «соседи:» на главной), потому
что «похожи» бывает разное:</p>
<p class="lead">• <b>По лексике</b> — <b>стилевой отпечаток</b>: вектор слов, которыми автор выделяется (те же
z-оценки weighted log-odds по нарицательной лексике), косинус. Сравниваем характерность, а не объём, поэтому
плодовитые авторы не липнут ко всем.<br>
• <b>По манере (Delta)</b> — классическая стилометрия (Burrows/Eder): берём частоты самых частых, в основном
<b>служебных</b> слов, z-нормируем каждое по всем авторам и считаем косинус. Это «как устроена речь»,
почти без влияния темы.<br>
• <b>По буквосочетаниям</b> — профиль <b>символьных 3-грамм</b> (буквенных троек с границами слов), tf-idf +
косинус. Устойчивый к теме почерк на уровне морфологии.<br>
• <b>По смыслу (нейросеть)</b> — <b>doc2vec</b> (Paragraph Vectors): небольшая нейросеть, которую мы обучаем
<b>локально на нашем корпусе</b> (без внешних моделей). Каждый автор получает вектор-эмбеддинг, соседи по косинусу.
Ближе к «про одно и то же / общее семантическое поле».</p>
<p class="lead">Интересно, что соседи по разным способам часто разные: это и есть разные грани «похожести».</p>
<h2>Честные оговорки</h2>
<p class="lead">Метрика ловит <b>разнообразие и характерность</b> словаря, а не «ум» или качество
вопросов. Темы часто отражают эрудиционные пристрастия автора, а не стиль. А в корпусе последних лет
есть белорусские и украинские вопросы: часть шумных слов оттуда.</p>
"""
    w("method.html", head("Как считаем — CHGK Lexicon", "method.html") + body + FOOT)

# ============================ years.html ============================
def build_years():
    extra = """
.yr{display:grid;grid-template-columns:74px 1fr;gap:14px;align-items:start;padding:12px 0;border-bottom:1px dotted var(--line)}
.yn{font-family:var(--pixel);font-size:16px;color:var(--maze)}
.big{font-size:20px;font-weight:700;color:var(--accent)}
.kv{color:var(--muted);font-size:12.5px;margin-top:2px}.kv b{color:var(--text)}
details.excl{background:var(--panel);border:2px solid var(--maze);border-radius:8px;padding:10px 14px;margin:8px 0 18px;box-shadow:4px 4px 0 var(--shadow)}
details.excl summary{cursor:pointer;font-weight:700;color:var(--accent)}
details.excl .chip{font-size:12px;padding:2px 7px}
"""
    body = """
<h2>Слово, имя и место года в ЧГК</h2>
<p class="lead">Для каждого года ищем слова, которые в этот год звучали <b>заметно чаще обычного</b>
(та же weighted log-odds, только год против всех лет). Получается летопись: во что играл мир и о чём
спрашивали знатоки.</p>
<p class="lead muted">Видно эпохи: <b>90-е</b> — античность («римлянин», «грек»); <b>2020</b> —
«коронавирус», <b>2021</b> — «пандемия», <b>2022</b> — «ведьмак», <b>2025</b> — «нейросеть».
А «место года» почти всегда спортивное: Ванкувер (2010), Сочи (2014), Лестер (2017), Ливерпуль (2019).</p>
__EXCL__
<div id="list"></div>
"""
    meta_chips = "".join(f'<span class="chip">{w}</span>' for w in stoplist["meta_words"])
    stop_chips = "".join(f'<span class="chip">{w}</span>' for w in stoplist["stop_words"])
    excl = (f'<details class="excl"><summary>Какие слова мы не учитываем ({len(stoplist["meta_words"])} технических + '
            f'{len(stoplist["stop_words"])} служебных) — клик</summary>'
            '<p class="muted" style="margin-top:8px">Технический и форматный жаргон ЧГК (икс, замена, '
            'раздатка, бескрылка, синхрон, названия носителей и жанров) — выкидываем, чтобы «слово года» '
            'было про содержание, а не про механику вопроса:</p>'
            f'<div>{meta_chips}</div>'
            '<p class="muted" style="margin-top:12px">И служебные слова (предлоги, местоимения, союзы):</p>'
            f'<div>{stop_chips}</div></details>')
    body = body.replace("__EXCL__", excl)
    script = """
<script>
const Y=__YEARS__.years;const fmt=n=>n.toLocaleString('ru-RU');
function cell(x){return x?`<span class="big">${x.lemma}</span>`:'<span class="muted">—</span>';}
document.getElementById('list').innerHTML=Y.slice().reverse().map(y=>{
  const t5=y.top5.map(x=>x.lemma).join(', ');
  return `<div class="yr"><div class="yn">${y.year}</div><div>
    <div>${cell(y.word)} <span class="muted" style="font-size:12px">слово года</span></div>
    <div class="kv">Имя года: <b>${y.name?y.name.lemma:'—'}</b> &nbsp;·&nbsp; Место года: <b>${y.geo?y.geo.lemma:'—'}</b></div>
    <div class="kv">Ещё характерное: ${t5}</div>
    <div class="kv">${fmt(y.tokens)} слов в вопросах этого года</div>
  </div></div>`;}).join('');
</script>
"""
    html = head("Слово года — CHGK Lexicon", "years.html", extra) + body + FOOT
    html = html.replace("</body></html>", script + "</body></html>")
    w("years.html", html.replace("__YEARS__", json.dumps(years, ensure_ascii=False, separators=(",", ":"))))

# ============================ cliches.html ============================
def build_cliches():
    extra = """
.cols{display:grid;grid-template-columns:1fr 1fr;gap:26px}
@media(max-width:680px){.cols{grid-template-columns:1fr}}
.pr{display:grid;grid-template-columns:1fr auto;gap:8px;align-items:center;padding:5px 0;border-bottom:1px dotted var(--line)}
.pr .p{font-size:13.5px}.pr .c{font-family:var(--pixel);font-size:10px;color:var(--accent)}
.pbar{grid-column:1/-1;height:6px;border-radius:3px;background:linear-gradient(90deg,var(--fill1),var(--fill2))}
"""
    body = """
<h2>Штампы и клише ЧГК</h2>
<p class="lead">Как знатоки начинают вопросы и какими оборотами злоупотребляют. Считано по тексту
<b>всех 436 тысяч вопросов</b>. Классика жанра: <b>«Внимание, в вопросе...»</b>, <b>«Перед вами...»</b>,
<b>«...мы заменили на...»</b>, <b>«Назовите его двумя словами»</b>.</p>
<div class="cols">
  <div><h2>Как начинаются вопросы</h2><div id="op"></div></div>
  <div><h2>Заезженные обороты</h2><div id="tg"></div></div>
</div>
"""
    script = """
<script>
const C=__CLICHES__;const fmt=n=>n.toLocaleString('ru-RU');
function list(el,arr){const max=arr[0].count;el.innerHTML=arr.map(x=>
`<div class="pr"><span class="p">${x.phrase}</span><span class="c">${fmt(x.count)}</span>
<span class="pbar" style="width:${Math.max(4,x.count/max*100)}%"></span></div>`).join('');}
list(document.getElementById('op'),C.openers3.slice(0,22));
list(document.getElementById('tg'),C.trigrams.slice(0,22));
</script>
"""
    html = head("Штампы ЧГК — CHGK Lexicon", "cliches.html", extra) + body + FOOT
    html = html.replace("</body></html>", script + "</body></html>")
    w("cliches.html", html.replace("__CLICHES__", json.dumps(cliches, ensure_ascii=False, separators=(",", ":"))))

# ============================ coauthors.html ============================
def build_coauthors():
    extra = """
#wrapg{position:relative;border:3px solid var(--maze);border-radius:10px;background:var(--panel);
  box-shadow:5px 5px 0 var(--shadow);overflow:hidden}
#g{display:block;width:100%;height:600px;touch-action:none}
#tip{position:absolute;pointer-events:none;background:var(--bg);border:2px solid var(--maze);border-radius:6px;
  padding:6px 9px;font-size:12px;display:none;z-index:3;box-shadow:2px 2px 0 var(--shadow)}
#tip b{color:var(--accent)}
.cbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:0 0 10px}
#gs{font-family:var(--mono);font-size:13px;background:var(--panel);border:2px solid var(--maze);color:var(--text);
  border-radius:6px;padding:9px 12px;min-width:220px}
.tc{display:grid;grid-template-columns:34px 1fr auto auto;gap:10px 14px;align-items:baseline}
.tc .r{font-family:var(--pixel);font-size:10px;color:var(--maze);text-align:right}
.tc .nm a{color:var(--text);text-decoration:none;font-weight:700;border-bottom:1px solid transparent}
.tc .nm a:hover{color:var(--accent);border-bottom-color:var(--accent)}
.tc .v{font-family:var(--pixel);font-size:10px;color:var(--accent);white-space:nowrap}
.tc .v small{font-family:var(--mono);color:var(--muted);font-size:11px;margin-left:4px}
.tc .rowc{display:contents}.tc .rowc>*{padding:5px 0;border-bottom:1px dotted var(--line)}
"""
    body = """
<h2>Кто с кем пишет вопросы</h2>
<p class="lead">Граф соавторства по <b>всей базе</b>. Узел — автор, ребро — совместные вопросы; толще
ребро = чаще пишут вместе. Показаны связи силой <b id="wmin"></b>+ совместных вопросов, чтобы не утонуть в
одиночных парах. Наведите на узел, кликните — откроется профиль. Поиск подсвечивает автора.</p>
<div class="cbar"><input id="gs" type="search" placeholder="Найти автора в графе…" autocomplete="off"></div>
<div id="wrapg"><canvas id="g"></canvas><div id="tip"></div></div>
<p class="muted" id="gmeta" style="margin-top:10px"></p>
<h2>У кого больше всего связей</h2>
<p class="lead">По всей базе: с каким числом <b>разных</b> соавторов человек писал вопросы (и сколько всего
совместных вопросов). Клик по имени — профиль.</p>
<div class="tc">__TOPCONN__</div>
"""
    tc = "".join(
        f'<div class="rowc"><div class="r">{i+1}</div>'
        f'<div class="nm"><a href="https://gotquestions.online/person/{x["pid"]}" target="_blank" rel="noopener">{x["name"]}</a></div>'
        f'<div class="v">{x["partners"]}<small>соавторов</small></div>'
        f'<div class="v">{x["joint"]}<small>совм.</small></div></div>'
        for i, x in enumerate(coauthors.get("top_connected", [])))
    body = body.replace("__TOPCONN__", tc)
    script = """
<script>
const GD=__COAUTHORS__;
const cvs=document.getElementById('g'),ctx=cvs.getContext('2d'),tip=document.getElementById('tip');
const wrap=document.getElementById('wrapg');
document.getElementById('wmin').textContent=GD.meta.wmin;
document.getElementById('gmeta').textContent=
`Узлов: ${GD.meta.nodes} · связей: ${GD.meta.edges} · всего авторов с соавторством: ${GD.meta.total_authors} (пар: ${GD.meta.total_pairs}).`;
let W=0,H=600,DPR=Math.min(2,window.devicePixelRatio||1);
const nodes=GD.nodes.map(n=>({...n,x:0,y:0,vx:0,vy:0}));
const idx={};nodes.forEach((n,i)=>idx[n.id]=i);
const edges=GD.edges.map(e=>({a:idx[e.a],b:idx[e.b],w:e.w})).filter(e=>e.a!=null&&e.b!=null);
const maxDeg=Math.max(...nodes.map(n=>n.deg));
function rad(n){return 3+Math.sqrt(n.deg/maxDeg)*13;}
function resize(){W=wrap.clientWidth;cvs.width=W*DPR;cvs.height=H*DPR;cvs.style.height=H+'px';ctx.setTransform(DPR,0,0,DPR,0,0);}
// стартовые позиции по кругу
nodes.forEach((n,i)=>{const a=i/nodes.length*6.283;n.x=Math.cos(a)*220+ (i%7-3)*8;n.y=Math.sin(a)*220+(i%5-2)*8;});
function step(){
  const k=0.02;
  for(let i=0;i<nodes.length;i++){const a=nodes[i];
    for(let j=i+1;j<nodes.length;j++){const b=nodes[j];let dx=a.x-b.x,dy=a.y-b.y;let d2=dx*dx+dy*dy+0.01;
      let f=(rad(a)+rad(b)+30)*(rad(a)+rad(b)+30)/d2;if(f>1.2)f=1.2;const d=Math.sqrt(d2);
      const fx=dx/d*f,fy=dy/d*f;a.vx+=fx;a.vy+=fy;b.vx-=fx;b.vy-=fy;}
    a.vx-=a.x*k*0.02;a.vy-=a.y*k*0.02;}
  edges.forEach(e=>{const a=nodes[e.a],b=nodes[e.b];let dx=b.x-a.x,dy=b.y-a.y;let d=Math.sqrt(dx*dx+dy*dy)+0.01;
    const target=40+120/(e.w);const f=(d-target)*0.01*Math.min(3,e.w);const fx=dx/d*f,fy=dy/d*f;
    a.vx+=fx;a.vy+=fy;b.vx-=fx;b.vy-=fy;});
  nodes.forEach(n=>{if(n.fx==null){n.vx*=0.85;n.vy*=0.85;n.x+=n.vx;n.y+=n.vy;}});
}
let sx=0,sy=0,scale=1;
function fit(){let minx=1e9,miny=1e9,maxx=-1e9,maxy=-1e9;
  nodes.forEach(n=>{minx=Math.min(minx,n.x);miny=Math.min(miny,n.y);maxx=Math.max(maxx,n.x);maxy=Math.max(maxy,n.y);});
  const pad=40;scale=Math.min((W-pad*2)/(maxx-minx+1),(H-pad*2)/(maxy-miny+1));
  scale=Math.max(0.15,Math.min(2.2,scale));sx=W/2-(minx+maxx)/2*scale;sy=H/2-(miny+maxy)/2*scale;}
function T(n){return[n.x*scale+sx,n.y*scale+sy];}
let hoverI=-1,query='';
function accent(){return getComputedStyle(document.documentElement).getPropertyValue('--accent').trim();}
function draw(){
  ctx.clearRect(0,0,W,H);const ac=accent();
  ctx.lineWidth=1;
  edges.forEach(e=>{const[ax,ay]=T(nodes[e.a]),[bx,by]=T(nodes[e.b]);
    const hot=hoverI>=0&&(e.a===hoverI||e.b===hoverI);
    ctx.strokeStyle=hot?ac:'rgba(120,130,170,'+Math.min(.5,.08+e.w*0.02)+')';
    ctx.lineWidth=hot?2:Math.min(3,0.4+e.w*0.12);ctx.beginPath();ctx.moveTo(ax,ay);ctx.lineTo(bx,by);ctx.stroke();});
  nodes.forEach((n,i)=>{const[x,y]=T(n);const r=rad(n)*Math.min(1.4,scale>0?1:1);
    const match=query&&n.name.toLowerCase().includes(query);
    ctx.beginPath();ctx.arc(x,y,rad(n),0,6.283);
    ctx.fillStyle=(i===hoverI||match)?ac:(document.documentElement.getAttribute('data-theme')==='dark'?'#6b74a8':'#8b93c0');
    ctx.fill();
    if(i===hoverI||match){ctx.lineWidth=2;ctx.strokeStyle=ac;ctx.stroke();
      ctx.fillStyle=getComputedStyle(document.documentElement).getPropertyValue('--text').trim();
      ctx.font='11px "Space Mono",monospace';ctx.fillText(n.name,x+rad(n)+3,y+3);}});
}
let ticks=0;function loop(){if(ticks<320){step();ticks++;}fit();draw();requestAnimationFrame(loop);}
function pick(mx,my){let best=-1,bd=1e9;nodes.forEach((n,i)=>{const[x,y]=T(n);const d=(x-mx)**2+(y-my)**2;
  if(d<bd&&d<(rad(n)+6)**2){bd=d;best=i;}});return best;}
cvs.addEventListener('mousemove',e=>{const rct=cvs.getBoundingClientRect();const mx=e.clientX-rct.left,my=e.clientY-rct.top;
  const i=pick(mx,my);hoverI=i;
  if(i>=0){tip.style.display='block';tip.style.left=(mx+12)+'px';tip.style.top=(my+12)+'px';
    tip.innerHTML=`<b>${nodes[i].name}</b><br>${nodes[i].q} вопр. · связей: ${GD.edges.filter(e=>e.a===nodes[i].id||e.b===nodes[i].id).length}`;
    cvs.style.cursor='pointer';}else{tip.style.display='none';cvs.style.cursor='default';}});
cvs.addEventListener('mouseleave',()=>{hoverI=-1;tip.style.display='none';});
cvs.addEventListener('click',e=>{const rct=cvs.getBoundingClientRect();const i=pick(e.clientX-rct.left,e.clientY-rct.top);
  if(i>=0)window.open('https://gotquestions.online/person/'+nodes[i].pid,'_blank');});
// drag
let drag=-1;cvs.addEventListener('mousedown',e=>{const rct=cvs.getBoundingClientRect();drag=pick(e.clientX-rct.left,e.clientY-rct.top);});
window.addEventListener('mousemove',e=>{if(drag<0)return;const rct=cvs.getBoundingClientRect();
  const n=nodes[drag];n.x=((e.clientX-rct.left)-sx)/scale;n.y=((e.clientY-rct.top)-sy)/scale;n.fx=1;});
window.addEventListener('mouseup',()=>{if(drag>=0){nodes[drag].fx=null;}drag=-1;});
document.getElementById('gs').addEventListener('input',e=>{query=e.target.value.trim().toLowerCase();});
window.onThemeChange=draw;
window.addEventListener('resize',()=>{resize();});
resize();loop();
</script>
"""
    html = head("Соавторы — CHGK Lexicon", "coauthors.html", extra) + body + FOOT
    html = html.replace("</body></html>", script + "</body></html>")
    w("coauthors.html", html.replace("__COAUTHORS__", json.dumps(coauthors, ensure_ascii=False, separators=(",", ":"))))

# ============================ pipeline.html ============================
def build_pipeline():
    m = report["meta"]; cm = coauthors["meta"]
    extra = """
.step{display:grid;grid-template-columns:36px 1fr;gap:14px;align-items:start;margin:12px 0;
  background:var(--panel);border:2px solid var(--maze);border-radius:8px;padding:12px 14px;box-shadow:4px 4px 0 var(--shadow)}
.step .num{font-family:var(--pixel);font-size:14px;color:var(--pac);background:var(--maze);border-radius:6px;
  width:36px;height:36px;display:flex;align-items:center;justify-content:center}
.step h3{margin:0 0 4px;font-size:15px;color:var(--accent)}
.step code{background:var(--chip);border:1px solid var(--line);border-radius:4px;padding:1px 5px;font-size:12px}
pre{background:var(--panel);border:2px solid var(--maze);border-radius:8px;padding:12px 14px;overflow:auto;
  font-size:12.5px;line-height:1.5;box-shadow:4px 4px 0 var(--shadow)}
.formula{font-family:var(--mono);background:var(--chip);border:1px solid var(--line);border-radius:6px;
  padding:10px 12px;display:inline-block;font-size:13px}
ul.tight{margin:6px 0}ul.tight li{margin:3px 0}
"""
    body = f"""
<h2>Кухня: как это всё собрано</h2>
<p class="lead">Здесь без прикрас: откуда данные, что делают скрипты и по каким формулам считаются
метрики. Весь код открыт на <a href="https://github.com/ImangulovA/chgk-vocab" target="_blank" rel="noopener">GitHub</a>.</p>

<div class="stats">
  <div class="stat"><div class="n">6701</div><div class="l">пакетов вопросов</div></div>
  <div class="stat"><div class="n">{m['total_questions']:,}</div><div class="l">вопросов</div></div>
  <div class="stat"><div class="n">{m['total_authors']:,}</div><div class="l">авторов</div></div>
  <div class="stat"><div class="n">21,6 млн</div><div class="l">кириллических слов</div></div>
</div>

<h2>Откуда данные</h2>
<p class="lead">Источник — публичный дамп базы вопросов ЧГК с
<a href="https://gotquestions.online/" target="_blank" rel="noopener">gotquestions.online</a> (наследник
db.chgk.info). Один JSON на турнир/пакет, внутри — туры и вопросы:</p>
<pre>pack
 ├─ tours[]
 │   └─ questions[]
 │        ├─ text        // текст вопроса
 │        ├─ comment     // авторский комментарий
 │        ├─ answer / source / zachet ...
 │        └─ authors[] {{ id, name, gender }}   // id == профиль gotquestions.online/person/&lt;id&gt;</pre>
<p class="lead">Ключевой факт: <code>id</code> автора в дампе совпадает с id его профиля на сайте, поэтому
каждое имя на страницах кликабельно.</p>

<h2>Как строится корпус автора</h2>
<ul class="tight lead">
  <li>Берём <b>text + comment</b> каждого вопроса автора. Ответы и источники не считаем: это не авторская проза.</li>
  <li>Оставляем <b>только кириллические</b> токены (латиница, цифры, пунктуация выбрасываются),
      приводим к нижнему регистру.</li>
  <li>Лемматизируем морфоанализатором <b>pymorphy3</b> (каждое слово к начальной форме).</li>
  <li>Дедуп по глобальному <b>id вопроса</b>: один вопрос живёт в нескольких пакетах, но считается один раз.</li>
  <li>Со-авторский вопрос засчитывается <b>каждому</b> из соавторов.</li>
</ul>

<h2>Три шага пайплайна</h2>
<div class="step"><div class="num">1</div><div>
  <h3>build_report.py → report.json</h3>
  <p>Два прохода по всем пакетам: сперва считаем объём корпуса на автора и отбираем тех, у кого
  ≥ 10&nbsp;000 слов ({m['displayed']} авторов). Затем собираем их слова в хронологии и считаем главную
  метрику — <b>число уникальных лемм в первых 25&nbsp;000 словах</b> (окно как у Иноземцева). У кого корпус
  меньше 25k — «бледный» ряд ({m['reliable']} надёжных из {m['displayed']}).</p></div></div>
<div class="step"><div class="num">2</div><div>
  <h3>compute_features.py → report.json + coauthors/years/cliches.json</h3>
  <p>Тяжёлая часть, один проход + кэш. Считает фирменные слова (weighted log-odds), родственных авторов
  (tf-idf + косинус), граф соавторства, слово/имя/место года и штампы. Промежуточные счётчики кэшируются
  в <code>_raw.pkl</code>, так что перебор фильтров занимает секунды, а не минуты (пересчёт: <code>--fresh</code>).</p></div></div>
<div class="step"><div class="num">3</div><div>
  <h3>build_site.py → 6 страниц</h3>
  <p>Вшивает JSON прямо в HTML: каждая страница <b>самодостаточна</b> (данные внутри файла, ничего не грузится
  с бэкенда). Общие тема, навигация и переключатель светлая/тёмная.</p></div></div>

<h2>Фирменные слова: weighted log-odds</h2>
<p class="lead">Не «самые частые» (у всех выйдет «который») и не «только у него» (это опечатки). Сравниваем
частоту слова <b>у автора</b> и <b>во всём остальном корпусе</b>, со сглаживающим приором Дирихле
(Monroe, Colaresi &amp; Quinn, 2008). Итог — z-оценка «насколько надёжно слово отличает автора»:</p>
<p><span class="formula">δ = log( (y<sub>i</sub>+α<sub>w</sub>) / (n<sub>i</sub>−y<sub>i</sub>+…) ) − log( то же для «всех остальных» ) ;&nbsp; z = δ / √(вариация)</span></p>
<p class="lead">Слова делим на <b>темы</b> (имена, фамилии, города, организации — по морфо-тегам pymorphy
Surn/Name/Geox/Orgn) и <b>стиль</b> (нарицательная лексика). Подробнее — на странице
<a href="method.html">Как считаем</a>.</p>

<h2>Остальные метрики коротко</h2>
<ul class="tight lead">
  <li><b>Родственные авторы</b>: 4 способа на выбор (селектор «соседи:») — по лексике (log-odds отпечаток),
      по манере (Cosine Delta на служебных словах), по буквосочетаниям (символьные 3-граммы),
      по смыслу (локальный doc2vec, обучаем нейросеть на нашем корпусе). Считает <code>similarity.py</code>.</li>
  <li><b>Граф соавторства</b>: пары авторов по совместным вопросам; показываем связи силой ≥ {cm['wmin']}
      ({cm['nodes']} узлов, {cm['edges']} рёбер из {cm['total_pairs']} пар), чтобы не утонуть в одиночных.</li>
  <li><b>Слово/имя/место года</b>: та же log-odds, но «год против всех лет»; форматный жаргон ЧГК
      (икс, замена, раздатка, альфа) вынесен в стоп-лист.</li>
  <li><b>Фирменные обороты автора</b>: word би-/три-граммы по weighted log-odds (скрипт <code>phrases.py</code>) —
      характерные для автора словосочетания, а не общие штампы ЧГК.</li>
  <li><b>Штампы</b>: частоты зачинов (первые 2–4 слова) и триграмм по тексту всех вопросов.</li>
  <li><b>Чистка</b>: отсев бел/укр по буквам і/ї/є/ґ/ў, снятие ударений (U+0301), дедуп леммы на вопрос,
      + LLM-аудит имён/мест (обрывки, отчества, бренды-не-места в стоп-листе).</li>
</ul>

<h2>Честные оговорки</h2>
<ul class="tight lead">
  <li>Метрика словаря — про <b>разнообразие</b>, а не про «ум» или качество вопросов.</li>
  <li>«Темы» отражают эрудиционные пристрастия автора, а не манеру письма.</li>
  <li>В корпусе последних лет есть белорусские и украинские вопросы — часть шумных слов оттуда.</li>
  <li>Мы публикуем только агрегаты и код; сам дамп вопросов (чужой контент) не выкладываем.</li>
</ul>
"""
    w("pipeline.html", head("Кухня — CHGK Lexicon", "pipeline.html", extra) + body + FOOT)

build_index(); build_method(); build_years(); build_cliches(); build_coauthors(); build_pipeline()
print("site built")
