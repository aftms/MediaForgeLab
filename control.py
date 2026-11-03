"""Start/stop this miniportal only; no changes to the Gateway runtime."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request

BASE = Path(__file__).resolve().parent
RUNTIME = BASE / ".runtime"
STATE = RUNTIME / "server.json"
CONFIG = BASE / "config.local.json"


def request(url, token=None):
    headers = {"X-MAG-Control": token} if token else {}
    data = b"" if token else None
    # Explicit direct LAN connection, never a system/environment proxy.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(urllib.request.Request(url, headers=headers, data=data), timeout=2) as response:
        return json.load(response)


def live():
    try:
        saved = json.loads(STATE.read_text(encoding="utf-8"))
        from server import APP_ID, load_config
        cfg = load_config(CONFIG)
        expected = "http://%s:%s" % (cfg["host"], cfg["port"])
        if saved["url"] != expected:
            return None
        health = request(expected + "/api/health")
        if health.get("app") == APP_ID and health.get("instance") == saved["instance"] and health.get("pid") == saved["pid"]:
            return saved
    except (OSError, ValueError, KeyError):
        pass
    return None


def start():
    if not CONFIG.exists():
        shutil.copyfile(BASE / "config.example.json", CONFIG)
    previous = live()
    if previous:
        print("Portal ja ativo: " + previous["url"] + "/index.html")
        return 0
    from server import load_config
    cfg = load_config(CONFIG)
    RUNTIME.mkdir(exist_ok=True)
    flags = 0
    executable = sys.executable
    if os.name == "nt":
        candidate = Path(executable).with_name("pythonw.exe")
        if candidate.exists():
            executable = str(candidate)
        flags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
    # Inherit only basic OS variables; never the repository's environment/tokens.
    keep = ("SYSTEMROOT", "WINDIR", "TEMP", "TMP", "LOCALAPPDATA", "PATH")
    child_env = {key: os.environ[key] for key in keep if key in os.environ}
    child = subprocess.Popen([executable, str(BASE / "server.py"), "--config", str(CONFIG)],
                             cwd=str(BASE), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, creationflags=flags, env=child_env,
                             start_new_session=os.name != "nt")
    for _ in range(180):
        active = live()
        if active and active["pid"] == child.pid:
            print("Portal ativo em segundo plano: " + active["url"] + "/index.html")
            print("Parar: parar-portal.bat | Estado: estado-portal.bat")
            return 0
        if child.poll() is not None:
            break
        time.sleep(0.25)
    print("Nao foi possivel arrancar. Verifique IP/porta, lista e .runtime/startup-error.txt.")
    return 1


def stop():
    active = live()
    if not active:
        print("Portal nao esta ativo ou a identidade nao foi confirmada; nenhum processo foi parado.")
        return 0
    request(active["url"] + "/__stop", active["control"])
    for _ in range(30):
        if not live():
            print("Portal parado.")
            return 0
        time.sleep(0.2)
    print("A paragem ainda nao foi confirmada.")
    return 1


def start_manager():
    """Keep management available even when the portal itself is stopped."""
    url = 'http://127.0.0.1:8092/health'
    try:
        return 0 if request(url).get('app') == 'magforgelab-manager' else 1
    except (OSError, ValueError):
        pass
    executable = Path(sys.executable)
    candidate = executable.with_name('pythonw.exe')
    if os.name == 'nt' and candidate.exists():
        executable = candidate
    keep = ('SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'LOCALAPPDATA', 'PATH')
    child = subprocess.Popen([str(executable), str(BASE/'admin_service.py')], cwd=str(BASE),
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        env={k:os.environ[k] for k in keep if k in os.environ},
        creationflags=(subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS) if os.name=='nt' else 0,
        start_new_session=os.name!='nt')
    for _ in range(20):
        try:
            if request(url).get('app') == 'magforgelab-manager':
                return 0
        except (OSError, ValueError):
            pass
        if child.poll() is not None:
            break
        time.sleep(.1)
    print('Painel de gestão indisponível na porta 8092. O portal pode ser controlado pelos ficheiros BAT.')
    return 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("start", "stop", "status", "manage"))
    action = parser.parse_args().action
    try:
        if action == "start":
            start_manager()
            return start()
        if action == "manage":
            return start_manager()
        if action == "stop":
            return stop()
        active = live()
        print("Portal ativo: " + active["url"] + "/index.html" if active else "Portal parado.")
        return 0 if active else 1
    except Exception as error:
        print("Operacao nao concluida: " + type(error).__name__)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
