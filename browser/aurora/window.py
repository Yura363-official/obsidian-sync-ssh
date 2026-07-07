"""Главное окно браузера Aurora: вкладки, тулбар, адресная строка, меню, поиск."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSize, Qt, QUrl, QTimer
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLineEdit, QMainWindow, QMenu, QMessageBox,
    QPushButton, QTabWidget, QToolBar, QWidget,
)
from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest, QWebEngineScript

from .extensions import build_injection_script
from .tab import WebView


class BrowserWindow(QMainWindow):
    """Окно = контроллер: содержит ссылки на db/extensions/config/sync и логику вкладок."""

    def __init__(self, app, profile, profile_name="default", incognito=False) -> None:
        super().__init__()
        self.app = app
        self.profile = profile
        self.profile_name = profile_name
        self.incognito = incognito
        self.db = app.db
        self.extensions = app.extensions
        self.config = app.config
        self.sync = app.sync
        self.version = app.version

        self.setWindowTitle("Aurora" + (" — Инкогнито" if incognito else ""))
        self.resize(1180, 760)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.setCentralWidget(self.tabs)

        self._build_toolbar()
        self._build_find_bar()
        self._build_shortcuts()
        self.reload_extensions()
        self.setup_downloads()

        self.add_tab(QUrl(self.config.get("home_page")), switch=True)

    # ---------- Тулбар ----------
    def _build_toolbar(self) -> None:
        tb = QToolBar()
        tb.setIconSize(QSize(18, 18))
        tb.setMovable(False)
        self.addToolBar(tb)

        def button(text, slot, tip=""):
            b = QPushButton(text)
            b.setFlat(True)
            b.setToolTip(tip)
            b.clicked.connect(slot)
            b.setFixedHeight(32)
            b.setStyleSheet("QPushButton{font-size:16px;padding:0 8px;border:none;}")
            tb.addWidget(b)
            return b

        button("◀", lambda: self.current().back(), "Назад")
        button("▶", lambda: self.current().forward(), "Вперёд")
        button("⟳", lambda: self.current().reload(), "Обновить")
        button("⌂", lambda: self.navigate(self.config.get("home_page")), "Домой")

        self.address = QLineEdit()
        self.address.setPlaceholderText("Введите запрос или адрес…")
        self.address.setClearButtonEnabled(True)
        self.address.returnPressed.connect(self._on_address_enter)
        self.address.setStyleSheet("QLineEdit{border-radius:16px;padding:6px 14px;font-size:14px;}")
        tb.addWidget(self.address)

        self.star = button("☆", self.toggle_bookmark, "Добавить в закладки")
        button("＋", lambda: self.add_tab(QUrl(self.config.get("home_page")), switch=True), "Новая вкладка")
        button("👤", self.show_profiles_menu, "Профили — переключиться или создать новый")
        button("⋮", self.show_main_menu, "Меню")

    def _build_find_bar(self) -> None:
        self.find_bar = QToolBar()
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Найти на странице…")
        self.find_input.textChanged.connect(lambda t: self.current().findText(t))
        self.find_input.returnPressed.connect(lambda: self.current().findText(self.find_input.text()))
        self.find_bar.addWidget(self.find_input)
        close = QPushButton("✕")
        close.clicked.connect(lambda: self.find_bar.setVisible(False))
        self.find_bar.addWidget(close)
        self.addToolBarBreak()
        self.addToolBar(self.find_bar)
        self.find_bar.setVisible(False)

    def _build_shortcuts(self) -> None:
        def act(seq, slot):
            a = QAction(self)
            a.setShortcut(QKeySequence(seq))
            a.triggered.connect(slot)
            self.addAction(a)

        act("Ctrl+T", lambda: self.add_tab(QUrl(self.config.get("home_page")), switch=True))
        act("Ctrl+W", lambda: self.close_tab(self.tabs.currentIndex()))
        act("Ctrl+L", lambda: (self.address.setFocus(), self.address.selectAll()))
        act("Ctrl+R", lambda: self.current().reload())
        act("F5", lambda: self.current().reload())
        act("Ctrl+F", self._show_find)
        act("Ctrl+D", self.toggle_bookmark)
        act("Ctrl+H", lambda: self.navigate("aurora://history"))
        act("Ctrl+J", lambda: self.navigate("aurora://downloads"))
        act("Ctrl+Shift+N", self.app.open_incognito_window)
        act("Ctrl+N", lambda: self.app.open_window(self.profile_name))
        act("Ctrl+Tab", lambda: self.tabs.setCurrentIndex((self.tabs.currentIndex() + 1) % max(1, self.tabs.count())))
        act("Ctrl+=", lambda: self._zoom(0.1))
        act("Ctrl+-", lambda: self._zoom(-0.1))
        act("Ctrl+0", lambda: self.current().setZoomFactor(1.0))

    # ---------- Вкладки ----------
    def add_tab(self, url: QUrl | None = None, switch: bool = False) -> WebView:
        view = WebView(self.profile, self, self)
        idx = self.tabs.addTab(view, "Новая вкладка")
        view.urlChanged.connect(lambda u, v=view: self._on_url_changed(v, u))
        view.loadFinished.connect(lambda ok, v=view: self.refresh_tab(v))
        if url is not None:
            view.setUrl(url)
        if switch:
            self.tabs.setCurrentIndex(idx)
        return view

    def close_tab(self, index: int) -> None:
        if self.tabs.count() <= 1:
            self.add_tab(QUrl(self.config.get("home_page")), switch=True)
        w = self.tabs.widget(index)
        self.tabs.removeTab(index)
        if w:
            w.deleteLater()

    def current(self) -> WebView:
        return self.tabs.currentWidget()

    def _on_tab_changed(self, _idx: int) -> None:
        view = self.current()
        if view:
            self._update_address(view.url())
            self._update_star(view.url().toString())
            self.setWindowTitle(f"{view.title() or 'Aurora'} — Aurora")

    def _on_url_changed(self, view: WebView, url: QUrl) -> None:
        if view is self.current():
            self._update_address(url)
            self._update_star(url.toString())

    def refresh_tab(self, view: WebView) -> None:
        idx = self.tabs.indexOf(view)
        if idx < 0:
            return
        title = view.title() or "Новая вкладка"
        self.tabs.setTabText(idx, title[:22])
        self.tabs.setTabToolTip(idx, title)
        icon = view.icon()
        if not icon.isNull():
            self.tabs.setTabIcon(idx, icon)
        if view is self.current():
            self.setWindowTitle(f"{title} — Aurora")

    # ---------- Навигация ----------
    def navigate(self, url_str: str) -> None:
        self.current().setUrl(QUrl(url_str))

    def _on_address_enter(self) -> None:
        text = self.address.text().strip()
        if not text:
            return
        self.current().setUrl(QUrl(self._resolve(text)))
        self.current().setFocus()

    def _resolve(self, text: str) -> str:
        if text.startswith(("http://", "https://", "aurora://", "file://", "about:")):
            return text
        # Похоже на домен (есть точка, нет пробелов)?
        if " " not in text and "." in text:
            return "http://" + text
        engine = self.config.get("search_engine")
        return engine.replace("{q}", QUrl.toPercentEncoding(text).data().decode())

    def _update_address(self, url: QUrl) -> None:
        s = url.toString()
        if s == "about:blank":
            s = ""
        if not self.address.hasFocus():
            self.address.setText(s)
            self.address.setCursorPosition(0)

    # ---------- Закладки ----------
    def toggle_bookmark(self) -> None:
        view = self.current()
        url = view.url().toString()
        if not url or url.startswith("aurora://"):
            return
        if self.db.is_bookmarked(url):
            self.db.remove_bookmark(url)
        else:
            self.db.add_bookmark(url, view.title() or url)
        self._update_star(url)

    def _update_star(self, url: str) -> None:
        self.star.setText("★" if self.db.is_bookmarked(url) else "☆")

    # ---------- Поиск на странице ----------
    def _show_find(self) -> None:
        self.find_bar.setVisible(True)
        self.find_input.setFocus()
        self.find_input.selectAll()

    # ---------- Масштаб ----------
    def _zoom(self, delta: float) -> None:
        v = self.current()
        v.setZoomFactor(max(0.3, min(3.0, v.zoomFactor() + delta)))

    # ---------- Расширения ----------
    def reload_extensions(self) -> None:
        scripts = self.profile.scripts()
        scripts.clear()
        for ext in self.extensions.enabled_extensions():
            src = build_injection_script(ext)
            s = QWebEngineScript()
            s.setName(ext.id)
            s.setSourceCode(src)
            s.setInjectionPoint(
                QWebEngineScript.InjectionPoint.DocumentReady
                if ext.run_at == "document_end"
                else QWebEngineScript.InjectionPoint.DocumentCreation
            )
            s.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
            s.setRunsOnSubFrames(True)
            scripts.insert(s)

    def install_extension_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите manifest.json или .zip расширения",
            str(Path.home()), "Расширения (manifest.json *.zip)")
        if not path:
            return
        p = Path(path)
        try:
            if p.suffix == ".zip":
                ext = self.extensions.install_from_zip(p)
            else:
                ext = self.extensions.install_from_folder(p.parent)
            self.reload_extensions()
            QMessageBox.information(self, "Aurora", f"Установлено: {ext.name if ext else p.name}")
        except (ValueError, OSError) as e:
            QMessageBox.warning(self, "Ошибка установки", str(e))

    # ---------- Загрузки ----------
    def setup_downloads(self) -> None:
        self.profile.downloadRequested.connect(self._on_download)

    def _on_download(self, item: QWebEngineDownloadRequest) -> None:
        target = Path(self.config.get("download_dir")) / item.downloadFileName()
        target.parent.mkdir(parents=True, exist_ok=True)
        item.setDownloadDirectory(str(target.parent))
        item.setDownloadFileName(target.name)
        dl_id = self.db.add_download(item.url().toString(), str(target))
        item.accept()

        def on_state():
            if item.isFinished():
                self.db.finish_download(dl_id, item.receivedBytes(),
                                        "completed" if item.state() ==
                                        QWebEngineDownloadRequest.DownloadState.DownloadCompleted
                                        else "failed")
        item.isFinishedChanged.connect(on_state)

    # ---------- Профили (кнопка 👤) ----------
    def show_profiles_menu(self) -> None:
        menu = QMenu(self)
        menu.addAction(f"Текущий профиль: {self.profile_name}").setEnabled(False)
        menu.addSeparator()
        for name in self.app.list_profiles():
            act = menu.addAction(("● " if name == self.profile_name else "○ ") + name)
            act.triggered.connect(lambda _=False, n=name: self.app.open_window(n))
        menu.addSeparator()
        menu.addAction("➕ Новый профиль…", self._create_profile)
        menu.addAction("🕵 Окно инкогнито", self.app.open_incognito_window)
        menu.exec(self.cursor().pos())

    def _create_profile(self) -> None:
        from PyQt6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Новый профиль", "Имя профиля:")
        if ok and name.strip():
            self.app.open_window(name.strip())

    # ---------- Главное меню (⋮) ----------
    def show_main_menu(self) -> None:
        m = QMenu(self)
        m.addAction("Новая вкладка\tCtrl+T", lambda: self.add_tab(QUrl(self.config.get("home_page")), switch=True))
        m.addAction("Новое окно\tCtrl+N", lambda: self.app.open_window(self.profile_name))
        m.addAction("Инкогнито\tCtrl+Shift+N", self.app.open_incognito_window)
        m.addSeparator()
        m.addAction("История\tCtrl+H", lambda: self.navigate("aurora://history"))
        m.addAction("Закладки", lambda: self.navigate("aurora://bookmarks"))
        m.addAction("Загрузки\tCtrl+J", lambda: self.navigate("aurora://downloads"))
        m.addAction("Расширения", lambda: self.navigate("aurora://extensions"))
        m.addSeparator()
        m.addAction("Найти на странице\tCtrl+F", self._show_find)
        zoom = m.addMenu("Масштаб")
        zoom.addAction("Увеличить", lambda: self._zoom(0.1))
        zoom.addAction("Уменьшить", lambda: self._zoom(-0.1))
        zoom.addAction("Сбросить", lambda: self.current().setZoomFactor(1.0))
        m.addAction("Печать…", self._print)
        m.addSeparator()
        m.addAction("Синхронизировать сейчас", self.sync_now)
        m.addAction("Настройки", lambda: self.navigate("aurora://settings"))
        m.addAction("О браузере", self._about)
        m.exec(self.cursor().pos())

    def _print(self) -> None:
        try:
            from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
            printer = QPrinter()
            if QPrintDialog(printer, self).exec():
                self.current().page().print(printer, lambda ok: None)
        except Exception as e:  # noqa: BLE001
            QMessageBox.information(self, "Печать", f"Печать недоступна: {e}")

    def _about(self) -> None:
        QMessageBox.about(
            self, "О браузере Aurora",
            f"<b>Aurora</b> {self.version}<br>Настоящий браузер на движке Chromium "
            f"(QtWebEngine), без Electron.<br><br>Профиль: {self.profile_name}")

    # ---------- Синхронизация (делегируем в app) ----------
    def google_sign_in(self):
        self.app.google_sign_in(self)

    def google_sign_out(self):
        self.app.google_sign_out(self)

    def sync_now(self):
        self.app.sync_now(self)
