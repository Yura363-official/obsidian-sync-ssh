#!/usr/bin/env python3
"""Запуск браузера Aurora.

    python run.py            # обычный запуск
    python run.py <url>      # открыть сразу с адресом

Требует PyQt6 и PyQt6-WebEngine (см. requirements.txt).
"""
from __future__ import annotations

import os
import sys

# Флаги Chromium: включаем современные веб-фичи и аппаратное ускорение по возможности.
_flags = "--enable-features=WebRTCPipeWireCapturer --autoplay-policy=user-gesture-required"
# Chromium отказывается работать от root без --no-sandbox (например, в контейнерах).
if hasattr(os, "geteuid") and os.geteuid() == 0:
    _flags += " --no-sandbox"
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", _flags)


def main() -> int:
    try:
        # QtWebEngineWidgets ДОЛЖЕН быть импортирован до создания QApplication.
        from PyQt6 import QtWebEngineWidgets  # noqa: F401
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QColor, QPalette
        from PyQt6.QtCore import Qt
        from PyQt6.QtWebEngineCore import QWebEngineUrlScheme
    except ImportError:
        sys.stderr.write(
            "\nНе установлены зависимости. Установи их:\n"
            "    pip install -r requirements.txt\n\n"
            "Минимум нужно: PyQt6 и PyQt6-WebEngine.\n"
        )
        return 1

    # ВАЖНО: собственный scheme aurora:// нужно зарегистрировать до создания QApplication.
    scheme = QWebEngineUrlScheme(b"aurora")
    scheme.setFlags(
        QWebEngineUrlScheme.Flag.SecureScheme
        | QWebEngineUrlScheme.Flag.LocalAccessAllowed
        | QWebEngineUrlScheme.Flag.CorsEnabled
    )
    scheme.setSyntax(QWebEngineUrlScheme.Syntax.Host)
    QWebEngineUrlScheme.registerScheme(scheme)

    qapp = QApplication(sys.argv)

    # Тёмная палитра для рамок/меню (сами сайты рендерятся как есть).
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, QColor("#12141f"))
    pal.setColor(QPalette.ColorRole.WindowText, QColor("#e7e9f3"))
    pal.setColor(QPalette.ColorRole.Base, QColor("#191d2e"))
    pal.setColor(QPalette.ColorRole.Text, QColor("#e7e9f3"))
    pal.setColor(QPalette.ColorRole.Button, QColor("#191d2e"))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor("#e7e9f3"))
    pal.setColor(QPalette.ColorRole.Highlight, QColor("#6c8cff"))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    qapp.setPalette(pal)

    from aurora.app import AuroraApp

    app = AuroraApp(qapp)
    app.open_window("default")

    if len(sys.argv) > 1 and app.active_window:
        from PyQt6.QtCore import QUrl
        app.active_window.current().setUrl(QUrl(app.active_window._resolve(sys.argv[1])))

    app._apply_sync_timer()
    return qapp.exec()


if __name__ == "__main__":
    raise SystemExit(main())
