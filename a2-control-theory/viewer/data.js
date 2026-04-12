window.A2_GRAPH_VIEWER_DATA = {
  "meta": {
    "dataset": "A2 Control Theory Knowledge Graph",
    "generated_at": "2026-04-10T11:07:19.786466+00:00",
    "note_count": 85,
    "internal_edge_count": 240,
    "out_of_scope_reference_count": 83,
    "missing_reference_count": 34,
    "subgraphs": {
      "0. 基础知识": 10,
      "1. 经典控制理论": 34,
      "2. 现代控制理论": 23,
      "3. 计算机控制系统": 15,
      "4. 先进控制理论": 2,
      "未分类": 1
    },
    "root_notes": [
      "经典控制理论",
      "现代控制理论",
      "计算机控制系统",
      "自动控制原理"
    ]
  },
  "graph": {
    "nodes": [
      {
        "id": "线性时不变系统",
        "name": "线性时不变系统",
        "category": "0. 基础知识",
        "subcategory": "0. 基础知识",
        "size": 4,
        "summary": "Linear Time Invariant LTI System",
        "pinned": false
      },
      {
        "id": "反馈",
        "name": "反馈",
        "category": "0. 基础知识",
        "subcategory": "0. 基础知识",
        "size": 6,
        "summary": "Feedback 反馈",
        "pinned": false
      },
      {
        "id": "时间常数",
        "name": "时间常数",
        "category": "0. 基础知识",
        "subcategory": "0. 基础知识",
        "size": 4,
        "summary": "(terminology::Time Constant ) $\\tau$\n由系统本身决定，反映系统的惯性",
        "pinned": false
      },
      {
        "id": "模态",
        "name": "模态",
        "category": "0. 基础知识",
        "subcategory": "0. 基础知识",
        "size": 4,
        "summary": "微分方程\\可以用来描述系统状态随时间的变化，而模态是系统自由响应的特征\n系统的自然振动模式或响应模式。在多自由度系统或分布参数系统中，模态是系统在自由振动时的固有振动形态。每个模态都与特定的自然频率和阻尼特性相关联。",
        "pinned": false
      },
      {
        "id": "涌现",
        "name": "涌现",
        "category": "0. 基础知识",
        "subcategory": "0. 基础知识",
        "size": 4,
        "summary": "Emergence\n系统\\理论中的概念，指的是在复杂系统中，整体的行为和属性不是由单个组成部分单独决定的，而是通过这些部分之间的相互作用产生的。",
        "pinned": false
      },
      {
        "id": "系统",
        "name": "系统",
        "category": "0. 基础知识",
        "subcategory": "0. 基础知识",
        "size": 8,
        "summary": "System \n本质上是对象在给定初始条件下，输入到输出的一个变换\n“由一些相互关联、相互作用、相互影响的组织部分构成并具有某些功能的整体”",
        "pinned": false
      },
      {
        "id": "系统科学",
        "name": "系统科学",
        "category": "0. 基础知识",
        "subcategory": "0. 基础知识",
        "size": 5,
        "summary": "Systems Science 系统科学",
        "pinned": true
      },
      {
        "id": "脉冲函数",
        "name": "脉冲函数",
        "category": "0. 基础知识",
        "subcategory": "0. 基础知识",
        "size": 4,
        "summary": "Pulse Function\n脉冲函数是一个实际的、物理可实现的信号，它具有有限的持续时间和幅度。\n脉冲函数可以是矩形脉冲、高斯脉冲、梯形脉冲等多种形状，通常用于模拟电子信号、声波等。\n脉冲函数在时间轴上的定义是非零的，并且其幅度和宽度都是有限的。",
        "pinned": false
      },
      {
        "id": "自动控制系统",
        "name": "自动控制系统",
        "category": "0. 基础知识",
        "subcategory": "0. 基础知识",
        "size": 4,
        "summary": "(terminology:：Automatic Control System)",
        "pinned": false
      },
      {
        "id": "阶跃函数",
        "name": "阶跃函数",
        "category": "0. 基础知识",
        "subcategory": "0. 基础知识",
        "size": 4,
        "summary": "Step function\n阶跃函数为有限段分段常数函数的组合",
        "pinned": false
      },
      {
        "id": "0°根轨迹绘制规则",
        "name": "0°根轨迹绘制规则",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 4,
        "summary": "绘制法则，参考 180°根轨迹绘制法则\\\n### 一、非最小相位系统\n在 s 右半平面具有开环零极点的控制系统为非最小相位系统\\",
        "pinned": false
      },
      {
        "id": "经典环节的传递函数",
        "name": "经典环节的传递函数",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 12,
        "summary": "复杂传递函数\\由经典输入信号\\的传递函数构成，其行为也由由基本环节的行为决定",
        "pinned": false
      },
      {
        "id": "传递函数",
        "name": "传递函数",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 27,
        "summary": "Transform Fuction",
        "pinned": false
      },
      {
        "id": "系统结构框图",
        "name": "系统结构框图",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 6,
        "summary": "System Diagram\n 求传递函数\\方法之一，系统原理图和数学方程的结合。\n### 一、基本单元\n信号线：箭头表示信号的流向。直线旁标记信号的时间函数或象函数\n引出点/测量点：表示信号引出或测量的位置。从同一位置引出的信号在数值和性质上完全相同\n比较点/综合点：表示对两个及以上的信号进行加减运算\n方框/环节：对信号进行的数学变换",
        "pinned": false
      },
      {
        "id": "信号流图",
        "name": "信号流图",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 4,
        "summary": "可由系统结构框图\\得到，求传递函数\\的方法\n[!important] 注意\n根据系统结构图绘制信号流图时：\n要明确系统的输入和输出\n一定要区分引出点、比较点\n（多拉出一个信号，增益为 1 即可）\n虽然前后的信号表面上相同，但实质是不同的信号，应用公式计算时会有影响\n明确前向通路和回路\n不要漏也不要多\n 注意符号",
        "pinned": false
      },
      {
        "id": "经典输入信号",
        "name": "经典输入信号",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 10,
        "summary": "Classical Input Signal 特殊的信号\\",
        "pinned": false
      },
      {
        "id": "180°根轨迹绘制法则",
        "name": "180°根轨迹绘制法则",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 4,
        "summary": "常规根轨迹\n[!note] \n开环传函的其他参数变化都可采用，下面以根轨迹增益 $K^{}$变化为讨论前提",
        "pinned": false
      },
      {
        "id": "Bode 图",
        "name": "Bode 图",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 8,
        "summary": "Bode Plot 对数频率特性图\n一种将系统的频率响应以对数坐标表示的图形工具，用于描述传递函数 $G(s)$ 在 $s=j\\omega$ 时的性质，便于进行频域分析与控制系统设计。\n横坐标：频率的对数分度 $\\lg \\omega$ $rad / s$\n纵坐标： 频率特性\\\n幅频特性：$L(\\omega)=20\\lg |G(j\\omega)|$ 单位： 分贝\\ 显示增益随频率变化的趋势\n相频特性：$\\phi(\\omega)=\\angle G(j\\omega)$ 单位：$度^",
        "pinned": false
      },
      {
        "id": "Nyquist图",
        "name": "Nyquist图",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 6,
        "summary": "极坐标图/幅相曲线图/Nyquist图\n$$\\begin{align}\nG(j\\omega )&=|G(j\\omega )|e^{ j \\angle G(j\\omega ) }=P(\\omega ) +jQ(\\omega )\n\\end{align}$$",
        "pinned": false
      },
      {
        "id": "PID",
        "name": "PID",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 5,
        "summary": "Proportional-Integral-Derivative Controller PID controller \n对误差信号 $e(t)$ 进行比例、积分和微分运算变换后形成的控制规律",
        "pinned": false
      },
      {
        "id": "一阶系统的时域分析",
        "name": "一阶系统的时域分析",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 4,
        "summary": "经典环节的传递函数\\\n传递函数标准形式：(其中特征根 $- \\dfrac{1}{T}$，$T$ 为时间常数\\)\n$$\\begin{align}\n\\Phi(s)= \\dfrac{C(s)}{G(s)}= \\dfrac{1}{Ts+1}\n\\end{align}$$",
        "pinned": false
      },
      {
        "id": "二阶系统的时域分析",
        "name": "二阶系统的时域分析",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 6,
        "summary": "$$\\begin{align} \\\\\n\\text{Open loop:}\\quad G(s)&=\\frac{\\omega _{n}^{2}}{s(s+2\\zeta \\omega _{n})} \\\\\n\\text{Closed loop:}\\quad \\Phi(s)&=\\frac{\\omega _{n}^{2}}{s^{2}+2\\zeta \\omega _{n}s+\\omega_{n}^{2}} =\\frac{1}{T^{2}s^{2}+2\\zeta Ts+1}\n\\end{ali",
        "pinned": false
      },
      {
        "id": "信号保持",
        "name": "信号保持",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 4,
        "summary": "Signal Holding\n保持器：将数字信号转换为连续信号，本质是解决采样点之间的插值\\问题。\n为了实现对被控对象的有效控制，必须把数字信号恢复为连续信号，实践上，常采用接近理想低通滤波器的零阶保持器对信号进行重构",
        "pinned": false
      },
      {
        "id": "信号采样",
        "name": "信号采样",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 4,
        "summary": "Signal sampling",
        "pinned": false
      },
      {
        "id": "广义根轨迹",
        "name": "广义根轨迹",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 4,
        "summary": "除了 $K^{*}$ 变化的常规根轨迹，其他情况的根轨迹属于广义根轨迹\n参数根轨迹：根轨迹增益以外其他参数变化时的根轨迹\n### 绘制的基本方法\n只需要明确根轨迹本质就是 特征方程\n写出闭环特征方程：1+开环传递函数\n等效开环传递函数(闭环极点相同)：就是将要变换的参数分离（例如：参数 p），写成：\n $\\dfrac{p\\cdot f(s)}{g(s)}=-1$ 的形式\n绘制等效系统的根轨迹：参考 180°根轨迹绘制法则\\",
        "pinned": false
      },
      {
        "id": "开环频率特性",
        "name": "开环频率特性",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 4,
        "summary": "基于 Bode 图\\的开环传函分析\n### 低频段\n分析系统的稳态性能\n斜率决定稳态性能\n高度决定开环增益",
        "pinned": false
      },
      {
        "id": "控制系统的数学模型",
        "name": "控制系统的数学模型",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 4,
        "summary": "机理分析 ：基于内部机理和物理原理\n真实性和可解释性：基于系统的内部机理和物理原理\n预测和设计能力：便于设计、优化和控制，达到性能指标 \n传递能力：从某系统中获取的知识和理解转移到其他类似系统",
        "pinned": false
      },
      {
        "id": "时间响应的性能指标",
        "name": "时间响应的性能指标",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 4,
        "summary": "Performance indicators of time response",
        "pinned": false
      },
      {
        "id": "校正环节的设计",
        "name": "校正环节的设计",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 4,
        "summary": "已知单位反馈系统的传递函数\\ $G_{0}(s)$，设计串联校正环节，串联一个零极点校正装置：",
        "pinned": false
      },
      {
        "id": "根轨迹法基础",
        "name": "根轨迹法基础",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 6,
        "summary": "根轨迹/根迹：开环传函某一参数从零变到无穷时，闭环系统特征方程的根在s 平面上变化的轨迹\n由开环传递函数绘出闭环根的轨迹 \n根据闭环极点的分布分析系统性",
        "pinned": false
      },
      {
        "id": "欠阻尼二阶系统动态分析",
        "name": "欠阻尼二阶系统动态分析",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 4,
        "summary": "在二阶系统的时域分析\\基础上分析",
        "pinned": false
      },
      {
        "id": "滞后校正",
        "name": "滞后校正",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 4,
        "summary": "适用于：未校正系统的动态性能已经满足，但是稳定性能不满足要求",
        "pinned": false
      },
      {
        "id": "稳定裕度",
        "name": "稳定裕度",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 10,
        "summary": "Stability Margins\n是控制系统设计和分析中的重要概念，它提供了线性系统稳定性分析\\的定量度量",
        "pinned": false
      },
      {
        "id": "线性系统的校正",
        "name": "线性系统的校正",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 5,
        "summary": "校正与控制器之间的关系：\n校正：由控制器执行的操作或过程，本身不是控制器 \n控制器：根据输入和系统状态生成控制输出的设备或算法，根据反馈信息调整系统操作，实现控制目标",
        "pinned": false
      },
      {
        "id": "线性系统稳定性分析",
        "name": "线性系统稳定性分析",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 10,
        "summary": "Stability Analysis of Linear System\n系统分析的前提是稳定\n### 一、基础概念\n稳定性：系统在扰动消失后，由初始偏差状态恢复到原平衡状态的性能\n李雅普诺夫稳定性理论：线性系统在初始扰动的影响下，其动态过程随时间推移逐渐衰减并趋于零，则称系统渐近稳定\n经典控制理论的稳定性属于李雅普诺夫稳定性理论\\中的渐进稳定",
        "pinned": false
      },
      {
        "id": "线性系统稳态误差计算",
        "name": "线性系统稳态误差计算",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 9,
        "summary": "Steady-state Error Calculation for Linear Systems",
        "pinned": false
      },
      {
        "id": "经典控制理论",
        "name": "经典控制理论",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 32,
        "summary": "Classical Control Theory\n以传递函数为基础，研究 SISO 线性定常系统",
        "pinned": true
      },
      {
        "id": "超前校正",
        "name": "超前校正",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 4,
        "summary": "系统稳定性和动态性能",
        "pinned": false
      },
      {
        "id": "零极点",
        "name": "零极点",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 11,
        "summary": "传递函数\\ 根轨迹法基础\\\n零点 Zeros：传递函数分子多项式为零的点\n极点 Poles：传递函数分母多项式为零的点",
        "pinned": false
      },
      {
        "id": "非最小相位系统",
        "name": "非最小相位系统",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 7,
        "summary": "Nonminimum-phase system",
        "pinned": false
      },
      {
        "id": "频域稳定判据",
        "name": "频域稳定判据",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 5,
        "summary": "利用开环频率特性判断闭环系统的线性系统稳定性分析\\",
        "pinned": false
      },
      {
        "id": "频带宽度",
        "name": "频带宽度",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 6,
        "summary": "Bandwidth\n先有稳定，再谈性能指标。稳定裕度\\、谐振峰值\n对闭环系统而言",
        "pinned": false
      },
      {
        "id": "频率特性",
        "name": "频率特性",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 5,
        "summary": "Frequency Response\n由传递函数\\决定",
        "pinned": false
      },
      {
        "id": "高阶系统的时域分析",
        "name": "高阶系统的时域分析",
        "category": "1. 经典控制理论",
        "subcategory": "1. 经典控制理论",
        "size": 4,
        "summary": "$$\\begin{align}\ny(t)=1+\\sum\\limits_{i=1}^{q}A_{i}e^{ s_{i}t }+\\sum\\limits_{k=1}^{r}D_{k}e^{ -\\zeta_{k}\\omega _{nk}t }\\sin(\\omega _{dk}t+\\theta_{k})\n\\end{align}$$\n稳态分量+暂态分量 = 稳态分量+指数衰减+振荡衰减",
        "pinned": false
      },
      {
        "id": "传递函数矩阵",
        "name": "传递函数矩阵",
        "category": "2. 现代控制理论",
        "subcategory": "2. 现代控制理论",
        "size": 7,
        "summary": "Transfer Function Matrix\n传递函数的矩阵形式，用来研究多输入-多输出系统，实际上反映了系统中线性系统的结构分解#三、按能控能观性分解\\的动力学行为\n[!important] Description\n前置知识：传递函数\\、矩阵\\、状态空间\\",
        "pinned": false
      },
      {
        "id": "传递函数阵的实现问题",
        "name": "传递函数阵的实现问题",
        "category": "2. 现代控制理论",
        "subcategory": "2. 现代控制理论",
        "size": 5,
        "summary": "(terminology:: Transfer Function Matrix Realization)\n多输入多输出系统的能控能观标准型。\n[!important] Description \n状态空间表达式的能控标准型和能观标准型\\的扩展延伸\n传递函数矩阵\\只能反映系统中能控且能观的子系统的动力学行为",
        "pinned": false
      },
      {
        "id": "李雅普诺夫方法在线性系统中的应用",
        "name": "李雅普诺夫方法在线性系统中的应用",
        "category": "2. 现代控制理论",
        "subcategory": "2. 现代控制理论",
        "size": 4,
        "summary": "充要条件：对线性定常系统而言\n$Q>0$， $A^{T}P+PA=-Q$ 解出并判断 $P>0$ 则系统大范围渐进稳定\n$Q\\geq 0$， $A^{T}P+PA=-Q$ 解出并判断 $P>0$ 则系统稳定",
        "pinned": false
      },
      {
        "id": "李雅普诺夫方法在非线性系统中的应用",
        "name": "李雅普诺夫方法在非线性系统中的应用",
        "category": "2. 现代控制理论",
        "subcategory": "2. 现代控制理论",
        "size": 4,
        "summary": "非线性系统的稳定性可能只有局部性质\n且李雅普诺夫第二法\\只能给出非线性系统渐近稳定的充分条件，而非必要条件，求解较为简单，如果无法找到李雅普诺夫函数才使用下述方法。\n### 一、雅可比矩阵法/克拉索夫斯基法\n理论基础：雅可比矩阵\\，寻找线性系统李雅普诺夫函数的推广方法。\n$$\\begin{align}\n \\dot{\\mathbf{x}}=\\mathbf{f}(\\mathbf{x})\\quad \\mathbf{J}(\\mathbf{x})= \\dfrac{\\partial \\m",
        "pinned": false
      },
      {
        "id": "李雅普诺夫稳定性理论",
        "name": "李雅普诺夫稳定性理论",
        "category": "2. 现代控制理论",
        "subcategory": "2. 现代控制理论",
        "size": 4,
        "summary": "Lyapunov Stability Theory\n稳定是系统分析的前提，是系统正常工作的必要条件。\n李雅普诺夫稳定性分析适用于几乎所有系统的稳定性分析，是稳定性问题解决的最基本方法。在此基础上衍生了多种稳定性判别方法。\n[!important] Description \n前置知识：范数\\ 线性系统稳定性分析\\",
        "pinned": false
      },
      {
        "id": "李雅普诺夫第一法",
        "name": "李雅普诺夫第一法",
        "category": "2. 现代控制理论",
        "subcategory": "2. 现代控制理论",
        "size": 4,
        "summary": "Lyapunov's First Method\n间接法，利用系统矩阵的特征值或系统状态方程的解来判断系统稳定性。主要针对线性定常系统和非线性不是很严重的系统",
        "pinned": false
      },
      {
        "id": "李雅普诺夫第二法",
        "name": "李雅普诺夫第二法",
        "category": "2. 现代控制理论",
        "subcategory": "2. 现代控制理论",
        "size": 6,
        "summary": "Lyapunov's Second Method\n直接法：构造李雅普诺夫函数从能量的观点进行稳定性分析\n[!important] Description \n前置知识：对称矩阵\\ 二次型\\ 能\\ 偏导数\\ 状态空间\\ 李雅普诺夫稳定性理论\\ \n相关：神经网络的稳定性\\",
        "pinned": false
      },
      {
        "id": "极点配置与系统镇定",
        "name": "极点配置与系统镇定",
        "category": "2. 现代控制理论",
        "subcategory": "2. 现代控制理论",
        "size": 5,
        "summary": "Pole Configuration System Stabilization\n控制系统的性能主要取决于系统极点在根平面上的分布，给定一组极点或根据时域指标转换为一组等价的期望极点，作为综合系统性能指标的一种形式。\n[!important] Description \n前置知识：根轨迹法基础\\ 线性反馈系统的基本结构\\",
        "pinned": false
      },
      {
        "id": "状态向量的线性变换",
        "name": "状态向量的线性变换",
        "category": "2. 现代控制理论",
        "subcategory": "2. 现代控制理论",
        "size": 6,
        "summary": "Linear Transformation of State Vectors\n状态空间表达式进行线性变换变为标准型的基础。\n[!important] Description \n前置知识：特征值和特征向量\\ 矩阵对角化\\ 状态空间\\ 线性变换\\\n特殊矩阵：Jordan矩阵\\ 友矩阵\\ 范德蒙德矩阵\\",
        "pinned": false
      },
      {
        "id": "状态空间",
        "name": "状态空间",
        "category": "2. 现代控制理论",
        "subcategory": "2. 现代控制理论",
        "size": 10,
        "summary": "State Space \n系统的内部描述方法",
        "pinned": false
      },
      {
        "id": "状态空间表达式的建立",
        "name": "状态空间表达式的建立",
        "category": "2. 现代控制理论",
        "subcategory": "2. 现代控制理论",
        "size": 8,
        "summary": "State Space Representation\n得到状态空间表达式\n[!important] Description \n前置知识： 系统\\ 状态空间\\ 传递函数\\\n本节从系统的两个层次来建立状态空间表达式",
        "pinned": false
      },
      {
        "id": "状态空间表达式的能控标准型和能观标准型",
        "name": "状态空间表达式的能控标准型和能观标准型",
        "category": "2. 现代控制理论",
        "subcategory": "2. 现代控制理论",
        "size": 9,
        "summary": "寻找线性变换，得到单输入单输出系统的能控能控标准型。\n[!important] Description \n判断能控能观性：线性定常系统的能控性\\ 线性定常系统的能观性\\\n化为标准型：状态向量的线性变换\\\n写为传递函数：状态空间表达式的建立#二、从外部描述建立\\",
        "pinned": false
      },
      {
        "id": "状态观测器",
        "name": "状态观测器",
        "category": "2. 现代控制理论",
        "subcategory": "2. 现代控制理论",
        "size": 5,
        "summary": "Observer\n用可测的输入输出“估算”系统内部状态，实现无法直接测量的线性反馈系统的基本结构#1. 状态反馈\\。",
        "pinned": false
      },
      {
        "id": "现代控制理论",
        "name": "现代控制理论",
        "category": "2. 现代控制理论",
        "subcategory": "2. 现代控制理论",
        "size": 25,
        "summary": "Modern Control Theory\n以状态空间为基础，研究 MIMO 系统。以状态反馈和输出反馈为核心来分析和设计系统。\n主要是：线性系统的状态空间分析与综合",
        "pinned": true
      },
      {
        "id": "系统解耦",
        "name": "系统解耦",
        "category": "2. 现代控制理论",
        "subcategory": "2. 现代控制理论",
        "size": 4,
        "summary": "System Decoupling",
        "pinned": false
      },
      {
        "id": "线性反馈系统的基本结构",
        "name": "线性反馈系统的基本结构",
        "category": "2. 现代控制理论",
        "subcategory": "2. 现代控制理论",
        "size": 6,
        "summary": "Basic Structure of Linear Feedback Systems\n[!important] Description \n前置知识：反馈\\ 传递函数\\ 状态空间\\",
        "pinned": false
      },
      {
        "id": "线性定常状态方程的解",
        "name": "线性定常状态方程的解",
        "category": "2. 现代控制理论",
        "subcategory": "2. 现代控制理论",
        "size": 4,
        "summary": "Solution of linear time-invariant state equations",
        "pinned": false
      },
      {
        "id": "线性定常系统的能控性",
        "name": "线性定常系统的能控性",
        "category": "2. 现代控制理论",
        "subcategory": "2. 现代控制理论",
        "size": 6,
        "summary": "Controllability\n### 基本定义\n状态变量可以由输入来影响和控制，而由任意的初态达到原点。",
        "pinned": false
      },
      {
        "id": "线性定常系统的能观性",
        "name": "线性定常系统的能观性",
        "category": "2. 现代控制理论",
        "subcategory": "2. 现代控制理论",
        "size": 4,
        "summary": "Observability\n### 基本定义\n考察系统所有状态变量的任意形式的运动是否均可以由输出完全反映。只需要考虑状态变量的影响，无需考虑输入，所以只需要看状态空间方程的齐次部分和输出方程\n系统完全可观测：系统的输出能唯一确定状态向量的初值，则称系统是完全可观测的\n系统不可观测：系统的输出不能唯一确定所有状态向量的初值",
        "pinned": false
      },
      {
        "id": "线性时变状态方程的解",
        "name": "线性时变状态方程的解",
        "category": "2. 现代控制理论",
        "subcategory": "2. 现代控制理论",
        "size": 4,
        "summary": "只有当 $A_{(t)}$ 和 $\\int _{t_{0}}^{t} A(\\tau)\\, d\\tau$ 满足乘法可交换条件，时变系统的自由解才可以写为封闭的幂级数形式：\n$$\\begin{align}\n\\varPhi(t,t_{0})= \\exp \\left[\\int _{t_{0}}^{t} A(\\tau) \\mathrm{d}\\tau \\right] \\boldsymbol{x}_{(t_0)}\n\\end{align}$$",
        "pinned": false
      },
      {
        "id": "线性时变系统的能控能观性",
        "name": "线性时变系统的能控能观性",
        "category": "2. 现代控制理论",
        "subcategory": "2. 现代控制理论",
        "size": 4,
        "summary": "对于线性时变系统\n$$\\begin{align}\n\\dot{\\mathbf{x}}(t)&=\\mathbf{A}(t) \\mathbf{x}(t)+ \\mathbf{B}(t) \\mathbf{u}(t) \\\\\n\\mathbf{y}(t)&=\\mathbf{C}(t)\\mathbf{x}(t)+\\mathbf{D}(t) \\mathbf{u}(t)\n\\end{align}$$\n$$\\begin{gathered}\n\\mathbf{x}(t)=\\varPhi(t,t_{0})\\",
        "pinned": false
      },
      {
        "id": "线性系统的结构分解",
        "name": "线性系统的结构分解",
        "category": "2. 现代控制理论",
        "subcategory": "2. 现代控制理论",
        "size": 7,
        "summary": "将状态空间按照能控性和能观性进行结构分解，在理论上揭示了状态空间\\的本质特征，也为传递函数阵的实现问题\\提供了理论依据。",
        "pinned": false
      },
      {
        "id": "连续时间系统状态方程的离散化",
        "name": "连续时间系统状态方程的离散化",
        "category": "2. 现代控制理论",
        "subcategory": "2. 现代控制理论",
        "size": 4,
        "summary": "Discretization of continuous-time system state equations\n### 一、线性定常系统的离散化\n线性时变状态方程的解\\为：\n$$\\begin{align}\n \\boldsymbol{x}_{(t)}=e^{ A(t-t_{0}) }\\boldsymbol{x}_{(t_{0} )}+e^{ At } \\int _{t_{0}}^{t} e^{ -A\\tau }B\\boldsymbol{u}_{(t)} \\, d\\tau\n\\e",
        "pinned": false
      },
      {
        "id": "计算机控制系统概述",
        "name": "计算机控制系统概述",
        "category": "3. 计算机控制系统",
        "subcategory": "3. 计算机控制系统",
        "size": 4,
        "summary": "#### 计算机控制系统的特点\n易于控制算法设计与更新\n能实现集中监视和远程控制\n能实现最优控制\n高可靠性和可维护性",
        "pinned": false
      },
      {
        "id": "线性定常系统的差分方程求解",
        "name": "线性定常系统的差分方程求解",
        "category": "3. 计算机控制系统",
        "subcategory": "3. 计算机控制系统",
        "size": 4,
        "summary": "差分方程\\\n非齐次线性定常前向差分方程、非齐次线性定常后向差分方程",
        "pinned": false
      },
      {
        "id": "脉冲传递函数",
        "name": "脉冲传递函数",
        "category": "3. 计算机控制系统",
        "subcategory": "3. 计算机控制系统",
        "size": 5,
        "summary": "Z-Transfer Function z 传递函数\n线性定常离散系统的脉冲传递函数\\定义为：系统输出采样信号的 z 变换与输入采样信号的 z 变换\\ 之比。用于描述系统的差分方程\\：",
        "pinned": false
      },
      {
        "id": "离散系统的稳定性分析",
        "name": "离散系统的稳定性分析",
        "category": "3. 计算机控制系统",
        "subcategory": "3. 计算机控制系统",
        "size": 4,
        "summary": "Stability Analysis of Discrete Systems",
        "pinned": false
      },
      {
        "id": "离散系统稳态分析",
        "name": "离散系统稳态分析",
        "category": "3. 计算机控制系统",
        "subcategory": "3. 计算机控制系统",
        "size": 4,
        "summary": "Steady-state Analysis of Discrete Systems",
        "pinned": false
      },
      {
        "id": "模拟控制器离散化",
        "name": "模拟控制器离散化",
        "category": "3. 计算机控制系统",
        "subcategory": "3. 计算机控制系统",
        "size": 6,
        "summary": "Discretization of Analog Controllers",
        "pinned": false
      },
      {
        "id": "数字 PID 控制器",
        "name": "数字 PID 控制器",
        "category": "3. 计算机控制系统",
        "subcategory": "3. 计算机控制系统",
        "size": 7,
        "summary": "Discrete-time PID Controller 离散 PID 控制器",
        "pinned": false
      },
      {
        "id": "数字PID 参数整定",
        "name": "数字PID 参数整定",
        "category": "3. 计算机控制系统",
        "subcategory": "3. 计算机控制系统",
        "size": 4,
        "summary": "数字 PID 控制器\\的参数整定\n采样周期的选择：满足条件下尽可能大，而不是越小越好 信号采样\\\n### 一、扩充临界比例度法\n选择足够短的采样周期 \n将 PID 设定为纯比例控制，逐步减小比例度，产生等幅振荡，记下此时的比例度和振荡周期\n选定比例度\n查表得到采样周期、比例度、积分时间、微分时间的值",
        "pinned": false
      },
      {
        "id": "数字控制器",
        "name": "数字控制器",
        "category": "3. 计算机控制系统",
        "subcategory": "3. 计算机控制系统",
        "size": 11,
        "summary": "Digital Controller\n### 一、基本思想 \n将系统中被控对象及零阶保持器进行离散化，得到广义对象 $G(z)=\\mathscr{Z}[G_{h}(s)G_{0}(s)]$\n根据系统的性能指标及约束条件，确定闭环期望传递函数 $\\varPhi(z)$ 或误差传递函数 $\\varPhi_{e}(z)$\n进一步得到数字控制器 $D(z)$\n将 $D(z)$ 写为差分方程的形式，得到控制算法",
        "pinned": false
      },
      {
        "id": "参数优化的低阶算法",
        "name": "参数优化的低阶算法",
        "category": "3. 计算机控制系统",
        "subcategory": "3. 计算机控制系统",
        "size": 4,
        "summary": "一阶控制器：\n$$\\begin{align}\nD(z)=\\dfrac{a_{0}+a_{1}z^{-1}}{1-z^{-1}}\n\\end{align}$$\n$$\\begin{align}\nu(k)=u(k-1)+a_{0}e(k)+a_{1}e(k-1)\n\\end{align}$$",
        "pinned": false
      },
      {
        "id": "最小拍控制器",
        "name": "最小拍控制器",
        "category": "3. 计算机控制系统",
        "subcategory": "3. 计算机控制系统",
        "size": 6,
        "summary": "Deadbeat Response 最少调节时间/暂态过程时间最少系统\n在经典输入信号\\作用下，系统可经过最小拍使输出响应的稳态误差为零。（某种特定的输入在最少个采样周期内达到无静差的稳态） 实现时间最优控制",
        "pinned": false
      },
      {
        "id": "最小拍控制器的改进",
        "name": "最小拍控制器的改进",
        "category": "3. 计算机控制系统",
        "subcategory": "3. 计算机控制系统",
        "size": 4,
        "summary": "首先根据最小拍控制器\\的设计，考虑所有情况得到误差传递函数或闭环传递函数，再进行改进\n### 一、无波纹最小拍控制器\n在 5 种情况后，再消除被控对象的单位圆内零点。",
        "pinned": false
      },
      {
        "id": "史密斯预估补偿控制",
        "name": "史密斯预估补偿控制",
        "category": "3. 计算机控制系统",
        "subcategory": "3. 计算机控制系统",
        "size": 4,
        "summary": "被控对象含纯滞后环节的闭环传递函数：\n$$\\begin{align}\nG(s)= G_{0}(s) e^{ -\\tau s }\\quad \\quad W(s)= \\dfrac{D(s)G_{0}(s)e^{ -\\tau s }}{1+D(s)G_{0}(s)e^{ -\\tau s }}\n\\end{align}$$\n注意这里是将被控对象不包含纯滞后的部分作为 $G_{0}(s)$",
        "pinned": false
      },
      {
        "id": "大林算法控制器",
        "name": "大林算法控制器",
        "category": "3. 计算机控制系统",
        "subcategory": "3. 计算机控制系统",
        "size": 4,
        "summary": "Dahlin\n针对于含有纯滞后环节的连续被控对象，将超调量作为主要的设计指标",
        "pinned": false
      },
      {
        "id": "计算机控制系统",
        "name": "计算机控制系统",
        "category": "3. 计算机控制系统",
        "subcategory": "3. 计算机控制系统",
        "size": 19,
        "summary": "Computer Control System\n计算机\\参与控制的闭环控制系统，也称数字控制系统或离散控制系统。",
        "pinned": true
      },
      {
        "id": "MPC",
        "name": "MPC",
        "category": "4. 先进控制理论",
        "subcategory": "4. 先进控制理论",
        "size": 4,
        "summary": "Model Predictive Control 模型预测控制\n它通过预测系统未来的行为来计算当前的最优控制\\动作\n模型预测控制（MPC）是一种先进的控制策略，它在每个时间步，利用系统模型预测未来的行为，并求解一个优化问题来确定当前的最优控制输入。MPC 的核心思想是滚动优化 (Receding Horizon Optimization) 和反馈校正 (Feedback Correction)，使其能够处理复杂的约束和多变量系统，在机器人\\、自动驾驶和工业过程控制等领域得到广",
        "pinned": false
      },
      {
        "id": "卡尔曼滤波",
        "name": "卡尔曼滤波",
        "category": "4. 先进控制理论",
        "subcategory": "4. 先进控制理论",
        "size": 4,
        "summary": "(terminology::Kalman Filter ) \nOptimal-Recursive-Data Processing-Algorithm 优化-递归-数据处理-算法",
        "pinned": false
      },
      {
        "id": "自动控制原理",
        "name": "自动控制原理",
        "category": "未分类",
        "subcategory": "未分类",
        "size": 9,
        "summary": "Principles of Automatic Control",
        "pinned": true
      }
    ],
    "links": [
      {
        "source": "0°根轨迹绘制规则",
        "target": "180°根轨迹绘制法则",
        "weight": 2,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          },
          {
            "label": "绘制规则",
            "count": 1
          }
        ]
      },
      {
        "source": "0°根轨迹绘制规则",
        "target": "非最小相位系统",
        "weight": 1,
        "relation_label": "非最小相位系统",
        "relation_candidates": [
          {
            "label": "非最小相位系统",
            "count": 1
          }
        ]
      },
      {
        "source": "180°根轨迹绘制法则",
        "target": "零极点",
        "weight": 1,
        "relation_label": "起始角和终止角",
        "relation_candidates": [
          {
            "label": "起始角和终止角",
            "count": 1
          }
        ]
      },
      {
        "source": "Bode 图",
        "target": "Nyquist图",
        "weight": 1,
        "relation_label": "低频段初始角度补画",
        "relation_candidates": [
          {
            "label": "低频段初始角度补画",
            "count": 1
          }
        ]
      },
      {
        "source": "Bode 图",
        "target": "经典环节的传递函数",
        "weight": 1,
        "relation_label": "画渐近特性曲线",
        "relation_candidates": [
          {
            "label": "画渐近特性曲线",
            "count": 1
          }
        ]
      },
      {
        "source": "Bode 图",
        "target": "频率特性",
        "weight": 1,
        "relation_label": "纵坐标",
        "relation_candidates": [
          {
            "label": "纵坐标",
            "count": 1
          }
        ]
      },
      {
        "source": "Nyquist图",
        "target": "传递函数",
        "weight": 1,
        "relation_label": "基本的画法",
        "relation_candidates": [
          {
            "label": "基本的画法",
            "count": 1
          }
        ]
      },
      {
        "source": "PID",
        "target": "数字 PID 控制器",
        "weight": 1,
        "relation_label": "PID 比例积分微分",
        "relation_candidates": [
          {
            "label": "PID 比例积分微分",
            "count": 1
          }
        ]
      },
      {
        "source": "PID",
        "target": "滞后校正",
        "weight": 1,
        "relation_label": "PI 比例积分",
        "relation_candidates": [
          {
            "label": "PI 比例积分",
            "count": 1
          }
        ]
      },
      {
        "source": "PID",
        "target": "线性系统稳态误差计算",
        "weight": 1,
        "relation_label": "比例 P",
        "relation_candidates": [
          {
            "label": "比例 P",
            "count": 1
          }
        ]
      },
      {
        "source": "PID",
        "target": "超前校正",
        "weight": 1,
        "relation_label": "PD 比例微分",
        "relation_candidates": [
          {
            "label": "PD 比例微分",
            "count": 1
          }
        ]
      },
      {
        "source": "一阶系统的时域分析",
        "target": "时间响应的性能指标",
        "weight": 1,
        "relation_label": "动态性能指标",
        "relation_candidates": [
          {
            "label": "动态性能指标",
            "count": 1
          }
        ]
      },
      {
        "source": "一阶系统的时域分析",
        "target": "时间常数",
        "weight": 1,
        "relation_label": "传递函数标准形式",
        "relation_candidates": [
          {
            "label": "传递函数标准形式",
            "count": 1
          }
        ]
      },
      {
        "source": "一阶系统的时域分析",
        "target": "经典环节的传递函数",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "二阶系统的时域分析",
        "target": "时间常数",
        "weight": 1,
        "relation_label": "过阻尼",
        "relation_candidates": [
          {
            "label": "过阻尼",
            "count": 1
          }
        ]
      },
      {
        "source": "二阶系统的时域分析",
        "target": "欠阻尼二阶系统动态分析",
        "weight": 1,
        "relation_label": "欠阻尼",
        "relation_candidates": [
          {
            "label": "欠阻尼",
            "count": 1
          }
        ]
      },
      {
        "source": "传递函数",
        "target": "信号流图",
        "weight": 1,
        "relation_label": "求传递函数的方法",
        "relation_candidates": [
          {
            "label": "求传递函数的方法",
            "count": 1
          }
        ]
      },
      {
        "source": "传递函数",
        "target": "时间常数",
        "weight": 1,
        "relation_label": "$\\tau\\quad T$ 为",
        "relation_candidates": [
          {
            "label": "$\\tau\\quad T$ 为",
            "count": 1
          }
        ]
      },
      {
        "source": "传递函数",
        "target": "根轨迹法基础",
        "weight": 1,
        "relation_label": "首 1 标准型",
        "relation_candidates": [
          {
            "label": "首 1 标准型",
            "count": 1
          }
        ]
      },
      {
        "source": "传递函数",
        "target": "模态",
        "weight": 1,
        "relation_label": "极点",
        "relation_candidates": [
          {
            "label": "极点",
            "count": 1
          }
        ]
      },
      {
        "source": "传递函数",
        "target": "系统结构框图",
        "weight": 1,
        "relation_label": "求传递函数的方法",
        "relation_candidates": [
          {
            "label": "求传递函数的方法",
            "count": 1
          }
        ]
      },
      {
        "source": "传递函数",
        "target": "线性时不变系统",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "传递函数",
        "target": "经典控制理论",
        "weight": 1,
        "relation_label": "尾 1 标准型",
        "relation_candidates": [
          {
            "label": "尾 1 标准型",
            "count": 1
          }
        ]
      },
      {
        "source": "传递函数",
        "target": "经典环节的传递函数",
        "weight": 1,
        "relation_label": "经典环节的传递函数",
        "relation_candidates": [
          {
            "label": "经典环节的传递函数",
            "count": 1
          }
        ]
      },
      {
        "source": "传递函数",
        "target": "经典输入信号",
        "weight": 2,
        "relation_label": "传递函数的计算",
        "relation_candidates": [
          {
            "label": "传递函数的计算",
            "count": 1
          },
          {
            "label": "时间响应",
            "count": 1
          }
        ]
      },
      {
        "source": "传递函数",
        "target": "零极点",
        "weight": 1,
        "relation_label": "极点与零点",
        "relation_candidates": [
          {
            "label": "极点与零点",
            "count": 1
          }
        ]
      },
      {
        "source": "传递函数矩阵",
        "target": "传递函数",
        "weight": 2,
        "relation_label": "前置知识",
        "relation_candidates": [
          {
            "label": "前置知识",
            "count": 1
          },
          {
            "label": "传递函数矩阵",
            "count": 1
          }
        ]
      },
      {
        "source": "传递函数矩阵",
        "target": "状态空间",
        "weight": 1,
        "relation_label": "前置知识",
        "relation_candidates": [
          {
            "label": "前置知识",
            "count": 1
          }
        ]
      },
      {
        "source": "传递函数矩阵",
        "target": "线性系统的结构分解",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "传递函数阵的实现问题",
        "target": "传递函数矩阵",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "传递函数阵的实现问题",
        "target": "状态空间表达式的能控标准型和能观标准型",
        "weight": 2,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          },
          {
            "label": "最小实现",
            "count": 1
          }
        ]
      },
      {
        "source": "传递函数阵的实现问题",
        "target": "线性系统的结构分解",
        "weight": 1,
        "relation_label": "最小实现",
        "relation_candidates": [
          {
            "label": "最小实现",
            "count": 1
          }
        ]
      },
      {
        "source": "信号保持",
        "target": "数字控制器",
        "weight": 1,
        "relation_label": "零阶保持器 ZOH",
        "relation_candidates": [
          {
            "label": "零阶保持器 ZOH",
            "count": 1
          }
        ]
      },
      {
        "source": "信号流图",
        "target": "传递函数",
        "weight": 2,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          },
          {
            "label": "梅森增益",
            "count": 1
          }
        ]
      },
      {
        "source": "信号流图",
        "target": "系统结构框图",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "信号采样",
        "target": "脉冲函数",
        "weight": 1,
        "relation_label": "采样信号与连续信号的关系",
        "relation_candidates": [
          {
            "label": "采样信号与连续信号的关系",
            "count": 1
          }
        ]
      },
      {
        "source": "信号采样",
        "target": "频带宽度",
        "weight": 1,
        "relation_label": "香农采样定理",
        "relation_candidates": [
          {
            "label": "香农采样定理",
            "count": 1
          }
        ]
      },
      {
        "source": "卡尔曼滤波",
        "target": "状态空间",
        "weight": 2,
        "relation_label": "预测",
        "relation_candidates": [
          {
            "label": "预测",
            "count": 1
          },
          {
            "label": "理论",
            "count": 1
          }
        ]
      },
      {
        "source": "卡尔曼滤波",
        "target": "状态观测器",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "参数优化的低阶算法",
        "target": "数字 PID 控制器",
        "weight": 1,
        "relation_label": "参数优化的低阶算法",
        "relation_candidates": [
          {
            "label": "参数优化的低阶算法",
            "count": 1
          }
        ]
      },
      {
        "source": "参数优化的低阶算法",
        "target": "数字控制器",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "反馈",
        "target": "系统科学",
        "weight": 3,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 2
          },
          {
            "label": "负反馈控制的基本规律",
            "count": 1
          }
        ]
      },
      {
        "source": "反馈",
        "target": "自动控制系统",
        "weight": 2,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          },
          {
            "label": "负反馈控制的基本规律",
            "count": 1
          }
        ]
      },
      {
        "source": "史密斯预估补偿控制",
        "target": "模拟控制器离散化",
        "weight": 1,
        "relation_label": "控制算法",
        "relation_candidates": [
          {
            "label": "控制算法",
            "count": 1
          }
        ]
      },
      {
        "source": "大林算法控制器",
        "target": "数字控制器",
        "weight": 2,
        "relation_label": "设计目标",
        "relation_candidates": [
          {
            "label": "设计目标",
            "count": 1
          },
          {
            "label": "基本形式",
            "count": 1
          }
        ]
      },
      {
        "source": "大林算法控制器",
        "target": "模拟控制器离散化",
        "weight": 1,
        "relation_label": "基本形式",
        "relation_candidates": [
          {
            "label": "基本形式",
            "count": 1
          }
        ]
      },
      {
        "source": "广义根轨迹",
        "target": "180°根轨迹绘制法则",
        "weight": 2,
        "relation_label": "绘制等效系统的根轨迹",
        "relation_candidates": [
          {
            "label": "绘制等效系统的根轨迹",
            "count": 1
          },
          {
            "label": "绘制的基本方法",
            "count": 1
          }
        ]
      },
      {
        "source": "开环频率特性",
        "target": "Bode 图",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "开环频率特性",
        "target": "线性系统稳态误差计算",
        "weight": 1,
        "relation_label": "低频段",
        "relation_candidates": [
          {
            "label": "低频段",
            "count": 1
          }
        ]
      },
      {
        "source": "开环频率特性",
        "target": "经典环节的传递函数",
        "weight": 1,
        "relation_label": "高频段",
        "relation_candidates": [
          {
            "label": "高频段",
            "count": 1
          }
        ]
      },
      {
        "source": "数字 PID 控制器",
        "target": "数字控制器",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "数字 PID 控制器",
        "target": "模拟控制器离散化",
        "weight": 1,
        "relation_label": "般 PID 算法的离散化",
        "relation_candidates": [
          {
            "label": "般 PID 算法的离散化",
            "count": 1
          }
        ]
      },
      {
        "source": "数字PID 参数整定",
        "target": "信号采样",
        "weight": 1,
        "relation_label": "采样周期的选择",
        "relation_candidates": [
          {
            "label": "采样周期的选择",
            "count": 1
          }
        ]
      },
      {
        "source": "数字PID 参数整定",
        "target": "数字 PID 控制器",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "数字控制器",
        "target": "信号保持",
        "weight": 1,
        "relation_label": "广义对象传递函数",
        "relation_candidates": [
          {
            "label": "广义对象传递函数",
            "count": 1
          }
        ]
      },
      {
        "source": "数字控制器",
        "target": "参数优化的低阶算法",
        "weight": 1,
        "relation_label": "常用数字控制器",
        "relation_candidates": [
          {
            "label": "常用数字控制器",
            "count": 1
          }
        ]
      },
      {
        "source": "数字控制器",
        "target": "大林算法控制器",
        "weight": 1,
        "relation_label": "常用数字控制器",
        "relation_candidates": [
          {
            "label": "常用数字控制器",
            "count": 1
          }
        ]
      },
      {
        "source": "数字控制器",
        "target": "数字 PID 控制器",
        "weight": 1,
        "relation_label": "常用数字控制器",
        "relation_candidates": [
          {
            "label": "常用数字控制器",
            "count": 1
          }
        ]
      },
      {
        "source": "数字控制器",
        "target": "最小拍控制器",
        "weight": 1,
        "relation_label": "常用数字控制器",
        "relation_candidates": [
          {
            "label": "常用数字控制器",
            "count": 1
          }
        ]
      },
      {
        "source": "时间响应的性能指标",
        "target": "线性系统稳态误差计算",
        "weight": 1,
        "relation_label": "稳态误差",
        "relation_candidates": [
          {
            "label": "稳态误差",
            "count": 1
          }
        ]
      },
      {
        "source": "最小拍控制器",
        "target": "数字控制器",
        "weight": 1,
        "relation_label": "最小拍控制控制器的设计",
        "relation_candidates": [
          {
            "label": "最小拍控制控制器的设计",
            "count": 1
          }
        ]
      },
      {
        "source": "最小拍控制器",
        "target": "最小拍控制器的改进",
        "weight": 1,
        "relation_label": "最小拍控制器的改进",
        "relation_candidates": [
          {
            "label": "最小拍控制器的改进",
            "count": 1
          }
        ]
      },
      {
        "source": "最小拍控制器",
        "target": "经典输入信号",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "最小拍控制器的改进",
        "target": "最小拍控制器",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "李雅普诺夫方法在线性系统中的应用",
        "target": "李雅普诺夫第二法",
        "weight": 1,
        "relation_label": "~~二、线性时变连续系统~~",
        "relation_candidates": [
          {
            "label": "~~二、线性时变连续系统~~",
            "count": 1
          }
        ]
      },
      {
        "source": "李雅普诺夫方法在非线性系统中的应用",
        "target": "李雅普诺夫第二法",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "李雅普诺夫稳定性理论",
        "target": "线性系统稳定性分析",
        "weight": 1,
        "relation_label": "前置知识",
        "relation_candidates": [
          {
            "label": "前置知识",
            "count": 1
          }
        ]
      },
      {
        "source": "李雅普诺夫第一法",
        "target": "李雅普诺夫第二法",
        "weight": 1,
        "relation_label": "非线性系统（线性化）",
        "relation_candidates": [
          {
            "label": "非线性系统（线性化）",
            "count": 1
          }
        ]
      },
      {
        "source": "李雅普诺夫第二法",
        "target": "李雅普诺夫稳定性理论",
        "weight": 1,
        "relation_label": "前置知识",
        "relation_candidates": [
          {
            "label": "前置知识",
            "count": 1
          }
        ]
      },
      {
        "source": "李雅普诺夫第二法",
        "target": "状态空间",
        "weight": 1,
        "relation_label": "前置知识",
        "relation_candidates": [
          {
            "label": "前置知识",
            "count": 1
          }
        ]
      },
      {
        "source": "极点配置与系统镇定",
        "target": "根轨迹法基础",
        "weight": 1,
        "relation_label": "前置知识",
        "relation_candidates": [
          {
            "label": "前置知识",
            "count": 1
          }
        ]
      },
      {
        "source": "极点配置与系统镇定",
        "target": "状态空间表达式的能控标准型和能观标准型",
        "weight": 1,
        "relation_label": "采用状态反馈",
        "relation_candidates": [
          {
            "label": "采用状态反馈",
            "count": 1
          }
        ]
      },
      {
        "source": "极点配置与系统镇定",
        "target": "线性反馈系统的基本结构",
        "weight": 1,
        "relation_label": "前置知识",
        "relation_candidates": [
          {
            "label": "前置知识",
            "count": 1
          }
        ]
      },
      {
        "source": "校正环节的设计",
        "target": "传递函数",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "校正环节的设计",
        "target": "根轨迹法基础",
        "weight": 3,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 3
          }
        ]
      },
      {
        "source": "校正环节的设计",
        "target": "零极点",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "根轨迹法基础",
        "target": "传递函数",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "模拟控制器离散化",
        "target": "脉冲传递函数",
        "weight": 1,
        "relation_label": "基本思想",
        "relation_candidates": [
          {
            "label": "基本思想",
            "count": 1
          }
        ]
      },
      {
        "source": "欠阻尼二阶系统动态分析",
        "target": "二阶系统的时域分析",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "涌现",
        "target": "系统",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "滞后校正",
        "target": "稳定裕度",
        "weight": 2,
        "relation_label": "校正的设计步骤",
        "relation_candidates": [
          {
            "label": "校正的设计步骤",
            "count": 2
          }
        ]
      },
      {
        "source": "状态向量的线性变换",
        "target": "状态空间",
        "weight": 1,
        "relation_label": "前置知识",
        "relation_candidates": [
          {
            "label": "前置知识",
            "count": 1
          }
        ]
      },
      {
        "source": "状态空间",
        "target": "状态空间表达式的建立",
        "weight": 1,
        "relation_label": "状态空间表达式",
        "relation_candidates": [
          {
            "label": "状态空间表达式",
            "count": 1
          }
        ]
      },
      {
        "source": "状态空间表达式的建立",
        "target": "传递函数",
        "weight": 1,
        "relation_label": "前置知识",
        "relation_candidates": [
          {
            "label": "前置知识",
            "count": 1
          }
        ]
      },
      {
        "source": "状态空间表达式的建立",
        "target": "状态空间",
        "weight": 1,
        "relation_label": "前置知识",
        "relation_candidates": [
          {
            "label": "前置知识",
            "count": 1
          }
        ]
      },
      {
        "source": "状态空间表达式的建立",
        "target": "状态空间表达式的能控标准型和能观标准型",
        "weight": 1,
        "relation_label": "2 传递函数有零点",
        "relation_candidates": [
          {
            "label": "2 传递函数有零点",
            "count": 1
          }
        ]
      },
      {
        "source": "状态空间表达式的建立",
        "target": "系统",
        "weight": 1,
        "relation_label": "前置知识",
        "relation_candidates": [
          {
            "label": "前置知识",
            "count": 1
          }
        ]
      },
      {
        "source": "状态空间表达式的建立",
        "target": "系统结构框图",
        "weight": 1,
        "relation_label": "1 系统模拟结构图建立",
        "relation_candidates": [
          {
            "label": "1 系统模拟结构图建立",
            "count": 1
          }
        ]
      },
      {
        "source": "状态空间表达式的能控标准型和能观标准型",
        "target": "传递函数矩阵",
        "weight": 1,
        "relation_label": "能控性与能观性的对偶关系",
        "relation_candidates": [
          {
            "label": "能控性与能观性的对偶关系",
            "count": 1
          }
        ]
      },
      {
        "source": "状态空间表达式的能控标准型和能观标准型",
        "target": "状态向量的线性变换",
        "weight": 1,
        "relation_label": "化为标准型",
        "relation_candidates": [
          {
            "label": "化为标准型",
            "count": 1
          }
        ]
      },
      {
        "source": "状态空间表达式的能控标准型和能观标准型",
        "target": "状态空间表达式的建立",
        "weight": 1,
        "relation_label": "写为传递函数",
        "relation_candidates": [
          {
            "label": "写为传递函数",
            "count": 1
          }
        ]
      },
      {
        "source": "状态空间表达式的能控标准型和能观标准型",
        "target": "线性定常系统的能控性",
        "weight": 2,
        "relation_label": "判断能控能观性",
        "relation_candidates": [
          {
            "label": "判断能控能观性",
            "count": 1
          },
          {
            "label": "能控标准型",
            "count": 1
          }
        ]
      },
      {
        "source": "状态空间表达式的能控标准型和能观标准型",
        "target": "线性定常系统的能观性",
        "weight": 2,
        "relation_label": "判断能控能观性",
        "relation_candidates": [
          {
            "label": "判断能控能观性",
            "count": 1
          },
          {
            "label": "能观标准型",
            "count": 1
          }
        ]
      },
      {
        "source": "状态观测器",
        "target": "卡尔曼滤波",
        "weight": 1,
        "relation_label": "状态观测器的扩展",
        "relation_candidates": [
          {
            "label": "状态观测器的扩展",
            "count": 1
          }
        ]
      },
      {
        "source": "状态观测器",
        "target": "极点配置与系统镇定",
        "weight": 1,
        "relation_label": "全维观测器",
        "relation_candidates": [
          {
            "label": "全维观测器",
            "count": 1
          }
        ]
      },
      {
        "source": "状态观测器",
        "target": "线性反馈系统的基本结构",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "现代控制理论",
        "target": "传递函数矩阵",
        "weight": 1,
        "relation_label": "状态空间基础知识",
        "relation_candidates": [
          {
            "label": "状态空间基础知识",
            "count": 1
          }
        ]
      },
      {
        "source": "现代控制理论",
        "target": "传递函数阵的实现问题",
        "weight": 1,
        "relation_label": "可控性和可观测性",
        "relation_candidates": [
          {
            "label": "可控性和可观测性",
            "count": 1
          }
        ]
      },
      {
        "source": "现代控制理论",
        "target": "李雅普诺夫方法在线性系统中的应用",
        "weight": 1,
        "relation_label": "稳定性分析",
        "relation_candidates": [
          {
            "label": "稳定性分析",
            "count": 1
          }
        ]
      },
      {
        "source": "现代控制理论",
        "target": "李雅普诺夫方法在非线性系统中的应用",
        "weight": 1,
        "relation_label": "稳定性分析",
        "relation_candidates": [
          {
            "label": "稳定性分析",
            "count": 1
          }
        ]
      },
      {
        "source": "现代控制理论",
        "target": "李雅普诺夫稳定性理论",
        "weight": 1,
        "relation_label": "稳定性分析",
        "relation_candidates": [
          {
            "label": "稳定性分析",
            "count": 1
          }
        ]
      },
      {
        "source": "现代控制理论",
        "target": "李雅普诺夫第一法",
        "weight": 1,
        "relation_label": "稳定性分析",
        "relation_candidates": [
          {
            "label": "稳定性分析",
            "count": 1
          }
        ]
      },
      {
        "source": "现代控制理论",
        "target": "李雅普诺夫第二法",
        "weight": 1,
        "relation_label": "稳定性分析",
        "relation_candidates": [
          {
            "label": "稳定性分析",
            "count": 1
          }
        ]
      },
      {
        "source": "现代控制理论",
        "target": "极点配置与系统镇定",
        "weight": 1,
        "relation_label": "线性系统综合",
        "relation_candidates": [
          {
            "label": "线性系统综合",
            "count": 1
          }
        ]
      },
      {
        "source": "现代控制理论",
        "target": "状态向量的线性变换",
        "weight": 1,
        "relation_label": "状态空间基础知识",
        "relation_candidates": [
          {
            "label": "状态空间基础知识",
            "count": 1
          }
        ]
      },
      {
        "source": "现代控制理论",
        "target": "状态空间",
        "weight": 1,
        "relation_label": "状态空间基础知识",
        "relation_candidates": [
          {
            "label": "状态空间基础知识",
            "count": 1
          }
        ]
      },
      {
        "source": "现代控制理论",
        "target": "状态空间表达式的建立",
        "weight": 1,
        "relation_label": "状态空间基础知识",
        "relation_candidates": [
          {
            "label": "状态空间基础知识",
            "count": 1
          }
        ]
      },
      {
        "source": "现代控制理论",
        "target": "状态空间表达式的能控标准型和能观标准型",
        "weight": 1,
        "relation_label": "可控性和可观测性",
        "relation_candidates": [
          {
            "label": "可控性和可观测性",
            "count": 1
          }
        ]
      },
      {
        "source": "现代控制理论",
        "target": "状态观测器",
        "weight": 1,
        "relation_label": "线性系统综合",
        "relation_candidates": [
          {
            "label": "线性系统综合",
            "count": 1
          }
        ]
      },
      {
        "source": "现代控制理论",
        "target": "系统解耦",
        "weight": 1,
        "relation_label": "线性系统综合",
        "relation_candidates": [
          {
            "label": "线性系统综合",
            "count": 1
          }
        ]
      },
      {
        "source": "现代控制理论",
        "target": "线性反馈系统的基本结构",
        "weight": 1,
        "relation_label": "线性系统综合",
        "relation_candidates": [
          {
            "label": "线性系统综合",
            "count": 1
          }
        ]
      },
      {
        "source": "现代控制理论",
        "target": "线性定常状态方程的解",
        "weight": 1,
        "relation_label": "状态方程求解",
        "relation_candidates": [
          {
            "label": "状态方程求解",
            "count": 1
          }
        ]
      },
      {
        "source": "现代控制理论",
        "target": "线性定常系统的能控性",
        "weight": 1,
        "relation_label": "可控性和可观测性",
        "relation_candidates": [
          {
            "label": "可控性和可观测性",
            "count": 1
          }
        ]
      },
      {
        "source": "现代控制理论",
        "target": "线性定常系统的能观性",
        "weight": 1,
        "relation_label": "可控性和可观测性",
        "relation_candidates": [
          {
            "label": "可控性和可观测性",
            "count": 1
          }
        ]
      },
      {
        "source": "现代控制理论",
        "target": "线性时变状态方程的解",
        "weight": 1,
        "relation_label": "状态方程求解",
        "relation_candidates": [
          {
            "label": "状态方程求解",
            "count": 1
          }
        ]
      },
      {
        "source": "现代控制理论",
        "target": "线性时变系统的能控能观性",
        "weight": 1,
        "relation_label": "可控性和可观测性",
        "relation_candidates": [
          {
            "label": "可控性和可观测性",
            "count": 1
          }
        ]
      },
      {
        "source": "现代控制理论",
        "target": "线性系统的结构分解",
        "weight": 1,
        "relation_label": "可控性和可观测性",
        "relation_candidates": [
          {
            "label": "可控性和可观测性",
            "count": 1
          }
        ]
      },
      {
        "source": "现代控制理论",
        "target": "连续时间系统状态方程的离散化",
        "weight": 1,
        "relation_label": "状态方程求解",
        "relation_candidates": [
          {
            "label": "状态方程求解",
            "count": 1
          }
        ]
      },
      {
        "source": "离散系统的稳定性分析",
        "target": "线性系统稳定性分析",
        "weight": 2,
        "relation_label": "离散系统稳定的充分必要条件",
        "relation_candidates": [
          {
            "label": "离散系统稳定的充分必要条件",
            "count": 1
          },
          {
            "label": "连续系统中",
            "count": 1
          }
        ]
      },
      {
        "source": "离散系统的稳定性分析",
        "target": "脉冲传递函数",
        "weight": 1,
        "relation_label": "离散系统稳定的充分必要条件",
        "relation_candidates": [
          {
            "label": "离散系统稳定的充分必要条件",
            "count": 1
          }
        ]
      },
      {
        "source": "离散系统稳态分析",
        "target": "线性系统稳态误差计算",
        "weight": 1,
        "relation_label": "稳态误差计算",
        "relation_candidates": [
          {
            "label": "稳态误差计算",
            "count": 1
          }
        ]
      },
      {
        "source": "稳定裕度",
        "target": "Bode 图",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "稳定裕度",
        "target": "Nyquist图",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "稳定裕度",
        "target": "线性系统稳定性分析",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "稳定裕度",
        "target": "非最小相位系统",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "系统",
        "target": "传递函数",
        "weight": 1,
        "relation_label": "外部描述",
        "relation_candidates": [
          {
            "label": "外部描述",
            "count": 1
          }
        ]
      },
      {
        "source": "系统",
        "target": "涌现",
        "weight": 1,
        "relation_label": "复杂系统 Complex System",
        "relation_candidates": [
          {
            "label": "复杂系统 Complex System",
            "count": 1
          }
        ]
      },
      {
        "source": "系统",
        "target": "状态空间",
        "weight": 1,
        "relation_label": "内部描述",
        "relation_candidates": [
          {
            "label": "内部描述",
            "count": 1
          }
        ]
      },
      {
        "source": "系统",
        "target": "线性时不变系统",
        "weight": 1,
        "relation_label": "系统的分类",
        "relation_candidates": [
          {
            "label": "系统的分类",
            "count": 1
          }
        ]
      },
      {
        "source": "系统科学",
        "target": "反馈",
        "weight": 1,
        "relation_label": "控制论 (Cybernetics)",
        "relation_candidates": [
          {
            "label": "控制论 (Cybernetics)",
            "count": 1
          }
        ]
      },
      {
        "source": "系统科学",
        "target": "系统",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "系统结构框图",
        "target": "传递函数",
        "weight": 2,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          },
          {
            "label": "传递函数的简化",
            "count": 1
          }
        ]
      },
      {
        "source": "线性反馈系统的基本结构",
        "target": "传递函数",
        "weight": 1,
        "relation_label": "前置知识",
        "relation_candidates": [
          {
            "label": "前置知识",
            "count": 1
          }
        ]
      },
      {
        "source": "线性反馈系统的基本结构",
        "target": "反馈",
        "weight": 1,
        "relation_label": "前置知识",
        "relation_candidates": [
          {
            "label": "前置知识",
            "count": 1
          }
        ]
      },
      {
        "source": "线性反馈系统的基本结构",
        "target": "状态空间",
        "weight": 1,
        "relation_label": "前置知识",
        "relation_candidates": [
          {
            "label": "前置知识",
            "count": 1
          }
        ]
      },
      {
        "source": "线性定常状态方程的解",
        "target": "状态向量的线性变换",
        "weight": 1,
        "relation_label": "求解核心",
        "relation_candidates": [
          {
            "label": "求解核心",
            "count": 1
          }
        ]
      },
      {
        "source": "线性定常状态方程的解",
        "target": "经典输入信号",
        "weight": 1,
        "relation_label": "线性定常非齐次状态方程的解",
        "relation_candidates": [
          {
            "label": "线性定常非齐次状态方程的解",
            "count": 1
          }
        ]
      },
      {
        "source": "线性定常系统的能控性",
        "target": "传递函数矩阵",
        "weight": 1,
        "relation_label": "~~3. 传递函数判断能控性~~",
        "relation_candidates": [
          {
            "label": "~~3. 传递函数判断能控性~~",
            "count": 1
          }
        ]
      },
      {
        "source": "线性定常系统的能控性",
        "target": "状态向量的线性变换",
        "weight": 1,
        "relation_label": "对角线规范型判据",
        "relation_candidates": [
          {
            "label": "对角线规范型判据",
            "count": 1
          }
        ]
      },
      {
        "source": "线性定常系统的能控性",
        "target": "零极点",
        "weight": 1,
        "relation_label": "~~3. 传递函数判断能控性~~",
        "relation_candidates": [
          {
            "label": "~~3. 传递函数判断能控性~~",
            "count": 1
          }
        ]
      },
      {
        "source": "线性定常系统的能观性",
        "target": "状态向量的线性变换",
        "weight": 1,
        "relation_label": "对角线规范型判据",
        "relation_candidates": [
          {
            "label": "对角线规范型判据",
            "count": 1
          }
        ]
      },
      {
        "source": "线性系统的校正",
        "target": "反馈",
        "weight": 1,
        "relation_label": "反馈校正",
        "relation_candidates": [
          {
            "label": "反馈校正",
            "count": 1
          }
        ]
      },
      {
        "source": "线性系统的校正",
        "target": "欠阻尼二阶系统动态分析",
        "weight": 1,
        "relation_label": "动态指标",
        "relation_candidates": [
          {
            "label": "动态指标",
            "count": 1
          }
        ]
      },
      {
        "source": "线性系统的校正",
        "target": "稳定裕度",
        "weight": 1,
        "relation_label": "相对稳定性",
        "relation_candidates": [
          {
            "label": "相对稳定性",
            "count": 1
          }
        ]
      },
      {
        "source": "线性系统的校正",
        "target": "线性系统稳态误差计算",
        "weight": 1,
        "relation_label": "稳态指标",
        "relation_candidates": [
          {
            "label": "稳态指标",
            "count": 1
          }
        ]
      },
      {
        "source": "线性系统的结构分解",
        "target": "传递函数阵的实现问题",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "线性系统的结构分解",
        "target": "状态空间",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "线性系统的结构分解",
        "target": "线性定常系统的能控性",
        "weight": 1,
        "relation_label": "按能控性分解",
        "relation_candidates": [
          {
            "label": "按能控性分解",
            "count": 1
          }
        ]
      },
      {
        "source": "线性系统的结构分解",
        "target": "线性定常系统的能观性",
        "weight": 1,
        "relation_label": "按能观性分解",
        "relation_candidates": [
          {
            "label": "按能观性分解",
            "count": 1
          }
        ]
      },
      {
        "source": "线性系统稳定性分析",
        "target": "传递函数",
        "weight": 1,
        "relation_label": "线性系统稳定的充分必要条件",
        "relation_candidates": [
          {
            "label": "线性系统稳定的充分必要条件",
            "count": 1
          }
        ]
      },
      {
        "source": "线性系统稳定性分析",
        "target": "李雅普诺夫稳定性理论",
        "weight": 1,
        "relation_label": "基础概念",
        "relation_candidates": [
          {
            "label": "基础概念",
            "count": 1
          }
        ]
      },
      {
        "source": "线性系统稳定性分析",
        "target": "零极点",
        "weight": 1,
        "relation_label": "线性系统稳定的充分必要条件",
        "relation_candidates": [
          {
            "label": "线性系统稳定的充分必要条件",
            "count": 1
          }
        ]
      },
      {
        "source": "线性系统稳态误差计算",
        "target": "线性系统稳定性分析",
        "weight": 2,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          },
          {
            "label": "判断是否稳定",
            "count": 1
          }
        ]
      },
      {
        "source": "线性系统稳态误差计算",
        "target": "经典输入信号",
        "weight": 1,
        "relation_label": "影响系统稳定误差的因素",
        "relation_candidates": [
          {
            "label": "影响系统稳定误差的因素",
            "count": 1
          }
        ]
      },
      {
        "source": "线性系统稳态误差计算",
        "target": "频率特性",
        "weight": 1,
        "relation_label": "正弦信号的输入下的误差计算",
        "relation_candidates": [
          {
            "label": "正弦信号的输入下的误差计算",
            "count": 1
          }
        ]
      },
      {
        "source": "经典控制理论",
        "target": "0°根轨迹绘制规则",
        "weight": 1,
        "relation_label": "根轨迹法",
        "relation_candidates": [
          {
            "label": "根轨迹法",
            "count": 1
          }
        ]
      },
      {
        "source": "经典控制理论",
        "target": "180°根轨迹绘制法则",
        "weight": 1,
        "relation_label": "根轨迹法",
        "relation_candidates": [
          {
            "label": "根轨迹法",
            "count": 1
          }
        ]
      },
      {
        "source": "经典控制理论",
        "target": "Bode 图",
        "weight": 1,
        "relation_label": "频域分析法",
        "relation_candidates": [
          {
            "label": "频域分析法",
            "count": 1
          }
        ]
      },
      {
        "source": "经典控制理论",
        "target": "Nyquist图",
        "weight": 1,
        "relation_label": "频域分析法",
        "relation_candidates": [
          {
            "label": "频域分析法",
            "count": 1
          }
        ]
      },
      {
        "source": "经典控制理论",
        "target": "PID",
        "weight": 1,
        "relation_label": "校正装置",
        "relation_candidates": [
          {
            "label": "校正装置",
            "count": 1
          }
        ]
      },
      {
        "source": "经典控制理论",
        "target": "一阶系统的时域分析",
        "weight": 1,
        "relation_label": "时域分析",
        "relation_candidates": [
          {
            "label": "时域分析",
            "count": 1
          }
        ]
      },
      {
        "source": "经典控制理论",
        "target": "二阶系统的时域分析",
        "weight": 1,
        "relation_label": "时域分析",
        "relation_candidates": [
          {
            "label": "时域分析",
            "count": 1
          }
        ]
      },
      {
        "source": "经典控制理论",
        "target": "传递函数",
        "weight": 1,
        "relation_label": "基础知识",
        "relation_candidates": [
          {
            "label": "基础知识",
            "count": 1
          }
        ]
      },
      {
        "source": "经典控制理论",
        "target": "信号流图",
        "weight": 1,
        "relation_label": "基础知识",
        "relation_candidates": [
          {
            "label": "基础知识",
            "count": 1
          }
        ]
      },
      {
        "source": "经典控制理论",
        "target": "广义根轨迹",
        "weight": 1,
        "relation_label": "根轨迹法",
        "relation_candidates": [
          {
            "label": "根轨迹法",
            "count": 1
          }
        ]
      },
      {
        "source": "经典控制理论",
        "target": "开环频率特性",
        "weight": 1,
        "relation_label": "频域分析法",
        "relation_candidates": [
          {
            "label": "频域分析法",
            "count": 1
          }
        ]
      },
      {
        "source": "经典控制理论",
        "target": "时间响应的性能指标",
        "weight": 1,
        "relation_label": "基础知识",
        "relation_candidates": [
          {
            "label": "基础知识",
            "count": 1
          }
        ]
      },
      {
        "source": "经典控制理论",
        "target": "校正环节的设计",
        "weight": 1,
        "relation_label": "线性系统的校正与设计",
        "relation_candidates": [
          {
            "label": "线性系统的校正与设计",
            "count": 1
          }
        ]
      },
      {
        "source": "经典控制理论",
        "target": "根轨迹法基础",
        "weight": 1,
        "relation_label": "根轨迹法",
        "relation_candidates": [
          {
            "label": "根轨迹法",
            "count": 1
          }
        ]
      },
      {
        "source": "经典控制理论",
        "target": "滞后校正",
        "weight": 1,
        "relation_label": "校正装置",
        "relation_candidates": [
          {
            "label": "校正装置",
            "count": 1
          }
        ]
      },
      {
        "source": "经典控制理论",
        "target": "稳定裕度",
        "weight": 1,
        "relation_label": "频域分析法",
        "relation_candidates": [
          {
            "label": "频域分析法",
            "count": 1
          }
        ]
      },
      {
        "source": "经典控制理论",
        "target": "系统结构框图",
        "weight": 1,
        "relation_label": "基础知识",
        "relation_candidates": [
          {
            "label": "基础知识",
            "count": 1
          }
        ]
      },
      {
        "source": "经典控制理论",
        "target": "线性系统的校正",
        "weight": 1,
        "relation_label": "线性系统的校正与设计",
        "relation_candidates": [
          {
            "label": "线性系统的校正与设计",
            "count": 1
          }
        ]
      },
      {
        "source": "经典控制理论",
        "target": "线性系统稳定性分析",
        "weight": 1,
        "relation_label": "稳定性分析",
        "relation_candidates": [
          {
            "label": "稳定性分析",
            "count": 1
          }
        ]
      },
      {
        "source": "经典控制理论",
        "target": "线性系统稳态误差计算",
        "weight": 1,
        "relation_label": "稳态误差",
        "relation_candidates": [
          {
            "label": "稳态误差",
            "count": 1
          }
        ]
      },
      {
        "source": "经典控制理论",
        "target": "经典环节的传递函数",
        "weight": 1,
        "relation_label": "基础知识",
        "relation_candidates": [
          {
            "label": "基础知识",
            "count": 1
          }
        ]
      },
      {
        "source": "经典控制理论",
        "target": "经典输入信号",
        "weight": 1,
        "relation_label": "基础知识",
        "relation_candidates": [
          {
            "label": "基础知识",
            "count": 1
          }
        ]
      },
      {
        "source": "经典控制理论",
        "target": "超前校正",
        "weight": 1,
        "relation_label": "校正装置",
        "relation_candidates": [
          {
            "label": "校正装置",
            "count": 1
          }
        ]
      },
      {
        "source": "经典控制理论",
        "target": "频域稳定判据",
        "weight": 1,
        "relation_label": "频域分析法",
        "relation_candidates": [
          {
            "label": "频域分析法",
            "count": 1
          }
        ]
      },
      {
        "source": "经典控制理论",
        "target": "频带宽度",
        "weight": 1,
        "relation_label": "频域分析法",
        "relation_candidates": [
          {
            "label": "频域分析法",
            "count": 1
          }
        ]
      },
      {
        "source": "经典控制理论",
        "target": "频率特性",
        "weight": 1,
        "relation_label": "频域分析法",
        "relation_candidates": [
          {
            "label": "频域分析法",
            "count": 1
          }
        ]
      },
      {
        "source": "经典控制理论",
        "target": "高阶系统的时域分析",
        "weight": 1,
        "relation_label": "时域分析",
        "relation_candidates": [
          {
            "label": "时域分析",
            "count": 1
          }
        ]
      },
      {
        "source": "经典环节的传递函数",
        "target": "传递函数",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "经典环节的传递函数",
        "target": "欠阻尼二阶系统动态分析",
        "weight": 1,
        "relation_label": "阶振荡环节",
        "relation_candidates": [
          {
            "label": "阶振荡环节",
            "count": 1
          }
        ]
      },
      {
        "source": "经典环节的传递函数",
        "target": "稳定裕度",
        "weight": 1,
        "relation_label": "阶振荡环节",
        "relation_candidates": [
          {
            "label": "阶振荡环节",
            "count": 1
          }
        ]
      },
      {
        "source": "经典环节的传递函数",
        "target": "经典输入信号",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "经典环节的传递函数",
        "target": "非最小相位系统",
        "weight": 1,
        "relation_label": "对称关系",
        "relation_candidates": [
          {
            "label": "对称关系",
            "count": 1
          }
        ]
      },
      {
        "source": "经典环节的传递函数",
        "target": "频带宽度",
        "weight": 1,
        "relation_label": "阶振荡环节",
        "relation_candidates": [
          {
            "label": "阶振荡环节",
            "count": 1
          }
        ]
      },
      {
        "source": "经典输入信号",
        "target": "经典控制理论",
        "weight": 1,
        "relation_label": "正弦信号",
        "relation_candidates": [
          {
            "label": "正弦信号",
            "count": 1
          }
        ]
      },
      {
        "source": "经典输入信号",
        "target": "脉冲函数",
        "weight": 1,
        "relation_label": "单位脉冲信号",
        "relation_candidates": [
          {
            "label": "单位脉冲信号",
            "count": 1
          }
        ]
      },
      {
        "source": "经典输入信号",
        "target": "阶跃函数",
        "weight": 1,
        "relation_label": "单位阶跃信号",
        "relation_candidates": [
          {
            "label": "单位阶跃信号",
            "count": 1
          }
        ]
      },
      {
        "source": "脉冲传递函数",
        "target": "传递函数",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "脉冲传递函数",
        "target": "信号保持",
        "weight": 1,
        "relation_label": "ZOH 串联的广义对象",
        "relation_candidates": [
          {
            "label": "ZOH 串联的广义对象",
            "count": 1
          }
        ]
      },
      {
        "source": "自动控制原理",
        "target": "控制系统的数学模型",
        "weight": 1,
        "relation_label": "基础知识",
        "relation_candidates": [
          {
            "label": "基础知识",
            "count": 1
          }
        ]
      },
      {
        "source": "自动控制原理",
        "target": "现代控制理论",
        "weight": 1,
        "relation_label": "主要分支",
        "relation_candidates": [
          {
            "label": "主要分支",
            "count": 1
          }
        ]
      },
      {
        "source": "自动控制原理",
        "target": "系统",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "自动控制原理",
        "target": "经典控制理论",
        "weight": 1,
        "relation_label": "主要分支",
        "relation_candidates": [
          {
            "label": "主要分支",
            "count": 1
          }
        ]
      },
      {
        "source": "自动控制原理",
        "target": "经典输入信号",
        "weight": 1,
        "relation_label": "基础知识",
        "relation_candidates": [
          {
            "label": "基础知识",
            "count": 1
          }
        ]
      },
      {
        "source": "自动控制原理",
        "target": "自动控制系统",
        "weight": 1,
        "relation_label": "基础知识",
        "relation_candidates": [
          {
            "label": "基础知识",
            "count": 1
          }
        ]
      },
      {
        "source": "自动控制原理",
        "target": "计算机控制系统",
        "weight": 1,
        "relation_label": "主要分支",
        "relation_candidates": [
          {
            "label": "主要分支",
            "count": 1
          }
        ]
      },
      {
        "source": "自动控制系统",
        "target": "反馈",
        "weight": 1,
        "relation_label": "反馈",
        "relation_candidates": [
          {
            "label": "反馈",
            "count": 1
          }
        ]
      },
      {
        "source": "自动控制系统",
        "target": "系统结构框图",
        "weight": 1,
        "relation_label": "基本框架",
        "relation_candidates": [
          {
            "label": "基本框架",
            "count": 1
          }
        ]
      },
      {
        "source": "计算机控制系统",
        "target": "信号保持",
        "weight": 1,
        "relation_label": "保持器",
        "relation_candidates": [
          {
            "label": "保持器",
            "count": 1
          }
        ]
      },
      {
        "source": "计算机控制系统",
        "target": "信号采样",
        "weight": 1,
        "relation_label": "采样器",
        "relation_candidates": [
          {
            "label": "采样器",
            "count": 1
          }
        ]
      },
      {
        "source": "计算机控制系统",
        "target": "参数优化的低阶算法",
        "weight": 1,
        "relation_label": "数字控制器的 z 域直接设计方法",
        "relation_candidates": [
          {
            "label": "数字控制器的 z 域直接设计方法",
            "count": 1
          }
        ]
      },
      {
        "source": "计算机控制系统",
        "target": "史密斯预估补偿控制",
        "weight": 1,
        "relation_label": "数字控制器的 z 域直接设计方法",
        "relation_candidates": [
          {
            "label": "数字控制器的 z 域直接设计方法",
            "count": 1
          }
        ]
      },
      {
        "source": "计算机控制系统",
        "target": "大林算法控制器",
        "weight": 1,
        "relation_label": "数字控制器的 z 域直接设计方法",
        "relation_candidates": [
          {
            "label": "数字控制器的 z 域直接设计方法",
            "count": 1
          }
        ]
      },
      {
        "source": "计算机控制系统",
        "target": "数字 PID 控制器",
        "weight": 1,
        "relation_label": "数字控制器模拟化设计方法",
        "relation_candidates": [
          {
            "label": "数字控制器模拟化设计方法",
            "count": 1
          }
        ]
      },
      {
        "source": "计算机控制系统",
        "target": "数字PID 参数整定",
        "weight": 1,
        "relation_label": "数字控制器模拟化设计方法",
        "relation_candidates": [
          {
            "label": "数字控制器模拟化设计方法",
            "count": 1
          }
        ]
      },
      {
        "source": "计算机控制系统",
        "target": "数字控制器",
        "weight": 1,
        "relation_label": "数字控制器的 z 域直接设计方法",
        "relation_candidates": [
          {
            "label": "数字控制器的 z 域直接设计方法",
            "count": 1
          }
        ]
      },
      {
        "source": "计算机控制系统",
        "target": "最小拍控制器",
        "weight": 1,
        "relation_label": "数字控制器的 z 域直接设计方法",
        "relation_candidates": [
          {
            "label": "数字控制器的 z 域直接设计方法",
            "count": 1
          }
        ]
      },
      {
        "source": "计算机控制系统",
        "target": "最小拍控制器的改进",
        "weight": 1,
        "relation_label": "数字控制器的 z 域直接设计方法",
        "relation_candidates": [
          {
            "label": "数字控制器的 z 域直接设计方法",
            "count": 1
          }
        ]
      },
      {
        "source": "计算机控制系统",
        "target": "模拟控制器离散化",
        "weight": 1,
        "relation_label": "数字控制器模拟化设计方法",
        "relation_candidates": [
          {
            "label": "数字控制器模拟化设计方法",
            "count": 1
          }
        ]
      },
      {
        "source": "计算机控制系统",
        "target": "离散系统的稳定性分析",
        "weight": 1,
        "relation_label": "离散控制系统分析",
        "relation_candidates": [
          {
            "label": "离散控制系统分析",
            "count": 1
          }
        ]
      },
      {
        "source": "计算机控制系统",
        "target": "离散系统稳态分析",
        "weight": 1,
        "relation_label": "离散控制系统分析",
        "relation_candidates": [
          {
            "label": "离散控制系统分析",
            "count": 1
          }
        ]
      },
      {
        "source": "计算机控制系统",
        "target": "线性定常系统的差分方程求解",
        "weight": 1,
        "relation_label": "差分方程求解",
        "relation_candidates": [
          {
            "label": "差分方程求解",
            "count": 1
          }
        ]
      },
      {
        "source": "计算机控制系统",
        "target": "脉冲传递函数",
        "weight": 1,
        "relation_label": "离散系统中的传递函数",
        "relation_candidates": [
          {
            "label": "离散系统中的传递函数",
            "count": 1
          }
        ]
      },
      {
        "source": "计算机控制系统",
        "target": "计算机控制系统概述",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "超前校正",
        "target": "稳定裕度",
        "weight": 3,
        "relation_label": "设计校正的步骤",
        "relation_candidates": [
          {
            "label": "设计校正的步骤",
            "count": 2
          },
          {
            "label": "改善动态性能",
            "count": 1
          }
        ]
      },
      {
        "source": "超前校正",
        "target": "频带宽度",
        "weight": 1,
        "relation_label": "改善动态性能",
        "relation_candidates": [
          {
            "label": "改善动态性能",
            "count": 1
          }
        ]
      },
      {
        "source": "连续时间系统状态方程的离散化",
        "target": "模拟控制器离散化",
        "weight": 1,
        "relation_label": "个基本假设",
        "relation_candidates": [
          {
            "label": "个基本假设",
            "count": 1
          }
        ]
      },
      {
        "source": "连续时间系统状态方程的离散化",
        "target": "线性时变状态方程的解",
        "weight": 1,
        "relation_label": "线性定常系统的离散化",
        "relation_candidates": [
          {
            "label": "线性定常系统的离散化",
            "count": 1
          }
        ]
      },
      {
        "source": "零极点",
        "target": "二阶系统的时域分析",
        "weight": 1,
        "relation_label": "动态性能分析",
        "relation_candidates": [
          {
            "label": "动态性能分析",
            "count": 1
          }
        ]
      },
      {
        "source": "零极点",
        "target": "传递函数",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "零极点",
        "target": "根轨迹法基础",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "零极点",
        "target": "线性系统稳定性分析",
        "weight": 1,
        "relation_label": "稳定性分析",
        "relation_candidates": [
          {
            "label": "稳定性分析",
            "count": 1
          }
        ]
      },
      {
        "source": "零极点",
        "target": "高阶系统的时域分析",
        "weight": 1,
        "relation_label": "闭环主导极点",
        "relation_candidates": [
          {
            "label": "闭环主导极点",
            "count": 1
          }
        ]
      },
      {
        "source": "非最小相位系统",
        "target": "Bode 图",
        "weight": 1,
        "relation_label": "非最小相位环节",
        "relation_candidates": [
          {
            "label": "非最小相位环节",
            "count": 1
          }
        ]
      },
      {
        "source": "非最小相位系统",
        "target": "Nyquist图",
        "weight": 1,
        "relation_label": "非最小相位环节",
        "relation_candidates": [
          {
            "label": "非最小相位环节",
            "count": 1
          }
        ]
      },
      {
        "source": "非最小相位系统",
        "target": "传递函数",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "非最小相位系统",
        "target": "经典环节的传递函数",
        "weight": 1,
        "relation_label": "非最小相位环节",
        "relation_candidates": [
          {
            "label": "非最小相位环节",
            "count": 1
          }
        ]
      },
      {
        "source": "频域稳定判据",
        "target": "Bode 图",
        "weight": 1,
        "relation_label": "Bode 判据",
        "relation_candidates": [
          {
            "label": "Bode 判据",
            "count": 1
          }
        ]
      },
      {
        "source": "频域稳定判据",
        "target": "Nyquist图",
        "weight": 1,
        "relation_label": "Nyquist 判据",
        "relation_candidates": [
          {
            "label": "Nyquist 判据",
            "count": 1
          }
        ]
      },
      {
        "source": "频域稳定判据",
        "target": "传递函数",
        "weight": 1,
        "relation_label": "幅角原理",
        "relation_candidates": [
          {
            "label": "幅角原理",
            "count": 1
          }
        ]
      },
      {
        "source": "频域稳定判据",
        "target": "线性系统稳定性分析",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "频带宽度",
        "target": "稳定裕度",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "频带宽度",
        "target": "频率特性",
        "weight": 1,
        "relation_label": "基本定义",
        "relation_candidates": [
          {
            "label": "基本定义",
            "count": 1
          }
        ]
      },
      {
        "source": "频率特性",
        "target": "传递函数",
        "weight": 1,
        "relation_label": "关联",
        "relation_candidates": [
          {
            "label": "关联",
            "count": 1
          }
        ]
      },
      {
        "source": "高阶系统的时域分析",
        "target": "二阶系统的时域分析",
        "weight": 1,
        "relation_label": "主导极点",
        "relation_candidates": [
          {
            "label": "主导极点",
            "count": 1
          }
        ]
      },
      {
        "source": "高阶系统的时域分析",
        "target": "零极点",
        "weight": 1,
        "relation_label": "主导极点",
        "relation_candidates": [
          {
            "label": "主导极点",
            "count": 1
          }
        ]
      }
    ]
  },
  "notes": {
    "线性时不变系统": {
      "id": "线性时不变系统",
      "title": "线性时不变系统",
      "category": "0. 基础知识",
      "subcategory": "0. 基础知识",
      "tags": [],
      "aliases": [
        "线性定常系统"
      ],
      "terminology": "Linear  Time Invariant",
      "summary": "Linear Time Invariant LTI System",
      "headings": [
        "基本性质",
        "1.线性",
        "2.时不变"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-04-16T13:01:27.000+08:00",
      "updated": "2025-09-26T12:06:16.000+08:00",
      "permalink": "/A2- 控制理论/0. 基础知识/LTI 线性时不变系统/",
      "dg_path": "A2- 控制理论/0. 基础知识/LTI 线性时不变系统.md",
      "source_path": "src/site/notes/线性时不变系统.md",
      "viewer_markdown_path": "../source-notes/线性时不变系统.md",
      "internal_links": [],
      "inbound_links": [
        "传递函数",
        "系统"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "Linear Time Invariant LTI System \n\n### 基本性质\n#### 1.线性\n$$\\begin{align} \no\\{\\alpha f_{1}(t)\\}&=\\alpha x_{1}(t) \\\\\n\no\\{f_{1}(t)+f_{2}(t)\\}&=x_{1}(t)+x_{2}(t) \\\\ \no\\{\\alpha_{1} f_{1}(t)+\\alpha_{2} f_{2}(t)\\}&=\\alpha_{1}x_{1}(t)+\\alpha_{2}x_{2}(t)\n\\end{align}$$\n\n叠加原理\n两个外作用同时加于系统所产生的总输出，等于各个外作用单独作用时分别产生的输出之和\n外作用的数值增大若干倍时，输出相应增大同样的倍数\n\n#### 2.时不变\n$$\\begin{align}\n o\\{ f(t)\\}&=x(t)\\\\\no\\{ f(t-\\tau)\\}&=x(t-\\tau)\n\\end{align}$$\n\n系统的输出信号在时间上的延迟等于输入信号在时间上的延迟"
    },
    "反馈": {
      "id": "反馈",
      "title": "反馈",
      "category": "0. 基础知识",
      "subcategory": "0. 基础知识",
      "tags": [],
      "aliases": [
        "Feedback"
      ],
      "terminology": "Feedback",
      "summary": "Feedback 反馈",
      "headings": [
        "一、基本概念",
        "二、反馈的分类",
        "负反馈 (Negative Feedback)",
        "正反馈 (Positive Feedback)",
        "三、负反馈控制的基本规律"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-09-03T23:41:44.290+08:00",
      "updated": "2026-02-28T13:02:24.690+08:00",
      "permalink": "/A2- 控制理论/0. 基础知识/反馈/",
      "dg_path": "A2- 控制理论/0. 基础知识/反馈.md",
      "source_path": "src/site/notes/反馈.md",
      "viewer_markdown_path": "../source-notes/反馈.md",
      "internal_links": [
        "系统科学",
        "自动控制系统"
      ],
      "inbound_links": [
        "系统科学",
        "线性反馈系统的基本结构",
        "线性系统的校正",
        "自动控制系统"
      ],
      "out_of_scope_links": [],
      "missing_links": [
        "伺服系统",
        "控制论",
        "放大电路"
      ],
      "content_excerpt": "Feedback 反馈\n\n反馈是系统科学\\和控制论\\中的一个核心概念，它指的是将系统输出信号的一部分或全部送回到输入端，并与输入信号进行比较，从而产生一个偏差信号，进而影响系统行为的过程。反馈是实现自动控制系统\\、稳定系统性能、抑制扰动和实现复杂功能的基础。\n[!note]\n\"反馈是系统科学\\的灵魂\" ——Norbert Wiener\n\n### 一、基本概念\n反馈：取出输出量送回输入端，并与输入信号相比较产生偏差信号的过程。\n反馈控制：采用负反馈，利用偏差进行控制的过程。\n开环控制：输出不影响输入的控制方式，没有反馈环节。\n闭环控制：输出通过反馈环节影响输入的控制方式，具有反馈环节。\n\n### 二、反馈的分类\n\n根据反馈信号与输入信号的叠加方式，反馈主要分为正反馈和负反馈。\n\n#### 1. 负反馈 (Negative Feedback)\n\nNegative Feedback 负反馈是指反馈信号与输入信号相减（或反相叠加）。负反馈是控制系统和电子电路中最常用和最重要的反馈形式，因为它能够：\n稳定系统：抑制系统内部参数变化、外部扰动和非线性因素对输出的影响，提高系统的稳定性。\n提高精度：减小稳态误差，使输出更接近期望值。\n扩展带宽：在放大电路\\中，负反馈可以牺牲增益来换取带宽的增加。\n抑制噪声和失真：有效抑制系统内部产生的噪声和非线性失真。\n改变输入/输出阻抗：根据反馈方式，可以提高或降低输入/输出阻抗。\n[!important]\n负反馈的本质是“变粗为精”、“变慢为快”、“变不稳定为稳定”。\n\n#### 2. 正反馈 (Positive Feedback)\n\nPositive Feedback 正反馈是指反馈信号与输入信号相加（或同相叠加）。正反馈会使系统增益增大，甚至可能导致系统不稳定或产生振荡。它主要用于：\n振荡器：产生周期性信号。\n施密特触发器：实现迟滞特性。\n锁存器：实现记忆功能。\n自激振荡：在某些情况下，正反馈可能导致系统失控或自激振荡。\n\n### 三、负反馈控制的基本规律\n\n负反馈控制系统具有以下基本规律：\n被调量存在误差：\n系统正是依靠被调量的偏差进行控制的。稳态误差只能减小，却不可能完全消除。这是因为如果误差为零，则没有偏差信号来驱动控制作用。\n抵抗扰动，服从给定：\n抵抗扰动：反馈控制系统具有良好的抗扰性能，它能有效地抑制一切被负反馈环所包围的前向通道上的扰动。对前向通路上的扰动有抑制作用，而反馈回路上的扰动反而会增大被调量的误差。\n服从给定：给定作用指的是所期望输出的信号。如果系统紧紧地跟随着给定作用，则称为伺服系统\\。\n系统的精度：\n给定决定系统输出，输出精度自然取决于给定精度。反馈控制系统能够使输出量精确地跟踪输入量，但其精度最终受限于给定信号的精度和测量反馈信号的精度。\n\n系统科学\\\n自动控制系统\\\n放大电路\\\n伺服系统\\"
    },
    "时间常数": {
      "id": "时间常数",
      "title": "时间常数",
      "category": "0. 基础知识",
      "subcategory": "0. 基础知识",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "(terminology::Time Constant ) $\\tau$\n由系统本身决定，反映系统的惯性",
      "headings": [],
      "pinned": false,
      "level": null,
      "created": "2024-05-21T15:20:28.000+08:00",
      "updated": "2025-06-30T16:31:48.000+08:00",
      "permalink": "/A2- 控制理论/0. 基础知识/时间常数/",
      "dg_path": "A2- 控制理论/0. 基础知识/时间常数.md",
      "source_path": "src/site/notes/时间常数.md",
      "viewer_markdown_path": "../source-notes/时间常数.md",
      "internal_links": [],
      "inbound_links": [
        "一阶系统的时域分析",
        "二阶系统的时域分析",
        "传递函数"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "(terminology::Time Constant ) $\\tau$\n由系统本身决定，反映系统的惯性\n\n反映动态过程的时间滞后作用，时间常数越小，惯性越小，系统响应过程越快\n\n惯性滞后：传热、电机\n容量滞后：容量的过渡，比如水箱液位\n\nmermaid\ngraph LR\n时间滞后 -->惯性滞后 & 容量滞后"
    },
    "模态": {
      "id": "模态",
      "title": "模态",
      "category": "0. 基础知识",
      "subcategory": "0. 基础知识",
      "tags": [],
      "aliases": [],
      "terminology": "Modal",
      "summary": "微分方程\\可以用来描述系统状态随时间的变化，而模态是系统自由响应的特征\n系统的自然振动模式或响应模式。在多自由度系统或分布参数系统中，模态是系统在自由振动时的固有振动形态。每个模态都与特定的自然频率和阻尼特性相关联。",
      "headings": [],
      "pinned": false,
      "level": null,
      "created": "2024-05-21T15:20:28.410+08:00",
      "updated": "2025-05-02T17:47:14.000+08:00",
      "permalink": "/A2- 控制理论/0. 基础知识/模态/",
      "dg_path": "A2- 控制理论/0. 基础知识/模态.md",
      "source_path": "src/site/notes/模态.md",
      "viewer_markdown_path": "../source-notes/模态.md",
      "internal_links": [],
      "inbound_links": [
        "传递函数"
      ],
      "out_of_scope_links": [
        "微分方程"
      ],
      "missing_links": [],
      "content_excerpt": "Modal\n\n微分方程\\可以用来描述系统状态随时间的变化，而模态是系统自由响应的特征\n系统的自然振动模式或响应模式。在多自由度系统或分布参数系统中，模态是系统在自由振动时的固有振动形态。每个模态都与特定的自然频率和阻尼特性相关联。\n\n在振动分析中通常也被称为振型 Mode Shape"
    },
    "涌现": {
      "id": "涌现",
      "title": "涌现",
      "category": "0. 基础知识",
      "subcategory": "0. 基础知识",
      "tags": [],
      "aliases": [],
      "terminology": "Emergence",
      "summary": "Emergence\n系统\\理论中的概念，指的是在复杂系统中，整体的行为和属性不是由单个组成部分单独决定的，而是通过这些部分之间的相互作用产生的。",
      "headings": [],
      "pinned": false,
      "level": null,
      "created": "2024-07-08T15:00:13.000+08:00",
      "updated": "2025-06-16T10:59:14.000+08:00",
      "permalink": "/A2- 控制理论/0. 基础知识/涌现/",
      "dg_path": "A2- 控制理论/0. 基础知识/涌现.md",
      "source_path": "src/site/notes/涌现.md",
      "viewer_markdown_path": "../source-notes/涌现.md",
      "internal_links": [
        "系统"
      ],
      "inbound_links": [
        "系统"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "Emergence\n系统\\理论中的概念，指的是在复杂系统中，整体的行为和属性不是由单个组成部分单独决定的，而是通过这些部分之间的相互作用产生的。\n\n涌现现象通常在系统达到一定规模和复杂度时出现，表现为系统的整体性能超出了单个部分性能的简单总和。\n自组织：涌现通常与自组织过程相关，系统中的个体在没有中央控制的情况下通过局部相互作用形成全局模式。\n不可预测性：涌现现象往往难以通过分析单个组成部分来预测，因为整体的行为是由所有部分的相互作用产生的。\n层次性：在多层次系统中，较低层次的相互作用可以导致较高层次的涌现特性。\n非线性：涌现现象往往与非线性动力学有关，即系统的输出与输入之间的关系不是简单的线性关系。\n适应性：涌现可以是适应性的，即系统能够根据环境变化调整其行为，以优化其性能。\n多样性：涌现现象可以在不同的系统中观察到，从生物学中的群体行为到社会学中的文化现象，再到经济学中的市场动态。\n反馈机制：涌现现象往往涉及到正反馈或负反馈机制，这些机制可以加强或抑制某些行为，从而影响整体系统的稳定性。\n临界点：在某些情况下，系统在达到一个临界点时会出现显著的涌现现象，这个临界点可能是由于系统规模的增加或参数的变化。"
    },
    "系统": {
      "id": "系统",
      "title": "系统",
      "category": "0. 基础知识",
      "subcategory": "0. 基础知识",
      "tags": [
        "Transform",
        "System",
        "Mindset"
      ],
      "aliases": [],
      "terminology": "System",
      "summary": "System \n本质上是对象在给定初始条件下，输入到输出的一个变换\n“由一些相互关联、相互作用、相互影响的组织部分构成并具有某些功能的整体”",
      "headings": [
        "一、系统的数学描述",
        "外部描述",
        "内部描述",
        "二、系统的分类",
        "三、系统工程",
        "系统的哲学"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-09-02T09:43:03.000+08:00",
      "updated": "2025-10-13T18:58:52.000+08:00",
      "permalink": "/A2- 控制理论/0. 基础知识/系统/",
      "dg_path": "A2- 控制理论/0. 基础知识/系统.md",
      "source_path": "src/site/notes/系统.md",
      "viewer_markdown_path": "../source-notes/系统.md",
      "internal_links": [
        "传递函数",
        "涌现",
        "状态空间",
        "线性时不变系统"
      ],
      "inbound_links": [
        "涌现",
        "状态空间表达式的建立",
        "系统科学",
        "自动控制原理"
      ],
      "out_of_scope_links": [],
      "missing_links": [
        "自组织",
        "非线性"
      ],
      "content_excerpt": "System \n本质上是对象在给定初始条件下，输入到输出的一个变换\n“由一些相互关联、相互作用、相互影响的组织部分构成并具有某些功能的整体”\n\n### 一、系统的数学描述\n假定研究的系统有多个输入和输出\n\n系统的外部变量\n环境对系统的输入：$\\mathbf{u}=\\begin{bmatrix}{u}_{1} , {u}_{2} , \\cdots , {u}_{p}\\end{bmatrix}^{T}$\n环境对系统的输出： $\\mathbf{y}=\\begin{bmatrix}{y}_{1} , {y}_{2} , \\cdots , {y}_{q}\\end{bmatrix}^{T}$\n\n系统的内部变量：\n描述系统内部每个时刻所处状态的变量 $\\mathbf{x}=\\begin{bmatrix}{x}_{1} , {x}_{2} , \\cdots , {x}_{n}\\end{bmatrix}^{T}$\n\n#### 1. 外部描述\n传递函数\\描述，也称输入-输出描述：将系统看作“黑箱”，只是反映系统外部变量（输入-输入）的因果关系\n\n#### 2. 内部描述\n状态空间\\描述，通常由两个方程表示\n状态方程：微分方程或差分方程的形式，表征输入变量和内部变量的因果关系\n输出方程：代数方程的形式，表征系统内部变量、输入变量、输出变量之间的转换关系\n\n### 二、系统的分类\n\nmermaid\nmindmap\nroot(( 系统的分类 ))\n ((组成))\n ((线性))\n ((非线性))\n ((时间))\n ((时变))\n ((时不变))\n ((阶数))\n ((一阶))\n ((二阶))\n ((高阶))\n ((能量属性))\n ((电气))\n ((机械))\n ((机电))\n ((气动))\n ((液压))\n ((热力))\n ((信息))\n ((白箱))\n ((黑箱))\n ((灰箱))\n\n理论学习中，一般从线性时不变系统\\的简单情况入手\n\n### 三、系统工程\n\n系统 System：相互联系、相互作用、相互依赖、相互制约的若干部分构成的具有特定功能的整体 \n\n要素 Element：构成系统的每个基本单元 \n\n环境 Environment：一个系统的环境是与该系统有关、但不属于该系统的所有对象的集合。\n\n变量\n连续型 C \n二元 B \n整型 I \n\n独立变量（independent variable）：彼此独立的变量。模型中的所有变量并不一定是互相独立的，但是从模型中总可以选出一组互相独立的变量。\n\n相关变量（dependent variable）：其值可由独立变量确定的量。\n\n目标函数：实际问题最优准则的数量描述。目标函数值直接用于评价一个方案的优劣程度\n\n约束条件：定量地描述系统中诸因素之间及系统与环境之间相互联系、相互制约的关系。\n\n 复杂系统 Complex System： 具有多个相互作用的组成部分的系统，这些组成部分的相互作用产生出新的模式、结构或行为。这些模式、结构或行为不能仅通过观察单个组成部分来预测。通常表现出非线性\\、自组织\\、适应性、反馈循环和涌现\\特性。\n\n### 系统的哲学"
    },
    "系统科学": {
      "id": "系统科学",
      "title": "系统科学",
      "category": "0. 基础知识",
      "subcategory": "0. 基础知识",
      "tags": [
        "System",
        "ControlTheory",
        "Philosophy"
      ],
      "aliases": [
        "Systems Science"
      ],
      "terminology": "Systems Science",
      "summary": "Systems Science 系统科学",
      "headings": [
        "一、老三论 (SCI)",
        "系统论 (Systems Theory)",
        "控制论 (Cybernetics)",
        "信息论 (Information Theory)",
        "二、新三论 (DSC)",
        "耗散结构论 (Dissipative Structures Theory)",
        "协同论 (Synergetics)",
        "突变论 (Catastrophe Theory)",
        "三、系统科学整体"
      ],
      "pinned": true,
      "level": null,
      "created": "2024-05-21T15:20:28.000+08:00",
      "updated": "2025-09-29T19:27:28.000+08:00",
      "permalink": "/A2- 控制理论/0. 基础知识/系统科学/",
      "dg_path": "A2- 控制理论/0. 基础知识/系统科学.md",
      "source_path": "src/site/notes/系统科学.md",
      "viewer_markdown_path": "../source-notes/系统科学.md",
      "internal_links": [
        "反馈",
        "系统"
      ],
      "inbound_links": [
        "反馈"
      ],
      "out_of_scope_links": [
        "数理统计",
        "概率论"
      ],
      "missing_links": [
        "信息"
      ],
      "content_excerpt": "Systems Science 系统科学\n\n系统科学是以系统\\为研究对象的基础理论和应用开发的学科组成的学科群。它着重考察各类系统的关系和属性，揭示其活动规律，探讨有关系统的各种理论和方法。系统科学的理论和方法正在从自然科学和工程技术向社会科学广泛转移。\n\n### 一、老三论 (SCI)\n\n老三论是系统科学的早期奠基性理论，主要关注系统的结构、功能和信息处理。\n\n#### 1. 系统论 (Systems Theory)\n“整体大于部分之和”\n\n系统论运用完整性、集中性、等级结构、终极性、逻辑同构等概念，研究适用于一切综合系统或子系统的模式、原则和规律，并力图对其结构和功能进行数学描述。系统强调整体与局部、局部与局部、整体与外部环境之间的有机联系，具有整体性、动态性和目的性三大基本特征。作为一种指导思想，系统论要求把事物当作一个整体或系统来考察，符合马克思主义关于物质世界普遍联系的哲学原理。\n\n#### 2. 控制论 (Cybernetics)\n“反馈是控制的基础”\n\n控制论运用信息\\、反馈\\等概念，通过黑箱系统辩识与功能模拟仿真等方法，研究系统的状态、功能和行为，调节和控制系统稳定地、最优地趋达目标。控制论充分体现了现代科学整体化和综合化的发展趋势，具有十分重要的方法论意义。\n\n#### 3. 信息论 (Information Theory)\n“信息是用来减少不确定性的”\n\n信息论以通信系统的模型为对象，以概率论\\和数理统计\\为工具，从量的方面描述了信息的传输和提取等问题。信息论的研究领域扩大到机器、生物和社会等系统，发展成为一门专门利用数学方法来研究如何计量、提取、变换、传递、存贮和控制各种系统信息的一般规律的科学。\n\n### 二、新三论 (DSC)\n\n新三论是系统科学在非线性、复杂性和自组织方面的发展，主要关注系统在远离平衡态条件下的演化和行为。\n\n#### 1. 耗散结构论 (Dissipative Structures Theory)\n“非平衡是有序之源”\n\n耗散结构论是由比利时物理学家普利高津于 1969 年提出的，它主要研究的是开放系统在远离平衡态条件下的有序性和自组织现象。该理论认为，非平衡是有序之源，系统在非线性相互作用和涨落的影响下，可能从无序状态突变为有序的耗散结构。\n\n#### 2. 协同论 (Synergetics)\n“局部相互作用产生全局协同效应”\n\n协同论由联邦德国理论物理学家赫尔曼·哈肯在 1973 年创立，它关注系统中各个子系统的相互作用与协同作用，以及这些作用如何导致系统整体的有序结构和行为。协同论强调序参量的概念，即系统内部要素协同作用形成的主导因素，它决定了系统从无序到有序的自组织行为。\n\n#### 3. 突变论 (Catastrophe Theory)\n“系统在临界点附近可能经历质的飞跃”\n\n突变论是由比利时科学家托姆在 1972 年创立的，它研究系统在临界点的状态，探讨自然和社会系统中的非连续性突然变化现象。突变论认为，系统的相变可以通过非连续的突变或连续的渐变来实现，相变的方式依赖于相变条件。\n\n### 三、系统科学整体\n\n新三论与老三论相互补充，共同构成了系统科学的理论基础。老三论侧重于系统的结构、功能和信息处理，而新三论则更关注系统的演化、自组织和非线性动力学行为。新三论的发展不仅推动了科学图景的改观，也为多个领域的研究提供了新的视角和方法。"
    },
    "脉冲函数": {
      "id": "脉冲函数",
      "title": "脉冲函数",
      "category": "0. 基础知识",
      "subcategory": "0. 基础知识",
      "tags": [],
      "aliases": [],
      "terminology": "Pulse Function",
      "summary": "Pulse Function\n脉冲函数是一个实际的、物理可实现的信号，它具有有限的持续时间和幅度。\n脉冲函数可以是矩形脉冲、高斯脉冲、梯形脉冲等多种形状，通常用于模拟电子信号、声波等。\n脉冲函数在时间轴上的定义是非零的，并且其幅度和宽度都是有限的。",
      "headings": [],
      "pinned": false,
      "level": null,
      "created": "2024-05-21T15:20:28.650+08:00",
      "updated": "2025-05-02T17:47:14.000+08:00",
      "permalink": "/A2- 控制理论/0. 基础知识/脉冲函数/",
      "dg_path": "A2- 控制理论/0. 基础知识/脉冲函数.md",
      "source_path": "src/site/notes/脉冲函数.md",
      "viewer_markdown_path": "../source-notes/脉冲函数.md",
      "internal_links": [],
      "inbound_links": [
        "信号采样",
        "经典输入信号"
      ],
      "out_of_scope_links": [
        "冲激函数"
      ],
      "missing_links": [],
      "content_excerpt": "Pulse Function\n脉冲函数是一个实际的、物理可实现的信号，它具有有限的持续时间和幅度。\n脉冲函数可以是矩形脉冲、高斯脉冲、梯形脉冲等多种形状，通常用于模拟电子信号、声波等。\n脉冲函数在时间轴上的定义是非零的，并且其幅度和宽度都是有限的。\n\n冲激函数\\是一个理论上的数学工具，而脉冲函数是实际可观测的信号。\n\n冲激函数可以用来简化对脉冲函数的分析，但在实际应用中，我们通常处理的是脉冲函数而不是理想的冲激函数。\n\n$$\\begin{align} \n&\\delta_{\\tau}(t)=\\begin{cases}\n\\dfrac{1}{\\tau}& 0<t<\\tau \\\\ \\\\\n\n0& \\text{其它}\n\\end{cases} \\\\ \\\\\n\n&\\delta(t)=\\lim\\limits_{ \\tau \\to 0 } \\delta_{\\tau}(t)=\\begin{cases}\n1& t=0 \\\\\n0& t\\neq 0\n\\end{cases} \\\\ \\\\\n\n&\\int _{-\\infty}^{+\\infty} \\delta_{\\tau}(t)\\, dt=1\n\\end{align}$$"
    },
    "自动控制系统": {
      "id": "自动控制系统",
      "title": "自动控制系统",
      "category": "0. 基础知识",
      "subcategory": "0. 基础知识",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "(terminology:：Automatic Control System)",
      "headings": [
        "一、基本框架",
        "二、控制的基本机制",
        "三、自动控制系统的分类",
        "按控制的方式：",
        "2.按系统特性：",
        "3.按输入量变化规律：",
        "4.按输入/输出个数",
        "四、基本性能要求：稳、快、准",
        "稳定性",
        "快速性",
        "准确性"
      ],
      "pinned": false,
      "level": 1,
      "created": "2024-05-21T15:20:28.000+08:00",
      "updated": "2025-08-28T21:53:14.000+08:00",
      "permalink": "/A2- 控制理论/0. 基础知识/自动控制系统/",
      "dg_path": "A2- 控制理论/0. 基础知识/自动控制系统. md",
      "source_path": "src/site/notes/自动控制系统.md",
      "viewer_markdown_path": "../source-notes/自动控制系统.md",
      "internal_links": [
        "反馈",
        "系统结构框图"
      ],
      "inbound_links": [
        "反馈",
        "自动控制原理"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "(terminology:：Automatic Control System)\n\n自动控制：有意识的进行人工设计，使得控制过程不需要人的参与，从而自动进行\n\n控制：使受控对象的受控变量产生预期响应\n受控对象：物理系统\n受控变量：受控对象的物理量\n预期响应：预先设定的期望信号，预期系统对输入信号或扰动的理想响应\n系统响应：系统实际输出的变化\n\n### 一、基本框架\n系统结构框图\\\n描述系统平衡时的状态\n平衡态被打破后，应用闭环/反馈的思路来解释如何重新实现平衡\n如果有前馈/顺馈，解释如何有助于维持系统的平衡\n预期输出/参考输入\n控制器：代替人脑 (中的部分功能），进行分析判断决策\n执行器：将控制信号转化为相应动作或操作的硬件装置或组件\n被控对象：要求实现自动工作的机器﹑设备或生产过程 \n被控变量：达到控制目标要求的被控对象的某个工作状态或参数\n[!note] \n注意 因果关系判断控制的过程：明确所要求的是什么（目的，预期，被控对象的被控变量）\n注意：被控对象为实际的物理系统/实体对象\n例如：被控对象为“水箱”（是控制水箱而不是控制水）\n\n### 二、控制的基本机制\n反馈：反馈\\的基本原理是通过不断比较系统输出与期望参考值之间的差异，从而对系统进行修正和调整\n\n顺馈/前馈：利用先验信息对系统期望响应预判\n按扰动补偿：直接抵消系统中的扰动\n按输入补偿：通过调整输入信号来抵消扰动\n\n开环控制：利用执行机构直接控制被控对象，控制器无反馈信息\n闭环控制：存在测量装置组成反馈回路，控制器利用反馈信息\n\n反馈控制：采用负反馈，利用偏差进行控制的过程\n\n扰动：对系统控制产生不利影响的输入信号。除给定信号外，作用在控制系统各环节上的一切会引起输出量变化的因素都叫做扰动\n内扰：系统内部产生的扰动\n外扰：系统外部产生的扰动\n\n### 三、自动控制系统的分类\n#### 1. 按控制的方式：\n开环控制\n闭环控制\n复合控制\n#### 2.按系统特性：\n线性连续控制：微分方程\n线性离散控制：差分方程\n非线性控制：非线性方程\n#### 3.按输入量变化规律：\n恒值控制：调节器\n随动控制：跟踪系统、伺服系统\n程序控制\n\n#### 4.按输入/输出个数\nSISO：单输入单输出系统（单变量系统） \nMIMO：多输入多输出系统（多变量系统）\n\n### 四、基本性能要求：稳、快、准\n#### 1. 稳定性\n系统正常运行的先决条件，由系统结构和参数决定，与外界因素无关。\n被控量偏离期望值的初始偏差应随时间的增长逐渐减小并趋于零。过渡过程，呈现振荡形式，振荡逐渐减弱达到平衡。\n#### 2. 快速性\n动态性能：过渡过程的时间和最大振荡幅度\n#### 3. 准确性\n稳态误差：被控量的稳态值与期望值之间的误差（由于系统结构、外作用形式、非线性因素的影响）"
    },
    "阶跃函数": {
      "id": "阶跃函数",
      "title": "阶跃函数",
      "category": "0. 基础知识",
      "subcategory": "0. 基础知识",
      "tags": [],
      "aliases": [],
      "terminology": "Step function",
      "summary": "Step function\n阶跃函数为有限段分段常数函数的组合",
      "headings": [],
      "pinned": false,
      "level": null,
      "created": "2024-10-06T11:54:26.000+08:00",
      "updated": "2025-09-23T16:38:26.000+08:00",
      "permalink": "/A2- 控制理论/0. 基础知识/阶跃函数/",
      "dg_path": "A2- 控制理论/0. 基础知识/阶跃函数.md",
      "source_path": "src/site/notes/阶跃函数.md",
      "viewer_markdown_path": "../source-notes/阶跃函数.md",
      "internal_links": [],
      "inbound_links": [
        "经典输入信号"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "Step function\n阶跃函数为有限段分段常数函数的组合\n\n$$ f(t)=\n\\begin{cases}\n0,\\quad t<0 \\\\\nR,\\quad t\\geq 0\n\\end{cases}$$\n\n单位阶跃函数 $1(t)$ \n幅值为 R 的阶跃函数 $f (t)=R·1 (t)$\n$t_{0}$ 出现的阶跃函数 $f (t-t_0)=R·1 (t-t_0)$\n\n单位阶跃函数：\n$$u(t)=\\begin{cases}\n0 \\quad t<0\\\\\n1\\quad t\\geq0\n\\end{cases}$$\n\n阶跃响应\nStep response"
    },
    "0°根轨迹绘制规则": {
      "id": "0°根轨迹绘制规则",
      "title": "0°根轨迹绘制规则",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "绘制法则，参考 180°根轨迹绘制法则\\\n### 一、非最小相位系统\n在 s 右半平面具有开环零极点的控制系统为非最小相位系统\\",
      "headings": [
        "一、非最小相位系统",
        "二、根轨迹方程",
        "三、绘制规则",
        "渐近线",
        "在实轴上的分布",
        "起始角和终止角"
      ],
      "pinned": false,
      "level": null,
      "created": "2025-08-02T10:36:26.000+08:00",
      "updated": "2025-11-24T18:31:35.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/0°根轨迹绘制规则/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/0°根轨迹绘制规则.md",
      "source_path": "src/site/notes/0°根轨迹绘制规则.md",
      "viewer_markdown_path": "../source-notes/0°根轨迹绘制规则.md",
      "internal_links": [
        "180°根轨迹绘制法则",
        "非最小相位系统"
      ],
      "inbound_links": [
        "经典控制理论"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "绘制法则，参考 180°根轨迹绘制法则\\\n### 一、非最小相位系统\n在 s 右半平面具有开环零极点的控制系统为非最小相位系统\\\n\n非最小相位系统来源：\n非最小相位系统中包含 𝑠 最高次幂的系数为负的因子\n （飞机、导弹本身特性所产生的, 或在系统结构图变换过程中所产生的）\n控制系统中包含有正反馈内回路 \n （由于某种性能指标要求, 使得在复杂的控制系统设计中, 必须包含正反馈内回路）\n\n### 二、根轨迹方程\n特征方程：$1-G(s)H(s)=0$\n根轨迹方程：$G(s)H(s)=1$\n[!important] 注意\n上面的只是针对单位正反馈系统的，单位负反馈还是和之前一样\n\n### 三、绘制规则\n只有以下几点与 180°根轨迹绘制法则\\不同，其余均一致\n\n#### 渐近线\n$$\\begin{align}\n\\varphi_{a}= \\dfrac{2k\\pi}{n-m}\n\\end{align}$$\n\n#### 在实轴上的分布\n右侧实轴上的开环零、极点数目之和为偶数，则所在的区域是根轨迹\n（右侧没有零极点，也是根轨迹的部分！）\n\n#### 起始角和终止角\n\n$$\\begin{align}\n\\theta_{p_{i}}=2k\\pi+ \\sum\\limits_{j=1}^{m} \\varphi_{z_{j}p_{i}}-\\sum\\limits_{j=1, j \\neq i}^{n} \\theta_{p_{j}p_{i}}\n\\end{align}$$\n\n$$\\begin{align}\n\\varphi_{z_{i}}=2k\\pi-(\\sum\\limits_{j=1,j\\neq i}^{m} \\varphi_{z_{j}z_{i}}-\\sum\\limits_{j=1}^{n} \\theta_{p_{j}z_{i}}) \n\\end{align}$$"
    },
    "经典环节的传递函数": {
      "id": "经典环节的传递函数",
      "title": "经典环节的传递函数",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "复杂传递函数\\由经典输入信号\\的传递函数构成，其行为也由由基本环节的行为决定",
      "headings": [
        "基本环节",
        "比例/放大环节",
        "纯积分环节",
        "纯微分环节",
        "一阶惯性环节",
        "一阶微分环节",
        "二阶振荡环节",
        "二阶微分环节",
        "延迟环节",
        "对称关系"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-04-16T13:01:27.000+08:00",
      "updated": "2025-07-23T18:02:54.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/1. 5 经典环节的传递函数/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/1. 5 经典环节的传递函数. md",
      "source_path": "src/site/notes/经典环节的传递函数.md",
      "viewer_markdown_path": "../source-notes/经典环节的传递函数.md",
      "internal_links": [
        "传递函数",
        "欠阻尼二阶系统动态分析",
        "稳定裕度",
        "经典输入信号",
        "非最小相位系统",
        "频带宽度"
      ],
      "inbound_links": [
        "Bode 图",
        "一阶系统的时域分析",
        "传递函数",
        "开环频率特性",
        "经典控制理论",
        "非最小相位系统"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "复杂传递函数\\由经典输入信号\\的传递函数构成，其行为也由由基本环节的行为决定\n\nmermaid\ngraph LR\n经典环节 ----> 比例环节 & 积分环节 & 1[微分环节] & 二阶振荡环节 & 延迟环节\n\n### 基本环节\n#### 1. 比例/放大环节\n$$\\begin{align}\nG(s)=K \\quad {\\color{red}\\Leftrightarrow} \\quad G(j\\omega)=K+j0 \\quad \\begin{cases}\n & |G(j\\omega)|=K\\\\ \n& L(\\omega )=20\\lg K \\\\\n & \\phi(\\omega )=0^{\\circ}\n\\end{cases}\n\\end{align}$$\n\n#### 2. 纯积分环节\n\n$$\\begin{align}\nG(s)=\\dfrac{1}{s} \\quad {\\color{red}\\Leftrightarrow} \\quad G(j\\omega)=\\dfrac{1}{j\\omega}=0-j \\dfrac{1}{\\omega} \\quad \\begin{cases}\n &|G(j\\omega )|=\\dfrac{1}{\\omega } \\\\\n& L(\\omega)=-20\\lg \\omega \\\\\n & \\phi(\\omega )=-90^{\\circ}\n\\end{cases}\n\\end{align}$$\n\n#### 3. 纯微分环节\n$$\\begin{align}\nG(s)=s\\quad {\\color{red}\\Leftrightarrow} \\quad G(j\\omega)=j\\omega=0+j\\omega\n\\end{align}$$\n\n$$\\begin{align} \n& |G_{j\\omega }|=\\omega \\\\ \n& L(\\omega )=20\\lg \\omega \\\\\n & \\phi(\\omega )=90^{\\circ}\n\\end{align}$$\n\n#### 4. 一阶惯性环节\n$$\\begin{align}\nG(s)=\\dfrac{1}{T s+1} \\quad {\\color{red}\\Leftrightarrow} \\quad\nG(j\\omega)=\\dfrac{1}{1+j\\omega T}=\\dfrac{1}{1+T^{2}\\omega^{2}}-j \\dfrac{\\omega T}{1+T^{2}\\omega^{2}}\n\\end{align}$$\n\n$$\\begin{align}\n |G(j\\omega )|&= \\dfrac{1}{\\sqrt{ 1+\\omega^{2}T^{2} }} \\\\\n L(\\omega )&= 20\\lg |G(j\\omega )| \\\\\n & =-10\\lg(1+\\omega^{2}T^{2}) \\\\\n & \\approx 0 (\\omega \\ll \\dfrac{1}{T} 低频渐近线) \\\\\n&\\approx-20\\lg \\omega +20\\lg \\dfrac{1}{T}\\quad (\\omega \\gg \\dfrac{1}{T} 高频特性) \\\\\n \\phi(\\omega )&=-\\arctan \\omega T\\quad (0^{\\circ},-90^{\\circ})\n\\end{align}$$\n\n转折频率/交接频率： $\\omega=\\dfrac{1}{T}$ \n对数幅频特性：曲线斜率为 $-20dB/dec$ 渐近线\n对数相频特性：对应 $-45^{\\circ}$ 转折点\n\n带宽频率： $\\omega_{b}=\\dfrac{1}{T}$，与单位阶跃响应速度成正比\n\n#### 5. 一阶微分环节\n$$\\begin{align}\nG(s)=\\tau s+1 \\quad {\\color{red}\\Leftrightarrow} \\quad G(j\\omega)=1+j\\omega \\tau\n\\end{align}$$\n\n$$\\begin{align}\n|G(j\\omega )|&=\\sqrt{ 1+\\omega^{2}\\tau^{2} } \\\\\nL(\\omega )&=20\\lg|G(j\\omega )| \\\\\n&=10\\lg(1+\\omega^{2}\\tau^{2}) \\\\\n&\\approx 20\\lg(\\omega )-20lg(\\dfrac{1}{\\tau})\\quad (\\omega \\gg \\dfrac{1}{\\tau}高频特性) \\\\\n\\phi(\\omega )&=\\arctan(\\omega \\tau)\\quad (0^{\\circ},90^{\\circ})\n\\end{align}$$\n\n转折频率/交接频率 $\\omega=\\dfrac{1}{\\tau}$ \n对数幅频特性：曲线斜率为 $20dB/dec$ 渐近线\n对数相频特性：对应 $45^{\\circ}$ 转折点\n\n#### 6. 二阶振荡环节\n开环传递函数：$G(s)=\\dfrac{\\omega_{n}^{2}}{s(s+2\\zeta \\omega_{n})}$\n自然振荡频率：$\\omega_{n}$\n欠阻尼二阶系统动态分析\\：$\\omega_{d}=\\omega_{n}\\sqrt{ 1-\\zeta^{2} }$\n\n$G(s)=\\dfrac{1}{T^{2}s^{2}+2T \\zeta s+1}= \\dfrac{1}{(\\dfrac{s}{\\omega_{n}})^{2}+2\\zeta(\\dfrac{s}{\\omega_{n}})+1}$\n$G(j\\omega)=\\dfrac{1}{1- \\dfrac{\\omega^{2}}{\\omega_{n}^{2}}+\\df"
    },
    "传递函数": {
      "id": "传递函数",
      "title": "传递函数",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [],
      "aliases": [],
      "terminology": "Transform Fuction",
      "summary": "Transform Fuction",
      "headings": [
        "一、传递函数标准形式",
        "首 1 标准型",
        "尾 1 标准型",
        "二、极点与零点",
        "三、传递函数的计算",
        "3.1 基本传函",
        "3.2 求传递函数的方法",
        "四、时间响应",
        "五、经典环节的传递函数",
        "RLC 电路",
        "例题",
        "六、非零初始条件的传递函数",
        "基本流程",
        "例题"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-10-16T12:50:55.000+08:00",
      "updated": "2026-01-03T16:50:26.100+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/1.1 传递函数/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/1.1 传递函数.md",
      "source_path": "src/site/notes/传递函数.md",
      "viewer_markdown_path": "../source-notes/传递函数.md",
      "internal_links": [
        "信号流图",
        "时间常数",
        "根轨迹法基础",
        "模态",
        "系统结构框图",
        "线性时不变系统",
        "经典控制理论",
        "经典环节的传递函数",
        "经典输入信号",
        "零极点"
      ],
      "inbound_links": [
        "Nyquist图",
        "传递函数矩阵",
        "信号流图",
        "校正环节的设计",
        "根轨迹法基础",
        "状态空间表达式的建立",
        "系统",
        "系统结构框图",
        "线性反馈系统的基本结构",
        "线性系统稳定性分析",
        "经典控制理论",
        "经典环节的传递函数",
        "脉冲传递函数",
        "零极点",
        "非最小相位系统",
        "频域稳定判据",
        "频率特性"
      ],
      "out_of_scope_links": [
        "拉普拉斯变换",
        "电路元件"
      ],
      "missing_links": [],
      "content_excerpt": "Transform Fuction\n\n复变量的有理分式 函数\n使用系统参数表示输出量与输入量之间关系的表达式\n只取决于系统或元件的结构与参数，表征了系统本身的动态特性\n输出（果）= 输入（因）\n与微分方程对应 $s \\leftrightarrow \\dfrac{\\mathrm{d} }{\\mathrm{d} t}$ 一个 $s$ 就是一个微分算子\n线性时不变系统\\中，定义为：零初始条件下，系统输出量与输入量的拉普拉斯变换\\之比\n\n### 一、传递函数标准形式\n#### 1. 首 1 标准型\n\n零极点形式，常见于根轨迹法基础\\：\n\n$$\\begin{align}\nG(s)&=\\frac{b_{0}(s-z_{1})(s-z_{2})\\cdots(s-z_{m})}{a_{0}(s-p_{1})(s-p_{2})\\cdots(s-p_{n})} =K^{}\\frac{\\prod\\limits_{i=1}^{m}(s-z_{i}) }{\\prod\\limits_{j=1}^{n}(s-p_{j})}\n\\end{align}$$\n$K^{}= \\dfrac{b_{0}}{a_{0}}$ 为根轨迹增益\n\n#### 2. 尾 1 标准型\n\n常见于经典控制理论#四、频域分析法\\\n\n$$\n\\begin{align}\nG(s)=\\dfrac{K \\prod\\limits_{i=1}^{m_{1}}(\\tau_{i}s+1)\\prod\\limits_{k=1}^{m_{2}}(\\tau_{k}^{2}s^{2}+2\\zeta_{k}\\tau_{k}s+1)}{s^{v}\\prod\\limits_{j=1}^{n_{1}}(T_{j}s+1)\\prod\\limits_{l=1}^{n_{2}}(T_{l}^{2}s^{2}+2\\zeta_{l}T_{l}s+1)}\n\\end{align}\n$$\n$\\tau\\quad T$ 为时间常数\\\n$K$ 为传递函数系数/系统的增益\n传递函数分母为特征方程\n\n### 二、极点与零点\n\n极点：分母多项式的解 ×，特征方程的根（特征根），可以受输入函数的激发，在输出响应中形成自由运动的模态\\，如果有极点 $p_{1},p_{2}$，则有模态：$e^{ p_{1}t }$ $e^{ p_{2} t}$\n\n零点：分子多项式的解 O， 不形成自由运动的模态，但是影响各模态在响应中所占的比重，影响响应曲线的形状\n[!note] 注意\n零点、极点、原点三者之间的距离共同影响响应曲线 （零极点\\ ）\n实际上，非零初始条件不会影响系统的传递函数，非零的输入与实际输入量满足叠加原理\n\n### 三、传递函数的计算\n\n经典输入信号\\\n\n#### 3.1 基本传函\n前向通路传递函数：输入端到输出端的通路的传递函数的乘积 （看输入和输出信号）\n开环传递函数：打开主反馈回路，主反馈信号与误差信号之比 （与输入信号无关，由系统本身结构决定）\n\n$$\\begin{align}\nG_{o}(S)=\\dfrac{B(s)}{E(s)}=G_c(s)G_{p}(s)H(s)\n\\end{align}$$\n闭环传递函数：\n\n$$闭环传递函数=\\dfrac{前向通路传递函数}{1+开环传递函数}$$\n误差传递函数：误差信号与输入信号之比\n\n$$\\begin{align}\n\\dfrac{C(s)}{R(s)}= \\dfrac{G_{c}(s)G_{p}(s)}{1+G_{o}(s)}\n\\end{align}$$\n\n$$\\begin{align}\n\\dfrac{C(s)}{N(s)}=\\dfrac{G_{p}(s)}{1+G_{o}(s)}\n\\end{align}$$\n\n$$\\begin{align}\n\\dfrac{E(s)}{N(s)}= \\dfrac{-G_{p}(s)H(s)}{1+G_{o}(s)}\n\\end{align}$$\n\n#### 3.2 求传递函数的方法\n系统结构框图\\\n信号流图\\\n\n### 四、时间响应\n已知传递函数 $G(s)$，求给定输入 $I(s)$ 下系统的输出 $O(s)$ 最终输出 $o(+\\infty)$\n\n一般给定输入为经典输入信号\\，求时间响应：主要使用拉普拉斯变换#6.极限性质\\\n\n$$\\begin{align}\nO(s)=G(s)I(s)\\quad o(+\\infty)=\\lim\\limits_{ s \\to 0 }sG(s)I(s)\n\\end{align}$$\n\n### 五、经典环节的传递函数\n经典环节的传递函数\\\n\n#### RLC 电路\n\n电路元件\\的传递函数\n电阻： $\\dfrac{U(s)}{I(s)}=R$\n电容： $\\dfrac{U(s)}{I(s)}= \\dfrac{1}{Cs}$\n电感： $\\dfrac{U(s)}{I(s)}=Ls$\n\n复数阻抗法：列写网络的微分方程时，由于流过电流相同。可以直接将输出电压和输入电压的比值，直接列写出传函，再拉普拉斯逆变换，求时域的微分关系\n\n#### 例题\n并联/串联电路的复数阻抗类似于求电阻 \n类似于分压原理求最后传函\n\n$$\\begin{align}\n\\dfrac{U_{o}(s)}{U_{i}(s)}&= \\dfrac{R_{2}+ \\dfrac{1}{C_{2}s}}{\\dfrac{R_{1} \\dfrac{1}{C_{1}s}}{R_{1}+ \\dfrac{1}{C_{1}s}}+R_{2}+ \\dfrac{1}{C_{2}s}}\n\\end{align}$$\n\n### 六、非零初始条件的传递函数\n#### 基本流程\n先根据系统结构，得到零初始条件下的传递函数\n根据拉普拉斯逆变换，写出传递函数对应的微分方程（注意“输出=输入”，输出在左，输入"
    },
    "系统结构框图": {
      "id": "系统结构框图",
      "title": "系统结构框图",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [
        "Graph"
      ],
      "aliases": [],
      "terminology": "System  Diagram",
      "summary": "System Diagram\n 求传递函数\\方法之一，系统原理图和数学方程的结合。\n### 一、基本单元\n信号线：箭头表示信号的流向。直线旁标记信号的时间函数或象函数\n引出点/测量点：表示信号引出或测量的位置。从同一位置引出的信号在数值和性质上完全相同\n比较点/综合点：表示对两个及以上的信号进行加减运算\n方框/环节：对信号进行的数学变换",
      "headings": [
        "一、基本单元",
        "二、等效变换及化简",
        "基本连接方式",
        "常用变形",
        "三、传递函数的简化"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-09-04T11:59:55.000+08:00",
      "updated": "2025-10-28T16:20:42.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/1.2 系统结构框图/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/1.2 系统结构框图.md",
      "source_path": "src/site/notes/系统结构框图.md",
      "viewer_markdown_path": "../source-notes/系统结构框图.md",
      "internal_links": [
        "传递函数"
      ],
      "inbound_links": [
        "传递函数",
        "信号流图",
        "状态空间表达式的建立",
        "经典控制理论",
        "自动控制系统"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "System Diagram\n 求传递函数\\方法之一，系统原理图和数学方程的结合。\n### 一、基本单元\n信号线：箭头表示信号的流向。直线旁标记信号的时间函数或象函数\n引出点/测量点：表示信号引出或测量的位置。从同一位置引出的信号在数值和性质上完全相同\n比较点/综合点：表示对两个及以上的信号进行加减运算\n方框/环节：对信号进行的数学变换\n\n### 二、等效变换及化简\n#### 1. 基本连接方式\n串联\n$$\\begin{align}\nG(s)=G_{1}(s)G_{2}(s)\n\\end{align}$$\n\n并联\n$$\\begin{align}\nG(s)=G_{1}(s)\\pm G_{2}(s)\n\\end{align}$$\n\n反馈连接\n$$\\begin{align}\nG(s)[R(s)\\pm H(s)C(s)]=\\frac{G(s)}{1\\mp G(s)H(s)}R(s)\n\\end{align}$$\n\n#### 2. 常用变形\n比较点的相加\n比较点前移、后移\n引出点前移、后移\n[!important] 注意事项\n利用结构图简化求传递函数时，不能跨比较点、引出点来直接简化\n先利用比较点、引出点的改变，化为简单的串、并、反馈结构\n再对传递函数化简\n\n### 三、传递函数的简化\n\n$$\\begin{align}\n & [R(s)-C(s)H(s)]G(s)=C(s) \\\\\n & R(s)G(s)=C(s)[1+H(s)G(s)] \\\\\n & \\frac{C(s)}{R(s)}=\\frac{G(s)}{1+H(s)G(s)}\n\\end{align}$$\n\n单位负反馈\n\n$$\\begin{align}\n\\frac{G(s)}{1+G(s)}=\\dfrac{\\dfrac{A}{B}}{1+\\dfrac{A}{B}}=\\frac{A}{A+B}\n\\end{align}$$\n负反馈\n$$\\begin{align}\n\\frac{G(s)}{1+G(s)}=\\dfrac{\\dfrac{A}{B}}{1+\\dfrac{A}{B}C}=\\frac{A}{AC+B}\n\\end{align}$$\n\n传递函数\\\n\n串联\n\n并联\n\n反馈\n\n$$\\begin{align}\n & [R(s)-C(s)H(s)]G(s)=C(s) \\\\\n & R(s)G(s)=C(s)[1+H(s)G(s)] \\\\\n & \\frac{C(s)}{R(s)}=\\frac{G(s)}{1+H(s)G(s)}\n\\end{align}$$\n单位负反馈\n\n$$\\begin{align}\n\\frac{G(s)}{1+G(s)}=\\dfrac{\\dfrac{A}{B}}{1+\\dfrac{A}{B}}=\\frac{A}{A+B}\n\\end{align}$$\n负反馈\n\n$$\\begin{align}\n\\frac{G(s)}{1+G(s)}=\\dfrac{\\dfrac{A}{B}}{1+\\dfrac{A}{B}C}=\\frac{A}{AC+B}\n\\end{align}$$"
    },
    "信号流图": {
      "id": "信号流图",
      "title": "信号流图",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [
        "Graph"
      ],
      "aliases": [],
      "terminology": null,
      "summary": "可由系统结构框图\\得到，求传递函数\\的方法\n[!important] 注意\n根据系统结构图绘制信号流图时：\n要明确系统的输入和输出\n一定要区分引出点、比较点\n（多拉出一个信号，增益为 1 即可）\n虽然前后的信号表面上相同，但实质是不同的信号，应用公式计算时会有影响\n明确前向通路和回路\n不要漏也不要多\n 注意符号",
      "headings": [
        "基本结构",
        "基本术语",
        "梅森增益",
        "利用梅森增益求传递函数",
        "注意的点"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-10-09T12:02:37.790+08:00",
      "updated": "2025-08-28T21:53:14.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/1.3 信号流图/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/1.3 信号流图.md",
      "source_path": "src/site/notes/信号流图.md",
      "viewer_markdown_path": "../source-notes/信号流图.md",
      "internal_links": [
        "传递函数",
        "系统结构框图"
      ],
      "inbound_links": [
        "传递函数",
        "经典控制理论"
      ],
      "out_of_scope_links": [
        "克拉默法则"
      ],
      "missing_links": [],
      "content_excerpt": "可由系统结构框图\\得到，求传递函数\\的方法\n[!important] 注意\n根据系统结构图绘制信号流图时：\n要明确系统的输入和输出\n一定要区分引出点、比较点\n（多拉出一个信号，增益为 1 即可）\n虽然前后的信号表面上相同，但实质是不同的信号，应用公式计算时会有影响\n明确前向通路和回路\n不要漏也不要多\n 注意符号\n\n### 基本结构\n节点 标志系统的 变量 o\n支路 相当于 乘法器 写传递函数\n箭头单向传递 表征 因果关系\n\n### 基本术语\n源节点： source input node\n陷节点： sink output node\n混合节点： mixed node\n\n前向通路： 信号从输入节点到输出节点的通路，传递时，每个节点只通过一次\n\n前向通路增益：前向通路中各前向支路增益乘积\n\n回路：起点和终点在同一节点，并且信号通过每一节点不多于一次的闭合通路\n\n回路增益：回路中所有支路增益之乘积\n[!note] \n抓住定义，有顺序的找\n不要多找或少找\n\n不接触回路：回路之间没有公共节点的回路\n\n### 梅森增益\nMason \n按克拉默法则\\求解线性方程组时，将解的分子多项式及分母多项式与信号流图巧妙结合的结果\n直接求取从源节点到陷节点的传递函数\\\n\n梅森增益公式：\n$$P=\\dfrac{1}{\\Delta}\\sum\\limits_{k=1}^{n}p_{k}\\Delta_{k}$$\n\nP 为源节点到陷节点的传递函数（总增益）\n\n流图特征式： $\\Delta$\n\n$$\\begin{align}\n\\Delta=1-\\sum L_{a}+\\sum L_{b}L_{c}-\\sum L_{d}L_{e}L_{f}+\\cdots\n\\end{align}$$\n$\\sum L_{a}$ 所有单独回路增益之和\n$\\sum L_{b}L_{c}$ 所有互不相接触的单独回路中，每次取其中两个回路的回路增益乘积之和\n$\\sum L_{d}L_{e}L_{f}$ 所有互不相接触的单独回路中，每次取其中三个回路的回路增益乘积之和\n\n前向通路增益： $p_{k}$ 从源节点到陷节点的第 $k$ 条前向通路增益\n流图余因子式：$\\Delta_{k}$ 流图特征式中除去与第 $k$ 条前向通路相接触的回路增益项之后的余项式\n\n### 利用梅森增益求传递函数\n先找前向通路：确定几条，以及对应的增益 $P_{n}$\n再找独立回路：确定回路增益\n之后求流图特征式\n最后求总的传递函数\n\n### 注意的点\n找前向通路时： 一定要区分引出点、比较点前后的信号\n[!note] \n抓住定义，不要被实际题目迷惑多找或者少找了\n像上面的图，红色的也是一条前向通路\n一共 4 条\n\n而这只有一条前向通路"
    },
    "经典输入信号": {
      "id": "经典输入信号",
      "title": "经典输入信号",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [],
      "aliases": [],
      "terminology": "Classical Input Signal",
      "summary": "Classical Input Signal 特殊的信号\\",
      "headings": [
        "一、经典输入信号的特性",
        "二、基本输入信号类型",
        "单位脉冲信号",
        "单位阶跃信号",
        "单位斜坡信号",
        "单位加速度信号",
        "正弦信号"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-10-08T18:34:47.000+08:00",
      "updated": "2025-09-18T21:26:22.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/1.4 经典输入信号/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/1.4 经典输入信号.md",
      "source_path": "src/site/notes/经典输入信号.md",
      "viewer_markdown_path": "../source-notes/经典输入信号.md",
      "internal_links": [
        "经典控制理论",
        "脉冲函数",
        "阶跃函数"
      ],
      "inbound_links": [
        "传递函数",
        "最小拍控制器",
        "线性定常状态方程的解",
        "线性系统稳态误差计算",
        "经典控制理论",
        "经典环节的传递函数",
        "自动控制原理"
      ],
      "out_of_scope_links": [
        "冲激函数",
        "拉普拉斯变换"
      ],
      "missing_links": [
        "信号"
      ],
      "content_excerpt": "Classical Input Signal 特殊的信号\\\n\n### 一、经典输入信号的特性\n反映系统在某一方面的性质，函数形式简单，易于产生，方便实验和测试，且拉普拉斯变换\\具有简单的形式\n现场或实验易于实现 \n控制系统的性能代表实际条件下的性能 \n数学表达简单，利于理论计算\n系统对输入信号导数的响应，等于系统对该输入信号响应的导数\n系统对输入信号积分的响应，等于系统对该输入信号响应的积分，积分常数由零输入初始条件决定\n[!note] 例\n已知系统的单位阶跃响应（时域）\n直接对单位阶跃响应 求导 就为 单位脉冲响应\n而 单位脉冲响应(时域) 的拉氏反变换就为 传递函数\n\n### 二、基本输入信号类型\n\n#### 1. 单位脉冲信号\n脉冲函数\\极限为冲激函数\\，考察对扰动的调节能力、对高频冲激的抑制能力\n$$\n\\delta(t)=\\lim\\limits_{ t_{0} \\to 0 } \\frac{1}{t_{0}}[1(t)-1(t-t_{0})]\\quad\\quad \\mathscr{L}[\\delta(t)]=1\n$$\n\n#### 2. 单位阶跃信号\n阶跃函数\\考察对信号的跟踪能力\n $$1(t)=\\begin{cases}\n0,\\quad t<0 \\\\\n1,\\quad t\\geq 0\n\\end{cases} \\quad \\quad \\mathscr{L}[1(t)]=\\dfrac{1}{s}$$\n\n#### 3. 单位斜坡信号\n$$f(t)=\\begin{cases}\n0,\\quad t<0 \\\\\nt,\\quad t\\geq 0\n\\end{cases}\\quad \\quad \\mathscr{L}[t]=\\dfrac{1}{s^{2}}$$\n\n#### 4. 单位加速度信号\n$$f(t)=\\frac{1}{2}t^{2}\\quad \\quad \\mathscr{L}\\left[ \\dfrac{1}{2}t^{2} \\right]=\\dfrac{1}{s^{3}}$$\n\n#### 5. 正弦信号\n正弦信号一般用于经典控制理论#四、频域分析法\\，考察对周期变化信号的跟踪能力\n$$\nf(t)=A\\sin (\\omega t-\\phi)\n$$\n具有无穷阶的导数\n包含位置、速度和加速度等各种作用 \n控制系统各个信号均可分解为许多不同频率的正弦信号 \n$$\\begin{gathered}\n\\mathscr{L}[A\\sin \\omega t]=A \\frac{\\omega}{s^{2}+\\omega^{2}} \\\\\n\\mathscr{L}[A\\cos \\omega t]=A \\frac{s}{s^{2}+\\omega^{2}} \\\\ \n\\mathscr{L}[e^{ -bt }\\sin at]=\\frac{a}{(s+b)^{2}+a^{2}} \\\\\n\\mathscr{L}[e^{ -bt }\\cos at]=\\frac{s+b}{(s+b)^{2}+a^{2}} \\\\\n\\end{gathered}$$"
    },
    "180°根轨迹绘制法则": {
      "id": "180°根轨迹绘制法则",
      "title": "180°根轨迹绘制法则",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "常规根轨迹\n[!note] \n开环传函的其他参数变化都可采用，下面以根轨迹增益 $K^{}$变化为讨论前提",
      "headings": [
        "起点和终点",
        "分支数、对称性、连续性",
        "渐近线",
        "在实轴上的分布",
        "分离点和分离角",
        "起始角和终止角",
        "与虚轴的交点",
        "极点之和",
        "特殊的轨迹"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-04-16T13:01:27.000+08:00",
      "updated": "2025-09-29T19:26:42.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/80°根轨迹绘制法则/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/80°根轨迹绘制法则.md",
      "source_path": "src/site/notes/180°根轨迹绘制法则.md",
      "viewer_markdown_path": "../source-notes/180°根轨迹绘制法则.md",
      "internal_links": [
        "零极点"
      ],
      "inbound_links": [
        "0°根轨迹绘制规则",
        "广义根轨迹",
        "经典控制理论"
      ],
      "out_of_scope_links": [
        "复数"
      ],
      "missing_links": [],
      "content_excerpt": "常规根轨迹\n[!note] \n开环传函的其他参数变化都可采用，下面以根轨迹增益 $K^{}$变化为讨论前提\n\n$$\\begin{align}\nK^{} \\dfrac{\\prod\\limits_{j=1}^{m}(s-z_{j})}{\\prod\\limits_{i=1}^{n}(s-p_{i})}=-1\n\\end{align}$$\n\n闭环特征方程：$1+G(s)H(s)=0$ (就是 1+开环传递函数！)\n根轨迹方程：$G(s)H(s)=-1$\n\n### 1. 起点和终点\n根轨迹起于开环极点，终于开环零点，如果零点数小于极点数，则必有无穷远点为终点\n\n### 2. 分支数、对称性、连续性\n分支数=$Max\\left\\{m,n \\right\\}$\nm：开环有限零点数\nn ：开环有限极点数\n根轨迹均连续并且对称于实轴\n\n### 3. 渐近线\n$n>m$ 时，有 $n-m$ 条根轨迹分支沿着与实轴夹角 $\\varphi_{a}$、交点为 $\\sigma_{a}$ 的一组渐近线趋向无穷远处：\n\n$$\\begin{align}\n\\varphi_{a}= \\dfrac{(2k+1)\\pi}{n-m} \\quad \\quad \\sigma_{a}=\\dfrac{\\sum\\limits_{i=1}^{n}p_{i}-\\sum\\limits_{j=1}^{m}z_{j} }{n-m}\n\\end{align}$$\n与实轴的交点： （极点之和-零点之和）/根轨迹分支数\n与实轴的夹角：根轨迹分支数平分 360°\n\n### 4. 在实轴上的分布\n实轴上某一区域，若其右边开环实数零、极点个数之和为奇数，则该区域必是根轨迹\n{ #2fb7cb}\n[!important] 注意\n只是判断在实轴上的分布\n如果发现右边零极点个数之和不为奇数的实轴之上有根轨迹，不要惊讶\n### 4. 分离点和分离角\n\n分离点：两条或两条以上根轨迹分支在s 平面上相遇又立即分开的点：\n\n$$\\begin{align}\n\\sum\\limits_{i=1}^{n} \\dfrac{1}{d-p_{i}}=\\sum\\limits_{j=1}^{m} \\dfrac{1}{d-z_{j}}\n\\end{align}$$\n\n如果无有限开环零点:\n\n$$\\begin{align}\n\\sum\\limits_{i=1}^{n} \\dfrac{1}{d-p_{i}}=0\n\\end{align}$$\n\n意味着有重根：\n$$\\begin{align}\n & G_{0}(s)= \\dfrac{N(s)}{D(s)}=-1 \\\\\n & N'(s)D(s)-N(s)D'(s)=0\n\\end{align}$$\n\n分离角：根轨迹进入分离点的切线方向与离开分离点的切线方向之间的夹角（$l$ 为进入分离点的分支数）\n$$\\begin{align}\n\\theta_{d} = \\dfrac{1}{l} (2k+1)\\pi\n\\end{align}$$\n\n根轨迹在实轴上汇合分离，满足“上下对称原则”及 “周角等分原则”（分离角：分支数平分 360°）\n\n### 6. 起始角和终止角\n一般针对在实轴之上的零极点\\（有虚部的）为了画得更精细\n\n起始角：离开开环复数极点的切线与正实轴的夹角\n$$\\begin{align}\n\\theta_{p_{i}}=(2k+1)\\pi+ \\sum\\limits_{j=1}^{m} \\varphi_{z_{j}p_{i}}-\\sum\\limits_{j=1,j \\neq i}^{n} \\theta_{p_{j}p_{i}}\n\\end{align}$$\n\n终止角：进入开环复数零点的切线与正实轴的夹角\n$$\\begin{align}\n\\varphi_{z_{i}}=(2k+1)\\pi-(\\sum\\limits_{j=1,j\\neq i}^{m} \\varphi_{z_{j}z_{i}}-\\sum\\limits_{j=1}^{n} \\theta_{p_{j}z_{i}}) \n\\end{align}$$\n\n本质是根据相角条件计算（开环复数零极点也在根轨迹上，取极限，代点计算）\n$$\\begin{align}\n & \\sum\\limits_{j=1}^{m}\\angle(s-z_{j})-\\sum\\limits_{i=1}^{n}\\angle(s-p_{i})=(2k+1)\\pi\n\\end{align}$$\n\n### 7. 与虚轴的交点\n方法一：利用Routh表，出现全零行，结合辅助方程\n方法二：闭环特征方程，代入纯虚数 设根为 $j\\omega$，利用复数\\，求解\n\n$$\\begin{align}\n1+G(j\\omega )H(j\\omega )=0\n\\end{align}$$\n\n### 8. 极点之和\n闭环极点之和等于开环极点之和，且为常数\n根轨迹重心：当根轨迹增益 $Ｋ^{}$ 变化，某些闭环极点在 $s$ 平面上向左移动时，则必有另一些极点向右移动\n\n### 特殊的轨迹\n如果为圆，需要简单的证明：一般是求闭环特征方程的根，取出实部和虚部，再证明根的实部和虚部满足圆的方程（注意参数的范围）\n\n例子：证明根轨迹是圆的一部分，特征方程：\n\n$$\\begin{align}\nD(s)=(1+K^{})s^{2}+(2+3K^{})s+3=0\n\\end{align}$$\n\n设根为 $s=\\sigma\\pm j\\omega$\n\n$$\\begin{cases}\ns_{1}+s_{2}=2\\sigma=- \\dfrac{2+3K^{}}{1+K^{}} \\\\ \\\\\n\ns_{1}s_{2}=\\sigma^{2}+\\omega^{2}=\\dfrac{3}{1+K^{}}\n\\end{cases}$$\n\n解得：\n$$"
    },
    "Bode 图": {
      "id": "Bode 图",
      "title": "Bode 图",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [
        "Graph"
      ],
      "aliases": [],
      "terminology": "Bode Plot",
      "summary": "Bode Plot 对数频率特性图\n一种将系统的频率响应以对数坐标表示的图形工具，用于描述传递函数 $G(s)$ 在 $s=j\\omega$ 时的性质，便于进行频域分析与控制系统设计。\n横坐标：频率的对数分度 $\\lg \\omega$ $rad / s$\n纵坐标： 频率特性\\\n幅频特性：$L(\\omega)=20\\lg |G(j\\omega)|$ 单位： 分贝\\ 显示增益随频率变化的趋势\n相频特性：$\\phi(\\omega)=\\angle G(j\\omega)$ 单位：$度^",
      "headings": [
        "基本画法",
        "画渐近特性曲线",
        "Bode 图的增补",
        "低频段初始角度补画",
        "不连续相位补画",
        "对数幅频渐近特性"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-05-21T15:20:27.000+08:00",
      "updated": "2025-09-26T12:08:20.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/Bode图/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/Bode图.md",
      "source_path": "src/site/notes/Bode 图.md",
      "viewer_markdown_path": "../source-notes/Bode 图.md",
      "internal_links": [
        "Nyquist图",
        "经典环节的传递函数",
        "频率特性"
      ],
      "inbound_links": [
        "开环频率特性",
        "稳定裕度",
        "经典控制理论",
        "非最小相位系统",
        "频域稳定判据"
      ],
      "out_of_scope_links": [],
      "missing_links": [
        "分贝"
      ],
      "content_excerpt": "Bode Plot 对数频率特性图\n一种将系统的频率响应以对数坐标表示的图形工具，用于描述传递函数 $G(s)$ 在 $s=j\\omega$ 时的性质，便于进行频域分析与控制系统设计。\n横坐标：频率的对数分度 $\\lg \\omega$ $rad / s$\n纵坐标： 频率特性\\\n幅频特性：$L(\\omega)=20\\lg |G(j\\omega)|$ 单位： 分贝\\ 显示增益随频率变化的趋势\n相频特性：$\\phi(\\omega)=\\angle G(j\\omega)$ 单位：$度^{\\circ}$ 显示相角随频率变化的趋势\n\n### 基本画法\n\n线性叠加\n\n$$\\begin{align}\nG(s)&=\\dfrac{K\\prod\\limits_{i=1}^{m}(\\tau_{i}s+1)}{s^{v}\\prod\\limits_{i=1}^{n-v}(T_{i}s+1)} \\quad \\Rightarrow\\quad G(j\\omega )=\\dfrac{K\\prod\\limits_{i=1}^{m}(j\\tau_{i}\\omega +1)}{(j\\omega )^{v}\\prod\\limits_{i=1}^{n-v}(jT_{i}\\omega +1)}\n\\end{align}$$\n\n关键求： $L(\\omega)=20\\lg |G(j\\omega)|$ $\\phi(\\omega)=\\angle G(j\\omega)$\n开环传函分解成各典型环节相串联，定转折频率，从小到大排列\n\n### 画渐近特性曲线\n\n了解经典环节的传递函数\\的特性：确定初始的点及转折频率，斜率在转折点处改变\n注意斜率单位为： dB/dec （分贝每十倍）是一种用来描述增益或衰减随频率变化的单位\n\n横坐标轴上的值要取对数进行计算\n例如 $\\omega_{1},\\omega_{2}$ 斜率 $-20dB/ dec$，$-20(\\lg(\\omega_{2})-\\lg (\\omega_{1}))$\n\n### Bode 图的增补\n\n一般补画对数相频特性曲线\n\n#### 1. 低频段初始角度补画\n在 Nyquist图\\中：从 $G(0^{+})$ 逆时针开始补画 $v\\times 90^{\\circ}$ ，半径为 $\\infty$ 的顺时针圆弧\n\n对应于 Bode 图中：从 $\\omega$ 较小，且 $L(\\omega)>0$ 的点向上补画 $v\\times 90^{\\circ}$ 的一条虚直线\n\n#### 2. 不连续相位补画\n在 Nyquist 图中：从 $G(j\\omega_{n}^{-})$ 以半径为无穷大顺时针作 $v\\times 180^{\\circ}$ 的圆弧至 $G(j\\omega_{n}^{+})$\n\n对应于 Bode 图中：从 $\\phi(\\omega^{-})$ 点向上/或下（取决于突变的方向）补作 $v\\times 180^{\\circ}$ 的虚直线至 $\\phi(\\omega^{+})$ 处\n\n### 对数幅频渐近特性\n\n一般取 $\\omega=1$ 为起始点，使用斜率不断地作出直线，来得到对数幅频渐近特性\n如果 $\\omega=1$ 为转折频率，一般取比 1 小的点作直线"
    },
    "Nyquist图": {
      "id": "Nyquist图",
      "title": "Nyquist图",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [
        "Graph"
      ],
      "aliases": [],
      "terminology": null,
      "summary": "极坐标图/幅相曲线图/Nyquist图\n$$\\begin{align}\nG(j\\omega )&=|G(j\\omega )|e^{ j \\angle G(j\\omega ) }=P(\\omega ) +jQ(\\omega )\n\\end{align}$$",
      "headings": [
        "基本的画法",
        "相位的范围",
        "绘制起点和终点",
        "与实虚轴的交点",
        "3.注意二阶振荡环节",
        "Nyquist 曲线的增补",
        "起始点",
        "不连续的点 $\\omega_{n}$"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-10-08T17:09:44.000+08:00",
      "updated": "2025-09-18T23:10:38.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/Nyquist图/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/Nyquist图.md",
      "source_path": "src/site/notes/Nyquist图.md",
      "viewer_markdown_path": "../source-notes/Nyquist图.md",
      "internal_links": [
        "传递函数"
      ],
      "inbound_links": [
        "Bode 图",
        "稳定裕度",
        "经典控制理论",
        "非最小相位系统",
        "频域稳定判据"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "极坐标图/幅相曲线图/Nyquist图\n$$\\begin{align}\nG(j\\omega )&=|G(j\\omega )|e^{ j \\angle G(j\\omega ) }=P(\\omega ) +jQ(\\omega )\n\\end{align}$$\n\n$\\omega: 0\\to \\infty$ $G(j\\omega)$ 在复平面上的轨迹,也即 $P(\\omega),Q(\\omega)$ 变化的曲线\n一般只画 $0\\to +\\infty$ 的部分（$0\\to -\\infty$ 只需要以实轴为对称轴翻折即可）\n\n### 基本的画法\n一般是对开环传递函数绘制传递函数#2. 尾 1 标准型\\：\n\n$$\\begin{align}\nG(s)&=\\dfrac{K\\prod\\limits_{i=1}^{m}(\\tau_{i}s+1)}{s^{v}\\prod\\limits_{i=1}^{n-v}(T_{i}s+1)} \\\\\nG(j\\omega )&=\\dfrac{K\\prod\\limits_{i=1}^{m}(j\\tau_{i}\\omega +1)}{(j\\omega )^{v}\\prod\\limits_{i=1}^{n-v}(jT_{i}\\omega +1)}\n\\end{align}$$\n\n同时计算：\n将 $G(j\\omega)$ 化为 $P(\\omega ) +jQ(\\omega )$ 的形式\n$P(\\omega)\\quad Q(\\omega)\\quad |G(j\\omega)|\\quad \\angle G(j\\omega)$\n\n$A(\\omega)=|G(j\\omega)|$ \n$\\phi(\\omega)=|G(j\\omega)|$\n\n#### 相位的范围\n相位范围不等号的方向变为一致\n分子对应的范围：\n$$\n\\left[0\\;,\\; \\sum\\limits_{i=1}^{m}\\arctan \\tau_{i}\\omega\\right]\n$$\n\n分母对应的范围：\n$$\\left[ -90^{\\circ}\\times v-\\sum\\limits_{i=1}^{n-v}\\arctan T_{i}\\omega\\;, \\; -90^{\\circ}\\times v\\right]$$\n\n可能出现的范围：\n$$\n\\left[ -90^{\\circ}\\times v-\\sum\\limits_{i=1}^{n-v}\\arctan T_{i}\\omega\\;, \\; -90^{\\circ}\\times v+\\sum\\limits_{i=1}^{m}\\arctan \\tau_{i}\\omega\\right]\n$$\n\n#### 1. 绘制起点和终点 \n注意渐近线和始末的辐角\n$\\omega \\to 0^{+}$：$P(0^{+})\\quad Q(0^{+})\\quad |G(0^{+})|\\quad \\angle G(0^{+})$\n$\\omega \\to +\\infty$：$P(+\\infty)\\quad Q(+\\infty)\\quad |G(+\\infty)|\\quad \\angle G(+\\infty)$\n\n#### 2. 与实虚轴的交点\n确定实际的相位范围\n$Q(\\omega)=0$ 计算与实轴交点\n$P(\\omega)=0$ 计算与虚轴交点\n\n#### 3.注意二阶振荡环节\n如果阻尼比为 0，可能会出现极限频率问题，会产生分支，不连续的点：相角的不连续带来幅值的不连续，关注使得分母为 0 的 $\\omega$，要讨论左右极限\n$P(\\omega^{-})\\quad Q(\\omega^{-})\\quad |G(\\omega^{-})|\\quad \\angle G(\\omega^{-})$\n$P(\\omega^{+})\\quad Q(\\omega^{+})\\quad |G(\\omega^{+})|\\quad \\angle G(\\omega^{+})$\n\n自然震荡频率的极限问题：通过对幅值 $\\left\\lvert G(j\\omega) \\right\\rvert$ 求导，得到幅值和对应的角频率\n谐振频率、谐振峰值\n\n### Nyquist 曲线的增补\n#### 起始点\n从 $G(0^{+})$ 逆时针开始补画 $v\\times 90^{\\circ}$ ，半径为 $\\infty$ 的顺时针圆弧\n[!tip] 注意\n从逆时针补画的原因只是不存在实际的 $G(0)$\n从 $G(0^{+})$ 开始画比较方便\n最后的圆弧还是顺时针的\n#### 不连续的点 $\\omega_{n}$\n从 $G(j\\omega_{n}^{-})$ 以半径为无穷大顺时针作 $v\\times 180^{\\circ}$ 的圆弧至 $G(j\\omega_{n}^{+})$"
    },
    "PID": {
      "id": "PID",
      "title": "PID",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [
        "Control"
      ],
      "aliases": [],
      "terminology": "Proportional-Integral-Derivative Controller",
      "summary": "Proportional-Integral-Derivative Controller PID controller \n对误差信号 $e(t)$ 进行比例、积分和微分运算变换后形成的控制规律",
      "headings": [
        "一、PID 基础",
        "比例 P",
        "积分 I",
        "微分 D",
        "二、常用控制器形式",
        "PD 比例微分",
        "PI 比例积分",
        "PID 比例积分微分"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-05-21T15:20:27.000+08:00",
      "updated": "2025-09-01T10:05:44.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/PID/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/PID.md",
      "source_path": "src/site/notes/PID.md",
      "viewer_markdown_path": "../source-notes/PID.md",
      "internal_links": [
        "数字 PID 控制器",
        "滞后校正",
        "线性系统稳态误差计算",
        "超前校正"
      ],
      "inbound_links": [
        "经典控制理论"
      ],
      "out_of_scope_links": [
        "模拟式PID控制器"
      ],
      "missing_links": [],
      "content_excerpt": "Proportional-Integral-Derivative Controller PID controller \n对误差信号 $e(t)$ 进行比例、积分和微分运算变换后形成的控制规律\n\n### 一、PID 基础\n在模拟式PID控制器\\中有更详细的叙述\n#### 比例 P \n$$\\begin{align}\nG_{c}(s)=K_{p}\n\\end{align}$$\n输出与误差信号成比例，提高系统的开环增益，减小系统线性系统稳态误差计算\\\n\n#### 积分 I \n$$\\begin{align}\nG_{c}(s)= \\dfrac{1}{T_{i}s}\n\\end{align}$$\n输出与误差信号随时间的积分成比例积分的累积作用，不单独使用\n提高系统型别，减小稳态误差\n相角滞后，可能使系统不稳定\n\n#### 微分 D \n$$\\begin{align}\nG_{c}(s)=T_{d}s\n\\end{align}$$\n输出与误差信号的变化率成比例，对噪声敏感，一般不单独使用\n\n### 二、常用控制器形式\n#### PD 比例微分\n实际上属于超前校正\\，增加开环零点，对高频信号的抑制能力减弱\n$$\\begin{align}\nG_{c}(s)=K_{p}(1+T_{d}s)\n\\end{align}$$\n\n#### PI 比例积分\n实际上属于滞后校正\\，PI 控制器相当于增加了一个位于原点的开环极点和一个负实开环零点 \n开环极点可以提高型次，减小系统稳态误差 \n开环零点可以改善缓和极点对系统稳定性及动态过程产生的不利影响 \n改善中频段，提升截止频率，改善动态性能\n\n$$\\begin{align}\nG_{c}(s)&=K_{p}(1+ \\dfrac{1}{T_{i}s}) = \\dfrac{K_{p}(s+\\dfrac{1}{T_{i}})}{s}\n\\end{align}$$\n\n#### PID 比例积分微分\n$$\\begin{align}\nG_{c}(s)&=K_{p}(1+ \\dfrac{1}{T_{i}s}+ T_{d}s) \n\\end{align}$$\n\n一般不能单独使用 D（按偏差控制，系统不稳定）, I (误差累积)\n数学模型已知及大多数数学模型难以确定的控制系统或过程 \nPID 控制参数整定方便，结构灵活 \n数字 PID 控制器\\ 控制越来越普及"
    },
    "一阶系统的时域分析": {
      "id": "一阶系统的时域分析",
      "title": "一阶系统的时域分析",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "经典环节的传递函数\\\n传递函数标准形式：(其中特征根 $- \\dfrac{1}{T}$，$T$ 为时间常数\\)\n$$\\begin{align}\n\\Phi(s)= \\dfrac{C(s)}{G(s)}= \\dfrac{1}{Ts+1}\n\\end{align}$$",
      "headings": [
        "一、单位阶跃响应",
        "二、动态性能指标"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-04-16T13:01:27.000+08:00",
      "updated": "2025-06-30T16:32:36.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/一阶系统的时域分析/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/一阶系统的时域分析.md",
      "source_path": "src/site/notes/一阶系统的时域分析.md",
      "viewer_markdown_path": "../source-notes/一阶系统的时域分析.md",
      "internal_links": [
        "时间响应的性能指标",
        "时间常数",
        "经典环节的传递函数"
      ],
      "inbound_links": [
        "经典控制理论"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "经典环节的传递函数\\\n传递函数标准形式：(其中特征根 $- \\dfrac{1}{T}$，$T$ 为时间常数\\)\n$$\\begin{align}\n\\Phi(s)= \\dfrac{C(s)}{G(s)}= \\dfrac{1}{Ts+1}\n\\end{align}$$\n\n### 一、单位阶跃响应\n$$\\begin{align}\nC(s)&= \\dfrac{1}{s(Ts+1)} = \\dfrac{1}{s}- \\dfrac{T}{T(s+\\dfrac{1}{T})} \\\\\nc(t)&=1- e^{ -t/T } \\\\\nc(\\infty)&= \\lim\\limits_{ s \\to 0 } sC(s)=1\n\\end{align}$$\n\n一阶惯性环节的阶跃响应无振荡，趋于稳态值\n\n### 二、动态性能指标\n上升时间： $t_{r}=2.20T$\n调节时间： $t_{s}=3T(\\Delta=5\\%)\\quad t_{s}=4T(\\Delta=2\\%)$\n实际做题时，动态性能指标还是要根据时间响应的性能指标\\来计算"
    },
    "二阶系统的时域分析": {
      "id": "二阶系统的时域分析",
      "title": "二阶系统的时域分析",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "$$\\begin{align} \\\\\n\\text{Open loop:}\\quad G(s)&=\\frac{\\omega _{n}^{2}}{s(s+2\\zeta \\omega _{n})} \\\\\n\\text{Closed loop:}\\quad \\Phi(s)&=\\frac{\\omega _{n}^{2}}{s^{2}+2\\zeta \\omega _{n}s+\\omega_{n}^{2}} =\\frac{1}{T^{2}s^{2}+2\\zeta Ts+1}\n\\end{ali",
      "headings": [
        "二阶系统的标准形式",
        "二、单位阶跃响应",
        "三、 $\\zeta$ 大小与极点、响应的关系",
        "不稳定",
        "无阻尼",
        "欠阻尼",
        "临界阻尼",
        "过阻尼"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-04-16T13:01:27.000+08:00",
      "updated": "2025-09-18T23:09:46.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/二阶系统的时域分析/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/二阶系统的时域分析.md",
      "source_path": "src/site/notes/二阶系统的时域分析.md",
      "viewer_markdown_path": "../source-notes/二阶系统的时域分析.md",
      "internal_links": [
        "时间常数",
        "欠阻尼二阶系统动态分析"
      ],
      "inbound_links": [
        "欠阻尼二阶系统动态分析",
        "经典控制理论",
        "零极点",
        "高阶系统的时域分析"
      ],
      "out_of_scope_links": [],
      "missing_links": [
        "一元二次方程"
      ],
      "content_excerpt": "### 二阶系统的标准形式\n\n$$\\begin{align} \\\\\n\\text{Open loop:}\\quad G(s)&=\\frac{\\omega _{n}^{2}}{s(s+2\\zeta \\omega _{n})} \\\\\n\\text{Closed loop:}\\quad \\Phi(s)&=\\frac{\\omega _{n}^{2}}{s^{2}+2\\zeta \\omega _{n}s+\\omega_{n}^{2}} =\\frac{1}{T^{2}s^{2}+2\\zeta Ts+1}\n\\end{align}$$\n$\\omega_{n}$ 自然频率\n$\\zeta$ 阻尼比 \n\n特征方程为一元二次方程\\： $s^{2}+2\\zeta \\omega _{n}s+\\omega_{n}^{2}=0$\n两根 $-\\zeta \\omega_{n}\\pm \\omega_{n}\\sqrt{ \\zeta^{2}-1 }=-\\sigma \\pm j\\omega_{d}$\n衰减系数 $\\sigma=\\zeta \\omega_{n}$ \n阻尼振荡频率 $\\omega_{d}=\\omega_{n}\\sqrt{ 1-\\zeta^{2} }$ \n[!note] 特征根的性质取决于 $\\zeta$ 的大小\n一方面影响实部的正负来影响模态，决定发散还是收敛；另一方面决定有无虚部，决定是否振荡\n[!note] 阻尼\n在振动或运动系统中，由于介质或其他原因而引起的系统运动的逐渐减弱或趋于稳定的现象\n本质是系统中能量的耗散\n\n### 二、单位阶跃响应\n\n当 $\\left\\lvert \\zeta \\right\\rvert<1$ 时：\n\n$$\\begin{align}\nC(s)&=\\frac{1}{s} \\frac{\\omega _{n}^{2}}{s^{2}+2\\zeta \\omega _{n}s+\\omega_{n}^{2}} =\\frac{1}{s} \\frac{\\omega _{n}^{2}}{(s+\\sigma-j\\omega _{d})(s+\\sigma+j\\omega _{d})} \\\\\n&=\\frac{1}{s}+\\frac{c_{1}}{s+\\sigma-j\\omega _{d}}+\\frac{c_{2}}{s+\\sigma+j\\omega _{d}} \\\\ \\\\\nc_{1}&=\\frac{\\omega _{n}^{2}}{(-\\sigma +j\\omega _{d})(2j\\omega d)}=\\frac{1}{2(-\\zeta+j\\sqrt{ 1-\\zeta^{2} })j\\sqrt{ 1-\\zeta^{2} }} \\\\ \n&=-\\frac{1}{2} \\frac{j\\zeta\\sqrt{ 1-\\zeta^{2}}-(1-\\zeta^{2})}{1-\\zeta^{2}}\\\\\n\\end{align}$$\n\n$$\\begin{align}\nc(t)&=1- \\frac{1}{\\sqrt{ 1-\\zeta^{2} }}e^{-\\zeta \\omega _{n}t}(\\sqrt{ 1-\\zeta^{2} }\\cos \\omega _{d}t+\\zeta \\sin \\omega _{d}t)\\\\\n&=1- \\frac{1}{\\sqrt{ 1-\\zeta^{2} }}e^{-\\zeta \\omega _{n}t}\\sin(\\omega _{d}t+\\beta) \\\\\n\\beta&=\\arctan \\frac{\\sqrt{ 1-\\zeta^{2} }}{\\zeta} \\quad \\zeta =\\cos \\beta\n\\end{align}$$\n\n### 三、 $\\zeta$ 大小与极点、响应的关系\n \n\n#### 1. 不稳定 \n $\\zeta<0$ 两个具有正实部的极点，发散\n \n#### 2. 无阻尼 \n $\\zeta=0$ 两个共轭纯虚极点，等幅振荡\n$$\\begin{align}\nc(t)=1-\\cos \\omega _{n}t\n\\end{align}$$\n\n#### 3. 欠阻尼 \n$0<\\zeta<1$ 两个具有负实部的共轭复极点，衰减振荡 欠阻尼二阶系统动态分析\\\n$$\\begin{align}\nc(t)=1-\\frac{1}{\\sqrt{ 1-\\zeta^{2} }}e^{-\\zeta \\omega _{n}t}\\sin(\\omega _{d}t+\\beta)\n\\end{align}$$\n\n#### 4. 临界阻尼 \n$\\zeta=1$ 两个相同的负实极点，无振荡，趋于稳定，稳态值为 1 的无超调量单调上升过程\n\n$$\\begin{align}\n1-e^{ -\\omega _{n}t }(1+\\omega _{n}t)\n\\end{align}$$\n\n#### 5. 过阻尼\n$1<\\zeta$\n\n$$\\begin{gathered}\nc(t)=1+\\frac{e^{ -t/T_{1} }}{\\frac{T_{2}}{T_{1}}-1}+\\frac{e^{ -t/T_{2} }}{\\frac{T_{1}}{T_{2}}-1} \\\\\nT_{1}= \\dfrac{1}{\\omega _{n}(\\zeta-\\sqrt{ \\zeta^{2}-1 })} \\quad T_{2}= \\dfrac{1}{\\omega _{n}(\\zeta+\\sqrt{ \\zeta^{2}-1 })}\n\\end{gathered}$$\n\n两根 $-\\zeta \\omega_{n}\\pm \\omega_{n}\\sqrt{ \\zeta^{2}-1 }$\n\n两个互异负实极点，无振荡，趋于稳定，$T_{1}\\quad T_{2}$ 为时间常数\\\n\n上升时间：$t_{r}= "
    },
    "信号保持": {
      "id": "信号保持",
      "title": "信号保持",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [],
      "aliases": [],
      "terminology": "Signal Holding",
      "summary": "Signal Holding\n保持器：将数字信号转换为连续信号，本质是解决采样点之间的插值\\问题。\n为了实现对被控对象的有效控制，必须把数字信号恢复为连续信号，实践上，常采用接近理想低通滤波器的零阶保持器对信号进行重构",
      "headings": [
        "一、保持器数学描述",
        "二、零阶保持器 ZOH"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-07-05T14:08:00.000+08:00",
      "updated": "2025-09-10T22:22:40.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/信号保持/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/信号保持.md",
      "source_path": "src/site/notes/信号保持.md",
      "viewer_markdown_path": "../source-notes/信号保持.md",
      "internal_links": [
        "数字控制器"
      ],
      "inbound_links": [
        "数字控制器",
        "脉冲传递函数",
        "计算机控制系统"
      ],
      "out_of_scope_links": [
        "插值"
      ],
      "missing_links": [],
      "content_excerpt": "Signal Holding\n保持器：将数字信号转换为连续信号，本质是解决采样点之间的插值\\问题。\n为了实现对被控对象的有效控制，必须把数字信号恢复为连续信号，实践上，常采用接近理想低通滤波器的零阶保持器对信号进行重构\n\n### 一、保持器数学描述\n在 $nT$ 时刻：\n$$e(t)\\Big|_{t=nT}=e(nT)=e^{}(nT)$$\n在 $(n+1)T$ 时刻：\n$$e(t)\\Big|_{t=(n+1)T}=e[ (n+1)T]=e^{} [ (n+1)T]$$\n在 $0<\\Delta t<T$ 时，使用插值\\，递推公式：\n$$e(nT+\\Delta t)=a_{0}+a_{1}\\Delta t+a_{2}(\\Delta t)^{2}+\\cdots+a_{m}(\\Delta t)^{m}$$\n$nT+\\Delta T$ 时刻的输出的值，取决于 $\\Delta t=0,-T,-2T,\\cdots,-mT$ 时\n各过去时刻的离散信号 $e^{}(nT),e^{}[(n-1)T],\\cdots,e^{*}[(n-m)T]$ 的 $(m+1)$ 个值\n称为 m 阶保持器\n\n### 二、零阶保持器 ZOH\nZero-Order Holder\n\n零阶保持器：\n\n$$\\begin{align}\nf_{h}(t)=1(t)-1(t-T)\n\\end{align}$$\n\n零阶保持器的传递函数：\n\n$$\\begin{align}\n\\mathscr{L}[1(t)-1(t-T)]= \\dfrac{1}{s}- \\dfrac{1}{s}\\exp (-Ts)= \\dfrac{1-\\exp(-Ts)}{s}\n\\end{align}$$\n\n绝大部分使用零阶保持器，产生大约 $\\dfrac{1}{2}$ 个周期的纯滞后\n\n$$\\begin{align}\n\\dfrac{1}{s}- \\dfrac{1}{s}e^{ -Ts }=\\dfrac{1-\\exp(-Ts)}{s} =\\dfrac{\\exp(\\dfrac{1}{2}Ts)-\\exp(-\\dfrac{1}{2}Ts)}{\\exp( \\dfrac{1}{2}Ts)\\cdot s} \\approx \\dfrac{1+ \\dfrac{1}{2}Ts-(1- \\dfrac{1}{2}Ts)}{\\exp( \\dfrac{1}{2}Ts)\\cdot s}= T \\exp(-\\dfrac{1}{2}Ts)\n\\end{align}$$\n\n数字控制器#零阶保持器和惯性环节串联的 z 变换\\"
    },
    "信号采样": {
      "id": "信号采样",
      "title": "信号采样",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [
        "Discrete"
      ],
      "aliases": [],
      "terminology": "Signal sampling",
      "summary": "Signal sampling",
      "headings": [
        "一、采样信号与连续信号的关系",
        "二、采样过程的数学描述",
        "采样信号的拉普拉斯变换",
        "采样信号的频谱",
        "三、采样周期的选取",
        "香农采样定理"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-07-05T14:07:08.000+08:00",
      "updated": "2025-09-10T22:15:48.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/信号采样/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/信号采样.md",
      "source_path": "src/site/notes/信号采样.md",
      "viewer_markdown_path": "../source-notes/信号采样.md",
      "internal_links": [
        "脉冲函数",
        "频带宽度"
      ],
      "inbound_links": [
        "数字PID 参数整定",
        "计算机控制系统"
      ],
      "out_of_scope_links": [
        "傅里叶变换",
        "拉普拉斯变换"
      ],
      "missing_links": [],
      "content_excerpt": "Signal sampling\n\n采样器： 把连续信号变换为脉冲序列\n\n采样器的采样过程可以使用一个周期性闭合的采样开关 S 表示\n$S$ 采样开关\n$e(t)$ 采样器输入信号（连续信号）\n$e^{}(t)$ 采样器输出信号（离散信号） 采样信号\n$T$ 采样周期\n$\\tau$ 采样时间\n\n### 一、采样信号与连续信号的关系\n\n理想单位脉冲序列（理想采样开关）：\n$$\\begin{align}\n\\delta_{T}(t)&=\\sum\\limits_{n=0}^{\\infty}\\delta(t-nT)\n\\end{align}$$\n$\\delta(t-nT)$ 是出现在时刻 $t=nT$ 强度为 1 的单位脉冲函数\\\n\n连续信号在采样的瞬时点 $t=nT$ 为： $e(nT)$\n则采样信号表示为：\n$$\\begin{align}\n e^{}(t) =e(t)\\delta_{T}(t) =\\sum\\limits_{n=0}^{\\infty} e(nT)\\delta_{T}(t-nT)\n\\end{align}$$\n\n### 二、采样过程的数学描述\n\n#### 1. 采样信号的拉普拉斯变换\n\n拉普拉斯变换#3. 位移性质\\\n\n$$\\begin{align}\nE^{}(s)&=\\mathscr{L}[e^{}(t)] \\\\\n&=\\mathscr{L}\\left[ \\sum\\limits_{n=0}^{\\infty}e(nT)\\delta_{T}(t-nT) \\right] \\\\\n&=\\sum\\limits_{n=0}^{\\infty} e(nT) \\mathscr{L}[\\delta_{T}(t-nT)] \\\\\n&=\\sum\\limits_{n=0}^{\\infty} e(nT) e^{ -nTs }\n\\end{align}$$\n\n#### 2. 采样信号的频谱 \n傅里叶变换\\\n$$\\begin{align}\ne^{}(t)&= \\dfrac{1}{T} \\sum\\limits_{n=-\\infty}^{\\infty} e(t)e^{ jn\\omega _{s} t } \\\\\nE^{}(s)&= \\dfrac{1}{T} \\sum\\limits_{n=-\\infty}^{\\infty}E(s+jn\\omega _{s}) \\\\\nE^{*}(j\\omega )&= \\dfrac{1}{T} \\sum\\limits_{n=-\\infty}^{\\infty}E[j(\\omega +n\\omega _{s})]\n\\end{align}$$\n\n### 三、采样周期的选取\n\n#### 香农采样定理\n如果采样器的输入信号具有有限频带宽度\\，并且有直到 $\\omega_{h}$ 的频率分量（即最高频率为 $\\omega_{h}$）\n则使得信号完全从采样信号中恢复过来的采样周期 $T$ 满足：(采样频率 $\\omega_{s}\\geq 2\\omega_{h}$)\n$$\\begin{align}\n \\omega _{s} \\geq 2\\omega _{h} \\quad \\Rightarrow \\quad T=\\dfrac{2\\pi}{\\omega _{s}} & \\leq \\dfrac{2\\pi}{2\\omega _{h}} \n\\end{align}$$\n\n工程实践中，一般不取等号\n$\\omega_{h}$ 为带宽频率\n$\\omega_{s}$ 采样角频率\n$T$ 采样周期\n\n采样周期小于最小时间常数的一半，例子：\n\n$$\\begin{align}\n\\dfrac{1}{(s+1)(s+2)} \\quad T_{1}=1, T_{2}= \\dfrac{1}{2} \\quad T 非开放题，如果无采样周期，要自己选择合理的采样周期，就要注意采样的限制\n一般取整数倍，且不要大于纯滞后的延迟时间，纯滞后的延迟时间一般为采样周期的整数倍\n\n实际例子：给定以下传递函数，问合适的采样周期是？\n$$\\begin{align}\n\\dfrac{1}{(5s+1)(10s+1)}e^{ -2s }\n\\end{align}$$\n\n~~2.5~~ 2 ~~1.5~~ 1 ~~0.5~~"
    },
    "广义根轨迹": {
      "id": "广义根轨迹",
      "title": "广义根轨迹",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "除了 $K^{*}$ 变化的常规根轨迹，其他情况的根轨迹属于广义根轨迹\n参数根轨迹：根轨迹增益以外其他参数变化时的根轨迹\n### 绘制的基本方法\n只需要明确根轨迹本质就是 特征方程\n写出闭环特征方程：1+开环传递函数\n等效开环传递函数(闭环极点相同)：就是将要变换的参数分离（例如：参数 p），写成：\n $\\dfrac{p\\cdot f(s)}{g(s)}=-1$ 的形式\n绘制等效系统的根轨迹：参考 180°根轨迹绘制法则\\",
      "headings": [
        "绘制的基本方法",
        "根轨迹族"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-05-21T15:20:28.000+08:00",
      "updated": "2025-10-28T16:19:36.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/广义根轨迹/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/广义根轨迹.md",
      "source_path": "src/site/notes/广义根轨迹.md",
      "viewer_markdown_path": "../source-notes/广义根轨迹.md",
      "internal_links": [
        "180°根轨迹绘制法则"
      ],
      "inbound_links": [
        "经典控制理论"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "除了 $K^{*}$ 变化的常规根轨迹，其他情况的根轨迹属于广义根轨迹\n参数根轨迹：根轨迹增益以外其他参数变化时的根轨迹\n### 绘制的基本方法\n只需要明确根轨迹本质就是 特征方程\n写出闭环特征方程：1+开环传递函数\n等效开环传递函数(闭环极点相同)：就是将要变换的参数分离（例如：参数 p），写成：\n $\\dfrac{p\\cdot f(s)}{g(s)}=-1$ 的形式\n绘制等效系统的根轨迹：参考 180°根轨迹绘制法则\\\n\n例子：\n$$\\begin{align}\n & 开环传函：G_{o}(s) =\\dfrac{4}{s(s+p)} \\\\\n & 闭环特征方程：s^{2}+ps+4=0 \\\\\n &改写形式：1+ \\dfrac{ps}{s^{2}+4}=0 \\\\\n &等效开环传函： \\dfrac{ps}{s^{2}+4}\n\\end{align}$$\n\n将闭环特征方程改写，得到 等效的开环传递函数，转为 180°根轨迹绘制法则\\的分析\n\n### 根轨迹族\n根轨迹族：当系统有两个以上的参数变化时，绘制的根轨迹 \n绘制方法：选定第一个参数为常数，第二个参数从0→∞绘制根轨迹 \n再改变第一个参数，重复绘制关于第二个参数的根轨迹"
    },
    "开环频率特性": {
      "id": "开环频率特性",
      "title": "开环频率特性",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "基于 Bode 图\\的开环传函分析\n### 低频段\n分析系统的稳态性能\n斜率决定稳态性能\n高度决定开环增益",
      "headings": [
        "低频段",
        "中频段",
        "高频段"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-05-20T13:11:25.640+08:00",
      "updated": "2025-05-02T17:47:14.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/开环频率特性/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/开环频率特性.md",
      "source_path": "src/site/notes/开环频率特性.md",
      "viewer_markdown_path": "../source-notes/开环频率特性.md",
      "internal_links": [
        "Bode 图",
        "线性系统稳态误差计算",
        "经典环节的传递函数"
      ],
      "inbound_links": [
        "经典控制理论"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "基于 Bode 图\\的开环传函分析\n### 低频段\n分析系统的稳态性能\n斜率决定稳态性能\n高度决定开环增益\n\n低频段的斜率本质上表征系统的线性系统稳态误差计算\\\n$0dB/dec$ 型次为 0\n$-20dB/dec$ 型次为 1\n$-40dB/dec$ 型次为 2\n\n### 中频段\n分析系统的动态性能\n\n稳定性，快速性\n### 高频段\n分析系统的抗干扰能力\n\n高频段一般由时间常数很小的环节构成\n通常近似为经典环节的传递函数\\，反映对高频干扰信号的抑制能力"
    },
    "控制系统的数学模型": {
      "id": "控制系统的数学模型",
      "title": "控制系统的数学模型",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "机理分析 ：基于内部机理和物理原理\n真实性和可解释性：基于系统的内部机理和物理原理\n预测和设计能力：便于设计、优化和控制，达到性能指标 \n传递能力：从某系统中获取的知识和理解转移到其他类似系统",
      "headings": [
        "建模方法",
        "建立数学模型",
        "模型类别"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-06-22T12:47:22.000+08:00",
      "updated": "2025-05-12T13:43:18.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/控制系统的数学模型/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/控制系统的数学模型.md",
      "source_path": "src/site/notes/控制系统的数学模型.md",
      "viewer_markdown_path": "../source-notes/控制系统的数学模型.md",
      "internal_links": [],
      "inbound_links": [
        "自动控制原理"
      ],
      "out_of_scope_links": [
        "容量过程建模实例",
        "电机及电力拖动"
      ],
      "missing_links": [],
      "content_excerpt": "### 建模方法\n数学模型: 指过程在各输入量的作用下，其相应输出量变化的函数关系数学表达式。\n通道: 输入量与输出量间的信号联系\n\n机理分析 ：基于内部机理和物理原理\n真实性和可解释性：基于系统的内部机理和物理原理\n预测和设计能力：便于设计、优化和控制，达到性能指标 \n传递能力：从某系统中获取的知识和理解转移到其他类似系统\n\n系统辨识 ： 基于观测数据的建模方法，实验统计方法 \n通过测取系统在输入作用下的输出响应, 或正常运行的输入和输出数据记录, 估计系统数学模型 \n建立的数学模型一般是系统输入输出特性在某种准则意义下的一种近似\n\n### 建立数学模型\n建模实例：容量过程建模实例\\\n\n电机及电力拖动\\\n\n### 模型类别\nmermaid\ngraph LR \n数学模型--> 静态 & 动态\n静态--->代数方程\n动态-->连续时间 & 离散时间\n离散时间--> 差分方程 & Z变换\n连续时间--> 线性微分方程 & 非线性微分方程 & 拉普拉斯变换"
    },
    "时间响应的性能指标": {
      "id": "时间响应的性能指标",
      "title": "时间响应的性能指标",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [],
      "aliases": [],
      "terminology": "Performance indicators of time response",
      "summary": "Performance indicators of time response",
      "headings": [
        "一、动态性能指标",
        "二、稳态性能指标"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-04-16T13:01:27.000+08:00",
      "updated": "2025-09-16T16:24:44.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/时间响应的性能指标/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/时间响应的性能指标.md",
      "source_path": "src/site/notes/时间响应的性能指标.md",
      "viewer_markdown_path": "../source-notes/时间响应的性能指标.md",
      "internal_links": [
        "线性系统稳态误差计算"
      ],
      "inbound_links": [
        "一阶系统的时域分析",
        "经典控制理论"
      ],
      "out_of_scope_links": [
        "导数"
      ],
      "missing_links": [],
      "content_excerpt": "Performance indicators of time response\n\n### 一、动态性能指标\n动态过程（过渡过程/瞬态过程）：系统输出量从初始状态到最终状态的响应过程\n动态性能：稳定是动态系统能够运行的首要条件，只有当动态过程收敛时，动态性能才有意义\n延迟时间 $t_{d}$ ：第一次达到终值 $50\\%$ 所需的时间\n上升时间 rise time $t_{r}$： 终值 10%上升到终值 90%所需的时间\n峰值时间 peak time $t_{p}$：响应超过终值到达第一个峰值所需的时间\n超调量 $\\sigma\\%$： 最大偏离量与稳态值的差比上稳态值，最大偏离量可以通过导数\\得出（求极值）\n\n$$\\sigma\\%=\\dfrac{c(t_{p})-c(\\infty)}{c(\\infty)}\\times 100\\%$$\n调节时间 setting time $t_{s}$：响应到达并保持在与终值 $\\pm5\\%$ 内所需的最短时间\n\n基本步骤\n求传递函数\n求时间响应\n求动态性能指标 \n\n### 二、稳态性能指标\n稳态过程：当 t 趋于无穷时，系统输出量的表现形式\n误差：$e(t)=r(t)-c(t)$\n稳态误差： $e_{ss}(\\infty)$ 线性系统稳态误差计算\\"
    },
    "校正环节的设计": {
      "id": "校正环节的设计",
      "title": "校正环节的设计",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "已知单位反馈系统的传递函数\\ $G_{0}(s)$，设计串联校正环节，串联一个零极点校正装置：",
      "headings": [],
      "pinned": false,
      "level": null,
      "created": "2024-05-21T15:20:28.000+08:00",
      "updated": "2025-08-28T21:53:14.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/校正环节的设计/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/校正环节的设计.md",
      "source_path": "src/site/notes/校正环节的设计.md",
      "viewer_markdown_path": "../source-notes/校正环节的设计.md",
      "internal_links": [
        "传递函数",
        "根轨迹法基础",
        "零极点"
      ],
      "inbound_links": [
        "经典控制理论"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "已知单位反馈系统的传递函数\\ $G_{0}(s)$，设计串联校正环节，串联一个零极点校正装置：\n\n$$\\begin{align}\nG_{c}= \\dfrac{K_{c}(s+z_{c})}{(s+p_{c})}\n\\end{align}$$\n\n基本步骤：\n由原开环传递函数 $G_{0}(s)$，画出根轨迹法基础\\\n根据校正之后的理想指标确定校正后的零极点\\\n判断闭环主导极点在原来的根轨迹之左还是之右，来确定零点和极点的相对位置\n\n确定校正装置的零极点位置\n设校正后的闭环主导极点 $s_{d}$\n$s_{d}$ 在校正后的根轨迹上所以满足根轨迹法基础\\\n$$\\begin{align}\n\\angle(s_{d}-z_{c})+\\sum\\limits_{i=1}^{m}\\angle(s_{d}-z_{i})=\\pm(2k+1)\\pi +\\angle(s_{d}-p_{c})+\\sum\\limits_{i=1}^{n}\\angle(s_{d}-p_{i})\n\\end{align}$$\n$\\varphi=|\\angle(s_{d}-z_{c})-\\angle(s_{d}-p_{c})|$\n$\\beta=\\arctan \\dfrac{\\sqrt{ 1-\\zeta^{2} }}{\\zeta}$\n\n$$\\begin{align}\n & \\dfrac{|z_{c}|}{\\sin \\gamma}=\\dfrac{\\omega _{n}}{\\sin(\\pi-\\beta-\\gamma)} \\\\\n & \\dfrac{|p_{c}|} {\\sin(\\gamma+\\varphi)}=\\dfrac{\\omega _{n}}{\\sin(\\pi-\\beta-\\gamma-\\varphi)} \\\\\n & \\alpha=\\dfrac{|z_{c}|}{|p_{c}|} =\\dfrac{\\sin\\gamma\\cdot\\sin(\\pi-\\beta-\\gamma-\\varphi)}{\\sin(\\pi-\\beta-\\gamma)\\cdot \\sin(\\gamma+\\varphi)}\n\\end{align}$$\n\n$$\\begin{align}\n & \\alpha=\\dfrac{z_{c}}{p_{c}} \\\\\n & \\dfrac{\\mathrm{d} \\alpha}{\\mathrm{d} \\gamma} =0 \\Rightarrow \\gamma= \\dfrac{1}{2}(\\pi-\\beta-\\varphi)\n\\end{align}$$\n校正之后的开环传递函数\n$$\\begin{align}\nG'(s)=G_{0}(s)G_{c}(s)\n\\end{align}$$\n$s_{d}$ 满足根轨迹法基础\\\n确定 $K_{c}$"
    },
    "根轨迹法基础": {
      "id": "根轨迹法基础",
      "title": "根轨迹法基础",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "根轨迹/根迹：开环传函某一参数从零变到无穷时，闭环系统特征方程的根在s 平面上变化的轨迹\n由开环传递函数绘出闭环根的轨迹 \n根据闭环极点的分布分析系统性",
      "headings": [
        "根轨迹方程"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-05-21T15:20:28.390+08:00",
      "updated": "2025-09-18T20:25:22.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/根轨迹法基础/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/根轨迹法基础.md",
      "source_path": "src/site/notes/根轨迹法基础.md",
      "viewer_markdown_path": "../source-notes/根轨迹法基础.md",
      "internal_links": [
        "传递函数"
      ],
      "inbound_links": [
        "传递函数",
        "极点配置与系统镇定",
        "校正环节的设计",
        "经典控制理论",
        "零极点"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "根轨迹/根迹：开环传函某一参数从零变到无穷时，闭环系统特征方程的根在s 平面上变化的轨迹\n由开环传递函数绘出闭环根的轨迹 \n根据闭环极点的分布分析系统性\n\n传递函数\\：\n$$\\begin{align}\nG(s)&=\\frac{b_{0}(s-z_{1})(s-z_{2})\\cdots(s-z_{m})}{a_{0}(s-p_{1})(s-p_{2})\\cdots(s-p_{n})} =K^{}\\frac{\\prod\\limits_{i=1}^{m}(s-z_{i}) }{\\prod\\limits_{j=1}^{n}(s-p_{j})}\n\\end{align}$$\n\n$$\\begin{align}\n & G(s)=K_{G}^{} \\dfrac{\\prod\\limits_{i=1}^{f}(s-z_{i})}{\\prod\\limits_{i=1}^{q}(s-p_{i})} \\\\\n & H(s)=K_{H}^{} \\dfrac{\\prod\\limits_{j=1}^{l}(s-z_{j})}{\\prod\\limits_{j=1}^{h}(s-p_{j})} \\\\\n & G(s)H(s)=K_{G}^{} K_{H}^{}\\dfrac{\\prod\\limits_{i=1}^{f}(s-z_{i})}{\\prod\\limits_{i=1}^{q}(s-p_{i})}\\dfrac{\\prod\\limits_{j=1}^{l}(s-z_{j})}{\\prod\\limits_{j=1}^{h}(s-p_{j})} \\\\\n\\end{align}$$\n\n$$\\begin{align}\n & \\Phi(s)=K_{G}^{}(s) \\dfrac{\\prod\\limits_{i=1}^{f}(s-z_{i})\\prod\\limits_{j=1}^{h}(s-p_{j})}{\\prod\\limits_{i=1}^{n}(s-p_{i})+K^{}\\prod\\limits_{j=1}^{m}(s-z_{j})} \\\\\n & f+l=m\\quad q+h=n\n\\end{align}$$\n闭环系统根轨迹增益等于前向通路根轨迹增益\n闭环零点由前向通路传递函数的零点和反馈通路传递函数的极点所组成\n闭环系统极点，与开环系统零点/开环系统极点以及开环系统根轨迹增益有关\n[!important] 根轨迹法的基本任务：\n由已知的开环零、极点的分布及根轨迹增益，通过图解的方法找出闭环极点\n（确定闭环极点后，确定闭环传递函数的形式。在已知闭环传递函数时，利用拉普拉斯逆变换求出闭环系统的时间响应）\n\n### 根轨迹方程\n闭环特征方程：$1+G(s)H(s)=0$\n根轨迹方程：$G(s)H(s)=-1$\n\n$$\\begin{align}\nK^{} \\dfrac{\\prod\\limits_{j=1}^{m}(s-z_{j})}{\\prod\\limits_{i=1}^{n}(s-p_{i})}=-1\n\\end{align}$$\n相角条件：确定s平面上根轨迹的充分必要条件：根轨迹上的点满足相角条件，为闭环传函的极点\n\n$$\\begin{align}\n & \\sum\\limits_{j=1}^{m}\\angle(s-z_{j})-\\sum\\limits_{i=1}^{n}\\angle(s-p_{i})=(2k+1)\\pi\n\\end{align}$$\n模值条件：确定s平面上各点的 $K^{}$ 值时使用\n$$\\begin{align}\n& K^{}= \\dfrac{\\prod\\limits_{i=1}^{n}|s-p_{i}| }{\\prod\\limits_{j=1}^{m}|s-z_{j}|}\n\\end{align}$$"
    },
    "欠阻尼二阶系统动态分析": {
      "id": "欠阻尼二阶系统动态分析",
      "title": "欠阻尼二阶系统动态分析",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "在二阶系统的时域分析\\基础上分析",
      "headings": [
        "一、欠阻尼二阶系统基本量",
        "二、动态性能指标"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-04-16T13:01:27.300+08:00",
      "updated": "2025-09-18T23:07:48.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/欠阻尼二阶系统动态分析/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/欠阻尼二阶系统动态分析.md",
      "source_path": "src/site/notes/欠阻尼二阶系统动态分析.md",
      "viewer_markdown_path": "../source-notes/欠阻尼二阶系统动态分析.md",
      "internal_links": [
        "二阶系统的时域分析"
      ],
      "inbound_links": [
        "二阶系统的时域分析",
        "线性系统的校正",
        "经典环节的传递函数"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "在二阶系统的时域分析\\基础上分析\n\n### 一、欠阻尼二阶系统基本量\n\n二阶系统的设计一般取 $\\zeta=0.4\\sim 0.8$\n\n$$\\begin{align}\nc(t)&=1- \\frac{1}{\\sqrt{ 1-\\zeta^{2} }}e^{-\\zeta \\omega _{n}t}(\\sqrt{ 1-\\zeta^{2} }\\cos \\omega _{d}t+\\zeta \\sin \\omega _{d}t)\\\\\n&=1- \\frac{1}{\\sqrt{ 1-\\zeta^{2} }}e^{-\\zeta \\omega _{n}t}\\sin(\\omega _{d}t+\\beta) \\\\\n\\beta&=\\arctan \\frac{\\sqrt{ 1-\\zeta^{2} }}{\\zeta} \\\\\n\\zeta &=\\cos \\beta\n\\end{align}$$\n自然频率 $\\omega_{n}$ \n阻尼比 $\\zeta$ \n阻尼角 $\\beta$\n衰减系数 $\\sigma=\\zeta \\omega_{n}$ \n阻尼振荡频率 $\\omega_{d}=\\omega_{n}\\sqrt{ 1-\\zeta^{2} }$ \n\n### 二、动态性能指标\n$\\omega_{n}\\uparrow\\quad t_{d},t_{r},t_{p},t_{s} \\downarrow$\n$\\zeta \\uparrow\\quad t_{d},t_{r},t_{p} \\uparrow\\quad \\sigma,t_{s}\\downarrow$\n\n延迟时间：经验公式 \n\n$$\\begin{align}\nh(t_{d})=0.5\\quad t_{d}= \\dfrac{1+0.6\\zeta+0.2\\zeta^{2}}{\\omega_{n}}\n\\end{align}$$\n\n上升时间：\n\n$$\\begin{align}\nh(t_{r})=1\\quad \\sin(\\omega _{d}t_{r}+\\beta)=0 \\quad t_{r}= \\frac{\\pi-\\beta}{\\omega _{d}}\n\\end{align}$$\n\n峰值时间：\n$$\\begin{align}\n\\dfrac{\\mathrm{d} h}{\\mathrm{d} t}\\mid_{t=t_{p}} =0 \\quad t_{p}=\\frac{\\pi}{\\omega _{d}}\n\\end{align}$$\n\n阻尼振荡周期的一半，与闭环极点虚部成反比；闭环极点距离负实轴距离越远，峰值时间越短\n\n超调量：\n\n$$\\begin{align}\n\\sin(\\pi+\\beta)=-\\sqrt{ 1-\\zeta^{2} }\n\\end{align}$$\n\n$$\\begin{align}\nh(t_{p})&=1- \\frac{1}{\\sqrt{ 1-\\zeta^{2} }}e^{-\\pi \\zeta/\\sqrt{ 1-\\zeta^{2} }}\\sin(\\pi+\\beta) \\\\\n\\sigma\\%&=\\frac{h(t_{p})-h(\\infty)}{h(\\infty)} =e^{- \\pi \\zeta/\\sqrt{ 1-\\zeta^{2} }}\n\\end{align}$$\n\n调节时间：\n到达并保持在终值 ±5% 内所需的最短时间\n到达并保持在终值 ±2% 内所需的最短时间\n\n$$\\begin{align}\nt_{s}\\leq \\frac{3.5}{\\zeta \\omega _{n}}\\quad \\Delta=0.05 \\\\\nt_{s}\\leq \\frac{4.4}{\\zeta \\omega _{n}}\\quad \\Delta=0.02\n\\end{align}$$"
    },
    "滞后校正": {
      "id": "滞后校正",
      "title": "滞后校正",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "适用于：未校正系统的动态性能已经满足，但是稳定性能不满足要求",
      "headings": [
        "相关参数",
        "对系统的影响",
        "校正的设计步骤"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-06-03T21:08:31.000+08:00",
      "updated": "2025-08-28T21:53:14.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/滞后校正/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/滞后校正.md",
      "source_path": "src/site/notes/滞后校正.md",
      "viewer_markdown_path": "../source-notes/滞后校正.md",
      "internal_links": [
        "稳定裕度"
      ],
      "inbound_links": [
        "PID",
        "经典控制理论"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "适用于：未校正系统的动态性能已经满足，但是稳定性能不满足要求\n\n高频幅值衰减特性，使系统的截止频率减小\n\n高频段的校正\n\n利用滞后网络的高频幅值衰减特性，使系统的截止频率减小，获得足够的 $\\gamma$\n$$\\begin{align}\n\\dfrac{U_{2}(s)}{U_{1}(s)}&= \\dfrac{R_{2}+ \\dfrac{1}{Cs}}{R_{1}+R_{2}+ \\dfrac{1}{Cs}} =\\dfrac{1+R_{2}Cs}{1+(R_{1}+R_{2})Cs}\n\\end{align}$$\n\n$$\\begin{align}\nG_{c}(s)&= \\dfrac{1+bTs}{1+Ts}\\quad b<1\n\\end{align}$$\n\n### 相关参数\n分度系数：$b=\\dfrac{R_{2}}{R_{1}+R_{2}}$\n时间常数：$T=(R_{1}+R_{2})C$\n转折频率： $\\omega_{1}=\\dfrac{1}{T}$ $\\omega_{2}=\\dfrac{1}{b T}$ \n$0<\\omega<\\omega_{1}$\n$\\omega_{1}<\\omega<\\omega_{2}$\n$\\omega_{2}<\\omega<+\\infty$\n\n最大滞后角频率:\n$$\\begin{align}\n\\lg\\omega _{m}= \\dfrac{1}{2} (\\lg \\dfrac{1}{T}+ \\lg \\dfrac{1}{bT})\n\\end{align}$$\n\n$$\\begin{align}\n\\omega _{m}=\\sqrt{ \\dfrac{1}{bT}\\cdot \\dfrac{1}{T} }= \\dfrac{1}{T\\sqrt{ b }}\n\\end{align}$$\n\n最大滞后角:\n$$\\begin{align}\n\\varphi_{m}=\\arctan \\dfrac{b-1}{2\\sqrt{ b}}=\\arcsin \\dfrac{b-1}{b+1}\n\\end{align}$$\n\n为了提高相角裕度，防止系统不稳定，选择滞后参数，使得第二个转折频率 $\\omega_{2}\\ll \\omega_{c}''$（开环截止频率）\n\n$$\\begin{align}\n\\dfrac{1}{bT}&= \\dfrac{\\omega_{c}''}{10} \\quad\\quad \\varphi_{c}(\\omega _{c''}) \\approx acrtan[0.1(b-1)]\n\\end{align}$$\n\n### 对系统的影响\n降低中高频段幅值增益，提高了抗中高频干扰的能力 \n相角滞后，不利于相角裕度的提升（避免最大滞后角发生在已校正系统开环截止频率附近）\n\n### 校正的设计步骤\n根据稳态要求，确定未校正系统的放大系数 $K$\n画出未校正系统 $G_{o}(s)$ 的 Bode 图 (渐近特性图)\n 求未校正系统的稳定裕度\\ $\\omega_{c}$ 与稳定裕度\\ $\\gamma$\n根据相位裕度 $\\gamma'$ 的要求，确定未校正系统的相角裕度 $\\gamma(\\omega_{c}')$\n $\\gamma'=\\gamma(\\omega_{c}')+\\varphi_{c}(\\omega_{c}')$，取 $\\varphi_{c}(\\omega_{c}')=-6^{\\circ}\\sim -14^{\\circ}$\n 以及校正后系统的截止频率 $\\omega_{c}'$ \n确定校正系数\n $20\\lg b+L(\\omega_{c}')=0$\n 利用滞后校正环节的高频段拉低未校正的曲线，降低截止频率，使得相角裕度符合要求$\\dfrac{1}{bT}=0.1\\omega_{c}'$\n 还要保证第二个转折频率远远小于新的截止频率，避免最大滞后角的影响\n校正后的系统\n 校正环节 $G_{c}(s)= \\dfrac{1+bTs}{1+Ts}$"
    },
    "稳定裕度": {
      "id": "稳定裕度",
      "title": "稳定裕度",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [],
      "aliases": [],
      "terminology": "Stability Margins",
      "summary": "Stability Margins\n是控制系统设计和分析中的重要概念，它提供了线性系统稳定性分析\\的定量度量",
      "headings": [
        "幅值裕度",
        "相角裕度"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-05-21T15:20:28.580+08:00",
      "updated": "2025-09-18T23:22:12.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/稳定裕度/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/稳定裕度.md",
      "source_path": "src/site/notes/稳定裕度.md",
      "viewer_markdown_path": "../source-notes/稳定裕度.md",
      "internal_links": [
        "Bode 图",
        "Nyquist图",
        "线性系统稳定性分析",
        "非最小相位系统"
      ],
      "inbound_links": [
        "滞后校正",
        "线性系统的校正",
        "经典控制理论",
        "经典环节的传递函数",
        "超前校正",
        "频带宽度"
      ],
      "out_of_scope_links": [],
      "missing_links": [
        "最小相位系统"
      ],
      "content_excerpt": "Stability Margins\n是控制系统设计和分析中的重要概念，它提供了线性系统稳定性分析\\的定量度量\n\n稳定裕度主要有两种：\n幅值/增益裕度（Gain Margin）\n相角/相位裕度（Phase Margin）\n\n建立在 Nyquist图\\、Bode 图\\的分析之上\n[!important] 注意\n注意裕度的判定只适用于最小相位系统\\，非最小相位系统\\一般不用\n应用范围不如 Nyquist 和 Bode 判据（判定开环传函的零极点个数）\n\n### 幅值裕度\n是指在不引起系统不稳定的情况下，系统增益可以增加的最大倍数\n\n穿越频率 $\\omega_{x}$：\nNyquist 图中，与负实轴交点对应的频率\n $\\phi(\\omega_{x})=-\\pi$\n $A (\\omega _{x})=\\left\\lvert G (j\\omega ) \\right\\rvert$\nBode 图中, 对数相频特性为-180°对应的频率\n $\\phi(\\omega_{x})=-180^{\\circ}$\n $L(\\omega _{x})=20\\lg A(\\omega _{x})$\n\n幅值裕度：\n$$\\begin{align}\nh&=\\dfrac{1}{A(\\omega _{x})} \\;\\; {\\color{red}\\Leftrightarrow} \\; \\;h(dB)=20\\lg(h) \\;dB\\, =\\,-20\\lg (A(\\omega )) \\; dB\n\\end{align}$$\n$h>1\\quad h(dB)>0$ 即在单位圆内 $(-1,j 0)$ 的右边，系统稳定\n$h [!important] 注意\n幅值裕度可能无法得到：如果相频全在-180°以上，自然就不存在幅值裕度\n\n### 相角裕度\n是指在不引起振荡的情况下，系统相位可以延迟的最大角度\n\n剪切/截止频率 $\\omega_{c}$： 增益为 1 时，对应的频率\nNyquist 图中，与单位圆相交的频率 $A(\\omega_{c})=1$\nBode 图中，对数幅频特性为 0 时对应的频率 $L(\\omega_{c})=0dB$\n\n相角裕度：\n\n$$\\begin{align}\n\\gamma=180^{\\circ}+\\phi(\\omega _{c})\n\\end{align}$$\n当 $\\gamma>0^{\\circ}$ 时，系统稳定\n当 $\\gamma<0^{\\circ}$ 时，系统不稳定"
    },
    "线性系统的校正": {
      "id": "线性系统的校正",
      "title": "线性系统的校正",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "校正与控制器之间的关系：\n校正：由控制器执行的操作或过程，本身不是控制器 \n控制器：根据输入和系统状态生成控制输出的设备或算法，根据反馈信息调整系统操作，实现控制目标",
      "headings": [
        "一、基本概念",
        "二、校正的方式",
        "1.串联校正",
        "2.反馈校正",
        "3.前馈校正",
        "4.复合校正"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-05-30T09:55:47.000+08:00",
      "updated": "2025-08-28T21:53:14.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/线性系统的校正/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/线性系统的校正.md",
      "source_path": "src/site/notes/线性系统的校正.md",
      "viewer_markdown_path": "../source-notes/线性系统的校正.md",
      "internal_links": [
        "反馈",
        "欠阻尼二阶系统动态分析",
        "稳定裕度",
        "线性系统稳态误差计算"
      ],
      "inbound_links": [
        "经典控制理论"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "### 一、基本概念\n校正：在系统中加入参数可以根据需要而改变的机构或装置，使系统整个特性发生变化，满足给定的各项性能指标。\n\n校正与控制器之间的关系：\n校正：由控制器执行的操作或过程，本身不是控制器 \n控制器：根据输入和系统状态生成控制输出的设备或算法，根据反馈信息调整系统操作，实现控制目标\n\n校正目的：通过调整控制器或系统工作方式，使系统性能达到最佳状态或满足特定需求 \n校正方式：调整控制器参数、改变系统操作方式、更新系统模型等\n\n系统校正的依据\n稳态指标：线性系统稳态误差计算\\\n动态指标：欠阻尼二阶系统动态分析\\\n相对稳定性: 稳定裕度\\\n\n### 二、校正的方式\n\n#### 1.串联校正\n接在系统误差测量点之后、放大器之前\n开环频率特性的低频段表征了闭环系统的稳态性能\n开环频率特性的中频段表征了闭环系统的动态性能\n开环频率特性的高频段表征了闭环系统的复杂性和噪声抑制性能\n\n#### 2.反馈校正\n接在系统局部反馈\\通路中\n反馈控制确保稳定性，实现对系统输出的控制；\n反馈校正重点调整动态特性反馈控制系统可以包括反馈校正，但反馈校正不是反馈控制系统的必须部分\n\n#### 3.前馈校正\n在系统主反馈回路之外采用的校正方式\n\n#### 4.复合校正\n反馈校正+前馈校正\n扰动补偿：恰当选择控制器，消除扰动对系统的影响\n输入补偿：通过改变系统的输入信号来补偿系统的非线性、时滞、鲁棒性和模型不确定性等动态特性\n[!important] 注意\n一切的计算和验证都是基于渐近特性图得到的\n超前滞后校正是基于渐近幅频特性所作"
    },
    "线性系统稳定性分析": {
      "id": "线性系统稳定性分析",
      "title": "线性系统稳定性分析",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [],
      "aliases": [],
      "terminology": "Stability Analysis of Linear System",
      "summary": "Stability Analysis of Linear System\n系统分析的前提是稳定\n### 一、基础概念\n稳定性：系统在扰动消失后，由初始偏差状态恢复到原平衡状态的性能\n李雅普诺夫稳定性理论：线性系统在初始扰动的影响下，其动态过程随时间推移逐渐衰减并趋于零，则称系统渐近稳定\n经典控制理论的稳定性属于李雅普诺夫稳定性理论\\中的渐进稳定",
      "headings": [
        "一、基础概念",
        "二、线性系统稳定判据",
        "赫尔维茨判据",
        "劳斯判据",
        "特殊情况",
        "变例",
        "李纳德 -戚帕特判据"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-04-16T13:01:27.000+08:00",
      "updated": "2025-06-03T18:58:10.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/线性系统稳定性分析/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/线性系统稳定性分析.md",
      "source_path": "src/site/notes/线性系统稳定性分析.md",
      "viewer_markdown_path": "../source-notes/线性系统稳定性分析.md",
      "internal_links": [
        "传递函数",
        "李雅普诺夫稳定性理论",
        "零极点"
      ],
      "inbound_links": [
        "李雅普诺夫稳定性理论",
        "离散系统的稳定性分析",
        "稳定裕度",
        "线性系统稳态误差计算",
        "经典控制理论",
        "零极点",
        "频域稳定判据"
      ],
      "out_of_scope_links": [
        "行列式"
      ],
      "missing_links": [],
      "content_excerpt": "Stability Analysis of Linear System\n系统分析的前提是稳定\n### 一、基础概念\n稳定性：系统在扰动消失后，由初始偏差状态恢复到原平衡状态的性能\n李雅普诺夫稳定性理论：线性系统在初始扰动的影响下，其动态过程随时间推移逐渐衰减并趋于零，则称系统渐近稳定\n经典控制理论的稳定性属于李雅普诺夫稳定性理论\\中的渐进稳定\n\n线性系统稳定的充分必要条件：闭环系统特征方程的所有根均具有负实部，或闭环传递函数\\的零极点\\均位于 s 左半平面。（实部决定收敛和发散，虚部决定是否振荡）\n\n### 二、线性系统稳定判据\n闭环特征方程：$D(s)=a_{n}s^{n}+a_{n-1}s^{n-1}+\\cdots+a_{1}s+a_{0}=0$\n#### 1. 赫尔维茨判据\n必要条件：特征方程的各项系数为正数\n充分必要条件：由特征方程各项系数所构成的主行列式\\及其顺序主子式全部为正\n\n$n=1:$ 特征方程的各项系数为正\n$n=2:$ 特征方程的各项系数为正\n$n=3:$ 特征方程的各项系数为正，且 $a_{1}a_{2}-a_{0}a_{3}>0$\n$n=4:$ 特征方程的各项系数为正，且 $\\Delta_{2}=a_{1}a_{2}-a_{0}a_{3}>0$, 以及 $\\Delta_{2}> \\dfrac{a_{3}a_{0}}{a_{1}^{2}}$\n#### 2. 劳斯判据\n$D(s)=a_{n}s^{n}+a_{n-1}s^{n-1}+\\cdots+a_{1}s+a_{0}=0$\n劳斯表：\n\n$$\\begin{align}\nL_{31}=-\\frac{1}{a_{n-1}} \\begin{vmatrix}\na_{n} & a_{n-2} \\\\\na_{n-1} & a_{n-3} \\\\\n\\end{vmatrix} \\\\\nL_{32}=-\\frac{1}{a_{n-1}} \\begin{vmatrix}\na_{n} & a_{n-4} \\\\\na_{n-1} & a_{n-5} \\\\\n\\end{vmatrix} \\\\ \nL_{33}=-\\frac{1}{a_{n-1}} \\begin{vmatrix}\na_{n} & a_{n-6} \\\\\na_{n-1} & a_{n-7} \\\\\n\\end{vmatrix} \\\\ \\\\ \n\nL_{41}=-\\frac{1}{L_{31}} \\begin{vmatrix}\na_{n-1} & a_{n-3} \\\\\nL_{31} & L_{32} \\\\\n\\end{vmatrix} \\\\\nL_{42}=-\\frac{1}{L_{31}} \\begin{vmatrix}\na_{n-1} & a_{n-5} \\\\\nL_{31} & L_{33} \\\\\n\\end{vmatrix}\n\\end{align}$$\n\n系统稳定的充分必要条件：第一列各值为正值\n第一列中数据符号改变的次数等于系统特征方程正实部根的数目\n如果第一列中出现负值，系统不稳定\n[!important] 注意\n计算劳斯表时，不要漏掉负号\n\n##### 特殊情况\n某一行第一项为 0，而其余项不全为 0\n 用一个很小的正数 $\\varepsilon$ 替代 0\n 只是判断极限是大于零还是小于零即可, 所以从正半轴趋于零\n出现全零行\n 说明有大小相等、方向相反的根\n 零行的上一行系数构造一个辅助多项式， 并以该多项式导数的系数代替全零行\n \n 例如:\n $s^{4}\\quad 2\\quad 3\\quad 4$\n $s^{3}\\quad 0\\quad 0\\quad 0$\n $F(s)=2s^{4}+3s^{2}+4$\n 以该多项式求导的系数代替全零行\n $F'(s)=8s^{3}+6s$\n $s^{3}\\quad 8\\quad 6\\quad 0$\n\n##### 变例\n如果问在 $s=x_{0}$ 的右侧，直接 变量代换 $s=x_{0}+z\\quad z=s-x_{0}$\n将 $f(s)\\to g(z)$ 然后再沿用之前的计算方法\n#### 3. 李纳德 -戚帕特判据"
    },
    "线性系统稳态误差计算": {
      "id": "线性系统稳态误差计算",
      "title": "线性系统稳态误差计算",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [],
      "aliases": [],
      "terminology": "Steady-state Error Calculation for Linear Systems",
      "summary": "Steady-state Error Calculation for Linear Systems",
      "headings": [
        "一、求稳态误差的基本步骤",
        "二、影响系统稳定误差的因素",
        "三、减小输入作用下的稳态误差"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-04-16T13:01:27.000+08:00",
      "updated": "2025-06-30T16:40:12.000+08:00",
      "permalink": "/A2- 控制理论/1/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/线性系统稳态误差计算 md",
      "source_path": "src/site/notes/线性系统稳态误差计算.md",
      "viewer_markdown_path": "../source-notes/线性系统稳态误差计算.md",
      "internal_links": [
        "线性系统稳定性分析",
        "经典输入信号",
        "频率特性"
      ],
      "inbound_links": [
        "PID",
        "开环频率特性",
        "时间响应的性能指标",
        "离散系统稳态分析",
        "线性系统的校正",
        "经典控制理论"
      ],
      "out_of_scope_links": [
        "拉普拉斯变换"
      ],
      "missing_links": [],
      "content_excerpt": "Steady-state Error Calculation for Linear Systems\n\n只有当线性系统稳定性分析\\时，研究稳态误差才有意义\n\n$$e(t)=e_{ts}(t)+e_{ss}(t)$$\n暂态分量： $e_{ts}(t)$ $\\lim\\limits_{ t \\to \\infty }e_{ts}(t)=0$ 系统稳定是基本的要求\n稳态分量： $e_{ss}(t)$ $\\lim\\limits_{ t \\to \\infty }e(t)=e_{ss}(\\infty)$ 即系统的稳态误差\n\n使用拉普拉斯变换的拉普拉斯变换#6.极限性质\\计算：\n$$\\begin{align}\ne_{ss}(\\infty)=\\lim\\limits_{ s \\to 0 }sE(s) \n\\end{align}$$\n\n### 一、求稳态误差的基本步骤\n得到误差传递函数\n$$\\Phi_{e}(s)= \\dfrac{E(s)}{R(s)}= \\dfrac{1}{1+G(s)}$$\n判断是否稳定：利用误差传递函数的特征方程，判断系统是否线性系统稳定性分析\\\n利用终值定理求出稳态误差\n$$\\begin{align} \nE(s)= \\Phi_{e}(s)R(s) \\; {\\color{red}\\Rightarrow} \\; e_{ss}(\\infty)=\\lim\\limits_{ s \\to 0 }sE(s) \n\\end{align}$$\n[!important] 注意！\n一定要注意终值条件的使用前提！正弦信号的输入不能使用终值条件计算稳态误差\n正弦信号的输入下的误差计算：求误差传递函数，利用频率特性\\，代入输入信号的角频率，得到输出的误差信号。\n\n### 二、影响系统稳定误差的因素\n系统输入 $R(s)$\n开环增益 $K$\n型次/系统类型： $v$ \n\n开环传递函数极点为 0 的个数/纯积分环节的个数，可以直接判断传递函数对经典输入信号\\的跟踪能力\n$$\\begin{align}\n & v=0\\quad & 0型系统 \\\\\n & v=1\\quad & I型系统\\\\\n & v=2\\quad & II型系统\n\\end{align}$$\n\n开环传递函数：\n$$\\begin{align} \nG(s)H(s)= \\dfrac{K \\prod\\limits_{i=1}^{m}(\\tau_{i}s+1)}{s^{v} \\prod\\limits_{j=1}^{n-v}(T_{j}s+1)} \\; \\; {\\color{red}\\Rightarrow} \\; \\; \\lim\\limits_{ s \\to 0 } G(s)H(s)= \\dfrac{K}{s^{v}} \\\\ \n\\end{align}$$\n\n稳态误差：\n$$\\begin{align}\n e_{ss}(\\infty) & =\\lim\\limits_{ s \\to 0 } \\dfrac{sR(s)}{1+G(s)H(s)} \\\\ \\\\\n\n & = \\dfrac{\\lim\\limits_{ s \\to 0 }s^{v+1}R(s)}{K+ \\lim\\limits_{ s \\to 0 } s^{v}} = \\dfrac{\\lim\\limits_{ s \\to 0 }s^{v+1}R(s)}{K} \n\\end{align}$$\n\n$$e_{s s}(\\infty)=\\begin{cases}\n\\dfrac{R}{1+K_{p}} & 阶跃输入\\\\\n\\quad \\dfrac{R}{K_{v}} &斜坡输入\\\\\n\\quad \\dfrac{R}{K_{a}} & 加速度输入\n\\end{cases}$$\n\n求误差系数，也即在考虑输入的阶次时，对开环传递函数求极限\n阶跃输入 $\\dfrac{1}{s}$ $K_{p}=\\lim\\limits_{ s \\to 0 }G(s)H(s)=\\lim\\limits_{ s \\to 0 } \\dfrac{K}{s^{v}}$ 静态位置误差系数 \n斜坡输入 $\\dfrac{1}{s^{2}}$ $K_{v}=\\lim\\limits_{ s \\to 0 }sG(s)H(s)=\\lim\\limits_{ s \\to 0 } \\dfrac{K}{s^{v-1}}$ 静态速度误差系数\n加速度输入 $\\dfrac{1}{s^{3}}$ $K_{a}=\\lim\\limits_{ s \\to 0 }s^{2}G(s)H(s)=\\lim\\limits_{ s \\to 0 } \\dfrac{K}{s^{v-2}}$ 静态加速度误差系数 \n\n注意 $K$ 是误差传递函数化为尾 1 多项式的开环增益\n\n### 三、减小输入作用下的稳态误差\n增大系统开环增益\n增加开环传递函数的积分环节（前向通路或主反馈通道）"
    },
    "经典控制理论": {
      "id": "经典控制理论",
      "title": "经典控制理论",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [
        "Subject",
        "Control"
      ],
      "aliases": [],
      "terminology": "Classical Control Theory",
      "summary": "Classical Control Theory\n以传递函数为基础，研究 SISO 线性定常系统",
      "headings": [
        "一、基础知识",
        "二、时域分析法",
        "三、根轨迹法",
        "四、频域分析法",
        "五、线性系统的校正与设计",
        "六、离散控制系统"
      ],
      "pinned": true,
      "level": null,
      "created": "2024-12-03T17:18:05.000+08:00",
      "updated": "2025-09-18T23:10:32.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/经典控制理论/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/经典控制理论.md",
      "source_path": "src/site/notes/经典控制理论.md",
      "viewer_markdown_path": "../source-notes/经典控制理论.md",
      "internal_links": [
        "0°根轨迹绘制规则",
        "180°根轨迹绘制法则",
        "Bode 图",
        "Nyquist图",
        "PID",
        "一阶系统的时域分析",
        "二阶系统的时域分析",
        "传递函数",
        "信号流图",
        "广义根轨迹",
        "开环频率特性",
        "时间响应的性能指标",
        "校正环节的设计",
        "根轨迹法基础",
        "滞后校正",
        "稳定裕度",
        "系统结构框图",
        "线性系统的校正",
        "线性系统稳定性分析",
        "线性系统稳态误差计算",
        "经典环节的传递函数",
        "经典输入信号",
        "超前校正",
        "频域稳定判据",
        "频带宽度",
        "频率特性",
        "高阶系统的时域分析"
      ],
      "inbound_links": [
        "传递函数",
        "经典输入信号",
        "自动控制原理"
      ],
      "out_of_scope_links": [
        "拉普拉斯变换"
      ],
      "missing_links": [
        "根轨迹分析系统性能",
        "滞后-超前校正"
      ],
      "content_excerpt": "Classical Control Theory\n以传递函数为基础，研究 SISO 线性定常系统\n\n### 一、基础知识\n核心工具： 拉普拉斯变换\\ \n\n传递函数\\\n\n求传递函数的方法：\n系统结构框图\\ \n信号流图\\\n\n经典输入信号\\ 经典环节的传递函数\\\n\n### 二、时域分析法\nTime-domain Analysis\n\n基础：时间响应的性能指标\\\n时域分析：\n一阶系统的时域分析\\\n二阶系统的时域分析\\\n高阶系统的时域分析\\\n稳定性分析：线性系统稳定性分析\\\n稳态误差的计算：线性系统稳态误差计算\\\n\n### 三、根轨迹法\n\nRoot Locus Method\n\n根轨迹法基础\\\n\n根轨迹绘制法则：\n180°根轨迹绘制法则\\\n广义根轨迹\\\n0°根轨迹绘制规则\\\n\n系统性能分析：根轨迹分析系统性能\\\n\n### 四、频域分析法\n\nFrequency-Response Analysis\n\n频域分析法：控制系统对不同频率正弦信号的响应全面反映系统的各种性质\n\n对正弦信号输入，研究频率特性\\\n幅频特性 Magnitude Response\n相频特性 Phase Response\n\n频率特性的几何表示：\nNyquist图\\ 幅相曲线图\nBode 图\\ 对数频率特性图\n\n稳定性分析：\n频域稳定判据\\（稳定性的判断）\n稳定裕度\\ (相对稳定性/系统稳定性的度量）\n\n性能指标：\n频带宽度\\ （闭环频域性能指标）\n开环频率特性\\（开环频域性能指标）\n[!important] 注意！\n本节的内容重点是：利用开环频率特性研究系统的稳定性，Bode 图和 Nyquist 图，以及稳定裕度的相关概念，是基于开环传递函数画的。\n但是提及系统的输出或稳态误差的计算，是根据闭环传递函数进行分析的。\n频域分析法中的 $\\omega$ (无论是 Bode 图、 Nyquist 图，还是稳定裕度的计算) 都应该是以弧度为单位的\n\n### 五、线性系统的校正与设计\n线性系统的校正\\\n常用校正装置：超前校正\\、滞后校正\\、滞后-超前校正\\、PID\\\n\n校正环节的设计\\\n\n### 六、离散控制系统\n具体见：计算机控制系统"
    },
    "超前校正": {
      "id": "超前校正",
      "title": "超前校正",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "系统稳定性和动态性能",
      "headings": [
        "相关参数",
        "对系统的影响",
        "设计校正的步骤"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-06-03T21:09:11.040+08:00",
      "updated": "2025-08-28T21:53:14.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/超前校正/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/超前校正.md",
      "source_path": "src/site/notes/超前校正.md",
      "viewer_markdown_path": "../source-notes/超前校正.md",
      "internal_links": [
        "稳定裕度",
        "频带宽度"
      ],
      "inbound_links": [
        "PID",
        "经典控制理论"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "系统稳定性和动态性能\n\n mjx-container[jax=\"SVG\"] { direction: ltr;}mjx-container[jax=\"SVG\"] &gt; svg { overflow: visible; min-height: 1px; min-width: 1px;}mjx-container[jax=\"SVG\"] &gt; svg a { fill: blue; stroke: blue;}mjx-container[jax=\"SVG\"][display=\"true\"] { display: block; text-align: center; margin: 1em 0;}mjx-container[jax=\"SVG\"][display=\"true\"][width=\"full\"] { display: flex;}mjx-container[jax=\"SVG\"][justify=\"left\"] { text-align: left;}mjx-container[jax=\"SVG\"][justify=\"right\"] { text-align: right;}g[data-mml-node=\"merror\"] &gt; g { fill: red; stroke: red;}g[data-mml-node=\"merror\"] &gt; rect[data-background] { fill: yellow; stroke: none;}g[data-mml-node=\"mtable\"] &gt; line[data-line], svg[data-table] &gt; g &gt; line[data-line] { stroke-width: 70px; fill: none;}g[data-mml-node=\"mtable\"] &gt; rect[data-frame], svg[data-table] &gt; g &gt; rect[data-frame] { stroke-width: 70px; fill: none;}g[data-mml-node=\"mtable\"] &gt; .mjx-dashed, svg[data-table] &gt; g &gt; .mjx-dashed { stroke-dasharray: 140;}g[data-mml-node=\"mtable\"] &gt; .mjx-dotted, svg[data-table] &gt; g &gt; .mjx-dotted { stroke-linecap: round; stroke-dasharray: 0,140;}g[data-mml-node=\"mtable\"] &gt; g &gt; svg { overflow: visible;}[jax=\"SVG\"] mjx-tool { display: inline-block; position: relative; width: 0; height: 0;}[jax=\"SVG\"] mjx-tool &gt; mjx-tip { position: absolute; top: 0; left: 0;}mjx-tool &gt; mjx-tip { display: inline-block; padding: .2em; border: 1px solid #888; font-size: 70%; background-color: #F8F8F8; color: black; box-shadow: 2px 2px 5px #AAAAAA;}g[data-mml-node=\"maction\"][data-toggle] { cursor: pointer;}mjx-status { display: block; position: fixed; left: 1em; bottom: 1em; min-width: 25%; padding: .2em .4em; border: 1px solid #888; font-size: 90%; background-color: #F8F8F8; color: black;}foreignObject[data-mjx-xml] { font-family: initial; line-height: normal; overflow: visible;}mjx-container[jax=\"SVG\"] path[data-c], mjx-container[jax=\"SVG\"] use[data-c] { stroke-width: 3;} $R_1$ $R_2$ C C $U_2$ $U_1$ Text is not SVG - cannot display \n\n$$\\begin{align}\n\\dfrac{U_{2}(s)}{U_{1}(s)}&= \\dfrac{R_{2}}{R_{1}\\parallel \\dfrac{1}{Cs}+R_{2}} \\\\\n&=\\dfrac{R_{2}+R_{1}R_{2}Cs}{R_{1}+R_{2}+R_{1}R_{2}Cs} \\\\\n&=\\dfrac{\\dfrac{R_{2}}{R_{1}+R_{2}} + \\dfrac{R_{1}R_{2}C}{R_{1}+R_{2}}s}{1+\\dfrac{R_{1}R_{2}C}{R_{1}+R_{2}}s} \\\\\n&= \\dfrac{\\dfrac{1}{\\alpha}+Ts}{1+Ts}\n\\end{align}$$\n\n$$\\begin{align}\n\\alpha G_{c}(s)&=\\dfrac{1+\\al"
    },
    "零极点": {
      "id": "零极点",
      "title": "零极点",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "传递函数\\ 根轨迹法基础\\\n零点 Zeros：传递函数分子多项式为零的点\n极点 Poles：传递函数分母多项式为零的点",
      "headings": [
        "稳定性分析",
        "动态性能分析",
        "引入开环极点",
        "引入开环零点",
        "闭环主导极点",
        "偶极子"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-05-21T15:20:28.000+08:00",
      "updated": "2025-09-16T17:04:46.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/零极点/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/零极点.md",
      "source_path": "src/site/notes/零极点.md",
      "viewer_markdown_path": "../source-notes/零极点.md",
      "internal_links": [
        "二阶系统的时域分析",
        "传递函数",
        "根轨迹法基础",
        "线性系统稳定性分析",
        "高阶系统的时域分析"
      ],
      "inbound_links": [
        "180°根轨迹绘制法则",
        "传递函数",
        "校正环节的设计",
        "线性定常系统的能控性",
        "线性系统稳定性分析",
        "高阶系统的时域分析"
      ],
      "out_of_scope_links": [],
      "missing_links": [
        "PD"
      ],
      "content_excerpt": "传递函数\\ 根轨迹法基础\\\n零点 Zeros：传递函数分子多项式为零的点\n极点 Poles：传递函数分母多项式为零的点\n\n### 稳定性分析\n线性系统稳定性分析\\\n闭环系统特征方程的所有根均具有负实部，闭环传递函数的极点均位于 s 左半平面。\n\n### 动态性能分析\n根据根轨迹的位置，结合二阶系统的时域分析\\，判断系统的性能\n\n### 引入开环极点\n根轨迹向右弯曲，动态性能变差，甚至导致不稳定\n极点使峰值时间滞后，超调量减小\n\n### 引入开环零点\n相当于增加 PD\\ 矫正环节\n在开环系统中增加负实部零点，可以使根轨迹向左方移动，所引入的零点越靠近虚轴，根轨迹向左方移动的越显著，从而增加系统的相对稳定性，改善系统的动态特性。\n零点使峰值时间提前，超调量增大\n原理：根轨迹上的点应该始终满足 相角条件\n$$\\begin{align}\n & \\sum\\limits_{j=1}^{m}\\angle(s-z_{j})-\\sum\\limits_{i=1}^{n}\\angle(s-p_{i})=(2k+1)\\pi\n\\end{align}$$\n\n当引入开环零点时，仍要满足相角条件，根轨迹向左移动\n\n### 闭环主导极点\n闭环主导极点：距离虚轴比较近，且附近没有其他的零点的极点。利用闭环主导极点，对系统降阶，化为尾 1 多项式。 高阶系统的时域分析\\\n\n### 偶极子\n相距很近的闭环零极点，分为两类：\n不接近坐标原点对动态性能的影响很小(可以直接消去)\n接近坐标原点，必须考虑对动态性能的影响(不能消去)，但不影响系统主导极点的地位"
    },
    "非最小相位系统": {
      "id": "非最小相位系统",
      "title": "非最小相位系统",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [],
      "aliases": [],
      "terminology": "Nonminimum-phase system",
      "summary": "Nonminimum-phase system",
      "headings": [
        "非最小相位环节"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-05-21T15:20:28.000+08:00",
      "updated": "2025-09-29T18:57:54.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/非最小相位系统/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/非最小相位系统.md",
      "source_path": "src/site/notes/非最小相位系统.md",
      "viewer_markdown_path": "../source-notes/非最小相位系统.md",
      "internal_links": [
        "Bode 图",
        "Nyquist图",
        "传递函数",
        "经典环节的传递函数"
      ],
      "inbound_links": [
        "0°根轨迹绘制规则",
        "稳定裕度",
        "经典环节的传递函数"
      ],
      "out_of_scope_links": [],
      "missing_links": [
        "最小相位系统"
      ],
      "content_excerpt": "Nonminimum-phase system\n\n凡系统的传递函数\\在 s 平面的右半平面上具有一个或多个零点的系统即为非最小相位系统，与最小相位系统\\相对。\n\n### 非最小相位环节\n经典环节的传递函数\\\nBode 图\\：幅频特性一致；相频特性符号相反（关于 0°线对称）\nNyquist图\\：关于实轴对称"
    },
    "频域稳定判据": {
      "id": "频域稳定判据",
      "title": "频域稳定判据",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "利用开环频率特性判断闭环系统的线性系统稳定性分析\\",
      "headings": [
        "幅角原理",
        "Nyquist 判据",
        "Bode 判据"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-05-21T15:20:28.000+08:00",
      "updated": "2025-10-24T11:54:10.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/频域稳定判据/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/频域稳定判据.md",
      "source_path": "src/site/notes/频域稳定判据.md",
      "viewer_markdown_path": "../source-notes/频域稳定判据.md",
      "internal_links": [
        "Bode 图",
        "Nyquist图",
        "传递函数",
        "线性系统稳定性分析"
      ],
      "inbound_links": [
        "经典控制理论"
      ],
      "out_of_scope_links": [],
      "missing_links": [
        "卷绕数"
      ],
      "content_excerpt": "利用开环频率特性判断闭环系统的线性系统稳定性分析\\\n\n### 幅角原理\n\n在复平面 $[s]$ 任取一条闭合曲线 $\\Gamma$，包围 $F (s)$ 的 $Z$ 个零点和 $P$ 个极点，且不通过 $F (s)$ 的任何零点和极点\n当复变量 $s$ 沿曲线 $\\Gamma$ 顺时针绕一周时，在平面 $[F]$ 上，$\\Gamma_{F}$ 包围原点的卷绕数\\ $R=P-Z$\n\n开环传递函数 \\ ： $G(s)H(s)$\n1+开环传递函数： $F(s)=1+G(s)H(s)$ \n\n也即：闭环传递函数的分母\n$F(s)$ 的根，即 $F(s)$ 的零点，为闭环传递函数的极点\n\n$$Z=P-R$$\n$Z$ 为 $F(s)$ 的零点个数，也即闭环传递函数的极点个数\n$P$ 为 $F(s)$ 的极点个数，也即开环传递函数 $G(s)H(s)$ 的极点个数\n$R$ 为 $F$ 对应的曲线 $\\Gamma_{F}$ 包围原点的圈数，也即开环传递函数包围 $(-1,j 0)$ 的圈数\n系统稳定的充分必要条件为：闭环系统特征方程的所有根均具有负实部\n\n所以我们重点讨论右半平面\n\n选择闭合曲线 $\\Gamma$ 包围复平面的右半平面和虚轴，若被包围的 $F(s)$ 零点数 $Z=0$，则闭环系统稳定，因为 $Z=P-R$，开环传递函数在右半平面的极点个数为 $P$\n\n所以判断系统的稳定转化为判断 $F(s)$ 右半平面包围的零点个数，转化为求 $F(s)$ 包围零点的圈数 $R$，即求开环传递函数包围 $(-1,j0)$ 点的圈数 $R$\n\n### Nyquist 判据\n对于增补后的 Nyquist图\\\n\n闭环系统稳定的充要条件：曲线 $\\Gamma_{GH}$ 不穿过 $(-1,j 0)$, 且逆时针包围 $(-1,j 0)$ 的圈数 $R$ 等于开环传递函数正实部极点的个数 $P$\n\n正负穿越法：$\\omega: 0\\to +\\infty$ ，$\\Gamma_{GH}$ 穿越 $(-1,j 0)$ 左侧负实轴的次数\n\n逆时针为正方向\n正穿越 $N^{+}$：从上到下，辐角逐渐增大，穿越左侧负实轴\n负穿越 $N^{-}$：从下到上，辐角逐渐减小，穿越左侧负实轴(增补的穿越都为负穿越)\n半次正穿越 $\\dfrac{1}{2}N^{+}$ 起于负实轴\n半次负穿越 $\\dfrac{1}{2}N^{-}$，终于负实轴\n\n逆时针包围的圈数 $R$ ：\n$$\\begin{align}\nR=2N=2(N^{+}-N^{-})\n\\end{align}$$\n\n### Bode 判据\n对于增补后的 Bode 图\\\n\nNyquist 图中：$\\Gamma_{GH}$ 穿越 $(-1,j 0)$ 左侧负实轴的次数，对应 Bode 图中：幅频特性大于 $0dB$ 的所有频率内，相频特性穿越 $(2k+1)\\pi$ 的次数\n\n补作的虚直线都为负穿越：\n$$\\begin{align}\nR=2N=2(N^{+}-N^{-})\n\\end{align}$$"
    },
    "频带宽度": {
      "id": "频带宽度",
      "title": "频带宽度",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [],
      "aliases": [],
      "terminology": "Bandwidth",
      "summary": "Bandwidth\n先有稳定，再谈性能指标。稳定裕度\\、谐振峰值\n对闭环系统而言",
      "headings": [
        "一、基本定义",
        "二、意义",
        "三、经典环节的带宽",
        "频域指标和时域指标综合"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-05-20T13:11:25.650+08:00",
      "updated": "2025-05-02T17:47:14.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/频带宽度/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/频带宽度.md",
      "source_path": "src/site/notes/频带宽度.md",
      "viewer_markdown_path": "../source-notes/频带宽度.md",
      "internal_links": [
        "稳定裕度",
        "频率特性"
      ],
      "inbound_links": [
        "信号采样",
        "经典控制理论",
        "经典环节的传递函数",
        "超前校正"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "Bandwidth\n先有稳定，再谈性能指标。稳定裕度\\、谐振峰值\n对闭环系统而言\n\n### 一、基本定义\n$\\varPhi(j\\omega)$ 为系统闭环频率特性\\\n带宽频率 $\\omega_{b}$ ： 当闭环幅频特性下降到频率为 0 时的分贝值以下 3dB 时，即 $0.707\\left\\lvert \\Phi(j 0) \\right\\rvert$ 时，对应的频率 \n频带宽度/带宽 $(0,\\omega_{b})$： \n$$\\begin{align}\n\\left\\lvert \\varPhi(\\omega _{b}) \\right\\rvert&=0.707 \\left\\lvert \\varPhi(j 0) \\right\\rvert \\quad 20\\lg\\left\\lvert \\varPhi(\\omega _{b}) \\right\\rvert=20\\lg \\left\\lvert \\varPhi(j 0) \\right\\rvert-3dB\n\\end{align}$$\n\n### 二、意义\n反映系统跟踪输入信号的能力\n小于 $\\omega_{b}$ 的频率分量可以输出\n大于 $\\omega_{b}$ 的频率分量会不同程度地衰减\n带宽的选择在设计中应折中考虑：对于输入端信号, 带宽大, 跟踪控制信号的能力强，抑制输入端高频干扰的能力弱\n### 三、经典环节的带宽\n带宽频率为 $\\omega_{b}$\n一阶系统：\n$$\\begin{align}\n\\phi(s)= \\dfrac{1}{Ts+1}\\quad \\left\\lvert \\phi(j\\omega) \\right\\rvert= \\dfrac{1}{\\sqrt{ T^{2}\\omega^{2}+1 }} \\; {\\color{red}\\Rightarrow} \\; \\omega_{b}= \\dfrac{1}{T}\n\\end{align}$$\n\n二阶系统：\n$$\\begin{align}\n\\phi(s)=\\dfrac{\\omega_{n}^{2}}{s^{2}+2\\zeta \\omega_{n}s+\\omega_{n}^{2}} \\; {\\color{red}\\Rightarrow} \\; \\omega_{b}=\\omega_{n}\\sqrt{ (1-2\\zeta^{2})+\\sqrt{ 2-4\\zeta^{2}+4\\zeta^{4} } }\n\\end{align}$$\n正比于自然振荡频率 $\\omega_{n}$ 以及单位阶跃响应的速度\n与阻尼比 $\\zeta$ 成反比\n带宽扩大 $\\lambda$ 倍, 响应速度加快 $\\lambda$ 倍 \n### 频域指标和时域指标综合\n二阶系统\n高阶系统: 经验公式"
    },
    "频率特性": {
      "id": "频率特性",
      "title": "频率特性",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [],
      "aliases": [],
      "terminology": "Frequency Response",
      "summary": "Frequency Response\n由传递函数\\决定",
      "headings": [
        "定义一",
        "定义二",
        "实际例题"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-05-26T18:53:13.000+08:00",
      "updated": "2025-08-28T21:53:14.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/频率特性/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/频率特性.md",
      "source_path": "src/site/notes/频率特性.md",
      "viewer_markdown_path": "../source-notes/频率特性.md",
      "internal_links": [
        "传递函数"
      ],
      "inbound_links": [
        "Bode 图",
        "线性系统稳态误差计算",
        "经典控制理论",
        "频带宽度"
      ],
      "out_of_scope_links": [
        "复数"
      ],
      "missing_links": [],
      "content_excerpt": "Frequency Response\n由传递函数\\决定\n\n对于稳定的线性定常系统：\n幅频特性 Magnitude Response\n相频特性 Phase Response\n都为输入频率 $\\omega$ 的函数\n[!important] 注意\n频率特性是由闭环传递函数定义的！系统的输出与系统的输入要明确！\n\n### 定义一\n输入信号： $A\\sin(\\omega t)$\n输出信号： $B\\sin(\\omega t+\\phi)$\n幅频特性： $\\dfrac{B}{A}$\n相频特性：$\\phi$\n\n### 定义二\n传递函数： $G(s)$ $s\\to j\\omega$\n$G(j\\omega)=|G(j\\omega)|e^{ j \\angle G(j\\omega) }$ \n\n输入信号： $A\\sin(\\omega t)$\n输出信号： $A|G(j\\omega)|\\sin(\\omega t+\\angle G(j\\omega))$\n幅频特性：$|G(j\\omega)|$\n相频特性： $\\angle G(j\\omega)$\n\n复数\\\n\n### 实际例题\n$\\arctan T_{1}+\\arctan T_{2}=90^{\\circ}$\n\n取正切函数，并利用两角和的正切公式，转为代数方程\n$$\\begin{align}\n & tan(\\arctan T_{1}+\\arctan T_{2})=\\infty \\\\\n & \\dfrac{\\tan(\\arctan T_{1})+\\tan(\\arctan T_{2})}{1-\\tan(\\arctan T_{1})\\tan(\\arctan T_{2})}=\\infty \\\\\n & \\dfrac{T_{1}+T_{2}}{1-T_{1}T_{2}}=\\infty \\; {\\color{red}\\Rightarrow} \\; T_{1}T_{2}=1\n\\end{align}$$"
    },
    "高阶系统的时域分析": {
      "id": "高阶系统的时域分析",
      "title": "高阶系统的时域分析",
      "category": "1. 经典控制理论",
      "subcategory": "1. 经典控制理论",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "$$\\begin{align}\ny(t)=1+\\sum\\limits_{i=1}^{q}A_{i}e^{ s_{i}t }+\\sum\\limits_{k=1}^{r}D_{k}e^{ -\\zeta_{k}\\omega _{nk}t }\\sin(\\omega _{dk}t+\\theta_{k})\n\\end{align}$$\n稳态分量+暂态分量 = 稳态分量+指数衰减+振荡衰减",
      "headings": [
        "单位阶跃响应",
        "主导极点"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-04-16T13:01:27.000+08:00",
      "updated": "2025-10-28T16:16:26.000+08:00",
      "permalink": "/A2- 控制理论/1. 经典控制理论/高阶系统的时域分析/",
      "dg_path": "A2- 控制理论/1. 经典控制理论/高阶系统的时域分析.md",
      "source_path": "src/site/notes/高阶系统的时域分析.md",
      "viewer_markdown_path": "../source-notes/高阶系统的时域分析.md",
      "internal_links": [
        "二阶系统的时域分析",
        "零极点"
      ],
      "inbound_links": [
        "经典控制理论",
        "零极点"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "### 单位阶跃响应\n\n$$\\begin{align}\ny(t)=1+\\sum\\limits_{i=1}^{q}A_{i}e^{ s_{i}t }+\\sum\\limits_{k=1}^{r}D_{k}e^{ -\\zeta_{k}\\omega _{nk}t }\\sin(\\omega _{dk}t+\\theta_{k})\n\\end{align}$$\n稳态分量+暂态分量 = 稳态分量+指数衰减+振荡衰减\n\n### 主导极点\n\n利用高阶系统的闭环主导零极点\\进行动态性能分析\n极点距虚轴的距离越近，对响应曲线的影响越明显。\n\n闭环主导极点：距离虚轴比较近，且附近没有其他的零点的极点 \n高阶系统常调整到使系统具有一对共轭复极点，可近似用二阶系统的动态性能指标来估算高阶系统的动态性能，转化为二阶系统的时域分析\\\n[!important] 注意！\n根据首一多项式（即零极点模型），先判断出闭环主导极点\n再将多项式化为 尾一多项式，保留 静态增益\n之后再将多项式降阶，对降阶后的系统分析"
    },
    "传递函数矩阵": {
      "id": "传递函数矩阵",
      "title": "传递函数矩阵",
      "category": "2. 现代控制理论",
      "subcategory": "2. 现代控制理论",
      "tags": [],
      "aliases": [],
      "terminology": "Transfer Function Matrix",
      "summary": "Transfer Function Matrix\n传递函数的矩阵形式，用来研究多输入-多输出系统，实际上反映了系统中线性系统的结构分解#三、按能控能观性分解\\的动力学行为\n[!important] Description\n前置知识：传递函数\\、矩阵\\、状态空间\\",
      "headings": [
        "一、传递函数矩阵基本概念",
        "二、子系统连接的传递函数矩阵",
        "并联连接",
        "串联连接",
        "反馈连接",
        "实际例题"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-10-08T22:50:19.930+08:00",
      "updated": "2025-08-29T10:31:20.000+08:00",
      "permalink": "/A2- 控制理论/2. 现代控制理论/传递函数矩阵/",
      "dg_path": "A2- 控制理论/2. 现代控制理论/传递函数矩阵.md",
      "source_path": "src/site/notes/传递函数矩阵.md",
      "viewer_markdown_path": "../source-notes/传递函数矩阵.md",
      "internal_links": [
        "传递函数",
        "状态空间",
        "线性系统的结构分解"
      ],
      "inbound_links": [
        "传递函数阵的实现问题",
        "状态空间表达式的能控标准型和能观标准型",
        "现代控制理论",
        "线性定常系统的能控性"
      ],
      "out_of_scope_links": [
        "矩阵"
      ],
      "missing_links": [],
      "content_excerpt": "Transfer Function Matrix\n传递函数的矩阵形式，用来研究多输入-多输出系统，实际上反映了系统中线性系统的结构分解#三、按能控能观性分解\\的动力学行为\n[!important] Description\n前置知识：传递函数\\、矩阵\\、状态空间\\\n\n### 一、传递函数矩阵基本概念\n传递函数矩阵：初始条件为零时，输出向量的拉普拉斯变换与输入向量的拉普拉斯变换式之间的传递关系。（类似与传递函数\\的定义）\n\n系统状态空间方程为：\n$$\\begin{align}\n\\dot{\\mathbf{x}}(t)&=A \\mathbf{x}(t)+ B\\mathbf{u}(t) \\\\\n\\mathbf{y}(t)&=C\\mathbf{x}(t)+D \\mathbf{u}(t)\n\\end{align}$$\n\n初始条件为零时，拉普拉斯变换为：\n$$\\begin{align}\ns\\mathbf{X}(s)=A\\mathbf{X}(s)+B\\mathbf{U}(s) \\\\\n\\mathbf{Y}(s)=C\\mathbf{X}(s)+D\\mathbf{U}(s)\n\\end{align}$$\n进一步整理得到：\n$$\\begin{gathered}\n\\mathbf{X}(s)=(sI-A)^{-1}B\\mathbf{U}(s) \\\\\n\\mathbf{Y}(s)=\\left[C(sI-A)^{-1}B+D\\right]\\mathbf{U}(s)\n\\end{gathered}$$\n\n最终得到系统的传递矩阵表达式为：\n$$\\begin{align}\nW(s)={\\color{red}C}{\\color{#7496ff}(sI-A)^{-1}}{\\color{red}B}+D\n\\end{align}$$\n\n$$\\begin{align}\n\\begin{pmatrix}\nY_{1}(s) \\\\\nY_{2}(s) \\\\\n\\vdots \\\\\nY_{m}(s)\n\\end{pmatrix}=\\begin{pmatrix}\n W_{11}(s) & \\cdots & W_{1r}(s) \\\\\n W_{21}(s) & \\cdots & W_{2r}(s) \\\\\n\\vdots & & \\vdots & \\\\\n W_{m1}(s) & \\cdots & W_{mr}(s) \\\\\n\\end{pmatrix}\\begin{pmatrix}\nU_{1}(s) \\\\\n\\vdots \\\\\nU_{r}(s)\n\\end{pmatrix}\n\\end{align}$$\n[!important] 注意\n计算传递函数矩阵要正确计算矩阵的逆，由于存在 $s$，只能使用伴随矩阵法求逆。\n\n### 二、子系统连接的传递函数矩阵\n\n#### 1. 并联连接\n子系统并联时，系统传递函数阵等于子系统传递函数阵的代数和\n$$\\begin{align}\nW(s)=W_{1}(s)\\pm W_{2}(s)\n\\end{align}$$\n#### 2. 串联连接\n子系统串联时，系统传递函数阵等于子系统传递函数阵之积（注意矩阵相乘的先后次序不能改变）\n$$\\begin{align}\nW(s)=W_{2}(s)W_{1}(s)\n\\end{align}$$\n#### 3. 反馈连接\n$$\\begin{align}\nW(s)=W_{1}(s)\\left[I+{\\color{red}W_{2}(s)W_{1}(s)}\\right]^{-1} \\\\\nW(s)=\\left[ I+ W_{1}(s)W_{2}(s)\\right]^{-1}W_{1}(s)\n\\end{align}$$\n\n也要注意矩阵乘法不满足交换律，注意乘的次序\n\n### 实际例题\n计算传递函数：\n$$\\begin{align}\nA=\\begin{pmatrix}\n0 & 1 & 0 \\\\\n-2 & -3 & 0 \\\\\n-1 & 1 & -3\n\\end{pmatrix}\\quad B=\\begin{pmatrix}\n0\\\\ 1 \\\\ 2\n\\end{pmatrix}\\quad C=\\begin{pmatrix}\n0 & 0 & 1\n\\end{pmatrix}\n\\end{align}$$\n\n$$\\begin{align}\nW(s)=C(sI-A)^{-1}B\n\\end{align}$$\n$$\\begin{align}\n(sI-A)^{-1}=\\begin{pmatrix}\ns & -1 & 0 \\\\\n2 & s+3 & 0 \\\\\n1 & -1 & s+3\n\\end{pmatrix}^{-1} & = \\dfrac{1}{(s+3)(s+2)(s+1)} \\begin{pmatrix}\n(s+3)^{2} & (s+3) & 0\\\\\n-2(s+3) & s(s+3) & 0 \\\\\n -(s+5)& s-1 & (s+2)(s+1)\n\\end{pmatrix}\n\\end{align}$$\n\n$$\\begin{align}\nC(sI-A)^{-1}B=\\dfrac{2(s+2)(s+1)+s-1}{(s+3)(s+2)(s+1)} =\\dfrac{2s+1}{(s+2)(s+1)}\n\\end{align}$$\n\n求闭环传递函数矩阵\n$$\\begin{align}\nW_{1}(s)=\\begin{pmatrix}\n\\dfrac{1}{s+1} & -\\dfrac{1}{s} \\\\\n0 & \\dfrac{1}{s+2}\n\\end{pmatrix}\\quad W_{2}(s)=I_{(2\\times2)}\n\\end{align}$$\n\n$$\\begin{align}\nW(s)=W_{1}(s)[I+W_{2}(s)W_{1}(s)]^{-1} & =\\begin{"
    },
    "传递函数阵的实现问题": {
      "id": "传递函数阵的实现问题",
      "title": "传递函数阵的实现问题",
      "category": "2. 现代控制理论",
      "subcategory": "2. 现代控制理论",
      "tags": [],
      "aliases": [
        "最小实现问题"
      ],
      "terminology": null,
      "summary": "(terminology:: Transfer Function Matrix Realization)\n多输入多输出系统的能控能观标准型。\n[!important] Description \n状态空间表达式的能控标准型和能观标准型\\的扩展延伸\n传递函数矩阵\\只能反映系统中能控且能观的子系统的动力学行为",
      "headings": [
        "一、实现的基本概念",
        "二、能控标准型和能观标准型实现",
        "能控标准型",
        "能观标准型",
        "三、最小实现",
        "传递函数零极点对消和能控能观性的关系"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-10-22T17:57:51.000+08:00",
      "updated": "2025-06-30T17:47:44.000+08:00",
      "permalink": "/A2- 控制理论/2. 现代控制理论/传递函数阵的实现问题/",
      "dg_path": "A2- 控制理论/2. 现代控制理论/传递函数阵的实现问题.md",
      "source_path": "src/site/notes/传递函数阵的实现问题.md",
      "viewer_markdown_path": "../source-notes/传递函数阵的实现问题.md",
      "internal_links": [
        "传递函数矩阵",
        "状态空间表达式的能控标准型和能观标准型",
        "线性系统的结构分解"
      ],
      "inbound_links": [
        "现代控制理论",
        "线性系统的结构分解"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "(terminology:: Transfer Function Matrix Realization)\n多输入多输出系统的能控能观标准型。\n[!important] Description \n状态空间表达式的能控标准型和能观标准型\\的扩展延伸\n传递函数矩阵\\只能反映系统中能控且能观的子系统的动力学行为\n\n### 一、实现的基本概念\n系统状态空间方程为：\n$$\\begin{align}\n\\dot{\\mathbf{x}}(t)&=A \\mathbf{x}(t)+ B\\mathbf{u}(t) \\\\\n\\mathbf{y}(t)&=C\\mathbf{x}(t)+D \\mathbf{u}(t)\n\\end{align}$$\n传递矩阵表达式为：\n$$\\begin{align}\nW(s)=C(sI-A)^{-1}B+D\n\\end{align}$$\n传递函数阵 $W(s)$ 可实现的条件：\n矩阵的元的分子分母的多项式系数均为实常数\n矩阵的元是 $s$ 的有理分式函数：分子多项式的次数低于或等于分母多项式的次数\n低于分母多项式的次数，实现具有 $(A,B,C)$ 的形式\n等于分母多项式的次数，实现具有 $(A,B,C,D)$ 的形式，$D=\\lim\\limits_{ s \\to \\infty } W(s)$\n 如果不为严格的真有理分式，可以先计算出 $D$，再寻求 $(A,B,C)$ 的形式的实现\n$$\\begin{align}\nW(s)-D=C(sI-A)^{-1}B\n\\end{align}$$\n### 二、能控标准型和能观标准型实现\n\n注意对于多输入多输出系统而言，能控和能观标准型并非是对偶关系（矩阵的维数不同）\n\n$$\\begin{align}\nW(s)=\\bar{\\mathbf{c}}(sI-\\bar{A}) ^{-1}\\bar{\\mathbf{b}} =\\dfrac{{\\boldsymbol{\\beta}}_{{n-1}}{s}^{n-1}+{\\boldsymbol{\\beta}}_{{n-2}}{s}^{n-2}+\\cdots+\\boldsymbol{\\beta}_{1}s+\\boldsymbol{\\beta}_{0}}{s^{n}+a_{n-1}s^{n-1}+\\cdots+a_{1}s+a_{0}}\n\\end{align}$$\n输入矢量的维度为 $r$，输出矢量的维度为 $m$，传递函数矩阵正是反映输入到输出的关系，所以为 $m\\times r$ 的矩阵（化为能控/能观标准型时，可以考虑选择维度更小的标准型）。\n\n#### 1. 能控标准型\n维数：$nr\\times nr$ 每一个元都为 $r\\times r$ 的矩阵\n\n$$\\begin{align}\nA_{c} & = \\begin{pmatrix}\n\\mathbf{0}_{r} & I_{r} & \\mathbf{0}_{r} & \\cdots & \\mathbf{0}_{r} \\\\\n\\mathbf{0}_{r} & \\mathbf{0}_{r} & I_{r} & \\cdots & \\mathbf{0}_{r} \\\\\n\\vdots & \\vdots & \\vdots & \\ddots & \\vdots \\\\\n\\mathbf{0}_{r} & \\mathbf{0}_{r} & \\mathbf{0}_{r} & \\cdots & I_{r} \\\\\n-a_{0}I_{r} & -a_{1}I_{r} & -a_{2}I_{r} & \\cdots & -a_{n-1}I_{r} \n\\end{pmatrix} \\\\\nB_{c} & =\\begin{pmatrix}\n\\mathbf{0}_{r} \\\\\\mathbf{0}_{r} \\\\\\vdots \\\\ I_{r} \n\\end{pmatrix}\\quad C_{c} =\\begin{pmatrix}\n\\boldsymbol{\\beta}_{0},\\boldsymbol{\\beta}_{1},\\cdots,\\boldsymbol{\\beta}_{n-1}\n\\end{pmatrix}\n\\end{align}$$\n\n#### 2. 能观标准型\n维数：$nm \\times nm$ 每一个元都为 $m\\times m$ 的矩阵\n$$\\begin{align}\nA_{o} & = \\begin{pmatrix}\n \\mathbf{0}_m & \\mathbf{0}_m & \\cdots & \\mathbf{0}_m & -a_{0}I_m \\\\\n I_m & \\mathbf{0}_m & \\cdots & \\mathbf{0}_m & -a_{1}I_m \\\\\n \\vdots & \\vdots & \\ddots & \\vdots & \\vdots\\\\\n \\mathbf{0}_m & \\mathbf{0}_m & \\cdots & I_m & -a_{n-1}I_m\\\\\n\\end{pmatrix} \\\\\nB_{o} & =\\begin{pmatrix}\n\\boldsymbol{\\beta}_{0}\\\\ \\boldsymbol{\\beta}_{1}\\\\\\vdots\\\\\\boldsymbol{\\beta}_{n-1}\n\\end{pmatrix} \\quad C_{o}=\\begin{pmatrix}\n\\mathbf{0}_m , \\mathbf{0}_m ,\\cdots , I_m \n\\end{pmatrix}\n\\end{align}$$\n\n### 三、最小实现\n\n传递函数矩阵只能反映系统中能控且能观的子系统的动力学行为，对于一个可实现的传递函数阵而言，有无穷多个状态空间表达式与之对应。\n\n最小实现实际上是对状态空间表达式进行线性系统的"
    },
    "李雅普诺夫方法在线性系统中的应用": {
      "id": "李雅普诺夫方法在线性系统中的应用",
      "title": "李雅普诺夫方法在线性系统中的应用",
      "category": "2. 现代控制理论",
      "subcategory": "2. 现代控制理论",
      "tags": [
        "Linear"
      ],
      "aliases": [],
      "terminology": null,
      "summary": "充要条件：对线性定常系统而言\n$Q>0$， $A^{T}P+PA=-Q$ 解出并判断 $P>0$ 则系统大范围渐进稳定\n$Q\\geq 0$， $A^{T}P+PA=-Q$ 解出并判断 $P>0$ 则系统稳定",
      "headings": [
        "一、线性定常连续系统",
        "~~二、线性时变连续系统~~",
        "~~三、线性定常离散系统~~",
        "~~四、线性时变离散系统~~"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-10-28T09:35:40.000+08:00",
      "updated": "2025-06-30T16:27:52.000+08:00",
      "permalink": "/A2- 控制理论/2. 现代控制理论/李雅普诺夫方法在线性系统中的应用/",
      "dg_path": "A2- 控制理论/2. 现代控制理论/李雅普诺夫方法在线性系统中的应用.md",
      "source_path": "src/site/notes/李雅普诺夫方法在线性系统中的应用.md",
      "viewer_markdown_path": "../source-notes/李雅普诺夫方法在线性系统中的应用.md",
      "internal_links": [
        "李雅普诺夫第二法"
      ],
      "inbound_links": [
        "现代控制理论"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "充要条件：对线性定常系统而言\n$Q>0$， $A^{T}P+PA=-Q$ 解出并判断 $P>0$ 则系统大范围渐进稳定\n$Q\\geq 0$， $A^{T}P+PA=-Q$ 解出并判断 $P>0$ 则系统稳定\n\n### 一、线性定常连续系统\n$$\\begin{align}\n\\dot{\\mathbf{x}}=A\\mathbf{x}\n\\end{align}$$\n平衡状态 $\\mathbf{x}_{e}=\\mathbf{0}$ 为大范围渐进稳定的充分必要条件： $A$ 的特征值均有负实部。\n等价于：对于任意给定的正定对称矩阵 $Q$ ，存在正定对称矩阵 $P>0$ ，使得 $A^{T}P+PA=-Q 0\\quad \\quad \\dot{V}(x)=-\\mathbf{x}^{T}Q\\mathbf{x} 0$，等价于 $A$ 的特征值均有负实部，也即认为系统在平衡点出大范围渐进稳定。\n如果只要求系统稳定，可以取 $Q$ 为半正定矩阵。\n\n### ~~二、线性时变连续系统~~\n$$\\begin{align}\n\\dot{\\mathbf{x}}=A(t)\\mathbf{x}\n\\end{align}$$\n系统在平衡点处大范围渐近稳定的充分必要条件：对于任意给定的连续对称正定矩阵 $Q(t)$，必存在一个连续对称矩阵 $P(t)$，满足：$\\dot{P}(t)=-A^{T}(t)P(t)-P(t)A(t)-Q(t)$\n李雅普诺夫函数为：$V(\\mathbf{x},t)=\\mathbf{x}^{T}(t)P(t)\\mathbf{x}(t)$\n\nRiccati 矩阵微分方程的解（理论结果漂亮，但是不要求掌握，主要还是李雅普诺夫第二法\\求解）\n\n### ~~三、线性定常离散系统~~\n$$\\begin{align}\n\\mathbf{x}(k+1)=G\\mathbf{x}(k)\n\\end{align}$$\n\n则平衡状态处渐近稳定的充分必要条件：$G$ 的特征根均在单位开圆盘内。\n等价于：存在对称矩阵 $P>0$，使得 $G^{T}PG-P=-Q 0$\n$$\\begin{align}\nG^{T}(k+1,k)P(k+1)G(K+1,k)-P(k)=-Q(k)\n\\end{align}$$\n$$\\begin{align}\nV[\\mathbf{x}(k),k]=\\mathbf{x}^{T}(k)P(k)\\mathbf{x}(k)\n\\end{align}$$"
    },
    "李雅普诺夫方法在非线性系统中的应用": {
      "id": "李雅普诺夫方法在非线性系统中的应用",
      "title": "李雅普诺夫方法在非线性系统中的应用",
      "category": "2. 现代控制理论",
      "subcategory": "2. 现代控制理论",
      "tags": [
        "Nonlinear"
      ],
      "aliases": [],
      "terminology": null,
      "summary": "非线性系统的稳定性可能只有局部性质\n且李雅普诺夫第二法\\只能给出非线性系统渐近稳定的充分条件，而非必要条件，求解较为简单，如果无法找到李雅普诺夫函数才使用下述方法。\n### 一、雅可比矩阵法/克拉索夫斯基法\n理论基础：雅可比矩阵\\，寻找线性系统李雅普诺夫函数的推广方法。\n$$\\begin{align}\n \\dot{\\mathbf{x}}=\\mathbf{f}(\\mathbf{x})\\quad \\mathbf{J}(\\mathbf{x})= \\dfrac{\\partial \\m",
      "headings": [
        "一、雅可比矩阵法/克拉索夫斯基法",
        "~~二、变量梯度法/舒茨-基布逊法~~"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-11-10T23:37:14.000+08:00",
      "updated": "2025-05-23T17:12:08.000+08:00",
      "permalink": "/A2- 控制理论/2. 现代控制理论/李雅普诺夫方法在非线性系统中的应用/",
      "dg_path": "A2- 控制理论/2. 现代控制理论/李雅普诺夫方法在非线性系统中的应用.md",
      "source_path": "src/site/notes/李雅普诺夫方法在非线性系统中的应用.md",
      "viewer_markdown_path": "../source-notes/李雅普诺夫方法在非线性系统中的应用.md",
      "internal_links": [
        "李雅普诺夫第二法"
      ],
      "inbound_links": [
        "现代控制理论"
      ],
      "out_of_scope_links": [
        "旋度",
        "梯度",
        "雅可比矩阵"
      ],
      "missing_links": [],
      "content_excerpt": "非线性系统的稳定性可能只有局部性质\n且李雅普诺夫第二法\\只能给出非线性系统渐近稳定的充分条件，而非必要条件，求解较为简单，如果无法找到李雅普诺夫函数才使用下述方法。\n### 一、雅可比矩阵法/克拉索夫斯基法\n理论基础：雅可比矩阵\\，寻找线性系统李雅普诺夫函数的推广方法。\n$$\\begin{align}\n \\dot{\\mathbf{x}}=\\mathbf{f}(\\mathbf{x})\\quad \\mathbf{J}(\\mathbf{x})= \\dfrac{\\partial \\mathbf{f}(\\mathbf{x})}{\\partial \\mathbf{x}} = \\begin{pmatrix} \\dfrac{\\partial f_1}{\\partial x_1} & \\dfrac{\\partial f_1}{\\partial x_2} & \\cdots & \\dfrac{\\partial f_1}{\\partial x_n} \\\\ \\dfrac{\\partial f_2}{\\partial x_1} & \\dfrac{\\partial f_2}{\\partial x_2} & \\cdots & \\dfrac{\\partial f_2}{\\partial x_n} \\\\ \\vdots & \\vdots & \\ddots & \\vdots \\\\ \\dfrac{\\partial f_m}{\\partial x_1} & \\dfrac{\\partial f_m}{\\partial x_2} & \\cdots & \\dfrac{\\partial f_m}{\\partial x_n} \\end{pmatrix} \n\\end{align}$$\n\n在原点渐近稳定的 充分条件是：对于任意给定的实对称矩阵 $P$，使得矩阵 $Q(x)=-[J^{T}(\\mathbf{x})P+PJ(\\mathbf{x})]$ 为正定矩阵，李雅普诺夫函数： $V(\\mathbf{x})=\\mathbf{f}^{T}(\\mathbf{x})P\\mathbf{f}(\\mathbf{x})$\n\n实际计算一般设 $P=I$，$Q>0$ 则系统在平衡点处渐近稳定\n$$\\begin{align}\nQ(\\mathbf{x})=-\\left[J^{T}(\\mathbf{x})+J(\\mathbf{x})\\right]>0\n\\end{align}$$\n\n$$\\begin{align}\nV(\\mathbf{x})=\\mathbf{f}^{T}(\\mathbf{x})\\mathbf{f}(\\mathbf{x})\\to \\infty \\quad (\\left\\lvert \\left\\lvert \\mathbf{x} \\right\\rvert\\right\\rvert \\to \\infty)\n\\end{align}$$\n则进一步有大范围渐近稳定\n\n### ~~二、变量梯度法/舒茨-基布逊法~~\n理论基础：梯度\\ 旋度\\\n$$\\begin{align}\n\\nabla V = \\dfrac{\\partial V}{\\partial \\mathbf{x}} =\\begin{pmatrix}\n\\dfrac{\\partial V}{\\partial x_{1}}\\\\ \\dfrac{\\partial V}{\\partial x_{2}} \\\\ \\vdots\\\\\\dfrac{\\partial V}{\\partial x_{n}} \n\\end{pmatrix} =grad \\; V(\\mathbf{x})\n\\end{align}$$\n\n$$\\begin{align}\n\\dot{V}(\\mathbf{x})= (\\dfrac{\\partial V}{\\partial x_{1}}, \\dfrac{\\partial V}{\\partial x_{2}},\\cdots,\\dfrac{\\partial V}{\\partial x_{n}} ) \\begin{pmatrix}\n\\dot{x}_{1} \\\\\\dot{x}_{2}\\\\ \\vdots \\\\ \\dot{x}_{n}\n\\end{pmatrix} =\\left[\\;\\nabla V\\;\\right]^{T} \\mathbf{\\dot{x}}\n\\end{align}$$\n\n$$\\begin{align}\nV(\\mathbf{x})=\\int _{0}^{\\mathbf{x}} (\\nabla V)^{T}\\, d\\mathbf{\\mathbf{x}}=\\int _{0}^{x_{1}(x_{2}=\\cdots=x_{n}=0)} \\nabla V_{1}\\, dx_{1} +\\int _{0}^{x_{2}(x_{1}=x_{1},x_{3}=\\cdots=x_{n}=0)} \\nabla V_{2}\\, dx_{2} +\\cdots+ \\int _{0}^{x_{n}(x_{1}=x_{1},\\cdots,x_{n-1}=x_{n-1})} \\nabla V_{n}\\, dx_{n} \n\\end{align}$$"
    },
    "李雅普诺夫稳定性理论": {
      "id": "李雅普诺夫稳定性理论",
      "title": "李雅普诺夫稳定性理论",
      "category": "2. 现代控制理论",
      "subcategory": "2. 现代控制理论",
      "tags": [],
      "aliases": [],
      "terminology": "Lyapunov Stability Theory",
      "summary": "Lyapunov Stability Theory\n稳定是系统分析的前提，是系统正常工作的必要条件。\n李雅普诺夫稳定性分析适用于几乎所有系统的稳定性分析，是稳定性问题解决的最基本方法。在此基础上衍生了多种稳定性判别方法。\n[!important] Description \n前置知识：范数\\ 线性系统稳定性分析\\",
      "headings": [
        "一、稳定性理论基础",
        "二、李雅普诺夫稳定性",
        "稳定",
        "渐近稳定",
        "全局渐近稳定 （大范围渐进稳定）"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-10-04T14:40:36.000+08:00",
      "updated": "2025-08-29T10:41:10.000+08:00",
      "permalink": "/A2- 控制理论/2. 现代控制理论/李雅普诺夫稳定性理论/",
      "dg_path": "A2- 控制理论/2. 现代控制理论/李雅普诺夫稳定性理论.md",
      "source_path": "src/site/notes/李雅普诺夫稳定性理论.md",
      "viewer_markdown_path": "../source-notes/李雅普诺夫稳定性理论.md",
      "internal_links": [
        "线性系统稳定性分析"
      ],
      "inbound_links": [
        "李雅普诺夫第二法",
        "现代控制理论",
        "线性系统稳定性分析"
      ],
      "out_of_scope_links": [
        "范数"
      ],
      "missing_links": [],
      "content_excerpt": "Lyapunov Stability Theory\n稳定是系统分析的前提，是系统正常工作的必要条件。\n李雅普诺夫稳定性分析适用于几乎所有系统的稳定性分析，是稳定性问题解决的最基本方法。在此基础上衍生了多种稳定性判别方法。\n[!important] Description \n前置知识：范数\\ 线性系统稳定性分析\\\n\n### 一、稳定性理论基础\n稳定性是自动控制系统最重要的特征：1. 判别系统是否稳定 2. 改善系统的稳定性\n\n平衡点：导数为零的点\n极限环：在极限环内渐进稳定，极限环外不稳定\n线性系统的稳定性：只取决于系统的结构和参数。\n $\\dot{x}=Ax$，实际上平衡点就是 $Ax=0$ 。线性定常系统仅需要看系统矩阵，如果系统矩阵非奇异，仅有一个平衡点$\\mathbf{0}$；系统矩阵奇异，有无穷多个平衡点。\n非线性系统的稳定性：和系统的结构和参数、初始条件、外界扰动的大小均有关。\n 非线性系统各导数为零求出平衡点。一般有一到多个平衡点，不同的平衡点可能表现不同的稳定性，需要逐个分别讨论。\n\n### 二、李雅普诺夫稳定性\n不稳定 稳定 --> 渐近稳定 --> 全局渐近稳定\n\n只讨论坐标原点的稳定解情况（都可通过坐标变换转化到原点）\n$$\\begin{align}\n\\dot{\\mathbf{x}}=f(\\mathbf{x},t)\\quad \\mathbf{x}= \\varPhi(t;\\mathbf{x}_{0},t_{0})\n\\end{align}$$\n$$\\begin{align}\n\\left\\lvert \\left\\lvert \\mathbf{x}_{}-\\mathbf{x}_{e} \\right\\rvert \\right\\rvert=\\left\\lvert \\left\\lvert \\varPhi(t;\\mathbf{x}_{0},t_{0})-\\mathbf{x}_{e}\\right\\rvert \\right\\rvert =\\sqrt{ \\left[(x_{1}-x_{1e})^{2}+\\cdots+(x_{n}-x_{ne})^{2}\\right] }\\leq \\varepsilon\n\\end{align}$$\n\n#### 1. 稳定\n随着时间的增长，系统响应的幅值是有界的\n$$\\begin{align}\n\\left\\lvert \\left\\lvert \\varPhi(t;\\mathbf{x}_{0},t_{0})-\\mathbf{x}_{e} \\right\\rvert \\right\\rvert\\leq \\varepsilon\\quad t_{0}\\leq t<\\infty\n\\end{align}$$\n\n#### 2. 渐近稳定\n首先要稳定，且随时间无限增长，状态轨线最终趋于平衡状态 $\\mathbf{x}_{e}$\n$$\\begin{align}\n\\lim\\limits_{ t \\to \\infty } \\left\\lvert \\left\\lvert \\mathbf{x}(t;\\mathbf{x}_{0},t_{0})-\\mathbf{x}_{e} \\right\\rvert \\right\\rvert=0\n\\end{align}$$\n经典控制理论下的稳定系统实际上为渐近稳定系统\n只在李雅普诺夫意义下稳定的称为临界稳定系统，在工程上属于不稳定系统\n\n#### 3. 全局渐近稳定 （大范围渐进稳定）\n平衡状态稳定，只有一个稳定点，从所有初始状态出发的状态轨线都具有渐进稳定性。\n（对于线性系统：平衡状态渐近稳定，则必然大范围渐近稳定。）"
    },
    "李雅普诺夫第一法": {
      "id": "李雅普诺夫第一法",
      "title": "李雅普诺夫第一法",
      "category": "2. 现代控制理论",
      "subcategory": "2. 现代控制理论",
      "tags": [
        "Linear",
        "Nonlinear"
      ],
      "aliases": [],
      "terminology": "Lyapunov's First Method",
      "summary": "Lyapunov's First Method\n间接法，利用系统矩阵的特征值或系统状态方程的解来判断系统稳定性。主要针对线性定常系统和非线性不是很严重的系统",
      "headings": [
        "一、线性定常系统",
        "1 状态稳定（内部稳定）",
        "2 输出稳定",
        "二、非线性系统（线性化）",
        "实际例题"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-10-28T09:46:07.000+08:00",
      "updated": "2025-08-29T10:41:46.000+08:00",
      "permalink": "/A2- 控制理论/2. 现代控制理论/李雅普诺夫第一法/",
      "dg_path": "A2- 控制理论/2. 现代控制理论/李雅普诺夫第一法.md",
      "source_path": "src/site/notes/李雅普诺夫第一法.md",
      "viewer_markdown_path": "../source-notes/李雅普诺夫第一法.md",
      "internal_links": [
        "李雅普诺夫第二法"
      ],
      "inbound_links": [
        "现代控制理论"
      ],
      "out_of_scope_links": [
        "雅可比矩阵"
      ],
      "missing_links": [],
      "content_excerpt": "Lyapunov's First Method\n间接法，利用系统矩阵的特征值或系统状态方程的解来判断系统稳定性。主要针对线性定常系统和非线性不是很严重的系统\n\n### 一、线性定常系统\n#### 1. 1 状态稳定（内部稳定）\n在平衡状态渐近稳定\n充分必要条件：系统矩阵 $A$ 所有特征值均具有负实部 $\\left\\lvert \\lambda I-A \\right\\rvert=0\\quad\\lambda_{i}<0$\n\n#### 1. 2 输出稳定\n输出稳定：系统对于有界输入所引起的输出是有界的。\n充分必要条件：传递函数的极点均具有负实部 (在 $s$ 左半平面) $W(s)=c(sI-A)^{-1}b\\quad Re \\;s_{i}<0$\n\n虽然状态矩阵的特征值和传递函数矩阵分母的根（极点）相同，但是传递函数可能出现零极点对消现象，使得状态稳定性和输出稳定性可能不一致。状态不稳定时，可能也会有输出稳定。\n\n### 二、非线性系统（线性化）\n\n$$\\begin{align}\n\\dot{\\mathbf{x}}=f(\\mathbf{x}) \\quad \\Rightarrow \\quad \\dot{\\mathbf{x}}=\\mathbf{f}(\\mathbf{x}_{e},t)+\\left. \\dfrac{\\partial \\mathbf{f}}{\\partial \\mathbf{x}} \\right\\rvert_{\\mathbf{x}=\\mathbf{x}_{e}}(\\mathbf{x}-\\mathbf{x}_{e})+R(x)\n\\end{align}$$\n$$\\begin{align}\n\\Delta \\mathbf{x}=\\mathbf{x}-\\mathbf{x}_{e}\\quad \\Rightarrow \\quad \\Delta \\mathbf{\\dot{x}}=A\\Delta \\mathbf{x}\n\\end{align}$$\n确定系统的平衡点，所有状态变量的导数为零的点，也即联立方程 $\\mathbf{0}=f(\\mathbf{x})$ 求解\n使用雅可比矩阵\\将非线性系统一次线性化，得到线性化的状态矩阵 $A$ 表达式\n在不同平衡点处，分别代入平衡点，得到对应的状态矩阵 $A$\n\n$$ \\dfrac{\\partial \\mathbf{f}}{\\partial \\mathbf{x}} = \\begin{pmatrix} \\dfrac{\\partial f_1}{\\partial x_1} & \\dfrac{\\partial f_1}{\\partial x_2} & \\cdots & \\dfrac{\\partial f_1}{\\partial x_n} \\\\ \\dfrac{\\partial f_2}{\\partial x_1} & \\dfrac{\\partial f_2}{\\partial x_2} & \\cdots & \\dfrac{\\partial f_2}{\\partial x_n} \\\\ \\vdots & \\vdots & \\ddots & \\vdots \\\\ \\dfrac{\\partial f_m}{\\partial x_1} & \\dfrac{\\partial f_m}{\\partial x_2} & \\cdots & \\dfrac{\\partial f_m}{\\partial x_n} \\end{pmatrix}\\quad A= \\left. \\dfrac{\\partial \\mathbf{f}}{\\partial \\mathbf{x}} \\right\\rvert_{\\mathbf{x}=\\mathbf{x}_{e}} $$\n\n线性化后得到特征矩阵，计算矩阵的特征值\n所有特征值均具有负实部，原非线性系统在平衡点处渐近稳定\n至少有一个特征值具有正实部，原非线性系统不稳定\n至少有一个特征值为零，不能根据特征矩阵判别原非线性系统的稳定性，只能看高阶导数项（较为复杂，很难判断，最为不利的情况），无法确定\n在非线性系统稳定性分析存在瓶颈，不建议使用，建议使用李雅普诺夫第二法\\\n\n### 实际例题\n$$\\begin{cases}\n\\dot{x}_{1}=x_{1}-x_{1}x_{2} \\\\\n\\dot{x}_{2}=-x_{2}+x_{1}x_{2}\n\\end{cases}$$\n\n平衡点\n$$\\begin{align}\n\\begin{cases}\n0=x_{1}-x_{1}x_{2} \\\\\n0=-x_{2}+x_{1}x_{2}\n\\end{cases}\n\\end{align}\\Rightarrow x_{e_{1}}=\\begin{pmatrix}\n0 \\\\\n0\n\\end{pmatrix},x_{e_{2}}=\\begin{pmatrix}\n1\\\\ 1\n\\end{pmatrix}$$\n\n$$\\begin{align}\nA=\\begin{pmatrix}\n1-x_{2} & -x_{1}\\\\ x_{2} & -1+x_{1}\n\\end{pmatrix}\n\\end{align}\\Rightarrow A_{1}=\\begin{pmatrix}\n1 & 0\\\\ 0 & -1\n\\end{pmatrix}\\quad A_{2}=\\begin{pmatrix}\n0 & -1 \\\\ 1 & 0\n\\end{pmatrix}$$"
    },
    "李雅普诺夫第二法": {
      "id": "李雅普诺夫第二法",
      "title": "李雅普诺夫第二法",
      "category": "2. 现代控制理论",
      "subcategory": "2. 现代控制理论",
      "tags": [
        "Nonlinear",
        "Linear"
      ],
      "aliases": [],
      "terminology": "Lyapunov's Second Method",
      "summary": "Lyapunov's Second Method\n直接法：构造李雅普诺夫函数从能量的观点进行稳定性分析\n[!important] Description \n前置知识：对称矩阵\\ 二次型\\ 能\\ 偏导数\\ 状态空间\\ 李雅普诺夫稳定性理论\\ \n相关：神经网络的稳定性\\",
      "headings": [
        "一、标量函数的符号性质",
        "标量函数的符号性质",
        "二次型标量函数的符号性质",
        "希尔维斯特判据",
        "二、稳定性判据",
        "2.1. 李雅普诺夫函数",
        "2.2 李雅普诺夫函数的时间导数",
        "2.3 稳定性判断",
        "实际例题"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-10-28T09:46:04.000+08:00",
      "updated": "2025-08-29T11:05:00.000+08:00",
      "permalink": "/A2- 控制理论/2. 现代控制理论/李雅普诺夫第二法/",
      "dg_path": "A2- 控制理论/2. 现代控制理论/李雅普诺夫第二法.md",
      "source_path": "src/site/notes/李雅普诺夫第二法.md",
      "viewer_markdown_path": "../source-notes/李雅普诺夫第二法.md",
      "internal_links": [
        "李雅普诺夫稳定性理论",
        "状态空间"
      ],
      "inbound_links": [
        "李雅普诺夫方法在线性系统中的应用",
        "李雅普诺夫方法在非线性系统中的应用",
        "李雅普诺夫第一法",
        "现代控制理论"
      ],
      "out_of_scope_links": [
        "二次型",
        "偏导数",
        "对称矩阵"
      ],
      "missing_links": [
        "神经网络的稳定性",
        "能"
      ],
      "content_excerpt": "Lyapunov's Second Method\n直接法：构造李雅普诺夫函数从能量的观点进行稳定性分析\n[!important] Description \n前置知识：对称矩阵\\ 二次型\\ 能\\ 偏导数\\ 状态空间\\ 李雅普诺夫稳定性理论\\ \n相关：神经网络的稳定性\\\n\n### 一、标量函数的符号性质\n#### 1. 标量函数的符号性质\n$V(\\mathbf{x})$ 为 $n$ 维矢量 $\\mathbf{x}$ 定义的标量函数，$\\mathbf{x} \\in \\Omega$，$V(\\mathbf{0})\\equiv \\mathbf{0}$，且对于 $\\mathbf{x}\\neq \\mathbf{0}$ 有：\n$V(\\mathbf{x})>0$ 正定 $V(\\mathbf{x})\\geq0$ 半正定\n$V(\\mathbf{x}) 0,V(\\mathbf{x}) 0$，所有特征值均大于零\n$P$ 负定，$V(\\mathbf{x})$ 负定，$P 0$\n矩阵负定：$\\Delta _{i}=\\begin{cases} 0\\quad \\text{i 为偶数} \\end{cases}$\n\n### 二、稳定性判据\n如果沿状态轨线方向计算的时间导数 $\\dfrac{\\mathrm{d} V (\\mathbf{x})}{\\mathrm{d} t}$ 是负定的，则系统为渐进稳定的。\n\n#### 2.1. 李雅普诺夫函数\n李雅普诺夫函数：\n定义的一个正定的标量函数 $V(\\mathbf{x})$ 作为虚构的能量函数 （$x=0,V(x)=0; x\\neq 0,V(x)>0$）\n对所有的状态变量 $\\mathbf{x}$ 都具有一阶连续偏导数。\n\n要根据系统结构参数选取，不过一般可以考虑 $V(\\mathbf{x})=\\mathbf{x}_{1}^{2}+\\mathbf{x}_{2}^{2}+\\cdots+\\mathbf{x}^{2}_{n}$\n只能表示系统在平衡状态附近某邻域内的局部运动的稳定情况。\n\n#### 2.2 李雅普诺夫函数的时间导数\n李雅普诺夫函数沿状态轨线方向计算的时间导数 $\\dfrac{\\mathrm{d} V (\\mathbf{x})}{\\mathrm{d} t}$：\n\n$$\\begin{align}\n {\\color{red} \\dot{V}(\\mathbf{x})}=\\dfrac{\\mathrm{d} V(\\mathbf{x})}{\\mathrm{d} t} = \\dfrac{\\partial V}{\\partial \\mathbf{x}} \\dfrac{\\mathrm{d} \\mathbf{x}}{\\mathrm{d} t} =\\sum\\limits_{i=1}^{n} \\dfrac{\\partial V}{\\partial {x}_{i}} \\dfrac{\\mathrm{d} x_{i}}{\\mathrm{d} t} =\\color{red} \\sum\\limits_{i=1}^{n} \\dfrac{\\partial V}{\\partial {x}_{i}} \\times\\dot{x}_{i}\n\\end{align}$$\n\n#### 2.3 稳定性判断\n如果时间导数正负定判定为：\n半负定：一般而言可以判定系统稳定（不一定渐进稳定）\n如果除去 $\\mathbf{x}=\\mathbf{0}$ 外，$\\dot{V}(\\mathbf{x})$ 不恒为零，则原点平衡状态是渐进稳定的\n如果 $\\dot{V}(\\mathbf{x})$ 恒为零，运动轨迹不会收敛于原点，会落到某个特定曲面（超球面/极限环） $V(\\mathbf{x})=C$ 上，只是稳定，而非渐进稳定\n负定：原点平衡状态渐进稳定。当 $\\left\\lvert \\left\\lvert \\mathbf{x} \\right\\rvert \\right\\rvert \\to \\infty,V(\\mathbf{x})\\to \\infty$，则进一步得到系统大范围渐进稳定\n正定：系统不稳定\n\n对于给定系统，如果能找到满足判据条件的函数就能对系统稳定性进行肯定的判断。但是只是充分*而非必要的，如果找不到，就不能判断稳定性。\n\n### 实际例题\n$$\\begin{align}\nV(\\mathbf{x})=x_{1}^{2}+x_{2}^{2}>0\\quad \\dot{V}(\\mathbf{x})=2x_{1}\\dot{x}_{1}+2x_{2}\\dot{x}_{2}\n\\end{align}$$"
    },
    "极点配置与系统镇定": {
      "id": "极点配置与系统镇定",
      "title": "极点配置与系统镇定",
      "category": "2. 现代控制理论",
      "subcategory": "2. 现代控制理论",
      "tags": [],
      "aliases": [],
      "terminology": "Pole Configuration",
      "summary": "Pole Configuration System Stabilization\n控制系统的性能主要取决于系统极点在根平面上的分布，给定一组极点或根据时域指标转换为一组等价的期望极点，作为综合系统性能指标的一种形式。\n[!important] Description \n前置知识：根轨迹法基础\\ 线性反馈系统的基本结构\\",
      "headings": [
        "一、极点配置",
        "采用状态反馈",
        "采用从输出到状态变量导数的反馈",
        "~~3. 采用输出反馈或动态补偿器（简略）~~",
        "二、系统镇定",
        "实际例题"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-11-06T12:42:21.000+08:00",
      "updated": "2025-09-26T11:50:56.000+08:00",
      "permalink": "/A2- 控制理论/2. 现代控制理论/极点配置与系统镇定/",
      "dg_path": "A2- 控制理论/2. 现代控制理论/极点配置与系统镇定.md",
      "source_path": "src/site/notes/极点配置与系统镇定.md",
      "viewer_markdown_path": "../source-notes/极点配置与系统镇定.md",
      "internal_links": [
        "根轨迹法基础",
        "状态空间表达式的能控标准型和能观标准型",
        "线性反馈系统的基本结构"
      ],
      "inbound_links": [
        "状态观测器",
        "现代控制理论"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "Pole Configuration System Stabilization\n控制系统的性能主要取决于系统极点在根平面上的分布，给定一组极点或根据时域指标转换为一组等价的期望极点，作为综合系统性能指标的一种形式。\n[!important] Description \n前置知识：根轨迹法基础\\ 线性反馈系统的基本结构\\\n\n极点实际上只取决于系统矩阵，而经过反馈，可以改变系统矩阵\n核心就是设计反馈矩阵，使得反馈后的特征多项式等于期望极点系统对应的多项式。\n如果维数较低，可以直接比较特征多项式，而无需化为标准型；\n如果系统直接写为标准型，则也可直接得到反馈增益矩阵\n\n### 一、极点配置\n#### 1. 采用状态反馈\n\n采用状态反馈对系统任意配置极点的充分必要条件为系统完全能控\n首先要进行能控性判别\n将系统进行线性变换 $T_{c_{1}}$ 转化为状态空间表达式的能控标准型和能观标准型\\\n设出线性变换后的状态反馈增益矩阵 $\\bar{K}=T_{c_{1}}K=\\begin{pmatrix}\\bar{k}_{0}\\quad \\bar{k}_{1}\\quad \\cdots \\quad \\bar{k}_{n-1} \\end{pmatrix}$\n\n$$\\begin{align}\n\\mathbf{u}=K \\mathbf{x} +\\mathbf{v} \\quad \\dot{\\mathbf{x}}=A\\mathbf{x}+ B(\\mathbf{v}+K\\mathbf{x})=({\\color{red} A+BK})\\mathbf{x}+B\\mathbf{v} \n\\end{align}$$\n\n原系统：\n\n$$\\begin{align}\n\\det \\left[ \\lambda I-A\\right] =f(\\lambda)= \\prod\\limits_{i=1}^{n}(\\lambda-\\lambda_{i})=\\lambda^{n}+a_{n-1}\\lambda^{n-1}+\\cdots +a_{1}\\lambda+a_{0}\n\\end{align}$$\n\n期望极点系统：\n\n$$\\begin{align}\nf^{}(\\lambda)= \\prod\\limits_{i=1}^{n}(\\lambda-\\lambda_{i}^{})=\\lambda^{n}+a_{n-1}^{}\\lambda^{n-1}+\\cdots +a_{1}^{}\\lambda+a_{0}^{}\n\\end{align}$$\n\n设计线性变换后的反馈矩阵 $\\bar{K}$ 系统：\n\n$$\\begin{align}\n\\det \\left[ \\lambda I-({\\color{red} A+BK})\\right]= \\prod\\limits_{i=1}^{n}(\\lambda-\\lambda_{i}^{})=\\lambda^{n}+(a_{n-1}-\\bar{k}_{n-1})\\lambda^{n-1}+\\cdots +(a_{1}-\\bar{k}_{1})\\lambda+(a_{0}-\\bar{k}_{0})\n\\end{align}$$\n\n$$\\begin{align}\nT_{c_{1}}={\\color{red}\\begin{pmatrix}\nA^{n-1}\\mathbf{b} & A^{n-2}\\mathbf{b} & \\cdots & A\\mathbf{b} & \\mathbf{b}\n\\end{pmatrix} }\\begin{pmatrix}\n1 \\\\\na_{n-1} & 1 \\\\\n\\vdots & \\vdots & \\ddots \\\\\na_{2} & a_{3} & \\cdots & 1 \\\\\na_{1} & a_{2} & \\cdots & a_{n-1} & 1\n\\end{pmatrix}\n\\end{align}$$\n\n$$\\begin{align}\n\\bar{A} & =T_{c_{1}}^{-1}AT_{c_{1}}= \\begin{pmatrix}\n0 & 1 & 0 & \\cdots & 0 \\\\\n0 & 0 & 1 & \\cdots & 0 \\\\\n\\vdots & \\vdots & \\vdots & \\ddots & \\vdots \\\\\n0 & 0 & 0 & \\cdots & 1 \\\\\n-a_{0} & -a_{1} & -a_{2} & \\cdots & -a_{n-1}\n\\end{pmatrix} \\\\\n\\bar{\\mathbf{b}} & =T_{c_{1}}^{-1}\\mathbf{b}=\\begin{pmatrix}\n0 \\\\0 \\\\\\vdots \\\\ 1 \n\\end{pmatrix} \\quad \\bar{\\mathbf{c}} =\\mathbf{c} T_{c_{1}} =\\begin{pmatrix}\n\\beta_{0},\\beta_{1},\\cdots,\\beta_{n-1}\n\\end{pmatrix}\n\\end{align}$$\n\n$$\\begin{align}\n\\bar{A}+\\bar{b}\\bar{K}= \\begin{pmatrix}\n0 & 1 & 0 & \\cdots & 0 \\\\\n0 & 0 & 1 & \\cdots & 0 \\\\\n\\vdots & \\vdots & \\vdots & \\ddots & \\vdots \\\\\n0 & 0 & 0 & \\cdots & 1 \\\\\n-a_{0}+\\bar{k}_{0} & -a_{1}+\\bar{k}_{1} & -a_{2}+\\bar{k}_{2} & \\cdots & -a_{n-1}+\\bar{k}_{n-1}\n\\end{pmatrix}\n\\end{align"
    },
    "状态向量的线性变换": {
      "id": "状态向量的线性变换",
      "title": "状态向量的线性变换",
      "category": "2. 现代控制理论",
      "subcategory": "2. 现代控制理论",
      "tags": [],
      "aliases": [
        "状态空间表达式Jordan标准化,系统特征值及系统的不变量"
      ],
      "terminology": "Linear Transformation of State Vectors",
      "summary": "Linear Transformation of State Vectors\n状态空间表达式进行线性变换变为标准型的基础。\n[!important] Description \n前置知识：特征值和特征向量\\ 矩阵对角化\\ 状态空间\\ 线性变换\\\n特殊矩阵：Jordan矩阵\\ 友矩阵\\ 范德蒙德矩阵\\",
      "headings": [
        "一、基本概念",
        "一、系统矩阵为任意矩阵（通用形式）",
        "特征值无重根",
        "特征值有重根",
        "二、系统矩阵为友矩阵（标准型/特殊形式）",
        "特征值无重根",
        "特征值有重根",
        "三、并联型实现 （约旦标准型实现）",
        "无重根",
        "有重根"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-10-04T19:02:03.000+08:00",
      "updated": "2025-06-30T17:49:00.000+08:00",
      "permalink": "/A2- 控制理论/2. 现代控制理论/状态向量的线性变换/",
      "dg_path": "A2- 控制理论/2. 现代控制理论/状态向量的线性变换.md",
      "source_path": "src/site/notes/状态向量的线性变换.md",
      "viewer_markdown_path": "../source-notes/状态向量的线性变换.md",
      "internal_links": [
        "状态空间"
      ],
      "inbound_links": [
        "状态空间表达式的能控标准型和能观标准型",
        "现代控制理论",
        "线性定常状态方程的解",
        "线性定常系统的能控性",
        "线性定常系统的能观性"
      ],
      "out_of_scope_links": [
        "友矩阵",
        "有理函数",
        "特征值和特征向量",
        "矩阵对角化",
        "线性变换"
      ],
      "missing_links": [
        "Jordan矩阵",
        "范德蒙德矩阵"
      ],
      "content_excerpt": "Linear Transformation of State Vectors\n状态空间表达式进行线性变换变为标准型的基础。\n[!important] Description \n前置知识：特征值和特征向量\\ 矩阵对角化\\ 状态空间\\ 线性变换\\\n特殊矩阵：Jordan矩阵\\ 友矩阵\\ 范德蒙德矩阵\\\n\n### 一、基本概念\n\n$$\\begin{cases}\n\\dot{\\mathbf{x}} =A\\mathbf{x}+B\\mathbf{u} \\\\\n\\mathbf{y}=C\\mathbf{x}+D\\mathbf{u}\n\\end{cases}$$\n系统的特征值：就是系统矩阵 $A$ 的特征值和特征向量\\，也就是特征方程 $\\left\\lvert \\lambda I-A \\right\\rvert=0$ 的根。\n系统的不变量： 特征多项式 $\\left\\lvert \\lambda I-A \\right\\rvert=0$ 的系数（唯一地确定系统的特征值）\n\n经过非奇异的线性变换后，系统的特征值和系统的不变量均不改变。\n\n求变换矩阵 $T$，$\\mathbf{x}=T\\mathbf{z}$，将系统矩阵 $A$ 变换为 Jordan 标准型 $J=T^{-1}AT$，得到变换后的状态空间表达式：\n$$\\begin{align}\n\\begin{cases}\nT\\mathbf{\\dot{z}} = AT\\mathbf{z}+B\\mathbf{u} \\\\\n\\;\\;\\mathbf{y}=CT\\mathbf{z} +D \\mathbf{u}\n\\end{cases}\\quad \\Rightarrow\\quad \\begin{cases}\n\\dot{\\mathbf{z}}=T^{-1}AT\\mathbf{z}+T^{-1}B\\mathbf{u} \\\\\n\\mathbf{y}=CT\\mathbf{z}+D\\mathbf{u}\n\\end{cases}\n\\end{align}$$\n\n$$\\dot{\\mathbf{z}}=T^{-1}AT\\mathbf{z}+T^{-1}B\\mathbf{u} =\\begin{cases} \n\\mathbf{\\dot{z}}=\\Lambda \\mathbf{z}+T^{-1}B\\mathbf{u} \\quad \\text{特征值无重根，化为对角阵}\\\\ \\\\\n\\mathbf{\\dot{z}}=J \\mathbf{z} +T^{-1}B\\mathbf{u} \\quad \\text{特征值有重根，化为约旦标准型}\n\\end{cases}$$\n\n### 一、系统矩阵为任意矩阵（通用形式）\n计算系统矩阵的特征值和特征向量\\进行矩阵对角化\\\n\n#### 1. 特征值无重根\n由 $n$ 个互异特征值求得的 $n$ 个特征向量构成变换矩阵：\n$\\left\\lvert {\\color{red}\\lambda I-A} \\right\\rvert=0$ 计算出特征值，$(\\lambda_{i}I-A)P_{i}=0$ 计算第 $i$ 个特征值对应的特征向量 $P_{i}$\n$$\\begin{align}\n{\\color{red}(\\lambda_{i}I-A)}P_{i}=0 \\quad \\Rightarrow \\quad T=\\begin{pmatrix}\n{\\mathbf{P}}_{1} , {\\mathbf{P}}_{2} , \\cdots , {\\mathbf{P}}_{n}\n\\end{pmatrix}\n\\end{align}$$\n$$\\begin{align}\n\\Lambda=T^{-1}AT= \\begin{pmatrix}\n\\lambda_{1} & \\\\\n & \\lambda_{2} & \\\\\n & & \\ddots \\\\\n & & & \\lambda_{n}\n\\end{pmatrix}\n\\end{align}$$\n#### 2. 特征值有重根\n假设有 $q$ 个 $\\lambda_{1}$ 的重根，其余 $(n-q)$ 个互异的根\n$\\mathbf{P}_{1}$ 为特征值 $\\lambda_{1}$ 对应的 特征向量，$\\mathbf{P}_{2},\\cdots,\\mathbf{P}_{q}$ 为广义特征向量\n$$\\begin{align}\nT=({\\mathbf{P}}_{1} , {\\mathbf{P}}_{2} , \\cdots , \\mathbf{P}_{q},\\mathbf{P}_{q+1},\\cdots,{\\mathbf{P}}_{n})\n\\end{align}$$\n$$\\begin{cases}\n\\lambda_{1}\\mathbf{P}_{1}-A\\mathbf{P}_{1}=0 \\\\\n\\lambda_{1}\\mathbf{P}_{2}-A\\mathbf{P}_{2}=-\\mathbf{P}_{1} \\\\\n\\quad \\vdots \\\\\n\\lambda_{1}\\mathbf{P}_{q}-A\\mathbf{P}_{q}=-\\mathbf{P}_{q-1}\n\\end{cases}\\quad \\quad \n\\begin{cases} \n{\\color{red}(\\lambda_{1}I-A)}\\mathbf{P}_{1}=0 \\\\\n{\\color{red}(\\lambda_{1}I-A)}\\mathbf{P}_{2}={\\color{red}-}\\mathbf{P}_{1} \\\\\n {\\color{red}(\\lambda_{1}I-A)}\\mathbf{P}_{3}={\\color{red}-}\\mathbf{P}_{2} \\\\\n\\quad \\vdots \\\\\n{\\color{red}(\\lambda_{"
    },
    "状态空间": {
      "id": "状态空间",
      "title": "状态空间",
      "category": "2. 现代控制理论",
      "subcategory": "2. 现代控制理论",
      "tags": [
        "State",
        "Control",
        "System",
        "Linear",
        "Nonlinear"
      ],
      "aliases": [
        "状态",
        "状态空间方程",
        "状态空间表达式"
      ],
      "terminology": "State Space",
      "summary": "State Space \n系统的内部描述方法",
      "headings": [
        "一、基本概念",
        "二、状态空间表达式",
        "1.连续形式",
        "2.离散形式",
        "状态空间表达式的矩阵维度关系"
      ],
      "pinned": false,
      "level": 1,
      "created": "2024-09-04T12:29:34.090+08:00",
      "updated": "2025-07-10T00:17:12.000+08:00",
      "permalink": "/A2- 控制理论/2. 现代控制理论/状态空间/",
      "dg_path": "A2- 控制理论/2. 现代控制理论/状态空间.md",
      "source_path": "src/site/notes/状态空间.md",
      "viewer_markdown_path": "../source-notes/状态空间.md",
      "internal_links": [
        "状态空间表达式的建立"
      ],
      "inbound_links": [
        "传递函数矩阵",
        "卡尔曼滤波",
        "李雅普诺夫第二法",
        "状态向量的线性变换",
        "状态空间表达式的建立",
        "现代控制理论",
        "系统",
        "线性反馈系统的基本结构",
        "线性系统的结构分解"
      ],
      "out_of_scope_links": [
        "向量"
      ],
      "missing_links": [],
      "content_excerpt": "State Space \n系统的内部描述方法\n\n### 一、基本概念\n状态：是描述系统在某一时刻所具有的特定属性(运动信息)和行为的集合。\n提供了一种理解和描述系统的基本框架，无论是自然界的物理系统，还是人造的计算机系统，或是社会经济系统，状态都是不可或缺的。\n\n状态变量: 确定系统状态，完全描述系统的一组独立的、数目最小的变量。\n对于确定系统的状态是充分必要的，n 阶系统使用 n 个状态变量描述，它包含了系统的所有相关信息, 可以用来预测系统在未来的行为。\n$$x(t), \\dot{x}(t),\\cdots,x^{(n-1)}(t)$$\n（状态变量的个数等于微分方程的阶数，也即独立的储能元件的个数）\n\n状态向量：将描述系统状态的 $n$ 个状态变量看作向量\\的分量\n$$\\begin{align}\n\\mathbf{x}(t)=\\begin{bmatrix}\nx(t), \\dot{x}(t),\\cdots,x^{(n-1)}(t)\n\\end{bmatrix}^{T}\n\\end{align}$$\n状态空间：以 $n$ 个状态变量为基底所组成的 $n$ 维空间\n\n### 二、状态空间表达式\n状态空间表达式通常由两个方程表示，构成对一个系统的完整描述：\n状态方程 一阶向量微分方程/差分方程的形式：表征输入变量和内部变量的因果关系。\n输出方程 向量代数方程的形式：表征系统内部变量、输入变量、输出变量之间的转换关系。\n\n得到具体的状态空间表达式见状态空间表达式的建立\\\n\n#### 1.连续形式\n$$\\begin{align}\n\\dot{\\mathbf{x}}(t)&=\\mathbf{A}(t) \\mathbf{x}(t)+ \\mathbf{B}(t) \\mathbf{u}(t) \\\\\n\\mathbf{y}(t)&=\\mathbf{C}(t)\\mathbf{x}(t)+\\mathbf{D}(t) \\mathbf{u}(t)\n\\end{align}$$\n#### 2.离散形式\n$$\\begin{gathered}\n \\mathbf{x}(k+1) =\\mathbf{G}(k)\\mathbf{x}(k)+\\mathbf{H}(k)\\mathbf{u}(k) \\\\\n \\mathbf{y}(k) =\\mathbf{C}(k)\\mathbf{x}(k)+\\mathbf{D}(k)\\mathbf{u}(k)\n\\end{gathered}$$\n\n#### 状态空间表达式的矩阵维度关系"
    },
    "状态空间表达式的建立": {
      "id": "状态空间表达式的建立",
      "title": "状态空间表达式的建立",
      "category": "2. 现代控制理论",
      "subcategory": "2. 现代控制理论",
      "tags": [],
      "aliases": [],
      "terminology": "State Space Representation",
      "summary": "State Space Representation\n得到状态空间表达式\n[!important] Description \n前置知识： 系统\\ 状态空间\\ 传递函数\\\n本节从系统的两个层次来建立状态空间表达式",
      "headings": [
        "一、从内部结构机理建立",
        "1.1 系统模拟结构图建立",
        "1.2 系统机理建立",
        "二、从外部描述建立",
        "2.1 传递函数无零点",
        "2.2 传递函数有零点"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-09-17T18:44:42.000+08:00",
      "updated": "2026-01-21T10:27:49.735+08:00",
      "permalink": "/A2- 控制理论/2. 现代控制理论/状态空间表达式的建立/",
      "dg_path": "A2- 控制理论/2. 现代控制理论/状态空间表达式的建立.md",
      "source_path": "src/site/notes/状态空间表达式的建立.md",
      "viewer_markdown_path": "../source-notes/状态空间表达式的建立.md",
      "internal_links": [
        "传递函数",
        "状态空间",
        "状态空间表达式的能控标准型和能观标准型",
        "系统",
        "系统结构框图"
      ],
      "inbound_links": [
        "状态空间",
        "状态空间表达式的能控标准型和能观标准型",
        "现代控制理论"
      ],
      "out_of_scope_links": [
        "友矩阵"
      ],
      "missing_links": [],
      "content_excerpt": "State Space Representation\n得到状态空间表达式\n[!important] Description \n前置知识： 系统\\ 状态空间\\ 传递函数\\\n本节从系统的两个层次来建立状态空间表达式\n\n$$\\begin{align}\n\\begin{cases}\n\\dot{\\mathbf{x}} ={\\color{red}{A} } \\mathbf{x}+{\\color{blue}{B} }\\mathbf{u} \\\\\\\\\n\\mathbf{y}={\\color{green}{C} }\\mathbf{x}+D\\mathbf{u}\n\\end{cases}\n\\end{align}$$\n### 一、从内部结构机理建立\n#### 1.1 系统模拟结构图建立\n和经典控制理论的系统结构框图\\一致，使用框图表示信号传递关系。\n积分器的个数和状态变量数一致，积分器的输出就为状态变量。输入 $\\dot{x}$, 输出 $x$\n\n#### 1.2 系统机理建立\n$$\\begin{align}\nC \\dfrac{\\mathrm{d} u_{C}}{\\mathrm{d} t}=i\\quad L\\dfrac{\\mathrm{d} i}{\\mathrm{d} t} =u_{L} \n\\end{align}$$\n\n### 二、从外部描述建立\n实现问题：由描述系统输入-输出动态关系的微分方程/差分方程或传递函数建立系统的状态空间表达式。（保持了原有的输入-输出关系，又将系统的内部关系揭示出来；注意系统的实现是不唯一的）\n#### 2.1 传递函数无零点\n高阶微分方程：\n$$\\begin{align}\ny^{(n)}+a_{n-1}y^{(n-1)}+\\cdots + a_{1}y' +a_{0}y=b_{0} u(t)\n\\end{align}$$\n\n对应传递函数：\n$$\\begin{align}\nW(s)= \\dfrac{b_{0}}{s^{n}+a_{n-1}s^{n-1}+\\cdots + a_{1}s+a_{0}}\n\\end{align}$$\n取系统状态空间表达式为：\n$$\\begin{align}\n\\begin{cases}\n\\dot{x}_{1}=x_{2} \\\\\n\\dot{x}_{2}=x_{3} \\\\\n\\quad \\;\\vdots \\\\\n\\dot{x}_{n-1}=x_{n} \\\\\n\\dot{x}_{n}=-a_{0}x_{1}-a_{1}x_{2}-\\cdots-a_{n-1}x_{n}+u\n\\end{cases}\\quad y=b_{0}x_{1}\n\\end{align}$$\n\n对应状态空间表达式：\n$$\\begin{align}\nA= \\begin{pmatrix}\n0 & 1 & 0 & \\cdots & 0 \\\\\n0 & 0 & 1 & \\cdots & 0 \\\\\n\\vdots & \\vdots & \\vdots & \\ddots & \\vdots \\\\\n0 & 0 & 0 & \\cdots & 1 \\\\\n-a_0 & -a_1 & -a_2 & \\cdots & -a_{n-1}\n\\end{pmatrix}\\quad B= \\begin{pmatrix}\n0 \\\\ 0 \\\\ \\vdots \\\\ 0 \\\\ 1\n\\end{pmatrix}\\quad C= \\begin{pmatrix}\nb_{0}\\quad 0\\quad \\cdots\\quad 0\n\\end{pmatrix}\n\\end{align}$$\n系统矩阵为特征多项式对应的友矩阵\\！\n\n#### 2.2 传递函数有零点\n高阶微分方程：\n$$\\begin{align}\ny^{(n)}+a_{n-1}y^{(n-1)}+\\cdots + a_{1}y' +a_{0}y=b_{m} u^{(m)}+ b_{m-1} u^{(m-1)}+\\cdots + b_{1}u'+b_{0}u\n\\end{align}$$\n\n对应传递函数：\n$$\\begin{align}\nW(s)= \\dfrac{b_{m}s^{m}+ b_{m-1} s^{m-1}+\\cdots + b_{1}s+b_{0}}{s^{n}+a_{n-1}s^{n-1}+\\cdots + a_{1}s+a_{0}}\\quad m\\leq n\n\\end{align}$$\n\n对应状态空间表达式：(以下是当 $m=n$ 时情况，如果 $m<n$，注意 $b_{m+1},\\cdots, b_{n}=0$ 即可)\n\n形式一：\n$$\\begin{gathered}\nA= \\begin{pmatrix}\n0 & 1 & 0 & \\cdots & 0 \\\\\n0 & 0 & 1 & \\cdots & 0 \\\\\n\\vdots & \\vdots & \\vdots & \\ddots & \\vdots \\\\\n0 & 0 & 0 & \\cdots & 1 \\\\\n-a_0 & -a_1 & -a_2 & \\cdots & -a_{n-1}\n\\end{pmatrix}\\quad B= \\begin{pmatrix}\n0 \\\\ 0 \\\\ \\vdots \\\\ 0 \\\\ 1\n\\end{pmatrix}\\quad \\\\\n \\\\\n C= \\begin{pmatrix}\nb_{0}-a_{0}b_{n} \\quad b_{1}-a_{1}b_{n}\\quad \\cdots\\quad b_{n-1}-a_{n-1}b_{n}\n\\end{pmatrix}\\quad D=b_{n}\n\\end{gathered}$$\n（实际上为状态空间表达式的能控标准型和能观标准型#1.1 能控标准 I 型\\）\n\n~~形式二：~~\n$$\\begin{gathered}\nA= \\"
    },
    "状态空间表达式的能控标准型和能观标准型": {
      "id": "状态空间表达式的能控标准型和能观标准型",
      "title": "状态空间表达式的能控标准型和能观标准型",
      "category": "2. 现代控制理论",
      "subcategory": "2. 现代控制理论",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "寻找线性变换，得到单输入单输出系统的能控能控标准型。\n[!important] Description \n判断能控能观性：线性定常系统的能控性\\ 线性定常系统的能观性\\\n化为标准型：状态向量的线性变换\\\n写为传递函数：状态空间表达式的建立#二、从外部描述建立\\",
      "headings": [
        "能控性与能观性的对偶关系",
        "定常系统",
        "时变系统",
        "一、能控标准型",
        "1.1 能控标准 I 型",
        "1.2 能控标准 II 型",
        "二、 能观标准型",
        "2.2 能观标准 I 型",
        "2.2 能观标准 II 型",
        "三、实际例题",
        "能控标准型",
        "能控标准 I 型",
        "能控标准 II 型",
        "能观标准型",
        "能观标准 I 型",
        "能观标准 II 型"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-10-17T01:26:56.000+08:00",
      "updated": "2025-08-28T21:53:14.000+08:00",
      "permalink": "/A2- 控制理论/2. 现代控制理论/状态空间表达式的能控标准型和能观标准型/",
      "dg_path": "A2- 控制理论/2. 现代控制理论/状态空间表达式的能控标准型和能观标准型.md",
      "source_path": "src/site/notes/状态空间表达式的能控标准型和能观标准型.md",
      "viewer_markdown_path": "../source-notes/状态空间表达式的能控标准型和能观标准型.md",
      "internal_links": [
        "传递函数矩阵",
        "状态向量的线性变换",
        "状态空间表达式的建立",
        "线性定常系统的能控性",
        "线性定常系统的能观性"
      ],
      "inbound_links": [
        "传递函数阵的实现问题",
        "极点配置与系统镇定",
        "状态空间表达式的建立",
        "现代控制理论"
      ],
      "out_of_scope_links": [
        "友矩阵"
      ],
      "missing_links": [],
      "content_excerpt": "寻找线性变换，得到单输入单输出系统的能控能控标准型。\n[!important] Description \n判断能控能观性：线性定常系统的能控性\\ 线性定常系统的能观性\\\n化为标准型：状态向量的线性变换\\\n写为传递函数：状态空间表达式的建立#二、从外部描述建立\\\n\n$$\\begin{gathered}\n\\dot{\\mathbf{z}}=T^{-1}AT\\mathbf{z}+T^{-1}B\\mathbf{u} \\\\\n\\mathbf{y}=CT\\mathbf{z}+D\\mathbf{u}\n\\end{gathered}$$\n\n### 能控性与能观性的对偶关系\n互为对偶系统的两个系统：系统能控性分析 $\\Leftrightarrow$ 能观性分析\n系统的能控性等价于对偶系统的能观测性\n对偶系统的传递函数矩阵\\相互转置\n对偶系统的特征方程相同。\n\n#### 1. 定常系统\n$$\\begin{align}\n\\Sigma_{1} (A,B,C)\\quad \\Sigma_{2}(A^{T},C^{T},B^{T})\n\\end{align}$$\n$$\\begin{align}\nSym 1=\\begin{cases}\n\\dot{x}=Ax+Bu \\\\\ny=Cx\n\\end{cases} \\quad \\Leftrightarrow \\quad Sym 2=\\begin{cases}\n\\dot{x}=A^{T}+C^{T}u \\\\\ny=B^{T}x\n\\end{cases}\n\\end{align}$$\n#### 2. 时变系统\n$$\\begin{align}\n\\Sigma_{1} (A,B,C)\\quad \\Sigma_{2}(-A^{T},C^{T},B^{T})\n\\end{align}$$\n$$\\begin{align}\nSym 1=\\begin{cases}\n\\dot{x}=A(t)x+B(t)u \\\\\ny=C(t)x\n\\end{cases} \\quad \\Leftrightarrow \\quad Sym 2=\\begin{cases}\n\\dot{x}=-A^{T}(t)+C^{T}(t)u \\\\\ny=B^{T}(t)x\n\\end{cases}\n\\end{align}$$\n\n### 一、能控标准型\n首先判断系统是否线性定常系统的能控性\\，构造能控性矩阵 $rank\\; M =rank \\; {\\color{red}\\begin{pmatrix} b & Ab & \\cdots & A^{n-1}b\\end{pmatrix}}=n$\n其次利用系统矩阵计算特征多项式：\n$$\\begin{align}\n\\left\\lvert \\lambda I-A \\right\\rvert=\\lambda^{n}+{\\color{#944075} a_{n-1}}\\lambda^{n-1}+\\cdots +{\\color{#944075} a_{1}}\\lambda_{1}+ {\\color{#944075}a_{0}}\n\\end{align}$$\n#### 1.1 能控标准 I 型\n找线性变换使得系统矩阵为友矩阵\\，可以直接写出对应的传递函数。\n\n$$\\begin{align}\nT_{c_{1}}={\\color{red}\\begin{pmatrix}\nA^{n-1}\\mathbf{b} & A^{n-2}\\mathbf{b} & \\cdots & A\\mathbf{b} & \\mathbf{b}\n\\end{pmatrix} }\\begin{pmatrix}\n1 \\\\\n \\color{#944075}a_{n-1} & 1 \\\\\n\\vdots & \\vdots & \\ddots \\\\\n\\color{#944075}a_{2} & \\color{#944075}a_{3} & \\cdots & 1 \\\\\n\\color{#944075}a_{1} & \\color{#944075}a_{2} & \\cdots & \\color{#944075}a_{n-1} & 1\n\\end{pmatrix}\n\\end{align}$$\n\n$$\\begin{align}\n\\bar{A} & =T_{c_{1}}^{-1}AT_{c_{1}}= \\begin{pmatrix}\n0 & 1 & 0 & \\cdots & 0 \\\\\n0 & 0 & 1 & \\cdots & 0 \\\\\n\\vdots & \\vdots & \\vdots & \\ddots & \\vdots \\\\\n0 & 0 & 0 & \\cdots & 1 \\\\\n-\\color{#944075}a_{0} & -\\color{#944075}a_{1} & -\\color{#944075}a_{2} & \\cdots & -\\color{#944075}a_{n-1}\n\\end{pmatrix} \\\\\n\\bar{\\mathbf{b}} & =T_{c_{1}}^{-1}\\mathbf{b}=\\begin{pmatrix}\n0 \\\\0 \\\\\\vdots \\\\ 1 \n\\end{pmatrix} \\quad {\\color{ #7496ff }\\bar{\\mathbf{c}} =\\mathbf{c} T_{c_{1}} =\\begin{pmatrix}\n\\beta_{0},\\beta_{1},\\cdots,\\beta_{n-1}\n\\end{pmatrix}}\n\\end{align}$$\n\n可以直接得到系统的传递函数：\n$$\\begin{align}\nW(s)=\\bar{\\mathbf{c}}(sI-\\bar{A}) ^{-1}\\bar{\\mathbf{b}} =\\dfrac{{\\beta}_{{n-1}}{s}^{n-1}+"
    },
    "状态观测器": {
      "id": "状态观测器",
      "title": "状态观测器",
      "category": "2. 现代控制理论",
      "subcategory": "2. 现代控制理论",
      "tags": [],
      "aliases": [],
      "terminology": "Observer",
      "summary": "Observer\n用可测的输入输出“估算”系统内部状态，实现无法直接测量的线性反馈系统的基本结构#1. 状态反馈\\。",
      "headings": [
        "一、全维观测器",
        "实际例题",
        "二、降维观测器",
        "三、状态观测器实现状态反馈的系统",
        "四、状态观测器的扩展"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-09-02T17:54:35.000+08:00",
      "updated": "2025-08-28T23:56:12.000+08:00",
      "permalink": "/A2- 控制理论/2. 现代控制理论/状态观测器/",
      "dg_path": "A2- 控制理论/2. 现代控制理论/状态观测器.md",
      "source_path": "src/site/notes/状态观测器.md",
      "viewer_markdown_path": "../source-notes/状态观测器.md",
      "internal_links": [
        "卡尔曼滤波",
        "极点配置与系统镇定",
        "线性反馈系统的基本结构"
      ],
      "inbound_links": [
        "卡尔曼滤波",
        "现代控制理论"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "Observer\n用可测的输入输出“估算”系统内部状态，实现无法直接测量的线性反馈系统的基本结构#1. 状态反馈\\。\n\n### 一、全维观测器\n对线性定常系统 $\\Sigma_{0}=(A,B,C)$，状态观测器存在的充要条件是 $\\Sigma_{0}$ 的不能观子系统为渐近稳定或完全能观。\n如果线性定常系统 $\\Sigma_{0}=(A,B,C)$ 完全能观，则其状态矢量 $\\mathbf{x}$ 可以由输出 $\\mathbf{y}$ 和输入 $\\mathbf{u}$ 进行重构。\n\n状态观测器方程为:\n$$\\begin{align}\n\\mathbf{\\dot{\\hat{x}}}=({\\color{red}A-GC})\\hat{\\mathbf{x}}+G\\mathbf{y}+B\\mathbf{u}\n\\end{align}$$\n\n重点设计误差反馈矩阵 $G$ （实际上和极点配置与系统镇定#2. 采用从输出到状态变量导数的反馈\\类似）\n\n首先要进行能观性判别\n\n原系统：\n$$\\begin{align}\n\\det \\left[ \\lambda I-A\\right] =f(\\lambda)= \\prod\\limits_{i=1}^{n}(\\lambda-\\lambda_{i})=\\lambda^{n}+a_{n-1}\\lambda^{n-1}+\\cdots +a_{1}\\lambda+a_{0}\n\\end{align}$$\n期望极点系统：\n$$\\begin{align}\n\\det \\left[ \\lambda I-({\\color{red}A-GC})\\right] =f^{}(\\lambda)= \\prod\\limits_{i=1}^{n}(\\lambda-\\lambda_{i}^{})=\\lambda^{n}+a_{n-1}^{}\\lambda^{n-1}+\\cdots +a_{1}^{}\\lambda+a_{0}^{}\n\\end{align}$$\n\n#### 实际例题\n试采用状态观测器实现状态反馈控制，使闭环系统的极点配置在 $-50,-50$\n$$\\begin{align}\n\\dot{\\mathbf{x}}=\\begin{pmatrix}\n0 & 1 \\\\\n0 & -5\n\\end{pmatrix} \\mathbf{x}+\\begin{pmatrix}\n0 \\\\\n100\n\\end{pmatrix}\\mathbf{u}\\quad y=\\begin{pmatrix}\n1 & 0\n\\end{pmatrix}\\mathbf{x}\n\\end{align}$$\n\n$$\\begin{align}\nN=\\begin{pmatrix}\nC \\\\\nCA\n\\end{pmatrix}=\\begin{pmatrix}\n1 & 0 \\\\\n0 & 1\n\\end{pmatrix}\n\\end{align}$$\n$$\\begin{align}\nf^{}(\\lambda)=(\\lambda+50)^{2}=\\lambda^{2}+100\\lambda+2500\n\\end{align}$$\n\n设反馈增益矩阵 $G=\\begin{pmatrix} g_{1}\\\\ g_{2}\\end{pmatrix}$\n$$\\begin{align}\nf(\\lambda)=\\left\\lvert \\lambda I-(A-GC) \\right\\rvert=\\lambda^{2}+(g_{1}+5)\\lambda+5g_{1}+g_{2}\n\\end{align}$$\n\n对比系数得到：$g_{1}=95\\quad g_{2}=2025$，所以 $G=\\begin{pmatrix}95\\\\ 2025\\end{pmatrix}$\n状态观测器方程为：$\\mathbf{\\dot{\\hat{x}}}=({\\color{red}A-GC})\\hat{\\mathbf{x}}+G\\mathbf{y}+B\\mathbf{u}$\n[!important] 注意\n首先要判断系统的能观性\n求出反馈增益矩阵 $G$ 后，还要写出状态观测器的方程\n\n### 二、降维观测器\n如果系统能观，输出矩阵的秩为 $m$，则 $m$ 个状态分量可以直接由 $\\mathbf{y}$ 直接获得，则剩余 $n-m$ 个状态变量使用 $n-m$ 维的降维观测器进行重构。\n\n### 三、状态观测器实现状态反馈的系统\n状态反馈矩阵 $K$ 和观测器反馈矩阵 $G$ 可以分别进行设计。称为闭环极点设计的分离性\n观测器构成的状态反馈和状态直接反馈系统具有相同的传递函数矩阵。\n\n### 四、状态观测器的扩展\n卡尔曼滤波\\"
    },
    "现代控制理论": {
      "id": "现代控制理论",
      "title": "现代控制理论",
      "category": "2. 现代控制理论",
      "subcategory": "2. 现代控制理论",
      "tags": [
        "Subject",
        "Control"
      ],
      "aliases": [],
      "terminology": "Modern Control Theory",
      "summary": "Modern Control Theory\n以状态空间为基础，研究 MIMO 系统。以状态反馈和输出反馈为核心来分析和设计系统。\n主要是：线性系统的状态空间分析与综合",
      "headings": [
        "一、状态空间基础知识",
        "二、状态空间表达式的解",
        "三、可控性和可观测性",
        "四、稳定性分析",
        "五、线性系统综合"
      ],
      "pinned": true,
      "level": null,
      "created": "2024-12-03T17:16:58.000+08:00",
      "updated": "2025-08-29T10:00:36.000+08:00",
      "permalink": "/A2- 控制理论/2. 现代控制理论/现代控制理论/",
      "dg_path": "A2- 控制理论/2. 现代控制理论/现代控制理论.md",
      "source_path": "src/site/notes/现代控制理论.md",
      "viewer_markdown_path": "../source-notes/现代控制理论.md",
      "internal_links": [
        "传递函数矩阵",
        "传递函数阵的实现问题",
        "李雅普诺夫方法在线性系统中的应用",
        "李雅普诺夫方法在非线性系统中的应用",
        "李雅普诺夫稳定性理论",
        "李雅普诺夫第一法",
        "李雅普诺夫第二法",
        "极点配置与系统镇定",
        "状态向量的线性变换",
        "状态空间",
        "状态空间表达式的建立",
        "状态空间表达式的能控标准型和能观标准型",
        "状态观测器",
        "系统解耦",
        "线性反馈系统的基本结构",
        "线性定常状态方程的解",
        "线性定常系统的能控性",
        "线性定常系统的能观性",
        "线性时变状态方程的解",
        "线性时变系统的能控能观性",
        "线性系统的结构分解",
        "连续时间系统状态方程的离散化"
      ],
      "inbound_links": [
        "自动控制原理"
      ],
      "out_of_scope_links": [
        "矩阵指数函数"
      ],
      "missing_links": [
        "离散时间系统状态方程的解",
        "离散时间系统的能控性和能观性"
      ],
      "content_excerpt": "Modern Control Theory\n以状态空间为基础，研究 MIMO 系统。以状态反馈和输出反馈为核心来分析和设计系统。\n主要是：线性系统的状态空间分析与综合\n\n### 一、状态空间基础知识\n状态空间\\：核心基础\n状态空间表达式的建立\\：系统建模的核心\n状态向量的线性变换\\：将状态空间表达式变为标准型\n传递函数矩阵\\：传递函数的矩阵形式\n\n### 二、状态空间表达式的解\n矩阵指数函数\\：求解态空间表达式\n线性定常状态方程的解\\（主要讨论）\n线性时变状态方程的解\\\n离散时间系统状态方程的解\\\n连续时间系统状态方程的离散化\\\n\n### 三、可控性和可观测性\n线性定常系统的能控性\\\n线性定常系统的能观性\\\n线性时变系统的能控能观性\\\n离散时间系统的能控性和能观性\\\n\n状态空间表达式的能控标准型和能观标准型\\\n线性系统的结构分解\\\n传递函数阵的实现问题\\\n\n### 四、稳定性分析\n李雅普诺夫稳定性理论\\\n李雅普诺夫第一法\\\n李雅普诺夫第二法\\\n李雅普诺夫方法在线性系统中的应用\\\n李雅普诺夫方法在非线性系统中的应用\\\n\n### 五、线性系统综合\n线性反馈系统的基本结构\\\n极点配置与系统镇定\\\n系统解耦\\\n状态观测器\\"
    },
    "系统解耦": {
      "id": "系统解耦",
      "title": "系统解耦",
      "category": "2. 现代控制理论",
      "subcategory": "2. 现代控制理论",
      "tags": [],
      "aliases": [],
      "terminology": "System Decoupling",
      "summary": "System Decoupling",
      "headings": [
        "一、前馈补偿器解耦",
        "二、状态反馈解耦",
        "状态反馈的特征量",
        "能解耦性判据",
        "积分型解耦系统",
        "能解耦标准型"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-11-06T11:52:19.000+08:00",
      "updated": "2025-06-30T17:41:08.000+08:00",
      "permalink": "/A2- 控制理论/2. 现代控制理论/系统解耦/",
      "dg_path": "A2- 控制理论/2. 现代控制理论/系统解耦.md",
      "source_path": "src/site/notes/系统解耦.md",
      "viewer_markdown_path": "../source-notes/系统解耦.md",
      "internal_links": [],
      "inbound_links": [
        "现代控制理论"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "System Decoupling\n\n使输入输出相互关联的多变量系统实现：每一个输出仅受相应的一个输入所控制，每一个输入也仅能控制相应的一个输出。\n\n### 一、前馈补偿器解耦\n$$\\begin{align}\nW(s)=W_{0}(s)W_{d}(s)\n\\end{align}$$\n只要 $W_{0}^{-1}$ 存在，则串联补偿器传递函数矩阵为 $W_{d}(s)=W_{0}^{-1}(s)W(s)$\n\n### 二、状态反馈解耦\n检验系统是否满足解耦型判据\n计算状态反馈矩阵 $K$，和输入变换矩阵 $F$，将系统化为积分型解耦形式\n对各独立子系统采用附加状态反馈，将系统期望极点配置为期望值\n\n#### 状态反馈的特征量\n\n#### 能解耦性判据\n\n#### 积分型解耦系统\n\n#### 能解耦标准型"
    },
    "线性反馈系统的基本结构": {
      "id": "线性反馈系统的基本结构",
      "title": "线性反馈系统的基本结构",
      "category": "2. 现代控制理论",
      "subcategory": "2. 现代控制理论",
      "tags": [],
      "aliases": [
        "状态反馈"
      ],
      "terminology": "Basic Structure of Linear Feedback Systems",
      "summary": "Basic Structure of Linear Feedback Systems\n[!important] Description \n前置知识：反馈\\ 传递函数\\ 状态空间\\",
      "headings": [
        "一、反馈的基本结构",
        "状态反馈",
        "输出反馈",
        "从输出到状态矢量导数的反馈",
        "动态补偿器",
        "二、闭环系统的能控性和能观性"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-11-06T11:55:01.000+08:00",
      "updated": "2025-08-28T23:56:16.000+08:00",
      "permalink": "/A2- 控制理论/2. 现代控制理论/线性反馈系统的基本结构/",
      "dg_path": "A2- 控制理论/2. 现代控制理论/线性反馈系统的基本结构.md",
      "source_path": "src/site/notes/线性反馈系统的基本结构.md",
      "viewer_markdown_path": "../source-notes/线性反馈系统的基本结构.md",
      "internal_links": [
        "传递函数",
        "反馈",
        "状态空间"
      ],
      "inbound_links": [
        "极点配置与系统镇定",
        "状态观测器",
        "现代控制理论"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "Basic Structure of Linear Feedback Systems\n[!important] Description \n前置知识：反馈\\ 传递函数\\ 状态空间\\\n\n受控对象和反馈控制器两部分组成闭环系统，经典控制理论主要为输出反馈，现代控制理论为状态反馈。状态空间表达式：\n$$\\begin{align}\n\\dot{\\mathbf{x}} =A\\mathbf{x}+B\\mathbf{u} \\\\\n\\mathbf{y}=C\\mathbf{x}+D\\mathbf{u}\n\\end{align}$$\n\n为简单考虑，接下来的讨论将 $D=0$\n\n### 一、反馈的基本结构\n#### 1. 状态反馈\n将每一个状态变量乘以相应的反馈系数，反馈到输入端和参考输入相加形成控制律，作为受控系统的控制输入。（现代控制理论常使用）\n\n$$\\begin{align}\n\\mathbf{u}={\\color{red} K \\mathbf{x}} +\\mathbf{v} \\quad \\dot{\\mathbf{x}}=A\\mathbf{x}+ B(\\mathbf{v}+K\\mathbf{x})=(A+{\\color{red}BK})\\mathbf{x}+B\\mathbf{v} \n\\end{align}$$\n\n#### 2. 输出反馈\n采用输出矢量构成线性反馈律（经典控制理论常使用）\n$$\\begin{align}\n\\mathbf{u}= {\\color{red}H\\mathbf{y}}+\\mathbf{v}\\quad \\dot{\\mathbf{x}}=A\\mathbf{x}+B(\\mathbf{v}+H\\mathbf{y}) =(A+{\\color{red}BHC})\\mathbf{x}+B\\mathbf{v}\n\\end{align}$$\n\n#### 3. 从输出到状态矢量导数的反馈\n（状态观测器中常使用）\n$$\\begin{align}\n\\dot{\\mathbf{x}}=A\\mathbf{x}+B\\mathbf{u}+{\\color{red}G\\mathbf{y}}=A\\mathbf{x}+B\\mathbf{u}+GC\\mathbf{x}\\quad \\dot{\\mathbf{x}}=(A+{\\color{red}GC})\\mathbf{x}+B\\mathbf{u}\n\\end{align}$$\n\n#### 4. 动态补偿器\n引入动态子系统来改善系统性能。\n\n### 二、闭环系统的能控性和能观性\n状态反馈不改变受控系统的能控性，但是不保证是否影响能观性。\n从能控型矩阵来看：能控型矩阵的秩不会改变\n从引入状态反馈的传递函数来看，传递函数分子多项式不变，而分母多项式改变，可能发生零极点对消，破坏能观性。\n输出反馈不会改变受控系统的能控性和能观性"
    },
    "线性定常状态方程的解": {
      "id": "线性定常状态方程的解",
      "title": "线性定常状态方程的解",
      "category": "2. 现代控制理论",
      "subcategory": "2. 现代控制理论",
      "tags": [],
      "aliases": [],
      "terminology": "Solution of linear time-invariant state equations",
      "summary": "Solution of linear time-invariant state equations",
      "headings": [
        "一、线性定常齐次状态方程",
        "化为约旦标准型",
        "拉普拉斯变换",
        "凯莱哈密顿定理",
        "3.1 如果特征值均不相等",
        "3.2 如果特征值均相等",
        "二、线性定常非齐次状态方程的解"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-08-17T00:53:50.000+08:00",
      "updated": "2025-06-30T18:18:50.000+08:00",
      "permalink": "/A2- 控制理论/2. 现代控制理论/线性定常状态方程的解/",
      "dg_path": "A2- 控制理论/2. 现代控制理论/线性定常状态方程的解.md",
      "source_path": "src/site/notes/线性定常状态方程的解.md",
      "viewer_markdown_path": "../source-notes/线性定常状态方程的解.md",
      "internal_links": [
        "状态向量的线性变换",
        "经典输入信号"
      ],
      "inbound_links": [
        "现代控制理论"
      ],
      "out_of_scope_links": [
        "凯莱-哈密顿定理",
        "卷积",
        "拉普拉斯逆变换",
        "矩阵指数函数",
        "逆矩阵"
      ],
      "missing_links": [
        "范德蒙德矩阵"
      ],
      "content_excerpt": "Solution of linear time-invariant state equations\n\n矩阵指数函数\\\n\n### 一、线性定常齐次状态方程\n当初始时刻为 $t_{0}$，初始状态 $\\mathbf{x}(t_{0})$ 时，矩阵微分方程的解为：\n$$\\begin{align}\n\\dot{\\mathbf{x}}(t)=A\\mathbf{x}(t) \\quad \\Rightarrow\\quad \\mathbf{x}(t)=e^{ A(t-t_{0}) }\\mathbf{x}(t_{0}) =\\varPhi(t-t_{0})\\mathbf{x}(t_{0})\n\\end{align}$$\n\n#### 1. 化为约旦标准型\n求解核心：利用状态向量的线性变换\\将系统矩阵化为标准型，再结合矩阵指数函数#三、特殊矩阵的指数函数\\\n\n计算出特征值： $\\left\\lvert {\\color{red}\\lambda I-A} \\right\\rvert=0$ \n特征值无重根：$T^{-1}AT=\\Lambda \\quad A={\\color{red}T}\\Lambda {\\color{red}T^{-1}}\\quad e^{ At }=Te^{ \\Lambda t }T^{-1}$\n特征值有重根： $T^{-1}AT=J \\quad A=TJ T^{-1}\\quad e^{ At }=Te^{J t }T^{-1}$\n\n#### 2. 拉普拉斯变换\n求解的核心：计算逆矩阵\\，分解因式进行拉普拉斯逆变换\\，求得时间域上的解。\n\n由拉普拉斯变换得到：\n$$\\begin{gathered}\ns\\mathbf{X}(s)=A\\mathbf{X}(s)+\\mathbf{x}(0) \\\\ \\\\\n(sI-A)\\mathbf{X}(s)=\\mathbf{x}(0) \\\\\n\\mathbf{X}(s)=(sI-A)^{-1}\\mathbf{x}(0) \\\\\n\\mathbf{x}(t)=\\mathscr{L}^{-1}[(sI-A)^{-1}]\\mathbf{x}(0)\n\\end{gathered}$$\n\n对比矩阵指数得到：\n$$\\begin{align}\ne^{ At }=\\mathscr{L}^{-1}[{\\color{red}(sI-A)}^{-1}]\n\\end{align}$$\n\n#### 3. 凯莱哈密顿定理\n求解核心：将矩阵指数表达为 $n-1$ 及 $n-1$ 以下幂次的线性组合，记住系数的计算公式\n\n计算出特征值： $\\left\\lvert {\\color{red}\\lambda I-A} \\right\\rvert=0$ \n由凯莱-哈密顿定理\\得到：\n$$\\begin{align}\ne^{ \\mathbf{A}t } & =\\sum\\limits_{m=0}^{n-1} \\alpha_{m}(t)\\mathbf{A}^{m} =\\alpha_{n-1}\\mathbf{A}^{n-1}+\\alpha_{n-2}\\mathbf{A}^{n-2}+\\cdots+ \\alpha_{1}\\mathbf{A} +\\alpha_{0}\\mathbf{I}\n\\end{align}$$\n\n##### 3.1 如果特征值均不相等\n范德蒙德矩阵\\的转置的逆\n$$\\begin{align}\n\\begin{pmatrix}\n\\alpha_{0} \\\\\n\\alpha_{1} \\\\\n\\vdots \\\\\n\\alpha_{n-1}\n\\end{pmatrix}=\\begin{pmatrix}\n 1 & \\lambda_{1} & \\lambda_{1}^{2} & \\cdots & \\lambda_{1}^{n-1} \\\\\n1 & \\lambda_{2} & \\lambda_{2}^{2} & \\cdots & \\lambda_{2}^{n-1} \\\\ \n\\vdots & \\vdots & \\vdots & \\ddots & \\vdots & \\\\\n1 & \\lambda_{n} & \\lambda_{n}^{2} & \\cdots & \\lambda_{n}^{n-1} \\\\\n\\end{pmatrix}^{-1} \\begin{pmatrix}\ne^{ \\lambda 1 t} \\\\\ne^{ \\lambda_{2} t} \\\\\n\\vdots \\\\\ne^{ \\lambda_{n}t }\n\\end{pmatrix}\n\\end{align}$$\n\n$$\\begin{align}\n\\begin{pmatrix}\n\\alpha_{0} \\\\\n\\alpha_{1} \\\\\n\\alpha_{2}\n\\end{pmatrix}=\\begin{pmatrix}\n 1 & \\lambda_{1} & \\lambda_{1}^{2} \\\\\n1 & \\lambda_{2} & \\lambda_{2}^{2} \\\\ \n1 & \\lambda_{3} & \\lambda_{3}^{2} \\\\\n\\end{pmatrix}^{-1} \\begin{pmatrix}\ne^{ \\lambda 1 t} \\\\\ne^{ \\lambda_{2} t} \\\\\ne^{ \\lambda_{3}t }\n\\end{pmatrix}\n\\end{align}$$\n\n##### 3.2 如果特征值均相等\n$$\\begin{align}\n\\begin{pmatrix}\n\\alpha_{0} \\\\\n\\alpha_{1} \\\\\n\\vdots \\\\\n\\alpha_{n-2}\\\\\n\\alpha_{n-1} \n\\end{pmatrix}= \\begin{pmatrix}\n 0 & 0 & 0 & \\cdots & 0 & 1 \\\\"
    },
    "线性定常系统的能控性": {
      "id": "线性定常系统的能控性",
      "title": "线性定常系统的能控性",
      "category": "2. 现代控制理论",
      "subcategory": "2. 现代控制理论",
      "tags": [],
      "aliases": [
        "线性系统的可控性",
        "能控性"
      ],
      "terminology": "Controllability",
      "summary": "Controllability\n### 基本定义\n状态变量可以由输入来影响和控制，而由任意的初态达到原点。",
      "headings": [
        "基本定义",
        "一、线性定常系统的可控性判据",
        "对角线规范型判据",
        "构造能控性矩阵判断（秩判据）（主要使用）",
        "~~3. 传递函数判断能控性~~"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-10-09T11:28:58.000+08:00",
      "updated": "2025-09-18T23:39:48.000+08:00",
      "permalink": "/A2- 控制理论/2. 现代控制理论/线性定常系统的能控性/",
      "dg_path": "A2- 控制理论/2. 现代控制理论/线性定常系统的能控性.md",
      "source_path": "src/site/notes/线性定常系统的能控性.md",
      "viewer_markdown_path": "../source-notes/线性定常系统的能控性.md",
      "internal_links": [
        "传递函数矩阵",
        "状态向量的线性变换",
        "零极点"
      ],
      "inbound_links": [
        "状态空间表达式的能控标准型和能观标准型",
        "现代控制理论",
        "线性系统的结构分解"
      ],
      "out_of_scope_links": [
        "凯莱-哈密顿定理"
      ],
      "missing_links": [],
      "content_excerpt": "Controllability\n### 基本定义\n状态变量可以由输入来影响和控制，而由任意的初态达到原点。\n\n系统的可控性是从状态方程的角度看的，系统的可控建立在状态的可控。\n\nmermaid\ngraph LR \n输入 --> 状态可控 --> 系统可控 & 系统不完全可控\n\n状态可控：对于一个初始条件下的非零初始状态 $\\mathbf{x}(t_{0})=\\mathbf{x}_{0}$，存在一个无约束的容许控制，在有限时间内，使得状态由 $\\mathbf{x}(t_{0})=\\mathbf{x}_{0}$ 转移到 $\\mathbf{x}(t_{1})=\\mathbf{0}$\n系统可控：状态空间中的所有非零状态都是可控的\n系统不完全可控：存在一个或一些非零状态在时刻 $t_{0}$ 是不可控的\n\n### 一、线性定常系统的可控性判据\n考虑线性定常系统的状态方程\n$$\\begin{align}\n\\dot{\\mathbf{x}}(t)={\\color{red}{A} } \\mathbf{x}(t)+{\\color{#7496ff}B}\\mathbf{u}(t)\n\\end{align}$$\n\n系统的能控性取决于系统矩阵 $A$ 和控制矩阵 $B$。\n\n#### 1. 对角线规范型判据\n利用状态向量的线性变换\\将系统矩阵进行线性变换\n\n$$\\dot{\\mathbf{z}}=T^{-1}AT\\mathbf{z}+T^{-1}B\\mathbf{u} =\\begin{cases} \n\\mathbf{\\dot{z}}=\\Lambda \\mathbf{z}+T^{-1}B\\mathbf{u} \\quad \\text{特征值无重根，化为对角阵}\\\\ \\\\\n\\mathbf{\\dot{z}}=J \\mathbf{z} +T^{-1}B\\mathbf{u} \\quad \\text{特征值有重根，化为约旦标准型}\n\\end{cases}$$\n如果化为对角阵，只要控制矩阵元素全不为零，则系统能控。\n如果化为 Jordan 标准型\n 不同特征值对应的不同约旦块的最后一行元素不为零向量\n 相同特征值产生的约旦块的最后一行元素不仅不为零向量，且要满足线性独立的条件\n\n$$\\begin{align}\nA=\\begin{pmatrix}\n\\lambda_{1} & 1 & 0\\\\0 & \\lambda_{1} & 1\\\\ 0 & 0 & \\color{#00b7d3}{\\lambda_{1}} \\\\\n & & & \\lambda_{2} & 1 \\\\\n & & & & \\color{#11cabb}{\\lambda_{2}} \\\\\n & & & & & \\color{red}{\\lambda_{3} }\n\\end{pmatrix}\\quad B=\\begin{pmatrix}\n\\\\ \\\\ \\color{#00b7d3}{b_{1} } & \\color{#00b7d3}{b_{2}} \\\\\\ \\\\ \\color{#11cabb}{b_{3} } & \\color{#11cabb}{b_{4}} \\\\ \\color{red}{b_{5} } & \\color{red}{b_{6}}\n\\end{pmatrix}\n\\end{align}$$\n\n如果 $\\lambda_{1}\\neq\\lambda_{2} \\neq\\lambda_{3}$，只要 $(b_{1},b_{2}),(b_{3},b_{4}),(b_{5},b_{6})$ 不为零向量即可\n如果 $\\lambda_{1}=\\lambda_{2}\\neq\\lambda_{3}$ ，不仅要 $(b_{1},b_{2}),(b_{3},b_{4})$ 不为零向量，且要线性独立\n\n#### 2. 构造能控性矩阵判断（秩判据）（主要使用）\n由凯莱-哈密顿定理\\得到能控的充分必要条件：\n$$\\begin{align}\nrank\\; M =rank \\; \\begin{pmatrix}\nB & AB & \\cdots & A^{{\\color{red}{n-1} } }B\n\\end{pmatrix}=n\n\\end{align}$$\n\n \n#### ~~3. 传递函数判断能控性~~\n\n$$\\begin{align}\nW_{ux}(s)=(sI-A)^{-1}B\n\\end{align}$$\n\n计算传递函数矩阵\\，如果不存在零极点\\对消，则系统能控\n传递函数分子和分母约掉一个相同的公因子后，就相当于状态变量减少了一维，系统出现低维能控子空间和不能控子空间，则系统不能控。"
    },
    "线性定常系统的能观性": {
      "id": "线性定常系统的能观性",
      "title": "线性定常系统的能观性",
      "category": "2. 现代控制理论",
      "subcategory": "2. 现代控制理论",
      "tags": [],
      "aliases": [
        "线性系统的可观测性",
        "能观性"
      ],
      "terminology": "Observability",
      "summary": "Observability\n### 基本定义\n考察系统所有状态变量的任意形式的运动是否均可以由输出完全反映。只需要考虑状态变量的影响，无需考虑输入，所以只需要看状态空间方程的齐次部分和输出方程\n系统完全可观测：系统的输出能唯一确定状态向量的初值，则称系统是完全可观测的\n系统不可观测：系统的输出不能唯一确定所有状态向量的初值",
      "headings": [
        "基本定义",
        "一、线性定常系统的能观性",
        "对角线规范型判据",
        "构造能观判别矩阵（秩判据）"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-10-17T01:09:53.350+08:00",
      "updated": "2025-08-29T10:34:24.000+08:00",
      "permalink": "/A2- 控制理论/2. 现代控制理论/线性定常系统的能观性/",
      "dg_path": "A2- 控制理论/2. 现代控制理论/线性定常系统的能观性.md",
      "source_path": "src/site/notes/线性定常系统的能观性.md",
      "viewer_markdown_path": "../source-notes/线性定常系统的能观性.md",
      "internal_links": [
        "状态向量的线性变换"
      ],
      "inbound_links": [
        "状态空间表达式的能控标准型和能观标准型",
        "现代控制理论",
        "线性系统的结构分解"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "Observability\n### 基本定义\n考察系统所有状态变量的任意形式的运动是否均可以由输出完全反映。只需要考虑状态变量的影响，无需考虑输入，所以只需要看状态空间方程的齐次部分和输出方程\n系统完全可观测：系统的输出能唯一确定状态向量的初值，则称系统是完全可观测的\n系统不可观测：系统的输出不能唯一确定所有状态向量的初值\n\n### 一、线性定常系统的能观性\n$$\\begin{cases}\n\\mathbf{\\dot{x}}=A\\mathbf{x}\\quad \\mathbf{x}(t_{0})=\\mathbf{x}_{0} \\\\\n\\mathbf{y}=C\\mathbf{x}\n\\end{cases}$$\n#### 1. 对角线规范型判据\n利用状态向量的线性变换\\将系统矩阵进行线性变换\n$$\\begin{align}\n\\dot{\\mathbf{z}} & =T^{-1}AT\\mathbf{z} =\\begin{cases} \n\\mathbf{\\dot{z}}=\\Lambda \\mathbf{z}\\quad \\text{特征值无重根，化为对角阵}\\\\ \\\\\n\\mathbf{\\dot{z}}=J \\mathbf{z} \\quad \\text{特征值有重根，化为约旦标准型} \\\\\n\\end{cases} \\\\\ny&=CT\\mathbf{z}\n\\end{align}$$\n\n线性变换后，看输出矩阵 $CT$\n如果化为对角阵，只要输出矩阵元素全不为零\n如果化为 Jordan 标准型\n 不同特征值对应的不同约旦块的第一列元素不为零向量\n 相同特征值产生的约旦块的第一列元素不仅不为零向量，且要满足线性独立的条件\n\n$$\\begin{align}\nA=\\begin{pmatrix}\n\\color{#00b7d3}{\\lambda_{1}} & 1 & 0\\\\0 & \\lambda_{1} & 1\\\\ 0 & 0 & \\lambda_{1} \\\\\n & & & \\color{#11cabb}{\\lambda_{2}} & 1 \\\\\n & & & & \\lambda_{2} \\\\\n & & & & & \\color{red}{\\lambda_{3} }\n\\end{pmatrix}\\quad C=\\begin{pmatrix}\n\\color{#00b7d3}{c_{1} } & & & \\color{#11cabb}{c_{3} } & & \\color{red}{c_{5} }\\\\ \\color{#00b7d3}{c_{2}} & & & \\color{#11cabb}{c_{4}} & & \\color{red}{c_{6}}\n\\end{pmatrix}\n\\end{align}$$\n\n#### 2. 构造能观判别矩阵（秩判据）\n\n系统完全能观的充分必要条件：\n$$\\begin{align}\nrank \\;N=rank \\begin{pmatrix}\nC \\\\\nCA \\\\\n\\vdots \\\\\nCA^{n-1}\n\\end{pmatrix}=n\n\\end{align}$$"
    },
    "线性时变状态方程的解": {
      "id": "线性时变状态方程的解",
      "title": "线性时变状态方程的解",
      "category": "2. 现代控制理论",
      "subcategory": "2. 现代控制理论",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "只有当 $A_{(t)}$ 和 $\\int _{t_{0}}^{t} A(\\tau)\\, d\\tau$ 满足乘法可交换条件，时变系统的自由解才可以写为封闭的幂级数形式：\n$$\\begin{align}\n\\varPhi(t,t_{0})= \\exp \\left[\\int _{t_{0}}^{t} A(\\tau) \\mathrm{d}\\tau \\right] \\boldsymbol{x}_{(t_0)}\n\\end{align}$$",
      "headings": [
        "一、线性齐次时变状态方程的解",
        "时变状态转移矩阵的基本性质",
        "二、线性非齐次时变状态方程的解"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-10-14T10:05:47.000+08:00",
      "updated": "2025-06-29T19:00:30.000+08:00",
      "permalink": "/A2- 控制理论/2. 现代控制理论/线性时变状态方程的解/",
      "dg_path": "A2- 控制理论/2. 现代控制理论/线性时变状态方程的解.md",
      "source_path": "src/site/notes/线性时变状态方程的解.md",
      "viewer_markdown_path": "../source-notes/线性时变状态方程的解.md",
      "internal_links": [],
      "inbound_links": [
        "现代控制理论",
        "连续时间系统状态方程的离散化"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "### 一、线性齐次时变状态方程的解\n$$\\begin{align}\n\\boldsymbol{\\dot{x}}=A_{(t)}\\boldsymbol{x}_{(t)}\\quad \\Rightarrow\\quad \\boldsymbol{x}_{(t)}=\\varPhi_{(t,t_{0})}\\boldsymbol{x}_{_{(t_0)}}\n\\end{align}$$\n\n只有当 $A_{(t)}$ 和 $\\int _{t_{0}}^{t} A(\\tau)\\, d\\tau$ 满足乘法可交换条件，时变系统的自由解才可以写为封闭的幂级数形式：\n$$\\begin{align}\n\\varPhi(t,t_{0})= \\exp \\left[\\int _{t_{0}}^{t} A(\\tau) \\mathrm{d}\\tau \\right] \\boldsymbol{x}_{(t_0)}\n\\end{align}$$\n\n如果不满足乘法可交换条件，只能用级数近似：\n$$\\begin{align}\n\\varPhi(t,t_{0})=I+ \\int _{t_{0}}^{t}A(\\tau_{0}) \\, d\\tau_{0}+ \\int _{t_{0}}^{t} \\int _{t_{0}}^{\\tau_{0}} A(\\tau_{1}) \\, d\\tau_{1}d \\tau_{0}+ \\int _{t_{0}}^{t} \\int _{t_{0}}^{\\tau_{0}} \\int _{t_{0}}^{\\tau_{1}} A(\\tau_{2}) \\, d\\tau_{2}d \\tau_{1}d \\tau_{0}+\\cdots \n\\end{align}$$\n\n#### 时变状态转移矩阵的基本性质\n$$\\begin{gathered}\n\\varPhi(t,t)=I \\\\\n\\varPhi(t_{2},t_{1})\\varPhi(t_{1},t_{0})=\\varPhi (t_{2},t_{0}) \\\\\n\n\\varPhi(t,t_{0})=\\varPhi^{-1}(t_{0},t) \\\\ \n\\dot{\\varPhi}(t,t_{0})= A_{(t)}\\varPhi(t,t_{0})\n\\end{gathered}$$\n\n### 二、线性非齐次时变状态方程的解\n$$\\begin{align}\n\\boldsymbol{\\dot{x}}_{(t)}=A_{(t)}\\boldsymbol{x}_{(t)}+B_{(t)}\\boldsymbol{u}_{(t)}\\quad \\Rightarrow\\quad \n\\boldsymbol{x}_{(t)}=\\varPhi(t,t_{0})\\boldsymbol{x}_{(t_0)}+\\int _{t_{0}}^{t} \\varPhi(t,\\tau)B(\\tau)\\boldsymbol{u}(\\tau)\\, d\\tau\n\\end{align}$$\n\n$$\\begin{align}\n& \\boldsymbol{\\dot{x}}_{(t)} =A\\boldsymbol{x}_{(t)}+B\\boldsymbol{u}_{(t)} \\\\\n\\; {\\color{red}\\Rightarrow} \\; & e^{ -At } \\boldsymbol{\\dot{x}_{(t)}}= e^{ -At } A\\boldsymbol{x}_{(t)}+e^{ -At }B\\boldsymbol{u}_{(t)} \\\\\n\\; {\\color{red}\\Rightarrow} \\; & \\dfrac{\\mathrm{d} (\\; e^{ -At }\\boldsymbol{x}_{(t)} \\;)}{\\mathrm{d} t} =e^{ -At }B\\boldsymbol{u}_{(t)} \\\\\n\\end{align}$$\n\n两边积分得到：\n$$\\begin{align}\n & \\int _{t_{0}}^{t} \\dfrac{\\mathrm{d} (e^{ -A\\tau }\\boldsymbol{x}_{(\\tau)})}{\\mathrm{d} t}\\, d\\tau = \\int _{t_{0}}^{t} e^{ -A\\tau }B\\boldsymbol{u}_{(\\tau)} \\, d\\tau \\\\ \n \n\\; {\\color{red}\\Rightarrow} \\; & \\left. e^{ -A\\tau }\\boldsymbol{x}_{(\\tau)}\\right\\rvert ^{t}_{t_{0}} =\\int _{t_{0}}^{t} e^{ -A\\tau }B\\boldsymbol{u}_{(\\tau)} \\, d\\tau \n \\\\\n\n \\; {\\color{red}\\Rightarrow} \\; & e^{ -At }\\boldsymbol{x}_{(t)}=e^{ -At_{0} }\\boldsymbol{x}_{t_{0}}+\\int _{t_{0}}^{t} e^{ -At }B\\boldsymbol{u}_{(\\tau)} \\, d\\tau \\\\\n\n\\; {\\color{red}\\Rightarrow} \\; & \\boldsymbol{x}_{(t)}=e^{ A(t-t_{0}) }\\boldsymbol{x}_{(t_{0} )}+e^{ At } \\int _{t_{0}}^{t} e^{ -A\\tau }B\\boldsymbol{u}_{(t)} \\, d\\tau\n\\end{align}$$"
    },
    "线性时变系统的能控能观性": {
      "id": "线性时变系统的能控能观性",
      "title": "线性时变系统的能控能观性",
      "category": "2. 现代控制理论",
      "subcategory": "2. 现代控制理论",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "对于线性时变系统\n$$\\begin{align}\n\\dot{\\mathbf{x}}(t)&=\\mathbf{A}(t) \\mathbf{x}(t)+ \\mathbf{B}(t) \\mathbf{u}(t) \\\\\n\\mathbf{y}(t)&=\\mathbf{C}(t)\\mathbf{x}(t)+\\mathbf{D}(t) \\mathbf{u}(t)\n\\end{align}$$\n$$\\begin{gathered}\n\\mathbf{x}(t)=\\varPhi(t,t_{0})\\",
      "headings": [
        "一、线性时变系统的可控性判据",
        "充分必要条件",
        "充分条件",
        "二、线性时变系统的能观性",
        "充分必要条件",
        "充分条件"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-12-03T16:40:27.010+08:00",
      "updated": "2025-05-02T17:47:14.000+08:00",
      "permalink": "/A2- 控制理论/2. 现代控制理论/线性时变系统的能控能观性/",
      "dg_path": "A2- 控制理论/2. 现代控制理论/线性时变系统的能控能观性.md",
      "source_path": "src/site/notes/线性时变系统的能控能观性.md",
      "viewer_markdown_path": "../source-notes/线性时变系统的能控能观性.md",
      "internal_links": [],
      "inbound_links": [
        "现代控制理论"
      ],
      "out_of_scope_links": [],
      "missing_links": [
        "Gram矩阵"
      ],
      "content_excerpt": "对于线性时变系统\n$$\\begin{align}\n\\dot{\\mathbf{x}}(t)&=\\mathbf{A}(t) \\mathbf{x}(t)+ \\mathbf{B}(t) \\mathbf{u}(t) \\\\\n\\mathbf{y}(t)&=\\mathbf{C}(t)\\mathbf{x}(t)+\\mathbf{D}(t) \\mathbf{u}(t)\n\\end{align}$$\n$$\\begin{gathered}\n\\mathbf{x}(t)=\\varPhi(t,t_{0})\\mathbf{x}_{0}+\\int _{t_{0}}^{T} \\varPhi(t,\\tau)\\mathbf{B}(\\tau)\\mathbf{u}(\\tau) \\, d\\tau \\\\\n\\mathbf{y}(t)=\\mathbf{C}(t)\\varPhi(t,t_{0})\\mathbf{x}_{0}+\\mathbf{C}(t)\\int _{t_{0}}^{T} \\varPhi(t,\\tau)\\mathbf{B}(\\tau)\\mathbf{u}(\\tau) \\, d\\tau+\\mathbf{D}(t) \\mathbf{u}(t)\n\\end{gathered}$$\n### 一、线性时变系统的可控性判据\n#### 充分必要条件\nGram矩阵\\非奇异\n$$\\begin{align}\nW_{c}(t_{0},t_{f})=\\int _{t_{0}}^{t_{f}} \\varPhi(t_{0},t)B(t)B^{T}(t) \\varPhi^{T}(t_{0},t)\\, dt \n\\end{align}$$\n#### 充分条件\n$$\\begin{gathered}\nB_{1}(t)=B(t)\\quad B_{i}(t)=-A(t)B_{i-1}(t)+\\dot{B}_{i-1}(t) \\\\\nQ_{c}(t)=\\begin{pmatrix}\nB_{1}(t),B_{2}(t),\\cdots,B_{n}(t)\n\\end{pmatrix}\n\\end{gathered}$$\n\n在 $[0,t_{f}]$ 上状态完全能控：\n$$\\begin{align}\n rank\\;Q_{c}(t_{f})=n\n\\end{align}$$\n\n### 二、线性时变系统的能观性\n\n时变系统能观性：根据不能观测的定义，得到不能观测状态的数学表达式：\n$$\\begin{align}\nC(t)\\varPhi(t,t_{0})\\mathbf{x}(t_{0}) \\equiv 0,t\\in\\left[t_{0},t_{f}\\right]\n\\end{align}$$\n#### 充分必要条件\n$$\\begin{align}\nW_{0}(t_{0},t_{f})= \\int _{t_{0}}^{t_{f}} \\varPhi^{T}(t_{0},t)C^{T}(t) C(t) \\varPhi(t_{0},t)\\, dt\n\\end{align}$$\n\n#### 充分条件\n$C_{1}(t)=C(t),C_{i}(t)=C_{i-1}(t)A(t)+\\dot{C}_{i-1}(t)$\n\n$$\\begin{align}\nR(t)=\\begin{pmatrix}\\;\nC_{1}(t),C_{2}(t),\\cdots,C_{n}(t)\\;\n\\end{pmatrix}^{T}\n\\end{align}$$"
    },
    "线性系统的结构分解": {
      "id": "线性系统的结构分解",
      "title": "线性系统的结构分解",
      "category": "2. 现代控制理论",
      "subcategory": "2. 现代控制理论",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "将状态空间按照能控性和能观性进行结构分解，在理论上揭示了状态空间\\的本质特征，也为传递函数阵的实现问题\\提供了理论依据。",
      "headings": [
        "一、按能控性分解",
        "二、按能观性分解",
        "三、按能控能观性分解"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-10-07T09:34:36.490+08:00",
      "updated": "2025-05-02T17:47:14.000+08:00",
      "permalink": "/A2- 控制理论/2. 现代控制理论/线性系统的结构分解/",
      "dg_path": "A2- 控制理论/2. 现代控制理论/线性系统的结构分解.md",
      "source_path": "src/site/notes/线性系统的结构分解.md",
      "viewer_markdown_path": "../source-notes/线性系统的结构分解.md",
      "internal_links": [
        "传递函数阵的实现问题",
        "状态空间",
        "线性定常系统的能控性",
        "线性定常系统的能观性"
      ],
      "inbound_links": [
        "传递函数矩阵",
        "传递函数阵的实现问题",
        "现代控制理论"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "将状态空间按照能控性和能观性进行结构分解，在理论上揭示了状态空间\\的本质特征，也为传递函数阵的实现问题\\提供了理论依据。\n\n对于线性定常系统：\n$$\\begin{cases}\n\\dot{\\mathbf{x}}=A\\mathbf{x}+B\\mathbf{u} \\\\\n\\mathbf{y} =C\\mathbf{x}\n\\end{cases}$$\n\n### 一、按能控性分解\n线性定常系统的能控性\\判别矩阵：\n$$\\begin{align}\nrank\\; M =rank \\; \\begin{pmatrix}\nB & AB & \\cdots & A^{n-1}B\n\\end{pmatrix}= n_{1} [!important] 注意\n能观性分解时，首先得到的是非奇异变换的逆矩阵！而不是非奇异变换本身！！！\n\n得到变换后的状态空间表达式：\n$$\\mathbf{x}=R_{o}\\mathbf{\\tilde{x}} \\Rightarrow\\begin{cases}\n\\dot{\\tilde{\\mathbf{x}}}=\\tilde{A} \\tilde{\\mathbf{x}}+\\tilde{B}\\mathbf{u} \\\\\n\\mathbf{y}=\\tilde{C}\\mathbf{\\tilde{x}}\n\\end{cases}$$\n$$\\begin{align}\n\\tilde{A} & =R_{o}^{-1}AR_{o}=\\begin{pmatrix}\n\\color{red}{\\tilde{A}_{11}} & 0\\\\\n\\tilde{A}_{21} & \\tilde{A}_{22}\n\\end{pmatrix} \\\\\n\\tilde{B} & =R_{o}^{-1}B=\\begin{pmatrix}\n\\color{red}{\\tilde{B}_{1}}\\\\ \\tilde{B}_{2}\n\\end{pmatrix} \\\\\n\\tilde{C} & = CR_{o}=\\begin{pmatrix}\n\\color{red}{\\tilde{C}_{1}} & \\mathbf{0}\n\\end{pmatrix} \\\\\n\\tilde{\\mathbf{x}} & =\\begin{pmatrix}\n\\color{red}{\\tilde{\\mathbf{x}}_{1}} \\\\ -- \\\\\n\\tilde{\\mathbf{x}}_{2}\n\\end{pmatrix}\n\\end{align}$$\n\n能观子空间：\n$$\\begin{align}\n\\tilde{\\hat{\\mathbf{x}}}_{1} & =\\tilde{A}_{11}\\tilde{\\mathbf{x}}_{1}+\\tilde{B}_{1}\\mathbf{u}_{1} \\\\\n\\mathbf{y} & =\\tilde{C}_{1} \\tilde{\\mathbf{x}}_{1}\n\\end{align}$$\n\n### 三、按能控能观性分解\n如果系统不完全能观，不完全能控，则可以分解为四个子空间（实际上是先进行能控性分解，再进行能观性分解）\n$$\\begin{align}\n{A} & =R^{-1}AR=\\begin{pmatrix}\n\\color{#c44869}{{A}_{11}} & 0 & A_{13} & 0\\\\\n{A}_{21} & \\color{#e371aa}{{A}_{22}} & A_{23} & A_{24} \\\\\n0 & 0 & \\color{#00c9ab}{A_{33}} & 0 \\\\\n0 & 0 & A_{34} & \\color{#005b47}{A_{44}}\n\\end{pmatrix} \\\\\n{B} & =R^{-1}B=\\begin{pmatrix}\n{B}_{1}\\\\ {B}_{2} \\\\ 0 \\\\ 0\n\\end{pmatrix} \\\\\n{C} & = CR=\\begin{pmatrix}\n{C}_{1} & 0 & C_{3} & 0\n\\end{pmatrix} \\\\\n{\\mathbf{x}} & =\\begin{pmatrix}\n\\color{#c44869}{\\mathbf{x}_{co}} \\\\\n\\color{#e371aa}{\\mathbf{x}_{c \\bar{o}}} \\\\\n\\color{#00c9ab}{\\mathbf{x}_{\\bar{c}o}} \\\\\n\\color{#005b47}{\\mathbf{x}_{\\bar{c} \\bar{o}}}\n\\end{pmatrix}\n\\end{align}$$"
    },
    "连续时间系统状态方程的离散化": {
      "id": "连续时间系统状态方程的离散化",
      "title": "连续时间系统状态方程的离散化",
      "category": "2. 现代控制理论",
      "subcategory": "2. 现代控制理论",
      "tags": [
        "Continuous",
        "Discrete"
      ],
      "aliases": [],
      "terminology": "Discretization of continuous-time system state equations",
      "summary": "Discretization of continuous-time system state equations\n### 一、线性定常系统的离散化\n线性时变状态方程的解\\为：\n$$\\begin{align}\n \\boldsymbol{x}_{(t)}=e^{ A(t-t_{0}) }\\boldsymbol{x}_{(t_{0} )}+e^{ At } \\int _{t_{0}}^{t} e^{ -A\\tau }B\\boldsymbol{u}_{(t)} \\, d\\tau\n\\e",
      "headings": [
        "一、线性定常系统的离散化",
        "实际例子",
        "二、线性时变系统的离散化",
        "三个基本假设"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-10-01T13:31:52.000+08:00",
      "updated": "2025-06-29T19:08:38.000+08:00",
      "permalink": "/A2- 控制理论/2. 现代控制理论/连续时间系统状态方程的离散化/",
      "dg_path": "A2- 控制理论/2. 现代控制理论/连续时间系统状态方程的离散化.md",
      "source_path": "src/site/notes/连续时间系统状态方程的离散化.md",
      "viewer_markdown_path": "../source-notes/连续时间系统状态方程的离散化.md",
      "internal_links": [
        "模拟控制器离散化",
        "线性时变状态方程的解"
      ],
      "inbound_links": [
        "现代控制理论"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "Discretization of continuous-time system state equations\n### 一、线性定常系统的离散化\n线性时变状态方程的解\\为：\n$$\\begin{align}\n \\boldsymbol{x}_{(t)}=e^{ A(t-t_{0}) }\\boldsymbol{x}_{(t_{0} )}+e^{ At } \\int _{t_{0}}^{t} e^{ -A\\tau }B\\boldsymbol{u}_{(t)} \\, d\\tau\n\\end{align}$$\n考虑采样时间 $t_{k+1}-t_{k}=T$ 内：\n$$\\begin{align}\n\\boldsymbol{x}{[k+1]} & = {\\large e^{ A(t_{k+1}-t_{k}) }}\\boldsymbol{x}{[k] }+ \\int _{t_{k}}^{t_{k+1}} {\\large e^{ A(t_{k+1}-\\tau)} } B\\boldsymbol{u}_{[k]} \\, d\\tau \n\\end{align}$$\n系统的状态方程离散化后，系数改变：\n$$\\begin{align}\n\\dot{\\boldsymbol{x}}(t)&=\\boldsymbol{A} \\boldsymbol{x}(t)+ \\boldsymbol{B}\\boldsymbol{u}(t) \\quad {\\color{red}\\Rightarrow} \\quad \\boldsymbol{x}(k+1) =\\boldsymbol{G}(T)\\boldsymbol{x}(k)+\\boldsymbol{H}(T)\\boldsymbol{u}(k) \n\\end{align}$$\n\n$T$ 为采样周期，新的系数为：\n$$\\begin{align}\n \\boldsymbol{G}(T) & =e^{ \\boldsymbol{A}T } \\quad \\quad \\boldsymbol{H}(T)=\\int _{0}^{T} e^{ \\boldsymbol{A}t }\\, dt\\cdot \\boldsymbol{B} =-\\boldsymbol{A}^{-1} (e^{ 0 }-e^{ \\boldsymbol{A}T })\\boldsymbol{B}=A^{-1}(F-I)B\n\\end{align}$$\n系统的输出方程离散化后，系数不变：\n$$\\begin{align} \n \\boldsymbol{y}(k) & =\\boldsymbol{C}\\boldsymbol{x}(k)+\\boldsymbol{D}\\boldsymbol{u}(k) \\quad {\\color{red}\\Rightarrow} \\quad \n\\boldsymbol{y}(t)=\\boldsymbol{C}\\boldsymbol{x}(t)+\\boldsymbol{D} \\boldsymbol{u}(t)\n\\end{align}$$\n\n#### 实际例子\n\n### 二、线性时变系统的离散化\n$$\\begin{align}\n \\boldsymbol{G}(kT) & =\\varPhi[(k+1)T,kT] \\\\\n \\boldsymbol{H}(kT) & =\\int _{kT}^{(k+1)T} \\varPhi[(k+1)T,\\tau]\\quad \\boldsymbol{B}(\\tau)\\, d\\tau \\\\\nC(kT) & =C(t) |_{t=kT}\\\\\nD(kT) & =D(t) |_{t=kT} \n\\end{align}$$\n\n### 三个基本假设\n连续时间系统状态方程的离散化通常基于以下三个基本假设：\n模拟控制器离散化\\\n采样时刻输入输出相等：在采样时刻，连续信号的函数值与离散信号的函数值是相等的。这意味着在每个采样点，连续时间系统的输出值与离散时间系统的输出值相同。数学上可以表示为：\n $$\n e(t)|_{t=nT} = e(nT) = e^(nT)\n $$\n $$\n e(t)|_{t=(n+1)T} = e((n+1)T) = e^((n+1)T)\n $$\n 其中 $e(t)$ 为连续信号，$e^(t)$ 为采样信号。\n零阶保持（Zero-Order Hold, ZOH）：在两个采样点之间，输入信号被假设为恒定的，即输入信号在采样间隔内保持不变。这相当于使用零阶保持器，它将数字信号转换为连续信号，以解决各采样点之间的插值问题。零阶保持器的外推公式为：\n $$\n e(nT + \\Delta t) = a_0 + a_1 \\Delta t + a_2 (\\Delta t)^2 + \\ldots + a_m (\\Delta t)^m\n $$\n 其中，$\\Delta t$ 是以 $nT$ 时刻为原点的坐标，现在时刻的输出 $e(nT + \\Delta t)$ 值，取决于 $\\Delta t = 0, -T, -2T, \\ldots, -mT$ 各过去时刻的离散信号 $e^(nT), e^((n-1)T), \\ldots, e^((n-m)T)$ 的 $(m+1)$ 个值。\n线性系统假设：在离散化过程中，假设系统是线性的，这意味着系统的状态方程和输出方程可以表示为：\n $$\n \\dot{x}(t) = Ax(t) + Bu(t)\n $$\n $$\n y(t) = Cx(t) + Du(t)\n $$\n 其中，$x(t)$ 是状态向量，$u(t)$ 是输入向量，$y(t)$ 是输出向量，$A$，$B$，$C$，和 $D$ 是系统矩阵。在离散化过程中，这些矩阵保持不变，但它们的作用是在离散时间点上通过离散化方法来近似连续时间系统的行为。\n\n这些假设是连续时间系统状态"
    },
    "计算机控制系统概述": {
      "id": "计算机控制系统概述",
      "title": "计算机控制系统概述",
      "category": "3. 计算机控制系统",
      "subcategory": "3. 计算机控制系统",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "#### 计算机控制系统的特点\n易于控制算法设计与更新\n能实现集中监视和远程控制\n能实现最优控制\n高可靠性和可维护性",
      "headings": [
        "一、基础知识",
        "系统中的信号",
        "计算机控制系统的特点",
        "二、基本概念",
        "三、计算机控制系统的分类"
      ],
      "pinned": false,
      "level": null,
      "created": "2025-03-29T23:23:54.000+08:00",
      "updated": "2025-06-29T16:30:06.000+08:00",
      "permalink": "/A2- 控制理论/3/",
      "dg_path": "A2- 控制理论/3. 计算机控制系统/0",
      "source_path": "src/site/notes/计算机控制系统概述.md",
      "viewer_markdown_path": "../source-notes/计算机控制系统概述.md",
      "internal_links": [],
      "inbound_links": [
        "计算机控制系统"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "### 一、基础知识\n#### 系统中的信号\n模拟信号：时间上连续存在、幅值上连续变化\n数字信号：时间上离散、幅值上以二进制编码形式表示\n离散模拟信号/采样信号\n\n#### 计算机控制系统的特点\n易于控制算法设计与更新\n能实现集中监视和远程控制\n能实现最优控制\n高可靠性和可维护性\n\n### 二、基本概念\n计算机控制系统\n主要作用：实时数据处理；对生产过程实施实时控制；对生产过程进行监督和管理\n控制过程：实时数据采集、实时决策、实时控制\n\n计算机控制系统的工作方式： 在线、离线\n控制子程序：实现数据采集、控制算法、控制量的输出和存储\n模拟信号- 采样信号 - 量化信号（经过时间和幅值两方面的量化过程） - 数字信号\n\n实时性：信号的输入、计算、输出都要在采样间隔内完成。\n在线：计算机与被控对象相连，直接交换信息\n离线：计算机与被控对象不直接相连，记录信息完成相应的控制操作\n实时一定在线，离线一定不实时。\n\n### 三、计算机控制系统的分类\n操作指导控制系统 OGCS Operation Guide Control System：只承担数据的采集和处理，而不直接参与控制\n直接数字控制 DDC Direct Digital Control：参与闭环控制\n监督控制系统 SCC Supervisory Computer Control : 针对某目标函数设计数学模型\n集散控制系统 DCS Distributed Control System ：多台计算机连接多个设备的多个控制回路，分散控制、集中管理\n现场总线控制 FCS Fieldbus Control System：全分散、数字化、开放、互操作\n网络控制系统 NCS Network Control System： 分布式闭环反馈\n\n基于单片机、IPC、PLC、DCS、FCS\n\n主要优点\n复杂控制规律\n性价比高\n组成方式灵活\n更大的经济效益\n很强的可靠性、可维护性\n企业综合自动化打下良好基础"
    },
    "线性定常系统的差分方程求解": {
      "id": "线性定常系统的差分方程求解",
      "title": "线性定常系统的差分方程求解",
      "category": "3. 计算机控制系统",
      "subcategory": "3. 计算机控制系统",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "差分方程\\\n非齐次线性定常前向差分方程、非齐次线性定常后向差分方程",
      "headings": [
        "基本步骤",
        "实际例子"
      ],
      "pinned": false,
      "level": null,
      "created": "2025-03-31T21:54:02.150+08:00",
      "updated": "2025-05-02T17:47:14.000+08:00",
      "permalink": "/A2- 控制理论/3. 计算机控制系统/1.1 线性定常系统的差分方程求解/",
      "dg_path": "A2- 控制理论/3. 计算机控制系统/1.1 线性定常系统的差分方程求解.md",
      "source_path": "src/site/notes/线性定常系统的差分方程求解.md",
      "viewer_markdown_path": "../source-notes/线性定常系统的差分方程求解.md",
      "internal_links": [],
      "inbound_links": [
        "计算机控制系统"
      ],
      "out_of_scope_links": [
        "z 反变换",
        "z 变换",
        "差分方程"
      ],
      "missing_links": [],
      "content_excerpt": "差分方程\\\n非齐次线性定常前向差分方程、非齐次线性定常后向差分方程\n\n### 基本步骤\n设离散系统的输入为 $e(k)$，输出为 $u(k)$，（此时采样周期为 1 ，则 $t=kT \\Rightarrow k$）\n将差分方程进行 z 变换\\\n利用线性或时间平移等 z 变换的性质得到输出离散序列的 z 变换 $U(z)$\n对 $U(z)$ 进行 z 反变换\\，得到差分方程的解 $u(k)$\n$$\\begin{align}\n & \\sum\\limits_{j=0}^{n} a_{j}u(k-j) =\\sum\\limits_{i=0}^{m} b_{i} e(k-i)\n \\\\\n\\; {\\color{red}\\Rightarrow} \\; & \\sum\\limits_{j=0}^{n} a_{j}z^{-j}U(z)=\\sum\\limits_{i=0}^{m} b_{i}z^{-i} E(z) \\\\\n \\; {\\color{red}\\Rightarrow} \\; & U(z)= \\dfrac{\\sum\\limits_{i=0}^{m} b_{i}z^{-i} }{\\sum\\limits_{j=0}^{n} a_{j}z^{-j}}E(z) \\\\\n \\; {\\color{red}\\Rightarrow} \\; & u(k)=\\mathscr{Z}^{-1}[U(z)]\n\\end{align}$$\n\n### 实际例子\n$u(k)+au(k-1)=e(k),e(k)=1(k),u(k)=0(k\\leq-1)$, 求输出 $u(k)$\n\n$$\\begin{align}\n & U(z)+az^{-1}[U(z)+u(-1)]=E(z) \\\\\n \\quad \\Rightarrow \\quad & U(z)= \\dfrac{1}{1+az^{-1}} E(z)=\\dfrac{1}{1+az^{-1} } \\dfrac{1}{1-z^{-1}} \\\\\n \\quad \\Rightarrow \\quad & \\dfrac{U(z)}{z}= \\dfrac{z}{(z+a)(z-1)}= \\dfrac{a}{a+1} \\dfrac{1}{z+a}+ \\dfrac{1}{a+1} \\dfrac{1}{z-1}\\\\\n \\quad \\Rightarrow \\quad & u(k)=\\dfrac{a}{a+1} (-a)^{k}+ \\dfrac{1}{a+1}1(k)\n \\end{align}$$\n\n$$\\begin{align}\ny(k+2)-1.2(k+1)+0.32y(k)=1.2u(k+1)\\quad y(0)=1,y(1)=2.4 ,u(0)=1\n\\end{align}$$\n\n$$\\begin{align}\n & z^{2}\\left[Y(z)-y(0)-y(1)z^{-1}\\right]-1.2z\\left[Y(z)-y(0)\\right]+0.32Y(z)=1.2z\\left[U(z)-u(0)\\right] \\\\\n\\; {\\color{red}\\Rightarrow} \\; &(z^{2}-1.2z+0.32)Y(z)-z^{2}-2.4z+1.2z=1.2zU(z)-1.2z \\\\\n\\; {\\color{red}\\Rightarrow} \\; & Y(z)=\\dfrac{1.2zU(z)}{z^{2}-1.2z+0.32 } +\\dfrac{ z^{2}}{z^{2}-1.2z+0.32} \\\\\n\\; {\\color{red}\\Rightarrow} \\; & y(k)=\\mathscr{Z}^{-1} \\left[Y(z) \\right] \n\\end{align}$$\n\n$$\\begin{align}\ny(k)-5y(k-1)+6y(k-2)=u(k)\n\\end{align}$$\n\n$$\\begin{align}\n & Y(z)-5z^{-1}Y(z)+6z^{-2}Y(z)=U(z) \\\\\n\\; {\\color{red}\\Rightarrow} \\; & Y(z)=\\dfrac{z^{2}}{z^{2}-5z+6} \\times \\dfrac{z}{z-1}=\\dfrac{z^{3}}{(z-2)(z-3)(z-1)} \\\\\n\\; {\\color{red}\\Rightarrow} \\; & \\dfrac{Y(z)}{z}=\\dfrac{1}{2} \\dfrac{1}{z-1}-4 \\dfrac{1}{z-2}+\\dfrac{9}{2} \\dfrac{1}{z-3} \\\\\n\\; {\\color{red}\\Rightarrow} \\; & y(k)= \\dfrac{1}{2}-4\\cdot2^{k}+ \\dfrac{9}{2}\\cdot3^{k}\n\\end{align}$$"
    },
    "脉冲传递函数": {
      "id": "脉冲传递函数",
      "title": "脉冲传递函数",
      "category": "3. 计算机控制系统",
      "subcategory": "3. 计算机控制系统",
      "tags": [],
      "aliases": [
        "z 传递函数"
      ],
      "terminology": "Z-Transfer Function",
      "summary": "Z-Transfer Function z 传递函数\n线性定常离散系统的脉冲传递函数\\定义为：系统输出采样信号的 z 变换与输入采样信号的 z 变换\\ 之比。用于描述系统的差分方程\\：",
      "headings": [
        "一、开环控制",
        "串联环节",
        "并联环节",
        "二、闭环控制"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-07-11T17:46:53.000+08:00",
      "updated": "2025-09-26T12:09:22.000+08:00",
      "permalink": "/A2- 控制理论/3. 计算机控制系统/1.3 脉冲传递函数/",
      "dg_path": "A2- 控制理论/3. 计算机控制系统/1.3 脉冲传递函数.md",
      "source_path": "src/site/notes/脉冲传递函数.md",
      "viewer_markdown_path": "../source-notes/脉冲传递函数.md",
      "internal_links": [
        "传递函数",
        "信号保持"
      ],
      "inbound_links": [
        "模拟控制器离散化",
        "离散系统的稳定性分析",
        "计算机控制系统"
      ],
      "out_of_scope_links": [
        "z 变换",
        "差分方程"
      ],
      "missing_links": [],
      "content_excerpt": "Z-Transfer Function z 传递函数\n线性定常离散系统的脉冲传递函数\\定义为：系统输出采样信号的 z 变换与输入采样信号的 z 变换\\ 之比。用于描述系统的差分方程\\：\n\n$$\\begin{align}\nG(z)&=\\dfrac{Y(z)}{U(z)}= \\dfrac{\\mathscr{Z}[y(kT)]}{\\mathscr{Z}[u(kT)]} =\\dfrac{\\sum\\limits_{k=0}^{\\infty}y(nT)z^{-k}}{\\sum\\limits_{k=0}^{\\infty}u(nT)z^{-k}}\n\\end{align}$$\n\n### 一、开环控制\n\n#### 串联环节\n串联环节有采样开关：总的传递函数为每个环节传递函数之积\n$$\\begin{align}\nY(s)=G^{}_{1}(s)G^{}_{2}(s)U^{}(s)\\; {\\color{red}\\Rightarrow} \\; \\dfrac{Y(z)}{U(z)}=G_{1}(z)G_{2}(z)\n\\end{align}$$\n串联环节无采样开关：$G_{1}G_{2}(z)$ 表示先将传递函数相乘，再进行 $z$ 变换\n\n$$\\begin{align}\nY(s)=[G_{1}(s)G_{2}(s)]^{}U^{}(s)\\; {\\color{red}\\Rightarrow} \\; \\dfrac{Y(z)}{U(z)}=G_{1}G_{2}(z)\n\\end{align}$$\nZOH 串联的广义对象： 信号保持#二、零阶保持器 ZOH\\\n\n$$\\begin{align}\nG_{h}(s)=\\dfrac{1-e^{ -Ts }}{s}\\quad G(z)= \\dfrac{Y(z)}{U(z)}=\\mathscr{Z}\\left[(1-e^{ -Ts })\\cdot \\dfrac{G_{o}(s)}{s}\\right]=(1-z^{-1})\\mathscr{Z}[\\dfrac{G_{o}(s)}{s}]\n\\end{align}$$\n\n#### 并联环节\n\n### 二、闭环控制\n\n$$\\begin{align}\n & Y(s)=\\dfrac{G_{1}(s)G_{2}(s)}{1+G_{1}(s)G_{2}(s)F(s)}R(s) \\\\ \\\\\n\n\\; {\\color{red}\\Rightarrow} \\; & Y^{}(s)=\\dfrac{[G_{1}(s)G_{2}(s)]^{}}{1+[G_{1}(s)G_{2}(s)F(s)]^{}}R(s) \\\\ \\\\\n\n\\; {\\color{red}\\Rightarrow} \\; & \\dfrac{Y(z)}{R(z)}=\\dfrac{G_{1}G_{2}(z)}{1+G_{1}G_{2}F(z)}\n\\end{align}$$\n\n$$\\begin{align}\n & Y(s)= \\dfrac{G_{1}(s)G_{2}(s)G_{3}(s)}{1+G_{1}(s)G_{2}(s)G_{3}(s)H(s)} R(s) \\\\ \\\\\n\n\\; {\\color{red}\\Rightarrow} \\; & Y^{}(s)= \\dfrac{\\left[G_{1}(s)R(s)\\right]^{}\\; G_{2}^{}(s)\\; G_{3}^{}(s)}{1+G^{}_{2}(s)\\;[G_{1}(s)G_{3}(s)H(s)]^{}} \\\\ \\\\\n\n\\; {\\color{red}\\Rightarrow} \\; & \\dfrac{Y(z)}{R(z)}= \\dfrac{G_{2}(z)G_{3}(z) {\\color{red}G_{1}R(z)}}{1+G_{2}(z)G_{3}HG_{1}(z)} \\dfrac{1}{\\color{red}R(z)}\n\\end{align}$$\n[!important] \n一定要注意采样开关的位置！！！"
    },
    "离散系统的稳定性分析": {
      "id": "离散系统的稳定性分析",
      "title": "离散系统的稳定性分析",
      "category": "3. 计算机控制系统",
      "subcategory": "3. 计算机控制系统",
      "tags": [],
      "aliases": [],
      "terminology": "Stability Analysis of Discrete Systems",
      "summary": "Stability Analysis of Discrete Systems",
      "headings": [
        "一、离散系统稳定的充分必要条件",
        "二、稳定性判据",
        "2.1 修正的劳斯稳定性准则",
        "2.2 朱利判据"
      ],
      "pinned": false,
      "level": null,
      "created": "2025-03-18T10:25:33.000+08:00",
      "updated": "2025-09-11T19:21:16.000+08:00",
      "permalink": "/A2- 控制理论/3. 计算机控制系统/2.1 离散系统的稳定性分析/",
      "dg_path": "A2- 控制理论/3. 计算机控制系统/2.1 离散系统的稳定性分析.md",
      "source_path": "src/site/notes/离散系统的稳定性分析.md",
      "viewer_markdown_path": "../source-notes/离散系统的稳定性分析.md",
      "internal_links": [
        "线性系统稳定性分析",
        "脉冲传递函数"
      ],
      "inbound_links": [
        "计算机控制系统"
      ],
      "out_of_scope_links": [
        "z 变换"
      ],
      "missing_links": [],
      "content_excerpt": "Stability Analysis of Discrete Systems\n\n### 一、离散系统稳定的充分必要条件\n由线性系统稳定性分析\\知道：线性连续系统的闭环传递函数的极点都在 s 域的左半平面时，系统稳定。类似的，由映射关系可以得到，离散系统稳定的充分必要条件为：系统的闭环 脉冲传递函数\\ 的所有极点都在 z 平面的单位圆内部，$\\left\\lvert p_{i} \\right\\rvert | $\\cdots$ | $\\cdots$ | $\\cdots$ |\n\n$$\\begin{align}\nL_{31}=-\\frac{1}{\\color{red} a_{n-1}} \\begin{vmatrix}\na_{n} & a_{n-2} \\\\\na_{n-1} & a_{n-3} \\\\\n\\end{vmatrix} \\\\\nL_{32}=-\\frac{1}{a_{n-1}} \\begin{vmatrix}\na_{n} & a_{n-4} \\\\\na_{n-1} & a_{n-5} \\\\\n\\end{vmatrix} \\\\ \nL_{33}=-\\frac{1}{a_{n-1}} \\begin{vmatrix}\na_{n} & a_{n-6} \\\\\na_{n-1} & a_{n-7} \\\\\n\\end{vmatrix} \\\\ \\\\ \n\nL_{41}=-\\frac{1}{L_{31}} \\begin{vmatrix}\na_{n-1} & a_{n-3} \\\\\nL_{31} & L_{32} \\\\\n\\end{vmatrix} \\\\\nL_{42}=-\\frac{1}{L_{31}} \\begin{vmatrix}\na_{n-1} & a_{n-5} \\\\\nL_{31} & L_{33} \\\\\n\\end{vmatrix}\n\\end{align}$$\n\n#### 2.2 朱利判据\n直接在 z 域根据线性离散系统的闭环特征方程进行稳定性判别\n$$\\begin{align}\n\\alpha(z)={a}_{0}z^{n} + {a}_{1}z^{n-1} + \\cdots + {a}_{n}=0\n\\end{align}$$\n\n离散系统稳定的充分必要条件为：所有奇数行第一列元素均大于零（$a_{0},b_{0},\\cdots,m_{0}>0$），即特征方程的全部特征根均在单位圆内。\n如果有小于零的元素，则离散系统不稳定，且小于零的元素个数就是位于圆外的特征根的个数。\n\n$$\\begin{align}\nb_{0}=a_{0}- a_{n} \\dfrac{a_{n}}{a_{0}}\\quad b_{1}=a_{1}-a_{n-1} \\dfrac{a_{n}}{a_{0}}\\quad b_{2}=a_{2}-a_{n-2} \\dfrac{a_{n}}{a_{0}} \\quad \\cdots\\\\\nc_{0}=b_{0}- b_{n-1} \\dfrac{b_{n-1}}{b_{0}}\\quad c_{1}=b_{1}-b_{n-2} \\dfrac{b_{n-1}}{b_{0}}\\quad c_{2}=b_{2}-b_{n-3} \\dfrac{b_{n-1}}{b_{0}}\\quad \\cdots\n\\end{align}$$"
    },
    "离散系统稳态分析": {
      "id": "离散系统稳态分析",
      "title": "离散系统稳态分析",
      "category": "3. 计算机控制系统",
      "subcategory": "3. 计算机控制系统",
      "tags": [],
      "aliases": [],
      "terminology": "Steady-state Analysis of Discrete Systems",
      "summary": "Steady-state Analysis of Discrete Systems",
      "headings": [
        "一、稳态误差计算",
        "二、误差系数计算"
      ],
      "pinned": false,
      "level": null,
      "created": "2025-04-01T01:33:44.410+08:00",
      "updated": "2025-08-28T21:53:14.000+08:00",
      "permalink": "/A2- 控制理论/3. 计算机控制系统/2.2 离散系统稳态分析/",
      "dg_path": "A2- 控制理论/3. 计算机控制系统/2.2 离散系统稳态分析.md",
      "source_path": "src/site/notes/离散系统稳态分析.md",
      "viewer_markdown_path": "../source-notes/离散系统稳态分析.md",
      "internal_links": [
        "线性系统稳态误差计算"
      ],
      "inbound_links": [
        "计算机控制系统"
      ],
      "out_of_scope_links": [
        "z 变换"
      ],
      "missing_links": [],
      "content_excerpt": "Steady-state Analysis of Discrete Systems\n\n### 一、稳态误差计算\n线性系统稳态误差计算\\\n\n误差传递函数：误差信号与输入信号之比\n$\\varPhi_{k}(z)$ 为开环传递函数，$\\varPhi_{e}(z)$ 为误差传递函数：\n$$\\begin{align}\n\\varPhi_{k}(z)=D(z)G(z)\\quad \\varPhi_{e}(z)= \\dfrac{E(z)}{R(z)} = \\dfrac{1}{1+\\varPhi_{k}(z)}\\; {\\color{red}\\Rightarrow} \\; E(z)=\\varPhi_{e}(z)R(z)=\\dfrac{R(z)}{1+\\varPhi_{k}(z)}\n\\end{align}$$\n\n根据z 变换#4. 极限定理\\，稳态误差表示为：\n$$\\begin{align}\ne(\\infty)= \\lim\\limits_{ z \\to 1 } (z-1) R(z) \\varPhi_{e}(z)\n\\end{align}$$\n\n### 二、误差系数计算\n位置误差系数：\n$$\\begin{align}\ne(\\infty)= \\lim\\limits_{ z \\to 1 } (z-1) \\dfrac{1}{1+\\varPhi_{k}(z)} \\dfrac{1}{1-z^{-1}}= \\dfrac{1}{1+\\varPhi_{k}(z)} = \\dfrac{1}{1+K_{p}}\\; {\\color{red}\\Rightarrow} \\; K_{p}= \\varPhi_{k}(1)\n\\end{align}$$\n\n速度误差系数：\n$$\\begin{align}\ne(\\infty)= \\lim\\limits_{ z \\to 1 } (z-1) \\dfrac{1}{1+\\varPhi_{k}(z)} \\dfrac{Tz}{(z-1)^{2}}= \\dfrac{T}{\\varPhi_{k}(z)(z-1)} =\\dfrac{1}{K_{v}} \\; {\\color{red}\\Rightarrow} \\; K_{v}= \\dfrac{(z-1)\\varPhi_{k}(z)}{T}\n\\end{align}$$\n\n加速度误差系数：\n$$\\begin{align}\ne(\\infty)= \\lim\\limits_{ z \\to 1 } (z-1) \\dfrac{1}{1+\\varPhi_{k}(z)} \\dfrac{T^{2}z(z+1)}{2(z-1)^{3}}= \\dfrac{1}{K_{a}}\\; {\\color{red}\\Rightarrow} \\; K_{a}= \\dfrac{(z-1)^{2}\\varPhi_{k}(z)}{T^{2}}\n\\end{align}$$"
    },
    "模拟控制器离散化": {
      "id": "模拟控制器离散化",
      "title": "模拟控制器离散化",
      "category": "3. 计算机控制系统",
      "subcategory": "3. 计算机控制系统",
      "tags": [
        "Continuous",
        "#Discrete"
      ],
      "aliases": [],
      "terminology": "Discretization of Analog Controllers",
      "summary": "Discretization of Analog Controllers",
      "headings": [
        "一、响应不变法（z 变换法）",
        "1.1 脉冲响应不变法",
        "1.2 阶跃响应不变法",
        "二、差分变换法",
        "前向差分",
        "后向差分",
        "双线性差分 Tustin 变换法",
        "三、零极点匹配法",
        "例题 1",
        "例题 2"
      ],
      "pinned": false,
      "level": null,
      "created": "2025-03-20T12:44:59.000+08:00",
      "updated": "2025-09-12T16:33:48.000+08:00",
      "permalink": "/A2- 控制理论/3. 计算机控制系统/3.1 模拟控制器离散化/",
      "dg_path": "A2- 控制理论/3. 计算机控制系统/3.1 模拟控制器离散化.md",
      "source_path": "src/site/notes/模拟控制器离散化.md",
      "viewer_markdown_path": "../source-notes/模拟控制器离散化.md",
      "internal_links": [
        "脉冲传递函数"
      ],
      "inbound_links": [
        "史密斯预估补偿控制",
        "大林算法控制器",
        "数字 PID 控制器",
        "计算机控制系统",
        "连续时间系统状态方程的离散化"
      ],
      "out_of_scope_links": [
        "z 变换",
        "拉普拉斯变换",
        "欧拉法",
        "泰勒级数"
      ],
      "missing_links": [],
      "content_excerpt": "Discretization of Analog Controllers\n\n离散系统控制设计完后，都写上控制器算法\n\n$$\\begin{align}\n D(z)=\\dfrac{U(z)}{E(z)}\\quad \\quad u(k)=\\mathscr{Z}^{-1}[D(z)E(z)]\n\\end{align}$$\n\n### 一、响应不变法（z 变换法）\n\n#### 1.1 脉冲响应不变法\n\n基本思想：数字控制器 $D(z)$ 产生的脉冲响应序列与模拟控制器 $D(s)$ 产生的脉冲响应序列在采样瞬间相等。由于 $\\mathscr{L}[\\delta(t)]=1$，实际上就是对 $D(s)$ 取 z 变换\\：\n\n$$\\begin{align}\nU(s)=D(s)E(s)=D(s)\\quad D(z)=\\mathscr{Z}[D(s)]\n\\end{align}$$\n\n如果原控制器稳定，则离散化后也稳定，不具有串联性质\n\n#### 1.2 阶跃响应不变法\n\n基本思想：数字控制器 $D(z)$ 产生的单位阶跃响应与模拟控制器 $D(s)$ 产生的单位阶跃响应在采样瞬间相等。实际上就是 脉冲传递函数#开环控制\\ 的 z 变换：\n\n$$\\begin{align}\nD(z)=\\mathscr{Z}[\\dfrac{1-e^{ -Ts }}{s} D(s)]=(1-z^{-1}) \\mathscr{Z}[ \\dfrac{D(s)}{s}]\n\\end{align}$$\n\n如果原控制器稳定，则离散化后也稳定，不具有串联性质\n\n例子： $D(s)= \\dfrac{a}{s+a}$，求阶跃响应不变法对应的数字控制器，以及对应的差分方程\n\n$$\\begin{align}\n\\dfrac{U(z)}{E(z)} & =D(z)=(1-z^{-1})\\mathscr{Z}[\\dfrac{a}{(s+a)s}]=(1-z^{-1})\\mathscr{Z}[(\\dfrac{1}{s}- \\dfrac{1}{s+a})] \\\\\n & =(1-z^{-1}) (\\dfrac{1}{1-z^{-1}}- \\dfrac{1}{1-e^{ -aT }z^{-1}})=\\dfrac{z^{-1}(1-e^{ -aT })}{1-e^{ -aT }z^{-1}}\n\\end{align}$$\n\n进一步得到差分方程：\n$$\\begin{align}\n u(k)-e^{ -aT }u(k-1)=(1-e^{ -aT })e(k-1)\n\\end{align}$$\n\n### 二、差分变换法\n\n将微分方程中的导数项用有限差分来近似等效，得到一个与原微分方程逼近的差分方程。欧拉法\\\n根据 z 变换\\ 的定义，以及泰勒级数\\展开有：\n\n$$\\begin{align}\nz=e^{ Ts }=1+Ts+ \\dfrac{T^{2}s^{2}}{2!}+\\cdots\n\\end{align}$$\n\n离散化稳态增益保持不变，都不能保持脉冲响应和频率响应\n\n#### 1. 前向差分\n$$\\begin{align}\nz=e^{ sT }\\approx 1+Ts\\quad \\Rightarrow\\quad s=\\dfrac{z-1}{T} \\\\\n\\end{align}$$\n前向差分可能将 s 域左半平面的稳定极点映射到 z 平面单位圆外。\n原控制器 $D(s)$ 稳定时，数字控制器 $D(z)$ 不一定稳定，实际一般不用前向差分\n\n#### 2. 后向差分\n\n$$\\begin{align}\n\\dfrac{\\mathrm{d} u(t)}{\\mathrm{d} t} \\approx \\dfrac{u(k)-u(k-1)}{T}=e(k)\n\\end{align}$$\n\n$$\\begin{align}\ne^{ sT} = \\dfrac{1}{e^{ -sT }} \\approx \\dfrac{1}{1-Ts}\\quad \\Rightarrow\\quad s= \\dfrac{z-1}{Tz} \n\\end{align}$$\n\n后向差分将 s 域左半平面的稳定极点映射到 z 平面单位圆内的一个小圆内。\n如果 $D(s)$ 稳定，则离散化的数字控制器 $D(z)$ 也一定稳定。（应用较多）\n（映射关系有畸变，变换精度较低）\n\n#### 3. 双线性差分 Tustin 变换法\n$$\\begin{align}\nu(k)=u(k-1)+ \\dfrac{T}{2 }[e(k)-e(k-1)]\n\\end{align}$$\n$$\\begin{align}\ne^{ sT }=\\dfrac{e^{ sT/ 2 }}{e^{ -sT / 2 }}\\approx \\dfrac{1+ \\dfrac{T}{2}s}{1- \\dfrac{T}{2 } s}\\quad \\Rightarrow\\quad s= \\dfrac{2}{T} \\dfrac{z-1}{z+1}\n\\end{align}$$\n双线性差分将 s 域左半平面的稳定极点映射到 z 平面单位圆内。\n如果 $D(s)$ 稳定，则离散化的数字控制器 $D(z)$ 也一定稳定。（应用较多）\n[!important] \n注意得到数字控制器后，如果要进一步得到差分方程，要注意不要出现 $z$ 的项，可以上下同除以 $z$ \n\n$$\\begin{align}\nD(z)=\\dfrac{U(z)}{E(z)}= \\dfrac{aT}{z+(aT-1)}=\\dfrac{aTz^{-1}}{1+(aT-1)z^{-1}}\\; {\\color{red}\\Rightarrow} \\; u(k)=aTe(k-1)-(aT-1)u(k-1)\n\\end{align}$$\n$$\\begin{align}\nD("
    },
    "数字 PID 控制器": {
      "id": "数字 PID 控制器",
      "title": "数字 PID 控制器",
      "category": "3. 计算机控制系统",
      "subcategory": "3. 计算机控制系统",
      "tags": [
        "Discrete",
        "Practical",
        "Control"
      ],
      "aliases": [],
      "terminology": "Discrete-time  PID Controller",
      "summary": "Discrete-time PID Controller 离散 PID 控制器",
      "headings": [
        "一、数字 PID 算法",
        "位置式 PID 算法",
        "增量式 PID 算法",
        "一般 PID 算法的离散化",
        "二、改进的数字 PID 算法",
        "积分分离算法",
        "抗饱和积分算法",
        "遇限削弱算法",
        "不完全微分",
        "微分先行",
        "带死区的 PID"
      ],
      "pinned": false,
      "level": null,
      "created": "2025-03-10T10:07:21.000+08:00",
      "updated": "2025-09-12T17:12:34.000+08:00",
      "permalink": "/A2- 控制理论/3. 计算机控制系统/3.2 数字 PID 控制器/",
      "dg_path": "A2- 控制理论/3. 计算机控制系统/3.2 数字 PID 控制器.md",
      "source_path": "src/site/notes/数字 PID 控制器.md",
      "viewer_markdown_path": "../source-notes/数字 PID 控制器.md",
      "internal_links": [
        "数字控制器",
        "模拟控制器离散化"
      ],
      "inbound_links": [
        "PID",
        "参数优化的低阶算法",
        "数字PID 参数整定",
        "数字控制器",
        "计算机控制系统"
      ],
      "out_of_scope_links": [
        "模拟式PID控制器"
      ],
      "missing_links": [],
      "content_excerpt": "Discrete-time PID Controller 离散 PID 控制器 \n\n模拟式PID控制器\\的离散化，得到数字控制器\\\n\n### 一、数字 PID 算法\n已知连续时间的 PID 控制，拉普拉斯变换得到：\n\n$$\\begin{align}\nu(t)=K_{p}\\left[e(t)+ \\dfrac{1}{T_{i}} \\int _{0}^{t} e(\\tau)\\, d\\tau +T_{d}\\dfrac{\\mathrm{d} e(t)}{\\mathrm{d} t} \\right] \\quad {\\color{red}\\Leftrightarrow} \\quad D(s)=\\dfrac{U(s)}{E(s)}= K_{p}(1+\\dfrac{1}{T_{i}s}+T_{d}s)\n\\end{align}$$\n\n$$\\begin{align}\n\\begin{cases}\n & u(t) \\approx u(k) \\\\\n & e(t)\\approx e(k) \\\\\n & \\int _{0}^{t} e{ (\\tau )}\\, d\\tau \\approx \\sum\\limits_{j=0}^{k}e(j)T \\\\ \n & \\dfrac{\\mathrm{d} e(t)}{\\mathrm{d} t} \\approx \\dfrac{e(k)-e(k-1)}{T}\n\\end{cases}\n\\end{align}$$\n\n#### 1. 位置式 PID 算法\n$$\\begin{align}\nu(k)=K_{p}e(k)+K_{i} \\sum\\limits_{j=0}^{k} e(j)+K_{d}\\left[e(k)-e(k-1)\\right]\n\\end{align}$$\n稳态精度高，直观易于理解\n计算量大，容易出现积分饱和\n\n#### 2. 增量式 PID 算法\n$$\\begin{align}\n\\Delta u & =u(k)-u(k-1) \\\\\n & =K_{p}\\left[e(k)-e(k-1)\\right]+K_{i}e(k)+K_{d}\\left[e(k)-2e(k-1)+e(k-2)\\right] \\\\\n & =(K_{p}+K_{i}+K_{d})e(k)-(K_{p}+2K_{d})e(k-1)+K_{d}e(k-2)\n\\end{align}$$\n节约内存和计算时间；控制量冲击小，能平滑过渡\n无积分环节积累，可能存在一定误差\n\n#### 3. 一般 PID 算法的离散化\n一般常用模拟控制器离散化#二、差分变换法\\ ，用后向差分，或双线性差分，并写为控制器的形式\n\n### 二、改进的数字 PID 算法\n\n#### 1. 积分分离算法\n在系统误差较大时，取消积分作用；当误差减小到一定值时，再重新积分。$e_{0}$ 为积分分离阈值\n\n$\\left\\lvert e(k) \\right\\rvert\\leq e_{0}$ 采用 PID 控制，保证稳态误差为 0\n$\\left\\lvert e(k) \\right\\rvert> e_{0}$ 采用 PD 控制，大幅度减小超调量\n\n$$\\begin{align}\nu(k)=K_{p}\\left[e(k)+\\dfrac{T}{T_{i}} {\\color{red}\\sum\\limits_{i=0}^{k} e(i)}+ \\dfrac{T_{d}}{T} \\left(e(k)-e(k-1)\\right)\\right]\n\\end{align}$$\n$$\\sum\\limits_{i=0}^{k} e(i)=\\begin{cases}\n\\sum\\limits_{i=0}^{k} e(i)\\quad \\left\\lvert e(k) \\right\\rvert\\leq e_{0} \\\\ \\\\\n\\sum\\limits_{i=0}^{k-1} e(i)\\quad \\left\\lvert e(k) \\right\\rvert> e_{0} \n\\end{cases}$$\n#### 2. 抗饱和积分算法\n\n输出限幅，输出超限时不积分\n\n$$\\sum\\limits_{i=0}^{k} e(i)=\\begin{cases}\n\\sum\\limits_{i=0}^{k} e(i)\\quad u_{min}\\leq u(k) \\leq u_{max}\\\\ \\\\\n\\sum\\limits_{i=0}^{k-1} e(i)\\quad u_{min}> u(k) \\; \\text{or}\\; u(k)> u_{max}\n\\end{cases}$$\n\n#### 3. 遇限削弱算法\n$$\\sum\\limits_{i=0}^{k} e(i)=\\begin{cases}\n\\sum\\limits_{i=0}^{k} e(i)\\quad \\begin{cases}\n\\left\\lvert u(k) \\right\\rvert \\leq u_{0} \\\\ \\\\\nu(k) > u_{0} \\; \\text{and} \\;e(k) 0 \n\\end{cases}\\\\ \\\\\n\\sum\\limits_{i=0}^{k-1} e(i) \\quad \\begin{cases}\n u(k) > u_{0} \\; \\text{and} \\;e(k)>0 \\\\\n \\\\\n u(k) e_{0} \\\\ \\\\\n\\sum\\limits_{i=0}^{k-1} e(i)\\quad \\left\\lvert e(k) \\right\\rvert\\leq e_{0} \n\\end{cases}$$"
    },
    "数字PID 参数整定": {
      "id": "数字PID 参数整定",
      "title": "数字PID 参数整定",
      "category": "3. 计算机控制系统",
      "subcategory": "3. 计算机控制系统",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "数字 PID 控制器\\的参数整定\n采样周期的选择：满足条件下尽可能大，而不是越小越好 信号采样\\\n### 一、扩充临界比例度法\n选择足够短的采样周期 \n将 PID 设定为纯比例控制，逐步减小比例度，产生等幅振荡，记下此时的比例度和振荡周期\n选定比例度\n查表得到采样周期、比例度、积分时间、微分时间的值",
      "headings": [
        "一、扩充临界比例度法",
        "二、扩充响应曲线法"
      ],
      "pinned": false,
      "level": null,
      "created": "2025-04-03T11:43:31.000+08:00",
      "updated": "2025-09-12T17:10:06.000+08:00",
      "permalink": "/A2- 控制理论/3. 计算机控制系统/3.3 数字PID 参数整定/",
      "dg_path": "A2- 控制理论/3. 计算机控制系统/3.3 数字PID 参数整定.md",
      "source_path": "src/site/notes/数字PID 参数整定.md",
      "viewer_markdown_path": "../source-notes/数字PID 参数整定.md",
      "internal_links": [
        "信号采样",
        "数字 PID 控制器"
      ],
      "inbound_links": [
        "计算机控制系统"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "数字 PID 控制器\\的参数整定\n采样周期的选择：满足条件下尽可能大，而不是越小越好 信号采样\\\n### 一、扩充临界比例度法\n选择足够短的采样周期 \n将 PID 设定为纯比例控制，逐步减小比例度，产生等幅振荡，记下此时的比例度和振荡周期\n选定比例度\n查表得到采样周期、比例度、积分时间、微分时间的值\n\n### 二、扩充响应曲线法\n根据特性曲线\n断开数字控制器，给被控对象阶跃输入信号\n记录下阶跃响应曲线\n在最大斜率处做切线，得到等效纯滞后时间和时间常数\n选择比例度\n经验公式求得各个 PID 参数"
    },
    "数字控制器": {
      "id": "数字控制器",
      "title": "数字控制器",
      "category": "3. 计算机控制系统",
      "subcategory": "3. 计算机控制系统",
      "tags": [],
      "aliases": [],
      "terminology": "Digital Controller",
      "summary": "Digital Controller\n### 一、基本思想 \n将系统中被控对象及零阶保持器进行离散化，得到广义对象 $G(z)=\\mathscr{Z}[G_{h}(s)G_{0}(s)]$\n根据系统的性能指标及约束条件，确定闭环期望传递函数 $\\varPhi(z)$ 或误差传递函数 $\\varPhi_{e}(z)$\n进一步得到数字控制器 $D(z)$\n将 $D(z)$ 写为差分方程的形式，得到控制算法",
      "headings": [
        "一、基本思想",
        "二、数字控制器一般形式",
        "三、零阶保持器和惯性环节串联的 z 变换",
        "零阶保持器和一阶惯性环节串联 (一阶)",
        "零阶保持器和一阶惯性环节与一阶积分串联 (二阶)",
        "零阶保持器和二阶惯性环节串联（二阶）",
        "四、数字控制器的可实现性",
        "五、常用数字控制器"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-10-08T10:26:32.000+08:00",
      "updated": "2026-01-03T18:25:07.639+08:00",
      "permalink": "/A2- 控制理论/3. 计算机控制系统/4.1 数字控制器/",
      "dg_path": "A2- 控制理论/3. 计算机控制系统/4.1 数字控制器.md",
      "source_path": "src/site/notes/数字控制器.md",
      "viewer_markdown_path": "../source-notes/数字控制器.md",
      "internal_links": [
        "信号保持",
        "参数优化的低阶算法",
        "大林算法控制器",
        "数字 PID 控制器",
        "最小拍控制器"
      ],
      "inbound_links": [
        "信号保持",
        "参数优化的低阶算法",
        "大林算法控制器",
        "数字 PID 控制器",
        "最小拍控制器",
        "计算机控制系统"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "Digital Controller\n### 一、基本思想 \n将系统中被控对象及零阶保持器进行离散化，得到广义对象 $G(z)=\\mathscr{Z}[G_{h}(s)G_{0}(s)]$\n根据系统的性能指标及约束条件，确定闭环期望传递函数 $\\varPhi(z)$ 或误差传递函数 $\\varPhi_{e}(z)$\n进一步得到数字控制器 $D(z)$\n将 $D(z)$ 写为差分方程的形式，得到控制算法\n\n### 二、数字控制器一般形式\n\n广义对象传递函数： 信号保持\\\n\n$$\\begin{align}\nG(z)=\\mathscr{Z}[G_{h}(s)G_{0}(s)]=G_{h}G_{0}(z)=(1-z^{-1}) \\mathscr{Z}[ \\dfrac{G_{0}(s)}{s}]\n\\end{align}$$\n\n误差传递函数及误差序列：\n\n$$\\begin{align}\n\\varPhi_{e}(z)= \\dfrac{E(z)}{R(z)}= \\dfrac{1}{1+D(z)G(z)}\\quad \\quad e(k)=\\mathscr{Z}^{-1} [\\varPhi_{e}(z)R(z)]\n\\end{align}$$\n\n闭环传递函数及输出序列：\n\n$$\\begin{align}\n\\varPhi(z)= \\dfrac{Y(z)}{R(z)}= \\dfrac{D(z)G(z)}{1+D(z)G(z)}=D(z)G(z)\\varPhi_{e}(z) = 1- \\varPhi_{e}(z)\\quad \\quad y(k)=\\mathscr{Z}^{-1}[\\varPhi(z)R(z)]\n\\end{align}$$\n$$\\begin{align}\nY(z)+E(z)=R(z)\\quad \\quad y(k)=r(k)-e(k)\n\\end{align}$$\n\n数字控制器及控制序列： \n\n$$\\begin{align}\n D(z)=\\dfrac{U(z)}{E(z)}= \\dfrac{1}{G(z)} \\dfrac{\\varPhi(z)}{1-\\varPhi(z)}\\quad \\quad u(k)=\\mathscr{Z}^{-1}[D(z)E(z)]\n\\end{align}$$\n[!question] \n离散序列指的是 $u(kT)$，为书写方便，可以直接写为 $u(k)$\n\n### 三、零阶保持器和惯性环节串联的 z 变换\n\n#### 1. 零阶保持器和一阶惯性环节串联 (一阶)\n\n$$\\begin{align}\n & \\mathscr{Z} \\left[ \\dfrac{1-e^{ -sT }}{s}\\times \\dfrac{1}{T_{1}s+1}\\right] \\\\\n=& (1-z^{-1})\\mathscr{Z} \\left[ \\dfrac{1}{s(T_{1}s+1)} \\right] = (1-z^{-1})\\mathscr{Z} \\left[ \\dfrac{1}{s} -\\dfrac{T_{1}}{T_{1}s+1} \\right] \\\\\n = &(1-z^{-1}) \\mathscr{Z} \\left[ \\dfrac{1}{s}- \\dfrac{1}{s+ \\dfrac{1}{T_{1}}} \\right] = \\left(1- \\dfrac{1-z^{-1}}{1- e^{ -T/T_{1} }z^{-1}}\\right) \\\\\n = & \\dfrac{ (1-e^{ -T/T_{1} } ) z^{-1}}{1-e^{ -T/T_{1} }z^{-1}}\n\\end{align}$$\n\n#### 2. 零阶保持器和一阶惯性环节与一阶积分串联 (二阶)\n\n$$\\begin{align}\n & \\mathscr{Z} \\left[ \\dfrac{1-e^{ -sT }}{s}\\times \\dfrac{1}{s(T_{1}s+1)} \\right] =(1-z^{-1})\\mathscr{Z} \\left[ \\dfrac{1}{s^{2}(T_{1}s+1)}\\right] \\\\\n= & (1-z^{-1})\\mathscr{Z} \\left[ \\dfrac{1}{s^{2}}+ \\dfrac{-T_{1}}{s}+ \\dfrac{T_{1}}{s+\\dfrac{1}{T_{1}}} \\right] \\\\\n= & \\dfrac{Tz^{-1}-T_{1}(1-z^{-1})}{1-z^{-1}}+ \\dfrac{T_{1}(1-z^{-1})}{ 1-e^{ -T/T_{1} }z^{-1}} \\\\\n= & \\dfrac{(T-T_{1}+T_{1}e^{ -T/T_{1} })z^{-1}+(T_{1}-Te^{ -T/T_{1} }-T_{1}e^{ -T/T_{1} })z^{-2}}{(1-z^{-1})(1-e^{ -T/T_{1} }z^{-1})} \\\\\n= & \\dfrac{c_{1} z^{-1}+c_{2}z^{-2}}{(1-z^{-1})(1-e^{ -T/T_{1} }z^{-1})} \\\\\n \\\\\n & \\begin{cases}\nc_{1}=T-T_{1}+T_{1}e^{ -T/T_{1} } \\\\\nc_{2}=T_{1}-(T+T_{1})e^{ -T/T_{1}}\n\\end{cases}\n\\end{align}$$\n\n#### 3. 零阶保持器和二阶惯性环节串联（二阶）\n\n$$\\begin{align}\n & \\mathscr{Z} \\left[ \\dfrac{1-e^{ -Ts }}{s} \\dfrac{1}{(T_{1}s+1)(T_{2}s+1)} \\right]"
    },
    "参数优化的低阶算法": {
      "id": "参数优化的低阶算法",
      "title": "参数优化的低阶算法",
      "category": "3. 计算机控制系统",
      "subcategory": "3. 计算机控制系统",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "一阶控制器：\n$$\\begin{align}\nD(z)=\\dfrac{a_{0}+a_{1}z^{-1}}{1-z^{-1}}\n\\end{align}$$\n$$\\begin{align}\nu(k)=u(k-1)+a_{0}e(k)+a_{1}e(k-1)\n\\end{align}$$",
      "headings": [
        "参数优化的低阶算法"
      ],
      "pinned": false,
      "level": null,
      "created": "2025-04-08T09:31:53.000+08:00",
      "updated": "2025-05-02T17:47:14.000+08:00",
      "permalink": "/A2- 控制理论/3. 计算机控制系统/4.2 参数优化的低阶算法/",
      "dg_path": "A2- 控制理论/3. 计算机控制系统/4.2 参数优化的低阶算法.md",
      "source_path": "src/site/notes/参数优化的低阶算法.md",
      "viewer_markdown_path": "../source-notes/参数优化的低阶算法.md",
      "internal_links": [
        "数字 PID 控制器",
        "数字控制器"
      ],
      "inbound_links": [
        "数字控制器",
        "计算机控制系统"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "数字控制器\\\n\n### 参数优化的低阶算法\n能消除静差的数字控制器的最简单结构为：\n$$\\begin{align}\nD(z)=\\dfrac{{a}_{0} + {a}_{1}z^{-1} + \\cdots + {a}_{m}z^{-m}}{1-z^{-1}}\n\\end{align}$$\n\n一阶控制器：\n$$\\begin{align}\nD(z)=\\dfrac{a_{0}+a_{1}z^{-1}}{1-z^{-1}}\n\\end{align}$$\n$$\\begin{align}\nu(k)=u(k-1)+a_{0}e(k)+a_{1}e(k-1)\n\\end{align}$$\n\n二阶控制器：\n$$\\begin{align}\nD(z)=\\dfrac{a_{0}+a_{1}z^{-1}+ a_{2}z^{-2}}{1-z^{-1}}\n\\end{align}$$\n\n$$\\begin{align}\nu(k)=u(k-1) + a_{0} e(k)+ a_{1}e(k-1) +a_{2}e(k-2)\n\\end{align}$$\n\n当参数的值都大于零时，实际上就是数字 PID 控制器\\（二阶消除静差算法的特例）\n（时间参数默认都大于零）\n\n优化指标：\n$$\\begin{align}\nJ = \\sum\\limits_{k=0}^{M} \\left[e^{2}(k)+ r \\Delta u^{2}(k)\\right]\n\\end{align}$$\n$\\Delta u(k)=u(k)-u(k-1)$\n$\\Delta u(k)=u(k)-u(\\infty)$"
    },
    "最小拍控制器": {
      "id": "最小拍控制器",
      "title": "最小拍控制器",
      "category": "3. 计算机控制系统",
      "subcategory": "3. 计算机控制系统",
      "tags": [],
      "aliases": [],
      "terminology": "Deadbeat Response",
      "summary": "Deadbeat Response 最少调节时间/暂态过程时间最少系统\n在经典输入信号\\作用下，系统可经过最小拍使输出响应的稳态误差为零。（某种特定的输入在最少个采样周期内达到无静差的稳态） 实现时间最优控制",
      "headings": [
        "一、最小拍系统的具体要求",
        "二、最小拍控制控制器的设计",
        "输入信号的类型（基础）",
        "对象存在纯滞后",
        "对象存在单位圆外零点",
        "对象存在单位圆外极点",
        "对象存在单位圆上极点 (1,0)",
        "三、全部情况综合以及实际例题",
        "四、最小拍控制器的局限性",
        "五、最小拍控制器的改进"
      ],
      "pinned": false,
      "level": null,
      "created": "2025-04-13T22:32:41.000+08:00",
      "updated": "2025-09-13T17:41:30.000+08:00",
      "permalink": "/A2- 控制理论/3. 计算机控制系统/4.3 最小拍控制器/",
      "dg_path": "A2- 控制理论/3. 计算机控制系统/4.3 最小拍控制器.md",
      "source_path": "src/site/notes/最小拍控制器.md",
      "viewer_markdown_path": "../source-notes/最小拍控制器.md",
      "internal_links": [
        "数字控制器",
        "最小拍控制器的改进",
        "经典输入信号"
      ],
      "inbound_links": [
        "数字控制器",
        "最小拍控制器的改进",
        "计算机控制系统"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "Deadbeat Response 最少调节时间/暂态过程时间最少系统\n在经典输入信号\\作用下，系统可经过最小拍使输出响应的稳态误差为零。（某种特定的输入在最少个采样周期内达到无静差的稳态） 实现时间最优控制\n\n### 一、最小拍系统的具体要求\n无静差：特定参考输入信号，在达到稳态后，在采样点的输出值准确跟随输入信号，不存在静差\n最小拍：在有限拍内达到稳态，准确跟随输入信号所需的采样周期最少\n可实现：必须在物理上可实现\n稳定：闭环系统必须稳定\n\n### 二、最小拍控制控制器的设计\n\n数字控制器\\\n\n广义对象传递函数：\n\n$$\\begin{align}\nG(z)=\\mathscr{Z}[G_{h}(s)G_{0}(s)]=G_{h}G_{0}(z)=(1-z^{-1}) \\mathscr{Z}[ \\dfrac{G_{0}(s)}{s}]\n\\end{align}$$\n[!important] \n注意要写为标准型，便于观察是否存在单位圆外的零极点，例如：\n$$\\begin{align}\nG(z)=\\dfrac{z^{-1}(a+z^{-1})}{(b+cz^{-1})}=\\dfrac{a}{b} \\dfrac{z^{-1}(1+ \\dfrac{1}{a}z^{-1})}{(1+ \\dfrac{c}{b}z^{-1})} \n\\end{align}$$\n\n#### 1. 输入信号的类型（基础）\n根据输入信号的类型，在误差传递函数上消除误差\n\n输入信号的一般形式及稳态误差：\n$$\\begin{align}\nr(t)=t^ {{\\color{red} n-1}} \\; {\\color{red}\\Rightarrow} \\;\\quad R(z)= \\dfrac{A(z)}{ {\\color{red} (1-z^{-1})^{n} } }\\quad \\;e(\\infty)= \\lim\\limits_{ z \\to 1 } (1-z^{-1})R(z)\\varPhi_{e}(z) =0\n\\end{align}$$\n\n满足稳态误差为零且最小拍的误差传递函数：\n$$\\begin{align}\n\\varPhi_{e}(z)= \\dfrac{E(z)}{R(z)} = {\\color{red} (1-z^{-1})^{n} } \\\\\n\\end{align}$$\n得到期望的闭环传递函数：\n$$\\begin{align}\n\\varPhi(z)=\\dfrac{Y(z)}{R(z)}=1-\\varPhi_{e}(z)= 1- (1-z^{-1})^{n} ={\\color{red} {m}_{1} z^{-1}+ {m}_{2} z^{-2}+ \\cdots + {m}_{n}z^{-n} } \n\\end{align}$$\n\n进一步得到数字控制器：\n$$\\begin{align}\n D(z)= \\dfrac{U(z)}{E(z)} = \\dfrac{\\varPhi(z)}{G(z)\\varPhi_{e}(z)} =\\dfrac{1-(1-z^{-1})^{m}}{G(z)(1-z^{-1})^{m}}\n\\end{align}$$\n\n$$\\begin{cases}\nR(z)= \\dfrac{A(z)}{ {\\color{Red}(1-z^{-1})^{N}}}\\quad {\\Rightarrow} \\quad \\varPhi_{e}(z)= {\\color{Red}(1-z^{-1})^{N}}\\\\ \\\\\nG(z) \\quad {\\Rightarrow} \\quad \\varPhi(z)= {\\color{Red} {m}_{1} z^{-1}+ {m}_{2} z^{-2}+ \\cdots + {m}_{N}z^{-N}}\n\\end{cases}$$\n\n#### 2. 对象存在纯滞后\n如果对象存在纯滞后，需要在闭环传递函数上将纯滞后消除\n\n$$\\begin{align}\nD(z)= \\dfrac{1}{ G(z)z^{-({\\color{#c44f70}M}+1)}} \\dfrac{\\varPhi(z) {\\color{#c44f70}z^{-M}}}{\\varPhi_{e}'(z)}\n\\end{align}$$\n\n$$\\begin{cases}\nR(z)= \\dfrac{A(z)}{ {\\color{Red}(1-z^{-1})^{N}}}\\quad & {\\Rightarrow} \\quad \\varPhi_{e}'(z)= {\\color{Red}(1-z^{-1})^{N}} {\\color{#c44f70} (1+f_{1}z^{-1}+f_{2}z^{-2}+\\cdots+ f_{M}z^{-M}) }\n\\\\ \n\\\\\n\\quad \\quad G(z) {z^{-({\\color{#c44f70}M}+1)}} \\quad & {\\Rightarrow} \\quad \\varPhi'(z)={\\color{#c44f70}z^{-M}} ( {\\color{Red} {m}_{1} z^{-1}+ {m}_{2} z^{-2}+ \\cdots +{m}_{N}^{-N}})\n\\end{cases}$$\n注意广义对象由于串联零阶保持器，带 $z^{-1}$ 一个纯滞后，这个纯滞后是不计算在对象的纯滞后上的。一般如果对象表示为 $G(z)z^{-(M+1)}$，则表示有 $M$ 个纯滞后\n\n#### 3. 对象存在单位圆外零点\n对象单位圆外零点在闭环传递函数消除\n\n$$\\begin{align}\nD(z)= \\dfrac{1}{G(z)\\cdot{\\color{#c44f70}\\prod\\limits_{i=1}^{q}(1-b_{i}z^"
    },
    "最小拍控制器的改进": {
      "id": "最小拍控制器的改进",
      "title": "最小拍控制器的改进",
      "category": "3. 计算机控制系统",
      "subcategory": "3. 计算机控制系统",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "首先根据最小拍控制器\\的设计，考虑所有情况得到误差传递函数或闭环传递函数，再进行改进\n### 一、无波纹最小拍控制器\n在 5 种情况后，再消除被控对象的单位圆内零点。",
      "headings": [
        "一、无波纹最小拍控制器",
        "二、惯性因子法最小拍控制器",
        "三、非最小的有限拍控制器"
      ],
      "pinned": false,
      "level": null,
      "created": "2025-04-15T09:36:55.000+08:00",
      "updated": "2025-09-12T19:02:56.000+08:00",
      "permalink": "/A2- 控制理论/3. 计算机控制系统/4.4 最小拍控制器的改进/",
      "dg_path": "A2- 控制理论/3. 计算机控制系统/4.4 最小拍控制器的改进.md",
      "source_path": "src/site/notes/最小拍控制器的改进.md",
      "viewer_markdown_path": "../source-notes/最小拍控制器的改进.md",
      "internal_links": [
        "最小拍控制器"
      ],
      "inbound_links": [
        "最小拍控制器",
        "计算机控制系统"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "首先根据最小拍控制器\\的设计，考虑所有情况得到误差传递函数或闭环传递函数，再进行改进\n### 一、无波纹最小拍控制器\n在 5 种情况后，再消除被控对象的单位圆内零点。\n\n例题：\n$$\\begin{align}\nG(z)=\\dfrac{(1+0.5z^{-1})(1+1.5z^{-1})}{(1-0.3z^{-1})(1-1.3z^{-1})}z^{-2}\\quad r(t)= \\dfrac{1}{2}t^{2}\n\\end{align}$$\n\n$$\\begin{cases}\n\\;\\varPhi_{e}(z) & = (1-z^{-1})^{3}(1-1.3z^{-1}) (1+f_{1}z^{-1}+\\cdots+f_{3}z^{-3})\\\\ \\\\\n\n\\;\\;\\varPhi(z) & =z^{-1}(1+1.5z^{-1}) {\\color{red} (1+0.5z^{-1}) } (m_{1}z^{-1}+\\cdots+m_{4}z^{-4})\n\\end{cases}$$\n\n### 二、惯性因子法最小拍控制器\n它以损失控制的有限拍无差性质为代价，而使系统对多种类型的输入有较满意的响应\n$$\\begin{align}\n\\varPhi_{e}'(z)= \\dfrac{\\varPhi_{e}(z)}{1-cz^{-1}}\\; {\\color{red}\\Rightarrow} \\; \\varPhi(z)'=\\dfrac{1-cz^{-1}-\\varPhi_{e}(z)}{1-cz^{-1}}\n\\end{align}$$\n\n### 三、非最小的有限拍控制器\n基本思想：在最小拍的基础上，将闭环传递函数的 $z^{-1}$ 的幂次适当提高一到二阶。会增加一些自由度，一般情况下，这有利于降低系统对参数变化的敏感性，并减小控制作用：\n$$\\begin{align}\n\\varPhi_{e}'(z)= \\varPhi_{e}(z)F(z)\\; {\\color{red}\\Rightarrow} \\; \\varPhi(z)'=1-\\varPhi_{e}(z)F(z)\n\\end{align}$$\n$F(z)=1+kz^{-1}$ (取 $k$，保证单位圆内)"
    },
    "史密斯预估补偿控制": {
      "id": "史密斯预估补偿控制",
      "title": "史密斯预估补偿控制",
      "category": "3. 计算机控制系统",
      "subcategory": "3. 计算机控制系统",
      "tags": [],
      "aliases": [],
      "terminology": null,
      "summary": "被控对象含纯滞后环节的闭环传递函数：\n$$\\begin{align}\nG(s)= G_{0}(s) e^{ -\\tau s }\\quad \\quad W(s)= \\dfrac{D(s)G_{0}(s)e^{ -\\tau s }}{1+D(s)G_{0}(s)e^{ -\\tau s }}\n\\end{align}$$\n注意这里是将被控对象不包含纯滞后的部分作为 $G_{0}(s)$",
      "headings": [
        "一、基本补偿原理",
        "二、控制算法"
      ],
      "pinned": false,
      "level": null,
      "created": "2025-04-03T12:11:33.000+08:00",
      "updated": "2025-09-12T20:56:50.000+08:00",
      "permalink": "/A2- 控制理论/3. 计算机控制系统/4.5 史密斯预估补偿控制/",
      "dg_path": "A2- 控制理论/3. 计算机控制系统/4.5 史密斯预估补偿控制.md",
      "source_path": "src/site/notes/史密斯预估补偿控制.md",
      "viewer_markdown_path": "../source-notes/史密斯预估补偿控制.md",
      "internal_links": [
        "模拟控制器离散化"
      ],
      "inbound_links": [
        "计算机控制系统"
      ],
      "out_of_scope_links": [],
      "missing_links": [],
      "content_excerpt": "### 一、基本补偿原理\n\n被控对象含纯滞后环节的闭环传递函数：\n$$\\begin{align}\nG(s)= G_{0}(s) e^{ -\\tau s }\\quad \\quad W(s)= \\dfrac{D(s)G_{0}(s)e^{ -\\tau s }}{1+D(s)G_{0}(s)e^{ -\\tau s }}\n\\end{align}$$\n注意这里是将被控对象不包含纯滞后的部分作为 $G_{0}(s)$\n\n造成系统难以控制的本质是特征方程中含有纯滞后环节，引入与含纯滞后环节的被控对象并联的补偿器，称为史密斯预估补偿器 $G_{m}(s)$: \n\n$$\\begin{align}\nW_{1}(s)=\\dfrac{D(s)G_{0}(s)e^{ -\\tau s }}{1+D(s)G_{0}(s)e^{ -\\tau s }+ D(s)G_{m}(s)}= \\dfrac{D(s)G_{0}(s)e^{ -\\tau s }}{1+D(s)G_{0}(s)} \\; \\;{\\color{red}\\Rightarrow} \\; \\; G_{m}(s)=G_{0}(s)(1-e^{ -\\tau s })\n\\end{align}$$\n\n### 二、控制算法\n对补偿器模拟控制器离散化#1.2 阶跃响应不变法\\进行离散化\n\n$$\\begin{align}\nG_{m}(z) =\\mathscr{Z} \\left[ G_{m}(s)G_{h}(s) \\right] =\\mathscr{Z}\\left[G_{0}(s)(1-e^{ -\\tau s } ) \\dfrac{1-e^{ -T s }}{s}\\right] =(1-z^{-1})(1-z^{-N}) \\mathscr{Z}[ \\dfrac{G_{0}(s)}{s}]\\quad N= \\dfrac{\\tau}{T}\n\\end{align}$$\n\n再写为控制算法的形式：\n$$\\begin{align}\nG_{m}(z)=\\dfrac{Q(z)}{U(z)}\\; {\\color{red}\\Rightarrow} \\; q(k)=\\mathscr{Z}^{-1} \\left[ G_{m}(z)U(z) \\right] \n\\end{align}$$\n[!important] \n千万要注意题目的表达 ! 不要被符号搞混了\n要注意给的被控对象可能直接写为 $G_{0}(s)$ , 要把其中的纯滞后提出来！ \n\n$$\\begin{align}\ne^{ -\\tau s }\\approx \\dfrac{1- \\dfrac{1}{2}\\tau s+\\dfrac{1}{8}\\tau^{2}s^{2}}{1+ \\dfrac{1}{2}\\tau s+\\dfrac{1}{8}\\tau^{2}s^{2}} \n\\end{align}$$"
    },
    "大林算法控制器": {
      "id": "大林算法控制器",
      "title": "大林算法控制器",
      "category": "3. 计算机控制系统",
      "subcategory": "3. 计算机控制系统",
      "tags": [],
      "aliases": [],
      "terminology": "Dahlin",
      "summary": "Dahlin\n针对于含有纯滞后环节的连续被控对象，将超调量作为主要的设计指标",
      "headings": [
        "一、基本形式",
        "二、振铃现象",
        "振铃现象产生原因",
        "振铃幅度",
        "消除振铃现象"
      ],
      "pinned": false,
      "level": null,
      "created": "2025-04-08T09:34:41.000+08:00",
      "updated": "2025-09-26T12:17:38.000+08:00",
      "permalink": "/A2- 控制理论/3. 计算机控制系统/4.6 大林算法控制器/",
      "dg_path": "A2- 控制理论/3. 计算机控制系统/4.6 大林算法控制器.md",
      "source_path": "src/site/notes/大林算法控制器.md",
      "viewer_markdown_path": "../source-notes/大林算法控制器.md",
      "internal_links": [
        "数字控制器",
        "模拟控制器离散化"
      ],
      "inbound_links": [
        "数字控制器",
        "计算机控制系统"
      ],
      "out_of_scope_links": [
        "带纯滞后的惯性环节"
      ],
      "missing_links": [],
      "content_excerpt": "Dahlin\n针对于含有纯滞后环节的连续被控对象，将超调量作为主要的设计指标\n\n设计目标：设计合适的数字控制器\\，使得闭环系统的传递函数为带纯滞后的惯性环节\\，且闭环系统的纯滞后时间与被控对象的纯滞后时间完全相同，且为采样周期的整数倍。\n\n### 一、基本形式\n\n期望的闭环传递函数，使用模拟控制器离散化#1.2 阶跃响应不变法\\进行离散化（和零阶保持器串联）：\n\n$$\\begin{align}\n\\tau=NT\\; {\\color{red}\\Rightarrow} \\;\\varPhi(s)= \\dfrac{e^{ -NT s}}{T_{0}s+1} \\; {\\color{red}\\Rightarrow} \\; \\varPhi(z)=\\mathscr{Z}\\left[\\dfrac{1-e^{ -Ts }}{s} \\cdot\\dfrac{e^{ -NT s}}{T_{0}s+1}\\right]\n\\end{align}$$\n\n广义对象的传递函数：\n\n$$\\begin{align}\nG(z)=\\mathscr{Z} \\left[ G_{0}(s)G_{h}(s) \\right] =(1-z^{-1}) \\mathscr{Z} \\left[ \\dfrac{G_{0}(s)}{s} \\right] \n\\end{align}$$\n\n得到大林算法控制器：\n\n$$\\begin{align}\nD(z)= \\dfrac{1}{G(z)} \\dfrac{\\varPhi(z)}{1-\\varPhi(z)}=\\dfrac{1}{G(z)} \\,\\cdot\\,\\dfrac{(1-e^{ -T/T_{0} })z^{-(N+1)}}{1-e^{ -T/T_{0} }z^{-1}-(1-e^{ -T/T_{0} })z^{-(N+1)}}\n\\end{align}$$\n期望闭环传递函数和广义对象都可数字控制器#零阶保持器和惯性环节串联的 z 变换\\\n\n### 二、振铃现象\n\nRinging 现象：数字控制器 $D(z)$ 的控制器输出会以 $\\dfrac{1}{2}$ 采样频率大幅度上下摆动\n振铃现象对系统的输出几乎无影响，但会增加执行机构的磨损，并影响多参数系统的稳定性\n\n#### 1. 振铃现象产生原因\n\n数字控制器的输出量和系统参考输入量之间的关系为：\n\n$$\\begin{align}\nU(z)= \\dfrac{Y(z)}{G(z)}=\\dfrac{\\varPhi(z)R(z)}{G(z)}=\\dfrac{\\varPhi(z)}{G(z)} R(z) = \\dfrac{D(z)}{1+D(z)G(z)}R(z)=\\varPhi_{u}(z)R(z)\n\\end{align}$$\n\n对于纯滞后的二阶惯性环节对象，会产生与 $z=-1$ 相近的极点，此极点将引起振铃现象。\n\n#### 2. 振铃幅度\n\nRinging Amplitude：系统单位阶跃信号的作用下，数字控制器第 0 拍和第 1 拍输出的差值，实际上就是输入和控制器输出的传递函数分母 $z^{-1}$ 的系数和分子 $z^{-1}$ 的系数之差：\n\n$$\\begin{align}\n\\varPhi_{u}(z)= \\dfrac{\\varPhi(z)}{G(z)} =\\dfrac{D(z)}{1+D(z)G(z)}=\\dfrac{1+b_{1}z^{-1}+b_{2}z^{-2}+\\cdots}{1+a_{1}z^{-1}+a_{2}z^{-2}+\\cdots} \n\\end{align}$$\n\n$$\\begin{align}\n & U(z)=\\varPhi_{u}(z)R(z) \\\\\n & =\\dfrac{1+b_{1}z^{-1}+b_{2}z^{-2}+\\cdots}{1+a_{1}z^{-1}+a_{2}z^{-2}+\\cdots} \\dfrac{1}{1-z^{-1}} \\\\\n & =1+(b_{1}-a_{1}+1)z^{-1}+\\cdots\\; \\\\\n{\\color{red}\\Rightarrow} \\; & RA= 1-(b_{1}-a_{1}+1)=a_{1}-b_{1}\n\\end{align}$$\n\n例子：\n$$\\begin{align}\n\\varPhi_{u}(z)= \\dfrac{1}{1+0.5z^{-1}}\\quad b_{0}=0,a_{0}=0.5\\quad RA=0.5\n\\end{align}$$\n$$\\begin{align}\n\\varPhi_{u}(z)= \\dfrac{1-0.5z^{-1}}{(1+0.5z^{-1})(1-0.2z^{-1})}\\quad b_{0}=-0.5,a_{0}=0.3\\quad RA=0.3-(-0.5)=0.8\n\\end{align}$$\n\n#### 3. 消除振铃现象\n令控制器导致振铃的极点项(接近 $z=-1$) 的 $z$ 直接为 1，影响动态响应，但是不影响静态\n$(1+az^{-1})\\; {\\color{red}\\Rightarrow} \\;(1+a)$\n$$\\begin{align}\nD(z)=\\dfrac{K(1-0.9512z^{-1})(1-0.989z^{-1})}{{\\color{red} (1+0.9619z^{-1}) } (1-0.9355z^{-1})}=\\dfrac{K(1-0.9512z^{-1})(1-0.989z^{-1})}{{\\color{red} 1.9619 }(1-0.9355z^{-1})}\n\\end{align}$$\n修正的闭环传递函数：\n$$\\begin{align}\n\\varPhi_{k}(z)=D(z)G(z)\\quad \\varPhi(z)=\\dfrac{D"
    },
    "计算机控制系统": {
      "id": "计算机控制系统",
      "title": "计算机控制系统",
      "category": "3. 计算机控制系统",
      "subcategory": "3. 计算机控制系统",
      "tags": [
        "Subject"
      ],
      "aliases": [
        "离散控制系统"
      ],
      "terminology": "Computer Control System",
      "summary": "Computer Control System\n计算机\\参与控制的闭环控制系统，也称数字控制系统或离散控制系统。",
      "headings": [
        "一、计算机控制的信号转换与模型",
        "信号转换基础",
        "核心工具",
        "离散控制系统分析",
        "二、数字控制器模拟化设计方法",
        "三、数字控制器的 z 域直接设计方法"
      ],
      "pinned": true,
      "level": null,
      "created": "2025-03-04T09:26:38.000+08:00",
      "updated": "2025-09-10T22:58:34.000+08:00",
      "permalink": "/A2- 控制理论/3. 计算机控制系统/计算机控制系统/",
      "dg_path": "A2- 控制理论/3. 计算机控制系统/计算机控制系统.md",
      "source_path": "src/site/notes/计算机控制系统.md",
      "viewer_markdown_path": "../source-notes/计算机控制系统.md",
      "internal_links": [
        "信号保持",
        "信号采样",
        "参数优化的低阶算法",
        "史密斯预估补偿控制",
        "大林算法控制器",
        "数字 PID 控制器",
        "数字PID 参数整定",
        "数字控制器",
        "最小拍控制器",
        "最小拍控制器的改进",
        "模拟控制器离散化",
        "离散系统的稳定性分析",
        "离散系统稳态分析",
        "线性定常系统的差分方程求解",
        "脉冲传递函数",
        "计算机控制系统概述"
      ],
      "inbound_links": [
        "自动控制原理"
      ],
      "out_of_scope_links": [
        "ADC",
        "DAC",
        "z 反变换",
        "z 变换",
        "计算机"
      ],
      "missing_links": [
        "广义 z 变换"
      ],
      "content_excerpt": "Computer Control System\n计算机\\参与控制的闭环控制系统，也称数字控制系统或离散控制系统。\n\n计算机控制系统概述\\\n\n### 一、计算机控制的信号转换与模型\n\n离散时间系统： 采样控制系统/脉冲控制系统。控制系统中，有一处或几处信号是脉冲序列或数字序列，定义在离散时间上，这样的系统即为离散时间系统，简称为离散系统。\n\n#### 1. 信号转换基础\n采样器：信号采样\\ \n保持器：信号保持\\\n数字控制器：数字控制器设计\n模数转换：ADC\\ 数模转换：DAC\\\n采样器、保持器、数字控制器的结构形式及控制规律决定系统的动态性能，是主要的研究对象\n系统的稳态控制精度由 A/D D/A 转换器的分辨率决定，而不影响动态性能。\n\n#### 2. 核心工具\n\n核心工具：z 变换\\ z 反变换\\ 广义 z 变换\\\n差分方程求解：线性定常系统的差分方程求解\\\n离散系统中的传递函数：脉冲传递函数\\\n\n#### 3. 离散控制系统分析\n\n离散系统的稳定性分析\\\n离散系统的暂态分析\n离散系统稳态分析\\\n\n### 二、数字控制器模拟化设计方法\n直接设计连续系统的模拟控制器 $D(s)$，将其离散化得到等价的数字控制器 $D(z)$\n\n模拟控制器离散化\\\n数字 PID 控制器\\\n数字PID 参数整定\\\n\n### 三、数字控制器的 z 域直接设计方法\n写出控制器传递函数后，还要写出对应的控制器算法，得到差分方程\n\n数字控制器\\\n参数优化的低阶算法\\\n最小拍控制器\\\n最小拍控制器的改进\\\n史密斯预估补偿控制\\\n大林算法控制器\\"
    },
    "MPC": {
      "id": "MPC",
      "title": "MPC",
      "category": "4. 先进控制理论",
      "subcategory": "4. 先进控制理论",
      "tags": [],
      "aliases": [
        "模型预测控制"
      ],
      "terminology": "Model Predictive Control",
      "summary": "Model Predictive Control 模型预测控制\n它通过预测系统未来的行为来计算当前的最优控制\\动作\n模型预测控制（MPC）是一种先进的控制策略，它在每个时间步，利用系统模型预测未来的行为，并求解一个优化问题来确定当前的最优控制输入。MPC 的核心思想是滚动优化 (Receding Horizon Optimization) 和反馈校正 (Feedback Correction)，使其能够处理复杂的约束和多变量系统，在机器人\\、自动驾驶和工业过程控制等领域得到广",
      "headings": [
        "一、核心思想：预测未来，优化当下",
        "二、基本原理",
        "预测模型 (Prediction Model)",
        "滚动优化 (Receding Horizon Optimization)",
        "反馈校正 (Feedback Correction)",
        "三、数学公式：优化问题",
        "四、优缺点分析",
        "五、应用领域"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-08-18T23:01:08.000+08:00",
      "updated": "2025-09-01T10:46:16.000+08:00",
      "permalink": "/A2- 控制理论/4. 先进控制理论/MPC/",
      "dg_path": "A2- 控制理论/4. 先进控制理论/MPC.md",
      "source_path": "src/site/notes/MPC.md",
      "viewer_markdown_path": "../source-notes/MPC.md",
      "internal_links": [],
      "inbound_links": [],
      "out_of_scope_links": [
        "机器人"
      ],
      "missing_links": [
        "最优控制",
        "运动规划"
      ],
      "content_excerpt": "Model Predictive Control 模型预测控制\n它通过预测系统未来的行为来计算当前的最优控制\\动作\n模型预测控制（MPC）是一种先进的控制策略，它在每个时间步，利用系统模型预测未来的行为，并求解一个优化问题来确定当前的最优控制输入。MPC 的核心思想是滚动优化 (Receding Horizon Optimization) 和反馈校正 (Feedback Correction)，使其能够处理复杂的约束和多变量系统，在机器人\\、自动驾驶和工业过程控制等领域得到广泛应用。\n\n### 一、核心思想：预测未来，优化当下\nMPC 的核心思想可以概括为：\n预测 (Predict): 在当前时间步 $t$，利用系统的数学模型，根据当前的系统状态和未来一段时间内的控制输入序列，预测系统在未来预测时域 (Prediction Horizon) 内的行为。\n优化 (Optimize): 在预测时域内，求解一个优化问题，找到一个最优的控制输入序列，使得某个性能指标（如跟踪误差、能耗）最小化，同时满足所有系统约束（如执行器限制、安全边界）。\n执行 (Execute): 只执行优化得到的控制序列的第一个控制输入。\n滚动 (Recede): 在下一个时间步 $t+1$，重新测量系统状态，并重复上述过程。预测时域会向前滚动，因此 MPC 也被称为“滚动时域控制”。\n\n### 二、基本原理\n\n#### 1. 预测模型 (Prediction Model)\nMPC 依赖于一个准确的系统模型来预测未来的状态。这个模型可以是线性的或非线性的，离散的或连续的。例如，对于一个简单的线性系统：\n\n$$ x(t+1) = A x(t) + B u(t) $$\n\n其中 $x(t)$ 是系统状态，$u(t)$ 是控制输入，$A, B$ 是系统矩阵。\n\n#### 2. 滚动优化 (Receding Horizon Optimization)\n在每个时间步 $t$，MPC 会：\n定义一个预测时域 $N_p$: 预测未来 $N_p$ 个时间步的系统行为。\n定义一个控制时域 $N_c$: 在未来 $N_c$ 个时间步内优化控制输入（通常 $N_c \\le N_p$）。\n求解优化问题: 找到一个控制序列 $U^ = [u^(t), u^(t+1), \\dots, u^(t+N_c-1)]^T$，使得目标函数最小化，并满足所有约束。\n\n#### 3. 反馈校正 (Feedback Correction)\n\nMPC 的鲁棒性来源于其反馈机制。在每个时间步，MPC 都会重新测量系统的实际状态，并将其作为下一次优化的起始点。这使得 MPC 能够纠正模型误差、外部扰动和未建模动态的影响。\n\n### 三、数学公式：优化问题\nMPC 在每个时间步求解的优化问题通常是一个约束优化问题：\n\n$$ \\min_{u(t), \\dots, u(t+N_c-1)} J(x, u) $$\n\n目标函数 $J(x, u)$: 通常包含两部分：\n状态跟踪误差: 衡量预测状态与期望轨迹之间的偏差。\n控制输入成本: 惩罚过大的控制输入或控制输入的剧烈变化。\n\n$$ J(x, u) = \\sum_{k=1}^{N_p} \\|x(t+k) - x_{ref}(t+k)\\|^2_Q + \\sum_{k=0}^{N_c-1} \\|u(t+k)\\|^2_R $$\n\n其中 $Q, R$ 是权重矩阵。\n\n约束条件: \n系统动力学: $x(t+1) = f(x(t), u(t))$ (由预测模型给出)。\n状态约束: $x_{\\min} \\le x(t+k) \\le x_{\\max}$ (如机器人关节角度限制)。\n控制输入约束: $u_{\\min} \\le u(t+k) \\le u_{\\max}$ (如电机力矩限制)。\n碰撞约束: 机器人不能与障碍物发生碰撞。\n\n### 四、优缺点分析\n\n### 五、应用领域\nMPC 因其强大的处理复杂约束和多变量系统的能力，在许多领域得到广泛应用：\n机器人\\控制: 机器人轨迹跟踪、运动规划\\、无人机控制。\n自动驾驶: 车辆路径跟踪、避障、自适应巡航控制。\n工业过程控制: 化工过程、电力系统、炼油厂等。\n航空航天: 飞行器控制。"
    },
    "卡尔曼滤波": {
      "id": "卡尔曼滤波",
      "title": "卡尔曼滤波",
      "category": "4. 先进控制理论",
      "subcategory": "4. 先进控制理论",
      "tags": [
        "Linear"
      ],
      "aliases": [],
      "terminology": null,
      "summary": "(terminology::Kalman Filter ) \nOptimal-Recursive-Data Processing-Algorithm 优化-递归-数据处理-算法",
      "headings": [
        "引入例子",
        "步骤",
        "数学基础",
        "数据融合",
        "协方差矩阵",
        "核心公式",
        "1.预测",
        "2.校正/更新",
        "推导过程",
        "实际使用",
        "理论"
      ],
      "pinned": false,
      "level": null,
      "created": "2024-10-15T15:57:06.080+08:00",
      "updated": "2025-08-28T21:53:14.000+08:00",
      "permalink": "/A2- 控制理论/4. 先进控制理论/卡尔曼滤波/",
      "dg_path": "A2- 控制理论/4. 先进控制理论/卡尔曼滤波.md",
      "source_path": "src/site/notes/卡尔曼滤波.md",
      "viewer_markdown_path": "../source-notes/卡尔曼滤波.md",
      "internal_links": [
        "状态空间",
        "状态观测器"
      ],
      "inbound_links": [
        "状态观测器"
      ],
      "out_of_scope_links": [
        "协方差矩阵",
        "正态分布",
        "递归"
      ],
      "missing_links": [
        "扩展卡尔曼滤波",
        "滤波电路",
        "贝叶斯估计理论"
      ],
      "content_excerpt": "(terminology::Kalman Filter ) \nOptimal-Recursive-Data Processing-Algorithm 优化-递归-数据处理-算法\n\n最优的线性滤波器，虽然名称为滤波电路\\，但实际上也可属于状态观测器\\（State Observer），用来从输入和输出“重构”系统的状态。\n\n生活中存在大量的不确定性，此算法得以普适地应用\n不存在完美的数学模型\n系统的扰动不可控，较难建模\n测量传感器存在误差\n\n### 引入例子\n估计真实结果，取平均值\n第 $k$ 次测量 $z_{k}$ \n第 $k$ 次的估计值 $\\hat{x}_{k}$\n\n$$\\begin{align}\n\\hat{x}_{k}&=\\dfrac{1}{k}(z_{1}+z_{2}+\\cdots+z_{k}) \\\\\n&=\\dfrac{1}{k}(z_{1}+z_{2}+\\cdots+z_{k-1})+\\dfrac{1}{k} z_{k} \\\\\n&=\\dfrac{k-1}{k} \\dfrac{1}{k-1}(z_{1}+z_{2}+\\cdots+z_{k-1})+\\dfrac{1}{k} z_{k} \\\\\n&=\\dfrac{k-1}{k} \\hat{x}_{k-1}+\\dfrac{1}{k} z_{k} \\\\\n&=\\hat{x}_{k-1}+ \\dfrac{1}{k}(z_{k}-\\hat{x}_{k-1})\n\\end{align}$$\n\n提炼出：\n\n$$\\begin{align}\n\\hat{x}_{k}=\\hat{x}_{k-1}+ K_{k}(z_{k}-\\hat{x}_{k-1})\n\\end{align}$$\n$\\hat{x}_{k}$ 当前估计值\n$\\hat{x}_{k-1}$ 上一次的估计值\n$K_{k}$ Kalman Gain \n$z_{k}$ 当前的测量值\n\n递归\\，且只与上一次的有关联\n\n$$\\begin{align}\nK_{k}= \\large \\dfrac{e_{EST_{k-1}}}{e_{EST_{k-1}}+e_{MEA_{k}}}\n\\end{align}$$\n$e_{EST}$ 估计误差\n$e_{MEA}$ 测量误差\n 测量方法或测量工具（传感器测量）的固定误差范围\n\n$$\\begin{cases}\ne_{EST_{k-1}}\\gg e_{MEA_{k}} & K_{k}\\to 1 & \\hat{x}_{k}=z_{k} \\\\ \\\\\n\ne_{EST_{k-1}}\\ll e_{MEA_{k}} & K_{k}\\to 0 & \\hat{x}_{k}=\\hat{x}_{k-1}\n\\end{cases}$$\n\n### 步骤\n$K_{k}= \\dfrac{e_{EST_{k-1}}}{e_{EST_{k-1}}+e_{MEA_{k}}}$\n$\\hat{x}_{k}=\\hat{x}_{k-1}+ K_{k}(z_{k}-\\hat{x}_{k-1})$\n$e_{EST_{k}}=(1-K_{k})e_{EST_{k-1}}$\n\n### 数学基础\n#### 数据融合\n卡尔曼滤波器把不同来源的数据按不同的信噪比加权“整合”起来\nData Fusion\n\n正态分布\\\n\n$X_{1}\\sim N(\\mu_{1} ,\\sigma_{1}^{2}),X_{2}\\sim N(\\mu_{2} ,\\sigma_{2}^{2})$\n$\\hat{X}=X_{1}+K(X_{2}-X_{1})$ \n$$\\hat{X}=\\begin{cases}\nX_{1}\\quad K=0 \\\\\n \\\\\nX_{2} \\quad K=1\n\\end{cases}$$\n求 $K$ 为何值时，$D(\\hat{X})$ 最小\n\n$$\\begin{align}\nD(\\hat{X})&=(1-K)^{2}\\sigma_{1}^{2}+K^{2}\\sigma_{2} ^{2} \\\\\n\\end{align}$$\n\n$\\dfrac{\\mathrm{d} D(\\hat{X})}{\\mathrm{d} X}=0$ 时，$K=\\dfrac{\\sigma_{1}^{2}}{\\sigma_{1}^{2}+\\sigma_{2}^{2}}$\n\n估计的数据：$\\hat{X}\\sim N(\\dfrac{\\mu_{1}\\sigma_{2}^{2}+\\mu_{2}\\sigma_{1}^{2}}{\\sigma_{1}^{2}+\\sigma_{2}^{2}},\\dfrac{\\sigma_{1}^{2}\\sigma_{2}^{2}}{\\sigma_{1}^{2}+\\sigma_{2}^{2}})$\n\n#### 协方差矩阵\n协方差矩阵\\\n\n### 核心公式\n\n#### 1.预测\n状态空间\\\n\n先验估计值： \n$$\\begin{align}\n\\hat{X}_{k^{-}}=A \\hat{X}_{k-1}+Bu_{k-1}\n\\end{align}$$\n$A$ 为状态矩阵\n$B$ 为控制矩阵\n\n先验误差的协方差矩阵：\n\n$$\\begin{align}\nP_{k^{-}}=AP_{k-1}A^{T}+Q\n\\end{align}$$\n$P_{k-1}$ $k-1$ 次的后验误差的协方差矩阵\n$Q$ 过程误差的协方差矩阵\n\n#### 2.校正/更新\n卡尔曼增益：\n$$\\begin{align}\nK_{k}=\\dfrac{P_{k^{-}}H^{T}}{HP_{k^{-}}H^{T}+R}\n\\end{align}$$\n\n后验估计值：\n$$\\begin{align}\n\\hat{X}_{k}&=\\hat{X}_{k^{-}}+K_{k}(Z_{k}-H \\hat{X}_{k^{-}})\n\\end{align}$"
    },
    "自动控制原理": {
      "id": "自动控制原理",
      "title": "自动控制原理",
      "category": "未分类",
      "subcategory": "未分类",
      "tags": [
        "Control"
      ],
      "aliases": [],
      "terminology": "Principles of Automatic Control",
      "summary": "Principles of Automatic Control",
      "headings": [
        "一、基础知识",
        "二、主要分支",
        "参考资料"
      ],
      "pinned": true,
      "level": 0,
      "created": "2024-10-17T01:25:19.000+08:00",
      "updated": "2025-09-07T13:42:42.000+08:00",
      "permalink": "/A2- 控制理论/自动控制原理/",
      "dg_path": "A2- 控制理论/自动控制原理.md",
      "source_path": "src/site/notes/自动控制原理.md",
      "viewer_markdown_path": "../source-notes/自动控制原理.md",
      "internal_links": [
        "控制系统的数学模型",
        "现代控制理论",
        "系统",
        "经典控制理论",
        "经典输入信号",
        "自动控制系统",
        "计算机控制系统"
      ],
      "inbound_links": [],
      "out_of_scope_links": [
        "z 变换",
        "微分方程",
        "拉普拉斯变换"
      ],
      "missing_links": [
        "最优控制",
        "非线性控制"
      ],
      "content_excerpt": "Principles of Automatic Control\n\n系统分析和设计的目的是通过求取系统\\的运动形式，以稳定性问题的解决为中心，对系统实施有效的控制。\n\n### 一、基础知识\n基本概念：\n\n自动控制系统\\：自动控制原理设计的对象\n经典输入信号\\：函数形式简单，易于产生，方便实验和测试，反映系统在某一方面的性质\n控制系统的数学模型\\：利用数学建模方法，对控制系统进行建模\n\n数学基础：\n\n微分方程\\：描述系统随时间的变化情况，主要数学问题\n拉普拉斯变换\\：将时域转到复频域，将微分方程转为代数方程\nz 变换\\：采样信号的拉普拉斯变换，主要在离散系统中使用\n\n### 二、主要分支\n\n经典控制理论\\：以传递函数为基础，研究 SISO 线性定常系统\n现代控制理论\\：以状态空间为基础，研究MIMO 非线性系统\n计算机控制系统\\：计算机参与控制的闭环控制系统，也称数字控制系统或离散控制系统\n非线性控制\\：由非线性微分方程（或差分方程）描述的动态系统\n最优控制\\：设计一个控制律，使得某个特定的性能指标（或称成本泛函）达到极值\n\n控制系统的分析与综合\n分析：建立数学模型的基础上分析系统的各种性能，及其与系统的结构、参数和外部作用间的关系。\n综合：设计控制器，寻求改善系统性能的各种控制规律，以保证系统的各项性能指标要求都能得到满足。（使得系统性能满足某种笼统指标要求的为常规综合，系统性能在某种意义下达到最优的为最优综合）\n\n### 参考资料\n胡寿松，姜斌，张绍杰. 自动控制原理（第八版）. 科学出版社\n刘豹，唐万生.现代控制理论（第三版）. 机械工业出版社 \nRichard C.Dorf, Robert H.Bishop. Modern Control Systems (13th)*. Pearson"
    }
  }
};
