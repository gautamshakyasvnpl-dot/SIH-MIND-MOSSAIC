from app.services.tutor import evaluate_answer, make_viva_question


def next_question(chunks: list[str], asked: list[str]) -> str | None:
    return make_viva_question(chunks, asked)


def grade(question: str, reference: str, answer: str) -> dict:
    return evaluate_answer(question, reference, answer)
