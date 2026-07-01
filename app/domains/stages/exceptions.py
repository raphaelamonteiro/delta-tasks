class ProjectError(Exception):
    """Base error for the stage domain."""


class ProjectNotFoundError(ProjectError):
    def __init__(self, stage_id: int) -> None:
        self.stage_id = stage_id
        super().__init__(f"Stage not found: {stage_id}")
