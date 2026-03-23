"""Wiki 角色爬虫模块

从 https://clocktower-wiki.gstonegames.com 爬取所有角色数据，包括：
  - 中文名、英文名、类型、能力描述、token 图片 URL

使用标准库，无需额外依赖。
"""
import re
import time
import urllib.request
import urllib.parse
from html.parser import HTMLParser

WIKI_BASE = "https://clocktower-wiki.gstonegames.com"

# 各类型分类页 URL 片段 → type_key
CATEGORY_MAP = {
    "%E9%95%87%E6%B0%91":         "townsfolk",   # 镇民
    "%E5%A4%96%E6%9D%A5%E8%80%85": "outsider",   # 外来者
    "%E7%88%AA%E7%89%99":          "minion",      # 爪牙
    "%E6%81%B6%E9%AD%94":          "demon",       # 恶魔
    "%E6%97%85%E8%A1%8C%E8%80%85": "traveller",  # 旅行者
    "%E4%BC%A0%E5%A5%87%E8%A7%92%E8%89%B2": "fabled",  # 传奇角色
}

# 全局已知跳过页面（分类子页/列表页，不是角色）
SKIP_TITLES = {
    "镇民", "外来者", "爪牙", "恶魔", "旅行者", "传奇角色", "奇遇角色",
    "角色能力类别总览", "新角色公布计划", "未公布的测试中角色公告",
    "暗流涌动", "黯月初升", "梦殒春宵", "实验性角色", "官方角色",
}

# --------------------------------------------------------------------- #
# HTML 解析辅助类
# --------------------------------------------------------------------- #

class _LinkParser(HTMLParser):
    """解析页面中所有 <a href="..."> 标签，收集 /index.php?title=XXX 链接"""

    def __init__(self):
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        attrs_dict = dict(attrs)
        href = attrs_dict.get("href", "")
        if href.startswith("/index.php?title="):
            full = WIKI_BASE + href
            # 去掉 # 锚点
            full = full.split("#")[0]
            if full not in self.links:
                self.links.append(full)


class _ImgParser(HTMLParser):
    """解析页面中 /images/thumb/ 路径的图片 src"""

    def __init__(self):
        super().__init__()
        self.token_url: str = ""

    def handle_starttag(self, tag, attrs):
        if self.token_url:
            return
        if tag != "img":
            return
        attrs_dict = dict(attrs)
        src = attrs_dict.get("src", "")
        if "/images/thumb/" in src:
            self.token_url = src


# --------------------------------------------------------------------- #
# 工具函数
# --------------------------------------------------------------------- #

def _fetch(url: str, retries: int = 3, delay: float = 1.0) -> str:
    """HTTP GET，返回 HTML 字符串，失败时重试"""
    import ssl
    # Wiki 使用自签名证书，需要跳过验证
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": WIKI_BASE + "/",
    }
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as exc:
            if attempt == retries - 1:
                raise
            print(f"  ⚠ 重试 {attempt+1}/{retries}: {url} — {exc}")
            time.sleep(delay * (attempt + 1))
    return ""


def _thumb_to_original(thumb_src: str) -> str:
    """
    把 thumb 路径转为原始大图 URL。
    例：/images/thumb/4/45/Washerwoman.png/200px-Washerwoman.png
        → https://…/images/4/45/Washerwoman.png
    """
    # 如果已经是完整 URL，先去掉 domain
    src = thumb_src
    if src.startswith("http"):
        parsed = urllib.parse.urlparse(src)
        src = parsed.path

    # 匹配 /images/thumb/{a}/{b}/{filename}
    m = re.match(r"(/images/thumb/)([^/]+/[^/]+/[^/]+)", src)
    if m:
        # 去掉 /thumb/ 并去掉末段（尺寸前缀段）
        path = "/images/" + m.group(2)
        return WIKI_BASE + path

    # 已是原始路径
    if src.startswith("/"):
        return WIKI_BASE + src
    return src


def _title_from_url(url: str) -> str:
    """从 wiki URL 提取 title 参数（URL 解码）"""
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)
    titles = qs.get("title", [""])
    return urllib.parse.unquote(titles[0])


# --------------------------------------------------------------------- #
# 分类页抓取
# --------------------------------------------------------------------- #

def scrape_category(category_slug: str, char_type: str) -> list[dict]:
    """
    抓取一个分类页面（如「外来者」），返回该页列出的角色链接 + type。
    角色链接位于 <ul class="gallery mw-gallery-nolines"> 中的图片链接。

    返回：[{"url": "…", "type": char_type, "name": "管家"}, …]
    """
    url = f"{WIKI_BASE}/index.php?title={category_slug}"
    print(f"  ▶ 分类页: {url}")
    html = _fetch(url)

    results = []
    seen_urls: set[str] = set()

    # 找所有 gallery list item 内的链接
    # 结构：<li class="gallerybox"> … <a href="/index.php?title=xxx">…</a> … </li>
    gallery_items = re.findall(
        r'<li\s+class="gallerybox"[^>]*>(.*?)</li>',
        html, re.DOTALL
    )

    for item in gallery_items:
        # 提取 href
        m = re.search(r'href="(/index\.php\?title=([^"#&]+))"', item)
        if not m:
            continue
        path = m.group(1)
        title_encoded = m.group(2)
        title = urllib.parse.unquote(title_encoded)
        full_url = WIKI_BASE + path

        # 跳过已知非角色和重复
        if title in SKIP_TITLES or full_url in seen_urls:
            continue
        # 跳过特殊页面
        if title.startswith("特殊:") or ":" in title:
            continue
        seen_urls.add(full_url)
        results.append({"url": full_url, "type": char_type, "name": title})

    print(f"    找到 {len(results)} 个角色链接")
    return results


# --------------------------------------------------------------------- #
# 角色页抓取
# --------------------------------------------------------------------- #

def scrape_character(page_url: str) -> dict | None:
    """
    抓取单个角色页面，返回角色数据字典，失败时返回 None。

    返回字段：
      name      中文名
      name_en   英文名
      type      类型（由调用方注入）
      ability   能力描述（中文）
      image     原始大图 URL
      wiki_url  wiki 页面 URL
    """
    html = _fetch(page_url)

    # 1. token 图片
    img_parser = _ImgParser()
    img_parser.feed(html)
    image_url = _thumb_to_original(img_parser.token_url) if img_parser.token_url else ""

    # 2. 英文名（格式：「英文名：Washerwoman」或 「- 英文名：Washerwoman」）
    name_en = ""
    m = re.search(r"英文名[：:]\s*([A-Za-z][A-Za-z\s\-']+?)(?:\s*[\n<\-–—]|$)", html)
    if m:
        name_en = m.group(1).strip()

    # 3. 能力描述 —— 取「角色能力」小节下第一段正文
    ability = ""
    # 先找 id="角色能力" 的 heading，然后取随后的 <p> 文本
    m_sec = re.search(
        r'id=["\']角色能力["\'].*?</h[23]>\s*(.*?)<h[23]',
        html, re.DOTALL
    )
    if m_sec:
        raw = m_sec.group(1)
        # 去掉 HTML 标签
        text = re.sub(r"<[^>]+>", "", raw).strip()
        # 取第一段非空内容
        for line in text.splitlines():
            line = line.strip()
            if line:
                ability = line
                break

    # 如果上面失败，尝试 mw-parser-output > p 策略
    if not ability:
        # 找页面内 <p> 标签内容（去标签后最长的段落）
        paras = re.findall(r"<p>(.*?)</p>", html, re.DOTALL)
        for p in paras:
            text = re.sub(r"<[^>]+>", "", p).strip()
            # 跳过过短或只含标点的段落
            if len(text) > 10 and not text.startswith("晚礼服"):
                ability = text
                break

    data = {
        "name": _title_from_url(page_url),
        "name_en": name_en,
        "ability": ability,
        "image": image_url,
        "wiki_url": page_url,
    }
    return data


# --------------------------------------------------------------------- #
# 一键抓取全部角色
# --------------------------------------------------------------------- #

def scrape_all_characters(delay: float = 0.5) -> list[dict]:
    """
    遍历所有角色分类页，抓取所有角色数据。

    Args:
        delay: 每次请求之间的间隔秒数（礼貌性延迟）

    Returns:
        角色字典列表，每个字典含 name/name_en/type/ability/image/wiki_url
    """
    all_chars: list[dict] = []
    seen_names: set[str] = set()

    for slug, char_type in CATEGORY_MAP.items():
        print(f"\n{'='*50}")
        print(f"类型: {char_type} ({urllib.parse.unquote(slug)})")
        print(f"{'='*50}")

        char_links = scrape_category(slug, char_type)
        time.sleep(delay)

        for item in char_links:
            name = item["name"]
            if name in seen_names:
                print(f"  ↷ 跳过重复: {name}")
                continue
            seen_names.add(name)

            print(f"  抓取: {name} …", end=" ", flush=True)
            try:
                char_data = scrape_character(item["url"])
                if char_data:
                    char_data["type"] = char_type
                    all_chars.append(char_data)
                    print(f"✓ ({char_data['name_en']})")
                else:
                    print("✗ 无数据")
            except Exception as exc:
                print(f"✗ 错误: {exc}")

            time.sleep(delay)

    print(f"\n{'='*50}")
    print(f"共抓取 {len(all_chars)} 个角色")
    return all_chars
