import jinja2
import pathlib
from typing import Union


def render_jinja_template(src: Union[str, pathlib.Path],
                          **kwargs) -> str:
    """This functions enable to copy a file and render the 
        tags (identified by {{ my_tag }}) with the values provided in kwargs.
        
        Arguments:
            src {Union[str, pathlib.Path]} -- The path to the template which should be rendered

        Returns:
            str -- A string that contains all the files with replaced tags.
    """
    src = pathlib.Path(src)

    with open(src) as file_handler:
        template = jinja2.Template(file_handler.read())
    parsed_template = template.render(**kwargs)
    return parsed_template


def write_jinja_template(src: Union[str, pathlib.Path],
                         dst: Union[str, pathlib.Path],
                         **kwargs) -> None:
    """Write a template file and replace tis jinja's tags
     (identified by {{ my_tag }}) with the values provided in kwargs.
    
    Arguments:
        src {Union[str, pathlib.Path]} -- Path to the template which should be rendered
        dst {Union[str, pathlib.Path]} -- Path where the rendered template should be saved
    """
    dst = pathlib.Path(dst)
    parsed_template = render_jinja_template(src, **kwargs)
    with open(dst, "w") as file_handler:
        file_handler.write(parsed_template)
