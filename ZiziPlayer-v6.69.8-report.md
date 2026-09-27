# ZiziPlayer 6.69.8 — CI renderer candidate

**Статус: подготовлен и проверен офлайн кандидат исправления сбоя эмулятора. Успешный Android/Lavapipe и release-прогон ещё НЕ получен.**

## Что подтверждено

27 сентября 2026 повторно проверены актуальные дерево и запуски публичного репозитория
https://github.com/Eren2932/ZiziPlayer. Последний мобильный исходный ZIP — 6.69.7,
versionCode 132. Его Git blob `a61e87b202189a8b018980b2a50c48525f4ad71a` совпал с
сохранёнными байтами архива; CRC проверены. Корневой workflow в GitHub всё ещё имеет blob
`0d81c429edcc4473c4a6106b8654a139f09a8e82` — ранее подготовленный патч туда не применён.

Последний workflow run: https://github.com/Eren2932/ZiziPlayer/actions/runs/36307603542
Commit: `2680f16e30a9fe0fd686219d85de89ef19b46f7d`. В его журналах:

- debug APK и test APK собраны;
- API 28 прошёл 25/25;
- API 35 завершил 9 тестов, затем оборвался; XML содержит 10 записей, включая прерванную;
- Gradle: `device 'emulator-5554' not found`, `Expected 27 tests, received 9`;
- release/R8/подпись после этого не выполнялись.

Эмулятор исчез до команды штатного cleanup. В конце выполнялся
`uniformBodyKeepsBrightnessDuringMerge6696`; assertion о неправильной яркости не получен.
Последнее окно — между idle на progress=0.35 и завершением захвата кадра. Это НЕ доказывает
дефект PixelCopy, RenderEffect или математики. Native stack trace и доказательство OOM
в имеющихся отчётах отсутствуют. Сообщение Lyrics configuration не является причиной сбоя.

## Изменения 6.69.8

`versionName = "6.69.8"`, `versionCode = 133`: корневой распаковщик выберет этот архив,
а не 6.69.7. `app/src/main`, `app/src/test`, `app/src/androidTest` и серверный код не меняются.
Тестовый inventory, пороги яркости/геометрии, runner и порядок release gates сохранены.

В workflow API 35 переключён с `swiftshader_indirect` на `lavapipe`; удалено старое
принудительное `-feature -Vulkan`, добавлен `-verbose`. Это изменение графической конфигурации,
не доказанный fix конкретного native-дефекта. Официальная документация перечисляет Lavapipe
и помечает swiftshader_indirect deprecated с 36.4.9:
https://developer.android.com/studio/run/emulator-acceleration
Deprecated само по себе не означает broken.

Для обоих API фиксируется emulator build `15917651` (тот же 37.1.11.0, не downgrade) и
commit android-emulator-runner `a421e43855164a8197daf9d8d40fe71c6996bb0d`.
Поддержка входа `emulator-build` проверена по action.yml. Установка фиксированного бинарника
в этой среде не выполнялась. Рендеринг API 28 оставлен прежним: он уже проходил 25/25.
Ubuntu/system-image ревизии не зафиксированы; полной воспроизводимости окружения это не даёт.

После API 35 до выгрузки артефакта собираются доступные crashdb, source.properties, AVD
config, версия emulator, GPU modes, host dmesg через sudo -n и список coredumpctl.
Диагностика хранится в `build/ci/android-api-35/emulator-host/` и существующем артефакте
`camera-collection-api-35`. Лимит копирования файлов 64 MiB; отсутствующие файлы, ограничения
и отказ команд отражаются в отчётах. Полный AVD, keystore, кэши и окружение не копируются.
Наличие native dump не гарантируется; диагностические дампы стоит просматривать перед
публикацией — они потенциально содержат фрагменты памяти тестового процесса.

Обе копии workflow внутри ZIP синхронизированы с отдельным файлом `build.yml`.
Offline-тест `tools/test_camera_ci_6697.py` теперь строго проверяет раздельные backend
API 28/API 35, pins и порядок diagnostics/upload. Проверка старого флага на ОБОИХ API
заменена на проверку нового целевого поведения; Android assertions не ослаблены.

## Что реально запущено

В the Computer выполнены:

- полный `python tools/check_selftest.py`: exit 0;
- 13 тестов патча: YAML-структура, границы diff, неизменность gates, Bash/heredoc,
  распаковщик ZIP (включая закрытый ZIP, дубликаты версий, traversal), сбор диагностик;
- 12 CI fixtures: подставные adb/Gradle, строгий inventory и неполные/stale XML;
- 4 material-теста: исполнение production Java с **691077 assertions**, 6 мутаций отвергнуты;
- 7 geometry/wiring-тестов: production Java с **463009 assertions**, 8 мутаций отвергнуты;
- Kotlin syntax/import/static-reference эвристики: exit 0, замечаний нет;
- повторная проверка реального оборванного API 35: корректно отклонён, exit 1;
- проверка упаковки: CRC, побайтовая неизменность app/src, одинаковые workflow,
  выбор 6.69.8/versionCode 133 реальным распаковщиком рядом с 6.69.7.

Это 1154086 assertions двух production Java-наборов, а НЕ столько независимых сценариев
и НЕ проверка Android-пикселей. Java-компиляция выполнялась встроенным compiler module
JDK 21 с source/target 17; она не заменяет Gradle/D8/R8.
Логи, снимки parsed YAML и тесты находятся в `verification/v6.69.8/`.
Исторические `verification/v6.69.7` и более старые документы оставлены как история,
не как доказательство прохождения новой версии.

**Android SDK/emulator и Gradle в the Computer отсутствуют: APK, instrumentation на
Lavapipe, release/R8 и физический телефон для 6.69.8 здесь не проверены.**

## Установка с телефона — нужны ДВА изменения

1. Загрузить `ZiziPlayer-v6.69.8.zip` в корень репозитория. Это исходники, не APK.
   Старые версии можно оставить: versionCode 133 выше. Не загружать две копии 6.69.8
   под разными именами — распаковщик намеренно отклоняет дубликат максимальной версии.
2. Открыть существующий `.github/workflows/build.yml` в GitHub, нажать редактирование,
   полностью заменить содержимое приложенным `build.yml` и сохранить в main.
   При раздельных коммитах сначала загрузить ZIP, затем заменить workflow; новый push
   отменит предыдущий прогон той же ветки благодаря concurrency.

**Не загружать build.yml просто в корень и не ограничиваться ZIP: GitHub НЕ исполняет
workflow внутри ZIP.** В ZIP правильная копия также лежит в
`ZiziPlayer-6.69.8/repo-update/.github/workflows/build.yml`.
После обоих изменений смотреть самый новый запуск Build & release ZiziPlayer APK.
Ожидаемые gates: JVM → debug/test APK → API 28 25/25 → API 35 27/27 → release → подпись/APK.
Публикация при провале, continue-on-error, удаление тестов и повторы до зелёного не добавлены.

Для первичного подтверждения нужен полный зелёный прогон; затем желательно повторить
на том же коммите. Если снова упадёт, нужны Download log archive и camera-collection-api-35
ИМЕННО нового запуска. Отдельно отличаем native/device loss от assertion яркости.
Репозиторий и Actions из этой сессии не изменялись и не запускались.
