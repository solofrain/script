#!/usr/bin/env python3
"""
Split a large EPUB into multiple volumes based on chapter filenames.

This version edits the original EPUB package directly instead of rebuilding it
with ebooklib.  That keeps the OPF/NCX/XHTML/CSS structure very close to the
source EPUB, which is important for older readers such as Sony PRS-950.

Usage:
  python split-epub.py <input_epub_file> [split_config_file]

Config file format, one split-start chapter filename per line:
  Chapter0007.xhtml
  Chapter0125.xhtml
  Chapter0249.xhtml
"""

import os
import posixpath
import re
import sys
import uuid
import zipfile
import xml.etree.ElementTree as ET
from html import unescape
from pathlib import Path

OPF_NS = "http://www.idpf.org/2007/opf"
DC_NS = "http://purl.org/dc/elements/1.1/"
NCX_NS = "http://www.daisy.org/z3986/2005/ncx/"
CONTAINER_NS = "urn:oasis:names:tc:opendocument:xmlns:container"

ET.register_namespace("", OPF_NS)
ET.register_namespace("dc", DC_NS)
ET.register_namespace("opf", OPF_NS)
ET.register_namespace("", NCX_NS)

TITLE_CLASS_RE = re.compile(
    r'<(?:h[1-6]|div)[^>]*class=["\'][^"\']*\bver-box2\b[^"\']*["\'][^>]*>(.*?)</(?:h[1-6]|div)>',
    re.IGNORECASE | re.DOTALL,
)
HEADING_RE = re.compile(r'<h[1-6][^>]*>(.*?)</h[1-6]>', re.IGNORECASE | re.DOTALL)


def clean_html_text(text):
    text = re.sub(r'<br\s*/?\s*>', ' ', text or '', flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_title_from_html(data, fallback):
    text = data.decode('utf-8', errors='ignore')
    for regex in (TITLE_CLASS_RE, HEADING_RE):
        match = regex.search(text)
        if match:
            title = clean_html_text(match.group(1))
            if title:
                return title
    return fallback


def read_split_config(config_file):
    splits = []
    with open(config_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            splits.append(line)
    return splits


def sanitize_filename(text):
    text = re.sub(r'[<>:"/\\|?*]', '', text or '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text.rstrip('. ')


def ns(tag, namespace=OPF_NS):
    return f'{{{namespace}}}{tag}'


def read_container(zf):
    data = zf.read('META-INF/container.xml')
    root = ET.fromstring(data)
    rootfile = root.find(f'.//{{{CONTAINER_NS}}}rootfile')
    if rootfile is None:
        raise RuntimeError('Cannot find rootfile in META-INF/container.xml')
    return rootfile.attrib['full-path']


def is_chapter_href(href):
    base = posixpath.basename(href)
    return bool(re.match(r'Chapter\d+(?:_\d+)?\.(?:xhtml|html)$', base, re.IGNORECASE))


def copy_zipinfo(src_info, filename=None):
    zi = zipfile.ZipInfo(filename or src_info.filename, date_time=src_info.date_time)
    zi.comment = src_info.comment
    zi.extra = src_info.extra
    zi.internal_attr = src_info.internal_attr
    zi.external_attr = src_info.external_attr
    zi.create_system = src_info.create_system
    zi.compress_type = src_info.compress_type
    return zi


def write_xml_bytes(root):
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def split_epub_by_chapters(input_file, config_file):
    input_file = os.path.abspath(input_file)
    output_dir = os.path.join(os.path.dirname(input_file), Path(input_file).stem + '_split')
    os.makedirs(output_dir, exist_ok=True)

    chapter_filenames = read_split_config(config_file)
    if not chapter_filenames:
        print('Error: No chapter filenames defined in configuration file')
        return False

    with zipfile.ZipFile(input_file, 'r') as zf:
        opf_path = read_container(zf)
        opf_dir = posixpath.dirname(opf_path)
        opf_data = zf.read(opf_path)
        opf_root = ET.fromstring(opf_data)

        metadata = opf_root.find(ns('metadata'))
        manifest = opf_root.find(ns('manifest'))
        spine = opf_root.find(ns('spine'))
        if metadata is None or manifest is None or spine is None:
            raise RuntimeError('Invalid OPF: missing metadata, manifest, or spine')

        title_el = metadata.find(ns('title', DC_NS))
        book_title = title_el.text.strip() if title_el is not None and title_el.text else Path(input_file).stem

        id_to_item = {item.attrib['id']: item for item in manifest.findall(ns('item')) if 'id' in item.attrib}
        spine_itemrefs = list(spine.findall(ns('itemref')))

        spine_entries = []
        for itemref in spine_itemrefs:
            item_id = itemref.attrib.get('idref')
            item = id_to_item.get(item_id)
            if item is None:
                continue
            href = item.attrib.get('href', '')
            full_path = posixpath.normpath(posixpath.join(opf_dir, href)) if opf_dir else href
            spine_entries.append({'id': item_id, 'href': href, 'full_path': full_path, 'itemref': itemref})

        print(f'Reading {input_file}...')
        print(f'Found {len(spine_entries)} items in spine')

        split_points = []
        for chapter_filename in chapter_filenames:
            found = None
            for idx, entry in enumerate(spine_entries):
                if posixpath.basename(entry['href']) == chapter_filename or entry['href'] == chapter_filename:
                    found = (idx, entry)
                    break
            if found is None:
                print(f"Error: Chapter '{chapter_filename}' not found in EPUB spine")
                return False
            idx, entry = found
            fallback = posixpath.splitext(posixpath.basename(entry['href']))[0]
            title = extract_title_from_html(zf.read(entry['full_path']), fallback)
            split_points.append((idx, title))
            print(f"  Found: {chapter_filename} at index {idx} - '{title}'")

        split_points.sort(key=lambda x: x[0])
        split_points.append((len(spine_entries), None))
        print(f'\nWill create {len(split_points) - 1} volumes\n')

        all_infos = {info.filename: info for info in zf.infolist()}
        all_names = [info.filename for info in zf.infolist()]

        ncx_id = spine.attrib.get('toc')
        ncx_href = id_to_item.get(ncx_id).attrib.get('href') if ncx_id in id_to_item else None
        ncx_path = posixpath.normpath(posixpath.join(opf_dir, ncx_href)) if ncx_href else None
        ncx_root_original = ET.fromstring(zf.read(ncx_path)) if ncx_path and ncx_path in all_infos else None

        for vol_num in range(len(split_points) - 1):
            start_idx, volume_subtitle = split_points[vol_num]
            end_idx = split_points[vol_num + 1][0]
            selected_entries = spine_entries[start_idx:end_idx]
            selected_ids = {entry['id'] for entry in selected_entries}
            selected_hrefs = {entry['href'] for entry in selected_entries}
            selected_paths = {entry['full_path'] for entry in selected_entries}

            safe_subtitle = sanitize_filename(volume_subtitle or '')
            if safe_subtitle:
                new_title = f'{book_title} - {vol_num + 1:02d} - {safe_subtitle}'
            else:
                new_title = f'{book_title} - {vol_num + 1:02d}'

            print(f'Creating Volume {vol_num + 1:02d}: {volume_subtitle}')
            print(f'  Chapters {start_idx + 1} to {end_idx} ({len(selected_entries)} spine items)')

            new_opf_root = ET.fromstring(opf_data)
            new_metadata = new_opf_root.find(ns('metadata'))
            new_manifest = new_opf_root.find(ns('manifest'))
            new_spine = new_opf_root.find(ns('spine'))

            title_node = new_metadata.find(ns('title', DC_NS))
            if title_node is not None:
                title_node.text = new_title
            identifier_node = new_metadata.find(ns('identifier', DC_NS))
            if identifier_node is not None:
                identifier_node.text = f'urn:uuid:{uuid.uuid4()}'

            for child in list(new_manifest):
                href = child.attrib.get('href', '')
                media_type = child.attrib.get('media-type', '')
                keep = True
                if media_type == 'application/xhtml+xml' and is_chapter_href(href) and href not in selected_hrefs:
                    keep = False
                if not keep:
                    new_manifest.remove(child)

            for child in list(new_spine):
                new_spine.remove(child)
            for entry in selected_entries:
                new_itemref = ET.Element(ns('itemref'))
                new_itemref.set('idref', entry['id'])
                linear = entry['itemref'].attrib.get('linear')
                if linear:
                    new_itemref.set('linear', linear)
                new_spine.append(new_itemref)

            new_ncx_bytes = None
            if ncx_root_original is not None and ncx_path:
                new_ncx_root = ET.fromstring(zf.read(ncx_path))
                ncx_title_text = new_ncx_root.find(f'.//{{{NCX_NS}}}docTitle/{{{NCX_NS}}}text')
                if ncx_title_text is not None:
                    ncx_title_text.text = new_title
                nav_map = new_ncx_root.find(f'.//{{{NCX_NS}}}navMap')
                if nav_map is not None:
                    for child in list(nav_map):
                        nav_map.remove(child)
                    for play_order, entry in enumerate(selected_entries, start=1):
                        fallback = posixpath.splitext(posixpath.basename(entry['href']))[0]
                        chapter_title = extract_title_from_html(zf.read(entry['full_path']), fallback)
                        nav_point = ET.SubElement(nav_map, f'{{{NCX_NS}}}navPoint')
                        nav_point.set('id', f'navPoint-{play_order}')
                        nav_point.set('playOrder', str(play_order))
                        nav_label = ET.SubElement(nav_point, f'{{{NCX_NS}}}navLabel')
                        text_node = ET.SubElement(nav_label, f'{{{NCX_NS}}}text')
                        text_node.text = chapter_title
                        content_node = ET.SubElement(nav_point, f'{{{NCX_NS}}}content')
                        content_node.set('src', entry['href'])
                new_ncx_bytes = write_xml_bytes(new_ncx_root)

            output_filename = sanitize_filename(new_title) + '.epub'
            output_file = os.path.join(output_dir, output_filename)

            with zipfile.ZipFile(output_file, 'w') as out:
                if 'mimetype' in all_infos:
                    out.writestr('mimetype', zf.read('mimetype'), compress_type=zipfile.ZIP_STORED)

                for name in all_names:
                    if name == 'mimetype':
                        continue
                    if name == opf_path:
                        out.writestr(copy_zipinfo(all_infos[name]), write_xml_bytes(new_opf_root))
                        continue
                    if name == ncx_path and new_ncx_bytes is not None:
                        out.writestr(copy_zipinfo(all_infos[name]), new_ncx_bytes)
                        continue

                    # Remove unused chapter files, but keep all CSS/images/fonts/front matter.
                    rel = posixpath.relpath(name, opf_dir) if opf_dir else name
                    if is_chapter_href(rel) and name not in selected_paths:
                        continue
                    out.writestr(copy_zipinfo(all_infos[name]), zf.read(name))

            print(f'  -> Saved to {output_filename}\n')

    print(f'Successfully created {len(split_points) - 1} volumes in {output_dir}')
    return True


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print('Usage: python split-epub.py <input_epub_file> [split_config_file]')
        sys.exit(1)

    input_epub = os.path.expanduser(sys.argv[1])
    if not os.path.exists(input_epub):
        print(f'Error: Input file not found: {input_epub}')
        sys.exit(1)

    if len(sys.argv) == 3:
        config_file = os.path.expanduser(sys.argv[2])
    else:
        epub_dir = os.path.dirname(input_epub)
        epub_basename = Path(input_epub).stem
        config_file = os.path.join(epub_dir, f'{epub_basename}.split')

    if not os.path.exists(config_file):
        print(f'Error: Config file not found: {config_file}')
        print(f'Expected file: {config_file}')
        sys.exit(1)

    print(f'Using config file: {config_file}\n')
    success = split_epub_by_chapters(input_epub, config_file)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
