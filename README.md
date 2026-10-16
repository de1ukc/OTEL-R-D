# Two FastAPI services

Проект содержит два сервиса:

- `service_a` слушает `http://127.0.0.1:8000` и вызывает `service_b`;
- `service_b` слушает `http://127.0.0.1:8001`, возвращает значение или намеренно отвечает ошибкой.

## Запуск

В отдельных терминалах:

```bash
uv run uvicorn service_b.main:app --reload --port 8001
uv run uvicorn service_a.main:app --reload --port 8000
```

URL второго сервиса можно изменить через `SECOND_SERVICE_URL`.

## Docker Compose и OpenTelemetry

Запустить оба приложения и OpenTelemetry Collector:

```bash
docker compose up --build
```

В Compose сервисы обращаются друг к другу по именам `service-a` и `service-b`.
Оба приложения автоматически отправляют OTLP-метрики, трейсы и логи в Collector.
Трейсы дополнительно попадают в Jaeger, а метрики — в Prometheus. Телеметрия
включается без изменения кода приложений: Compose запускает
`opentelemetry-instrument`, который автоматически инструментирует FastAPI,
Starlette и HTTPX, включая переход `service-a` → `service-b`. В stdout-логах
Uvicorn выводятся `trace_id` и `span_id`, поэтому `trace_id` можно использовать
как request ID для поиска связанного trace в Jaeger.

## Где смотреть telemetry

- Jaeger UI: http://127.0.0.1:16686 — полный путь запроса и длительность
  каждого span; переключатель светлой/тёмной темы включён;
- Grafana: http://127.0.0.1:3000 — метрики из автоматически настроенного
  Prometheus datasource, вход без обязательной авторизации;
- Prometheus: http://127.0.0.1:9090;
- сырой endpoint метрик Collector:
  http://127.0.0.1:8889/metrics.

Сгенерировать trace:

```bash
curl http://127.0.0.1:8000/api/aggregate
```

В Jaeger выбери сервис `service-a`, найди новый trace и раскрой spans:
`service-a` (серверный запрос) → `HTTP GET service-b:8001` (клиентский вызов)
→ `service-b` (серверный запрос). У каждого span будет собственная длительность.

Логи Collector:

```bash
docker compose logs -f otel-collector
```

Логи приложений с корреляцией:

```bash
docker compose logs -f service-a service-b
```

В строках запросов будут поля вида
`trace_id=... span_id=...`. Значение `trace_id` можно вставить в поиск Jaeger.

## Идентификатор запроса

Приложения не создают и не обрабатывают `X-Request-ID`. OpenTelemetry
автоматически создаёт и прокидывает стандартный trace context через заголовки
`traceparent`/`tracestate`; единый `trace_id` виден в Jaeger и логах обоих
сервисов. Стандартной настройки OpenTelemetry для генерации отдельного
`X-Request-ID` нет. Если нужен именно такой HTTP-заголовок без изменения
приложений, его должен добавлять внешний proxy или sidecar (например, Envoy),
а не Collector.

OTLP-порты Collector доступны на `4317` (gRPC) и `4318` (HTTP).

## Эндпоинты

| Метод и URL | Результат |
| --- | --- |
| `GET /health` | Проверка соответствующего сервиса |
| `GET http://127.0.0.1:8001/api/value` | Успешный ответ от service B |
| `GET http://127.0.0.1:8001/api/fail` | HTTP 503 от service B |
| `GET http://127.0.0.1:8000/api/aggregate` | service A вызывает service B и возвращает его данные |
| `GET http://127.0.0.1:8000/api/remote-failure` | service A вызывает ошибочный endpoint service B и передаёт HTTP 503 |
