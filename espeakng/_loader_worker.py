"""Subprocess entry point for the isolated espeakng-loader backend."""

import json
import sys

from espeakng._native import synthesize


def main():
    request = json.load(sys.stdin)
    if request.get("protocol") != 1:
        raise RuntimeError("Unsupported loader worker protocol")

    synthesize(
        phrase=request["phrase"],
        voice=request["voice"],
        wpm=request["wpm"],
        pitch=request["pitch"],
        amplitude=request["amplitude"],
        wordgap=request["wordgap"],
        export_path=request.get("export_path"),
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        json.dump(
            {"type": type(exc).__name__, "message": str(exc)},
            sys.stderr,
        )
        sys.stderr.write("\n")
        raise SystemExit(1)
