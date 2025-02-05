# Deployment patterns for kedro pipelines as model

A step by step tutorial with code is available in the [kedro-mlflow-tutorial repository on github](https://github.com/Galileo-Galilei/kedro-mlflow-tutorial#serve-the-inference-pipeline-to-an-end-user) which explains how to serve the pipeline as an API or a batch.

## Deploying a KedroPipelineModel

::::{tab-set}

:::{tab-item} Reuse from a python script

```{note}
See tutorial:  <https://github.com/Galileo-Galilei/kedro-mlflow-tutorial?tab=readme-ov-file#scenario-1-reuse-from-a-python-script>
```

If you want to load and predict with your model from python, the ``load_model`` function of mlflow is what you need:

```python
PROJECT_PATH = r"<your/project/path>"
RUN_ID = "<your-run-id>"

from kedro.framework.startup import bootstrap_project
from kedro.framework.session import KedroSession
from mlflow.pyfunc import load_model

bootstrap_project(PROJECT_PATH)
session = Kedrosession.create(
    session_id=1,
    project_path=PROJECT_PATH,
    package_name="kedro_mlflow_tutorial",
)
local_context = session.load_context()  # setup mlflow config

instances = local_context.io.load("instances")
model = load_model(f"runs:/{RUN_ID}/kedro_mlflow_tutorial")

predictions = model.predict(
    instances
)  # runs ``session.run(pipeline=inference)`` with the artifacts created ruing training. You should see the kedro logs.
```

The ``predictions`` object is a ``pandas.DataFrame`` and can be handled as usual.
:::

:::{tab-item} Reuse in a kedro pipeline

```{note}
See tutorial: <https://github.com/Galileo-Galilei/kedro-mlflow-tutorial?tab=readme-ov-file#scenario-2-reuse-in-a-kedro-pipeline>
```

Say that you want to reuse this trained model in a kedro Pipeline, like the user_app. The easiest way to do it is to add the model in the catalog.yml file

```yaml
pipeline_inference_model:
  type: kedro_mlflow.io.models.MlflowModelLoggerDataSet
  flavor: mlflow.pyfunc
  pyfunc_workflow: python_model
  artifact_path: kedro_mlflow_tutorial  # the name of your mlflow folder = the model_name in pipeline_ml_factory
  run_id: <your-run-id>  # put it in globals.yml to help people find out what to modify
```

Then you can reuse it in a node to predict with this model which is the entire inference pipeline at the time you launched the training.

```python
# nodes.py
def predict_from_model(model, data):
    return model.predict(data)


# pipeline.py
def create_pipeline():
    return pipeline(
        [
            node(
                func=predict_from_model,
                inputs={"model": pipeline_inference_model, "data": "validation_data"},
            )
        ]
    )
```

:::

:::{tab-item} Serve the model with mlflow

```{note}
See tutorial: <https://github.com/Galileo-Galilei/kedro-mlflow-tutorial?tab=readme-ov-file#scenario-3-serve-the-model-with-mlflow>
```

Mlflow provide helpers to serve the model as an API with one line of code:

``mlflow models serve -m "runs:/<your-model-run-id>/kedro_mlflow_tutorial"``

This will serve your model as an API (beware: there are known issues on windows). You can test it with:
``curl -d "{\"columns\":[\"text\"],\"index\":[0,1],\"data\":[[\"This movie is cool\"],[\"awful film\"]]}" -H "Content-Type: application/json"  localhost:5000/invocations``
:::

::::

## Frequently asked questions

:::{dropdown} How can I pass parameters at runtime to a ``KedroPipelineModel``?

Since ``kedro-mlflow>0.14.0``, you can pass parameters when predicting with  a ``KedroPipelineModel`` object.

We assume you've trained a model with ``pipeline_factory_function``. First, load the model, e.g. through the catalog or as described in the previous section:

```yaml
# catalog.yml
pipeline_inference_model:
    type: kedro_mlflow.io.models.MlflowModelTrackingDataset
    flavor: mlflow.pyfunc
    pyfunc_workflow: python_model
    artifact_path: kedro_mlflow_tutorial  # the name of your mlflow folder = the model_name in pipeline_ml_factory
    run_id: <your-run-id>  
```

Then, pass params as a dict under the ``params`` argument of the ``predict`` method:

```python
catalog.load("pipeline_inference_model")  # You can also load it in a node "as usual"
predictions = model.predict(input_data, params={"my_param": "<my_param_value>"})
```

```{warning}
This will only work if ``my_param`` is a parameter (i.e. prefixed with ``params:``) of the inference pipeline.
```

```{tip}
Available params are visible in the model signature in the UI
```

:::

:::{dropdown} How can I change the runner at runtime when predicting with a ``KedroPipelineModel``?

Assuming the syntax of previous section, a special key in "params" is reserved for the kedro runner:

```python
catalog.load("pipeline_inference_model")
predictions = model.predict(
    input_data, params={"my_param": "<my_param_value>", "runner": "ThreadRunner"}
)
```

```{tip}
You can pass any kedro runner, or even a custom runner by using the path to the module: ``params={"runner": "my_package.my_module.MyRunner"}``
```

:::
