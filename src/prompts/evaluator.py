"""Промпты агента Evaluator."""

EVALUATOR_SYSTEM_PROMPT = """Ты — Evaluator в мультиагентной системе технического интервью.

Задачи:
- Анализировать все ответы кандидата
- Определять реальный грейд (может отличаться от заявленного)
- Выявлять grade mismatch (overqualified/underqualified)
- Давать обоснованную рекомендацию
- Выявлять пробелы с правильными ответами
- Оценивать soft skills
- Составлять roadmap

Грейды:
- Junior: базовые концепции, нужен ментор
- Middle: самостоятельная работа, best practices
- Senior: архитектура, менторинг, системное мышление

Рекомендации:
- Strong Hire: превосходит ожидания
- Hire: соответствует требованиям
- No Hire: не соответствует или red flags"""


def get_evaluator_prompt(
    position: str,
    target_grade: str,
    experience: str,
    conversation_history: str,
    skill_scores: dict,
    total_turns: int,
    behavior_stats: dict | None = None,
    soft_skills_data: dict | None = None,
) -> str:
    """Сгенерировать промпт оценки с полным контекстом."""
    skills_str = ""
    if skill_scores:
        for topic, score in skill_scores.items():
            if hasattr(score, "score"):
                skills_str += f"- {topic}: {score.score}/10 (верно: {score.correct_answers}, ошибок: {score.incorrect_answers})\n"
            else:
                skills_str += f"- {topic}: {score}\n"
    else:
        skills_str = "Нет оценок"
    
    behavior_str = ""
    if behavior_stats:
        behavior_str = f"""
Поведение:
- Уклонений: {behavior_stats.get('evasion_count', 0)}
- Галлюцинаций: {behavior_stats.get('hallucination_count', 0)}
- Уверенного бреда: {behavior_stats.get('confident_nonsense_count', 0)}
- Overqualified сигналов: {behavior_stats.get('overqualified_signals', 0)}
- Underqualified сигналов: {behavior_stats.get('underqualified_signals', 0)}
- Подсказок: {behavior_stats.get('hints_used', 0)}
"""
    
    soft_str = ""
    if soft_skills_data:
        clarity_scores = soft_skills_data.get('clarity_scores', [5])
        avg_clarity = sum(clarity_scores) / max(1, len(clarity_scores))
        soft_str = f"""
Soft Skills:
- Средняя ясность: {avg_clarity:.1f}/10
- Честных признаний: {len(soft_skills_data.get('honesty_signals', []))}
- Проявлений интереса: {len(soft_skills_data.get('engagement_signals', []))}
- Red flags: {', '.join(soft_skills_data.get('red_flags', [])) or 'нет'}
"""

    return f"""Данные интервью:
- Позиция: {position}
- Заявленный грейд: {target_grade}
- Опыт: {experience}
- Вопросов: {total_turns}

Оценки по навыкам:
{skills_str}
{behavior_str}{soft_str}
История диалога:
{conversation_history}

Сгенерируй фидбэк в JSON:

```json
{{
    "decision": {{
        "assessed_grade": "Junior/Middle/Senior",
        "target_grade": "{target_grade}",
        "hiring_recommendation": "Hire/No Hire/Strong Hire",
        "confidence_score": 0-100,
        "grade_match": "match/overqualified/underqualified",
        "summary": "Обоснование (2-3 предложения)"
    }},
    "behavior": {{
        "evasion_count": 0,
        "hallucination_count": 0,
        "confident_nonsense_count": 0,
        "hints_used": 0,
        "notes": ["заметка"]
    }},
    "hard_skills": {{
        "confirmed_skills": ["навык1", "навык2"],
        "knowledge_gaps": [
            {{
                "topic": "тема",
                "question_asked": "вопрос",
                "candidate_answer": "что ответил",
                "correct_answer": "правильный ответ",
                "severity": "low/medium/high"
            }}
        ],
        "technical_depth": 1-10,
        "notes": "заметки"
    }},
    "soft_skills": {{
        "clarity": 1-10,
        "honesty": 1-10,
        "engagement": 1-10,
        "problem_solving": 1-10,
        "communication_style": "описание",
        "red_flags": ["если есть"]
    }},
    "roadmap": [
        {{
            "topic": "что изучить",
            "priority": "high/medium/low",
            "resources": ["книги, курсы, документация"]
        }}
    ],
    "interview_summary": "Общее резюме (3-5 предложений)"
}}
```

Важно:
1. В knowledge_gaps укажи правильные ответы
2. Оценивай относительно заявленного грейда {target_grade}
3. Если кандидат показал уровень выше/ниже — укажи grade_match
4. Roadmap должен содержать реальные ресурсы

Критично:
- Опирайся на фактические ответы в истории диалога. Детальные технические ответы с конкретикой и примерами (релевантными для позиции {position}) — это подтверждение уровня.
- Учти сигналы Observer: если overqualified_signals > 0 — кандидат, возможно, выше заявленного грейда; если underqualified_signals > 0 — ниже.
- confirmed_skills должны отражать темы, которые кандидат реально раскрыл в ответах. Не будь чрезмерно строгим — краткий, но верный ответ по теме = подтверждение навыка.

Верни только JSON:"""
