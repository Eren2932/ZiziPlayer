# ZiziPlayer 6.84.0-rc2 — исправление сборки

Полный мобильный проект, `versionCode = 177`. База исправления — ранее выданный `ZiziPlayer-v6.84.0-rc1-source.zip`, SHA-256 `6624ec8d23238d22e15d23fdb1a75adb050c1762c8597cf54eb90a3df96cc042`.

## Что было сломано

Предоставленный лог GitHub Actions (run `37137739056`) содержит семь диагностик на каждой из двух задач `compileDebugKotlin` и `compileReleaseKotlin`. Они сводятся к четырём причинам в трёх файлах. Это ошибки изменений rc1, а не настройки keystore, сервера или репозитория.

| Причина | Исправление |
|---|---|
| `supportsRecommendations` отсутствует в `RemoteCatalog` | Убрано обращение к вымышленному свойству. Поддержка определяется настоящим nullable-ответом `recommendHome`; null при явном выборе приводит к ошибке с сохранённым выбором, не к ложному успеху. |
| `app.ziziplayer` внутри `HomeScreen` разрешается через локальную переменную `app` | `HomeTasteInviteGeometry` и `Amoled` явно импортированы и используются по короткому имени. |
| `ZiziSheetScaffold` импортирован из `ui.components`, хотя объявлен в `ui.screens` | Неверный импорт удалён; используется существующая функция своего пакета из `Sheets.kt`. |
| `ColumnScope.AnimatedVisibility` недоступен через неявный receiver внутри `Box` | Вызвана полным именем top-level `androidx.compose.animation.AnimatedVisibility`. Устранена и связанная ошибка контекста `@Composable`. |

## Что сохранено

Код расчёта геометрии, коллаж, экран выбора, поиск, вставка похожих исполнителей, ограничения выбора, отмена устаревших запросов и шифрованное хранилище не заменялись. В production изменены только три Kotlin-файла выше и номер версии в Gradle. Backend и playback не менялись.

## Проверки и ограничения

Добавлены четыре source-регрессии в существующий `tools/test_home_taste_6840.py`; они подключены к действующему `check_selftest.py`. Все четыре сначала запущены против реально выданных исходников rc1 и закономерно упали, затем прошли на rc2. Это проверка конкретных исходных конструкций, **не** Kotlin-компиляция.

Текущие результаты полного локального прогона, Java-проверок, проверок импортов, лексического синтаксиса и вызовов находятся в `verification/artist-onboarding-6840-rc2/validation.json` и `selftest-and-source-checks.log`. Исторический отчёт rc1 оставлен для воспроизводимости; после его выдачи Android-компиляция rc1 не прошла, как показал присланный лог.

**Gradle/Android-сборка rc2, тесты на устройстве, нативная визуальная сверка и живой сервер здесь не запускались.** Окончательное подтверждение сборки — новый запуск GitHub Actions, не число source-проверок. Совместимость сервера и происхождение декоративных портретов описаны в `ARTIST_ONBOARDING_6840.md` и `REFERENCE_ASSET_NOTICE.md`; rc2 этих ограничений не меняет.

## Как использовать

Загрузить `ZiziPlayer-v6.84.0-rc2-source.zip` в корень репозитория вместо rc1 или рядом с ним. Workflow выбирает проект с максимальным `versionCode`: 177 выше 176. Десктопный `current.json` и GitHub Secrets менять не нужно.

При локально установленном Android SDK и доступных Gradle-зависимостях:

````bash
python tools/check_selftest.py
./gradlew :app:compileDebugKotlin :app:compileReleaseKotlin :app:testDebugUnitTest :app:testReleaseUnitTest
./gradlew :app:assembleDebug
````

Инструментальные тесты API 28/35 запускаются отдельно через существующий workflow с `run_camera_tests`.
