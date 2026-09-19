

<img width="2912" height="1440" alt="Gemini_Generated_Image_am0pnwam0pnwam0p" src="https://github.com/user-attachments/assets/dbe3af9e-9271-40f4-9cf9-1c756765957a" />
<img width="1353" height="497" alt="Screenshot 2026-09-19 at 14-23-39 RequestRider" src="https://github.com/user-attachments/assets/45c5dd27-d9e8-4a00-9dcf-7157b0bd61a7" />


# RequestRider

RequestRider — локальний інструмент для ручного QA, аналізу HTTP-трафіку та
дозволеного тестування власних систем. Проєкт об’єднує Django UI, Go engine,
SQLite History, passive MITM proxy і явний маршрут Direct або SOCKS5/Tor.

> Використовуйте інструмент лише проти систем, якими ви володієте або на
> тестування яких маєте явний дозвіл. Tor, VPN, Docker і віртуальна машина не
> роблять несанкціоноване тестування дозволеним.

## Зміст

- [Архітектура](#архітектура)
- [Можливості](#можливості)
- [Швидкий локальний запуск](#швидкий-локальний-запуск)
- [Docker Compose](#docker-compose)
- [Маршрутизація через Direct або SOCKS5/Tor](#маршрутизація-через-direct-або-socks5tor)
- [Passive MITM і локальний CA](#passive-mitm-і-локальний-ca)
- [Основний workflow](#основний-workflow)
- [API](#api)
- [Перевірка та діагностика](#перевірка-та-діагностика)
- [Безпека](#безпека)
- [Пов’язані документи](#повязані-документи)

## Архітектура

### Локальний режим

```text
Browser :8000
    -> Django web gateway + SQLite History
    -> Go engine :8081
         -> outbound HTTP execution
         -> Intruder / Target / OSINT / Scanner
         -> passive MITM proxy :8080
         -> Direct або SOCKS5/Tor
```

### Docker Compose

```text
Browser :8000
    -> web container
         -> engine:8081
              -> tor:9050
              -> passive proxy :8080
```

`web` відповідає за UI, workspace і browser-facing API. `engine` виконує
HTTP-операції, Intruder, Target, OSINT, Scanner і passive capture. `tor` —
окремий SOCKS5 upstream у Compose-мережі. SQLite зберігається у web-контейнері
та залежить від його filesystem/volume-конфігурації.

Локальні сервіси за замовчуванням використовують loopback:

```text
127.0.0.1:8000  Django UI
127.0.0.1:8080  passive HTTP MITM proxy
127.0.0.1:8081  Go engine API
127.0.0.1:9050  локальний SOCKS5 Tor
```

Не запускайте локальний і Docker-режим одночасно: вони використовують однакові
порти.

## Можливості

- **Repeater** — raw HTTP editor, повторне надсилання, перегляд відповіді,
  збереження exchange у History.
- **Intruder** — Sniper, Battering Ram, Pitchfork, Cluster Bomb, dictionaries,
  transformations, bounded worker pool, pause/resume/cancel, polling і
  JSON/CSV export.
- **Target** — асинхронна статична карта сайту з обмеженнями pages/depth/delay,
  same-origin, cancel і JSON/CSV/HTML export. JavaScript не виконується.
- **OSINT** — DNS/IP, MX/NS/TXT, HTTP metadata, redirects, technologies,
  cookies, security headers, robots/sitemap і пасивні WAF-сигнали.
- **Scanner Pro** — bounded read-only перевірки CMS/public paths, TLS,
  cookies, methods, headers і configuration exposure signals.
- **Comparer** — Words і Bytes.
- **Decoder** — URL, Base64, Base64 URL-safe, HTML, Hex, byte, JSON і SHA-256.
- **Traffic** — live SSE-потік passive proxy, Repeater і Intruder.
- **History** — SQLite-записи завершених exchange, tags/notes, export/import.
- **AI** — аналіз лише явно прикріплених оператором evidence; автономного
  виконання дій немає.
- **Workspace** — окремі вкладки інструментів, autosave і session JSON.

Scanner та інші активні інструменти не замінюють дозвіл на тестування і не
призначені для exploit, brute force, fuzzing або access-control bypass.

## Швидкий локальний запуск

Потрібні Go, Python 3, `curl` і `venv` або `virtualenv`.

Із кореня репозиторію:

```bash
./run-engine.sh
```

Скрипт:

1. запускає Go engine, якщо `/health` ще недоступний;
2. створює `web/.venv` і встановлює Python-залежності;
3. застосовує Django migrations;
4. запускає UI на `127.0.0.1:8000`.

Перевірка:

```bash
curl http://127.0.0.1:8081/health
curl -I http://127.0.0.1:8000/
```

Очікувано:

```json
{"ok":true}
```

Якщо engine або UI вже працюють, не запускайте другий екземпляр. Для
нестандартного CA або engine:

```bash
CA_DIR=/path/to/ca ./run-engine.sh
ENGINE_URL=http://127.0.0.1:8081 ./run-engine.sh
```

### Ручний запуск компонентів

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

## Docker Compose

Переконайтеся, що Docker daemon доступний:

```bash
docker ps
```

Якщо користувач щойно доданий до групи `docker`, застосуйте нову групу без
перезавантаження:

```bash
newgrp docker
```

Збірка і запуск:

```bash
docker compose build
docker compose up -d
docker compose ps
```

Compose створює три сервіси:

| Сервіс | Роль | Внутрішня адреса |
|---|---|---|
| `tor` | SOCKS5 Tor upstream | `tor:9050` |
| `engine` | Go API і passive proxy | `engine:8081`, `engine:8080` |
| `web` | Django UI і gateway | `web:8000` |

У `docker-compose.yml` engine отримує:

```text
ROUTE_ADDRESS=tor:9050
PROXY_LISTEN_ADDR=0.0.0.0:8080
ENGINE_LISTEN_ADDR=0.0.0.0:8081
```

`0.0.0.0` тут потрібен лише всередині контейнера, щоб Docker network могла
доставити трафік до сервісу. На host порти публікуються тільки на
`127.0.0.1`.

Перевірка:

```bash
curl http://127.0.0.1:8081/health
curl http://127.0.0.1:8081/route
docker compose logs --no-color tor
```

У логах Tor має з’явитися:

```text
Bootstrapped 100% (done)
```

Зупинка:

```bash
docker compose stop
```

Видалення контейнерів і мережі:

```bash
docker compose down
```

Видалення образів цього Compose-проєкту:

```bash
docker compose down --rmi all
```

Не використовуйте `docker system prune`, якщо не хочете видалити ресурси
інших проєктів.

## Маршрутизація через SOCKS5/Tor

Маршрут налаштовується у вкладці **Tor/Proxy**.

- Порожня адреса — **Direct**.
- `127.0.0.1:9050` — локальний Tor при локальному запуску.
- `tor:9050` — Tor-контейнер для engine у Docker Compose.
- Будь-який інший доступний SOCKS5 `host:port` — віддалений або локальний
  SOCKS5-проксі.

Після введення адреси натисніть **Apply route**. **Cancel route** очищає
адресу і повертає Direct. **Check connection** перевіряє ціль, latency,
HTTP status і зовнішню IP-адресу через `https://api.ipify.org?format=json`.

Для ручної перевірки у браузері можна використовувати:

| Сервіс | URL | Призначення |
|---|---|---|
| Tor Project | <https://check.torproject.org/> | Перевірка, чи визначається браузер як підключений через Tor |
| ipify | <https://api.ipify.org?format=json> | Мінімальна JSON-відповідь із зовнішньою IP |
| ifconfig.me | <https://ifconfig.me/ip> | Зовнішня IP у plain text |
| icanhazip | <https://icanhazip.com/> | Зовнішня IP у plain text |
| ipinfo.io | <https://ipinfo.io/json> | IP та базова інформація у JSON |

Щоб ручна перевірка показувала Tor-маршрут, браузер має використовувати
`127.0.0.1:8080` як HTTP/HTTPS proxy для RequestRider або `127.0.0.1:9050`
як SOCKS5. Посилання в UI саме по собі не змінює маршрут браузера. Не
надсилайте через сторонні IP-сервіси секретні дані й враховуйте, що кожен
сервіс бачить IP-адресу та час запиту.

### Як проходить трафік

Для активних інструментів:

```text
Repeater / Intruder / Target / OSINT / Scanner
    -> Go engine transport
    -> Direct або SOCKS5/Tor
    -> target
```

Для браузерного трафіку:

```text
Browser
    -> HTTP proxy 127.0.0.1:8080
    -> passive MITM
    -> той самий outbound transport
    -> Direct або SOCKS5/Tor
    -> target
```

Активні інструменти не проходять повторно через `:8080`; вони використовують
той самий route manager без подвійного MITM. Їхні події все одно публікуються
у спільний Traffic Store.

У Docker engine не може використовувати `127.0.0.1:9050` для Tor-контейнера:
це loopback самого engine-контейнера. Використовуйте саме `tor:9050`.

Після зміни маршруту нові з’єднання використовують нову адресу, а кеш
підтвердженої source IP очищається. Якщо SOCKS5 недоступний, запит має
завершитися явною помилкою, а не непомітним fallback у Direct.

## Passive MITM і локальний CA

Engine автоматично створює:

```text
data/ca/ca.crt
data/ca/ca.key
```

Для HTTPS імпортуйте `data/ca/ca.crt` лише в окремий тестовий профіль
браузера. `data/ca/ca.key` — приватний ключ і не повинен потрапляти до Git,
логів або сторонніх систем.

Налаштування браузера:

```text
HTTP proxy:  127.0.0.1
HTTP port:   8080
HTTPS proxy:  127.0.0.1
HTTPS port:  8080
```

Traffic є in-memory Store engine. Pending exchange спочатку показується зі
статусом `pending`, після відповіді оновлюється тим самим ID. Перезапуск engine
або очищення Traffic видаляє незбережені live events. **Save row** переносить
вибраний exchange у Django History/SQLite.

Системні запити браузера, наприклад Firefox Push Service, можуть потрапляти у
Traffic. Це не обов’язково трафік тестованого сайту; використовуйте окремий
профіль браузера і не відкривайте особисті сесії через MITM.

## Основний workflow

1. Визначте письмовий scope і дозвіл на тестування.
2. Запустіть локальний або Docker Compose режим, але не обидва одночасно.
3. Перевірте `/health`, активний route і зовнішню IP.
4. Якщо потрібен браузерний Traffic, імпортуйте CA в тестовий профіль і
   встановіть proxy `127.0.0.1:8080`.
5. Почніть із Repeater, потім використовуйте Target/OSINT/Scanner для
   read-only аналізу.
6. Для Intruder задайте мінімальні dictionaries, concurrency і delay.
7. Зберігайте лише потрібні записи, очищайте cookies, tokens і exports після
   завершення.

## API

### Django gateway

| Method | Endpoint | Призначення |
|---|---|---|
| `GET` | `/` | UI |
| `POST` | `/api/execute` | Repeater |
| `POST` | `/api/intruder` | Запуск Intruder |
| `GET` | `/api/intruder?attack_id=<id>` | Статус і результати |
| `DELETE` | `/api/intruder?attack_id=<id>` | Cancel Intruder |
| `GET/POST` | `/api/intruder/saved` | Saved configurations |
| `POST` | `/api/target-map` | Target map |
| `GET/DELETE` | `/api/target-map?map_id=<id>` | Статус або cancel |
| `POST` | `/api/osint` | OSINT |
| `POST` | `/api/scanner` | Scanner Pro |
| `GET/PUT` | `/api/route` | Читання або зміна маршруту |
| `POST` | `/api/route/check` | Перевірка route і source IP |
| `GET` | `/api/history` | History |
| `GET` | `/api/history/export` | Export History |
| `DELETE` | `/api/history/<id>` | Видалення запису |
| `POST` | `/api/history/bulk` | Масове видалення |
| `GET/DELETE` | `/api/traffic` | Traffic або очищення |
| `GET` | `/api/traffic/stream` | Traffic SSE |
| `POST` | `/api/traffic/save` | Save Traffic row |
| `POST` | `/api/traffic/annotate` | Tags/notes |
| `POST` | `/api/agent/chat` | Один AI chat turn |

### Go engine

```text
GET  /health
GET  /route
PUT  /route
POST /route/check
POST /proxy/request
POST /proxy/intruder
GET  /proxy/intruder/<attack_id>
DELETE /proxy/intruder/<attack_id>
GET  /events
GET  /events/stream
```

## Перевірка та діагностика

З кореня репозиторію:

```bash
cd engine && go test ./... -count=1
cd ../web && python manage.py check
cd web && python manage.py test -v 2
```

Перевірка inline JavaScript:

```bash
python3 - <<'PY'
from pathlib import Path
import re
import subprocess
import tempfile

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

Docker-диагностика:

```bash
docker compose ps
docker compose logs --no-color --tail=100 tor engine web
docker system df
df -h /
```

Типові проблеми:

| Симптом | Причина | Дія |
|---|---|---|
| `permission denied /var/run/docker.sock` | користувач не в групі Docker | `newgrp docker` або новий login |
| `address already in use` | локальний режим уже займає порт | зупинити один режим перед запуском іншого |
| Tor не працює | bootstrap ще не завершився | дочекатися `Bootstrapped 100% (done)` |
| Docker Tor не доступний з engine | використано `127.0.0.1` замість service DNS | у Compose використовувати `tor:9050` |
| `no space left on device` | переповнений host або Docker cache | звільнити місце і перевірити `docker system df` |
| HTTPS certificate error | CA не імпортований у тестовий профіль | імпортувати `data/ca/ca.crt` |

## Безпека

Розширені рекомендації щодо LUKS, VPN/kill switch, firewall, VM, Docker,
секретів, CA і безпечного scope зберігаються в [`SECURITY.md`](SECURITY.md).
Це практична пам’ятка, а не гарантія абсолютної анонімності або безпеки.

## Пов’язані документи

- [`SECURITY.md`](SECURITY.md) — операційна безпека та checklist.
- [`ROADMAP.md`](ROADMAP.md) — короткий актуальний план розвитку.
- [`AGENT_USER_GUIDE.md`](AGENT_USER_GUIDE.md) — окрема інструкція AI-вкладки.
- [`AGENT_RUNTIME.md`](AGENT_RUNTIME.md) — межі та модель AI runtime.

