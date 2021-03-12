from kedro_mlflow.utils import _parse_requirements


def test_parse_requirements(tmp_path):

    with open(tmp_path / "requirements.txt", "w") as f:
        f.writelines(["kedro==0.17.0\n", " mlflow==1.11.0\n" "-r pandas\n"])

    requirements = _parse_requirements(tmp_path / "requirements.txt")
    expected_requirements = ["kedro==0.17.0", "mlflow==1.11.0"]

    assert requirements == expected_requirements
