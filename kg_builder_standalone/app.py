from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from kg_builder_standalone.pipeline import PDFKnowledgeGraphBuilder


st.set_page_config(page_title="教材知识图谱生成器", layout="wide")
st.title("教材 PDF -> 知识图谱（半自动/全自动）")
st.caption("流程：上传 PDF -> 自动抽取候选节点与关系 -> 人工审核 -> 生成最终图谱并可视化")


with st.sidebar:
    st.header("生成参数")
    min_nodes = st.slider("最少知识点", 20, 120, 50)
    max_nodes = st.slider("最多知识点", 30, 160, 100)
    top_terms_per_chapter = st.slider("每章候选关键词数量", 10, 60, 28)
    graph_name = st.text_input("图谱名称", value="course_knowledge_graph")
    output_dir = st.text_input("输出目录", value="kg_builder_standalone/outputs")


uploaded_file = st.file_uploader("上传教材 PDF（支持几十 MB）", type=["pdf"])

if "nodes_df" not in st.session_state:
    st.session_state.nodes_df = pd.DataFrame()
if "edges_df" not in st.session_state:
    st.session_state.edges_df = pd.DataFrame()
if "metadata" not in st.session_state:
    st.session_state.metadata = {}
if "html_path" not in st.session_state:
    st.session_state.html_path = ""


if uploaded_file and st.button("自动生成候选图谱", type="primary"):
    builder = PDFKnowledgeGraphBuilder(
        min_nodes=min_nodes,
        max_nodes=max_nodes,
        top_terms_per_chapter=top_terms_per_chapter,
    )

    with st.spinner("正在解析 PDF 并抽取知识点，请稍候..."):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.getbuffer())
            temp_pdf_path = tmp.name

        nodes_df, edges_df, metadata = builder.generate(temp_pdf_path)

    st.session_state.nodes_df = nodes_df
    st.session_state.edges_df = edges_df
    st.session_state.metadata = metadata
    st.success("候选图谱生成完成。请先人工审核，再点击生成最终图谱。")


if st.session_state.metadata:
    meta = st.session_state.metadata
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("页数", meta.get("pages", 0))
    col2.metric("章节数", meta.get("chapters", 0))
    col3.metric("候选节点", meta.get("selected_nodes", 0))
    col4.metric("候选关系", meta.get("selected_edges", 0))


if not st.session_state.nodes_df.empty:
    st.subheader("人工审核：知识点节点")
    st.session_state.nodes_df = st.data_editor(
        st.session_state.nodes_df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="nodes_editor",
    )

if not st.session_state.edges_df.empty:
    st.subheader("人工审核：知识点关系")
    st.session_state.edges_df = st.data_editor(
        st.session_state.edges_df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="edges_editor",
    )


if not st.session_state.nodes_df.empty and st.button("生成最终知识图谱并可视化"):
    builder = PDFKnowledgeGraphBuilder(
        min_nodes=min_nodes,
        max_nodes=max_nodes,
        top_terms_per_chapter=top_terms_per_chapter,
    )

    final_name = f"{graph_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    paths = builder.finalize(
        nodes_df=st.session_state.nodes_df,
        edges_df=st.session_state.edges_df,
        output_dir=output_dir,
        graph_name=final_name,
    )
    st.session_state.html_path = paths["html"]

    st.success("最终知识图谱已生成。")
    st.write(paths)


if st.session_state.html_path:
    st.subheader("知识图谱可视化")
    html_file = Path(st.session_state.html_path)
    if html_file.exists():
        html_content = html_file.read_text(encoding="utf-8")
        components.html(html_content, height=860, scrolling=True)
        st.download_button(
            label="下载可视化 HTML",
            data=html_content,
            file_name=html_file.name,
            mime="text/html",
        )
