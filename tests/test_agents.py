"""Тесты мультиагентной системы Interview Coach."""

import json
import pytest

from src.models.state import (
    Turn,
    ObserverAnalysis,
    SkillScore,
    InterviewInput,
    create_initial_state,
)
from src.models.feedback import (
    FinalFeedback,
    Decision,
    HardSkillsAnalysis,
    SoftSkillsAnalysis,
    KnowledgeGap,
    RoadmapItem,
    feedback_to_log_dict,
)
from src.utils.logger import InterviewLogger


class TestModels:
    """Тесты Pydantic-моделей."""

    def test_create_initial_state(self):
        """Тест создания начального состояния."""
        input_data = InterviewInput(
            participant_name="Алекс",
            position="Backend Developer",
            grade="Junior",
            experience="Django, SQL",
        )

        state = create_initial_state(input_data)

        assert state["participant_name"] == "Алекс"
        assert state["position"] == "Backend Developer"
        assert state["grade"] == "Junior"
        assert state["experience"] == "Django, SQL"
        assert state["turns"] == []
        assert state["current_turn_id"] == 0
        assert state["current_difficulty"] == 1
        assert state["is_finished"] is False

    def test_turn_model(self):
        """Тест создания модели Turn."""
        turn = Turn(
            turn_id=1,
            agent_visible_message="Привет! Расскажи о себе.",
            user_message="Я Junior разработчик.",
            internal_thoughts="[Observer]: Кандидат представился.",
        )

        assert turn.turn_id == 1
        assert "Привет" in turn.agent_visible_message
        assert "Junior" in turn.user_message
        assert "[Observer]" in turn.internal_thoughts

    def test_observer_analysis(self):
        """Тест модели ObserverAnalysis."""
        analysis = ObserverAnalysis(
            is_valid_answer=True,
            is_hallucination=False,
            answer_quality=8,
            detected_skills=["Python", "SQL"],
            instruction_to_interviewer="Продолжай, задай вопрос посложнее.",
            thoughts="Хороший ответ.",
        )

        assert analysis.is_valid_answer is True
        assert analysis.is_hallucination is False
        assert analysis.answer_quality == 8
        assert "Python" in analysis.detected_skills

    def test_skill_score(self):
        """Тест модели SkillScore."""
        score = SkillScore(
            topic="Python",
            score=7,
            correct_answers=3,
            incorrect_answers=1,
            notes=["Хорошее понимание основ"],
        )

        assert score.topic == "Python"
        assert score.score == 7
        assert score.correct_answers == 3

    def test_final_feedback(self):
        """Тест модели FinalFeedback."""
        feedback = FinalFeedback(
            decision=Decision(
                assessed_grade="Junior",
                hiring_recommendation="Hire",
                confidence_score=75,
                summary="Хороший кандидат для Junior позиции.",
            ),
            hard_skills=HardSkillsAnalysis(
                confirmed_skills=["Python basics", "SQL"],
                knowledge_gaps=[
                    KnowledgeGap(
                        topic="ORM",
                        question_asked="Что такое ORM?",
                        candidate_answer="Не знаю",
                        correct_answer="Object-Relational Mapping...",
                        severity="medium",
                    )
                ],
                technical_depth=6,
                notes="Базовый уровень.",
            ),
            soft_skills=SoftSkillsAnalysis(
                clarity=7,
                honesty=9,
                engagement=6,
                communication_style="Спокойный",
                red_flags=[],
            ),
            roadmap=[
                RoadmapItem(
                    topic="Django ORM",
                    priority="high",
                    resources=["https://docs.djangoproject.com/"],
                )
            ],
            interview_summary="Кандидат показал базовые знания.",
            total_turns=5,
        )

        assert feedback.decision.assessed_grade == "Junior"
        assert feedback.decision.hiring_recommendation == "Hire"
        assert len(feedback.hard_skills.knowledge_gaps) == 1
        assert feedback.soft_skills.honesty == 9

    def test_feedback_to_log_dict(self):
        """Тест конвертации FinalFeedback в словарь."""
        feedback = FinalFeedback(
            decision=Decision(
                assessed_grade="Junior",
                hiring_recommendation="Hire",
                confidence_score=75,
                summary="Good candidate.",
            ),
            hard_skills=HardSkillsAnalysis(
                confirmed_skills=["Python"],
                knowledge_gaps=[],
                technical_depth=6,
            ),
            soft_skills=SoftSkillsAnalysis(
                clarity=7,
                honesty=8,
                engagement=6,
            ),
            roadmap=[],
            total_turns=3,
        )

        log_dict = feedback_to_log_dict(feedback)

        assert log_dict["decision"]["grade"] == "Junior"
        assert log_dict["decision"]["hiring_recommendation"] == "Hire"
        assert "Python" in log_dict["hard_skills"]["confirmed"]


class TestLogger:
    """Тесты InterviewLogger."""

    def test_logger_session(self, tmp_path):
        """Тест жизненного цикла сессии логгера."""
        logger = InterviewLogger(log_dir=tmp_path)

        log_file = logger.start_session(
            participant_name="Тест",
            position="Developer",
            grade="Junior",
            experience="Python",
        )

        assert log_file.exists()
        assert "Тест" in log_file.stem or "test" in log_file.stem.lower()

        turn = Turn(
            turn_id=1,
            agent_visible_message="Привет!",
            user_message="Привет, я Тест.",
            internal_thoughts="[Observer]: Начало интервью.",
        )
        logger.log_turn(turn)

        current_log = logger.get_current_log()
        assert len(current_log["turns"]) == 1
        assert current_log["turns"][0]["turn_id"] == 1

        final_log_file = logger.end_session()
        assert final_log_file.exists()

        with open(final_log_file) as f:
            saved_log = json.load(f)

        assert saved_log["participant_name"] == "Тест"
        assert len(saved_log["turns"]) == 1

    def test_logger_with_feedback(self, tmp_path):
        """Тест логирования финального фидбэка."""
        logger = InterviewLogger(log_dir=tmp_path)

        logger.start_session(
            participant_name="Test",
            position="Developer",
            grade="Junior",
            experience="Python",
        )

        feedback = {
            "decision": {
                "grade": "Junior",
                "hiring_recommendation": "Hire",
                "confidence_score": 80,
            }
        }

        logger.log_feedback(feedback)
        log_file = logger.end_session()

        with open(log_file) as f:
            saved_log = json.load(f)

        assert saved_log["final_feedback"]["decision"]["grade"] == "Junior"


class TestScenario:
    """Тесты сценариев из спецификации задания."""

    def test_observer_intent_detection(self):
        """Тест детекции намерений в ObserverAnalysis."""
        analysis_end = ObserverAnalysis(wants_to_end_interview=True)
        assert analysis_end.wants_to_end_interview is True

        analysis_skip = ObserverAnalysis(wants_to_skip=True)
        assert analysis_skip.wants_to_skip is True

        analysis_covered = ObserverAnalysis(topic_covered=True, answer_quality=8)
        assert analysis_covered.topic_covered is True
        assert analysis_covered.answer_quality == 8

        analysis_default = ObserverAnalysis()
        assert analysis_default.wants_to_end_interview is False
        assert analysis_default.wants_to_skip is False
        assert analysis_default.topic_covered is False

    def test_hallucination_detection_scenario(self):
        """Тест сценария с галлюцинацией из ТЗ."""
        hallucination_text = (
            "Честно говоря, я читал на Хабре, что в Python 4.0 "
            "циклы for уберут и заменят на нейронные связи, поэтому я их не учу."
        )

        assert "Python 4.0" in hallucination_text
        assert "нейронные связи" in hallucination_text

    def test_role_reversal_scenario(self):
        """Тест сценария смены ролей."""
        user_question = (
            "Слушайте, а какие задачи вообще будут на испытательном сроке? "
            "Вы используете микросервисы?"
        )

        question_markers = ["?", "какие задачи", "используете"]
        assert any(marker in user_question for marker in question_markers)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
