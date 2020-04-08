from typing import Callable, Any, Dict, Union
from mlflow.pyfunc import PythonModel
from kedro.io import DataCatalog
from kedro.pipeline import Pipeline
from kedro.runner import SequentialRunner


class KedroPipelineModel(PythonModel):
    def __init__(self,
                 training: Pipeline,
                 inference: Pipeline,
                 input_formatter: Callable = None,
                 formatter_kwargs: Dict[str, Any] = None,
                 instance_name: Union[str, None] = None):

        free_inputs_set = set(inference.inputs) - set(training.outputs)
        if len(free_inputs_set) == 1:
            free_input = list(free_inputs_set)[0]
        else:
            raise KedroPipelineModelInputsError("""
        The following inputs are free for the inference pipeline:
            - {inputs}. 
        Only one free input is allowed. 
        Please make sure that 'inference' pipeline inputs are 'training' pipeline outputs,
        except one.""".format("\n     - ".join(free_inputs_set)))

        self.catalog = DataCatalog()
        self.training = training
        self.inference = inference
        self.input_formatter = input_formatter
        self.formatter_kwargs = formatter_kwargs
        self.instance_name = instance_name or free_input

    def load_context(self, context):
        self.catalog.add_feed_dict(context.artifacts)

    def predict(self, context, model_input):
        input_data = self.input_formatter(data=model_input,
                                          **self.formatter_kwargs)
        self.catalog.add_feed_dict({self.instance_name: input_data})
        runner = SequentialRunner()
        run_outputs = runner.run(pipeline=self.inference,
                                 catalog=self.catalog)
        return run_outputs


class KedroPipelineModelInputsError(Exception):
    """Error raised when the inputs of KedroPipelineMoel are invalid
    """
