# Как установить обновление в репозиторий

Это набор файлов ДЛЯ размещения в Eren2932/ZiziPlayer, не бинарный установщик. Сначала распакуй внешний ZiziDesktop-0.3.0-repo-update.zip. Не загружай его целиком в корень как новую мобильную версию.

## Загрузка через GitHub

Перенеси содержимое папок desktop/ и docs/ в одноимённые папки репозитория с сохранением структуры. Замени desktop/current.json. Исходный desktop/releases/ZiziDesktop-0.3.0-preview-source.zip, напротив, распаковывать в репозитории не нужно: его извлекает CI. Старый ZIP 0.2.0 можно оставить для отката.

В .github/workflows создай desktop.yml из этого пакета. Если веб-загрузчик не показывает скрытую .github, открой репозиторий -> Add file -> Create new file, задай полный путь .github/workflows/desktop.yml и вставь содержимое. Действующий .github/workflows/build.yml НЕ менять и НЕ заменять. Мобильный ZIP 6.39.9 не трогать.

Удали прежний desktop.yml из корня (он не работает как GitHub workflow). Добавь HANDOFF_DESKTOP_0.3.0.md в корень для следующего диалога. CI-скрипт ci/extract_desktop.py уже есть в репозитории и не меняется.

После попадания правильного workflow в default branch: Actions -> Build Zizi Desktop Windows preview (manual) -> Run workflow. Должны пройти тесты и createDistributable; затем скачать ZiziDesktop-Windows-x64-0.3.0-preview. При ошибке скачать ZiziDesktop-test-reports. Не публиковать release до успешной Windows-приёмки.

## Локально без GitHub

Распакуй только desktop/releases/ZiziDesktop-0.3.0-preview-source.zip. Открой новую папку отдельно от рабочей 0.2.0; выполни Build-Desktop.cmd -Action check/run с прежними путями Gradle и FFmpeg. Пример есть в README.md исходного проекта. Не удаляй рабочую 0.2.0 до проверки.

## Откат

Верни прежний desktop/current.json из git-истории, указывающий на ZIP 0.2.0 с прежним SHA-256. Правильное расположение .github/workflows/desktop.yml оставь. Ни Android ZIP, ни Android workflow для отката Desktop менять не требуется.
