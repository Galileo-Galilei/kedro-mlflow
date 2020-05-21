import pytest

from kedro_mlflow.framework.cli.cli_utils import (
    render_jinja_template,
    write_jinja_template,
)


@pytest.fixture
def template_path(tmp_path):
    return tmp_path / "template.py"


@pytest.fixture
def jinja_template(template_path):
    with open(template_path, "w") as file_handler:
        file_handler.write("fake file\n which contains {{ fake_tag }}. Nice, isn't it?")
    return "fake file\n which contains 'Hello world!'. Nice, isn't it?"


@pytest.fixture
def cookiecutter_template(template_path):
    with open(template_path, "w") as file_handler:
        file_handler.write(
            "fake file\n which contains {{ cookiecutter.fake_tag }}. Nice, isn't it?"
        )
    return "fake file\n which contains 'Hello world!'. Nice, isn't it?"


def test_render_jinja_template(template_path, jinja_template):
    rendered = render_jinja_template(src=template_path, fake_tag="'Hello world!'")
    assert rendered == jinja_template


def test_render_jinja_template_with_cookiecutter_tags(
    template_path, cookiecutter_template
):
    rendered = render_jinja_template(
        src=template_path, fake_tag="'Hello world!'", is_cookiecutter=True
    )
    assert rendered == cookiecutter_template


def test_write_jinja_template(tmp_path, template_path, jinja_template):
    rendered_path = tmp_path / "rendered.py"
    write_jinja_template(
        src=template_path, dst=rendered_path, fake_tag="'Hello world!'"
    )
    with open(rendered_path, "r") as file_handler:
        rendered = file_handler.read()
    assert rendered == jinja_template


def test_write_jinja_template_with_cookiecutter_tags(
    tmp_path, template_path, cookiecutter_template
):
    rendered_path = tmp_path / "rendered.py"
    write_jinja_template(
        src=template_path,
        dst=rendered_path,
        is_cookiecutter=True,
        fake_tag="'Hello world!'",
    )
    with open(rendered_path, "r") as file_handler:
        rendered = file_handler.read()
    assert rendered == cookiecutter_template
