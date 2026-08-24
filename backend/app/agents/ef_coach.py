from app.services.tutor import break_into_sprints


def plan_task(title: str, notes: str | None, pace: str) -> list[dict]:
    return break_into_sprints(title, notes, pace)
