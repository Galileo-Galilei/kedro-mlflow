# Example project
## Check your installation
Create a conda environment and ``kedro-mlflow`` (this will automatically install ``kedro>=0.16.0``).

```console
conda create -n km_example python=3.6.8 --yes
conda activate km_example
pip install kedro-mlflow
```
## Install the toy project
For this end to end example, we will use the [kedro starter](https://kedro.readthedocs.io/en/latest/02_getting_started/05_starters.html#creating-new-projects-with-kedro-starters) with the [iris dataset](https://github.com/quantumblacklabs/kedro-starter-pandas-iris).

We use this project because:
- it covers most of the common use cases
- it is compatible with older version of ``Kedro`` so newcomers are used to it
- it is maintained by ``Kedro`` maintainers and therefore enforces some best practices.

### Installation with ``kedro>=0.16.3``
The default starter is now called "pandas-iris". In a new console, enter:
```console
kedro new --starter=pandas-iris
```
Answer ``Kedro Mlflow Example``, ``km-example`` and ``km_example`` to the three setup questions of a new kedro project:
```
Project Name:
=============
Please enter a human readable name for your new project.
Spaces and punctuation are allowed.
 [New Kedro Project]: Kedro Mlflow Example

Repository Name:
================
Please enter a directory name for your new project repository.
Alphanumeric characters, hyphens and underscores are allowed.
Lowercase is recommended.
 [kedro-mlflow-example]: km-example

Python Package Name:
====================
Please enter a valid Python package name for your project package.
Alphanumeric characters and underscores are allowed.
Lowercase is recommended. Package name must start with a letter or underscore.
 [kedro_mlflow_example]: km_example
```

### Installation with ``kedro>=0.16.0, <=0.16.2``

With older versions of ``Kedro``, the starter option is not available, but this ``kedro new`` provides an "Include example" question. Answer ``y`` to this question to get the same starter as above. In a new console, enter:
```console
kedro new
```

Answer ``Kedro Mlflow Example``, ``km-example``, ``km_example`` and ``y`` to the four setup questions of a new kedro project:

```console
Project Name:
=============
Please enter a human readable name for your new project.
Spaces and punctuation are allowed.
 [New Kedro Project]: Kedro Mlflow Example

Repository Name:
================
Please enter a directory name for your new project repository.
Alphanumeric characters, hyphens and underscores are allowed.
Lowercase is recommended.
 [kedro-mlflow-example]: km-example

Python Package Name:
====================
Please enter a valid Python package name for your project package.
Alphanumeric characters and underscores are allowed.
Lowercase is recommended. Package name must start with a letter or underscore.
 [kedro_mlflow_example]: km_example

Generate Example Pipeline:
==========================
Do you want to generate an example pipeline in your project?
Good for first-time users. (default=N)
 [y/N]: y
```

# Install dependencies

Move to the project directory:
```
cd km-example
```

Install the project dependencies:

```console
pip install -r src/requirements.txt
pip install --upgrade kedro-mlflow==0.2.0
```
**Warning: Do not use ``kedro install`` commands does not seem to install the packages in your activated environment.**
