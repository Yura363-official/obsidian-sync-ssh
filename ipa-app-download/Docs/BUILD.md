# Сборка и получение .ipa

## Требования

- macOS + Xcode 15+
- [XcodeGen](https://github.com/yonaskolb/XcodeGen): `brew install xcodegen`

## Генерация проекта

```bash
cd ipa-app-download
xcodegen generate
open IpaAppDownload.xcodeproj
```

## Сборка .ipa из командной строки

Без платного Apple Developer Program подпись будет «Personal Team» —
именно её потом переподпишет Sideloadly, так что это нормально.

```bash
# 1. Archive
xcodebuild -project IpaAppDownload.xcodeproj \
  -scheme IpaAppDownload \
  -configuration Release \
  -archivePath build/IpaAppDownload.xcarchive \
  archive

# 2. Экспорт .ipa (нужен ExportOptions.plist, см. ниже)
xcodebuild -exportArchive \
  -archivePath build/IpaAppDownload.xcarchive \
  -exportOptionsPlist ExportOptions.plist \
  -exportPath build/ipa
```

Пример `ExportOptions.plist` для development-подписи:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>method</key>
  <string>development</string>
  <key>signingStyle</key>
  <string>automatic</string>
  <key>stripSwiftSymbols</key>
  <true/>
  <key>compileBitcode</key>
  <false/>
</dict>
</plist>
```

## Установка через Sideloadly

1. Скачай Sideloadly: <https://sideloadly.io>
2. Подключи iPhone кабелем, открой Sideloadly.
3. Перетащи `build/ipa/IpaAppDownload.ipa`, укажи Apple ID → **Start**.
4. На iPhone: **Настройки → Основные → VPN и управление устройством** →
   доверься профилю разработчика.

> Бесплатный Apple ID даёт сертификат на 7 дней — приложение придётся
> переустанавливать раз в неделю. Платный аккаунт разработчика — на год.
