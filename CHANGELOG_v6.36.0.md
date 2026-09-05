# ZiziPlayer 6.36.0 — «гибрид наконец включён»

**Дата:** 5 сентября 2026. **versionCode 66, versionName 6.36.0.** База — 6.35.0 (`versionCode 65`).
**Что это за релиз:** ничего нового не написано. Включено то, что лежало написанным с 6.30.0 и
шесть релизов подряд не работало, потому что дефолт настройки указывал мимо.

---

## 0. Диагноз: витрина была построена и не подключена

С 6.30.0 в реестре каталогов первым стоит `MixCatalog` — витрина Deezer, склеенная с остальными
источниками. Сервер к нему готов: `/catalog/*` и `/match/deezer` живые, `catalog/health` отвечает
`{"ok":true,"deezer":true}` с мобильного интернета без VPN.

Пользователь не видел из этого ничего. Причина в одной строке:

```kotlin
// SettingsStore.kt, до 6.36.0
val catalogProvider: String = "yt",
```

`CatalogRegistry.withFallback(preferred)` ставит предпочтённый каталог **первым**, а остальные
пробует, только если первый УПАЛ. С включённым VPN Innertube не падал — значит отвечал всегда, и
`mix` не вызывался ни разу. То есть человек с VPN видел ровно ту сырую выдачу YouTube, ради ухода
от которой писалась 6.30.0, а человек без VPN получал 4.5 секунды ожидания и ту же выдачу через
запасной путь.

Добивала строка «Источник» в настройках: она переключала `yt` ⇄ `audius` и про микс не знала. Тот,
кто разбирался «почему всё как на ютубе», этой строкой записывал себе явное `yt` — то есть делал
ровно то, от чего убегал, и это значение переживало обновление приложения.

---

## 1. Дефолт каталога: `yt` → `mix`

| Файл | Правка |
|---|---|
| `data/SettingsStore.kt` | `catalogProvider` по умолчанию `mix` (в `UserSettings` и в чтении из DataStore) |
| `data/SettingsStore.kt` | `migrateCatalogDefault()` — разовая уборка сохранённого `yt` |

Смены дефолта в коде мало: обновление APK не трогает DataStore, и у всех, кто трогал «Источник»,
там лежит явное `yt`, которое сильнее нового дефолта. Миграция удаляет **только** значение `yt` и
**только один раз** (флаг `catalog_default_mix_v1`): выбранный осознанно `audius` остаётся, а выбор,
сделанный уже после обновления, затереть невозможно.

Запускается первой строкой стартового прогрева, до чтения настроек, — иначе прогрев успел бы
прочитать то значение, которое мы прямо сейчас отменяем.

---

## 2. Телефон больше не ходит в Google

Новая настройка `youtubeDirect`, **по умолчанию выключена**. Это не про приватность: без VPN запрос
к Innertube не получает отказ, он висит до таймаута. Выключенный флаг убирает три источника такого
ожидания.

**Поиск.** `MixCatalog` получил `active` — части, которые опрашиваются сейчас:

```kotlin
private val active: List<RemoteCatalog>
    get() = if (RemoteRuntime.youtubeDirect) parts else parts.filter { it.id != InnertubeCatalog.ID }
```

Полный `parts` остался у `unwrap`, и это принципиально: `r:mix:yt:...`, сохранённый в избранном при
включённом флаге, обязан резолвиться после того, как флаг выключили.

**Аттестация.** `SessionWebToken.start()` убран из `ZiziApplication.onCreate`. Он поднимал WebView и
шёл в Google на каждом запуске приложения — при том что нужен ровно одному потребителю, прямому
поиску в Innertube. Теперь стартует в прогреве и только под флагом. Ленивый путь сохранён:
`SessionWebToken.await()` сам зовёт `start()`, если защищённый запрос всё-таки случится.

**Прогрев.** Грелись все каталоги подряд, то есть Innertube грелся всегда. Теперь греется один — тот,
который будет отвечать (`registry.byId(catalogProvider)`).

**Чего это НЕ трогает:** воспроизведение. Звук и так идёт через `/stream` (`RESOLVER_PROXY = true`),
и старые треки `r:yt:...` играют по-прежнему: `InnertubeCatalog.resolveStream` первым делом
спрашивает `ZiziResolve` и до клиентской лестницы доходит, только когда сервер недоступен.

**В настройках** строка «Источник» заменена переключателем «Ходить в YouTube с телефона» — то
единственное, что здесь реально меняет поведение и что нельзя решить за человека: выкл — витрина,
обложки и звук через свой сервер, VPN не нужен; вкл — в поиск добавляется охват YouTube, и VPN
нужен снова.

---

## 3. Обложки через свой сервер

CDN обложек был последним местом, куда телефон ходил напрямую. Без VPN это давало серую сетку при
полностью живом каталоге: текст приехал, картинок нет.

**Сервер, `server/zizi_catalog.py`** — новый `GET /img?u=<адрес>`: тянет картинку сам, кладёт на
диск (`ZIZI_IMG_DIR`, по умолчанию `/opt/zizi/img`), отдаёт с `Cache-Control: immutable`. Кэш
бессрочный — адрес обложки у Deezer и YouTube содержит идентификатор записи и меняется вместе с
картинкой. Квота `ZIZI_IMG_QUOTA_MB` (512 МБ), вытеснение по времени доступа, счёт только при
переполнении. Домены — по **суффиксу** хоста и только каталожные: без этой проверки `/img` был бы
открытым прокси, и первый же чужой бот утащил бы канал VPS на что угодно. Запись через `*.part` и
`os.replace`: два телефона, открывшие один чарт, пишут один и тот же путь.

**Клиент** — `ZiziResolve.imageUrl()` и один изменённый порядок попыток в `Artwork.fromNetwork`:

```kotlin
val bytes = ZiziResolve.imageUrl(sized)?.let { ZiziHttp.fetchBytes(it) }
    ?: ZiziHttp.fetchBytes(sized)
    ?: (if (sized != url) ZiziHttp.fetchBytes(url) else null)
    ?: return null
```

Прокси здесь — улучшение, а не обязательный шаг: если `/img` на сервере ещё не обновлён, ответ 404
просто уронит первую попытку и обложка приедет напрямую, как раньше. Никакой отдельной выкладки
клиента и сервера «в один момент» не требуется.

`/catalog/health` теперь показывает и `images_cached`.

---

## 4. Что нужно сделать на сервере

```bash
# 1. заменить файл
scp server/zizi_catalog.py root@147.45.166.244:/opt/zizi/zizi_catalog.py
# 2. каталог под обложки (создастся и сам, но пусть права будут правильные)
ssh root@147.45.166.244 'mkdir -p /opt/zizi/img && systemctl restart zizi-resolver'
# 3. проверка
curl -s 'http://147.45.166.244:8080/catalog/health'
curl -sI 'http://147.45.166.244:8080/img?u=https%3A%2F%2Fe-cdns-images.dzcdn.net%2Fimages%2Fcover%2F1%2F500x500-000000-80-0-0.jpg'
```

`zizi_resolver.py` не изменён ни на байт — это условие, а не совпадение.

---

## 5. Проверки

```
tools/check_kotlin_syntax.py   files with issues: 0
tools/check_imports.py         проблем: 0
tools/check_static_refs.py     подозрений: 0
tools/check_call_args.py       подозрительных вызовов: 3   (все три — из 6.35.0, в нетронутых
                                                            файлах: EqualizerScreen, PlayerScreen)
python3 -c "import ast; ast.parse(open('server/zizi_catalog.py').read())"   ok
```

## 6. Изменённые файлы

```
app/build.gradle.kts                                    versionCode 66, 6.36.0
app/src/main/java/app/ziziplayer/ZiziApplication.kt      прогрев одного каталога, аттестация под флагом
app/src/main/java/app/ziziplayer/data/SettingsStore.kt   дефолт mix, youtubeDirect, миграция
app/src/main/java/app/ziziplayer/data/MusicRepository.kt setYoutubeDirect
app/src/main/java/app/ziziplayer/data/remote/DeezerCatalog.kt   MixCatalog.active
app/src/main/java/app/ziziplayer/data/remote/ZiziResolve.kt     imageUrl()
app/src/main/java/app/ziziplayer/playback/RemoteRuntime.kt      youtubeDirect
app/src/main/java/app/ziziplayer/ui/MainViewModel.kt            setYoutubeDirect
app/src/main/java/app/ziziplayer/ui/components/Artwork.kt       обложка через /img
app/src/main/java/app/ziziplayer/ui/screens/Sheets.kt           «Источник» → «Ходить в YouTube»
server/zizi_catalog.py                                          GET /img, images_cached
```
