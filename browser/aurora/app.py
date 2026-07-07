"""AuroraApp — оркестратор: профили, окна, синхронизация, блокировщик рекламы."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QTimer, QUrl
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile, QWebEngineSettings, QWebEngineUrlRequestInterceptor,
)
from PyQt6.QtWidgets import QMessageBox

from . import __version__, config as cfgmod
from .config import Config, DATA_DIR, PROFILE_DIR
from .database import Database
from .extensions import ExtensionManager
from .pages import AuroraSchemeHandler
from .sync import GoogleSync, SyncUnavailable, merge_history
from .window import BrowserWindow

# Мини-список рекламных/трекинговых хостов для простого блокировщика.
AD_HOSTS = {
    "doubleclick.net", "googlesyndication.com", "google-analytics.com",
    "adservice.google.com", "ads.yahoo.com", "adnxs.com", "criteo.com",
    "scorecardresearch.com", "moatads.com", "outbrain.com", "taboola.com",
}


class AdBlockInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config

    def interceptRequest(self, info) -> None:  # noqa: N802
        if not self.config.get("block_ads"):
            return
        host = info.requestUrl().host()
        if any(host == h or host.endswith("." + h) for h in AD_HOSTS):
            info.block(True)


class AuroraApp:
    def __init__(self, qapp) -> None:
        self.qapp = qapp
        self.version = __version__
        self.config = Config()
        self.db = Database(cfgmod.DB_PATH)
        self.extensions = ExtensionManager(cfgmod.EXTENSIONS_DIR, cfgmod.BUILTIN_EXTENSIONS_DIR)
        self.sync = GoogleSync(cfgmod.GOOGLE_CLIENT_SECRET, cfgmod.GOOGLE_TOKEN)

        # Один обработчик aurora:// на все профили; контроллер = это приложение.
        self.scheme_handler = AuroraSchemeHandler(self)
        self.interceptor = AdBlockInterceptor(self.config)

        self._profiles: dict[str, QWebEngineProfile] = {}
        self._windows: list[BrowserWindow] = []
        self.active_window: BrowserWindow | None = None

        self._sync_timer = QTimer(self.qapp)
        self._sync_timer.timeout.connect(lambda: self.sync_now(silent=True))

    # ---------- Профили ----------
    def list_profiles(self) -> list[str]:
        base = DATA_DIR / "profiles"
        names = {"default"}
        if base.exists():
            names |= {p.name for p in base.iterdir() if p.is_dir()}
        names |= set(self._profiles)
        return sorted(names)

    def _get_profile(self, name: str) -> QWebEngineProfile:
        if name in self._profiles:
            return self._profiles[name]
        prof = QWebEngineProfile(f"aurora-{name}", self.qapp)
        storage = DATA_DIR / "profiles" / name
        storage.mkdir(parents=True, exist_ok=True)
        prof.setPersistentStoragePath(str(storage))
        prof.setCachePath(str(storage / "cache"))
        prof.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        self._configure_profile(prof)
        self._profiles[name] = prof
        return prof

    def _incognito_profile(self) -> QWebEngineProfile:
        prof = QWebEngineProfile(self.qapp)  # без имени = off-the-record
        self._configure_profile(prof)
        return prof

    def _configure_profile(self, prof: QWebEngineProfile) -> None:
        prof.installUrlSchemeHandler(b"aurora", self.scheme_handler)
        prof.setUrlRequestInterceptor(self.interceptor)
        s = prof.settings()
        s.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.ScreenCaptureEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.DnsPrefetchEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)

    # ---------- Окна ----------
    def open_window(self, profile_name: str = "default") -> BrowserWindow:
        prof = self._get_profile(profile_name)
        win = BrowserWindow(self, prof, profile_name=profile_name)
        self._register_window(win)
        return win

    def open_incognito_window(self) -> BrowserWindow:
        prof = self._incognito_profile()
        win = BrowserWindow(self, prof, profile_name="Инкогнито", incognito=True)
        win._incognito_profile_ref = prof  # держим ссылку, чтобы не собрал GC
        self._register_window(win)
        return win

    def _register_window(self, win: BrowserWindow) -> None:
        self._windows.append(win)
        self.active_window = win
        win.destroyed.connect(lambda: self._windows.remove(win) if win in self._windows else None)
        win.show()

    # ---------- Расширения / диалоги (через активное окно) ----------
    def reload_extensions(self) -> None:
        for w in self._windows:
            w.reload_extensions()

    def install_extension_dialog(self) -> None:
        if self.active_window:
            self.active_window.install_extension_dialog()

    # ---------- Синхронизация ----------
    def _apply_sync_timer(self) -> None:
        if self.config.get("sync_enabled") and self.sync.is_signed_in():
            self._sync_timer.start(int(self.config.get("sync_interval_min", 10)) * 60_000)
        else:
            self._sync_timer.stop()

    def google_sign_in(self, window=None) -> None:
        win = window or self.active_window
        try:
            self.sync.sign_in()
            self.config.set("sync_enabled", True)
            self._apply_sync_timer()
            self.sync_now()
            if win:
                QMessageBox.information(win, "Aurora", "Вход выполнен. Синхронизация включена.")
        except SyncUnavailable as e:
            if win:
                QMessageBox.warning(win, "Синхронизация недоступна", str(e))

    def google_sign_out(self, window=None) -> None:
        self.sync.sign_out()
        self.config.set("sync_enabled", False)
        self._apply_sync_timer()

    def sync_now(self, window=None, silent: bool = False) -> None:
        win = window or self.active_window
        if not self.sync.is_signed_in():
            if not silent and win:
                QMessageBox.information(win, "Синхронизация", "Сначала войди через Google в настройках.")
            return
        try:
            remote = self.sync.download_remote()
            local_hist = [
                {"url": h.url, "title": h.title, "visited": h.visited}
                for h in self.db.all_history()
            ]
            merged = merge_history(local_hist, remote.get("history", []))
            # Импортируем недостающие записи локально.
            known = {(h.url, int(h.visited)) for h in self.db.all_history()}
            for item in merged:
                key = (item["url"], int(item.get("visited", 0)))
                if key not in known:
                    self.db.add_history_entry(item["url"], item.get("title", ""), item.get("visited", 0))
            local_bm = [dict(b) for b in self.db.all_bookmarks()]
            self.sync.upload_remote({"history": merged, "bookmarks": local_bm})
            if not silent and win:
                QMessageBox.information(win, "Aurora", f"Синхронизировано записей: {len(merged)}.")
        except SyncUnavailable as e:
            if not silent and win:
                QMessageBox.warning(win, "Синхронизация", str(e))

    # ---------- Запуск ----------
    def run(self) -> int:
        self.qapp.setApplicationName("Aurora")
        self.qapp.setOrganizationName("Aurora")
        self.open_window("default")
        self._apply_sync_timer()
        return self.qapp.exec()
