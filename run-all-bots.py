import sys
import time
import subprocess
from pathlib import Path

SCRIPTS = [
    "central-bank.py",
    "linar-bank.py",
    "tax-authority.py",
]


def terminate_all(processes: list[tuple[str, subprocess.Popen]]) -> None:
    for _, proc in processes:
        if proc.poll() is None:
            proc.terminate()
    for _, proc in processes:
        if proc.poll() is None:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


def main() -> int:
    base_dir = Path(__file__).resolve().parent
    processes: list[tuple[str, subprocess.Popen]] = []

    for script in SCRIPTS:
        script_path = base_dir / script
        if not script_path.exists():
            print(f"Missing script: {script_path}")
            return 1
        proc = subprocess.Popen([sys.executable, str(script_path)], cwd=str(base_dir))
        processes.append((script, proc))
        print(f"Started {script} (pid={proc.pid})")

    exit_code = 0
    try:
        while True:
            for script, proc in processes:
                code = proc.poll()
                if code is not None:
                    print(f"{script} exited with code {code}. Stopping other bots...")
                    exit_code = code
                    raise RuntimeError("bot_exited")
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping bots...")
    except RuntimeError:
        pass
    finally:
        terminate_all(processes)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
