import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import os
import time
import argparse

# Define a feature engineering function
def create_features(df):
    """
    A simple feature engineering function.
    """
    df['new_feature'] = df['feature1'] * df['feature2']
    return df

def main(epoch):

    with mlflow.start_run() as run:
        mlflow.set_tag("developer", "gemini-cli")
        mlflow.set_tag("use_case", "example_script")

        # Feature Engineering & Registration
        feature_script_path = "feature_creator.py"
        with open(feature_script_path, "w") as f:
            f.write(
"""
def create_features(df):
    df['new_feature'] = df['feature1'] * df['feature2']
    return df
"""
            )
        mlflow.log_artifact(feature_script_path, "feature_engineering")

        # Create dummy data
        data = {
            'feature1': np.random.rand(100),
            'feature2': np.random.rand(100) * 5,
            'label': np.random.randint(0, 2, 100)
        }
        df = pd.DataFrame(data)

        # Apply feature engineering
        df_featured = create_features(df.copy())

        X = df_featured[['feature1', 'feature2', 'new_feature']]
        y = df_featured['label']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Log parameters
        params = {
            "solver": "lbfgs",
            "random_state": 42
        }
        mlflow.log_params(params)

        # Train model
        model = LogisticRegression(**params)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        # Log metrics
        mlflow.log_metric("accuracy", accuracy)
        mlflow.sklearn.log_model(model, "model")

        # Register model in MLflow Model Registry
        model_name = "ExampleModel"  # Hardcoded
        model_uri = f"runs:/{run.info.run_id}/model"
        mlflow.register_model(model_uri, model_name)

        time.sleep(epoch)  # Ensure all logs are flushed

    os.remove(feature_script_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MLflow Example Script with Dummy Argument")
    parser.add_argument("--epoch", type=str, default=10, help="A dummy argument for demonstration")
    args = parser.parse_args()
    main(int(args.epoch))
