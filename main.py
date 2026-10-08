"""docker-compose service health checker.

Run this script to verify that all services defined in a docker‑compose
file report a healthy status.  Pass the compose file path with
`-f/--file` and an optional service name.  The script exits with 0
if all queried services are healthy, otherwise 1.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def get_compose_output(compose_file: Path, command: list[str]) -> str:
    """Run a docker‑compose command and return its stdout."""
    result = subprocess.run(
        ["docker-compose", "-f", str(compose_file)] + command,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def parse_health_status(compose_file: Path, services: list[str]) -> bool:
    """Return True if all requested services are healthy."""
    status_out = get_compose_output(compose_file, ["ps"])
    healthy = True
    for line in status_out.splitlines():
        parts = line.split()
        if not parts:
            continue
        name, state = parts[0], parts[1] if len(parts) > 1 else ""
        if services and name not in services:
            continue
        if "Up" not in state:
            healthy = False
            continue
        # State can be "Up (healthy)" or "Up (unhealthy)" or just "Up"
        if "(unhealthy)" in state or "(starting)" in state:
            healthy = False
    return healthy


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check docker‑compose service health status."
    )
    parser.add_argument(
        "-f",
        "--file",
        type=Path,
        default=Path("docker-compose.yml"),
        help="Path to docker‑compose file (default: docker-compose.yml)",
    )
    parser.add_argument(
        "services",
        nargs="*",
        help="Specific services to check (default: all services)",
    )
    args = parser.parse_args()

    try:
        healthy = parse_health_status(args.file, args.services)
    except subprocess.CalledProcessError as exc:
        print(f"Error running docker‑compose: {exc}", file=sys.stderr)
        sys.exit(2)

    if healthy:
        print("All services are healthy.")
        sys.exit(0)
    else:
        print("One or more services are not healthy.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()