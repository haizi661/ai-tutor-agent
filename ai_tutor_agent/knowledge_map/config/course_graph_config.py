from __future__ import annotations

from typing import Any


# 关系类型配置：后面要改名字、加新关系，都尽量改这里
RELATION_TYPES = {
    "PRE_REQUIRES": "前置关系",
    "LEADS_TO": "后继关系",
    "HAS_SUBTOPIC": "包含关系",
    "RELATED_TO": "相关关系",
    "APPLIED_IN": "应用关系",
}


# 节点层级配置
NODE_LEVELS = {
    1: "一级",
    2: "二级",
}


# 一级/二级知识点骨架
# 先用静态配置，后面再逐步接课程大纲、教材目录、RAG 检索
COURSE_GRAPH_CONFIG: dict[str, Any] = {
    "course_name": "自动控制原理",
    "version": "v2_skeleton",
    "chapters": [
        {
            "chapter": "第一章",
            "name": "自动控制的一般概念",
            "level": 1,
            "enabled": True,
            "is_focus": True,
            "page_range": [9, 32],
            "retrieval_keywords": ["自动控制", "一般概念", "反馈控制系统"],
            "summary": "介绍自动控制的基本原理、系统组成、分类、要求及分析设计工具。",
            "tags": ["自动控制", "基本概念", "控制系统"],
            "subtopics": [
                {
                    "name": "自动控制的基本原理与方式",
                    "summary": "说明自动控制实现的基本机制与常见控制方式。",
                    "tags": ["基本原理", "开环控制", "闭环控制"],
                },
                {
                    "name": "自动控制系统示例",
                    "summary": "通过典型实例理解自动控制系统的构成和工作过程。",
                    "tags": ["系统示例", "实例"],
                },
                {
                    "name": "自动控制系统的分类",
                    "summary": "从不同角度对自动控制系统进行分类。",
                    "tags": ["分类", "开环", "闭环", "系统分类", "控制类型"],
                },
                {
                    "name": "对自动控制系统的基本要求",
                    "summary": "介绍稳定性、快速性、准确性等基本性能要求。",
                    "tags": ["性能要求", "稳定性", "快速性", "准确性"],
                },
                {
                    "name": "自动控制系统的分析与设计工具",
                    "summary": "介绍研究控制系统常用的分析与设计工具。",
                    "tags": ["分析工具", "设计工具", "分析方法", "设计方法"],
                },
            ],
        },
        {
            "chapter": "第二章",
            "name": "控制系统的数学模型",
            "level": 1,
            "enabled": True,
            "is_focus": True,
            "page_range": [33, 81],
            "retrieval_keywords": ["数学模型", "系统建模", "传递函数"],
            "summary": "介绍控制系统的时域模型、复域模型、结构图与信号流图等数学表示方法。",
            "tags": ["数学模型", "传递函数", "方块图", "信号流图"],
            "subtopics": [
                {
                    "name": "控制系统的时域数学模型",
                    "summary": "从微分方程角度建立控制系统的数学模型。",
                    "tags": ["时域模型", "微分方程"],
                },
                {
                    "name": "控制系统的复数域数学模型",
                    "summary": "通过拉普拉斯变换与传递函数描述系统。",
                    "tags": ["复域模型", "传递函数", "拉普拉斯变换"],
                },
                {
                    "name": "控制系统的结构图与信号流图",
                    "summary": "介绍方块图和信号流图的构成与化简方法。",
                    "tags": ["结构图", "信号流图", "化简"],
                },
                {
                    "name": "控制系统建模实例",
                    "summary": "通过典型实例说明系统建模过程。",
                    "tags": ["建模实例", "应用"],
                },
            ],
        },
        {
            "chapter": "第三章",
            "name": "线性系统的时域分析法",
            "level": 1,
            "enabled": True,
            "is_focus": True,
            "page_range": [82, 159],
            "retrieval_keywords": ["时域分析", "时间响应", "系统响应"],
            "summary": "研究线性系统的动态响应、稳态误差与稳定性等时域分析内容。",
            "tags": ["时域分析", "动态响应", "稳态误差", "稳定性"],
            "subtopics": [
                {
                    "name": "系统时间响应的性能指标",
                    "summary": "介绍时域响应中常用的性能评价指标。",
                    "tags": ["性能指标", "超调量", "调节时间"],
                },
                {
                    "name": "一阶系统的时域分析",
                    "summary": "分析一阶系统的单位阶跃响应及性能特征。",
                    "tags": ["一阶系统", "单位阶跃响应"],
                },
                {
                    "name": "二阶系统的时域分析",
                    "summary": "分析二阶系统动态过程及典型性能指标。",
                    "tags": ["二阶系统", "阻尼比", "自然频率"],
                },
                {
                    "name": "高阶系统的时域分析",
                    "summary": "研究高阶系统时域分析中的近似处理方法。",
                    "tags": ["高阶系统", "近似分析"],
                },
                {
                    "name": "线性系统的稳定性分析",
                    "summary": "研究系统稳定性的判别与分析。",
                    "tags": ["稳定性", "稳定判据"],
                },
                {
                    "name": "线性系统的稳态误差计算",
                    "summary": "研究稳态误差的概念、类型及计算方法。",
                    "tags": ["稳态误差", "误差系数"],
                },
                {
                    "name": "控制系统时域设计",
                    "summary": "结合时域指标进行控制系统设计。",
                    "tags": ["时域设计", "系统设计"],
                },
            ],
        },
        {
            "chapter": "第四章",
            "name": "线性系统的根轨迹法",
            "level": 1,
            "enabled": True,
            "is_focus": True,
            "page_range": [160, 204],
            "retrieval_keywords": ["根轨迹", "根轨迹法"],
            "summary": "介绍根轨迹法的基本概念、绘制规则及其在系统分析设计中的应用。",
            "tags": ["根轨迹", "复域分析", "系统设计"],
            "subtopics": [
                {
                    "name": "根轨迹法的基本概念",
                    "summary": "说明根轨迹的定义及其与系统性能的关系。",
                    "tags": ["根轨迹", "基本概念"],
                },
                {
                    "name": "根轨迹绘制的基本法则",
                    "summary": "介绍绘制根轨迹的基本规则。",
                    "tags": ["绘制法则", "根轨迹规则"],
                },
                {
                    "name": "广义根轨迹",
                    "summary": "介绍更一般情况下的根轨迹分析方法。",
                    "tags": ["广义根轨迹"],
                },
                {
                    "name": "系统性能的分析",
                    "summary": "利用根轨迹分析系统动态性能与稳定性。",
                    "tags": ["性能分析", "稳定性"],
                },
                {
                    "name": "控制系统复域设计",
                    "summary": "利用根轨迹进行控制系统设计。",
                    "tags": ["复域设计", "系统设计"],
                },
            ],
        },
        {
            "chapter": "第五章",
            "name": "线性系统的频域分析法",
            "level": 1,
            "enabled": True,
            "is_focus": True,
            "page_range": [205, 262],
            "retrieval_keywords": ["频域分析", "频率响应", "波特图"],
            "summary": "介绍频率特性、频域稳定性分析及频域性能分析方法。",
            "tags": ["频域分析", "频率特性", "Nyquist", "Bode"],
            "subtopics": [
                {
                    "name": "频率特性",
                    "summary": "介绍频率特性的定义与表示方法。",
                    "tags": ["频率特性", "频率响应"],
                },
                {
                    "name": "典型环节与开环系统的频率特性",
                    "summary": "研究典型环节及开环系统的频域特征。",
                    "tags": ["典型环节", "开环系统"],
                },
                {
                    "name": "频率域稳定判据",
                    "summary": "介绍 Nyquist 稳定性判据等频域稳定分析方法。",
                    "tags": ["Nyquist", "稳定判据"],
                },
            ],
        },
        {
            "chapter": "第六章",
            "name": "线性系统的校正方法",
            "level": 1,
            "enabled": True,
            "is_focus": True,
            "page_range": [263, 311],
            "retrieval_keywords": ["系统校正", "控制器设计"],
            "summary": "介绍串联校正、反馈校正、复合校正等控制系统校正方法。",
            "tags": ["校正方法", "超前校正", "滞后校正", "复合校正"],
            "subtopics": [
                {
                    "name": "常用校正装置及其特性",
                    "summary": "介绍常见校正装置及其频率特性。",
                    "tags": ["校正装置", "频率特性"],
                },
                {
                    "name": "串联校正",
                    "summary": "介绍通过串联校正改善系统性能的方法。",
                    "tags": ["串联校正"],
                },
                {
                    "name": "反馈校正",
                    "summary": "介绍通过反馈校正改善系统性能的方法。",
                    "tags": ["反馈校正"],
                },
                {
                    "name": "复合校正",
                    "summary": "介绍复合校正的原理与应用。",
                    "tags": ["复合校正"],
                },
            ],
        },
        {
            "chapter": "第七章",
            "name": "线性离散系统的分析与校正",
            "level": 1,
            "enabled": True,
            "is_focus": False,
            "page_range": [312, 392],
            "retrieval_keywords": ["离散系统", "采样系统"],
            "summary": "介绍离散系统的基本概念、分析方法及数字校正。",
            "tags": ["离散系统", "Z变换", "数字控制"],
            "subtopics": [
                {
                    "name": "离散系统的基本概念",
                    "summary": "介绍离散控制系统与采样过程的基本概念。",
                    "tags": ["离散系统", "采样"],
                },
                {
                    "name": "Z变换与脉冲传递函数",
                    "summary": "介绍 Z 变换及脉冲传递函数模型。",
                    "tags": ["Z变换", "脉冲传递函数"],
                },
            ],
        },
        {
            "chapter": "第八章",
            "name": "线性系统的状态空间分析与综合",
            "level": 1,
            "enabled": True,
            "is_focus": False,
            "page_range": [393, 454],
            "retrieval_keywords": ["状态空间", "状态变量"],
            "summary": "介绍状态空间表达、可控性、可观性和状态反馈等内容。",
            "tags": ["状态空间", "可控性", "可观性", "状态反馈"],
            "subtopics": [
                {
                    "name": "状态空间表达式",
                    "summary": "介绍系统状态空间模型的建立。",
                    "tags": ["状态空间", "状态方程"],
                },
                {
                    "name": "可控性与可观性",
                    "summary": "介绍系统可控性、可观性的定义与判别。",
                    "tags": ["可控性", "可观性"],
                },
            ],
        },
        {
            "chapter": "第九章",
            "name": "非线性控制系统分析",
            "level": 1,
            "enabled": True,
            "is_focus": False,
            "page_range": [455, 560],
            "retrieval_keywords": ["非线性系统"],
            "summary": "介绍非线性系统的特点及常见分析方法。",
            "tags": ["非线性系统", "相平面", "描述函数"],
            "subtopics": [],
        },
        {
            "chapter": "第十章",
            "name": "动态系统的最优控制方法",
            "level": 1,
            "enabled": True,
            "is_focus": False,
            "page_range": [561, 632],
            "retrieval_keywords": ["现代控制", "最优控制"],
            "summary": "介绍最优控制的基本思想和典型方法。",
            "tags": ["最优控制", "性能指标", "最优化"],
            "subtopics": [],
        },
    ],
}