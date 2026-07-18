# GdeBenz — мультиплатформенное приложение

Приложение-обёртка, которое показывает сайт **https://gdebenz.ru/** и по плавающей
кнопке в правом нижнем углу переключается на **https://gdebenz.org/** (и обратно).
Переход на любые другие сайты заблокирован — навигация разрешена только по доменам
`gdebenz.ru` и `gdebenz.org`.

Сделано на [Tauri 2](https://v2.tauri.app/) — один код собирается под:

| Платформа | Файл |
|---|---|
| Android | `GdeBenz.apk` (подписан, ставится напрямую) |
| iOS | `GdeBenz-unsigned.ipa` (без подписи — см. ниже) |
| Windows | установщик `.exe` (NSIS) + `.msi` |
| Linux | `.AppImage`, `.deb`, `.rpm` |

## Где скачать готовые файлы

Сборка происходит автоматически в GitHub Actions:

1. Откройте вкладку **Actions** репозитория.
2. Выберите последний запуск **Build GdeBenz app**.
3. Внизу страницы в разделе **Artifacts** скачайте нужную платформу:
   `GdeBenz-android-apk`, `GdeBenz-ios-ipa`, `GdeBenz-windows`, `GdeBenz-linux`.

## Про iOS (IPA)

Apple не позволяет устанавливать подписанные «просто так» приложения: для подписи
нужен аккаунт Apple Developer. Поэтому IPA собирается **без подписи** и ставится
через сайдлоадинг — например [Sideloadly](https://sideloadly.io/) или AltStore
(они подписывают IPA вашим Apple ID при установке).

## Локальная сборка (для разработки)

```bash
cd gdebenz-app
npm install
npx tauri icon app-icon.png   # сгенерировать иконки
npx tauri dev                 # запуск на десктопе
npx tauri build               # сборка под текущую ОС
npx tauri android init && npx tauri android build --apk   # Android
npx tauri ios init && npx tauri ios build                 # iOS (нужен macOS)
```
