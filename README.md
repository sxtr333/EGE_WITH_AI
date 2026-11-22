# ЕГЭ-навигатор формул

Справочник формул по подтипам Решу ЕГЭ.  
Формулы берутся **из реальных решений**, а не из «типичных списков» в интернете.

## Как пользоваться

1. Открыл задачу на Решу ЕГЭ → понял подтип  
2. Открыл карточку в `cards/`  
3. Нашёл нужный блок формул → решил

## Готово

- [x] №1 · Решение прямоугольного треугольника → `cards/01-pryamougolnyy-treugolnik.md`

## Как качать следующий подтип

```bash
.venv/bin/python scripts/fetch_category.py 80 --name ravnobedrennyy
```

Потом по файлу `data/*_for_analysis.txt` собираем карточку в `cards/`.

## Источник

https://math-ege.sdamgia.ru/prob_catalog  
Печатная выгрузка категории: `/test?filter=all&category_id=ID&print=true`
