#!/usr/bin/env python3
"""Start FloodGuard.

    python run.py           start everything (mock IMD + API + web)
    python run.py api       start just one  (mock | api | web)
    python run.py check     are the services up?
    python run.py doctor    diagnose setup + verify the Gemini key works

Ctrl+C stops everything it started.
"""
import argparse
import os
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_PY = ROOT / ".venv" / "bin" / "python"
if os.name == "nt":                              # Windows layout
    VENV_PY = ROOT / ".venv" / "Scripts" / "python.exe"

# name → (port, command, working directory, colour)
SERVICES = {
    "mock": (8080, [str(VENV_PY), "-m", "uvicorn", "mock_imd_server:app",
                    "--port", "8080", "--app-dir", "apps/mock-imd", "--reload"], ROOT, "36"),
    "api":  (8000, [str(VENV_PY), "-m", "uvicorn", "app.main:app",
                    "--port", "8000", "--reload"], ROOT / "apps" / "api", "33"),
    "web":  (3000, ["npm", "run", "dev"], ROOT / "apps" / "web", "35"),
}
ORDER = ["mock", "api", "web"]


def colour(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if sys.stdout.isatty() else text


def port_busy(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.4)
        return s.connect_ex(("127.0.0.1", port)) == 0


def preflight(names: list[str]) -> bool:
    """Fail early with a fix, rather than a stack trace thirty seconds in."""
    problems = []

    if not VENV_PY.exists() and ({"mock", "api"} & set(names)):
        problems.append(f"No virtualenv at {VENV_PY.parent.parent}\n"
                        f"     fix: python3.11 -m venv .venv && "
                        f".venv/bin/pip install -r apps/api/requirements.txt")

    if "web" in names:
        if not shutil.which("npm"):
            problems.append("npm is not on PATH — install Node.js 18+")
        elif not (ROOT / "apps" / "web" / "node_modules").exists():
            problems.append("Web dependencies missing\n     fix: cd apps/web && npm install")

    if "api" in names:
        if not (ROOT / "services" / "ml" / "models" / "flood_severity_hgb.joblib").exists():
            problems.append("No trained model — /predictions will return 503\n"
                            "     fix: .venv/bin/python services/ml/training/train_flood_severity.py")
        if not (ROOT / "services" / "rag" / "chroma_db").exists():
            problems.append("No vector store — /chat will return 503\n"
                            "     fix: .venv/bin/python services/rag/fast_ingest.py --reset")

    for name in names:
        if port_busy(SERVICES[name][0]):
            problems.append(f"Port {SERVICES[name][0]} is already in use ({name} may be running)")

    for p in problems:
        print(f"  {colour('!', '31')} {p}")
    return not problems


def pump(stream, name: str, code: str) -> None:
    """Tag each line so three services in one terminal stay readable."""
    tag = colour(f"{name:<5}", code)
    for line in iter(stream.readline, ""):
        print(f"{tag} │ {line.rstrip()}", flush=True)
    stream.close()


def start(names: list[str]) -> None:
    procs = []
    for name in names:
        port, cmd, cwd, code = SERVICES[name]
        proc = subprocess.Popen(
            cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
        procs.append((name, proc))
        threading.Thread(target=pump, args=(proc.stdout, name, code), daemon=True).start()
        print(f"  {colour('▸', code)} {name:<5} starting on :{port}")

    print()
    for name in names:
        port = SERVICES[name][0]
        for _ in range(60):
            if port_busy(port):
                print(f"  {colour('✓', '32')} {name:<5} http://localhost:{port}")
                break
            if all(p.poll() is not None for _, p in procs if _ == name):
                print(f"  {colour('✗', '31')} {name:<5} exited during startup")
                break
            time.sleep(1)
        else:
            print(f"  {colour('✗', '31')} {name:<5} did not open :{port} in 60s")

    if "web" in names:
        print(f"\n  Open {colour('http://localhost:3000', '1;32')}\n")
    print("  Ctrl+C to stop.\n")

    def shutdown(*_):
        print("\n  stopping…")
        for _, proc in procs:
            if proc.poll() is None:
                proc.terminate()
        for _, proc in procs:
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    while True:                                  # a crash should not go unnoticed
        for name, proc in procs:
            if proc.poll() is not None:
                print(f"  {colour('✗', '31')} {name} exited (code {proc.returncode}) — stopping the rest")
                shutdown()
        time.sleep(1)


def check() -> None:
    import urllib.request
    targets = [("mock", "http://127.0.0.1:8080/"),
               ("api", "http://127.0.0.1:8000/health"),
               ("web", "http://127.0.0.1:3000/"),
               ("proxy", "http://127.0.0.1:3000/api/health")]
    for name, url in targets:
        try:
            with urllib.request.urlopen(url, timeout=4) as r:
                print(f"  {colour('✓', '32')} {name:<6} {r.status}  {url}")
        except Exception as exc:
            print(f"  {colour('✗', '31')} {name:<6} down  ({exc.__class__.__name__})")


def doctor() -> None:
    """Diagnose configuration — especially whether the Gemini key actually works."""
    import json
    import urllib.request

    ok = lambda t: print(f"  {colour('✓', '32')} {t}")
    bad = lambda t: print(f"  {colour('✗', '31')} {t}")
    warn = lambda t: print(f"  {colour('!', '33')} {t}")

    print("\n  Setup")
    ok(f"virtualenv {VENV_PY.parent.parent.name}") if VENV_PY.exists() else \
        bad("no virtualenv — python3.11 -m venv .venv")
    ok("web dependencies installed") if (ROOT / "apps/web/node_modules").exists() else \
        bad("cd apps/web && npm install")
    ok("severity model trained") if (ROOT / "services/ml/models/flood_severity_hgb.joblib").exists() else \
        bad(".venv/bin/python services/ml/training/train_flood_severity.py")
    ok("RAG vector store built") if (ROOT / "services/rag/chroma_db").exists() else \
        bad(".venv/bin/python services/rag/fast_ingest.py --reset")

    print("\n  Configuration")
    env = ROOT / "apps" / "api" / ".env"
    key = ""
    if not env.exists():
        bad("apps/api/.env missing — cp apps/api/.env.example apps/api/.env")
    else:
        ok("apps/api/.env present")
        for line in env.read_text().splitlines():
            if line.strip().startswith("GEMINI_API_KEY="):
                key = line.split("=", 1)[1].strip()
        if key:
            ok(f"GEMINI_API_KEY set ({key[:6]}…{key[-4:]}, {len(key)} chars)")
        elif False:
            pass
        else:
            warn("GEMINI_API_KEY blank — /chat returns source passages instead of "
                 "written answers, summaries use a template. Everything else works.")
        owkey = ""
        for line in env.read_text().splitlines():
            if line.strip().startswith("OPENWEATHER_API_KEY="):
                owkey = line.split("=", 1)[1].strip()
        if owkey:
            ok(f"OPENWEATHER_API_KEY set ({owkey[:6]}…{owkey[-4:]}) — live conditions enabled")
        else:
            warn("OPENWEATHER_API_KEY blank — no live weather; IMD mock only")

    ok("apps/web/.env.local present") if (ROOT / "apps/web/.env.local").exists() else \
        warn("apps/web/.env.local missing — defaults to http://localhost:8000")

    print("\n  Services")
    if not port_busy(8000):
        warn("API not running — start it with `python run.py` to test the key live")
        print()
        return
    check()

    print("\n  Live sources")
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=10) as r:
            h = json.load(r)
        src = h.get("sources", {})
        if src.get("openweather", {}).get("configured"):
            ok("OpenWeather — real observed conditions + forecast")
        else:
            warn("OpenWeather not configured")
        warn("IMD — mock server (real API needs government credentials)")
        db = h.get("database", {})
        ok(f"{db.get('observations', 0)} observations · {db.get('events', 0)} correlated events")
    except Exception as exc:
        bad(f"could not read /health ({exc.__class__.__name__})")

    print("\n  Gemini (live call)")
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/llm/check", timeout=90) as r:
            res = json.load(r)

        # Settings are read once at import and --reload only watches .py files, so
        # editing .env under a live server changes nothing until it restarts. Compare
        # fingerprints to catch that, instead of reporting it as a bad key.
        import hashlib
        want = hashlib.sha256(key.encode()).hexdigest()[:8] if key else None
        got = None
        try:
            with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=10) as r:
                got = json.load(r).get("llm", {}).get("key_fingerprint")
        except Exception:
            pass

        if want != got:
            bad("the running API is using a different GEMINI_API_KEY than apps/api/.env "
                "— restart it (Ctrl+C, then `python run.py`)")
        elif res.get("ok"):
            ok(f"{res['model']} responded in {res['latency_ms']}ms — chat and summaries "
               f"will be AI-written")
        elif res.get("reason") == "no_key":
            warn("no key configured (see above)")
        else:
            bad(f"[{res.get('reason')}] {res.get('error')}")
    except Exception as exc:
        bad(f"could not reach /llm/check ({exc.__class__.__name__})")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Start FloodGuard.")
    parser.add_argument("service", nargs="?", default="all",
                        choices=["all", "mock", "api", "web", "check", "doctor"])
    args = parser.parse_args()

    if args.service == "check":
        return check()
    if args.service == "doctor":
        return doctor()

    names = ORDER if args.service == "all" else [args.service]
    print(f"\n  FloodGuard — starting {', '.join(names)}\n")
    if not preflight(names):
        sys.exit(1)
    start(names)


if __name__ == "__main__":
    main()
