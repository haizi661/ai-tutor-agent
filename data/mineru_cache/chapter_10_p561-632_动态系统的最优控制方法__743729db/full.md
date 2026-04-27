# 第十章 动态系统的最优控制方法

![](images/bcb2079b293d5252259b0d5e414442128b868866c59d185737a3d33305736d61.jpg)  
本章导学

20世纪 60年代初，由于空间技术的迅猛发展和计算机的广泛应用，动态系统的优化理论得到迅速发展，形成了最优控制这一重要的学科分支，并在控制工程、经济管理与决策以及人口控制等领域得到了成功的应用，取得了显著的成效。最优控制在被控对象参数已知的情况下，已经成为设计复杂系统的有效方法之一。本章将介绍动态系统最优控制的基本原理和常用方法，以及若干工程应用。

# 10-1 最优控制的一般概念

# 1. 最优控制的基本概念

最优控制是现代控制理论的核心。最优控制研究的主要问题是：根据已建立的被控对象的数学模型，选择一个容许的控制律，使得被控对象按预定要求运行，并使给定的某一性能指标达到极小值(或极大值)。从数学观点来看，最优控制研究的问题是求解一类带有约束条件的泛函极值问题，属于变分学的范畴。然而，经典变分理论只能解决控制无约束，即容许控制属于开集的一类最优控制问题，而工程实践中所遇到的多为控制有约束，即容许控制属于闭集的一类最优控制问题。为了满足工程实践的需要，20世纪 50年代中期，出现了现代变分理论，其中最常用的方法是动态规划和极小值原理。

动态规划是美国学者 R.E.贝尔曼于 1957 年创立的。贝尔曼依据最优性原理，发展了变分学中的哈密顿-雅可比方程，解决了控制有闭集约束的变分问题。极小值原理是苏联科学院院士Л．C．庞特里亚金于 1958 年创立的。庞特里亚金在力学哈密顿原理的启发下，推测并证明了极小值原理，同样解决了控制有闭集约束的变分问题。动态规划和极小值原理的提出，极大地丰富了最优控制理论的内涵。

![](images/4e1c433d9cc0f25ed75fe941da54cddffb8de99d25ed8d0c73234c12040eb904.jpg)  
庞特里亚金

# 2. 最优控制问题

最优控制是一门工程背景很强的学科分支，其研究的问题都是从具体工程实践中归纳和

提炼出来的。例如，1969年美国阿波罗11号实现了人类历史上的首次载人登月飞行，任务要求登月舱在月球表面实现软着陆，即登月舱到达月球表面时的速度为零，并在登月过程中，选择登月舱发动机推力的最优控制律，使燃料消耗最少，以便宇航员完成月球考察任务后，登月舱有足够的燃料离开月球与母船会合，从而安全返回地球。由于登月舱发动机的最大推力是有限的，因而这是一个控制有闭集约束的最小燃耗控制问题。设登月舱软着陆示意图如图10-1所示。图中， $m ( t )$ 为登月舱质量； $h ( t )$ 为高度；

![](images/91ed0ed0485b408bddd44689f8856b9aba3c4d99175542c2fb6788e38c9b04ac.jpg)  
图 10-1 登月舱软着陆示意图

$\nu ( t )$ 为登月舱垂直速度； $g$ 为月球重力加速度； $u ( t )$ 为登月舱发动机推力。设登月舱不含燃料时的质量为 $M$ ，登月舱所载燃料质量为 $F$ ，登月舱发动机工作的末端时刻为 $t _ { f }$ ，发动机最大推力为 $u _ { \mathrm { m a x } }$ 。已知登月舱登月时的初始高度为 $h _ { 0 }$ ，初始垂直速度为 $\nu _ { 0 }$ ，登月舱初始质量为 $m _ { 0 }$ ，则控制有约束的最小燃耗控制问题可归纳如下：

运动方程

$$
\dot {h} (t) = v (t), \quad \dot {v} (t) = \frac {u (t)}{m (t)} - g
$$

$$
\dot {m} (t) = - k u (t), \quad k = \text {c o n s t}
$$

边界条件

初始条件 $h ( 0 ) = h _ { \scriptscriptstyle 0 } , \quad \nu ( 0 ) = \nu _ { \scriptscriptstyle 0 } , \quad m ( 0 ) = m _ { \scriptscriptstyle 0 } = M + F$

末端条件 $h ( t _ { f } ) = 0 , \quad \nu ( t _ { f } ) = 0$

控制约束

$$
0 \leqslant u (t) \leqslant u _ {\max }
$$

性能指标

$$
J = m \left(t _ {f}\right)
$$

最优控制任务是在满足控制约束条件下，寻求发动机推力的最优变化律 $u ^ { * } ( t )$ ，使登月舱由已知初态转移到要求的末态，并使性能指标 $J = m ( t _ { f } ) = \operatorname* { m a x }$ ，从而使登月过程中燃料消耗量最小。

登月舱的燃耗最优控制表明，一个最优控制问题应包含以下四个方面内容。

# (1) 系统数学模型

在集总参数情况下，被控系统的数学模型通常以定义在 $[ t _ { 0 } , t _ { f } ]$ 上的状态方程来表示

$$
\dot {\boldsymbol {x}} (t) = f [ \boldsymbol {x} (t), \boldsymbol {u} (t), t ], \quad \boldsymbol {x} \left(t _ {0}\right) = \boldsymbol {x} _ {0} \tag {10-1}
$$

式中， $\ b { x } ( t ) \in \mathbf { R } ^ { n }$ ，为状态向量； $\pmb { u } ( t ) \in \mathbf { R } ^ { m }$ ，为控制向量，且在 $[ t _ { 0 } , t _ { f } ]$ 上分段连续； $f ( \cdot ) \in \mathbf { R } ^ { n }$ ，为连续向量函数，且对 $\mathbf { } x ( t )$ 和 $t$ 连续可微。

# (2) 边界条件与目标集

动态系统的运动过程，是系统从状态空间的一个状态到另一个状态的转移，其运动轨迹在状态空间中形成轨线 $\mathbf { } x ( t )$ 。为了确定要求的轨线 $\mathbf { } x ( t )$ ，需要确定轨线的两点边界值。因此，要求确定初态 $\boldsymbol { x } ( t _ { 0 } )$ 和末态 $ { \boldsymbol { { x } } } ( t _ { f } )$ ，这是求解状态方程(10-1)必需的边界条件。

在最优控制问题中，初始时刻 $t _ { 0 }$ 和初始状态 $\boldsymbol { x } ( t _ { 0 } )$ 通常是已知的，但是末端时刻 $t _ { f }$ 和末端状态 $ { \boldsymbol { { x } } } ( t _ { f } )$ 则视具体控制问题而异。一般来说，末端时刻 $t _ { f }$ 可以固定，也可以自由；末端状态 $ { \boldsymbol { { x } } } ( t _ { f } )$ 可以固定，也可以自由，或者部分固定、部分自由。对于 $t _ { f }$ 和 $ { \boldsymbol { { x } } } ( t _ { f } )$ 的这种要求，通常用如下目标集加以概括：

$$
\boldsymbol {\psi} \left[ \boldsymbol {x} \left(t _ {f}\right), t _ {f} \right] = \mathbf {0} \tag {10-2}
$$

式中， $\pmb { \psi } ( \cdot ) \in { \bf R } ^ { r }$ ，为连续可微向量函数， $r \leqslant n$ 。

# (3) 容许控制

在属于闭集的控制中，控制向量 $\pmb { u } ( t )$ 的取值范围称为控制域，以 $^ { \varOmega }$ 标志。由于 $\pmb { u } ( t )$ 可在 $^ { \varOmega }$ 的边界上取值，故凡属集合 $^ { \varOmega }$ 且分段连续的控制向量，称为容许控制，以$\pmb { u } ( t ) \in \varOmega$ 标志。

# (4) 性能指标

在状态空间中，可以采用不同的控制向量函数去实现使系统由已知初态到要求的末态(或目标集)的转移。性能指标则是衡量系统在不同控制向量作用下工作优良度的标准。

性能指标的内容与形式，取决于最优控制问题所要完成的任务。不同的最优控制问题，有不同的性能指标，其一般形式可以归纳为

$$
J = \varphi [ \boldsymbol {x} (t _ {f}), t _ {f} ] + \int_ {t _ {0}} ^ {t _ {f}} L [ \boldsymbol {x} (t), \boldsymbol {u} (t), t ] d t \tag {10-3}
$$

式中， $\varphi ( \cdot )$ 和 $L ( \cdot )$ 为连续可微的标量函数。 $\varphi [ { \boldsymbol { x } } ( t _ { f } ) , t _ { f } ]$ 称为末值项， $\int _ { t _ { 0 } } ^ { t _ { f } } L [ \boldsymbol { x } ( t ) , \boldsymbol { u } ( t ) , t ] \mathrm { d } t$ 称0t为过程项，两者均有具体的物理含义。

根据最优控制问题的基本组成部分，可以概括最优控制问题的一般提法：在满足系统方程(10-1)的约束条件下，在容许控制域 $\varOmega$ 中确定一个最优控制律 $\pmb { u } ^ { * } ( t )$ ，使系统状态$\mathbf { } x ( t )$ 从已知初态 $\mathbf { \delta x } _ { 0 }$ 转移到要求的目标集(10-2)，并使性能指标(10-3)达到极值。

通常，最优控制问题可用下列泛函形式表示：

$$
\min  _ {\boldsymbol {u} (t) \in \Omega} J = \varphi [ \boldsymbol {x} (t _ {f}), t _ {f} ] + \int_ {t _ {0}} ^ {t _ {f}} L [ \boldsymbol {x} (t), \boldsymbol {u} (t), t ] d t
$$

# 3. 最优控制的应用类型

最优控制在航空、航天及工业过程控制等许多领域得到了广泛应用，因而难以详尽归纳最优控制在工程实践中的应用类型。考虑到最优控制的应用类型与性能指标的形式密切相关，因而可按性能指标的数学形式进行大致的区分。性能指标按其数学形式有如下三类：

# (1) 积分型性能指标

数学描述为

$$
J = \int_ {t _ {0}} ^ {t _ {f}} L [ \boldsymbol {x} (t), \boldsymbol {u} (t), t ] \mathrm {d} t \tag {10-4}
$$

积分型性能指标表示在整个控制过程中，系统的状态及控制应该满足的要求。采用积分型性能指标的最优控制系统，又可分为以下几种应用类型：

1) 最小时间控制。

$$
J = \int_ {t _ {0}} ^ {t _ {f}} \mathrm {d} t = t _ {f} - t _ {0} \tag {10-5}
$$

最小时间控制是最优控制中常见的应用类型之一。它表示要求设计一个快速控制律，使系统在最短时间内由已知初态 $\boldsymbol { x } ( t _ { 0 } )$ 转移到要求的末态 $ { \boldsymbol { { x } } } ( t _ { f } )$ 。例如，导弹拦截器的轨道

转移即属于此类问题。

2) 最少燃耗控制。

$$
J = \int_ {t _ {0}} ^ {t _ {f}} \sum_ {j = 1} ^ {m} \left| u _ {j} (t) \right| \mathrm {d} t \tag {10-6}
$$

式中， $\sum _ { j = 1 } ^ { m } \left| u _ { j } ( t ) \right|$ 表示燃料消耗。这是航天工程中常遇到的重要问题之一。由于航天器所能携带的燃料有限，希望航天器在轨道转移时所消耗的燃料尽可能地少。图 10-1 所示的登月舱软着陆控制，即属于此类问题。

3) 最少能量控制。

$$
J = \int_ {t _ {0}} ^ {t _ {f}} \boldsymbol {u} ^ {\mathrm {T}} (t) \boldsymbol {u} (t) \mathrm {d} t \tag {10-7}
$$

对于一个能量有限的物理系统，如通信卫星上的太阳能电池，为了使系统在有限的能源条件下保证正常工作，就需要对控制过程中消耗的能量进行约束。显然，式(10-7)中的 $\pmb { u } ^ { \mathrm { T } } \pmb { u }$ 表示与消耗的功率成正比的控制能量。

# (2) 末值型性能指标

数学描述为

$$
J = \varphi \left[ \boldsymbol {x} \left(t _ {f}\right), t _ {f} \right] \tag {10-8}
$$

式中，末端时刻 $t _ { f }$ 可以固定，也可以自由。末值型性能指标表示在控制过程结束后，对系统末态 $ { \boldsymbol { { x } } } ( t _ { f } )$ 的要求，例如要求导弹的脱靶量最小等，而对控制过程中的系统状态和控制不作任何要求。

# (3) 复合型性能指标

数学描述如式(10-3)所示。复合型性能指标是最一般的性能指标形式，表示对整个控制过程和末端状态都有要求。采用复合型性能指标的最优控制系统，主要有以下两种应用类型：

1) 状态调节器。

$$
J = \frac {1}{2} \boldsymbol {x} ^ {\mathrm {T}} \left(t _ {f}\right) \boldsymbol {F} \boldsymbol {x} \left(t _ {f}\right) + \frac {1}{2} \int_ {t _ {0}} ^ {t _ {f}} \left[ \boldsymbol {x} ^ {\mathrm {T}} (t) \boldsymbol {Q} \boldsymbol {x} (t) + \boldsymbol {u} ^ {\mathrm {T}} (t) \boldsymbol {R} \boldsymbol {u} (t) \right] \mathrm {d} t \tag {10-9}
$$

式中， $F = F ^ { \mathrm { T } } \geqslant { \bf 0 } , Q = Q ^ { \mathrm { T } } \geqslant { \bf 0 } ,$ $\pmb { R } { = } \pmb { R } ^ { \mathrm { T } } > \mathbf { 0 }$ ，称为加权矩阵。为了便于设计，权阵 $F$ ， $\pmb { Q }$ 和$\pmb { R }$ 通常取为对角阵。性能指标(10-9)表示对于运行在某一平稳状态的线性控制系统，在系统受扰偏离原平衡状态时，控制律 $\pmb { u } ^ { * } ( t )$ 使系统恢复到原平衡状态附近时所要求的性能。其中， ${ \pmb x } ^ { \operatorname { T } } ( t ) Q { \pmb x } ( t )$ 表示控制过程中的状态偏差； $\pmb { u } ^ { \operatorname { T } } ( t ) \pmb { R } \pmb { u } ( t )$ 表示控制过程中消耗的控制能量， $\pmb { x } ^ { \operatorname { T } } ( t _ { f } ) \pmb { F } \pmb { x } ( t _ { f } )$ 表示控制过程结束时的末态偏差，1/2 是为便于进行二次型函数运算而加入的标量因子。采用式(10-9)作为性能指标的线性控制系统有许多种，例如导弹的横滚控制回路以及发电厂的电压调节系统，都属于状态调节器范畴。

2) 输出跟踪控制。

$$
J = \frac {1}{2} e ^ {\mathrm {T}} \left(t _ {f}\right) F e \left(t _ {f}\right) + \frac {1}{2} \int_ {t _ {0}} ^ {t _ {f}} \left[ e ^ {\mathrm {T}} (t) Q e (t) + u ^ {\mathrm {T}} (t) R u (t) \right] d t \tag {10-10}
$$

式中， $e ( t ) = z ( t ) - y ( t )$ 为跟踪误差； $z ( t )$ 为理想输出向量，与实际输出向量 $y ( t )$ 同维；加权矩阵 $F$ ， $\varrho$ 和 $\pmb { R }$ 的要求同式(10-9)。式(10-10)中各组成部分的物理意义与性能指标与式(10-9)类似。许多实际控制系统，例如飞机、导弹及航天器的指令信号跟踪、模型跟踪控制系统中的状态或输出跟踪等，均采用式(10-10)形式的性能指标。

# 4. 最优控制的研究方法

当系统数学模型、约束条件及性能指标确定后，求解最优控制问题的主要方法有以下三类：

# (1) 解析法

解析法适用于性能指标及约束条件有明显解析表达式的情况。一般先用求导方法或变分法求出最优控制的必要条件，得到一组方程式或不等式，然后求解这组方程式或不等式，得到最优控制的解析解。解析法大致又可分成两类：当控制无约束时，采用经典微分法或经典变分法；当控制有约束时，采用极小值原理或动态规划。如果系统是线性的，性能指标是二次型形式的，则可采用状态调节器理论求解。

# (2) 数值计算法

若性能指标比较复杂，或无法用变量显函数表示，则可以采用直接搜索法，经过若干次迭代，搜索到最优点。数值计算法又可分为：

1) 区间消去法，又称一维搜索法。适用于求解单变量极值问题，主要有裴波那西法、黄金分割法和多项式插值法等。

2) 爬山法，又称多维搜索法。适用于求解多变量极值问题，主要有坐标轮换法、步长加速法、方向加速法等。

# (3) 梯度型法

这是一种解析与数值计算相结合的方法，其中包括：

1) 无约束梯度法。主要有陡降法、拟牛顿法、共轭梯度法和变尺度法等。  
2) 有约束梯度法。主要有可行方向法和梯度投影法等。

在上述最优控制研究方法中，数值计算法和梯度型法可参考《最优化方法》相关书籍。本书仅介绍最优控制的解析求解方法，包括变分法、极小值原理以及线性二次型最优控制法。

# 10-2 最优控制中的变分法

当系统的数学模型由向量微分方程来描述，性能指标由泛函来表示时，确定控制无约束时的最优解问题，就成为在微分方程约束下求泛函的条件极值问题，其数学基础为经典变分理论。

# 1. 泛函与变分

泛函与变分有如下基本概念。

# (1) 泛函与泛函算子

设对于自变量 $t$ ，存在一类函数 $\{ x ( t ) \}$ 。如果对于每个函数 $x ( t )$ ，有一个 $J$ 值与之对应，则变量 $J$ 称为依赖于函数 $x ( t )$ 的泛函数，简称泛函，记为 $J [ x ( t ) ]$ 。

由上述泛函定义可见，泛函为标量，可以理解为“函数的函数”，其值由函数的选取而定。例如，函数的定积分是一个泛函。设

$$
J [ x ] = \int_ {0} ^ {1} x (t) \mathrm {d} t \tag {10-11}
$$

当 $x ( t ) { = } t$ 时，有 $J [ x ] { = } 1 / 2$ ；当 ${ \boldsymbol { x } } ( t ) { = } \mathrm { c o s } t$ 时，有 $J [ x ] = \sin { 1 }$ 。表明式(10-11)确为泛函。

在最优控制问题中，如果取如下形式的积分型性能指标：

$$
J = \int_ {t _ {0}} ^ {t _ {f}} L [ \boldsymbol {x} (t), \dot {\boldsymbol {x}} (t), t ] d t \tag {10-12}
$$

则 $J$ 的数值取决于 $n$ 维向量函数 $x ( t )$ ，故式(10-12)为泛函，常称为积分型指标泛函。

指标泛函可以看作是线性赋范空间中的某个子集到实数集的映射算子，其定义如下：设 $\mathbf { R } ^ { n }$ 为 $n$ 维线性赋范空间， $\mathbf { R }$ 为实数集，若存在一一对应关系：

$$
y = J [ \boldsymbol {x} ], \tag {10-13}
$$

$$
\forall \boldsymbol {x} \in \mathbf {R} ^ {n}, \quad y \in \mathbf {R}
$$

则称 $J [ x ]$ 为 $\mathbf { R } ^ { n }$ 到 $\mathbf { R }$ 的泛函算子，记为 $\pmb { J } [ \pmb { x } ]$ ： $\mathbf { R } ^ { n } \to \mathbf { R }$ 。

为了对泛函进行运算，常要求泛函 $J [ x ]$ 具有连续性和线性。

# (2) 连续泛函与线性泛函

如果式(10-13)满足下列线性条件：

1) $J { \big [ } x _ { 1 } + x _ { 2 } { \big ] } = J { \big [ } x _ { 1 } { \big ] } + J { \big [ } x _ { 2 } { \big ] } , \quad \forall x _ { 1 } , x _ { 2 } \in \mathbf { R } ^ { n }$   
2) $J [ \alpha { \pmb x } ] = \alpha J [ { \pmb x } ] , \quad \forall { \pmb x } \in { \bf R } ^ { n }$ (10-14)

则称 $J [ { \pmb x } ] : { \mathbf { R } } ^ { n }  { \mathbf { R } }$ 为线性泛函算子，其中 $\alpha$ 为标量。

为了讨论泛函 $\boldsymbol { \mathcal { I } } [ \boldsymbol { x } ]$ 的性质和运算， $\ J [ { \boldsymbol { x } } ]$ 需为连续的，其定义如下：设 $\boldsymbol { \mathcal { I } } \boldsymbol { x }$ ]是线性赋范空间 $\mathbf { R } ^ { n }$ 中子集 $D ( J )$ 到实数集 $\mathbf { R }$ 上的泛函算子， $D ( J )$ 为泛函 $\boldsymbol { \mathcal { I } } [ \boldsymbol { x } ]$ 的定义域。若对于收敛于点 $\boldsymbol { x } _ { 0 }$ 的点列 $ { \boldsymbol { { x } } } _ { n }$ ，其中 $\boldsymbol { x } _ { 0 }$ ， $\pmb { x } _ { n } \in D ( J )$ ，均有

$$
\lim  _ {n \rightarrow \infty} J [ \boldsymbol {x} _ {n} ] = J [ \boldsymbol {x} _ {0} ] \tag {10-15}
$$

则称泛函 $J$ 在 $\mathbf { \boldsymbol { x } } _ { 0 }$ 处连续；若 $\ J [ x ]$ 在子集 $D ( J )$ 上的每一点都连续，则称 $\boldsymbol { \mathcal { I } } [ \boldsymbol { x } ]$ 在 $D ( J )$ 中连续。

由于泛函 $\ J [ x ]$ 定义在线性赋范空间上，因此对于线性泛函 $\boldsymbol { \mathcal { I } } [ \boldsymbol { x } ]$ ，若

$$
\left\| \boldsymbol {x} _ {n} - \boldsymbol {x} \right\|\rightarrow 0 (n \rightarrow \infty), \quad \forall \boldsymbol {x} _ {n}, \boldsymbol {x} \in \mathbf {R} ^ {n}
$$

时，必有

$$
\lim  _ {n \rightarrow \infty} J [ \boldsymbol {x} _ {n} ] = J [ \boldsymbol {x} ]
$$

则线性泛函 $\boldsymbol { \mathcal { I } } \boldsymbol { x }$ ]是连续的，称 $\boldsymbol { \mathcal { I } } [ \boldsymbol { x } ]$ 为线性连续泛函。

在用变分法求解最优控制问题时，要求指标泛函 $\boldsymbol { \mathcal { I } } [ \boldsymbol { x } ]$ 为线性连续泛函，以使得 $\ J [ x ]$ 在任一点上的值均可用该点附近的泛函值任意逼近。应当指出，在有限维线性空间上，任何线性泛函都是连续的。

# (3) 泛函的变分

研究泛函的极值问题，需要采用变分法。变分在泛函研究中的作用，如同微分在函数研究中的作用一样。泛函的变分与函数的微分，其定义式几乎完全相当。

为了研究泛函的变分，应先研究宗量的变分。设 $\ J [ x ]$ 为连续泛函， $\ b { x } ( t ) \in \mathbf { R } ^ { n }$ 为宗量，则宗量变分可表示为

$$
\delta \boldsymbol {x} = \boldsymbol {x} (t) - \boldsymbol {x} _ {0} (t), \quad \forall \boldsymbol {x} (t), \boldsymbol {x} _ {0} (t) \in \mathbf {R} ^ {n} \tag {10-16}
$$

宗量变分 $\delta x$ 表示 $\mathbf { R } ^ { n }$ 中点 $x \left( t \right)$ 与 ${ \boldsymbol x } _ { 0 } \left( t \right)$ 之间的差。由于 $\delta x$ 存在，必然引起泛函数值的变化，并以 $\boldsymbol { \mathcal { I } } [ \boldsymbol { x } + \varepsilon \delta \boldsymbol { x }$ ]表示。其中， $0 \leqslant \varepsilon \leqslant 1$ 为参变数。当 $\varepsilon = 1$ 时，得增加后的泛函值 $\boldsymbol { \mathcal { I } } \boldsymbol { x }$ $+ \delta x ]$ ；当 $\varepsilon = 0$ 时，得泛函原来的值 $\boldsymbol { \mathcal { I } } [ \boldsymbol { x } ]$ 。

# 1) 泛函变分的定义。

定义 10-1 设 $\boldsymbol { \mathcal { I } } [ \boldsymbol { x } ]$ 是线性赋范空间 $\mathbf { R } ^ { n }$ 上的连续泛函，若其增量可表示为

$$
\Delta J [ \boldsymbol {x} ] = J [ \boldsymbol {x} + \delta \boldsymbol {x} ] - J [ \boldsymbol {x} ] = L [ \boldsymbol {x}, \delta \boldsymbol {x} ] + r [ \boldsymbol {x}, \delta \boldsymbol {x} ] \tag {10-17}
$$

式中， $L [ x , \delta x ]$ 是关于 $\delta x$ 的线性连续泛函， $r [ { \boldsymbol { x } } , \delta { \boldsymbol { x } } ]$ 是关于 $\delta x$ 的高阶无穷小，则

$$
\delta J = L [ x, \delta x ]
$$

称为泛函 $\boldsymbol { \mathcal { I } } ( \boldsymbol { x } \boldsymbol { ] }$ 的变分。

上述定义表明，泛函变分就是泛函增量的线性主部。当一个泛函具有变分时，亦称该泛函可微。如同函数的微分一样，泛函的变分可以利用求导的方法来确定。

# 2) 泛函变分的求法。

定理 10-1 设 $\boldsymbol { \mathcal { I } } [ \boldsymbol { x } ]$ 是线性赋范空间 $\mathbf { R } ^ { n }$ 上的连续泛函，若在 $\mathbf { \boldsymbol { x } } = \mathbf { \boldsymbol { x } } _ { 0 }$ 处 $\boldsymbol { \mathcal { I } } [ \boldsymbol { x } ]$ 可微，其中 $\boldsymbol { x }$ ， $\pmb { x } _ { 0 } \in \mathbf { R } ^ { n }$ ，则 $\boldsymbol { \mathcal { I } } [ \boldsymbol { x } ]$ 的变分为

$$
\delta J \left[ \boldsymbol {x} _ {0}, \delta \boldsymbol {x} \right] = \frac {\partial}{\partial \varepsilon} J \left[ \boldsymbol {x} _ {0} + \varepsilon \delta \boldsymbol {x} \right] \mid_ {\varepsilon = 0}, \quad 0 \leqslant \varepsilon \leqslant 1 \tag {10-18}
$$

证明 因在 $\mathbf { \delta x } _ { 0 }$ 处 $\boldsymbol { \mathcal { I } } [ \boldsymbol { x } ]$ 可微，故必在 $\mathbf { \delta x } _ { 0 }$ 处存在变分。因 $\boldsymbol { \mathcal { I } } [ \boldsymbol { x } ]$ 连续，故由式(10-17)知 $\boldsymbol { \mathcal { I } } [ \boldsymbol { x } ]$ 的增量为

$$
\Delta J = J \left[ \boldsymbol {x} _ {0} + \varepsilon \delta \boldsymbol {x} \right] - J \left[ \boldsymbol {x} _ {0} \right] = L \left[ \boldsymbol {x} _ {0}, \varepsilon \delta \boldsymbol {x} \right] + r \left[ \boldsymbol {x} _ {0}, \varepsilon \delta \boldsymbol {x} \right]
$$

由于 $L [ x _ { 0 } , \varepsilon \delta x$ ]是 $\varepsilon \delta x$ 的线性连续泛函，故

$$
L \left[ \boldsymbol {x} _ {0}, \varepsilon \delta \boldsymbol {x} \right] = \varepsilon L \left[ \boldsymbol {x} _ {0}, \delta \boldsymbol {x} \right]
$$

又因 $\mathbf { \xi } _ { r \left[ \mathbf { \mathcal { X } } _ { 0 } , \varepsilon \delta \mathbf { x } \right. }$ ]是 $\varepsilon \delta x$ 的高阶无穷小，故

$$
\lim  _ {\varepsilon \rightarrow 0} \frac {r [ \boldsymbol {x} _ {0} , \varepsilon \delta \boldsymbol {x} ]}{\varepsilon} = 0
$$

于是

$$
\begin{array}{l} \frac {\partial}{\partial \varepsilon} J [ \boldsymbol {x} _ {0} + \varepsilon \delta \boldsymbol {x} ] \mid_ {\varepsilon = 0} = \lim  _ {\varepsilon \rightarrow 0} \frac {J [ \boldsymbol {x} _ {0} + \varepsilon \delta \boldsymbol {x} ] - J [ \boldsymbol {x} _ {0} ]}{\varepsilon} \\ = \lim  _ {\varepsilon \rightarrow 0} \frac {1}{\varepsilon} \left\{L \left[ \boldsymbol {x} _ {0}, \varepsilon \delta \boldsymbol {x} \right] + r \left[ \boldsymbol {x} _ {0}, \varepsilon \delta \boldsymbol {x} \right]\right\} = \delta J \left[ \boldsymbol {x} _ {0}, \delta \boldsymbol {x} \right] \\ \end{array}
$$

3) 泛函变分的规则。

由变分定义可以看出，泛函的变分是一种线性映射，因而其运算规则类似于函数的线性运算。设 $L _ { 1 }$ 和 $L _ { 2 }$ 是函数 $\boldsymbol { x }$ ， $\dot { x }$ 和 $t$ 的函数，则有如下变分规则：

① 1 2 1 2 ( ) L L L L      ；  
$\textcircled { 2 } \delta ( L _ { 1 } L _ { 2 } ) = L _ { 1 } \delta L _ { 2 } + L _ { 2 } \delta L _ { 1 }$ ；

③ [ , , ]d [ , , ]d b b   
④ 8 d d x 。 dt d  t

例 10-1 已知连续泛函为

$$
J = \int_ {t _ {0}} ^ {t _ {f}} L [ x, \dot {x}, t ] d t
$$

式中， $x$ 和 $\dot { x }$ 为标量函数。试求泛函变分J。

解 根据定理 10-1，可得

$$
\begin{array}{l} \delta J = \frac {\partial}{\partial \varepsilon} \int_ {t _ {0}} ^ {t _ {f}} L (x + \varepsilon \delta x, \dot {x} + \varepsilon \delta \dot {x}, t) d t \left| _ {\varepsilon = 0} \right. \\ = \int_ {t _ {0}} ^ {t _ {f}} \left[ \frac {\partial L}{\partial x} \frac {\partial (x + \varepsilon \delta x)}{\partial \varepsilon} + \frac {\partial L}{\partial \dot {x}} \frac {\partial (\dot {x} + \varepsilon \delta \dot {x})}{\partial \varepsilon} \right] \Bigg | _ {\varepsilon = 0} d t \\ = \int_ {t _ {0}} ^ {t _ {f}} \left(\frac {\partial L}{\partial x} \delta x + \frac {\partial L}{\partial \dot {x}} \delta \dot {x}\right) d t \\ \end{array}
$$

(4) 泛函的极值与变分预备定理

可以证明，泛函极值与达到极值的条件与函数类同。

1) 泛函极值的定义。

定义 10-2 设 J[ $\boldsymbol { x }$ ]是线性赋范空间 $\mathbf { R } ^ { n }$ 上某个子集 $D$ 中的线性连续泛函，点 $\boldsymbol { x } _ { 0 } \in D$ ，若存在某一正数 $\sigma$ 以及集合

$$
U \left(\boldsymbol {x} _ {0}, \sigma\right) = \left\{\boldsymbol {x} \mid \left\| \boldsymbol {x} - \boldsymbol {x} _ {0} \right\| <   \sigma , \boldsymbol {x} \in \mathbf {R} ^ {n} \right\}
$$

在 $\pmb { x } \in U ( \pmb { x } _ { 0 } , \sigma ) \subset D$ 时，均有

$$
\Delta J [ \boldsymbol {x} ] = J [ \boldsymbol {x} ] - J [ \boldsymbol {x} _ {0} ] \geqslant 0 \tag {10-19}
$$

或者 $\Delta J \big [ \boldsymbol { x } \big ] = J \big [ \boldsymbol { x } \big ] - J \big [ \boldsymbol { x } _ { \mathrm { 0 } } \big ] \leqslant 0$ (10-20)

则称泛函 $\boldsymbol { \mathcal { I } } \boldsymbol { x }$ ]在 $\mathbf { \boldsymbol { x } } = \mathbf { \boldsymbol { x } } _ { 0 }$ 处达到极小值(或极大值)。

2) 泛函极值的必要条件。

定理 10-2 设 $\boldsymbol { \mathcal { I } } \boldsymbol { x }$ ]是在线性赋范空间 $\mathbf { R } ^ { n }$ 上某个开子集 $D$ 中定义的可微泛函，且在$\mathbf { \boldsymbol { x } } = \mathbf { \boldsymbol { x } } _ { 0 }$ 处达到极值，则泛函 $\ J [ x ]$ 在 $\mathbf { \boldsymbol { x } } = \mathbf { \boldsymbol { x } } _ { 0 }$ 处必有

$$
\delta J \left[ x _ {0}, \delta x \right] = 0 \tag {10-21}
$$

定理表明，泛函一次变分为零，是泛函达到极值的必要条件。

3) 变分预备定理。

为了深入研究无约束泛函极值条件和有约束泛函极值条件，以及用变分法求解控制

无约束的最优控制问题，需要应用变分预备定理。

定理 10-3 (变分预备定理) 设 $\zeta ( t )$ 是时间区间 $[ t _ { 0 } , \ t _ { 1 } ] .$ 上连续的 $n$ 维向量函数， $\pmb { \eta } ( t )$ 为任意的 $n$ 维连续向量函数，且有 $\pmb { \eta } ( t _ { 0 } ) = \pmb { \eta } ( t _ { 1 } ) = \mathbf { 0 }$ 。若满足

$$
\int_ {t _ {0}} ^ {t _ {1}} \boldsymbol {\zeta} ^ {\mathrm {T}} (t) \boldsymbol {\eta} (t) \mathrm {d} t = 0
$$

则必有 $\pmb { \zeta } ( t ) \equiv \mathbf { 0 } , \forall t \in \left[ t _ { 0 } , t _ { 1 } \right]$

# 2. 欧拉方程

欧拉方程又称欧拉-拉格朗日方程，是无约束泛函极值及有约束泛函极值的必要条件。在推导欧拉方程的过程中，应用了式(10-21)所示的泛函极值的必要条件，并且为了便于讨论，假定了 $t _ { 0 }$ 和 $t f$ 给定，且初态 $\boldsymbol { x } ( t _ { 0 } )$ 和末态 $ { \boldsymbol { { x } } } ( t _ { f } )$ 为两端固定的情况。

(1) 无约束泛函极值的必要条件

定理 10-4 设有如下泛函极值问题：

$$
\min  _ {\boldsymbol {x} (t)} J [ \boldsymbol {x} ] = \int_ {t _ {0}} ^ {t _ {f}} L (\boldsymbol {x}, \dot {\boldsymbol {x}}, t) d t
$$

式中， $L ( x , { \dot { x } } , t )$ 及 $\mathbf { } x ( t )$ 在 $[ t _ { 0 } , t _ { f } ]$ 上连续可微， $t _ { 0 }$ 及 $t _ { f }$ 给定。已知 $\pmb { x } ( t _ { 0 } ) = \pmb { x } _ { 0 }$ , $\pmb { x } ( t _ { f } ) = \pmb { x } _ { f } , \pmb { x } ( t ) \in \mathbf { R } ^ { n }$ ，则极值轨线 $\boldsymbol { x } ^ { * } ( t )$ 满足如下欧拉方程

$$
\frac {\partial L}{\partial \boldsymbol {x}} - \frac {\mathrm {d}}{\mathrm {d} t} \frac {\partial L}{\partial \dot {\boldsymbol {x}}} = \mathbf {0} \tag {10-22}
$$

及横截条件 $\left( \frac { \partial L } { \partial \dot { \pmb x } } \right) ^ { \operatorname { T } } \delta \pmb x \left( t _ { f } \right) - \left( \frac { \partial L } { \partial \dot { \pmb x } } \right) ^ { \operatorname { T } } \bigg | _ { t _ { 0 } } \delta \pmb x \left( t _ { 0 } \right) = 0$ (10-23)

证明 设 $\boldsymbol { x } ^ { * } ( t )$ 是满足边界条件 $\pmb { x } ( t _ { 0 } ) = \pmb { x } _ { 0 }$ 和 $\boldsymbol { x } ( t _ { f } ) { = } \boldsymbol { x } _ { f }$ 的极值轨线， $\mathbf { } x ( t )$ 是 $x ^ { * } ( t )$ 邻域中的一条容许轨线。 $\mathbf { } x ( t )$ 与 $x ^ { * } ( t )$ 之间有下列关系：

$$
\boldsymbol {x} (t) = \boldsymbol {x} ^ {*} (t) + \delta \boldsymbol {x} (t), \quad \dot {\boldsymbol {x}} (t) = \dot {\boldsymbol {x}} ^ {*} (t) + \delta \dot {\boldsymbol {x}} (t)
$$

以及 ${ \pmb x } ( t _ { 0 } ) = { \pmb x } ^ { * } ( t _ { 0 } ) = { \pmb x } _ { 0 } , \qquad { \pmb x } ( t _ { f } ) = { \pmb x } ^ { * } ( t _ { f } ) = { \pmb x } _ { f }$

取泛函增量

$$
\begin{array}{l} \Delta J [ \boldsymbol {x} ] = J [ \boldsymbol {x} ^ {*} + \delta \boldsymbol {x} ] - J [ \boldsymbol {x} ^ {*} ] = \int_ {t _ {0}} ^ {t _ {f}} \left[ L (\boldsymbol {x} ^ {*} + \delta \boldsymbol {x}, \dot {\boldsymbol {x}} ^ {*} + \delta \dot {\boldsymbol {x}}, t) - L (\boldsymbol {x} ^ {*}, \dot {\boldsymbol {x}}, t) \right] d t \\ = \int_ {t _ {0}} ^ {t _ {f}} \left[ \left(\frac {\partial L}{\partial \boldsymbol {x}}\right) ^ {\mathrm {T}} \delta \boldsymbol {x} + \left(\frac {\partial L}{\partial \dot {\boldsymbol {x}}}\right) ^ {\mathrm {T}} \delta \dot {\boldsymbol {x}} + \mathrm {H O T} \right] \mathrm {d} t \\ \end{array}
$$

式中，HOT 代表泰勒展开式中的高阶项(high order term)。由变分定义知，取上式主部可得

$$
\delta J = \int_ {t _ {0}} ^ {t _ {f}} \left[ \left(\frac {\partial L}{\partial \boldsymbol {x}}\right) ^ {\mathrm {T}} \delta \boldsymbol {x} + \left(\frac {\partial L}{\partial \dot {\boldsymbol {x}}}\right) ^ {\mathrm {T}} \delta \dot {\boldsymbol {x}} \right] \mathrm {d} t
$$

对上式中的第二项作分部积分，有

$$
\delta J = \int_ {t _ {0}} ^ {t _ {f}} \left(\frac {\partial L}{\partial \boldsymbol {x}} - \frac {\mathrm {d}}{\mathrm {d} t} \frac {\partial L}{\partial \dot {\boldsymbol {x}}}\right) ^ {\mathrm {T}} \delta \boldsymbol {x} \mathrm {d} t + \left(\frac {\partial L}{\partial \dot {\boldsymbol {x}}}\right) ^ {\mathrm {T}} \delta \boldsymbol {x} \Bigg | _ {t _ {0}} ^ {t _ {f}}
$$

由定理 10-2，令 $\delta J = 0$ ，再由定理 10-3，考虑到 $\delta x$ 任意，立即证得本定理的结论式(10-22)和式(10-23)。

在一般情况下，欧拉方程是一个时变二阶非线性微分方程，求解时所需的两点边界值由横截条件式(10-23)提供。由于在两端固定情况下，必有 $\delta \mathbf { x } ( t _ { 0 } ) = \mathbf { 0 }$ 和 $\delta \boldsymbol { x } ( t _ { f } ) = \mathbf { 0 }$ ，因此定理 10-4 中的横截条件退化为已知边界条件 0 0x x ( ) t  和 ( )f fx x t  。 $\pmb { x } ( t _ { 0 } ) = \pmb { x } _ { 0 }$ $x ( t _ { f } ) = x _ { f }$

应当指出，欧拉方程是泛函极值的必要条件，而不是充分必要条件。在处理实际泛函极值问题时，可从实际问题的性质出发，判断泛函极值的存在性，并直接利用欧拉方程求出极值轨线 $\boldsymbol { x } ^ { * } ( t )$ 。

例 10-2 设有泛函

$$
J [ \boldsymbol {x} ] = \int_ {0} ^ {\pi / 2} \left[ \dot {x} ^ {2} (t) - x ^ {2} (t) \right] d t
$$

已知边界条件为 $x ( 0 ) = 0 , x ( \pi / 2 ) = 2$ 。求使泛函达到极值的极值轨线 $x ^ { * } ( t )$ 。

解 本例 $L ( x , { \dot { x } } ) = { \dot { x } } ^ { 2 } - x ^ { 2 }$ ，因

$$
\frac {\partial L}{\partial x} = - 2 x, \quad \frac {\partial L}{\partial \dot {x}} = 2 \dot {x}, \quad \frac {\mathrm {d}}{\mathrm {d} t} \frac {\partial L}{\partial \dot {x}} = 2 \ddot {x}
$$

故欧拉方程为

$$
\dot {x} (t) + x (t) = 0
$$

其通解为

$$
x ^ {*} (t) = c _ {1} \cos t + c _ {2} \sin t
$$

在上式中，分别代入已知边界条件 $x ( 0 ) { = } 0$ 和 $x ( \pi / 2 ) { = } 2$ ，可求出 $c _ { 1 } { = } 0$ ， $\scriptstyle c _ { 2 } = 2$ 。于是求出

$$
x ^ {*} (t) = 2 \sin t
$$

# (2) 有等式约束泛函极值的必要条件

在求解实际系统的最优控制问题时，要求使指标泛函取极值的极值轨线同时满足系统的运动微分方程式。因此，控制系统的最优控制问题，要求确定在微分方程等式约束条件下的泛函极值，即条件极值变分问题。

在讨论条件极值的变分问题时，我们仍然先考虑最简单的两端固定情况。利用拉格朗日乘子法，可以将有等式约束的泛函条件极值问题化为无约束泛函极值问题。

定理 10-5 设有如下条件泛函极值问题：

$$
\min  _ {\boldsymbol {x} (t)} J [ \boldsymbol {x} ] = \int_ {t _ {0}} ^ {t _ {f}} g (\boldsymbol {x}, \dot {\boldsymbol {x}}, t) d t
$$

$$
\text {s . t .} \quad f (x, \dot {x}, t) = 0
$$

式中， $f ( x , { \dot { x } } , t ) = \mathbf { 0 }$ 为系统运动微分方程； $g ( x , { \dot { x } } , t )$ 及 $\mathbf { } x ( t )$ 在 $[ t _ { 0 } , t _ { f } ]$ 上连续可微；$x , { \dot { x } } , f ( \cdot ) \in \mathbf { R } ^ { n }$ ； $t _ { 0 }$ 及 $t _ { f }$ 给定。已知 $\pmb { x } ( t _ { 0 } ) = \pmb { x } _ { 0 }$ ， $x ( t _ { f } ) = x _ { f }$ ，则极值轨线 $\boldsymbol { x } ^ { * } ( t )$ 满足如下欧拉方程及相应的横截条件：

$$
\frac {\partial L}{\partial \boldsymbol {x}} - \frac {\mathrm {d}}{\mathrm {d} t} \frac {\partial L}{\partial \dot {\boldsymbol {x}}} = \boldsymbol {0}
$$

$$
\left. \left(\frac {\partial L}{\partial \dot {\boldsymbol {x}}}\right) ^ {\mathrm {T}} \right| _ {t _ {f}} \delta \boldsymbol {x} \left(t _ {f}\right) - \left. \left(\frac {\partial L}{\partial \dot {\boldsymbol {x}}}\right) ^ {\mathrm {T}} \right| _ {t _ {0}} \delta \boldsymbol {x} \left(t _ {0}\right) = 0
$$

其中， $L ( x , { \dot { x } } , \lambda , t ) = g ( x , { \dot { x } } , t ) + \lambda ^ { \operatorname { T } } ( t ) f ( x , { \dot { x } } , t )$ 为拉格朗日函数， $\ b { \lambda } ( t ) \in \mathbf { R } ^ { n }$ 为待定拉格朗日乘子。

证明 设 $\ b { \lambda } ( t ) \in \mathbf { R } ^ { n }$ 待定，构造广义泛函

$$
J _ {a} [ \boldsymbol {x} ] = \int_ {t _ {0}} ^ {t _ {f}} \left[ g (\boldsymbol {x}, \dot {\boldsymbol {x}}, t) + \boldsymbol {\lambda} ^ {\mathrm {T}} (t) \boldsymbol {f} (\boldsymbol {x}, \dot {\boldsymbol {x}}, t) \right] \mathrm {d} t = \int_ {t _ {0}} ^ {t _ {f}} L (\boldsymbol {x}, \dot {\boldsymbol {x}}, \boldsymbol {\lambda}, t) \mathrm {d} t
$$

于是，原性能泛函的条件极值问题，转化为广义泛函的无约束极值问题。根据定理 10-4，本定理得证。

与定理 10-4 情况相同，在两端固定情况下，定理 10-5 的横截条件退化为已知的两点边界条件。

例 10-3 设人造地球卫星姿态控制系统的状态方程为

$$
\dot {\boldsymbol {x}} (t) = \left[ \begin{array}{l l} 0 & 1 \\ 0 & 0 \end{array} \right] \boldsymbol {x} (t) + \left[ \begin{array}{l} 0 \\ 1 \end{array} \right] u (t)
$$

指标泛函取

$$
J = \frac {1}{2} \int_ {0} ^ {2} u ^ {2} (t) d t
$$

边界条件为

$$
\boldsymbol {x} (0) = \left[ \begin{array}{l} 1 \\ 1 \end{array} \right], \qquad \boldsymbol {x} (2) = \left[ \begin{array}{l} 0 \\ 0 \end{array} \right]
$$

试求使指标泛函取极值的极值轨线 $x ^ { * } ( t )$ 和极值控制 $\pmb { u } ^ { * } ( t )$ 。

解 本例为有等式约束泛函极值问题。由题意

$$
g = \frac {1}{2} u ^ {2}, \quad \boldsymbol {\lambda} ^ {\mathrm {T}} = \left[ \begin{array}{l l} \lambda_ {1} & \lambda_ {2} \end{array} \right], \quad \boldsymbol {f} = \left[ \begin{array}{l} f _ {1} \\ f _ {2} \end{array} \right] = \left[ \begin{array}{l} x _ {2} - \dot {x} _ {1} \\ u - \dot {x} _ {2} \end{array} \right]
$$

故拉格朗日标量函数

$$
L = g + \boldsymbol {\lambda} ^ {\mathrm {T}} \boldsymbol {f} = \frac {1}{2} u ^ {2} + \lambda_ {1} \left(x _ {2} - \dot {x} _ {1}\right) + \lambda_ {2} \left(u - \dot {x} _ {2}\right)
$$

欧拉方程

$$
\frac {\partial L}{\partial x _ {1}} - \frac {\mathrm {d}}{\mathrm {d} t} \frac {\partial L}{\partial \dot {x} _ {1}} = \dot {\lambda} _ {1} = 0, \quad \lambda_ {1} = a
$$

$$
\frac {\partial L}{\partial x _ {2}} - \frac {\mathrm {d}}{\mathrm {d} t} \frac {\partial L}{\partial \dot {x} _ {2}} = \lambda_ {1} + \dot {\lambda} _ {2} = 0, \quad \lambda_ {2} = - a t + b
$$

$$
\frac {\partial L}{\partial u} - \frac {\mathrm {d}}{\mathrm {d} t} \frac {\partial L}{\partial \dot {u}} = u + \lambda_ {2} = 0, \quad u = a t - b
$$

式中，常数 $a$ ， $^ { b }$ 待定。

由状态约束方程

$$
\dot {x} _ {2} = u = a t - b, \quad x _ {2} = \frac {1}{2} a t ^ {2} - b t + c
$$

$$
\dot {x} _ {1} = x _ {2} = \frac {1}{2} a t ^ {2} - b t + c, \quad x _ {1} = \frac {1}{6} a t ^ {3} - \frac {1}{2} b t ^ {2} + c t + d
$$

式中，常数 c， $d$ 待定。代入已知边界条件： $x _ { 1 } ( 0 ) { = } 1$ ， $x _ { 2 } ( 0 ) { = } 1$ ， $x _ { 1 } ( 2 ) { = } 0$ ， $x _ { 2 } ( 2 ) { = } 0$ ，可求得

$$
a = 3, \quad b = 3. 5, \quad c = d = 1
$$

于是极值轨线 ${ x _ { 1 } } ^ { * } ( t ) = 0 . 5 t ^ { 3 } - 1 . 7 5 t ^ { 2 } + t + 1$

$$
x _ {2} ^ {*} (t) = 1. 5 t ^ {2} - 3. 5 t ^ {2} + 1
$$

极值控制 $u ^ { * } ( t ) = 3 t - 3 . 5$

# 3. 横截条件

求解欧拉方程，需要由横截条件提供两点边界值。前面研究的两端固定，且初始时刻 $t _ { 0 }$ 和末端时刻 $t _ { f }$ 同时固定的情况，是一种最简单的情况。在实际工程问题中，初始时刻 $t _ { 0 }$ 和初始状态 $\boldsymbol { x } ( t _ { 0 } )$ 往往是固定的，但末端时刻 $t f$ 可以固定，也可以自由；末端状态$\boldsymbol { x } ( t _ { f } )$ 可以固定，可以自由，也可以受约束。下面将讨论 $t f$ 固定和 $t f$ 自由时的各种横截条件，同时指出，在不同横截条件情况下，欧拉方程的形式总是不变的。

# (1) 末端时刻固定时的横截条件

当 $t _ { f }$ 固定时，由泛函极值的必要条件可知，横截条件的一般表达式为式(10-23)。在$\boldsymbol { x } ( t _ { 0 } ) = \boldsymbol { x } _ { 0 }$ 固定情况下，因 $\delta \mathbf { x } ( t _ { 0 } ) = \mathbf { 0 }$ ，故横截条件及边界条件的一般形式应为

$$
\left. \left(\frac {\partial L}{\partial \dot {\boldsymbol {x}}}\right) ^ {\mathrm {T}} \right| _ {t _ {f}} \delta \boldsymbol {x} \left(t _ {f}\right) = 0, \quad \boldsymbol {x} \left(t _ {0}\right) = \boldsymbol {x} _ {0} \tag {10-24}
$$

显然，当末端固定 ${  { \boldsymbol { \mathbf { x } } } } ( t _ { f } ) = {  { \boldsymbol { \mathbf { x } } } } _ { f }$ 时，末端状态变分 $\delta \boldsymbol { x } ( t _ { f } ) = \mathbf { 0 }$ ，横截条件及边界条件式(10-24)退化为边界条件 $x ( t _ { f } ) = x _ { f }$ 和 $\boldsymbol { x } ( t _ { 0 } ) = \boldsymbol { x } _ { 0 }$ ；当末端状态 $ { \boldsymbol { { x } } } ( t _ { f } )$ 自由时，末端状态变分 $\delta \pmb { x } ( t _ { f } ) \neq \pmb { 0 }$ ，横截条件及边界条件式(10-24)演变为

$$
\left. \frac {\partial L}{\partial \dot {\boldsymbol {x}}} \right| _ {t = t _ {f}} = \boldsymbol {0}, \quad \boldsymbol {x} \left(t _ {0}\right) = \boldsymbol {x} _ {0} \tag {10-25}
$$

# (2) 末端时刻自由时的横截条件

$t f$ 自由且 $\boldsymbol { x } ( t _ { f } )$ 自由或受约束情况，属于变动端点情况。在变动端点问题中，可以证明：极值仅在欧拉方程的解 $\pmb { x } = \pmb { x } ( t , c _ { 1 } , c _ { 2 } )$ 上达到。其中，待定系数 $c _ { 1 }$ 和 $c _ { 2 }$ 由横截条件确定。因此，泛函极值由 $\pmb { x } ( t , c _ { 1 } , c _ { 2 } )$ 一类函数确定。

设 $t f$ 自由，起点固定 $\pmb { x } ( t _ { 0 } ) = \pmb { x } _ { 0 }$ ，末端有约束 $ { \boldsymbol { { x } } } ( t _ { f } ) =  { \boldsymbol { { c } } } ( t _ { f } )$ 的变分问题如图 10-2 所示。图中， $\boldsymbol { x } ^ { * } ( t )$ 为极值轨线； $\mathbf { } x ( t )$ 为 $x ^ { * } ( t )$ 邻域内的任一条容许轨线； $( x _ { 0 } , t _ { 0 } )$ 表示起点；点

$( x _ { f } , t _ { f } )$ 到点 $( \boldsymbol { x } _ { f } + \delta \boldsymbol { x } _ { f } , t _ { f } + \delta t _ { f } )$ 表示变动端； $\mathbf { } c ( t )$ 表示端点约束曲线，要求 $ { \boldsymbol { { x } } } ( t _ { f } ) =  { \boldsymbol { { c } } } ( t _ { f } )$ ；$\delta t _ { f }$ 为微变量，表示末端时刻的变分。例如，利用地空导弹截击按程序机构控制飞行轨迹的高空无人侦察机即属于这类问题。其中，导弹轨迹 $\mathbf { } x ( t )$ 和无人机轨迹 $c ( t )$ 都随时间而变，但要求有 $ { \boldsymbol { { x } } } ( t _ { f } ) =  { \boldsymbol { { c } } } ( t _ { f } )$ 。

![](images/aab8c8997a69b5a620e4df73d9f64203e49d53b343efd1075c25b380c685e66a.jpg)  
图 10-2 末端时刻自由时的变分问题图示

由图 10-2 可见，在末端受约束时，存在如下近似关系式：

$$
\delta \boldsymbol {x} \left(t _ {f}\right) = \delta \boldsymbol {x} _ {f} - \dot {\boldsymbol {x}} \left(t _ {f}\right) \delta t _ {f} \tag {10-26}
$$

$$
\delta \boldsymbol {x} _ {f} = \dot {\boldsymbol {c}} \left(t _ {f}\right) \delta t _ {f} \tag {10-27}
$$

如果末端 $ { \boldsymbol { { x } } } ( t _ { f } )$ 自由，由于约束曲线 $c ( t )$ 不存在，故仅存在关系式(10-26)。

设性能指标泛函为下列连续泛函：

$$
J [ \boldsymbol {x} ] = \int_ {t _ {0}} ^ {t _ {f}} L (\boldsymbol {x}, \dot {\boldsymbol {x}}, t) \mathrm {d} t \tag {10-28}
$$

容许轨线 $\mathbf { } x ( t )$ 与极值轨线 $x ^ { * } ( t )$ 之间有如下关系：

$$
\boldsymbol {x} (t) = \boldsymbol {x} ^ {*} (t) + \delta \boldsymbol {x} (t), \quad \dot {\boldsymbol {x}} (t) = \dot {\boldsymbol {x}} ^ {*} (t) + \delta \dot {\boldsymbol {x}} (t) \tag {10-29}
$$

当末端由 $( x _ { f } , t _ { f } )$ 位置移动到 $( \boldsymbol { x } _ { f } + \delta \boldsymbol { x } _ { f } , t _ { f } + \delta t _ { f } )$ 位置时，产生如下泛函增量：

$$
\begin{array}{l} \Delta J = \int_ {t _ {0}} ^ {t _ {f} + \delta t _ {f}} L \left(\boldsymbol {x} ^ {*} + \delta \boldsymbol {x}, \dot {\boldsymbol {x}} ^ {*} + \delta \dot {\boldsymbol {x}}, t\right) d t - \int_ {t _ {0}} ^ {t _ {f}} L \left(\boldsymbol {x} ^ {*}, \dot {\boldsymbol {x}} ^ {*}, t\right) d t \\ = \int_ {t _ {f}} ^ {t _ {f} + \delta t _ {f}} L \left(\boldsymbol {x} ^ {*} + \delta \boldsymbol {x}, \dot {\boldsymbol {x}} ^ {*} + \delta \dot {\boldsymbol {x}}, t\right) d t \\ + \int_ {t _ {0}} ^ {t _ {f}} \left[ L \left(\boldsymbol {x} ^ {*} + \delta \boldsymbol {x}, \dot {\boldsymbol {x}} ^ {*} + \delta \dot {\boldsymbol {x}}, t\right) - L \left(\boldsymbol {x} ^ {*}, \dot {\boldsymbol {x}} ^ {*}, t\right) \right] d t \tag {10-30} \\ \end{array}
$$

对于式(10-30)右端第一项，根据积分中值定理可得

$$
\left. \int_ {t _ {f}} ^ {t _ {f} + \delta t _ {f}} L \left(\boldsymbol {x} ^ {*} + \delta \boldsymbol {x}, \dot {\boldsymbol {x}} ^ {*} + \delta \dot {\boldsymbol {x}}, t\right) d t = L \left(\boldsymbol {x} ^ {*} + \delta \boldsymbol {x}, \dot {\boldsymbol {x}} ^ {*} + \delta \dot {\boldsymbol {x}}, t\right) \right| _ {t = t _ {f} + \theta \delta t _ {f}} \delta t _ {f}
$$

式中， $0 { < } \theta { < } 1$ 。由于函数 $L ( \cdot )$ 是连续的，因而

$$
L \left(\boldsymbol {x} ^ {*} + \delta \boldsymbol {x}, \dot {\boldsymbol {x}} ^ {*} + \delta \dot {\boldsymbol {x}}, t\right) \bigg | _ {t = t _ {f} + \theta \delta t _ {f}} = L \left(\boldsymbol {x} ^ {*}, \dot {\boldsymbol {x}} ^ {*}, t\right) \bigg | _ {t _ {f}} + \varepsilon_ {1}
$$

式中 $\varepsilon _ { \mathrm { 1 } } \to 0$ ，故有

$$
\left. \int_ {t _ {f}} ^ {t _ {f} + \delta t _ {f}} L \left(\boldsymbol {x} ^ {*} + \delta \boldsymbol {x}, \dot {\boldsymbol {x}} ^ {*} + \delta \dot {\boldsymbol {x}}, t\right) d t = L \left(\boldsymbol {x} ^ {*}, \dot {\boldsymbol {x}} ^ {*}, t\right) \right| _ {t _ {f}} \delta t _ {f} + \varepsilon_ {1} \delta t _ {f} \tag {10-31}
$$

对于式(10-30)右端第二项，将被积函数在极值轨线处展成泰勒级数，有

$$
\begin{array}{l} \int_ {t _ {0}} ^ {t _ {f}} \left[ L \left(\boldsymbol {x} ^ {*} + \delta \boldsymbol {x}, \dot {\boldsymbol {x}} ^ {*} + \delta \dot {\boldsymbol {x}}, t\right) - L \left(\boldsymbol {x} ^ {*}, \dot {\boldsymbol {x}} ^ {*}, t\right) \right] d t \\ = \int_ {t _ {0}} ^ {t _ {f}} \left[ \left(\frac {\partial L}{\partial \boldsymbol {x}}\right) ^ {\mathrm {T}} \delta \boldsymbol {x} + \left(\frac {\partial L}{\partial \dot {\boldsymbol {x}}}\right) ^ {\mathrm {T}} \delta \dot {\boldsymbol {x}} + \text {H O T} \right] \mathrm {d} t \tag {10-32} \\ \end{array}
$$

取上式右端中第二项进行分部积分，得

$$
\left. \int_ {t _ {0}} ^ {t _ {f}} \left(\frac {\partial L}{\partial \dot {\mathbf {x}}}\right) ^ {\mathrm {T}} \delta \dot {\mathbf {x}} d t = \left[ \left(\frac {\partial L}{\partial \dot {\mathbf {x}}}\right) ^ {\mathrm {T}} \delta \mathbf {x} \right] _ {t _ {0}} ^ {t _ {f}} - \int_ {t _ {0}} ^ {t _ {f}} \left(\frac {d}{d t} \frac {\partial L}{\partial \dot {\mathbf {x}}}\right) ^ {\mathrm {T}} \delta \mathbf {x} d t \right. \tag {10-33}
$$

将式(10-33)代入式(10-32)，所得结果代入式(10-30)，同时将式(10-31)也代入式(10-30)，然后对式(10-30)表示的泛函增量取线性主部，即得泛函变分

$$
\delta J = \int_ {t _ {0}} ^ {t _ {f}} \left(\frac {\partial L}{\partial \boldsymbol {x}} - \frac {\mathrm {d}}{\mathrm {d} t} \frac {\partial L}{\partial \dot {\boldsymbol {x}}}\right) ^ {\mathrm {T}} \delta \boldsymbol {x} \mathrm {d} t + \left(\frac {\partial L}{\partial \dot {\boldsymbol {x}}}\right) ^ {\mathrm {T}} \delta \boldsymbol {x} \left| _ {t _ {0}} ^ {t _ {f}} + L \left(\boldsymbol {x} ^ {*}, \dot {\boldsymbol {x}} ^ {*}, t\right) \right| _ {t _ {f}} \delta t _ {f} \tag {10-34}
$$

令式(10-34)表示的 $\delta J = 0$ ，同时考虑到 $\delta \boldsymbol { x } ( t _ { 0 } ) = \mathbf { 0 }$ ，立即得到 $t _ { f }$ 自由、末端变动时泛函极值的必要条件：

欧拉方程

$$
\frac {\partial L}{\partial \boldsymbol {x}} - \frac {\mathrm {d}}{\mathrm {d} t} \frac {\partial L}{\partial \dot {\boldsymbol {x}}} = \mathbf {0} \tag {10-35}
$$

横截条件及边界条件

$$
\left. \left(\frac {\partial L}{\partial \dot {\boldsymbol {x}}}\right) ^ {\mathrm {T}} \right| _ {t _ {f}} \delta \boldsymbol {x} \left(t _ {f}\right) + L \left(\boldsymbol {x} ^ {*}, \dot {\boldsymbol {x}} ^ {*}, t\right) \bigg | _ {t _ {f}} \delta t _ {f} = 0, \quad \boldsymbol {x} \left(t _ {0}\right) = \boldsymbol {x} _ {0} \tag {10-36}
$$

由式(10-35)、式(10-36)的推导过程和推导结果，可见：

1) $t _ { f }$ 自由、末端变动时的欧拉方程(10-35)的形式，与 $t _ { f }$ 固定、末端固定时的欧拉方程(10-22)完全相同，这一结论同样适用于有等式约束的泛函极值问题。  
2) $t _ { f }$ 自由、末端变动时的横截条件及边界条件通式(10-36)，包含了 $t _ { f }$ 固定、末端固定时的横截条件及边界条件通式(10-24)，因为在 $t _ { f }$ 固定的情况下必有 $\delta t _ { f } = 0$ 。

(3) 末端时刻自由、末端状态变动时的横截条件

1) 末端自由时的横截条件。当末端 $ { \boldsymbol { { x } } } ( t _ { f } )$ 自由时，关系式(10-26)成立，将式(10-26)代入式(10-36)，整理得

$$
\begin{array}{l} \left. \left(\frac {\partial L}{\partial \dot {\boldsymbol {x}}}\right) ^ {\mathrm {T}} \right| _ {t _ {f}} \delta \boldsymbol {x} _ {f} + \left[ L \left(\boldsymbol {x} ^ {*}, \dot {\boldsymbol {x}} ^ {*}, t\right) - \dot {\boldsymbol {x}} ^ {\mathrm {T}} (t) \frac {\partial L}{\partial \dot {\boldsymbol {x}}} \right] | _ {t _ {f}} \delta t _ {f} = 0 \tag {10-37} \\ \boldsymbol {x} \left(t _ {0}\right) = \boldsymbol {x} _ {0} \\ \end{array}
$$

因为 $\delta \pmb { x } _ { f }$ 和 $\delta t _ { f }$ 均任意，故 $t _ { f }$ 自由、 $ { \boldsymbol { { x } } } ( t _ { f } )$ 自由时的横截条件和边界条件为

$$
\boldsymbol {x} (t _ {0}) = \boldsymbol {x} _ {0}
$$

$$
\left. \left(\frac {\partial L}{\partial \dot {\boldsymbol {x}}}\right) ^ {\mathrm {T}} \right| _ {t _ {f}} = \mathbf {0} \tag {10-38}
$$

$$
\left. \left[ L \left(\boldsymbol {x} ^ {*}, \dot {\boldsymbol {x}} ^ {*}, t\right) - \boldsymbol {x} ^ {\mathrm {T}} (t) \frac {\partial L}{\partial \dot {\boldsymbol {x}}} \right] \right| _ {t _ {f}} = 0
$$

2) 末端受约束时的横截条件。设末端约束方程为

$$
\boldsymbol {x} \left(t _ {f}\right) = \boldsymbol {c} \left(t _ {f}\right)
$$

此时， $\delta \pmb { x } _ { f }$ 不能任意。将式(10-27)代入式(10-37)，整理得

$$
\boldsymbol {x} (t _ {0}) = \boldsymbol {x} _ {0}
$$

$$
\left. \left[ L \left(\boldsymbol {x} ^ {*}, \dot {\boldsymbol {x}} ^ {*}, t\right) + (\dot {c} - \dot {x}) ^ {\mathrm {T}} \frac {\partial L}{\partial \dot {\boldsymbol {x}}} \right] \right| _ {t _ {f}} \delta t _ {f} = 0
$$

因为 $\delta t _ { f }$ 任意，故 $t _ { f }$ 自由、 $ { \boldsymbol { { x } } } ( t _ { f } )$ 受约束时的横截条件和边界条件为

$$
\boldsymbol {x} (t _ {0}) = \boldsymbol {x} _ {0}
$$

$$
\boldsymbol {x} \left(t _ {f}\right) = \boldsymbol {c} \left(t _ {f}\right) \tag {10-39}
$$

$$
\left. \left[ L \left(\boldsymbol {x} ^ {*}, \dot {\boldsymbol {x}} ^ {*}, t\right) + (\dot {c} - \dot {x}) ^ {\mathrm {T}} \frac {\partial L}{\partial \dot {\boldsymbol {x}}} \right] \right| _ {t _ {f}} = 0
$$

在初始时刻 $t _ { 0 }$ 及初始状态 $\pmb { x } ( t _ { 0 } ) = \pmb { x } _ { 0 }$ 固定的情况下，不同末端时刻和不同末端边界所对应的横截条件与边界条件，如表10-1所示。

表 10-1 不同边界情况下的横截条件  

<table><tr><td colspan="2">J[x] = ∫t0xfL(x, x,t)dt</td><td>横截条件与边界条件</td></tr><tr><td rowspan="2">tf固定(x(t0)固定)</td><td>x(tf)固定</td><td>x(t0) = x0, x(tf) = xf</td></tr><tr><td>x(tf)自由</td><td>x(tf) = x0, ∅L/∂x|tf=0</td></tr><tr><td rowspan="2">tf自由(x(t0)固定)</td><td>x(tf)自由</td><td>x(tf) = x0, ∅L/∂x|tf=0
[L - xT ∂L/∂x]tf=0</td></tr><tr><td>x(tf)约束</td><td>x(tf)0 = x0, x(tf) = c(tf)
[L + (c - xT)T ∂L/∂x]tf=0</td></tr></table>

例 10-4 设性能指标泛函

$$
J = \int_ {0} ^ {t _ {f}} \left(1 + \dot {x} ^ {2}\right) ^ {1 / 2} d t
$$

式中，末端时刻 $t _ { f }$ 未给定。已知 $x ( 0 ) = 1$ ，要求

$$
x \left(t _ {f}\right) = c \left(t _ {f}\right) = 2 - t _ {f}
$$

求使泛函为极值的最优轨线 $x ^ { * } ( t )$ 及相应的 $t _ { f } ^ { ^ { \ast } }$ 和 $J ^ { * }$ 。

解 本例为起点固定、 $t _ { f }$ 自由、末端受约束的泛函极值问题。显然，所给出的指标泛函就是 $x ( t )$ 的弧长，约束方程 $c ( t ) = 2 - t$ 为平面上的直线，如图 10-3 所示。本例问题的实质是求从 $x ( 0 )$ 到直线 $c ( t )$ 并使弧长最短的曲线 $x ^ { * } ( t )$ 。图中， $x ( t )$ 为一条任意的容许

轨线。

由题意

$$
L (x, \dot {x}, t) = (1 + \dot {x} ^ {2}) ^ {1 / 2}
$$

其偏导数为

$$
\frac {\partial L}{\partial x} = 0, \quad \frac {\partial L}{\partial \dot {x}} = \frac {\dot {x}}{\left(1 + \dot {x} ^ {2}\right) ^ {1 / 2}}
$$

![](images/de5ac28239e2426eddd6801b868cdafa6c3ed22b235e60bed698c1b2b231d3be.jpg)  
图 10-3 例 10-4 的最优轨线

根据欧拉方程

$$
\frac {\partial L}{\partial x} - \frac {\mathrm {d}}{\mathrm {d} t} \frac {\partial L}{\partial \dot {x}} = - \frac {\mathrm {d}}{\mathrm {d} t} \left[ \frac {\dot {x}}{\sqrt {1 + \dot {x} ^ {2}}} \right] = 0
$$

求得 ${ \frac { \dot { x } } { \sqrt { 1 + \dot { x } ^ { 2 } } } } = c , { \dot { x } } ^ { 2 } = { \frac { c ^ { 2 } } { 1 - c ^ { 2 } } } = a ^ { 2 }$ 2, c x  2 1 c 2c 2 a

式中， $c$ 为积分常数， $a$ 为待定常数。因而

$$
\dot {x} (t) = a, \quad x (t) = a t + b
$$

其中 $^ { b }$ 也是待定常数。

由 $x ( 0 ) = 1$ ，求出 $b { = } 1$ ；由横截条件

$$
\left. \left[ L + (\dot {c} - \dot {x}) ^ {\mathrm {T}} \frac {\partial L}{\partial \dot {x}} \right] \right| _ {t _ {f}} = \left. \left[ \sqrt {1 + \dot {x} ^ {2}} + (- 1 - \dot {x}) \frac {\dot {x}}{\sqrt {1 + \dot {x} ^ {2}}} \right] \right| _ {t _ {f}} = 0
$$

解得 $\dot { { \boldsymbol x } } ( t _ { f } ) = 1$ 。因为 $\dot { { \boldsymbol x } } ( t ) = { \boldsymbol a }$ ，所以有 $a { = } 1$ 。从而最优轨线为

$$
x ^ {*} (t) = t + 1
$$

当 $t = t _ { f }$ 时， $x ( t _ { f } ) = c ( t _ { f } )$ ，即

$$
t _ {f} + 1 = 2 - t _ {f}
$$

求出最优末端时刻 ${ t _ { f } } ^ { * } { = } 0 . 5$ 。将 $x ^ { * } ( t )$ 及 ${ t _ { f } } ^ { * }$ 代入指标泛函，可得最优性能指标 $J ^ { * } = 0 . 7 0 7$ 。

# 4. 变分法解最优控制问题

在控制向量不受约束，且是时间的连续函数情况下，可用变分法导出最优控制解的必要条件。在变分法问题中，以复合型指标泛函、末端受约束的情况最有代表性。

设系统状态方程为

$$
\dot {\boldsymbol {x}} (t) = \boldsymbol {f} (\boldsymbol {x}, \boldsymbol {u}, t), \quad \boldsymbol {x} \left(t _ {0}\right) = \boldsymbol {x} _ {0} \tag {10-40}
$$

性能指标泛函为

$$
J = \varphi \left[ \boldsymbol {x} \left(t _ {f}\right), t _ {f} \right] + \int_ {t _ {0}} ^ {t _ {f}} L (\boldsymbol {x}, \boldsymbol {u}, t) d t \tag {10-41}
$$

式中， $\pmb { x } \in \mathbf { R } ^ { n } ; \pmb { u } \in \mathbf { R } ^ { m }$ ，无约束，且在 $[ t _ { 0 } , t _ { f } ]$ 上连续；在 $[ t _ { 0 } , t _ { f } ]$ 上，向量函数 $f ( \cdot )$ 、标量函数 $\varphi ( \cdot )$ 和 $L ( \cdot )$ 连续且可微；末端时刻 $t _ { f }$ 可以固定，也可以自由；末端状态 $\boldsymbol { x } ( t _ { f } )$ 受约束，其要求的目标集为

$$
\boldsymbol {\psi} \left[ \boldsymbol {x} \left(t _ {f}\right), t _ {f} \right] = \mathbf {0} \tag {10-42}
$$

其中 $\pmb { \psi } \in \mathbf { R } ^ { r }$ ， $r \leqslant n$ 。最优控制问题是：确定最优控制 $u ^ { * } ( t )$ 和最优轨线 $\boldsymbol { x } ^ { * } ( t )$ ，使系统(10-40)由已知初态 $\boldsymbol { x } _ { 0 }$ 转移到要求的目标集(10-42)，并使给定的指标泛函(10-41)达到极值。

显然，上述问题是一个有等式约束的泛函极值问题，可以采用拉格朗日乘子法，把有约束泛函极值问题化为无约束泛函极值问题。构造哈密顿函数

$$
H (\boldsymbol {x}, \boldsymbol {u}, \boldsymbol {\lambda}, t) = L (\boldsymbol {x}, \boldsymbol {u}, t) + \boldsymbol {\lambda} ^ {\mathrm {T}} (t) \boldsymbol {f} (\boldsymbol {x}, \boldsymbol {u}, t) \tag {10-43}
$$

式中， $\boldsymbol { \lambda } \in \mathbf { R } ^ { n }$ 为拉格朗日乘子向量。则最优解的必要条件可以分别讨论如下。

# (1) 末端时刻固定时的最优解

当 $t _ { f }$ 固定时，引入拉格朗日乘子向量 $\ b { \lambda } ( t ) \in \mathbf { R } ^ { n }$ ， $\gamma \in \mathbf { R } ^ { r }$ ，构造如下广义泛函：

$$
\begin{array}{l} J _ {a} = \varphi [ \boldsymbol {x} (t _ {f}) ] + \boldsymbol {\gamma} ^ {\mathrm {T}} \boldsymbol {\psi} [ \boldsymbol {x} (t _ {f}) ] + \int_ {t _ {0}} ^ {t _ {f}} \left\{L (\boldsymbol {x}, \boldsymbol {u}, t) + \boldsymbol {\lambda} ^ {\mathrm {T}} (t) [ \boldsymbol {f} (\boldsymbol {x}, \boldsymbol {u}, t) - \dot {\boldsymbol {x}} (t) ] \right\} d t \\ = \varphi \left[ \boldsymbol {x} \left(t _ {f}\right) \right] + \boldsymbol {\gamma} ^ {\mathrm {T}} \boldsymbol {\psi} \left[ \boldsymbol {x} \left(t _ {f}\right) \right] + \int_ {t _ {0}} ^ {t _ {f}} \left[ H (\boldsymbol {x}, \boldsymbol {u}, \boldsymbol {\lambda}, t) - \boldsymbol {\lambda} ^ {\mathrm {T}} (t) \dot {\boldsymbol {x}} (t) \right] \mathrm {d} t \\ \end{array}
$$

由于分部积分

$$
- \int_ {t _ {0}} ^ {t _ {f}} \boldsymbol {\lambda} ^ {\mathrm {T}} (t) \dot {\boldsymbol {x}} (t) \mathrm {d} t = - \left. \boldsymbol {\lambda} ^ {\mathrm {T}} (t) \boldsymbol {x} (t) \right| _ {t _ {0}} ^ {t _ {f}} + \int_ {t _ {0}} ^ {t _ {f}} \dot {\boldsymbol {\lambda}} ^ {\mathrm {T}} (t) \boldsymbol {x} (t) \mathrm {d} t
$$

故广义泛函可表示为

$$
\begin{array}{l} J _ {a} = \varphi [ \boldsymbol {x} (t _ {f}) ] + \boldsymbol {\gamma} ^ {\mathrm {T}} \boldsymbol {\psi} [ \boldsymbol {x} (t _ {f}) ] - \boldsymbol {\lambda} ^ {\mathrm {T}} (t _ {f}) \boldsymbol {x} (t _ {f}) + \boldsymbol {\lambda} ^ {\mathrm {T}} (t _ {0}) \boldsymbol {x} (t _ {0}) \\ + \int_ {t _ {0}} ^ {t _ {f}} \left[ H (\boldsymbol {x}, \boldsymbol {u}, \boldsymbol {\lambda}, t) + \dot {\boldsymbol {\lambda}} ^ {\top} (t) \boldsymbol {x} (t) \right] d t \tag {10-44} \\ \end{array}
$$

对广义泛函式(10-44)取一次变分，注意到待定乘子向量 $\lambda ( t )$ 和 $\gamma$ 不变分，以及$\delta \boldsymbol { x } ( t _ { 0 } ) = \mathbf { 0 }$ ，可得

$$
\delta J _ {a} = \delta \mathbf {x} ^ {\mathrm {T}} \left(t _ {f}\right) \left[ \frac {\partial \varphi}{\partial \mathbf {x} \left(t _ {f}\right)} + \frac {\partial \boldsymbol {\psi} ^ {\mathrm {T}}}{\partial \mathbf {x} \left(t _ {f}\right)} \boldsymbol {\gamma} - \boldsymbol {\lambda} \left(t _ {f}\right) \right] + \int_ {t _ {0}} ^ {t _ {f}} \left[ \left(\frac {\partial \boldsymbol {H}}{\partial \boldsymbol {x}} + \dot {\boldsymbol {\lambda}}\right) ^ {\mathrm {T}} \delta \boldsymbol {x} + \left(\frac {\partial \boldsymbol {H}}{\partial \boldsymbol {u}}\right) ^ {\mathrm {T}} \delta \boldsymbol {u} \right] d t \tag {10-45}
$$

根据泛函极值的必要条件，令式(10-45)为零，考虑到宗量变分 $\delta x$ ， $\delta \pmb { u }$ 和 $\delta x ( t _ { f } )$ 的任意性及变分预备定理，得如下广义泛函取极值的必要条件：

欧拉方程

$$
\dot {\lambda} (t) = - \frac {\partial H}{\partial x} \tag {10-46}
$$

$$
\frac {\partial H}{\partial \boldsymbol {u}} = \mathbf {0} \tag {10-47}
$$

横截条件 $\pmb { \lambda } ( t _ { f } ) = \frac { \hat { \partial } \varphi } { \hat { \partial } \pmb { x } ( t _ { f } ) } + \frac { \hat { \partial } \pmb { \psi } ^ { \mathrm { T } } } { \hat { \partial } \pmb { x } ( t _ { f } ) } \pmb { \gamma }$ ( ) ( )ft t   x (10-48)

由于引进哈密顿函数形式(10-43)，使得

$$
\dot {\boldsymbol {x}} (t) = \frac {\partial H}{\partial \boldsymbol {\lambda}} = \boldsymbol {f} (\boldsymbol {x}, \boldsymbol {u}, t) \tag {10-49}
$$

上式与式(10-46)形成正则形式，其右端都是哈密顿函数的适当偏导数，故将式(10-49)和式(10-46)称为正则方程。因为式(10-49)是众知的状态方程，故称式(10-46)为协态方程，相应的乘子向量 $\lambda ( t )$ 称为协态向量。

正则方程(10-49)和(10-46)是 $2 n$ 个一阶微分方程组，初始条件 $\pmb { x } ( t _ { 0 } ) = \pmb { x } _ { 0 }$ 和横截条件(10-48)正好为正则方程提供 $2 n$ 个边界条件，根据对 $f ( \cdot )$ ， $L ( \cdot )$ 和 $\varphi ( \cdot )$ 的连续性和可微性假设，正则方程可以唯一确定状态向量 $\mathbf { } x ( t )$ 和协态向量 $\lambda ( t )$ 。

对于确定的 $\mathbf { } x ( t )$ 和 $\lambda ( t )$ ，哈密顿函数 $H ( \cdot )$ 是控制向量 $\pmb { u } ( t )$ 的函数。式(10-47)表明，最优控制 $\pmb { u } ^ { * } ( t )$ 使哈密顿函数 $H ( \cdot )$ 取驻值，因此式(10-47)通常称为极值条件或控制方程。由极值条件(10-47)，可以确定最优控制 $\pmb { u } ^ { * } ( t )$ 与最优轨线 $x ^ { * } ( t )$ 和协态向量 $\lambda ^ { * } ( t )$ 之间的关系。

应当指出，正则方程(10-49)、(10-46)与极值条件(10-47)，形成变量间相互耦合的方程组，其边界条件由初始条件、横截条件(10-48)和目标集(10-42)提供，其中目标集条件(10-42)用于联合确定待定的拉格朗日乘子向量 。

上述讨论，可以归纳为如下定理。(为便于书写，今后凡不致混淆之处，均省略“*”号)。

定理 10-6 对于如下最优控制问题：

$$
\min  _ {\boldsymbol {u} (t)} J = \varphi [ \boldsymbol {x} (t) ] + \int_ {t _ {0}} ^ {t _ {f}} L (\boldsymbol {x}, \boldsymbol {u}, t) d t
$$

s.t.

式中， $\pmb { x } \in \mathbf { R } ^ { n } ; \pmb { u } \in \mathbf { R } ^ { m }$ ，无约束且在 $[ t _ { 0 } , t _ { f } ]$ 上连续； $\psi \in \mathbf { R } ^ { r }$ ， $r \leqslant n$ ；在 $[ t _ { 0 } , t _ { f } ]$ 上， $f ( \cdot )$ ，$\psi ( \cdot )$ $\varphi ( \cdot )$ 和 $L ( \cdot )$ 连续且可微； $t _ { f }$ 固定。最优解的必要条件为

$1 ) x ( t )$ 和 $\lambda ( t )$ 满足正则方程

$$
\dot {\boldsymbol {x}} (t) = \frac {\partial H}{\partial \boldsymbol {\lambda}}, \quad \dot {\boldsymbol {\lambda}} (t) = - \frac {\partial H}{\partial \boldsymbol {x}}
$$

式中 $H ( \pmb { x } , \pmb { u } , \lambda , t ) = L ( \pmb { x } , \pmb { u } , t ) + \lambda ^ { \operatorname { T } } ( t ) \pmb { f } ( \pmb { x } , \pmb { u } , t )$

2) 边界条件与横截条件

$$
\boldsymbol {x} \left(t _ {0}\right) = \boldsymbol {x} _ {0}, \quad \psi \left[ \boldsymbol {x} \left(t _ {f}\right) \right] = \mathbf {0}
$$

$$
\boldsymbol {\lambda} \left(t _ {f}\right) = \frac {\partial \varphi}{\partial \boldsymbol {x} \left(t _ {f}\right)} + \frac {\partial \boldsymbol {\psi} ^ {\mathrm {T}}}{\partial \boldsymbol {x} \left(t _ {f}\right)} \boldsymbol {\gamma}
$$

# 3) 极值条件

$$
\frac {\partial H}{\partial \boldsymbol {u}} = \mathbf {0}
$$

定理 10-6 是 $t _ { f }$ 固定、末端 $\boldsymbol { x } ( t _ { f } )$ 受约束时泛函极值的必要条件，通过适当修改，其结论可以移植到末端自由和末端固定时的情况。

当末端时刻 $t _ { f }$ 固定、末端 $ { \boldsymbol { { x } } } ( t _ { f } )$ 自由时，由于不存在目标集条件(10-42)，因此在定理 10-6 的结论中，删除向量 $\psi [ { \boldsymbol { x } } ( t _ { f } ) ]$ ，即为 $t _ { f }$ 固定、 $ { \boldsymbol { { x } } } ( t _ { f } )$ 自由时泛函极值的必要条件。这一结论，通过定理 10-6 的推导过程明显可见。

当末端时刻 $t _ { f }$ 固定、末端 $ { \boldsymbol { { x } } } ( t _ { f } ) =  { \boldsymbol { { x } } } _ { f }$ 固定时，由于 $\delta \boldsymbol { x } ( t _ { 0 } ) = \mathbf { 0 }$ 以及 $\delta \boldsymbol { x } ( t _ { f } ) = \mathbf { 0 }$ ，广义泛函 $J _ { a }$ 的一次变分(10-45)变成

$$
\delta J _ {a} = \int_ {t _ {0}} ^ {t _ {f}} \left[ \left(\frac {\partial H}{\partial \boldsymbol {x}} + \dot {\boldsymbol {\lambda}}\right) ^ {\mathrm {T}} \delta \boldsymbol {x} + \left(\frac {\partial H}{\partial \boldsymbol {u}}\right) ^ {\mathrm {T}} \delta \boldsymbol {u} \right] \mathrm {d} t \tag {10-50}
$$

式中， $\delta x$ 是任意的，但容许控制变分 $\delta \pmb { u }$ 不再是完全任意的，必须满足某些限制条件。卡尔曼曾经论证：若系统完全可控，同样可以导出 ${ \hat { \partial } } H / { \hat { \partial } } \pmb { u } = \mathbf { 0 }$ 的极值条件。因此，在系统可控条件下，令式(10-50)为零，由变分预备定理得

$$
\dot {\boldsymbol {\lambda}} (t) = - \frac {\partial H}{\partial \boldsymbol {x}}, \quad \frac {\partial H}{\partial \boldsymbol {u}} = \mathbf {0}
$$

应当特别注意的是，因为 $\delta \boldsymbol { x } ( t _ { f } ) = \mathbf { 0 }$ ，所以横截条件式(10-48)不成立，也不可能是$\pmb { \lambda } ( t _ { f } ) = \hat { \sigma } \varphi / \hat { \sigma } \pmb { x } ( t _ { f } )$ ；当 $\varphi ( \cdot ) = 0$ 时， $\lambda ( t _ { f } ) = \mathbf { 0 }$ 也不能成立。此时，已知的 $\boldsymbol { x } ( t _ { 0 } ) = \boldsymbol { x } _ { 0 }$ 和$x ( t _ { f } ) = x _ { f }$ ，就是求解正则方程的两端边界条件。

例 10-5 设系统方程为

$$
\dot {x} _ {1} (t) = x _ {2} (t)
$$

$$
\dot {x} _ {2} (t) = u (t)
$$

求从已知初态 $x _ { 0 } ( 0 ) = 0$ 和 $x _ { 2 } ( 0 ) = 0$ ，在 $t _ { f } = 1$ 时转移到目标集(末端约束)

$$
x _ {1} (1) + x _ {2} (1) = 1
$$

且使性能指标

$$
J = \frac {1}{2} \int_ {0} ^ {1} u ^ {2} (t) \mathrm {d} t
$$

为最小的最优控制 $u ^ { * } ( t )$ 和相应的最优轨线 $\boldsymbol { x } ^ { * } ( t )$ 。

解 本例控制无约束，可用变分法求解，属积分型性能指标、 $t _ { f }$ 固定、末端受约束的泛函极值问题。由题意：

$$
\varphi \left[ \boldsymbol {x} \left(t _ {f}\right) \right] = 0, \quad L (\cdot) = \frac {1}{2} u ^ {2}
$$

$$
\psi \left[ \boldsymbol {x} \left(t _ {f}\right) \right] = x _ {1} (1) + x _ {2} (1) - 1
$$

构造哈密顿函数

$$
H = \frac {1}{2} u ^ {2} + \lambda_ {1} x _ {2} + \lambda_ {2} u
$$

由协态方程

$$
\dot {\lambda} _ {1} = - \frac {\partial H}{\partial x _ {1}} = 0, \quad \lambda_ {1} (t) = c _ {1}
$$

$$
\dot {\lambda} _ {2} = - \frac {\partial H}{\partial x _ {2}} = - \lambda_ {1}, \quad \quad \lambda_ {2} (t) = - c _ {1} t + c _ {2}
$$

由极值条件

$$
\frac {\partial H}{\partial u} = u + \lambda_ {2} = 0, \quad u (t) = - \lambda_ {2} (t) = c _ {1} t - c _ {2}
$$

由状态方程

$$
\dot {x} _ {2} = u = c _ {1} t - c _ {2}, \quad x _ {2} (t) = \frac {1}{2} c _ {1} t ^ {2} - c _ {2} t + c _ {3}
$$

$$
\dot {x} _ {1} = x _ {2} = \frac {1}{2} c _ {1} t ^ {2} - c _ {2} t + c _ {3}, \quad x _ {1} (t) = \frac {1}{6} c _ {1} t ^ {3} - \frac {1}{2} c _ {2} t ^ {2} + c _ {3} t + c _ {4}
$$

根据已知初态 $x _ { 1 } ( 0 ) = x _ { 2 } ( 0 ) = 0$ ，求出

$$
c _ {3} = c _ {4} = 0
$$

再由目标集条件 $x _ { 1 } ( 1 ) + x _ { 2 } ( 1 ) - 1 = 0$ ，求得

$$
4 c _ {1} - 9 c _ {2} = 6
$$

根据横截条件

$$
\lambda_ {1} (1) = \frac {\partial \psi}{\partial x _ {1} (1)} \gamma = \gamma , \quad \lambda_ {2} (1) = \frac {\partial \psi}{\partial x _ {2} (1)} \gamma = \gamma
$$

得到 $\lambda _ { 1 } ( 1 ) = \lambda _ { 2 } ( 1 )$ ，故有 $c _ { _ 1 } = \frac { 1 } { 2 } c _ { _ 2 }$ 。于是解出

$$
c _ {1} = - \frac {3}{7}, \quad c _ {2} = - \frac {6}{7}
$$

从而，本例最优解为

$$
u ^ {*} (t) = - \frac {3}{7} (t - 2)
$$

$$
x _ {1} ^ {*} (t) = - \frac {1}{1 4} t ^ {2} (t - 6)
$$

$$
x _ {2} ^ {*} (t) = - \frac {3}{1 4} t (t - 4)
$$

(2) 末端时刻自由时的最优解

当 $t _ { f }$ 自由时，末端状态又可区分为受约束、自由和固定等三种情况。其中，以复合型性能指标、末端受约束的泛函极值问题最具一般性，所得到的结果可以方便地推广到末端自由和末端固定情况。末端时刻自由时所讨论的问题，除 $t _ { f }$ 自由外，其余与末端时刻固定时所讨论的内容相同。

定理 10-7 对于如下最优控制问题：

$$
\min  _ {\boldsymbol {u} (t)} J = \varphi \left[ \boldsymbol {x} \left(t _ {f}\right), t _ {f} \right] + \int_ {t _ {0}} ^ {t _ {f}} L (\boldsymbol {x}, \boldsymbol {u}, t) d t
$$

s.t. $\textcircled { 1 } \dot { \mathbf { x } } ( t ) = \pmb { f } ( \pmb { x } , \pmb { u } , t ) , \mathbf { x } ( t _ { 0 } ) = \pmb { x } _ { 0 }$

$$
② \psi [ x (t _ {f}), t _ {f} ] = 0
$$

式中， $t _ { f }$ 自由，其余假设同定理 10-6，则最优解的必要条件为

1) $\mathbf { } x ( t )$ 和 $\lambda ( t )$ 满足正则方程

$$
\dot {\boldsymbol {x}} (t) = \frac {\partial H}{\partial \boldsymbol {\lambda}}, \quad \dot {\boldsymbol {\lambda}} (t) = - \frac {\partial H}{\partial \boldsymbol {x}}
$$

其中 $H ( \pmb { x } , \pmb { u } , \lambda , t ) = L ( \pmb { x } , \pmb { u } , t ) + \pmb { \lambda } ^ { \mathrm { T } } ( t ) \pmb { f } ( \pmb { x } , \pmb { u } , t )$

2) 边界条件与横截条件

$$
\boldsymbol {x} \left(t _ {0}\right) = \boldsymbol {x} _ {0}, \quad \boldsymbol {\psi} \left[ \boldsymbol {x} \left(t _ {f}\right), t _ {f} \right] = \mathbf {0}
$$

$$
\boldsymbol {\lambda} \left(t _ {f}\right) = \frac {\partial \varphi}{\partial \boldsymbol {x} \left(t _ {f}\right)} + \frac {\partial \boldsymbol {\psi} ^ {\mathrm {T}}}{\partial \boldsymbol {x} \left(t _ {f}\right)} \boldsymbol {\gamma}
$$

3) 极值条件

$$
\frac {\partial H}{\partial \boldsymbol {u}} = \mathbf {0}
$$

4) 在最优轨线末端哈密顿函数变化律

$$
H \left(t _ {f}\right) = - \frac {\partial \varphi}{\partial t _ {f}} - \boldsymbol {\gamma} ^ {\mathrm {T}} \frac {\partial \boldsymbol {\psi}}{\partial t _ {f}}
$$

证明 引入拉格朗日乘子向量 $\ b { \lambda } ( t ) \in \mathbf { R } ^ { n }$ 和 $\gamma \in \mathbf { R } ^ { r }$ ，构造广义泛函

$$
J _ {a} = \varphi [ \boldsymbol {x} (t _ {f}), t _ {f} ] + \boldsymbol {\gamma} ^ {\mathrm {T}} \boldsymbol {\psi} [ \boldsymbol {x} (t _ {f}), t _ {f} ] + \int_ {t _ {0}} ^ {t _ {f}} [ H (\boldsymbol {x}, \boldsymbol {u}, \boldsymbol {\lambda}, t) - \boldsymbol {\lambda} ^ {\mathrm {T}} (t) \dot {\boldsymbol {x}} (t) ] d t
$$

式中，哈密顿函数 $H ( x , u , \lambda , t )$ 定义同式(10-43)。

当末端位置由 $( x _ { f } , t _ { f } )$ 移动到 $( \boldsymbol { x } _ { f } + \delta \boldsymbol { x } _ { f } , t _ { f } + \delta t _ { f } )$ 时，产生如下广义泛函增量：

$$
\begin{array}{l} \Delta J _ {a} = \varphi \left[ \boldsymbol {x} ^ {*} \left(t _ {f}\right) + \delta \boldsymbol {x} _ {f}, t _ {f} + \delta t _ {f} \right] - \varphi \left[ \boldsymbol {x} ^ {*} \left(t _ {f}\right), t _ {f} \right] \\ + \boldsymbol {\gamma} ^ {\mathrm {T}} \left\{\boldsymbol {\psi} \left[ \boldsymbol {x} ^ {*} \left(t _ {f}\right) + \delta \boldsymbol {x} _ {t}, t _ {f} + \delta t _ {f} \right] - \boldsymbol {\psi} \left[ \boldsymbol {x} ^ {*} \left(t _ {f}\right), t _ {f} \right] \right\} \\ + \int_ {t _ {f}} ^ {t _ {f} + \delta t _ {f}} \left\{H \left(\boldsymbol {x} ^ {*} + \delta \boldsymbol {x}, \boldsymbol {u} ^ {*} + \delta \boldsymbol {u}, \lambda , t\right) - \boldsymbol {\lambda} ^ {\mathrm {T}} (t) \left[ \dot {\boldsymbol {x}} ^ {*} + \delta \dot {\boldsymbol {x}} \right] \right\} d t \\ + \int_ {t _ {0}} ^ {t _ {f}} \left[ H \left(\boldsymbol {x} ^ {*} + \delta \boldsymbol {x}, \boldsymbol {u} ^ {*} + \delta \boldsymbol {u}, \boldsymbol {\lambda}, t\right) - H \left(\boldsymbol {x} ^ {*}, \boldsymbol {u} ^ {*}, \boldsymbol {\lambda}, t\right) - \boldsymbol {\lambda} ^ {\mathrm {T}} \delta \dot {\boldsymbol {x}} \right] d t \\ \end{array}
$$

将上式展成泰勒级数并取主部，以及应用积分中值定理并考虑到 $\delta \boldsymbol { x } ( t _ { 0 } ) = \mathbf { 0 }$ ，可得广义泛函变分表达式

$$
\begin{array}{l} \delta J _ {a} = \left[ \frac {\partial \varphi}{\partial \boldsymbol {x} \left(t _ {f}\right)} \right] ^ {\mathrm {T}} \delta \boldsymbol {x} _ {f} + \frac {\partial \varphi}{\partial t _ {f}} \delta t _ {f} + \boldsymbol {\gamma} ^ {\mathrm {T}} \left\{\left[ \frac {\partial \boldsymbol {\psi} ^ {\mathrm {T}}}{\partial \boldsymbol {x} \left(t _ {f}\right)} \right] ^ {\mathrm {T}} \delta \boldsymbol {x} _ {f} + \frac {\partial \boldsymbol {\psi}}{\partial t _ {f}} \delta t _ {f} \right\} + (H - \boldsymbol {\lambda} ^ {\mathrm {T}} \dot {\boldsymbol {x}}) \Bigg | _ {t _ {f}} \delta t _ {f} \tag {10-51} \\ + \int_ {t _ {0}} ^ {t _ {f}} \left[ \left(\frac {\partial H}{\partial \boldsymbol {x}} + \dot {\boldsymbol {\lambda}}\right) ^ {\mathrm {T}} \delta \boldsymbol {x} + \left(\frac {\partial H}{\partial \boldsymbol {u}}\right) ^ {\mathrm {T}} \delta \boldsymbol {u} \right] \mathrm {d} t - (\boldsymbol {\lambda} ^ {\mathrm {T}} \delta \boldsymbol {x}) \Bigg | _ {t _ {f}} \\ \end{array}
$$

由式(10-26)知，如下关系式成立：

$$
\delta \boldsymbol {x} \left(t _ {f}\right) = \delta \boldsymbol {x} _ {f} - \dot {\boldsymbol {x}} \left(t _ {f}\right) \delta t _ {f}
$$

将式(10-26)代入式(10-51)，整理得

$$
\begin{array}{l} \delta J _ {a} = \left[ \frac {\partial \varphi}{\partial t _ {f}} + \boldsymbol {\gamma} ^ {\mathrm {T}} \frac {\partial \boldsymbol {\psi}}{\partial t _ {f}} + H \left(t _ {f}\right) \right] \delta t _ {f} + \left[ \frac {\partial \varphi}{\partial \boldsymbol {x} \left(t _ {f}\right)} + \frac {\partial \boldsymbol {\psi} ^ {\mathrm {T}}}{\partial \boldsymbol {x} \left(t _ {f}\right)} \boldsymbol {\gamma} - \boldsymbol {\lambda} \left(t _ {f}\right) \right] ^ {\mathrm {T}} \delta \boldsymbol {x} _ {f} \tag {10-52} \\ + \int_ {t _ {0}} ^ {t _ {f}} \left[ \left(\frac {\partial H}{\partial \boldsymbol {x}} + \dot {\boldsymbol {\lambda}}\right) ^ {\mathrm {T}} \delta \boldsymbol {x} + \left(\frac {\partial H}{\partial \boldsymbol {u}}\right) ^ {\mathrm {T}} \delta \boldsymbol {u} \right] d t \\ \end{array}
$$

令上式 $\delta J _ { a } = 0$ ，考虑到式中各微变量 $\delta t _ { f }$ 、 $\delta \pmb { x } _ { f }$ 、 $\delta x$ 和 $\delta \pmb { u }$ 均是任意的，由变分预备定理立即证得本定理的各项结论。

定理 10-7 的结论同样可方便地推广至末端自由和末端固定的情况，其注意事项与末端时刻固定时最优解的情况相同。不同末端状态边界条件下求最优解的必要条件列于表 10-2，以供使用时参考。

表 10-2 用变分法求最优解的必要条件  

<table><tr><td colspan="2">minJ=φ(·)+∫t0L(x,u,t)dt
s.t. x̂(t)=f(x,u,t)
x(t0)=x0
ψ[x(tf),tf]=0
H=L(x,u,t)+λTf(x,u,t)</td><td>正则方程</td><td>极值条件</td><td>边界条件与横截条件</td><td>H变化律</td></tr><tr><td rowspan="3">tf固定</td><td>末端约束</td><td rowspan="4">x̂=∂H/∂λ
λ=-∂H/∂x</td><td rowspan="4">∂H/∂u=0</td><td>x(t0)=x0,ψ[x(tf)]=0
λ(tf)=∂φ/∂x(tf)+∂ψT/∂x(tf)γ</td><td rowspan="3"></td></tr><tr><td>末端自由</td><td>x(t0)=x0
λ(tf)=∂φ/∂x(tf)</td></tr><tr><td>末端固定
(系统可控)</td><td>x(t0)=x0
λ(tf)=xf</td></tr><tr><td rowspan="3">tf自由</td><td>末端约束</td><td>x(t0)=x0
ψ[x(tf),tf]=0
λ(tf)=∂φ/∂x(tf)+∂ψT/∂x(tf)γ</td><td>H(tf)=-∂φ/∂tf-γT∂ψ/∂tf</td></tr><tr><td>末端自由</td><td rowspan="2">x̂=∂H/∂λ
λ=-∂H/∂x</td><td rowspan="2">∂H/∂u=0</td><td>x(t0)=x0
λ(tf)=∂φ/∂x(tf)</td><td>H(tf)=-∂φ/∂tf</td></tr><tr><td>末端固定
(系统可控)</td><td>x(t0)=x0
λ(tf)=xf</td><td>H(tf)=-∂φ/∂tf</td></tr></table>

例 10-6 设一阶系统方程为

$$
\dot {x} (t) = u (t)
$$

已知 $x ( 0 ) { = } 1$ ，要求 $x ( t _ { f } ) = 0$ ，试求使性能指标

$$
J = t _ {f} + \frac {1}{2} \int_ {0} ^ {t _ {f}} u ^ {2} (t) d t
$$

为极小的最优控制 $u ^ { * } ( t )$ ，以及相应的最优轨线 $x ^ { * } ( t )$ 、最优末端时刻 $t _ { f } ^ { ^ { \ast } }$ 、最小指标 $J ^ { * }$ 。其中，末端时刻 $t _ { f }$ 未给定。

解 本例为复合型性能指标、 $t _ { f }$ 自由、末端固定、控制无约束的泛函极值问题。

由已知的系统方程知，系统是可控的。令

$$
H = \frac {1}{2} u ^ {2} + \lambda u
$$

因 $\dot { \lambda } ( t ) = - \frac { \hat { \partial } H } { \hat { \partial } x } = 0$ 0 H ，故 ( ) const t a   。再由 $\lambda ( t ) = a = \mathrm { c o n s t }$

$$
\frac {\partial H}{\partial u} = u + \lambda = 0, \quad \frac {\partial^ {2} H}{\partial u ^ {2}} = 1 > 0
$$

$$
u ^ {*} (t) = - \lambda (t) = - a
$$

可使 $H = \operatorname* { m i n }$ 。由状态方程

$$
\dot {x} (t) = u = - a, \quad \int_ {x (0)} ^ {x (t)} d x = - \int_ {0} ^ {t} a d t
$$

代入 $x ( 0 ) = 1$ ，解出

$$
x ^ {*} (t) = 1 - a t
$$

利用已知的末态条件

$$
x \left(t _ {f}\right) = 1 - a t _ {f} = 0, \quad t _ {f} = 1 / a
$$

最后，根据 $H$ 变化律条件

$$
H \left(t _ {f}\right) = - \frac {\partial \varphi}{\partial t _ {f}} = - 1, \quad \frac {1}{2} u ^ {2} \left(t _ {f}\right) + \lambda \left(t _ {f}\right) u \left(t _ {f}\right) = - 1
$$

求得 ${ \frac { 1 } { 2 } } a ^ { 2 } - a ^ { 2 } = - 1 , \qquad a = { \sqrt { 2 } }$

于是，本例最优解如下：

$$
u ^ {*} = - \sqrt {2}, \quad x ^ {*} (t) = 1 - \sqrt {2} t
$$

$$
t _ {f} ^ {*} = \sqrt {2} / 2, \quad J ^ {*} = \sqrt {2}
$$

# 10-3 极小值原理及其应用

应用经典变分法求解最优控制问题，要求控制向量不受任何约束，而且要求哈密顿

函数对控制向量连续可微。但是，在实际工程问题中，控制变量往往受到一定的限制。例如，高性能飞机的舵偏角一般不超过 $\pm 5 ^ { \circ }$ ；又如，采用空气舵的地-空战术导弹，容许的最大偏舵角一般不超过 $\pm 2 0 ^ { \circ }$ 。这就使得飞机和导弹的控制力矩受到一定的限制，容许控制集合形成一个有界闭集，在容许控制集合边界上，控制变分 $\delta \pmb { u }$ 不能任意，最优控制的必要条件 ${ \partial H } / { \partial u } = \mathbf { 0 }$ 亦不满足。

为了解决控制有约束的变分问题，庞特里亚金提出并证明了极小值原理，其结论与经典变分法的结论有许多相似之处，能够应用于控制变量受边界限制的情况，并且不要求哈密顿函数对控制向量连续可微，因此获得了广泛应用。

# 1. 连续系统的极小值原理

为方便阐述，先研究定常系统、末值型性能指标、末端自由时的极小值原理，然后将所得结果加以推广。

# (1) 末端自由时的极小值原理

定理 10-8 对于如下定常系统、末值型性能指标、末端自由、控制受约束的最优控制问题

$$
\min  _ {\boldsymbol {u} (t) \in \Omega} J (\boldsymbol {u}) = \varphi [ \boldsymbol {x} \left(t _ {f}\right) ]
$$

$$
\text {s . t .} \quad \dot {\boldsymbol {x}} (t) = \boldsymbol {f} (\boldsymbol {x}, \boldsymbol {u}), \quad \boldsymbol {x} (t _ {0}) = \boldsymbol {x} _ {0}
$$

式中， $\mathbf { \Delta } \mathbf { x } ( t ) \in \mathbf { R } ^ { n } ; \pmb { u } ( t ) \in \varOmega \subset \mathbf { R } ^ { m }$ ，为任意分段连续函数， $\varOmega$ 为容许控制域；末端状态 $\boldsymbol { x } ( t _ { f } )$ 自由；末端时刻 $t _ { f }$ 固定或自由。假设：

1) 向量函数 $f ( x , \pmb { u } )$ 和标量函数 $\varphi ( x )$ 都是其自变量的连续可微函数。  
2) 在有界集上，函数 $f ( x , \pmb { u } )$ 对变量 $x$ 满足利普希茨条件。

$$
\left| \boldsymbol {f} \left(\boldsymbol {x} _ {1}, \boldsymbol {u}\right) - \boldsymbol {f} \left(\boldsymbol {x} _ {2}, \boldsymbol {u}\right) \right| \leqslant a \left| \boldsymbol {x} _ {1} - \boldsymbol {x} _ {2} \right|, \quad a > 0
$$

则对于最优解 $\pmb { u } ^ { * } ( t )$ ， ${ t _ { f } } ^ { * }$ ，和 $\boldsymbol { x } ^ { * } ( t )$ ，必存在非零的 $\ b { \lambda } ( t ) \in \mathbf { R } ^ { n }$ ，使下列必要条件成立：

# 1) 正则方程

$$
\dot {\boldsymbol {x}} (t) = \frac {\partial H}{\partial \boldsymbol {\lambda}}, \quad \dot {\boldsymbol {\lambda}} = - \frac {\partial H}{\partial \boldsymbol {x}}
$$

式中，哈密顿函数

$$
H (\boldsymbol {x}, \boldsymbol {u}, \boldsymbol {\lambda}) = \boldsymbol {\lambda} ^ {\mathrm {T}} (t) \boldsymbol {f} (\boldsymbol {x}, \boldsymbol {u})
$$

# 2) 边界条件与横截条件

$$
\boldsymbol {x} \left(t _ {0}\right) = \boldsymbol {x} _ {0}, \quad \boldsymbol {\lambda} \left(t _ {f}\right) = \frac {\partial \varphi}{\partial \boldsymbol {x} \left(t _ {f}\right)}
$$

# 3) 极小值条件

$$
H \left(\boldsymbol {x} ^ {*}, \boldsymbol {u} ^ {*}, \lambda\right) = \min  _ {\boldsymbol {u} \in \Omega} H \left(\boldsymbol {x} ^ {*}, \boldsymbol {u}, \lambda\right)
$$

4) 沿最优轨线哈密顿函数变化律( $t _ { f }$ 自由时用)

$$
H \left[ \boldsymbol {x} ^ {*} \left(t _ {f} ^ {*}\right), \boldsymbol {u} ^ {*} \left(t _ {f} ^ {*}\right), \boldsymbol {\lambda} \left(t _ {f} ^ {*}\right) \right] = 0
$$

应当指出，定理 10-8 中的必要条件 3)又可表示为

$$
H \left[ \boldsymbol {x} ^ {*} (t), \boldsymbol {u} ^ {*} (t), \boldsymbol {\lambda} (t) \right] \leqslant H _ {\boldsymbol {u} (t) \in \Omega} \left[ \boldsymbol {x} ^ {*} (t), \boldsymbol {u} (t), \boldsymbol {\lambda} (t) \right]
$$

上式表示，对所有 $t \in \left[ t _ { 0 } , t _ { f } \right]$ ， $\pmb { u } ( t )$ 遍取 $^ { \varOmega }$ 中所有点，使 $H$ 为绝对极小值的 $\mathbf { \boldsymbol { \mathsf { u } } } ( t ) = \mathbf { \boldsymbol { \mathsf { u } } } ^ { * } ( t )$ 。因而庞特里亚金原理一般称为极小值原理。

与经典变分法相比，极小值原理的重要意义有如下几方面：

1) 容许控制条件放宽了。极小值条件对通常的控制约束均适用。  
2) 最优控制使哈密顿函数取全局极小值。当满足经典变分法的应用条件时，其极值条件 ${ \hat { \partial } } H / { \hat { \partial } } \pmb { u } = \mathbf { 0 }$ 是极小值原理中极小值条件 $\boldsymbol { H } ^ { * } = \operatorname* { m i n } _ { \boldsymbol { u } \in \mathcal { Q } } \boldsymbol { H }$ 的一种特例。  
3) 极小值原理不要求哈密顿函数对控制向量的可微性，因而扩大了应用范围。  
4) 极小值原理给出的是最优解的必要而非充分条件。如果由实际工程问题的物理意义可以判定解是存在的，而由极小值原理求出的控制又是唯一的，则该控制为要求的最优控制。实际遇到的工程问题往往属于这种情况。

例 10-7 设系统方程及初始条件为

$$
\dot {x} _ {1} (t) = - x _ {1} (t) + u (t), \quad x _ {1} (0) = 1
$$

$$
\dot {x} _ {2} (t) = x _ {1} (t), \quad \quad \quad \quad \quad \quad \quad \quad \quad x _ {2} (0) = 0
$$

式中， $\left| u ( t ) \right| \leqslant 1$ 。若系统末态 $ { \boldsymbol { { x } } } ( t _ { f } )$ 自由，试求 $u ^ { * } ( t )$ 使性能指标

$$
J = x _ {2} (1) = \min
$$

解 本例为定常系统、末值型性能指标、末端自由、 $t _ { f }$ 固定、控制受约束的最优控制问题。由题意

$$
\varphi \left[ \boldsymbol {x} \left(t _ {f}\right) \right] = x _ {2} (1), \quad t _ {f} = 1
$$

令 $H ( \pmb { x } , \boldsymbol { u } , \pmb { \lambda } ) = \lambda _ { 1 } ( - x _ { 1 } + u ) + \lambda _ { 2 } x _ { 1 }$

由协态方程

$$
\dot {\lambda} _ {2} = - \frac {\partial H}{\partial x _ {2}} = 0, \quad \lambda_ {2} (t) = c _ {2}
$$

$$
\dot {\lambda} _ {1} = - \frac {\partial H}{\partial x _ {1}} = \lambda_ {1} - \lambda_ {2}, \quad \lambda_ {1} (t) = c _ {1} e ^ {t} + c _ {2}
$$

式中， $c _ { 1 }$ 和 $c _ { 2 }$ 为待定常数。

由横截条件

$$
\lambda_ {1} (1) = \frac {\partial \varphi}{\partial x _ {1} (1)} = 0, \quad \lambda_ {2} (1) = \frac {\partial \varphi}{\partial x _ {2} (1)} = 1
$$

解出 $c _ { 1 } = - \mathsf { e } ^ { - 1 }$ ， $c _ { 2 } = 1$ 。故有 $\lambda _ { 1 } ( t ) = 1 - \mathsf { e } ^ { t - 1 }$ 。

由极小值条件

$$
u ^ {*} (t) = - \operatorname {s g n} (\lambda_ {1}) = \left\{ \begin{array}{l l} - 1, & \quad \lambda_ {1} > 0 \\ 1, & \quad \lambda_ {1} <   0 \end{array} \right.
$$

易知 $\lambda _ { 1 } ( t ) = 1 - \mathbf { e } ^ { t - 1 } > 0 , \qquad \forall t \in [ 0 , 1 )$

$$
\lambda_ {1} (t) = 0, \quad t = 1
$$

故所求最优控制

$$
u ^ {*} (t) = \left\{ \begin{array}{l l} - 1, & \quad \forall t \in [ 0, 1) \\ 0, & \quad t = 1 \end{array} \right.
$$

定理 10-8是适用于定常系统、末值型性能指标、末端自由时的极小值原理，但许多常见的最优控制问题都可以化为这种形式，例如可推广于时变系统。

定理 10-9 对于如下时变系统、末值型性能指标、末端自由、控制受约束的最优控制问题

$$
\min  _ {\boldsymbol {u} (t) \in \Omega} J (\boldsymbol {u}) = \varphi \left[ \boldsymbol {x} \left(t _ {f}\right), t _ {f} \right]
$$

$$
\text {s . t .} \quad \dot {\boldsymbol {x}} (t) = \boldsymbol {f} (\boldsymbol {x}, \boldsymbol {u}, t), \quad \boldsymbol {x} \left(t _ {0}\right) = \boldsymbol {x} _ {0}
$$

式中， $t _ { f }$ 固定或自由，假设同定理 10-8。则最优解的必要条件如下。

1) 正则方程

$$
\dot {\boldsymbol {x}} (t) = \frac {\partial H}{\partial \boldsymbol {\lambda}}, \quad \dot {\boldsymbol {\lambda}} (t) = - \frac {\partial H}{\partial \boldsymbol {x}}
$$

其中哈密顿函数

$$
H (\boldsymbol {x}, \boldsymbol {u}, \lambda , t) = \lambda^ {\mathrm {T}} (t) \boldsymbol {f} (\boldsymbol {x}, \boldsymbol {u}, t)
$$

2) 边界条件与横截条件

$$
\boldsymbol {x} \left(t _ {0}\right) = \boldsymbol {x} _ {0}, \quad \lambda \left(t _ {f}\right) = \frac {\partial \varphi}{\partial \boldsymbol {x} \left(t _ {f}\right)}
$$

3) 极小值条件

$$
H \left(\boldsymbol {x} ^ {*}, \boldsymbol {u} ^ {*}, \lambda , t\right) = \min  _ {\boldsymbol {u} (t) \in \Omega} H \left(\boldsymbol {x} ^ {*}, \boldsymbol {u}, \lambda , t\right)
$$

4) 沿最优轨线哈密顿函数变化律( $t _ { f }$ 自由时用)

$$
H \left[ \boldsymbol {x} ^ {*} \left(t _ {f} ^ {*}\right), \boldsymbol {u} ^ {*} \left(t _ {f} ^ {*}\right), \boldsymbol {\lambda} \left(t _ {f} ^ {*}\right), t _ {f} ^ {*} \right] = - \frac {\partial \varphi \left[ \boldsymbol {x} ^ {*} \left(t _ {f} ^ {*}\right) , t _ {f} ^ {*} \right]}{\partial t _ {f}}
$$

证明 令辅助变量 $X _ { n + 1 } ( t ) = t$ ，则有

$$
\dot {x} _ {n + 1} (t) = 1, \quad x _ {n + 1} \left(t _ {0}\right) = t _ {0}, \quad x _ {n + 1} \left(t _ {f}\right) = t _ {f}
$$

构造增广向量

$$
\overline {{\boldsymbol {x}}} (t) = \left[ \begin{array}{c} \boldsymbol {x} (t) \\ x _ {n + 1} (t) \end{array} \right], \quad \overline {{\boldsymbol {f}}} (\overline {{\boldsymbol {x}}}, \boldsymbol {u}) = \left[ \begin{array}{c} \boldsymbol {f} (\boldsymbol {x}, \boldsymbol {u}, t) \\ 1 \end{array} \right], \quad \overline {{\boldsymbol {x}}} _ {0} (t _ {0}) = \left[ \begin{array}{c} \boldsymbol {x} _ {0} \\ t _ {0} \end{array} \right] = \overline {{\boldsymbol {x}}} _ {0}
$$

于是，该时变问题转化为如下定常问题：

$$
\min  _ {\boldsymbol {u} (t) \in \Omega} J = \varphi [ \bar {\boldsymbol {x}} (t _ {f}) ] = \varphi [ \boldsymbol {x} (t _ {f}), x _ {n + 1} (t _ {f}) ]
$$

$$
\text {s . t .} \quad \dot {\overline {{\boldsymbol {x}}}} (t) = \overline {{\boldsymbol {f}}} [ \overline {{\boldsymbol {x}}} (t), \boldsymbol {u} (t) ], \quad \overline {{\boldsymbol {x}}} (t _ {0}) = \overline {{\boldsymbol {x}}} _ {0}
$$

令辅助协态变量为 $\lambda _ { n + 1 } ( t )$ ，构造增广协态向量

$$
\bar {\lambda} (t) = \left[ \begin{array}{c} \lambda (t) \\ \lambda_ {n + 1} (t) \end{array} \right] \tag {10-53}
$$

哈密顿函数

$$
\begin{array}{l} \bar {H} (\bar {x}, u, \bar {\lambda}) = \bar {\lambda} ^ {\mathrm {T}} (t) \bar {f} (\bar {x}, u) = \lambda^ {\mathrm {T}} (t) f (x, u, t) + \lambda_ {n + 1} (t) \tag {10-54} \\ = H (\boldsymbol {x}, \boldsymbol {u}, \lambda , t) + \lambda_ {n + 1} (t) \\ \end{array}
$$

其中 $H ( x , \pmb { u } , \pmb { \lambda } , t ) = \pmb { \lambda } ^ { \mathrm { { T } } } ( t ) \pmb { f } ( \pmb { x } , \pmb { u } , t )$ (10-55)

由定理 10-8，协态方程为

$$
\dot {\bar {\lambda}} (t) = - \frac {\partial \bar {H}}{\partial \bar {x}}
$$

代入式(10-53)和式(10-54)，得

$$
\dot {\lambda} (t) = - \frac {\partial H}{\partial x}, \quad \dot {\lambda} _ {n + 1} (t) = - \frac {\partial H}{\partial t} \tag {10-56}
$$

由式(10-55)，下式显然成立

$$
\dot {\boldsymbol {x}} (t) = \frac {\partial H}{\partial \boldsymbol {\lambda}} = \boldsymbol {f} (\boldsymbol {x}, \boldsymbol {u}, t)
$$

从而证明了本定理的结论 1)。

根据定理 10-8，横截条件

$$
\bar {\lambda} \left(t _ {f}\right) = \frac {\partial \varphi \left[ \bar {x} \left(t _ {f}\right) \right]}{\partial \bar {x} \left(t _ {f}\right)}
$$

代入 $\overline { { \lambda } } ( t _ { f } )$ 和 $\overline { { \boldsymbol { x } } } ( t _ { f } )$ 表达式，易得

$$
\boldsymbol {\lambda} \left(t _ {f}\right) = \frac {\partial \varphi}{\partial \boldsymbol {x} \left(t _ {f}\right)}, \quad \lambda_ {n + 1} \left(t _ {f}\right) = \frac {\partial \varphi}{\partial t _ {f}} \tag {10-57}
$$

于是，证明了本定理的结论 2)。

由定理 10-8，极小值条件为

$$
\bar {H} (\bar {x} ^ {*}, u ^ {*}, \bar {\lambda}) = \min  _ {u \in \Omega} \bar {H} (\bar {x} ^ {*}, u, \bar {\lambda})
$$

代入式(10-54)，上式可写为

$$
H \left(\boldsymbol {x} ^ {*}, \boldsymbol {u} ^ {*}, \boldsymbol {\lambda}, t\right) + \lambda_ {n + 1} (t) = \min  _ {\boldsymbol {u} \in \Omega} H \left(\boldsymbol {x} ^ {*}, \boldsymbol {u}, \boldsymbol {\lambda}, t\right) + \lambda_ {n + 1} (t)
$$

立即证得本定理的结论 3)。

根据定理 10-8 中的沿最优轨线哈密顿函数变化律以及式(10-54)，有

$$
\begin{array}{l} \bar {H} \left[ \bar {x} ^ {*} \left(t _ {f} ^ {*}\right), u ^ {*} \left(t _ {f} ^ {*}\right), \bar {\lambda} \left(t _ {f} ^ {*}\right) \right] \\ = H \left[ \boldsymbol {x} ^ {*} \left(t _ {f} ^ {*}\right), \boldsymbol {u} ^ {*} \left(t _ {f} ^ {*}\right), \boldsymbol {\lambda} \left(t _ {f} ^ {*}\right), t _ {f} ^ {*} \right] + \lambda_ {n + 1} \left(t _ {f} ^ {*}\right) = 0 \\ \end{array}
$$

代入式(10-57)，证得本定理结论 4)：

$$
H ^ {*} \left(t _ {f} ^ {*}\right) = - \frac {\partial \varphi}{\partial t _ {f}}
$$

比较定理 10-9与定理 10-8可见，时变性并不影响极小值原理中的正则方程、横截条件和极小值条件，但却改变了哈密顿函数沿最优轨线的变化律。

定理 10-8 的形式还可推广于积分型性能指标的问题。

定理 10-10 对于如下定常系统、积分型性能指标、末端自由、控制受约束的最优控制问题

$$
\min  _ {\boldsymbol {u} (t) \in \Omega} J (\boldsymbol {u}) = \int_ {t _ {0}} ^ {t _ {f}} L (\boldsymbol {x}, \boldsymbol {u}) d t
$$

$$
\text {s . t .} \quad \dot {\boldsymbol {x}} (t) = \boldsymbol {f} (\boldsymbol {x}, \boldsymbol {u}), \quad \boldsymbol {x} (t _ {0}) = \boldsymbol {x} _ {0}
$$

式中， $t _ { f }$ 固定或自由，假设同定理 10-8。则最优解的必要条件如下。

1) 正则方程

$$
\dot {\boldsymbol {x}} (t) = \frac {\partial H}{\partial \boldsymbol {\lambda}}, \quad \dot {\boldsymbol {\lambda}} (t) = - \frac {\partial H}{\partial \boldsymbol {x}}
$$

其中哈密顿函数

$$
H (\boldsymbol {x}, \boldsymbol {u}, \lambda) = L (\boldsymbol {x}, \boldsymbol {u}) + \lambda^ {\mathrm {T}} (t) \boldsymbol {f} (\boldsymbol {x}, \boldsymbol {u})
$$

2) 边界条件与横截条件

$$
\boldsymbol {x} \left(t _ {0}\right) = \boldsymbol {x} _ {0}, \quad \boldsymbol {\lambda} \left(t _ {f}\right) = \mathbf {0}
$$

3) 极小值条件

$$
H \left(\boldsymbol {x} ^ {*}, \boldsymbol {u} ^ {*}, \lambda\right) = \min  _ {\boldsymbol {u} \in \Omega} H \left(\boldsymbol {x} ^ {*}, \boldsymbol {u}, \lambda\right)
$$

4) 沿最优轨线哈密顿函数变化律( $t _ { f }$ 自由时用)

$$
H \left[ \boldsymbol {x} ^ {*} \left(t _ {f} ^ {*}\right), \boldsymbol {u} ^ {*} \left(t _ {f} ^ {*}\right), \boldsymbol {\lambda} \left(t _ {f} ^ {*}\right) \right] = 0
$$

证明 令辅助变量 $x _ { 0 } ( t ) = \int _ { t _ { 0 } } ^ { t } L ( x , \pmb { u } ) \mathrm { d } t$ ，则有

$$
\dot {x} _ {0} (t) = L (\boldsymbol {x}, \boldsymbol {u}), \quad x _ {0} \left(t _ {0}\right) = 0
$$

$$
x _ {0} \left(t _ {f}\right) = \int_ {t _ {0}} ^ {t _ {f}} L (\boldsymbol {x}, \boldsymbol {u}) d t = J (\boldsymbol {u})
$$

构造增广向量

$$
\bar {\boldsymbol {x}} (t) = \left[ \begin{array}{c} x _ {0} (t) \\ \boldsymbol {x} (t) \end{array} \right], \qquad \bar {\boldsymbol {f}} (\bar {\boldsymbol {x}}, \boldsymbol {u}) = \left[ \begin{array}{c} L (\boldsymbol {x}, \boldsymbol {u}) \\ \boldsymbol {f} (\boldsymbol {x}, \boldsymbol {u}) \end{array} \right], \qquad \bar {\boldsymbol {x}} (t _ {0}) = \left[ \begin{array}{c} 0 \\ \boldsymbol {x} _ {0} \end{array} \right] = \bar {\boldsymbol {x}} _ {0}
$$

于是，积分型性能指标问题转化为如下末值型性能指标问题：

$$
\min  _ {\boldsymbol {u} (t) \in \Omega} J (\boldsymbol {u}) = x _ {0} \left(t _ {f}\right) \triangleq \varphi \left[ \bar {\boldsymbol {x}} \left(t _ {f}\right) \right]
$$

$\begin{array} { r } { \mathrm { s . t . } \qquad \dot { \overline { { x } } } ( t ) = \overline { { f } } \big [ \overline { { x } } , \boldsymbol { u } \big ] , \qquad \overline { { x } } ( t _ { 0 } ) = \overline { { x } } _ { 0 } } \end{array}$

令 $\lambda _ { 0 } ( t )$ 为辅助协态变量，构造增广协态向量

$$
\bar {\lambda} (t) = \left[ \begin{array}{l} \lambda_ {0} (t) \\ \lambda (t) \end{array} \right] \tag {10-58}
$$

及哈密顿函数

$$
\begin{array}{l} \bar {H} (\bar {x}, u, \bar {\lambda}) = \bar {\lambda} ^ {\mathrm {T}} (t) \bar {f} (\bar {x}, u) = \lambda_ {0} L (x, u) + \lambda^ {\mathrm {T}} f (x, u) \tag {10-59} \\ = H _ {0} (\boldsymbol {x}, \boldsymbol {u}, \boldsymbol {\lambda}) + \lambda_ {0} L (\boldsymbol {x}, \boldsymbol {u}) \\ \end{array}
$$

由定理 10-8，协态方程为

$$
\dot {\vec {\lambda}} (t) = \frac {\partial \bar {H}}{\partial \bar {x}}
$$

代入式(10-58)及式(10-59)，得

$$
\left[ \begin{array}{l} \dot {\lambda} _ {0} (t) \\ \dot {\boldsymbol {\lambda}} (t) \end{array} \right] = - \left[ \begin{array}{l} \frac {\partial \bar {H}}{\partial x _ {0}} \\ \frac {\partial \bar {H}}{\partial \boldsymbol {x}} \end{array} \right] = - \left[ \begin{array}{l} 0 \\ \frac {\partial \bar {H}}{\partial \boldsymbol {x}} \end{array} \right]
$$

因而有

$$
\lambda_ {0} (t) = \text {c o n s t} \tag {10-60}
$$

$$
\dot {\lambda} (t) = - \frac {\partial \bar {H}}{\partial x} \tag {10-61}
$$

再由定理 10-8的横截条件可得

$$
\bar {\lambda} \left(t _ {f}\right) = \frac {\partial \varphi \left[ \bar {x} \left(t _ {f}\right) \right]}{\partial \bar {x} \left(t _ {f}\right)}
$$

因 $\varphi [ \overline { { \boldsymbol { x } } } ( t _ { f } ) ] = x _ { 0 } ( t _ { f } )$ ，故上式可表示为

$$
\left[ \begin{array}{l} \lambda_ {0} (t _ {f}) \\ \boldsymbol {\lambda} (t _ {f}) \end{array} \right] = \left[ \begin{array}{c} \frac {\partial \varphi}{\partial x _ {0} (t _ {f})} \\ \frac {\partial \varphi}{\partial \boldsymbol {x} (t _ {f})} \end{array} \right] = \left[ \begin{array}{l} 1 \\ \boldsymbol {0} \end{array} \right]
$$

从而

$$
\lambda \left(t _ {f}\right) = 0, \quad \lambda_ {0} (t) = \lambda_ {0} \left(t _ {f}\right) = 1
$$

哈密顿函数

$$
\bar {H} (\bar {\boldsymbol {x}}, \boldsymbol {u}, \bar {\lambda}) = L (\boldsymbol {x}, \boldsymbol {u}) + \lambda^ {\mathrm {T}} \boldsymbol {f} (\boldsymbol {x}, \boldsymbol {u}) = H (\boldsymbol {x}, \boldsymbol {u}, \lambda) \tag {10-62}
$$

由定理 10-8，其状态方程为

$$
\dot {\bar {\mathbf {x}}} (t) = \frac {\partial \bar {H}}{\partial \bar {\boldsymbol {\lambda}}} = \frac {\partial H}{\partial \bar {\boldsymbol {\lambda}}}
$$

代入 $\overline { { { \bf x } } } ( t )$ 和 $\overline { { \lambda } } ( t )$ 的增广形式，证得

$$
\dot {\boldsymbol {x}} (t) = \frac {\partial H}{\partial \boldsymbol {\lambda}}, \quad \dot {\boldsymbol {x}} _ {0} (t) = L (\boldsymbol {x}, \boldsymbol {u})
$$

再将式(10-62)代入式(10-61)，有

$$
\dot {\lambda} (t) = - \frac {\partial H}{\partial x}
$$

由定理 10-8，其极小值条件为

$$
\bar {H} (\bar {x} ^ {*}, u ^ {*}, \bar {\lambda}) = \min  _ {u \in \Omega} \bar {H} (\bar {x} ^ {*}, u, \bar {\lambda})
$$

已证 $\boldsymbol { \overline { { H } } } ( \boldsymbol { \overline { { x } } } ^ { * } , \boldsymbol { u } , \boldsymbol { \overline { { \lambda } } } ) = \boldsymbol { H } ( \boldsymbol { x } , \boldsymbol { u } , \lambda )$ ，立即证得

$$
H \left(\boldsymbol {x} ^ {*}, \boldsymbol {u} ^ {*}, \lambda\right) = \min  _ {\boldsymbol {u} \in \Omega} H \left(\boldsymbol {x} ^ {*}, \boldsymbol {u}, \lambda\right)
$$

由定理 10-8，在最优轨线末端有

$$
\bar {H} \left[ \bar {\boldsymbol {x}} ^ {*} \left(t _ {f} ^ {*}\right), \boldsymbol {u} ^ {*} \left(t _ {f} ^ {*}\right), \bar {\boldsymbol {\lambda}} \left(t _ {f} ^ {*}\right) \right] = 0
$$

代入式(10-62)，立即证得 $H ^ { ^ { * } } ( t _ { f } ^ { ^ { * } } ) = 0$ 。

比较定理 10-10、定理 10-8 可见，积分型性能指标改变了哈密顿函数的形式，也影响了横截条件表达式。应当指出，不论是复合型性能指标，还是积分型性能指标，抑或是末值型性能指标，其哈密顿函数的统一形式应为

$$
H (\boldsymbol {x}, \boldsymbol {u}, \boldsymbol {\lambda}) = L (\boldsymbol {x}, \boldsymbol {u}) + \boldsymbol {\lambda} ^ {\mathrm {T}} (t) \boldsymbol {f} (\boldsymbol {x}, \boldsymbol {u}) \tag {10-63}
$$

这一规定，对时变系统同样适用。

例 10-8 设一阶系统方程为

$$
\dot {x} (t) = x (t) - u (t), \quad x (0) = 5
$$

其中控制约束： $0 . 5 \leqslant u ( t ) \leqslant 1$ 。试求使性能指标

$$
J = \int_ {0} ^ {1} [ x (t) + u (t) ] d t
$$

为极小值的最优控制 $u ^ { * } ( t )$ 及最优轨线 $x ^ { * } ( t )$ 。

解 本例为定常系统、积分型性能指标、 $t _ { f }$ 固定、末端自由、控制受约束的最优控

制问题。令哈密顿函数

$$
H = x + u + \lambda (x - u) = x (1 + \lambda) + u (1 - \lambda)
$$

由于 $H$ 是 $u$ 的线性函数，根据极小值原理知，使 $H$ 绝对极小就相当于使性能指标极小，因此要求 $u ( 1 - \lambda )$ 极小。因 $u$ 的取值上限为 1，下限为 0.5，故应取

$$
u ^ {*} (t) = \left\{ \begin{array}{l l} 1, & \lambda > 1 \\ 0. 5, & \lambda <   1 \end{array} \right.
$$

由协态方程

$$
\dot {\lambda} (t) = - \frac {\partial H}{\partial x} = - (1 + \lambda)
$$

其解为 $\lambda ( t ) = c \mathbf { e } ^ { - t } - 1$ ，其中常数 $c$ 待定。

由横截条件

$$
\lambda (1) = c \mathrm {e} ^ {- 1} - 1 = 0
$$

求出 $c { = } \mathrm { e }$ 。于是

$$
\lambda (t) = \mathrm {e} ^ {1 - t} - 1
$$

显然，当 $\lambda ( t _ { s } ) = 1$ 时， $u ^ { * } ( t )$ 产生切换，其中 $t _ { s }$ 为切换时间。令 $\lambda ( t _ { s } ) = \mathbf { e } ^ { 1 - t _ { s } } - 1 = 1$ 得 $t _ { s } = 0 . 3 0 7$ ，故最优控制

$$
u ^ {*} (t) = \left\{ \begin{array}{l l} 1, & \quad 0 \leqslant t <   0. 3 0 7 \\ 0. 5, & \quad 0. 3 0 7 \leqslant t \leqslant 1 \end{array} \right.
$$

将 $u ^ { * } ( t )$ 代入状态方程，有

$$
\dot {x} (t) = \left\{ \begin{array}{l l} x (t) - 1, & 0 \leqslant t <   0. 3 0 7 \\ x (t) - 0. 5, & 0. 3 0 7 \leqslant t \leqslant 1 \end{array} \right.
$$

解得

$$
x (t) = \left\{ \begin{array}{l l} c _ {1} \mathrm {e} ^ {t} + 1, & 0 \leqslant t <   0. 3 0 7 \\ c _ {2} \mathrm {e} ^ {t} + 0. 5, & 0. 3 0 7 \leqslant t \leqslant 1 \end{array} \right.
$$

代入 $x ( 0 ) = 5$ ，求出 $c _ { \scriptscriptstyle 1 } = 4$ ，因而

$$
x ^ {*} (t) = 4 \mathrm {e} ^ {t} + 1, \quad 0 \leqslant t <   0. 3 0 7
$$

在上式中，令 $t { = } 0 . 3 0 7$ ，可以求出 $0 . 3 0 7 \leqslant t \leqslant 1$ 时 $x ( t )$ 的初态 $x ( 0 . 3 0 7 ) = 6 . 4 4$ ，从而求得$c _ { 2 } = 4 . 3 7$ 。于是，最优轨线为

$$
x ^ {*} (t) = \left\{ \begin{array}{l l} 4 \mathrm {e} ^ {t} + 1, & 0 \leqslant t <   0. 3 0 7 \\ 4. 3 7 \mathrm {e} ^ {t} + 0. 5, & 0. 3 0 7 \leqslant t \leqslant 1 \end{array} \right.
$$

本例最优解曲线如图 10-4 所示。

# (2) 末端约束时的极小值原理

对于具有目标集约束条件的最优控制问题，需要把极小值原理的原始形式推广到末端受约束时的最优控制问题。

![](images/f36def03d7210a969865296e10c361b67877b34495795be2d9846b5fc3c2dfb5.jpg)  
图 10-4 例10-8最优解曲线

定理 10-11 对于如下定常系统、末值型性能指标、末端受约束、控制也受约束的最优控制问题

$$
\begin{array}{l} \min  _ {\boldsymbol {u} (t) \in \Omega} J (\boldsymbol {u}) = \varphi [ \boldsymbol {x} (t _ {f}) ] \\ s. t. ① \dot {\boldsymbol {x}} (t) = \boldsymbol {f} (\boldsymbol {x}, \boldsymbol {u}), \quad \boldsymbol {x} \left(t _ {0}\right) = \boldsymbol {x} _ {0} \\ ② \psi [ x (t _ {f}) ] = 0 \\ \end{array}
$$

式中， $t _ { f }$ 固定或自由； $\pmb { \psi } ( \cdot ) \in { \bf R } ^ { r }$ ， $r \leqslant n$ ，在$[ t _ { 0 } , t _ { f } ]$ 上连续可微；其余假设同定理 10-8。则必存在非零常向量 $\gamma \in \mathbf { R } ^ { r }$ 和 $\ b { \lambda } ( t ) \in \mathbf { R } ^ { n }$ ，使最优解满足如下必要条件：

1) 正则方程

$$
\dot {\boldsymbol {x}} (t) = \frac {\partial H}{\partial \boldsymbol {\lambda}}, \quad \dot {\boldsymbol {\lambda}} (t) = - \frac {\partial H}{\partial \boldsymbol {x}}
$$

其中哈密顿函数

$$
H (\boldsymbol {x}, \boldsymbol {u}, \lambda) = \lambda^ {\mathrm {T}} (t) \boldsymbol {f} (\boldsymbol {x}, \boldsymbol {u})
$$

2) 边界条件与横截条件

$$
\boldsymbol {x} \left(t _ {0}\right) = \boldsymbol {x} _ {0}, \quad \boldsymbol {\psi} \left[ \boldsymbol {x} \left(t _ {f}\right) \right] = \mathbf {0}, \quad \boldsymbol {\lambda} \left(t _ {f}\right) = \frac {\partial \varphi}{\partial \boldsymbol {x} \left(t _ {f}\right)} + \frac {\partial \boldsymbol {\psi} ^ {\mathrm {T}}}{\partial \boldsymbol {x} \left(t _ {f}\right)} \boldsymbol {\gamma}
$$

3) 极小值条件

$$
H \left(\boldsymbol {x} ^ {*}, \boldsymbol {u} ^ {*}, \boldsymbol {\lambda}\right) = \min  _ {\boldsymbol {u} \in \Omega} H \left(\boldsymbol {x} ^ {*}, \boldsymbol {u}, \boldsymbol {\lambda}\right)
$$

4) 沿最优轨线哈密顿函数变化律( $t _ { f }$ 自由时用)

$$
H \left[ \boldsymbol {x} ^ {*} \left(t _ {f} ^ {*}\right), \boldsymbol {u} ^ {*} \left(t _ {f} ^ {*}\right), \boldsymbol {\lambda} \left(t _ {f} ^ {*}\right) \right] = 0
$$

证明 引入拉格朗日乘子向量 $\lambda ( t ) \in \mathbf { R } ^ { n }$ 和 $\gamma \in \mathbf { R } ^ { r }$ ，构造等价末值型性能指标

$$
\tilde {J} (\boldsymbol {u}) = \tilde {\varphi} [ \boldsymbol {x} (t _ {f}) ] = \varphi [ \boldsymbol {x} (t _ {f}) ] + \boldsymbol {\gamma} ^ {\mathrm {T}} \boldsymbol {\psi} [ \boldsymbol {x} (t _ {f}) ]
$$

则最优控制问题等同于定理 10-8。

根据定理 10-8，横截条件为

$$
\boldsymbol {\lambda} \left(t _ {f}\right) = \frac {\partial \tilde {\varphi}}{\partial \boldsymbol {x} \left(t _ {f}\right)} = \frac {\partial \varphi}{\partial \boldsymbol {x} \left(t _ {f}\right)} + \frac {\partial \boldsymbol {\psi} ^ {\mathrm {T}}}{\partial \boldsymbol {x} \left(t _ {f}\right)} \boldsymbol {\gamma}
$$

其余结论同定理 10-8，故本定理得证。

不难证明，上述定理可以推广到时变情况。

定理 10-12 对于如下时变系统、末值型性能指标、末端受约束、控制也受约束的最优控制问题

$$
\min  _ {\boldsymbol {u} (t) \in \Omega} J (\boldsymbol {u}) = \varphi \left[ \boldsymbol {x} \left(t _ {f}\right), t _ {f} \right]
$$

s.t. $\textcircled { 1 } \dot { \mathbf { x } } ( t ) = \mathbf { \boldsymbol { f } } ( \mathbf { \boldsymbol { x } } , \mathbf { \boldsymbol { u } } , t ) , ~ \mathbf { \boldsymbol { x } } ( t _ { 0 } ) = \mathbf { \boldsymbol { x } } _ { 0 }$

$$
② \psi [ x (t _ {f}), t _ {f} ] = 0
$$

式中， $t _ { f }$ 固定或自由，假设条件同定理 10-11。则必存 $r$ 维非零常向量 和 $n$ 维向量 $\lambda ( t )$ ，使最优解满足如下必要条件：

1) 正则方程

$$
\dot {\boldsymbol {x}} (t) = \frac {\partial H}{\partial \boldsymbol {\lambda}}, \quad \dot {\boldsymbol {\lambda}} (t) = - \frac {\partial H}{\partial \boldsymbol {x}}
$$

其中哈密顿函数

$$
H (\boldsymbol {x}, \boldsymbol {u}, \lambda , t) = \lambda^ {\mathrm {T}} (t) \boldsymbol {f} (\boldsymbol {x}, \boldsymbol {u}, t)
$$

2) 边界条件与横截条件

$$
\boldsymbol {x} \left(t _ {0}\right) = \boldsymbol {x} _ {0}, \quad \psi \left[ \boldsymbol {x} \left(t _ {f}\right), t _ {f} \right] = \mathbf {0}, \quad \boldsymbol {\lambda} \left(t _ {f}\right) = \frac {\partial \varphi}{\partial \boldsymbol {x} \left(t _ {f}\right)} + \frac {\partial \boldsymbol {\psi} ^ {\mathrm {T}}}{\partial \boldsymbol {x} \left(t _ {f}\right)} \boldsymbol {\gamma}
$$

3) 极小值条件

$$
H \left(\boldsymbol {x} ^ {*}, \boldsymbol {u} ^ {*}, \boldsymbol {\lambda}, t\right) = \min  _ {\boldsymbol {u} \in \Omega} H \left(\boldsymbol {x} ^ {*}, \boldsymbol {u}, \boldsymbol {\lambda}, t\right)
$$

4) 沿最优轨线哈密顿函数变化律( $t _ { f }$ 自由时用)

$$
H \left[ \boldsymbol {x} ^ {*} \left(t _ {f} ^ {*}\right), \boldsymbol {u} ^ {*} \left(t _ {f} ^ {*}\right), \boldsymbol {\lambda} \left(t _ {f} ^ {*}\right), t _ {f} ^ {*} \right] = - \frac {\partial \varphi}{\partial t _ {f}} - \boldsymbol {\gamma} ^ {\mathrm {T}} \frac {\partial \boldsymbol {\psi}}{\partial t _ {f}}
$$

证明 引入拉格朗日乘子 $\lambda ( t ) \in R ^ { n }$ 和 $\gamma \in R ^ { r }$ ，构造等价末值型性能指标

$$
\tilde {J} (\boldsymbol {u}) = \tilde {\varphi} \left[ \boldsymbol {x} \left(t _ {f}\right), t _ {f} \right] = \varphi \left[ \boldsymbol {x} \left(t _ {f}\right), t _ {f} \right] + \boldsymbol {\gamma} ^ {\mathrm {T}} \boldsymbol {\psi} \left[ \boldsymbol {x} \left(t _ {f}\right), t _ {f} \right]
$$

则最优控制问题等同于定理 10-9。

根据定理 10-9，横截条件为

$$
\boldsymbol {\lambda} \left(t _ {f}\right) = \frac {\partial \tilde {\varphi}}{\partial \boldsymbol {x} \left(t _ {f}\right)} = \frac {\partial \varphi}{\partial \boldsymbol {x} \left(t _ {f}\right)} + \frac {\partial \boldsymbol {\psi} ^ {\mathrm {T}}}{\partial \boldsymbol {x} \left(t _ {f}\right)} \boldsymbol {\gamma}
$$

沿最优轨线哈密顿函数变化律为

$$
H \left[ \boldsymbol {x} ^ {*} \left(t _ {f} ^ {*}\right), \boldsymbol {u} ^ {*} \left(t _ {f} ^ {*}\right), \boldsymbol {\lambda} \left(t _ {f} ^ {*}\right), t _ {f} ^ {*} \right] = - \frac {\partial \tilde {\varphi}}{\partial t _ {f}} = - \frac {\partial \varphi}{\partial t _ {f}} - \boldsymbol {\gamma} ^ {\mathrm {T}} \frac {\partial \boldsymbol {\psi}}{\partial t _ {f}}
$$

最优解必要条件中其余的结论与 $\tilde { \varphi } [ \mathbf { \boldsymbol { x } } ( t _ { f } ) , t _ { f } ]$ 无关，等同于定理 10-9。于是，本定理得证。

利用扩充变量法，还可以导出其他各种情况下的极小值原理形式。表 10-3分别给出了各种具体最优控制问题的极小值原理结论，以供查阅。

表 10-3 连续系统极小值原理的必要条件  

<table><tr><td>末端时刻</td><td>性能指标</td><td>末端状态</td><td>正则方程</td><td>极小值条件</td><td>边界条件与横截条件</td><td>H变化律</td></tr><tr><td rowspan="7">tf自由</td><td rowspan="2">J=φ[x(tf),tf]+∫t0L(x,u,t)dt</td><td>末端约束</td><td rowspan="5">x̂=∂H/∂λλ=-∂H/∂x其中H=L+λTf</td><td rowspan="5">H* = minH</td><td>x(t0)=x0,ψ[x(tf),tf]=0λ(tf)=[∂φ/∂x+∂ψT/∂xγ]tf</td><td>H*(tf*)=-[∂φ/∂t+γT/∂ψ]tf</td></tr><tr><td>末端自由</td><td>x(t0)=x0λ(tf)=∂φ/∂x(tf)</td><td>H*(tf*)=-∂φ/∂t</td></tr><tr><td rowspan="3">J=∫t0L(x,u,t)dt</td><td>末端约束</td><td>x(t0)=x0,ψ[x(tf),tf]=0λ(tf)=∂ψT/∂x(tf)γ</td><td>H*(tf*)=-γT/∂ψ/∂t</td></tr><tr><td>末端自由</td><td>x(t0)=x0,λ(tf)=0</td><td>H*(tf*)=0</td></tr><tr><td>末端固定</td><td>x(t0)=x0, x(tf)=xf</td><td>H*(tf*)=0</td></tr><tr><td rowspan="2">J=φ[x(tf),tf]</td><td>末端约束</td><td rowspan="2">x̂=∂H/∂λλ=-∂H/∂x其中H=λTf</td><td rowspan="2">H* = minH</td><td>x(t0)=x0,ψ[x(tf),tf]=0λ(tf)=[∂φ/∂x+∂ψT/∂xγ]tf</td><td>H*(tf*)=-[∂φ/∂t+γT/∂ψ]tf</td></tr><tr><td>末端自由</td><td>x(t0)=x0,ψ[x(tf),tf]=0λ(tf)=∂φ/∂x(tf)</td><td>H*(tf*)=-∂φ/∂t</td></tr><tr><td rowspan="7">tf固定</td><td rowspan="2">J=φ[x(tf),tf]+∫t0L(x,u,t)dt</td><td>末端约束</td><td rowspan="5">x̂=∂H/∂λλ=-∂H/∂x其中H=L+λTf</td><td rowspan="5">x(t0)=x0,ψ[x(tf),tf]=0λ(tf)=[∂φ/∂x+∂ψT/∂xγ]tf</td><td></td><td rowspan="2"></td></tr><tr><td>末端自由</td><td>x(t0)=x0,ψ[x(tf),tf]=0λ(tf)=∂φ/∂x(tf)</td></tr><tr><td rowspan="3">J=∫t0L(x,u,t)dt</td><td>末端约束</td><td>x(t0)=x0,ψ[x(tf),tf]=0λ(tf)=∂ψT/∂x(tf)</td><td rowspan="3"></td></tr><tr><td>末端自由</td><td>x(t0)=x0,ψ[x(tf),tf]=0λ(tf)=∂φ/∂x/∂xγ]tf</td></tr><tr><td>末端固定</td><td>x(t0)=x0x(tf)=xf</td></tr><tr><td rowspan="2">J=φ[x(tf),tf]</td><td>末端约束</td><td rowspan="2">x̂=∂H/∂λλ=-∂H/∂x其中H=λTf</td><td rowspan="2">x(t0)=x0,ψ[x(tf),tf]=0λ(tf)=[∂φ/∂x+∂ψT/∂xγ]tf</td><td></td><td rowspan="2"></td></tr><tr><td>末端自由</td><td>x(t0)=x0,ψ[x(tf),tf]=0λ(tf)=∂φ/∂x/∂xγ]tf</td></tr></table>

注：对于定常系统，当 $t _ { f }$ 固定时，最优解的必要条件同本表中 $t _ { f }$ 的固定情况；当 $t _ { f }$ 自由时，除 $H$ 变化律均为 $H ^ { ^ { * } } ( t _ { f } ^ { ^ { * } } ) = 0$ 外，其余同本表中 $t _ { f }$ 的自由情况。

例 10-9 设宇宙飞船登月舱的质量为 $m ( t )$ ，高度为 $h ( t )$ ，垂直速度为 $\nu ( t )$ ，发动机推力为 $u ( t )$ ，月球表面重力加速度为常数 $g$ ，不含燃料时登月舱质量为 $M$ ，初始燃料的总质量为 $F$ 。已知登月舱的状态方程为

$$
\dot {h} (t) = v (t), \qquad h (0) = h _ {0}
$$

$$
\dot {v} (t) = \frac {u (t)}{m (t)} - g, \quad v (0) = v _ {0}
$$

$$
\dot {m} (t) = - k u (t), \quad m (0) = M + F
$$

要求登月舱在月球表面实现软着陆，即目标集为

$$
\psi_ {1} = h \left(t _ {f}\right) = 0, \quad \psi_ {2} = v \left(t _ {f}\right) = 0
$$

发动机推力 $u ( t )$ 的约束为

$$
u (t) \in \Omega , \qquad \Omega = \left\{u (t) \mid 0 \leqslant u (t) \leqslant \alpha \right\}, \qquad \forall t \in \left[ 0, t _ {f} \right]
$$

试确定最优控制 $u ^ { * } ( t )$ ，使登月舱由已知初态转移到要求的目标集，并使登月舱燃料消耗

$$
J = - m \left(t _ {f}\right) = \min
$$

解 本例为时变系统、末值型性能指标、 $t _ { f }$ 自由、末端约束、控制受约束的最优控制问题。构造哈密顿函数

$$
H = \lambda_ {1} v + \lambda_ {2} \left(\frac {u}{m} - g\right) - \lambda_ {3} k u
$$

式中， $\lambda _ { \mathrm { l } } ( t )$ ， $\lambda _ { 2 } ( t )$ 和 $\lambda _ { _ 3 } ( t )$ 为待定的拉格朗日乘子。根据题意

$$
\varphi = - m \left(t _ {f}\right)
$$

由协态方程

$$
\dot {\lambda} _ {1} (t) = - \frac {\partial H}{\partial h} = 0
$$

$$
\dot {\lambda} _ {2} (t) = - \frac {\partial H}{\partial v} = - \lambda_ {1} (t)
$$

$$
\dot {\lambda} _ {3} (t) = - \frac {\partial H}{\partial m} = \frac {\lambda_ {2} (t) u (t)}{m ^ {2} (t)}
$$

由横截条件

$$
\lambda_ {1} \left(t _ {f}\right) = \frac {\partial \varphi}{\partial h \left(t _ {f}\right)} + \frac {\partial \psi_ {1}}{\partial h \left(t _ {f}\right)} \gamma_ {1} = \gamma_ {1}
$$

$$
\lambda_ {2} \left(t _ {f}\right) = \frac {\partial \varphi}{\partial v \left(t _ {f}\right)} + \frac {\partial \psi_ {2}}{\partial v \left(t _ {f}\right)} \gamma_ {2} = \gamma_ {2}
$$

$$
\lambda_ {3} \left(t _ {f}\right) = \frac {\partial \varphi}{\partial m \left(t _ {f}\right)} = - 1
$$

式中， $\gamma _ { \mathrm { { 1 } } }$ 和 $\gamma _ { _ 2 }$ 为待定的拉格朗日乘子。

将哈密顿函数整理成

$$
H = \left(\lambda_ {1} v - \lambda_ {2} g\right) + \left(\frac {\lambda_ {2}}{m} - k \lambda_ {3}\right) u
$$

由极小值条件， $H$ 相对 $u ^ { * } ( t )$ 取绝对极小值。因此，最优控制

$$
u ^ {*} (t) = \left\{ \begin{array}{l l} \alpha , & \frac {\lambda_ {2}}{m} - k \lambda_ {3} <   0 \\ 0, & \frac {\lambda_ {2}}{m} - k \lambda_ {3} > 0 \end{array} \right.
$$

上述结果表明，只有登月舱发动机推力在其最大值和零值之间进行开关控制，才有可能在软着陆的同时，保证登月舱的燃料消耗最少。

# 2. 离散系统的极小值原理

随着数字计算机的日益普及，计算机控制系统日益增多，离散系统最优控制问题的研究亦显得十分重要。其原因是多方面的：例如，许多实际问题本身就是离散的，这类问题有经济与资源系统的优化问题、交通管制问题、河流污染控制问题等；又如，对有约束的连续系统最优控制问题，需要采用计算机求数值解，使得连续最优控制中难以求解的两点边界值问题，化为易于用计算机求解的离散化两点边界值问题。

离散系统极小值原理的普遍论述比较复杂，证明过程也十分冗长。为简单起见，仅讨论控制向量序列不受约束、末端时刻(数据窗口长度)固定、末端自由或受约束情况下的离散极小值原理，然后不加证明地推广到控制向量序列受约束的情况。

# (1) 末端约束时的离散极小值原理

定理 10-13 设离散系统状态差分方程为

$$
\boldsymbol {x} (k + 1) = \boldsymbol {f} [ \boldsymbol {x} (k), \boldsymbol {u} (k), k ], \quad \boldsymbol {x} (0) = \boldsymbol {x} _ {0} \tag {10-64}
$$

$$
(k = 0, 1, \dots , N - 1)
$$

性能指标

$$
J = \varphi [ \boldsymbol {x} (N) ] + \sum_ {k = 0} ^ {N - 1} L [ \boldsymbol {x} (k), \boldsymbol {u} (k), k ] \tag {10-65}
$$

式中， $N$ 固定； $f ( \cdot )$ 、 $\varphi ( \cdot )$ 和 $L ( \cdot )$ 都是其自变量的连续可微函数； $\pmb { x } ( k ) \in \mathbf { R } ^ { n } ; \pmb { u } ( k ) \in \mathbf { R } ^ { m }$ ，其约束 $\pmb { u } ( k ) \in \varOmega$ ， $\varOmega$ 为容许控制域。末端状态受下列目标集约束：

$$
\boldsymbol {\psi} [ \boldsymbol {x} (N) ] = \mathbf {0} \tag {10-66}
$$

式中， $\pmb { \psi } ( \cdot ) \in \mathbf { R } ^ { r }$ 且连续可微， $r \leqslant n$ 。

若 $\pmb { u } ^ { * } ( k )$ 是使性能指标(10-65)为最小的最优控制序列， $x ^ { * } ( k )$ 是相应的最优轨线序列，则必存在 $r$ 维非零常向量 和 $n$ 维向量序列 $\lambda ( k )$ ，使得最优解满足如下必要条件：

1) $x ( k )$ 和 $\lambda ( k )$ 满足差分方程

$$
\boldsymbol {x} (k + 1) = \frac {\partial H (k)}{\partial \boldsymbol {\lambda} (k + 1)} \tag {10-67}
$$

$$
\boldsymbol {\lambda} (k) = \frac {\partial H (k)}{\partial \boldsymbol {x} (k)} \tag {10-68}
$$

式中，离散哈密顿函数

$$
\begin{array}{l} H (k) \triangleq H [ \boldsymbol {x} (k), \boldsymbol {u} (k), \boldsymbol {\lambda} (k), k ] \tag {10-69} \\ = L [ \boldsymbol {x} (k), \boldsymbol {u} (k), k ] + \boldsymbol {\lambda} ^ {\mathrm {T}} (k + 1) \boldsymbol {f} [ \boldsymbol {x} (k), \boldsymbol {u} (k), k ] \\ \end{array}
$$

2) 边界条件与横截条件

$$
\boldsymbol {x} (0) = \boldsymbol {x} _ {0}, \quad \boldsymbol {\psi} [ \boldsymbol {x} (N) ] = \mathbf {0}
$$

$$
\boldsymbol {\lambda} (N) = \frac {\partial \varphi}{\partial \boldsymbol {x} (N)} + \frac {\partial \boldsymbol {\psi} ^ {\mathrm {T}}}{\partial \boldsymbol {x} (N)} \gamma \tag {10-70}
$$

3) 离散哈密顿函数对最优控制序列取极小值

$$
H ^ {*} (k) = \min  _ {u (k) \in \Omega} H (k) \tag {10-71}
$$

若 $\pmb { u } ( k )$ 无约束，则极值条件为

$$
\frac {\partial H (k)}{\partial \boldsymbol {u} (k)} = \mathbf {0} \tag {10-72}
$$

证明 引入拉格朗日乘子 $\lambda ( k )$ 和，构造离散广义泛函

$$
\begin{array}{l} J _ {a} = \varphi [ \boldsymbol {x} (N) ] + \boldsymbol {\gamma} ^ {\mathrm {T}} \boldsymbol {\psi} [ \boldsymbol {x} (N) ] + \sum_ {k = 0} ^ {N - 1} \left\{L [ \boldsymbol {x} (k), \boldsymbol {u} (k), k ] \right. \tag {10-73} \\ \left. + \boldsymbol {\lambda} ^ {\mathrm {T}} (k + 1) \left[ \boldsymbol {f} (\boldsymbol {x} (k), \boldsymbol {u} (k), k) - \boldsymbol {x} (k + 1) \right] \right\} \\ \end{array}
$$

令离散哈密顿函数

$$
H (k) = L [ \boldsymbol {x} (k), \boldsymbol {u} (k), k ] + \boldsymbol {\lambda} ^ {\mathrm {T}} (k + 1) \boldsymbol {f} [ \boldsymbol {x} (k), \boldsymbol {u} (k), k ]
$$

则式(10-73)可表示为

$$
J _ {a} = \varphi [ \boldsymbol {x} (N) ] + \boldsymbol {\gamma} ^ {\mathrm {T}} \boldsymbol {\psi} [ \boldsymbol {x} (N) ] + \sum_ {k = 0} ^ {N - 1} [ H (k) - \boldsymbol {\lambda} ^ {\mathrm {T}} (k + 1) \boldsymbol {x} (k + 1) ]
$$

因为“离散分部积分”

$$
\begin{array}{l} \sum_ {k = 0} ^ {N - 1} \boldsymbol {\lambda} ^ {\mathrm {T}} (k + 1) \boldsymbol {x} (k + 1) = \sum_ {m = 1} ^ {N} \boldsymbol {\lambda} ^ {\mathrm {T}} (m) \boldsymbol {x} (m) = \sum_ {m = 0} ^ {N - 1} \boldsymbol {\lambda} ^ {\mathrm {T}} (m) \boldsymbol {x} (m) - \boldsymbol {\lambda} ^ {\mathrm {T}} (0) \boldsymbol {x} (0) + \boldsymbol {\lambda} ^ {\mathrm {T}} (N) \boldsymbol {x} (N) \\ = \sum_ {k = 0} ^ {N - 1} \boldsymbol {\lambda} ^ {\mathrm {T}} (k) \boldsymbol {x} (k) - \boldsymbol {\lambda} ^ {\mathrm {T}} (0) \boldsymbol {x} (0) + \boldsymbol {\lambda} ^ {\mathrm {T}} (N) \boldsymbol {x} (N) \\ \end{array}
$$

所以，离散广义泛函可写为

$$
J _ {a} = \varphi [ \boldsymbol {x} (N) ] + \boldsymbol {\gamma} ^ {\mathrm {T}} \boldsymbol {\psi} [ \boldsymbol {x} (N) ] + \sum_ {k = 0} ^ {N - 1} [ H (k) - \boldsymbol {\lambda} ^ {\mathrm {T}} (k) \boldsymbol {x} (k) ] + \boldsymbol {\lambda} ^ {\mathrm {T}} (0) \boldsymbol {x} (0) - \boldsymbol {\lambda} ^ {\mathrm {T}} (N) \boldsymbol {x} (N)
$$

对上式取一次变分，考虑到 $\delta { \pmb x } ( 0 ) = { \pmb 0 }$ ，可得

$$
\begin{array}{l} \delta J _ {a} = \left[ \frac {\partial \varphi}{\partial \boldsymbol {x} (N)} + \frac {\partial \boldsymbol {\psi} ^ {\mathrm {T}}}{\partial \boldsymbol {x} (N)} \boldsymbol {\gamma} - \boldsymbol {\lambda} (N) \right] ^ {\mathrm {T}} \delta \boldsymbol {x} (N) \\ + \sum_ {k = 0} ^ {N - 1} \left\{\left[ \frac {\partial H (k)}{\partial \boldsymbol {x} (k)} - \boldsymbol {\lambda} (k) \right] ^ {\mathrm {T}} \delta \boldsymbol {x} (k) + \left[ \frac {\partial H (k)}{\partial \boldsymbol {u} (k)} \right] ^ {\mathrm {T}} \delta \boldsymbol {u} (k) \right\} \\ \end{array}
$$

令 $\delta J _ { a } = 0$ ，考虑到变分 $\delta x ( k )$ 和 $\delta { x } ( N )$ 是任意的，可得

$$
\boldsymbol {\lambda} (k) = \frac {\partial H (k)}{\partial \boldsymbol {x} (k)}, \quad \boldsymbol {\lambda} (N) = \frac {\partial \varphi}{\partial \boldsymbol {x} (N)} + \frac {\partial \boldsymbol {\psi} ^ {\mathrm {T}}}{\partial \boldsymbol {x} (N)} \boldsymbol {\gamma}
$$

对于

$$
\sum_ {k = 0} ^ {N - 1} \left[ \frac {\partial H (k)}{\partial \boldsymbol {u} (k)} \right] ^ {\mathrm {T}} \delta \boldsymbol {u} (k) = 0
$$

当 $\pmb { u } ( k )$ 不受约束时， $\delta \pmb { u } ( k )$ 是任意的，故必有

$$
\frac {\partial H (k)}{\partial \boldsymbol {u} (k)} = \mathbf {0}
$$

当 $\pmb { u } ( k ) \in \varOmega$ 时，不加证明得

$$
H ^ {*} (k) = \min  _ {u (k) \in \Omega} H (k)
$$

# (2) 末端自由时的离散极小值原理

如果离散系统末端自由，则离散极小值原理的形式如下，其证明过程类似于定理10-13。读者不妨自行推证。

定理 10-14 设离散系统状态差分方程为

$$
\boldsymbol {x} (k + 1) = \boldsymbol {f} [ \boldsymbol {x} (k), \boldsymbol {u} (k), k ], \quad \boldsymbol {x} (0) = \boldsymbol {x} _ {0} (k = 0, 1, \dots , N - 1)
$$

性能指标

$$
J = \varphi [ \boldsymbol {x} (N) ] + \sum_ {k = 0} ^ {N - 1} L [ \boldsymbol {x} (k), \boldsymbol {u} (k), k ]
$$

式中， $N$ 固定，末端状态 $x ( N )$ 自由，其余假设同定理 10-13。

若 $\pmb { u } ^ { * } ( k )$ 是使性能指标为极小的最优控制序列， $x ^ { * } ( k )$ 为相应的最优轨线序列，则必存在 $n$ 维向量序列 $\lambda ( k )$ ，使得最优解满足如下必要条件：

1) $x ( k )$ 和 $\lambda ( k )$ 满足下列差分方程：

$$
\boldsymbol {x} (k + 1) = \frac {\partial H (k)}{\partial \boldsymbol {\lambda} (k + 1)}, \quad \boldsymbol {\lambda} (k) = \frac {\partial H (k)}{\partial \boldsymbol {x} (k)}
$$

式中，离散哈密顿函数

$$
\begin{array}{l} H (k) \triangleq H [ \boldsymbol {x} (k), \boldsymbol {u} (k), \boldsymbol {\lambda} (k), k ] \\ = L [ \boldsymbol {x} (k), \boldsymbol {u} (k), k ] + \boldsymbol {\lambda} ^ {\mathrm {T}} (k + 1) \boldsymbol {f} [ \boldsymbol {x} (k), \boldsymbol {u} (k), k ] \\ \end{array}
$$

2) 边界条件与横截条件

$$
\boldsymbol {x} (0) = \boldsymbol {x} _ {0}, \quad \lambda (N) = \frac {\partial \varphi}{\partial \boldsymbol {x} (N)}
$$

3) 离散哈密顿函数对最优控制序列取极小值

$$
H ^ {*} (k) = \min  _ {u (k) \in \Omega} H (k)
$$

若控制变量不受约束，则极值条件为

$$
\frac {\partial H (k)}{\partial \boldsymbol {u} (k)} = \mathbf {0}
$$

上述定理 10-13及定理 10-14表明，离散系统最优化问题归结为求解一个离散两点边值问题，且使离散性能指标泛函为极小与使离散哈密顿函数为极小是等价的。

例 10-10 设离散系统状态方程为

$$
\boldsymbol {x} (k + 1) = \left[ \begin{array}{l l} 1 & 0. 1 \\ 0 & 1 \end{array} \right] \boldsymbol {x} (k) + \left[ \begin{array}{l} 0 \\ 0. 1 \end{array} \right] u (k)
$$

已知边界条件

$$
\boldsymbol {x} (0) = \left[ \begin{array}{l} 1 \\ 0 \end{array} \right], \qquad \boldsymbol {x} (2) = \left[ \begin{array}{l} 0 \\ 0 \end{array} \right]
$$

试用离散极小值原理求最优控制序列，使性能指标

$$
J = 0. 0 5 \sum_ {k = 0} ^ {1} u ^ {2} (k)
$$

取极小值，并求出最优轨线序列。

解 本例为控制无约束， $N$ 固定，末端固定的离散最优控制问题。构造离散哈密顿函数

$$
H (k) = 0. 0 5 u ^ {2} (k) + \lambda_ {1} (k + 1) \left[ x _ {1} (k) + 0. 1 x _ {2} (k) \right] + \lambda_ {2} (k + 1) \left[ x _ {2} (k) + 0. 1 u (k) \right]
$$

式中， $\lambda _ { \mathrm { 1 } } ( k + 1 )$ 和 $\lambda _ { 2 } ( k + 1 )$ 为待定拉格朗日乘子序列。

由协态方程，有

$$
\lambda_ {1} (k) = \frac {\partial H (k)}{\partial x _ {1} (k)} = \lambda_ {1} (k + 1)
$$

$$
\lambda_ {2} (k) = \frac {\partial H (k)}{\partial x _ {2} (k)} = 0. 1 \lambda_ {1} (k + 1) + \lambda_ {2} (k + 1)
$$

所以 $\begin{array} { r l } { \lambda _ { 1 } ( 0 ) = \lambda _ { 1 } ( 1 ) , } & { { } \ \lambda _ { 2 } ( 0 ) = 0 . 1 \lambda _ { 1 } ( 1 ) + \lambda _ { 2 } ( 1 ) } \\ { \lambda _ { 1 } ( 1 ) = \lambda _ { 1 } ( 2 ) , } & { { } \ \lambda _ { 2 } ( 1 ) = 0 . 1 \lambda _ { 1 } ( 2 ) + \lambda _ { 2 } ( 2 ) } \end{array}$

由极值条件

$$
\frac {\partial H (k)}{\partial u (k)} = 0. 1 u (k) + 0. 1 \lambda_ {2} (k + 1) = 0
$$

$$
\frac {\partial^ {2} H (k)}{\partial u ^ {2} (k)} = 0. 1 > 0
$$

故 $u ^ { * } ( k ) = - \lambda _ { 2 } ( k + 1 )$

可使 $H ( k ) = \operatorname* { m i n }$ 。令 $k = 0$ 和 $k = 1$ ，得

$$
u ^ {*} (0) = - \lambda_ {2} (1), \quad u ^ {*} (1) = - \lambda_ {2} (2)
$$

将 $\boldsymbol { u } ^ { * } ( k )$ 表达式代入状态方程，可得

$$
x _ {1} (k + 1) = x _ {1} (k) + 0. 1 x _ {2} (k)
$$

$$
x _ {2} (k + 1) = x _ {2} (k) - 0. 1 \lambda_ {2} (k + 1)
$$

令 $k$ 分别等于 0 和 1，有

$$
x _ {1} (1) = x _ {1} (0) + 0. 1 x _ {2} (0), \quad x _ {2} (1) = x _ {2} (0) - 0. 1 \lambda_ {2} (1)
$$

$$
x _ {1} (2) = x _ {1} (1) + 0. 1 x _ {2} (1), \quad x _ {2} (2) = x _ {2} (1) - 0. 1 \lambda_ {2} (2)
$$

由已知边界条件

$$
x _ {1} (0) = 1, \quad x _ {2} (0) = 0
$$

$$
x _ {1} (2) = 0, \quad x _ {2} (2) = 0
$$

不难解出最优解

$$
u ^ {*} (0) = - 1 0 0, \quad u ^ {*} (1) = 1 0 0
$$

$$
\boldsymbol {x} ^ {*} (0) = \left[ \begin{array}{c} 1 \\ 0 \end{array} \right], \qquad \boldsymbol {x} ^ {*} (1) = \left[ \begin{array}{c} 1 \\ - 1 0 \end{array} \right], \qquad \boldsymbol {x} ^ {*} (2) = \left[ \begin{array}{c} 0 \\ 0 \end{array} \right]
$$

$$
\boldsymbol {\lambda} (0) = \left[ \begin{array}{c} 2 0 0 0 \\ 3 0 0 \end{array} \right], \qquad \boldsymbol {\lambda} (1) = \left[ \begin{array}{c} 2 0 0 0 \\ 1 0 0 \end{array} \right], \qquad \boldsymbol {\lambda} (2) = \left[ \begin{array}{c} 2 0 0 0 \\ - 1 0 0 \end{array} \right]
$$

# 3. 最小时间控制

最小时间控制，是可用极小值原理求最优解的一种控制类型。最小时间控制问题，又称时间最优控制问题，它要求在容许控制范围内寻求最优控制，使系统以最短的时间从任意初始状态转移到要求的目标集。一般来说，求非线性系统和任意目标集的时间最优控制的解析解十分困难，这里仅考虑线性定常系统且目标集为状态空间原点，即末端固定时的时间最优控制问题。

# (1) 最小时间控制问题

问题 10-1 设线性定常系统

$$
\dot {\boldsymbol {x}} (t) = \boldsymbol {A} \boldsymbol {x} (t) + \boldsymbol {B} \boldsymbol {u} (t) \tag {10-74}
$$

是完全可控的， $\ b { x } ( t ) \in \mathbf { R } ^ { n }$ ， $\pmb { u } ( t ) \in \mathbf { R } ^ { m }$ ， $\pmb { A }$ ， $\pmb { B }$ 为维数适当的常阵。求满足下列不等式约束的容许控制：

$$
\left| u _ {j} (t) \right| \leqslant 1; \quad j = 1, 2, \dots , m
$$

使系统(10-74)从已知初态 $\mathbf { \boldsymbol { x } } ( 0 ) = \mathbf { \boldsymbol { x } } _ { 0 }$ 转移到 $\boldsymbol { x } ( t _ { f } ) = \mathbf { 0 }$ ，并使性能指标

$$
J = \int_ {0} ^ {t _ {f}} \mathrm {d} t \tag {10-75}
$$

极小，其中 $t _ { f }$ 自由。

求解问题 10-1 之前，应首先判断该问题是否可用极小值原理求解?可以证明，只有当

系统(10-74)正常时，才能应用极小值原理求得最优解。

# (2) 正常情况与奇异情况

对于问题 10-1，构造哈密顿函数

$$
H (\boldsymbol {x}, \boldsymbol {u}, \lambda) = 1 + \lambda^ {\mathrm {T}} \boldsymbol {A} \boldsymbol {x} + \lambda^ {\mathrm {T}} \boldsymbol {B} \boldsymbol {u}
$$

根据极小值条件 $\boldsymbol { H } ^ { * } = \operatorname* { m i n } _ { \boldsymbol { u } \in \boldsymbol { \mathcal { Q } } } \boldsymbol { H }$ ，有

$$
1 + \boldsymbol {\lambda} ^ {\mathrm {T}} \boldsymbol {A} \boldsymbol {x} ^ {*} (t) + \boldsymbol {\lambda} ^ {\mathrm {T}} (t) \boldsymbol {B} \boldsymbol {u} ^ {*} (t) = \min  _ {| u | <   1} \left\{1 + \boldsymbol {\lambda} ^ {\mathrm {T}} (t) \boldsymbol {A} \boldsymbol {x} ^ {*} (t) + \boldsymbol {\lambda} ^ {\mathrm {T}} (t) \boldsymbol {B} \boldsymbol {u} (t) \right\}
$$

上式又可表示为

设 $\pmb { { \cal B } } = \left[ \pmb { { \cal b } } _ { 1 } \quad \pmb { { \cal b } } _ { 2 } \quad \cdots \quad \pmb { { \cal b } } _ { m } \right]$ (10-77)

$$
g _ {j} (t) = \boldsymbol {\lambda} ^ {\mathrm {T}} (t) \boldsymbol {b} _ {j} \tag {10-78}
$$

式中， $\pmb { b } _ { j } \in \mathbf { R } ^ { n }$ ， $j = 1 , 2 , \cdots , m$ ，则式(10-76)可用下列符号函数表示：

$$
u _ {j} ^ {*} (t) = - \operatorname {s g n} \left\{g _ {j} (t) \right\} = \left\{ \begin{array}{l l} + 1, & g _ {j} (t) <   0 \\ - 1, & g _ {j} (t) > 0 \\ \text {不 定}, & g _ {j} (t) = 0 \end{array} \right.
$$

显见，若 ${ \boldsymbol { g } } _ { j } ( t ) \neq 0 , \forall t \in [ 0 , t _ { f } ]$ $g _ { j } ( t ) \neq 0$ ，则可用极小值原理确定 ${ u _ { j } } ^ { * } ( t )$ ， $j = 1$ ，2，…， $m$ 。这种情况称为正常(平凡)情况，相应的系统(10-74)称为正常系统。

若 $g _ { j } ( t ) = 0$ ， $\forall t \in [ t _ { 1 } , t _ { 2 } ] \subset [ 0 , t _ { f } ]$ ，则因 $\boldsymbol { u _ { j } } ^ { * } ( t )$ 不定，无法应用极小值原理确定 $\boldsymbol { u _ { j } } ^ { * } ( t )$ ，只能取满足约束条件 $\left| u _ { j } ( t ) \right| \leqslant 1$ 的任意值。这种情况称为奇异(非平凡)情况，相应的系统(10-74)称为奇异系统。

# (3) 奇异性的充分必要条件

定理 10-15 对于问题 10-1，设矩阵

$$
\boldsymbol {G} _ {j} = \left[ \begin{array}{l l l l} \boldsymbol {b} _ {j} & \boldsymbol {A} \boldsymbol {b} _ {j} & \dots & \boldsymbol {A} ^ {n - 1} \boldsymbol {b} _ {j} \end{array} \right]; \quad j = 1, 2, \dots , m \tag {10-79}
$$

式中， $\pmb { b } _ { j } \in \mathbf { R } ^ { n }$ ，为矩阵 $\pmb { B }$ 的列向量。当且仅当 $m$ 个 $G _ { j }$ 矩阵中至少有一个 $G _ { j }$ 是奇异矩阵，问题 10-1 是奇异的。

证明 构造哈密顿函数

$$
H (\boldsymbol {x}, \boldsymbol {u}, \boldsymbol {\lambda}) = 1 + \boldsymbol {\lambda} ^ {\mathrm {T}} (t) [ A \boldsymbol {x} (t) + \boldsymbol {B} \boldsymbol {u} (t) ] \tag {10-80}
$$

由极小值原理知，应有 $H ^ { ^ { * } } ( t _ { f } ^ { ^ { * } } ) = 0$ ，所以在式(10-80)中，必有

$$
\boldsymbol {\lambda} (t) \neq \mathbf {0}, \quad \forall t \in \left[ 0, t _ {f} \right] \tag {10-81}
$$

由协态方程

$$
\dot {\boldsymbol {\lambda}} (t) = - \frac {\partial H}{\partial \boldsymbol {x}} = - \boldsymbol {A} ^ {\mathrm {T}} \boldsymbol {\lambda} (t)
$$

其解为 $\lambda ( t ) = \mathrm { e } ^ { - A ^ { \mathrm { T } } t } \lambda ( 0 ) , ~ \lambda ( 0 ) \neq 0$

因而 $g _ { j } ( t ) = \lambda ^ { \mathrm { { T } } } ( t ) { \pmb { b } } _ { j } = \lambda ^ { \mathrm { { T } } } ( 0 ) \mathrm { { e } } ^ { - \pmb { A } t } { \pmb { b } } _ { j }$

设存在奇异区间 $[ t _ { 1 } , t _ { 2 } ] \subset [ 0 , t _ { f } ]$ ，使得

$$
\mathbf {g} _ {j} (t) = \boldsymbol {\lambda} ^ {\mathrm {T}} (0) \mathbf {e} ^ {- A t} \mathbf {b} _ {j} = 0, \quad \forall t \in \left[ t _ {1}, t _ {2} \right]
$$

对上式求导 $n { - } 1$ 次，并根据矩阵指数性质，有

$$
(- 1) ^ {n - 1} g _ {j} ^ {(n - 1)} (t) = \boldsymbol {\lambda} ^ {\mathrm {T}} (0) \mathrm {e} ^ {- A t} \boldsymbol {A} ^ {n - 1} \boldsymbol {b} _ {j} = 0
$$

将 $g _ { j } ( t )$ 各次导数表达式写为矩阵形式，有

$$
\boldsymbol {\lambda} ^ {\mathrm {T}} (0) \left[ \begin{array}{l l l l} \mathrm {e} ^ {- A t} \boldsymbol {b} _ {j} & \mathrm {e} ^ {- A t} \boldsymbol {A} \boldsymbol {b} _ {j} & \dots & \mathrm {e} ^ {- A t} \boldsymbol {A} ^ {n - 1} \boldsymbol {b} _ {j} \end{array} \right] = 0 \tag {10-82}
$$

由矩阵论知，向量(0) 有非零解的充分必要条件为系数矩阵奇异，因此式(10-82)成立的充分必要条件为

$$
\begin{array}{l} \det \left[ \mathrm {e} ^ {- A t} \boldsymbol {b} _ {j} \quad \mathrm {e} ^ {- A t} \boldsymbol {A} \boldsymbol {b} _ {j} \quad \dots \quad \mathrm {e} ^ {- A t} \boldsymbol {A} ^ {n - 1} \boldsymbol {b} _ {j} \right] \tag {10-83} \\ = \det e ^ {- A t} \det \left[ \begin{array}{l l l l} \boldsymbol {b} _ {j} & \boldsymbol {A} \boldsymbol {b} _ {j} & \dots & \boldsymbol {A} ^ {n - 1} \boldsymbol {b} _ {j} \end{array} \right] = 0 \\ \end{array}
$$

因为 $\mathbf { e } ^ { - A t }$ 为状态转移矩阵，是非奇异的，故式(10-83)成立的充分必要条件为

$$
\det  \boldsymbol {G} _ {j} = \det  \left[ \begin{array}{l l l l} \boldsymbol {b} _ {j} & \boldsymbol {A} \boldsymbol {b} _ {j} & \dots & \boldsymbol {A} ^ {n - 1} \boldsymbol {b} _ {j} \end{array} \right] = 0, \quad \forall j = 1, 2, \dots , m
$$

由上述定理，立即可得问题 10-1 正常的充分必要条件。

定理 10-16 问题 10-1是正常的，当且仅当

$$
\operatorname {r a n k} G _ {j} = n, \quad \forall j = 1, 2, \dots , m \tag {10-84}
$$

式中， $\pmb { b } _ { j } \in \mathbf { R } ^ { n }$ ，由式(10-77)定义； $G _ { j }$ 为 $n { \times } n$ 矩阵，由式(10-79)定义。

事实上，正常系统与可控系统存在包含关系。在矩阵 $G _ { j }$ 中，若增加一些线性无关的列，则 $G _ { j }$ 的行秩不变。因此，式(10-84)可写为

$$
\begin{array}{l} \operatorname {r a n k} \left[ \begin{array}{l l l l} \boldsymbol {b} _ {j} & \boldsymbol {A} \boldsymbol {b} _ {j} & \dots & \boldsymbol {A} ^ {n - 1} \boldsymbol {b} _ {j} \end{array} \right] \tag {10-85} \\ = \operatorname {r a n k} \left[ \begin{array}{l l l l l l l l} \boldsymbol {b} _ {1} & \boldsymbol {A} \boldsymbol {b} _ {1} & \dots & \boldsymbol {A} ^ {n - 1} \boldsymbol {b} _ {1} & \dots & \boldsymbol {b} _ {m} & \boldsymbol {A} \boldsymbol {b} _ {m} & \dots & \boldsymbol {A} ^ {n - 1} \boldsymbol {b} _ {m} \end{array} \right] = n \\ \end{array}
$$

对式(10-85)进行列初等变换，并考虑到式(10-77)，则式(10-85)又可写为

$$
\operatorname {r a n k} \left[ \begin{array}{l l l l} \boldsymbol {B} & \boldsymbol {A B} & \dots & \boldsymbol {A} ^ {n - 1} \boldsymbol {B} \end{array} \right] = n \tag {10-86}
$$

上式正好是系统(10-74)完全可控的充分必要条件。因此，正常子空间包含于可控子空间。这种包含关系表明，系统可控是系统正常的前提条件。因此，在问题 10-1中提出了可控要求。显然，对于单输入系统， $j { = } 1$ ，系统正常与系统可控彼此等价。

# (4) Bang-Bang 控制原理

对于线性定常系统，若系统正常，则可应用极小值原理求解时间最优控制问题，其最优控制在容许控制域内，从一个边界值来回切换到另一个边界值，形成 Bang-Bang 控制特色。其主要结果可以归纳为如下定理。

定理 10-17 对于问题 10-1，若系统(10-74)正常，则最优解的必要条件为

1) 正则方程

$$
\dot {\boldsymbol {x}} (t) = \frac {\partial H}{\partial \boldsymbol {\lambda}} = \boldsymbol {A} \boldsymbol {x} (t) + \boldsymbol {B} \boldsymbol {u} (t)
$$

$$
\dot {\boldsymbol {\lambda}} (t) = - \frac {\partial H}{\partial \boldsymbol {x}} = - \boldsymbol {A} ^ {\mathrm {T}} \boldsymbol {\lambda} (t)
$$

式中，哈密顿函数

$$
H (\boldsymbol {x}, \boldsymbol {u}, \boldsymbol {\lambda}) = 1 + \boldsymbol {\lambda} ^ {\mathrm {T}} (t) [ A \boldsymbol {x} (t) + B \boldsymbol {u} (t) ]
$$

2) 边界条件

$$
\boldsymbol {x} (0) = \boldsymbol {x} _ {0}, \quad \boldsymbol {x} \left(t _ {f}\right) = \mathbf {0}
$$

3) 极小值条件

$$
u _ {j} ^ {*} (t) = - \operatorname {s g n} \left(\boldsymbol {b} _ {j} ^ {\mathrm {T}} \boldsymbol {\lambda}\right) = \left\{ \begin{array}{l l} + 1, & \boldsymbol {b} _ {j} ^ {\mathrm {T}} \boldsymbol {\lambda} <   0 \\ - 1, & \boldsymbol {b} _ {j} ^ {\mathrm {T}} \boldsymbol {\lambda} > 0 \end{array} \quad (j = 1, 2, \dots , m) \right.
$$

式中， $\pmb { b } _ { j } \in \mathbf { R } ^ { n }$ ，为矩阵 $\pmb { B }$ 的列向量。

4) 沿最优轨线 $H$ 变化律

$$
H ^ {*} \left(t _ {f} ^ {*}\right) = 0
$$

例 10-11 设系统状态方程为

$$
\dot {x} _ {1} (t) = x _ {2} (t), \quad \dot {x} _ {2} (t) = u (t)
$$

边界条件为

$$
x _ {1} (0) = x _ {1 0}, \quad x _ {2} (0) = x _ {2 0}, \quad x _ {1} \left(t _ {f}\right) = x _ {2} \left(t _ {f}\right) = 0
$$

控制变量的不等式约束为 $\left| u ( t ) \right| \leqslant 1$ ，性能指标

$$
J = \int_ {0} ^ {t _ {f}} \mathrm {d} t = t _ {f}
$$

求最优控制 $u ^ { * } ( t )$ ，使 $J$ 极小。

解 本例为二次积分模型的最小时间控制问题。不难验证，系统可控，因而正常，故时间最优控制必为 Bang-Bang控制，可用极小值原理求解。构造哈密顿函数

$$
H = 1 + \lambda_ {1} x _ {2} + \lambda_ {2} u
$$

由定理 10-17 知，最优控制

$$
u ^ {*} (t) = - \operatorname {s g n} \big \{\lambda_ {2} (t) \big \} = \left\{ \begin{array}{l l} + 1, & \lambda_ {2} (t) <   0 \\ - 1, & \lambda_ {2} (t) > 0 \end{array} \right.
$$

由协态方程

$$
\lambda_ {1} (t) = - \frac {\partial H}{\partial x _ {1}} = 0, \quad \lambda_ {1} (t) = c _ {1}
$$

$$
\lambda_ {2} (t) = - \frac {\partial H}{\partial x _ {2}} = - \lambda_ {1} (t), \quad \lambda_ {2} (t) = - c _ {1} t + c _ {2}
$$

式中， $c _ { 1 }$ 和 $c _ { 2 }$ 为待定常数。

若令 $u ^ { * } = 1$ ，状态方程的解为

$$
\dot {x} _ {2} (t) = 1, \quad x _ {2} (t) = t + x _ {2 0}
$$

$$
\dot {x} _ {1} (t) = t + x _ {2 0}, \quad x _ {1} (t) = \frac {1}{2} t ^ {2} + x _ {2 0} t + x _ {1 0}
$$

在解 $\{ x _ { 1 } ( t ) , x _ { 2 } ( t ) \}$ 中，消去 t，求得相应的最优轨线方程

$$
x _ {1} = \frac {1}{2} x _ {2} ^ {2} + \left(x _ {1 0} - \frac {1}{2} x _ {2 0}\right)
$$

上式表示一簇抛物线，如图 10-5 中实线所示。图中曲线上的箭头表示时间 $t$ 的增加方向，由于 $x _ { 2 } ( t ) = t + x _ { 2 0 }$ ，故 $x _ { 2 } ( t )$ 随 $t$ 的增加而增大。显然，满足末态要求的最优轨线为 $\widehat { A O }$ ，表示为

$$
\gamma_ {+} = \left\{\left(x _ {1}, x _ {2}\right) \mid x _ {1} = \frac {1}{2} x _ {2} ^ {2}, x _ {2} \leqslant 0 \right\} \tag {10-87}
$$

若令 $u ^ { * } = - 1$ ，状态方程的解为

$$
\dot {x} _ {2} (t) = - 1, \quad x _ {2} (t) = - t + x _ {2 0}
$$

$$
\dot {x} _ {1} (t) = - t + x _ {2 0}, \quad x _ {1} (t) = - \frac {1}{2} t ^ {2} + x _ {2 0} t + x _ {1 0}
$$

相应的最优轨线方程为

$$
x _ {1} = - \frac {1}{2} x _ {2} ^ {2} + \left(x _ {1 0} + \frac {1}{2} x _ {2 0}\right)
$$

上式也描绘了一簇抛物线，如图 10-5中虚线所示。显然满足末态要求的最优轨线为 $\widehat { B O }$ ，可以表示为

$$
\gamma_ {-} = \left\{\left(x _ {1}, x _ {2}\right) \mid x _ {1} = - \frac {1}{2} x _ {2} ^ {2}, \quad x _ {2} \geqslant 0 \right\} \tag {10-88}
$$

![](images/62e9527dd4357e9c7d9f71cb2a5bd7b59996adeb54d8b465b84a8521ae15ae40.jpg)  
图 10-5 时间最优控制的最优轨线

![](images/475fae5e89a94e302dc272007275c1e1f9e8812e68cc54ea6bcbc7db92286ffd.jpg)  
图 10-6 相平面上的开关曲线

曲线 $\gamma _ { + }$ 和 $\gamma _ { - }$ 在相平面上组合成曲线，称为开关曲线，如图 10-6 中 $\widehat { B O A }$ 所示。其表达式可由式(10-87)和式(10-88)导出为

$$
\gamma = \gamma_ {+} \cup \gamma_ {-} = \left\{\left(x _ {1}, x _ {2}\right) \mid x _ {1} = - \frac {1}{2} x _ {2} \left| x _ {2} \right| \right\} \tag {10-89}
$$

由图 10-6 可见，曲线将相平面分割为 $R _ { + }$ 和 $R _ { - }$ 两个区域，作为状态的集合，可以表示如下：

$$
R _ {+} = \left\{\left(x _ {1}, x _ {2}\right) \mid x _ {1} <   - \frac {1}{2} x _ {2} \mid x _ {2} \right\} \tag {10-90}
$$

$$
R _ {-} = \left\{\left(x _ {1}, x _ {2}\right) \mid x _ {1} > - \frac {1}{2} x _ {2} \mid x _ {2} \right\} \tag {10-91}
$$

当初始状态 $( x _ { 1 0 } , x _ { 2 0 } )$ 为不同情况时，系统的最优控制和运动轨线可以讨论如下：

1) 若 $( x _ { 1 0 } , x _ { 2 0 } )$ 位于 $\gamma _ { - }$ 上，则在 $u = - 1$ 作用下，沿 $\widehat { B O }$ 运动至要求的原点，此时最优控制为 $u ^ { * } ( t ) = - 1 , t \in [ 0 , t _ { f } ]$ 。  
2) 若 $( x _ { 1 0 } , x _ { 2 0 } )$ 位于 $\gamma _ { + }$ 上，则在 $u = + 1$ 作用下，沿 $\widehat { A O }$ 运动至要求的原点，此时最优控制为 $u ^ { * } ( t ) = + 1 , t \in [ 0 , t _ { f } ]$ 。  
3) 若 $( x _ { 1 0 } , x _ { 2 0 } )$ 位于 $R _ { + }$ 区域，则状态转移分两段进行。首先，在 $u = + 1$ 作用下，沿 $u = + 1$ 的某一条抛物线转移至 $\widehat { B O }$ 上的某点，然后在交点处控制改变为 $u = - 1$ 沿 $\gamma _ { - }$ 转移至原点。此时，最优控制 $u ^ { * } ( t ) = \{ + 1 , - 1 \}$ ，控制作用在 $\gamma _ { - }$ 曲线的交点处产生一次切换。  
4) 若 $( x _ { 1 0 } , x _ { 2 0 } )$ 位于 $R _ { - }$ 区域，则在 $u = - 1$ 作用下，沿 $u = - 1$ 的某一条抛物线转移至 $\gamma _ { + }$ 曲线上的某一点，然后在交点处控制改变为 $u = + 1$ ，沿 $\gamma _ { + }$ 转移至原点。此时，最优控制$u ^ { * } = \{ - 1 , + 1 \}$ ，控制作用在 $\gamma _ { + }$ 曲线的交点处产生一次切换。

由上述讨论可见，不论初始状态位于 $R _ { + }$ 区域或 $R _ { - }$ 区域，将状态由已知初态向要求末态 $\boldsymbol { x } ( t _ { f } ) = \mathbf { 0 }$ 转移时，都必须在 $\gamma$ 曲线上改变控制的符号，产生控制切换，故式(10-89)表示的 $\gamma$ 曲线称为开关曲线。于是，本例的时间最优控制为

$$
u ^ {*} (t) = \left\{ \begin{array}{l l} + 1, & \quad \forall (x _ {1}, x _ {2}) \in \boldsymbol {\gamma} _ {+} \bigcup R _ {+} \\ - 1, & \quad \forall (x _ {1}, x _ {2}) \in \boldsymbol {\gamma} _ {-} \bigcup R _ {-} \end{array} \right.
$$

# 10-4 线性二次型问题的最优控制

如果所研究的系统是线性的，且性能指标为状态变量和控制变量的二次型函数，则最优控制问题称为线性二次型问题。由于线性二次型问题的最优解具有统一的解析表达式，且可导致一个简单的线性状态反馈控制律，易于构成闭环最优反馈控制，便于工程实现，因而在实际工程问题中得到了广泛应用。

# 1. 线性二次型问题

设线性时变系统的动态方程为

$$
\begin{array}{l} \dot {\boldsymbol {x}} (t) = \boldsymbol {A} (t) \boldsymbol {x} (t) + \boldsymbol {B} (t) \boldsymbol {u} (t), \quad \boldsymbol {x} \left(t _ {0}\right) = \boldsymbol {x} _ {0} \tag {10-92} \\ \boldsymbol {y} (t) = \boldsymbol {C} (t) \boldsymbol {x} (t) \\ \end{array}
$$

性能指标为

$$
J = \frac {1}{2} \boldsymbol {e} ^ {\mathrm {T}} \left(t _ {f}\right) \boldsymbol {F} \boldsymbol {e} \left(t _ {f}\right) + \frac {1}{2} \int_ {t _ {0}} ^ {t _ {f}} \left[ \boldsymbol {e} ^ {\mathrm {T}} (t) \boldsymbol {Q} (t) \boldsymbol {e} (t) + \boldsymbol {u} ^ {\mathrm {T}} (t) \boldsymbol {R} (t) \boldsymbol {u} (t) \right] \mathrm {d} t \tag {10-93}
$$

式中， $\ b { x } ( t ) \in \mathbf { R } ^ { n }$ ； $\pmb { u } ( t ) \in \mathbf { R } ^ { m }$ ，无约束； $\mathbf { \boldsymbol { y } } ( t ) \in \mathbf { \boldsymbol { \mathbf { R } } } ^ { l }$ ， $0 < l \leqslant m \leqslant n$ ；输出误差向量$\pmb { e } ( t ) = z ( t ) - \pmb { y } ( t ) ; z ( t ) \in \mathbf { R } ^ { l }$ ，为理想输出向量； $A ( t ) \ : , \ : B ( t ) \ : , \ : C ( t )$ $A ( t )$ 为维数适当的时变矩阵，其各元连续且有界；权阵 $\pmb { F } = \pmb { F } ^ { \mathrm { T } } \geqslant \pmb { 0 }$ ， $Q ( t ) = Q ^ { \mathrm { { T } } } ( t ) \geqslant 0$ ， $\pmb { R } ( t ) = \pmb { R } ^ { \mathrm { T } } ( t ) > 0$ ； $t _ { 0 }$ 及 $t _ { f }$ 固定。要求确定最优控制 $u ^ { * } ( t )$ ，使性能指标(10-93)极小。

在今后讨论中，若非特别指出，以上假设始终满足。为了便于工程应用，式(10-93)中的权阵 $F _ { \mathrm { { ; } } }$ ， $\mathbf { } Q ( t )$ 和 $\pmb { R } ( t )$ 多取为对角阵，则其对称性自然满足。

在二次型指标(10-93)中，其各项都有明确的物理含义，可分述如下：

1) 末值项 $\frac { 1 } { 2 } e ^ { \mathrm { T } } ( t _ { f } ) F e ( t _ { f } )$ 。若取 $\pmb { F } = \mathrm { d i a g } ( f _ { 1 } , f _ { 2 } , \cdots , f _ { l } )$ ，则有

$$
\frac {1}{2} \boldsymbol {e} ^ {\mathrm {T}} \left(t _ {f}\right) \boldsymbol {F e} \left(t _ {f}\right) = \frac {1}{2} \sum_ {i = 1} ^ {l} f _ {i} e _ {i} ^ {2} \left(t _ {f}\right)
$$

上式表明，末值项是末态跟踪误差向量 $e ( t _ { f } )$ 与希望的零向量之间的距离加权平方和。式中，系数 1/2 是为了便于运算， $e _ { i } ( t _ { f } )$ 为 $e ( t _ { f } )$ 的变量。

由此可见，末值项的物理含义是表示在控制过程结束后，对系统末态跟踪误差的要求。

2) 积分项 $\frac { 1 } { 2 } \int _ { t _ { 0 } } ^ { t _ { f } } \pmb { e } ^ { \operatorname { T } } ( t ) \pmb { Q } ( t ) e ( t ) \mathrm { d } t$ 。若取 $\pmb { Q } ( t ) = \mathrm { d i a g } \{ q _ { 1 } ( t ) , q _ { 2 } ( t ) , \cdots , q _ { l } ( t ) \}$ ，则有

$$
\frac {1}{2} \int_ {t _ {0}} ^ {t _ {f}} e ^ {\mathrm {T}} (t) Q (t) e (t) d t = \frac {1}{2} \int_ {t _ {0}} ^ {t _ {f}} \sum_ {i = 1} ^ {l} q _ {i} (t) e _ {i} ^ {2} (t) d t
$$

上式表明，该积分项表示在系统控制过程中，对系统动态跟踪误差加权平方和的积分要求，是系统在控制过程中动态跟踪误差的总度量，几何上以面积大小表示。该积分项与末值项反映了系统的控制效果。

3) 积分项 $\frac { 1 } { 2 } \int _ { t _ { 0 } } ^ { t _ { f } } \pmb { u } ^ { \mathrm { T } } ( t ) \pmb { R } ( t ) \pmb { u } ( t ) \mathrm { d } t$ 。若取 $\pmb { R } ( t ) = \mathrm { d i a g } \{ r _ { 1 } ( t ) , r _ { 2 } ( t ) , \cdots , r _ { m } ( t ) \}$ ，则有

$$
\frac {1}{2} \int_ {t _ {0}} ^ {t _ {f}} \boldsymbol {u} ^ {\mathrm {T}} (t) \boldsymbol {R} (t) \boldsymbol {u} (t) \mathrm {d} t = \frac {1}{2} \int_ {t _ {0}} ^ {t _ {f}} \sum_ {i = 1} ^ {m} r _ {i} (t) u _ {i} ^ {2} (t) \mathrm {d} t
$$

因为控制信号的大小往往正比于作用力或力矩，所以上式表明，该积分项定量地刻画了在整个控制过程中所消耗的控制能量。

上述分析表明，使二次型指标(10-93)极小的物理意义是：使系统在整个控制过程中的动态跟踪误差与控制能量消耗，以及控制过程结束时的末端跟踪偏差综合最优。

从性能指标的物理意义可知，式(10-93)中权矩阵 ${ \pmb F }$ ， $Q ( t ) R ( t )$ 都必须至少取为非负矩阵，不能取为负定矩阵，否则性能指标(10-93)的数学描述就会违背物理现实和最优控制问题的本质。至于要求权矩阵 $\pmb { R } ( t )$ 正定，那是由于最优控制律的需要，以保证最优解的存在。

线性二次型最优控制问题有如下几种类型：

# (1) 状态调节器问题

在系统方程(10-92)和二次型性能指标(10-93)中，如果 $\mathbf { } C ( t ) = I$ ， $z ( t ) = \mathbf { 0 }$ ，则有

$$
\boldsymbol {e} (t) = - \boldsymbol {y} (t) = - \boldsymbol {x} (t)
$$

从而性能指标(10-93)演变为

$$
J = \frac {1}{2} \boldsymbol {x} ^ {\mathrm {T}} \left(t _ {f}\right) \boldsymbol {F} \boldsymbol {x} \left(t _ {f}\right) + \frac {1}{2} \int_ {t _ {0}} ^ {t _ {f}} \left[ \boldsymbol {x} ^ {\mathrm {T}} (t) \boldsymbol {Q} (t) \boldsymbol {x} (t) + \boldsymbol {u} ^ {\mathrm {T}} (t) \boldsymbol {R} (t) \boldsymbol {u} (t) \right] \mathrm {d} t \tag {10-94}
$$

这时，线性二次型最优控制问题为：当系统(10-92)受扰偏离原零平衡状态时，要求产生一控制向量，使系统状态 $\mathbf { } x ( t )$ 恢复到原平衡状态附近，并使性能指标(10-94)极小。因而，称为状态调节器问题。

# (2) 输出调节器问题

对于系统方程(10-92)和性能指标(10-93)，如果理想输出向量 $z ( t ) = \mathbf { 0 }$ ，则有$e ( t ) = - y ( t )$ 。从而，性能指标(10-93)演变为

$$
J = \frac {1}{2} \mathbf {y} ^ {\mathrm {T}} \left(t _ {f}\right) \mathbf {F} \mathbf {y} \left(t _ {f}\right) + \frac {1}{2} \int_ {t _ {0}} ^ {t _ {f}} \left[ \mathbf {y} ^ {\mathrm {T}} (t) \mathbf {Q} (t) \mathbf {y} (t) + \mathbf {u} ^ {\mathrm {T}} (t) \mathbf {R} (t) \mathbf {u} (t) \right] \mathrm {d} t \tag {10-95}
$$

这时，线性二次型最优控制问题为：当系统(10-92)受扰偏离原输出平衡状态时，要求产生一控制向量，使系统输出 $y ( t )$ 保持在原零平衡状态附近，并使性能指标(10-95)极小。因而，称为输出调节器问题。

# (3) 输出跟踪系统问题

对于系统方程(10-92)和性能指标(10-93)，其中 $\begin{array} { r } { \pmb { C } ( t ) \neq \pmb { I } , } \end{array}$ ， $z ( t ) \neq \mathbf { 0 }$ ，则线性二次型最优控制问题归结为：当理想输出向量 $z ( t )$ 作用于系统时，要求系统产生一控制向量，使系统实际输出向量 $y ( t )$ 始终跟踪 $z ( t )$ 的变化，并使性能指标(10-93)极小。因而，这一类线性二次型最优控制问题称为输出跟踪系统问题。

此外，根据不同的出发点，线性二次型最优控制问题还有其他的分类方法。例如，根据末端时刻 $t _ { f }$ 是有限或无限，可以分为有限时间线性二次型问题和无限时间线性二次型问题；根据被控系统是连续的还是离散的，可以分为线性连续系统二次型最优控制问题和线性离散系统二次型最优控制问题。

由于线性离散二次型最优控制方法原则上是线性连续二次型最优控制方法的平行推广，因此我们仅讨论连续系统的线性二次型最优控制问题。

# 2. 有限时间时变状态调节器

当末端时刻 $t _ { f }$ 有限时，有限时间时变状态调节器问题可以描述如下：

问题 10-2 设线性时变系统状态方程为

$$
\dot {\boldsymbol {x}} (t) = \boldsymbol {A} (t) \boldsymbol {x} (t) + \boldsymbol {B} (t) \boldsymbol {u} (t), \quad \boldsymbol {x} \left(t _ {0}\right) = \boldsymbol {x} _ {0} \tag {10-96}
$$

式中， $\ b { x } ( t ) \in \mathbf { R } ^ { n }$ ； $\pmb { u } ( t ) \in \mathbf { R } ^ { m }$ ，无约束；矩阵 $\mathbf { } A ( t )$ 与 $\pmb { B } ( t )$ 维数适当，其各元在 $[ t _ { 0 } , t _ { f } ]$ 上连续且有界。要求确定最优控制 $\pmb { u } ^ { * } ( t )$ ，使性能指标(10-94)极小。其中，权阵 $\pmb { F } = \pmb { F } ^ { \mathrm { T } } \geqslant \pmb { 0 }$ ，$Q ( t ) = Q ^ { \mathrm { T } } ( t ) \geqslant 0$ ， $\pmb { R } ( t ) = \pmb { R } ^ { \mathrm { T } } ( t ) > 0$ ，其各元在 $[ t _ { 0 } , t _ { f } ]$ 上均连续且有界；末端状态 $ { \boldsymbol { { x } } } ( t _ { f } )$ 自由；末端时刻 $t _ { f }$ 给定且有限。

# (1) 最优解的充分必要条件

定理 10-18 对于问题 10-2，其最优控制的充分必要条件为

$$
\boldsymbol {u} ^ {*} (t) = - \boldsymbol {R} ^ {- 1} (t) \boldsymbol {B} ^ {\mathrm {T}} (t) \boldsymbol {P} (t) \boldsymbol {x} (t) \tag {10-97}
$$

最优性能指标

$$
J ^ {*} = \frac {1}{2} \boldsymbol {x} ^ {\mathrm {T}} \left(t _ {0}\right) \boldsymbol {P} \left(t _ {0}\right) \boldsymbol {x} \left(t _ {0}\right) \tag {10-98}
$$

式中， $P ( t )$ 为 $n { \times } n$ 对称非负矩阵，满足下列里卡蒂矩阵微分方程：

$$
- \dot {\boldsymbol {P}} (t) = \boldsymbol {P} (t) \boldsymbol {A} (t) + \boldsymbol {A} ^ {\mathrm {T}} (t) \boldsymbol {P} (t) - \boldsymbol {P} (t) \boldsymbol {B} (t) \boldsymbol {R} ^ {- 1} \boldsymbol {B} ^ {\mathrm {T}} (t) \boldsymbol {P} (t) + \boldsymbol {Q} (t) \tag {10-99}
$$

其边界条件

$$
\boldsymbol {P} \left(t _ {f}\right) = \boldsymbol {F} \tag {10-100}
$$

而最优轨线 $\boldsymbol { x } ^ { * } ( t )$ ，则是下列线性向量微分方程的解：

$$
\dot {\boldsymbol {x}} (t) = \left[ \boldsymbol {A} (t) - \boldsymbol {B} (t) \boldsymbol {R} ^ {- 1} (t) \boldsymbol {B} ^ {\mathrm {T}} (t) \boldsymbol {P} (t) \right] \boldsymbol {x} (t), \quad \boldsymbol {x} \left(t _ {0}\right) = \boldsymbol {x} _ {0} \tag {10-101}
$$

证明 必要性：若 $\pmb { u } ^ { * } ( t )$ 为最优控制，可证式(10-97)成立。

因 ${ \pmb u } ^ { * } ( t )$ 最优，故必满足极小值原理。构造哈密顿函数

$$
H = \frac {1}{2} \boldsymbol {x} ^ {\mathrm {T}} \boldsymbol {Q} \boldsymbol {x} + \frac {1}{2} \boldsymbol {u} ^ {\mathrm {T}} \boldsymbol {R} \boldsymbol {u} + \lambda^ {\mathrm {T}} \boldsymbol {A} \boldsymbol {x} + \lambda^ {\mathrm {T}} \boldsymbol {B} \boldsymbol {u}
$$

由极值条件

$$
\frac {\partial H}{\partial \boldsymbol {u}} = \boldsymbol {R} \boldsymbol {u} + \boldsymbol {B} ^ {\mathrm {T}} \boldsymbol {\lambda} = \boldsymbol {0}, \quad \frac {\partial^ {2} H}{\partial \boldsymbol {u} ^ {2}} = \boldsymbol {R} > \boldsymbol {0}
$$

故

$$
\boldsymbol {u} ^ {*} (t) = - \boldsymbol {R} ^ {- 1} \boldsymbol {B} ^ {\mathrm {T}} \boldsymbol {\lambda} (t) \tag {10-102}
$$

可使哈密顿函数极小。再由正则方程

$$
\dot {\boldsymbol {x}} (t) = \frac {\partial H}{\partial \boldsymbol {\lambda}} = \boldsymbol {A} (t) \boldsymbol {x} (t) - \boldsymbol {B} (t) \boldsymbol {R} ^ {- 1} (t) \boldsymbol {B} ^ {\mathrm {T}} (t) \boldsymbol {\lambda} (t) \tag {10-103}
$$

$$
\dot {\boldsymbol {\lambda}} (t) = - \frac {\partial H}{\partial \boldsymbol {x}} = - \boldsymbol {Q} (t) \boldsymbol {x} (t) - \boldsymbol {A} ^ {\mathrm {T}} (t) \boldsymbol {\lambda} (t) \tag {10-104}
$$

因末态 $ { \boldsymbol { { x } } } ( t _ { f } )$ 自由，所以横截条件为

$$
\boldsymbol {\lambda} \left(t _ {f}\right) = \frac {\partial}{\partial \boldsymbol {x} \left(t _ {f}\right)} \left[ \frac {1}{2} \boldsymbol {x} ^ {\mathrm {T}} \left(t _ {f}\right) \boldsymbol {F} \boldsymbol {x} \left(t _ {f}\right) \right] = \boldsymbol {F} \boldsymbol {x} \left(t _ {f}\right) \tag {10-105}
$$

由于在式(10-105)中， $\lambda ( t _ { f } )$ 与 $ { \boldsymbol { { x } } } ( t _ { f } )$ 存在线性关系，且正则方程又是线性的，因此可以假设

$$
\boldsymbol {\lambda} (t) = \boldsymbol {P} (t) \boldsymbol {x} (t), \quad \forall t \in \left[ t _ {0}, t _ {f} \right] \tag {10-106}
$$

式中矩阵 $\pmb { P } ( t )$ 待定。对上式求导，得

$$
\dot {\boldsymbol {\lambda}} (t) = \dot {\boldsymbol {P}} (t) \boldsymbol {x} (t) + \boldsymbol {P} (t) \dot {\boldsymbol {x}} (t) \tag {10-107}
$$

将式(10-103)和式(10-106)代入式(10-107)，有

$$
\dot {\boldsymbol {\lambda}} (t) = \left[ \dot {\boldsymbol {P}} (t) + \boldsymbol {P} (t) \boldsymbol {A} (t) - \boldsymbol {P} (t) \boldsymbol {B} (t) \boldsymbol {R} ^ {- 1} (t) \boldsymbol {B} ^ {\mathrm {T}} (t) \boldsymbol {P} (t) \right] \boldsymbol {x} (t) \tag {10-108}
$$

将式(10-106)代入式(10-104)，则又有

$$
\dot {\boldsymbol {\lambda}} (t) = - \left[ \boldsymbol {Q} (t) + \boldsymbol {A} ^ {\mathrm {T}} (t) \boldsymbol {P} (t) \right] \boldsymbol {x} (t) \tag {10-109}
$$

比较式(10-108)和式(10-109)，立即证得里卡蒂方程(10-99)成立。

在式(10-106)中，令 $t = t _ { f }$ ，有

$$
\boldsymbol {\lambda} \left(t _ {f}\right) = \boldsymbol {P} \left(t _ {f}\right). \boldsymbol {x} \left(t _ {f}\right)
$$

上式与横截条件式(10-105)比较，证得里卡蒂方程的边界条件式(10-100)成立。

因 $P ( t )$ 可解，将式(10-106)代入式(10-102)，证得 $\pmb { u } ^ { * } ( t )$ 表达式(10-97)。

显然，将式(10-97)代入式(10-96)，得式(10-101)最优闭环系统方程，其解必为最优轨线 $x ^ { * } ( t )$ 。

充分性：若式(10-97)成立，可证 $\pmb { u } ^ { * } ( t )$ 必为最优控制。

根据连续动态规划法，可以方便地证明最优控制的充分性及最优性能指标(10-98)成立。其证明过程略。

在上述定理的证明过程中，应用了里卡蒂方程解的有关性质，需要加以说明。

# (2) 里卡蒂方程解的若干性质

在式(10-97)中，令反馈增益矩阵

$$
\boldsymbol {K} (t) = \boldsymbol {R} ^ {- 1} (t) \boldsymbol {B} ^ {\mathrm {T}} (t) \boldsymbol {P} (t) \tag {10-110}
$$

则最优控制可表示为

$$
\boldsymbol {u} ^ {*} (t) = - \boldsymbol {K} (t) \boldsymbol {x} (t) \tag {10-111}
$$

将上式代入式(10-96)，得最优闭环系统方程

$$
\dot {\boldsymbol {x}} (t) = \left[ \boldsymbol {A} (t) - \boldsymbol {B} (t) \boldsymbol {K} (t) \right] \boldsymbol {x} (t), \quad \boldsymbol {x} \left(t _ {0}\right) = \boldsymbol {x} _ {0} \tag {10-112}
$$

因为矩阵 $\mathbf { } A ( t )$ ， $\pmb { { \cal B } } ( t )$ 及 $\pmb { R } ( t )$ 已知，故闭环系统的性质与 $\pmb { K } ( t )$ 密切相关，而 $\pmb { K } ( t )$ 的性质又取决于里卡蒂方程(10-99)在边界条件(10-100)下的解 $P ( t )$ 。

1) $P ( t )$ 是唯一的。矩阵 $P ( t )$ 是里卡蒂方程(10-99)在边界条件(10-100)下的解。而方程(10-99)实质上是 $n ( n { + } 1 ) / 2$ 个非线性标量微分方程组，当矩阵 $\mathbf { } A ( t )$ ， $\pmb { { \cal B } } ( t )$ ， $\pmb { R } ( t )$ 和 $Q ( t )$ 满足问题 10-2 的假设条件时，根据微分方程理论中解的存在性与唯一性定理知，在区间$[ t _ { 0 } , t _ { f } ]$ 上， $P ( t )$ 唯一存在。

# 2) $P ( t )$ 是对称的。

命题 10-1 若矩阵 $P ( t )$ 是里卡蒂方程(10-99)及其边界条件(10-100)的唯一解，则

$$
\boldsymbol {P} (t) = \boldsymbol {P} ^ {\mathrm {T}} (t) \tag {10-113}
$$

证明 对里卡蒂方程(10-99)及其边界条件(10-100)取转置，可得

$$
- \dot {\boldsymbol {P}} ^ {\mathrm {T}} (t) = \boldsymbol {A} ^ {\mathrm {T}} (t) \boldsymbol {P} ^ {\mathrm {T}} (t) + \boldsymbol {P} ^ {\mathrm {T}} (t) \boldsymbol {A} (t) - \boldsymbol {P} ^ {\mathrm {T}} (t) \boldsymbol {B} (t) \boldsymbol {R} ^ {- \mathrm {T}} (t) \boldsymbol {B} ^ {\mathrm {T}} (t) \boldsymbol {P} ^ {\mathrm {T}} (t) + \boldsymbol {Q} ^ {\mathrm {T}} (t) \tag {10-114}
$$

以及

$$
\boldsymbol {P} ^ {\mathrm {T}} \left(t _ {f}\right) = \boldsymbol {F} ^ {\mathrm {T}} \tag {10-115}
$$

因为 $\pmb { R } ( t ) = \pmb { R } ^ { \mathrm { T } } ( t )$ ， $Q ( t ) = Q ^ { \mathrm { T } } ( t )$ ， $\pmb { F } = \pmb { F } ^ { \mathrm { T } }$ ，于是式(10-114)及式(10-115)可写为

$$
- \dot {\boldsymbol {P}} ^ {\mathrm {T}} (t) = \boldsymbol {P} ^ {\mathrm {T}} (t) \boldsymbol {A} (t) + \boldsymbol {A} ^ {\mathrm {T}} (t) \boldsymbol {P} ^ {\mathrm {T}} (t) - \boldsymbol {P} ^ {\mathrm {T}} (t) \boldsymbol {B} (t) \boldsymbol {R} ^ {- 1} (t) \boldsymbol {B} ^ {\mathrm {T}} (t) \boldsymbol {P} ^ {\mathrm {T}} (t) + \boldsymbol {Q} ^ {\mathrm {T}} (t) \tag {10-116}
$$

$$
\boldsymbol {P} ^ {\mathrm {T}} \left(t _ {f}\right) = \boldsymbol {F} \tag {10-117}
$$

比较式(10-99)、式(10-100)与式(10-116)、式(10-117)可见， $P ( t )$ 与 $\pmb { P } ^ { \mathrm { T } } ( t )$ 是在同一边界条件下的同一矩阵微分方程的解。因为 $P ( t )$ 是唯一的，故式(10-113)必然成立。

3) $P ( t )$ 是非负的。

命题 10-2 对于性能指标(10-94)，如果在区间 $[ t _ { 0 } , t _ { f } ]$ 上，有 $F \geqslant \mathbf { 0 } \ , Q ( t ) \geqslant \mathbf { 0 } \ , R ( t ) > \mathbf { 0 }$ ，则对于任意的 $\pmb { u } ( t )$ 和相应的 $\mathbf { } x ( t )$ ，总有 $J [ { \pmb x } ( t ) , { \pmb u } ( t ) , t ] \geqslant 0$ 。

证明 由命题假设，二次型函数

$$
\boldsymbol {x} ^ {\mathrm {T}} \left(t _ {f}\right) \boldsymbol {F} \boldsymbol {x} \left(t _ {f}\right) \geqslant 0, \quad \boldsymbol {x} ^ {\mathrm {T}} (t) \boldsymbol {Q} (t) \boldsymbol {x} (t) \geqslant 0, \quad \boldsymbol {u} ^ {\mathrm {T}} (t) \boldsymbol {R} (t) \boldsymbol {u} (t) > 0
$$

从而，对任意的 $\pmb { u } ( t )$ 和相应的 $\mathbf { } x ( t )$ ，由式(10-94)描述的性能指标，总有

$$
J [ \boldsymbol {x} (t), \boldsymbol {u} (t), t ] \geqslant 0, \quad \forall t \in [ t _ {0}, t _ {f} ]
$$

命题 10-3 若矩阵 $P ( t )$ 是里卡蒂方程(10-99)及其边界条件(10-100)的唯一解，则

$$
\boldsymbol {P} (t) \geqslant \mathbf {0}, \quad \forall t \in \left[ t _ {0}, t _ {f} \right] \tag {10-118}
$$

证明 由命题 10-2，对任意的 $\pmb { u } ( t )$ 和相应的 $\mathbf { } x ( t )$ ，有

$$
J [ \boldsymbol {x} (t), \boldsymbol {u} (t), t ] \geqslant 0, \quad \forall t \in \left[ t _ {0}, t _ {f} \right]
$$

取 $\mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { }  \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { }  \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { }  \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { }  \mathbf \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf \mathbf { } \mathbf { } \mathbf { } \mathbf { } \mathbf \mathbf { } \mathbf { } \mathbf { } \mathbf \mathbf { } \mathbf { } \mathbf \mathbf { } \mathbf { } \mathbf \mathbf { } \mathbf \mathbf { } \mathbf { } \mathbf \mathbf { } \mathbf  \mathbf \mathbf { } \mathbf \mathbf { } \mathbf \mathbf { } \mathbf \mathbf $ ，命题 10-2 仍然成立。由定理 10-18 知，最优性能指标

$$
J ^ {*} [ \boldsymbol {x} (t), t ] = \frac {1}{2} \boldsymbol {x} ^ {\mathrm {T}} (t) \boldsymbol {P} (t) \boldsymbol {x} (t) \geqslant 0, \quad \forall t \in [ t _ {0}, t _ {f} ]
$$

则由二次型函数性质知，命题成立。

(3) 最优控制解的存在与唯一性

若问题 10-2 有最优控制解，该解必满足定理 10-18 的结论。可以证明，该解是存在且唯一的。

定理 10-19 在定理 10-18中，最优控制解

$$
\boldsymbol {u} (t) = - \boldsymbol {R} ^ {- 1} (t) \boldsymbol {B} ^ {\mathrm {T}} (t) \boldsymbol {P} (t) \boldsymbol {x} (t)
$$

存在且唯一。

证明 先证存在性：因 $P ( t )$ 存在且唯一，故 $\pmb { u } ^ { * } ( t )$ 存在。再证唯一性：反设 ${ \pmb u } ^ { * } ( t )$ 不唯一，不失一般性，令 ${ \pmb u } _ { 1 } ^ { * } ( t )$ 和 ${ \pmb u } _ { 2 } ^ { * } ( t )$ 均为最优控制解，则由 $P ( t )$ 的唯一性可知

$$
\boldsymbol {u} _ {1} ^ {*} (t) = - \boldsymbol {R} ^ {- 1} (t) \boldsymbol {B} ^ {\mathrm {T}} (t) \boldsymbol {P} (t) \boldsymbol {x} _ {1} (t), \quad \boldsymbol {u} _ {2} ^ {*} (t) = - \boldsymbol {R} ^ {- 1} (t) \boldsymbol {B} ^ {\mathrm {T}} (t) \boldsymbol {P} (t) \boldsymbol {x} _ {2} (t)
$$

相应的闭环系统方程(10-101)为

$$
\dot {\boldsymbol {x}} _ {1} ^ {*} (t) = \left[ \boldsymbol {A} (t) - \boldsymbol {B} (t) \boldsymbol {R} ^ {- 1} (t) \boldsymbol {B} ^ {\mathrm {T}} (t) \boldsymbol {P} (t) \right] \boldsymbol {x} _ {1} ^ {*} (t), \quad \boldsymbol {x} _ {1} ^ {*} (t _ {0}) = \boldsymbol {x} _ {0}
$$

$$
\dot {\boldsymbol {x}} _ {2} ^ {*} (t) = \left[ \boldsymbol {A} (t) - \boldsymbol {B} (t) \boldsymbol {R} ^ {- 1} (t) \boldsymbol {B} ^ {\mathrm {T}} (t) \boldsymbol {P} (t) \right] \boldsymbol {x} _ {2} ^ {*} (t), \quad \boldsymbol {x} _ {2} ^ {*} \left(t _ {0}\right) = \boldsymbol {x} _ {0}
$$

可见，最优轨线 ${ \boldsymbol x } _ { 1 } ^ { * } ( t )$ 和 ${ \boldsymbol x } _ { 2 } ^ { * } ( t )$ 是同一向量微分方程且具有同样初始条件下的解。根据微分方程对初值问题解的唯一性，显然有

$$
\boldsymbol {x} _ {1} ^ {*} (t) = \boldsymbol {x} _ {2} ^ {*} (t), \quad \forall t \in \left[ t _ {0}, t _ {f} \right]
$$

从而必有 $\pmb { u } _ { 1 } ^ { * } ( t ) = \pmb { u } _ { 2 } ^ { * } ( t ) , \qquad \forall t \in \left[ t _ { 0 } , t _ { f } \right]$

唯一性得证。

例 10-12 设系统状态方程为

$$
\dot {x} _ {1} (t) = x _ {2} (t), \quad \dot {x} _ {2} (t) = u (t)
$$

初始条件为： $x _ { \mathrm { 1 } } ( 0 ) = 1$ ， $x _ { 2 } ( 0 ) = 0$ 。性能指标

$$
J = \frac {1}{2} \int_ {0} ^ {t _ {f}} \left[ x _ {1} ^ {2} (t) + u ^ {2} (t) \right] d t
$$

式中， $t _ { f }$ 为某一给定值。试求最优控制 $u ^ { * } ( t )$ ，使 $J = { \mathrm { m i n } }$ 。

解 本例为有限时间状态调节器问题。由题意：

$$
\boldsymbol {A} = \left[ \begin{array}{l l} 0 & 1 \\ 0 & 0 \end{array} \right], \quad \boldsymbol {b} = \left[ \begin{array}{l} 0 \\ 1 \end{array} \right], \quad \boldsymbol {F} = \mathbf {0}, \quad \boldsymbol {Q} = \left[ \begin{array}{l l} 1 & 0 \\ 0 & 0 \end{array} \right], \quad r = 1
$$

由里卡蒂方程

$$
- \dot {\boldsymbol {P}} = \boldsymbol {P} \boldsymbol {A} + \boldsymbol {A} ^ {\mathrm {T}} \boldsymbol {P} - \boldsymbol {P} b r ^ {- 1} \boldsymbol {b} ^ {\mathrm {T}} \boldsymbol {P} + \boldsymbol {Q}, \quad \boldsymbol {P} (t _ {f}) = \boldsymbol {F}
$$

代入相应的 $\pmb { A }$ ，b，Q，r，F，并令矩阵

$$
\boldsymbol {P} (t) = \left[ \begin{array}{c c} P _ {1 1} & P _ {1 2} \\ P _ {1 2} & P _ {2 2} \end{array} \right]
$$

可得下列微分方程组及相应的边界条件：

$$
\dot {P} _ {1 1} (t) = - 1 + P _ {1 2} ^ {2} (t), \quad P _ {1 1} \left(t _ {f}\right) = 0
$$

$$
\dot {P} _ {1 2} (t) = - P _ {1 1} (t) + P _ {1 2} (t) P _ {2 2} (t), \quad P _ {1 2} \left(t _ {f}\right) = 0
$$

$$
\dot {P} _ {2 2} (t) = - 2 P _ {1 2} (t) + P _ {2 2} ^ {2} (t), \quad \quad P _ {2 2} \left(t _ {f}\right) = 0
$$

利用计算机逆时间方向求解上述微分方程组，可以得到 $P ( t ) , t \in [ 0 , t _ { f } ]$ 。

最优控制

$$
u ^ {*} (t) = - r ^ {- 1} \boldsymbol {b} ^ {\mathrm {T}} \boldsymbol {P} \boldsymbol {x} (t) = - P _ {1 2} x _ {1} (t) - P _ {2 2} x _ {2} (t)
$$

式中， $P _ { 1 2 }$ 和 $P _ { 2 2 }$ 随时间变化曲线如图 10-7 所示。由于反馈系数 $P _ { 1 2 }$ 和 $P _ { 2 2 }$ 都是时变的，在设计系统时，需离线算出 $P _ { 1 2 }$ 和 $P _ { 2 2 }$ 的值，并存储于计算机内，以便实现控制时调用。

最优控制系统的结构图如图 10-8 所示。

![](images/53cbe877aa1739570a98e6f055065c1748dd9fccf0bba0cab30fc21049d41bbe.jpg)  
图 10-7 例 10-12 的里卡蒂方程解曲线(MATLAB)

![](images/8c9053f6a1139f92970ed6aae4a39439635936ab0259264ee5db4c16bffa03a0.jpg)  
图 10-8 例10-12的最优控制系统结构图

对于上述结论及例题求解过程，需要作如下几点说明：

1) 最优控制律(10-97)是一个线性状态反馈控制律，便于实现闭环最优控制。  
2) 里卡蒂方程(10-99)为非线性矩阵微分方程，通常只能采用计算机逆时间方向求数值解。由于里卡蒂方程与状态及控制变量无关，因而在定常系统情况下，可以离线算出$P ( t )$ 。  
3) 只要时间区间 $[ t _ { 0 } , t _ { f } ]$ 是有限的，里卡蒂方程的解 $P ( t )$ 就是时变的，最优反馈系统将成为线性时变系统，即使矩阵 $\pmb { A }$ 、 $\pmb { B }$ 、 $\pmb { Q }$ 和 $\pmb { R }$ 都是常值矩阵，求出的 $P ( t )$ 仍然是时变的。

# 3. 无限时间定常状态调节器

若系统受扰偏离原零平衡状态后，希望系统能最优地恢复到原平衡状态，不产生稳态误差，则必须采用无限时间状态调节器；若同时要求最优闭环系统渐近稳定，则应采用无限时间定常状态调节器，其最优状态反馈矩阵为常阵，可以离线计算，便于实时控制。

# (1) 问题描述

问题 10-3 设线性定常系统状态方程

$$
\dot {\boldsymbol {x}} (t) = \boldsymbol {A} \boldsymbol {x} (t) + \boldsymbol {B} \boldsymbol {u} (t), \quad \boldsymbol {x} (0) = \boldsymbol {x} _ {0} \tag {10-119}
$$

性能指标 $J = \frac { 1 } { 2 } { \int _ { 0 } ^ { \infty } } \Bigl [ { \pmb x } ^ { \mathrm { T } } ( t ) { \pmb Q } { \pmb x } ( t ) + { \pmb u } ^ { \mathrm { T } } ( t ) { \pmb R } { \pmb u } ( t ) \Bigr ] \mathrm { d } t$ (10-120)

式中， $\pmb { x } ( t ) \in \mathbf { R } ^ { n } \ ; \pmb { u } ( t ) \in \mathbf { R } ^ { m }$ $\ b { x } ( t ) \in \mathbf { R } ^ { n }$ ，无约束； ${ \mathbf { } } A , B , Q$ 和 $\pmb { R }$ 为维数适当的常值矩阵；权阵 $\pmb { Q } = \pmb { Q } ^ { \mathrm { T } } \geqslant \pmb { 0 }$ ，$\pmb { R } = \pmb { R } ^ { \mathrm { T } } > \mathbf { 0 }$ 。要求确定最优控制 ${ \pmb u } ^ { * } ( t )$ ，使性能指标(10-120)极小。

# (2) 最优解结果

定理 10-20 在问题 10-3 中，若对于任意矩阵 $\pmb { D }$ ，有 $\pmb { D } \pmb { D } ^ { \mathrm { T } } = \pmb { Q }$ ，且 $\bar { P }$ 是里卡蒂矩阵代数方程

$$
\bar {P} A + A ^ {\mathrm {T}} \bar {P} - \bar {P} B R ^ {- 1} B ^ {\mathrm {T}} \bar {P} + Q = 0
$$

的解，则阵对 $\{ A , D \}$ 完全可观的充分必要条件是 $\bar { P }$ 为对称正定矩阵。

定理 10-21 对于问题 10-3，若阵对 $\{ A , B \}$ 完全可控，阵对 $\{ A , D \}$ 完全可观，其中$\pmb { D } \pmb { D } ^ { \mathrm { T } } = \pmb { Q }$ ，且 $\pmb { D }$ 任意，则存在唯一的最优控制

$$
\boldsymbol {u} ^ {*} (t) = - \boldsymbol {R} ^ {- 1} \boldsymbol {B} ^ {\mathrm {T}} \bar {\boldsymbol {P}} \boldsymbol {x} (x) \tag {10-121}
$$

最优性能指标为

$$
J ^ {*} = \frac {1}{2} \boldsymbol {x} ^ {\mathrm {T}} (0) \bar {\boldsymbol {P}} \boldsymbol {x} (0) \tag {10-122}
$$

式中， $\bar { P }$ 为对称正定常阵，是里卡蒂矩阵代数方程

$$
\bar {P} A + A ^ {\mathrm {T}} \bar {P} - \bar {P} B R ^ {- 1} B ^ {\mathrm {T}} \bar {P} + Q = 0 \tag {10-123}
$$

的唯一解。

(3) 最优闭环系统的渐近稳定性

定理 10-22 对于问题 10-3，由定理 10-21 得到的最优闭环系统

$$
\dot {\boldsymbol {x}} (t) = \left(\boldsymbol {A} - \boldsymbol {B} \boldsymbol {R} ^ {- 1} \boldsymbol {B} ^ {\mathrm {T}} \bar {\boldsymbol {P}}\right) \boldsymbol {x} (t), \quad \boldsymbol {x} (0) = \boldsymbol {x} _ {0} \tag {10-124}
$$

必定是渐近稳定的。

证明 取二次型函数

$$
V (\boldsymbol {x}) = \boldsymbol {x} ^ {\mathrm {T}} (t) \bar {\boldsymbol {P}} \boldsymbol {x} (t) \tag {10-125}
$$

上式仅当 $\mathbf { \boldsymbol { x } } ( t ) = \mathbf { \boldsymbol { 0 } }$ 时，才有 $V ( \pmb { x } ) = 0$ ；对于非零 $\mathbf { } x ( t )$ ，由于 $\bar { P }$ 为对称正定常值矩阵，必有$V ( \pmb { x } ) \neq 0$ ；而且

$$
\lim  _ {\| x \| \rightarrow \infty} V (x) = \lim  _ {\| x \| \rightarrow \infty} x ^ {T} (t) \bar {P} x (t) \rightarrow \infty
$$

故式(10-125)表示的 $V ( x )$ 是一个李雅普诺夫函数。

取式(10-125)对时间 $t$ 的导数，得

$$
\dot {V} (\boldsymbol {x}) = \dot {\boldsymbol {x}} ^ {\mathrm {T}} (t) \bar {\boldsymbol {P}} \boldsymbol {x} (t) + \boldsymbol {x} ^ {\mathrm {T}} (t) \bar {\boldsymbol {P}} \dot {\boldsymbol {x}} (t)
$$

将式(10-119)及式(10-123)代入上式，可得

$$
\begin{array}{l} \dot {V} (\boldsymbol {x}) = \boldsymbol {x} ^ {\mathrm {T}} (t) \left[ \left(\boldsymbol {A} - \boldsymbol {B} \boldsymbol {R} ^ {- 1} \boldsymbol {B} ^ {\mathrm {T}} \bar {\boldsymbol {P}}\right) ^ {\mathrm {T}} \bar {\boldsymbol {P}} + \bar {\boldsymbol {P}} \left(\boldsymbol {A} - \boldsymbol {B} \boldsymbol {R} ^ {- 1} \boldsymbol {B} ^ {\mathrm {T}} \bar {\boldsymbol {P}}\right) \right] \boldsymbol {x} (t) \tag {10-126} \\ = - \boldsymbol {x} ^ {\mathrm {T}} (t) \left(\boldsymbol {Q} + \bar {\boldsymbol {P}} \boldsymbol {B} \boldsymbol {R} ^ {- 1} \boldsymbol {B} ^ {\mathrm {T}} \bar {\boldsymbol {P}}\right) \boldsymbol {x} (t) \\ \end{array}
$$

因 $\pmb { Q } \geqslant \pmb { 0 }$ ， $\pmb { R } > \mathbf { 0 }$ ，故有

$$
\dot {V} (\boldsymbol {x}) \leqslant 0
$$

显然，仅在 $\pmb { x } ( t ) = \pmb { x } _ { 0 } = \pmb { 0 }$ 的原平衡状态时，才有 $\dot { V } ( \pmb { x } ) = 0$ ，此外 $\dot { V } ( \boldsymbol { x } ) \neq 0$ 。反设对于非零 $\boldsymbol { x } _ { 0 }$ 有 $\dot { V } ( \boldsymbol { x } ) \equiv 0$ ，则由式(10-126)知，应有

$$
\boldsymbol {x} ^ {\mathrm {T}} (t) \boldsymbol {Q} \boldsymbol {x} (t) = 0 \tag {10-127}
$$

$$
\boldsymbol {x} ^ {\mathrm {T}} (t) \bar {\boldsymbol {P}} \boldsymbol {B} \boldsymbol {R} ^ {- 1} \boldsymbol {B} ^ {\mathrm {T}} \bar {\boldsymbol {P}} \boldsymbol {x} (t) = 0 \tag {10-128}
$$

将 $\pmb { u } ^ { * } ( t ) = - \pmb { R } ^ { - 1 } \pmb { B } ^ { \mathrm { T } } \pmb { \bar { P } } \pmb { x } ( t )$ 代入式(10-128)，得

$$
\boldsymbol {u} ^ {* \mathrm {T}} (t) \boldsymbol {R} \boldsymbol {u} ^ {*} (t) = 0
$$

由于 $\pmb { R } > \mathbf { 0 }$ ，故应有 $\pmb { u } ^ { * } ( t ) = \pmb { 0 }$ ，此时系统(10-119)只有零输入响应

$$
\boldsymbol {x} (t) = \mathrm {e} ^ {A t} \boldsymbol {x} _ {0}, \quad \forall \boldsymbol {x} _ {0} \neq \mathbf {0} \tag {10-129}
$$

将式(10-129)代入式(10-127)，可得

$$
\boldsymbol {x} _ {0} ^ {\mathrm {T}} \mathrm {e} ^ {\boldsymbol {A} ^ {\mathrm {T}} t} \boldsymbol {D} \boldsymbol {D} ^ {\mathrm {T}} \mathrm {e} ^ {\boldsymbol {A} t} \boldsymbol {x} _ {0} = 0
$$

式中， $\pmb { D } \pmb { D } ^ { \mathrm { T } } = \pmb { Q }$ 。上式表明

$$
\boldsymbol {D} ^ {\mathrm {T}} \mathrm {e} ^ {A t} \boldsymbol {x} _ {0} = \mathbf {0}, \quad \forall \boldsymbol {x} _ {0} \neq \mathbf {0}
$$

故 $\pmb { D } ^ { \mathrm { T } } \mathrm { e } ^ { \pmb { A } t }$ 列相关，这与 $\{ A , D \}$ 完全可观矛盾，反设不成立。

根据李雅普诺夫稳定性定理，系统(10-124)大范围渐近稳定。

对于以上主要结论，需作如下几点说明：

1) 在定理 10-21 中，对系统(10-119)提出的可控性要求，是为了保证最优解的存在。

在有限时间调节器问题中，对系统并无可控性要求，因为式(10-120)的积分上限 $t _ { f }$ 有限，无论系统可控与否，性能指标 $J$ 不会趋于无穷。但在 $t _ { f } \to \infty$ 时，当不可控状态不稳定，且又包含于性能指标 $J$ 之中时，便会使 $J \to \infty$ ，从而使最优解不存在。

例 10-13 设系统状态方程及初始条件为

$$
\dot {x} _ {1} (t) = x _ {1} (t), \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad x _ {1} (0) = 1
$$

$$
\dot {x} _ {2} (t) = x _ {2} (t) + u (t), \quad x _ {2} (0) = 0
$$

性能指标

$$
J = \frac {1}{2} \int_ {0} ^ {\infty} [ \boldsymbol {x} ^ {\mathrm {T}} (t) \boldsymbol {x} (t) + u ^ {2} (t) ] \mathrm {d} t
$$

试求最优控制 $u ^ { * } ( t )$ 及最优性能指标 $J ^ { * }$ 。

解 本例为无限时间定常状态调节器问题。由题意，状态 $x _ { \mathrm { 1 } } ( t )$ 显然不可控。因为系统矩阵及状态转移矩阵为

$$
\boldsymbol {A} = \left[ \begin{array}{c c} 1 & 0 \\ 0 & 1 \end{array} \right], \qquad \mathrm {e} ^ {\boldsymbol {A} t} = \mathcal {S} ^ {- 1} \left[ \left(\boldsymbol {s} \boldsymbol {I} - \boldsymbol {A}\right) ^ {- 1} \right] = \left[ \begin{array}{c c} \mathrm {e} ^ {t} & 0 \\ 0 & \mathrm {e} ^ {t} \end{array} \right]
$$

故系统的零输入响应

$$
\left[ \begin{array}{l} x _ {1} (t) \\ x _ {2} (t) \end{array} \right] = \mathrm {e} ^ {A t} \boldsymbol {x} (0) = \left[ \begin{array}{l} \mathrm {e} ^ {t} \\ 0 \end{array} \right]
$$

显然 $\operatorname* { l i m } _ { t \to \infty } x _ { 1 } ( t ) = \operatorname* { l i m } _ { t \to \infty } \mathbf { e } ^ { t } \to \infty$

性能指标 $J = \frac { 1 } { 2 } \int _ { 0 } ^ { \infty } \Bigl [ x ^ { \mathrm { \scriptscriptstyle T } } ( t ) x ( t ) + u ^ { 2 } ( t ) \Bigr ] \mathrm { d } t = \frac { 1 } { 2 } \int _ { 0 } ^ { \infty } \Bigl [ x _ { 1 } ^ { 2 } ( t ) + x _ { 2 } ^ { 2 } ( t ) + u ^ { 2 } ( t ) \Bigr ] \mathrm { d } t \to \infty$

因而本例不存在最优解。

2) 在定理 10-21中，要求阵对 $\{ A , D \}$ 完全可观，是为了保证最优闭环系统(10-124)渐近稳定性。如果强化性能指标中权阵 $Q$ 的条件，要求 $\pmb { Q } = \pmb { Q } ^ { \operatorname { T } } > \pmb { 0 }$ ，则可去掉 $\{ A , D \}$ 可观的要求。至于 $\bar { P }$ 矩阵的正定性，卡尔曼曾经指出：系统可控的假设和取权阵 $\scriptstyle { F = 0 }$ ，意味着 $t _ { f } \to \infty$ 时， $\bar { P }$ 为正定矩阵。  
3) 对于无限时间状态调节器，通常在性能指标中不考虑终点指标，取权阵 $\scriptstyle { F = 0 }$ ，其原因有二：一是希望 $t _ { f } \to \infty$ 时， $\boldsymbol { x } ( t _ { f } ) = \mathbf { 0 }$ ，即要求稳态误差为零，因而在性能指标中不必加入体现终点指标的末值项；二是工程上仅考虑系统在有限时间内的响应，因而$t _ { f } \to \infty$ 时的终点指标将失去工程意义。

例 10-14 设系统状态方程及初始条件为

$$
\dot {x} _ {1} (t) = u (t), \quad x _ {1} (0) = 0
$$

$$
\dot {x} _ {2} (t) = x _ {1} (t), \quad x _ {2} (0) = 1
$$

性能指标

$$
J = \int_ {0} ^ {\infty} \left[ x _ {2} ^ {2} (t) + \frac {1}{4} u ^ {2} (t) \right] d t
$$

试求最优控制 $u ^ { * } ( t )$ 和最优性能指标 $J ^ { * }$ 。

解 本例为无限时间状态调节器问题。因

$$
J = \frac {1}{2} \int_ {0} ^ {\infty} \left(2 x _ {2} ^ {2} + \frac {1}{2} u ^ {2}\right) d t = \frac {1}{2} \int_ {0} ^ {\infty} \left\{\left[ x _ {1}, x _ {2} \right] \left[ \begin{array}{l l} 0 & 0 \\ 0 & 2 \end{array} \right] \left[ \begin{array}{l} x _ {1} \\ x _ {2} \end{array} \right] + \frac {1}{2} u ^ {2} \right\} d t
$$

故由题意

$$
\boldsymbol {A} = \left[ \begin{array}{l l} 0 & 0 \\ 1 & 0 \end{array} \right], \quad \boldsymbol {b} = \left[ \begin{array}{l} 1 \\ 0 \end{array} \right], \quad \boldsymbol {Q} = \left[ \begin{array}{l l} 0 & 0 \\ 0 & 2 \end{array} \right], \quad r = \frac {1}{2}, \quad \boldsymbol {d} ^ {\mathrm {T}} = \left[ \begin{array}{l l} 0 & \sqrt {2} \end{array} \right]
$$

检验可控性与可观性：

$$
\operatorname {r a n k} \left[ \begin{array}{l l} \boldsymbol {b} & \boldsymbol {A b} \end{array} \right] = \operatorname {r a n k} \left[ \begin{array}{l l} 1 & 0 \\ 0 & 1 \end{array} \right] = 2
$$

$$
\operatorname {r a n k} \left[ \begin{array}{l} \boldsymbol {d} ^ {\mathrm {T}} \\ \boldsymbol {d} ^ {\mathrm {T}} \boldsymbol {A} \end{array} \right] = \operatorname {r a n k} \left[ \begin{array}{l l} 0 & \sqrt {2} \\ \sqrt {2} & 0 \end{array} \right] = 2
$$

故 $u ^ { * } ( t )$ 存在且最优闭环系统渐近稳定。

解里卡蒂方程：令

$$
\overline {{\boldsymbol {P}}} = \left[ \begin{array}{c c} P _ {1 1} & P _ {1 2} \\ P _ {1 2} & P _ {2 2} \end{array} \right]
$$

由 $\overline { { { P } } } A + A ^ { \mathrm { T } } \overline { { { P } } } - \overline { { { P } } } b r ^ { - 1 } b ^ { \mathrm { T } } \overline { { { P } } } + Q = { \bf 0 }$

得代数方程组

$$
2 P _ {1 2} - 2 P _ {1 1} ^ {2} = 0
$$

$$
P _ {2 2} - 2 P _ {1 1} P _ {1 2} = 0
$$

$$
- 2 P _ {1 2} ^ {2} + 2 = 0
$$

联立求解，得

$$
\overline {{\boldsymbol {P}}} = \left[ \begin{array}{c c} 1 & 1 \\ 1 & 2 \end{array} \right] > 0
$$

求最优解：

$$
u ^ {*} (t) = - r ^ {- 1} \boldsymbol {b} ^ {\mathrm {T}} \bar {\boldsymbol {P}} \boldsymbol {x} (t) = - 2 x _ {1} (t) - 2 x _ {2} (t)
$$

$$
J ^ {*} = \frac {1}{2} \boldsymbol {x} ^ {\mathrm {T}} (0) \bar {\boldsymbol {P}} \boldsymbol {x} (0) = 1
$$

检验闭环系统的稳定性：

$$
\dot {\boldsymbol {x}} (t) = (\boldsymbol {A} - \boldsymbol {b} r ^ {- 1} \boldsymbol {b} ^ {\mathrm {T}} \bar {\boldsymbol {P}}) \boldsymbol {x} (t) = \left[ \begin{array}{c c} - 2 & - 2 \\ 1 & 0 \end{array} \right] \boldsymbol {x} (t) = \bar {\boldsymbol {A}} \boldsymbol {x} (t)
$$

其特征方程为

$$
\begin{array}{l} \det  (\lambda I - \overline {{A}}) = \det  \left[ \begin{array}{c c} \lambda + 2 & 2 \\ - 1 & \lambda \end{array} \right] \\ = \lambda^ {2} + 2 \lambda + 2 = 0 \\ \end{array}
$$

求出特征值为 $\lambda _ { 1 } = - 1 + \mathrm { j }$ ， $\lambda _ { 2 } = - 1 - \mathrm { j }$ 。由特征值判据知，闭环系统渐近稳定。

# 4. 无限时间定常输出跟踪系统

对于无限时间输出跟踪系统问题，目前还没有严格的一般性求解方法。当理想输出为常值向量时，无限时间定常输出最优跟踪系统问题，有如下工程上可以应用的近似结果。

定理 10-23 设线性定常系统的动态方程为

$$
\dot {\boldsymbol {x}} (t) = \boldsymbol {A} \boldsymbol {x} (t) + \boldsymbol {B} \boldsymbol {u} (t), \quad \boldsymbol {x} (0) = \boldsymbol {x} _ {0} \tag {10-130}
$$

$$
\boldsymbol {y} (t) = \boldsymbol {C x} (t)
$$

式中， $\ b { x } ( t ) \in \mathbf { R } ^ { n }$ ； $\pmb { u } ( t ) \in \mathbf { R } ^ { m }$ ，无约束； $\mathbf { \boldsymbol { y } } ( t ) \in \mathbf { \boldsymbol { \mathbf { R } } } ^ { l }$ ， $0 < l \leqslant m \leqslant n$ ；A， $\pmb { B }$ ， $C$ 为维数适当的常值矩阵。

设 $\hat { z } \in \mathbf { R } ^ { l }$ 为理想输出常向量， $e ( t )$ 为输出误差向量，由

$$
\boldsymbol {e} (t) = \hat {\boldsymbol {z}} - \boldsymbol {y} (t) \tag {10-131}
$$

定义性能指标

$$
J = \frac {1}{2} \int_ {0} ^ {\infty} \left[ e ^ {\mathrm {T}} (t) Q e (t) + u ^ {\mathrm {T}} (t) R u (t) \right] \mathrm {d} t \tag {10-132}
$$

式中，权阵 $\pmb { Q }$ 和 $\pmb { R }$ 均为对称正定常值矩阵，维数适当。

若阵对 $\{ A , B \}$ 完全可控，阵对 $\{ A , C \}$ 完全可观，则使性能指标(10-132)极小的近似最优控制

$$
\hat {\boldsymbol {u}} ^ {*} (t) = - \boldsymbol {R} ^ {- 1} \boldsymbol {B} ^ {\mathrm {T}} \hat {\boldsymbol {P}} \boldsymbol {x} (t) + \boldsymbol {R} ^ {- 1} \boldsymbol {B} ^ {\mathrm {T}} \hat {\boldsymbol {g}} \tag {10-133}
$$

式中， $\hat { P }$ 为对称正定常阵，满足下列里卡蒂矩阵代数方程：

$$
\hat {\boldsymbol {P}} \boldsymbol {A} + \boldsymbol {A} ^ {\mathrm {T}} \hat {\boldsymbol {P}} - \hat {\boldsymbol {P}} \boldsymbol {B} \boldsymbol {R} ^ {- 1} \boldsymbol {B} ^ {\mathrm {T}} \hat {\boldsymbol {P}} + \boldsymbol {C} ^ {\mathrm {T}} \boldsymbol {Q} \boldsymbol {C} = \mathbf {0} \tag {10-134}
$$

常值伴随向量

$$
\hat {\boldsymbol {g}} = \left[ \hat {\boldsymbol {P}} \boldsymbol {B} \boldsymbol {R} ^ {- 1} \boldsymbol {B} ^ {\mathrm {T}} - \boldsymbol {A} ^ {\mathrm {T}} \right] ^ {- 1} \boldsymbol {C} ^ {\mathrm {T}} \boldsymbol {Q} \hat {\boldsymbol {z}} \tag {10-135}
$$

闭环系统方程

$$
\dot {\boldsymbol {x}} (t) = \left(\boldsymbol {A} - \boldsymbol {B} \boldsymbol {R} ^ {- 1} \boldsymbol {B} ^ {\mathrm {T}} \hat {\boldsymbol {P}}\right) \boldsymbol {x} (t) + \boldsymbol {B} \boldsymbol {R} ^ {- 1} \boldsymbol {B} ^ {\mathrm {T}} \hat {\boldsymbol {g}}, \quad \boldsymbol {x} (0) = \boldsymbol {x} _ {0} \tag {10-136}
$$

的解，为近似最优轨线 $\hat { \boldsymbol { x } } ^ { * } ( t )$ 。

应当指出，定理 10-23并没有论证闭环系统的稳定性，因此在实际应用时，需对闭环

系统的渐近稳定性加以检验。

例 10-15 有一理想化轮船操纵系统，其从激励信号 $u ( t )$ 到实际航向 $y ( t )$ 的传递函数为 $4 / s ^ { 2 }$ ，试设计近似最优激励信号 $\hat { u } ^ { * } ( t )$ ，使性能指标

$$
J = \int_ {0} ^ {\infty} \left\{\left[ \hat {z} - y (t) \right] ^ {2} + u ^ {2} (t) \right\} d t
$$

极小。式中， $\hat { z } = 1 ( t )$ 为理想输出。

解 本例为无限时间定常输出跟踪系统问题，可按如下步骤求解：

1) 系统状态空间建模。由于传递函数

$$
G (s) = \frac {Y (s)}{U (s)} = \frac {4}{s ^ {2}}
$$

可得 ${ \dot { x } } _ { 1 } ( t ) = x _ { 2 } ( t ) , { \dot { x } } _ { 2 } ( t ) = 4 u ( t ) , { \mathbf { \ } } y ( t ) = x _ { 1 } ( t )$

于是 $A = { \left[ \begin{array} { l l } { 0 } & { 1 } \\ { 0 } & { 0 } \end{array} \right] } , \quad \quad b = { \left[ \begin{array} { l } { 0 } \\ { 4 } \end{array} \right] } , \quad \quad c = { \left[ \begin{array} { l l } { 1 } & { 0 } \end{array} \right] }$

检验 1 24 G s s ( ) ( )     c I A b $G ( s ) = c ( s I - A ) ^ { - 1 } b = \frac 4 { s ^ { 2 } }$ 2

2) 检验可控性与可观性。性能指标又可表示为

$$
J = \frac {1}{2} \int_ {0} ^ {\infty} \left\{2 [ \hat {z} - y (t) ] ^ {2} + 2 u ^ {2} (t) \right\} d t
$$

故有 $r = q = 2 , \quad \quad { \boldsymbol { c } } ^ { \mathrm { T } } q { \boldsymbol { c } } = { \left[ \begin{array} { l l } { 2 } & { 0 } \\ { 0 } & { 0 } \end{array} \right] }$

$$
\operatorname {r a n k} [ \boldsymbol {b} \quad \boldsymbol {A} \boldsymbol {b} ] = \operatorname {r a n k} \left[ \begin{array}{l l} 0 & 4 \\ 4 & 0 \end{array} \right] = 2
$$

因为$\operatorname { r a n k } { \left[ \begin{array} { l } { c } \\ { c A } \end{array} \right] } = \operatorname { r a n k } { \left[ \begin{array} { l l } { 1 } & { 0 } \\ { 0 } & { 1 } \end{array} \right] } = 2$

故 $\{ A , b \}$ 可控， $\{ A , c \}$ 可观。

3) 解里卡蒂方程。令 ˆ  P $\hat { \pmb { P } } = \left[ \begin{array} { l l } { P _ { 1 1 } } & { P _ { 1 2 } } \\ { P _ { 1 2 } } & { P _ { 2 2 } } \end{array} \right]$ 11 12P P    ，由式(10-134)得

$$
- 8 P _ {1 2} ^ {2} + 2 = 0
$$

$$
P _ {1 1} - 8 P _ {1 2} P _ {2 2} = 0
$$

$$
2 P _ {1 2} - 8 P _ {2 2} ^ {2} = 0
$$

联立解出

$$
\hat {\boldsymbol {P}} = \left[ \begin{array}{c c} \sqrt {2} & \frac {1}{2} \\ \frac {1}{2} & \frac {\sqrt {2}}{4} \end{array} \right] > \mathbf {0}
$$

4) 求伴随常向量。

$$
\hat {\boldsymbol {g}} = \left(\hat {\boldsymbol {P}} \boldsymbol {b} r ^ {- 1} \boldsymbol {b} ^ {\mathrm {T}} - \boldsymbol {A} ^ {\mathrm {T}}\right) ^ {- 1} \boldsymbol {c} ^ {\mathrm {T}} q \hat {\boldsymbol {z}} = \left[ \begin{array}{l} \sqrt {2} \\ \frac {1}{2} \end{array} \right]
$$

5) 确定近似最优控制。

$$
\begin{array}{l} \hat {u} ^ {*} (t) = - r ^ {- 1} \boldsymbol {b} ^ {\mathrm {T}} \hat {\boldsymbol {P}} \boldsymbol {x} (t) + r ^ {- 1} \boldsymbol {b} ^ {\mathrm {T}} \hat {\boldsymbol {g}} \\ = - x _ {1} (t) - \frac {\sqrt {2}}{2} x _ {2} (t) + 1 = - y (t) - \frac {\sqrt {2}}{2} \dot {y} (t) + 1 \\ \end{array}
$$

6) 检验闭环输出跟踪系统的稳定性。闭环系统的系统矩阵为

$$
\overline {{A}} = \left(A - b r ^ {- 1} \boldsymbol {b} ^ {\mathrm {T}} \hat {\boldsymbol {P}}\right) = \left[ \begin{array}{c c} 0 & 1 \\ - 4 & - 2 \sqrt {2} \end{array} \right]
$$

特征方程

$$
\det  (\lambda I - \bar {A}) = \lambda^ {2} + 2 \sqrt {2} \lambda + 4 = 0
$$

解得特征值

$$
\lambda_ {1} = - \sqrt {2} + \mathrm {j} \sqrt {2}, \quad \lambda_ {2} = - \sqrt {2} - \mathrm {j} \sqrt {2}
$$

故闭环输出跟踪系统渐近稳定。

# 10-5 控制系统优化设计

工程系统的优化设计方法有多种，除线性二次型优化法以外，ITAE(integrated timeabsolute error)优化方法也是一种常用的方法。

例 10-16 PID 控制系统的优化设计。

在优化控制系统设计中，一种合适的性能指标是时间与绝对误差的乘积积分，称为ITAE性能指标，表示如下：

$$
\mathrm {I T A E} = \int_ {0} ^ {t _ {f}} t | e (t) | \mathrm {d} t \tag {10-137}
$$

选择 ITAE指标，是为了减小较大的初始误差对性能指标取值的影响，同时也是为了强调最近的响应的影响。

当所选的性能指标达到极小值时，控制系统称为是最优的。如果稳定系统的闭环传递函数具有如下的一般形式：

$$
\Phi (s) = \frac {Y (s)}{R (s)} = \frac {b _ {0}}{s ^ {n} + a _ {n - 1} s ^ {n - 1} + \cdots + a _ {1} s + a _ {0}} \tag {10-138}
$$

式中， $a _ { 0 } { = } b _ { 0 }$ ，则可以确定 $\phi \left( s \right)$ 的最优系数，使系统对阶跃响应的 ITAE 性能指标极小。式(10-138)传递函数有 $n$ 个极点，没有零点，而且系统对阶跃响应的稳态误差为零。

在高阶线性系统中，ITAE最优性能指标的几何意义是误差的广义面积极小，它也是多维相空间曲面上的一个极值，它的维数就是该方程所描述系统的状态数。显然，用解析法很难得到该极值，一般采用实验的方法来确定 $\phi ( s )$ 的最优系数。

为了减少计算的复杂程度，不妨采用标准化微分方程形式，这样可以把 $n$ 维空间降低 为 $n { - } 1$ 维。例如，对于标准化时间 $\omega _ { n } t$ ，标准二阶系统 $\phi ( s ) = \frac { \omega _ { n } ^ { 2 } } { s ^ { 2 } + \beta \omega _ { n } s + \omega _ { n } ^ { 2 } } =$

$\frac { \omega _ { n } ^ { 2 } } { s ^ { 2 } + 2 \zeta \omega _ { n } s + \omega _ { n } ^ { 2 } }$ 就只取决于参数 $\beta = 2 \zeta$ ，标准三阶系统 $\phi ( s ) = \frac { \omega _ { n } ^ { 3 } } { s ^ { 3 } + \beta _ { 2 } { \omega _ { n } } s ^ { 2 } + \beta _ { 1 } { \omega _ { n } ^ { 2 } } s + { \omega _ { n } ^ { 3 } } }$ 就只取决于 $\beta _ { \mathrm { { l } } }$ 和 $\beta _ { 2 }$ 两个系数，依此类推。这里仅以三阶标准化微分方程所描述的系统在单位阶跃输入作用下的 ITAE最优系数的确定方法为例，说明其基本实验原理。

不妨取 $\omega _ { n } = 1$ ，则标准三阶系统的微分方程为

$$
\ddot {y} + \beta_ {2} \dot {y} + \beta_ {1} \dot {y} + y = 1
$$

写成可控标准型形式

$$
\left[ \begin{array}{l} \dot {x} _ {1} \\ \dot {x} _ {2} \\ \dot {x} _ {3} \end{array} \right] = \left[ \begin{array}{c c c} 0 & 1 & 0 \\ 0 & 0 & 1 \\ - 1 & - \beta_ {1} & - \beta_ {2} \end{array} \right] \left[ \begin{array}{l} x _ {1} \\ x _ {2} \\ x _ {3} \end{array} \right] + \left[ \begin{array}{l} 0 \\ 0 \\ 1 \end{array} \right] u
$$

$$
y = \left[ \begin{array}{l l l} 1 & 0 & 0 \end{array} \right] \left[ \begin{array}{l} x _ {1} \\ x _ {2} \\ x _ {3} \end{array} \right]
$$

其对应的状态变量图如图 10-9 中虚框所示。

![](images/336e392ef7f79fc55dd815a245688cbe9d462d40b23e454afcb2e3a9515a1f9a.jpg)  
图 10-9 标准三阶系统可控标准型状态变量图及其 ITAE 指标实现

建立 ITAE最优性能指标

$$
\mathrm {I T A E} = \int_ {0} ^ {t _ {f}} t | e (t) | d t
$$

需要从图 10-9 中引出误差信号 $e ( t )$ 。显然

$$
e (t) = 1 - y (t) = \ddot {y} + \beta_ {2} \dot {y} + \beta_ {1} \dot {y}
$$

将 $e ( t )$ 取绝对值后与和 $t$ 一起输入乘法器，相乘结果累加就可得到 ITAE 积分泛函值 $J$ ，如图 10-9所示。

在实验中，每当给定一系数 $\beta _ { 2 } =$ const (或 $\beta _ { \mathrm { l } }$ )后，每次再改变另一系数 $\beta _ { \mathrm { l } }$ (或 $\beta _ { 2 }$ )，就可以得到一个相应的 $J = f ( { \boldsymbol { \beta } } _ { 1 } , { \boldsymbol { \beta } } _ { 2 } )$ 值，将这些 $J$ 值连成光滑曲线，可以得到图 10-10 所示

的曲线簇。这些曲线簇实际上是 $J - \beta _ { 1 } - \beta _ { 2 }$ 三维空间中同一个曲面在不同 $\beta _ { 2 } =$ const 值下的切面。给定不同的 $\beta _ { 2 }$ 值可得到不同的曲线簇。再根据这些切面的曲面簇可以得到它在$J - { \boldsymbol { \beta } } _ { 1 } - { \boldsymbol { \beta } } _ { 2 }$ 三维空间中的曲面，如图 10-11 所示，它的最佳系数就落在曲面的最底部。对于标准三阶系统，当 $\beta _ { \mathrm { 1 } } = 2 . 1 5$ ， $\beta _ { 2 } = 1 . 7 5$ 时， $J = \mathrm { I T A E } = \int _ { 0 } ^ { t _ { f } } t \big | e ( t ) \big | \mathrm { d } t = \mathrm { m i n }$ 。

![](images/24648f15ebf156e524bea9a69e50e406c97b759fb9fd6287e2049a0b7e800874.jpg)  
图 10-10 标准三阶系统满足ITAE最优指标的切面曲线簇

![](images/1acc69de9852aace264db41b033da629f759c74413d8492ef73e7a142e534c72.jpg)  
图 10-11 标准三阶系统满足ITAE最优指标的曲线

对于三阶以上的高阶系统，其实验原理基本一致，只是确定最佳系数的曲面为一超曲面。对阶跃响应的基于 ITAE指标的最优系数，如表 10-4所示。

表 10-4 对阶跃响应而言，基于ITAE指标的 (s)的最优系数  
$s + \omega_{n}$ $s^2 +1.4\omega_n s + \omega_n^2$ $s^3 +1.75\omega_ns^2 +2.15\omega_n^2 s + \omega_n^3$ $s^4 +2.1\omega_ns^3 +3.4\omega_n^2 s^2 +2.7\omega_n^3 s + \omega_n^4$ $s^5 +2.8\omega_ns^4 +5.0\omega_n^2 s^3 +5.5\omega_n^3 s^2 +3.4\omega_n^4 s + \omega_n^5$ $s^6 +3.25\omega_ns^5 +6.60\omega_n^2 s^4 +8.60\omega_n^3 s^3 +7.45\omega_n^4 s^2 +3.95\omega_n^5 s + \omega_n^6$

当系统 $\phi ( s )$ 具有表 10-4 所示的最优系数时，系统的阶跃响应如图 10-12 所示，其中时间尺度为标准化时间 $\omega _ { n } t$ 。

对于斜坡输入，当闭环稳定系统传递函数具有如下标准形式：

$$
\Phi (s) = \frac {b _ {1} s + b _ {0}}{s ^ {n} + a _ {n - 1} s ^ {n - 1} + \cdots + a _ {1} s + a _ {0}} \tag {10-139}
$$

式中， $a _ { 0 } { = } b _ { 0 }$ ， $a _ { 1 } { = } b _ { 1 }$ ，则可由表 10-5 确定使 ITAE 指标极小化的最优系数。式(10-139)传递函数对斜坡输入的稳态误差为零。显然，系统相应的开环传递函数 $G ( s )$ 应至少有两个纯积分环节。

![](images/dcfd0aca52631e516991d4d28000062e8df4d3777136aff493892341cad1cfbb.jpg)  
图 10-12 传递函数具有标准形式且取最优系数时，系统关于标准化时间 $\omega _ { n } t$ 的单位阶跃响应

表 10-5 对斜坡输入而言，基于 ITAE 指标的(s)的最优系数  

<table><tr><td>s2+3.2ωn s + ωn2</td></tr><tr><td>s3+1.75ωn s2+3.25ωn2s + ωn3</td></tr><tr><td>s4+2.41ωn s3+4.93ωn2s2+5.14ωn3s + ωn4</td></tr><tr><td>s5+2.19ωn s4+6.50ωn2s3+6.30ωn3s2+5.24ωn4s + ωn5</td></tr></table>

采用 ITAE性能指标，以及表 10-4或表 10-5给出的最优系数，可以确定常用的 PID控制器

$$
G _ {c} (s) = K _ {1} + \frac {K _ {2}}{s} + K _ {3} s = \frac {K _ {3} s ^ {2} + K _ {1} s + K _ {2}}{s} \tag {10-140}
$$

的参数 $K _ { 1 }$ ， $K _ { 2 }$ 和 $K _ { 3 }$ ，使系统的 ITAE 性能指标达到最小，且对阶跃输入或斜坡输入的动态响应极好。采用 ITAE方法时，PID控制器的设计过程可以归纳如下：

1) 根据对调节时间的要求，确定闭环系统的自然频率 $\omega _ { n }$ 。  
2) 根据选定的闭环最优系数(参见表 10-4 或表 10-5)以及上一步给出的 $\omega _ { n }$ ，确定 PID控制器式(10-140)的三个参数 $K _ { 1 }$ ， $K _ { 2 }$ 和 $K _ { 3 }$ ，从而得到 $G _ { c } ( s )$ 。  
3) 确定合适的前置滤波器 $G _ { p } ( s )$ ，使得闭环传递函数的零点符合式(10-138)或式(10-139)的要求。

设控制系统如图 10-13 所示，其中被控对象的传递函数为

$$
G _ {0} (s) = \frac {4 0}{(s + 1) ^ {2}}
$$

当 $G _ { c } \left( s \right) = 1$ 时，系统为 0 型系统，静态位置误差系数 $K _ { p } { = } 4 0$ ，在单位阶跃函数作用

下，其稳态误差

$$
e _ {s s} (\infty) = \frac {1}{1 + K _ {p}} = 2.4 \%
$$

![](images/5d582d2b83d2aeb52244e0615f4d08c3505ba7d254e7ccc56594bb118238c1ae.jpg)  
图 10-13 带有期望输入 $R ( s )$ 和扰动输入 $N ( s )$ 的反馈控制系统结构图

再由相应的闭环传递函数

$$
\Phi_ {1} (s) = \frac {4 0}{s ^ {2} + 2 s + 4 1} = \frac {4 0}{s ^ {2} + 2 \zeta \omega_ {n} s + \omega_ {n} ^ {2}}
$$

知， $\omega _ { n } { = } 6 . 4$ ， $\zeta = 0 . 1 5 6$ ，因而超调量及调节时间 $4 = 2 \%$ ) 分别为

$$
\sigma \% = 100 \mathrm{e}^{-\pi \zeta / \sqrt{1 - \zeta^2}} \% = 60.9 \%, \quad t_s = \frac{4.4}{\zeta \omega_n} = 4.4s
$$

现要求系统的阶跃响应具有最优的 ITAE性能，且调节时间 $( A = 2 \% )$ 小于 0.8s，试设计最优 PID 控制器 $G _ { c } ( s )$ 及前置滤波器 $G _ { _ p } ( s )$ 。

解 令 $G _ { p } ( s ) = 1$ ，由于

$$
G _ {c} (s) = \frac {K _ {3} s ^ {2} + K _ {1} s + K _ {2}}{s}
$$

闭环传递函数为

$$
\Phi_ {2} (s) = \frac {G _ {c} (s) G _ {0} (s)}{1 + G _ {c} (s) G _ {0} (s)} = \frac {4 0 \left(K _ {3} s ^ {2} + K _ {1} s + K _ {2}\right)}{s ^ {3} + \left(2 + 4 0 K _ {3}\right) s ^ {2} + \left(1 + 4 0 K _ {1}\right) s + 4 0 K _ {2}} \tag {10-141}
$$

当采用 ITAE 指标时，由表 10-4 可知，最优特征多项式为

$$
D ^ {*} (s) = s ^ {3} + 1. 7 5 \omega_ {n} s ^ {2} + 2. 1 5 \omega_ {n} ^ {2} s + \omega_ {n} ^ {3}
$$

为了满足调节时间的设计要求，需要选取 $\omega _ { n }$ 的合适值。由于 $t _ { \scriptscriptstyle s } = 4 . 4 / ( \zeta \omega _ { \scriptscriptstyle n } ) \leqslant 0 . 8$ ，可选$\omega _ { n } = 1 0$ ，则最优特征多项式为

$$
D ^ {*} (s) = s ^ {3} + 1. 7 5 s ^ {2} + 2 1 5 s + 1 0 0 0
$$

将上式与式(10-141)的分母多项式相比，应有

$$
2 + 4 0 K _ {3} = 1 7. 5
$$

$$
1 + 4 0 K _ {1} = 2 1 5
$$

$$
4 0 K _ {2} = 1 0 0 0
$$

可得， $K _ { 1 } { = } 5 . 3 5$ ， $K _ { 2 } { = } 2 5$ ， $K _ { 3 } { = } 0 . 3 8 7 5$ 。于是，式(10-141)可以写成

$$
\Phi_ {2} (s) = \frac {1 5 . 5 s ^ {2} + 2 1 4 s + 1 0 0 0}{s ^ {3} + 1 7 . 5 s ^ {2} + 2 1 5 s + 1 0 0 0} = \frac {1 5 . 5 \left(s ^ {2} + 1 3 . 8 s + 6 4 . 5\right)}{s ^ {3} + 1 7 . 5 s ^ {2} + 2 1 5 s + 1 0 0 0}
$$

此时，系统性能如表 10-6所示，其阶跃响应的超调量高达 $34 \%$ 。系统在单位阶跃输入及单位阶跃扰动作用下的时间响应，分别如图 10-14(a)、(b)所示。

表 10-6 系统性能  

<table><tr><td>控制系统性能\控制器</td><td>\( G_c(s) = 1 \)</td><td>PID 和 \( G_p(s) = 1 \)</td><td>带前置滤波器 \( G_p(s) \) 的 PID</td></tr><tr><td>超调量</td><td>60.9%</td><td>34%</td><td>1.9%</td></tr><tr><td>调节时间/s</td><td>4.2</td><td>0.62</td><td>0.75</td></tr><tr><td>稳态误差</td><td>2.4%</td><td>0.0%</td><td>0.0%</td></tr><tr><td>\( |y_n(t)|_{\max} \)</td><td>1.57%</td><td>0.165</td><td>0.165</td></tr></table>

![](images/8bec36bec9d9fd8c1848c7785c94b44e762661cb7855b9e89c2df43d206e26d9.jpg)  
(a)单位阶跃输入响应

![](images/39c5e226dd3e0642805925903d3324973f385ad0d281db89085a8ba003383cc6.jpg)  
(b)单位阶跃扰动响应  
图 10-14 $G _ { p } ( s ) { = } 1$ 时系统的时间响应(MATLAB)

为了进一步改善系统性能，在系统输入端接入前置滤波器 $G _ { p } ( s )$ ，使系统闭环传递函数具有式(10-138)的形式，从而具有预期的最优 ITAE 指标。引入 $G _ { p } ( s )$ 后，系统的闭环传递函数应变为

$$
\Phi (s) = \frac {G _ {p} (s) G _ {c} (s) G _ {0} (s)}{1 + G _ {c} (s) G _ {0} (s)} = \frac {1 0 0 0}{s ^ {3} + 1 7 . 5 s ^ {2} + 2 1 5 s + 1 0 0 0}
$$

由此求得

$$
G _ {p} (s) = \frac {6 4 . 5}{s ^ {2} + 1 3 . 8 s + 6 4 . 5}
$$

表 10-6 中的第四列给出了这时系统的阶跃响应指标。由表可见，经过优化后的系统，只有 $1 . 9 \%$ 的超调量，调节时间小于 0.8s，稳态误差为零。此外，由单位阶跃扰动 $N ( s ) = 1 / s$ 引起的最大输出为 0.165。有前置滤波器时，系统的时间响应如图 10-15 所示。仿真结果表明，本例的设计结果是较为满意的。

MATLAB 程序如下：

K1=5.35;

K2=25;

K3=0.3875;

G0=zpk([ ]，[1 1]，40);

Gc=tf([K3 K1 K2]，[1 0]);

Gp=tf([64.5]，[1 13.8 64.5]);

```matlab
sys0=feedback(Gc*G0,1); %无前置滤波器时闭环系统  
sysn=feedback(G0,Gc); %扰动端传递函数  
sys=series(sys0,Gp); %加入前置滤波器后的闭环系统  
figure(1)  
subplot(2,1,1);step(sys0);grid; %绘制无前置滤波器的单位阶跃输入响应曲线  
subplot(2,1,2);step(sysn); %绘制无前置滤波器的单位阶跃扰动响应曲线  
axis([0,1.2,0,1.5]);grid;  
figure(2)  
subplot(2,1,1);step(sys);grid; %绘制带前置滤波器的单位阶跃输入响应曲线  
subplot(2,1,2);step(sysn); %绘制带前置滤波器的单位阶跃扰动响应曲线  
axis([0,0.8,0,1.5]);grid;
```

![](images/4f94bff84eb9d5ac613e2bd94a75a9659ba22cad722d03b0db1aab806c9a9d1e.jpg)  
(a)单位阶跃输入响应

![](images/ed6b71642634f3961c8b51cbf6dfa7c2a52762477a93860c162ac73e3d808901.jpg)  
(b)单位阶跃扰动响应  
图 10-15 带 $G _ { p } ( s )$ 时系统的时间响应(MATLAB)

例 10-17 鲁棒最优系统设计。

设控制系统如图 10-13 所示，其中被控对象的传递函数为

$$
G _ {0} (s) = \frac {K}{(T s + 1) ^ {2}}
$$

其参数变化范围为 $0 . 5 \leqslant T \leqslant 1$ ， $1 \leqslant K \leqslant 2$ 。要求设计一个带前置滤波器的 ITAE最优鲁棒控制系统，使得在给定的参数变化范围内，系统的阶跃响应性能始终保持 $\sigma \% < 4 \%$ ，$t _ { \mathnormal { s } } < 2 \mathrm { s } ( \varDelta = 2 \% )$ 。

解 令前置滤波器 $G _ { p } ( s ) = 1$ ，取 $T { = } 1$ 和 $K { = } 1$ 为标称值，设计 ITAE 最优系统。

采用 PID 控制器

$$
G _ {c} (s) = \frac {K _ {3} s ^ {2} + K _ {1} s + K _ {2}}{s}
$$

则相应闭环系统

$$
\Phi_ {2} (s) = \frac {K _ {3} s ^ {2} + K _ {1} s + K _ {2}}{s ^ {3} + (2 + K _ {3}) s ^ {2} + (1 + K _ {1}) s + K _ {2}}
$$

由表 10-4 知，最优特征多项式为

$$
D ^ {*} (s) = s ^ {3} + 1. 7 5 \omega_ {n} s ^ {2} + 2. 1 5 \omega_ {n} ^ {2} s + \omega_ {n} ^ {3}
$$

根据对系统阶跃响应的调节时间要求

$$
t _ {s} = \frac {4 . 4}{\zeta \omega_ {n}} <   2
$$

可初选 $\omega _ { n } = 8$ ，相应 $\zeta > 0 . 2 8$ ，则最优特征多项式为

$$
D ^ {*} (s) = s ^ {3} + 1 4 s ^ {2} + 1 3 7. 6 s + 5 1 2
$$

与 $\phi _ { 2 } ( s )$ 的分母多项式相比，根据对应项系数相等，可求得 PID 控制器参数为

$K _ { 3 } = 1 2 , K _ { 1 } = 1 3 6 . 6 , K _ { 2 } = 5 1 2$ 于是 $\phi _ { 2 } ( s ) = \frac { 1 2 ( s ^ { 2 } + 1 1 . 3 8 s + 4 2 . 6 7 ) } { s ^ { 3 } + 1 4 s ^ { 2 } + 1 3 7 . 6 s + 5 1 2 }$

故前置滤波器应取为

$$
G _ {p} (s) = \frac {4 2 . 6 7}{s ^ {2} + 1 1 . 3 8 s + 4 2 . 6 7}
$$

由此得 ITAE 意义下的最优闭环传递函数

$$
\Phi (s) = \frac {5 1 2}{s ^ {3} + 1 4 s ^ {2} + 1 3 7 . 6 s + 5 1 2}
$$

系统的阶跃响应性能如表 10-7 中第二列所示： $\sigma \% = 2 \%$ ， $t _ { s } = 0 . 9 4 \mathrm { s }$ ，表明标称系统的性能满足设计指标要求， $\omega _ { n } = 8$ 的选择是合适的。

表 10-7 例 10-17 的设计结果( $\scriptstyle ( { \boldsymbol { \omega } } _ { m } = { \mathbf { 8 } } )$   

<table><tr><td colspan="2">对象条件</td><td>T=1
K=1</td><td>T=0.5
K=1</td><td>T=1
K=2</td><td>T=0.5
K=2</td></tr><tr><td rowspan="2">动态性能</td><td>超调量</td><td>2%</td><td>0</td><td>0</td><td>0.4%</td></tr><tr><td>调节时间/s</td><td>0.94</td><td>0.65</td><td>0.63</td><td>0.66</td></tr></table>

为了考察系统对参数变化的鲁棒性，保持 $G _ { c } ( s )$ 和 $G _ { _ p } ( s )$ 不变，分别取 $T { = } 0 . 5 , K { = } 1 ; T$ =1，$K { = } 2$ 以及 $T { = } 0 . 5$ ， $K { = } 2$ ，测得系统的阶跃响应性能，如表10-7中第三至第五列所示。由表可以看出，这是一个鲁棒性很强的系统。系统参数变化时的系统时间响应如图 $1 0 \cdot 1 6 \sim$ 图 10-19 所示。

![](images/0ca0340709587ba1b2ec76e9ede21dcb103035a2ebb538eda45027a4113927d4.jpg)  
图 10-16 T=1， $K { = } 1$ 时系统的时间响应

![](images/6417659c1c478e8bfcdd57952c4469666073f4522d120f0243f9eb440bd115af.jpg)  
图 10-17 $T { = } 0 . 5$ ， $K { = } 1$ 时系统的时间响应

![](images/2ba2fefe77ae92ce93bdf0c15ffe82907344b4b927137cae6ff85145db09b5ea.jpg)  
(MATLAB)   
图 10-18 T=1， $K { = } 2$ 时系统的时间响应  
(MATLAB)

![](images/a9c2aa86a316bab49e02dc57d6d142dc1f046874df8b8b9ec9deb07d001db5ad.jpg)  
(MATLAB)   
图 10-19 $T { = } 0 . 5$ ， $K { = } 2$ 时系统的时间响应  
(MATLAB)

MATLAB 程序如下：

$$
\mathrm {K} = 2; \mathrm {T} = 0. 5; \mathrm {K} 3 = 1 2; \mathrm {K} 1 = 1 3 6. 6; \mathrm {K} 2 = 5 1 2;
$$

$$
\mathrm {G 0 = t f (K , [ T ^ {\wedge} 2 , 2 * T , 1 ])};
$$

$$
\% \text{定义开环传递函数}
$$

$$
\mathrm {G c} = \operatorname {t f} ([ \mathrm {K 3}, \mathrm {K 1}, \mathrm {K 2} ], [ 0, 1, 0 ])
$$

$$
\% \text {定义 PID 控制器传递函数}
$$

$$
\mathrm {G} = \text {s e r i e s} (\mathrm {G 0}, \mathrm {G c});
$$

$$
\mathrm {G p} = \operatorname {t f} (4 2. 6 7, [ 1, 1 1. 3 8, 4 2. 6 7 ])
$$

$$
\operatorname {s y s 0} = \text {f e e d b a c k} (G, 1);
$$

$$
\mathrm {s y s} = \text {s e r i e s (s y s 0 , G p)};
$$

$$
\% \text{带前置滤波器的闭环传递函数}
$$

$$
\text {s t e p (s y s) ; a x i s (\left[ 0 , 1 , 0 , 1 . 3 \right]) ; g r i d ;}
$$

需要指出，实际的被控对象不容许有过大的输入量，因而图 10-13 系统中控制器$G _ { c } ( s )$ 的输出 $u ( t )$ 有最大允许值的限制，这样，系统自然频率 $\omega _ { n }$ 的可选值将会受到约束。

通常，当 $e ( t )$ 的最大值为 1 时， $u ( t )$ 的数值将不得大于 100。为了说明 $u ( t )$ 对 $\omega _ { n }$ 的影响，以图 10-13 系统为例，并假设

$$
G _ {0} (s) = \frac {1}{s (s + 1)}
$$

在进行 ITAE 最优设计时，可参考表 10-8 中给出的 $\omega _ { n }$ 分别取 10，20 和 40 时的 PID 控制器参数、前置滤波器和最优闭环传递函数。

表 10-8 不同 $\omega _ { \pmb { n } }$ 下的设计结果  

<table><tr><td rowspan="2">\( \omega_n \)</td><td colspan="3">PID</td><td rowspan="2">\( G_p(s) \)</td><td rowspan="2">\( \Phi(s) \)</td></tr><tr><td>\( K_3 \)</td><td>\( K_1 \)</td><td>\( K_2 \)</td></tr><tr><td>10</td><td>16.5</td><td>215</td><td>1000</td><td>\( \frac{60.6}{s^2 + 13.03s + 60.6} \)</td><td>\( \frac{1000}{s^3 + 17.5s^2 + 215s + 1000} \)</td></tr><tr><td>20</td><td>34</td><td>860</td><td>8000</td><td>\( \frac{235.29}{s^2 + 25.29s + 235.29} \)</td><td>\( \frac{8000}{s^3 + 35s^2 + 860s + 8000} \)</td></tr><tr><td>40</td><td>69</td><td>3440</td><td>64000</td><td>\( \frac{927.54}{s^2 + 49.86s + 927.54} \)</td><td>\( \frac{64000}{s^3 + 70s^2 + 3440s + 64000} \)</td></tr></table>

根据表 10-8 中给出的结果，表 10-9 给出了 $\omega _ { n }$ 分别等于 10，20 和 40 时允许的 $u ( t )$ 最大值。从中可以推知，如果 $u ( t )$ 的最大允许值为 100，系统自然频率 $\omega _ { n }$ 就不能大于 16。显然，限制 $\omega _ { n }$ 的取值范围，也就限制了系统能达到的最小调节时间。

表 10-9 被控对象的最大输入  

<table><tr><td>\( {\omega }_{n} \)</td><td>10</td><td>20</td><td>40</td></tr><tr><td>当输入为 \( R\left( s\right) = 1/s \)时, \( u\left( t\right) \) 的最大值</td><td>35</td><td>135</td><td>550</td></tr><tr><td>调节时间/s</td><td>0.8</td><td>0.4</td><td>0.2</td></tr></table>

当取 $\omega _ { n } { = } 1 0$ 时，系统的单位阶跃响应 $y ( t )$ 及被控对象输入响应 $u ( t )$ 分别如图 10-20 及图 10-21 所示。

![](images/7567e112e4418c55cf41273fde1c61693661b8106332e92f98f5958e5f6bce07.jpg)  
图 10-20 系统的时间响应( $\omega _ { n } = 1 0$ )(MATLAB)

![](images/0511613fbc3df4c85af006901fb62425e2b59574d79d8ee8f9d6b012b276ff42.jpg)  
图 10-21 被控对象输入响应( =10)(MATLAB)

MATLAB 程序如下：

$\mathrm{G0 = tf(1,[1,1,0])}$ $\mathrm{Gc = tf([16.5,215,1000],[0,1,0])}$ $\mathrm{Gp = tf(60.6,[1,13.03,60.6])}$ sys1 $\equiv$ tf(1000,[1,17.5,215,1000]); %定义闭环系统传递函数  
sys2 $=$ Gc*Gp/(1+Gc*G0); %定义期望输入到被控对象输入之间的传递函数  
figure(1)  
step(sys1);  
axis([0,1,0,1.4]);  
grid;  
figure(2)  
step(sys2);  
grid;

# 习 题

10-1 求通过 $x ( 0 ) { = } 1$ ， $x ( 1 ) { = } 2$ ，使下列性能指标为极值的曲线 $x ^ { * } ( t )$ ：

$$
J = \int_ {t _ {0}} ^ {t _ {f}} (\dot {x} ^ {2} + 1) \mathrm {d} t
$$

10-2 设 ${ \boldsymbol x } { = } { \boldsymbol x } ( t )$ ， $0 \leqslant t \leqslant 1$ ，求从 $x ( 0 ) { = } 0$ 到 $x ( 1 ) { = } 1$ 间的最短曲线。  
10-3 求性能指标

$$
J = \int_ {0} ^ {1} (\dot {x} ^ {2} + 1) d t
$$

在边界条件 $x ( 0 ) { = } 0$ ， $x ( 1 )$ 是自由情况下的极值曲线。

10-4 求性能指标

$$
J = \int_ {0} ^ {\frac {\pi}{2}} \left(\dot {x} _ {1} ^ {2} + \dot {x} _ {2} ^ {2} + 2 x _ {1} x _ {2}\right) d t
$$

在边界条件 ${ x } _ { 1 } ( 0 ) { = } { x } _ { 2 } ( 0 ) { = } 0$ ， $x _ { 1 } \left( \frac { \pi } { 2 } \right) = x _ { 2 } \left( \frac { \pi } { 2 } \right) = 1$ x  下的极值曲线。

10-5 已知性能指标函数为

$$
J = \int_ {0} ^ {1} \left[ x ^ {2} (t) + t x (t) \right] d t
$$

试求： $( 1 ) \delta J$ 的表达式；

(2)当 $x ( t ) { = } t ^ { 2 }$ ， $\delta x = 0 . 1 t$ 和 $\delta x = 0 . 2 t$ 时的变分 $\delta J$ 的值。

10-6 试求下列性能指标的变分 $\delta J$

$$
J = \int_ {t _ {0}} ^ {t _ {f}} \left(t ^ {2} + x ^ {2} + \dot {x} ^ {2}\right) d t
$$

10-7 已知性能指标为

$$
J = \int_ {0} ^ {R} \sqrt {1 + \dot {x} _ {1} ^ {2} + \dot {x} _ {2} ^ {2}} d t
$$

求 $J$ 在约束条件 $t ^ { 2 } + x _ { 1 } ^ { 2 } = R ^ { 2 }$ 和边界条件 $x _ { 1 } ( 0 ) { = } { - } R$ ， $x _ { 2 } ( 0 ) { = } 0$ ； $x _ { 1 } ( R ) { = } 0$ ， $x _ { 2 } ( R ) { = } \pi$ 下的极值。

10-8 已知系统的状态方程为

$$
\dot {x} _ {1} (t) = x _ {2} (t), \quad \dot {x} _ {2} (t) = u (t)
$$

边界条件为 ${ x } _ { 1 } ( 0 ) { = } { x } _ { 2 } ( 0 ) { = } 1$ ， $\scriptstyle x 1 ( 3 ) = x 2 ( 3 ) = 0$ ，试求使性能指标

$$
J = \int_ {0} ^ {3} \frac {1}{2} u ^ {2} (t) \mathrm {d} t
$$

取极小值的最优控制 $u ^ { * } ( t )$ 以及最优轨线 $x ^ { * } ( t )$ 。

10-9 已知系统状态方程及初始条件为

$$
\dot {x} = u, \quad x (0) = 1
$$

试确定最优控制使下列性能指标取极小值

$$
J = \int_ {0} ^ {1} \left(x ^ {2} + u ^ {2}\right) \mathrm {e} ^ {2 t} \mathrm {d} t
$$

10-10 求使系统

$$
\dot {x} _ {1} = x _ {2}, \quad \dot {x} _ {2} = u
$$

由初始状态 ${ x } _ { 1 } ( 0 ) { = } { x } _ { 2 } ( 0 ) { = } 0$ 出发，在 $t _ { f } = 1$ 时转移到目标集 $x _ { 1 } ( 1 ) + x _ { 2 } ( 1 ) = 1$ ，并使性能指标

$$
J = \frac {1}{2} \int_ {0} ^ {1} u ^ {2} (t) \mathrm {d} t
$$

为最小值的最优控制 $u ^ { * } ( t )$ 及相应的最优轨线 $x ^ { * } ( t )$ 。

10-11 已知一阶系统

$$
\dot {x} (t) = - x (t) + u (t), \quad x (0) = 3
$$

(1) 试确定最优控制 $u ^ { * } ( t )$ ，使系统在 $t _ { f } = 2$ 时转移到 $x ( 2 ) { = } 0$ ，并使性能泛函

$$
J = \int_ {0} ^ {2} (1 + u ^ {2}) \mathrm {d} t = \min
$$

(2) 如果使系统转移到 $x ( t _ { f } ) = 0$ 的终端时间 $t _ { f }$ 自由，问 $u ^ { * } ( t )$ 应如何确定?

10-12 设系统状态方程及初始条件为

$$
\dot {x} (t) = u (t), \quad x (0) = 1
$$

试确定最优控制 $u ^ { * } ( t )$ ，使性能指标

$$
J = t _ {f} + \frac {1}{2} \int_ {0} ^ {t _ {f}} u ^ {2} d t
$$

为极小，其中终端时间 $t _ { f }$ 未定， $x ( t _ { f } ) = 0$ 。

10-13 设二次积分模型为

$$
\dot {\theta} (t) = \omega (t), \quad \dot {\omega} (t) = u (t)
$$

性能指标为

$$
J = \frac {1}{2} \int_ {0} ^ {1} u ^ {2} (t) \mathrm {d} t
$$

已知 $\theta ( 0 ) = \omega ( 0 ) = 1$ ， $\theta ( 1 ) = 0$ ， $\omega ( 1 )$ 自由，试求最优控制 $u ^ { * } ( t )$ 和最优轨线 $\boldsymbol { \theta } ^ { * } ( t )$ ， $\omega ^ { ^ { * } } ( t )$ 。

10-14 设系统状态方程及初始条件为

$$
\dot {x} _ {1} (t) = x _ {2} (t), \quad x _ {1} (0) = 2
$$

$$
\dot {x} _ {2} (t) = u (t), \quad x _ {2} (0) = 1
$$

性能指标为

$$
J = \frac {1}{2} \int_ {0} ^ {t _ {f}} u ^ {2} d t
$$

要求达到 $x ( t _ { f } ) = 0$ ，试求：

(1) $t _ { f } = 5$ 时的最优控制 $u ^ { * } ( t )$ ；  
(2) $t _ { f }$ 自由时的最优控制 $u ^ { * } ( t )$ 。

10-15 设一阶系统方程

$$
\dot {x} (t) = u (t), \qquad x (0) = 1
$$

性能指标

$$
J = \frac {1}{2} \int_ {0} ^ {1} \left(x ^ {2} + u ^ {2}\right) d t
$$

已知 $x ( 1 ) { = } 0$ ，某工程师认为从工程观点出发可取最优控制函数 $u ^ { * } ( t ) = - 1$ ，试分析他的意见是否正确，并说明理由。

10-16 给定二阶系统

$$
\dot {x} _ {1} (t) = x _ {2} (t) + \frac {1}{4}, \quad x _ {1} (0) = - \frac {1}{4}
$$

$$
\dot {x} _ {2} (t) = u (t), \quad x _ {2} (0) = - \frac {1}{4}
$$

控制约束为 $\left| u ( t ) \right| \leqslant \frac { 1 } { 2 }$ ，要求最优控制 $u ^ { * } ( t )$ ，使系统在 $t = t _ { f }$ 时转移到 $x ( t _ { f } ) = 0$ ，并使

$$
J = \int_ {0} ^ {t _ {f}} u ^ {2} (t) \mathrm {d} t = \min
$$

式中， $t _ { f }$ 自由。

10-17 设一阶系统方程为

$$
\dot {x} (t) = x (t) - u (t), \quad x (0) = 5
$$

控制约束 $0 . 5 \leqslant u ( t ) \leqslant 1$ ，性能指标为

$$
J = \int_ {0} ^ {1} (x + u) d t
$$

终端状态自由，试求 $u ^ { * } ( t )$ ， $x ^ { * } ( t )$ 和 $J ^ { * }$ 。

10-18 设二阶系统

$$
\dot {x} _ {1} (t) = - x _ {1} (t) + u (t), \quad x _ {1} (0) = 1
$$

$$
\dot {x} _ {2} (t) = x _ {1} (t), \quad \quad \quad \quad \quad x _ {2} (0) = 0
$$

控制约束 $\left| u ( t ) \right| \leqslant 1$ ，当系统终端自由时，求最优控制 $u ^ { * } ( t )$ ，使性能指标

$$
J = 2 x _ {1} (1) + x _ {2} (1)
$$

取极小值，并求最优轨线 $x ^ { * } ( t )$ 。

10-19 已知二阶系统

$$
\dot {x} _ {1} (t) = x _ {2} (t), \quad \dot {x} _ {2} (t) = u (t)
$$

控制约束 $\big | u ( t ) \big | \leqslant 1$ ，试确定最小时间控制 $u ^ { * } ( t )$ ，使系统由任意初态最快地转移到终端状态 $x _ { 1 } ( t _ { f } ) = 2$ ，$x _ { 2 } ( t _ { f } ) = 1$ ，要求写出开关曲线方程 并画出 曲线的图形。

10-20 已知一阶系统

$$
\dot {x} (t) = - \frac {1}{2} x (t) + u (t)
$$

性能指标

$$
J = \frac {1}{2} \left[ 1 0 x ^ {2} (1) \right] + \frac {1}{2} \int_ {0} ^ {1} \left(2 x ^ {2} + u ^ {2}\right) d t
$$

求最优控制 $u ^ { * } ( t )$ 。

10-21 已知二阶系统

$$
\dot {x} _ {1} (t) = x _ {2} (t), \quad \dot {x} _ {2} (t) = u (t)
$$

试确定最优控制 $u ^ { * } ( t )$ ，使下列性能指标取极小值：

$$
J = \frac {1}{2} \left[ x _ {1} ^ {2} (3) + 2 x _ {2} ^ {2} (3) \right] + \frac {1}{2} \int_ {0} ^ {3} \left[ 2 x _ {1} ^ {2} (t) + 4 x _ {2} ^ {2} (t) + 2 x _ {1} (t) x _ {2} (t) + \frac {1}{2} u ^ {2} (t) \right] d t
$$

10-22 设控制系统如图 10-13 所示，其中被控对象

$$
G _ {0} (s) = \frac {6 0}{(s + 2) (s + 3)}
$$

试设计最优 PID 控制器 $G _ { c } ( s )$ 及前置滤波器 $G _ { _ p } ( s )$ ，使系统具有最优的 ITAE 性能，且调节时间小于$0 . 8 \mathrm { s } ( A = 2 \% )$ 。

10-23 设被控对象为

$$
G _ {0} (s) = \frac {1 0}{s ^ {2}}
$$

试设计一个带有 PID控制器和前置滤波器的单位负反馈控制系统，使系统的阶跃响应具有最优的 ITAE指标，峰值时间为0.8s左右，并给出系统的单位阶跃响应曲线。

10-24 在太阳黑子活动的高峰期，NASA会把射线图像设备(GRID)系于高空飞行的气球上，以从事长时间的观测实验。GRID设备能拍摄更准确的X射线的强度图，也可以拍摄 射线强度图。这些信息有利于在下一次太阳活动高峰期，对太阳中的高能现象进行研究。装配在气球上的GRID如图10-22(a)所示，其主要组成部分是：直径为 $5 . 2 \mathrm { m }$ 的吊舱，GRID 有效载荷，高空气球和连接气球与吊舱的缆绳。GRID 设备指向控制系统如图 10-22(b)所示。其中，扭矩电机负责驱动圆桶式吊舱装置。要求设计 PID 控制器 $G _ { c } ( s )$ 及前置滤波器 $G _ { \scriptscriptstyle p } ( s )$ ，使系统在阶跃输入作用下的稳态跟踪误差为零，并具有 ITAE优化性能。

![](images/77e8bf87e897692d874ebd36321fc7337146b9bb5b8f3852d5d9d4529c55a0a1.jpg)

![](images/efe9c30aa48ad2476dee1c1b3ac1ab8b88cbaeba89f290b155b323797a4313cf.jpg)  
(b)指向控制系统  
图 10-22 GRID设备的指向控制系统

10-25 图 10-23 的模型描述了人类站立时的平衡调节机制。对于丧失自主站立能力的下身残疾的伤残人士，需要安装图10-23所示的站立和腿关节人工控制系统。设计要求：

![](images/0438f602188015357457f84ac65ec933ef036710ce1a33d6f311abbcf0984a1a.jpg)  
图 10-23 站立和腿关节的人工控制系统结构图

(1) 若肌肉-神经系统的参数标称值为 $K { = } 1 0$ ， $a { = } 1 2$ ， $scriptstyle b = 1 0 0$ ，试用 ITAE 优化法设计 PI 控制器 $G _ { c } ( s )$ 和前置滤波器 $G _ { p } ( s )$ ，使人工控制系统阶跃响应的 $\sigma \% < 1 0 \%$ ， $e _ { s s } ( \infty ) < 5 \%$ ， $t _ { s } < 2 \mathrm { s } ( \varDelta = 2 \% )$ ；  
(2) 当人疲乏时，肌肉-神经系统的参数变化为 $K { = } 1 5$ ， $a { = } 8$ ， $b { = } 1 4 4$ ，试沿用在(1)中得到的 PI 控制器和前置滤波器，检验系统的鲁棒性能，绘出系统参数变化前后的单位阶跃响应曲线。

10-26 空间机器人的机械臂及其控制框图如图 10-24 所示。已知电机与机械臂构成的手臂传递函数为

$$
G _ {0} (s) = \frac {1 0}{s (s + 1 0)}
$$

设计要求：

(1) 当 $G _ { c } ( s ) = K$ 时，确定 $K$ 的合适取值，使系统阶跃响应的超调量 $\sigma \% = 4 . 5 \%$ ；  
(2) 采用 ITAE 优化方法，并选取 $\omega _ { n } = 1 0$ ，设计合适的 PD 控制器 $G _ { c } ( s )$ ，确定对应的前置滤波器$G _ { _ p } ( s )$ ；  
(3) 采用 ITAE 优化方法，设计合适的 PI 控制器 $G _ { c } ( s )$ 和相应的前置滤波器 $G _ { p } ( s )$ ；  
(4) 采用 ITAE 优化方法和 $\omega _ { n } { = } 1 0$ ，设计合适的 PID 控制器 $G _ { c } ( s )$ 和前置滤波器 $G _ { _ { p } } ( s )$ ；  
(5) 对上述各种设计效果，列表比较系统对单位阶跃输入响应的 $\sigma \%$ ， $t _ { p }$ ， $t _ { s } ( A = 2 \% )$ ，以及由单位阶跃扰动引起的输出 $y ( t )$ 的最大值和稳态值。

![](images/2791526df6623ce66cca90ed1da7000a39c7f75423cc063deca11028eb29b8a9.jpg)

![](images/58c6af0479b016d5ae3453d7b5186086c124220b4ffceb76b5af3ae778ed94c1.jpg)  
(b)控制框图  
图 10-24 空间机器人的机械臂控制系统