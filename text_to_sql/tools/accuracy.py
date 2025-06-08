import os
import pandas as pd

folder_path = "files/experiment_result/deepseek_soccer"

results = []

for filename in os.listdir(folder_path):
    if filename.endswith(".csv"):
        file_path = os.path.join(folder_path, filename)
        df = pd.read_csv(file_path)
        
        if "Execution Accuracy" in df.columns:
            final_accuracy = df["Execution Accuracy"].mean()
        else:
            final_accuracy = None

        results.append({
            "filename": filename,
            "final_execution_accuracy": final_accuracy
        })

summary_df = pd.DataFrame(results)
summary_df = summary_df.sort_values(by="final_execution_accuracy", ascending=False)
print(summary_df)
