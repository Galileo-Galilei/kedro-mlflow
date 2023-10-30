from mlflow.utils.name_utils import _generate_random_name


def resolve_random_name(x=None):
    # a resolver must have an argument, see: https://github.com/omry/omegaconf/issues/1060
    return _generate_random_name()
