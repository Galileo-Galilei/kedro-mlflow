## Register a pipeline to mlflow with ``KedroPipelineModel`` custom mlflow model

``kedro-mlflow`` has a ``KedroPipelineModel`` class (which inherits from ``mlflow.pyfunc.PythonModel``) which can turn any kedro ``Pipeline`` object to a Mlflow Model.

To convert a ``Pipeline`` to a mlflow model, you need to create a ``KedroPipelineModel`` and then log it to mlflow. An example is given in below snippet:

```python
from pathlib import Path
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project

bootstrap_project(r"<path/to/project>")
session = KedroSession.create(project_path=r"<path/to/project>")

# "pipeline" is the Pipeline object you want to convert to a mlflow model

context = session.load_context()  # this setups mlflow configuration
catalog = context.catalog
pipeline = context.pipelines["<my-pipeline>"]
input_name = "instances"


# artifacts are all the inputs of the inference pipelines that are persisted in the catalog

# (optional) get the schema of the input dataset
input_data = catalog.load(input_name)
model_signature = infer_signature(model_input=input_data)

# you can optionnally pass other arguments, like the "copy_mode" to be used for each dataset
kedro_pipeline_model = KedroPipelineModel(
    pipeline=pipeline, catalog=catalog, input_name=input_name
)

artifacts = kedro_pipeline_model.extract_pipeline_artifacts()

mlflow.pyfunc.log_model(
    artifact_path="model",
    python_model=kedro_pipeline_model,
    artifacts=artifacts,
    conda_env={"python": "3.7.0", dependencies: ["kedro==0.16.5"]},
    model_signature=model_signature,
)
```

Note that you need to provide the ``log_model`` function a bunch of non trivial-to-retrieve informations (the conda environment, the "artifacts" i.e. the persisted data you need to reuse like tokenizers / ml models / encoders, the model signature i.e. the columns names and types...). The ``KedroPipelineModel`` object has methods like `extract_pipeline_artifacts` to help you, but it needs some work on your side.

> Saving Kedro pipelines as Mlflow Model objects is convenient and enable pipeline serving. However, it does not does not solve the decorrelation between training and inference: each time one triggers a training pipeline, (s)he must think to save it immediately afterwards. `kedro-mlflow` offers a convenient API to simplify this workflow, as described in the following sections.
