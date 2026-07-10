"""Внутренние страницы Aurora (aurora://home, aurora://history и т.д.).

Оформление — фирменный стиль «северное сияние»: ночное небо, живые ленты сияния
на новой вкладке, моноширинные адреса. Реализованы через собственный URL-scheme
и обработчик, который сам рендерит HTML и выполняет действия по параметрам URL.
"""
from __future__ import annotations

import html
import time
from datetime import datetime

from PyQt6.QtCore import QBuffer, QByteArray, QIODevice, QUrl, QUrlQuery
from PyQt6.QtWebEngineCore import QWebEngineUrlSchemeHandler

SCHEME = "aurora"

# Градиенты для плиток «часто посещаемых» (циклически).
TILE_GRADS = [
    "linear-gradient(135deg,#3aa0ff,#7c5cff)",
    "linear-gradient(135deg,#24292e,#57606a)",
    "linear-gradient(135deg,#ff5f6d,#ffc371)",
    "linear-gradient(135deg,#11998e,#38ef7d)",
    "linear-gradient(135deg,#ee0979,#ff6a00)",
    "linear-gradient(135deg,#8e2de2,#4a00e0)",
    "linear-gradient(135deg,#00c6ff,#0072ff)",
    "linear-gradient(135deg,#f7971e,#ffd200)",
]

DARK_TOKENS = {
    "bg": "#0b0e18", "bg2": "#0e1220", "surface": "#151a2b", "surface2": "#1b2136",
    "line": "#262d47", "text": "#e9edfb", "muted": "#8b93b3", "tile": "#141a2c",
    "teal": "#4fe0c4", "violet": "#9d8bff", "magenta": "#ff8bd0", "accent": "#7c8cff",
    "glass": "rgba(20,26,44,.62)", "aurora": "1",
}
LIGHT_TOKENS = {
    "bg": "#eef1fa", "bg2": "#e6eaf6", "surface": "#ffffff", "surface2": "#f4f6fd",
    "line": "#dbe0f0", "text": "#141a2e", "muted": "#5b6484", "tile": "#ffffff",
    "teal": "#12b3a0", "violet": "#6d5cff", "magenta": "#e05fae", "accent": "#5b6cff",
    "glass": "rgba(255,255,255,.72)", "aurora": ".5",
}


def _fmt_time(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%d.%m.%Y %H:%M")


def _tokens_css(theme: str) -> str:
    t = LIGHT_TOKENS if theme == "light" else DARK_TOKENS
    scheme = "light" if theme == "light" else "dark"
    body = ";".join(f"--{k}:{v}" for k, v in t.items())
    return f":root{{{body};color-scheme:{scheme}}}"


STATIC_CSS = """
*{box-sizing:border-box}
html,body{margin:0}
body{
  background:
    radial-gradient(1100px 640px at 82% -8%, color-mix(in srgb,var(--violet) 16%,transparent),transparent 60%),
    radial-gradient(900px 560px at 8% -4%, color-mix(in srgb,var(--teal) 12%,transparent),transparent 55%),
    linear-gradient(180deg,var(--bg),var(--bg2));
  color:var(--text); min-height:100vh;
  font-family:system-ui,-apple-system,'Segoe UI',Roboto,Inter,sans-serif;
  -webkit-font-smoothing:antialiased;
}
a{color:var(--accent);text-decoration:none}
.mono{font-family:ui-monospace,'SF Mono','JetBrains Mono','Cascadia Code',monospace}
.wrap{max-width:980px;margin:0 auto;padding:26px 24px 90px;position:relative;z-index:2}
.nav{display:flex;gap:18px;align-items:center;margin-bottom:26px}
.nav a{color:var(--muted);font-weight:600;font-size:14px}
.nav a:hover{color:var(--text)}
.brand{font-weight:850;font-size:20px;letter-spacing:-.02em;display:flex;align-items:center;margin-right:auto}
.dot{width:9px;height:9px;border-radius:50%;margin-left:5px;
  background:radial-gradient(circle at 30% 30%,#fff,var(--teal) 45%,var(--violet));
  box-shadow:0 0 14px var(--teal)}
h1{font-size:26px;letter-spacing:-.02em;margin:6px 0 20px}
.muted{color:var(--muted)}
.chip{font-size:11px;padding:3px 9px;border-radius:999px;border:1px solid var(--line);color:var(--muted)}
.card{background:var(--surface);border:1px solid var(--line);border-radius:14px;
  padding:12px 14px;margin:10px 0;display:flex;align-items:center;gap:12px}
.card .ic{width:34px;height:34px;border-radius:10px;background:var(--surface2);
  display:grid;place-items:center;flex:none;font-size:16px}
.card .grow{flex:1;min-width:0}
.card .grow b{font-size:14px;font-weight:600;display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.card .grow small{color:var(--muted);font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:block}
.time{color:var(--muted);font-size:12px;white-space:nowrap;font-variant-numeric:tabular-nums}
.btn{background:var(--accent);color:#fff;border:none;border-radius:10px;padding:8px 14px;
  cursor:pointer;font-size:13px;display:inline-flex;align-items:center;gap:6px}
.btn:hover{filter:brightness(1.08)}
.btn.ghost{background:transparent;border:1px solid var(--line);color:var(--text)}
.btn.danger{background:transparent;border:1px solid color-mix(in srgb,#ff7a85 45%,var(--line));color:#ff7a85}
.toolbar{display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap}
input[type=text],input[type=search],select{width:100%;padding:12px 14px;font-size:15px;
  border-radius:12px;border:1px solid var(--line);background:var(--bg);color:var(--text)}
.toggle{width:42px;height:24px;border-radius:999px;position:relative;flex:none;display:inline-block;
  background:linear-gradient(90deg,var(--teal),var(--violet))}
.toggle.off{background:var(--surface2)}
.toggle::after{content:'';position:absolute;top:3px;right:3px;width:18px;height:18px;border-radius:50%;background:#fff;transition:.15s}
.toggle.off::after{right:auto;left:3px}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:18px 20px;margin:12px 0}
.panel h3{margin:0 0 12px;font-size:15px}
"""


def _shell(title: str, body: str, theme: str = "dark", canvas: bool = False,
           extra_js: str = "") -> str:
    canvas_html = '<canvas id="aurora"></canvas>' if canvas else ""
    canvas_css = (
        "#aurora{position:fixed;inset:0;width:100vw;height:100vh;z-index:0;"
        "opacity:var(--aurora);pointer-events:none}"
        "@media (prefers-reduced-motion:reduce){#aurora{display:none}}"
    ) if canvas else ""
    canvas_js = AURORA_JS if canvas else ""
    return (
        "<!doctype html><html lang='ru'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{html.escape(title)}</title><style>"
        + _tokens_css(theme) + STATIC_CSS + canvas_css +
        "</style></head><body>" + canvas_html +
        "<div class='wrap'>"
        "<div class='nav'>"
        "<div class='brand'>Aurora<span class='dot'></span></div>"
        "<a href='aurora://home'>Главная</a>"
        "<a href='aurora://history'>История</a>"
        "<a href='aurora://bookmarks'>Закладки</a>"
        "<a href='aurora://downloads'>Загрузки</a>"
        "<a href='aurora://extensions'>Расширения</a>"
        "<a href='aurora://settings'>Настройки</a>"
        "</div>"
        + body +
        "</div>"
        "<script>if(location.search){history.replaceState(null,'',location.href.split('?')[0]);}"
        + canvas_js + extra_js + "</script></body></html>"
    )


AURORA_JS = """
(function(){
  var cv=document.getElementById('aurora'); if(!cv) return;
  if(matchMedia('(prefers-reduced-motion:reduce)').matches) return;
  var ctx=cv.getContext('2d'),W,H,dpr;
  function resize(){dpr=Math.min(devicePixelRatio||1,2);W=innerWidth;H=innerHeight;
    cv.width=W*dpr;cv.height=H*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);}
  addEventListener('resize',resize);resize();
  var R=[{a:'#4fe0c4',b:'#7c8cff',amp:60,y:0.34,sp:0.00035,ph:0},
         {a:'#9d8bff',b:'#ff8bd0',amp:80,y:0.46,sp:0.00026,ph:2},
         {a:'#4fe0c4',b:'#9d8bff',amp:50,y:0.28,sp:0.00045,ph:4}];
  function draw(t){
    ctx.clearRect(0,0,W,H);ctx.globalCompositeOperation='lighter';
    for(var i=0;i<R.length;i++){var r=R[i];
      var g=ctx.createLinearGradient(0,0,W,0);
      g.addColorStop(0,r.a+'00');g.addColorStop(.5,r.a+'4d');g.addColorStop(1,r.b+'00');
      ctx.beginPath();
      for(var x=0;x<=W;x+=8){var y=H*r.y+Math.sin(x*0.006+t*r.sp+r.ph)*r.amp
        +Math.sin(x*0.013+t*r.sp*1.7)*r.amp*0.35; x===0?ctx.moveTo(x,y):ctx.lineTo(x,y);}
      ctx.lineTo(W,H);ctx.lineTo(0,H);ctx.closePath();
      ctx.fillStyle=g;ctx.globalAlpha=.5;ctx.fill();ctx.globalAlpha=1;}
    ctx.globalCompositeOperation='source-over';requestAnimationFrame(draw);
  }
  requestAnimationFrame(draw);
})();
"""


class Pages:
    """Генерирует HTML внутренних страниц. Действия выполняет контроллер."""

    def __init__(self, controller) -> None:
        self.c = controller

    # ---------- Главная / новая вкладка ----------
    def home(self) -> str:
        cfg = self.c.config
        engine = cfg.get("search_engine")
        domain = engine.split("/")[2] if "//" in engine else "поиске"
        top = self.c.db.top_sites(8)
        tiles = ""
        for i, s in enumerate(top):
            label = html.escape((s.title or s.url)[:14])
            letter = html.escape((s.title or s.url).lstrip("htps:/").upper()[:1] or "•")
            grad = TILE_GRADS[i % len(TILE_GRADS)]
            tiles += (
                f'<a class="tile" href="{html.escape(s.url)}">'
                f'<div class="g" style="background:{grad}">{letter}</div>'
                f'<span>{label}</span></a>'
            )
        if not tiles:
            tiles = '<div class="muted">Часто посещаемые сайты появятся здесь.</div>'

        css = (
            ".hero{min-height:64vh;display:flex;flex-direction:column;align-items:center;justify-content:center}"
            ".big{font-weight:850;font-size:48px;letter-spacing:-.03em;display:flex;align-items:center;margin-bottom:24px}"
            ".big .dot{width:13px;height:13px;margin-left:7px}"
            ".search{width:min(560px,100%);display:flex;align-items:center;gap:12px;background:var(--glass);"
            "border:1px solid var(--line);border-radius:16px;padding:15px 18px;backdrop-filter:blur(12px);"
            "box-shadow:0 24px 60px -28px rgba(0,0,0,.6)}"
            ".search:focus-within{border-color:color-mix(in srgb,var(--accent) 60%,var(--line));"
            "box-shadow:0 0 0 4px color-mix(in srgb,var(--accent) 18%,transparent)}"
            ".search input{all:unset;flex:1;font-size:16px;color:var(--text)}"
            ".search .k{color:var(--muted);border:1px solid var(--line);border-radius:6px;padding:2px 8px;font-size:11px}"
            ".tiles{display:flex;gap:14px;margin-top:30px;flex-wrap:wrap;justify-content:center}"
            ".tile{width:92px;height:92px;border-radius:16px;background:var(--tile);border:1px solid var(--line);"
            "display:flex;flex-direction:column;align-items:center;justify-content:center;gap:9px;transition:transform .15s,border-color .15s}"
            ".tile:hover{transform:translateY(-3px);border-color:color-mix(in srgb,var(--accent) 45%,var(--line))}"
            ".tile .g{width:38px;height:38px;border-radius:12px;display:grid;place-items:center;font-weight:800;color:#fff;font-size:17px}"
            ".tile span{font-size:11.5px;color:var(--muted)}"
        )
        body = (
            f"<style>{css}</style>"
            '<div class="hero">'
            '<div class="big">Aurora<span class="dot"></span></div>'
            '<form class="search" onsubmit="return go(event)">'
            '<span class="muted">🔍</span>'
            f'<input id="q" autofocus placeholder="Найдётся всё — поиск в {html.escape(domain)} или адрес">'
            '<span class="k">⏎</span></form>'
            f'<div class="tiles">{tiles}</div>'
            '</div>'
        )
        go_js = (
            "function go(e){e.preventDefault();var v=document.getElementById('q').value.trim();"
            "if(!v)return false;"
            "if(/^https?:\\/\\//.test(v)||(/^[\\w-]+\\.[\\w.-]+/.test(v)&&v.indexOf(' ')<0)){"
            "location.href=v.indexOf('http')===0?v:'http://'+v;}else{"
            "location.href=" + repr(engine) + ".replace('{q}',encodeURIComponent(v));}return false;}"
        )
        return _shell("Новая вкладка", body, cfg.get("theme"), canvas=True, extra_js=go_js)

    # ---------- История ----------
    def history(self, query: str = "") -> str:
        items = self.c.db.search_history(query)
        rows = ""
        for it in items:
            letter = html.escape((it.title or it.url).lstrip("htps:/").upper()[:1] or "•")
            rows += (
                '<div class="card">'
                f'<div class="ic">{letter}</div>'
                '<div class="grow">'
                f'<b><a href="{html.escape(it.url)}">{html.escape(it.title or it.url)}</a></b>'
                f'<small class="mono">{html.escape(it.url)}</small></div>'
                f'<span class="time">{_fmt_time(it.visited)}</span>'
                f'<a class="btn danger" href="aurora://history?delete={it.id}">Удалить</a>'
                '</div>'
            )
        if not rows:
            rows = '<div class="muted">Записей нет.</div>'
        synced = self.c.config.get("sync_enabled")
        chip = ("синхронизация Google · вкл" if synced else "синхронизация Google · выкл")
        body = (
            f'<h1>История <span class="chip">только твоя · {chip}</span></h1>'
            '<div class="toolbar">'
            '<form action="aurora://history" style="flex:1">'
            f'<input type="search" name="q" value="{html.escape(query)}" placeholder="Поиск по истории"></form>'
            '<a class="btn ghost" href="aurora://history?add=1">＋ Добавить запись</a>'
            '<a class="btn danger" href="aurora://history?clear=1" '
            "onclick=\"return confirm('Очистить всю историю?')\">Очистить всё</a>"
            '</div>'
            + rows
        )
        return _shell("История", body, self.c.config.get("theme"))

    def history_add_form(self) -> str:
        body = (
            "<h1>Добавить запись в историю</h1>"
            '<div class="panel"><form action="aurora://history" method="get">'
            '<p><input type="text" name="url" placeholder="https://example.com" required></p>'
            '<p><input type="text" name="title" placeholder="Заголовок (необязательно)"></p>'
            '<input type="hidden" name="save" value="1">'
            '<button class="btn" type="submit">Сохранить</button> '
            '<a class="btn ghost" href="aurora://history">Отмена</a>'
            '</form></div>'
        )
        return _shell("Добавить в историю", body, self.c.config.get("theme"))

    # ---------- Закладки ----------
    def bookmarks(self) -> str:
        rows = ""
        for b in self.c.db.all_bookmarks():
            letter = html.escape((b["title"] or b["url"]).lstrip("htps:/").upper()[:1] or "•")
            rows += (
                '<div class="card">'
                f'<div class="ic">{letter}</div>'
                '<div class="grow">'
                f'<b><a href="{html.escape(b["url"])}">{html.escape(b["title"])}</a></b>'
                f'<small class="mono">{html.escape(b["url"])}</small></div>'
                f'<a class="btn danger" href="aurora://bookmarks?delete={html.escape(b["url"])}">Удалить</a>'
                '</div>'
            )
        if not rows:
            rows = '<div class="muted">Пока нет закладок. Нажми ☆ в адресной строке.</div>'
        return _shell("Закладки", f"<h1>Закладки</h1>{rows}", self.c.config.get("theme"))

    # ---------- Загрузки ----------
    def downloads(self) -> str:
        rows = ""
        for d in self.c.db.all_downloads():
            size = f"{d['size']/1_048_576:.1f} МБ" if d["size"] else ""
            rows += (
                '<div class="card"><div class="ic">⬇</div><div class="grow">'
                f'<b>{html.escape(d["path"].split("/")[-1])}</b>'
                f'<small class="mono">{html.escape(d["url"])}</small></div>'
                f'<span class="chip">{html.escape(d["state"])}</span>'
                f'<span class="time">{size}</span></div>'
            )
        if not rows:
            rows = '<div class="muted">Загрузок пока нет.</div>'
        return _shell("Загрузки", f"<h1>Загрузки</h1>{rows}", self.c.config.get("theme"))

    # ---------- Расширения ----------
    def extensions(self) -> str:
        rows = ""
        for e in self.c.extensions.load_all():
            off = "" if e.enabled else " off"
            rows += (
                '<div class="card"><div class="ic">🧩</div><div class="grow">'
                f'<b>{html.escape(e.name)} <span class="chip">v{html.escape(e.version)}</span></b>'
                f'<small>{html.escape(e.description)}</small></div>'
                f'<a href="aurora://extensions?toggle={html.escape(e.id)}" title="Вкл/выкл">'
                f'<span class="toggle{off}"></span></a>'
                f'<a class="btn danger" href="aurora://extensions?remove={html.escape(e.id)}">Удалить</a>'
                '</div>'
            )
        if not rows:
            rows = '<div class="muted">Расширений пока нет.</div>'
        body = (
            '<h1>Расширения <span class="chip">из файлов</span></h1>'
            '<div class="toolbar">'
            '<a class="btn" href="aurora://extensions?install=1">＋ Установить из файла</a>'
            f'<span class="muted" style="align-self:center">Папка: <span class="mono">{html.escape(str(self.c.extensions.ext_dir))}</span></span>'
            '</div>'
            '<div class="muted" style="margin-bottom:14px">'
            'Формат Aurora: папка с <span class="mono">manifest.json</span> + JS/CSS. '
            'Настоящие Chrome-расширения из Web Store движок не поддерживает — '
            'используется открытый формат в стиле userscript.</div>'
            + rows
        )
        return _shell("Расширения", body, self.c.config.get("theme"))

    # ---------- Настройки ----------
    def settings(self) -> str:
        cfg = self.c.config
        from .config import SEARCH_ENGINES

        engines = "".join(
            f'<option value="{html.escape(url)}" {"selected" if url==cfg.get("search_engine") else ""}>{name}</option>'
            for name, url in SEARCH_ENGINES.items()
        )
        signed = self.c.sync.is_signed_in() if self.c.sync else False
        sync_block = (
            '<div class="muted">Выполнен вход в Google. Синхронизируется только твоя история и закладки.</div>'
            '<a class="btn danger" href="aurora://settings?signout=1">Выйти</a>'
            if signed else
            '<a class="btn" href="aurora://settings?signin=1">Войти через Google для синхронизации</a>'
        )
        body = (
            "<h1>Настройки</h1>"
            '<div class="panel"><h3>Поиск</h3>'
            '<form action="aurora://settings" method="get" style="display:flex;gap:10px;flex-wrap:wrap">'
            f'<select name="engine" style="max-width:220px">{engines}</select>'
            '<button class="btn" name="save" value="1">Сохранить</button></form></div>'
            '<div class="panel"><h3>Тема</h3>'
            '<a class="btn ghost" href="aurora://settings?theme=dark">🌙 Тёмная (ночное небо)</a> '
            '<a class="btn ghost" href="aurora://settings?theme=light">☀️ Светлая</a></div>'
            '<div class="panel"><h3>Синхронизация через Google</h3>'
            '<p class="muted">Только твоя история и закладки, между твоими устройствами. Чужие данные не собираются.</p>'
            f'{sync_block}'
            f'<p><a class="btn ghost" href="aurora://settings?synctoggle=1">'
            f'{"Отключить" if cfg.get("sync_enabled") else "Включить"} авто-синхронизацию</a> '
            '<a class="btn ghost" href="aurora://settings?syncnow=1">Синхронизировать сейчас</a></p></div>'
            '<div class="panel"><h3>Приватность</h3>'
            f'<a class="btn ghost" href="aurora://settings?dnt=1">Do Not Track: {"вкл" if cfg.get("do_not_track") else "выкл"}</a> '
            f'<a class="btn ghost" href="aurora://settings?ads=1">Блокировка рекламы: {"вкл" if cfg.get("block_ads") else "выкл"}</a></div>'
            f'<div class="muted">Aurora {self.c.version} · движок Chromium (QtWebEngine), без Electron</div>'
        )
        return _shell("Настройки", body, cfg.get("theme"))


class AuroraSchemeHandler(QWebEngineUrlSchemeHandler):
    """Обрабатывает запросы aurora://… : выполняет действия и отдаёт HTML."""

    def __init__(self, controller) -> None:
        super().__init__()
        self.c = controller
        self.pages = Pages(controller)

    def requestStarted(self, job) -> None:  # noqa: N802 (Qt override)
        url = job.requestUrl()
        host = url.host() or "home"
        q = QUrlQuery(url)
        html_out = self._route(host, q)
        data = QByteArray(html_out.encode("utf-8"))
        buf = QBuffer(job)
        buf.setData(data)
        buf.open(QIODevice.OpenModeFlag.ReadOnly)
        job.reply(b"text/html", buf)

    def _route(self, host: str, q: QUrlQuery) -> str:
        c = self.c
        p = self.pages
        if host == "history":
            if q.hasQueryItem("delete"):
                c.db.delete_history(int(q.queryItemValue("delete")))
            elif q.hasQueryItem("clear"):
                c.db.clear_history()
            elif q.hasQueryItem("add"):
                return p.history_add_form()
            elif q.hasQueryItem("save"):
                c.db.add_history_entry(
                    q.queryItemValue("url"), q.queryItemValue("title"), time.time()
                )
            return p.history(q.queryItemValue("q") if q.hasQueryItem("q") else "")
        if host == "bookmarks":
            if q.hasQueryItem("delete"):
                c.db.remove_bookmark(q.queryItemValue("delete"))
            return p.bookmarks()
        if host == "downloads":
            return p.downloads()
        if host == "extensions":
            if q.hasQueryItem("toggle"):
                eid = q.queryItemValue("toggle")
                cur = {e.id: e.enabled for e in c.extensions.load_all()}.get(eid, True)
                c.extensions.set_enabled(eid, not cur)
                c.reload_extensions()
            elif q.hasQueryItem("remove"):
                c.extensions.uninstall(q.queryItemValue("remove"))
                c.reload_extensions()
            elif q.hasQueryItem("install"):
                c.install_extension_dialog()
            return p.extensions()
        if host == "settings":
            self._settings_actions(q)
            return p.settings()
        return p.home()

    def _settings_actions(self, q: QUrlQuery) -> None:
        c = self.c
        if q.hasQueryItem("theme"):
            c.config.set("theme", q.queryItemValue("theme"))
        elif q.hasQueryItem("save") and q.hasQueryItem("engine"):
            c.config.set("search_engine", q.queryItemValue("engine"))
        elif q.hasQueryItem("dnt"):
            c.config.set("do_not_track", not c.config.get("do_not_track"))
        elif q.hasQueryItem("ads"):
            c.config.set("block_ads", not c.config.get("block_ads"))
        elif q.hasQueryItem("synctoggle"):
            c.config.set("sync_enabled", not c.config.get("sync_enabled"))
        elif q.hasQueryItem("signin"):
            c.google_sign_in()
        elif q.hasQueryItem("signout"):
            c.google_sign_out()
        elif q.hasQueryItem("syncnow"):
            c.sync_now()
