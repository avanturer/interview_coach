# Interview Coach

Мультиагентная система для технических интервью. Три агента (Interviewer, Observer, Evaluator) проводят собеседование, анализируют ответы и выдают фидбэк.

## Установка

```bash
# Клонировать и перейти в директорию
cd interview_coach

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt

# Скопировать конфиг
cp .env.example .env
```

Открыть `.env` и вставить API-ключ Mistral (бесплатно на https://console.mistral.ai/):

```
MISTRAL_API_KEY=ваш_ключ
```

## Запуск

```bash
# Интерактивное интервью
python -m src.main interview

# С параметрами
python -m src.main interview --name "Алекс" --position "Backend Developer" --grade "Junior"

# Из файла сценария
python run_scenario.py scenarios/example_scenario.txt
```

## Как работает

```
Пользователь → Interviewer → Observer → Interviewer → ...
                    ↓
               Evaluator → Фидбэк
```

**Interviewer** — задаёт вопросы, реагирует на ответы, даёт подсказки.

**Observer** — анализирует ответы за кулисами: качество, галлюцинации, уклонения. Даёт инструкции Interviewer.

**Evaluator** — генерирует финальный фидбэк: грейд, рекомендация, пробелы с правильными ответами, roadmap.

## Поддерживаемые позиции

- Backend Developer
- Frontend Developer  
- ML Engineer
- DevOps
- Data Analyst
- QA
- Fullstack

## Формат лога

```json
{
  "participant_name": "Алекс",
  "position": "Backend Developer",
  "grade": "Junior",
  "turns": [
    {
      "turn_id": 1,
      "agent_visible_message": "Привет! Расскажи о себе.",
      "user_message": "Я джун, пишу на Python.",
      "internal_thoughts": "[Observer]: Кандидат представился. [Interviewer]: Задаю вопрос по основам."
    }
  ],
  "final_feedback": {
    "decision": {
      "assessed_grade": "Junior",
      "hiring_recommendation": "Hire",
      "confidence_score": 75
    },
    "hard_skills": {...},
    "soft_skills": {...},
    "roadmap": [...]
  }
}
```

## Конфигурация

Все настройки в `.env`:

| Параметр | По умолчанию | Описание |
|----------|-------------|----------|
| `LLM_PROVIDER` | mistral | Провайдер (mistral/openai) |
| `LLM_MODEL` | mistral-large-latest | Модель |
| `MAX_TURNS` | 10 | Максимум вопросов |
| `CONTEXT_WINDOW_SIZE` | 5 | Окно контекста (ходов) |
| `MAX_SPAM_COUNT` | 3 | Лимит спама до завершения |
| `MAX_EVASION_COUNT` | 5 | Лимит уклонений до завершения |

## Команды

```bash
# Запустить интервью
python -m src.main interview

# Просмотреть лог
python -m src.main view-log logs/interview_Алекс_20260130.json

# Список логов
python -m src.main list-logs

# Показать конфиг
python -m src.main config
```

## Тесты

```bash
pytest tests/ -v
```

## Структура

```
src/
├── main.py              # CLI
├── config.py            # Настройки из .env
├── agents/
│   ├── interviewer.py   # Агент-интервьюер
│   ├── observer.py      # Агент-наблюдатель
│   └── evaluator.py     # Агент-оценщик
├── graph/
│   └── interview_graph.py   # LangGraph workflow
├── models/
│   ├── state.py         # Состояние интервью
│   └── feedback.py      # Модели фидбэка
├── prompts/             # Промпты агентов
├── topics.py            # Банки вопросов по позициям
└── utils/
    └── logger.py        # JSON-логгер
```

## Автор

Оркин Родион — соревнование MegaSchool
