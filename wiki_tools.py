"""
血染钟楼 · Wiki 工具集

用法：
  .venv/bin/python wiki_tools.py import [--force] [--dry]
      从 Wiki 抓取所有角色并导入数据库
      --force  同时更新已存在的角色
      --dry    只预览，不写数据库

  .venv/bin/python wiki_tools.py import-scripts [--force] [--dry]
      从 Wiki 抓取官方基础剧本并导入数据库
      --force  同时更新已存在的剧本
      --dry    只预览，不写数据库

  .venv/bin/python wiki_tools.py export-scripts [--out data/scripts.json]
      将数据库中的剧本导出为默认种子文件

  .venv/bin/python wiki_tools.py export [--dir data/by_type]
      将数据库角色按阵营类型导出为独立 JSON 文件
      输出：townsfolk.json / outsider.json / minion.json / demon.json / traveller.json / fabled.json

  .venv/bin/python wiki_tools.py auto-tag
      对所有角色按能力描述文字自动推断并保存筛选标签

  .venv/bin/python wiki_tools.py all [--force]
      依次执行 import → auto-tag → export（一键全流程）
"""
import os
import re
import sys
import json
import hashlib
import argparse

sys.path.insert(0, os.path.dirname(__file__))

TYPE_NAMES = {
    "townsfolk": "镇民",
    "outsider":  "外来者",
    "minion":    "爪牙",
    "demon":     "恶魔",
    "traveller": "旅行者",
    "fabled":    "传奇角色",
    "fabled2":   "奇遇角色",
}


def _char_id(char: dict) -> str:
    name_en = char.get("name_en", "").strip()
    if name_en:
        return re.sub(r"[^a-z0-9]", "", name_en.lower())
    return "cn_" + hashlib.md5(char["name"].encode()).hexdigest()[:8]


# ─────────────────────────────────────────────────────────────
# 子命令：import
# ─────────────────────────────────────────────────────────────
def cmd_import(args):
    import time
    import ssl
    import urllib.request
    import urllib.parse
    from utils.wiki_scraper import (
        CATEGORY_MAP, WIKI_BASE, SKIP_TITLES,
        scrape_character, _fetch,
    )
    from app_new import create_app
    from models import db, Character
    from services.character_service import _infer_tags

    print("=" * 60)
    print("  血染钟楼 · Wiki 角色导入（实时写库）")
    print("=" * 60)

    import re as _re

    def _gallery_links(html: str, char_type: str) -> list[dict]:
        """从分类页 gallery 块提取角色链接"""
        import re
        items = re.findall(r'<li\s+class="gallerybox"[^>]*>(.*?)</li>', html, re.DOTALL)
        results, seen = [], set()
        for item in items:
            m = re.search(r'href="(/index\.php\?title=([^"#&]+))"', item)
            if not m:
                continue
            title = urllib.parse.unquote(m.group(2))
            url   = WIKI_BASE + m.group(1)
            if title in SKIP_TITLES or url in seen or ":" in title:
                continue
            seen.add(url)
            results.append({"url": url, "name": title, "type": char_type})
        return results

    # 先启动 Flask App Context，后续所有 DB 操作都在里面
    app = create_app("development")
    with app.app_context():
        imported = updated = skipped = 0
        delay = 0.6

        for slug, char_type in CATEGORY_MAP.items():
            category_url = f"{WIKI_BASE}/index.php?title={slug}"
            print(f"\n[{char_type}] {urllib.parse.unquote(slug)}")
            try:
                html = _fetch(category_url)
            except Exception as exc:
                print(f"  ! 分类页抓取失败: {exc}")
                continue

            links = _gallery_links(html, char_type)
            print(f"  找到 {len(links)} 个角色链接")
            time.sleep(delay)

            for item in links:
                print(f"  抓取: {item['name']} …", end=" ", flush=True)
                try:
                    c = scrape_character(item["url"])
                except Exception as exc:
                    print(f"✗ {exc}")
                    time.sleep(delay)
                    continue

                if not c:
                    print("✗ 无数据")
                    time.sleep(delay)
                    continue

                c["type"] = char_type
                cid = _char_id(c)

                if getattr(args, 'dry', False):
                    print(f"[dry] {cid}")
                    time.sleep(delay)
                    continue

                tags = _infer_tags(c.get("ability", "") or "")
                existing = Character.query.filter_by(id=cid).first()

                if existing:
                    if args.force:
                        existing.name    = c["name"]
                        existing.name_en = c.get("name_en", existing.name_en)
                        existing.type    = char_type
                        if c.get("ability"): existing.ability = c["ability"]
                        if c.get("image"):   existing.image   = c["image"]
                        for f, v in tags.items(): setattr(existing, f, v)
                        existing.deleted_at = None
                        db.session.commit()
                        print(f"↺ 已更新")
                        updated += 1
                    else:
                        print(f"- 已存在，跳过")
                        skipped += 1
                else:
                    char = Character(
                        id=cid,
                        name=c["name"],
                        name_en=c.get("name_en", ""),
                        type=char_type,
                        ability=c.get("ability", ""),
                        image=c.get("image", ""),
                        **tags,
                    )
                    db.session.add(char)
                    db.session.commit()   # ← 立即写库
                    print(f"✓ 已写入")
                    imported += 1

                time.sleep(delay)

        if not args.dry:
            print(f"\n{'='*60}")
            print(f"完成：新增 {imported} 个，更新 {updated} 个，跳过 {skipped} 个")


def cmd_import_scripts(args):
    from utils.wiki_scraper import scrape_character, scrape_official_scripts
    from app_new import create_app
    from models import db, Character, Script
    from services.character_service import _infer_tags

    print("=" * 60)
    print("  血染钟楼 · Wiki 剧本导入")
    print("=" * 60)

    app = create_app("development")
    with app.app_context():
        imported = updated = skipped = 0

        for script_data in scrape_official_scripts(delay=0.5):
            character_ids = []
            missing = []

            for item in script_data["characters"]:
                character = Character.query.filter_by(name=item["name"], deleted_at=None).first()

                if not character:
                    try:
                        scraped = scrape_character(item["url"])
                    except Exception as exc:
                        print(f"  ! 角色补抓失败 {item['name']}: {exc}")
                        missing.append(item["name"])
                        continue

                    if not scraped:
                        missing.append(item["name"])
                        continue

                    cid = _char_id(scraped)
                    character = Character.query.filter_by(id=cid, deleted_at=None).first()
                    if not character:
                        tags = _infer_tags(scraped.get("ability", "") or "")
                        character = Character(
                            id=cid,
                            name=scraped["name"],
                            name_en=scraped.get("name_en", ""),
                            type=item.get("type", "townsfolk"),
                            ability=scraped.get("ability", ""),
                            image=scraped.get("image", ""),
                            **tags,
                        )
                        db.session.add(character)
                        db.session.commit()
                        print(f"  + 已补抓角色: {scraped['name']} ({character.id})")

                if character:
                    character_ids.append(character.id)
                else:
                    missing.append(item["name"])

            if missing:
                print(f"  ! 剧本 {script_data['name']} 缺少角色: {', '.join(missing)}")
                if not args.force:
                    print("  - 未开启 --force，跳过该剧本")
                    skipped += 1
                    continue

            if args.dry:
                print(f"  [dry] {script_data['id']}: {len(character_ids)} 个角色")
                continue

            existing = Script.query.filter_by(id=script_data["id"]).first()
            payload = json.dumps(character_ids, ensure_ascii=False)

            if existing:
                if args.force:
                    existing.name = script_data["name"]
                    existing.character_ids = payload
                    existing.deleted_at = None
                    db.session.commit()
                    print(f"  ↺ 已更新: {script_data['name']} ({len(character_ids)} 个角色)")
                    updated += 1
                else:
                    print(f"  - 已存在，跳过: {script_data['name']}")
                    skipped += 1
            else:
                script = Script(
                    id=script_data["id"],
                    name=script_data["name"],
                    character_ids=payload,
                )
                db.session.add(script)
                db.session.commit()
                print(f"  ✓ 已写入: {script_data['name']} ({len(character_ids)} 个角色)")
                imported += 1

        if not args.dry:
            print(f"\n{'='*60}")
            print(f"完成：新增 {imported} 个，更新 {updated} 个，跳过 {skipped} 个")


def cmd_export_scripts(args):
    from app_new import create_app
    from models import Script

    out_path = os.path.join(os.path.dirname(__file__), args.out)

    app = create_app("development")
    with app.app_context():
        scripts = (
            Script.query
            .filter_by(deleted_at=None)
            .order_by(Script.id.asc())
            .all()
        )
        payload = [s.to_dict() for s in scripts]

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"已导出 {len(payload)} 个剧本到 {out_path}")


# ─────────────────────────────────────────────────────────────
# 子命令：export
# ─────────────────────────────────────────────────────────────
def cmd_export(args):
    from app_new import create_app
    from models import Character

    out_dir = os.path.join(os.path.dirname(__file__), args.dir)
    os.makedirs(out_dir, exist_ok=True)

    app = create_app("development")
    with app.app_context():
        total = Character.query.filter_by(deleted_at=None).count()
        print(f"数据库共 {total} 个角色，导出至 {out_dir}/\n")
        for type_key, type_name in TYPE_NAMES.items():
            chars = (
                Character.query
                .filter_by(type=type_key, deleted_at=None)
                .order_by(Character.name)
                .all()
            )
            if not chars:
                continue
            out_path = os.path.join(out_dir, f"{type_key}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump([c.to_dict() for c in chars], f, ensure_ascii=False, indent=2)
            print(f"  ✓ {type_name:6s} ({type_key:10s}): {len(chars):3d} 个  → {type_key}.json")
        print("\n导出完成。")


# ─────────────────────────────────────────────────────────────
# 子命令：auto-tag
# ─────────────────────────────────────────────────────────────
def cmd_auto_tag(args):
    from app_new import create_app
    from services.character_service import CharacterService

    app = create_app("development")
    with app.app_context():
        n = CharacterService.bulk_auto_tag()
        print(f"自动标签完成，共处理 {n} 个角色。")


# ─────────────────────────────────────────────────────────────
# 子命令：all（一键全流程）
# ─────────────────────────────────────────────────────────────
def cmd_all(args):
    print(">>> Step 1/4: import")
    cmd_import(args)
    print("\n>>> Step 2/4: import-scripts")
    cmd_import_scripts(args)
    print("\n>>> Step 3/4: auto-tag")
    cmd_auto_tag(args)
    print("\n>>> Step 4/4: export")
    args.dir = "data/by_type"
    cmd_export(args)


# ─────────────────────────────────────────────────────────────
# 入口
# ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="血染钟楼 · Wiki 工具集",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_import = sub.add_parser("import", help="从 Wiki 爬取并导入角色")
    p_import.add_argument("--force", action="store_true", help="覆盖已存在角色")
    p_import.add_argument("--dry",   action="store_true", help="试运行，不写数据库")

    p_import_scripts = sub.add_parser("import-scripts", help="从 Wiki 爬取并导入官方剧本")
    p_import_scripts.add_argument("--force", action="store_true", help="覆盖已存在剧本")
    p_import_scripts.add_argument("--dry",   action="store_true", help="试运行，不写数据库")

    p_export_scripts = sub.add_parser("export-scripts", help="导出数据库剧本为种子文件")
    p_export_scripts.add_argument("--out", default="data/scripts.json", help="输出文件")

    p_export = sub.add_parser("export", help="按阵营导出 JSON 文件")
    p_export.add_argument("--dir", default="data/by_type", help="输出目录")

    sub.add_parser("auto-tag", help="从能力描述自动推断筛选标签")

    p_all = sub.add_parser("all", help="import + auto-tag + export 一键全流程")
    p_all.add_argument("--force", action="store_true", help="覆盖已存在角色")

    args = parser.parse_args()
    {
        "import": cmd_import,
        "import-scripts": cmd_import_scripts,
        "export-scripts": cmd_export_scripts,
        "export": cmd_export,
        "auto-tag": cmd_auto_tag,
        "all": cmd_all,
    }[args.cmd](args)


if __name__ == "__main__":
    main()
