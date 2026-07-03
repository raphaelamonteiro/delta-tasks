class StageError(Exception):
    """Base error for the stage domain."""


class StageNotFoundError(StageError):
    def __init__(self, stage_id: int) -> None:
        self.stage_id = stage_id
        super().__init__(f"Stage not found: {stage_id}")


class InvalidStageOrderError(StageError):
    def __init__(self, project_id: int) -> None:
        self.project_id = project_id
        super().__init__(f"stage_ids do not match the columns of project {project_id}")
