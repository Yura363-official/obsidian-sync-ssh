"""Система расширений «из файлов».

Настоящие Chrome-расширения (.crx из Web Store) QtWebEngine запускать не умеет —
это ограничение движка. Поэтому Aurora использует свой открытый формат:
папка с файлом manifest.json + JS/CSS. Такие расширения устанавливаются
копированием папки (или через кнопку «Установить из файла») и внедряются на
страницы. Формат близок к userscript-менеджерам (Tampermonkey/Stylus).

Пример manifest.json:
{
  "name": "Hello World",
  "version": "1.0",
  "description": "Показывает приветствие",
  "matches": ["*://*/*"],
  "js": ["script.js"],
  "css": ["style.css"],
  "run_at": "document_end"
}
"""
from __future__ import annotations

import json
import re
import shutil
import zipfile
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Extension:
    path: Path
    name: str
    version: str = "1.0"
    description: str = ""
    matches: list[str] = field(default_factory=lambda: ["*://*/*"])
    js: list[str] = field(default_factory=list)
    css: list[str] = field(default_factory=list)
    run_at: str = "document_end"
    enabled: bool = True

    @property
    def id(self) -> str:
        return self.path.name

    def read_js(self) -> str:
        return "\n".join((self.path / f).read_text("utf-8") for f in self.js if (self.path / f).exists())

    def read_css(self) -> str:
        return "\n".join((self.path / f).read_text("utf-8") for f in self.css if (self.path / f).exists())


def _match_to_regex(pattern: str) -> str:
    """Преобразует match-шаблон (*://*/*) в регулярное выражение."""
    esc = re.escape(pattern)
    esc = esc.replace(r"\*", ".*")
    return "^" + esc + "$"


def build_injection_script(ext: Extension) -> str:
    """Собирает единый JS, который сам проверяет URL и внедряет CSS+JS расширения."""
    css = ext.read_css()
    js = ext.read_js()
    regexes = [_match_to_regex(m) for m in ext.matches] or ["^.*$"]
    guard = " || ".join(f"new RegExp({json.dumps(r)}).test(location.href)" for r in regexes)
    css_js = ""
    if css:
        css_js = (
            "var __s=document.createElement('style');"
            f"__s.textContent={json.dumps(css)};"
            "__s.setAttribute('data-aurora-ext', %s);"
            "(document.head||document.documentElement).appendChild(__s);"
        ) % json.dumps(ext.id)
    user_js = ""
    if js:
        # Оборачиваем в IIFE, чтобы не засорять глобальную область.
        user_js = "(function(){try{%s}catch(e){console.error('[Aurora ext %s]',e);}})();" % (
            js, ext.id,
        )
    return (
        "(function(){if(!(%s))return;%s%s})();" % (guard, css_js, user_js)
    )


class ExtensionManager:
    def __init__(self, ext_dir: Path, builtin_dir: Path | None = None) -> None:
        self.ext_dir = ext_dir
        self.builtin_dir = builtin_dir
        self.ext_dir.mkdir(parents=True, exist_ok=True)
        self._seed_builtins()

    def _seed_builtins(self) -> None:
        """Один раз копируем встроенные примеры в пользовательскую папку."""
        if not self.builtin_dir or not self.builtin_dir.exists():
            return
        for src in self.builtin_dir.iterdir():
            if src.is_dir() and (src / "manifest.json").exists():
                dst = self.ext_dir / src.name
                if not dst.exists():
                    shutil.copytree(src, dst)

    def _load_one(self, folder: Path) -> Extension | None:
        manifest = folder / "manifest.json"
        if not manifest.exists():
            return None
        try:
            data = json.loads(manifest.read_text("utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        disabled = (folder / ".disabled").exists()
        return Extension(
            path=folder,
            name=data.get("name", folder.name),
            version=str(data.get("version", "1.0")),
            description=data.get("description", ""),
            matches=data.get("matches", ["*://*/*"]),
            js=data.get("js", []),
            css=data.get("css", []),
            run_at=data.get("run_at", "document_end"),
            enabled=not disabled,
        )

    def load_all(self) -> list[Extension]:
        exts: list[Extension] = []
        for folder in sorted(self.ext_dir.iterdir()):
            if folder.is_dir():
                ext = self._load_one(folder)
                if ext:
                    exts.append(ext)
        return exts

    def enabled_extensions(self) -> list[Extension]:
        return [e for e in self.load_all() if e.enabled]

    def set_enabled(self, ext_id: str, enabled: bool) -> None:
        flag = self.ext_dir / ext_id / ".disabled"
        if enabled and flag.exists():
            flag.unlink()
        elif not enabled and not flag.exists():
            flag.touch()

    def install_from_folder(self, source: Path) -> Extension | None:
        """Установить расширение, скопировав папку с manifest.json."""
        if not (source / "manifest.json").exists():
            raise ValueError("В папке нет manifest.json")
        dst = self.ext_dir / source.name
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(source, dst)
        return self._load_one(dst)

    def install_from_zip(self, zip_path: Path) -> Extension | None:
        """Установить расширение из ZIP-архива (папка внутри или файлы в корне)."""
        target = self.ext_dir / zip_path.stem
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(target)
        # Если manifest лежит во вложенной единственной папке — поднимем его наверх.
        if not (target / "manifest.json").exists():
            subs = [p for p in target.iterdir() if p.is_dir()]
            if len(subs) == 1 and (subs[0] / "manifest.json").exists():
                for item in subs[0].iterdir():
                    shutil.move(str(item), str(target / item.name))
                shutil.rmtree(subs[0])
        return self._load_one(target)

    def uninstall(self, ext_id: str) -> None:
        folder = self.ext_dir / ext_id
        if folder.exists():
            shutil.rmtree(folder)
