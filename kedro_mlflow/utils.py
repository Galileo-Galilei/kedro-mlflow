from typing import Union
import pathlib
import os

def _is_kedro_project(project_path: Union[str, pathlib.Path, None] = None)-> bool:
    """Best effort to check if the function is called
     inside a kedro project.
    
    Returns:
        bool -- True if the working directory is the root of a kedro project 
    """
    if project_path is None:
        project_path = pathlib.Path.cwd()
    flag = (project_path / ".kedro.yml").is_file()
    return flag
    