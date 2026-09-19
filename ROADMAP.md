# Roadmap RequestRider

Цей файл містить лише актуальні майбутні роботи. Поточні можливості, запуск,
архітектура, Tor/SOCKS5 і діагностика описані в [`README.md`](README.md).
Реалізовані функції не дублюються тут як повний каталог.

## Поточний стан

- [x] Django UI, Go engine, SQLite History і passive MITM.
- [x] Repeater, Intruder, Target, OSINT, Scanner, Comparer і Decoder.
- [x] Live Traffic через SSE та History збереження.
- [x] Direct або явний SOCKS5-маршрут для всіх outbound-інструментів.
- [x] Docker Compose із сервісами `web`, `engine` і `tor`.
- [x] Route check із latency, HTTP status і зовнішньою IP-адресою.
- [x] AI chat із явним прикріпленням evidence без автономного виконання дій.
- [x] Українська та англійська локалізація основного UI.

## Пріоритет 1 — надійність

- [ ] Додати CI для Go tests, Django tests, migrations і JavaScript syntax.
- [ ] Додати локальний deterministic HTTP test server для E2E.
- [ ] Додати Playwright smoke-тести вкладок, локалізації, Decoder, Traffic SSE
  і Scanner.
- [ ] Покрити malformed payloads, binary responses, порожні dictionaries,
  timeout і помилки route.
- [ ] Додати тести для всіх evidence attachment actions.

## Пріоритет 2 — Traffic і History

- [ ] Додати UI для Traffic sessions і відновлення bundle.
- [ ] Перенести великий browser cache з `localStorage` до IndexedDB.
- [ ] Додати віртуалізацію Traffic для великих snapshot.
- [ ] Додати фільтри за source, status, host, method, URL і часом.
- [ ] Додати контрольований memory limit і stress tests.

## Пріоритет 3 — Intruder і Scanner

- [ ] Додати перевірку відповідності markers і dictionaries.
- [ ] Додати імпорт dictionaries із файлів і збережені набори.
- [ ] Додати видимі timeout, RPS, concurrency, retry policy та circuit breaker.
- [ ] Показувати оцінку jobs і очікуваного навантаження до старту.
- [ ] Автоматично призупиняти operation після серії `429`, `503` або timeout.
- [ ] Додати Scanner profiles `Generic Web`, `CMS`, `API` і `Security Headers`.
- [ ] Додати confidence score та повторну перевірку finding.

## Пріоритет 4 — Findings і Projects

- [ ] Ввести Project із target scope, environment, notes, tags і snapshots.
- [ ] Створити єдину Findings-модель із severity, confidence, evidence,
  recommendation і timestamps.
- [ ] Додати стани `New`, `Confirmed`, `False positive`, `Accepted risk`,
  `Fixed`.
- [ ] Додати Findings Center та експорт у JSON, CSV, Markdown і HTML.
- [ ] Додати маскування cookies, JWT, Authorization і API keys за замовчуванням.

## Пріоритет 5 — browser-driven Target

- [ ] Додати окремий Chromium/Playwright worker.
- [ ] Збирати маршрути, які з’являються після JavaScript і browser actions.
- [ ] Додати явний безпечний режим форм із локальними fixtures.
- [ ] Не змішувати browser-driven worker зі статичним crawler без окремого
  контролю scope і тестового середовища.

## Пріоритет 6 — proxy та AI

- [ ] Додати локальний route override для окремої вкладки/операції.
- [ ] Додати HTTP proxy і HTTPS proxy profiles.
- [ ] Додати import/export proxy profiles без відкритого збереження секретів.
- [ ] Додати provider latency, retry, context-size status і streaming для AI.
- [ ] Додати export conversation разом із прикріпленими evidence.
- [ ] Додати негативні тести на prompt injection у headers, body, HTML і
  зовнішніх відповідях.

## Не планується без окремого обґрунтування

- автономні observe → plan → execute цикли;
- shell, arbitrary filesystem або arbitrary HTTP для AI;
- приховане автоматичне передавання всього workspace;
- приховані SSRF/host/scope-обмеження замість явного контролю оператора;
- повний Intercept, якщо він лише дублює live Traffic.

## Правила пріоритизації

1. Не втрачати й не спотворювати HTTP-дані.
2. Перед розширенням автоматизації додавати safety controls.
3. Кожну зміну покривати targeted test або відтворюваним smoke-сценарієм.
4. Зберігати loopback defaults і явність proxy-маршруту.
5. Не послаблювати ізоляцію AI від виконання дій.
