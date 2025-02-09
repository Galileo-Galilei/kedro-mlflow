# Custom registering of a ``KedroPipelineModel``

```{warning}
The goal of this section is to give tool to machine learning engineer or platform engineer to reuse the objects and customize the workflow. This is specially useful in case you need high customisation or fine grained control of the kedro objects or the mlflow model attributes. This is **very unlikely you need this section** if you are using a kedro project "in the standard way" as a data scientist, in which case you should refer to the section [scikit-learn like pipeline in kedro](https://kedro-mlflow.readthedocs.io/en/stable/source/).
```

## Log a pipeline to mlflow programatically with ``KedroPipelineModel`` custom mlflow model

```{hint}
When using the ``KedroPipelineModel`` programatically, we focus only on the ``inference`` pipeline. We assume That you already ran the ``training`` pipeline previously, and that you now want to log the ``inference`` pipeline in mlflow manually by retrieveing all the needed objects to create the custom model.
```

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
model_signature = infer_signature(
    model_input=input_data
)  # if you want to pass parameters in "predict", you should specify them in the signature

# you can optionally pass other arguments, like the "copy_mode" to be used for each dataset
kedro_pipeline_model = KedroPipelineModel(
    pipeline=pipeline, catalog=catalog, input_name=input_name
)

artifacts = kedro_pipeline_model.extract_pipeline_artifacts()

mlflow.pyfunc.log_model(
    artifact_path="model",
    python_model=kedro_pipeline_model,
    artifacts=artifacts,
    conda_env={"python": "3.10.0", dependencies: ["kedro==0.18.11"]},
    model_signature=model_signature,
)
```

```{important}
Note that you need to provide the ``log_model`` function a bunch of non trivial-to-retrieve informations (the conda environment, the "artifacts" i.e. the persisted data you need to reuse like tokenizers / ml models / encoders, the model signature i.e. the columns names and types and the predict parameters...). The ``KedroPipelineModel`` object has methods like `extract_pipeline_artifacts` to help you, but it needs some work on your side.
```

```{note}
Saving Kedro pipelines as Mlflow Model objects is convenient and enable pipeline serving. However, it does not does not solve the decorrelation between training and inference: each time one triggers a training pipeline, (s)he must think to save it immediately afterwards. `kedro-mlflow` offers a convenient API through hooks to simplify this workflow, as described in the section [scikit-learn like pipeline in kedro](https://kedro-mlflow.readthedocs.io/en/stable/source/) .
```

## Log a pipeline to mlflow with the CLI

```{note}
This command is mainly a helper to relog a model manually without retraining (e.g. because you slighlty modify the preprocessing or post processing and don't want to train again.)
```

```{warning}
We **assume that you already ran the ``training`` pipeline previously**, which created persisted artifacts. Now you want to trigger logging the ``inference`` pipeline in mlflow trhough the CLI. This is dangerous because the commmand does not check that your pipeline is working correctly or that the perssited model has not been modified.
```

You can log a Kedro ``Pipeline`` to mlflow as a custom model through the CLI with ``modelify`` command:

```bash
kedro mlflow modelify --pipeline=<your-inference-pipeline> --input-name <name-in-catalog-of-input-data>
```

This command will create a new run with an artifact named ``model`` and persist it the code fo your pipeline and all its inputs as artifacts (hence they should have been created *before* running this command, e.g. the model should already be persisted on the disk). Open the user interface with ``kedro mlflow ui`` to check the result. You can also:

- specify the run id in which you want to log the pipeline with the ``--run-id`` argument, and its name with the ``--run-name`` argument.
- pass almost all arguments accepted by [``mlflow.pyfunc.log_model``](https://www.mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#mlflow.pyfunc.log_model), see the list of all accepted arguments in the [API documentation](https://kedro-mlflow.readthedocs.io/en/latest/source/05_API/01_python_objects/04_CLI.html#modelify)
