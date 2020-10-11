"""Application entry point."""
from kedro.framework.context import KedroContext


class ProjectContext(KedroContext):
    """Users can override the remaining methods from the parent class here,
    or create new ones (e.g. as required by plugins)
    """

    project_name = "dummy_package"
    # `project_version` is the version of kedro used to generate the project
    project_version = "0.16.5"
    package_name = "dummy_package"
