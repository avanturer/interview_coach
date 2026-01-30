# Interview Coach

Система для технических интервью на базе нескольких AI-агентов. Проводит собеседование, анализирует ответы и выдаёт структурированный фидбэк.

## Что умеет

- **7 позиций с отдельными банками тем** — Backend, Frontend, ML, DevOps, Data Analyst, QA, Fullstack. У каждой свои вопросы (junior/middle/senior), без подмены на Backend
- **Адаптивная сложность** — вопросы усложняются или упрощаются в зависимости от качества ответов
- **Детекция галлюцинаций** — если кандидат уверенно несёт чушь (типа «Python 4.0 уберёт циклы»), Observer помечает `is_hallucination` / `is_confident_nonsense`
- **Встречные вопросы** — если кандидат спрашивает про испытательный срок или стек, интервьюер отвечает
- **Семантическое завершение** — понимает «давай фидбэк», «хватит», «give me feedback» без жёсткого списка слов
- **Английский** — по запросу кандидата можно переключить язык интервью
- **Антиспам** — при `MAX_SPAM_COUNT` уклонений или троллинга интервью завершается досрочно

## Чем выделяется

**Три агента, не два.** Evaluator вынесен отдельно — он не склеен с Observer. В конце анализирует весь диалог целиком и собирает фидбэк: грейд, пробелы с правильными ответами, roadmap с ресурсами.

**Пробелы с правильными ответами.** Не просто «не знает SQL» — Evaluator для каждого `KnowledgeGap` даёт `correct_answer`: что именно нужно было ответить. Roadmap — с приоритетами и ресурсами для обучения.

**Soft skills по ходу.** Observer отслеживает clarity, honesty, engagement на каждом ответе; Evaluator сводит в итоговые оценки (1–10) и red_flags.

**Не переспрашивает.** Система запоминает `candidate_mentioned` — что кандидат уже рассказал о себе (проекты, курсы, стек). Interviewer получает это в промпте и не дёргает «расскажи про опыт» по кругу.

**Честная валидация позиции.** Ввели «Uborshik» — попросит ввести заново. Не подменяет тихо на Backend.

**Лог под сдачу.** Команда `run_scenario ... interview_log_1.json` выдаёт файл в формате инструкции 1:1: `participant_name`, `turns`, `final_feedback` строкой. Internal_thoughts в формате `[Observer]: мысль\n[Interviewer]: мысль` — как требуют.

**Grade mismatch.** Observer считает `overqualified_signals` / `underqualified_signals`. Evaluator выставляет `grade_match: match | overqualified | underqualified`. Если Junior отвечает как Middle — в фидбэке будет overqualified.

**Разные температуры агентов.** Interviewer — 0.7 (креативность), Observer — 0.3 (точность анализа), Evaluator — 0.5 (баланс). Настраивается в `.env`.

## Как устроено

Три агента, оркестрация через LangGraph:

1. **Interviewer** — задаёт вопросы, реагирует на ответы, даёт подсказки
2. **Observer** — анализирует каждый ответ «за кулисами»: качество, галлюцинации, уклонения, инструкции для интервьюера
3. **Evaluator** — в конце собирает всё в фидбэк: грейд, рекомендация Hire/No Hire, пробелы с правильными ответами, roadmap

Observer не общается с кандидатом напрямую — только пишет инструкции Interviewer. В логах видно эти «внутренние мысли».

## Установка

Нужен **Python 3.10 или выше** — на 3.9 зависимости не встанут.

**Linux / macOS:**
```bash
cd interview_coach
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

**Windows (cmd):**
```cmd
cd interview_coach
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

**Windows (PowerShell):**
```powershell
cd interview_coach
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

В `.env` прописать `MISTRAL_API_KEY` — ключ бесплатно берётся на https://console.mistral.ai/

## Запуск

Интерактивно:
```bash
python -m src.main interview
```

С параметрами (без вопросов):
```bash
python -m src.main interview -n "Иван" -p "Backend Developer" -g "Junior" -e "1 год"
```

Из файла сценария (для прогона тестовых сценариев):
```bash
python run_scenario.py scenarios/example_scenario.txt
```

Файл для сдачи в формате инструкции:
```bash
python run_scenario.py scenarios/example_scenario.txt interview_log_1.json --participant "Иван Иванович Иванов"
```
Скрипт спросит ФИО, если `--participant` не указан. **participant_name в JSON — твоё реальное ФИО для жюри**, не персонаж сценария (Алекс). Модель обращается к герою сценария, но в логе — твоё имя.

## Пример работы

```
Интервьюер: Привет! Расскажи о себе и опыте.
Кандидат: Я Алекс, Junior Backend. Знаю Python, SQL и Git.

Интервьюер: Какие структуры данных в Python используешь?
Кандидат: Переменные — это контейнеры для данных, x = 5.

Интервьюер: А списки, словари?
Кандидат: Честно, читал что в Python 4.0 циклы for уберут и заменят на нейронные связи.

Интервьюер: Давай вернёмся к текущей версии. Какие структуры знаешь?
Кандидат: Слушайте, а какие задачи будут на испытательном сроке? Микросервисы используете?

Интервьюер: На испытательном — backend-задачи, API. Да, микросервисы. Теперь про SQL...
Кандидат: Стоп игра. Давай фидбэк.

Интервьюер: Спасибо! Вот фидбэк: Junior, No Hire, 80%. Пробелы: структуры данных, SQL. Roadmap: основы Python, SQL...
```

В логе при этом видно, как Observer помечал галлюцинацию, уклонение, запрос на завершение.

## Логи

При интерактивном запуске — `logs/interview_{имя}_{дата}.json` (полный формат).

При `run_scenario ... interview_log_N.json` — файл в формате инструкции: только `participant_name`, `turns`, `final_feedback` строкой. Его и загружать в форму. **participant_name** — твоё ФИО (для сопоставления с базой студентов), не имя персонажа сценария.

## Конфиг

В `.env`:
- `MISTRAL_API_KEY` — обязательно
- `LLM_PROVIDER` — mistral или openai
- `MAX_TURNS` — лимит вопросов (по умолчанию 10)
- `CONTEXT_WINDOW_SIZE` — сколько последних реплик в контексте (по умолчанию 5)
- `MAX_SPAM_COUNT`, `MAX_EVASION_COUNT` — при каком количестве завершать досрочно
- `TEMP_INTERVIEWER`, `TEMP_OBSERVER`, `TEMP_EVALUATOR` — температуры LLM для агентов

## Тесты

```bash
pip install pytest
pytest tests/ -v
```

## Структура проекта

```
src/
├── main.py           — CLI
├── config.py         — настройки
├── agents/           — Interviewer, Observer, Evaluator
├── graph/            — LangGraph workflow
├── models/           — состояние, фидбэк
├── prompts/          — промпты агентов
├── topics.py         — банки вопросов по позициям
└── utils/            — логгер
```

## Итог

ТЗ закрыто: 3 агента, скрытая рефлексия в логах (`internal_thoughts`), контекстное окно, адаптивная сложность, устойчивость к галлюцинациям и off-topic. Отдельный Evaluator, семантический стоп-интент, английский по запросу, честная валидация позиций, лог в формате инструкции без ручной правки. Пробелы с правильными ответами, soft skills по ходу, grade mismatch, антиспам, разные температуры агентов.

Оркин Родион, MegaSchool
