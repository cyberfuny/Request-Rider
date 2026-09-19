<img width="2912" height="1440" alt="Gemini_Generated_Image_am0pnwam0pnwam0p (1)" src="https://github.com/user-attachments/assets/d24a8205-5324-4a97-8754-17dc437acb55" />

<img width="1141" height="356" alt="Screenshot 2026-09-18 at 11-53-24 Screenshot_2026-09-18_11-48-37 png (PNG Image 1366 × 733 pixels) — Scaled (84_)" src="https://github.com/user-attachments/assets/e2dfb7f5-18b1-41d5-acd1-83fad058a846" />



# RequestRider

RequestRider — локальний браузерний QA-інструмент для ручного аналізу,
повторного надсилання та безпечного дослідження HTTP-трафіку. Проєкт поєднує
Django UI, Go engine, SQLite History і локальний passive MITM proxy.

> Використовуйте інструмент лише для власних систем або цілей, на які маєте
> явний дозвіл. Intruder, Target, OSINT і Scanner Pro не замінюють дозвіл на
> тестування та не призначені для обходу доступу, brute force або експлуатації
> чужих систем.

## Можливості

### Робочі вкладки

- **Repeater** — редагування та повторне надсилання повного raw HTTP-запиту.
  Підтримуються Host/Path overrides, `Ctrl+Enter`/`Cmd+Enter`, перегляд
  відповіді та збереження exchange у History.
- **Intruder** — режими Sniper, Battering Ram, Pitchfork і Cluster Bomb,
  dictionaries, transformations, bounded worker pool, pause/resume/cancel,
  polling та експорт результатів.
- **Target** — статична карта сайту без виконання JavaScript і HTML-форм.
  Є обмеження pages/depth/delay, same-origin режим, cancel, фільтри,
  сортування та експорт у JSON/CSV/HTML/tree.
- **OSINT** — DNS/IP, MX/NS/TXT, HTTP metadata, redirects, technologies,
  cookies, security headers, robots/sitemap discovery і пасивні WAF-сигнали.
- **Scanner Pro** — обмежені read-only перевірки явно вказаної цілі:
  CMS/public paths, admin/API endpoints, backup/debug/config exposure, TLS,
  cookies, HTTP methods, headers і WAF-сигнали.
- **Traffic** — live-потік passive proxy, Repeater та Intruder через SSE.
- **History** — SQLite-сховище завершених exchange з пошуком, tags/notes,
  переглядом повного запиту й відповіді та експортом.
- **Comparer** — порівняння запитів або відповідей у режимах Words і Bytes.
- **Decoder** — URL, Base64, Base64 URL-safe, HTML entities, Hex, byte
  encoding/decoding, JSON pretty/minify та SHA-256.
- **AI** — чат із вибраним LLM-провайдером. До AI передаються лише дані, які
  оператор явно прикріпив кнопкою `Send ... to AI`.
- **Workspace** — вкладки та їхній стан автоматично зберігаються у браузері;
  доступні Save session і Export/Import session JSON.

Scanner Pro не виконує exploit, fuzzing, brute force, authentication attacks
або access-control bypass. HTTP `200` для публічного шляху — це сигнал для
ручної перевірки, а не доказ уразливості.

## Швидкий запуск

Потрібні Go, Python 3, `curl` і `venv` або `virtualenv`.

Із кореня репозиторію:

```bash
./run-engine.sh
```

Скрипт запускає Go engine, створює `web/.venv`, встановлює залежності,
застосовує Django-міграції та запускає UI.

Після запуску:

- UI: <http://127.0.0.1:8000>
- engine health: <http://127.0.0.1:8081/health>
- passive HTTP proxy: `127.0.0.1:8080`

Якщо engine уже запущений, скрипт не створює другий процес. Для нестандартної
конфігурації:

```bash
CA_DIR=/path/to/ca ./run-engine.sh
ENGINE_URL=http://127.0.0.1:8081 ./run-engine.sh
```

Усі сервіси за замовчуванням використовують loopback. Не відкривайте UI, engine
або proxy назовні без розуміння того, що вони можуть обробляти cookies,
заголовки, тіла запитів та інші секретні дані.

### Ручний запуск

Термінал 1:

```bash
cd engine
go run .
```

Термінал 2:

```bash
cd web
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
ENGINE_URL=http://127.0.0.1:8081 python manage.py runserver 127.0.0.1:8000
```

### Docker Compose

Не запускайте Docker Compose одночасно з `./run-engine.sh`: обидва варіанти
використовують порти `8000`, `8080` і `8081`.

Для Docker Compose v2:

```bash
docker compose up --build
```

Для систем, де використовується окрема команда Compose:

```bash
docker-compose up --build
```

Перевірте запущені сервіси:

```bash
docker compose ps
curl http://127.0.0.1:8081/health
curl -I http://127.0.0.1:8000/
```

Якщо у системі доступна лише команда `docker-compose`, замініть нею
`docker compose` у наведених командах.

Після запуску:

- UI доступний на <http://localhost:8000>;
- engine health доступний на <http://127.0.0.1:8081/health>;
- passive proxy працює на `127.0.0.1:8080`.
- контейнер Tor надає SOCKS5 upstream `tor:9050` всередині Compose-мережі та
  публікує його як `127.0.0.1:9050` для локальної діагностики.

Для passive proxy налаштуйте браузер або інший дозволений QA-інструмент на HTTP
proxy `127.0.0.1:8080`. Для HTTPS імпортуйте `data/ca/ca.crt` до довіреного
сховища клієнта. Файл `data/ca/ca.key` є приватним ключем, тому його не можна
публікувати, передавати іншим людям або комітити.

Зупинити контейнери без їх видалення:

```bash
docker compose stop
```

Зупинити та видалити контейнери й мережу цього Compose-проєкту:

```bash
docker compose down
```

Видалити також образи цього Compose-проєкту:

```bash
docker compose down --rmi all
```

Видалити образи та volumes цього Compose-проєкту:

```bash
docker compose down --rmi all -v
```

Для старої команди Compose використовуйте відповідно `docker-compose stop`,
`docker-compose down`, `docker-compose down --rmi all` і
`docker-compose down --rmi all -v`.

Не використовуйте `docker system prune`, якщо не хочете видалити ресурси інших
Docker-проєктів.

Переконатися, що сервіси зупинені, можна командами:

```bash
docker compose ps
docker ps
```

### Маршрутизація через SOCKS5/TOR

У верхній панелі UI доступний глобальний профіль маршруту:

- **Direct** — пряме з'єднання без upstream proxy;
- **SOCKS5** — SOCKS5-адреса з поля `127.0.0.1:9050` або іншої вказаної адреси;
- **TOR** — той самий SOCKS5-механізм із профільною назвою для локального Tor.

Для локального Tor запустіть Tor із SOCKS5 на `127.0.0.1:9050`, виберіть
**TOR** і натисніть **Apply route**. Для Docker Compose виберіть **TOR** та
вкажіть `tor:9050`, оскільки engine у контейнері не може звернутися до
loopback-адреси host як до іншого контейнера.

Маршрут застосовується до Repeater, Intruder, Target, OSINT і Scanner, а також
до upstream-з'єднань passive MITM. Ланцюжок для браузера залишається таким:

```text
Browser -> RequestRider MITM :8080 -> SOCKS5/TOR :9050 -> target
```

Для активних інструментів повторний прохід через `:8080` не використовується:
вони застосовують той самий outbound transport напряму. Це не створює
подвійного MITM, але результати Repeater/Intruder усе одно публікуються у
спільний Traffic Store.

Після зміни профілю нові з'єднання використовують новий маршрут; idle
з'єднання закриваються. Якщо SOCKS5/Tor недоступний, запит завершується явною
помилкою, а не успішним fallback на Direct.

## Налаштування AI

Відкрийте вкладку **AI**, виберіть провайдера та за потреби заповніть:

1. **Endpoint** — URL API;
2. **Model** — назва моделі;
3. **API key** — токен або ключ доступу.

Поле **API key** є password-полем і не зберігається у workspace/session JSON.
Для Ollama токен не потрібен: запустіть Ollama локально та встановіть вибрану
модель, наприклад:

```bash
ollama pull llama3.1
```

Підтримуються Ollama, OpenAI, Anthropic Claude, OpenRouter, Google Gemini, Groq,
Mistral і Custom OpenAI-compatible. Для вбудованих провайдерів endpoint і
модель мають значення за замовчуванням; їх можна змінити в UI.

### Додавання токена через змінні середовища

Замість введення ключа в UI його можна передати процесу Django. Назви змінних:

| Провайдер | Токен | Endpoint і модель |
|---|---|---|
| OpenAI | `OPENAI_LLM_API_KEY` | `OPENAI_LLM_ENDPOINT`, `OPENAI_LLM_MODEL` |
| Anthropic | `ANTHROPIC_LLM_API_KEY` | `ANTHROPIC_LLM_ENDPOINT`, `ANTHROPIC_LLM_MODEL` |
| OpenRouter | `OPENROUTER_LLM_API_KEY` | `OPENROUTER_LLM_ENDPOINT`, `OPENROUTER_LLM_MODEL` |
| Gemini | `GEMINI_LLM_API_KEY` | `GEMINI_LLM_ENDPOINT`, `GEMINI_LLM_MODEL` |
| Groq | `GROQ_LLM_API_KEY` | `GROQ_LLM_ENDPOINT`, `GROQ_LLM_MODEL` |
| Mistral | `MISTRAL_LLM_API_KEY` | `MISTRAL_LLM_ENDPOINT`, `MISTRAL_LLM_MODEL` |
| Custom OpenAI-compatible | `AGENT_LLM_API_KEY` | `AGENT_LLM_ENDPOINT`, `AGENT_LLM_MODEL` |

Приклад запуску:

```bash
OPENAI_LLM_API_KEY='ваш-токен' ./run-engine.sh
```

Щоб не зберігати ключ в історії shell, задайте змінну в оточенні перед запуском:

```bash
export OPENAI_LLM_API_KEY='ваш-токен'
./run-engine.sh
```

Для Custom OpenAI-compatible endpoint:

```bash
export AGENT_LLM_ENDPOINT='https://llm.example.test/v1/chat/completions'
export AGENT_LLM_MODEL='your-model'
export AGENT_LLM_API_KEY='ваш-токен'
./run-engine.sh
```

Віддалені endpoint мають використовувати HTTPS і не можуть вказувати на
loopback. Локальний Ollama дозволений лише через HTTP на `127.0.0.1`,
`localhost` або `::1`.

### Як передати дані до AI

AI не отримує весь workspace автоматично і не має доступу до shell, filesystem,
History API, Traffic API або Go engine. Спочатку виберіть потрібні дані та
натисніть `Send ... to AI` у Repeater, Intruder, Target, OSINT, Scanner, History
або Traffic. Потім поставте запитання у вкладці AI.

Прикріплені дані можуть містити Authorization, cookies, JWT, API keys, headers,
параметри та тіла запитів. Перед надсиланням до зовнішнього provider перевірте,
чи немає в них секретів. Автоматичне masking не застосовується.

AI формує лише текстову аналітичну відповідь. Він не запускає Repeater,
Intruder, OSINT, Scanner, Target Map або інші функції RequestRider.

## Passive proxy та CA

Налаштуйте браузер або інший дозволений QA-інструмент на HTTP proxy
`127.0.0.1:8080`. Для HTTPS імпортуйте `data/ca/ca.crt`. Події доступні у
вкладці **Traffic**.

Traffic зберігається в пам’яті engine та очищається після його перезапуску або
через **Clear**. Збереження до SQLite виконується окремо дією **Save row**.
Кнопка **Refresh traffic** очищає поточний in-memory snapshot, а не надсилає
повторний запит.

## Архітектура

```text
Browser :8000
   │
   ▼
Django web
   ├── UI та browser persistence
   ├── SQLite History
   └── browser-facing API gateway
         │
         ▼
Go engine :8081
   ├── HTTP execution, Intruder, Target, OSINT, Scanner
   ├── passive capture
   └── SSE events
         │
         ▼
Passive MITM proxy :8080
```

UI відповідає за введення, відображення та стан workspace. Django надає
browser API і History. Go engine виконує HTTP-операції, фонові workflows та
passive capture. Локальний CA автоматично створюється engine у `data/ca/`.

Окремі proxy-профілі HTTP/HTTPS/SOCKS5/TOR і browser-driven Chromium worker не
входять до поточної реалізації; вони перелічені лише в roadmap.

## API

### Django API

| Method | Endpoint | Призначення |
|---|---|---|
| `GET` | `/` | UI |
| `POST` | `/api/execute` | Repeater |
| `POST` | `/api/intruder` | Запуск Intruder |
| `GET` | `/api/intruder?attack_id=<id>` | Статус і результати Intruder |
| `DELETE` | `/api/intruder?attack_id=<id>` | Скасування Intruder |
| `GET/POST` | `/api/intruder/saved` | Перелік і збереження конфігурацій |
| `POST` | `/api/intruder/saved/<id>/run` | Повторний запуск конфігурації |
| `POST` | `/api/target-map` | Запуск Target map |
| `GET` | `/api/target-map?map_id=<id>` | Статус Target map |
| `DELETE` | `/api/target-map?map_id=<id>` | Скасування Target map |
| `POST` | `/api/osint` | OSINT |
| `POST` | `/api/scanner` | Scanner Pro |
| `POST` | `/api/agent/chat` | Один AI chat turn |
| `GET` | `/api/history` | History |
| `GET` | `/api/history/export` | Експорт History |
| `POST` | `/api/history/import` | Legacy backend endpoint; не доступний у UI |
| `DELETE` | `/api/history/<id>` | Видалення запису History |
| `POST` | `/api/history/bulk` | Масове видалення записів History |
| `GET/DELETE` | `/api/traffic` | Перегляд і очищення Traffic |
| `GET` | `/api/traffic/stream` | Traffic SSE |
| `POST` | `/api/traffic/save` | Збереження Traffic у History |
| `POST` | `/api/traffic/annotate` | Tags/notes для Traffic |

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

## Збереження даних

Workspace зберігається локально у browser storage. Session JSON може містити
вкладки, запити, відповіді та результати аналізу, але не містить
`data/ca/ca.key`, серверних файлів або SQLite. Не зберігайте й не експортуйте
session JSON, якщо в ньому є секрети.

Локальні артефакти `web/.venv/`, `web/db.sqlite3`, логи, `__pycache__` і
`data/ca/ca.key` не повинні потрапляти до репозиторію.

## Особливості інструментів

### Intruder

Підтримуються маркери `§name§`, `{{name}}` і `%name%`. Останній варіант
зручний для URL-фазингу у стилі ffuf, наприклад `/FUZZ/%payload%/`.

- **Sniper** — кожен marker окремо перебирає перший словник.
- **Battering Ram** — одне значення підставляється в усі markers.
- **Pitchfork** — списки перебираються паралельно за індексами до коротшого.
- **Cluster Bomb** — декартів добуток словників.

Transformations застосовуються зліва направо. `base64Decode` і `hexDecode`
можуть повертати binary bytes; вони не відхиляються лише через відсутність
UTF-8. `delay_ms` задає паузу між запитами; за значення, більшого за нуль,
jobs виконуються послідовно.

POST повертає `attack_id`, GET віддає прогрес і накопичені результати. GET
підтримує `since`, повертає `result_offset`, а `limit` обмежує розмір порції.
DELETE скасовує незавершену атаку через context. HTTP `4xx`/`5xx` з отриманою
відповіддю є повноцінними результатами для аналізу.

### Target

`POST /api/target-map` приймає `url`, `max_pages`, `max_depth`, `delay_ms` і
`same_origin`; GET повертає прогрес і `pages`, DELETE скасовує обхід.

Виявляються HTML links/forms, JS/CSS/JSON URLs, `robots.txt`, `sitemap.xml`,
`Sitemap:` і XML `<loc>`. Для ресурсів зберігаються `url`, `depth`, `стан`,
`content_type` і `kind`.

Target не виконує JavaScript і не надсилає форми. Browser-driven обхід із
Chromium/Playwright залишається майбутнім напрямом. UI експортує карту в JSON,
CSV і текстове дерево.

### AI

AI-вкладка аналізує лише явно прикріплені оператором observations. Контекст не
завантажується автоматично для звичайного повідомлення. Доступні провайдери:
`ollama`, `openai`, `anthropic`, `openrouter`, `gemini`, `groq`, `mistral` і
`openai_compatible`.

AI не має tools, execution profile, доступу до History/Traffic API, Go engine,
shell, filesystem або arbitrary HTTP. Віддалений provider endpoint має
використовувати HTTPS; локальний Ollama дозволений лише на loopback.

Просіть AI відокремлювати FACT, HYPOTHESIS та UNKNOWN. Observable change не є
автоматично доказом уразливості.

## Перевірка

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

Перевірка inline JavaScript:

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

Smoke test для явно дозволеної цілі:

```bash
TARGET_URL=https://authorized.example.test/api/echo?value=smoke ./tools/smoke.sh
```

## Документація

- `AGENTS.md` — правила для агентів і розробників;
- `AGENT_RUNTIME.md` — архітектура AI chat, evidence context і обмеження
  provider connection;
- `AGENT_USER_GUIDE.md` — користувацький workflow AI;
- `ROADMAP.md` — виконані етапи та майбутні напрямки;
- `LLM_ROADMAP.md` — майбутній roadmap LLM-тестування;
- `DEVELOPMENT_ISSUES.md` — відомі проблеми та їхні рішення;
- `BUG_BOUNTY_AND_DEVELOPERS.md` — повідомлення про помилки та участь у проєкті.
