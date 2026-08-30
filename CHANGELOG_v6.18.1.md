# ZiziPlayer 6.18.1

versionCode 34 · versionName 6.18.1 · база v5 (миграции нет, ставится поверх 6.18.0/6.17.0)

Хотфикс одной строки: 6.18.0 не собралась.

## Что упало

```
e: .../ui/components/ZiziIcons.kt:45:13 Unresolved reference 'path'
> Task :app:compileReleaseKotlin FAILED
```

`path { }` внутри `ImageVector.Builder` — не метод билдера, а top-level extension
`androidx.compose.ui.graphics.vector.path`. Без явного импорта имя не резолвится; в файле были
импортированы `ImageVector` и `PathBuilder`, а сама DSL-функция — нет. Никакой другой ошибки
компиляции в логе нет: ресурсы, KSP и остальные 46 файлов прошли.

## Что сделано

* `ZiziIcons.kt`: добавлен `import androidx.compose.ui.graphics.vector.path`.
* `ZiziIcons.stroked(...)`: `pathBuilder = pathBuilder` заменено на трейлинг-лямбду
  `) { pathBuilder() }`. `path` объявлена `inline`, и передача туда сохранённого функционального
  значения вместо литерала — лишний риск на ровном месте; лямбда-литерал компилятор глотает всегда.
* Версия поднята до 6.18.1 / 34, чтобы не перевыпускать занятый тег v6.18.0.

Функционально к 6.18.0 не добавлено ничего: геометрия иконок, анимации выбора и правки ревью — те же.

## Правило на будущее

В Compose половина «методов» — top-level extension-функции (`path`, `group`, `drawCircle` в
`DrawScope` — член, а `Modifier.*` — extension). Новый файл с DSL-конструктором проверяем не по
«есть ли такой метод», а по строке импорта на каждое имя, которое пишется без точки-получателя.
