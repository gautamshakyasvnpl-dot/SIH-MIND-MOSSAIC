from app.services.tutor import answer_question


def run_tutor_turn(chunks: list[str], question: str) -> dict:
    return answer_question(chunks, question)
