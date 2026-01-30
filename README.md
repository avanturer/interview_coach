# Interview Coach

Система для технических интервью на базе нескольких AI-агентов. Проводит собеседование, анализирует ответы и выдаёт структурированный фидбэк.

## Что умеет

- **7 позиций**: Backend, Frontend, ML Engineer, DevOps, Data Analyst, QA, Fullstack
- **Адаптивная сложность** — вопросы усложняются или упрощаются в зависимости от ответов
- **Детекция галлюцинаций** — если кандидат уверенно несёт чушь (типа «Python 4.0 уберёт циклы»), система это ловит
- **Встречные вопросы** — если кандидат спрашивает про испытательный срок или стек, интервьюер отвечает
- **Семантическое завершение** — понимает «давай фидбэк», «хватит», «give me feedback» без жёсткого списка слов
- **Английский** — по запросу кандидата можно переключить язык интервью

## Как устроено

Три агента работают по цепочке:

1. **Interviewer** — задаёт вопросы, реагирует на ответы, даёт подсказки
2. **Observer** — анализирует каждый ответ «за кулисами»: качество, галлюцинации, уклонения, инструкции для интервьюера
3. **Evaluator** — в конце собирает всё в фидбэк: грейд, рекомендация Hire/No Hire, пробелы с правильными ответами, roadmap

Observer не общается с кандидатом напрямую — он только пишет инструкции Interviewer. В логах видно эти «внутренние мысли».

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
python run_scenario.py scenarios/example_scenario.txt interview_log_1.json
```

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

При `run_scenario ... interview_log_N.json` — файл в формате инструкции: только `participant_name`, `turns`, `final_feedback` строкой. Его и загружать в форму.

## Конфиг

В `.env`:
- `MISTRAL_API_KEY` — обязательно
- `LLM_PROVIDER` — mistral или openai
- `MAX_TURNS` — лимит вопросов (по умолчанию 10)
- `MAX_SPAM_COUNT`, `MAX_EVASION_COUNT` — при каком количестве завершать досрочно

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

Система покрывает требования ТЗ: минимум 2 агента, скрытая рефлексия в логах, контекст, адаптивность, устойчивость к галлюцинациям и off-topic. Добавлен Evaluator для структурированного фидбэка, поддержка английского и семантическое распознавание стоп-интента. Лог для сдачи генерируется в формате инструкции.

Оркин Родион, MegaSchool
