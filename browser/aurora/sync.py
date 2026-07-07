"""Синхронизация ТВОЕЙ истории и закладок между ТВОИМИ устройствами через Google Drive.

Данные хранятся в скрытой служебной папке твоего Google Drive (appDataFolder),
доступ к которой есть только у этого приложения. Никакие чужие данные тут не
участвуют — синхронизируется только история/закладки владельца аккаунта, и только
после явного входа через Google.

Как включить:
1. Создай проект в Google Cloud Console, включи Google Drive API.
2. Создай OAuth-клиент типа «Desktop app», скачай client_secret.json.
3. Положи его в ~/.aurora/google_client_secret.json
4. В браузере: Меню → Синхронизация → Войти через Google.

Если библиотеки Google или client_secret не настроены — синхронизация просто
выключена, а браузер работает как обычно.
"""
from __future__ import annotations

import io
import json
import time
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/drive.appdata"]
REMOTE_FILENAME = "aurora_sync.json"


class SyncUnavailable(Exception):
    pass


def _require_google():
    try:
        from google.auth.transport.requests import Request  # noqa: F401
        from google.oauth2.credentials import Credentials  # noqa: F401
        from google_auth_oauthlib.flow import InstalledAppFlow  # noqa: F401
        from googleapiclient.discovery import build  # noqa: F401
        from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload  # noqa: F401
    except ImportError as exc:  # pragma: no cover
        raise SyncUnavailable(
            "Не установлены библиотеки Google. Выполни:\n"
            "  pip install google-auth google-auth-oauthlib google-api-python-client"
        ) from exc


class GoogleSync:
    def __init__(self, client_secret: Path, token_path: Path) -> None:
        self.client_secret = client_secret
        self.token_path = token_path
        self._service = None
        self.email: str | None = None

    # ---------- Авторизация ----------
    def is_configured(self) -> bool:
        try:
            _require_google()
        except SyncUnavailable:
            return False
        return self.client_secret.exists() or self.token_path.exists()

    def is_signed_in(self) -> bool:
        return self.token_path.exists()

    def _load_credentials(self):
        _require_google()
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials

        creds = None
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
        if creds and creds.valid:
            return creds
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            self.token_path.write_text(creds.to_json(), "utf-8")
            return creds
        return None

    def sign_in(self):
        """Открывает браузерное окно Google для входа. Блокирует до завершения."""
        _require_google()
        from google_auth_oauthlib.flow import InstalledAppFlow

        if not self.client_secret.exists():
            raise SyncUnavailable(
                f"Нет файла {self.client_secret.name}. Смотри инструкцию в sync.py."
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(self.client_secret), SCOPES)
        creds = flow.run_local_server(port=0, prompt="consent")
        self.token_path.write_text(creds.to_json(), "utf-8")
        return creds

    def sign_out(self) -> None:
        if self.token_path.exists():
            self.token_path.unlink()
        self._service = None
        self.email = None

    def _get_service(self):
        _require_google()
        from googleapiclient.discovery import build

        if self._service is not None:
            return self._service
        creds = self._load_credentials()
        if creds is None:
            raise SyncUnavailable("Нужен вход через Google.")
        self._service = build("drive", "v3", credentials=creds, cache_discovery=False)
        return self._service

    # ---------- Обмен данными ----------
    def _find_remote_id(self) -> str | None:
        service = self._get_service()
        res = service.files().list(
            spaces="appDataFolder",
            q=f"name = '{REMOTE_FILENAME}'",
            fields="files(id, name)",
        ).execute()
        files = res.get("files", [])
        return files[0]["id"] if files else None

    def download_remote(self) -> dict:
        from googleapiclient.http import MediaIoBaseDownload

        service = self._get_service()
        file_id = self._find_remote_id()
        if not file_id:
            return {"history": [], "bookmarks": [], "updated": 0}
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, service.files().get_media(fileId=file_id))
        done = False
        while not done:
            _, done = downloader.next_chunk()
        buf.seek(0)
        try:
            return json.loads(buf.read().decode("utf-8"))
        except json.JSONDecodeError:
            return {"history": [], "bookmarks": [], "updated": 0}

    def upload_remote(self, payload: dict) -> None:
        from googleapiclient.http import MediaIoBaseUpload

        service = self._get_service()
        payload["updated"] = time.time()
        data = io.BytesIO(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        media = MediaIoBaseUpload(data, mimetype="application/json", resumable=False)
        file_id = self._find_remote_id()
        if file_id:
            service.files().update(fileId=file_id, media_body=media).execute()
        else:
            service.files().create(
                body={"name": REMOTE_FILENAME, "parents": ["appDataFolder"]},
                media_body=media,
            ).execute()


def merge_history(local: list[dict], remote: list[dict]) -> list[dict]:
    """Объединяет истории по (url, округлённое время визита), убирая дубликаты."""
    seen: dict[tuple[str, int], dict] = {}
    for item in list(remote) + list(local):
        key = (item["url"], int(item.get("visited", 0)))
        seen.setdefault(key, item)
    return sorted(seen.values(), key=lambda x: x.get("visited", 0), reverse=True)
