import pandas as pd
import os
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_path", default="./test_data/train_local.csv")
    parser.add_argument("--output_path", default="./test_data/processed/train_local_processed.csv")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output_path), exist_ok=True)

    print(f"📂 Loading dataset from {args.input_path}...")
    df = pd.read_csv(args.input_path)

    print("🔧 Performing mock ETL...")
    df["processed"] = df["value"] * 2  # simple transformation

    print(f"💾 Saving processed dataset to {args.output_path}")
    df.to_csv(args.output_path, index=False)

if __name__ == "__main__":
    main()
