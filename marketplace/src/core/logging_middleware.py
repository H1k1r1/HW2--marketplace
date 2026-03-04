# src/core/logging_middleware.py
import time
import json
import uuid
import logging
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger("api_access")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для логирования API-запросов в JSON-формате"""
    
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint
    ) -> Response:
        # Генерация request_id
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Извлечение user_id (если есть)
        user_id: Optional[str] = None
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            # В реальном проекте здесь был бы разбор JWT
            # Для демо берём из state, если установлено
            user_id = getattr(request.state, "user_id", None)
        
        start_time = time.time()
        
        # Выполнение запроса
        response = await call_next(request)
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Формирование лога
        log_entry = {
            "request_id": request_id,
            "method": request.method,
            "endpoint": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "user_id": user_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
        # Логирование body для мутационных запросов
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            # Внимание: чтение body в middleware требует special handling
            # Для простоты здесь только метаданные
            log_entry["has_body"] = True
        
        # Запись в лог
        logger.info(json.dumps(log_entry, ensure_ascii=False))
        
        # Добавление request_id в ответ
        response.headers["X-Request-Id"] = request_id
        
        return response