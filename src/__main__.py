import json
import os
import re
import textwrap

from github import Github

from src import parser


def main():
    if not os.path.exists("./config.json"):
        print("[ERROR] config.json not found.")
        exit(1)

    with open("./config.json", "r") as f:
        config = json.load(f)

    data = {
        "count": 0,
        "firstTime": None
    }
    if os.path.exists("./data.json"):
        with open("./data.json", "r") as f:
            data = json.load(f)

    logs = parser(config["path"])

    with open("./output.json", "w") as f:
        json.dump(logs, f)

    dataCount = len(logs)
    firstTime = logs[0]["time"]

    if firstTime == data["firstTime"]:
        logs = logs[data["count"]:]

    for log in logs:
        errorParser(log)

    with open("./data.json", "w") as f:
        json.dump({
            "count": dataCount,
            "firstTime": firstTime
        }, f)


def errorParser(log: dict):
    if log["level"] != "ERROR" and log["level"] != "WARN":
        return
    if "com.jaoafa.mymaid4" not in log["messages"]:
        return

    lines = log["messages"].split("\n")
    getCauseLine(log["time"], lines)


def isIssueCreated(file: str):
    if not os.path.exists("created.json"):
        return False

    with open("created.json", "r") as f:
        created = json.load(f)
        return file in created


def createIssue(file: str, title: str, body: str):
    with open("./config.json", "r") as f:
        config = json.load(f)
    g = Github(config["access_token"])
    repo = g.get_repo(config["repository"])
    repo.create_issue(title=title, body=body)

    created = []
    if os.path.exists("created.json"):
        with open("created.json", "r") as f:
            created = json.load(f)

    created.append(file)
    with open("created.json", "w") as f:
        json.dump(created, f)


def getCauseLine(datetime: str, messages: list):
    # 優先度: command -> customEvents -> event -> tasks -> discordEvent -> httpServer -> lib
    mymaid_messages = list(filter(lambda x: x.startswith("\tat com.jaoafa.mymaid4"), messages))
    regex = r"at (.+?)\((.+)\.java:([0-9]+)\)"
    mymaid_messages = list(map(lambda x: re.search(regex, x), mymaid_messages))

    matchCommand = list(filter(lambda x: x[0].startswith("at com.jaoafa.mymaid4.command"), mymaid_messages))
    matchCustomEvent = list(filter(lambda x: x[0].startswith("at com.jaoafa.mymaid4.customEvents"), mymaid_messages))
    matchEvent = list(filter(lambda x: x[0].startswith("at com.jaoafa.mymaid4.event"), mymaid_messages))
    matchTasks = list(filter(lambda x: x[0].startswith("at com.jaoafa.mymaid4.tasks"), mymaid_messages))
    matchDiscordEvent = list(filter(lambda x: x[0].startswith("at com.jaoafa.mymaid4.discordEvent"), mymaid_messages))
    matchHttpServer = list(filter(lambda x: x[0].startswith("at com.jaoafa.mymaid4.httpServer"), mymaid_messages))
    matchLib = list(filter(lambda x: x[0].startswith("at com.jaoafa.mymaid4.lib"), mymaid_messages))

    match = (
        matchCommand[0].groups() if len(matchCommand) != 0 else
        matchCustomEvent[0].groups() if len(matchCustomEvent) != 0 else
        matchEvent[0].groups() if len(matchEvent) != 0 else
        matchTasks[0].groups() if len(matchTasks) != 0 else
        matchDiscordEvent[0].groups() if len(matchDiscordEvent) != 0 else
        matchHttpServer[0].groups() if len(matchHttpServer) != 0 else
        matchLib[0].groups() if len(matchLib) != 0 else
        None
    )

    title = "[{0}:{1}] {2}".format(
        (match[1] if match is not None else "?"),
        (match[2] if match is not None else "?"),
        messages[1])

    body = textwrap.dedent("""
    ### Stacktrace
    {TITLE} ({DATE})

    ```
    {STACKTRACE}
    ```

    ### LINK

    {URL}
    """).format(
        TITLE=title,
        DATE=datetime,
        STACKTRACE="\n".join(messages),
        URL="https://github.com/jaoafa/MyMaid4/blob/master/src/main/java/{0}.java#L{1}".format(
            match[0][:match[0].rfind(".")].replace(".", "/"),
            match[2]
        ))
    print(title)
    print(body)

    print(match[0] + ":" + match[2])

    if isIssueCreated(match[0] + ":" + match[2]):
        return

    createIssue(match[0] + ":" + match[2], title, body)


if __name__ == "__main__":
    main()
