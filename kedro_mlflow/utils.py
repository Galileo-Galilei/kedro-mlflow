from pathlib import Path
from typing import Union

KEDRO_YML = ".kedro.yml"


def _is_kedro_project(project_path: Union[str, Path, None] = None) -> bool:
    """Best effort to check if the function is called
     inside a kedro project.

    Returns:
        bool -- True if the working directory is the root of a kedro project
    """
    project_path = _validate_project_path(project_path)
    flag = (project_path / KEDRO_YML).is_file()
    return flag


def _validate_project_path(project_path: Union[str, Path, None] = None) -> Path:
    if project_path is None:
        project_path = Path.cwd()
    else:
        project_path = Path(project_path)
    return project_path


def _already_updated(project_path: Union[str, Path, None] = None) -> bool:
    project_path = _validate_project_path(project_path)
    flag = False
    # TODO : add a better check ...
    if (project_path / "conf" / "base" / "mlflow.yml").is_file():
        flag = True
    return flag


def _parse_requirements(path, encoding="utf-8"):
    with open(path, mode="r", encoding=encoding) as file_handler:
        requirements = [
            x.strip() for x in file_handler if x.strip() and not x.startswith("-r")
        ]
    return requirements
