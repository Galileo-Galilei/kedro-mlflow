# Why we need a mlops framework to manage machine learning development lifecycle

## Machine learning deployment is hard because it comes with a lot of constraints and no adequate tooling

### Identifying the challenges to address when deploying machine learning

It is a very common pattern to hear that "machine learning deployment is hard", and this is supposed to explain why so many firms do not achieve to insert ML models in their IT systems (and consequently, not make money despite consequent investments in ML).

On the other hand, you can find thousands of tutorial across the web to explain how to deploy a ML API in 5 min, either locally or on the cloud. There is also a large amount of training sessions which can teach you "how to become a machine learning engineer in 3 months".

*Who is right then? Both!*

Actually, there is a confusion on what "deployment" means, especially in big enterprises that are not "tech native" or for newbies in ML world. Serving a model over an API pattern is a start, but you often need to ensure (at least) the following properties for your system:

- **scalability and cost control**: in many cases, you need to be able to deal with a lot of (possibly concurrent) requests (likely much more than during training phase). It may be hard to ensure that the app will be able to deal with such an important amount of data. Another issue is that ML oftens needs specific infrastrusture (e.g., GPU's) which are very expensive. Since the request against the model often vary wildly over time, it may be important to adapt the infrastructure in real time to avoid a lot of infrastructure costs
- **speed**: A lot of recent *state of the art* (SOTA) deep learning / ensemble models are computationally heavy and this may hurt inference speed, which is critical for some systems.
- **disponibility and resilience**: Machine learning systems are more complex than traditional softwares because they have more moving parts (i.e. data and parameters). This increases the risk of errors, and since ML systems are used for critical systems making both the infrastructure and the code robust is key.
- **portability / ease of integration with external components**: ML models are not intended to be directly used by the end users, but rather be consumed by another part of your system (e.g a call to an API). To speed up deployment, your model must be easy to be consumed, i.e. *as self contained as possible*. As a consequence, you must **deploy a ML pipeline which hanbles business objects instead of only a ML model**. If the other part which consumes your API needs to make a lot of data preprocessing *before* using your model, it makes it:
  - very risky to use, because preprocessing and model are decoupled: any change in your model must be reflected in this other data pipeline and there is a huge mismatch risk when redeploying
  - slow and costful to deploy because each deployment of your model needs some new development on the client side
  - poorly reusable beacuse each new app who wants to use the model needs some specific development on its own
- **reproducibility**: the ML development is very iterative by nature. You often try a simple baseline model and iterate (sometimes directly by discussing with the final user) to finally get the model that suits the most your needs ( wich is the balance between speed / accuracy / interpretability / maintenance costs / inference costs / data availability / labelling costs...). Looping through these iterations, it is very easy to forget what was the best model. You should not rely only on your memory to compare your experiments. Moreover, many countries have regulatory constraints to avoid discriminations (e.g. GDPR in the EU), and your must be able to justify how your model was built and to that extent reproducibility is key. It is also essential when you redeploy a model that turns out to be worse than the old one and you have to rollback fast.
- **monitoring and ease of redeployment**: It is well known that model quality decay over time (sometimes quickly!), and if you use ML for a critical activity, you will have to retrain your model periodically to maintain its performance. It is critical to be able to redeploy easily your model. This implies that retraining (or even redeployment of a new model) must be as **automated as possible** to ensure deployment speed and model quality.

An additional problem that happens in real world is that it is sometimes poorly understood by end users that the ML model is not standalone. It implies
**external developments** from the client side (at least to call the model, sometimes to adapt a data pipeline or to change the user interface to add the ML functionality) and they have hard times to understand the entire costs of a ML project as well as their responsibilities in the project. This is not really a problem of ML but rather on how to give a minimal culture on ML to business end users.

### A comparison between traditional software development and machine learning projects

#### ML and traditional software have different moving parts

A traditional software project contains several moving parts:

- code
- environment (packages versions...)
- infrastructure (build on Windows, deploy on linux)

Since it is a more mature industry, efficient tools exists to manage these items (Git, pip/conda, infra as code...). On the other hand, a ML project has additional moving parts:

- parameters
- data

As ML is a much less mature field, efficient tooling to adress these items are very recent and not completely standardized yet (e.g. Mlflow to track parameters, DVC to version data, `great-expectations` to monitor data which go through your pipelines, `tensorboard` to monitor your model metrics...)

> **Mlflow is one of the most mature tool to manage these new moving parts.**

#### ML and traditional software have different development lifecycles

In traditional software, the development workflow is roughly the following:

- you create a git branch
- you develop your new feature
- you add tests and ensure there are no regression
- you merge the branch on the main branch to add your feature to the codebase

This is a **linear** development process based on **determinist** behaviour of the code.

However in ML development, the workflow is much more iterative and may looklike this:

- you create a notebook
- you make some exploration on the data with some descriptive analysis and a baseline model
- you switch to a git branch and python scripts once the model is quite stable
- you retrain the model, eventually do some parameter tuning
- you merge your code on the main branch to share your work

If you need to modify the model later (do a different preprocessing, change the model type...), you do not **add** code to the codebase, you **modify** the existing code. This makes unit testing much harder because the desired features change over time.

The other difficulty when testing machine learning applications is it hard to test for regression, since the model depends on underlying data and the chosen metrics. If a new model performs slightly better or worse than the previous one ont the same dataset, it may be due to randomness and not to code quality. If the metric varies on a different dataset, it is even harder to know if it is due to code quality or to innate randomness.

This is a **cyclic** development process based on a **stochastic** behaviour of the code.

> **Kedro is a very new tool and cannot be called "mature" at this stage but tries to solve this development lifecyle with a very fluent API to create and modify machine learning pipelines.**

## Deployment issues addressed by `kedro-mlflow` and their solutions

### Out of scope

We will focus on machine learning *development* lifecycle. As a consequence, these items are out of scope:

- Orchestration
- Issues related to infrastructure (related, but not limited to, the 3 first items of above list: scalability and cost control, inference speed, disponibility and resilience)
- Issues related to model monitoring: Data distribution changes over time, model decay, data access...

### Issue 1: The training process is poorly reproducible

The main reason which explains why training is hard to reproduce is the iterative process. Data scientists launch several times the same run with slightly different parameters / data / preprocessing. If they rely on their memory to compare these runs, they will likely struggle to remember what was the best one.

> **`kedro-mlflow` offers automatic parameters versioning** when a pipeline is ran to easily link a model to its training parameters.

Note that there is also a lot of "innate" randomness in ML pipelines and if a seed is not set explictly as a parameter , the run will likely not be reproducible (separation train/test/validation, moving underlying data sources, random initialisation for optimizers, random split for bootstrap...).

### Issue 2: The data scientist and stakeholders focus on training

While building the ML model, the inference pipeline is often completely ignored by the data scientist. The best example are Kaggle competitions where a very common workflow is the following:

- merge the training and the test data at the beginning of their script
- do the preprocessing on the entire dataset
- resplit just before training the model
- train the model on training data
- predict on test data
- anayze their metrics, finetune their hyper parameters
- submit their predictions as data (i.e. as a file) to Kaggle

The very important issue which arises with such a workflow is that **you completely ignore the non reproducibility which arises from the preprocessing (encoding, randomness...)**. Most Kaggle solutions are never tested on an end to end basis, i.e. by running the inference pipeline from the test data input file to the predictions file. This facilitates very bad coding practices and teaches beginner data scientists bad software engineering practice.

> `kedro-mlflow` enables to log the inference pipeline as a Mlflow Model (through a `KedroPipelineModel` class) to ensure that you deploy the inference pipeline as a whole.

### Issue 3: Inference and training are entirely decoupled

As stated previous paragraph, the inference pipeline is not a primary concern when experimenting and developing your model. This raises strong reproducibility issues. Assume that you have logged the model and all its parameters when training (which is a good point!), you will still need to retrieve the code used during training to create the inference pipeline. This is in my experience quite difficult:

- in the best case, you have trained the model from a git sha which is logged in mlflow. Any potential user can (but it takes time) recreate the exact inference pipeline from your source code, and retrieve all necessary artifacts from mlflow. This is tedious, error prone, and gives a lot of responsibility and work to your end user, but at least it makes your model usable.
- most likely, you did not train your model from a version control commit. While experimenting /debug, it is very common to modify the code and retrain without committing. The exact code associated to a given model will likely be impossible to find out later.  

> `kedro-mlflow` offers a `PipelineML` (and its helpers `pipeline_ml_factory`) class which binds the `training` and `inference` pipeline, and a hook which autolog such pipelines when they are run. This enables data scientists to ensure that each training model is logged with its associated inference pipeline, and is ready to use for any end user. This decreases a lot the necessary cognitive complexity to ensure coherence between training and inference.

### Issue 4: Data scientists do not handle business objects

It is often said that data scientists deliver machine learning *models*. This assumes that all the preprocessing will be recoded the end user of your model. This is a major cause of poor adoption of your model in an enterprise setup because it makes your model:

- hard to use (developments are need on the client side)
- hard to update (it needs code update from the end user)
- very error prone (never trust the client!)

If you struggle representing it, imagine that you have developed a NLP model. Would you really ask your end user to give you a one-hot encoded matrix or BERT-tokenized texts with your custom embbeddings and vocabulary?

Your model must handle business objects (e.g. a mail, a movie review, a customer with its characteristic, a raw image...) to be usable.

> Kedro `Pipeline`'s are able to handle processing from the business object to the prediction. Your real model must be a `Pipeline`, and the `KedroPipelineModel` of `kedro-mlflow` helps to store them and log them in mlflow. Additionally, `kedro-mlflow` suggests how your project should be organized in "apps" to make this transition easy.

### Overcoming these problems: support an organisational solution with an efficient tool

``kedro-mlflow`` assume that we declare a clear contrat of what the output of the data science project is: it is an an inference pipeline. This defines a clear "definition of done" of the data science project: is it ready to deploy?

The downside of such an approach is that it increases data scientist's responsibilities,because s(he) is responsible for his code.

``kedro-mlflow`` offers a very convenient way (through the ``pipeline_ml_factory`` function) to make sure that each experiment will result in creating a compliant "output".

This is very transparent for the data scientist who have no extra constraints (apart from developing in Kedro) to respect this contract. Hence, the data scientist still benefits from the interactivity he needs to work. This is why we want to leverage Kedro which is very flexible and offers a convenient way to transition from notebooks to pipeline, and leverage Mlflow for standardising the definiton of an "output" of a datscience project.

> Enforcing these solutions with a tool: `kedro-mlflow` at the rescue
