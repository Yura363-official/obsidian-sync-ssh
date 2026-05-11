# obsidian-sync-ssh

# Obsidian Sync — Руководство по настройке

---

## Содержание

- [Первоначальная настройка](#первоначальная-настройка)
- [SSH-синхронизация](#ssh-синхронизация)
- [Google Drive](#google-drive)
- [Яндекс.Диск](#яндексдиск)
- [Microsoft OneDrive](#microsoft-onedrive)
- [iCloud Drive](#icloud-drive)
- [Расписание облачных копий](#расписание-облачных-копий)

---

## Первоначальная настройка

1. Запустите приложение — откроется главное окно.
2. Нажмите значок шестерёнки ⚙ (Настройки) в правом верхнем углу.
3. В разделе **SSH Подключение** введите данные сервера и локальную папку Obsidian.
4. Нажмите **Сохранить**, затем **▶ Запустить** для автоматической синхронизации по расписанию.

---

## SSH-синхронизация

| Поле | Описание |
|---|---|
| Хост / IP | Адрес удалённого сервера |
| Порт | Обычно `22` |
| Пользователь | Имя пользователя на сервере |
| Пароль | Пароль или оставьте пустым при использовании ключа |
| SSH-ключ | Путь к файлу ключа (необязательно) |
| Удалённая папка | Папка на сервере, откуда брать файлы |
| Локальная папка | Папка Obsidian на вашем компьютере |
| Интервал | Как часто проверять обновления (ч / м / с) |

После заполнения нажмите **Сохранить**, затем **▶ Запустить**.

---

## Google Drive

### Шаг 1 — Создайте проект в Google Cloud Console

1. Откройте [console.cloud.google.com](https://console.cloud.google.com)
2. Нажмите **«Выбрать проект»** → **«Новый проект»**, дайте любое название, нажмите **Создать**.
3. В левом меню: **API и сервисы → Включённые API** → нажмите **«+ Включить API»** → найдите **Google Drive API** → **Включить**.

### Шаг 2 — Настройте экран согласия OAuth

1. Левое меню: **API и сервисы → Экран согласия OAuth**.
2. Тип пользователей: **Внешний** → **Создать**.
3. Заполните: название приложения (любое), email поддержки → **Сохранить и продолжить**.
4. На шаге **«Тестовые пользователи»** нажмите **«+ Add Users»** и добавьте ваш Gmail-адрес.
5. Нажмите **Сохранить и продолжить** до конца.

### Шаг 3 — Создайте учётные данные OAuth

1. Левое меню: **API и сервисы → Учётные данные** → **«+ Создать учётные данные»** → **OAuth client ID**.
2. Тип приложения: **Веб-приложение**.
3. В разделе **«Авторизованные URI перенаправления»** добавьте:
   ```
   http://localhost:3333/oauth/google/callback
   ```
4. Нажмите **Создать** — появится окно с **Client ID** и **Client Secret**.
5. Скопируйте оба значения в JSON-файл или запомните.

### Шаг 4 — Подключите в приложении

1. В настройках приложения откройте раздел **Google-аккаунт**.
2. Вставьте **Client ID** и **Client Secret** → нажмите **Сохранить**.
3. Нажмите **«Войти через Google»** — откроется браузер.
4. Войдите в тот Gmail-аккаунт, который добавляли в тестовые пользователи.
5. После успешного входа окно закроется, в настройках появится ваш email.

### Возможности после подключения

- **↑ Сохранить в Drive** — сохраняет конфигурацию приложения в Google Drive.
- **↓ Загрузить из Drive** — восстанавливает конфигурацию с Google Drive.
- **Резервная копия .md в Drive** — копирует все .md файлы в папку `Obsidian Backup` на Drive.
- **Основная синхронизация** — включить/выключить автоматический backup по расписанию.
- **App Dep/[компьютер]** — включить/выключить синхронизацию локальной папки в `App Dep/ИмяКомпьютера` на Drive.

---

## Яндекс.Диск

### Шаг 1 — Зарегистрируйте приложение

1. Откройте [oauth.yandex.ru](https://oauth.yandex.ru) и войдите в Яндекс-аккаунт.
2. Нажмите **«Зарегистрировать новое приложение»**.
3. Название: любое (например, `ObsidianSync`).
4. В разделе **«Платформы»** выберите **«Веб-сервисы»**.
5. В поле **Redirect URI** введите:
   ```
   http://localhost:3333/oauth/yandex/callback
   ```
6. В разделе **«Доступы»** найдите **Яндекс.Диск** и включите:
   - `cloud_api:disk.read`
   - `cloud_api:disk.write`
7. Нажмите **Создать приложение** — получите **AppID** (Client ID) и **AppPassword** (Client Secret).

### Шаг 2 — Подключите в приложении

1. В настройках откройте раздел **Яндекс ID**.
2. Вставьте **Client ID** и **Client Secret** → нажмите **Сохранить**.
3. Нажмите **«Войти через Яндекс»** — откроется браузер с авторизацией.
4. После входа окно закроется, появится ваш Яндекс-email.

### Возможности после подключения

- **Резервная копия в Яндекс.Диск** — копирует .md файлы в папку `Obsidian Backup`.
- **Основная синхронизация** — включить/выключить автоматический backup.
- **App Dep/[компьютер]** — синхронизация локальной папки в `disk:/App Dep/ИмяКомпьютера`.

---

## Microsoft OneDrive

### Шаг 1 — Зарегистрируйте приложение в Azure

1. Откройте [portal.azure.com](https://portal.azure.com) и войдите в Microsoft-аккаунт.
2. В строке поиска введите **«App registrations»** → выберите результат.
3. Нажмите **«+ New registration»**.
4. Заполните:
   - **Name:** любое, например `ObsidianSync`
   - **Supported account types:** «Personal Microsoft accounts only»
   - **Redirect URI:** тип **Web**, значение:
     ```
     http://localhost:3333/oauth/microsoft/callback
     ```
5. Нажмите **Register**.

### Шаг 2 — Получите Client ID

На странице созданного приложения скопируйте **Application (client) ID** — это ваш **Client ID**.

### Шаг 3 — Создайте Client Secret

1. В левом меню выберите **«Certificates & secrets»**.
2. Вкладка **«Client secrets»** → **«+ New client secret»**.
3. Укажите срок действия → **Add**.
4. Скопируйте значение из колонки **Value** (оно видно только сразу после создания).

### Шаг 4 — Добавьте разрешения API

1. Левое меню: **«API permissions»** → **«+ Add a permission»**.
2. Выберите **Microsoft Graph** → **Delegated permissions**.
3. Найдите и добавьте:
   - `Files.ReadWrite`
   - `offline_access`
   - `User.Read`
4. Нажмите **«Grant admin consent»** (если доступно).

### Шаг 5 — Подключите в приложении

1. В настройках откройте раздел **Microsoft OneDrive**.
2. Вставьте **Client ID** и **Client Secret** → нажмите **Сохранить**.
3. Нажмите **«Войти через Microsoft»** — откроется окно авторизации.
4. После входа появится ваш Microsoft email.

### Возможности после подключения

- **Резервная копия в OneDrive** — копирует .md файлы в папку `Obsidian Backup`.
- **Основная синхронизация** — включить/выключить автоматический backup.
- **App Dep/[компьютер]** — синхронизация локальной папки в `App Dep/ИмяКомпьютера` на OneDrive.

---

## iCloud Drive

> iCloud Drive на Windows работает через локальную папку, которую создаёт приложение **iCloud для Windows**. OAuth не требуется.

### Шаг 1 — Установите iCloud для Windows

Скачайте и установите **iCloud для Windows** из Microsoft Store или с сайта Apple. После входа в Apple ID на компьютере появится папка `iCloudDrive`.

### Шаг 2 — Подключите в приложении

1. В настройках откройте раздел **iCloud Drive**.
2. Нажмите кнопку **«Найти»** — приложение автоматически попытается найти папку iCloudDrive.
3. Если не нашло, введите путь вручную, например:
   ```
   C:\Users\ВашеИмя\iCloudDrive
   ```
4. Нажмите **«Сохранить путь»** — появится зелёная галочка если папка найдена.

### Возможности после подключения

- **Резервная копия .md в iCloud** — копирует файлы в `iCloudDrive\Obsidian Backup\`.
- **Основная синхронизация** — включить/выключить автоматический backup.
- **App Dep/[компьютер]** — синхронизация в `iCloudDrive\App Dep\ИмяКомпьютера\`.

iCloud для Windows автоматически синхронизирует все файлы в этой папке с облаком.

---

## Расписание облачных копий

В разделе **«Расписание облачных копий»** можно настроить автоматический backup на все подключённые облачные сервисы одновременно.

| Элемент | Описание |
|---|---|
| Интервал (ч / м / с) | Как часто выполнять резервное копирование |
| **▶ Запустить** | Запустить автоматический режим |
| **■ Стоп** | Остановить |
| **↻ Сейчас** | Выполнить немедленно |
| Счётчик | Показывает время до следующего копирования |

### Управление синхронизацией папки App Dep (все сервисы)

Внизу раздела находятся кнопки:
- **✓ Включить всё** — включает синхронизацию папки App Dep на всех подключённых сервисах.
- **✗ Выключить всё** — выключает на всех сразу.

### Папка App Dep

При включённой синхронизации App Dep на каждом облачном сервисе создаётся структура:
```
App Dep/
  └── ИмяВашегоКомпьютера/
        ├── заметка1.md
        ├── заметка2.md
        └── ...
```
Это позволяет хранить файлы с разных компьютеров раздельно в одном облаке.

---

---

# Obsidian Sync — Setup Guide

---

## Table of Contents

- [Initial Setup](#initial-setup)
- [SSH Sync](#ssh-sync)
- [Google Drive](#google-drive-1)
- [Yandex.Disk](#yandexdisk)
- [Microsoft OneDrive](#microsoft-onedrive-1)
- [iCloud Drive](#icloud-drive-1)
- [Cloud Backup Schedule](#cloud-backup-schedule)

---

## Initial Setup

1. Launch the app — the main window will open.
2. Click the ⚙ gear icon (Settings) in the top right corner.
3. In the **SSH Connection** section, enter your server details and local Obsidian folder.
4. Click **Save**, then **▶ Start** to enable automatic sync on a schedule.

---

## SSH Sync

| Field | Description |
|---|---|
| Host / IP | Remote server address |
| Port | Usually `22` |
| Username | Server username |
| Password | Password, or leave blank if using a key |
| SSH Key | Path to key file (optional) |
| Remote folder | Folder on the server to pull files from |
| Local folder | Your Obsidian folder on this computer |
| Interval | How often to check for updates (h / m / s) |

Fill in the fields, click **Save**, then **▶ Start**.

---

## Google Drive

### Step 1 — Create a project in Google Cloud Console

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click **«Select project»** → **«New project»**, give it any name, click **Create**.
3. Left menu: **APIs & Services → Enabled APIs** → **«+ Enable APIs»** → search **Google Drive API** → **Enable**.

### Step 2 — Configure the OAuth consent screen

1. Left menu: **APIs & Services → OAuth consent screen**.
2. User type: **External** → **Create**.
3. Fill in: app name (anything), support email → **Save and Continue**.
4. On the **«Test users»** step, click **«+ Add Users»** and add your Gmail address.
5. Click **Save and Continue** to the end.

### Step 3 — Create OAuth credentials

1. Left menu: **APIs & Services → Credentials** → **«+ Create Credentials»** → **OAuth client ID**.
2. Application type: **Web application**.
3. Under **«Authorized redirect URIs»** add:
   ```
   http://localhost:3333/oauth/google/callback
   ```
4. Click **Create** — a window appears with your **Client ID** and **Client Secret**.

### Step 4 — Connect in the app

1. In settings, open the **Google Account** section.
2. Paste **Client ID** and **Client Secret** → click **Save**.
3. Click **«Sign in with Google»** — a browser window will open.
4. Sign in with the Gmail account added as a test user.
5. After signing in the window closes and your email appears in settings.

### Available features

- **↑ Save to Drive** — saves app configuration to Google Drive.
- **↓ Load from Drive** — restores configuration from Google Drive.
- **Backup .md files to Drive** — copies all .md files to `Obsidian Backup` on Drive.
- **Main sync** — enable/disable automatic backup on schedule.
- **App Dep/[computer]** — sync local folder to `App Dep/ComputerName` on Drive.

---

## Yandex.Disk

### Step 1 — Register an application

1. Go to [oauth.yandex.ru](https://oauth.yandex.ru) and sign in.
2. Click **«Register new application»**.
3. Name: anything (e.g. `ObsidianSync`).
4. Under **«Platforms»** select **«Web services»**.
5. In the **Redirect URI** field enter:
   ```
   http://localhost:3333/oauth/yandex/callback
   ```
6. Under **«Permissions»** find **Yandex.Disk** and enable:
   - `cloud_api:disk.read`
   - `cloud_api:disk.write`
7. Click **Create application** — you'll get **AppID** (Client ID) and **AppPassword** (Client Secret).

### Step 2 — Connect in the app

1. In settings, open the **Yandex ID** section.
2. Paste **Client ID** and **Client Secret** → click **Save**.
3. Click **«Sign in with Yandex»** — a browser window will open.
4. After signing in your Yandex email will appear.

### Available features

- **Backup to Yandex.Disk** — copies .md files to `Obsidian Backup`.
- **Main sync** — enable/disable automatic backup.
- **App Dep/[computer]** — sync local folder to `disk:/App Dep/ComputerName`.

---

## Microsoft OneDrive

### Step 1 — Register an application in Azure

1. Go to [portal.azure.com](https://portal.azure.com) and sign in.
2. In the search bar type **«App registrations»** and select the result.
3. Click **«+ New registration»**.
4. Fill in:
   - **Name:** anything, e.g. `ObsidianSync`
   - **Supported account types:** «Personal Microsoft accounts only»
   - **Redirect URI:** type **Web**, value:
     ```
     http://localhost:3333/oauth/microsoft/callback
     ```
5. Click **Register**.

### Step 2 — Get Client ID

On the app page, copy the **Application (client) ID** — this is your **Client ID**.

### Step 3 — Create a Client Secret

1. Left menu: **«Certificates & secrets»**.
2. Tab **«Client secrets»** → **«+ New client secret»**.
3. Set expiry → **Add**.
4. Copy the **Value** (only visible immediately after creation).

### Step 4 — Add API permissions

1. Left menu: **«API permissions»** → **«+ Add a permission»**.
2. Select **Microsoft Graph** → **Delegated permissions**.
3. Find and add:
   - `Files.ReadWrite`
   - `offline_access`
   - `User.Read`
4. Click **«Grant admin consent»** if available.

### Step 5 — Connect in the app

1. In settings, open the **Microsoft OneDrive** section.
2. Paste **Client ID** and **Client Secret** → click **Save**.
3. Click **«Sign in with Microsoft»** — a browser window will open.
4. After signing in your Microsoft email will appear.

### Available features

- **Backup .md files to OneDrive** — copies files to `Obsidian Backup`.
- **Main sync** — enable/disable automatic backup.
- **App Dep/[computer]** — sync local folder to `App Dep/ComputerName` on OneDrive.

---

## iCloud Drive

> iCloud Drive on Windows works through a local folder created by the **iCloud for Windows** app. No OAuth required.

### Step 1 — Install iCloud for Windows

Download and install **iCloud for Windows** from the Microsoft Store or Apple's website. After signing in with your Apple ID, an `iCloudDrive` folder will appear on your computer.

### Step 2 — Connect in the app

1. In settings, open the **iCloud Drive** section.
2. Click **«Detect»** — the app will try to find the iCloudDrive folder automatically.
3. If not found, enter the path manually, e.g.:
   ```
   C:\Users\YourName\iCloudDrive
   ```
4. Click **«Save path»** — a green checkmark will appear if the folder is found.

### Available features

- **Backup .md files to iCloud** — copies files to `iCloudDrive\Obsidian Backup\`.
- **Main sync** — enable/disable automatic backup.
- **App Dep/[computer]** — sync to `iCloudDrive\App Dep\ComputerName\`.

iCloud for Windows automatically syncs all files in this folder to the cloud.

---

## Cloud Backup Schedule

The **«Cloud Backup Schedule»** section lets you run automatic backups to all connected cloud services simultaneously.

| Element | Description |
|---|---|
| Interval (h / m / s) | How often to run the backup |
| **▶ Start** | Start automatic mode |
| **■ Stop** | Stop |
| **↻ Now** | Run immediately |
| Countdown | Shows time until next backup |

### App Dep folder sync — all services

At the bottom of the section:
- **✓ Enable all** — enables App Dep folder sync on all connected services.
- **✗ Disable all** — disables it on all at once.

### The App Dep folder

When App Dep sync is enabled, each cloud service gets this structure:
```
App Dep/
  └── YourComputerName/
        ├── note1.md
        ├── note2.md
        └── ...
```
This lets you store files from multiple computers separately within the same cloud account.
