# Как применить Desktop 0.3.4 preview

Это обновление ИСХОДНИКОВ, не готовый Windows EXE. В GitHub ничего автоматически не отправлено, Actions не запускались.

Распакуй содержимое ZiziDesktop-0.3.4-repo-update.zip в корень локального репозитория с сохранением путей. Если после 0.3.3 появились свои изменения, сначала сравни diff. Старый desktop/releases/0.3.3 ZIP не удаляй.

Обновляются desktop/current.json и ci/check_desktop_source.py; добавляются новый source ZIP и документация. Внутренний desktop/releases/ZiziDesktop-0.3.4-preview-source.zip вручную распаковывать в корень репозитория не нужно: это делает ci/extract_desktop.py. Просто загрузить внешний repo-update ZIP одним файлом в GitHub недостаточно. После загрузки содержимого desktop/current.json должен показывать 0.3.4-preview.

Закоммить в отдельную ветку и запусти существующий Actions → Build Zizi Desktop Windows preview (manual). Сохрани те же настройки RESOLVER_URL/RESOLVER_TOKEN и allow_http/DESKTOP_ALLOW_HTTP, с которыми работает твоя сборка. Не присылай секреты в чат и не записывай их в код. Workflows/Android не изменены.

После успешных тестов скачай ZiziDesktop-Windows-x64-0.3.4-preview. Распакуй всю app-image папку, не один EXE. FFmpeg и FFprobe остаются внешними, путь сохраняется как раньше. Не запускай старую и новую версии одновременно с общей папкой данных. Перед испытанием сделай копию %LOCALAPPDATA%/ZiziPlayer.

Если CI упадёт, сохрани ZiziDesktop-test-reports и desktop-build.txt: Kotlin/Compose в the Computer не собирались. Не обходи тесты ради EXE. Если сборка успешна, проверь checklist REVIEW_0.3.4.md, затем пришли скриншоты новой версии при том же масштабе.

Для отката верни desktop/current.json и ci/check_desktop_source.py из своего предыдущего коммита. Формат библиотеки не менялся.
