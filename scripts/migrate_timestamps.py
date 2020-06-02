"""
Convert timestamps in replies.json file from float to ISO string.

"""
import json
from datetime import datetime
from datetime import timezone


def fix_timestamps(filename: str) -> None:
    with open(filename) as fp:
        contents = fp.read()

    replies = json.loads(contents)

    for reply in replies:
        try:
            timestamp = int(float(reply["timestamp"]))
        except ValueError:
            continue

        reply["timestamp"] = (
            datetime.fromtimestamp(timestamp).astimezone(timezone.utc).isoformat()
        )

    contents = json.dumps(replies)
    with open(filename, "w") as fp:
        fp.write(contents)


if __name__ == "__main__":
    import sys

    filename = sys.argv[1]
    fix_timestamps(filename)
