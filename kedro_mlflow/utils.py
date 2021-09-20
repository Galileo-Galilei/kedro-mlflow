from pathlib import Path
from typing import List, Union


def _parse_requirements(path: Union[str, Path], encoding="utf-8") -> List:
    with open(path, mode="r", encoding=encoding) as file_handler:
        requirements = [
            x.strip() for x in file_handler if x.strip() and not x.startswith("-r")
        ]
    return requirements
