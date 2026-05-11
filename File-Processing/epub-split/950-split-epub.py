#!/usr/bin/env python3
"""
PRS-950 Optimized EPUB Splitter
"""

import os
import re
import sys
from pathlib import Path
from ebooklib import epub


# -----------------------------
# Title extraction
# -----------------------------
def extract_title_from_chapter(item):
    try:
        content = item.get_content().decode('utf-8', errors='ignore')

        match = re.search(r'class="ver-box2"[^>]*>(.*?)</', content, re.IGNORECASE | re.DOTALL)
        if match:
            title = match.group(1)
            title = re.sub(r'<br\s*/?\s*>', ' ', title)
            title = re.sub(r'<[^>]+>', '', title)
            title = re.sub(r'&nbsp;', ' ', title)
            title = re.sub(r'&[a-z]+;', '', title)
            return title.strip()

        match = re.search(r'<h[1-6][^>]*>(.*?)</h[1-6]>', content, re.IGNORECASE | re.DOTALL)
        if match:
            title = match.group(1)
            title = re.sub(r'<br\s*/?\s*>', ' ', title)
            title = re.sub(r'<[^>]+>', '', title)
            return title.strip()

    except:
        pass

    return item.get_name().replace('.xhtml', '').replace('.html', '')


# -----------------------------
# HTML optimization
# -----------------------------
def clean_html(html):
    html = re.sub(r'<div[^>]*>', '', html)
    html = re.sub(r'</div>', '', html)
    html = re.sub(r'<span[^>]*>', '', html)
    html = re.sub(r'</span>', '', html)
    html = re.sub(r'\s(class|style)="[^"]*"', '', html)
    return html

def split_html_content(html, max_chars=2500):
    body_match = re.search(r'<body.*?>(.*)</body>', html, re.DOTALL | re.IGNORECASE)
    if not body_match:
        return [html]

    body = body_match.group(1)

    # ---------- Step 1: 提取“结构段落” ----------
    # 优先保留完整标签块，而不是只取 inner text
    blocks = re.findall(r'<p[^>]*>.*?</p>', body, flags=re.IGNORECASE | re.DOTALL)

    # ---------- Step 2: fallback（没有 <p>） ----------
    if not blocks:
        blocks = re.findall(r'<div[^>]*>.*?</div>', body, flags=re.IGNORECASE | re.DOTALL)

    if not blocks:
        # 用 <br> 分割
        tmp = re.sub(r'<br\\s*/?>', '</p><p>', body, flags=re.IGNORECASE)
        blocks = re.findall(r'<p[^>]*>.*?</p>', f'<p>{tmp}</p>', flags=re.DOTALL)

    # ---------- Step 3: 最后 fallback ----------
    if not blocks:
        text = re.sub(r'<[^>]+>', '', body)
        blocks = [f'<p>{line}</p>' for line in re.split(r'(?<=[。！？])', text) if line.strip()]

    # ---------- Step 4: 清洗每个 block（而不是整体） ----------
    def clean_block(b):
        b = re.sub(r'<span[^>]*>', '', b)
        b = re.sub(r'</span>', '', b)
        b = re.sub(r'\s(class|style)=\"[^\"]*\"', '', b)
        return b

    blocks = [clean_block(b) for b in blocks]

    # ---------- Step 5: 按块拼 chunk ----------
    chunks = []
    current = ""

    for b in blocks:
        if len(current) + len(b) > max_chars:
            if current:
                chunks.append(current)
            current = b
        else:
            current += b

    if current:
        chunks.append(current)

    # ---------- Step 6: 包装 ----------
    result = []
    for chunk in chunks:
        result.append(f'''<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<body>
{chunk}
</body>
</html>''')

    return result

# -----------------------------
# Helpers
# -----------------------------
def read_split_config(config_file):
    splits = []
    with open(config_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            splits.append(line)
    return splits


def find_chapter_index(spine_items, chapter_filename):
    for idx, item in enumerate(spine_items):
        name = os.path.basename(item.get_name())
        if name == chapter_filename or item.get_name() == chapter_filename:
            return idx
    return None


# -----------------------------
# Main logic
# -----------------------------
def split_epub_by_chapters(input_file, config_file):
    print(f"Reading {input_file}...")
    book = epub.read_epub(input_file)

    spine_items = []
    for item_id, _ in book.spine:
        item = book.get_item_with_id(item_id)
        if item:
            spine_items.append(item)

    chapter_filenames = read_split_config(config_file)

    split_points = []
    for fname in chapter_filenames:
        idx = find_chapter_index(spine_items, fname)
        if idx is None:
            print(f"Missing chapter: {fname}")
            return False

        title = extract_title_from_chapter(spine_items[idx])
        split_points.append((idx, title))

    split_points.sort(key=lambda x: x[0])
    split_points.append((len(spine_items), None))

    output_dir = Path(input_file).with_suffix('').as_posix() + "_split"
    os.makedirs(output_dir, exist_ok=True)

    title_metadata = book.get_metadata('DC', 'title')
    book_title = title_metadata[0][0] if title_metadata else Path(input_file).stem

    for vol_num in range(len(split_points) - 1):
        start_idx = split_points[vol_num][0]
        end_idx = split_points[vol_num + 1][0]
        subtitle = split_points[vol_num][1]

        print(f"Creating Volume {vol_num+1:02d}: {subtitle}")

        new_book = epub.EpubBook()
        new_book.set_identifier(f"vol{vol_num+1:02d}")
        new_book.set_title(f"{book_title} - {vol_num+1:02d} - {subtitle}")
        new_book.set_language('zh')

        new_items = []
        toc = []

        for chap_idx, item in enumerate(spine_items[start_idx:end_idx]):
            html = item.get_content().decode('utf-8', errors='ignore')
            parts = split_html_content(html, max_chars=2500)

            base = os.path.basename(item.get_name()).replace('.xhtml', '')
            chapter_title = extract_title_from_chapter(item)

            first_item = None

            for i, part in enumerate(parts):
                if i == 0:
                    part = f"<h1>{chapter_title}</h1>" + part

                uid = f"{base}_{chap_idx}_{i}"

                new_item = epub.EpubHtml(
                    uid=uid,
                    title=chapter_title if i == 0 else "",
                    file_name=f"{base}_{chap_idx}_{i}.xhtml"
                )
                
                new_item.set_content(part.encode('utf-8'))  # ✅ 关键

                new_book.add_item(new_item)
                new_items.append(new_item)

                if i == 0:
                    first_item = new_item

            if first_item:
                toc.append(
                    epub.Link(
                        first_item.file_name,
                        chapter_title,
                        first_item.get_id()
                    )
                )

        new_book.spine = new_items
        new_book.toc = toc

        new_book.add_item(epub.EpubNcx())

        safe_sub = re.sub(r'[<>:"/\\|?*]', '', subtitle or '').strip()
        if safe_sub:
            fname = f"{book_title} - {vol_num+1:02d} - {safe_sub}.epub"
        else:
            fname = f"{book_title} - {vol_num+1:02d}.epub"

        out_path = os.path.join(output_dir, fname)
        epub.write_epub(out_path, new_book)

        print(f"Saved: {fname}")

    print("Done.")
    return True


# -----------------------------
# Entry
# -----------------------------
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python 950-split_epub.py $input.epub [config.split]")
        print("       Be sure $input.split exists in the same directory of $input.epub."
        sys.exit(1)

    input_epub = sys.argv[1]

    if len(sys.argv) == 3:
        config_file = sys.argv[2]
    else:
        config_file = Path(input_epub).with_suffix('.split')

    if not os.path.exists(config_file):
        print(f"Config not found: {config_file}")
        sys.exit(1)

    split_epub_by_chapters(input_epub, config_file)

