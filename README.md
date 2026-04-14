# Rishta — Telegram bot

Первая цифровая платформа для сватовства в Узбекистане.
Telegram-бот на aiogram 3 + PostgreSQL, деплой на Railway.

## Стек

- Python 3.11
- aiogram 3.15
- SQLAlchemy 2 (async) + asyncpg
- APScheduler (напоминания 30 дней, feedback 14 дней, дневной отчёт 20:00)
- Railway (hosting + Postgres)

## Структура

```
bot/
  __main__.py         — точка входа, сборка Dispatcher
  config.py           — загрузка env
  states.py           — FSM состояния
  texts.py            — ru/uz тексты всех 20 шагов
  db/
    engine.py         — async engine + session factory
    models.py         — User, Profile, Requirement, Favorite,
                        ContactRequest, Payment, Complaint,
                        Meeting, Feedback
  middlewares/db.py   — прокидывает AsyncSession в хендлеры
  keyboards/inline.py — все inline-клавиатуры (ru/uz)
  handlers/
    start.py          — Шаг 0 (согласие) + Шаг 1 (язык)
    menu.py           — Шаг 2 (главное меню), Шаг 3 (о платформе), Шаг 4 (мои заявки)
    questionnaire.py  — Шаг 5А/5Б, все 23 вопроса (+ 10Б, 20А, 21, 22, 23)
    tariff.py         — Шаг 6 (VIP/бесплатно) + Шаг 7 (требования)
    moderator.py      — Шаг 9 (модерация), Шаг 14 (оплата), Шаг 19 (жалобы)
    search.py         — Шаг 10 (поиск) + Шаг 11 (нотификация семье)
    payment.py        — Шаг 13–15 (оплата + выдача контактов)
    meeting.py        — Шаг 16 (планировщик встреч)
    feedback.py       — Шаг 17 (14-дневный follow-up)
    complaint.py      — Шаг 19 (жалобы)
  services/scheduler.py — Шаг 18, 17, 20 (APScheduler задачи)
  utils/helpers.py    — генерация display_id (#ДД-2026-00023)
```

## Локальный запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # заполнить BOT_TOKEN, DATABASE_URL, MODERATOR_CHAT_ID
python -m bot
```

## Деплой на Railway

1. Создать проект на https://railway.app
2. Добавить сервис **PostgreSQL** — скопировать `DATABASE_URL`
   (заменить `postgresql://` на `postgresql+asyncpg://`)
3. Добавить сервис из GitHub репозитория (этот репо)
4. В Variables задать:
   - `BOT_TOKEN` — токен от @BotFather
   - `DATABASE_URL` — см. шаг 2
   - `MODERATOR_CHAT_ID` — id чата модератора для уведомлений
   - `MODERATOR_TASHKENT`, `MODERATOR_USA`, `MODERATOR_CIS`, `MODERATOR_EUROPE`
   - (опц.) `PAYME_TOKEN`, `CLICK_TOKEN`, `STRIPE_SECRET_KEY`
5. Railway сам прочитает `Procfile` (`worker: python -m bot`)
   и запустит long polling

Таблицы создаются автоматически при старте (`Base.metadata.create_all`).

## Переменные окружения

| Переменная           | Назначение                                       |
|----------------------|--------------------------------------------------|
| `BOT_TOKEN`          | Токен бота                                       |
| `DATABASE_URL`       | `postgresql+asyncpg://user:pass@host:port/db`    |
| `MODERATOR_CHAT_ID`  | Chat id для уведомлений модератору               |
| `MODERATOR_TASHKENT` | @username модератора по UZ                       |
| `MODERATOR_USA`      | @username модератора по US                       |
| `MODERATOR_CIS`      | @username модератора по СНГ                      |
| `MODERATOR_EUROPE`   | @username модератора по Европе                   |
| `PAYME_TOKEN`        | Payme merchant token (опционально)               |
| `CLICK_TOKEN`        | Click merchant token (опционально)               |
| `STRIPE_SECRET_KEY`  | Stripe secret key (опционально)                  |

## Покрытие ТЗ (шаги 0–20)

- [x] Шаг 0  — согласие 18+ и спецкатегорий
- [x] Шаг 1  — выбор языка ru/uz
- [x] Шаг 2  — главное меню
- [x] Шаг 3  — о платформе
- [x] Шаг 4  — мои заявки
- [x] Шаг 5А — анкета сына (23 вопроса)
- [x] Шаг 5Б — анкета дочери (23 вопроса)
- [x] Шаг 6  — VIP / обычная
- [x] Шаг 7  — требования к кандидату
- [x] Шаг 8  — подтверждение, выдача display_id
- [x] Шаг 9  — модерация (публикация/отклонение)
- [x] Шаг 10 — поиск (VIP first, сортировка по совпадению)
- [x] Шаг 11 — нотификация семье при «Узнать подробнее»
- [x] Шаг 12 — связь с модератором по региону
- [x] Шаг 13 — оплата (Payme / Click / Uzum / карта / Stripe)
- [x] Шаг 14 — уведомление модератору
- [x] Шаг 15 — выдача контактов и адреса
- [x] Шаг 16 — планировщик встречи
- [x] Шаг 17 — follow-up через 14 дней
- [x] Шаг 18 — напоминание через 30 дней
- [x] Шаг 19 — жалобы
- [x] Шаг 20 — дневной отчёт модератору 20:00
