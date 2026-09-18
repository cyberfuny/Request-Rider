<img width="2912" height="1440" alt="Gemini_Generated_Image_am0pnwam0pnwam0p (1)" src="https://github.com/user-attachments/assets/d24a8205-5324-4a97-8754-17dc437acb55" />

<img width="1141" height="356" alt="Screenshot 2026-09-18 at 11-53-24 Screenshot_2026-09-18_11-48-37 png (PNG Image 1366 × 733 pixels) — Scaled (84_)" src="https://github.com/user-attachments/assets/e2dfb7f5-18b1-41d5-acd1-83fad058a846" />

# RequestRider

Локальний браузерний QA-інструмент для ручного аналізу, повторного
надсилання та безпечного дослідження HTTP-трафіку. Проєкт поєднує Django UI,
Go engine, SQLite History і локальний passive MITM proxy.

> **Важливо:** RequestRider призначений для власних або явно дозволених
> цілей. Intruder, Target, OSINT і Scanner Pro не замінюють дозвіл на
> тестування. Не використовуйте інструмент для обходу доступу, brute force,
> експлуатації або тестування чужих систем.

## Що вже працює

- **Repeater** — редагування повного raw HTTP-запиту та повторне надсилання.
- **Intruder** — Sniper, Battering Ram, Pitchfork і Cluster Bomb,
  dictionaries, transformations, worker pool, pause/resume/cancel, polling і
  експорт результатів.
- **Target** — асинхронна карта сайту з обмеженнями pages/depth/delay,
  same-origin режимом, cancel, фільтрами, сортуванням і JSON/CSV/HTML/tree
  експортом.
- **OSINT** — DNS/IP, HTTP, redirects, technologies, cookies, security
  headers, discovery і пасивні WAF-сигнали.
- **Scanner Pro / Safe CMS Recon** — bounded read-only перевірки авторизованої
  цілі: CMS/public paths, admin/API endpoints, backup/debug/configuration
  exposure, TLS, cookies, HTTP methods, headers і WAF. Findings мають
  severity `INFO / LOW / MEDIUM / HIGH`, evidence та recommendation.
- **Traffic** — live-потік passive proxy, Repeater і Intruder через SSE.
  Pending-запит згодом оновлюється відповіддю без створення дубліката.
- **History** — SQLite-сховище завершених Repeater/Intruder exchange з
  пошуком, tags/notes, переглядом повного запиту/відповіді та експортом.
- **Comparer** — порівняння двох запитів або відповідей у режимах Words і
  Bytes.
- **Decoder** — URL, Base64, Base64 URL-safe, HTML entities, Hex, byte
  decoding, JSON
  і SHA-256 у режимі однієї вибраної операції.
- **Browser-like workspaces** — окремі вкладки для Repeater, Intruder,
  Target, OSINT, Scanner, Comparer і Decoder.
- **Project Workspace** — автозбереження вкладок і стану, явний Save session,
  Export/Import session JSON, відновлення після reload.
- **Target Map preview** — дерево папок із кнопками `Collapse all` і
  `Expand all`.
- **Локальний CA** — engine автоматично створює `data/ca/ca.crt` і
  `data/ca/ca.key` для passive HTTPS proxy.

Поки що RequestRider використовує пряме вихідне з'єднання для активних
запитів, а passive proxy працює на локальному `127.0.0.1:8080`. AI-вкладка є
компактним conversational chat: оператор вручну прикріплює Repeater, Intruder,
Target Map, OSINT, Scanner, History або Traffic і просить LLM проаналізувати
лише ці дані. Поточний AI API та правила описані в
[`AGENT_RUNTIME.md`](AGENT_RUNTIME.md), [`AGENT_USER_GUIDE.md`](AGENT_USER_GUIDE.md)
і [`LLM_ROADMAP.md`](LLM_ROADMAP.md).

## Найшвидший запуск

Потрібні:

- Go;
- Python 3;
- `curl`;
- `virtualenv` або доступний Python `venv` для автоматичного створення;
  `web/.venv`;

Із кореня репозиторію:

```bash
./run-engine.sh
```

Скрипт:

1. перевіряє Go engine на `http://127.0.0.1:8081/health`;
2. запускає engine, якщо він ще не працює;
3. створює або відновлює `web/.venv`;
4. встановлює Django-залежності з `web/requirements.txt`;
5. застосовує Django-міграції до локальної SQLite-бази;
6. запускає Django UI на `http://127.0.0.1:8000`.

Після запуску відкрийте:

- UI: <http://127.0.0.1:8000>;
- engine health: <http://127.0.0.1:8081/health>;
- passive proxy: `127.0.0.1:8080`.

Зупинка foreground-процесу `run-engine.sh` завершує запущений ним engine.

За замовчуванням усі локальні сервіси використовують loopback-адреси. Не
змінюйте listen address на зовнішній інтерфейс без розуміння ризиків: UI,
engine і CA proxy можуть обробляти повні HTTP-запити, заголовки, cookies та
тіла.

## Зворотний зв’язок і внесок у проєкт

Повідомлення про помилки, пропозиції та запити щодо участі у розробці
надсилайте на <cyberfuny@proton.me>. Детальні рекомендації наведені у
файлі [`BUG_BOUNTY_AND_DEVELOPERS.md`](BUG_BOUNTY_AND_DEVELOPERS.md).
Якщо engine уже працював до запуску скрипта, він не дублюється і не
зупиняється скриптом.

Для нестандартного CA або адреси engine:

```bash
CA_DIR=/path/to/ca ./run-engine.sh
ENGINE_URL=http://127.0.0.1:8081 ./run-engine.sh
```

### Ручний запуск

Якщо потрібно запускати сервіси окремо:

```bash
cd engine
go run .
```

В іншому терміналі:

```bash
cd web
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
ENGINE_URL=http://127.0.0.1:8081 python manage.py runserver 127.0.0.1:8000
```

Для Kali/Debian, де системний `venv` може не містити `pip`, використовуйте
`virtualenv` або запускайте рекомендований `./run-engine.sh`.

### Docker Compose

Docker-профіль запускає engine і Django UI у двох контейнерах. Не запускайте
одночасно Docker і `./run-engine.sh`, оскільки вони використовують порти
`8000`, `8080` і `8081`.

Для Docker Compose v2:

```bash
docker compose up --build
```

Для Kali/Debian з окремою командою Compose:

```bash
docker-compose up --build
```

Docker-адреси:

- UI: <http://localhost:8000>;
- engine health: <http://127.0.0.1:8081/health>;
- proxy: `127.0.0.1:8080`.

Після запуску перевірте сервіси:

```bash
docker-compose ps
curl http://127.0.0.1:8081/health
curl -I http://127.0.0.1:8000/
```

Для passive proxy налаштуйте браузер або інший дозволений QA-інструмент на
HTTP proxy `127.0.0.1:8080`. Для HTTPS імпортуйте сертифікат
`data/ca/ca.crt` у довірене сховище клієнта. Файл `data/ca/ca.key` є
приватним ключем і не повинен публікуватися або передаватися іншим людям.
Після відкриття дозволеної цілі події можна переглядати у вкладці **Traffic**
за адресою <http://127.0.0.1:8000>.

Docker Compose не додає автоматично TOR або зовнішній proxy-маршрут. Для
таких сценаріїв потрібні окремі майбутні proxy-профілі з явним health check,
налаштуванням DNS і правилами обходу локальних адрес; не покладайтеся на
випадкові змінні середовища або неперевірений proxy.

Зупинити контейнери без їх видалення:

```bash
docker-compose stop
```

Зупинити та видалити контейнери й мережу цього Compose-проєкту:

```bash
docker-compose down
```

Видалити також образи цього Compose-проєкту:

```bash
docker-compose down --rmi all
```

Видалити образи та volumes цього Compose-проєкту:

```bash
docker-compose down --rmi all -v
```

Не використовуйте `docker system prune`, якщо не хочете видалити ресурси
інших Docker-проєктів. Перевірити, що сервіси зупинені, можна командою:

```bash
docker-compose ps
docker ps
```

Локальний запуск використовує loopback. Docker може використовувати
`0.0.0.0` усередині контейнера лише для опублікованих Docker-портів.

## Збереження вкладок і сесій

Стан workspace зберігається локально у браузері й не надсилається на сервер.
Автоматично зберігаються:

- усі вкладки та їхні назви;
- активна вкладка;
- поля Repeater, Intruder, Target, OSINT, Scanner, Comparer і Decoder;
- dictionaries, transformations і стан Decoder;
- Target map, Scanner findings, OSINT/Comparer результати;
- мова інтерфейсу.

У верхній панелі доступні:

| Кнопка | Призначення |
|---|---|
| **Save session** | Явно записує поточний snapshot у browser storage |
| **Export** | Завантажує session JSON-файл |
| **Import** | Відновлює вкладки та стан із session JSON |

Session snapshot не містить `data/ca/ca.key`, серверних файлів, SQLite або
інших приватних файлів. Не зберігайте у session JSON секрети, якщо вони
випадково введені у поля запиту.

## Архітектура

```text
Browser :8000
   │
   ▼
Django web
   ├── self-contained HTML/CSS/JavaScript UI
   ├── SQLite History
   └── browser-facing API gateway
         │
         ▼
Go engine :8081
   ├── /health
   ├── /proxy/request
   ├── /proxy/intruder
   ├── /proxy/target-map
   ├── /proxy/osint
   ├── /proxy/scanner
   ├── /events
   └── /events/stream
         │
         ▼
Passive MITM proxy :8080
```

Межі шарів:

- UI відповідає за введення, відображення, workspace і browser persistence;
- Django відповідає за browser API, SQLite History і gateway;
- Go відповідає за виконання HTTP-запитів, Intruder, Target, OSINT, Scanner і
  passive capture;
- `engine/pkg/ca` відповідає за локальний CA;
- `engine/pkg/passive` відповідає за Traffic Store і SSE subscriptions.
- майбутній proxy layer має відповідати за явні direct/HTTP/HTTPS/SOCKS5/TOR
  профілі та перевірку маршруту;
- майбутній AI layer має працювати через типізований tool API, а не отримувати
  довільний доступ до shell, filesystem або внутрішніх процесів.

## Інструменти

### Repeater

Repeater працює з одним повним raw HTTP editor:

```http
GET /api/echo?value=test HTTP/1.1
Host: 127.0.0.1:3000
Accept: application/json

```

Підтримуються Host/Path overrides, `Ctrl+Enter`/`Cmd+Enter`, Copy response,
повний response inspector, binary response у Base64/Hex-представленні та
автоматичне збереження завершеного exchange у History.

### Intruder

Підтримуються markers:

- `§name§`;
- `{{name}}`;
- `%name%`, зручний для URL-фазингу.

Режими:

- **Sniper** — кожен marker окремо з першим dictionary;
- **Battering Ram** — одне значення в усі markers;
- **Pitchfork** — dictionaries паралельно за індексами;
- **Cluster Bomb** — декартів добуток dictionaries.

Transformations застосовуються зліва направо. Є URL, Base64, Hex, HTML,
JSON, Unicode, whitespace, case, trim, prepend і append transformations.
Великі атаки використовують bounded worker pool, incremental polling і
windowed rendering. `4xx`/`5xx` з отриманою відповіддю залишаються повними
результатами для аналізу.

### Target

Target статично будує site map і не виконує JavaScript та HTML-форми. Він
виявляє:

- HTML links/forms;
- JS/CSS/JSON URLs;
- `robots.txt`, `sitemap.xml`, `Sitemap:`;
- XML `<loc>` entries;
- API-шляхи у статичних ресурсах.

Є controls `Max pages`, `Max depth`, `Delay ms`, `Same origin only`,
`Cancel`, filtering, sorting і exports. У `Map preview` можна згорнути або
розгорнути всі папки однією кнопкою. Browser-driven Chromium worker для
динамічних DOM-маршрутів залишається окремим майбутнім етапом.

### OSINT

OSINT виконує пасивні metadata checks:

- DNS/IP, MX, NS і TXT;
- HTTP status, headers, content type, size;
- redirect chain;
- technology signals;
- cookies;
- security headers;
- robots/sitemap discovery;
- пасивне WAF fingerprinting;
- необов’язковий benign WAF canary.

### Scanner Pro / Safe CMS Recon

Scanner Pro — це окремий read-only reconnaissance workflow, а не копія OSINT.
Він виконує bounded `HEAD`/`GET`/`OPTIONS` перевірки явно введеної цілі:

- WordPress: `/wp-admin/`, `/wp-login.php`, `/wp-json/`, `/xmlrpc.php`;
- Joomla: `/administrator/`;
- `/api/`, `/admin/`, `/phpmyadmin/`;
- `.env`, `.git/HEAD`, backup/database paths;
- `/server-status`, `/debug/`;
- CMS/technology fingerprints;
- security headers;
- TLS version/cipher;
- cookie `Secure`, `HttpOnly`, `SameSite`;
- `Allow` methods;
- WAF/edge signals.

Результат містить `summary`, `details`, `findings`, severity, evidence і
recommendation. Scanner Pro не виконує exploit, fuzzing, brute force,
authentication attacks або access-control bypass. HTTP `200` для публічного
шляху — це сигнал для ручної перевірки, а не автоматичний доказ
уразливості.

### Traffic і History

Traffic працює через SSE:

```text
Go Store -> /events/stream -> Django /api/traffic/stream -> Browser
```

Запит спочатку з’являється як `pending`, після відповіді оновлюється тим самим
event id. Джерелами можуть бути `proxy`, `repeater` і `intruder`.

History зберігає завершені Repeater та Intruder exchange у SQLite. Passive
Traffic зберігається у History лише після дії **Save row**. In-memory Traffic
Store очищується після restart engine або через **Clear** у Traffic.

### Comparer і Decoder

Comparer показує відмінності у Words/Bytes режимах. Decoder підтримує URL,
Base64, Base64 URL-safe, HTML entities, Hex, кодування й декодування байтів,
JSON pretty/minify і SHA-256. Byte encode перетворює текст у 8-бітні двійкові
групи, а Byte decode приймає двійкові групи або десяткові значення байтів.
Значення з History, Traffic і Comparer можна передавати без clipboard.

### Proxy, TOR і AI

Proxy/TOR ще не входять до поточного runtime. AI chat використовує adapters для
Ollama, OpenAI, Anthropic, Gemini, OpenRouter, Groq, Mistral і custom
OpenAI-compatible endpoint-ів. Контекст передається лише після явної дії
оператора `Send ... to AI`; автоматичного повного workspace context немає.
- proxy-профілі `Direct`, HTTP, HTTPS і SOCKS5;
- окремий локальний TOR SOCKS5 endpoint із видимим статусом підключення;
- вибір маршруту для Repeater, Intruder, Target, OSINT, Scanner, workflows
  і browser-driven worker;
- health check маршруту, DNS policy, latency та попередження про зміну
  source IP;
- окрема вкладка `AI` з компактними chat bubbles і preview прикріплених даних;
- ізольований AI chat без tools і без доступу до engine або workspace API;
- аналіз SPA fallback через fingerprints і black-box observable changes.

AI-агент не повинен отримувати довільне виконання shell-команд або доступ до
filesystem. Для поточного runtime активні запити та Intruder перевіряються
через execution profile, scope, rate limit, concurrency, budget і audit.
Прикріплений context навмисно може містити Authorization, cookies, JWT, API
keys та інші поля exchange, якщо вони є в History/Traffic. Обирайте provider з
урахуванням цієї політики; приховане masking не застосовується.

## API

### Django API

| Method | Endpoint | Призначення |
|---|---|---|
| `GET` | `/` | UI |
| `POST` | `/api/execute` | Repeater gateway |
| `POST` | `/api/intruder` | Запуск Intruder |
| `GET` | `/api/intruder?attack_id=<id>` | Прогрес і результати Intruder |
| `DELETE` | `/api/intruder?attack_id=<id>` | Cancel Intruder |
| `GET` | `/api/intruder/saved` | Збережені Intruder configurations |
| `POST` | `/api/intruder/saved` | Зберегти Intruder configuration |
| `POST` | `/api/intruder/saved/<id>/run` | Повторно запустити configuration |
| `POST` | `/api/target-map` | Запустити Target map |
| `GET` | `/api/target-map?map_id=<id>` | Статус Target map |
| `DELETE` | `/api/target-map?map_id=<id>` | Скасувати Target map |
| `POST` | `/api/osint` | OSINT metadata checks |
| `POST` | `/api/scanner` | Scanner Pro findings |
| `POST` | `/api/agent/chat` | Conversational AI turn із явним evidence context |
| `GET` | `/api/history` | History list |
| `GET` | `/api/history/export` | Експорт History JSON |
| `DELETE` | `/api/history/<id>` | Видалити History record |
| `GET` | `/api/traffic` | Traffic snapshot |
| `DELETE` | `/api/traffic` | Очистити live Traffic |
| `GET` | `/api/traffic/stream` | Traffic SSE |
| `POST` | `/api/traffic/save` | Зберегти Traffic exchange у History |
| `POST` | `/api/traffic/annotate` | Додати tags/notes до Traffic |

### Go engine API

```text
GET    /health
POST   /proxy/request
POST   /proxy/intruder
GET    /proxy/intruder/<attack_id>
DELETE /proxy/intruder/<attack_id>
POST   /proxy/target-map
GET    /proxy/target-map/<map_id>
DELETE /proxy/target-map/<map_id>
POST   /proxy/osint
POST   /proxy/scanner
GET    /events
DELETE /events
GET    /events/stream
```

## Структура проєкту

```text
Request-Rider/
├── engine/
│   ├── main.go
│   └── pkg/
│       ├── ca/
│       ├── intruder/
│       └── passive/
├── web/
│   ├── manage.py
│   ├── core/
│   ├── lab/
│   ├── templates/lab/index.html
│   ├── requirements.txt
│   └── .venv/
├── data/ca/
├── tests/e2e/
├── run-engine.sh
├── docker-compose.yml
├── ROADMAP.md
├── DEVELOPMENT_ISSUES.md
├── UX_TEST_REPORT.md
└── README.md
```

`web/.venv/`, `web/db.sqlite3`, logs, `__pycache__` і `data/ca/ca.key` є
локальними артефактами. Приватний CA-ключ не можна комітити або публікувати.

## Перевірка і QA

Go tests:

```bash
cd engine
go test ./... -count=1
```

Django checks і tests:

```bash
cd web
python manage.py check
python manage.py test -v 2
```

Inline JavaScript syntax:

```bash
python - <<'PY'
from pathlib import Path
import re, subprocess, tempfile

html = Path("web/templates/lab/index.html").read_text()
script = re.search(r"<script>(.*)</script>", html, re.S).group(1)
with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as handle:
    handle.write(script)
    path = handle.name
result = subprocess.run(["node", "--check", path], capture_output=True, text=True)
print(result.stderr, end="")
raise SystemExit(result.returncode)
PY
```


Smoke script для явно дозволеної test target:

```bash
TARGET_URL=https://authorized.example.test/api/echo?value=smoke ./tools/smoke.sh
```

## Документація і план

- `ROADMAP.md` — виконані етапи й майбутні напрямки;
- `AGENT_RUNTIME.md` — ізольований AI chat, explicit evidence context і
  provider connection policy;
- `LLM_ROADMAP.md` — конкретний roadmap ітеративного LLM-тестування,
  state, policy, verify та human-readable reports;
- `DEVELOPMENT_ISSUES.md` — відомі проблеми та рішення;
- `BUG_BOUNTY_AND_DEVELOPERS.md` — канал повідомлень про помилки, пропозицій
  і участі в розробці;
- зовнішній каталог `RequestRider-QA/QA_REPORT.md` — QA-звіт, якщо він
  створений у локальному середовищі;
- зовнішні каталоги `RequestRider-QA/selenium` і
  `RequestRider-QA/playwright` — окремі browser QA-набори.

Найближчі великі напрями — browser-driven Target worker на Chromium/Playwright,
явні proxy/TOR-профілі та безпечний AI tool layer. Browser automation, proxy
маршрутизація й AI-агент мають залишатися окремими компонентами з локальними
fixtures, approval gates і відтворюваними тестами.
