# Deployment patterns for kedro pipelines

A step by step tutorial with code is available in the [kedro-mlflow-tutorial repository on github](https://github.com/Galileo-Galilei/kedro-mlflow-tutorial#serve-the-inference-pipeline-to-an-end-user) which explains how to serve the pipeline as an API or a batch.

## Deploying a KedroPipelineModel

### Reuse from a python script

See tutorial:  https://github.com/Galileo-Galilei/kedro-mlflow-tutorial?tab=readme-ov-file#scenario-1-reuse-from-a-python-script

### Reuse in a kedro pipeline

See tutorial: https://github.com/Galileo-Galilei/kedro-mlflow-tutorial?tab=readme-ov-file#scenario-2-reuse-in-a-kedro-pipeline

### Serve the model with mlflow

See tutorial: https://github.com/Galileo-Galilei/kedro-mlflow-tutorial?tab=readme-ov-file#scenario-3-serve-the-model-with-mlflow

## Pass parameters at runtime to a Kedro PipelineModel

### Pipeline parameters

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

### Configuring the runner

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
