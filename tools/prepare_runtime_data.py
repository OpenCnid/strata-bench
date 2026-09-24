"""Build the exact offline runtime-data agent from previously acquired files."""

import argparse
import json
from pathlib import Path

from mcbench.runtime_data import prepare_runtime_data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--javac", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    result = prepare_runtime_data(json.loads(args.inputs.read_text(encoding="utf-8")), args.javac, args.destination)
    print(json.dumps({k: result[k] for k in ("policy", "jar_sha256", "jar_bytes", "installed")}))


if __name__ == "__main__":
    main()
