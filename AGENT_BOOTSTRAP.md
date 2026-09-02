# AGENT BOOTSTRAP — поднять проект ZiziPlayer в новом чате за 2 минуты

> Актуально на **6.24.4** (`versionCode 47`), 2 сентября 2026.
> Этот файл заменяет версию, которая описывала путь через `ZiziPlayer-v5.0-source.zip` и GitHub Blob API.
> Тот путь больше не нужен: архив забирается **одним запросом**.

---

## ПАСТА ДЛЯ НОВОГО ЧАТА (копировать целиком, вставить первым сообщением)

```
Проект: ZiziPlayer — Android-плеер. Kotlin 2.1 + Compose + Media3 1.5.1 + Room 2.7.1.
Репозиторий (публичный): https://github.com/Eren2932/ZiziPlayer

Сделай сразу, без вопросов:

1) Включи скилл Computer.

2) Скачай исходники ОДНИМ запросом:
   files__upload_from_url
     url:          https://raw.githubusercontent.com/Eren2932/ZiziPlayer/main/ZiziPlayer-v6.24.4.zip
     path:         conversation-<id>/ZiziPlayer-v6.24.4.zip
     content_type: application/octet-stream

3) Распакуй в песочнице:
   mkdir -p /tmp/zp && cd /tmp/zp
   unzip -oq /files/conversation/ZiziPlayer-v6.24.4.zip
   find . -type f | sort

4) Освежи знания — прочитай в таком порядке:
   STATUS.md                 (общая картина тракта и сервера)
   CHANGELOG_v6.24.4.md      (свой звуковой тракт, эквалайзер)
   CHANGELOG_v6.24.3.md      (предыдущий релиз)
   ISLAND_PLAN_v6.25.0.md    (что делаем дальше)

Отвечай по-русски, по делу, без воды. Приоритет — реальные баги и то, что сломается у людей,
которые ОБНОВЛЯЮТСЯ, а не ставят начисто.
```

---

## Почему именно так

`files__upload_from_url` исполняется **на сервере Dust**, мимо egress-фильтра песочницы
(`codeload.github.com` и `github.com` из песочницы закрыты — не трать на них время).
`raw.githubusercontent.com` отдаёт файл как есть, поэтому `content_type: application/octet-stream`
принимается и zip приезжает бинарём.

Старая схема (дерево репозитория → `sha` блоба → Blob API → base64 → `base64 -d`) работала,
но стоила двух запросов, промежуточного JSON на пару мегабайт и декодирования. Она нужна
**только** если raw отдаёт 404 — например, файл переименован. Тогда:

```
files__upload_from_url
  url: https://api.github.com/repos/Eren2932/ZiziPlayer/git/trees/main?recursive=1
  path: conversation-<id>/tree.json
  content_type: application/json
```

и смотришь фактическое имя архива в `.tree[].path`.

**UI Dust не даёт загрузить `application/zip` руками** — это ограничение интерфейса, а не сети.
Загрузка по url его обходит.

---

## Правила проекта (не обсуждаются)

1. **Никаких секретов в коде.** Только `.env`, `System.getenv`, GitHub Secrets.
   Перед отдачей архива — скан: `api_key`, `token`, `secret`, `AKIA`, `-----BEGIN`.
2. **Проверки перед сборкой обязательны**, Gradle в песочнице запустить нечем (нет Android SDK,
   сеть закрыта), поэтому синтаксис проверяется своими скриптами:
   ```
   python3 tools/check_kotlin_syntax.py
   python3 tools/check_static_refs.py
   ```
   Оба появились не от хорошей жизни: 6.19.0 не собралась из-за вложенного блочного комментария
   в KDoc, 6.19.1 — из-за члена экземпляра, вызванного через имя класса.
3. **Миграции Room — только вручную, без `fallbackToDestructiveMigration`.** Правила в
   `data/ZiziDatabase.kt`. Внешних ключей и CASCADE в проекте нет сознательно: они несовместимы
   с `OnConflictStrategy.REPLACE` в `upsertTracks` и стирали бы избранное при каждом пересканировании.
4. **Nullable-колонка добавляется БЕЗ `DEFAULT`.** Room не пишет DEFAULT в свою схему для такого
   поля, и `DEFAULT ''` в миграции валит проверку идентичности схемы у всех обновляющихся и ни у
   кого, кто ставит начисто. На этом уже подрывались миграции 2→3 и 3→4.
5. **Аудиоцепочка собирается только через `DefaultAudioProcessorChain`.** Соберёшь массивом
   вручную — молча исчезнут штатные `SilenceSkipping` и `Sonic`, то есть перестанут работать
   скорость, тональность и «пропускать тишину», и связать это с эквалайзером никто не сможет.
6. **Audio offload включать нельзя.** В нём сжатый поток уходит в DSP телефона мимо всей
   обработки: эквалайзер не звучит, и только на части устройств.
7. Версия поднимается **в паре**: `versionCode` и `versionName` в `app/build.gradle.kts`,
   плюс новый `CHANGELOG_vX.Y.Z.md` и шапка `STATUS.md`.

---

## Карта проекта (139 файлов, куда смотреть)

| Область | Файлы |
|---|---|
| Звуковой тракт (свой DSP) | `playback/dsp/` — `Biquad.kt`, `DspConfig.kt`, `DspEngine.kt`, `DspPresets.kt`, `ZiziAudioProcessor.kt`, `ZiziSpectrum.kt` |
| Воспроизведение | `playback/PlaybackService.kt`, `playback/PlayerController.kt` |
| Сеть и резолв | `data/remote/*`, `playback/StreamResolver.kt`, `server/zizi_resolver.py` |
| База | `data/ZiziDatabase.kt` (версия **7**), `data/Entities.kt`, `data/MusicDao.kt` |
| Настройки | `data/SettingsStore.kt` (DataStore) |
| Экраны | `ui/screens/` — `PlayerScreen.kt`, `EqualizerScreen.kt`, `LibraryScreen.kt`, `SearchScreen.kt`, `Sheets.kt` |
| Состояние UI | `ui/MainViewModel.kt`, `ui/SearchViewModel.kt` |
| Тесты | `app/src/test/...` — `DspEngineTest.kt`, `TrackIdTest.kt`, `SessionRequestPolicyTest.kt` |

Сборка на устройстве — `BUILD_FROM_PHONE.md`. CI — `.github/workflows/build.yml`
(синтаксис → статические ссылки → unit-тесты → сборка).

---

## Состояние на 6.24.4

**Готово:** свой звуковой тракт вместо прошивочных эффектов (10 полос, ревер, «под водой», 8D,
ширина стерео, сатуратор, воздух, лимитер), 26 пресетов в трёх складывающихся группах, свои
пресеты в таблице `eq_profiles`, спектр без `Visualizer` и без разрешения на микрофон, база 6 → 7
с переносом старого «Реверб %», экран эквалайзера с жестом по холсту.

**Следующее:** `ISLAND_PLAN_v6.25.0.md` — «Островок» внутри приложения и уведомление под
Android 16 (бамп `targetSdk 36` — главный риск релиза).

**Долги:** настройки тракта не уезжают вместе с плейлистами при экспорте; на очень старых
телефонах полностью забитый тракт заметен по батарее (выключенный тумблер стоит ровно ноль).
