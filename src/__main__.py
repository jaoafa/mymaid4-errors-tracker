import os
import json

from src import parser


def main():
    if not os.path.exists("../config.json"):
        print("[ERROR] config.json not found.")
        exit(1)

    with open("../config.json", "r") as f:
        config = json.load(f)

    data = {
        "count": 0,
        "firstTime": None
    }
    if os.path.exists("../data.json"):
        with open("../data.json", "r") as f:
            data = json.load(f)

    logs = parser(config["path"])

    with open("../output.json", "w") as f:
        json.dump(logs, f)

    dataCount = len(logs)
    firstTime = logs[0]["time"]

    if firstTime == data["firstTime"]:
        logs = logs[data["count"]:]

    print(logs)

    with open("../data.json", "w") as f:
        json.dump({
            "count": dataCount,
            "firstTime": firstTime
        }, f)


if __name__ == "__main__":
    main()
