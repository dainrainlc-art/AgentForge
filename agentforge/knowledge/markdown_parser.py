"""Markdown 解析器 - 解析 Obsidian 格式的 Markdown 文档

功能特性:
- 解析 YAML frontmatter
- 提取双向链接 [[link]]
- 解析标签 #tag
- 处理嵌入内容 ![[embed]]
- 提取代码块
- 解析表格
"""

import re
import yaml
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path


@dataclass
class ParsedMarkdown:
    """解析后的 Markdown 文档"""
    title: str
    content: str
    frontmatter: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    wikilinks: List[str] = field(default_factory=list)
    embeds: List[str] = field(default_factory=list)
    headings: List[Dict[str, Any]] = field(default_factory=list)
    code_blocks: List[Dict[str, Any]] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    links: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MarkdownParser:
    """Markdown 解析器"""

    FRONTMATTER_PATTERN = re.compile(
        r'^---\s*\n(.*?)\n---\s*\n',
        re.DOTALL
    )

    WIKILINK_PATTERN = re.compile(
        r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
    )

    EMBED_PATTERN = re.compile(
        r'!\[\[([^\]]+)\]\]'
    )

    TAG_PATTERN = re.compile(
        r'#(\w+(?:/\w+)*)'
    )

    HEADING_PATTERN = re.compile(
        r'^(#{1,6})\s+(.+)$',
        re.MULTILINE
    )

    CODE_BLOCK_PATTERN = re.compile(
        r'```(\w*)\n(.*?)```',
        re.DOTALL
    )

    TABLE_PATTERN = re.compile(
        r'(\|.+\|\n\|[-:\s|]+\|\n(?:\|.+\|\n?)+)',
        re.MULTILINE
    )

    IMAGE_PATTERN = re.compile(
        r'!\[([^\]]*)\]\(([^)]+)\)'
    )

    LINK_PATTERN = re.compile(
        r'(?<!!)\[([^\]]+)\]\(([^)]+)\)'
    )

    def parse(self, content: str, filepath: Optional[str] = None) -> ParsedMarkdown:
        """解析 Markdown 内容"""
        frontmatter = self._parse_frontmatter(content)
        body = self._remove_frontmatter(content)

        title = self._extract_title(body, filepath)
        tags = self._extract_tags(body, frontmatter)
        wikilinks = self._extract_wikilinks(body)
        embeds = self._extract_embeds(body)
        headings = self._extract_headings(body)
        code_blocks = self._extract_code_blocks(body)
        tables = self._extract_tables(body)
        images = self._extract_images(body)
        links = self._extract_links(body)

        metadata = {
            "word_count": len(body.split()),
            "char_count": len(body),
            "heading_count": len(headings),
            "code_block_count": len(code_blocks),
            "link_count": len(wikilinks) + len(links),
            "image_count": len(images) + len([e for e in embeds if self._is_image_embed(e)])
        }

        return ParsedMarkdown(
            title=title,
            content=body,
            frontmatter=frontmatter,
            tags=tags,
            wikilinks=wikilinks,
            embeds=embeds,
            headings=headings,
            code_blocks=code_blocks,
            tables=tables,
            images=images,
            links=links,
            metadata=metadata
        )

    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """解析 YAML frontmatter"""
        match = self.FRONTMATTER_PATTERN.match(content)
        if not match:
            return {}

        try:
            return yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            return {}

    def _remove_frontmatter(self, content: str) -> str:
        """移除 frontmatter"""
        return self.FRONTMATTER_PATTERN.sub('', content)

    def _extract_title(self, content: str, filepath: Optional[str]) -> str:
        """提取标题"""
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()

        if filepath:
            return Path(filepath).stem

        return "Untitled"

    def _extract_tags(self, content: str, frontmatter: Dict) -> List[str]:
        """提取标签"""
        tags: set[str] = set()

        if 'tags' in frontmatter:
            fm_tags = frontmatter['tags']
            if isinstance(fm_tags, list):
                tags.update(str(t) for t in fm_tags)
            elif isinstance(fm_tags, str):
                tags.add(fm_tags)

        for match in self.TAG_PATTERN.finditer(content):
            tag = match.group(1)
            if not tag.startswith('#'):
                tags.add(tag)

        return sorted(list(tags))

    def _extract_wikilinks(self, content: str) -> List[str]:
        """提取双向链接"""
        links = []
        for match in self.WIKILINK_PATTERN.finditer(content):
            link = match.group(1).strip()
            if link and link not in links:
                links.append(link)
        return links

    def _extract_embeds(self, content: str) -> List[str]:
        """提取嵌入内容"""
        embeds = []
        for match in self.EMBED_PATTERN.finditer(content):
            embed = match.group(1).strip()
            if embed and embed not in embeds:
                embeds.append(embed)
        return embeds

    def _extract_headings(self, content: str) -> List[Dict[str, Any]]:
        """提取标题结构"""
        headings = []
        for match in self.HEADING_PATTERN.finditer(content):
            level = len(match.group(1))
            text = match.group(2).strip()
            headings.append({
                "level": level,
                "text": text,
                "anchor": self._generate_anchor(text)
            })
        return headings

    def _extract_code_blocks(self, content: str) -> List[Dict[str, Any]]:
        """提取代码块"""
        blocks = []
        for match in self.CODE_BLOCK_PATTERN.finditer(content):
            language = match.group(1) or "text"
            code = match.group(2)
            blocks.append({
                "language": language,
                "code": code,
                "line_count": len(code.splitlines())
            })
        return blocks

    def _extract_tables(self, content: str) -> List[Dict[str, Any]]:
        """提取表格"""
        tables = []
        for match in self.TABLE_PATTERN.finditer(content):
            table_text = match.group(1)
            rows = [row.strip() for row in table_text.split('\n') if row.strip()]

            if len(rows) >= 2:
                headers = [cell.strip() for cell in rows[0].split('|') if cell.strip()]
                rows_data = []
                for row in rows[2:]:
                    cells = [cell.strip() for cell in row.split('|') if cell.strip()]
                    if cells:
                        rows_data.append(cells)

                tables.append({
                    "headers": headers,
                    "rows": rows_data,
                    "row_count": len(rows_data)
                })

        return tables

    def _extract_images(self, content: str) -> List[str]:
        """提取图片链接"""
        images = []
        for match in self.IMAGE_PATTERN.finditer(content):
            alt_text = match.group(1)
            url = match.group(2)
            images.append(url)
        return images

    def _extract_links(self, content: str) -> List[Dict[str, str]]:
        """提取普通链接"""
        links = []
        for match in self.LINK_PATTERN.finditer(content):
            text = match.group(1)
            url = match.group(2)
            links.append({"text": text, "url": url})
        return links

    def _generate_anchor(self, text: str) -> str:
        """生成锚点"""
        anchor = text.lower()
        anchor = re.sub(r'[^\w\s-]', '', anchor)
        anchor = re.sub(r'[\s]+', '-', anchor)
        return anchor

    def _is_image_embed(self, embed: str) -> bool:
        """检查是否为图片嵌入"""
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.bmp'}
        return any(embed.lower().endswith(ext) for ext in image_extensions)

    def extract_outline(self, content: str) -> List[Dict[str, Any]]:
        """提取文档大纲"""
        body = self._remove_frontmatter(content)
        headings = self._extract_headings(body)

        outline = []
        stack = []

        for heading in headings:
            level = heading["level"]

            while stack and stack[-1]["level"] >= level:
                stack.pop()

            item = {
                "level": level,
                "text": heading["text"],
                "anchor": heading["anchor"],
                "children": []
            }

            if stack:
                stack[-1]["children"].append(item)
            else:
                outline.append(item)

            stack.append(item)

        return outline

    def extract_summary(self, content: str, max_length: int = 200) -> str:
        """提取摘要"""
        body = self._remove_frontmatter(content)

        body = re.sub(r'^#+\s+.*$', '', body, flags=re.MULTILINE)
        body = re.sub(r'```.*?```', '', body, flags=re.DOTALL)
        body = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', body)
        body = re.sub(r'!?\[([^\]]*)\]\([^)]+\)', r'\1', body)
        body = re.sub(r'#+(\w+)', r'\1', body)
        body = re.sub(r'\*([^*]+)\*', r'\1', body)
        body = re.sub(r'_([^_]+)_', r'\1', body)
        body = re.sub(r'\s+', ' ', body).strip()

        if len(body) > max_length:
            body = body[:max_length].rsplit(' ', 1)[0] + '...'

        return body

    def convert_wikilinks_to_md(self, content: str) -> str:
        """将双向链接转换为标准 Markdown 链接"""
        def replace_wikilink(match):
            link = match.group(1)
            if '|' in link:
                parts = link.split('|', 1)
                return f'[{parts[1]}]({parts[0]}.md)'
            return f'[{link}]({link}.md)'

        return self.WIKILINK_PATTERN.sub(replace_wikilink, content)

    def convert_to_notion_blocks(self, content: str) -> List[Dict[str, Any]]:
        """转换为 Notion 块格式"""
        blocks = []
        body = self._remove_frontmatter(content)
        lines = body.split('\n')

        current_paragraph = []

        for line in lines:
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                if current_paragraph:
                    blocks.append({
                        "type": "paragraph",
                        "paragraph": {"rich_text": [{"type": "text", "text": {"content": '\n'.join(current_paragraph)}}]}
                    })
                    current_paragraph = []

                level = len(heading_match.group(1))
                text = heading_match.group(2)
                blocks.append({
                    "type": f"heading_{level}",
                    f"heading_{level}": {"rich_text": [{"type": "text", "text": {"content": text}}]}
                })
                continue

            code_match = re.match(r'^```(\w*)$', line)
            if code_match:
                if current_paragraph:
                    blocks.append({
                        "type": "paragraph",
                        "paragraph": {"rich_text": [{"type": "text", "text": {"content": '\n'.join(current_paragraph)}}]}
                    })
                    current_paragraph = []
                continue

            if line.startswith('- ') or line.startswith('* '):
                if current_paragraph:
                    blocks.append({
                        "type": "paragraph",
                        "paragraph": {"rich_text": [{"type": "text", "text": {"content": '\n'.join(current_paragraph)}}]}
                    })
                    current_paragraph = []

                text = line[2:]
                blocks.append({
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": text}}]}
                })
                continue

            if line.strip():
                current_paragraph.append(line)
            elif current_paragraph:
                blocks.append({
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": '\n'.join(current_paragraph)}}]}
                })
                current_paragraph = []

        if current_paragraph:
            blocks.append({
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": '\n'.join(current_paragraph)}}]}
            })

        return blocks
