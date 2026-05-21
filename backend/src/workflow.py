"""
错题本生成工作流 - LangGraph 实现
使用 StateGraph 将每个处理步骤定义为图节点
"""

import os
import re as _re
import json
import logging
import time
import traceback
import difflib as _difflib
from contextvars import copy_context
from typing import List, Dict, Any, TypedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from core.config import settings
from .utils import prepare_input, export_wrongbook, simplify_ocr_results, run_async

_HTML_TAG_RE = _re.compile(r"<[^>]+>")
_ANSWER_MARKER_RE = _re.compile(
    r"(?:参考答案|答案与解析|试题答案|参考解答|【答案】|【解析】|答案|解析|解答[:：]|解[:：])"
)
_QUESTION_START_RE = _re.compile(r"^\s*(\d{1,3})\s*[.、．]")
console = Console()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('workflow.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def _submit_with_current_context(pool: ThreadPoolExecutor, fn, *args, **kwargs):
    """在线程池任务中保留当前 ContextVar 上下文。"""
    ctx = copy_context()
    return pool.submit(ctx.run, fn, *args, **kwargs)


# ── 状态定义 ──────────────────────────────────────────────


class WorkflowState(TypedDict, total=False):
    """工作流全局状态"""
    file_paths: List[str]                # 输入文件路径列表（支持多文件）
    image_paths: List[str]               # 标准化后的图片路径列表
    questions: List[Dict[str, Any]]      # 分割后的题目列表
    selected_ids: List[str]              # 用户选中的题目 ID
    output_path: str                     # 导出文件路径
    model_provider: str                  # 模型供应商: "openai" | "anthropic"
    model_name: str                      # 用户选择的具体模型名称（可选，None 时使用 provider 默认）
    warnings: List[str]                  # 步骤警告信息（供前端展示）
    # 数据库凭据（由路由层注入，避免环境变量依赖）
    llm_credentials: Dict[str, Any]      # {api_key, base_url, light_model_name, supports_function_calling}
    ocr_credentials: Dict[str, Any]      # {api_url, token, model, use_doc_orientation, ...}
    ocr_cache_path: str                  # OCR 预览缓存文件路径（按用户隔离）
    confirmed_answer_layout: str         # 用户在前端确认后的答案版式
    selected_page_indices: List[int]     # 用户确认后仅用于分割的题目页索引


# ── 节点函数 ──────────────────────────────────────────────


def prepare_input_node(state: WorkflowState) -> dict:
    """节点: 准备输入（验证文件并复制到工作目录），支持多文件"""
    console.print("[bold yellow]步骤 1: 准备输入文件[/bold yellow]")
    step_start = time.time()

    file_paths = state["file_paths"]
    all_paths = []
    for fp in file_paths:
        all_paths.extend(prepare_input(fp))

    logger.info(f"步骤1完成: 准备输入文件，共 {len(all_paths)} 个文件（来自 {len(file_paths)} 个文件），耗时 {time.time() - step_start:.2f}s")
    return {"image_paths": all_paths}


# ── 并行分割辅助函数 ──────────────────────────────────────────


def _run_ocr_and_simplify(file_paths: List[str], ocr_credentials: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """执行 OCR 解析并简化结果（含重试机制）

    支持混合文件类型：PDF 直传 API，图片并行上传。
    然后将结果简化为 split_batch 所需的格式。

    Returns:
        简化后的 OCR 数据列表，每项包含 page_index 和 blocks
    """
    from src.paddleocr_client import PaddleOCRClient

    creds = ocr_credentials or {}
    client = PaddleOCRClient(
        api_url=creds.get("api_url"),
        token=creds.get("token"),
        model=creds.get("model"),
        use_doc_orientation=creds.get("use_doc_orientation"),
        use_doc_unwarping=creds.get("use_doc_unwarping"),
        use_chart_recognition=creds.get("use_chart_recognition"),
    )

    # 按文件类型分组
    pdf_paths = [p for p in file_paths if p.lower().endswith(".pdf")]
    image_paths = [p for p in file_paths if not p.lower().endswith(".pdf")]

    max_retries = 3
    retry_delays = [3, 5, 10]
    ocr_results = []
    last_error = None

    # PDF 直传（每个 PDF 单独提交，API 内部处理分页）
    for pdf_path in pdf_paths:
        result = None
        for attempt in range(1, max_retries + 1):
            try:
                result = client.parse_pdf(pdf_path, save_output=True)
                break
            except Exception as e:
                last_error = e
                tb = traceback.format_exc()
                if attempt < max_retries:
                    delay = retry_delays[attempt - 1]
                    logger.warning(f"OCR PDF 第 {attempt} 次失败 ({type(e).__name__}: {e})，{delay}s 后重试...\n{tb}")
                    console.print(f"[yellow]OCR PDF 第 {attempt} 次失败 ({type(e).__name__}: {e})，{delay}s 后重试...[/yellow]")
                    time.sleep(delay)
                else:
                    logger.error(f"OCR PDF 全部 {max_retries} 次重试失败 ({type(last_error).__name__}: {last_error})\n{tb}")
                    console.print(f"[red]OCR PDF 解析失败（已重试 {max_retries} 次）: {type(last_error).__name__}: {last_error}[/red]")
        if result is not None:
            ocr_results.append(result)

    # 图片并行上传
    if image_paths:
        img_results = None
        for attempt in range(1, max_retries + 1):
            try:
                img_results = run_async(
                    client.parse_images_async(image_paths, save_output=True)
                )
                break
            except Exception as e:
                last_error = e
                tb = traceback.format_exc()
                if attempt < max_retries:
                    delay = retry_delays[attempt - 1]
                    logger.warning(f"OCR 图片第 {attempt} 次失败 ({type(e).__name__}: {e})，{delay}s 后重试...\n{tb}")
                    console.print(f"[yellow]OCR 图片第 {attempt} 次失败 ({type(e).__name__}: {e})，{delay}s 后重试...[/yellow]")
                    time.sleep(delay)
                else:
                    logger.error(f"OCR 图片全部 {max_retries} 次重试失败 ({type(last_error).__name__}: {last_error})\n{tb}")
                    console.print(f"[red]OCR 图片解析失败（已重试 {max_retries} 次）: {type(last_error).__name__}: {last_error}[/red]")
        if img_results:
            ocr_results.extend(img_results)

    if not ocr_results:
        return []

    return simplify_ocr_results(ocr_results)


def _build_overlapping_batches(
    ocr_data: List[Dict[str, Any]],
    batch_size: int = 2,
    overlap: int = 1,
) -> List[List[Dict[str, Any]]]:
    """构建重叠批次，并为每页打上 is_primary 标记。

    每批 batch_size 页，相邻批次重叠 overlap 页。
    例如 5 页, batch_size=2, overlap=1:
        批次0: [page0(primary), page1(context)]
        批次1: [page1(primary), page2(context)]
        批次2: [page2(primary), page3(context)]
        批次3: [page3(primary), page4(primary←最后一批)]

    is_primary=True  → Agent 必须提取该页开始的所有题目
    is_primary=False → 仅作跨页上下文，Agent 不提取该页独立开始的题目

    最后一批次的所有页均为 primary（最后一页没有后续批次来处理它）。
    """
    if not ocr_data:
        return []

    n_pages = len(ocr_data)
    if n_pages <= batch_size:
        # 只有一批：全部页都是 primary
        return [[dict(page, is_primary=True) for page in ocr_data]]

    step = batch_size - overlap
    batches = []
    for start in range(0, n_pages, step):
        end = min(start + batch_size, n_pages)
        is_last = (end >= n_pages)
        batch = []
        for page_idx, page in enumerate(ocr_data[start:end]):
            # 第一页始终 primary；最后批次的所有页都 primary
            primary = (page_idx == 0) or is_last
            batch.append(dict(page, is_primary=primary))
        batches.append(batch)
        if is_last:
            break

    return batches


def _load_db_context():
    """加载数据库已有科目和标签"""
    db_subjects = []
    db_tags = []
    try:
        from db import SessionLocal
        from db.crud import get_existing_subjects, get_existing_tag_names

        with SessionLocal() as db:
            db_subjects = get_existing_subjects(db)
            db_tags = get_existing_tag_names(db)

        logger.info(f"已加载 DB 上下文: {len(db_subjects)} 个科目, {len(db_tags)} 个标签")
    except Exception as e:
        logger.warning(f"加载 DB 上下文失败（不影响分割）: {e}")
    return db_subjects, db_tags


def _extract_text_sample(ocr_data: List[Dict[str, Any]]) -> str:
    """从 OCR 数据前 2 页提取文本

    只读取 text / paragraph_title / doc_title 类型的 block。

    Args:
        ocr_data: 简化后的 OCR 数据列表

    Returns:
        拼接的文本字符串
    """
    if not ocr_data:
        return ""

    text_sample = ""
    for page in ocr_data[:2]:
        for block in page.get("blocks", []):
            if block.get("block_label") in ("text", "paragraph_title", "doc_title"):
                text_sample += block.get("block_content", "") + "\n"
    return text_sample


def _identify_subject(
    ocr_data: List[Dict[str, Any]],
    db_subjects: List[str],
    model_provider: str = "openai",
) -> str:
    """从 OCR 数据前几页识别科目（三层 fallback）

    1. LLM 预检（轻量模型，失败时静默 fallback）
    2. 关键词匹配（DB 已有科目 + 通用关键词）
    3. 内容特征推断（指标词计数）

    Args:
        ocr_data: 简化后的 OCR 数据列表
        db_subjects: 数据库已有科目列表
        model_provider: 模型供应商
    """
    if not ocr_data:
        return ""

    text_sample = _extract_text_sample(ocr_data)

    # ── 第 1 层：LLM 预检 ──
    try:
        from agents.error_correction.agent import detect_subject_via_llm

        llm_result = detect_subject_via_llm(text_sample, db_subjects, provider=model_provider)
        if llm_result:
            logger.info(f"LLM 科目识别成功: {llm_result}")
            return llm_result
    except Exception as e:
        logger.warning(f"LLM 科目识别失败，回退关键词匹配: {e}")

    # ── 第 2 层：关键词匹配 ──
    # 优先匹配 DB 已有科目
    for subj in db_subjects:
        if subj in text_sample:
            return subj

    # 通用关键词匹配
    subject_keywords = {
        "高中数学": ["数学试卷", "数学考试", "数学试题", "高中数学"],
        "高中物理": ["物理试卷", "物理考试", "物理试题", "高中物理"],
        "高中化学": ["化学试卷", "化学考试", "化学试题", "高中化学"],
        "高中生物": ["生物试卷", "生物考试", "生物试题", "高中生物"],
        "高中英语": ["英语试卷", "英语考试", "英语试题", "高中英语"],
        "高中语文": ["语文试卷", "语文考试", "语文试题", "高中语文"],
        "初中数学": ["初中数学"],
        "初中物理": ["初中物理"],
        "初中化学": ["初中化学"],
    }
    for subj, keywords in subject_keywords.items():
        for kw in keywords:
            if kw in text_sample:
                return subj

    # ── 第 3 层：内容特征推断 ──
    indicators = {
        "高中数学": ["函数", "方程", "不等式", "三角", "向量", "概率", "数列", "导数", "圆锥", "椭圆"],
        "高中物理": ["力", "速度", "加速度", "电场", "磁场", "动能", "势能"],
        "高中化学": ["离子", "溶液", "元素", "原子", "分子", "化学反应"],
    }
    scores = {subj: sum(1 for w in words if w in text_sample) for subj, words in indicators.items()}
    best = max(scores, key=scores.get)
    if scores[best] >= 2:
        return best

    return ""


def _content_fingerprint(q: Dict[str, Any]) -> str:
    """取第一个非空文本块的前 50 字作为内容指纹。

    重叠页产生的真重复：OCR 源文本相同，LLM 输出高度一致，前 50 字必然相同。
    不同板块的同号题（如小学试卷各板块都有第 1 题）：内容截然不同，指纹不同。
    """
    for block in q.get("content_blocks", []):
        content = block.get("content", "").strip()
        if content:
            return content[:50]
    return ""


def _question_text(q: Dict[str, Any], chars: int = 400) -> str:
    """提取题目纯文本，用于相似度计算。

    包含：content_blocks 中的 text 块（去除 HTML 标签）+ options 选项列表。
    image 块不参与计算。

    chars 上限设为 400：覆盖大多数题目的完整内容，同时避免超长题目的 O(n²) 开销。

    去除 HTML 标签的原因：表格题目在不同批次的 table 结构可能不同（th/td 排列差异），
    但纯文本内容相同。去标签后两个版本的实验描述文字完全一致，相似度可正确判断。

    纳入 options 的原因：跨页截断时题干可能不同，但选项往往相同，是最稳定的指纹。
    """
    parts = []
    for block in q.get("content_blocks", []):
        if block.get("block_type") == "text":
            content = block.get("content", "")
            content = _HTML_TAG_RE.sub("", content)   # 去除 HTML 标签，保留文本
            parts.append(content)
    for opt in q.get("options") or []:
        if isinstance(opt, str):
            parts.append(opt)
    return "".join(parts)[:chars]


def _image_paths(q: Dict[str, Any]) -> set:
    """提取题目所有 image block 的路径集合，用于图片指纹比对。"""
    paths = set()
    for block in q.get("content_blocks", []):
        if block.get("block_type") == "image":
            p = block.get("content", "").strip()
            if p:
                paths.add(p)
    return paths


def _text_similarity(q1: Dict[str, Any], q2: Dict[str, Any]) -> float:
    """计算两道题目内容相似度，返回 0~1。

    优先用文本相似度（difflib）；若两题文本均过短（图片题），
    则用图片路径 Jaccard 系数兜底，避免纯图片题的重复无法被检测到。
    """
    t1 = _question_text(q1)
    t2 = _question_text(q2)

    # 文本足够长时直接用 difflib
    if len(t1) >= 10 and len(t2) >= 10:
        return _difflib.SequenceMatcher(None, t1, t2).ratio()

    # 文本过短（图片题）：用图片路径 Jaccard 系数兜底
    imgs1 = _image_paths(q1)
    imgs2 = _image_paths(q2)
    if imgs1 or imgs2:
        intersection = len(imgs1 & imgs2)
        union = len(imgs1 | imgs2)
        return intersection / union if union else 0.0

    # 文本和图片都为空：不认为是重复
    return 0.0


def _fix_leading_images(questions: List[Dict[str, Any]]) -> None:
    """后处理：将题目 content_blocks 中排在所有文本之前的图片移到前一道题末尾。

    产生原因：试卷某题的插图印在下一页顶部，OCR 按页面顺序扫描时，该图片
    出现在下一题文字之前。Agent 在该批次里将其归入下一题的 content_blocks 首位，
    实际上属于上一题。

    判断规则：若一道题的 content_blocks 中第一个出现的 text block 之前存在
    image block，则这些 leading image 属于上一道题，移至上一题末尾。
    """
    for i in range(1, len(questions)):
        q = questions[i]
        blocks = q.get("content_blocks") or []
        if not blocks:
            continue

        # 分离开头的连续 image 块（在第一个 text 块之前）
        leading_images: List[Dict[str, Any]] = []
        rest: List[Dict[str, Any]] = []
        found_text = False
        for block in blocks:
            if not found_text and block.get("block_type") == "image":
                leading_images.append(block)
            else:
                if block.get("block_type") == "text":
                    found_text = True
                rest.append(block)

        if not leading_images:
            continue

        # 若去掉 leading images 后该题没有任何文本，说明它本身是纯图片题，不搬移
        if not any(b.get("block_type") == "text" for b in rest):
            continue

        # 移到前一道题末尾
        prev_q = questions[i - 1]
        prev_blocks = prev_q.get("content_blocks") or []
        prev_q["content_blocks"] = prev_blocks + leading_images
        q["content_blocks"] = rest
        logger.info(
            f"修复 leading image: {len(leading_images)} 张图片 "
            f"从题目 {q.get('question_id')} 移至题目 {prev_q.get('question_id')}"
        )


def _normalize_image_paths(questions: List[Dict[str, Any]]) -> None:
    """修复 LLM 可能篡改的图片路径，原地修改。

    LLM 有时会把输入中的 '/images/xxx.jpg' 改写为 'imgs/xxx.jpg'，
    导致前端通过 Vite proxy 请求时路径不匹配。统一规范为 '/images/xxx'。
    """
    def _fix(path: str) -> str:
        p = path.strip()
        if p.startswith("imgs/"):
            return "/images/" + p[len("imgs/"):]
        return p

    for q in questions:
        for block in q.get("content_blocks") or []:
            content = block.get("content", "")
            if block.get("block_type") == "image":
                block["content"] = _fix(content)
            elif block.get("block_type") == "text" and "imgs/" in content:
                # 修复 text block 中嵌入的 HTML 图片路径（如 table 中的 <img>）
                block["content"] = content.replace('src="imgs/', 'src="/images/')
        if q.get("image_refs"):
            q["image_refs"] = [_fix(ref) for ref in q["image_refs"]]
        if q.get("option_images"):
            q["option_images"] = [_fix(ref) if ref else ref for ref in q["option_images"]]


def _clean_extracted_answer(text: str) -> str:
    """清理提取出的答案文本，去掉多余前缀与空白。"""
    cleaned = (text or "").strip()
    cleaned = cleaned.lstrip(":： \n\r\t")
    return cleaned.strip()


def _question_id_from_text(text: str) -> str | None:
    """从文本块开头提取题号。"""
    match = _QUESTION_START_RE.match((text or "").strip())
    return match.group(1) if match else None


def _first_question_page_index(ocr_data: List[Dict[str, Any]]) -> int | None:
    """找到第一张出现题目的页面索引。"""
    for page in ocr_data:
        for block in page.get("blocks", []):
            if _question_id_from_text(block.get("block_content", "")):
                return int(page.get("page_index", 0))
    return None


def _classify_answer_layout(ocr_data: List[Dict[str, Any]]) -> str:
    """判断试卷是题答混排还是答案后置。

    规则：只看第一张出现题目的页面。若该页同时出现明显答案标记，则视为 mixed_inline；
    否则视为 separated_tail。
    """
    first_page_idx = _first_question_page_index(ocr_data)
    if first_page_idx is None:
        return "unknown"

    for page in ocr_data:
        if int(page.get("page_index", -1)) != first_page_idx:
            continue
        for block in page.get("blocks", []):
            content = (block.get("block_content") or "").strip()
            if not content:
                continue
            if _ANSWER_MARKER_RE.search(content):
                return "mixed_inline"
        break

    return "separated_tail"


def _extract_inline_answer_from_text(text: str) -> tuple[str, str | None]:
    """从单段题干文本中提取尾部答案或解析。

    仅在答案标记出现在文本后半段时才剥离，尽量避免误伤题干中正常出现的“答案”字样。
    """
    if not text:
        return text, None

    candidates = list(_ANSWER_MARKER_RE.finditer(text))
    if not candidates:
        return text, None

    split_at = None
    for match in candidates:
        if match.start() >= max(4, len(text) // 3):
            split_at = match.start()
            break

    if split_at is None:
        return text, None

    question_text = text[:split_at].rstrip(" \n\r\t:：;；,，。")
    answer_text = _clean_extracted_answer(text[split_at:])

    if not question_text or not answer_text:
        return text, None

    return question_text, answer_text


def _extract_inline_answers(questions: List[Dict[str, Any]]) -> int:
    """从题目尾部剥离混入题干的答案或解析。"""
    extracted = 0
    for q in questions:
        blocks = q.get("content_blocks") or []
        last_text_idx = None
        for idx in range(len(blocks) - 1, -1, -1):
            if blocks[idx].get("block_type") == "text":
                last_text_idx = idx
                break

        if last_text_idx is None:
            continue

        original = blocks[last_text_idx].get("content", "")
        cleaned, answer = _extract_inline_answer_from_text(original)
        if not answer:
            continue

        blocks[last_text_idx]["content"] = cleaned
        if not cleaned.strip():
            del blocks[last_text_idx]

        existing_answer = (q.get("answer") or "").strip()
        q["answer"] = answer if not existing_answer else f"{existing_answer}\n{answer}"
        extracted += 1
    return extracted


def _is_answer_section_title(text: str) -> bool:
    """判断一段 OCR 文本是否像是答案区标题。"""
    compact = _re.sub(r"\s+", "", (text or ""))
    if not compact or len(compact) > 30:
        return False
    markers = ("参考答案", "答案与解析", "试题答案", "参考解答", "答案")
    return any(marker in compact for marker in markers)


def _page_section_title_kind(page: Dict[str, Any]) -> str | None:
    """返回页面首个大标题的类型：answer / question / None。"""
    titles = []
    for block in sorted(page.get("blocks", []), key=lambda item: item.get("block_order") or 0):
        if block.get("block_label") != "paragraph_title":
            continue
        content = (block.get("block_content") or "").strip()
        if content:
            titles.append(content)

    if not titles:
        return None

    first_title = titles[0]
    return "answer" if _is_answer_section_title(first_title) else "question"


def _split_separated_tail_page_groups(
    ocr_data: List[Dict[str, Any]],
) -> tuple[List[int], List[int]]:
    """按整页区间划分题目页/答案页。

    规则：
    1. 先识别“首个大标题带答案字样”的页面，作为答案区起点页。
    2. 从该页开始直到文档结束，整页都算答案页。
    3. 起点页之前的页面都算题目页。
    """
    question_pages: List[int] = []
    answer_pages: List[int] = []
    in_answer_section = False

    for page in sorted(ocr_data, key=lambda item: int(item.get("page_index", 0))):
        page_idx = int(page.get("page_index", 0))
        title_kind = _page_section_title_kind(page)

        if title_kind == "answer":
            in_answer_section = True

        if in_answer_section:
            answer_pages.append(page_idx)
        else:
            question_pages.append(page_idx)

    return question_pages, answer_pages


def _preprocess_separated_tail_answers(
    ocr_data: List[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], Dict[str, str]]:
    """处理“题目和答案分开”版式。

    一旦某页的首个大标题带“答案/参考”字样，则从该页开始，到下一张首个大标题恢复为题目标题的页面前，
    整页都视为答案区，从 OCR 输入中移除，避免进入题目分割。
    """
    question_pages, answer_pages = _split_separated_tail_page_groups(ocr_data)
    answer_page_set = set(answer_pages)
    cleaned_pages: List[Dict[str, Any]] = [
        {
            "page_index": page.get("page_index"),
            "blocks": [dict(block) for block in page.get("blocks", [])],
        }
        for page in ocr_data
        if int(page.get("page_index", 0)) not in answer_page_set
    ]

    valid_question_ids = {
        _question_id_from_text((block.get("block_content") or "").strip())
        for page in cleaned_pages
        for block in page.get("blocks", [])
        if _question_id_from_text(block.get("block_content", ""))
    }
    valid_question_ids.discard(None)
    answer_map = _collect_answer_key_from_ocr(ocr_data, valid_question_ids)
    return cleaned_pages, answer_map


def _preprocess_mixed_inline_answers(
    ocr_data: List[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], Dict[str, str]]:
    """处理“题目后面紧跟答案”版式。

    检测到 `解：/答案：/解析：` 后，直到下一道题出现前的文本、公式、图片都视为答案，
    从送入分割模型的 OCR 数据里移除，并按题号记录到 answer_map。
    """
    cleaned_pages: List[Dict[str, Any]] = []
    answer_map: Dict[str, str] = {}
    current_qid: str | None = None
    in_answer_zone = False

    def append_answer(qid: str | None, text: str) -> None:
        if not qid:
            return
        cleaned = _clean_extracted_answer(text)
        if not cleaned:
            return
        prev = answer_map.get(qid)
        answer_map[qid] = cleaned if not prev else f"{prev}\n{cleaned}"

    for page in ocr_data:
        cleaned_blocks: List[Dict[str, Any]] = []
        for block in page.get("blocks", []):
            label = block.get("block_label")
            content = block.get("block_content", "") or ""
            question_id = _question_id_from_text(content) if label in ("text", "paragraph_title", "doc_title") else None

            if question_id:
                current_qid = question_id
                if in_answer_zone:
                    in_answer_zone = False

            if label in ("text", "paragraph_title", "doc_title"):
                if in_answer_zone and question_id:
                    cleaned_blocks.append(dict(block))
                    continue

                cleaned_text, extracted_answer = _extract_inline_answer_from_text(content)
                if extracted_answer and current_qid:
                    in_answer_zone = True
                    append_answer(current_qid, extracted_answer)
                    if cleaned_text.strip():
                        kept_block = dict(block)
                        kept_block["block_content"] = cleaned_text
                        cleaned_blocks.append(kept_block)
                    continue

                if in_answer_zone:
                    append_answer(current_qid, content)
                    continue

                cleaned_blocks.append(dict(block))
                continue

            if in_answer_zone:
                # 公式/图片/表格也算答案区内容，不再送进题目分割
                append_answer(current_qid, str(content))
                continue

            cleaned_blocks.append(dict(block))

        cleaned_pages.append({
            "page_index": page.get("page_index"),
            "blocks": cleaned_blocks,
        })

    return cleaned_pages, answer_map


def _preprocess_ocr_for_answer_layout(
    ocr_data: List[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], Dict[str, str], str]:
    """在 OCR 之后、AI 分割之前，先判断答案版式并清洗输入。"""
    layout = _classify_answer_layout(ocr_data)
    if layout == "mixed_inline":
        cleaned, answer_map = _preprocess_mixed_inline_answers(ocr_data)
    elif layout == "separated_tail":
        cleaned, answer_map = _preprocess_separated_tail_answers(ocr_data)
    else:
        cleaned, answer_map = ocr_data, {}

    logger.info(f"答案版式判断: {layout}, 预提取答案 {len(answer_map)} 道")
    return cleaned, answer_map, layout


def _collect_answer_key_from_ocr(
    ocr_data: List[Dict[str, Any]],
    valid_question_ids: set[str],
) -> Dict[str, str]:
    """从 OCR 答案页提取题号到答案的映射。"""
    if not ocr_data or not valid_question_ids:
        return {}

    _, answer_pages = _split_separated_tail_page_groups(ocr_data)
    answer_page_set = set(answer_pages)
    if not answer_page_set:
        return {}

    answer_chunks: List[str] = []
    for page in ocr_data:
        if int(page.get("page_index", 0)) not in answer_page_set:
            continue
        for block in page.get("blocks", []):
            if block.get("block_label") not in ("text", "paragraph_title", "doc_title"):
                continue
            content = (block.get("block_content") or "").strip()
            if not content:
                continue
            if _is_answer_section_title(content):
                continue
            answer_chunks.append(content)

    if not answer_chunks:
        return {}

    merged_text = "\n".join(answer_chunks)
    pattern = _re.compile(
        r"(?<!\d)(\d{1,3})\s*[.、．:：]?\s*(.*?)(?=(?<!\d)\d{1,3}\s*[.、．:：]|\Z)",
        _re.S,
    )

    answer_map: Dict[str, str] = {}
    for match in pattern.finditer(merged_text):
        qid = match.group(1).strip()
        if qid not in valid_question_ids:
            continue
        answer_text = _clean_extracted_answer(match.group(2))
        if not answer_text:
            continue
        previous = answer_map.get(qid)
        if previous is None or len(answer_text) > len(previous):
            answer_map[qid] = answer_text

    return answer_map


def _attach_answers(questions: List[Dict[str, Any]], ocr_data: List[Dict[str, Any]]) -> None:
    """统一处理题目答案：先剥离题干内答案，再尝试从答案区回填。"""
    inline_count = _extract_inline_answers(questions)

    from collections import Counter

    qid_counts = Counter(str(q.get("question_id", "")).strip() for q in questions if q.get("question_id"))
    unique_qids = {qid for qid, count in qid_counts.items() if count == 1}
    answer_map = _collect_answer_key_from_ocr(ocr_data, unique_qids)

    attached_count = 0
    for q in questions:
        qid = str(q.get("question_id", "")).strip()
        if not qid or qid not in answer_map or q.get("answer"):
            continue
        q["answer"] = answer_map[qid]
        attached_count += 1

    if inline_count or attached_count:
        logger.info(
            f"答案分离完成: 题干内剥离 {inline_count} 道, 答案区回填 {attached_count} 道"
        )


def _merge_prefetched_answers(questions: List[Dict[str, Any]], answer_map: Dict[str, str]) -> int:
    """把 OCR 预处理阶段提取出的答案回填到题目上。"""
    if not answer_map:
        return 0

    from collections import Counter

    qid_counts = Counter(str(q.get("question_id", "")).strip() for q in questions if q.get("question_id"))
    attached = 0
    for q in questions:
        qid = str(q.get("question_id", "")).strip()
        if not qid or qid_counts.get(qid) != 1:
            continue
        answer = answer_map.get(qid)
        if not answer:
            continue
        existing = (q.get("answer") or "").strip()
        if existing:
            continue
        q["answer"] = answer
        attached += 1
    return attached


def _propagate_section_between_batches(batch_results: List[List[Dict[str, Any]]]) -> None:
    """跨批次传播 section_title，原地修改 batch_results。

    并行批次处理完成后调用。若批次 i 开头若干题的 section_title=None，
    说明大题标题在前一批次的页面里，当前批次窗口看不到。
    从批次 i-1 的末尾向前找最后一个有 section_title 的题，将其 section_title
    赋给批次 i 中连续的 section=None 开头题，遇到批次 i 自己识别出 section_title
    的题时停止传播。

    防误传：若待传播 section 是在批次 i-1 中由题号较大的题建立的，则不向题号
    更小的题传播（说明该 None 题属于更早的大题，而非当前 last_section）。
    """
    def _to_int_id(q) -> int | None:
        try:
            return int(str(q.get("question_id", "")).strip())
        except (ValueError, TypeError):
            return None

    for i in range(1, len(batch_results)):
        # 单次遍历上一批次：同时找 last_section 和该节首次出现的最小题号
        last_section = None
        first_section_id: int | None = None
        for q in batch_results[i - 1]:
            s = q.get("section_title")
            if s:
                if s != last_section:
                    # 进入新节，重置首题号
                    last_section = s
                    first_section_id = None
                qid = _to_int_id(q)
                if qid is not None:
                    if first_section_id is None or qid < first_section_id:
                        first_section_id = qid

        if not last_section:
            continue

        # 将 last_section 赋给本批次开头连续的 section=None 题
        # 防误传：若待传播题的题号 < first_section_id，说明它属于更早的大题，跳过
        propagated = 0
        for q in batch_results[i]:
            if not q.get("section_title"):
                qid = _to_int_id(q)
                if first_section_id is not None and qid is not None and qid < first_section_id:
                    # 该题题号比 last_section 第一题还小，不应继承该 section
                    continue
                q["section_title"] = last_section
                propagated += 1
            else:
                break  # 本批次已有自己识别出的 section，停止传播

        if propagated:
            logger.info(
                f"跨批次 section 传播: 批次 {i} 前 {propagated} 道题 "
                f"继承 section_title={repr(last_section)}"
            )


def _dedup_questions(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """按「(大题, 题号)」去重，再用内容相似度消除跨批次重复。

    第一轮：同一 (section_title, question_id) 内保留最丰富版本。
    第二轮：同一 question_id 下若有多份，两两计算前 120 字相似度；
            相似度 ≥ 0.75 视为重复，优先保留有 section_title 的版本，
            相似度 < 0.75 视为不同大题下的同号题，全部保留。
    """
    if not questions:
        return []

    from collections import defaultdict

    # ── 预处理：将 question_id 统一归一化为 str，防止 int/str 类型不一致导致去重失效 ──
    for q in questions:
        qid = q.get("question_id")
        if qid is not None:
            q["question_id"] = str(qid).strip()

    # ── 第一轮：按 (section, qid) 复合键去重 ──────────────────
    groups: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
    no_id: List[Dict[str, Any]] = []

    for q in questions:
        qid = q.get("question_id", "")
        if not qid:
            no_id.append(q)
        else:
            section = q.get("section_title") or ""
            groups[(section, qid)].append(q)

    after_round1: List[Dict[str, Any]] = list(no_id)
    for qs in groups.values():
        after_round1.append(max(qs, key=_question_richness))

    # ── 第二轮：结构优先 + 内容相似度去重 ───────────────────────
    # 策略：
    #   1. 同一 qid 下同时存在有 section 和无 section 版本 → 直接丢弃所有 section=None 版本
    #      （section=None 说明该批次只捕获到选项/部分内容，有 section 的是完整版本）
    #   2. 同一 qid 下均有 section（不同 section）→ difflib 相似度 ≥ 0.75 视为重复，保留最优
    #   3. 同一 qid 下均无 section → 保留内容最丰富的一份
    by_qid: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for q in after_round1:
        by_qid[q.get("question_id", "")].append(q)

    SIMILARITY_THRESHOLD = 0.75
    final: List[Dict[str, Any]] = list(no_id)
    round2_removed = 0

    for qid, entries in by_qid.items():
        if not qid:
            continue
        if len(entries) == 1:
            final.extend(entries)
            continue

        sectioned = [q for q in entries if q.get("section_title")]
        unsectioned = [q for q in entries if not q.get("section_title")]

        # 策略1：有 section 版本存在时，丢弃全部 section=None 版本
        if sectioned and unsectioned:
            round2_removed += len(unsectioned)
            for q in unsectioned:
                logger.debug(
                    f"二次去重剔除(结构): qid={qid} "
                    f"section=None，保留有大题标题的版本，richness={_question_richness(q)}"
                )
            entries = sectioned

        if len(entries) == 1:
            final.extend(entries)
            continue

        # 策略2/3：全部有 section 或全部无 section → difflib 去重
        entries.sort(key=lambda q: (
            0 if q.get("section_title") else 1,
            -_question_richness(q)
        ))

        kept: List[Dict[str, Any]] = []
        for candidate in entries:
            sim = max(
                (_text_similarity(candidate, k) for k in kept),
                default=0.0,
            )
            if sim >= SIMILARITY_THRESHOLD:
                round2_removed += 1
                logger.debug(
                    f"二次去重剔除(相似度): qid={qid} "
                    f"section={repr(candidate.get('section_title'))} "
                    f"相似度={sim:.2f}"
                )
            else:
                kept.append(candidate)
        final.extend(kept)

    if round2_removed:
        logger.info(f"二次去重: 剔除 {round2_removed} 道重复题目（结构优先 + 相似度阈值={SIMILARITY_THRESHOLD}）")
        console.print(f"[yellow]二次去重: 剔除 {round2_removed} 道重复题目[/yellow]")

    # ── 排序：有 section 的题按首次出现顺序 + 题号，section=None 的题排最后 ──
    section_order: Dict[str, int] = {}
    for q in questions:
        s = q.get("section_title")
        if s and s not in section_order:
            section_order[s] = len(section_order)

    final.sort(key=lambda q: (
        0 if q.get("section_title") else 1,          # 有 section 的排前，None 排后
        section_order.get(q.get("section_title") or "", 999),
        _sort_key(q.get("question_id", ""))
    ))
    return final


def _question_richness(q: Dict[str, Any]) -> int:
    """计算题目内容丰富度（总字符数）"""
    score = 0
    for block in q.get("content_blocks", []):
        score += len(block.get("content", ""))
    for opt in (q.get("options") or []):
        score += len(opt)
    return score


def _sort_key(qid: str):
    """题号排序: 纯数字按数值，否则按字符串"""
    try:
        return (0, int(qid), "")
    except ValueError:
        return (1, 0, qid)


def split_questions_node(state: WorkflowState) -> dict:
    """节点: 并行 OCR + 分割题目

    不再依赖编排智能体的顺序处理，而是直接执行：
    1. OCR 解析（PaddleOCR，图片级并行）
    2. 构建重叠批次（2页/批，1页重叠）
    3. 并行调用 split_batch（批次级并行，每批独立的内层 agent）
    4. 按 question_id 去重（重叠页产生的重复题目）
    5. 保存结果
    """
    console.print("[bold yellow]步骤 2: 并行 OCR + 分割题目[/bold yellow]")
    step_start = time.time()

    results_dir = settings.results_dir
    os.makedirs(results_dir, exist_ok=True)

    file_paths = state["image_paths"]
    model_provider = state.get("model_provider", "openai")
    model_name = state.get("model_name")
    confirmed_answer_layout = state.get("confirmed_answer_layout", "")
    selected_page_indices = [int(i) for i in (state.get("selected_page_indices") or [])]
    llm_credentials = state.get("llm_credentials") or {}
    ocr_credentials = state.get("ocr_credentials") or {}

    # 清空旧的 questions.json 和 split_metadata.json
    questions_file = os.path.join(results_dir, "questions.json")
    if os.path.exists(questions_file):
        os.remove(questions_file)
    meta_path = os.path.join(results_dir, "split_metadata.json")
    if os.path.exists(meta_path):
        os.remove(meta_path)

    # ── Step 1: OCR 解析（优先使用缓存） ──
    ocr_cache_path = state.get("ocr_cache_path") or os.path.join(results_dir, "ocr_cache.json")
    ocr_data = None
    if os.path.exists(ocr_cache_path):
        try:
            with open(ocr_cache_path, 'r', encoding='utf-8') as f:
                ocr_data = json.load(f)
            console.print(f"[green]✓ 使用 OCR 缓存: {len(ocr_data)} 页[/green]")
            logger.info(f"使用 OCR 缓存: {len(ocr_data)} 页")
            os.remove(ocr_cache_path)  # 用完即删，避免下次误用
        except Exception as e:
            logger.warning(f"读取 OCR 缓存失败: {e}，将重新执行 OCR")
            ocr_data = None

    if not ocr_data:
        console.print(f"[cyan]OCR 解析 {len(file_paths)} 个文件...[/cyan]")
        ocr_start = time.time()
        ocr_data = _run_ocr_and_simplify(file_paths, ocr_credentials=ocr_credentials)

        if not ocr_data:
            logger.error("OCR 解析失败，无数据返回")
            console.print("[red]⚠ OCR 解析失败[/red]")
            return {
                "questions": [],
                "warnings": ["步骤 2（OCR 解析）失败：无法解析图片内容，请检查 PaddleOCR API Token 配置"],
            }

        total_blocks = sum(len(p.get("blocks", [])) for p in ocr_data)
        ocr_elapsed = time.time() - ocr_start
        logger.info(f"OCR 完成: {len(ocr_data)} 页, {total_blocks} 个 block, 耗时 {ocr_elapsed:.2f}s")
        console.print(f"[green]✓ OCR 完成: {len(ocr_data)} 页, {total_blocks} 个 block ({ocr_elapsed:.1f}s)[/green]")

    if confirmed_answer_layout == "separated_tail" and selected_page_indices:
        selected_page_set = set(selected_page_indices)
        ocr_data = [page for page in ocr_data if int(page.get("page_index", -1)) in selected_page_set]
        logger.info(f"按用户确认仅保留题目页参与分割: {sorted(selected_page_indices)}")
        prefetched_answers = {}
        answer_layout = confirmed_answer_layout
        original_ocr_data = ocr_data
    else:
        original_ocr_data = ocr_data
        ocr_data, prefetched_answers, answer_layout = _preprocess_ocr_for_answer_layout(ocr_data)

    # 保存 agent_input.json（供纠错节点使用）
    agent_input_path = os.path.join(results_dir, "agent_input.json")
    with open(agent_input_path, 'w', encoding='utf-8') as f:
        json.dump(ocr_data, f, ensure_ascii=False, indent=2)

    # ── Step 2: 加载 DB 上下文 ──
    db_subjects, db_tags = _load_db_context()

    # ── Step 3: 识别科目 ──
    subject = _identify_subject(ocr_data, db_subjects, model_provider=model_provider)
    if subject:
        console.print(f"[cyan]识别科目: {subject}[/cyan]")
        logger.info(f"识别科目: {subject}")

    # ── Step 3.5: 按科目过滤知识点标签 ──
    if subject and db_tags:
        from db import SessionLocal
        from db.crud import get_existing_tag_names

        try:
            with SessionLocal() as db:
                db_tags = get_existing_tag_names(db, subject=subject)
            logger.info(f"按科目 '{subject}' 过滤后剩余 {len(db_tags)} 个标签")
        except Exception as e:
            logger.warning(f"按科目过滤标签失败，使用全量标签: {e}")

    # ── Step 4: 构建重叠批次 ──
    batches = _build_overlapping_batches(ocr_data, batch_size=2, overlap=1)
    console.print(f"[cyan]构建 {len(batches)} 个批次（每批1主页+1上下文页）[/cyan]")

    # 保存完整批次数据到 agent_input.json（含 is_primary 标记，供调试和纠错节点使用）
    agent_input_path = os.path.join(results_dir, "agent_input.json")
    with open(agent_input_path, 'w', encoding='utf-8') as f:
        json.dump(batches, f, ensure_ascii=False, indent=2)

    # ── Step 5: 并行分割 ──
    split_start = time.time()
    console.print(f"[cyan]并行分割 {len(batches)} 个批次...[/cyan]")

    from agents.error_correction.tools import split_batch

    existing_tags_str = ",".join(db_tags) if db_tags else ""
    max_workers = min(len(batches), 3)
    batch_results: List[List[Dict[str, Any]]] = [[] for _ in range(len(batches))]
    batch_errors: List[str] = []  # 记录失败原因，供 warning 使用

    max_batch_retries = 2

    def _invoke_split(batch_idx: int, batch_data: list) -> None:
        """在线程中调用 split_batch 并存储结果（含重试）"""
        for attempt in range(1, max_batch_retries + 1):
            try:
                invoke_kwargs = {
                    "ocr_data": json.dumps(batch_data, ensure_ascii=False),
                    "subject": subject,
                    "existing_tags": existing_tags_str,
                    "model_provider": model_provider,
                    "answer_layout": answer_layout,
                }
                if model_name:
                    invoke_kwargs["model_name"] = model_name
                result_str = split_batch.invoke(invoke_kwargs)
                # split_batch 内部捕获异常并返回 "分割失败: ..." 字符串，
                # 需要检测这种情况并触发重试
                if not result_str or not result_str.startswith("["):
                    raise RuntimeError(f"split_batch 返回非JSON: {result_str[:200]}")
                questions = json.loads(result_str)
                batch_results[batch_idx] = questions
                logger.info(f"批次 {batch_idx} 完成: {len(questions)} 道题目")
                console.print(f"[green]  ✓ 批次 {batch_idx} 完成: {len(questions)} 道题目[/green]")
                return
            except Exception as e:
                if attempt < max_batch_retries:
                    logger.warning(f"批次 {batch_idx} 第 {attempt} 次失败 ({e})，重试中...")
                    console.print(f"[yellow]  ⚠ 批次 {batch_idx} 第 {attempt} 次失败，重试...[/yellow]")
                    time.sleep(2)
                else:
                    logger.error(f"批次 {batch_idx} 分割失败（已重试 {max_batch_retries} 次）: {e}")
                    console.print(f"[red]  ✗ 批次 {batch_idx} 失败: {e}[/red]")
                    batch_errors.append(str(e))

    if len(batches) == 1:
        _invoke_split(0, batches[0])
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                _submit_with_current_context(pool, _invoke_split, i, batch): i
                for i, batch in enumerate(batches)
            }
            # 等待全部完成
            for future in as_completed(futures):
                future.result()  # 触发异常传播（已在 _invoke_split 内处理）

    split_elapsed = time.time() - split_start
    logger.info(f"并行分割完成, 耗时 {split_elapsed:.2f}s")

    # ── Step 6: 跨批次 section 传播 + 合并 ──
    _propagate_section_between_batches(batch_results)

    all_questions = []
    for questions in batch_results:
        all_questions.extend(questions)

    # 暂时关闭自动去重，避免误删本不重复的题目。
    # 当前直接保留批次合并后的原始结果，后续再按真实样本重做更保守的去重策略。
    final_questions = list(all_questions)
    logger.info(f"自动去重已暂时关闭，保留 {len(final_questions)} 道题目")

    # 修复 leading image（页面顶部图属于上一题）
    _fix_leading_images(final_questions)

    # 修复 LLM 可能篡改的图片路径（如 imgs/xxx → /images/xxx）
    _normalize_image_paths(final_questions)

    # 先回填 OCR 预处理阶段已识别的答案；再用旧逻辑做兜底
    prefetched_count = _merge_prefetched_answers(final_questions, prefetched_answers)
    if not (confirmed_answer_layout == "separated_tail" and selected_page_indices):
        _attach_answers(final_questions, original_ocr_data)
    if prefetched_count:
        logger.info(f"OCR 预处理回填答案: {prefetched_count} 道")

    # 重新顺序编号，避免沿用 OCR/LLM 原始题号带来的重复或跳号。
    for i, q in enumerate(final_questions, start=1):
        q["question_id"] = str(i)
        q["uid"] = str(i - 1)

    # ── Step 7: 保存结果 ──
    with open(questions_file, 'w', encoding='utf-8') as f:
        json.dump(final_questions, f, ensure_ascii=False, indent=2)

    if subject:
        meta = {"subject": subject}
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    total_elapsed = time.time() - step_start
    if final_questions:
        logger.info(f"分割完成: 共 {len(final_questions)} 道题目, 总耗时 {total_elapsed:.2f}s")
        console.print(f"[bold green]✓ 成功分割 {len(final_questions)} 道题目 (总耗时 {total_elapsed:.1f}s)[/bold green]")
        return {"questions": final_questions}
    else:
        logger.warning("未生成任何题目，请检查执行日志")
        console.print("[yellow]⚠ 未生成任何题目[/yellow]")
        err_str = " ".join(batch_errors).lower()
        if "401" in err_str or "authentication" in err_str or "invalid" in err_str and "api key" in err_str:
            warning_msg = f"步骤 3（分割题目）失败：LLM API Key 认证错误，请检查 {model_provider.upper()} API Key 配置"
        elif "429" in err_str or "rate limit" in err_str or "quota" in err_str:
            warning_msg = "步骤 3（分割题目）失败：LLM API 请求频率超限，请稍后重试"
        elif batch_errors:
            warning_msg = f"步骤 3（分割题目）失败：{batch_errors[0][:80]}"
        else:
            warning_msg = "步骤 3（分割题目）失败：AI 未能从图片中识别出题目，请确认图片内容包含试题"
        return {
            "questions": [],
            "warnings": [warning_msg],
        }


def correct_questions_node(state: WorkflowState) -> dict:
    """节点: OCR 纠错

    对标记了 needs_correction 的题目执行 OCR 纠错。
    未标记的题目直接通过，不消耗额外 LLM 调用。
    """
    console.print("[bold yellow]步骤 2.5: OCR 纠错检查[/bold yellow]")
    step_start = time.time()

    questions = state.get("questions", [])
    if not questions:
        logger.info("纠错跳过: 无题目")
        return {"questions": questions}

    # 筛选需要纠错的题目
    flagged = [q for q in questions if q.get("needs_correction", False)]

    if not flagged:
        logger.info("纠错跳过: 无需纠错的题目")
        console.print("[green]✓ 所有题目均无 OCR 错误标记，跳过纠错[/green]")
        return {"questions": questions}

    console.print(f"[cyan]发现 {len(flagged)} 道题目需要纠错（共 {len(questions)} 道）[/cyan]")
    logger.info(f"开始纠错: {len(flagged)}/{len(questions)} 道题目")

    # 加载 OCR 数据作为纠错上下文
    # agent_input.json 现在保存的是批次数据（[[page, ...], ...]），需要还原为扁平页面列表
    ocr_context = "{}"
    agent_input_path = os.path.join(settings.results_dir, "agent_input.json")
    if os.path.exists(agent_input_path):
        with open(agent_input_path, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        # 兼容新格式（批次列表）和旧格式（扁平页面列表）
        if raw and isinstance(raw[0], list):
            # 新格式：按 page_index 去重，还原为扁平页面列表
            seen = {}
            for batch in raw:
                for page in batch:
                    idx = page.get("page_index", id(page))
                    if idx not in seen:
                        seen[idx] = page
            flat_pages = [seen[k] for k in sorted(seen)]
            ocr_context = json.dumps(flat_pages, ensure_ascii=False)
        else:
            ocr_context = json.dumps(raw, ensure_ascii=False)

    # 调用纠错工具
    from agents.error_correction.tools import correct_batch

    model_provider = state.get("model_provider", "openai")
    model_name = state.get("model_name")
    flagged_json = json.dumps(flagged, ensure_ascii=False)
    correct_kwargs = {
        "questions_json": flagged_json,
        "ocr_context": ocr_context,
        "model_provider": model_provider,
    }
    if model_name:
        correct_kwargs["model_name"] = model_name
    result_str = correct_batch.invoke(correct_kwargs)

    # 解析纠错结果
    try:
        corrected = json.loads(result_str)
    except (json.JSONDecodeError, TypeError):
        logger.error(f"纠错结果解析失败: {result_str[:200]}")
        console.print("[red]⚠ 纠错结果解析失败，保留原始题目[/red]")
        return {"questions": questions}

    # 按 (section_title, question_id) 复合键合并纠错结果，避免不同大题同号题互相覆盖
    corrected_map = {
        (q.get("section_title") or "", q["question_id"]): q
        for q in corrected
    }

    merged = []
    for q in questions:
        qid = q.get("question_id")
        section = q.get("section_title") or ""
        key = (section, qid)
        if key in corrected_map:
            cq = corrected_map[key]
            corrections = cq.pop("corrections_applied", [])
            cq["needs_correction"] = False
            cq["ocr_issues"] = None
            if not cq.get("answer") and q.get("answer"):
                cq["answer"] = q.get("answer")
            cq["uid"] = q.get("uid")  # 纠错对象来自 LLM 输出，不含 uid，从原题还原
            merged.append(cq)
            logger.info(f"题目 {section}-{qid} 已纠错: {corrections}")
        else:
            merged.append(q)

    # 更新 questions.json
    questions_file = os.path.join(settings.results_dir, "questions.json")
    with open(questions_file, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    logger.info(f"纠错完成: {len(corrected)}/{len(flagged)} 道题目已修复，耗时 {time.time() - step_start:.2f}s")
    console.print(f"[green]✓ 纠错完成: {len(corrected)} 道题目已修复[/green]")

    return {"questions": merged}


def export_node(state: WorkflowState) -> dict:
    """节点: 导出错题本"""
    console.print("[bold yellow]步骤 3: 导出错题本[/bold yellow]")
    step_start = time.time()
    output_path = export_wrongbook(state["questions"], state["selected_ids"])
    logger.info(f"导出完成: {output_path}，耗时 {time.time() - step_start:.2f}s")
    return {"output_path": output_path}


# ── 构建工作流图 ────────────────────────────────────────────


def build_workflow():
    """
    构建并编译工作流图。

    图结构:

        START → prepare_input → [中断] → split_questions → correct_questions → [中断] → export → END

    split_questions 节点直接执行 OCR + 并行分割（不再依赖编排智能体）:
    1. 调用 PaddleOCR API 解析图片（图片级并行）
    2. 构建重叠批次 → 并行调用 split_batch（批次级并行）
    3. 按 question_id 去重 → 保存结果

    纠错节点在分割后自动执行，仅对标记了 needs_correction 的题目调用纠错智能体。

    Returns:
        编译后的 CompiledStateGraph 实例
    """
    builder = StateGraph(WorkflowState)

    # 添加节点
    builder.add_node("prepare_input", prepare_input_node)
    builder.add_node("split_questions", split_questions_node)
    builder.add_node("correct_questions", correct_questions_node)
    builder.add_node("export", export_node)

    # 定义边
    builder.add_edge(START, "prepare_input")
    builder.add_edge("prepare_input", "split_questions")
    builder.add_edge("split_questions", "correct_questions")
    builder.add_edge("correct_questions", "export")
    builder.add_edge("export", END)

    # 编译：MemorySaver 保存中间状态，interrupt_before 在关键节点前暂停
    checkpointer = MemorySaver()
    graph = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["split_questions", "export"],
    )

    return graph
