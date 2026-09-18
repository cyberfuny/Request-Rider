# Roadmap conversational AI

Поточна AI-архітектура RequestRider — невеликий чат із явним прикріпленням
evidence. LLM аналізує спостереження оператора, а не запускає автономну
місію.

## Реалізовано

- AI chat із provider adapters для Ollama та підтримуваних remote providers;
- явне прикріплення Repeater, Intruder, Target Map, OSINT, Scanner, History і
  Traffic;
- компактний chat context без автоматичного завантаження workspace;
- ізольований chat без tool execution, shell, filesystem і arbitrary HTTP;
- повний exchange context без прихованої redaction policy;
- SPA fallback fingerprinting і black-box observable-change verification;
- scope, execution profile, budget, rate-limit, concurrency та audit checks для
  активних інструментів.

## Найближчі кроки

- додати regression tests для кожної кнопки evidence attachment у UI;
- додати зрозумілий preview прикріплених даних перед відправкою;
- показувати provider latency, retry та розмір context у chat status;
- додати експорт conversation разом із прикріпленими evidence;
- покращити provider contract tests для native Anthropic API та streaming;
- додати fixtures для великих binary і SPA responses без реальних зовнішніх
  запитів.

## Не планується без окремого обґрунтування

- autonomous observe → plan → execute loops;
- durable background missions and lifecycle event storage;
- HTML reports, phase gates і automatic follow-up execution;
- shell, arbitrary filesystem, arbitrary HTTP або post-compromise execution;
- автоматична передача всього workspace кожним повідомленням;
- приховане masking/redaction context.
