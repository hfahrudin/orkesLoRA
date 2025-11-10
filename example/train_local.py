import pandas as pd
from sklearn.linear_model import LinearRegression
import mlflow
import argparse
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset_path", default="./data/processed/train_local_processed.csv")
    parser.add_argument("--output_dir", default="./outputs/finetuned")
    parser.add_argument("--model_name", default="mock_model")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    mlflow.set_experiment("Mock_Local_Training")

    with mlflow.start_run():
        print(f"📂 Loading processed dataset from {args.dataset_path}")
        df = pd.read_csv(args.dataset_path)
        
        print("🏋️ Training mock model...")
        X = df[["value"]].values
        y = df["processed"].values
        model = LinearRegression()
        model.fit(X, y)

        print("💾 Logging model to MLflow...")
        model_path = os.path.join(args.output_dir, "linear_model.pkl")
        import joblib
        joblib.dump(model, model_path)
        mlflow.log_artifact(model_path)

        print("✅ Training finished!")

if __name__ == "__main__":
    main()
