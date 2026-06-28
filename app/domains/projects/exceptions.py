class ProjectError(Exception):
    """Base error for the projects domain."""


class ProjectNotFoundError(ProjectError):
    def __init__(self, project_id: int) -> None:
        self.project_id = project_id
        super().__init__(f"Project not found: {project_id}")
