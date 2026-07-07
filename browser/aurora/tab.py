"""Вкладка браузера: обёртка над QWebEngineView + страница с логикой истории."""
from __future__ import annotations

from PyQt6.QtCore import QUrl, pyqtSignal
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView


class WebPage(QWebEnginePage):
    """Страница, которая умеет открывать новые окна как вкладки."""

    def __init__(self, profile, controller, parent=None) -> None:
        super().__init__(profile, parent)
        self.controller = controller

    def createWindow(self, _type):  # noqa: N802 (Qt override)
        # Ссылки target=_blank и window.open открываем новой вкладкой.
        view = self.controller.add_tab(QUrl("about:blank"), switch=True)
        return view.page()

    def javaScriptConsoleMessage(self, level, message, line, source):  # noqa: N802
        # Тихо гасим шум из консоли страниц (можно включить для отладки).
        pass


class WebView(QWebEngineView):
    titleReady = pyqtSignal(str)

    def __init__(self, profile, controller, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.setPage(WebPage(profile, controller, self))
        self._wire()

    def _wire(self) -> None:
        self.loadFinished.connect(self._on_load_finished)
        self.iconChanged.connect(lambda _: self.controller.refresh_tab(self))
        self.titleChanged.connect(lambda t: self.controller.refresh_tab(self))

    def _on_load_finished(self, ok: bool) -> None:
        if not ok:
            return
        url = self.url().toString()
        title = self.title()
        # Записываем в историю (внутренние aurora:// страницы отфильтрует БД).
        if not self.controller.incognito:
            self.controller.db.add_history(url, title)
        self.controller.refresh_tab(self)

    def createWindow(self, _type):  # noqa: N802
        return self.controller.add_tab(QUrl("about:blank"), switch=True)
