import os
import re
import sys
import socket
import threading
import webbrowser
from pathlib import Path
from datetime import datetime

from flask import Flask, jsonify, request, render_template


def _resource_dir() -> Path:
    """templates/static の場所。PyInstaller frozen 時は展開先の一時ディレクトリを使う。"""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


def _app_dir() -> Path:
    """タスクフォルダのデフォルト親ディレクトリ。実行ファイルと同じ場所を使う。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def _find_free_port(start: int = 5000) -> int:
    for port in range(start, start + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start


_resource = _resource_dir()
app = Flask(
    __name__,
    template_folder=str(_resource / "templates"),
    static_folder=str(_resource / "static"),
)

CONFIG = {"tasks_dir": str(_app_dir() / "tasks")}

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)


def get_tasks_dir() -> Path:
    p = Path(CONFIG["tasks_dir"])
    p.mkdir(parents=True, exist_ok=True)
    return p


def parse_md(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    status = "todo"
    created = None
    body = content

    m = FRONTMATTER_RE.match(content)
    if m:
        for line in m.group(1).splitlines():
            if line.startswith("status:"):
                status = line.split(":", 1)[1].strip()
            elif line.startswith("created:"):
                created = line.split(":", 1)[1].strip()
        body = content[m.end():]

    return {
        "id": path.stem,
        "title": path.stem,
        "status": status,
        "created": created,
        "body": body.strip(),
    }


def write_md(path: Path, status: str, created: str, body: str = "") -> None:
    front = f"---\nstatus: {status}\ncreated: {created}\n---\n"
    path.write_text(front + (body + "\n" if body else ""), encoding="utf-8")


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/tasks")
def list_tasks():
    tasks_dir = get_tasks_dir()
    tasks = []
    for f in sorted(tasks_dir.glob("*.md")):
        tasks.append(parse_md(f))
    return jsonify(tasks)


@app.post("/api/tasks")
def create_task():
    data = request.get_json()
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400

    # Sanitize filename
    safe = re.sub(r'[\\/:*?"<>|]', "_", title)
    tasks_dir = get_tasks_dir()
    path = tasks_dir / f"{safe}.md"
    if path.exists():
        return jsonify({"error": "task already exists"}), 409

    created = datetime.now().strftime("%Y-%m-%d")
    write_md(path, "todo", created)
    return jsonify(parse_md(path)), 201


@app.patch("/api/tasks/<task_id>")
def update_task(task_id: str):
    tasks_dir = get_tasks_dir()
    path = tasks_dir / f"{task_id}.md"
    if not path.exists():
        return jsonify({"error": "not found"}), 404

    data = request.get_json()
    task = parse_md(path)

    if "status" in data:
        task["status"] = data["status"]
    write_md(path, task["status"], task["created"] or "", task["body"])
    return jsonify(parse_md(path))


@app.delete("/api/tasks/<task_id>")
def delete_task(task_id: str):
    tasks_dir = get_tasks_dir()
    path = tasks_dir / f"{task_id}.md"
    if not path.exists():
        return jsonify({"error": "not found"}), 404
    path.unlink()
    return "", 204


@app.get("/api/settings")
def get_settings():
    return jsonify({"tasks_dir": CONFIG["tasks_dir"]})


@app.post("/api/settings")
def update_settings():
    data = request.get_json()
    new_dir = (data.get("tasks_dir") or "").strip()
    if not new_dir:
        return jsonify({"error": "tasks_dir is required"}), 400
    CONFIG["tasks_dir"] = new_dir
    get_tasks_dir()  # create dir if needed
    return jsonify({"tasks_dir": CONFIG["tasks_dir"]})


if __name__ == "__main__":
    is_frozen = getattr(sys, "frozen", False)
    port = _find_free_port(5000)
    url = f"http://localhost:{port}"

    if is_frozen:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
        print(f"起動中: {url}")
        app.run(debug=False, port=port)
    else:
        app.run(debug=True, port=port)
