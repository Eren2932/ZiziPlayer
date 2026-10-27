# Zizi 7.6.1 (сборка 278): починка самотеста после 7.6.0

Код приложения не менялся: 7.6.1 = 7.6.0 + исправленный тест + поднятая версия.

## Что упало

Run по 7.6.0, шаг «Самотест проверок» (`tools/check_selftest.py`), единственный провал из 138 наборов:

```
FAIL: test_sharing_fails_instead_of_sending_text (tools/test_download_library_6952.py, Wiring)
AssertionError: 'OfflineStore.shareTarget' not found in 'track: TrackEntity) { ... shareOriginal ...'
```

Самотест стоит первым и валит сборку, поэтому ни синтаксис, ни импорты, ни Gradle (`compileDebugKotlin`, `testDebugUnitTest`) в том прогоне не выполнялись.

## Причина

Тест вырезал тело `shareTrack` и искал в нём файловый контракт отправки. В 7.6.0 `shareTrack` стал развилкой
(«как слышу» или оригинал), а сам код отправки переехал в `shareOriginal` и `sendProcessed`. Тест остался привязан к старому месту.

Второй дефект того же теста: ожидание `ClipData.newUri` противоречит решению 6.96.1 (тип клипа задаётся вручную через
`ClipDescription`, что закреплено в `test_audio_container_6961.py`). Тест до сих пор проходил случайно: строка `ClipData.newUri`
стояла в КОММЕНТАРИИ внутри `shareTrack`.

## Что исправлено

`test_sharing_fails_instead_of_sending_text` проверяет контракт на всех трёх функциях:

- `shareTrack`: без обработки идёт в `shareOriginal(track)`, с обработкой открывает лист (`processedShare.value = request`);
- `shareOriginal`: `withContext`, `OfflineStore.shareTarget`, `EXTRA_STREAM`, `ClipDescription(`, `FLAG_GRANT_READ_URI_PERMISSION`;
- `sendProcessed`: `EXTRA_STREAM`, `ClipDescription(`, `FLAG_GRANT_READ_URI_PERMISSION`, `AudioPayload.shareMime(`;
- ни в одной из трёх нет `EXTRA_TEXT`, `text/plain`, `ClipData.newUri` в КОДЕ (комментарии отбрасываются).

Проверено мутациями: подмена `EXTRA_SUBJECT` на `EXTRA_TEXT` в `shareOriginal` и удаление вызова `shareOriginal(track)` из
`shareTrack` валят тест.

## Что проверено

Локально, на распакованном архиве: `check_selftest.py` (138 наборов, код выхода 0), `check_kotlin_syntax`, `check_imports`,
`check_static_refs`, `check_package_shadow` (0 замечаний), серверные тесты (guard, catalog wiring, device, py_syntax),
шаги «Stage 2» (18 файлов), `lyrics_server` и `chat_server` unit-тесты.

## Чего НЕ проверено

**Gradle не запускался**: в песочнице нет Android SDK. Компиляция Kotlin 7.6.0 (новый пакет `render/`, `ProcessedShareSheet.kt`,
правки `MainActivity.kt`) ни в одном прогоне CI ещё не проходила: следующий шаг после самотеста может найти свои ошибки.
Тесты `accounts_server` не гонялись (нужен pip). Эмулятор и устройство не использовались.

Заметка: в `CHANGELOG_v7.6.0.md` написано «все 189 python-проверок ведут себя так же, как на 7.5.7». Для этого теста это не так:
он проходил на 7.5.7 и падал на 7.6.0.
