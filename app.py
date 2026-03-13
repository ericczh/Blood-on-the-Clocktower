"""
  cd /Users/wikiglobal/botc-assistant-py
  python3 app.py
  # 访问 http://localhost:5555

  如何给别人用

  最简单的方式：把这个项目推到 GitHub，然后部署到 Render.com（免费，支持 Python）:

  1. 项目根目录已有 requirements.txt
  2. 在 Render 创建 Web Service，指向你的 GitHub 仓库
  3. Start Command 填 python app.py（正式部署时换 gunicorn app:app）
  4. 自动分配 HTTPS 域名
"""

"""血染钟楼 · 说书人助手 — Flask 版"""
import json
import math
import os
import uuid
import time
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory

app = Flask(__name__)
app.secret_key = "botc-secret"

# Jinja2 注册 math 过滤器
app.jinja_env.filters["cos"] = math.cos
app.jinja_env.filters["sin"] = math.sin

BASE = Path(__file__).parent
DATA = BASE / "data"
IMG_DIR = DATA / "images"
CHAR_FILE = DATA / "characters.json"
SCRIPT_FILE = DATA / "scripts.json"
GAME_FILE = DATA / "games.json"

IMG_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}

TYPE_LABELS = {
    "townsfolk": "镇民",
    "outsider": "外来者",
    "minion": "爪牙",
    "demon": "恶魔",
    "traveller": "旅行者",
    "fabled": "传奇",
}

DISTRIBUTION = {
    5: [3, 0, 1, 1], 6: [3, 1, 1, 1], 7: [5, 0, 1, 1],
    8: [5, 1, 1, 1], 9: [5, 2, 1, 1], 10: [7, 0, 2, 1],
    11: [7, 1, 2, 1], 12: [7, 2, 2, 1], 13: [9, 0, 3, 1],
    14: [9, 1, 3, 1], 15: [9, 2, 3, 1],
}


# ── 数据读写 ──────────────────────────────────────────────

def load_json(path: Path) -> list:
    if path.exists():
        return json.loads(path.read_text("utf-8"))
    return []

def save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")

def get_characters() -> list[dict]:
    return load_json(CHAR_FILE)

def get_char_map() -> dict[str, dict]:
    return {c["id"]: c for c in get_characters()}

def save_characters(chars: list[dict]):
    save_json(CHAR_FILE, chars)

def get_scripts() -> list[dict]:
    return load_json(SCRIPT_FILE)

def save_scripts(scripts: list[dict]):
    save_json(SCRIPT_FILE, scripts)

def get_games() -> list[dict]:
    return load_json(GAME_FILE)

def save_games(games: list[dict]):
    save_json(GAME_FILE, games)


# ── 图片上传 ──────────────────────────────────────────────

def save_image(file) -> str:
    """保存上传图片，返回文件名"""
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        return ""
    filename = f"{uuid.uuid4().hex[:12]}{ext}"
    file.save(IMG_DIR / filename)
    return filename


# ── 页面路由 ──────────────────────────────────────────────

@app.route("/")
def index():
    games = get_games()
    active = [g for g in games if g.get("status") == "active"]
    finished = [g for g in games if g.get("status") == "finished"]
    return render_template("index.html", active=active, finished=finished, scripts=get_scripts())


# ── 角色管理 ──────────────────────────────────────────────

@app.route("/characters")
def characters():
    chars = get_characters()
    grouped = {}
    for c in chars:
        t = c.get("type", "townsfolk")
        grouped.setdefault(t, []).append(c)
    return render_template("characters.html", grouped=grouped, type_labels=TYPE_LABELS)


@app.route("/character/new", methods=["GET", "POST"])
@app.route("/character/<cid>/edit", methods=["GET", "POST"])
def character_edit(cid=None):
    chars = get_characters()
    char = None
    if cid:
        char = next((c for c in chars if c["id"] == cid), None)

    if request.method == "POST":
        new_id = request.form.get("id", "").strip()
        if not new_id:
            new_id = uuid.uuid4().hex[:8]

        # 处理图片：优先使用URL，其次使用上传文件
        image = ""
        if char:
            image = char.get("image", "")
        
        # 检查是否提供了URL
        image_url = request.form.get("image_url", "").strip()
        if image_url:
            # 如果旧图片是本地文件，删除它
            if image and not (image.startswith("http://") or image.startswith("https://")):
                if (IMG_DIR / image).exists():
                    (IMG_DIR / image).unlink()
            image = image_url
        else:
            # 没有URL，检查文件上传
            file = request.files.get("image_file")
            if file and file.filename:
                uploaded = save_image(file)
                if uploaded:
                    # 删除旧图片（仅当是本地文件时）
                    if image and not (image.startswith("http://") or image.startswith("https://")):
                        if (IMG_DIR / image).exists():
                            (IMG_DIR / image).unlink()
                    image = uploaded

        data = {
            "id": new_id,
            "name": request.form.get("name", "").strip(),
            "nameEn": request.form.get("nameEn", "").strip(),
            "type": request.form.get("type", "townsfolk"),
            "ability": request.form.get("ability", "").strip(),
            "image": image,
        }

        # 可选字段
        for field in ("firstNight", "otherNights"):
            val = request.form.get(field, "").strip()
            if val:
                data[field] = int(val)

        if request.form.get("causeDrunk"):
            data["causeDrunk"] = True
        if request.form.get("causePoison"):
            data["causePoison"] = True

        if cid:
            chars = [data if c["id"] == cid else c for c in chars]
        else:
            # 检查 id 重复
            if any(c["id"] == new_id for c in chars):
                new_id = f"{new_id}_{uuid.uuid4().hex[:4]}"
                data["id"] = new_id
            chars.append(data)

        save_characters(chars)
        return redirect(url_for("characters"))

    return render_template("character_edit.html", char=char, type_labels=TYPE_LABELS)


@app.route("/character/<cid>/delete", methods=["POST"])
def character_delete(cid):
    chars = [c for c in get_characters() if c["id"] != cid]
    save_characters(chars)
    return redirect(url_for("characters"))


# ── 剧本/板子管理 ────────────────────────────────────────

@app.route("/scripts")
def scripts():
    all_scripts = get_scripts()
    char_map = get_char_map()
    return render_template("scripts.html", scripts=all_scripts, char_map=char_map)


@app.route("/script/new", methods=["GET", "POST"])
@app.route("/script/<sid>/edit", methods=["GET", "POST"])
def script_edit(sid=None):
    all_scripts = get_scripts()
    script = None
    if sid:
        script = next((s for s in all_scripts if s["id"] == sid), None)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        selected = request.form.getlist("characters")

        if not name:
            return "请输入板子名称", 400

        if sid and script:
            script["name"] = name
            script["characterIds"] = selected
        else:
            new_script = {
                "id": uuid.uuid4().hex[:8],
                "name": name,
                "characterIds": selected,
            }
            all_scripts.append(new_script)

        save_scripts(all_scripts)
        return redirect(url_for("scripts"))

    chars = get_characters()
    grouped = {}
    for c in chars:
        t = c.get("type", "townsfolk")
        grouped.setdefault(t, []).append(c)

    selected_ids = set(script["characterIds"]) if script else set()
    return render_template("script_edit.html",
                           script=script, grouped=grouped,
                           type_labels=TYPE_LABELS, selected_ids=selected_ids)


@app.route("/script/<sid>/delete", methods=["POST"])
def script_delete(sid):
    scripts = [s for s in get_scripts() if s["id"] != sid]
    save_scripts(scripts)
    return redirect(url_for("scripts"))


# ── 对局管理 ─────────────────────────────────────────────

@app.route("/game/new", methods=["POST"])
def game_new():
    sid = request.form.get("script_id")
    player_count = int(request.form.get("player_count", 7))
    script = next((s for s in get_scripts() if s["id"] == sid), None)
    if not script:
        return redirect(url_for("index"))

    seats = []
    for i in range(1, player_count + 1):
        seats.append({
            "id": i, "playerName": "", "characterId": "",
            "alive": True, "hasVote": True, "drunkPoisoned": False,
            "notes": "", "claimedRole": "",
        })

    game = {
        "id": uuid.uuid4().hex[:8],
        "scriptId": sid,
        "scriptName": script["name"],
        "seats": seats,
        "days": [{"dayNumber": 0, "phase": "night", "nightActions": [], "nominations": [], "deaths": [], "notes": ""}],
        "createdAt": int(time.time()),
        "status": "active",
        "winner": "",
    }

    games = get_games()
    games.append(game)
    save_games(games)
    return redirect(url_for("game_view", gid=game["id"]))


@app.route("/game/<gid>")
def game_view(gid):
    games = get_games()
    game = next((g for g in games if g["id"] == gid), None)
    if not game:
        return redirect(url_for("index"))

    char_map = get_char_map()
    script = next((s for s in get_scripts() if s["id"] == game["scriptId"]), None)
    script_chars = []
    if script:
        script_chars = [char_map[cid] for cid in script["characterIds"] if cid in char_map]

    # 按类型分组
    grouped_chars = {}
    for c in script_chars:
        t = c.get("type", "townsfolk")
        grouped_chars.setdefault(t, []).append(c)

    dist = DISTRIBUTION.get(len(game["seats"]))
    return render_template("game.html", game=game, char_map=char_map,
                           grouped_chars=grouped_chars, type_labels=TYPE_LABELS, dist=dist)


@app.route("/game/<gid>/update", methods=["POST"])
def game_update(gid):
    """通用 AJAX 更新接口"""
    games = get_games()
    game = next((g for g in games if g["id"] == gid), None)
    if not game:
        return jsonify({"error": "not found"}), 404

    data = request.get_json(force=True)
    action = data.get("action")

    if action == "update_seat":
        seat_id = data["seatId"]
        for s in game["seats"]:
            if s["id"] == seat_id:
                for k in ("playerName", "characterId", "alive", "hasVote",
                          "drunkPoisoned", "notes", "claimedRole"):
                    if k in data:
                        s[k] = data[k]
                break

    elif action == "add_day":
        n = len(game["days"])
        game["days"].append({
            "dayNumber": n, "phase": "night",
            "nightActions": [], "nominations": [], "deaths": [], "notes": "",
        })

    elif action == "update_day":
        idx = data.get("dayIndex", 0)
        if 0 <= idx < len(game["days"]):
            for k in ("nightActions", "nominations", "deaths", "notes"):
                if k in data:
                    game["days"][idx][k] = data[k]

    elif action == "finish":
        game["status"] = "finished"
        game["winner"] = data.get("winner", "")

    save_games(games)
    return jsonify({"ok": True})


@app.route("/game/<gid>/delete", methods=["POST"])
def game_delete(gid):
    games = [g for g in get_games() if g["id"] != gid]
    save_games(games)
    return redirect(url_for("index"))


# ── 静态图片 ─────────────────────────────────────────────

@app.route("/images/<filename>")
def serve_image(filename):
    return send_from_directory(IMG_DIR, filename)


# ── API: 导出/导入 ───────────────────────────────────────

@app.route("/api/export/characters")
def api_export_chars():
    return jsonify(get_characters())

@app.route("/api/export/scripts")
def api_export_scripts():
    return jsonify(get_scripts())

@app.route("/api/import/characters", methods=["POST"])
def api_import_chars():
    data = request.get_json(force=True)
    if isinstance(data, list):
        chars = get_characters()
        existing_ids = {c["id"] for c in chars}
        for c in data:
            if c.get("id") not in existing_ids:
                chars.append(c)
        save_characters(chars)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True, port=5555)
