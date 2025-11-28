<h2 align="center">
  <img width="35%" alt="Flowkestra logo" src="assets/flowkestra.png"><br/>
  A Lightweight Orchestrator for Machine Learning Experiments
</h2>



Running machine learning experiments often involves a series of steps, such as data processing, training, and evaluation. Managing the dependencies and parameters for each step can become complex. Flowkestra simplifies this process by allowing you to define your entire workflow in a single configuration file.

This approach makes it easier to run, reproduce, and track your experiments, whether you are doing initial exploration on your local machine or preparing for more complex workflows.

---

## Core Features

- **YAML-based Workflows**: Define your experiment as a series of tasks in a simple `config.yml` file.
- **Sequential Task Execution**: Runs your Python scripts in the order you define them.
- **MLflow Integration**: Automatically logs your runs, parameters, and artifacts to an MLflow tracking server.
- **Local Execution**: Currently supports running experiments on your local machine.

---

## Getting Started

### 1. Installation

```bash
pip install flowkestra
```
*(Note: The package is not yet published to PyPI. To install locally, use `pip install .`)*

### 2. Create a Configuration File

Create a `config.yml` file to define your experiment. This file specifies the scripts to run, their inputs/outputs, and any parameters.

Here is an example for a local run:

```yaml
# config.yml

# A descriptive name for your MLflow experiment run.
run_name: local_training_run

# The URI for your MLflow tracking server. Can be a local path or a remote URL.
mlflow_tracking_uri: ./mlartifacts

# Defines where the tasks will be executed. 'local' is currently supported.
machine:
  type: local

# A list of tasks to be executed sequentially.
tasks:
  - # A descriptive name for the task.
    name: "Process-Data"
    # The Python script to execute for this task.
    script: "example/etl_local.py"
    # (Optional) Path to a requirements.txt file for this task's environment.
    requirements: "example/requirements_local.txt"
    # Path to the input data for the script.
    input_path: "example/train_local.csv"
    # Path where the output of the script will be saved.
    output_path: "local_train/etl_output.csv"

  - name: "Train-Model"
    script: "example/train_local.py"
    # The input for this task is the output from the previous task.
    input_path: "local_train/etl_output.csv"
    output_path: "local_train/model.pkl"
    # A dictionary of parameters to be passed to your script and logged by MLflow.
    params:
      n_estimators: 100
      random_state: 42
```

### 3. Run Your Experiment

Execute your experiment using the Flowkestra CLI, pointing it to your configuration file.

```bash
flowkestra -f config.yml
```

Flowkestra will then run your defined tasks in order.

---

## Potential Use Cases

- **Organizing Experiments**: Structure your ML code into reusable scripts and orchestrate them for different experiments.
- **Reproducible Runs**: Keep your configuration, parameters, and scripts together, ensuring that you can easily rerun an experiment.
- **Basic ML Pipelines**: Create simple, sequential pipelines for tasks like data preprocessing followed by model training.

---

## Roadmap & Next Features

- **Remote Training**: Support for executing tasks on remote machines via SSH.
- **Automated Parameter Tuning**: Integrate with libraries to automate hyperparameter searches.
- **Expanded Cloud Support**: Add direct support for cloud environments.

---

## Notes

- This project is in its early stages. Contributions and feedback are welcome.
