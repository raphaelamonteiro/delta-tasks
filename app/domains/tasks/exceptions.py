from uuid import UUID


class TaskError(Exception):
    """Base error for the tasks domain."""


class TaskNotFoundError(TaskError):
    def __init__(self, task_id: int) -> None:
        self.task_id = task_id
        super().__init__(f"Task not found: {task_id}")


class ResponsibleNotMemberError(TaskError):
    """Raised when the target responsible is not a member of the task's project (RN-006)."""

    def __init__(self, user_id: UUID, project_id: int) -> None:
        self.user_id = user_id
        self.project_id = project_id
        super().__init__(f"O usuário: {user_id} is not a member of project {project_id}")


class StageNotInProjectError(TaskError):
    """Raised when the destination column is not part of the task's project (RN-005)."""

    def __init__(self, stage_id: int, project_id: int) -> None:
        self.stage_id = stage_id
        self.project_id = project_id
        super().__init__(f"Stage {stage_id} is not part of project {project_id}")
