"""Topic banks for different IT positions.

Contains structured topics with difficulty levels for conducting
targeted technical interviews based on candidate's position and grade.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class Topic:
    """Interview topic with difficulty levels."""
    name: str
    junior_questions: tuple[str, ...]
    middle_questions: tuple[str, ...]
    senior_questions: tuple[str, ...]
    
    def get_questions(self, grade: str, difficulty: int) -> list[str]:
        """Get questions appropriate for grade and difficulty."""
        grade_lower = grade.lower()
        
        if "senior" in grade_lower or difficulty >= 4:
            return list(self.senior_questions)
        elif "middle" in grade_lower or difficulty >= 2:
            return list(self.middle_questions)
        return list(self.junior_questions)


# ============== BACKEND DEVELOPER ==============
BACKEND_TOPICS: Final[dict[str, Topic]] = {
    "python_basics": Topic(
        name="Python основы",
        junior_questions=(
            "Какие типы данных есть в Python?",
            "Чем отличается list от tuple?",
            "Что такое словарь (dict) и когда его использовать?",
        ),
        middle_questions=(
            "Как работает GIL в Python и как он влияет на многопоточность?",
            "Объясни разницу между deepcopy и shallow copy.",
            "Как устроены генераторы и когда их использовать?",
        ),
        senior_questions=(
            "Как бы ты оптимизировал память в приложении с большим объёмом данных?",
            "Опиши паттерны конкурентности в Python: asyncio vs threading vs multiprocessing.",
            "Как реализовать custom descriptor и когда это нужно?",
        ),
    ),
    "databases": Topic(
        name="Базы данных",
        junior_questions=(
            "Что такое SQL и NoSQL базы данных? В чём разница?",
            "Что такое первичный ключ (PRIMARY KEY)?",
            "Как работает JOIN? Приведи пример.",
        ),
        middle_questions=(
            "Объясни уровни изоляции транзакций.",
            "Как оптимизировать медленный SQL-запрос?",
            "Когда использовать индексы и какие бывают типы?",
        ),
        senior_questions=(
            "Как бы ты спроектировал схему для high-load системы с 1M RPS?",
            "Опиши стратегии шардинга и репликации.",
            "Как реализовать eventual consistency в распределённой системе?",
        ),
    ),
    "api_design": Topic(
        name="API Design",
        junior_questions=(
            "Что такое REST API? Какие HTTP-методы знаешь?",
            "Что такое JSON и для чего он используется?",
            "Что означают коды ответа 200, 404, 500?",
        ),
        middle_questions=(
            "Чем REST отличается от GraphQL?",
            "Как версионировать API?",
            "Как реализовать пагинацию в API?",
        ),
        senior_questions=(
            "Как спроектировать API для микросервисной архитектуры?",
            "Опиши стратегии backward compatibility.",
            "Как реализовать rate limiting и authentication в масштабе?",
        ),
    ),
    "testing": Topic(
        name="Тестирование",
        junior_questions=(
            "Что такое unit-тесты?",
            "Знаком ли с pytest?",
            "Что такое assert?",
        ),
        middle_questions=(
            "Чем unit-тесты отличаются от интеграционных?",
            "Что такое mock и fixture?",
            "Как писать тесты для асинхронного кода?",
        ),
        senior_questions=(
            "Как выстроить стратегию тестирования для микросервисов?",
            "Что такое contract testing?",
            "Как обеспечить >90% coverage без ущерба скорости разработки?",
        ),
    ),
    "docker_k8s": Topic(
        name="Docker и Kubernetes",
        junior_questions=(
            "Что такое Docker и зачем он нужен?",
            "Что такое Docker-образ и контейнер?",
            "Как запустить контейнер?",
        ),
        middle_questions=(
            "Как оптимизировать размер Docker-образа?",
            "Что такое docker-compose?",
            "Что такое Kubernetes и зачем он нужен?",
        ),
        senior_questions=(
            "Как настроить CI/CD pipeline с Docker и K8s?",
            "Как организовать blue-green deployment?",
            "Как отлаживать проблемы в production K8s кластере?",
        ),
    ),
}

# ============== ML ENGINEER ==============
ML_TOPICS: Final[dict[str, Topic]] = {
    "ml_basics": Topic(
        name="ML основы",
        junior_questions=(
            "Чем отличается supervised от unsupervised learning?",
            "Что такое переобучение (overfitting)?",
            "Какие метрики классификации знаешь?",
        ),
        middle_questions=(
            "Как бороться с переобучением?",
            "Объясни bias-variance tradeoff.",
            "Когда использовать precision vs recall?",
        ),
        senior_questions=(
            "Как выстроить MLOps pipeline для production?",
            "Как мониторить data drift и model decay?",
            "Расскажи про A/B тестирование ML моделей.",
        ),
    ),
    "deep_learning": Topic(
        name="Deep Learning",
        junior_questions=(
            "Что такое нейронная сеть?",
            "Что такое функция активации?",
            "Зачем нужен backpropagation?",
        ),
        middle_questions=(
            "Чем CNN отличается от RNN?",
            "Что такое batch normalization?",
            "Как работает dropout?",
        ),
        senior_questions=(
            "Как оптимизировать inference time модели?",
            "Расскажи про архитектуру Transformer.",
            "Как реализовать distributed training?",
        ),
    ),
    "feature_engineering": Topic(
        name="Feature Engineering",
        junior_questions=(
            "Что такое feature engineering?",
            "Как обрабатывать пропущенные значения?",
            "Что такое one-hot encoding?",
        ),
        middle_questions=(
            "Как работать с категориальными признаками высокой кардинальности?",
            "Что такое feature selection и какие методы знаешь?",
            "Как обрабатывать временные ряды для ML?",
        ),
        senior_questions=(
            "Как автоматизировать feature engineering?",
            "Расскажи про embeddings для категориальных признаков.",
            "Как строить features для real-time inference?",
        ),
    ),
    "frameworks": Topic(
        name="ML Frameworks",
        junior_questions=(
            "С какими ML-фреймворками работал?",
            "Что такое scikit-learn?",
            "Чем PyTorch отличается от TensorFlow?",
        ),
        middle_questions=(
            "Как организовать эксперименты в ML проекте?",
            "Что такое MLflow/Weights&Biases?",
            "Как сохранять и версионировать модели?",
        ),
        senior_questions=(
            "Как выбрать стек для ML в production?",
            "Опиши архитектуру ML платформы.",
            "Как обеспечить reproducibility экспериментов?",
        ),
    ),
}

# ============== FRONTEND DEVELOPER ==============
FRONTEND_TOPICS: Final[dict[str, Topic]] = {
    "javascript": Topic(
        name="JavaScript",
        junior_questions=(
            "Чем var отличается от let и const?",
            "Что такое замыкание (closure)?",
            "Как работает this в JavaScript?",
        ),
        middle_questions=(
            "Объясни Event Loop.",
            "Что такое Promise и async/await?",
            "Как работает прототипное наследование?",
        ),
        senior_questions=(
            "Как оптимизировать производительность JS-приложения?",
            "Что такое WeakMap/WeakSet и когда их использовать?",
            "Как реализовать custom итератор?",
        ),
    ),
    "react": Topic(
        name="React",
        junior_questions=(
            "Что такое компонент в React?",
            "Чем props отличается от state?",
            "Что такое JSX?",
        ),
        middle_questions=(
            "Как работают React hooks?",
            "Когда использовать useMemo и useCallback?",
            "Что такое Virtual DOM?",
        ),
        senior_questions=(
            "Как оптимизировать рендеринг большого списка?",
            "Опиши паттерны управления состоянием.",
            "Как реализовать Server-Side Rendering?",
        ),
    ),
    "css": Topic(
        name="CSS",
        junior_questions=(
            "Что такое flexbox?",
            "Чем class отличается от id в CSS?",
            "Что такое box model?",
        ),
        middle_questions=(
            "Чем Flexbox отличается от Grid?",
            "Как работает CSS specificity?",
            "Что такое CSS-in-JS?",
        ),
        senior_questions=(
            "Как организовать CSS архитектуру большого проекта?",
            "Как оптимизировать Critical CSS?",
            "Расскажи про CSS Houdini.",
        ),
    ),
}

# ============== DEVOPS ==============
DEVOPS_TOPICS: Final[dict[str, Topic]] = {
    "linux": Topic(
        name="Linux",
        junior_questions=(
            "Какие основные команды Linux знаешь?",
            "Что такое процесс и как его посмотреть?",
            "Что такое права доступа (chmod)?",
        ),
        middle_questions=(
            "Как настроить systemd сервис?",
            "Что такое cgroups и namespaces?",
            "Как отлаживать проблемы с производительностью?",
        ),
        senior_questions=(
            "Как настроить hardening Linux-сервера?",
            "Как работает Linux kernel scheduling?",
            "Как оптимизировать сетевой стек?",
        ),
    ),
    "ci_cd": Topic(
        name="CI/CD",
        junior_questions=(
            "Что такое CI/CD?",
            "Какие CI/CD системы знаешь?",
            "Что такое pipeline?",
        ),
        middle_questions=(
            "Как настроить multi-stage pipeline?",
            "Что такое GitOps?",
            "Как управлять секретами в CI/CD?",
        ),
        senior_questions=(
            "Как построить CI/CD для микросервисов?",
            "Как реализовать canary deployment?",
            "Как обеспечить security в CI/CD?",
        ),
    ),
    "monitoring": Topic(
        name="Мониторинг",
        junior_questions=(
            "Зачем нужен мониторинг?",
            "Какие инструменты мониторинга знаешь?",
            "Что такое логи и метрики?",
        ),
        middle_questions=(
            "Как настроить alerting?",
            "Что такое Prometheus и Grafana?",
            "Как собирать и анализировать логи?",
        ),
        senior_questions=(
            "Как построить observability платформу?",
            "Что такое SLI/SLO/SLA?",
            "Как реализовать distributed tracing?",
        ),
    ),
}

# ============== DATA ANALYST ==============
DATA_ANALYST_TOPICS: Final[dict[str, Topic]] = {
    "sql": Topic(
        name="SQL",
        junior_questions=(
            "Что такое SELECT, WHERE, ORDER BY?",
            "Как работает GROUP BY?",
            "Что такое агрегатные функции?",
        ),
        middle_questions=(
            "Объясни разницу между INNER/LEFT/RIGHT JOIN.",
            "Как работают оконные функции?",
            "Что такое CTE (Common Table Expression)?",
        ),
        senior_questions=(
            "Как оптимизировать сложные аналитические запросы?",
            "Как работать с иерархическими данными?",
            "Как строить эффективные витрины данных?",
        ),
    ),
    "statistics": Topic(
        name="Статистика",
        junior_questions=(
            "Что такое среднее, медиана, мода?",
            "Что такое корреляция?",
            "Что такое нормальное распределение?",
        ),
        middle_questions=(
            "Что такое A/B тест и как его провести?",
            "Как проверить статистическую значимость?",
            "Что такое p-value?",
        ),
        senior_questions=(
            "Как спланировать эксперимент с учётом power analysis?",
            "Какие методы коррекции множественных сравнений знаешь?",
            "Как работать с байесовской статистикой?",
        ),
    ),
    "visualization": Topic(
        name="Визуализация",
        junior_questions=(
            "Какие типы графиков знаешь?",
            "Когда использовать bar chart vs line chart?",
            "Какие инструменты визуализации использовал?",
        ),
        middle_questions=(
            "Как выбрать правильный тип визуализации?",
            "Что такое dashboard best practices?",
            "Как сделать визуализацию для non-technical аудитории?",
        ),
        senior_questions=(
            "Как построить real-time dashboard?",
            "Как визуализировать сложные многомерные данные?",
            "Как storytelling через данные?",
        ),
    ),
}

# Position to topics mapping
POSITION_TOPICS: Final[dict[str, dict[str, Topic]]] = {
    # Backend variations
    "backend": BACKEND_TOPICS,
    "backend developer": BACKEND_TOPICS,
    "python developer": BACKEND_TOPICS,
    "python разработчик": BACKEND_TOPICS,
    "бэкенд разработчик": BACKEND_TOPICS,
    "бэкенд": BACKEND_TOPICS,
    
    # ML variations
    "ml": ML_TOPICS,
    "ml engineer": ML_TOPICS,
    "machine learning": ML_TOPICS,
    "data scientist": ML_TOPICS,
    "ml инженер": ML_TOPICS,
    
    # Frontend variations
    "frontend": FRONTEND_TOPICS,
    "frontend developer": FRONTEND_TOPICS,
    "фронтенд разработчик": FRONTEND_TOPICS,
    "react developer": FRONTEND_TOPICS,
    
    # DevOps variations
    "devops": DEVOPS_TOPICS,
    "devops engineer": DEVOPS_TOPICS,
    "sre": DEVOPS_TOPICS,
    "infrastructure": DEVOPS_TOPICS,
    
    # Data Analyst variations
    "data analyst": DATA_ANALYST_TOPICS,
    "аналитик данных": DATA_ANALYST_TOPICS,
    "bi analyst": DATA_ANALYST_TOPICS,
}


SUPPORTED_POSITIONS = (
    "Backend Developer", "Frontend Developer", "ML Engineer",
    "DevOps", "Data Analyst", "QA", "Fullstack",
)


def normalize_position(position: str) -> str | None:
    """Normalize position to supported IT role. Returns None if not IT-related."""
    pos_lower = position.lower().strip()
    
    if pos_lower in POSITION_TOPICS:
        for supported in SUPPORTED_POSITIONS:
            if supported.lower() in pos_lower or pos_lower in supported.lower():
                return supported
    
    keywords = {
        "backend": "Backend Developer",
        "бэкенд": "Backend Developer",
        "бекенд": "Backend Developer",
        "бэк": "Backend Developer",
        "python": "Backend Developer",
        "java": "Backend Developer",
        "go разработ": "Backend Developer",
        "golang": "Backend Developer",
        "frontend": "Frontend Developer",
        "фронтенд": "Frontend Developer",
        "фронт": "Frontend Developer",
        "react": "Frontend Developer",
        "vue": "Frontend Developer",
        "angular": "Frontend Developer",
        "ml": "ML Engineer",
        "мл": "ML Engineer",
        "machine learning": "ML Engineer",
        "mle": "ML Engineer",
        "мл инженер": "ML Engineer",
        "мл-инженер": "ML Engineer",
        "data scien": "ML Engineer",
        "дата саентист": "ML Engineer",
        "devops": "DevOps",
        "девопс": "DevOps",
        "sre": "DevOps",
        "инфра": "DevOps",
        "analyst": "Data Analyst",
        "аналитик": "Data Analyst",
        "bi": "Data Analyst",
        "qa": "Backend Developer",
        "тестир": "Backend Developer",
        "тестировщик": "Backend Developer",
        "fullstack": "Backend Developer",
        "full stack": "Backend Developer",
        "фулстек": "Backend Developer",
        "фуллстек": "Backend Developer",
        "full-stack": "Backend Developer",
    }
    
    for keyword, role in keywords.items():
        if keyword in pos_lower:
            return role
    
    return None


def get_topics_for_position(position: str) -> dict[str, Topic]:
    """Get topic bank for a position, fallback to backend."""
    position_lower = position.lower().strip()
    
    # Direct match
    if position_lower in POSITION_TOPICS:
        return POSITION_TOPICS[position_lower]
    
    # Partial match
    for key, topics in POSITION_TOPICS.items():
        if key in position_lower or position_lower in key:
            return topics
    
    # Default to backend (most common)
    return BACKEND_TOPICS


def get_random_topic(position: str, covered: list[str], skipped: list[str]) -> Topic | None:
    """Get a random uncovered topic for the position."""
    import random
    
    topics = get_topics_for_position(position)
    available = [
        t for name, t in topics.items() 
        if t.name not in covered and t.name not in skipped
    ]
    
    return random.choice(available) if available else None
