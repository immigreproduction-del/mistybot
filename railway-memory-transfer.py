"""Remote transfer helper, sent over SSH stdin; never starts the Discord bot."""

import base64
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time

MAX_BYTES = 20 * 1024 * 1024


def digest(data):
    return hashlib.sha256(data).hexdigest()


def validate(data):
    if not 2 <= len(data) <= MAX_BYTES:
        raise ValueError("Memoire vide ou trop volumineuse (maximum 20 Mo).")
    if not isinstance(json.loads(data.decode("utf-8-sig")), dict):
        raise ValueError("La memoire doit contenir un objet JSON.")


def volume_path():
    path = Path(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", ""))
    if str(path) != "/app/data" or not path.is_dir():
        raise ValueError("Monter le volume Railway sur /app/data avant de continuer.")
    return path


def require_stopped(process_root=Path("/proc")):
    if not process_root.is_dir():
        raise ValueError("Impossible de verifier si le bot est arrete.")
    for entry in process_root.glob("[0-9]*/cmdline"):
        try:
            args = entry.read_bytes().split(b"\0")
        except FileNotFoundError:
            continue
        except PermissionError:
            raise ValueError("Impossible de verifier tous les processus du bot.")
        if any(arg.rsplit(b"/", 1)[-1] == b"main.py" for arg in args):
            pid = entry.parent.name
            shown = " ".join(a.decode("utf-8", "replace") for a in args if a)[:200]
            raise ValueError("Bot cible actif (processus " + pid + " : " + shown
                             + ") : deployer avec sleep infinity puis reessayer.")


def snapshot(path):
    for attempt in range(3):
        with path.open("rb") as stream:
            data = stream.read(MAX_BYTES + 1)
        try:
            validate(data)
            return data
        except (ValueError, UnicodeError):
            if attempt == 2:
                raise ValueError("memory.json invalide ou en cours d'ecriture. Reessayer.")
            time.sleep(0.25)


def sync_directory(root):
    directory_fd = os.open(root, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def restore(root, request, process_root=Path("/proc")):
    import fcntl

    transfer_id = request["transfer_id"]
    if not re.fullmatch(r"[A-Za-z0-9-]{1,80}", transfer_id):
        raise ValueError("Identifiant de transfert invalide.")
    data = base64.b64decode(request["data"], validate=True)
    validate(data)
    expected = request["sha256"]
    if digest(data) != expected:
        raise ValueError("Empreinte source incorrecte : restauration refusee.")
    destination = root / "memory.json"
    if destination.is_symlink():
        raise ValueError("memory.json est un lien symbolique : restauration refusee.")
    with (root / ".misty-transfer.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require_stopped(process_root)
        if destination.exists() and digest(destination.read_bytes()) == expected:
            return {"sha256": expected, "bytes": len(data), "unchanged": True}
        backup = root / ("memory-before-transfer-" + transfer_id + ".json")
        fd, temporary = tempfile.mkstemp(prefix=".misty-memory-", dir=root)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            if digest(Path(temporary).read_bytes()) != expected:
                raise ValueError("La verification du fichier temporaire a echoue.")
            if destination.exists():
                previous = destination.read_bytes()
                with backup.open("xb") as stream:
                    stream.write(previous)
                    stream.flush()
                    os.fsync(stream.fileno())
                if backup.read_bytes() != previous:
                    raise ValueError("Sauvegarde cible incorrecte : remplacement annule.")
            require_stopped(process_root)
            os.replace(temporary, destination)
            sync_directory(root)
            actual = digest(destination.read_bytes())
            if actual != expected:
                raise ValueError("La memoire cible a change apres la restauration.")
            return {"sha256": actual, "bytes": len(data),
                    "backup": str(backup) if backup.exists() else None}
        finally:
            Path(temporary).unlink(missing_ok=True)


def run(request):
    os.umask(0o077)
    operation = request.get("operation")
    try:
        root = volume_path()
        if operation == "probe":
            require_stopped()
            result = {"ready": True}
        elif operation == "export":
            data = snapshot(root / "memory.json")
            result = {"sha256": digest(data), "data": base64.b64encode(data).decode("ascii")}
        elif operation == "restore":
            result = restore(root, request)
        else:
            raise ValueError("Operation inconnue.")
        result.update(ok=True, operation=operation, transfer_id=request["transfer_id"])
    except Exception as exc:
        result = {"ok": False, "operation": operation,
                  "transfer_id": request.get("transfer_id"), "error": str(exc)}
    print("MISTY_RESULT:" + json.dumps(result, ensure_ascii=True), flush=True)
    if not result["ok"]:
        raise SystemExit(1)
