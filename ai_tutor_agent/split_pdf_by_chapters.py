from __future__ import annotations

import re
from pathlib import Path
from typing import Any, List, Tuple

from PyPDF2 import PdfReader, PdfWriter

from ai_tutor_agent.knowledge_map.config.course_graph_config import COURSE_GRAPH_CONFIG


def slugify_filename(text: str) -> str:
    """
    将文件名转成更安全的形式，尽量避免中文路径和特殊字符问题。
    这里只保留字母、数字、下划线和短横线。
    """
    if not text:
        return "untitled"

    # 先把常见空白替换成下划线
    text = text.strip().replace(" ", "_")

    # 去掉非安全字符
    text = re.sub(r"[^\w\-]+", "_", text, flags=re.UNICODE)

    # 连续下划线合并
    text = re.sub(r"_+", "_", text).strip("_")

    return text or "untitled"


def build_chapter_ranges(config: dict[str, Any]) -> List[dict[str, Any]]:
    """
    从 COURSE_GRAPH_CONFIG 里读取章节页码范围。
    """
    chapters = config.get("chapters", [])
    results: List[dict[str, Any]] = []

    for idx, chapter_cfg in enumerate(chapters, start=1):
        if not chapter_cfg.get("enabled", True):
            continue

        page_range = chapter_cfg.get("page_range", [])
        if not isinstance(page_range, list) or len(page_range) != 2:
            raise ValueError(f"章节 page_range 配置不合法: {chapter_cfg.get('name', '')}")

        start_page, end_page = page_range
        if not isinstance(start_page, int) or not isinstance(end_page, int):
            raise ValueError(f"章节页码必须是整数: {chapter_cfg.get('name', '')}")

        if start_page <= 0 or end_page < start_page:
            raise ValueError(f"章节页码范围错误: {chapter_cfg.get('name', '')} -> {page_range}")

        results.append(
            {
                "chapter_index": idx,
                "chapter_label": chapter_cfg.get("chapter", f"第{idx}章"),
                "chapter_name": chapter_cfg.get("name", f"chapter_{idx:02d}"),
                "start_page": start_page,
                "end_page": end_page,
            }
        )

    return results


def split_pdf_by_chapters(
    input_pdf: str,
    output_root_dir: str,
    book_alias: str,
    config: dict[str, Any],
) -> List[Path]:
    """
    按 course_graph_config 里的章节页码切分 PDF。
    """
    input_path = Path(input_pdf)
    if not input_path.exists():
        raise FileNotFoundError(f"找不到输入 PDF: {input_path}")

    output_root = Path(output_root_dir)
    output_dir = output_root / book_alias
    output_dir.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(str(input_path))
    total_pages = len(reader.pages)
    chapter_ranges = build_chapter_ranges(config)

    print(f"输入 PDF: {input_path}")
    print(f"总页数: {total_pages}")
    print(f"输出目录: {output_dir}")
    print("-" * 80)

    output_files: List[Path] = []

    for chapter in chapter_ranges:
        chapter_index = chapter["chapter_index"]
        chapter_label = chapter["chapter_label"]
        chapter_name = chapter["chapter_name"]
        start_page = chapter["start_page"]
        end_page = chapter["end_page"]

        if end_page > total_pages:
            raise ValueError(
                f"{chapter_label}《{chapter_name}》结束页 {end_page} 超过 PDF 总页数 {total_pages}"
            )

        writer = PdfWriter()

        # PyPDF2 使用 0-based 索引，这里配置是 1-based 页码
        for page_idx in range(start_page - 1, end_page):
            writer.add_page(reader.pages[page_idx])

        safe_name = slugify_filename(chapter_name)
        out_file = output_dir / (
            f"chapter_{chapter_index:02d}_p{start_page:03d}-{end_page:03d}_{safe_name}.pdf"
        )

        with open(out_file, "wb") as f:
            writer.write(f)

        output_files.append(out_file)
        print(
            f"已生成: {out_file.name} | {chapter_label} | {chapter_name} | 页码: {start_page}-{end_page}"
        )

    print("-" * 80)
    print(f"切分完成，共生成 {len(output_files)} 个章节 PDF。")

    return output_files


if __name__ == "__main__":
    # ===== 这里改成你的实际路径 =====
    input_pdf = r"E:\ai_code\ai-tutor-agent\data\knowledge\配套资料1：自动控制原理（第八版） (胡寿松、姜斌、张绍杰) .pdf"

    # 根目录，不是最终目录；脚本会自动在下面创建一个 book_alias 子目录
    output_root_dir = r"E:\ai_code\ai-tutor-agent\data\knowledge_splits"

    # 这本书的英文别名，避免中文路径问题
    book_alias = "Principles_of_Automatic_Control_Hu_Jiang_Zhang"

    split_pdf_by_chapters(
        input_pdf=input_pdf,
        output_root_dir=output_root_dir,
        book_alias=book_alias,
        config=COURSE_GRAPH_CONFIG,
    )