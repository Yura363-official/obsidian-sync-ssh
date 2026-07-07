"""Внутренние страницы Aurora (aurora://home, aurora://history и т.д.).

Реализованы через собственный URL-scheme и обработчик, который сам рендерит HTML
и выполняет действия (удалить запись истории, включить расширение) по параметрам URL.
"""
from __future__ import annotations

import html
import time
from datetime import datetime

from PyQt6.QtCore import QBuffer, QByteArray, QIODevice, QUrl, QUrlQuery
from PyQt6.QtWebEngineCore import QWebEngineUrlSchemeHandler

SCHEME = "aurora"


def _fmt_time(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%d.%m.%Y %H:%M")


def _shell(title: str, body: str, theme: str = "dark") -> str:
    dark = theme != "light"
    bg = "#0f1220" if dark else "#f6f7fb"
    fg = "#e7e9f3" if dark else "#1a1d29"
    card = "#191d2e" if dark else "#ffffff"
    muted = "#8b90a6" if dark else "#6b7280"
    accent = "#6c8cff"
    border = "#262b40" if dark else "#e5e7eb"
    return f"""<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
  :root {{ color-scheme: {'dark' if dark else 'light'}; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; font-family: -apple-system, 'Segoe UI', Roboto, Inter, sans-serif;
         background:{bg}; color:{fg}; }}
  a {{ color:{accent}; text-decoration:none; }}
  .wrap {{ max-width: 980px; margin: 0 auto; padding: 32px 24px 80px; }}
  h1 {{ font-size: 26px; margin: 8px 0 20px; }}
  .muted {{ color:{muted}; }}
  .card {{ background:{card}; border:1px solid {border}; border-radius:14px;
          padding:14px 16px; margin:10px 0; }}
  .row {{ display:flex; align-items:center; gap:12px; }}
  .row .grow {{ flex:1; min-width:0; }}
  .row .grow div {{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
  .btn {{ background:{accent}; color:#fff; border:none; border-radius:9px;
         padding:8px 14px; cursor:pointer; font-size:14px; }}
  .btn.ghost {{ background:transparent; border:1px solid {border}; color:{fg}; }}
  .btn.danger {{ background:#e5484d; }}
  input[type=text], input[type=search] {{ width:100%; padding:12px 14px; font-size:15px;
         border-radius:11px; border:1px solid {border}; background:{bg}; color:{fg}; }}
  .toolbar {{ display:flex; gap:10px; margin-bottom:16px; flex-wrap:wrap; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:12px; }}
  .tile {{ background:{card}; border:1px solid {border}; border-radius:14px; padding:18px;
          text-align:center; }}
  .tile .ico {{ font-size:26px; }}
  .pill {{ font-size:12px; padding:3px 9px; border-radius:20px; background:{bg};
          border:1px solid {border}; color:{muted}; }}
  .nav {{ display:flex; gap:16px; margin-bottom:24px; flex-wrap:wrap; }}
  .nav a {{ color:{muted}; font-weight:600; }}
  .nav a.active {{ color:{fg}; }}
  .brand {{ font-weight:800; font-size:20px; letter-spacing:.3px; }}
  .brand span {{ color:{accent}; }}
</style></head><body><div class="wrap">
<div class="nav">
  <div class="brand" style="margin-right:auto">Aurora<span>·</span></div>
  <a href="aurora://home">Главная</a>
  <a href="aurora://history">История</a>
  <a href="aurora://bookmarks">Закладки</a>
  <a href="aurora://downloads">Загрузки</a>
  <a href="aurora://extensions">Расширения</a>
  <a href="aurora://settings">Настройки</a>
</div>
{body}
</div>
<script>
  // Убираем служебные параметры действий из адресной строки.
  if (location.search) {{ history.replaceState(null,'',location.origin?location.pathname:location.href.split('?')[0]); }}
</script>
</body></html>"""


class Pages:
    """Генерирует HTML внутренних страниц. Действия выполняет контроллер."""

    def __init__(self, controller) -> None:
        self.c = controller  # объект с .db, .extensions, .config, .sync

    # ---------- Главная / новая вкладка ----------
    def home(self) -> str:
        cfg = self.c.config
        top = self.c.db.top_sites(10)
        tiles = ""
        for s in top:
            title = html.escape((s.title or s.url)[:22])
            u = html.escape(s.url)
            letter = html.escape((s.title or s.url).lstrip("htps:/").upper()[:1] or "•")
            tiles += (
                f'<a class="tile" href="{u}"><div class="ico">{letter}</div>'
                f'<div class="muted" style="margin-top:8px;font-size:13px">{title}</div></a>'
            )
        if not tiles:
            tiles = '<div class="muted">Часто посещаемые сайты появятся здесь.</div>'
        engine = cfg.get("search_engine")
        body = f"""
<div style="text-align:center;margin:6vh 0 4vh">
  <div class="brand" style="font-size:44px;margin-bottom:22px">Aurora<span>·</span></div>
  <form onsubmit="go(event)" style="max-width:620px;margin:0 auto">
    <input id="q" type="text" autofocus placeholder="Искать в {html.escape(engine.split('/')[2])} или ввести адрес">
  </form>
</div>
<h1 style="font-size:18px">Часто посещаемые</h1>
<div class="grid">{tiles}</div>
<script>
function go(e){{e.preventDefault();var v=document.getElementById('q').value.trim();
  if(!v)return;
  if(/^https?:\\/\\//.test(v)||/^[\\w-]+\\.[\\w.-]+/.test(v)&&!v.includes(' ')){{
    location.href = v.startsWith('http')?v:'http://'+v;
  }} else {{
    location.href = {engine!r}.replace('{{q}}', encodeURIComponent(v));
  }}
}}
</script>
"""
        return _shell("Новая вкладка", body, cfg.get("theme"))

    # ---------- История ----------
    def history(self, query: str = "") -> str:
        items = self.c.db.search_history(query)
        rows = ""
        for it in items:
            rows += f"""
<div class="card row">
  <div class="grow">
    <div><a href="{html.escape(it.url)}">{html.escape(it.title or it.url)}</a></div>
    <div class="muted" style="font-size:12px">{html.escape(it.url)}</div>
  </div>
  <div class="muted" style="font-size:12px;white-space:nowrap">{_fmt_time(it.visited)}</div>
  <a class="btn danger" href="aurora://history?delete={it.id}">Удалить</a>
</div>"""
        if not rows:
            rows = '<div class="muted">Записей нет.</div>'
        sync_state = "включена" if self.c.config.get("sync_enabled") else "выключена"
        body = f"""
<h1>История</h1>
<div class="toolbar">
  <form action="aurora://history" style="flex:1"><input type="search" name="q" value="{html.escape(query)}" placeholder="Поиск по истории"></form>
  <a class="btn ghost" href="aurora://history?add=1">+ Добавить запись</a>
  <a class="btn danger" href="aurora://history?clear=1" onclick="return confirm('Очистить всю историю?')">Очистить всё</a>
</div>
<div class="muted" style="margin-bottom:12px">Синхронизация с Google: {sync_state}. Это только твоя история на твоих устройствах.</div>
{rows}
"""
        return _shell("История", body, self.c.config.get("theme"))

    def history_add_form(self) -> str:
        body = """
<h1>Добавить запись в историю</h1>
<div class="card">
  <form action="aurora://history" method="get">
    <p><input type="text" name="url" placeholder="https://example.com" required></p>
    <p><input type="text" name="title" placeholder="Заголовок (необязательно)"></p>
    <input type="hidden" name="save" value="1">
    <button class="btn" type="submit">Сохранить</button>
    <a class="btn ghost" href="aurora://history">Отмена</a>
  </form>
</div>"""
        return _shell("Добавить в историю", body, self.c.config.get("theme"))

    # ---------- Закладки ----------
    def bookmarks(self) -> str:
        rows = ""
        for b in self.c.db.all_bookmarks():
            rows += f"""
<div class="card row">
  <div class="grow"><div><a href="{html.escape(b['url'])}">{html.escape(b['title'])}</a></div>
  <div class="muted" style="font-size:12px">{html.escape(b['url'])}</div></div>
  <a class="btn danger" href="aurora://bookmarks?delete={html.escape(b['url'])}">Удалить</a>
</div>"""
        if not rows:
            rows = '<div class="muted">Пока нет закладок. Нажми ☆ в адресной строке.</div>'
        return _shell("Закладки", f"<h1>Закладки</h1>{rows}", self.c.config.get("theme"))

    # ---------- Загрузки ----------
    def downloads(self) -> str:
        rows = ""
        for d in self.c.db.all_downloads():
            size = f"{d['size']/1_048_576:.1f} МБ" if d["size"] else ""
            rows += f"""
<div class="card row"><div class="grow">
  <div>{html.escape(d['path'].split('/')[-1])}</div>
  <div class="muted" style="font-size:12px">{html.escape(d['url'])}</div></div>
  <span class="pill">{html.escape(d['state'])}</span>
  <span class="muted" style="font-size:12px">{size}</span></div>"""
        if not rows:
            rows = '<div class="muted">Загрузок пока нет.</div>'
        return _shell("Загрузки", f"<h1>Загрузки</h1>{rows}", self.c.config.get("theme"))

    # ---------- Расширения ----------
    def extensions(self) -> str:
        rows = ""
        for e in self.c.extensions.load_all():
            state = "checked" if e.enabled else ""
            rows += f"""
<div class="card row">
  <div class="grow"><div><b>{html.escape(e.name)}</b> <span class="pill">v{html.escape(e.version)}</span></div>
  <div class="muted" style="font-size:13px">{html.escape(e.description)}</div>
  <div class="muted" style="font-size:11px">{html.escape(', '.join(e.matches))}</div></div>
  <a class="btn ghost" href="aurora://extensions?toggle={html.escape(e.id)}">{'Выключить' if e.enabled else 'Включить'}</a>
  <a class="btn danger" href="aurora://extensions?remove={html.escape(e.id)}">Удалить</a>
</div>"""
        if not rows:
            rows = '<div class="muted">Расширений пока нет.</div>'
        body = f"""
<h1>Расширения</h1>
<div class="toolbar">
  <a class="btn" href="aurora://extensions?install=1">Установить из файла</a>
  <span class="muted">Папка расширений: {html.escape(str(self.c.extensions.ext_dir))}</span>
</div>
<div class="muted" style="margin-bottom:14px">
  Формат Aurora: папка с <code>manifest.json</code> + JS/CSS. Настоящие Chrome-расширения
  из Web Store движок не поддерживает — используется открытый формат в стиле userscript.
</div>
{rows}"""
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
            f'<div>Выполнен вход в Google. <a class="btn danger" href="aurora://settings?signout=1">Выйти</a></div>'
            if signed else
            '<a class="btn" href="aurora://settings?signin=1">Войти через Google для синхронизации</a>'
        )
        body = f"""
<h1>Настройки</h1>
<div class="card">
  <h3>Поиск</h3>
  <form action="aurora://settings" method="get">
    <select name="engine" class="btn ghost" style="padding:8px">{engines}</select>
    <button class="btn" name="save" value="1">Сохранить</button>
  </form>
</div>
<div class="card">
  <h3>Тема</h3>
  <a class="btn ghost" href="aurora://settings?theme=dark">Тёмная</a>
  <a class="btn ghost" href="aurora://settings?theme=light">Светлая</a>
</div>
<div class="card">
  <h3>Синхронизация через Google</h3>
  <p class="muted">Синхронизируется только твоя история и закладки, между твоими устройствами.</p>
  {sync_block}
  <p><a class="btn ghost" href="aurora://settings?synctoggle=1">{'Отключить' if cfg.get('sync_enabled') else 'Включить'} авто-синхронизацию</a>
     <a class="btn ghost" href="aurora://settings?syncnow=1">Синхронизировать сейчас</a></p>
</div>
<div class="card">
  <h3>Приватность</h3>
  <a class="btn ghost" href="aurora://settings?dnt=1">Do Not Track: {'вкл' if cfg.get('do_not_track') else 'выкл'}</a>
  <a class="btn ghost" href="aurora://settings?ads=1">Блокировка рекламы: {'вкл' if cfg.get('block_ads') else 'выкл'}</a>
</div>
<div class="muted">Aurora {self.c.version} · движок Chromium (QtWebEngine)</div>
"""
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
