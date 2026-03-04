# Скачиваем папку либо zip либо git clone

# Запуск

```bash
docker-compose up --build

Лучше сделать сразу очистку(могли остаться данные) и запустить снова
```

# Теперь заходим в Swagger UI 

```
http://localhost:8000/docs#/ - все тесты там
```

# Перезапуск
```bash
docker-compose restart api - Перезапустить только API

docker-compose restart - перезапустить все
```

# Остановка

```bash
docker-compose down - обычная

docker-compose down -v - полная очистка
```

# Логи
```bash
docker-compose logs -f api - realtime

docker-compose logs -f db - бд

docker-compose logs api --tail=50 - проверка последних 50 строк
```

# БД
```bash
docker-compose exec db psql -U user -d marketplace - подключение к бд

docker-compose run --rm flyway migrate - ручная миграция
```
SQL запрос:

```bash
\dt - все таблицы

\d products - структура таблицы

SELECT id, name, price, stock, status FROM products; - просмотр товаров

SELECT id, user_id, status, total_amount FROM orders; - просмотр заказов

SELECT code, discount_value, current_uses, max_uses FROM promo_codes; - просмотр промокодов

\q - выход
```

# Если не запускается

## Проверить статус контейнеров
```bash
docker-compose ps
```
## Посмотреть логи ошибки
```bash
docker-compose logs api | tail -50
```
## Пересобрать образ
```bash
docker-compose build --no-cache
docker-compose up -d
```
