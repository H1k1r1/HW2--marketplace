# Проектирование OpenAPI + CRUD

## Структура 
```
marketplace/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── api/
│   │   ├── auth.py
│   │   ├── products.py
│   │   ├── orders.py
│   │   └── promo_codes.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── product_service.py
│   │   └── order_service.py
│   ├── core/
│   │   ├── security.py
│   │   ├── logging_middleware.py
│   │   └── exceptions.py
│   └── migrations/
│       ├── V1__initial_schema.sql
│       └── V2__add_promo_code_validation.sql
├── docker-compose.yml
├── Dockerfile
├── openapi.yaml
├── requirements.txt
├── run.md
├── .env
└── .gitignore
```

## Swagger UI 
<img width="1260" height="1212" alt="image" src="https://github.com/user-attachments/assets/4828fdea-f47f-405c-89c6-083ae3a2a0b1" />
<img width="1137" height="1131" alt="image" src="https://github.com/user-attachments/assets/618db3b7-fd48-45cd-bb81-e24a56454d00" />

