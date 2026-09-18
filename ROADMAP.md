# RequestRider Roadmap

План розвитку RequestRider після поточного QA-релізу. Виконані етапи
знаходяться на початку документа, незавершені — нижче. Позначка `[x]`
означає функцію, яка вже доступна в поточній версії; `[ ]` — майбутню роботу.

## Виконано

### Базова архітектура та запуск

- [x] Django UI із вкладками Repeater, Intruder, Target, OSINT, Scanner,
  Comparer, Decoder, History і Traffic.
- [x] Go engine для виконання HTTP-запитів, Intruder, Target map та passive
  MITM proxy.
- [x] SQLite History для завершених Repeater та Intruder exchange.
- [x] Автоматичне застосування Django migrations під час `run-engine.sh` та
  Docker-запуску.
- [x] Docker Compose для engine і web-контейнера з опублікованими портами
  `8000`, `8080` і `8081`.
- [x] Локальний CA: автоматичне створення `data/ca/ca.crt` і
  `data/ca/ca.key`.
- [x] Логування engine та Django без запису payload, body і заголовків у
  діагностичні логи.

### Repeater, Intruder і HTTP-виконання

- [x] Повний raw HTTP editor для Repeater та Intruder.
- [x] Передавання запиту Traffic/History у Repeater та Intruder.
- [x] Для Repeater та Intruder імпорт відкриває окрему робочу вкладку.
- [x] Режими Intruder: Sniper, Battering Ram, Pitchfork і Cluster Bomb.
- [x] Маркери `§name§`, `{{name}}` і `%name%`.
- [x] Payload dictionaries і transformations.
- [x] Візуальний редактор transformations зі збереженням JSON-формату API.
- [x] Попередній перегляд payload після transformations.
- [x] Підрахунок jobs до запуску та контроль кількості workers.
- [x] Налаштовувана затримка між Intruder-запитами.
- [x] Pause/resume/cancel атаки збереженням уже отриманих результатів.
- [x] Постійний `attack_id`, polling прогресу та відновлення polling після
  перезавантаження без автоматичного скасування.
- [x] Окреме відображення completed, failed та pending jobs.
- [x] Фільтри й сортування результатів Intruder за станом, часом, розміром і
  payload.
- [x] Збереження конфігурації атаки та повторний запуск.
- [x] Експорт результатів Intruder у JSON і CSV.
- [x] Збереження Intruder results у History під час виконання атаки.
- [x] Incremental polling і worker pool для великих наборів jobs.

### Traffic, History і передавання даних

- [x] Live Traffic через SSE з pending/completed lifecycle.
- [x] Оновлення pending event відповіддю без створення дубліката.
- [x] Відновлення SSE через event cursor і replay snapshot.
- [x] Сортування Traffic за часом, host, method та URL.
- [x] Очищення Traffic через `Clear` із повним скиданням snapshot, cursor та
  browser cache.
- [x] Перегляд повного raw request/response.
- [x] Пошук History за заголовками й тілом відповіді через backend/API.
- [x] Tags і notes для History/Traffic.
- [x] Видалення вибраних History records та експорт вибраних записів.
- [x] Експорт повного HTTP exchange у JSON і файл.
- [x] Передавання request і response з History/Traffic у Comparer та Decoder.
- [x] Передавання response у Decoder відкриває нову вкладку, не перезаписуючи
  вкладку з request.
- [x] Бінарні response bodies відображаються через base64/hex із початковим
  content type.

### Target, OSINT і Scanner

- [x] Target map з асинхронним обходом, progress, cancel, pages/depth/delay
  limits і same-origin режимом.
- [x] Виявлення HTML links/forms, JS, CSS, JSON, robots.txt та sitemap.xml.
- [x] Експорт Target map у JSON, CSV, HTML і текстове дерево.
- [x] OSINT: DNS/IP, HTTP, redirects, technologies, cookies, security
  headers, discovery та пасивні WAF-сигнали.
- [x] Scanner Pro / Safe CMS Recon із bounded read-only перевірками.
- [x] Scanner findings із severity, evidence та recommendation.
- [x] Експорт Scanner у JSON і CSV.
- [x] Явне обмеження Scanner режимом без exploit, fuzzing, brute force та
  bypass.

### Comparer, Decoder і workspace

- [x] Comparer у режимах Words і Bytes із підсвічуванням відмінностей.
- [x] Decoder для URL, Base64, Base64 URL-safe, HTML, Hex, JSON і SHA-256.
- [x] Byte encode: текст у 8-бітні двійкові групи.
- [x] Byte decode: двійкові групи або десяткові значення байтів у текст.
- [x] Decoder працює в режимі однієї вибраної операції без незрозумілого
  ланцюжка.
- [x] Base64 decode розпізнає службовий префікс бінарного response:
  `[binary content/type; base64]`.
- [x] Browser-like workspaces для Repeater, Intruder, Target, OSINT, Scanner,
  Comparer і Decoder.
- [x] Створення, перейменування, закриття та відновлення вкладок.
- [x] Автозбереження workspace, Save session, Export/Import session JSON.
- [x] Payload generators: числа, діапазони, UUID, дати, списки слів і
  шаблони.

### Тести та документація

- [x] Smoke script для health, Repeater, Intruder, History і SSE.
- [x] README з локальним і Docker Compose запуском, proxy, CA та очищенням
  контейнерів.
- [x] Документ `BUG_BOUNTY_AND_DEVELOPERS.md` для bug reports, пропозицій і
  участі в розробці.

## Не виконано

### Надійність і покриття тестами

- [ ] Додати тести для помилок engine, malformed transformations, порожніх
  словників і граничних випадків byte/base64 workflow.
- [ ] Додати структуровані log fields для машинного аналізу.
- [ ] Додати CI для Go tests, Django tests, JavaScript syntax checks та
  міграцій.
- [ ] Додати Playwright smoke-тести навігації, Decoder, workspace tabs і
  passive Scanner.
- [ ] Додати Selenium smoke-тест базового Python-оточення.
- [ ] Відокремити локальні generated files (`db.sqlite3`, `__pycache__`,
  logs) від початкових змін перед коммітом.
- [ ] Розширити E2E-набір стабільним локальним test server.

### Traffic і History

- [ ] Додати збереження Traffic snapshot між перезапусками engine.
- [ ] Додати імпорт окремого Traffic JSON.
- [ ] Додати повторне надсилання запису однією кнопкою з новим результатом
  поруч зі старим.
- [ ] Перенести довгоживучий Traffic cache з `localStorage` до IndexedDB.
- [ ] Додати віртуалізований список Traffic для десятків тисяч подій.
- [ ] Додати режими `Live`, `Paused` і `Buffered`.
- [ ] Додати фільтри Traffic за host, method, status, URL, розміром, часом і
  джерелом.
- [ ] Додати видимий ліміт пам'яті та повідомлення про видалення найстаріших
  подій.
- [ ] Додати targeted stress tests для 1k/10k/50k подій і body cache.

### Intruder

- [ ] Додати пресети transformations.
- [ ] Додати перевірку відповідності кількості markers і словників.
- [ ] Додати імпорт словників із кількох файлів і збереження набору
  словників у JSON.
- [ ] Додати повторний запуск тієї самої атаки безпосередньо з History.
- [ ] Додати профілі `Discovery`, `Parameter testing`, `Headers` та
  `Rate-limited audit`.
- [ ] Додати видимі RPS limit, concurrency, timeout, retry policy та circuit
  breaker.
- [ ] Додати оцінку навантаження до старту: jobs, concurrency і очікуваний
  обсяг трафіку.
- [ ] Автоматично зупиняти атаку при серії `429`, `503`, timeout або ознаках
  деградації target.
- [ ] Додати явне destructive/local-lab confirmation для небезпечних
  сценаріїв.

### Browser-driven Target

- [ ] Додати окремий Chromium/Playwright worker для виконання JavaScript.
- [ ] Додати безпечне заповнення й надсилання форм із явним режимом запуску.
- [ ] Збирати DOM-маршрути, що з'являються після дій користувача та виконання
  JavaScript.

### TOR і проксі-профілі

- [ ] Додати профілі вихідного з'єднання: пряме підключення, HTTP proxy,
  HTTPS proxy та SOCKS5.
- [ ] Додати окремий режим маршрутизації через локальний TOR SOCKS5 endpoint
  із явним налаштуванням host і port.
- [ ] Додати вибір proxy-профілю для Repeater, Intruder, Target, OSINT,
  Scanner, workflow runner та browser-driven worker.
- [ ] Додати перевірку активного маршруту, proxy/TOR connectivity та видимий
  health status без розкриття секретів у логах.
- [ ] Додати налаштування DNS resolution, proxy bypass для локальних адрес і
  окремі правила для HTTP та HTTPS.
- [ ] Додати import/export proxy profiles без збереження паролів і ключів у
  незашифрованому вигляді.
- [ ] Додати інтеграційні тести з локальними HTTP proxy, SOCKS5 fixture та
  mock TOR endpoint; не вважати доступ до публічної TOR-мережі обов'язковим
  для CI.
- [ ] Додати попередження про зміну source IP, latency, нестабільність
  ланцюжка та можливе витікання DNS до запуску довгих операцій.

### AI та автономний агент

- [x] Додати компактну AI-вкладку з conversational chat.
- [x] Додати явне прикріплення Repeater, Intruder, Target Map, OSINT, Scanner,
  History і Traffic evidence.
- [x] Додати provider adapters для Ollama та OpenAI-compatible providers.
- [x] Ізолювати AI chat від tool execution, shell, filesystem і arbitrary HTTP.
- [x] Передавати provider-у лише evidence після явного натискання кнопки.
- [x] Залишити scope, execution profile, budget, rate-limit, concurrency та
  audit checks активних інструментів.
- [x] Додати SPA fallback fingerprints і black-box observable-change
  verification.
- [ ] Додати preview прикріплених даних і експорт conversation.
- [ ] Додати provider latency/context-size status і streaming.
- [ ] Додати contract fixtures для великих binary та SPA responses.
- [ ] Додати негативні тести на prompt injection із HTTP body, headers,
  HTML, JavaScript, History, Traffic та зовнішніх відповідей.

### Project Workspace

- [ ] Ввести модель `Project` із target scope, environment, вкладками,
  Traffic filters, notes, tags, findings та історією запусків.
- [ ] Додати `New Project`, `Open Project`, `Save Project` і `Close Project`.
- [ ] Додати версії snapshot, автозбереження та відновлення після аварійного
  перезавантаження.
- [ ] Додати попередження про незбережені зміни.
- [ ] Додати експорт/імпорт project JSON із перевіркою формату.
- [ ] Підтримати окремі проєкти для різних локальних стендів і профілів.
- [ ] Не зберігати cookies, Authorization, JWT, CA-ключі та інші секрети без
  явного маскування.

### Findings Center і звіти

- [ ] Створити єдину модель finding із source, target, endpoint, severity,
  confidence, evidence, recommendation та timestamps.
- [ ] Додати стани `New`, `Confirmed`, `False positive`, `Accepted risk` і
  `Fixed`.
- [ ] Додати Findings-вкладку з пошуком, фільтрами та групуванням.
- [ ] Додати дії `Send to Repeater`, `Send to Comparer` і повторну перевірку
  конкретного finding.
- [ ] Показувати heuristic CMS/WAF результати як `Unconfirmed` із confidence.
- [ ] Додати diff результатів між двома Scanner runs.
- [ ] Додати експорт звітів у JSON, CSV, Markdown та HTML із evidence.
- [ ] Додати маскування секретів у findings та експортованих звітах.

### Scanner Pro

- [ ] Розділити профілі `Generic Web`, `CMS`, `API` та `Security Headers`.
- [ ] Додати confidence score і evidence для кожної перевірки.
- [ ] Додати повторний запуск одного finding без повного сканування.
- [ ] Додати порівняння `baseline` і `current` scan.
- [ ] Додати видимий scope та режим `LOCAL LAB` перед запуском.
- [ ] Додати bounded concurrency, timeout, rate limit і cancel для Scanner.
- [ ] Додати regression fixtures для generic local HTTP server.

### Workflows і collections

- [ ] Додати collections запитів із групами та описами.
- [ ] Додати workflow steps: request, delay, condition, extract, assertion і
  export.
- [ ] Додати environment variables та підстановку token, cookie, CSRF і
  response fields.
- [ ] Додати pause/resume/cancel і детальний журнал кожного step.
- [ ] Додати умови за HTTP status, header, JSON path та latency.
- [ ] Додати налаштовувані defaults і rate limit для workflow runner.
- [ ] Додати локальні fixtures: login → discover → scan → findings → report.

### UX та операційна безпека

- [ ] Додати глобальну target bar з target, scope, режимом і health status.
- [ ] Показувати `TARGET`, `MODE` та `AUTHORIZED` у серійних операціях.
- [ ] Додати health indicators для Django, Go engine, proxy та target.
- [ ] Додати глобальні дії `Pause jobs`, `Cancel jobs` і
  `Clear volatile data`.
- [ ] Додати context actions `Send to Repeater`, `Add to Intruder`,
  `Add to Scanner` та `Compare`.
- [ ] Додати генерацію curl, fetch і Python для вибраного HTTP exchange.
- [ ] Додати split-view request/response, sticky headers та hotkeys.
- [ ] Додати audit log для запусків, destructive confirmations та exports.
- [ ] Додати видимий профіль `Local Lab` без прихованого allowlist, SSRF
  блокування або автоматичної заборони зовнішніх цілей.
- [ ] Маскувати cookies, JWT, Authorization та API keys у Traffic, History і
  exports за замовчуванням.

## Поточні обмеження

- Traffic Store engine залишається in-memory і очищається після restart або
  через `Clear`.
- Target є статичним HTTP crawler: JavaScript не виконується, форми не
  надсилаються, DOM-маршрути після browser actions не збираються.
- Decoder виконує одну вибрану операцію за раз; для бінарних тіл потрібен
  окремий base64/hex або file-preview workflow.
- Повноцінний Burp-подібний Intercept навмисно не планується: події доступні
  у Traffic і можуть передаватися в Repeater або Intruder.

## Правила пріоритизації

1. Спочатку виправляти втрату або спотворення HTTP-даних і стабільність
   Traffic.
2. Потім забезпечити project/session recovery та відтворюваність запусків.
3. Потім об'єднати findings і покращити точність Scanner.
4. Потім додавати workflows, Intruder safety та browser-driven automation.
5. Proxy/TOR routing спочатку реалізовувати як явні профілі з локальними
   fixtures і health checks, а не як приховану зміну маршруту.
6. AI вкладку та автономного агента запускати після типізованого tool API,
   policy checks, audit log і відтворюваних provider contract tests.
7. Лише після цього розширювати UI навколо вже працюючих API.
8. Для кожної зміни додавати targeted test або відтворюваний smoke-сценарій.
9. Не додавати приховані policy/resource restrictions: SSRF, host, network,
   allowlist або scope блокування замість явного контролю користувача.
