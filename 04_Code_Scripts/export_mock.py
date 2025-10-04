# 04_Code_Scripts/export_mock.py  — annule-et-remplace (minimal)
from pathlib import Path

def main():
    out = Path("data/mock")
    out.mkdir(parents=True, exist_ok=True)
    (out / "README.txt").write_text(
        "Placeholder mock data folder.\n"
        "Real mock generation can be added later if needed.\n",
        encoding="utf-8",
    )
    print("Mock exported to data/mock/")

if __name__ == "__main__":
    main()
