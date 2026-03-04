build:
	docker-compose build --no-cache

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f api


migrate:
	docker-compose run --rm flyway migrate

clean:
	docker-compose down -v
	docker-compose build --no-cache
	docker-compose up -d

shell:
	docker-compose exec api /bin/bash

db:
	docker-compose exec db psql -U user -d marketplace