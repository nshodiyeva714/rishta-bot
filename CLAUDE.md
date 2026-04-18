# Rishta — Telegram матчмейкинг-бот (ru/uz)

Этот файл — краткая выжимка контекста для всех последующих сессий Claude.
Новая сессия читает его автоматически при старте в этом репо.

---

## Проект

- **Что:** двуязычный (русский / узбекский) Telegram-бот для сватовства
  между семьями. Анкеты сыновей и дочерей, фильтры поиска, избранное,
  VIP-подписки, передача контактов через оператора с оплатой.
- **Стек:** Python 3.11, aiogram 3, SQLAlchemy async, PostgreSQL
- **Хостинг:** Railway, auto-deploy по `git push origin main`
- **GitHub:** https://github.com/nshodiyeva714/rishta-bot
- **Moderators:** Ташкент (`@rishta_manager_tashkent`, ID `8400995899`)
  и Самарканд (`@rishta_manager_samarkand`, ID `6235004229`)

---

## Деплой

```bash
git add -A
git commit -m "..."
git push origin main   # Railway сам подхватит
```

**Пустой коммит = force redeploy:**
```bash
git commit --allow-empty -m "Force redeploy"
git push origin main
```

Миграции БД — идемпотентные `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`
в `bot/__main__.py` (секция `on_startup`). Накатываются автоматически
при запуске бота после деплоя.

`railway run ...` и `railway logs ...` из Claude-сессии **не работают**
(требуют интерактивного OAuth). Логи смотрит пользователь сам через
Railway Web UI или свой терминал после `railway login`.

---

## Критические грабли (не наступать по второму разу)

### 1. `RequestStatus.APPROVED` НЕ СУЩЕСТВУЕТ
В `bot/db/models.py` enum `RequestStatus` содержит только:
```
PENDING / TALKING / CONTACT_GIVEN / REJECTED
```
Для «передан» используй **`CONTACT_GIVEN`**, для «отклонён» — `REJECTED`.
ТЗ и подсказки иногда пишут `APPROVED` — это ошибка, заменяй.

### 2. `User.username` отсутствует в модели
`class User` содержит только: `id`, `language`, `consent_general`,
`consent_special`, `seen_favorites_count`, `created_at`, `updated_at`.

**Никогда не делай** `user.username` через `session.get(User, id)` —
получишь `AttributeError` → молча проглотится в `try/except` →
bug будет незаметен.

Username можно брать **только** из `callback.from_user.username` /
`message.from_user.username` в момент события (Telegram передаёт его
в update).

Если нужен username в `/requests` и подобных экранах, где есть только
user_id — показывай `f"ID:{user_id}"`.

### 3. Python 3.9 локально vs 3.11 на Railway
Локальная машина пользователя — Python 3.9.6.
Railway (`runtime.txt`: `python-3.11.9`) — 3.11.

`bot/keyboards/inline.py` использует синтаксис PEP 604 (`dict | None`
в type hints), который в рантайме работает только на 3.10+.

**Что это значит:**
- `python3 -m py_compile` работает на обоих — проверяет только AST
- `python3 -c "import bot.handlers.xxx"` **падает локально** с
  `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'`
  — это **НЕ баг проекта**, это ограничение локальной версии Python
- На Railway всё поднимается нормально

**Не тратить время** на этот import-тест локально. Вместо него:
- `py_compile` для синтаксиса
- Railway logs для реальной проверки

### 4. Все FSM-States должны быть импортированы
Типовой баг: handler использует `SomeStates.xxx` но сам класс
не импортирован → `NameError` в рантайме. `py_compile` не ловит.

Проверяй перед коммитом:
```bash
grep -n "ContactStates\|SomeStates" bot/handlers/xxx.py
grep -n "from bot.states import" bot/handlers/xxx.py
```

### 5. `railway` CLI не авторизован в Claude-сессии
Не пытайся `railway login`, `railway run`, `railway logs` — упадут
с `Unauthorized`. Всегда предлагай пользователю сделать это в своём
терминале.

### 6. `.claude/` в `.gitignore`
Папка Claude-worktrees исключена из репо. Не пытайся добавить её
`git add -A` — будет warning про embedded git repository.

---

## Архитектура handlers

Все handlers зарегистрированы в `bot/__main__.py` в этом порядке
(важен — aiogram ищет сверху вниз, `fallback` последний):

```
start → menu → questionnaire → questionnaire_ext → tariff →
moderator → search → payment → meeting → feedback → complaint → fallback
```

### Ключевые файлы

| Файл | Что делает | ~размер |
|---|---|---|
| `bot/handlers/start.py` | /start, выбор языка, 24h-напоминание | 200 строк |
| `bot/handlers/menu.py` | Главное меню, счётчик новых лайков | 800 строк |
| `bot/handlers/questionnaire.py` | Этап 1 анкеты (имя → фото) | 1200 строк |
| `bot/handlers/questionnaire_ext.py` | Этап 2 (семья, жильё, контакты) | 1000 строк |
| `bot/handlers/tariff.py` | Выбор тарифа, VIP-сроки, требования | 800 строк |
| `bot/handlers/search.py` | Поиск, фильтры, favorites, get_contact | ~2050 строк |
| `bot/handlers/moderator.py` | /ankety /stats /find /requests, VIP, оплата | ~2000 строк |
| `bot/handlers/payment.py` | Оплата VIP | 400 строк |
| `bot/handlers/meeting.py` | Встречи | 200 строк |
| `bot/handlers/feedback.py` | Обратная связь после свадьбы | 200 строк |
| `bot/handlers/complaint.py` | Жалобы на анкеты | 150 строк |
| `bot/handlers/fallback.py` | Необработанные callback/message | 60 строк |

### DB модели (`bot/db/models.py`)

9 таблиц:
- `User` — Telegram id + язык + согласие + seen_favorites_count
- `Profile` — анкета (59 колонок: имя, возраст, город, фото, etc.)
- `Requirement` — требования к кандидату
- `Favorite` — избранное
- `ContactRequest` — запрос контакта с `display_id` (ЗАП-NNN)
- `Payment` — оплата (в тиинах: 1 сум = 100 тиин)
- `Complaint` — жалоба
- `Meeting` — встреча семей
- `Feedback` — обратная связь

Все enum-колонки — через SQLAlchemy Enum. **Не передавай** строки —
используй Python enum объекты (`Education.HIGHER`, не `"higher"`).
Исключение — `occupation` (это `Text`, не Enum).

### FSM States (`bot/states.py`)

- `ConsentStates`, `QuestionnaireStates`, `RequirementStates`,
  `SearchStates`, `PaymentStates`, `MeetingStates`, `FeedbackStates`,
  `FeedbackSuggestionStates`, `ModeratorContactStates`,
  `ModeratorReplyStates`, `ModeratorEditStates`, `TariffStates`,
  `EditProfileStates`, `ContactStates`
- `ContactStates` (важный): `waiting_screenshot`, `waiting_question`,
  `waiting_reply`

---

## Текущее состояние фич (на момент коммита 7792fa1)

### 1. Поиск

- Показ по 1 анкете с двусторонней навигацией ⬅️ / ➡️
- Снимок списка IDs хранится в FSM (`search_results`, `current_index`)
- Живые фильтры: возраст (диапазоны + кастом), религиозность,
  образование, семейное положение, дети, проживание (страна → область УЗ),
  национальность
- Сортировка: VIP → vip_expires_at → match_score → published_at
- `Profile.status == PUBLISHED` (PENDING больше не показывается)
- `Profile.user_id != user_id` (свои анкеты не видно)
- Иконки во всех кнопках фильтров и значений анкеты
- Бейджи: ⭐ VIP, 🔥 Популярная (50+ просмотров), 👀 Много просмотров (20+)
- Ритм каждые 5 анкет — мотивирующая фраза
- Тосты на ❤️ / ➡️ / 💔 с вариациями (4 фразы каждая)

### 2. Contact flow (запрос контакта → оплата → передача)

Пользовательская часть (`search.py`):
- `get_contact:` → меню «💬 Задать вопрос / 📤 Запросить контакт»
- `ask_op:` → state `waiting_question` → текст → всем операторам
- `req_contact:` → создаёт `ContactRequest(PENDING)` с `display_id=ЗАП-NNN`
- `send_screenshot:` → state `waiting_screenshot` → photo → всем операторам
- Все callback несут `req_number` как 3-й сегмент

Операторская часть (`moderator.py`):
- `op_reply:` → state `waiting_reply` → текст ответа → пользователю
- `op_send_req:` → реквизиты (`5614 6887 0899 8959`, `SHODIYEVA NASIBA`,
  30 000 сум) + кнопки 📸/💬
- `op_reject:` → раннее отклонение, status = REJECTED
- `confirm_pay:` → передаёт контакт, уведомляет владельца (FYI без кнопок),
  status = CONTACT_GIVEN
- `reject_pay:` → позволяет пользователю retry (статус НЕ меняется)

**Номер запроса:** `ЗАП-001`, `ЗАП-002`... — порядковый счётчик
`SELECT COUNT(*) FROM contact_requests + 1`. Формат `:03d`.

**Цена:** 30 000 сум в `CONTACT_PRICE` в `moderator.py`.

### 3. /requests для модератора

- `/requests` — список активных (PENDING) запросов
- Клик на запрос → детальная карточка с навигацией ⬅️ / ➡️
- `view_req:{id}:{index}` — номер в списке пересчитывается каждый раз
- Кнопки в карточке: 💬 Ответить, 📤 Реквизиты, ❌ Отклонить

### 4. VIP

- `tariff:vip` → `vip_duration_kb` с 6 сроками (7/14/30/90/180/365 дней)
- Региональные цены: UZB (сум), SNG (рубли), USA (доллары)
- Кнопка «🔙 Назад» → `profile:back_to_tariff` → экран выбора тарифа
- `vip_dur:N` → сохраняет `is_vip=True, vip_days=N` → `_show_summary`

### 5. /ankety для модератора

- Подменю с 4 категориями и живыми счётчиками:
  `🆕 На проверке (N) / ✅ Активные (N) / ⏸ На паузе (N) / ❌ Отклонённые (N)`
- 5 анкет на страницу, пагинация
- Клик → полная анкета с `mod_review_kb`:
  ✅ Опубликовать, ❌ Отклонить, 📸 Отклонить фото, ⏸ Пауза/🟢 Активировать,
  ✏️ Редактировать, ⭐ Опубликовать VIP, 💬 Написать пользователю

### 6. Модератор: редактирование анкеты

4 поля: `name`, `character_hobbies`, `ideal_family_life` (как "about"),
`health_notes`. Через `ModeratorEditStates.choosing_field / editing_value`.
Уведомление владельцу после правки.

### 7. /stats для модератора

Показывает: новые пользователи сегодня, анкеты по статусам, sons/daughters,
оплаты сегодня (`Payment.CONFIRMED`, доход из `SUM(amount)/100`), просмотры,
топ-5 городов.

### 8. Прочее

- Уведомления владельцу при 5/10/25/50/100/200/500 просмотрах
- 24ч-напоминание новым пользователям (`asyncio.sleep(86400)`, in-memory dedup,
  не переживает рестарт Railway)
- Счётчик новых лайков при входе в меню (`User.seen_favorites_count`)
- Избранное через ❤️ с авто-переходом к следующей анкете
- `add_favorite` — реакции (4 фразы, ротация)

---

## Moderator-команды (в мерно-меню Telegram)

- `/start` — главное меню
- `/ankety` — анкеты на проверке (подменю)
- `/requests` — активные запросы контакта
- `/find <display_id или @username>` — найти анкету
- `/stats` — детальная статистика

**Debug-команды (только для модераторов, требуют `is_moderator`):**
- `/dbcheck` — диагностика БД (5 шагов, SQL)
- `/testsearch` — прямой SQL-тест поиска

---

## Правила работы

### Коммиты

- Формат сообщения: `Короткая тема` → пустая строка → bullet-points
- Всегда `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`
- **Никогда не** коммить `.claude/worktrees/*` (уже в `.gitignore`)
- **Не** амендить коммиты (`--amend`) — всегда новый коммит
- Ветки: `main` = прод. `feature/payment-flow` = бэкап VIP-оплаты
  (точная копия `main` на момент включения operator-only flow)

### Миграции БД

Добавляешь колонку в `bot/db/models.py` — **обязательно** добавь
`ALTER TABLE ... ADD COLUMN IF NOT EXISTS` в `bot/__main__.py`
перед `logger.info("Database tables ensured")`. SQL руками в
Railway Postgres Query — только как fallback если автомиграция
не отработала.

### Handler-ы

- Все контакт-flow callback-ы несут `req_number` 3-м сегментом
- Парсить через `parts[3] if len(parts) > 3 else "—"` (backward compat)
- `except Exception as _e: logger.debug("ignored: %s", _e)` — для
  не-критичных ошибок (edit_text, send_message заблокированному юзеру)
- `logger.error(...)` — для того, что реально сломалось
- **Перед регистрацией** `F.data.startswith("xxx:")` handler-а:
  убедись, что более специфичные handler-ы (`F.data == "xxx:back"`)
  зарегистрированы **раньше** — aiogram идёт по порядку

### Тексты

- Bilingual RU/UZ через `bot/texts.py` (словарь `T`, функция `t(key, lang, **fmt)`)
- Прямые строки в handler-ах — допустимо если их мало (иконки, short ad-hoc)
- 180 ключей, 100% покрытие обоих языков

### При работе с Enum-полями

```python
# ПРАВИЛЬНО
from bot.db.models import Education
profile.education = Education.HIGHER

# НЕПРАВИЛЬНО (работает не везде — SQLAlchemy конвертит по name, не value)
profile.education = "higher"
```

При чтении:
```python
edu_raw = profile.education.value if profile.education else "—"
```

---

## Seed-скрипт

`scripts/add_test_profiles.py` — создаёт 5 тестовых анкет (3 дочери + 2 сына)
+ технического `User(id=0)`. Идемпотентный (пропускает по `display_id`).

Запуск: `railway run python scripts/add_test_profiles.py`

---

## Ветки GitHub

- `main` — актуальное состояние
- `feature/payment-flow` — чистый backup `main` на момент перехода
  на operator-only flow. Когда вернёте полную VIP-оплату — оттуда
  можно черпать код

---

## Открытые TODO / что можно почистить при случае

- Debug-команды `/dbcheck` и `/testsearch` защищены `is_moderator`,
  но это технический hack. Можно убрать совсем когда стабилизируется
- Dead state `lang = await _lang(state)` в `choose_vip_duration`
  (`tariff.py:83`) — переменная не используется
- Много `except Exception as _e: logger.debug(...)` — не все нужны,
  иногда лучше `logger.error`
- `view_request` показывает `👤 ID:...` и `ID: ...` подряд (дубль)
- Локальный Python 3.9 vs Railway 3.11 — можно добавить
  `from __future__ import annotations` в `inline.py` для совместимости

---

## Быстрый глоссарий

- **ЗАП-NNN** — номер запроса контакта (display_id в ContactRequest)
- **ДД-2026-NNNNN** — display_id анкеты (дочь/сын + год + номер)
- **Operator-only flow** — текущий flow передачи контакта (без PayMe/Click,
  только через модератора с ручной проверкой скриншота)
- **is_guest** — поиск без своей анкеты (гостевой режим)
- **VIP** — платная подписка с приоритетом в поиске
- **display_id** — человеко-читаемый идентификатор (не PK)
