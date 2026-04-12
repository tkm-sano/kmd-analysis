from __future__ import annotations

from src.analysis import run_pipeline


if __name__ == "__main__":
    results = run_pipeline()
    print("分析が完了した。")
    print("主要結果")
    for key, value in results["summary"].items():
        print(f"- {key}: {value}")
