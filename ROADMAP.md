# Roadmap RequestRider

Цей документ описує фактичний стан RequestRider і порядок подальшої
розробки. Позначка `[x]` означає функцію, доступну в поточній версії; `[ ]` —
майбутню роботу.

## Поточний реліз

RequestRider уже має робочий локальний QA-процес:

```text
Browser :8000
    -> Django web gateway + SQLite History
    -> Go engine :8081
         -> outbound HTTP execution
         -> Intruder generation/execution
         -> Target site-map crawler
         -> passive MITM proxy :8080
```

Поточний AI — це ізольований conversational chat для аналізу явно прикріплених
оператором evidence. Він не є автономним агентом і не запускає дії
RequestRider.

## Реалізовано

### Архітектура, запуск і дані

- [x] Django UI із вкладками Repeater, Intruder, Target, OSINT, Scanner,
  Comparer, Decoder, History, Traffic і AI.
- [x] Go engine для HTTP-виконання, Intruder, Target map та passive MITM proxy.
- [x] SQLite History для Repeater, Intruder і збережених proxy exchange.
- [x] `run-engine.sh` із перевіркою health, автоматичним запуском engine,
  Python virtualenv і Django migrations.
- [x] Docker Compose для engine і web із loopback-портами `8000`, `8080`,
  `8081`.
- [x] Автоматичне створення локального CA у `data/ca/ca.crt` і
  `data/ca/ca.key`.
- [x] Логування без запису payload, body та заголовків до діагностичних логів.

### Repeater та Intruder

- [x] Єдиний raw HTTP editor для Repeater і Intruder.
- [x] Передавання запитів із Traffic/History до Repeater та Intruder.
- [x] Маркери `§name§`, `{{name}}` і `%name%`.
- [x] Режими Sniper, Battering Ram, Pitchfork і Cluster Bomb.
- [x] Dictionaries, transformations, preview transformed payloads і
  попередній підрахунок jobs.
- [x] Bounded worker pool, incremental polling, `since`, `limit` і
  `result_offset`.
- [x] Pause/resume/cancel зі збереженням уже отриманих результатів.
- [x] Відновлення polling після перезавантаження сторінки без автоматичного
  скасування атаки.
- [x] Фільтрація, сортування, повні request/response inspectors і експорт
  Intruder у JSON/CSV.
- [x] Збереження конфігурацій Intruder і повторний запуск.
- [x] Збереження HTTP-результатів Intruder у History під час виконання.

### Traffic і History

- [x] Live Traffic через SSE з lifecycle `pending` → `completed`.
- [x] Оновлення pending event без створення дубліката.
- [x] SSE reconnect через event cursor і replay backlog.
- [x] Сортування Traffic за часом, host, method і URL.
- [x] Повний raw request/response, binary body у base64/hex із content type.
- [x] Tags і notes для History/Traffic.
- [x] Вибіркове та масове видалення History.
- [x] Експорт та імпорт History JSON.
- [x] Збереження окремого Traffic exchange через **Save row**.
- [x] Збереження, перелік, перегляд та імпорт Traffic sessions як JSON bundle
  через backend API.
- [x] Передавання request/response із History та Traffic у Comparer і Decoder.

### Target, OSINT і Scanner

- [x] Асинхронний Target map з progress, cancel, `max_pages`, `max_depth`,
  `delay_ms` і `same_origin`.
- [x] Виявлення HTML links/forms, JS/CSS/JSON URLs, `robots.txt`,
  `sitemap.xml`, `Sitemap:` і XML `<loc>`.
- [x] Експорт Target map у JSON, CSV, HTML і текстове дерево.
- [x] OSINT: DNS/IP, MX/NS/TXT, HTTP metadata, redirects, technologies,
  cookies, security headers, discovery і пасивні WAF-сигнали.
- [x] Scanner Pro / Safe CMS Recon із bounded read-only перевірками.
- [x] Scanner findings із severity, evidence і recommendation.
- [x] Експорт Scanner у JSON/CSV та обмеження без exploit, fuzzing, brute
  force й access-control bypass.

### Decoder, Comparer і workspace

- [x] Comparer у режимах Words і Bytes.
- [x] Decoder для URL, Base64, Base64 URL-safe, HTML, Hex, byte
  encode/decode, JSON і SHA-256.
- [x] Browser-like workspaces для основних інструментів.
- [x] Створення, перейменування, закриття та відновлення вкладок.
- [x] Автозбереження workspace, Save session, Export/Import session JSON.
- [x] Payload generators: числа, діапазони, UUID, дати, списки слів і
  шаблони.

### AI chat

- [x] Conversational AI-вкладка з явним прикріпленням Repeater, Intruder,
  Target Map, OSINT, Scanner, History і Traffic evidence.
- [x] Provider adapters для Ollama, OpenAI, Anthropic, OpenRouter, Gemini,
  Groq, Mistral і custom OpenAI-compatible endpoint.
- [x] Введення API key у UI або через змінні середовища.
- [x] Компактний context без автоматичного завантаження всього workspace.
- [x] Ізоляція від tools, shell, filesystem, History API, Traffic API та
  arbitrary HTTP.
- [x] SPA fallback fingerprinting і black-box observable-change verification.

### Перевірка та документація

- [x] Go tests, Django checks/tests і smoke script для основних сервісів.
- [x] Перевірка inline JavaScript через `node --check`.
- [x] README з локальним запуском, Docker Compose, CA, passive proxy та
  налаштуванням AI-токена.
- [x] Документація `AGENTS.md`, `AGENT_RUNTIME.md` та
  `AGENT_USER_GUIDE.md`.

## Поточні обмеження

- [ ] Traffic Store engine залишається in-memory: незбережені live events
  зникають після перезапуску engine або `Clear`.
- [ ] Target є статичним HTTP crawler: JavaScript не виконується, форми не
  надсилаються, DOM-маршрути після browser actions не збираються.
- [ ] Немає окремої моделі Project: поточний workspace зберігається локально
  у browser storage та session JSON.
- [ ] Findings Scanner ще не об'єднані в єдиний Findings Center.
- [ ] AI не підтримує streaming, export conversation і видимий provider
  latency/context-size status.
- [ ] Повноцінний Burp-подібний Intercept навмисно відсутній: події доступні
  у Traffic і можуть передаватися в інші вкладки.

## Наступні етапи

Порядок визначено за впливом на надійність, відтворюваність і безпеку
авторизованого тестування.

### Етап 1. Надійність і регресійне покриття

- [ ] Додати CI для Go tests, Django tests, migrations і JavaScript syntax.
- [ ] Додати локальний deterministic test server для E2E та smoke-тестів.
- [ ] Покрити malformed transformations, порожні dictionaries, byte/base64,
  binary responses і помилки engine.
- [ ] Додати regression-тести для всіх UI-кнопок evidence attachment.
- [ ] Додати Playwright smoke-тести навігації, workspace tabs, Decoder,
  Traffic SSE та Scanner.
- [ ] Додати структуровані log fields для машинного аналізу без секретів.

### Етап 2. Traffic, History і відтворюваність

- [ ] Додати UI для збереження та відновлення Traffic sessions.
- [ ] Додати повторне надсилання History/Traffic exchange однією кнопкою з
  новим результатом поруч зі старим.
- [ ] Перенести великий локальний cache із `localStorage` до IndexedDB.
- [ ] Додати віртуалізований список Traffic для десятків тисяч подій.
- [ ] Додати режими `Live`, `Paused` і `Buffered`.
- [ ] Додати фільтри Traffic за host, method, status, URL, розміром, часом і
  джерелом.
- [ ] Додати контрольований memory limit і regression stress tests для
  1k/10k/50k events.

### Етап 3. Intruder і Scanner safety

- [ ] Додати перевірку відповідності кількості markers і dictionaries.
- [ ] Додати імпорт dictionaries із файлів та збереження наборів у JSON.
- [ ] Додати видимі RPS limit, concurrency, timeout, retry policy і circuit
  breaker.
- [ ] Додати оцінку навантаження до старту: jobs, concurrency та очікуваний
  обсяг трафіку.
- [ ] Автоматично призупиняти операцію після серії `429`, `503`, timeout або
  ознак деградації target.
- [ ] Додати Scanner-профілі `Generic Web`, `CMS`, `API` та
  `Security Headers`.
- [ ] Додати confidence score, baseline/current diff і повторну перевірку
  окремого Scanner finding.

### Етап 4. Project Workspace і Findings Center

- [ ] Ввести модель `Project` із target scope, environment, вкладками,
  Traffic sessions, notes, tags, findings і журналом запусків.
- [ ] Додати `New Project`, `Open Project`, `Save Project`, `Close Project`,
  snapshot versions та відновлення після аварійного перезавантаження.
- [ ] Додати єдину модель finding із source, target, endpoint, severity,
  confidence, evidence, recommendation і timestamps.
- [ ] Додати стани `New`, `Confirmed`, `False positive`, `Accepted risk` і
  `Fixed`.
- [ ] Додати Findings-вкладку з пошуком, фільтрами, групуванням і діями
  `Send to Repeater`, `Send to Comparer` та повторною перевіркою.
- [ ] Додати експорт findings у JSON, CSV, Markdown і HTML.
- [ ] Додати маскування cookies, JWT, Authorization та API keys у findings і
  експорті за замовчуванням.

### Етап 5. Browser-driven Target

- [ ] Додати окремий Chromium/Playwright worker для виконання JavaScript.
- [ ] Додати явний режим безпечного заповнення та надсилання форм.
- [ ] Збирати DOM-маршрути, що з'являються після дій користувача і виконання
  JavaScript.
- [ ] Ізолювати browser-driven worker від статичного Target crawler і
  покривати його локальними fixtures.

### Етап 6. Явні proxy-профілі

- [x] Додати профілі direct, SOCKS5 і TOR як SOCKS5-профіль.
- [x] Додати єдиний глобальний маршрут для Repeater, Intruder, Target, OSINT,
  Scanner і upstream passive MITM.
- [x] Додати UI-перемикач маршруту з адресою SOCKS5 і явним Apply route.
- [x] Додати Docker Compose Tor container із upstream `tor:9050`.
- [ ] Додати health check маршруту, DNS policy, proxy bypass для локальних
  адрес і видимий статус source IP/latency.
- [ ] Додати локальний override маршруту для окремої вкладки або операції.
- [ ] Додати профілі HTTP proxy та HTTPS proxy.
- [ ] Додати import/export proxy profiles без збереження паролів і ключів у
  незашифрованому вигляді.
- [ ] Покрити профілі локальними HTTP proxy/SOCKS5 fixtures; доступ до
  публічної TOR-мережі не повинен бути вимогою CI.

### Етап 7. AI chat без автономного виконання

- [ ] Додати preview прикріплених даних перед відправленням.
- [ ] Додати export conversation разом із прикріпленими evidence.
- [ ] Додати provider latency, retry і context-size status.
- [ ] Додати streaming для провайдерів, які його підтримують.
- [ ] Додати contract fixtures для великих binary та SPA responses.
- [ ] Додати негативні тести на prompt injection у HTTP body, headers, HTML,
  JavaScript, History, Traffic та зовнішніх відповідях.

## Не планується без окремого обґрунтування

- autonomous observe → plan → execute loops;
- durable background missions і довгоживуче сховище lifecycle events для AI;
- shell, arbitrary filesystem, arbitrary HTTP або post-compromise execution;
- автоматичне передавання всього workspace кожним повідомленням;
- приховане masking/redaction context;
- приховані SSRF, host, network, allowlist або scope-блокування замість
  явного контролю користувача;
- повноцінний Intercept, якщо він дублює live Traffic без чіткої користі.

## Правила пріоритизації

1. Не втрачати та не спотворювати HTTP-дані.
2. Забезпечити відтворюваність через тести, Traffic sessions і Project
   Workspace.
3. Додати safety controls для Intruder і Scanner до розширення автоматизації.
4. Об'єднати результати в Findings Center.
5. Додати browser-driven Target лише окремим worker із локальними fixtures.
6. Реалізовувати proxy/TOR як явні профілі з health checks, а не як приховану
   зміну маршруту.
7. Розширювати AI chat лише через provider contract tests і збереження
   ізоляції від виконання дій.
8. Для кожної зміни додавати targeted test або відтворюваний smoke-сценарій.
