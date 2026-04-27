# 第九章 线性系统的状态空间分析与综合

![](images/629879597ec2b1027197224982d3a2587d0b43e8fcc2a1805f22872ac34fccdc.jpg)

经典线性系统理论对于单输入-单输出线性定常系统的分析和综合是比较有效的，但其显著的缺点是只能揭示输入-输出的外部特性，难以揭示系统内部的结构特性，也难以有效处理多输入-多输出系统。

在 20世纪 50年代蓬勃兴起的航天技术的推动下，1960年前后开始了从经典控制理论到现代控制理论的过渡，其中一个重要标志就是卡尔曼系统地将状态空间概念引入到控制理论中来。现代控制理论正是在引入状态和状态空间概念的基础上发展起来的。

现代控制理论中的线性系统理论运用状态空间法描述输入-状态-输出诸变量间的因果关系，不但反映了系统的输入-输出外部特性，而且揭示了系统内部的结构特性，是一种既适用于单输入-单输出系统又适用于多输入-多输出系统，既可用于线性定常系统又可用于线性时变系统的有效分析和综合方法。

在线性系统理论中，根据所采用的数学工具及系统描述方法，又出现了一些平行的分支，目前主要有线性系统的状态空间法、线性系统的几何理论、线性系统的代数理论、线性系统的多变量频域方法等。由于状态空间法是线性系统理论中最重要和影响最广的分支，所以本章只介绍线性系统的状态空间法。

# 9-1 线性系统的状态空间描述

# 1. 系统数学描述的两种基本类型

这里所谓的系统是指由一些相互制约的部分构成的整体，它可能是一个由反馈闭合的整体，也可能是某一控制装置或被控对象。本章所研究的系统均假定具有若干的输入端和输出端，如图9-1所示。图中方框以外的部分为系统环境，环境对系统的作用为系统输入，系统对环境的作用为系统输出，二者分别用向量 $\pmb { u } { - } [ u _ { 1 } , u _ { 2 } , \cdots , u _ { p } ] ^ { \mathrm { T } }$ 和 $\mathbf { \boldsymbol { y } } = [ y _ { 1 } , y _ { 2 } , \cdots , y _ { q } ] ^ { \mathrm { T } }$ 表示，它们均为系统的外部变量。描述系统内部每个时刻所处状况的变量为系统的内部变量，以向量 $\scriptstyle { x = [ x _ { 1 } , x _ { 2 } , }$ …,$x _ { n } ] ^ { \mathrm { T } }$ 表示。系统的数学描述是反映系统变量间因果关系和变换关系的一种数学模型。

系统的数学描述通常有两种基本类型。一种是系统的外部描述，即输入-输出描述。这种描述将系统看作一个“黑箱”，只是反映系统外部变量间即输入-输出间的因果关系，而不去表征系统的内部结构和内部变量。系

![](images/c52b88fd96731cc38343586a67034be00aca77518c302f67b3ff7efecaa01908.jpg)  
图 9-1 系统的方框图表示

统描述的另一种类型是内部描述，即状态空间描述。这种描述是基于系统内部结构分析的一类数学模型，通常由两个数学方程组成：一个是反映系统内部变量 $\pmb { x } { = } [ x _ { 1 } , x _ { 2 } , \ \cdots , x _ { n } ] ^ { \mathrm { T } }$ 和输入变量 $\scriptstyle \pmb { u } = [ u _ { 1 } , \ u _ { 2 } , \ u _ { 2 } , \ u _ { 3 } , \ u _ { 4 } , \ u _ { 4 } , \ u _ { 5 } ]$ , …, $u _ { p } ] ^ { \mathrm { T } }$ 间因果关系的数学表达式，常具有微分方程或差分方程的形式，称为状态方程；另一个是表征系统内部变量 $\pmb { x } { = } [ x _ { 1 } , \ x _ { 2 } , \ \cdots , \ x _ { n } ] ^ { \mathrm { T } }$ 及输入变量 $\scriptstyle { \pmb { u } } = [ u _ { 1 } ,$ $\boldsymbol { u } _ { 2 } , \cdots , \boldsymbol { u } _ { p } ] ^ { \mathrm { T } }$ 和输出变量 $\mathbf { \psi } _ { y = [ y _ { 1 } , y _ { 2 } , \mathbf { \psi } } \cdots , y _ { q } ] ^ { \mathrm { T } }$ 间转换关系的数学表达式，具有代数方程的形式，

称为输出方程。外部描述仅描述系统的外部特性，不能反映系统的内部结构特性，而具有完全不同内部结构的两个系统也可能具有相同的外部特性，因而外部描述通常只是对系统的一种不完全的描述。内部描述则是对系统的一种完全的描述，它能完全表征系统的所有动力学特征。仅当在系统具有一定属性的条件下，两种描述才具有等价关系。

# 2. 系统状态空间描述常用的基本概念

在系统状态空间描述中常用如下的一些基本概念。

状态和状态变量 系统在时间域中的行为或运动信息的集合称为状态。确定系统状态的一组独立(数目最小)变量称为状态变量。

一个用 $n$ 阶微分方程描述的系统，当 $n$ 个初始条件 $x ( t _ { 0 } )$ , ${ \dot { x } } ( t _ { 0 } )$ , …, $x ^ { ( n - 1 ) } \left( t _ { 0 } \right)$ , 及 $t \geqslant t _ { 0 }$ 的输入 $u ( t )$ 给定时，可唯一确定方程的解，即系统将来的状态，故 $x ( t )$ ， ${ \dot { x } } ( t )$ , …, $x ^ { ( n - 1 ) } \left( t \right)$ 这 $n$ 个独立变量可选作状态变量。状态变量对于确定系统的行为既是必要的，也是充分的。$n$ 阶系统状态变量所含独立变量的个数为 $n$ 。显然，当变量个数小于 $n$ 时，便不能完全确定$n$ 阶系统的状态，而当变量个数大于 $n$ 时，对于确定系统的状态有的变量则是多余的。

状态变量的选取不具有唯一性，同一个系统可能有多种不同的状态变量选取方法。状态变量也不一定在物理上可量测，有时只具有数学意义，而无任何物理意义。但在具体工程问题中，应尽可能选取容易量测的量作为状态变量，以便实现状态的前馈和反馈等设计要求。例如，机械系统中常选取线(角)位移和线(角)速度作为变量，RCL网络中则常选取流经电感的电流和电容的端电压作为状态变量。

状态变量常用符号 $x _ { 1 } ( t ) , x _ { 2 } ( t ) , \ \cdots , x _ { n } ( t )$ $x _ { n } ( t )$ 表示。

状态向量 把描述系统状态的 $n$ 个状态变量 $x _ { 1 } ( t )$ ， $x _ { 2 } ( t ) .$ , …, $x _ { n } ( t )$ 看作向量 $x ( t )$ 的分量，即

$$
\boldsymbol {x} (t) = \left[ x _ {1} (t), x _ {2} (t), \dots , x _ {n} (t) \right] ^ {\mathrm {T}}
$$

则向量 ${ \mathbf { } } x ( t )$ 称为 $n$ 维状态向量。给定 ${ \mathrm { } } t { = } t _ { 0 }$ 时的初始状态向量 $\mathbf { \nabla } _ { \mathbf { \boldsymbol { x } } } ( t _ { 0 } ) .$ 及 $t \geqslant t _ { 0 }$ 的输入向量 ${ \pmb u } \left( t \right)$ ，则 $t \geqslant t _ { 0 }$ 的状态由状态向量 $x \left( t \right)$ 唯一确定。

状态空间 以 $n$ 个状态变量作为基底所组成的 $n$ 维空间称为状态空间。

状态轨线 系统在任一时刻的状态，在状态空间中用一点来表示。随着时间推移，系统状态在变化，便在状态空间中描绘出一条轨迹。这种系统状态在状态空间中随时间变化的轨迹称为状态轨迹或状态轨线。

线性系统的状态空间表达式 若线性系统描述系统状态量与输入量之间关系的状态方程是一阶向量线性微分方程或一阶向量线性差分方程，而描述输出量与状态量和输入量之间关系的输出方程是向量代数方程，则其组合称为线性系统状态空间表达式，或称为动态方程，其连续形式为

$$
\dot {\boldsymbol {x}} (t) = \boldsymbol {A} (t) \boldsymbol {x} (t) + \boldsymbol {B} (t) \boldsymbol {u} (t) \tag {9-1}
$$

$$
\boldsymbol {y} (t) = \boldsymbol {C} (t) \boldsymbol {x} (t) + \boldsymbol {D} (t) \boldsymbol {u} (t)
$$

对于线性离散时间系统，由于在实践中常取 $t _ { k } { = } k T ( T$ 为采样周期)，其状态空间表达式的一般形式可写为

$$
\boldsymbol {x} (k + 1) = \boldsymbol {G} (k) \boldsymbol {x} (k) + \boldsymbol {H} (k) \boldsymbol {u} (k) \tag {9-2}
$$

$$
\boldsymbol {y} (k) = \boldsymbol {C} (k) \boldsymbol {x} (k) + \boldsymbol {D} (k) \boldsymbol {u} (k)
$$

通常，若状态 $\boldsymbol { x }$ 、输入 $\pmb { u }$ 、输出 $\boldsymbol { y }$ 的维数分别为 $n , p , q$ ，则称 $n \times n$ 矩阵 $\mathbf { } A ( t )$ 及 ${ \pmb G } \left( k \right)$ 为系统矩阵或状态矩阵，称 $n \times p$ 矩阵 $\boldsymbol { B } \left( t \right)$ 及 $H ( k )$ 为控制矩阵或输入矩阵，称 $q \times n$ 矩阵 $C \left( t \right)$ 及 $C \left( k \right)$ 为观测矩阵或输出矩阵，称 $q \times p$ 矩阵 ${ \pmb D } \left( t \right)$ 及 $\pmb { D } \left( k \right)$ 为前馈矩阵或输入输出矩阵。

线性定常系统 在线性系统的状态空间表达式中，若系数矩阵 $A \left( t \right) , B \left( t \right) , C \left( \mathrm { t } \right) , D \left( t \right)$ 或 $\pmb { G } \left( k \right) , \pmb { H } \left( k \right) , \pmb { C } \left( k \right) , \pmb { D } \left( k \right)$ 的各元素都是常数，则称该系统为线性定常系统，否则为线性时变系统。线性定常系统状态空间表达式的一般形式为

$$
\dot {\boldsymbol {x}} (t) = \boldsymbol {A} \boldsymbol {x} (t) + \boldsymbol {B} \boldsymbol {u} (t) \tag {9-3}
$$

$$
\boldsymbol {y} (t) = \boldsymbol {C} \boldsymbol {x} (t) + \boldsymbol {D} \boldsymbol {u} (t)
$$

$\pmb { x } ( k + 1 ) = \pmb { G } \pmb { x } ( k ) + \pmb { H } \pmb { u } ( k )$ 或 (9-4) $\begin{array} { r } { \mathbf { \mathbf { \mathit { y } } } ( k ) = \mathbf { \mathbf { \mathit { C } } } \mathbf { \mathbf { \mathit { x } } } ( k ) + \mathbf { \mathit { D } } \mathbf { \mathbf { \mathit { u } } } ( k ) } \end{array}$

当输出方程中 $\pmb { D } \equiv 0$ 时，系统称为绝对固有系统，否则称为固有系统。为书写方便，常把固有系统(9-3)或(9-4)简记为系统 $( A , B , C , D )$ 或系统 $( G , H , C , D )$ ，而记相应的绝对固有系统为系统 $( A , B , C )$ 或系统 $( G , H , C )$ 。

线性系统的结构图 线性系统的状态空间表达式常用结构图表示。线性连续时间系统(9-3)的结构图如图 9-2所示，线性离散时间系统(9-4)的结构图如图 9-3所示。结构图中$\pmb { I }$ 为 $n \times n$ 单位矩阵， $s$ 是拉普拉斯算子， $z ^ { - 1 }$ 为单位延时算子， $s$ 和 $z$ 均为标量。每一方框的输入-输出关系规定为

输出向量 $=$ (方框所示矩阵) $\times$ (输入向量)

应注意到在向量、矩阵的乘法运算中，相乘顺序不允许任意颠倒。

![](images/91db029a00128bb3d12205cb0f8461ce139ce2e52552fa1b473a77b29c1e6f18.jpg)  
图 9-2 线性连续时间系统结构图

![](images/c1130866118f861bf1cb18372a4eae4a7397ff8d5c21840dd0332bb3f77a8b52.jpg)  
图 9-3 线性离散时间系统结构图

# 3. 线性定常连续系统状态空间表达式的建立

建立状态空间表达式的方法主要有两种：一是直接根据系统的机理建立相应的微分方程或差分方程，继而选择有关的物理量作为状态变量，从而导出其状态空间表达式；二是由已知的系统其他数学模型经过转化而得到状态空间表达式。

# (1) 根据系统机理建立状态空间表达式

下面通过例题来介绍根据系统机理建立线性定常连续系统状态空间表达式的方法。

例 9-1 试列写如图 9-4 所示 RLC 网络的电路方程，选择几组状态变量并建立相应的状态空间表达式，就所选状态变量间的关系进行讨论。

解 根据电路定律可列写如下方程：

$$
R i + L \frac {\mathrm {d} i}{\mathrm {d} t} + \frac {1}{C} \int i \mathrm {d} t = e
$$

电路输出量为

![](images/d2be7db7e018dad2d7fa0754738b8b9c9cfced386b3d74b653e95e48ef790833.jpg)  
图 9-4 RLC 网络

$$
y = e _ {c} = \frac {1}{C} \int i d t
$$

1) 设状态变量 $x _ { \mathrm { 1 } } = i$ ， $x _ { 2 } = \frac { 1 } { C } \int i \mathrm { d } t$ ，则状态方程为

$$
\dot {x} _ {1} = - \frac {R}{L} x _ {1} - \frac {1}{L} x _ {2} + \frac {1}{L} e
$$

$$
\dot {x} _ {2} = \frac {1}{C} x _ {1}
$$

输出方程为

$$
y = x _ {2}
$$

其向量-矩阵形式为

$$
\left[ \begin{array}{l} \dot {x} _ {1} \\ \dot {x} _ {2} \end{array} \right] = \left[ \begin{array}{c c} - \frac {R}{L} & - \frac {1}{L} \\ \frac {1}{C} & 0 \end{array} \right] \left[ \begin{array}{l} x _ {1} \\ x _ {2} \end{array} \right] + \left[ \begin{array}{l} \frac {1}{L} \\ 0 \end{array} \right] e
$$

$$
y = \left[ \begin{array}{l l} 0 & 1 \end{array} \right] \left[ \begin{array}{l} x _ {1} \\ x _ {2} \end{array} \right]
$$

简记为

$$
\dot {\boldsymbol {x}} = \boldsymbol {A} \boldsymbol {x} + \boldsymbol {b} e
$$

$$
y = c x
$$

式中

$$
\dot {\boldsymbol {x}} = \left[ \begin{array}{l} \dot {x} _ {1} \\ \dot {x} _ {2} \end{array} \right], \quad \boldsymbol {x} = \left[ \begin{array}{l} x _ {1} \\ x _ {2} \end{array} \right], \quad \boldsymbol {A} = \left[ \begin{array}{c c} - \frac {R}{L} & - \frac {1}{L} \\ \frac {1}{C} & 0 \end{array} \right], \quad \boldsymbol {b} = \left[ \begin{array}{l} \frac {1}{L} \\ 0 \end{array} \right], \quad \boldsymbol {c} = \left[ \begin{array}{l l} 0 & 1 \end{array} \right]
$$

2) 设状态变量 $x _ { \mathrm { 1 } } = i$ ， $x _ { 2 } = \int i { \mathrm d } t$ ，则有

$$
\left[ \begin{array}{l} \dot {x} _ {1} \\ \dot {x} _ {2} \end{array} \right] = \left[ \begin{array}{c c} - \frac {R}{L} & - \frac {1}{L C} \\ 1 & 0 \end{array} \right] \left[ \begin{array}{l} x _ {1} \\ x _ {2} \end{array} \right] + \left[ \begin{array}{l} \frac {1}{L} \\ 0 \end{array} \right] e, \quad y = \left[ \begin{array}{c c} 0 & \frac {1}{C} \end{array} \right] \left[ \begin{array}{l} x _ {1} \\ x _ {2} \end{array} \right]
$$

3) 设状态变量 $x _ { 1 } = \frac { 1 } { C } \int i { \mathrm d } t + R i$ ， $x _ { 2 } = \frac { 1 } { C } \int i \mathrm { d } t$ ，则

$$
x _ {1} = x _ {2} + R i, \quad L \frac {\mathrm {d} i}{\mathrm {d} t} = - x _ {1} + e
$$

故 ${ \dot { x } } _ { 1 } = { \dot { x } } _ { 2 } + R { \frac { \mathrm { d } i } { \mathrm { d } t } } = { \frac { 1 } { R C } } ( x _ { 1 } - x _ { 2 } ) + { \frac { R } { L } } ( - x _ { 1 } + e )$

$$
\dot {x} _ {2} = \frac {1}{C} i = \frac {1}{R C} \left(x _ {1} - x _ {2}\right)
$$

$$
y = x _ {2}
$$

其向量-矩阵形式为

$$
\left[ \begin{array}{l} \dot {x} _ {1} \\ \dot {x} _ {2} \end{array} \right] = \left[ \begin{array}{c c} \frac {1}{R C} - \frac {R}{L} & - \frac {1}{R C} \\ \frac {1}{R C} & - \frac {1}{R C} \end{array} \right] \left[ \begin{array}{l} x _ {1} \\ x _ {2} \end{array} \right] + \left[ \begin{array}{l} \frac {R}{L} \\ 0 \end{array} \right] e
$$

$$
y = \left[ \begin{array}{l l} 0 & 1 \end{array} \right] \left[ \begin{array}{c} x _ {1} \\ x _ {2} \end{array} \right]
$$

由上可见，系统的状态空间表达式不具有唯一性。选取不同的状态变量，便会有不同的状态空间表达式，但它们都描述了同一系统。可以推断，描述同一系统的不同状态空间表达式之间一定存在着某种线性变换关系。现研究本例题中两组状态变量之间的关系。

设 $x _ { 1 } = i , x _ { 2 } = \frac { 1 } { C } \int i \mathrm { d } t , \overline { { x } } _ { 1 } = i , \overline { { x } } _ { 2 } = \int i \mathrm { d } t$ ，则有

$$
x _ {1} = \bar {x} _ {1}, x _ {2} = \frac {1}{C} \bar {x} _ {2}
$$

其相应的向量-矩阵形式为

$$
x = P \bar {x}
$$

其中 $\pmb { x } = \left[ \begin{array} { l } { x _ { 1 } } \\ { x _ { 2 } } \end{array} \right] , \quad \overline { { \pmb { x } } } = \left[ \begin{array} { l } { \overline { { \pmb { x } } } _ { 1 } } \\ { \overline { { \pmb { x } } } _ { 2 } } \end{array} \right] , \quad \pmb { P } = \left[ \begin{array} { l l } { 1 } & { 0 } \\ { 0 } & { \frac { 1 } { C } } \end{array} \right]$

以上说明只要令 $\boldsymbol { x } = \boldsymbol { P } \boldsymbol { \overline { { x } } }$ ， $P$ 为非奇异变换矩阵，便可将 $x _ { 1 }$ ， $x _ { 2 }$ 变换为 $\overline { { x } } _ { 1 }$ ， $\overline { { x } } _ { 2 }$ 。若取任意的非奇异变换阵 $P$ ，便可变换出无穷多组状态变量，这就说明状态变量的选择不具有唯一性。对于图 9-4所示 RLC网络来说，由于电容端电压和电感电流容易测量，通常选择这些物理量作为状态变量。

(2) 由系统微分方程建立状态空间表达式

按系统输入量中是否含有导数项来分别研究。

1) 系统输入量中不含导数项。这种单输入-单输出线性定常连续系统微分方程的一般形式为

$$
y ^ {(n)} + a _ {n - 1} y ^ {(n - 1)} + a _ {n - 2} y ^ {(n - 2)} + \dots + a _ {1} \dot {y} + a _ {0} y = \beta_ {0} u \tag {9-5}
$$

式中， $y$ ， $u$ 分别为系统的输出、输入量； $a _ { 0 }$ ， $a _ { 1 }$ ，…， $a _ { n - 1 }$ ， $\beta _ { 0 }$ 是由系统特性确定的常系数。由于给定 $n$ 个初值 $y ( 0 )$ ， ${ \dot { y } } \left( 0 \right)$ ，…， $y ^ { n - 1 } ( 0 )$ 及 $t \geqslant 0$ 的 $u ( t )$ 时，可唯一确定 $t > 0$ 时系统的行为，可选取 $n$ 个状态变量为 $x _ { 1 } { = } y$ ， $x _ { 2 } = \dot { y }$ ，…， $x _ { n } = y ^ { ( n - 1 ) }$ ，故式(9-5)可化为

$$
\left\{ \begin{array}{l} \dot {x} _ {1} = x _ {2} \\ \dot {x} _ {2} = x _ {3} \\ \vdots \\ \dot {x} _ {n - 1} = x _ {n} \\ \dot {x} _ {n} = - a _ {0} x _ {1} - a _ {1} x _ {2} - \dots - a _ {n - 1} x _ {n} + \beta_ {0} u \\ y = x _ {1} \end{array} \right. \tag {9-6}
$$

其向量-矩阵形式为

$$
\dot {\boldsymbol {x}} = \boldsymbol {A} \boldsymbol {x} + \boldsymbol {b} u \tag {9-7}
$$

$$
y = c x
$$

式中

$$
\boldsymbol {x} = \left[ \begin{array}{l} x _ {1} \\ x _ {2} \\ \vdots \\ x _ {n - 1} \\ x _ {n} \end{array} \right], \quad \boldsymbol {A} = \left[ \begin{array}{c c c c c} 0 & 1 & 0 & \dots & 0 \\ 0 & 0 & 1 & \dots & 0 \\ \vdots & \vdots & \vdots & & \vdots \\ 0 & 0 & 0 & \dots & 1 \\ - a _ {0} & - a _ {1} & - a _ {2} & \dots & - a _ {n - 1} \end{array} \right], \quad \boldsymbol {b} = \left[ \begin{array}{l} 0 \\ 0 \\ \vdots \\ 0 \\ \beta_ {0} \end{array} \right]
$$

$$
\boldsymbol {c} = \left[ \begin{array}{l l l l} 1 & 0 & \dots & 0 \end{array} \right]
$$

按式(9-6)绘制的结构图称为状态变量图，如图 9-5 所示。每个积分器的输出都是对应的状态变量，状态方程由各积分器的输入-输出关系确定，输出方程在输出端获得。

![](images/d0d0e93b6752ac6982994fff3faaea607ceab17f69e0a542cd225105c9bc40ec.jpg)  
图 9-5 输入量中不含导数项时的系统状态变量图

2) 系统输入量中含有导数项。这种单输入-单输出线性定常连续系统微分方程的一般形式为

$$
y ^ {(n)} + a _ {n - 1} y ^ {(n - 1)} + a _ {n - 2} y ^ {(n - 2)} + \dots + a _ {1} \dot {y} + a _ {0} y \tag {9-8}
$$

$$
= b _ {n} u ^ {(n)} + b _ {n - 1} u ^ {(n - 1)} + \dots + b _ {1} \dot {u} + b _ {0} u
$$

一般输入导数项的次数小于或等于系统的阶数 $n$ 。首先研究 $b _ { n } { \neq } 0$ 时的情况。为了避免在状态方程中出现输入导数项，可按如下规则选择一组状态变量，设

$$
\left\{ \begin{array}{l} x _ {1} = y - h _ {0} u \\ x _ {i} = \dot {x} _ {i - 1} - h _ {i - 1} u; i = 2, 3, \dots , n \end{array} \right. \tag {9-9}
$$

其展开式为

$$
\left\{ \begin{array}{l} x _ {1} = y - h _ {0} u \\ x _ {2} = \dot {x} _ {1} - h _ {1} u = \dot {y} - h _ {0} \dot {u} - h _ {1} u \\ x _ {3} = \dot {x} _ {2} - h _ {2} u = \ddot {y} - h _ {0} \ddot {u} - h _ {1} \dot {u} - h _ {2} u \\ \vdots \\ x _ {n - 1} = \dot {x} _ {n - 2} - h _ {n - 2} u = y ^ {(n - 2)} - h _ {0} u ^ {(n - 2)} - h _ {1} u ^ {(n - 3)} - \dots - h _ {n - 2} u \\ x _ {n} = \dot {x} _ {n - 1} - h _ {n - 1} u = y ^ {(n - 1)} - h _ {0} u ^ {(n - 1)} - h _ {1} u ^ {(n - 2)} - \dots - h _ {n - 1} u \end{array} \right. \tag {9-10}
$$

式中， $h 0 , h _ { 1 } , h _ { 2 } , \cdots , h _ { n - 1 }$ 是 $n$ 个待定常数。由式(9-10)的第一个方程可得输出方程

$$
y = x _ {1} + h _ {0} u
$$

其余可得 $n { - } 1$ 个状态方程

$$
\begin{array}{l} \dot {x} _ {1} = x _ {2} + h _ {1} u \\ \dot {x} _ {2} = x _ {3} + h _ {2} u \\ \begin{array}{c} \vdots \\ \vdots \\ \vdots \end{array} \\ \dot {x} _ {n - 1} = x _ {n} + h _ {n - 1} u \\ \end{array}
$$

对 $x _ { n }$ 求导数并考虑式(9-8)，有

$$
\begin{array}{l} \dot {x} _ {n} = y ^ {(n)} - h _ {0} u ^ {(n)} - h _ {1} u ^ {(n - 1)} - \dots - h _ {n - 1} \dot {u} = \left(- a _ {n - 1} y ^ {(n - 1)} - a _ {n - 2} y ^ {(n - 2)} \right. \\ - \dots - a _ {1} \dot {y} - a _ {0} y + b _ {0} u ^ {(n)} + \dots + b _ {1} \dot {u} + b _ {0} u) - h _ {0} u ^ {(n)} - h _ {1} u ^ {(n - 1)} - \dots - h _ {n - 1} \dot {u} \\ \end{array}
$$

由式(9-10)将 $y ^ { ( n - 1 ) }$ , …, y , y 均以 $x _ { i }$ 及 $u$ 的各阶导数表示，经整理可得

$$
\begin{array}{l} \dot {x} _ {n} = - a _ {0} x _ {1} - a _ {1} x _ {2} - \dots - a _ {n - 2} x _ {n - 1} - a _ {n - 1} x _ {n} + \left(b _ {n} - h _ {0}\right) u ^ {(n)} \\ + \left(b _ {n - 1} - h _ {1} - a _ {n - 1} h _ {0}\right) u ^ {(n - 1)} + \left(b _ {n - 2} - h _ {2} - a _ {n - 1} h _ {1} - a _ {n - 2} h _ {0}\right) u ^ {(n - 2)} \\ + \dots + \left(b _ {1} - h _ {n - 1} - a _ {n - 1} h _ {n - 2} - a _ {n - 2} h _ {n - 3} - \dots - a _ {1} h _ {0}\right) \dot {u} \\ + \left(b _ {0} - a _ {n - 1} h _ {n - 1} - a _ {n - 2} h _ {n - 2} - \dots - a _ {1} h _ {1} - a _ {0} h _ {0}\right) u \\ \end{array}
$$

令上式中 $u$ 的各阶导数项的系数为零，可确定各 $h$ 值

$$
\begin{array}{l} h _ {0} = b _ {n} \\ h _ {1} = b _ {n - 1} - a _ {n - 1} h _ {0} \\ h _ {2} = b _ {n - 2} - a _ {n - 1} h _ {1} - a _ {n - 2} h _ {0} \\ \begin{array}{c} \vdots \\ \vdots \end{array} \\ h _ {n - 1} = b _ {1} - a _ {n - 1} h _ {n - 2} - a _ {n - 2} h _ {n - 3} - \dots - a _ {1} h _ {0} \\ \end{array}
$$

记 $h _ { n } = b _ { 0 } - a _ { n - 1 } h _ { n - 1 } - a _ { n - 2 } h _ { n - 2 } - \cdots - a _ { 1 } h _ { 1 } - a _ { 0 } h _ { 0 }$ ，故

$$
\dot {x} _ {n} = - a _ {0} x _ {1} - a _ {1} x _ {2} - \dots - a _ {n - 2} x _ {n - 1} - a _ {n - 1} x _ {n} + h _ {n} u
$$

则式(9-8)的向量-矩阵形式的动态方程为

$$
\dot {\boldsymbol {x}} = \boldsymbol {A} \boldsymbol {x} + \boldsymbol {b} u, \quad y = \boldsymbol {c x} + d u \tag {9-11}
$$

式中 $A = { \left[ \begin{array} { l l l l l } { 0 } & { 1 } & { 0 } & { \cdots } & { 0 } \\ { 0 } & { 0 } & { 1 } & { \cdots } & { 0 } \\ { \vdots } & { \vdots } & { \vdots } & & { \vdots } \\ { 0 } & { 0 } & { 0 } & { \cdots } & { 1 } \\ { - a _ { 0 } } & { - a _ { 1 } } & { - a _ { 2 } } & { \cdots } & { - a _ { n - 1 } } \end{array} \right] } , \quad \pmb { b } = { \left[ \begin{array} { l } { h _ { 1 } } \\ { h _ { 2 } } \\ { \vdots } \\ { h _ { n - 1 } } \\ { h _ { n } } \end{array} \right] }$

$$
c = \left[ \begin{array}{l l l l} 1 & 0 & \dots & 0 \end{array} \right], \quad d = h _ {0}
$$

式(9-8)的状态变量图见图 9-6。若输入量中仅含 $m$ 次导数且 $m { < } n$ ，可将高于 $m$ 次导数项的系数置零，仍可应用上述所得公式。

当 $b _ { n } { = } 0$ 时，可以令上述公式中的 $h _ { 0 } { = } 0$ 得到所需要的结果，也可按如下规则选择另一组状态变量。设

$$
\left\{ \begin{array}{l} x _ {n} = y \\ x _ {i} = \dot {x} _ {i + 1} + a _ {i} y - b _ {i} u; i = 1, 2, \dots , n - 1 \end{array} \right. \tag {9-12}
$$

其展开式为

![](images/ecf96d28ff476a189442368dee480b77666fafdb1c6073a04162944032b5803c.jpg)  
图 9-6 输入量中含有导数项时的系统状态变量图

$$
\begin{array}{l} x _ {n - 1} = \dot {x} _ {n} + a _ {n - 1} y - b _ {n - 1} u = \dot {y} + a _ {n - 1} y - b _ {n - 1} u \\ x _ {n - 2} = \dot {x} _ {n - 1} + a _ {n - 2} y - b _ {n - 2} u = \ddot {y} + a _ {n - 1} \dot {y} - b _ {n - 1} \dot {u} + a _ {n - 2} y - b _ {n - 2} u \\ \end{array}
$$

$$
x _ {2} = \dot {x} _ {3} + a _ {2} y - b _ {2} u = y ^ {(n - 2)} + a _ {n - 1} y ^ {(n - 3)} - b _ {n - 1} u ^ {(n - 3)} + a _ {n - 2} y ^ {(n - 4)} - b _ {n - 2} u ^ {(n - 4)} + \dots + a _ {2} y - b _ {2} u
$$

$$
x _ {1} = \dot {x} _ {2} + a _ {1} y - b _ {1} u = y ^ {(n - 1)} + a _ {n - 1} y ^ {(n - 2)} - b _ {n - 1} u ^ {(n - 2)} + a _ {n - 2} y ^ {(n - 3)} - b _ {n - 2} u ^ {(n - 3)} + \dots + a _ {1} y - b _ {1} u
$$

故有 $n { - } 1$ 个状态方程

$$
\dot {x} _ {n} = x _ {n - 1} - a _ {n - 1} x _ {n} + b _ {n - 1} u
$$

$$
\dot {x} _ {n - 1} = x _ {n - 2} - a _ {n - 2} x _ {n} + b _ {n - 2} u
$$

$$
\begin{array}{c} \bullet \\ \vdots \\ \bullet \end{array}
$$

$$
\dot {x} _ {2} = x _ {1} - a _ {1} x _ {n} + b _ {1} u
$$

对 $x _ { 1 }$ 求导数且考虑式(9-8)，经整理有

$$
\dot {x} _ {1} = - a _ {0} x _ {n} + b _ {0} u
$$

则式(9-8)在 $b _ { n } { = } 0$ 时的动态方程为

$$
\dot {\boldsymbol {x}} = \boldsymbol {A} \boldsymbol {x} + \boldsymbol {b} \boldsymbol {u}, \quad \boldsymbol {y} = \boldsymbol {c} \boldsymbol {x} \tag {9-13}
$$

式中

$$
\boldsymbol {A} = \left[ \begin{array}{l l l l l} 0 & 0 & \dots & 0 & - a _ {0} \\ 1 & 0 & \dots & 0 & - a _ {1} \\ 0 & 1 & \dots & 0 & - a _ {2} \\ \vdots & \vdots & & \vdots & \vdots \\ 0 & 0 & \dots & 1 & - a _ {n - 1} \end{array} \right], \quad \boldsymbol {b} = \left[ \begin{array}{l} b _ {0} \\ b _ {1} \\ b _ {2} \\ \vdots \\ b _ {n - 1} \end{array} \right], \quad \boldsymbol {c} = \left[ \begin{array}{l l l l} 0 & 0 & \dots & 1 \end{array} \right]
$$

例 9-2 设二阶系统微分方程为

$$
\ddot {y} + 2 \zeta \omega \dot {y} + \omega^ {2} y = T \dot {u} + u
$$

试求系统状态空间表达式。

解 设状态变量 $x _ { 1 } = y - h _ { 0 } u$ ， $x _ { 2 } = \dot { x } _ { 1 } - h _ { 1 } u = \dot { y } - h _ { 0 } \dot { u } - h _ { 1 } u$ ，故有

$$
y = x _ {1} + h _ {0} u, \quad \dot {x} _ {1} = x _ {2} + h _ {1} u
$$

对 $x _ { 2 }$ 求导数且考虑 $x _ { 1 }$ ， $x _ { 2 }$ 及系统微分方程,有

$$
\begin{array}{l} \dot {x} _ {2} = \ddot {y} - h _ {0} \dot {u} - h _ {1} \dot {u} = (- \omega^ {2} y - 2 \zeta \omega \dot {y} + T \dot {u} + u) - h _ {0} \dot {u} - h _ {1} \dot {u} \\ = - \omega^ {2} x _ {1} - 2 \zeta \omega x _ {2} - h _ {0} \ddot {u} + (T - 2 \zeta \omega h _ {0} - h _ {1}) \dot {u} + (1 - \omega^ {2} h _ {0} - 2 \zeta \omega h _ {1}) u \\ \end{array}
$$

令 $\ddot { u }$ ， $\dot { u }$ 项的系数为零，可得

$$
h _ {0} = 0, \quad h _ {1} = T
$$

故 $\dot { x } _ { 2 } = - \omega ^ { 2 } x _ { 1 } - 2 \zeta \omega x _ { 2 } + ( 1 - 2 \zeta \omega T ) u$

系统的状态空间表达式为

$$
\left[ \begin{array}{l} \dot {x} _ {1} \\ \dot {x} _ {2} \end{array} \right] = \left[ \begin{array}{c c} 0 & 1 \\ - \omega^ {2} & - 2 \zeta \omega \end{array} \right] \left[ \begin{array}{l} x _ {1} \\ x _ {2} \end{array} \right] + \left[ \begin{array}{c} T \\ 1 - 2 \zeta \omega T \end{array} \right] u, \quad y = \left[ \begin{array}{l l} 1 & 0 \end{array} \right] \left[ \begin{array}{l} x _ {1} \\ x _ {2} \end{array} \right]
$$

(3) 由系统传递函数建立状态空间表达式

式(9-8)所对应的系统传递函数为

$$
G (s) = \frac {Y (s)}{U (s)} = \frac {b _ {n} s ^ {n} + b _ {n - 1} s ^ {n - 1} + b _ {n - 2} s ^ {n - 2} + \cdots + b _ {1} s + b _ {0}}{s ^ {n} + a _ {n - 1} s ^ {n - 1} + a _ {n - 2} s ^ {n - 2} + \cdots + a _ {1} s + a _ {0}} \tag {9-14}
$$

应用综合除法有

$$
G (s) = b _ {n} + \frac {\beta_ {n - 1} s ^ {n - 1} + \beta_ {n - 2} s ^ {n - 2} + \cdots + \beta_ {1} s + \beta_ {0}}{s ^ {n} + a _ {n - 1} s ^ {n - 1} + a _ {n - 2} s ^ {n - 2} + \cdots + a _ {1} s + a _ {0}} \triangleq b _ {n} + \frac {N (s)}{D (s)} \tag {9-15}
$$

式中， $b _ { n }$ 是直接联系输入与输出量的前馈系数，当 $G ( s )$ 的分母次数大于分子次数时， $b _ { n } { = } 0$ ，$\frac { N ( s ) } { D ( s ) }$ 是严格有理真分式，其系数由综合除法得到为

$$
\beta_ {0} = b _ {0} - a _ {0} b _ {n}
$$

$$
\beta_ {1} = b _ {1} - a _ {1} b _ {n}
$$

$$
\beta_ {n - 2} = b _ {n - 2} - a _ {n - 2} b _ {n}
$$

$$
\beta_ {n - 1} = b _ {n - 1} - a _ {n - 1} b _ {n}
$$

下面介绍由 $\frac { N ( s ) } { D ( s ) }$ 导出几种标准形式动态方程的方法。

1) $\frac { N ( s ) } { D ( s ) }$ 串联分解的情况。将 $\frac { N ( s ) } { D ( s ) }$ 分解为两部分相串联，如图 9-7 所示， $z$ 为中间变量，z， $y$ 应满足

$$
z ^ {(n)} + a _ {n - 1} z ^ {(n - 1)} + \dots + a _ {1} \dot {z} + a _ {0} z = u
$$

$$
y = \beta_ {n - 1} z ^ {(n - 1)} + \dots + \beta_ {1} \dot {z} + \beta_ {0} z
$$

![](images/e3417d2cf464a2f7a2fdd4993054e9e73dc74263efa8187c5aa083969b681d7e.jpg)  
图 9-7 $\frac { N ( s ) } { D ( s ) }$ 的串联分解

选取状态变量

$$
x _ {1} = z, \quad x _ {2} = \dot {z}, \quad x _ {3} = \ddot {z}, \quad \dots , \quad x _ {n} = z ^ {(n - 1)}
$$

则状态方程为

$$
\dot {x} _ {1} = x _ {2}
$$

$$
\dot {x} _ {2} = x _ {3}
$$

$$
\begin{array}{c} \vdots \\ \vdots \end{array}
$$

$$
\begin{array}{l} \dot {x} _ {n} = - a _ {0} z - a _ {1} \dot {z} - \dots - a _ {n - 1} z ^ {(n - 1)} + u \\ = - a _ {0} x _ {1} - a _ {1} x _ {2} - \dots - a _ {n - 1} x _ {n} + u \\ \end{array}
$$

输出方程为

$$
y = - \beta_ {0} x _ {1} - \beta_ {1} x _ {2} - \dots - \beta_ {n - 1} x _ {n}
$$

其向量-矩阵形式的动态方程为

$$
\dot {\boldsymbol {x}} = \boldsymbol {A} \boldsymbol {x} + \boldsymbol {b} u, \quad \boldsymbol {y} = \boldsymbol {c x} \tag {9-16}
$$

式中 $A = { \left[ \begin{array} { l l l l l } { 0 } & { 1 } & { 0 } & { \cdots } & { 0 } \\ { 0 } & { 0 } & { 1 } & { \cdots } & { 0 } \\ { \vdots } & { \vdots } & { \vdots } & & { \vdots } \\ { 0 } & { 0 } & { 0 } & { \cdots } & { 1 } \\ { - a _ { 0 } } & { - a _ { 1 } } & { - a _ { 2 } } & { \cdots } & { - a _ { n - 1 } } \end{array} \right] } , \quad b = { \left[ \begin{array} { l } { 0 } \\ { 0 } \\ { \vdots } \\ { 0 } \\ { 1 } \\ { 1 } \end{array} \right] } , \quad c = [ \beta _ { 0 } \quad \beta _ { 1 } \quad \cdots \quad \beta _ { n - 1 } ]$

请读者注意 $\pmb { A }$ ， $\pmb { b }$ 的形状特征，这种 $\pmb { A }$ 阵又称友矩阵，若状态方程中的 $\pmb { A }$ ， $\pmb { b }$ 具有这种形式，则称为可控标准型。当 $\beta _ { 1 } = \beta _ { 2 } = \cdots = \beta _ { n - 1 } = 0$ 时， $A , b$ 的形式不变， $\pmb { c } = [ \beta _ { 0 } \_ 0 \cdots \ 0 ] _ { \emptyset }$ 。

因而，当 ( ) nG s b $G ( s ) = b _ { n } + { \frac { N ( s ) } { D ( s ) } }$ ( ) N s 时，A，b 不变， n y b u   cx 。 $\pmb { A }$ $\pmb { b }$ $y = c { \mathbf { x } } + b _ { n } u _ { \mathrm { ~ o ~ } } \ \frac { N ( s ) } { D ( s ) }$ 串联分解时系统的可控标准型状态变量图如图 9-8 所示。

![](images/cc8a1ae3b98e9295e814e13f071a556a13592f7c5cff242715bb27701950f830.jpg)  
图 9-8 $\frac { N ( s ) } { D ( s ) }$ 串联分解时系统的可控标准型状态变量图

当 $b _ { n } { = } 0$ 时，若按式(9-12)选取状态变量，则系统的 $\pmb { A }$ ，b，c 矩阵为

$$
\boldsymbol {A} = \left[ \begin{array}{l l l l l} 0 & 0 & \dots & 0 & - a _ {0} \\ 1 & 0 & \dots & 0 & - a _ {1} \\ 0 & 1 & \dots & 0 & - a _ {2} \\ \vdots & \vdots & & \vdots & \vdots \\ 0 & 0 & \dots & 1 & - a _ {n - 1} \end{array} \right], \quad \boldsymbol {b} = \left[ \begin{array}{l} \beta_ {0} \\ \beta_ {1} \\ \beta_ {2} \\ \vdots \\ \beta_ {n - 1} \end{array} \right], \quad \boldsymbol {c} = \left[ \begin{array}{l l l l} 0 & \dots & 0 & 1 \end{array} \right]
$$

请注意 A、 $c$ 的形状特征，此处 $\pmb { A }$ 矩阵是友矩阵的转置。若动态方程中的 A、 $c$ 具有这种形式，则称为可观测标准型。

由上可见，可控标准型与可观测标准型的各矩阵之间存在如下关系：

$$
\boldsymbol {A} _ {c} = \boldsymbol {A} _ {o} ^ {\mathrm {T}}, \quad \boldsymbol {b} _ {c} = \boldsymbol {c} _ {o} ^ {\mathrm {T}}, \quad \boldsymbol {c} _ {c} = \boldsymbol {b} _ {o} ^ {\mathrm {T}} \tag {9-17}
$$

式中，下标 $c$ 表示可控标准型； $o$ 表示可观测标准型；T 为转置符号。式(9-17)所示关系称为对偶关系。关于系统的可控和可观测等概念，后面还要进行较详细的论述。

例 9-3 试列写例 9-2所示系统的可控标准型、可观测标准型动态方程，并分别确定状态变量与输入、输出量的关系。

解 该系统的传递函数为

$$
G (s) = \frac {Y (s)}{U (s)} = \frac {T s + 1}{s ^ {2} + 2 \zeta \omega s + \omega^ {2}}
$$

可控标准型动态方程的各矩阵为

$$
\boldsymbol {x} _ {c} = \left[ \begin{array}{l} x _ {c 1} \\ x _ {c 2} \end{array} \right], \quad \boldsymbol {A} _ {c} = \left[ \begin{array}{l l} 0 & 1 \\ - \omega^ {2} & - 2 \zeta \omega \end{array} \right], \quad \boldsymbol {b} _ {c} = \left[ \begin{array}{l} 0 \\ 1 \end{array} \right], \quad \boldsymbol {c} _ {c} = \left[ \begin{array}{l l} 1 & T \end{array} \right]
$$

由 $G ( s )$ 串联分解并引入中间变量 $z$ 有

$$
\ddot {z} + 2 \zeta \omega \dot {z} + \omega^ {2} z = u
$$

$$
y = T \dot {z} + z
$$

对 $y$ 求导数并考虑上述关系式则有

$$
\dot {y} = T \ddot {z} + \dot {z} = (1 - 2 \zeta \omega T) \dot {z} - \omega^ {2} T z + T u
$$

令 $x _ { c 1 } = z$ ， $x _ { c 2 } = \dot { z }$ ，可导出状态变量与输入、输出量的关系：

$$
x _ {c 1} = \left[ - T \ddot {y} + (1 - 2 \zeta \omega T) y + T ^ {2} u \right] / \left(1 - 2 \zeta \omega T + \omega^ {2} T ^ {2}\right)
$$

$$
x _ {c 2} = \left(\dot {y} + \omega^ {2} T y - T u\right) / \left(1 - 2 \zeta \omega T + \omega^ {2} T ^ {2}\right)
$$

可观测标准型动态方程各矩阵为

$$
\boldsymbol {x} _ {o} = \left[ \begin{array}{l} x _ {o 1} \\ x _ {o 2} \end{array} \right], \quad \boldsymbol {A} _ {o} = \left[ \begin{array}{c c} 0 & - \omega^ {2} \\ 1 & - 2 \zeta \omega \end{array} \right], \quad \boldsymbol {b} _ {o} = \left[ \begin{array}{l} 1 \\ T \end{array} \right], \quad \boldsymbol {c} _ {o} = \left[ \begin{array}{l l} 0 & 1 \end{array} \right]
$$

根据式(9-12)可以写出状态变量与输入、输出量的关系

$$
x _ {o 1} = \dot {y} + 2 \zeta \omega y - T u
$$

$$
x _ {o 2} = y
$$

图 9-9 与图 9-10 分别示出了该系统可控标准型与可观测标准型的状态变量图。

2) $\frac { N ( s ) } { D ( s ) }$ 只含单实极点时的情况。当 $\frac { N ( s ) } { D ( s ) }$ 只含单实极点时，除了可化为上述可控标准型或可观测标准型动态方程以外，还可化为对角型动态方程，其 $\pmb { A }$ 阵是一个对角阵。

![](images/11f448441cc1b39d9251ba7315630d1e4f48d47e2b3954fef0d39b8445b06d30.jpg)  
图 9-9 例 9-3 系统可控标准型状态变量图

![](images/a3d733c6d1983effe19b149b9b6fccfb9fe3aa7552cf60e29ffea12742c8ae51.jpg)  
图 9-10 例9-3系统可观测标准型状态变量图

设 $D ( s )$ 可分解为

$$
D (s) = \left(s - \lambda_ {1}\right) \left(s - \lambda_ {2}\right) \dots \left(s - \lambda_ {n}\right)
$$

式中， $\lambda _ { 1 }$ , …, $\lambda _ { n }$ 为系统的单实极点，则传递函数可展成部分分式之和

$$
\frac {Y (s)}{U (s)} = \frac {N (s)}{D (s)} = \sum_ {i = 1} ^ {n} \frac {c _ {i}}{s - \lambda_ {i}}
$$

而 ic  $c _ { i } = \left[ \frac { N ( s ) } { D ( s ) } ( s - \lambda _ { i } ) \right] \Biggr | _ { s = \lambda }$ ) ( ) i s  ，为 $\frac { N ( s ) } { D ( s ) }$ 在极点 $\lambda _ { i }$ 处的留数，且有 is  

$$
Y (s) = \sum_ {i = 1} ^ {n} \frac {c _ {i}}{s - \lambda_ {i}} U (s)
$$

若令状态变量

$$
X _ {i} (s) = \frac {1}{s - \lambda_ {i}} U (s); \quad i = 1, 2, \dots , n
$$

其反变换结果为

$$
\dot {x} _ {i} (t) = \lambda_ {i} x _ {i} (t) + u (t)
$$

$$
y (t) = \sum_ {i = 1} ^ {n} c _ {i} x _ {i} (t)
$$

展开得

$$
\dot {x} _ {1} = \lambda_ {1} x _ {1} + u
$$

$$
\dot {x} _ {2} = \lambda_ {2} x _ {2} + u
$$

$$
\dot {x} _ {n} = \lambda_ {n} x _ {n} + u
$$

$$
y = c _ {1} x _ {1} + c _ {2} x _ {2} + \dots + c _ {n} x _ {n}
$$

其向量-矩阵形式为

$$
\left[ \begin{array}{c} \dot {x} _ {1} \\ \dot {x} _ {2} \\ \vdots \\ \dot {x} _ {n} \end{array} \right] = \left[ \begin{array}{c c c c} \lambda_ {1} & & & 0 \\ & \lambda_ {2} & & \\ & & \ddots & \\ 0 & & & \lambda_ {n} \end{array} \right] \left[ \begin{array}{c} x _ {1} \\ x _ {2} \\ \vdots \\ x _ {n} \end{array} \right] + \left[ \begin{array}{l} 1 \\ 1 \\ \vdots \\ 1 \end{array} \right] u, y = \left[ \begin{array}{c c c c} c _ {1} & c _ {2} & \dots & c _ {n} \end{array} \right] \left[ \begin{array}{c} x _ {1} \\ x _ {2} \\ \vdots \\ x _ {n} \end{array} \right] \tag {9-18}
$$

其状态变量图如图 9-11(a)所示。

若令状态变量

$$
X _ {i} (s) = \frac {c _ {i}}{s - \lambda_ {i}} U (s); \quad i = 1, 2, \dots , n
$$

则 $Y ( s ) = \sum _ { i = 1 } ^ { n } X _ { i } ( s )$

进行反变换并展开有

$$
\dot {x} _ {1} = \lambda_ {1} x _ {1} + c _ {1} u
$$

$$
\dot {x} _ {2} = \lambda_ {2} x _ {2} + c _ {2} u
$$

$$
\dot {x} _ {n} = \lambda_ {n} x _ {n} + c _ {n} u
$$

$$
y = x _ {1} + x _ {2} + \dots + x _ {n}
$$

其向量-矩阵形式为

$$
\left[ \begin{array}{c} \dot {x} _ {1} \\ \dot {x} _ {2} \\ \vdots \\ \dot {x} _ {n} \end{array} \right] = \left[ \begin{array}{c c c c} \lambda_ {1} & & & 0 \\ & \lambda_ {2} & & \\ & & \ddots & \\ 0 & & & \lambda_ {n} \end{array} \right] \left[ \begin{array}{c} x _ {1} \\ x _ {2} \\ \vdots \\ x _ {n} \end{array} \right] + \left[ \begin{array}{c} c _ {1} \\ c _ {2} \\ \vdots \\ c _ {n} \end{array} \right] u, y = [ 1 \quad 1 \quad \dots \quad 1 ] \left[ \begin{array}{c} x _ {1} \\ x _ {2} \\ \vdots \\ x _ {n} \end{array} \right] \tag {9-19}
$$

其状态变量图如图 9-11(b)所示。显见式(9-19)与式(9-18)存在对偶关系。

![](images/df9b15682e10a4908dd87b85a25161c85031a5e069037245aa49cc9b9461c046.jpg)

![](images/099c1911d530487294fb380342868a182211e69048f470ae78ed803f682ae5eb.jpg)  
(b)可观对角型  
图 9-11 系统对角型动态方程的状态变量图

3) $\frac { N ( s ) } { D ( s ) }$ 含重实极点时的情况。当传递函数除含单实极点之外还含有重实极点时，不仅可化为可控、可观测标准型，还可化为约当标准型动态方程，其 A 阵是一个含约当块的矩阵。设 $D ( s )$ 可分解为

$$
D (s) = \left(s - \lambda_ {1}\right) ^ {3} \left(s - \lambda_ {4}\right) \dots \left(s - \lambda_ {n}\right)
$$

式中， $\lambda _ { 1 }$ 为三重实极点； $\lambda _ { 4 }$ ，…， $\lambda _ { n }$ 为单实极点，则传递函数可展成下列部分分式之和：

$$
\frac {Y (s)}{U (s)} = \frac {N (s)}{D (s)} = \frac {c _ {1 1}}{(s - \lambda_ {1}) ^ {3}} + \frac {c _ {1 2}}{(s - \lambda_ {1}) ^ {2}} + \frac {c _ {1 3}}{(s - \lambda_ {1})} + \sum_ {i = 4} ^ {n} \frac {c _ {i}}{s - \lambda_ {i}}
$$

其状态变量的选取方法与只含单实极点时相同，可分别得出向量-矩阵形式的动态方程：

$$
\left[ \begin{array}{c} \dot {x} _ {1 1} \\ \dot {x} _ {1 2} \\ \dot {x} _ {1 3} \\ \dots \\ \dot {x} _ {4} \\ \vdots \\ \dot {x} _ {n} \end{array} \right] = \left[ \begin{array}{c c c c c c} \lambda_ {1} & 1 & & & & \\ & \lambda_ {1} & 1 & & 0 & \\ & & \lambda_ {1} & & \\ \dots & \dots & \dots & \lambda_ {4} & & \\ & 0 & & & \ddots & \\ & & & & & \lambda_ {n} \end{array} \right] \left[ \begin{array}{c} x _ {1 1} \\ x _ {1 2} \\ x _ {1 3} \\ \dots \\ x _ {4} \\ \vdots \\ x _ {n} \end{array} \right] + \left[ \begin{array}{c} 0 \\ 0 \\ 1 \\ \dots \\ 1 \\ \vdots \\ 1 \end{array} \right] u \tag {9-20}
$$

$$
y = \left[ \begin{array}{l l l l l} c _ {1 1} & c _ {1 2} & c _ {1 3} & c _ {4} & \dots \\ c _ {n} \end{array} \right] \boldsymbol {x}
$$

$$
\left[ \begin{array}{c} \dot {x} _ {1 1} \\ \dot {x} _ {1 2} \\ \dot {x} _ {1 3} \\ \dots \\ \dot {x} _ {4} \\ \vdots \\ \dot {x} _ {n} \end{array} \right] = \left[ \begin{array}{c c c c c c c} \lambda_ {1} & & & & & & \\ 1 & \lambda_ {1} & & & & 0 \\ & 1 & \lambda_ {1} & & & \\ \dots & \dots & \dots & \dots & \lambda_ {4} & & \\ & 0 & & & & \ddots & \\ & & & & & & \lambda_ {n} \end{array} \right] \left[ \begin{array}{c} x _ {1 1} \\ x _ {1 2} \\ x _ {1 3} \\ \dots \\ x _ {4} \\ \vdots \\ x _ {n} \end{array} \right] + \left[ \begin{array}{c} c _ {1 1} \\ c _ {1 2} \\ c _ {1 3} \\ \dots \\ c _ {4} \\ \vdots \\ c _ {n} \end{array} \right] u
$$

$$
y = \left[ \begin{array}{l l l l l l} 0 & 0 & 1 & 1 & \dots & 1 \end{array} \right] x \tag {9-21}
$$

其对应的状态变量图如图 9-12(a)，(b)所示。式(9-20)与式(9-21)也存在对偶关系。

![](images/03ec9fc8b597a903ad9d4765a07641d75ef2983b64b6cf0e03f3407ce5319e7f.jpg)

![](images/7879dcc2b8f0119539a6b2831fbf884c78123513973282cd3c1fb139a91c0dd5.jpg)  
图 9-12 系统约当型动态方程的状态变量图

# 4. 线性定常连续系统状态方程的解

# (1) 齐次状态方程的解

状态方程

$$
\dot {\boldsymbol {x}} (t) = \boldsymbol {A} \boldsymbol {x} (t) \tag {9-22}
$$

称为齐次状态方程，通常采用幂级数法和拉普拉斯变换法求解。

1) 幂级数法。设状态方程式(9-22)的解是 $t$ 的向量幂级数

$$
\boldsymbol {x} (t) = \boldsymbol {b} _ {0} + \boldsymbol {b} _ {1} t + \boldsymbol {b} _ {2} t ^ {2} + \dots + \boldsymbol {b} _ {k} t ^ {k} + \dots
$$

式中， $\pmb { x } , \pmb { b } _ { 0 } , \pmb { b } _ { 1 } , \cdots , \pmb { b } _ { k } ,$ , 都是 $n$ 维向量，则

$$
\dot {\boldsymbol {x}} (t) = \boldsymbol {b} _ {1} + 2 \boldsymbol {b} _ {2} t + \dots + k \boldsymbol {b} _ {k} t ^ {k - 1} + \dots = \boldsymbol {A} (\boldsymbol {b} _ {0} + \boldsymbol {b} _ {1} t + \boldsymbol {b} _ {2} t ^ {2} + \dots + \boldsymbol {b} _ {k} t ^ {k} + \dots)
$$

令上式等号两边 $t$ 的同次项的系数相等，则有

$$
\boldsymbol {b} _ {1} = \boldsymbol {A} \boldsymbol {b} _ {0}
$$

$$
\boldsymbol {b} _ {2} = \frac {1}{2} \boldsymbol {A} \boldsymbol {b} _ {1} = \frac {1}{2} \boldsymbol {A} ^ {2} \boldsymbol {b} _ {0}
$$

$$
\boldsymbol {b} _ {3} = \frac {1}{3} \boldsymbol {A} \boldsymbol {b} _ {2} = \frac {1}{6} \boldsymbol {A} ^ {3} \boldsymbol {b} _ {0}
$$

$$
\boldsymbol {b} _ {k} = \frac {1}{k} \boldsymbol {A} \boldsymbol {b} _ {k - 1} = \frac {1}{k !} \boldsymbol {A} ^ {k} \boldsymbol {b} _ {0}
$$

且 $\pmb { x } ( 0 ) \mathrm { = } \pmb { b } _ { 0 }$ ，故

$$
\boldsymbol {x} (t) = \left(\boldsymbol {I} + \boldsymbol {A} t + \frac {1}{2} \boldsymbol {A} ^ {2} t ^ {2} + \dots + \frac {1}{k !} \boldsymbol {A} ^ {k} t ^ {k} + \dots\right) \boldsymbol {x} (0) \tag {9-23}
$$

定义 $\mathrm { e } ^ { ^ { \boldsymbol { A } t } } = \boldsymbol { I } + \boldsymbol { A } t + \frac { 1 } { 2 } \boldsymbol { A } ^ { 2 } t ^ { 2 } + \cdots + \frac { 1 } { k ! } \boldsymbol { A } ^ { k } t ^ { k } + \cdots = \sum _ { k = 0 } ^ { \infty } \frac { 1 } { k ! } \boldsymbol { A } ^ { k } t ^ { k }$ (9-24)

则 $\mathbf { \boldsymbol { x } } ( t ) = \mathbf { \boldsymbol { e } } ^ { A t } \mathbf { \boldsymbol { x } } ( 0 )$ (9-25)

由于标量微分方程 ${ \dot { x } } = a x$ 的解为 $\boldsymbol { x } ( t ) = \mathbf { e } ^ { a t } \boldsymbol { x } ( 0 )$ ， $\operatorname { e } ^ { a t }$ 称为指数函数，而向量微分方程式(9-22)具有相似形式的解(式(9-25))，故把 $\mathrm { e } ^ { \boldsymbol { A } t }$ 称为矩阵指数函数，简称矩阵指数。由于 $\mathbf { \boldsymbol { x } } \left( t \right)$ 是由 $x \left( 0 \right)$ 转移而来，对于线性定常系统， $\mathrm { e } ^ { \boldsymbol { A } t }$ 又称为状态转移矩阵，记为 ${ \pmb { \phi } } ( t )$ ，即

$$
\boldsymbol {\Phi} (t) = \mathrm {e} ^ {A t} \tag {9-26}
$$

2) 拉普拉斯变换法。将式(9-22)取拉氏变换，有

$$
s \boldsymbol {X} (s) = \boldsymbol {A} \boldsymbol {X} (s) + \boldsymbol {x} (0)
$$

则 $( s I - A ) X ( s ) = x ( 0 )$ (9-27)

$$
\boldsymbol {X} (s) = (s \boldsymbol {I} - \boldsymbol {A}) ^ {- 1} \boldsymbol {x} (0)
$$

进行拉氏反变换，有

$$
\boldsymbol {x} (t) = \mathcal {S} ^ {- 1} \left[ (s \boldsymbol {I} - \boldsymbol {A}) ^ {- 1} \right] \boldsymbol {x} (0) \tag {9-28}
$$

![](images/27b65136dd555830177fe21aafe27cc171d8028aba7e6e435dcdf62d4edbaae4.jpg)

与式(9-25)相比有

$$
\mathrm {e} ^ {A t} = \mathscr {S} ^ {- 1} \left[ (s I - A) ^ {- 1} \right] \tag {9-29}
$$

式(9-29)给出了 $\mathrm { e } ^ { \boldsymbol { A } t }$ 的闭合形式，说明了式(9-24)所示级数的收敛性。

从上述分析可看出，求解齐次状态方程的问题，就是计算状态转移矩阵 $\pmb { \phi } ( t )$ 的问题，因而有必要研究 $\pmb { \mathcal { P } } ( t )$ 的运算性质。

# (2) 状态转移矩阵的运算性质

重写状态转移矩阵 $\pmb { \phi } ( t )$ 的幂级数展开式

$$
\boldsymbol {\Phi} (t) = \mathrm {e} ^ {A t} = \boldsymbol {I} + A t + \frac {1}{2} A ^ {2} t ^ {2} + \dots + \frac {1}{k !} A ^ {k} t ^ {k} + \dots \tag {9-30}
$$

${ \pmb { \phi } } ( t )$ 具有如下运算性质：

1) $\pmb { \mathcal { D } } ( 0 ) = \pmb { I }$ (9-31)   
2) $\dot { \pmb { \phi } } ( t ) = \pmb { A } \pmb { \phi } ( t ) = \pmb { \phi } ( t ) \pmb { A }$ (9-32)

上述性质利用式(9-30)很容易进行证明。式(9-32)表明， $\mathbfcal { A } \phi ( t )$ 与 ${ \pmb { \phi } } ( t ) A$ 可交换，$\dot { \pmb { \mathscr { P } } } ( 0 ) { = } A$ ，并且 $\pmb { \varPhi } ( t )$ 是微分方程

$$
\dot {\boldsymbol {\Phi}} (t) = \boldsymbol {A} \boldsymbol {\Phi} (t), \quad \boldsymbol {\Phi} (0) = \boldsymbol {I} \tag {9-33}
$$

的唯一解。

3) ${ \pmb { \mathcal { D } } } ( t _ { 1 } \pm t _ { 2 } ) = { \pmb { \mathcal { D } } } ( t _ { 1 } ) { \pmb { \mathcal { D } } } ( \pm t _ { 2 } ) = { \pmb { \mathcal { D } } } ( \pm t _ { 2 } ) { \pmb { \mathcal { D } } } ( t _ { 1 } )$ (9-34)

令式(9-30)中 $t = t _ { 1 } \pm t _ { 2 }$ ，便可证明这一性质。 $\pmb { \mathcal { D } } ( t _ { 1 } ) , \pmb { \mathcal { D } } ( t _ { 2 } ) , \pmb { \mathcal { D } } ( t _ { 1 } \pm t _ { 2 } )$ 分别表示由状态 $x ( 0 )$ 转移至状态 $x ( t _ { 1 } )$ ， $x ( t _ { 2 } )$ ， $\boldsymbol { x } ( t _ { 1 } \pm t _ { 2 } )$ 的状态转移矩阵。该性质表明 $\pmb { \mathcal { D } } ( t _ { 1 } \pm t _ { 2 } )$ 可分解为 $\pmb { \mathcal { D } } ( t _ { 1 } )$ 与 $\pmb { \mathcal { D } } ( \pm t _ { 2 } )$ 的乘积，且 $\pmb { \mathcal { D } } ( t _ { 1 } )$ 与 $\pm t _ { 2 } )$ 是可交换的。

4) ${ \pmb { \phi } } ^ { - 1 } ( t ) = { \pmb { \phi } } ( - t ) , { \pmb { \phi } } ^ { - 1 } ( - t ) = { \pmb { \phi } } ( t )$ (9-35)

证明 由性质 3)有

$$
\boldsymbol {\Phi} (t - t) = \boldsymbol {\Phi} (t) \boldsymbol {\Phi} (- t) = \boldsymbol {\Phi} (- t) \boldsymbol {\Phi} (t) = I
$$

根据逆矩阵的定义可得式(9-35)。

根据 $\pmb { \varPhi } ( t )$ 的这一性质，对于线性定常系统，显然有

$$
\boldsymbol {x} (t) = \boldsymbol {\Phi} (t) \boldsymbol {x} (0), \quad \boldsymbol {x} (0) = \boldsymbol {\Phi} ^ {- 1} (t) \boldsymbol {x} (t) = \boldsymbol {\Phi} (- t) \boldsymbol {x} (t)
$$

这说明状态转移具有可逆性， $\mathbf { \boldsymbol { x } } ( t )$ 可由 $x ( 0 )$ 转移而来， $x ( 0 )$ 也可由 $x ( t )$ 转移而来。

5) $\pmb { x } ( t _ { 2 } ) = \pmb { \varPhi } ( t _ { 2 } - t _ { 1 } ) \pmb { x } ( t _ { 1 } )$ (9-36)

证明 由于

$$
\boldsymbol {x} \left(t _ {1}\right) = \boldsymbol {\Phi} \left(t _ {1}\right) \boldsymbol {x} (0), \quad \boldsymbol {x} (0) = \boldsymbol {\Phi} ^ {- 1} \left(t _ {1}\right) \boldsymbol {x} \left(t _ {1}\right) = \boldsymbol {\Phi} \left(- t _ {1}\right) \boldsymbol {x} \left(t _ {1}\right)
$$

则 $\pmb { x } ( t _ { 2 } ) = \pmb { \mathscr { D } } ( t _ { 2 } ) \pmb { x } ( 0 ) = \pmb { \mathscr { D } } ( t _ { 2 } ) \pmb { \mathscr { D } } ( - t _ { 1 } ) \pmb { x } ( t _ { 1 } ) = \pmb { \mathscr { D } } ( t _ { 2 } - t _ { 1 } ) \pmb { x } ( t _ { 1 } )$

即由 $\boldsymbol { x } ( t _ { 1 } )$ 转移至 $x ( t _ { 2 } )$ 的状态转移矩阵为 $\pmb { \mathcal { P } } ( t _ { 2 } - t _ { 1 } )$ 。

6) $\pmb { \mathcal { D } } ( t _ { 2 } - t _ { 0 } ) = \pmb { \mathcal { D } } ( t _ { 2 } - t _ { 1 } ) \pmb { \mathcal { D } } ( t _ { 1 } - t _ { 0 } )$ (9-37)

证明 由于

$$
\boldsymbol {x} \left(t _ {2}\right) = \boldsymbol {\Phi} \left(t _ {2} - t _ {0}\right) \boldsymbol {x} \left(t _ {0}\right), \quad \boldsymbol {x} \left(t _ {1}\right) = \boldsymbol {\Phi} \left(t _ {1} - t _ {0}\right) \boldsymbol {x} \left(t _ {0}\right)
$$

则

$$
\boldsymbol {x} \left(t _ {2}\right) = \boldsymbol {\Phi} \left(t _ {2} - t _ {1}\right) \boldsymbol {x} \left(t _ {1}\right) = \boldsymbol {\Phi} \left(t _ {2} - t _ {1}\right) \boldsymbol {\Phi} \left(t _ {1} - t _ {0}\right) \boldsymbol {x} \left(t _ {0}\right) = \boldsymbol {\Phi} \left(t _ {2} - t _ {0}\right) \boldsymbol {x} \left(t _ {0}\right)
$$

故式(9-37)成立。

根据转移矩阵的这一性质，可把一个转移过程分为若干个小的转移过程来研究，如图 9-13 所示。

$$
7) \left[ \boldsymbol {\Phi} (t) \right] ^ {k} = \boldsymbol {\Phi} (k t) \tag {9-38}
$$

证明 由于

$$
\left[ \boldsymbol {\Phi} (t) \right] ^ {k} = \left(\mathrm {e} ^ {A t}\right) ^ {k} = \mathrm {e} ^ {k A t} = \mathrm {e} ^ {A (k t)} = \boldsymbol {\Phi} (k t)
$$

故式(9-38)成立。

![](images/0cc8f73893331e04214b1430477084273c8cf14058c757eee0f21ba8f16ca83f.jpg)  
图 9-13 状态转移矩阵性质6)的图示

8) 若 ${ \pmb { \phi } } ( t )$ 为 ${ \dot { \mathbf { x } } } ( t ) = A { \mathbf { x } } ( t )$ 的状态转移矩阵，则引入非奇异变换 $\scriptstyle { \boldsymbol { x } } = { \boldsymbol { P } } { \boldsymbol { \overline { { x } } } }$ 后的状态转移矩阵为

$$
\bar {\boldsymbol {\Phi}} (t) = \boldsymbol {P} ^ {- 1} \mathrm {e} ^ {A t} \boldsymbol {P} \tag {9-39}
$$

证明 将 $\scriptstyle x = P 5$ 代入 $\dot { { \mathbf { x } } } ( t ) { = } A { \mathbf { x } } ( t )$ ，有

$$
\boldsymbol {P} \dot {\overline {{x}}} = \boldsymbol {A} \boldsymbol {P} \overline {{x}}, \quad \dot {\overline {{x}}} = \boldsymbol {P} ^ {- 1} \boldsymbol {A} \boldsymbol {P} \overline {{x}}, \overline {{x}} (t) = \bar {\Phi} (t) \overline {{x}} (0) = \mathrm {e} ^ {\boldsymbol {P} ^ {- 1} A \boldsymbol {P} t} \overline {{x}} (0)
$$

式中 $\mathrm { e } ^ { P ^ { - 1 } A P t } = I + P ^ { - 1 } A P t + \frac { 1 } { 2 } ( P ^ { - 1 } A P ) ^ { 2 } t ^ { 2 } + \cdots + \frac { 1 } { k ! } ( P ^ { - 1 } A P ) ^ { k } t ^ { k } + \cdots$

$$
\begin{array}{l} = P ^ {- 1} I P + P ^ {- 1} A P t + \frac {1}{2} P ^ {- 1} A ^ {2} P t ^ {2} + \dots + \frac {1}{k !} P ^ {- 1} A ^ {k} P t ^ {k} + \dots \\ = \boldsymbol {P} ^ {- 1} \left(\boldsymbol {I} + \boldsymbol {A} t + \frac {1}{2} \boldsymbol {A} ^ {2} t ^ {2} + \dots + \frac {1}{k !} \boldsymbol {A} ^ {k} t ^ {k} + \dots\right) \boldsymbol {P} = \boldsymbol {P} ^ {- 1} \mathrm {e} ^ {\boldsymbol {A} t} \boldsymbol {P} \\ \end{array}
$$

因而式(9-39)成立。

9) 两种常见的状态转移矩阵。设 $A = \mathrm { d i a g } [ \lambda _ { 1 } , \lambda _ { 2 } , \cdots , \lambda _ { n } ]$ ，即 $\pmb { A }$ 为对角阵，且具有互异元素，则

$$
\boldsymbol {\Phi} (t) = \left[ \begin{array}{c c c c} \mathrm {e} ^ {\lambda_ {1} t} & & & 0 \\ & \mathrm {e} ^ {\lambda_ {2} t} & & \\ & & \ddots & \\ 0 & & & \mathrm {e} ^ {\lambda_ {n} t} \end{array} \right] \tag {9-40}
$$

设 $\pmb { A }$ 矩阵为 $m \times m$ 约当阵

$$
\boldsymbol {A} = \left[ \begin{array}{c c c c} \lambda & 1 & & 0 \\ & \lambda & \ddots & \\ & & \ddots & 1 \\ 0 & & & \lambda \end{array} \right]
$$

$$
\Phi (t) = \left[ \begin{array}{c c c c c} {\mathrm {e} ^ {\lambda t}} & {t \mathrm {e} ^ {\lambda t}} & {\frac {t ^ {2}}{2} \mathrm {e} ^ {\lambda t}} & {\dots} & {\frac {t ^ {m - 1}}{(m - 1) !} \mathrm {e} ^ {\lambda t}} \\ {0} & {\mathrm {e} ^ {\lambda t}} & {t \mathrm {e} ^ {\lambda t}} & {\dots} & {\frac {t ^ {m - 2}}{(m - 2) !} \mathrm {e} ^ {\lambda t}} \\ {\vdots} & {\vdots} & {\vdots} & & {\vdots} \\ {0} & {0} & {0} & {\dots} & {t \mathrm {e} ^ {\lambda t}} \\ {0} & {0} & {0} & {\dots} & {\mathrm {e} ^ {\lambda t}} \end{array} \right] \tag {9-41}
$$

用幂级数展开式即可证明式(9-40)和式(9-41)成立。

例 9-4 设系统状态方程为

$$
\left[ \begin{array}{l} \dot {x} _ {1} (t) \\ \dot {x} _ {2} (t) \end{array} \right] = \left[ \begin{array}{c c} 0 & 1 \\ - 2 & - 3 \end{array} \right] \left[ \begin{array}{l} x _ {1} (t) \\ x _ {2} (t) \end{array} \right]
$$

试求状态方程的解。

解 用拉氏变换求解

$$
s \boldsymbol {I} - \boldsymbol {A} = \left[ \begin{array}{c c} s & 0 \\ 0 & s \end{array} \right] - \left[ \begin{array}{c c} 0 & 1 \\ - 2 & - 3 \end{array} \right] = \left[ \begin{array}{c c} s & - 1 \\ 2 & s + 3 \end{array} \right]
$$

$$
(s \boldsymbol {I} - \boldsymbol {A}) ^ {- 1} = \frac {\operatorname {a d j} (s \boldsymbol {I} - \boldsymbol {A})}{| s \boldsymbol {I} - \boldsymbol {A} |} = \frac {1}{(s + 1) (s + 2)} \left[ \begin{array}{l l} s + 3 & 1 \\ - 2 & s \end{array} \right] = \left[ \begin{array}{l l} \frac {2}{s + 1} - \frac {1}{s + 2} & \frac {1}{s + 1} - \frac {1}{s + 2} \\ \frac {- 2}{s + 1} + \frac {2}{s + 2} & \frac {- 1}{s + 1} + \frac {2}{s + 2} \end{array} \right]
$$

$$
\boldsymbol {\Phi} (t) = \mathcal {S} ^ {- 1} \left[ (s \boldsymbol {I} - \boldsymbol {A}) ^ {- 1} \right] = \left[ \begin{array}{c c} 2 \mathrm {e} ^ {- t} - \mathrm {e} ^ {- 2 t} & \mathrm {e} ^ {- t} - \mathrm {e} ^ {- 2 t} \\ - 2 \mathrm {e} ^ {- t} + 2 \mathrm {e} ^ {- 2 t} & - \mathrm {e} ^ {- t} + 2 \mathrm {e} ^ {- 2 t} \end{array} \right]
$$

状态方程的解为

$$
\left[ \begin{array}{l} x _ {1} (t) \\ x _ {2} (t) \end{array} \right] = \boldsymbol {\Phi} (t) \left[ \begin{array}{l} x _ {1} (0) \\ x _ {2} (0) \end{array} \right] = \left[ \begin{array}{c c} 2 \mathrm {e} ^ {- t} - \mathrm {e} ^ {- 2 t} & \mathrm {e} ^ {- t} - \mathrm {e} ^ {- 2 t} \\ - 2 \mathrm {e} ^ {- t} + 2 \mathrm {e} ^ {- 2 t} & - \mathrm {e} ^ {- t} + 2 \mathrm {e} ^ {- 2 t} \end{array} \right] \left[ \begin{array}{l} x _ {1} (0) \\ x _ {2} (0) \end{array} \right]
$$

(3) 非齐次状态方程的解

状态方程

$$
\dot {\boldsymbol {x}} (t) = \boldsymbol {A} \boldsymbol {x} (t) + \boldsymbol {B} \boldsymbol {u} (t) \tag {9-42}
$$

称为非齐次状态方程，有如下两种解法。

1) 积分法。由式(9-42)可得

$$
\mathrm {e} ^ {- A t} (\dot {\boldsymbol {x}} (t) - \boldsymbol {A} \boldsymbol {x} (t)) = \mathrm {e} ^ {- A t} \boldsymbol {B} \boldsymbol {u} (t)
$$

由于 $\frac { \mathrm { d } } { \mathrm { d } t } ( \mathrm { e } ^ { - A t } \pmb { x } ( t ) ) = - A \mathrm { e } ^ { - A t } \pmb { x } ( t ) + \mathrm { e } ^ { - A t } \pmb { \dot { x } } ( t ) = \mathrm { e } ^ { - A t } \left[ \pmb { \dot { x } } ( t ) - A \pmb { x } ( t ) \right]$

积分可得 $\mathrm { e } ^ { - A t } { \pmb x } ( t ) - { \pmb x } ( 0 ) = \int _ { 0 } ^ { t } \mathrm { e } ^ { - A \tau } { \pmb B } { \pmb u } ( \tau ) \mathrm { d } \tau$

$$
\boldsymbol {x} (t) = \mathrm {e} ^ {A t} \boldsymbol {x} (0) + \int_ {0} ^ {t} \mathrm {e} ^ {A (t - \tau)} \boldsymbol {B u} (\tau) \mathrm {d} \tau = \boldsymbol {\Phi} (t) \boldsymbol {x} (0) + \int_ {0} ^ {t} \boldsymbol {\Phi} (t - \tau) \boldsymbol {B u} (\tau) \mathrm {d} \tau \tag {9-43}
$$

式中第一项是对初始状态的响应，第二项是对输入作用的响应。

若取 $t _ { 0 }$ 作为初始时刻，则有

$$
\begin{array}{l} \mathrm {e} ^ {- A t} \boldsymbol {x} (t) - \mathrm {e} ^ {- A t _ {0}} \boldsymbol {x} \left(t _ {0}\right) = \int_ {t _ {0}} ^ {t} \mathrm {e} ^ {- A \tau} \boldsymbol {B u} (\tau) \mathrm {d} \tau \\ \boldsymbol {x} (t) = \mathrm {e} ^ {\boldsymbol {A} (t - t _ {0})} \boldsymbol {x} \left(t _ {0}\right) + \int_ {t _ {0}} ^ {t} \mathrm {e} ^ {\boldsymbol {A} (t - \tau)} \boldsymbol {B} \boldsymbol {u} (\tau) \mathrm {d} \tau \tag {9-44} \\ = \boldsymbol {\Phi} (t - t _ {0}) \boldsymbol {x} (t _ {0}) + \int_ {t _ {0}} ^ {t} \boldsymbol {\Phi} (t - \tau) \boldsymbol {B u} (\tau) d \tau \\ \end{array}
$$

2) 拉普拉斯变换法。将式(9-42)两端取拉氏变换，有

$s X ( s ) - x ( 0 ) = A X ( s ) + B U ( s )$ 则 $( s I - A ) X ( s ) = x ( 0 ) + B U ( s )$

$$
\boldsymbol {X} (s) = (s \boldsymbol {I} - \boldsymbol {A}) ^ {- 1} \boldsymbol {x} (0) + (s \boldsymbol {I} - \boldsymbol {A}) ^ {- 1} \boldsymbol {B} \boldsymbol {U} (s)
$$

进行拉氏反变换，有

$$
\boldsymbol {x} (t) = \mathcal {S} ^ {- 1} \left[ (s \boldsymbol {I} - \boldsymbol {A}) ^ {- 1} \right] \boldsymbol {x} (0) + \mathcal {S} ^ {- 1} \left[ (s \boldsymbol {I} - \boldsymbol {A}) ^ {- 1} \boldsymbol {B} \boldsymbol {U} (s) \right]
$$

由拉氏变换卷积定理

$$
\mathscr {S} ^ {- 1} \left[ F _ {1} (s) F _ {2} (s) \right] = \int_ {0} ^ {t} f _ {1} (t - \tau) f _ {2} (\tau) d \tau = \int_ {0} ^ {t} f _ {1} (\tau) f _ {2} (t - \tau) d \tau
$$

在此将 $( s I - A ) ^ { - 1 }$ 视为 $F _ { 1 } ( s )$ ，将 $B U ( s )$ 视为 $F _ { 2 } ( s )$ ，则有

$$
\boldsymbol {x} (t) = \mathrm {e} ^ {A t} \boldsymbol {x} (0) + \int_ {0} ^ {t} \mathrm {e} ^ {A (t - \tau)} \boldsymbol {B u} (\tau) \mathrm {d} \tau = \boldsymbol {\Phi} (t) \boldsymbol {x} (0) + \int_ {0} ^ {t} \boldsymbol {\Phi} (t - \tau) \boldsymbol {B u} (\tau) \mathrm {d} \tau
$$

结果与式(9-43)相同。上式又可表示为

$$
\boldsymbol {x} (t) = \boldsymbol {\Phi} (t) \boldsymbol {x} (0) + \int_ {0} ^ {t} \boldsymbol {\Phi} (\tau) \boldsymbol {B u} (t - \tau) \mathrm {d} \tau \tag {9-45}
$$

有时利用式(9-45)求解更为方便。

例 9-5 系统状态方程为

$$
\left[ \begin{array}{l} \dot {x} _ {1} \\ \dot {x} _ {2} \end{array} \right] = \left[ \begin{array}{c c} 0 & 1 \\ - 2 & - 3 \end{array} \right] \left[ \begin{array}{l} x _ {1} \\ x _ {2} \end{array} \right] + \left[ \begin{array}{l} 0 \\ 1 \end{array} \right] u
$$

且 $\begin{array} { r l } { \pmb { x } ( 0 ) = \left[ x _ { 1 } ( 0 ) \quad x _ { 2 } ( 0 ) \right] ^ { \mathrm { T } } } \end{array}$ $x _ { 2 } ( 0 ) ] ^ { \mathrm { T } }$ 。试求在 $u ( t ) { = } 1 ( t )$ 作用下状态方程的解。

解 由于 $u ( t ) { = } 1$ ， $u ( t { - } \tau ) { = } 1$ ，根据式(9-45)可得

$$
\boldsymbol {x} (t) = \boldsymbol {\Phi} (t) \boldsymbol {x} (0) + \int_ {0} ^ {t} \boldsymbol {\Phi} (\tau) \boldsymbol {B} \mathrm {d} \tau
$$

由例 9-4 已求得

$$
\boldsymbol {\Phi} (t) = \left[ \begin{array}{c c} 2 \mathrm {e} ^ {- t} - \mathrm {e} ^ {- 2 t} & \mathrm {e} ^ {- t} - \mathrm {e} ^ {- 2 t} \\ - 2 \mathrm {e} ^ {- t} + 2 \mathrm {e} ^ {- 2 t} & - \mathrm {e} ^ {- t} + 2 \mathrm {e} ^ {- 2 t} \end{array} \right]
$$

$$
\int_ {0} ^ {t} \boldsymbol {\Phi} (\tau) \boldsymbol {B} \mathrm {d} \tau = \int_ {0} ^ {t} \left[ \begin{array}{c} \mathrm {e} ^ {- \tau} - \mathrm {e} ^ {- 2 \tau} \\ - \mathrm {e} ^ {- \tau} + 2 \mathrm {e} ^ {- 2 \tau} \end{array} \right] \mathrm {d} \tau = \left[ \begin{array}{c} - \mathrm {e} ^ {- \tau} + \frac {1}{2} \mathrm {e} ^ {- 2 \tau} \\ \mathrm {e} ^ {- \tau} - \mathrm {e} ^ {- 2 \tau} \end{array} \right] _ {0} ^ {t} = \left[ \begin{array}{c} - \mathrm {e} ^ {- t} + \frac {1}{2} \mathrm {e} ^ {- 2 t} + \frac {1}{2} \\ \mathrm {e} ^ {- t} - \mathrm {e} ^ {- 2 t} \end{array} \right]
$$

故

$$
\boldsymbol {x} (t) = \left[ \begin{array}{l} x _ {1} (t) \\ x _ {2} (t) \end{array} \right] = \left[ \begin{array}{c c} 2 \mathrm {e} ^ {- t} - \mathrm {e} ^ {- 2 t} & \mathrm {e} ^ {- t} - \mathrm {e} ^ {- 2 t} \\ - 2 \mathrm {e} ^ {- t} + 2 \mathrm {e} ^ {- 2 t} & - \mathrm {e} ^ {- t} + 2 \mathrm {e} ^ {- 2 t} \end{array} \right] \left[ \begin{array}{l} x _ {1} (0) \\ x _ {2} (0) \end{array} \right] + \left[ \begin{array}{c} - \mathrm {e} ^ {- t} + \frac {1}{2} \mathrm {e} ^ {- 2 t} + \frac {1}{2} \\ \mathrm {e} ^ {- t} - \mathrm {e} ^ {- 2 t} \end{array} \right]
$$

# 5. 系统的传递函数矩阵

对于多输入-多输出系统，需要讨论传递函数矩阵。

# (1) 定义及表达式

初始条件为零时，输出向量的拉氏变换式与输入向量的拉氏变换式之间的传递关系称为传递函数矩阵，简称传递矩阵。设系统动态方程为

$$
\dot {\boldsymbol {x}} (t) = \boldsymbol {A} \boldsymbol {x} (t) + \boldsymbol {B} \boldsymbol {u} (t), \quad \boldsymbol {y} (t) = \boldsymbol {C} \boldsymbol {x} (t) + \boldsymbol {D} \boldsymbol {u} (t) \tag {9-46}
$$

令初始条件为零，进行拉氏变换有

$$
s \boldsymbol {X} (s) = \boldsymbol {A X} (s) + \boldsymbol {B U} (s), \quad \boldsymbol {Y} (s) = \boldsymbol {C X} (s) + \boldsymbol {D U} (s)
$$

则 $\pmb { X } ( s ) = ( s \pmb { I } - \pmb { A } ) ^ { - 1 } \pmb { B } \pmb { U } ( s )$

$$
\boldsymbol {Y} (s) = \left[ \boldsymbol {C} (s \boldsymbol {I} - \boldsymbol {A}) ^ {- 1} \boldsymbol {B} + \boldsymbol {D} \right] \boldsymbol {U} (s) = \boldsymbol {G} (s) \boldsymbol {U} (s) \tag {9-47}
$$

系统的传递函数矩阵表达式为

$$
\boldsymbol {G} (s) = \boldsymbol {C} (s \boldsymbol {I} - \boldsymbol {A}) ^ {- 1} \boldsymbol {B} + \boldsymbol {D} \tag {9-48}
$$

若输入 $\pmb { u }$ 为 $p$ 维向量，输出 $\boldsymbol { y }$ 为 $q$ 维向量，则 $\pmb { G } ( s )$ 为 $q \times p$ 矩阵。式(9-47)的展开式为

$$
\left[ \begin{array}{c} Y _ {1} (s) \\ Y _ {2} (s) \\ \vdots \\ Y _ {q} (s) \end{array} \right] = \left[ \begin{array}{c c c c} G _ {1 1} (s) & G _ {1 2} (s) & \dots & G _ {1 p} (s) \\ G _ {2 1} (s) & G _ {2 2} (s) & \dots & G _ {2 p} (s) \\ \vdots & \vdots & & \vdots \\ G _ {q 1} (s) & G _ {q 2} (s) & \dots & G _ {q p} (s) \end{array} \right] \left[ \begin{array}{c} U _ {1} (s) \\ U _ {2} (s) \\ \vdots \\ U _ {p} (s) \end{array} \right] \tag {9-49}
$$

式中， $G _ { i j } ( s ) ( i = 1 , 2 , \ \cdots , q ; j = 1 , 2 , \ \cdots , p )$ 表示第 $i$ 个输出量与第 $j$ 个输入量之间的传递函数。

例 9-6 已知系统动态方程为

$$
\left[ \begin{array}{l} \dot {x} _ {1} \\ \dot {x} _ {2} \end{array} \right] = \left[ \begin{array}{l l} 0 & 1 \\ 0 & - 2 \end{array} \right] \left[ \begin{array}{l} x _ {1} \\ x _ {2} \end{array} \right] + \left[ \begin{array}{l l} 1 & 0 \\ 0 & 1 \end{array} \right] \left[ \begin{array}{l} u _ {1} \\ u _ {2} \end{array} \right]
$$

$$
\left[ \begin{array}{l} y _ {1} \\ y _ {2} \end{array} \right] = \left[ \begin{array}{l l} 1 & 0 \\ 0 & 1 \end{array} \right] \left[ \begin{array}{l} x _ {1} \\ x _ {2} \end{array} \right]
$$

试求系统的传递矩阵。

解 已知

$$
\boldsymbol {A} = \left[ \begin{array}{l l} 0 & 1 \\ 0 & - 2 \end{array} \right], \quad \boldsymbol {B} = \left[ \begin{array}{l l} 1 & 0 \\ 0 & 1 \end{array} \right], \quad C = \left[ \begin{array}{l l} 1 & 0 \\ 0 & 1 \end{array} \right], \quad \boldsymbol {D} = \mathbf {0}
$$

故

$$
(s \boldsymbol {I} - \boldsymbol {A}) ^ {- 1} = \left[ \begin{array}{l l} s & - 1 \\ 0 & s + 2 \end{array} \right] ^ {- 1} = \left[ \begin{array}{l l} \frac {1}{s} & \frac {1}{s (s + 2)} \\ 0 & \frac {1}{s + 2} \end{array} \right]
$$

$$
\boldsymbol {G} (s) = \boldsymbol {C} (s \boldsymbol {I} - \boldsymbol {A}) ^ {- 1} \boldsymbol {B} = \left[ \begin{array}{l l} 1 & 0 \\ 0 & 1 \end{array} \right] \left[ \begin{array}{l l} \frac {1}{s} & \frac {1}{s (s + 2)} \\ 0 & \frac {1}{s + 2} \end{array} \right] \left[ \begin{array}{l l} 1 & 0 \\ 0 & 1 \end{array} \right] = \left[ \begin{array}{l l} \frac {1}{s} & \frac {1}{s (s + 2)} \\ 0 & \frac {1}{s + 2} \end{array} \right]
$$

# (2) 开环与闭环传递矩阵

设多输入-多输出系统结构图如图 9-14 所示。图中 $U$ ，Y， $Z$ ， $E$ 分别为输入、输出、反馈、偏差向量； $\pmb { G }$ ， $\pmb { H }$ 分别为前向通路和反馈通路的传递矩阵。由图可知

$$
\boldsymbol {Z} (s) = \boldsymbol {H} (s) \boldsymbol {Y} (s) = \boldsymbol {H} (s) \boldsymbol {G} (s) \boldsymbol {E} (s) \tag {9-50}
$$

![](images/3b2b1882c1f6a33ce1369a8ae967b4516817854461b41b57ea7be17d4e9a4fa1.jpg)  
图 9-14 多输入-多输出系统结构图

定义偏差向量至反馈向量之间的传递矩阵 $\pmb { H } ( s ) \pmb { G } ( s )$ 为开环传递矩阵，它描述了 $\pmb { { \cal E } } ( s )$ 至 $\pmb { Z } ( s )$ 之间的传递关系。开环传递矩阵等于向量传递过程中所有部件传递矩阵的乘积，其相乘顺序与传递过程相反，而且由于是矩阵相乘，顺序不能任意交换。

由于

$$
\boldsymbol {Y} (s) = \boldsymbol {G} (s) \boldsymbol {E} (s) = \boldsymbol {G} (s) [ \boldsymbol {U} (s) - \boldsymbol {Z} (s) ] = \boldsymbol {G} (s) [ \boldsymbol {U} (s) - \boldsymbol {H} (s) \boldsymbol {Y} (s) ]
$$

则 $\pmb { Y } ( s ) = \left[ \pmb { I } + \pmb { G } ( s ) \pmb { H } ( s ) \right] ^ { - 1 } \pmb { G } ( s ) \pmb { U } ( s )$ (9-51)

定义输入向量至输出向量之间的传递矩阵为闭环传递矩阵，记为 $\varPhi ( s )$ ，则

$$
\boldsymbol {\Phi} (s) = \left[ \boldsymbol {I} + \boldsymbol {G} (s) \boldsymbol {H} (s) \right] ^ {- 1} \boldsymbol {G} (s) \tag {9-52}
$$

它描述了 $U ( s )$ 至 $Y ( s )$ 之间的传递关系。

由于

$$
\boldsymbol {E} (s) = \boldsymbol {U} (s) - \boldsymbol {Z} (s) = \boldsymbol {U} (s) - \boldsymbol {H} (s) \boldsymbol {G} (s) \boldsymbol {E} (s)
$$

则 $E ( s ) = \left[ { I + H ( s ) G ( s ) } \right] ^ { - 1 } U ( s )$ (9-53)

定义输入向量至偏差向量之间的传递矩阵为偏差传递矩阵，记为 $\boldsymbol { \varPhi } _ { e } ( s )$ ，则

$$
\boldsymbol {\Phi} _ {e} (s) = \left[ \boldsymbol {I} + \boldsymbol {H} (s) \boldsymbol {G} (s) \right] ^ {- 1} \tag {9-54}
$$

它描述了 $U ( s )$ 至 $E ( s )$ 之间的传递关系。

# (3) 解耦系统的传递矩阵

将式(9-49)写成标量方程组

$$
\begin{array}{l} Y _ {1} (s) = G _ {1 1} (s) U _ {1} (s) + G _ {1 2} (s) U _ {2} (s) + \dots + G _ {1 p} (s) U _ {p} (s) \\ \begin{array}{l} Y _ {2} (s) = G _ {2 1} (s) U _ {1} (s) + G _ {2 2} (s) U _ {2} (s) + \dots + G _ {2 p} (s) U _ {p} (s) \\ \vdots \end{array} \tag {9-55} \\ \end{array}
$$

$$
Y _ {q} (s) = G _ {q 1} (s) U _ {1} (s) + G _ {q 2} (s) U _ {2} (s) + \dots + G _ {q p} (s) U _ {p} (s)
$$

可见，一般多输入-多输出系统的传递矩阵不是对角阵，每一个输入量将影响所有输出量，而每一个输出量也都会受到所有输入量的影响。这种系统称为耦合系统，其控制方式称为耦合控制。

对一个耦合系统进行控制是复杂的，工程中常希望实现某一输出量仅受某一输入量的控制，这种控制方式称为解耦控制，其相应的系统称为解耦系统。解耦系统的输入向量和输出向量必有相同的维数，传递矩阵必为对角阵，即

$$
\left[ \begin{array}{c} Y _ {1} (s) \\ Y _ {2} (s) \\ \vdots \\ Y _ {m} (s) \end{array} \right] = \left[ \begin{array}{c c c c} G _ {1 1} (s) & & & 0 \\ & G _ {2 2} (s) & & \\ & & \ddots & \\ 0 & & & G _ {m m} (s) \end{array} \right] \left[ \begin{array}{c} U _ {1} (s) \\ U _ {2} (s) \\ \vdots \\ U _ {m} (s) \end{array} \right] \tag {9-56}
$$

可以看出，解耦系统是由 $m$ 个独立的单输入-单输出系统

$$
Y _ {i} (s) = G _ {i i} (s) U _ {i} (s), \quad i = 1, 2, \dots , m \tag {9-57}
$$

组成。为了控制每个输出量， $G _ { i i } ( s )$ 不得为零，即解耦系统的对角化传递矩阵必须是非奇异的。在系统中引入适当的校正环节使传递矩阵对角化，称为解耦。系统的解耦问题是一个相当复杂的问题，研究解耦问题的人很多，解耦的方法也很多。下面介绍适用于线性定常连续系统的两种简单解耦方法。

1) 用串联补偿器 $\pmb { G } _ { c } ( s )$ 实现解耦。系统结构图如图 9-15 所示。未引入 $\pmb { G } _ { c } ( s )$ 时，原系统为耦合系统，引入 $\pmb { G } _ { c } ( s )$ 后的闭环传递矩阵为

$$
\boldsymbol {\Phi} (s) = \left[ \boldsymbol {I} + \boldsymbol {G} _ {0} (s) \boldsymbol {G} _ {c} (s) \boldsymbol {H} (s) \right] ^ {- 1} \boldsymbol {G} _ {0} (s) \boldsymbol {G} _ {c} (s) \tag {9-58}
$$

以 $[ I / + G _ { 0 } ( s ) G _ { c } ( s ) H ( s ) ]$ 左乘式(9-58)两端，经整理有

$$
\boldsymbol {G} _ {0} (s) \boldsymbol {G} _ {c} (s) = \boldsymbol {\Phi} (s) \left[ \boldsymbol {I} - \boldsymbol {H} (s) \boldsymbol {\Phi} (s) \right] ^ {- 1} \tag {9-59}
$$

式中， ${ \pmb { \phi } } ( s )$ 为所希望的对角阵，阵中各元素与性能指标要求有关。由式(9-59)可见，在 $H ( s )$ 为对角阵的条件下， $[ { \pmb I } - { \pmb H } ( s ) { \pmb \varPhi } ( s ) ] ^ { - 1 }$ 仍为对角阵，故 $G _ { 0 } ( s ) G _ { c } ( s )$ 应为对角阵，且有

$$
\boldsymbol {G} _ {c} (s) = \boldsymbol {G} _ {0} ^ {- 1} (s) \boldsymbol {\Phi} (s) \left[ \boldsymbol {I} - \boldsymbol {H} (s) \boldsymbol {\Phi} (s) \right] ^ {- 1} \tag {9-60}
$$

按式(9-60)设计串联补偿器可使系统解耦。

2) 用前馈补偿器 ${ \bf \delta G } _ { d } ( s )$ 实现解耦。系统结构如图 9-16 所示， ${ \bf \delta G } _ { d } ( s )$ 的作用是对输入进行适当变换以实现解耦。未引入 ${ \cal G } _ { d } ( s )$ 时原系统的闭环传递矩阵为

![](images/24c163a3252e3cb0e707ea6d5a3e1494eabfb89ca4c5013b09ccca990d81d209.jpg)  
图 9-15 用串联补偿器实现解耦的系统结构图

![](images/235989c40f4581b793922945e02c1c5dac02c761d73c527fdbffcb94bdf5d330.jpg)  
图 9-16 用前馈补偿器实现解耦的系统结构图

$$
\boldsymbol {\Phi} ^ {\prime} (s) = \left[ \boldsymbol {I} + \boldsymbol {G} _ {0} (s) \right] ^ {- 1} \boldsymbol {G} _ {0} (s) \tag {9-61}
$$

引入 ${ \cal G } _ { d } ( s ) .$ 后解耦系统的闭环传递矩阵为

$$
\boldsymbol {\Phi} (s) = \boldsymbol {\Phi} ^ {\prime} (s) \boldsymbol {G} _ {d} (s) = \left[ \boldsymbol {I} + \boldsymbol {G} _ {0} (s) \right] ^ {- 1} \boldsymbol {G} _ {0} (s) \boldsymbol {G} _ {d} (s) \tag {9-62}
$$

式中， ${ \pmb { \phi } } ( s )$ 为所希望的对角阵。由式(9-62)可得

$$
\boldsymbol {G} _ {d} (s) = \boldsymbol {G} _ {0} ^ {- 1} (s) \left[ \boldsymbol {I} + \boldsymbol {G} _ {0} (s) \right] \boldsymbol {\Phi} (s) \tag {9-63}
$$

按式(9-63)设计前馈补偿器可使系统解耦。

![](images/e43f760181c8727af3ff9acb2314a826740cc2650f308651f32fda5e0a52ae83.jpg)  
图 9-17 双输入-双输出耦合系统结构图

例 9-7 已知双输入-双输出单位反馈系统结构图如图 9-17所示。试列写原系统的开、闭环传递矩阵，并求串联补偿器和前馈补偿器，使解耦系统的闭环传递矩阵为

$$
\boldsymbol {\Phi} (s) = \left[ \begin{array}{c c} \frac {1}{s + 1} & 0 \\ 0 & \frac {1}{5 s + 1} \end{array} \right]
$$

并画出解耦系统的结构图。

解 求原系统开环传递矩阵 $\pmb { G } _ { 0 } ( s )$ ，只需写出输出量(y1，y2)与误差量(e1，e2)各分量之间的关系，即

$$
Y _ {1} (s) = \frac {1}{2 s + 1} E _ {1} (s)
$$

$$
Y _ {2} (s) = E _ {1} (s) + \frac {1}{s + 1} E _ {2} (s)
$$

其向量-矩阵形式为

$$
\boldsymbol {Y} (s) = \left[ \begin{array}{l} Y _ {1} (s) \\ Y _ {2} (s) \end{array} \right] = \left[ \begin{array}{c c} \frac {1}{2 s + 1} & 0 \\ 1 & \frac {1}{s + 1} \end{array} \right] \left[ \begin{array}{l} E _ {1} (s) \\ E _ {2} (s) \end{array} \right] = \boldsymbol {G} _ {0} (s) \boldsymbol {E} (s)
$$

原系统开环传递矩阵为

$$
\boldsymbol {G} _ {0} (s) = \left[ \begin{array}{c c} \frac {1}{2 s + 1} & 0 \\ 1 & \frac {1}{s + 1} \end{array} \right]
$$

输出量(y1，y2)与输入量(u1，u2)各分量之间的关系为

$$
Y _ {1} (s) = \frac {1 / (2 s + 1)}{1 + 1 / (2 s + 1)} U _ {1} (s) = \frac {1}{2 (s + 1)} U _ {1} (s)
$$

$$
\begin{array}{l} Y _ {2} (s) = \frac {1 / (s + 1)}{1 + 1 / (s + 1)} U _ {2} (s) + \frac {1}{1 + 1 / (s + 1)} \cdot \frac {1}{1 + 1 / (2 s + 1)} U _ {1} (s) \\ = \frac {1}{s + 2} U _ {2} (s) + \frac {2 s + 1}{2 (s + 2)} U _ {1} (s) \\ \end{array}
$$

其向量-矩阵形式为

$$
\boldsymbol {Y} (s) = \left[ \begin{array}{l} Y _ {1} (s) \\ Y _ {2} (s) \end{array} \right] = \left[ \begin{array}{c c} \frac {1}{2 (s + 1)} & 0 \\ \frac {2 s + 1}{2 (s + 2)} & \frac {1}{s + 2} \end{array} \right] \left[ \begin{array}{l} U _ {1} (s) \\ U _ {2} (s) \end{array} \right] = \boldsymbol {\Phi} ^ {\prime} (s) \boldsymbol {U} (s)
$$

原系统闭环传递矩阵为

$$
\boldsymbol {\Phi} ^ {\prime} (s) = \left[ \begin{array}{c c} \frac {1}{2 (s + 1)} & 0 \\ \frac {2 s + 1}{2 (s + 2)} & \frac {1}{s + 2} \end{array} \right]
$$

串联补偿器 $\pmb { G } _ { c } ( s )$ 的设计：由式(9-60)并考虑 $H ( s ) { = } I$ ，有

$$
\boldsymbol {G} _ {c} (s) = \boldsymbol {G} _ {0} ^ {- 1} (s) \boldsymbol {\Phi} (s) \left[ \boldsymbol {I} - \boldsymbol {\Phi} (s) \right] ^ {- 1} = \left[ \begin{array}{l l} \frac {1}{2 s + 1} & 0 \\ 1 & \frac {1}{s + 1} \end{array} \right] ^ {- 1} \left[ \begin{array}{l l} \frac {1}{s + 1} & 0 \\ 0 & \frac {1}{5 s + 1} \end{array} \right] \left[ \begin{array}{l l} \frac {s}{s + 1} & 0 \\ 0 & \frac {5 s}{5 s + 1} \end{array} \right] ^ {- 1}
$$

$$
\begin{array}{l} = \left[ \begin{array}{c c} 2 s + 1 & 0 \\ - (2 s + 1) (s + 1) & s + 1 \end{array} \right] \left[ \begin{array}{c c} \frac {1}{s + 1} & 0 \\ 0 & \frac {1}{5 s + 1} \end{array} \right] \left[ \begin{array}{c c} \frac {s + 1}{s} & 0 \\ 0 & \frac {5 s + 1}{5 s} \end{array} \right] \\ = \left[ \begin{array}{c c} \frac {2 s + 1}{s} & 0 \\ - \frac {(2 s + 1) (s + 1)}{s} & \frac {s + 1}{5 s} \end{array} \right] = \left[ \begin{array}{l l} G _ {c 1 1} (s) & G _ {c 1 2} (s) \\ G _ {c 2 1} (s) & G _ {c 2 2} (s) \end{array} \right] \\ \end{array}
$$

式中， $G _ { c i j } ( s )$ 表示 $U _ { j } ( s )$ 至 $Y _ { i } ( s ) ( i , j { = } 1$ ，2)通道的串联补偿器传递函数。可以验证这种解耦系统的开环传递矩阵 $\mathbf { \delta G } _ { 0 } ( s ) \mathbf { G } _ { c } ( s )$ 为对角阵：

$$
\boldsymbol {G} _ {0} (s) \boldsymbol {G} _ {c} (s) = \left[ \begin{array}{l l} \frac {1}{2 s + 1} & 0 \\ 1 & \frac {1}{s + 1} \end{array} \right] \left[ \begin{array}{l l} \frac {2 s + 1}{s} & 0 \\ - \frac {(2 s + 1) (s + 1)}{s} & \frac {s + 1}{5 s} \end{array} \right] = \left[ \begin{array}{l l} \frac {1}{s} & 0 \\ 0 & \frac {1}{5 s} \end{array} \right]
$$

用串联补偿器实现解耦的系统结构图如图 9-18 所示。

![](images/5730da5f29e87479e0fc198a04d2cbb86cb91edf89dadd6ea5281b4a18252c0a.jpg)  
图 9-18 例 9-7 用串联补偿器实现解耦的系统结构图

前馈补偿器 ${ \bf \delta G } _ { d } ( s )$ 设计：由式(9-62)，有

$$
\begin{array}{l} \boldsymbol {G} _ {d} (s) = \boldsymbol {\Phi} ^ {t - 1} (s) \boldsymbol {\Phi} (s) = \left[ \begin{array}{c c} \frac {1}{2 (s + 1)} & 0 \\ \frac {2 s + 1}{2 (s + 2)} & \frac {1}{s + 2} \end{array} \right] ^ {- 1} \left[ \begin{array}{c c} \frac {1}{s + 1} & 0 \\ 0 & \frac {1}{5 s + 1} \end{array} \right] \\ = \left[ \begin{array}{c c} 2 (s + 1) & 0 \\ - (2 s + 1) (s + 1) & s + 2 \end{array} \right] \left[ \begin{array}{c c} \frac {1}{s + 1} & 0 \\ 0 & \frac {1}{5 s + 1} \end{array} \right] \\ = \left[ \begin{array}{c c} 2 & 0 \\ - (2 s + 1) & \frac {s + 2}{5 s + 1} \end{array} \right] = \left[ \begin{array}{l l} G _ {d 1 1} (s) & G _ {d 1 2} (s) \\ G _ {d 2 1} (s) & G _ {d 2 2} (s) \end{array} \right] \\ \end{array}
$$

式中， $G _ { d i j } ( s )$ 表示 $U _ { j } ( s )$ 至 $U _ { i } ^ { \prime } ( s ) ( i , j = 1 , 2 )$ 通道的串联补偿器传递函数。

用前馈补偿器实现解耦的系统结构图见图 9-19。

# 6. 线性离散系统状态空间表达式的建立及其解

离散系统的特点是系统中的各个变量被处理成为只在离散时刻取值，其状态空间描述只反映离散时刻的变量组间的因果关系和转换关系，因而这类系统通常称为离散时间系统，简称为离散系统。离散时间系统可以是一类实际的离散时间问题的数学模型，如社会经济问题、生态问题等，也可以是一个连续系统因为采用数字计算机进行计算或控制的需要而人为地加以时间离散化而导出的模型。线性离散系统的动态方程可以利用系统的差分方程建立，也可以利用线性连续动态方程的离散化得到。

![](images/d2421377d913431bed309f2b5ad8f11813061090a02d875e879fbac84d9872e8.jpg)  
图 9-19 例 9-7 用前馈补偿器实现解耦的系统结构图

# (1) 由差分方程建立动态方程

在经典控制理论中离散系统通常用差分方程或脉冲传递函数来描述。单输入-单输出线性定常离散系统差分方程的一般形式为

$$
\begin{array}{l} y (k + n) + a _ {n - 1} y (k + n - 1) + \dots + a _ {1} y (k + 1) + a _ {0} y (k) \tag {9-64} \\ = b _ {n} u (k + n) + b _ {n - 1} u (k + n - 1) + \dots + b _ {1} u (k + 1) + b _ {0} u (k) \\ \end{array}
$$

式中， $k$ 表示 $k T$ 时刻； $T$ 为采样周期； $y ( k )$ ， $u ( k )$ 分别为 $k T$ 时刻的输出量和输入量； $a _ { i }$ ，$b _ { i } ( i { = } 0 , 1 , 2 , \cdots , n$ ，且 $a _ { n } { = } 1$ )为表征系统特性的常系数。考虑初始条件为零时的 $z$ 变换关系有

$$
\mathscr {X} [ y (k) ] = Y (z), \quad \mathscr {X} [ y (k + i) ] = z ^ {i} Y (z)
$$

对式(9-64)两端取 $z$ 变换并加以整理可得

$$
\begin{array}{l} G (z) = \frac {Y (z)}{U (z)} = \frac {b _ {n} z ^ {n} + b _ {n - 1} z ^ {n - 1} + \cdots + b _ {1} z + b _ {0}}{z ^ {n} + a _ {n - 1} z ^ {n - 1} + \cdots + a _ {1} z + a _ {0}} \tag {9-65} \\ = b _ {n} + \frac {\beta_ {n - 1} z ^ {n - 1} + \cdots + \beta_ {1} z + \beta_ {0}}{z ^ {n} + a _ {n - 1} z ^ {n - 1} + \cdots + a _ {1} z + a _ {0}} = b _ {n} + \frac {N (z)}{D (z)} \\ \end{array}
$$

$G ( z )$ 称为脉冲传递函数，式(9-65)与式(9-15)在形式上相同，故连续系统动态方程的建立方法可用于离散系统。例如，在 $N ( z ) / D ( z )$ 的串联分解中，引入中间变量 $\mathcal { Q } ( z )$ 则有

$$
z ^ {n} Q (z) + a _ {n - 1} z ^ {n - 1} Q (z) + \dots + a _ {1} z Q (z) + a _ {0} Q (z) = U (z)
$$

$$
Y (z) = \beta_ {n - 1} z ^ {n - 1} Q (z) + \dots + \beta_ {1} z Q (z) + \beta_ {0} Q (z)
$$

设 $X _ { 1 } ( z ) = Q ( z )$

$$
\begin{array}{l} X _ {2} (z) = z Q (z) = z X _ {1} (z) \\ \vdots \end{array}
$$

$$
X _ {n} (z) = z ^ {n - 1} Q (z) = z X _ {n - 1} (z)
$$

则 $z ^ { n } Q ( z ) = - a _ { 0 } X _ { 1 } ( z ) - a _ { 1 } X _ { 2 } ( z ) \cdots - a _ { n - 1 } X _ { n } ( z ) + U ( z ) \mid$

$$
Y (z) = \beta_ {0} X _ {1} (z) + \beta_ {1} X _ {2} (z) + \dots + \beta_ {n - 1} X _ {n} (z)
$$

利用 $z$ 反变换关系

$$
\mathcal {X} ^ {- 1} \left[ X _ {i} (z) \right] = x _ {i} (k)
$$

$$
\mathcal {X} ^ {- 1} \left[ z X _ {i} (z) \right] = x _ {i} (k + 1)
$$

可得动态方程为

$$
x _ {1} (k + 1) = x _ {2} (k)
$$

$$
x _ {2} (k + 1) = x _ {3} (k)
$$

$$
\begin{array}{c} \vdots \\ \vdots \end{array}
$$

$$
x _ {n - 1} (k + 1) = x _ {n} (k)
$$

$$
x _ {n} (k + 1) = - a _ {0} x _ {1} (k) - a _ {1} x _ {2} (k) - \dots - a _ {n - 1} x _ {n} (k) + u (k)
$$

$$
y (k) = \beta_ {0} x _ {1} (k) + \beta_ {1} x _ {2} (k) + \dots + \beta_ {n - 1} x _ {n} (k)
$$

向量-矩阵形式为

$$
\left[ \begin{array}{c} x _ {1} (k + 1) \\ x _ {2} (k + 1) \\ \vdots \\ x _ {n - 1} (k + 1) \\ x _ {n} (k + 1) \end{array} \right] = \left[ \begin{array}{c c c c c} 0 & 1 & 0 & \dots & 0 \\ 0 & 0 & 1 & \dots & 0 \\ \vdots & \vdots & \vdots & & \vdots \\ 0 & 0 & 0 & \dots & 1 \\ - a _ {0} & - a _ {1} & - a _ {2} & \dots & - a _ {n - 1} \end{array} \right] \left[ \begin{array}{c} x _ {1} (k) \\ x _ {2} (k) \\ \vdots \\ x _ {n - 1} (k) \\ x _ {n} (k) \end{array} \right] + \left[ \begin{array}{l} 0 \\ 0 \\ \vdots \\ 0 \\ 1 \end{array} \right] u (k) \tag {9-66a}
$$

$$
y (k) = \left[ \begin{array}{l l l l} \beta_ {0} & \beta_ {1} & \dots & \beta_ {n - 1} \end{array} \right] \boldsymbol {x} (k) + b _ {n} u (k) \tag {9-66b}
$$

简记为

$$
\boldsymbol {x} (k + 1) = \boldsymbol {G} \boldsymbol {x} (k) + \boldsymbol {h} u (k) \tag {9-67a}
$$

$$
\boldsymbol {y} (k) = \boldsymbol {c x} (k) + d u (k) \tag {9-67b}
$$

式中， $\pmb { G }$ 为友矩阵； $\pmb { G }$ ， $\pmb { h }$ 为可控标准型。可以看出，离散系统状态方程描述了 $( k { + } 1 ) T$ 时刻的状态与 $k T$ 时刻的状态及输入量之间的关系，其输出方程描述了 $k T$ 时刻的输出量与$k T$ 时刻的状态及输入量之间的关系。

线性定常多输入-多输出离散系统的动态方程为

$$
\boldsymbol {x} (k + 1) = \boldsymbol {G} \boldsymbol {x} (k) + \boldsymbol {H} \boldsymbol {u} (k) \tag {9-68a}
$$

$$
\boldsymbol {y} (k) = \boldsymbol {C x} (k) + \boldsymbol {D u} (k) \tag {9-68b}
$$

系统结构图如图 9-3 所示，图中 $z ^ { - 1 }$ 为单位延迟器，其输入为 $( k { + } 1 ) T$ 时刻的状态，输出为延迟一个采样周期的 $k T$ 时刻的状态。

(2) 定常连续动态方程的离散化

已知定常连续系统状态方程 ${ \dot { \pmb x } } = { \pmb A } { \pmb x } + { \pmb B } { \pmb u }$ 在 $\boldsymbol { x } ( t _ { 0 } )$ 及 $\pmb { u } ( t )$ 作用下的解为

$$
\boldsymbol {x} (t) = \boldsymbol {\Phi} \left(t - t _ {0}\right) x \left(t _ {0}\right) + \int_ {t _ {0}} ^ {T} \boldsymbol {\Phi} (t - \tau) \boldsymbol {B u} (\tau) d \tau
$$

令 $t _ { 0 } { = } k T$ ，则 ${ \pmb x } \left( t _ { 0 } \right) = { \pmb x } \left( k T \right) = { \pmb x } \left( k \right)$ ；令 $_ { t = ( k + 1 ) T }$ ，则 ${ \pmb x } \left( t \right) = { \pmb x } \left[ ( k { + } 1 ) T \right] = { \pmb x } \left( k { + } 1 \right)$ ；在 $t \in \left[ k , k + 1 \right)$ 区间内， $\pmb { u } ( t ) \mathrm { = } \pmb { u } ( k ) \mathrm { = }$ 常数，于是其解化为

$$
\boldsymbol {x} (k + 1) = \boldsymbol {\Phi} [ (k + 1) T - k T ] \boldsymbol {x} (k) + \int_ {k T} ^ {(k + 1) T} \boldsymbol {\Phi} [ (k + 1) T - \tau ] \boldsymbol {B} d \tau \cdot \boldsymbol {u} (k)
$$

记 $\pmb { G } ( T ) = \int _ { k T } ^ { ( k + 1 ) T } \pmb { \varPhi } \big [ ( k + 1 ) T - \tau \big ] \pmb { B } \mathrm { d } \tau$ kT

为了便于计算 $G ( T )$ ，引入变量置换，令 $( k { + } 1 ) T { - } { \tau } { = } { \tau } ^ { \prime }$ ，则

$$
\boldsymbol {G} (T) = \int_ {0} ^ {T} \boldsymbol {\Phi} (\tau^ {\prime}) \boldsymbol {B} \mathrm {d} \tau^ {\prime} \tag {9-69}
$$

故离散化状态方程为

$$
\boldsymbol {x} (k + 1) = \boldsymbol {\Phi} (T) \boldsymbol {x} (k) + \boldsymbol {G} (T) \boldsymbol {u} (k) \tag {9-70}
$$

式中， ${ \pmb { \mathcal { D } } } ( T )$ 与连续系统状态转移矩阵 $\pmb { \phi } ( t )$ 的关系为

$$
\left. \boldsymbol {\Phi} (T) = \boldsymbol {\Phi} (t) \right| _ {t = T} \tag {9-71}
$$

离散化系统的输出方程仍为

$$
\boldsymbol {y} (k) = \boldsymbol {C x} (k) + \boldsymbol {D u} (k)
$$

# (3) 定常离散动态方程的解

求解离散动态方程的方法有递推法和 $z$ 变换法，这里只介绍常用的递推法，令式(9-70)中的 $k { = } 0 , 1 , \ \cdots , k { - } 1$ ，可得到 T，2T，…， $k T$ 时刻的状态，即

$$
k = 0: \quad \boldsymbol {x} (1) = \boldsymbol {\Phi} (T) \boldsymbol {x} (0) + \boldsymbol {G} (T) \boldsymbol {u} (0)
$$

$$
\begin{array}{l} k = 1: \quad \boldsymbol {x} (2) = \boldsymbol {\Phi} (T) \boldsymbol {x} (1) + \boldsymbol {G} (T) \boldsymbol {u} (1) \\ = \boldsymbol {\Phi} ^ {2} (T) \boldsymbol {x} (0) + \boldsymbol {\Phi} (T) \boldsymbol {G} (T) \boldsymbol {u} (0) + \boldsymbol {G} (T) \boldsymbol {u} (1) \\ \end{array}
$$

$$
\begin{array}{l} k = 2: \quad \boldsymbol {x} (3) = \boldsymbol {\Phi} (T) \boldsymbol {x} (2) + \boldsymbol {G} (T) \boldsymbol {u} (2) \\ = \boldsymbol {\Phi} ^ {3} (T) \boldsymbol {x} (0) + \boldsymbol {\Phi} ^ {2} (T) \boldsymbol {G} (T) \boldsymbol {u} (0) + \boldsymbol {\Phi} (T) \boldsymbol {G} (T) \boldsymbol {u} (1) + \boldsymbol {G} (T) \boldsymbol {u} (2) \\ \end{array}
$$

$$
\vdots \quad \boldsymbol {x} (k) = \boldsymbol {\Phi} (T) \boldsymbol {x} (k - 1) + \boldsymbol {G} (T) \boldsymbol {u} (k - 1)
$$

$$
\begin{array}{l} k = k - 1: \quad = \boldsymbol {\Phi} ^ {k} (T) \boldsymbol {x} (0) + \boldsymbol {\Phi} ^ {k - 1} (T) \boldsymbol {G} (T) \boldsymbol {u} (0) + \boldsymbol {\Phi} ^ {k - 2} (T) \boldsymbol {G} (T) \boldsymbol {u} (1) \\ + \dots + \boldsymbol {\Phi} (T) \boldsymbol {G} (T) \boldsymbol {u} (k - 2) + \boldsymbol {G} (T) \boldsymbol {u} (k - 1) \\ = \boldsymbol {\Phi} ^ {k} (T) \boldsymbol {x} (0) + \sum_ {i = 0} ^ {k - 1} \boldsymbol {\Phi} ^ {k - 1 - i} (T) \boldsymbol {G} (T) \boldsymbol {u} (i) \tag {9-72} \\ \end{array}
$$

式(9-72)为离散化状态方程的解，又称离散化状态转移方程。当 $u ( i ) { = } 0 ( i { = } 0 , \ 1 , \ \cdots , \ k { - } 1 )$ 时，有

$$
\boldsymbol {x} (k) = \boldsymbol {\Phi} ^ {k} (T) \boldsymbol {x} (0) = \boldsymbol {\Phi} (k T) \boldsymbol {x} (0) = \boldsymbol {\Phi} (k) \boldsymbol {x} (0)
$$

${ \pmb { \phi } } ( k )$ 称为离散化系统动态转移矩阵。

输出方程为

$$
\boldsymbol {y} (k) = \boldsymbol {C} \boldsymbol {x} (k) + \boldsymbol {D} \boldsymbol {u} (k) = \boldsymbol {C} \boldsymbol {\Phi} ^ {k} (T) \boldsymbol {x} (0) + \boldsymbol {C} \sum_ {i = 0} ^ {k - 1} \boldsymbol {\Phi} ^ {k - 1 - i} (T) \boldsymbol {G} (T) \boldsymbol {u} (i) + \boldsymbol {D} \boldsymbol {u} (k) \tag {9-73}
$$

对于离散动态方程式(9-68)，采用递推法可得其解为

$$
\boldsymbol {x} (k) = \boldsymbol {G} ^ {k} \boldsymbol {x} (0) + \sum_ {i = 0} ^ {k - 1} \boldsymbol {G} ^ {k - 1 - i} \boldsymbol {H u} (i) \tag {9-74}
$$

$$
\boldsymbol {y} (k) = \boldsymbol {C} \boldsymbol {G} ^ {k} \boldsymbol {x} (0) + \boldsymbol {C} \sum_ {i = 0} ^ {k - 1} \boldsymbol {G} ^ {k - 1 - i} \boldsymbol {H} \boldsymbol {u} (i) + \boldsymbol {D} \boldsymbol {u} (k) \tag {9-75}
$$

式中， $\pmb { G } ^ { k }$ 表示 $k$ 个 $\pmb { G }$ 自乘。

例 9-8 已知连续时间系统的状态方程为

$$
\dot {\boldsymbol {x}} = \left[ \begin{array}{c c} 0 & 1 \\ - 2 & - 3 \end{array} \right] \boldsymbol {x} + \left[ \begin{array}{l} 0 \\ 1 \end{array} \right] \boldsymbol {u}
$$

设 $T { = } 1$ ，试求相应的离散时间状态方程。

解 由例 9-4 已知该连续系统的状态转移矩阵为

$$
\boldsymbol {\Phi} (t) = \left[ \begin{array}{c c} 2 \mathrm {e} ^ {- t} - \mathrm {e} ^ {- 2 t} & \mathrm {e} ^ {- t} - \mathrm {e} ^ {- 2 t} \\ - 2 \mathrm {e} ^ {- t} + 2 \mathrm {e} ^ {- 2 t} & - \mathrm {e} ^ {- t} + 2 \mathrm {e} ^ {- 2 t} \end{array} \right]
$$

$$
\left. \boldsymbol {\Phi} (T) = \boldsymbol {\Phi} (t) \right| _ {t = T = 1} = \left[ \begin{array}{l l} 0. 6 0 0 4 & 0. 2 3 2 5 \\ - 0. 4 6 5 1 & - 0. 0 9 7 2 \end{array} \right]
$$

$$
\begin{array}{l} \boldsymbol {G} (t) = \int_ {0} ^ {T} \boldsymbol {\Phi} (\tau) \boldsymbol {B} \mathrm {d} \tau = \int_ {0} ^ {T} \left[ \begin{array}{c} \mathrm {e} ^ {- \tau} - \mathrm {e} ^ {- 2 \tau} \\ - \mathrm {e} ^ {- \tau} + 2 \mathrm {e} ^ {- 2 \tau} \end{array} \right] \mathrm {d} \tau = \left[ \begin{array}{c} \frac {1}{2} - \mathrm {e} ^ {- T} + \frac {1}{2} \mathrm {e} ^ {- 2 T} \\ \mathrm {e} ^ {- T} - \mathrm {e} ^ {- 2 T} \end{array} \right] \\ \left. \boldsymbol {G} (T) \right| _ {T = 1} = \left[ \begin{array}{l} 0. 1 9 9 8 \\ 0. 2 3 2 5 \end{array} \right] \\ \end{array}
$$

# 9-2 线性系统的可控性与可观测性

现代控制理论中用状态方程和输出方程描述系统，输入和输出构成系统的外部变量，而状态为系统的内部变量，这就存在着系统内的所有状态是否可受输入影响和是否可由输出反映的问题，这就是可控性和可观测性问题。如果系统所有状态变量的运动都可以由输入来影响和控制而由任意的初态达到原点，则称系统是完全可控的，或者更确切地说是状态完全可控的，简称为系统可控；否则，就称系统是不完全可控的，或简称为系统不可控。相应地，如果系统所有状态变量的任意形式的运动均可由输出完全反映，则称系统是状态完全可观测的，简称为系统可观测；反之，则称系统是不完全可观测的，或简称为系统不可观测。

可控性与可观测性概念，是卡尔曼于 20 世纪 60 年代首先提出来的，是用状态空间描述系统引申出来的新概念，在现代控制理论中起着重要作用。

例 9-9 给定系统的动态方程为

$$
\left[ \begin{array}{l} \dot {x} _ {1} \\ \dot {x} _ {2} \end{array} \right] = \left[ \begin{array}{c c} 4 & 0 \\ 0 & - 5 \end{array} \right] \left[ \begin{array}{l} x _ {1} \\ x _ {2} \end{array} \right] + \left[ \begin{array}{l} 1 \\ 2 \end{array} \right] u
$$

$$
y = \left[ \begin{array}{l l} 0 & - 6 \end{array} \right] \left[ \begin{array}{l} x _ {1} \\ x _ {2} \end{array} \right]
$$

将其表示为标量方程组的形式，有

$$
\dot {x} _ {1} = 4 x _ {1} + u
$$

$$
\dot {x} _ {2} = - 5 x _ {2} + 2 u
$$

$$
y = - 6 x _ {2}
$$

这表明状态变量 $x _ { 1 }$ 和 $x _ { 2 }$ 都可通过选择控制量 $u$ 而由始点达到原点，因而系统完全可控。但是，输出 $y$ 只能反映状态变量 $x _ { 2 }$ ，而与状态变量 $x _ { 1 }$ 既无直接关系也无间接关系，所以系统是不完全可观测的。

应当指出，上述对可控性和可观测性所作的直观说明，只是对这两个概念的直觉的

但不严密的描述，而且也只能用来解释和判断非常直观和非常简单系统的可控性和可观测性。为了揭示可控性和可观测性的本质属性，并用于分析和判断更为一般和较为复杂的系统，需要对这两个概念建立严格的定义，并在此基础上导出相应的判别准则。尽管本章主要研究线性定常系统，但由于线性时变系统的可控性和可观测性定义更具有代表性，而线性定常系统只是线性时变系统的一种特殊类型，因而我们用线性时变系统给出可控性和可观测性的严格定义。在研究线性定常连续和离散系统时，再分别给出可控性及可观测性判据。

# 1. 可控性

考虑线性时变系统的状态方程

$$
\dot {\boldsymbol {x}} (t) = \boldsymbol {A} (t) \boldsymbol {x} (t) + \boldsymbol {B} (t) \boldsymbol {u} (t), \quad t \in T _ {t} \tag {9-76}
$$

其中， $\boldsymbol { x }$ 为 $n$ 维状态向量； $u$ 为 $p$ 维输入向量； $T _ { t }$ 为时间定义区间； $\mathbf { } A ( t )$ 和 $\pmb { { \cal B } } ( t )$ 分别为 $n$ $\times n$ 矩阵和 $n \times p$ 矩阵。现对状态可控、系统可控和不可控分别定义如下：

状态可控 对于式(9-76)所示线性时变系统，如果对取定初始时刻 $t _ { 0 } \in T _ { t }$ 的一个非零初始状态 $\boldsymbol { x } ( t _ { 0 } ) { = } \boldsymbol { x } _ { 0 }$ ，存在一个时刻 $t _ { 1 } \in T _ { t }$ ， $t _ { 1 } { > } t _ { 0 }$ ，和一个无约束的容许控制 $\pmb { u } ( t )$ ， $t \in \left[ t _ { 0 } , t _ { 1 } \right]$ ，使状态由 $\boldsymbol { x } ( t _ { 0 } ) { = } \boldsymbol { x } _ { 0 }$ 转移到 $t _ { 1 }$ 时的 ${ \boldsymbol { x } } \left( t _ { 1 } \right) { \boldsymbol { = } } \mathbf { 0 }$ ，则称此 $\mathbf { \delta x } _ { 0 }$ 是在 $t _ { 0 }$ 时刻可控的。

系统可控 对于式(9-76)所示线性时变系统，如果状态空间中的所有非零状态都是在$t _ { 0 } ( t _ { 0 } \in T _ { t } )$ 时刻可控的，则称系统在时刻 $t _ { 0 }$ 是完全可控或一致可控的，简称系统在时刻 $t _ { 0 }$ 可控。

系统不完全可控 对于式(9-76)所示线性时变系统，取定初始时刻 $t _ { 0 } \in T _ { t }$ ，如果状态空间中存在一个或一些非零状态在时刻 $t _ { 0 }$ 是不可控的，则称系统在时刻 $t _ { 0 }$ 是不完全可控的，也称为系统是不可控的。

在上述定义中只要求系统在可找到的控制 ${ \pmb u } \left( t \right)$ 的作用下，使 $t _ { 0 }$ 时刻的非零状态 $\mathbf { \delta x } _ { 0 }$ 在$T _ { t }$ 上的一段有限时间内转移到状态空间的坐标原点，而对于状态转移的轨迹则未加任何限制和规定。所以，可控性是表征系统状态运动的一个定性特性。定义中对控制 ${ \pmb u } \left( t \right)$ 的每个分量的幅值并未加以限制，可为任意大的要求值。但 ${ \pmb u } \left( t \right)$ 必须是容许控制，即 ${ \pmb u } \left( t \right)$ 的每个分量 $u _ { i } ( t ) ( i { = } 1 , 2 , \ \cdots , p )$ 均在时间区间 $T _ { t }$ 上平方可积，即

$$
\int_ {t _ {0}} ^ {T} \left| u _ {i} (t) \right| ^ {2} d t <   \infty ; \quad t _ {0}, t \in T _ {t}
$$

此外，对于线性时变系统，其可控性与初始时刻 $t _ { 0 }$ 的选取有关，是相对于 $T _ { t }$ 中的一个取定时刻 $t _ { 0 }$ 来定义的。而对于线性定常系统，其可控性与初始时刻 $t _ { 0 }$ 的选取无关。

状态与系统的可达 对于式(9-76)所示线性时变系统，若存在能将状态 $\boldsymbol { x } \left( t _ { 0 } \right) { = } \mathbf { 0 }$ 转移到 ${ \pmb x } ( t _ { f } ) = { \pmb x } _ { f }$ 的控制作用，则称状态 $x _ { f }$ 是 $t _ { 0 }$ 时刻可达的。若 $x _ { f }$ 对所有时刻都是可达的，则称 $x _ { f }$ 为完全可达或一致可达。若系统对于状态空间中的每一个状态都是时刻 $t _ { 0 }$ 可达的，则称该系统是 $t _ { 0 }$ 时刻状态完全可达的，或简称该系统是 $t _ { 0 }$ 时刻可达的。

对于线性定常连续系统，可控性与可达性是等价的。但对于离散系统和时变系统，严格地说两者是不等价的。

# 2. 可观测性

可观测性表征了状态可由输出完全反映的性能，所以应同时考虑系统的状态方程和输出方程

$$
\dot {\boldsymbol {x}} (t) = \boldsymbol {A} (t) \boldsymbol {x} (t) + \boldsymbol {B} (t) \boldsymbol {u} (t), \quad t \in T _ {t} \tag {9-77a}
$$

$$
\boldsymbol {y} (t) = \boldsymbol {C} (t) \boldsymbol {x} (t) + \boldsymbol {D} (t) \boldsymbol {u} (t), \quad \boldsymbol {x} \left(t _ {0}\right) = \boldsymbol {x} _ {0} \tag {9-77b}
$$

其中，A(t)、B(t)、 $C ( t )$ 和 ${ \pmb D } ( t )$ 分别为 $( n \times n )$ ， $( n \times p )$ ， $( q \times n )$ 和 $( \boldsymbol { q } \times \boldsymbol { p } )$ 的满足状态方程解的存在唯一性条件的时变矩阵。式(9-77a)状态方程的解为

$$
\boldsymbol {x} (t) = \boldsymbol {\Phi} (t, t _ {0}) \boldsymbol {x} _ {0} + \int_ {t _ {0}} ^ {T} \boldsymbol {\Phi} (t, \tau) \boldsymbol {B} (\tau) \boldsymbol {u} (\tau) \mathrm {d} \tau \tag {9-78}
$$

其中， $\begin{array} { r l } { \\\\Dot { \pmb { \mathcal { D } } } \left( t , \mathrm { \Delta } t _ { 0 } \right) } \end{array}$ 为系统的状态转移矩阵。将式(9-78)代入式(9-77b)输出方程，可得输出响应为

$$
\boldsymbol {y} (t) = \boldsymbol {C} (t) \boldsymbol {\Phi} (t, t _ {0}) \boldsymbol {x} _ {0} + \boldsymbol {C} (t) \int_ {t _ {0}} ^ {T} \boldsymbol {\Phi} (t, \tau) \boldsymbol {B} (\tau) \boldsymbol {u} (\tau) \mathrm {d} \tau + \boldsymbol {D} (t) \boldsymbol {u} (t) \tag {9-79}
$$

在研究可观测性问题时，输出 $\boldsymbol { y }$ 和输入 $\pmb { u }$ 均假定为已知，只有初始状态 $\boldsymbol { x } _ { 0 }$ 是未知的。因此，若定义

$$
\bar {y} (t) \triangleq y (t) - C (t) \int_ {t _ {0}} ^ {T} \boldsymbol {\Phi} (t, \tau) \boldsymbol {B} (\tau) \boldsymbol {u} (\tau) d \tau - D (t) \boldsymbol {u} (t)
$$

则式(9-79)可写为

$$
\bar {\boldsymbol {y}} (t) = \boldsymbol {C} (t) \boldsymbol {\Phi} \left(t, t _ {0}\right) \boldsymbol {x} _ {0} \tag {9-80}
$$

这表明可观测性即是 $\boldsymbol { x } _ { 0 }$ 可由 $\bar { y }$ 完全估计的性能。由于 $\bar { y }$ 和 $\boldsymbol { x } _ { 0 }$ 可取任意值，所以这又等价于研究 $\pmb { u } = \mathbf { 0 }$ 时由 $\boldsymbol { y }$ 来估计 $\boldsymbol { x } _ { 0 }$ 的可能性，即研究零输入方程

$$
\dot {\boldsymbol {x}} (t) = \boldsymbol {A} (t) \boldsymbol {x} (t), \quad \boldsymbol {x} \left(t _ {0}\right) = \boldsymbol {x} _ {0}, \quad t _ {0}, t \in T _ {t} \tag {9-81a}
$$

$$
\boldsymbol {y} (t) = \boldsymbol {C} (t) \boldsymbol {x} (t) \tag {9-81b}
$$

的可观测性。式(9-79)成为

$$
\boldsymbol {y} (t) = \boldsymbol {C} (t) \boldsymbol {\Phi} \left(t, t _ {0}\right) \boldsymbol {x} _ {0} \tag {9-82}
$$

下面基于式(9-81)给出系统可观测性的有关定义。

系统完全可观测 对于式(9-81)所示线性时变系统，如果取定初始时刻 $t _ { 0 } \in T _ { t }$ ，存在一个有限时刻 $t _ { 1 } \in T _ { t }$ ， $t _ { 1 } { > } t _ { 0 }$ ，对于所有 $t \in \left[ t _ { 0 } , t _ { 1 } \right]$ ，系统的输出 $y ( t )$ 能唯一确定状态向量的初值 $\boldsymbol { x } ( t _ { 0 } )$ ，则称系统在 $\left[ t _ { 0 } , \ t _ { 1 } \right]$ 内是完全可观测的，简称系统可观测。如果对于一切 $t _ { 1 } { > } t _ { 0 }$ 系统都是可观测的，则称系统在 $\left[ t _ { 0 } , \infty \right)$ 内完全可观测。

系统不可观测 对于式(9-81)所示线性时变系统，如果取定初始时刻 $t _ { 0 } \in T _ { t }$ ，存在一个有限时刻 $t _ { 1 } \in T _ { t }$ ， $t _ { 1 } { > } t _ { 0 }$ ，对于所有 $t \in \left[ t _ { 0 } , t _ { 1 } \right]$ ，系统的输出 $y ( t )$ 不能唯一确定所有状态的初值 $x _ { i } ( t _ { 0 } )$ ，i=1, 2, …, $n$ ，即至少有一个状态的初值不能被 $y ( t )$ 确定，则称系统在时间区间 $\left[ t _ { 0 } , \ t _ { 1 } \right]$ 内是不完全可观测的，简称系统不可观测。

# 3. 线性定常连续系统的可控性判据

考虑线性定常连续系统的状态方程

$$
\dot {\boldsymbol {x}} (t) = \boldsymbol {A} \boldsymbol {x} (t) + \boldsymbol {B} \boldsymbol {u} (t), \quad \boldsymbol {x} (0) = \boldsymbol {x} _ {0}, \quad t \geqslant 0 \tag {9-83}
$$

其中， $\boldsymbol { x }$ 为 $n$ 维状态向量； $\pmb { u }$ 为 $p$ 维输入向量； $\pmb { A }$ 和 $\pmb { B }$ 分别为 $n \times n$ 和 $n \times p$ 常值矩阵。下面根据 $\pmb { A }$ 和 $\pmb { B }$ 给出系统可控性的常用判据。

格拉姆矩阵判据 线性定常连续系统式(9-83)完全可控的充分必要条件是，存在时刻$t _ { 1 } { > } 0$ ，使如下定义的格拉姆矩阵：

$$
\boldsymbol {W} \left(0, t _ {1}\right) \triangleq \int_ {0} ^ {t _ {1}} \mathrm {e} ^ {- A t} \boldsymbol {B} \boldsymbol {B} ^ {\mathrm {T}} \mathrm {e} ^ {- A ^ {\mathrm {T}} t} \mathrm {d} t \tag {9-84}
$$

为非奇异。

证明 充分性：已知 $\mathbf { \mathit { W } } ( 0 , \mathbf { \Pi } t _ { 1 } )$ 为非奇异，欲证系统完全可控。

已知 W 非奇异，故 $W ^ { - 1 }$ 存在。对任一非零初始状态 $\mathbf { \delta x } _ { 0 }$ 可选取控制 $\pmb { u } ( t )$ 为

$$
\boldsymbol {u} (t) = - \boldsymbol {B} ^ {\mathrm {T}} \mathrm {e} ^ {- \boldsymbol {A} ^ {\mathrm {T}} t} \boldsymbol {W} ^ {- 1} \left(0, t _ {1}\right) \boldsymbol {x} _ {0}, \quad t \in \left[ t _ {0}, t _ {1} \right] \tag {9-85}
$$

则在 $\pmb { u } ( t )$ 作用下系统(9-83)在 $t _ { 1 }$ 时刻的解为

$$
\begin{array}{l} \boldsymbol {x} \left(t _ {1}\right) = \mathrm {e} ^ {\boldsymbol {A} t _ {1}} \boldsymbol {x} _ {0} + \int_ {0} ^ {t _ {1}} \mathrm {e} ^ {\boldsymbol {A} \left(t _ {1} - t\right)} \boldsymbol {B} \boldsymbol {u} (t) \mathrm {d} t \\ = \mathrm {e} ^ {A t _ {1}} \boldsymbol {x} _ {0} - \mathrm {e} ^ {A t _ {1}} \int_ {0} ^ {t _ {1}} \mathrm {e} ^ {- A t} \boldsymbol {B} \boldsymbol {B} ^ {\mathrm {T}} \mathrm {e} ^ {- A ^ {\mathrm {T}} t} \mathrm {d} t \boldsymbol {W} ^ {- 1} (0, t _ {1}) \boldsymbol {x} _ {0} \\ = \mathrm {e} ^ {A t _ {1}} \boldsymbol {x} _ {0} - \mathrm {e} ^ {A t _ {1}} \boldsymbol {W} (0, t _ {1}) \boldsymbol {W} ^ {- 1} (0, t _ {1}) \boldsymbol {x} _ {0} = \boldsymbol {0}, \quad \forall \boldsymbol {x} _ {0} \in R ^ {n} \\ \end{array}
$$

这表明，对任一取定的初始状态 $\pmb { x } _ { 0 } \neq \pmb { 0 }$ ，都存在有限时刻 $t _ { 1 } { > } 0$ 和控制 ${ \pmb u } \left( t \right)$ ，使状态由 $\boldsymbol { x } _ { 0 }$ 转移到 $t _ { 1 }$ 时刻的状态 $\boldsymbol { x } ( t _ { 1 } ) { = } \mathbf { 0 }$ ，于是根据定义可知系统完全可控。充分性得证。

必要性：已知系统完全可控，欲证 $W ( 0 , \ t _ { 1 } )$ 为非奇异。

采用反证法。设 $W ( 0 , \ t _ { 1 } )$ 为奇异，则存在某个非零向量 $\overline { { \boldsymbol { x } } } _ { 0 } \in R ^ { n }$ ，使

$$
\boldsymbol {W} \left(0, t _ {1}\right) \bar {\boldsymbol {x}} _ {0} = \mathbf {0} \tag {9-86}
$$

成立，由此可导出

$$
\begin{array}{l} \overline {{\boldsymbol {x}}} _ {0} ^ {\mathrm {T}} \boldsymbol {W} (0, t _ {1}) \overline {{\boldsymbol {x}}} _ {0} = \int_ {0} ^ {t _ {1}} \overline {{\boldsymbol {x}}} _ {0} ^ {\mathrm {T}} \mathrm {e} ^ {- A t} \boldsymbol {B} \boldsymbol {B} ^ {\mathrm {T}} \mathrm {e} ^ {- A ^ {\mathrm {T}} t} \overline {{\boldsymbol {x}}} _ {0} \mathrm {d} t \\ = \int_ {0} ^ {t _ {1}} \left[ \boldsymbol {B} ^ {\mathrm {T}} \mathrm {e} ^ {- A ^ {\mathrm {T}} t} \overline {{\boldsymbol {x}}} _ {0} \right] ^ {\mathrm {T}} \left[ \boldsymbol {B} ^ {\mathrm {T}} \mathrm {e} ^ {- A ^ {\mathrm {T}} t} \overline {{\boldsymbol {x}}} _ {0} \right] \mathrm {d} t \tag {9-87} \\ = \int_ {0} ^ {t _ {1}} \left\| \boldsymbol {B} ^ {\mathrm {T}} \mathrm {e} ^ {- A ^ {\mathrm {r}} t} \overline {{\boldsymbol {x}}} _ {0} \right\| ^ {2} \mathrm {d} t = 0 \\ \end{array}
$$

其中  为范数，故其必非负。于是，欲使式(9-87)成立，应当有

$$
\boldsymbol {B} ^ {\mathrm {T}} \mathrm {e} ^ {- A ^ {\mathrm {T}} t} \bar {\boldsymbol {x}} _ {0} = \mathbf {0}, \quad \forall t \in [ 0, t _ {1} ] \tag {9-88}
$$

另一方面，因系统完全可控，根据定义，对此非零向量 $\overline { { \boldsymbol { x } } } _ { 0 }$ 应有

$$
\boldsymbol {x} \left(t _ {1}\right) = \mathrm {e} ^ {A t _ {1}} \bar {\boldsymbol {x}} _ {0} + \int_ {0} ^ {t _ {1}} \mathrm {e} ^ {A t _ {1}} \mathrm {e} ^ {- A t} \boldsymbol {B} \boldsymbol {u} (t) \mathrm {d} t = \mathbf {0} \tag {9-89}
$$

由此又可导出

$$
\bar {\boldsymbol {x}} _ {0} = - \int_ {0} ^ {t _ {1}} \mathrm {e} ^ {- A t} \boldsymbol {B} \boldsymbol {u} (t) \mathrm {d} t \tag {9-90}
$$

$$
\left\| \overline {{\boldsymbol {x}}} _ {0} \right\| ^ {2} = \overline {{\boldsymbol {x}}} _ {0} ^ {\mathrm {T}} \overline {{\boldsymbol {x}}} _ {0} = \left[ - \int_ {0} ^ {t _ {1}} \mathrm {e} ^ {- A t} \boldsymbol {B} \boldsymbol {u} (t) \mathrm {d} t \right] ^ {\mathrm {T}} \overline {{\boldsymbol {x}}} _ {0} = - \int_ {0} ^ {t _ {1}} \boldsymbol {u} ^ {\mathrm {T}} (t) \boldsymbol {B} ^ {\mathrm {T}} \mathrm {e} ^ {- A ^ {\mathrm {T}} t} \overline {{\boldsymbol {x}}} _ {0} \mathrm {d} t \tag {9-91}
$$

再利用式(9-88)，由式(9-91)可以得到

$$
\left\| \overline {{{\boldsymbol {x}}}} _ {0} \right\| ^ {2} = 0, \qquad \text {即} \qquad \overline {{{\boldsymbol {x}}}} _ {0} = {\bf 0} \tag {9-92}
$$

显然，此结果与假设 $\overline { { \boldsymbol { x } } } _ { 0 } \neq \mathbf { 0 }$ 相矛盾，即 $W ( 0 , t _ { 1 } )$ 为奇异的反设不成立。因此，若系统完全可控， $W ( 0 , \ t _ { 1 } )$ 必为非奇异。必要性得证。至此格拉姆矩阵判据证毕。

可以看出，在应用格拉姆矩阵判据时需计算矩阵指数 $\mathrm { e } ^ { \boldsymbol { A } t }$ ，在 $\pmb { A }$ 的维数 $n$ 较大时计算$\mathrm { e } ^ { \boldsymbol { A } t }$ 是困难的。所以格拉姆矩阵判据主要用于理论分析。线性定常连续系统可控性的常用判据是直接由矩阵 $\pmb { A }$ 和 $\pmb { B }$ 判断可控性的秩判据。由于在推导秩判据时要用到凯莱-哈密顿定理，所以下面先介绍凯莱-哈密顿定理，然后再给出秩判据。

凯莱-哈密顿定理 设 $n$ 阶矩阵 $\pmb { A }$ 的特征多项式为

$$
\begin{array}{l} f (\lambda) = \left| \lambda I - A \right| \tag {9-93} \\ = \lambda^ {n} + a _ {n - 1} \lambda^ {n - 1} + \dots + a _ {1} \lambda + a _ {0} \\ \end{array}
$$

则 $\pmb { A }$ 满足其特征方程，即

$$
f (\boldsymbol {A}) = \boldsymbol {A} ^ {n} + a _ {n - 1} \boldsymbol {A} ^ {n - 1} + \dots + a _ {1} \boldsymbol {A} + a _ {0} \boldsymbol {I} = \mathbf {0} \tag {9-94}
$$

证明 由于

$$
\left(\lambda I - A\right) ^ {- 1} = \frac {\boldsymbol {B} (\lambda)}{\left| \lambda I - A \right|} = \frac {\boldsymbol {B} (\lambda)}{f (\lambda)} \tag {9-95}
$$

式中，B ()为(IA)的伴随矩阵，其一般展开式为

$$
\boldsymbol {A} = \left[ \begin{array}{c c c c} a _ {1 1} & a _ {1 2} & \dots & a _ {1 n} \\ a _ {2 1} & a _ {2 2} & \dots & a _ {2 n} \\ \vdots & \vdots & & \vdots \\ a _ {n 1} & a _ {n 2} & \dots & a _ {n n} \end{array} \right], \quad \lambda \boldsymbol {I} - \boldsymbol {A} = \left[ \begin{array}{c c c c} \lambda - a _ {1 1} & - a _ {1 2} & \dots & - a _ {1 n} \\ - a _ {2 1} & \lambda - a _ {2 2} & \dots & - a _ {2 n} \\ \vdots & \vdots & & \vdots \\ - a _ {n 1} & - a _ {n 2} & \dots & \lambda - a _ {n n} \end{array} \right]
$$

$$
\boldsymbol {B} (\lambda) = \left[ \begin{array}{c c c c c c c c} (- 1) ^ {1 + 1} & \lambda - a _ {2 2} & \dots & - a _ {2 n} & & \dots & (- 1) ^ {n + 1} & - a _ {1 2} & \dots & - a _ {1 n} \\ & \vdots & & \vdots & & & \vdots & & \vdots \\ & - a _ {n 2} & \dots & \lambda - a _ {n n} & & & - a _ {n - 1, 2} & \dots & - a _ {n - 1, n} \\ & & \vdots & & & & & \vdots \\ (- 1) ^ {1 + n} & - a _ {2 1} & \dots & - a _ {2, n - 1} & & \dots & (- 1) ^ {n + n} & \lambda - a _ {1 1} & \dots & - a _ {1, n - 1} \\ & \vdots & & \vdots & & & \vdots & & \vdots \\ & - a _ {n 1} & \dots & - a _ {n, n - 1} & & & - a _ {n - 1, 1} & \dots & - a _ {n - 1, n - 1} \end{array} \right]
$$

显见 $\pmb { { \cal B } } ( \lambda )$ 的元素均为 $n { - } 1$ 阶多项式，由矩阵加法规则可将其分解为 $n$ 个矩阵之和，即

$$
\boldsymbol {B} (\lambda) = \lambda^ {n - 1} \boldsymbol {B} _ {n - 1} + \lambda^ {n - 2} \boldsymbol {B} _ {n - 2} + \dots + \lambda \boldsymbol {B} _ {1} + \boldsymbol {B} _ {0} \tag {9-96}
$$

式中 $B _ { n - 1 } , B _ { n - 2 } , \cdots , B _ { 0 }$ $\pmb { B } _ { 0 }$ 均为 $n$ 阶矩阵。将式(9-95)两端右乘(IA)，得

$$
\boldsymbol {B} (\lambda) (\lambda \boldsymbol {I} - \boldsymbol {A}) = f (\lambda) \boldsymbol {I} \tag {9-97}
$$

将式(9-96)代入式(9-97)并展开，有

$$
\begin{array}{l} \lambda^ {n} \boldsymbol {B} _ {n - 1} + \lambda^ {n - 1} \left(\boldsymbol {B} _ {n - 2} - \boldsymbol {B} _ {n - 1} \boldsymbol {A}\right) + \lambda^ {n - 2} \left(\boldsymbol {B} _ {n - 3} - \boldsymbol {B} _ {n - 2} \boldsymbol {A}\right) + \dots + \lambda \left(\boldsymbol {B} _ {0} - \boldsymbol {B} _ {1} \boldsymbol {A}\right) - \boldsymbol {B} _ {0} \boldsymbol {A} \tag {9-98} \\ = \lambda^ {n} \boldsymbol {I} + a _ {n - 1} \lambda^ {n - 1} \boldsymbol {I} + \dots + a _ {1} \lambda \boldsymbol {I} - a _ {0} \boldsymbol {I} \\ \end{array}
$$

令式(9-98)等号两边同次项的系数相等，可得

$$
\begin{array}{l} \boldsymbol {B} _ {n - 1} = \boldsymbol {I} \\ \boldsymbol {B} _ {n - 2} - \boldsymbol {B} _ {n - 1} \boldsymbol {A} = a _ {n - 1} \boldsymbol {I} \\ \vdots \tag {9-99} \\ \boldsymbol {B} _ {0} - \boldsymbol {B} _ {1} \boldsymbol {A} = a _ {1} \boldsymbol {I} \\ - \boldsymbol {B} _ {0} \boldsymbol {A} = a _ {0} \boldsymbol {I} \\ \end{array}
$$

将式(9-99)两端按顺序右乘 $A ^ { n } , A ^ { n - 1 } , \enspace \cdots , A , A ^ { 0 }$ 得

$$
\begin{array}{l} \boldsymbol {B} _ {n - 1} \boldsymbol {A} ^ {n} = \boldsymbol {A} ^ {n} \\ \boldsymbol {B} _ {n - 2} \boldsymbol {A} ^ {n - 1} - \boldsymbol {B} _ {n - 1} \boldsymbol {A} ^ {n} = a _ {n - 1} \boldsymbol {A} ^ {n - 1} \\ \vdots \tag {9-100} \\ \boldsymbol {B} _ {0} \boldsymbol {A} - \boldsymbol {B} _ {1} \boldsymbol {A} ^ {2} = a _ {1} \boldsymbol {A} \\ - \boldsymbol {B} _ {0} \boldsymbol {A} = a _ {0} \boldsymbol {I} \\ \end{array}
$$

将式(9-100)中各式相加，可得

$$
f (\boldsymbol {A}) = \boldsymbol {A} ^ {n} + a _ {n - 1} \boldsymbol {A} ^ {n - 1} + \dots + a _ {1} \boldsymbol {A} + a _ {0} \boldsymbol {I} = \boldsymbol {0}
$$

推论 $\mathbf { 1 }$ 矩阵 $\pmb { A }$ 的 $k ( k \geqslant n$ )次幂可表示为 $\pmb { A }$ 的 $n { - } 1$ 阶多项式

$$
\boldsymbol {A} ^ {k} = \sum_ {m = 0} ^ {n - 1} \alpha_ {m} \boldsymbol {A} ^ {m}, \quad k \geqslant n \tag {9-101}
$$

证明 由于

$$
\boldsymbol {A} ^ {n} = - a _ {n - 1} \boldsymbol {A} ^ {n - 1} - a _ {n - 2} \boldsymbol {A} ^ {n - 2} - \dots - a _ {1} \boldsymbol {A} - a _ {0} \boldsymbol {I}
$$

则 $\pmb { A } ^ { n + 1 } = \pmb { A } \pmb { A } ^ { n } = - \pmb { a } _ { n - 1 } \pmb { A } ^ { n } - \pmb { a } _ { n - 2 } \pmb { A } ^ { n - 1 } - \dots - \pmb { a } _ { 1 } \pmb { A } ^ { 2 } - \pmb { a } _ { 0 } \pmb { A }$

$$
\begin{array}{l} = - a _ {n - 1} \left(- a _ {n - 1} \boldsymbol {A} ^ {n - 1} - \dots - a _ {1} \boldsymbol {A} - a _ {0} \boldsymbol {I}\right) - a _ {n - 2} \boldsymbol {A} ^ {n - 1} - \dots - a _ {1} \boldsymbol {A} ^ {2} - a _ {0} \boldsymbol {A} \\ = \left(a _ {n - 1} ^ {2} - a _ {n - 2}\right) A ^ {n - 1} + \left(a _ {n - 1} a _ {n - 2} - a _ {n - 3}\right) A ^ {n - 2} + \dots \\ + \left(a _ {n - 1} a _ {2} - a _ {1}\right) A ^ {2} + \left(a _ {n - 1} a _ {1} - a _ {0}\right) A + a _ {n - 1} a _ {0} I \\ \end{array}
$$

故上述推论成立。式(9-101)中的 $\alpha _ { m }$ 与 $\pmb { A }$ 阵的元素有关。此推论可用以简化矩阵幂的计算。

推论 2 矩阵指数 $\mathrm { e } ^ { \boldsymbol { A } t }$ 可表示为 $\pmb { A }$ 的 $n { - } 1$ 阶多项式

$$
e ^ {A t} = \sum_ {m = 0} ^ {n - 1} \alpha_ {m} (t) A ^ {m} \tag {9-102}
$$

证明 由于

$$
\begin{array}{l} e ^ {A t} = I + A t + \frac {1}{2} A ^ {2} t ^ {2} + \dots + \frac {1}{(n - 1) !} A ^ {n - 1} t ^ {n - 1} + \frac {1}{n !} A ^ {n} t ^ {n} + \frac {1}{(n + 1) !} A ^ {n + 1} t ^ {n + 1} + \dots + \frac {1}{k !} A ^ {k} t ^ {k} + \dots \\ = \boldsymbol {I} + \boldsymbol {A} t + \frac {1}{2} \boldsymbol {A} ^ {2} t ^ {2} + \dots + \frac {1}{(n - 1) !} \boldsymbol {A} ^ {n - 1} t ^ {n - 1} + \frac {1}{n !} (- a _ {n - 1} \boldsymbol {A} ^ {n - 1} - a _ {n - 2} \boldsymbol {A} ^ {n - 2} - \dots - a _ {1} \boldsymbol {A} - a _ {0} \boldsymbol {I}) t ^ {n} \\ + \frac {1}{(n + 1) !} \left[ \left(a _ {n - 1} ^ {2} - a _ {n - 2}\right) A ^ {n - 1} + \left(a _ {n - 1} a _ {n - 2} - a _ {n - 3}\right) A ^ {n - 2} + \dots \right. \\ \left. + \left(a _ {n - 1} a _ {2} - a _ {1}\right) A ^ {2} + \left(a _ {n - 1} a _ {1} - a _ {0}\right) A + a _ {n - 1} a _ {0} I \right] t ^ {n + 1} + \dots \\ = \left(1 - \frac {1}{n !} a _ {0} t ^ {n} + \frac {1}{(n + 1) !} a _ {n - 1} a _ {0} t ^ {n + 1} + \dots\right) I \\ \end{array}
$$

$$
\begin{array}{l} + \left[ t - \frac {1}{n !} a _ {1} t ^ {n} + \frac {1}{(n + 1) !} \left(a _ {n - 1} a _ {1} - a _ {0}\right) t ^ {n + 1} + \dots \right] A \\ + \left[ \frac {1}{2} t ^ {2} - \frac {1}{n !} a _ {2} t ^ {n} + \frac {1}{(n + 1) !} \left(a _ {n - 1} a _ {2} - a _ {1}\right) t ^ {n + 1} + \dots \right] A ^ {2} + \dots \\ + \left[ \frac {1}{(n - 1) !} t ^ {n - 1} - \frac {1}{n !} a _ {n - 1} t ^ {n} + \frac {1}{(n + 1) !} \left(a _ {n - 1} ^ {2} - a _ {n - 2}\right) t ^ {n + 1} + \dots \right] A ^ {n - 1} \\ \end{array}
$$

令

$$
\alpha_ {0} (t) = 1 - \frac {1}{n !} a _ {0} t ^ {n} + \frac {1}{(n + 1) !} a _ {n - 1} a _ {0} t ^ {n + 1} + \dots
$$

$$
\alpha_ {1} (t) = t - \frac {1}{n !} a _ {1} t ^ {n} + \frac {1}{(n + 1) !} \left(a _ {n - 1} a _ {1} - a _ {0}\right) t ^ {n + 1} + \dots
$$

$$
\alpha_ {2} (t) = \frac {1}{2} t ^ {2} - \frac {1}{n !} a _ {2} t ^ {n} + \frac {1}{(n + 1) !} \left(a _ {n - 1} a _ {2} - a _ {1}\right) t ^ {n + 1} + \dots
$$

$$
\alpha_ {n - 1} (t) = \frac {1}{(n - 1) !} t ^ {n - 1} - \frac {1}{n !} a _ {n - 1} t ^ {n} + \frac {1}{(n + 1) !} \left(a _ {n - 1} ^ {2} - a _ {n - 2}\right) t ^ {n + 1} + \dots
$$

则有 $\mathrm { e } ^ { ^ { \boldsymbol { A } t } } = \alpha _ { 0 } ( t ) \boldsymbol { I } + \alpha _ { 1 } ( t ) \boldsymbol { A } + \alpha _ { 2 } ( t ) \boldsymbol { A } ^ { 2 } + \cdots + \alpha _ { n - 1 } ( t ) \boldsymbol { A } ^ { n - 1 } = \sum _ { m = 0 } ^ { n - 1 } \alpha _ { m } ( t ) \boldsymbol { A } ^ { m }$ ( ) m m A

故推论 2 成立。式(9-102)中的 $\alpha _ { m } ( t ) ( m { = } 0 , 1 , 2 , \cdots , n { - } 1 )$ 均为 $t$ 的幂函数，对于 $t \in [ 0 , t _ { f } ]$ ，不同时刻构成的向量组 $[ \alpha _ { 0 } ( 0 )$ , …, n1(0)], …, [0(tf), …, $\alpha _ { n - 1 } ( t _ { f } ) ]$ 是线性无关的向量组，其中任一向量都无法表示成为其他向量的线性组合。同理， $\mathbf { e } ^ { - A t }$ 也可表示为 $\pmb { A }$ 的 $n { - } 1$ 阶多项式

$$
e ^ {- A t} = \sum_ {m = 0} ^ {n - 1} \alpha_ {m} ^ {\prime} (t) A ^ {m} \tag {9-103}
$$

式中 $\alpha _ { 0 } ^ { \prime } ( t ) = 1 - ( - 1 ) ^ { n } { \frac { 1 } { n ! } } a _ { 0 } t ^ { n } + ( - 1 ) ^ { n + 1 } { \frac { 1 } { ( n + 1 ) ! } } a _ { { n - 1 } } a _ { 0 } t ^ { n + 1 } + \cdots$ 11 1  ( 1) n n a t    1 1 0 nn a a t   

$$
\alpha_ {1} ^ {\prime} (t) = - t - (- 1) ^ {n} \frac {1}{n !} a _ {1} t ^ {n} + (- 1) ^ {n + 1} \frac {1}{(n + 1) !} \left(a _ {n - 1} a _ {1} - a _ {0}\right) t ^ {n + 1} + \dots
$$

$$
\alpha_ {n - 1} ^ {\prime} (t) = (- 1) ^ {n - 1} \frac {1}{(n - 1) !} t ^ {n - 1} - (- 1) ^ {n} \frac {1}{n !} a _ {n - 1} t ^ {n} + (- 1) ^ {n + 1} \frac {1}{(n + 1) !} \left(a _ {n - 1} ^ {2} - a _ {n - 2}\right) t ^ {n + 1} + \dots
$$

例 9-10 已知 $\pmb { A } = \left[ \begin{array} { l l } { 1 } & { 2 } \\ { 0 } & { 1 } \end{array} \right]$ $\boldsymbol { A } ^ { 1 0 0 }$

解 $\pmb { A }$ 的特征多项式为

$$
f (\lambda) = \left| \lambda I - A \right| = \left| \begin{array}{c c} \lambda - 1 & - 2 \\ 0 & \lambda - 1 \end{array} \right| = \lambda^ {2} - 2 \lambda + 1
$$

根据凯莱-哈密顿定理，有

$$
f (\boldsymbol {A}) = \boldsymbol {A} ^ {2} - 2 \boldsymbol {A} + \boldsymbol {I} = 0
$$

$$
\boldsymbol {A} ^ {2} = 2 \boldsymbol {A} - \boldsymbol {I}
$$

故 $A ^ { 3 } = A A ^ { 2 } = 2 A ^ { 2 } - A = 2 ( 2 A - I ) - A = 3 A - 2 I$

$$
A ^ {4} = A A ^ {3} = 3 A ^ {2} - 2 A = 3 (2 A - I) - 2 A = 4 A - 3 I
$$

根据数学归纳法，有

$$
\boldsymbol {A} ^ {k} = k \boldsymbol {A} - (k - 1) \boldsymbol {I}
$$

$$
\boldsymbol {A} ^ {1 0 0} = 1 0 0 \boldsymbol {A} - 9 9 \boldsymbol {I} = \left[ \begin{array}{l l} 1 0 0 & 2 0 0 \\ 0 & 1 0 0 \end{array} \right] - \left[ \begin{array}{l l} 9 9 & 0 \\ 0 & 9 9 \end{array} \right] = \left[ \begin{array}{l l} 1 & 2 0 0 \\ 0 & 1 \end{array} \right]
$$

秩判据 线性定常连续系统(9-83)完全可控的充分必要条件是

$$
\operatorname {r a n k} \left[ \begin{array}{l l l l} \boldsymbol {B} & \boldsymbol {A B} & \dots & \boldsymbol {A} ^ {n - 1} \boldsymbol {B} \end{array} \right] = n \tag {9-104}
$$

其中， $n$ 为矩阵 $\pmb { A }$ 的维数； $\pmb { S } = \left[ \pmb { B } \right.$ AB … $\pmb { A } ^ { n - 1 } \pmb { B } \mp$ 称为系统的可控性判别阵。

证明 充分性：已知 $\operatorname { r a n k } S = n$ ，欲证系统完全可控。

采用反证法。反设系统为不完全可控，则根据格拉姆矩阵判据可知

$$
\boldsymbol {W} (0, t _ {1}) = \int_ {0} ^ {t _ {1}} \mathrm {e} ^ {- A t} \boldsymbol {B} \boldsymbol {B} ^ {\mathrm {T}} \mathrm {e} ^ {- A ^ {\mathrm {T}} t} \mathrm {d} t, \quad \forall t _ {1} > 0
$$

为奇异，这意味着存在某个非零 $n$ 维向量 $\pmb { \alpha }$ 使

$$
\boldsymbol {\alpha} ^ {\mathrm {T}} \boldsymbol {W} (0, t _ {1}) \boldsymbol {\alpha} = \int_ {0} ^ {t _ {1}} \boldsymbol {\alpha} ^ {\mathrm {T}} \mathrm {e} ^ {- A t} \boldsymbol {B} \boldsymbol {B} ^ {\mathrm {T}} \mathrm {e} ^ {- A ^ {\mathrm {T}} t} \boldsymbol {\alpha} \mathrm {d} t = \int_ {0} ^ {t _ {1}} \left[ \boldsymbol {\alpha} ^ {\mathrm {T}} \mathrm {e} ^ {- A t} \boldsymbol {B} \right] \left[ \boldsymbol {\alpha} ^ {\mathrm {T}} \mathrm {e} ^ {- A t} \boldsymbol {B} \right] ^ {\mathrm {T}} \mathrm {d} t = 0
$$

成立。显然，由此可导出

$$
\boldsymbol {\alpha} ^ {\mathrm {T}} \mathrm {e} ^ {- A t} \boldsymbol {B} = \mathbf {0}, \quad \forall t \in [ 0, t _ {1} ] \tag {9-105}
$$

将式(9-105)求导直至 $n { - } 1$ 次，再在所得结果中令 $\scriptstyle { t = 0 }$ ，得到

$$
\boldsymbol {\alpha} ^ {\mathrm {T}} \boldsymbol {B} = \mathbf {0}, \quad \boldsymbol {\alpha} ^ {\mathrm {T}} \boldsymbol {A} \boldsymbol {B} = \mathbf {0}, \quad \boldsymbol {\alpha} ^ {\mathrm {T}} \boldsymbol {A} ^ {2} \boldsymbol {B} = \mathbf {0}, \quad \dots , \quad \boldsymbol {\alpha} ^ {\mathrm {T}} \boldsymbol {A} ^ {n - 1} \boldsymbol {B} = \mathbf {0} \tag {9-106}
$$

式(9-106)又可表示为

$$
\boldsymbol {\alpha} ^ {\mathrm {T}} \left[ \begin{array}{l l l l l} \boldsymbol {B} & \boldsymbol {A B} & \boldsymbol {A} ^ {2} \boldsymbol {B} & \dots & \boldsymbol {A} ^ {n - 1} \boldsymbol {B} \end{array} \right] = \boldsymbol {\alpha} ^ {\mathrm {T}} \boldsymbol {S} = \mathbf {0} \tag {9-107}
$$

由于 ${ \pmb { \alpha } } \neq { \bf 0 }$ ，所以式(9-107)意味着 $s$ 为行线性相关，即 rankS $< n$ ，这显然和已知 rankS=n相矛盾。因而反设不成立，系统应为完全可控。

必要性：已知系统完全可控，欲证 $\operatorname { r a n k } S = n$ 。

采用反证法。反设 rankS $< n$ ，这意味着 $s$ 为线性相关，因此必存在一个非零 $n$ 维常数向量 $\pmb { \alpha }$ 使

$$
\boldsymbol {\alpha} ^ {\mathrm {T}} \boldsymbol {S} = \boldsymbol {\alpha} ^ {\mathrm {T}} \left[ \begin{array}{l l l l} \boldsymbol {B} & \boldsymbol {A B} & \dots & \boldsymbol {A} ^ {n - 1} \boldsymbol {B} \end{array} \right] = \boldsymbol {0}
$$

成立。考虑到问题的一般性，由上式可导出

$$
\boldsymbol {\alpha} ^ {\mathrm {T}} \boldsymbol {A} ^ {i} \boldsymbol {B} = \mathbf {0}, \quad i = 0, 1, 2, \dots , n - 1 \tag {9-108}
$$

根据凯莱-哈密顿定理， $A ^ { n }$ ， $A ^ { n + 1 }$ ，…均可表示为 $\pmb { A }$ 的 $n { - } 1$ 阶多项式，因而式(9-108)又可写为

$$
\boldsymbol {\alpha} ^ {\mathrm {T}} \boldsymbol {A} ^ {i} \boldsymbol {B} = \mathbf {0}, \quad i = 0, 1, 2, 3, \dots \tag {9-109}
$$

从而对任意 $t _ { 1 } { > } 0$ 有

$$
(- 1) ^ {i} \boldsymbol {\alpha} ^ {\mathrm {T}} \frac {\boldsymbol {A} ^ {i} t ^ {i}}{i !} \boldsymbol {B} = \mathbf {0}; \quad \forall t \in [ 0, t _ {1} ], \quad i = 0, 1, 2, \dots
$$

或 $\alpha ^ { \mathrm { \scriptscriptstyle T } } \bigg [ I - A t + \frac { 1 } { 2 } A ^ { 2 } t ^ { 2 } - \frac { 1 } { 3 ! } A ^ { 3 } t ^ { 3 } + \cdots \bigg ] B = \alpha ^ { \mathrm { \scriptscriptstyle T } } \mathrm { e } ^ { - A t } B = 0 , \quad \forall t \in \big [ 0 , t _ { 1 } \big ]$ (9-110)

因而有 αT ${ \pmb \alpha } ^ { \mathrm { T } } \int _ { 0 } ^ { t _ { 1 } } \mathrm { e } ^ { - A t } { \pmb B } { \pmb B } ^ { \mathrm { T } } \mathrm { e } ^ { - A ^ { \top } t } \mathrm { d } t { \pmb \alpha } = { \pmb \alpha } ^ { \mathrm { T } } { \pmb W } ( 0 , t _ { 1 } ) { \pmb \alpha } = { \bf 0 }$ (9-111)

因为已知 ${ \pmb { \alpha } } \neq { \bf 0 }$ ，若式(9-111)成立，则 $W ( 0 , \ t _ { 1 } )$ 必为奇异，系统为不完全可控，与已知结果相矛盾。于是有 $\operatorname { r a n k } S = n$ ，必要性得证。秩判据证毕。

例 9-11 桥式网络如图 9-20 所示，试用可控性判据判断其可控性。

![](images/4c2b4673831107efab23fda9120d9f5a720c1763c80a49e7632ec683c66fe244.jpg)  
图 9-20 桥式网络电路图

解 该桥式网络的微分方程为

$$
\dot {i} _ {L} = \dot {i} _ {1} + \dot {i} _ {2} = \dot {i} _ {3} + \dot {i} _ {4}
$$

$$
R _ {4} i _ {4} + u _ {C} = R _ {3} i _ {3}
$$

$$
R _ {1} i _ {1} + u _ {C} = R _ {2} i _ {2}
$$

$$
L \frac {\mathrm {d} i _ {L}}{\mathrm {d} t} + R _ {1} i _ {1} + R _ {3} i _ {3} = u
$$

选取状态变量 $x _ { 1 } { = } i _ { L }$ ， $x _ { 2 } { = } u c$ ，消去微分方组中的 $i _ { 1 }$ ，i2，i3， $i _ { 4 }$ ，可得状态方程

$$
\dot {x} _ {1} = - \frac {1}{L} \left(\frac {R _ {1} R _ {2}}{R _ {1} + R _ {2}} + \frac {R _ {3} R _ {4}}{R _ {3} + R _ {4}}\right) x _ {1} + \frac {1}{L} \left(\frac {R _ {1}}{R _ {1} + R _ {2}} - \frac {R _ {3}}{R _ {3} + R _ {4}}\right) x _ {2} + \frac {1}{L} u
$$

$$
\dot {x} _ {2} = \frac {1}{C} \left(\frac {R _ {2}}{R _ {1} + R _ {2}} - \frac {R _ {4}}{R _ {3} + R _ {4}}\right) x _ {1} - \frac {1}{C} \left(\frac {1}{R _ {1} + R _ {2}} - \frac {1}{R _ {3} + R _ {4}}\right) x _ {2}
$$

其可控性矩阵为

$$
\boldsymbol {S} = \left[ \begin{array}{l l} \boldsymbol {b} & \boldsymbol {A b} \end{array} \right] = \left[ \begin{array}{l l} \frac {1}{L} & - \frac {1}{L ^ {2}} \left(\frac {R _ {1} R _ {2}}{R _ {1} + R _ {2}} + \frac {R _ {3} R _ {4}}{R _ {3} + R _ {4}}\right) \\ 0 & - \frac {1}{L C} \left(\frac {R _ {4}}{R _ {3} + R _ {4}} - \frac {R _ {2}}{R _ {1} + R _ {2}}\right) \end{array} \right]
$$

当 $\frac { R _ { 4 } } { R _ { 3 } + R _ { 4 } } \neq \frac { R _ { 2 } } { R _ { 1 } + R _ { 2 } }$  时， $\operatorname { r a n k } S = 2 { = } n$ ，系统可控。但是，当电桥处于平衡状态，即 $R _ { 1 } R _ { 4 } { = } R _ { 2 } R _ { 3 }$

时， $\frac { R _ { 1 } } { R _ { 1 } + R _ { 2 } } { = } \frac { R _ { 3 } } { R _ { 3 } + R _ { 4 } }$ 及 $\frac { R _ { _ 2 } } { R _ { _ 1 } + R _ { _ 2 } } { = } \frac { R _ { _ 4 } } { R _ { _ 3 } + R _ { _ 4 } }$ 4 R 成立，这时状态方程变为

$$
\dot {x} _ {1} = - \frac {1}{L} \left(\frac {R _ {1} R _ {2}}{R _ {1} + R _ {2}} + \frac {R _ {3} R _ {4}}{R _ {3} + R _ {4}}\right) x _ {1} + \frac {1}{L} u
$$

$$
\dot {x} _ {2} = - \frac {1}{C} \left(\frac {1}{R _ {1} + R _ {2}} - \frac {1}{R _ {3} + R _ {4}}\right) x _ {2}
$$

可控性矩阵为

$$
\boldsymbol {S} = \left[ \begin{array}{l l} \boldsymbol {b} & \boldsymbol {A b} \end{array} \right] = \left[ \begin{array}{c c} \frac {1}{L} & - \frac {1}{L ^ {2}} \left(\frac {R _ {1} R _ {2}}{R _ {1} + R _ {2}} + \frac {R _ {3} R _ {4}}{R _ {3} + R _ {4}}\right) \\ 0 & 0 \end{array} \right]
$$

rankS $\mathop { : = } 1 { < } n$ ，系统不可控， $u$ 不能控制 $x _ { 2 }$ ， $x _ { 2 }$ 是不可控状态变量。

PBH 秩判据 线性定常连续系统(9-83)完全可控的充分必要条件是，对矩阵 $\pmb { A }$ 的所有特征值 $\lambda _ { i } ( i { = } 1 , 2 , \cdots , n )$ ，有

$$
\operatorname {r a n k} \left[ \lambda_ {i} \boldsymbol {I} - \boldsymbol {A} \quad \boldsymbol {B} \right] = n, \quad i = 1, 2, \dots , n \tag {9-112}
$$

均成立，或等价地表示为

$$
\operatorname {r a n k} \left[ s \boldsymbol {I} - \boldsymbol {A} \quad \boldsymbol {B} \right] = n, \quad \forall s \in C \tag {9-113}
$$

由于这一判据是由波波夫(Popov)和贝尔维奇(Belevitch)首先提出，并由豪塔斯(Hautus)最先指出其可广泛应用性，故称为 PBH 秩判据。

证明 必要性：已知系统完全可控，欲证式(9-112)成立。

采用反证法。反设对某个 $\lambda _ { i }$ 有 rank $\begin{array} { r } { [ \lambda _ { i } \pmb { I } - \pmb { A } \quad \pmb { B } ] < _ { n } } \end{array}$ ，则意味着 $\begin{array} { r l } { [ \lambda _ { i } I - A } & { { } B ] } \end{array}$ 为行线性相关，因而必存在一个非零常数向量 $\pmb { \alpha }$ ，使

$$
\boldsymbol {\alpha} ^ {\mathrm {T}} \left[ \begin{array}{l l} \lambda_ {i} \boldsymbol {I} - \boldsymbol {A} & \boldsymbol {B} \end{array} \right] = \boldsymbol {0} \tag {9-114}
$$

成立。考虑到问题的一般性，由式(9-114)可导出

$$
\boldsymbol {\alpha} ^ {\mathrm {T}} \boldsymbol {A} = \lambda_ {i} \boldsymbol {\alpha} ^ {\mathrm {T}}, \quad \boldsymbol {\alpha} ^ {\mathrm {T}} \boldsymbol {B} = \mathbf {0} \tag {9-115}
$$

进而可得

$$
\boldsymbol {\alpha} ^ {T} \boldsymbol {B} = \mathbf {0}, \quad \boldsymbol {\alpha} ^ {T} \boldsymbol {A} \boldsymbol {B} = \lambda_ {i} \boldsymbol {\alpha} ^ {T} \boldsymbol {B} = \mathbf {0}, \quad \dots , \quad \boldsymbol {\alpha} ^ {T} \boldsymbol {A} ^ {n - 1} \boldsymbol {B} = \mathbf {0}
$$

于是有

$$
\boldsymbol {\alpha} ^ {\mathrm {T}} \left[ \begin{array}{l l l l} \boldsymbol {B} & \boldsymbol {A B} & \dots & \boldsymbol {A} ^ {n - 1} \boldsymbol {B} \end{array} \right] = \boldsymbol {\alpha} ^ {\mathrm {T}} \boldsymbol {S} = \mathbf {0} \tag {9-116}
$$

因已知 ${ \pmb { \alpha } } \neq \mathbf { 0 }$ ，所以欲使式(9-116)成立，必有

$$
\operatorname {r a n k} S <   n
$$

这意味着系统不可控，显然与已知条件相矛盾，因而此反设不成立，而式(9-112)成立。考虑到 $\left[ s I - A B \right]$ 为多项式矩阵，且对复数域 $C$ 上除 $\lambda _ { i } ( i { = } 1 , 2 , \cdots , n )$ 以外的所有 $s$ 均有$\operatorname* { d e t } ( s I - A ) { \neq } 0$ ，所以式(9-112)等价于式(9-113)。必要性得证。

充分性：已知式(9-112)成立，欲证系统完全可控。

采用反证法。利用与上述相反的思路，即可证明充分性。至此，PBH秩判据证毕。

例 9-12 已知线性定常连续系统的状态方程为

$$
\dot {\boldsymbol {x}} = \left[ \begin{array}{c c c c} 0 & 1 & 0 & 0 \\ 0 & 0 & - 1 & 0 \\ 0 & 0 & 0 & 1 \\ 0 & 0 & 5 & 0 \end{array} \right] \boldsymbol {x} + \left[ \begin{array}{c c} 0 & 1 \\ 1 & 0 \\ 0 & 1 \\ - 2 & 0 \end{array} \right] \boldsymbol {u}, \quad n = 4
$$

试判别系统的可控性。

解 根据状态方程可写出

$$
\left[ \begin{array}{l l} s \boldsymbol {I} - \boldsymbol {A} & \boldsymbol {B} \end{array} \right] = \left[ \begin{array}{c c c c c c} s & - 1 & 0 & 0 & 0 & 1 \\ 0 & s & 1 & 0 & 1 & 0 \\ 0 & 0 & s & - 1 & 0 & 1 \\ 0 & 0 & - 5 & s & - 2 & 0 \end{array} \right]
$$

考虑到 $\pmb { A }$ 的特征值为 $\lambda _ { 1 } { = } \lambda _ { 2 } { = } 0$ ， $\lambda _ { 3 } { = } \sqrt { 5 }$ ， $\lambda _ { 4 } { = } _ { - } \sqrt { 5 }$ ，所以只需对它们来检验上述矩阵的秩。通过计算可知，当 $s { = } \lambda _ { 1 } { = } \lambda _ { 2 } { = } 0$ 时，有

$$
\operatorname {r a n k} \left[ \begin{array}{l l} s \boldsymbol {I} - \boldsymbol {A} & \boldsymbol {B} \end{array} \right] = \operatorname {r a n k} \left[ \begin{array}{c c c c} - 1 & 0 & 0 & 0 \\ 0 & 1 & 0 & 1 \\ 0 & 0 & - 1 & 0 \\ 0 & - 5 & 0 & - 2 \end{array} \right] = 4
$$

当 $s = \lambda _ { 3 } { = } \sqrt { 5 }$ 时，有

$$
\operatorname {r a n k} \left[ \begin{array}{l l} s \boldsymbol {I} - \boldsymbol {A} & \boldsymbol {B} \end{array} \right] = \operatorname {r a n k} \left[ \begin{array}{c c c c} \sqrt {5} & - 1 & 0 & 1 \\ 0 & \sqrt {5} & 1 & 0 \\ 0 & 0 & 0 & 1 \\ 0 & 0 & - 2 & 0 \end{array} \right] = 4
$$

当 $s { = } \lambda _ { 4 } { = } - \sqrt { 5 }$ 时，有

$$
\operatorname {r a n k} \left[ \begin{array}{l l} s \boldsymbol {I} - \boldsymbol {A} & \boldsymbol {B} \end{array} \right] = \operatorname {r a n k} \left[ \begin{array}{c c c c} - \sqrt {5} & - 1 & 0 & 1 \\ 0 & - \sqrt {5} & 1 & 0 \\ 0 & 0 & 0 & 1 \\ 0 & 0 & - 2 & 0 \end{array} \right] = 4
$$

计算结果表明，充分必要条件式(9-112)成立，故系统完全可控。

对角线规范型判据 若线性定常连续系统(9-83)矩阵 $\pmb { A }$ 的特征值1, 2,…, $\lambda _ { n }$ 两两相异，由线性变换式(9-83)可变为对角线规范型

$$
\dot {\overline {{\boldsymbol {x}}}} = \left[ \begin{array}{c c c c} \lambda_ {1} & & & 0 \\ & \lambda_ {2} & & \\ & & \ddots & \\ 0 & & & \lambda_ {n} \end{array} \right] \overline {{\boldsymbol {x}}} + \overline {{\boldsymbol {B}}} \boldsymbol {u} \tag {9-117}
$$

则系统(9-83)完全可控的充分必要条件是，在式(9-117)中， $\overline { B }$ 不包含元素全为零的行。

证明 可用秩判据予以证明，推证过程略。

例 9-13 已知线性定常连续系统的对角线规范型为

$$
\left[ \begin{array}{l} \dot {\overline {{x}}} _ {1} \\ \dot {\overline {{x}}} _ {2} \\ \dot {\overline {{x}}} _ {3} \end{array} \right] = \left[ \begin{array}{l l l} 8 & 0 & 0 \\ 0 & - 1 & 0 \\ 0 & 0 & 2 \end{array} \right] \left[ \begin{array}{l} \overline {{x}} _ {1} \\ \overline {{x}} _ {2} \\ \overline {{x}} _ {3} \end{array} \right] + \left[ \begin{array}{l l} 0 & 1 \\ 3 & 0 \\ 0 & 2 \end{array} \right] \left[ \begin{array}{l} u _ {1} \\ u _ {2} \end{array} \right]
$$

试判定系统的可控性。

解 由于此规范型中 $\bar { B }$ 不包含元素全为零的行，故系统完全可控。

# 4. 输出可控性

如果系统需要控制的是输出量而不是状态，则需研究系统的输出可控性。

输出可控性 若在有限时间间隔 $\left[ t _ { 0 } , \ t _ { 1 } \right]$ 内，存在无约束分段连续控制函数 ${ \pmb u } \left( t \right)$ ，$t \in \left[ t _ { 0 } , t _ { 1 } \right]$ ，能使任意初始输出 $y ( t _ { 0 } )$ 转移到任意最终输出 $y ( t _ { 1 } )$ ，则称此系统输出完全可控，简称输出可控。

输出可控性判据 设线性定常连续系统的状态方程和输出方程为

$$
\dot {\boldsymbol {x}} = \boldsymbol {A} \boldsymbol {x} + \boldsymbol {B} \boldsymbol {u}, \quad \boldsymbol {x} (0) = \boldsymbol {x} _ {0}, \quad t \in [ 0, t _ {1} ] \tag {9-118}
$$

$$
\boldsymbol {y} = \boldsymbol {C x} + \boldsymbol {D u} \tag {9-119}
$$

式中， $\pmb { u }$ 为 $p$ 维输入向量； $\boldsymbol { y }$ 为 $q$ 维输出向量； $x$ 为 $\pmb { n }$ 维状态向量。状态方程(9-118)的解为

$$
\boldsymbol {x} \left(t _ {1}\right) = \mathrm {e} ^ {\boldsymbol {A} t _ {1}} \boldsymbol {x} _ {0} + \int_ {0} ^ {t _ {1}} \mathrm {e} ^ {\boldsymbol {A} \left(t _ {1} - t\right)} \boldsymbol {B} \boldsymbol {u} (t) \mathrm {d} t
$$

则输出为

$$
\boldsymbol {y} \left(t _ {1}\right) = \boldsymbol {C} \mathrm {e} ^ {\boldsymbol {A} t _ {1}} \boldsymbol {x} _ {0} + \boldsymbol {C} \int_ {0} ^ {t _ {1}} \mathrm {e} ^ {\boldsymbol {A} \left(t _ {1} - t\right)} \boldsymbol {B} \boldsymbol {u} (t) \mathrm {d} t + \boldsymbol {D} \boldsymbol {u} \left(t _ {1}\right) \tag {9-120}
$$

不失一般性，令 $y ( t _ { 1 } ) = 0$ ，并应用凯莱-哈密顿定理的推论 2 有

$$
\begin{array}{l} \boldsymbol {C} \mathrm {e} ^ {\boldsymbol {A} t _ {1}} \boldsymbol {x} _ {0} = - \boldsymbol {C} \int_ {0} ^ {t _ {1}} \mathrm {e} ^ {\boldsymbol {A} (t _ {1} - t)} \boldsymbol {B} \boldsymbol {u} (t) \mathrm {d} t - \boldsymbol {D} \boldsymbol {u} (t _ {1}) \\ = - \boldsymbol {C} \int_ {0} ^ {t _ {1}} \sum_ {m = 0} ^ {n - 1} \alpha_ {m} (t) \boldsymbol {A} ^ {m} \boldsymbol {B} \boldsymbol {u} (t) \mathrm {d} t - \boldsymbol {D} \boldsymbol {u} \left(t _ {1}\right) \\ = - \boldsymbol {C} \sum_ {m = 0} ^ {n - 1} \boldsymbol {A} ^ {m} \boldsymbol {B} \int_ {0} ^ {t _ {1}} \alpha_ {m} (t) \boldsymbol {u} (t) \mathrm {d} t - \boldsymbol {D} \boldsymbol {u} (t _ {1}) \\ \end{array}
$$

令 $\pmb { u } _ { m } ( t _ { 1 } ) = \int _ { 0 } ^ { t _ { 1 } } \alpha _ { m } ( t ) \pmb { u } ( t ) \mathrm { d } t$ ，则

$$
\begin{array}{l} \boldsymbol {C} \mathrm {e} ^ {\boldsymbol {A} t _ {1}} \boldsymbol {x} _ {0} = - \boldsymbol {C} \sum_ {m = 0} ^ {n - 1} \boldsymbol {A} ^ {m} \boldsymbol {B} \boldsymbol {u} _ {m} (t) - \boldsymbol {D} \boldsymbol {u} (t _ {1}) \\ = - C B u _ {0} \left(t _ {1}\right) - C A B u _ {1} \left(t _ {1}\right) - \dots - C A ^ {n - 1} B u _ {n - 1} \left(t _ {1}\right) - D u \left(t _ {1}\right) \\ = - \left[ \begin{array}{l l l l} \boldsymbol {C B} & \boldsymbol {C A B} & \dots & \boldsymbol {C A} ^ {n - 1} \boldsymbol {B} & \boldsymbol {D} \end{array} \right] \left[ \begin{array}{c} \boldsymbol {u} _ {0} \left(t _ {1}\right) \\ \boldsymbol {u} _ {1} \left(t _ {1}\right) \\ \vdots \\ \boldsymbol {u} _ {n - 1} \left(t _ {1}\right) \\ \boldsymbol {u} \left(t _ {1}\right) \end{array} \right] \tag {9-121} \\ \end{array}
$$

令 $\pmb { S } _ { 0 } = \left[ \pmb { C } \pmb { B } \quad \pmb { C } \pmb { A } \pmb { B } \quad \cdots \quad \pmb { C } \pmb { A } ^ { n - 1 } \pmb { B } \quad \pmb { D } \right]$ (9-122)

$\pmb { S } _ { 0 }$ 为 $q \times ( n { + } 1 ) p$ 矩阵，称为输出可控性矩阵。输出可控的充分必要条件是，输出可控性 矩阵的秩等于输出向量的维数 $q$ ，即

$$
\operatorname {r a n k} \boldsymbol {S} _ {0} = q \tag {9-123}
$$

需要注意的是，状态可控性与输出可控性是两个不同的概念，二者没有什么必然的联系。

例 9-14 已知系统的状态方程和输出方程为

$$
\dot {\boldsymbol {x}} = \left[ \begin{array}{c c} 0 & 1 \\ - 1 & - 2 \end{array} \right] \boldsymbol {x} + \left[ \begin{array}{c} 1 \\ - 1 \end{array} \right] u
$$

$$
y = \left[ \begin{array}{c c} 1 & 0 \end{array} \right] x
$$

试判断系统的状态可控性和输出可控性。

解 系统的状态可控性矩阵为

$$
\boldsymbol {S} = \left[ \begin{array}{l l} \boldsymbol {b} & \boldsymbol {A} \boldsymbol {b} \end{array} \right] = \left[ \begin{array}{l l} 1 & - 1 \\ - 1 & 1 \end{array} \right]
$$

$| { \boldsymbol { S } } | = 0$ ，rankS < 2，故状态不完全可控。

输出可控性矩阵为

$$
\boldsymbol {S} _ {0} = \left[ \begin{array}{l l l} \boldsymbol {c b} & \boldsymbol {c A b} & d \end{array} \right] = \left[ \begin{array}{l l l} 1 & - 1 & 0 \end{array} \right]
$$

$\operatorname { r a n k } S _ { 0 } { = } 1 { = } q$ ，故输出可控。

# 5. 线性定常连续系统的可观测性判据

考虑输入 ${ \pmb u } = { \pmb 0 }$ 时系统的状态方程和输出方程

$$
\dot {\boldsymbol {x}} = \boldsymbol {A} \boldsymbol {x}, \quad \boldsymbol {x} (0) = \boldsymbol {x} _ {0}, \quad t \geqslant 0, \quad \boldsymbol {y} = \boldsymbol {C} \boldsymbol {x} \tag {9-124}
$$

式中， $\boldsymbol { x }$ 为 $n$ 维状态向量； $\boldsymbol { y }$ 为 $q$ 维输出向量； $\pmb { A }$ 和 $c$ 分别为 $n \times n$ 和 $q \times n$ 的常值矩阵。

格拉姆矩阵判据 线性定常连续系统(9-124)完全可观测的充分必要条件是，存在有限时刻 $t _ { 1 } { > } 0$ ，使如下定义的格拉姆矩阵：

$$
\boldsymbol {M} (0, t) \triangleq \int_ {0} ^ {t _ {1}} \mathrm {e} ^ {\boldsymbol {A} ^ {T} t} \boldsymbol {C} ^ {\mathrm {T}} \boldsymbol {C} \mathrm {e} ^ {\boldsymbol {A} t} \mathrm {d} t \tag {9-125}
$$

为非奇异。

证明 充分性：已知 $M ( 0 , \ t _ { 1 } )$ 非奇异，欲证系统为完全可观测。

由式(9-124)可得

$$
\boldsymbol {y} (t) = \boldsymbol {C} \boldsymbol {\Phi} (t, 0) \boldsymbol {x} _ {0} = \boldsymbol {C} \mathrm {e} ^ {A t} \boldsymbol {x} _ {0} \tag {9-126}
$$

将式(9-126)左乘 $\mathrm { e } ^ { \boldsymbol { A } ^ { \mathrm { T } } t } \boldsymbol { C } ^ { \mathrm { T } }$ ，然后从 0 到 $t _ { 1 }$ 积分，得

$$
\int_ {0} ^ {t _ {1}} \mathrm {e} ^ {A ^ {\mathrm {T}} t} \boldsymbol {C} ^ {\mathrm {T}} \boldsymbol {y} (t) \mathrm {d} t = \int_ {0} ^ {t _ {1}} \mathrm {e} ^ {A ^ {\mathrm {T}} t} \boldsymbol {C} ^ {\mathrm {T}} \boldsymbol {C} \mathrm {e} ^ {A t} \mathrm {d} t \boldsymbol {x} _ {0} = \boldsymbol {M} \left(0, t _ {1}\right) \boldsymbol {x} _ {0} \tag {9-127}
$$

已知 $M ( 0 , \ t _ { 1 } )$ 非奇异，即 $\mathbf { \delta } M ^ { - 1 } ( 0 , \mathbf { \delta } t _ { 1 } )$ 存在，故由式(9-127)得

$$
\boldsymbol {x} _ {0} = \boldsymbol {M} ^ {- 1} (0, t _ {1}) \int_ {0} ^ {t _ {1}} \mathrm {e} ^ {\boldsymbol {A} ^ {\mathrm {T}} t} \boldsymbol {C} ^ {\mathrm {T}} \boldsymbol {y} (t) \mathrm {d} t
$$

这表明，在 $M ( 0 , \ t _ { 1 } )$ 非奇异的条件下，总可以根据[0，t1]上的输出 $y ( t )$ ，唯一地确定非零初始状态 $\boldsymbol { x } _ { 0 }$ 。因此，系统为完全可观测。充分性得证。

必要性：已知系统完全可观测，欲证 $M ( 0 , \ t _ { 1 } )$ 非奇异。

采用反证法。反设 $M ( 0 , \ t _ { 1 } )$ 奇异，假设存在某一非零 $\overline { { \boldsymbol { x } } } _ { 0 } \in R ^ { n }$ ，使

$$
\overline {{\boldsymbol {x}}} _ {0} ^ {\mathrm {T}} \boldsymbol {M} (0, t _ {1}) \overline {{\boldsymbol {x}}} _ {0} = \int_ {0} ^ {t _ {1}} \overline {{\boldsymbol {x}}} _ {0} ^ {\mathrm {T}} \mathrm {e} ^ {\boldsymbol {A} ^ {\mathrm {T}} t} \boldsymbol {C} ^ {\mathrm {T}} \boldsymbol {C} \mathrm {e} ^ {\boldsymbol {A} t} \overline {{\boldsymbol {x}}} _ {0} \mathrm {d} t = \int_ {0} ^ {t _ {1}} \boldsymbol {y} ^ {\mathrm {T}} (t) \boldsymbol {y} (t) \mathrm {d} t = \int_ {0} ^ {t _ {1}} \| \boldsymbol {y} (t) \| ^ {2} \mathrm {d} t = 0 \tag {9-128}
$$

成立，这意味着

$$
\boldsymbol {y} (t) = \boldsymbol {C} \mathrm {e} ^ {A t} \overline {{\boldsymbol {x}}} _ {0} \equiv \mathbf {0}, \quad \forall t \in \left[ 0, t _ {1} \right]
$$

显然， $\overline { { \boldsymbol { x } } } _ { 0 }$ 为状态空间中的不可观测状态。这和已知系统完全可观测相矛盾，所以反设不成立，必要性得证。至此格拉姆矩阵判据证毕。

秩判据 线性定常连续系统(9-124)完全可观测的充分必要条件是

$$
\operatorname {r a n k} V = \operatorname {r a n k} \left[ \begin{array}{c} C \\ C A \\ \vdots \\ C A ^ {n - 1} \end{array} \right] = n \tag {9-129}
$$

或 $\mathrm { r a n k } V = \mathrm { r a n k } \left[ { \pmb { C } } ^ { \mathrm { T } } \quad { \pmb { A } } ^ { \mathrm { T } } { \pmb { C } } ^ { \mathrm { T } } \quad ( { \pmb { A } } ^ { \mathrm { T } } ) ^ { 2 } { \pmb { C } } ^ { \mathrm { T } } \quad \cdots \quad ( { \pmb { A } } ^ { \mathrm { T } } ) ^ { n - 1 } { \pmb { C } } ^ { \mathrm { T } } \right] = n$ (9-130)

式(9-129)和式(9-130)中的矩阵均称为系统可观测性判别阵，简称可观测性阵。

证明 证明方法与可控性秩判据相似，在此不再详述。这里仅从式(9-126)出发，进一步论证秩判据的充分必要条件。

由式(9-126)，利用 $\mathrm { e } ^ { \boldsymbol { A } t }$ 的级数展开式(9-102)，可得

$$
\begin{array}{l} \boldsymbol {y} (t) = \boldsymbol {C} \mathrm {e} ^ {A t} \boldsymbol {x} _ {0} = \boldsymbol {C} \sum_ {m = 0} ^ {n - 1} \alpha_ {m} (t) A ^ {m} \boldsymbol {x} _ {0} \\ = \left[ \boldsymbol {C} \alpha_ {0} (t) + \boldsymbol {C} \alpha_ {1} (t) \boldsymbol {A} + \dots + \boldsymbol {C} \alpha_ {n - 1} (t) \boldsymbol {A} ^ {n - 1} \right] \boldsymbol {x} _ {0} \\ = \left[ \begin{array}{l l l l} \alpha_ {0} (t) \boldsymbol {I} _ {q} & \alpha_ {1} (t) \boldsymbol {I} _ {q} & \dots & \alpha_ {n - 1} (t) \boldsymbol {I} _ {q} \end{array} \right] \left[ \begin{array}{c} \boldsymbol {C} \\ \boldsymbol {C A} \\ \vdots \\ \boldsymbol {C A} ^ {n - 1} \end{array} \right] \boldsymbol {x} _ {0} \tag {9-131} \\ \end{array}
$$

式中， $I _ { q }$ 为 $q$ 阶单位阵。已知 $[ \alpha _ { 0 } ( t ) I _ { q } \cdots \alpha _ { n - 1 } ( t ) I _ { q } ]$ 的 nq 列线性无关，于是根据测得的 y(t)可唯一确定 $\mathbf { \boldsymbol { x } } _ { 0 }$ 的充分必要条件是

$$
\operatorname {r a n k} V = \operatorname {r a n k} \left[ \begin{array}{c} C \\ C A \\ \vdots \\ C A ^ {n - 1} \end{array} \right] = n
$$

这就是式(9-129)。

例 9-15 判断下列两个系统的可观测性。

$$
\dot {x} = A x + B u, y = C x
$$

$A = { \left[ \begin{array} { l l } { - 2 } & { 0 } \\ { 0 } & { - 1 } \end{array} \right] } , \quad b = { \left[ \begin{array} { l } { 3 } \\ { 1 } \end{array} \right] } , \quad c = { \left[ \begin{array} { l l } { 1 } & { 0 } \end{array} \right] } ;$

解 1) $\mathrm { r a n k } V = \mathrm { r a n k } \left[ \pmb { c } ^ { \top } \quad A ^ { \top } \pmb { c } ^ { \top } \right] = \mathrm { r a n k } \left[ \begin{array} { c c } { 1 } & { - 2 } \\ { 0 } & { 0 } \end{array} \right] = 1 < n = 2$ ，故系统不可观测。

2) $\mathrm { r a n k } V = \mathrm { r a n k } \left[ { \pmb C } ^ { \mathrm { T } } \quad { \pmb A } ^ { \mathrm { T } } { \pmb C } ^ { \mathrm { T } } \right] = \mathrm { r a n k } \left[ \begin{array} { c c c c } { 1 } & { - 1 } & { 1 } & { 0 } \\ { 0 } & { 1 } & { - 1 } & { 2 } \end{array} \right] = 2 = n$ ，故系统可观测。

PBH 秩判据 线性定常连续系统(9-124)完全可观测的充分必要条件是，对矩阵 $\pmb { A }$ 的所有特征值 $\lambda _ { i } ( i { = } 1 , ~ 2 , ~ \cdots , ~ n )$ ，均有

$$
\operatorname {r a n k} \left[ \begin{array}{c} \boldsymbol {C} \\ \lambda_ {i} \boldsymbol {I} - \boldsymbol {A} \end{array} \right] = n; \quad i = 1, 2, \dots , n \tag {9-132}
$$

或等价地表示为

$$
\operatorname {r a n k} \left[ \begin{array}{c} C \\ s I - A \end{array} \right] = n; \quad \forall s \in C \tag {9-133}
$$

对角线规范型判据 线性定常连续系统(9-124)完全可观测的充分必要条件是：

当矩阵 $\pmb { A }$ 的特征值1, $\lambda _ { 2 }$ , …, $\lambda _ { n }$ 两两相异时，由式(9-124)线性变换导出的对角线规范型为

$$
\dot {\bar {x}} = \left[ \begin{array}{c c c c} \lambda_ {1} & & & 0 \\ & \lambda_ {2} & & \\ & & \ddots & \\ 0 & & & \lambda_ {n} \end{array} \right] \bar {x}, \quad y = \bar {C} \bar {x} \tag {9-134}
$$

式中， $\bar { c }$ 不包含元素全为零的列。

例 9-16 已知线性定常连续系统的对角线规范型为

$$
\dot {\bar {x}} = \left[ \begin{array}{c c c} 8 & 0 & 0 \\ 0 & - 1 & 0 \\ 0 & 0 & 2 \end{array} \right] \bar {x}, \quad y = \left[ \begin{array}{c c c} 1 & 0 & 0 \\ 0 & 2 & 3 \end{array} \right] \bar {x}
$$

试判定系统的可观测性。

解 显然，此规范型中 $\bar { c }$ 不包含元素全为零的列，故系统为完全可观测。

# 6. 线性离散时间系统的可控性和可观测性

线性离散时间系统简称为线性离散系统。由于线性定常离散系统只是线性时变离散系统的一种特殊类型，为便于读者全面理解基本概念，我们利用线性时变离散系统给出有关定义，而在介绍可控性和可观测性判据时，受篇幅限制，则仅限于线性定常离散系统。

(1) 线性离散系统的可控性和可达性

设线性时变离散时间系统的状态方程为

$$
\boldsymbol {x} (k + 1) = \boldsymbol {G} (k) \boldsymbol {x} (k) + \boldsymbol {H} (k) \boldsymbol {u} (k), \quad k \in T _ {k} \tag {9-135}
$$

其中 $T _ { k }$ 为离散时间定义区间。如果对初始时刻 $l \in T _ { k }$ 和状态空间中的所有非零状态 $x ( l )$ ，都存在时刻 $m \in T _ { k } , m > l$ ，和对应的控制 ${ \pmb u } \left( k \right)$ ，使得 $\scriptstyle { \boldsymbol { x } } ( m ) = \mathbf { 0 }$ ，则称系统在时刻 $l$ 为完全可

控。对应地，如果对初始时刻 $l \in T _ { k }$ 和初始状态 $\boldsymbol { x } \left( l \right) { = } \mathbf { 0 }$ ，存在时刻 $m \in T _ { k } , m > l$ ，和相应的控制 ${ \pmb u } \left( k \right)$ ，使 $\mathbf { \boldsymbol { x } } \left( \boldsymbol { m } \right)$ 可为状态空间中的任意非零点，则称系统在时刻 $l$ 为完全可达。

对于离散时间系统，不管是时变的还是定常的，其可控性和可达性只有在一定条件下才是等价的。业已证明，其等价的条件分别如下：

1) 线性离散时间系统(9-135)的可控性和可达性为等价的充分必要条件是，系统矩阵$\pmb { G } ( k )$ 对所有 $k \in [ l , m - 1 ]$ 为非奇异。  
2) 线性定常离散时间系统

$$
\boldsymbol {x} (k + 1) = \boldsymbol {G x} (k) + \boldsymbol {H u} (k); \quad k = 0, 1, 2, \dots \tag {9-136}
$$

的可控性和可达性等价的充分必要条件是系统矩阵 $\pmb { G }$ 为非奇异。  
3) 如果线性离散时间系统(9-135)或(9-136)是相应连续时间系统的时间离散化模型，则其可控性和可达性必是等价的。

线性定常离散系统的可控性判据 设单输入线性定常离散系统的状态方程为

$$
\boldsymbol {x} (k + 1) = \boldsymbol {G} \boldsymbol {x} (k) + \boldsymbol {h} u (k) \tag {9-137}
$$

式中， $x$ 为 $n$ 维状态向量； $u$ 为标量输入； $\pmb { G }$ 为 $n \times n$ 非奇异矩阵。状态方程(9-137)的解为

$$
\boldsymbol {x} (k) = \boldsymbol {G} ^ {k} \boldsymbol {x} (0) + \sum_ {i = 0} ^ {k - 1} \boldsymbol {G} ^ {k - 1 - i} \boldsymbol {h u} (i) \tag {9-138}
$$

根据可控性定义，假定 $k { = } n$ 时， $\scriptstyle x ( n ) = \mathbf { 0 }$ ，将式(9-138)两端左乘 $\pmb { G } ^ { - n }$ ，则有

$$
\begin{array}{l} \boldsymbol {x} (0) = - \sum_ {i = 0} ^ {n - 1} \boldsymbol {G} ^ {- 1 - i} \boldsymbol {h u} (i) \\ = - \left[ \boldsymbol {G} ^ {- 1} \boldsymbol {h} u (0) + \boldsymbol {G} ^ {- 2} \boldsymbol {h} u (1) + \dots + \boldsymbol {G} ^ {- n} \boldsymbol {h} u (n - 1) \right] \\ = - \left[ \begin{array}{l l l l} \boldsymbol {G} ^ {- 1} \boldsymbol {h} & \boldsymbol {G} ^ {- 2} \boldsymbol {h} & \dots & \boldsymbol {G} ^ {- n} \boldsymbol {h} \end{array} \right] \left[ \begin{array}{c} u (0) \\ u (1) \\ \vdots \\ u (n - 1) \end{array} \right] \tag {9-139} \\ \end{array}
$$

记 $\pmb { S } _ { 1 } ^ { \prime } = \left[ \pmb { G } ^ { - 1 } \pmb { h } \quad \pmb { G } ^ { - 2 } \pmb { h } \quad \cdots \quad \pmb { G } ^ { - n } \pmb { h } \right]$ (9-140)

称 $\pmb { S } _ { 1 } ^ { \prime }$ 为 $n \times n$ 可控性矩阵。式(9-139)是一个非奇异线性方程组，含 $n$ 个方程，有 $n$ 个未知数 $u ( 0 )$ ， $u ( 1 )$ ，…， $u ( n { - } 1 )$ 。由线性方程组解的存在定理可知，当矩阵 $\pmb { S } _ { 1 } ^ { \prime }$ 的秩与增广矩阵$\big [ S _ { 1 } ^ { \prime } \vdots x ( 0 ) \big ]$ 的秩相等时，方程组有解且为唯一解，否则无解。在 $x \left( 0 \right)$ 为任意的情况下，使方程组有解的充分必要条件是矩阵 $\pmb { S } _ { 1 } ^ { \prime }$ 满秩，即

$$
\operatorname {r a n k} \boldsymbol {S} _ {1} ^ {\prime} = n \tag {9-141}
$$

或矩阵 $\pmb { S } _ { 1 } ^ { \prime }$ 的行列式不为零

$$
\det S _ {1} ^ {\prime} \neq 0 \tag {9-142}
$$

或矩阵 $\pmb { S } _ { 1 } ^ { \prime }$ 是非奇异的。

由于满秩矩阵与另一满秩矩阵 $G ^ { n }$ 相乘其秩不变，故

$$
\operatorname {r a n k} S _ {1} ^ {\prime} = \operatorname {r a n k} \left[ \boldsymbol {G} ^ {n} \boldsymbol {S} _ {1} ^ {\prime} \right] = \operatorname {r a n k} \left[ \boldsymbol {G} ^ {n - 1} \boldsymbol {h} \quad \dots \quad \boldsymbol {G} \boldsymbol {h} \quad \boldsymbol {h} \right] = n \tag {9-143}
$$

交换矩阵的列，且记为 $\pmb { S } _ { 1 }$ ，其秩也不变，故有

$$
\operatorname {r a n k} S _ {1} = \operatorname {r a n k} \left[ \begin{array}{l l l l} \boldsymbol {h} & \boldsymbol {G h} & \dots & \boldsymbol {G} ^ {n - 1} \boldsymbol {h} \end{array} \right] = n \tag {9-144}
$$

由于式(9-144)避免了矩阵求逆，在判断系统的可控性时，使用式(9-144)比较方便。

式(9-141)～式(9-144)都称为可控性判据， $\pmb { S } _ { 1 } ^ { \prime }$ 和 $\pmb { S } _ { 1 }$ 都称为单输入离散系统的可控性矩阵。状态可控性取决于 $\pmb { G }$ 和 $\pmb { h }$ 。

当 $\mathrm { r a n k } S _ { 1 } { < } n$ 时，系统不可控，表示不存在使任意 $x \left( 0 \right)$ 转移至 $\scriptstyle { \boldsymbol { x } } ( n ) = \mathbf { 0 }$ 的控制。

以上研究了终态为 $\scriptstyle { \boldsymbol { x } } ( n ) = \mathbf { 0 }$ 的情况，若令终态为任意给定状态 $x \left( n \right)$ ，则式(9-138)变为

$$
\boldsymbol {G} ^ {n} \boldsymbol {x} (0) - \boldsymbol {x} (n) = - \sum_ {i = 0} ^ {n - 1} \boldsymbol {G} ^ {n - 1 - i} \boldsymbol {h u} (i)
$$

将上式两端左乘 $\pmb { G } ^ { - n }$ ，有

$$
\boldsymbol {x} (0) - \boldsymbol {G} ^ {- n} \boldsymbol {x} (n) = - \left[ \begin{array}{l l l l} \boldsymbol {G} ^ {- 1} \boldsymbol {h} & \boldsymbol {G} ^ {- 2} \boldsymbol {h} & \dots & \boldsymbol {G} ^ {- n} \boldsymbol {h} \end{array} \right] \left[ \begin{array}{c} u (0) \\ u (1) \\ \vdots \\ u (n - 1) \end{array} \right]
$$

当 $\pmb { G }$ 满秩时，该式左端只不过是任意给定的另一初态，其状态可控性条件可用以上推导方法得出完全相同的结论。若令 $\mathbf { \nabla } _ { \mathbf { \boldsymbol { x } } } ( 0 ) { = } \mathbf { 0 }$ ，上述结论同样成立。可见，当 $\pmb { G }$ 为非奇异阵时，系统的可控性和可达性是等价的。

上述研究单输入离散系统可控性的方法可推广到多输入系统。设系统的状态方程为

$$
\boldsymbol {x} (k + 1) = \boldsymbol {G} \boldsymbol {x} (k) + \boldsymbol {H} \boldsymbol {u} (k) \tag {9-145}
$$

所谓可控性问题即是能否求出无约束控制向量序列 ${ \pmb u } ( 0 ) , { \pmb u } ( 1 ) , \cdots , { \pmb u } ( n - 1 )$ ，使系统能从任意初态 $x \left( 0 \right)$ 转移至 $\scriptstyle x ( n ) = \mathbf { 0 }$ 。式(9-145)的解为

$$
\boldsymbol {x} (k) = \boldsymbol {G} ^ {k} \boldsymbol {x} (0) + \sum_ {i = 0} ^ {k - 1} \boldsymbol {G} ^ {k - 1 - i} \boldsymbol {H u} (i) \tag {9-146}
$$

令 $k { = } n$ ， $\scriptstyle x ( n ) = \mathbf { 0 }$ ，且式(9-146)两端左乘 $\pmb { G } ^ { - n }$ ，有

$$
\begin{array}{l} \boldsymbol {x} (0) = - \sum_ {i = 0} ^ {n - 1} \boldsymbol {G} ^ {- 1 - i} \boldsymbol {H u} (i) = - \left[ \boldsymbol {G} ^ {- 1} \boldsymbol {H u} (0) + \boldsymbol {G} ^ {- 2} \boldsymbol {H u} (1) + \dots + \boldsymbol {G} ^ {- n} \boldsymbol {H u} (n - 1) \right] \\ = - \left[ \begin{array}{l l l l} \boldsymbol {G} ^ {- 1} \boldsymbol {H} & \boldsymbol {G} ^ {- 2} \boldsymbol {H} & \dots & \boldsymbol {G} ^ {- n} \boldsymbol {H} \end{array} \right] \left[ \begin{array}{c} \boldsymbol {u} (0) \\ \boldsymbol {u} (1) \\ \vdots \\ \boldsymbol {u} (n - 1) \end{array} \right] \tag {9-147} \\ \end{array}
$$

记 $\pmb { S } _ { 2 } ^ { \prime } = \left[ \pmb { G } ^ { - 1 } \pmb { H } \quad \pmb { G } ^ { - 2 } \pmb { H } \quad \cdots \quad \pmb { G } ^ { - n } \pmb { H } \right]$ (9-148)

为 $n \times n p$ 矩阵，由子列向量 ${ \pmb u } ( 0 ) , { \pmb u } ( 1 ) , \cdots , { \pmb u } ( n - 1 )$ 构成的控制列向量是 $n p$ 维的。式(9-147)含 $n$ 个方程，但有 $n p$ 个待求的控制量。由于初态 $x ( 0 )$ 可任意给定，根据解存在定理，矩阵 $\pmb { S } _ { 2 } ^ { \prime }$ 的秩为 $n$ 时，方程组才有解。于是多输入线性离散系统状态可控的充分必要条件是

$$
\operatorname {r a n k} \boldsymbol {S} _ {2} ^ {\prime} = n \tag {9-149}
$$

或 $\mathrm { r a n k } S _ { 2 } ^ { \prime } = \mathrm { r a n k } { \left[ { \pmb G } ^ { n } S _ { 2 } ^ { \prime } \right] } { = } \mathrm { r a n k } { \left[ { \pmb G } ^ { n - 1 } { \pmb H } \quad \cdots \quad G H \quad H \right] } { = } n$ (9-150)

或 ${ \mathrm { r a n k } } S _ { 2 } = { \mathrm { r a n k } } { \left[ { H \begin{array} { l l l l } { G H } & { \cdots } & { G ^ { n - 1 } H } \end{array} } \right] } = n$ (9-151)

式(9-149) $\sim$ 式(9-151)都是多输入线性离散系统的可控性判据，通常使用式(9-151)较为方便。应当指出：

1) 由于式(9-147)中方程个数少于未知量个数，方程组的解便不唯一，任意假定 npn个控制量，其余 $n$ 个控制量才能唯一确定。多输入线性离散系统控制序列的选择，通常具有无穷多种方式。  
2) 由于 $\pmb { S } _ { 2 }$ 的行数总小于列数，因而在列写 $\pmb { S } _ { 2 }$ 时，只要所选取的列能判断出 $\pmb { S } _ { 2 }$ 的秩为 $n$ ，便不必再将 $\pmb { S } _ { 2 }$ 的其余列都列写出来。  
3) 多输入线性定常离散系统由任意初态转移至原点一般可少于 $n$ 个采样周期。

例 9-17 设单输入线性定常离散系统状态方程为

$$
\boldsymbol {x} (k + 1) = \left[ \begin{array}{c c c} 1 & 0 & 0 \\ 0 & 2 & - 2 \\ - 1 & 1 & 0 \end{array} \right] \boldsymbol {x} (k) + \left[ \begin{array}{l} 1 \\ 0 \\ 1 \end{array} \right] u (k)
$$

试判断其可控性；若初始状态 $\scriptstyle { \mathbf { 1 } } ( 0 ) = [ 2 \ 1 \ 0 ] ^ { \mathrm { T } }$ ，确定使 $\mathbf { \nabla } x \left( 3 \right) = \mathbf { 0 }$ 的控制序列 $u ( 0 ) , u ( 1 ) , u ( 2 )$ ；研究使 $\mathbf { \nabla } x \left( 2 \right) = \mathbf { 0 }$ 的可能性。

解 由题意知

$$
\boldsymbol {G} = \left[ \begin{array}{c c c} 1 & 0 & 0 \\ 0 & 2 & - 2 \\ - 1 & 1 & 0 \end{array} \right], \quad \boldsymbol {h} = \left[ \begin{array}{l} 1 \\ 0 \\ 1 \end{array} \right]
$$

$$
\operatorname {r a n k} \boldsymbol {S} _ {1} = \operatorname {r a n k} \left[ \begin{array}{l l l} \boldsymbol {h} & \boldsymbol {G h} & \boldsymbol {G} ^ {2} \boldsymbol {h} \end{array} \right] = \operatorname {r a n k} \left[ \begin{array}{l l l} 1 & 1 & 1 \\ 0 & - 2 & - 2 \\ 1 & - 1 & - 3 \end{array} \right] = 3 = n
$$

故系统可控。可按式(9-139)求出 $u ( 0 )$ 、 $u ( 1 )$ 、 $u ( 2 )$ ，为了减少求逆阵的麻烦，现用递推法来求。令 $k { = } 0 , 1 , 2$ ，可得状态序列

$$
\boldsymbol {x} (1) = \boldsymbol {G} \boldsymbol {x} (0) + \boldsymbol {h} u (0) = \left[ \begin{array}{l l l} 1 & 0 & 0 \\ 0 & 2 & - 2 \\ - 1 & 1 & 0 \end{array} \right] \left[ \begin{array}{l} 2 \\ 1 \\ 0 \end{array} \right] + \left[ \begin{array}{l} 1 \\ 0 \\ 1 \end{array} \right] u (0) = \left[ \begin{array}{l} 2 \\ 2 \\ - 1 \end{array} \right] + \left[ \begin{array}{l} 1 \\ 0 \\ 1 \end{array} \right] u (0)
$$

$$
\boldsymbol {x} (2) = \boldsymbol {G} \boldsymbol {x} (1) + \boldsymbol {h} u (1) = \left[ \begin{array}{l} 2 \\ 6 \\ 0 \end{array} \right] + \left[ \begin{array}{l} 1 \\ - 2 \\ - 1 \end{array} \right] u (0) + \left[ \begin{array}{l} 1 \\ 0 \\ 1 \end{array} \right] u (1)
$$

$$
\boldsymbol {x} (3) = \boldsymbol {G} \boldsymbol {x} (2) + \boldsymbol {h} u (2) = \left[ \begin{array}{l} 2 \\ 1 2 \\ 4 \end{array} \right] + \left[ \begin{array}{l} 1 \\ - 2 \\ - 3 \end{array} \right] u (0) + \left[ \begin{array}{l} 1 \\ - 2 \\ - 1 \end{array} \right] u (1) + \left[ \begin{array}{l} 1 \\ 0 \\ 1 \end{array} \right] u (2)
$$

令 $\mathbf { \nabla } _ { \mathbf { \boldsymbol { x } } } ( 3 ) { = } \mathbf { 0 }$ ，则有

$$
\left[ \begin{array}{r r r} 1 & 1 & 1 \\ - 2 & - 2 & 0 \\ - 3 & - 1 & 1 \end{array} \right] \left[ \begin{array}{l} u (0) \\ u (1) \\ u (2) \end{array} \right] = \left[ \begin{array}{l} - 2 \\ - 1 2 \\ - 4 \end{array} \right]
$$

其系数矩阵即可控性矩阵 $\pmb { S } _ { 1 }$ 是非奇异的，因而可得

$$
\left[ \begin{array}{l} u (0) \\ u (1) \\ u (2) \end{array} \right] = \left[ \begin{array}{l l l} 1 & 1 & 1 \\ - 2 & - 2 & 0 \\ - 3 & - 1 & 1 \end{array} \right] ^ {- 1} \left[ \begin{array}{l} - 2 \\ - 1 2 \\ - 4 \end{array} \right] = \left[ \begin{array}{l l l} \frac {1}{2} & \frac {1}{2} & - \frac {1}{2} \\ - \frac {1}{2} & - 1 & \frac {1}{2} \\ 1 & \frac {1}{2} & 0 \end{array} \right] \left[ \begin{array}{l} - 2 \\ - 1 2 \\ - 4 \end{array} \right] = \left[ \begin{array}{l} - 5 \\ 1 1 \\ - 8 \end{array} \right]
$$

若令 $\pmb { x } ( 2 ) \mathbf { = } \mathbf { 0 }$ ，即解方程组

$$
\left[ \begin{array}{l l} 1 & 1 \\ - 2 & 0 \\ - 1 & 1 \end{array} \right] \left[ \begin{array}{l} u (0) \\ u (1) \end{array} \right] = \left[ \begin{array}{l} - 2 \\ - 6 \\ 0 \end{array} \right]
$$

容易看出其系数矩阵的秩为 2，但增广矩阵

$$
\left[ \begin{array}{c c c} 1 & 1 & - 2 \\ - 2 & 0 & - 6 \\ - 1 & 1 & 0 \end{array} \right]
$$

的秩为 3，两个秩不等，方程组无解，意味着不能在两个采样周期内使系统由初始状态转移至原点。若该两个秩相等，则可用两步完成状态转移。

# (2) 线性离散系统的可观测性

设离散系统为

$$
\boldsymbol {x} (k + 1) = \boldsymbol {G} (k) \boldsymbol {x} (k) + \boldsymbol {H} (k) \boldsymbol {u} (k), \quad k \in T _ {k}
$$

$$
\boldsymbol {y} (k) = \boldsymbol {C} (k) \boldsymbol {x} (k) + \boldsymbol {D} (k) \boldsymbol {u} (k) \tag {9-152}
$$

若对初始时刻 $l \in T _ { k }$ 的任一非零初始状态 $\boldsymbol { x } \left( l \right) = \boldsymbol { x } _ { 0 }$ ，都存在有限时刻 $m \in T _ { k }$ ， $m { > } l$ ，且可由$[ l , ~ m ]$ 上的输出 $y ( k )$ 唯一地确定 $\boldsymbol { x } _ { 0 }$ ，则称系统在时刻 $l$ 是完全可观测的。

线性定常离散系统的可观测性判据 设线性定常离散系统的动态方程为

$$
\boldsymbol {x} (k + 1) = \boldsymbol {G} \boldsymbol {x} (k) + \boldsymbol {H} \boldsymbol {u} (k), \quad \boldsymbol {y} (k) = \boldsymbol {C} \boldsymbol {x} (k) + \boldsymbol {D} \boldsymbol {u} (k) \tag {9-153}
$$

式中， $x \left( k \right)$ 为 $n$ 维状态向量； $y ( k )$ 为 $q$ 维输出向量，其解为

$$
\boldsymbol {x} (k) = \boldsymbol {G} ^ {k} \boldsymbol {x} (0) + \sum_ {i = 0} ^ {k - 1} \boldsymbol {G} ^ {k - 1 - i} \boldsymbol {H u} (i) \tag {9-154}
$$

$$
\boldsymbol {y} (k) = \boldsymbol {C} \boldsymbol {G} ^ {k} \boldsymbol {x} (0) + \boldsymbol {C} \sum_ {i = 0} ^ {k - 1} \boldsymbol {G} ^ {k - 1 - i} \boldsymbol {H} \boldsymbol {u} (i) + \boldsymbol {D} \boldsymbol {u} (k) \tag {9-155}
$$

研究可观测性问题时， ${ \pmb u } \left( k \right)$ 、G、H、C、D 均为已知，故不失一般性，可将动态方程简化为

$$
\boldsymbol {x} (k + 1) = \boldsymbol {G} \boldsymbol {x} (k), \quad \boldsymbol {y} (k) = \boldsymbol {C} \boldsymbol {x} (k) \tag {9-156}
$$

对应的解为

$$
\boldsymbol {x} (k) = \boldsymbol {G} ^ {k} \boldsymbol {x} (0), \quad \boldsymbol {y} (k) = \boldsymbol {C} \boldsymbol {G} ^ {k} \boldsymbol {x} (0) \tag {9-157}
$$

将 $y ( k )$ 写成展开式

$$
\left\{ \begin{array}{l} \mathbf {y} (0) = \boldsymbol {C} \mathbf {x} (0) \\ \mathbf {y} (1) = \boldsymbol {C} \boldsymbol {G} \mathbf {x} (0) \\ \vdots \\ \mathbf {y} (n - 1) = \boldsymbol {C} \boldsymbol {G} ^ {n - 1} \mathbf {x} (0) \end{array} \right. \tag {9-158}
$$

其向量-矩阵形式为

$$
\left[ \begin{array}{c} \boldsymbol {y} (0) \\ \boldsymbol {y} (1) \\ \vdots \\ \boldsymbol {y} (n - 1) \end{array} \right] = \left[ \begin{array}{c} \boldsymbol {C} \\ \boldsymbol {C G} \\ \vdots \\ \boldsymbol {C G} ^ {n - 1} \end{array} \right] \left[ \begin{array}{c} x _ {1} (0) \\ x _ {2} (0) \\ \vdots \\ x _ {n} (0) \end{array} \right] \tag {9-159}
$$

令 $V _ { 1 } ^ { \mathrm { T } } = \left[ \begin{array} { c } { { C } } \\ { { C G } } \\ { { \vdots } } \\ { { C G ^ { n - 1 } } } \end{array} \right]$ (9-160)

$V _ { \mathrm { 1 } } ^ { \mathrm { T } }$ 称为线性定常离散系统的可观测性矩阵，为 $n q \times n$ 矩阵。式(9-159)含有 nq 个方程，若其中有 $n$ 个独立方程，便可确定唯一的一组 $x _ { 1 } ( 0 )$ ， $x _ { 2 } ( 0 )$ ，…， $x _ { n } ( 0 )$ 。当独立方程个数大于 $n$ 时，解会出现矛盾；当独立方程个数小于 $n$ 时，便有无穷多解。故系统可观测的充分必要条件为

$$
\operatorname {r a n k} V _ {1} ^ {\mathrm {T}} = n \tag {9-161}
$$

由于 rank $V _ { \mathrm { 1 } } ^ { \mathrm { T } } { = } \mathrm { r a n k } V _ { \mathrm { 1 } }$ ，故线性定常离散系统的可观测性判据常表示为

$$
\operatorname {r a n k} V _ {1} = \operatorname {r a n k} \left[ \begin{array}{l l l l} \boldsymbol {C} ^ {\mathrm {T}} & \boldsymbol {G} ^ {\mathrm {T}} \boldsymbol {C} ^ {\mathrm {T}} & \dots & (\boldsymbol {G} ^ {\mathrm {T}}) ^ {n - 1} \boldsymbol {C} ^ {\mathrm {T}} \end{array} \right] = n \tag {9-162}
$$

例 9-18 已知线性定常离散系统的动态方程为

$$
\boldsymbol {x} (k + 1) = \boldsymbol {G x} (k) + \boldsymbol {h u} (k), \quad \boldsymbol {y} (k) = \boldsymbol {C} _ {i} \boldsymbol {x} (k), \quad i = 1, 2
$$

其中 $\mathbf { G } = { \left[ \begin{array} { l l l } { 1 } & { 0 } & { - 1 } \\ { 0 } & { - 2 } & { 1 } \\ { 3 } & { 0 } & { 2 } \end{array} \right] } , \quad h = { \left[ \begin{array} { l } { 2 } \\ { - 1 } \\ { 1 } \end{array} \right] } , \quad c _ { 1 } = { \left[ \begin{array} { l l l } { 0 } & { 1 } & { 0 } \end{array} \right] } , \quad { \mathbf { C } } _ { 2 } = { \left[ \begin{array} { l l l } { 0 } & { 0 } & { 1 } \\ { 1 } & { 0 } & { 0 } \end{array} \right] }$ 1 ， 2C

试判断系统的可观测性，并讨论可观测性的物理解释。

解 当观测矩阵为 $c _ { 1 }$ 时，

$$
\boldsymbol {c} _ {1} ^ {\mathrm {T}} = \left[ \begin{array}{l} 0 \\ 1 \\ 0 \end{array} \right], \quad \boldsymbol {G} ^ {\mathrm {T}} \boldsymbol {c} _ {1} ^ {\mathrm {T}} = \left[ \begin{array}{l} 0 \\ - 2 \\ 1 \end{array} \right], \quad (\boldsymbol {G} ^ {\mathrm {T}}) ^ {2} \boldsymbol {c} _ {1} ^ {\mathrm {T}} = \left[ \begin{array}{l} 3 \\ 4 \\ 0 \end{array} \right]
$$

$$
\operatorname {r a n k} V _ {1} = \operatorname {r a n k} \left[ \begin{array}{c c c} 0 & 0 & 3 \\ 1 & - 2 & 4 \\ 0 & 1 & 0 \end{array} \right] = 3 = n
$$

故系统可观测。由输出方程 $\scriptstyle y ( k ) = c _ { 1 } x ( k ) = x _ { 2 } ( k )$ 可见，在第 $k$ 步便可由输出确定状态变量 $x _ { 2 } ( k )$ 。

由于

$$
y (k + 1) = x _ {2} (k + 1) = - 2 x _ {2} (k) + x _ {3} (k)
$$

故在第 $k { + } 1$ 步便可确定 $x _ { 3 } ( k )$ 。由于

$$
\begin{array}{l} y (k + 2) = x _ {2} (k + 2) = - 2 x _ {2} (k + 1) + x _ {3} (k + 1) \\ = - 2 \left[ - 2 x _ {2} (k) + x _ {3} (k) \right] + 3 x _ {1} (k) + 2 x _ {3} (k) = 4 x _ {2} (k) + 3 x _ {1} (k) \\ \end{array}
$$

故在第 $k { + } 2$ 步便可确定 $x _ { 1 } ( k )$ 。

该系统为三阶系统，可观测意味着至多三步便可由输出 $y ( k )$ ， $y ( k { + } 1 )$ ， $y ( k { + } 2 )$ 的测量值来确定三个状态变量。

当观测矩阵为 $C _ { 2 }$ 时，

$$
\begin{array}{l} \boldsymbol {C} _ {2} ^ {\mathrm {T}} = \left[ \begin{array}{l l} 0 & 1 \\ 0 & 0 \\ 1 & 0 \end{array} \right], \quad \boldsymbol {G} ^ {\mathrm {T}} \boldsymbol {C} _ {2} ^ {\mathrm {T}} = \left[ \begin{array}{l l} 3 & 1 \\ 0 & 0 \\ 2 & - 1 \end{array} \right], \quad (\boldsymbol {G} ^ {\mathrm {T}}) ^ {2} \boldsymbol {C} _ {2} ^ {\mathrm {T}} = \left[ \begin{array}{l l} 9 & - 2 \\ 0 & 0 \\ 1 & - 3 \end{array} \right] \\ \operatorname {r a n k} V _ {1} = \operatorname {r a n k} \left[ \begin{array}{c c c c c c} 0 & 1 & 3 & 1 & 9 & - 2 \\ 0 & 0 & 0 & 0 & 0 & 0 \\ 1 & 0 & 2 & - 1 & 1 & - 3 \end{array} \right] = 2 \neq n = 3 \\ \end{array}
$$

故系统不可观测。

根据系统动态方程可导出

$$
\begin{array}{l} \boldsymbol {y} (k) = \left[ \begin{array}{c} x _ {3} (k) \\ x _ {1} (k) \end{array} \right] \\ \boldsymbol {y} (k + 1) = \left[ \begin{array}{c} x _ {3} (k + 1) \\ x _ {1} (k + 1) \end{array} \right] = \left[ \begin{array}{c} 3 x _ {1} (k) + 2 x _ {3} (k) \\ x _ {1} (k) - x _ {3} (k) \end{array} \right] \\ \boldsymbol {y} (k + 2) = \left[ \begin{array}{l} x _ {3} (k + 2) \\ x _ {1} (k + 2) \end{array} \right] = \left[ \begin{array}{l} 3 x _ {1} (k + 1) + 2 x _ {3} (k + 1) \\ x _ {1} (k + 1) - x _ {3} (k + 1) \end{array} \right] = \left[ \begin{array}{l} 9 x _ {1} (k) + x _ {3} (k) \\ - 2 x _ {1} (k) - 3 x _ {3} (k) \end{array} \right] \\ \end{array}
$$

可看出三步的输出测量值中始终不含 $x _ { 2 } ( k )$ ，故 $x _ { 2 } ( k )$ 是不可观测状态变量。只要有一个状态变量不可观测，则称系统不完全可观测，简称不可观测。

# (3) 连续动态方程离散化后的可控性和可观测性

一个可控的或可观测的连续系统，当其离散化后并不一定能保持其可控性或可观测性，现举例来说明。

设连续系统动态方程为

$$
\left[ \begin{array}{l} \dot {x} _ {1} \\ \dot {x} _ {2} \end{array} \right] = \left[ \begin{array}{c c} 0 & 1 \\ - \omega^ {2} & 0 \end{array} \right] \left[ \begin{array}{l} x _ {1} \\ x _ {2} \end{array} \right] + \left[ \begin{array}{l} 0 \\ 1 \end{array} \right] u, \quad y = \left[ \begin{array}{l l} 0 & 1 \end{array} \right] \left[ \begin{array}{l} x _ {1} \\ x _ {2} \end{array} \right]
$$

由于系统的状态方程为可控标准型，故一定可控。根据可观测性判据，有

$$
\operatorname {r a n k} V _ {1} = \operatorname {r a n k} \left[ \begin{array}{l l} 1 & 0 \\ 0 & 1 \end{array} \right] = 2 = n
$$

故系统可观测。

系统的状态转移矩阵为

$$
\begin{array}{l} \boldsymbol {\Phi} (t) = \mathcal {S} ^ {- 1} \left[ (s \boldsymbol {I} - \boldsymbol {A}) ^ {- 1} \right] = \mathcal {S} ^ {- 1} \left[ \begin{array}{c c} s & - 1 \\ \omega^ {2} & s \end{array} \right] ^ {- 1} = \mathcal {S} ^ {- 1} \left[ \begin{array}{c c} \frac {s}{s ^ {2} + \omega^ {2}} & \frac {1}{s ^ {2} + \omega^ {2}} \\ \frac {- \omega^ {2}}{s ^ {2} + \omega^ {2}} & \frac {s}{s ^ {2} + \omega^ {2}} \end{array} \right] \\ = \left[ \begin{array}{c c} \cos \omega t & \frac {\sin \omega t}{\omega} \\ - \omega \sin \omega t & \cos \omega t \end{array} \right] \\ \end{array}
$$

$$
\boldsymbol {G} (t) = \int_ {0} ^ {t} \varPhi (\tau) \boldsymbol {b} \mathrm {d} \tau = \int_ {0} ^ {T} \left[ \begin{array}{c} \frac {\sin \omega \tau}{\omega} \\ \cos \omega \tau \end{array} \right] \mathrm {d} \tau = \left[ \begin{array}{c} \frac {1 - \cos \omega t}{\omega^ {2}} \\ \frac {\sin \omega t}{\omega} \end{array} \right]
$$

系统离散化后的状态方程为

$$
\begin{array}{l} \boldsymbol {x} (k + 1) = \boldsymbol {\Phi} (T) \boldsymbol {x} (k) + \boldsymbol {G} (T) u (k) \\ = \left[ \begin{array}{l l} \cos \omega T & \frac {\sin \omega T}{\omega} \\ - \omega \sin \omega T & \cos \omega T \end{array} \right] \left[ \begin{array}{l} x _ {1} (k) \\ x _ {2} (k) \end{array} \right] + \left[ \begin{array}{l} \frac {1 - \cos \omega T}{\omega^ {2}} \\ \frac {\sin \omega T}{\omega} \end{array} \right] u (k) \\ \end{array}
$$

离散化后系统的可控性矩阵为

$$
\boldsymbol {S} _ {1} = \left[ \begin{array}{l l} \boldsymbol {G} (T) & \Phi (T) \boldsymbol {G} (T) \end{array} \right] = \left[ \begin{array}{l l} \frac {1 - \cos \omega T}{\omega^ {2}} & \frac {\cos \omega T - \cos^ {2} \omega T + \sin^ {2} \omega T}{\omega^ {2}} \\ \frac {\sin \omega T}{\omega} & \frac {2 \sin \omega T \cos \omega T - \sin \omega T}{\omega} \end{array} \right]
$$

离散化后系统的可观测性矩阵为

$$
\boldsymbol {V} _ {1} = \left[ \begin{array}{l l} \boldsymbol {C} ^ {\mathrm {T}} & \boldsymbol {\Phi} ^ {\mathrm {T}} (T) \boldsymbol {C} ^ {\mathrm {T}} \end{array} \right] = \left[ \begin{array}{l l} 1 & \cos \omega T \\ 0 & \frac {\sin \omega T}{\omega} \end{array} \right]
$$

当采样周期 $T = \frac { k \pi } { \omega } ( k = 1 , 2 , \cdots )$ 时，可控性矩阵 $\pmb { S } _ { 1 }$ 和可观测性矩阵 $V _ { 1 }$ 均出现零行，$\operatorname { r a n k } S _ { 1 } { = } 1 { < } n$ ，ran $\operatorname { k } V _ { 1 } { = } 1 { < } n$ ，系统不可控也不可观测。这表明连续系统可控或可观测时，若采样周期选择不当，对应的离散化系统便有可能不可控或不可观测，也有可能既不可控又不可观测。若连续系统不可控或不可观测，不管采样周期 T 如何选择，离散化后的系统一定是不可控或不可观测的。

# 7. 线性定常系统的线性变换

为便于对系统进行分析和综合设计，经常需要对系统进行各种非奇异变换，例如将 $\pmb { A }$ 阵对角化、约当化、将 $\left\{ A , b \right\}$ 化为可控标准型，将 $\left\{ A , c \right\}$ 化为可观测标准型等，本小节将介绍在线性定常系统研究中常用的一些线性变换方法及非奇异线性变换的一些不变特性。

# (1) 状态空间表达式的线性变换

在研究线性定常连续系统状态空间表达式的建立方法时可以看到，选取不同的状态

变量便有不同形式的动态方程。若两组状态变量之间用一个非奇异矩阵联系着，则两组动态方程的系数矩阵与该非奇异矩阵有确定关系。

设系统动态方程为

$$
\dot {\boldsymbol {x}} = \boldsymbol {A} \boldsymbol {x} + \boldsymbol {b} u, \quad y = \boldsymbol {c x} \tag {9-163}
$$

令 $\scriptstyle { x = P { \overline { { x } } } }$ (9-164)

式中， $P$ 为非奇异线性变换矩阵，它将 $\boldsymbol { x }$ 变换为 $\bar { x }$ ，变换后的动态方程为

$$
\dot {\overline {{\boldsymbol {x}}}} = \overline {{\boldsymbol {A}}} \overline {{\boldsymbol {x}}} + \overline {{\boldsymbol {b}}} u, \quad \overline {{y}} = \overline {{\boldsymbol {c x}}} = y \tag {9-165}
$$

式中 $\overline { { { A } } } = P ^ { - 1 } A P , \quad \overline { { { b } } } = P ^ { - 1 } b , \quad \overline { { { c } } } = c P$ (9-166)

并称为对系统进行 $P$ 变换。对系统进行线性变换的目的在于使 $\overline { { A } }$ 阵规范化，以便揭示系统特性及分析计算，并不会改变系统的原有性质，故称为等价变换。待获得所需结果之后，再引入反变换关系 $\overline { { { \pmb x } } } = { \pmb P } ^ { - 1 } { \pmb x }$ ，换算回原来的状态空间中去，得出最终结果。

下面概括给出本章中常用的几种线性变换关系。

# 1) 化 $\pmb { A }$ 阵为对角型。

$\textcircled{1}$ 设 $\pmb { A }$ 阵为任意形式的方阵，且有 $n$ 个互异实数特征值1，2，…， $\lambda _ { n }$ ，则可由非奇异线性变换化为对角阵 $\varLambda$ 。

$$
\Lambda = \boldsymbol {P} ^ {- 1} \boldsymbol {A} \boldsymbol {P} = \left[ \begin{array}{c c c c} \lambda_ {1} & & & 0 \\ & \lambda_ {2} & & \\ & & \ddots & \\ 0 & & & \lambda_ {n} \end{array} \right] \tag {9-167}
$$

$P$ 阵由 $\pmb { A }$ 阵的实数特征向量 $\pmb { p } _ { i } ( i \mathrm { = 1 } , \ 2 , \ \cdots , \ n ) \mathrm { : }$ 组成

$$
\boldsymbol {P} = \left[ \begin{array}{l l l l} \boldsymbol {p} _ {1} & \boldsymbol {p} _ {2} & \dots & \boldsymbol {p} _ {n} \end{array} \right] \tag {9-168}
$$

特征向量满足

$$
\boldsymbol {A} \boldsymbol {p} _ {i} = \lambda_ {i} P _ {i}, \quad i = 1, 2, \dots , n \tag {9-169}
$$

$\textcircled{2}$ 若 $\pmb { A }$ 阵为友矩阵，且有 $n$ 个互异实数特征值1， $\lambda _ { 2 }$ ，…， $\lambda _ { n }$ ，则下列的范德蒙德(Vandermonde)矩阵 $P$ 可使 $\pmb { A }$ 对角化：

$$
\boldsymbol {A} = \left[ \begin{array}{c c c c c} 0 & 1 & 0 & \dots & 0 \\ 0 & 0 & 1 & \dots & 0 \\ \vdots & \vdots & \vdots & & \vdots \\ 0 & 0 & 0 & \dots & 1 \\ - a _ {0} & - a _ {1} & - a _ {2} & \dots & - a _ {n - 1} \end{array} \right], \quad \boldsymbol {P} = \left[ \begin{array}{c c c c} 1 & 1 & \dots & 1 \\ \lambda_ {1} & \lambda_ {2} & \dots & \lambda_ {n} \\ \lambda_ {1} ^ {2} & \lambda_ {2} ^ {2} & \dots & \lambda_ {n} ^ {2} \\ \vdots & \vdots & & \vdots \\ \lambda_ {1} ^ {n - 1} & \lambda_ {2} ^ {n - 1} & \dots & \lambda_ {n} ^ {n - 1} \end{array} \right] \tag {9-170}
$$

# 2) 化 $\pmb { A }$ 阵为约当型。

设 $\pmb { A }$ 阵具有 $m$ 重实特征值1，其余为 $n { - } m$ 个互异实特征值，但在求解 $A p _ { i } = \lambda _ { 1 } p _ { i }$ 时只有一个独立实特征向量 ${ \pmb p } _ { 1 }$ ，则只能使 $\pmb { A }$ 化为约当阵 $J _ { \circ }$

$$
\boldsymbol {J} = \boldsymbol {P} ^ {- 1} \boldsymbol {A} \boldsymbol {P} = \left[ \begin{array}{c c c c c c c c} \lambda_ {1} & 1 & & & & & \\ & \lambda_ {1} & \ddots & & & 0 & \\ & & \ddots & 1 & & \\ & & & \lambda_ {1} & & \\ \dots & \dots & \dots & \dots & \lambda_ {m + 1} & & \\ & 0 & & & & \ddots & \\ & & & & & & \lambda_ {n} \end{array} \right] \tag {9-171}
$$

$J$ 中虚线示出存在一个约当块。

$$
\boldsymbol {P} = \left[ \begin{array}{l l l l l l} \boldsymbol {p} _ {1} & \boldsymbol {p} _ {2} & \dots & \boldsymbol {p} _ {m} & \boldsymbol {p} _ {m + 1} & \dots & \boldsymbol {p} _ {n} \end{array} \right] \tag {9-172}
$$

式中， ${ \pmb p } _ { 2 }$ , 3 p , …, $\pmb { p } _ { m }$ 是广义实特征向量，满足

$$
\left[ \begin{array}{l l l l} \boldsymbol {p} _ {1} & \boldsymbol {p} _ {2} & \dots & \boldsymbol {p} _ {m} \end{array} \right] \left[ \begin{array}{c c c c} \lambda_ {1} & 1 & & 0 \\ & \lambda_ {1} & \ddots & \\ & & \ddots & 1 \\ 0 & & & \lambda_ {1} \end{array} \right] = A \left[ \begin{array}{l l l l} \boldsymbol {p} _ {1} & \boldsymbol {p} _ {2} & \dots & \boldsymbol {p} _ {m} \end{array} \right] \tag {9-173}
$$

$\pmb { p } _ { m + 1 }$ , …, ${ \pmb p } _ { n }$ 是互异特征值对应的实特征向量。

# 3) 化可控系统为可控标准型。

在前面研究状态空间表达式的建立问题时，曾得出单输入线性定常系统状态方程的可控标准型：

$$
\left[ \begin{array}{l} \dot {x} _ {1} \\ \dot {x} _ {2} \\ \vdots \\ \dot {x} _ {n - 1} \\ \dot {x} _ {n} \end{array} \right] = \left[ \begin{array}{c c c c c} 0 & 1 & 0 & \dots & 0 \\ 0 & 0 & 1 & \dots & 0 \\ \vdots & \vdots & \vdots & & \vdots \\ 0 & 0 & 0 & \dots & 1 \\ - a _ {0} & - a _ {1} & - a _ {2} & \dots & - a _ {n - 1} \end{array} \right] \left[ \begin{array}{l} x _ {1} \\ x _ {2} \\ \vdots \\ x _ {n - 1} \\ x _ {n} \end{array} \right] + \left[ \begin{array}{l} 0 \\ 0 \\ \vdots \\ 0 \\ 1 \end{array} \right] u \tag {9-174}
$$

与该状态方程对应的可控性矩阵 $s$ 是一个右下三角阵，其主对角线元素均为1，故 $\mathrm { \ d e t } \pm 0$ ，系统一定可控，这就是形如式(9-174)中的 $\pmb { A }$ ， $\pmb { b }$ 称为可控标准型名称的由来。其可控性矩阵 S 形如

$$
\boldsymbol {S} = \left[ \begin{array}{l l l l l l} \boldsymbol {b} & \boldsymbol {A} \boldsymbol {b} & \dots & \boldsymbol {A} ^ {n - 1} \boldsymbol {b} \end{array} \right] = \left[ \begin{array}{c c c c c c} 0 & 0 & 0 & \dots & 0 & 1 \\ 0 & 0 & 0 & \dots & 1 & - a _ {n - 1} \\ \vdots & \vdots & \vdots & & \vdots & \vdots \\ 0 & 0 & 1 & \dots & \times & \times \\ 0 & 1 & - a _ {n - 1} & \dots & \times & \times \\ 1 & - a _ {n - 1} & - a _ {n - 2} & \dots & \times & \times \end{array} \right] \tag {9-175}
$$

一个可控系统，当 $\pmb { A }$ ， $\pmb { b }$ 不具有可控标准型时，一定可以选择适当的变换化为可控标准型。设系统状态方程为

$$
\dot {\boldsymbol {x}} = \boldsymbol {A} \boldsymbol {x} + \boldsymbol {b} u \tag {9-176}
$$

进行 $P ^ { - 1 }$ 变换，即令

$$
\boldsymbol {x} = \boldsymbol {P} ^ {- 1} \boldsymbol {z} \tag {9-177}
$$

变换为 $\dot { z } = P A P ^ { - 1 } z + P b u$ (9-178)

要求 $P A P ^ { - 1 } = { \left[ \begin{array} { l l l l l } { 0 } & { 1 } & { 0 } & { \cdots } & { 0 } \\ { 0 } & { 0 } & { 1 } & { \cdots } & { 0 } \\ { \vdots } & { \vdots } & { \vdots } & & { \vdots } \\ { 0 } & { 0 } & { 0 } & { \cdots } & { 1 } \\ { - a _ { 0 } } & { - a _ { 1 } } & { - a _ { 2 } } & { \cdots } & { - a _ { n - 1 } } \end{array} \right] } , \qquad P b = { \left[ \begin{array} { l } { 0 } \\ { 0 } \\ { \vdots } \\ { 0 } \\ { 1 } \end{array} \right] }$ (9-179)

下面具体推导变换矩阵 $P$ ：

设变换矩阵 $P$ 为

$$
\boldsymbol {P} = \left[ \begin{array}{l l l l} \boldsymbol {p} _ {1} ^ {\mathrm {T}} & \boldsymbol {p} _ {2} ^ {\mathrm {T}} & \dots & \boldsymbol {p} _ {n} ^ {\mathrm {T}} \end{array} \right] ^ {\mathrm {T}} \tag {9-180}
$$

根据 $\pmb { A }$ 阵变换要求， $P$ 应满足式(9-179)，有

$$
\left[ \begin{array}{l} \boldsymbol {p} _ {1} \\ \boldsymbol {p} _ {2} \\ \vdots \\ \boldsymbol {p} _ {n - 1} \\ \boldsymbol {p} _ {n} \end{array} \right] \boldsymbol {A} = \left[ \begin{array}{c c c c c} 0 & 1 & 0 & \dots & 0 \\ 0 & 0 & 1 & \dots & 0 \\ \vdots & \vdots & \vdots & & \vdots \\ 0 & 0 & 0 & \dots & 1 \\ - a _ {0} & - a _ {1} & - a _ {2} & \dots & - a _ {n - 1} \end{array} \right] \left[ \begin{array}{l} \boldsymbol {p} _ {1} \\ \boldsymbol {p} _ {2} \\ \vdots \\ \boldsymbol {p} _ {n - 1} \\ \boldsymbol {p} _ {n} \end{array} \right] \tag {9-181}
$$

展开为 ${ \pmb p } _ { 1 } { \pmb A } = { \pmb p } _ { 2 }$

$$
\boldsymbol {p} _ {2} \boldsymbol {A} = \boldsymbol {p} _ {3}
$$

$$
\begin{array}{c} \vdots \\ \vdots \\ \vdots \end{array}
$$

$$
\boldsymbol {p} _ {n - 1} \boldsymbol {A} = \boldsymbol {p} _ {n}
$$

$$
\boldsymbol {p} _ {n} \boldsymbol {A} = - a _ {0} \boldsymbol {p} _ {1} - a _ {1} \boldsymbol {p} _ {2} - \dots - a _ {n - 1} \boldsymbol {p} _ {n}
$$

经整理有 ${ \pmb p } _ { 1 } { \pmb A } = { \pmb p } _ { 2 }$

$$
\boldsymbol {p} _ {2} \boldsymbol {A} = \boldsymbol {p} _ {1} \boldsymbol {A} ^ {2} = \boldsymbol {p} _ {3}
$$

$$
\begin{array}{c} \vdots \\ \vdots \end{array}
$$

$$
\boldsymbol {p} _ {n - 1} \boldsymbol {A} = \boldsymbol {p} _ {1} \boldsymbol {A} ^ {n - 1} = \boldsymbol {p} _ {n}
$$

由此可得变换矩阵

$$
\boldsymbol {P} = \left[ \begin{array}{c} \boldsymbol {p} _ {1} \\ \boldsymbol {p} _ {1} \boldsymbol {A} \\ \vdots \\ \boldsymbol {p} _ {1} \boldsymbol {A} ^ {n - 1} \end{array} \right] \tag {9-182}
$$

又根据 $\pmb { b }$ 阵变换要求， $P$ 应满足式(9-179)，有

$$
\boldsymbol {P} \boldsymbol {b} = \left[ \begin{array}{c} \boldsymbol {p} _ {1} \\ \boldsymbol {p} _ {1} \boldsymbol {A} \\ \vdots \\ \boldsymbol {p} _ {1} \boldsymbol {A} ^ {n - 1} \end{array} \right] \boldsymbol {b} = \boldsymbol {p} _ {1} \left[ \begin{array}{c} \boldsymbol {b} \\ \boldsymbol {A} \boldsymbol {b} \\ \vdots \\ \boldsymbol {A} ^ {n - 1} \boldsymbol {b} \end{array} \right] = \left[ \begin{array}{c} 0 \\ \vdots \\ 0 \\ 1 \end{array} \right] \tag {9-183}
$$

即 $p _ { 1 } \left[ { \pmb b } \quad { \pmb A } { \pmb b } \quad \cdots \quad { \pmb A } ^ { n - 1 } { \pmb b } \right] = \left[ 0 \quad \cdots \quad 0 \quad 1 \right]$ (9-184)

故 $\pmb { p } _ { 1 } = \left[ 0 \quad \cdots \quad 0 \quad 1 \right] \left[ \pmb { b } \quad \pmb { A } \pmb { b } \quad \cdots \quad \pmb { A } ^ { n - 1 } \pmb { b } \right] ^ { - 1 }$ (9-185)

该式表明 ${ \pmb p } _ { 1 }$ 是可控性矩阵的逆阵的最后一行，于是可得出变换矩阵 $P ^ { - 1 }$ 的求法如下：

$\textcircled{1}$ 计算可控性矩阵 $S = [ { \pmb { b } } \quad A { \pmb { b } } \cdots A ^ { n - 1 } { \pmb { b } } ]$ $\pmb { S } = [ \pmb { b }$ ；  
$\textcircled{2}$ 计算可控性矩阵的逆阵 $\pmb { S } ^ { - 1 }$ ，设一般形式为

$$
\boldsymbol {S} ^ {- 1} = \left[ \begin{array}{c c c c} S _ {1 1} & S _ {1 2} & \dots & S _ {1 n} \\ S _ {2 1} & S _ {2 2} & \dots & S _ {2 n} \\ \vdots & \vdots & & \vdots \\ S _ {n 1} & S _ {n 2} & \dots & S _ {n n} \end{array} \right]
$$

$\textcircled{3}$ 取出 $\pmb { S } ^ { - 1 }$ 的最后一行(即第 $n$ 行)构成 ${ \pmb p } _ { 1 }$ 行向量

$$
\boldsymbol {p} _ {1} = \left[ \begin{array}{l l l l} S _ {n 1} & S _ {n 2} & \dots & S _ {n n} \end{array} \right]
$$

$\textcircled{4}$ 构造 $P$ 阵

$$
\boldsymbol {P} = \left[ \begin{array}{c} \boldsymbol {p} _ {1} \\ \boldsymbol {p} _ {1} \boldsymbol {A} \\ \vdots \\ \boldsymbol {p} _ {1} \boldsymbol {A} ^ {n - 1} \end{array} \right]
$$

$\textcircled{5}$ ${ \pmb P } ^ { - 1 }$ 便是将非标准型可控系统化为可控标准型的变换矩阵。

4) 化可观系统为可观标准型。

可观标准型变换过程如下：

$\textcircled{1}$ 针对线性连续定常系统 $( A , \pmb { b } , \pmb { c } )$ ，计算可观性矩阵

$$
V = \left[ \begin{array}{c} c \\ c A \\ \vdots \\ c A ^ {n - 1} \end{array} \right]
$$

$\textcircled{2}$ 求 $V$ 的逆矩阵 $V ^ { - 1 }$ 。  
$\textcircled{3}$ 取 $V ^ { - 1 }$ 的最后一列即第 $n$ 列， 构成向量 $\pmb { p }$   
$\textcircled{4}$ 构造变换矩阵及其逆矩阵

$$
\boldsymbol {P} = \left[ \begin{array}{l l l l} \boldsymbol {p} & \boldsymbol {A} \boldsymbol {p} & \dots & \boldsymbol {A} ^ {n - 1} \boldsymbol {p} \end{array} \right]
$$

$\textcircled{5}$ 求线性变换，得到可观标准型的状态空间表达式

$$
\boldsymbol {A} _ {0} = \boldsymbol {P} ^ {- 1} \boldsymbol {A} \boldsymbol {P}, \quad \boldsymbol {b} _ {0} = \boldsymbol {P} ^ {- 1} \boldsymbol {b}, \quad \boldsymbol {c} _ {0} = \boldsymbol {c} \boldsymbol {P}
$$

例 9-19 已知线性连续定常系统 $( A , b , c )$ 为

$$
\boldsymbol {A} = \left[ \begin{array}{l l l} 2 & - 1 & - 1 \\ 0 & 1 & 0 \\ 0 & 2 & 1 \end{array} \right], \quad \boldsymbol {b} = \left[ \begin{array}{l} 7 \\ 2 \\ 1 \end{array} \right], \quad \boldsymbol {c} = \left[ \begin{array}{l l l} 1 & 1 & 0 \end{array} \right]
$$

请将该系统化为可观标准型，并求出相应的变换矩阵。

解 计算可观性矩阵

$$
\boldsymbol {V} = \left[ \begin{array}{l} \boldsymbol {c} \\ \boldsymbol {c A} \\ \boldsymbol {c A ^ {2}} \end{array} \right] = \left[ \begin{array}{l l l} 1 & 1 & 0 \\ 2 & 0 & - 1 \\ 4 & - 4 & - 3 \end{array} \right]
$$

由于 $\operatorname { r a n k } V = 3 = n$ ，因此系统可观测。

求 $V$ 的逆矩阵

$$
V ^ {- 1} = \left[ \begin{array}{c c c} 2 & - 1. 5 & 0. 5 \\ - 1 & 1. 5 & - 0. 5 \\ 4 & - 4 & 1 \end{array} \right]
$$

取 $V ^ { - 1 }$ 的最后一列

$$
\boldsymbol {p} = \left[ \begin{array}{c} 0. 5 \\ - 0. 5 \\ 1 \end{array} \right]
$$

构造变换矩阵及其逆矩阵

$$
\boldsymbol {P} = \left[ \begin{array}{l l l} \boldsymbol {p} & \boldsymbol {A p} & \boldsymbol {A ^ {2} p} \end{array} \right] = \left[ \begin{array}{l l l} 0. 5 & 0. 5 & 1. 5 \\ - 0. 5 & - 0. 5 & - 0. 5 \\ 1 & 0 & - 1 \end{array} \right]
$$

$$
\boldsymbol {P} ^ {- 1} = \left[ \begin{array}{r r r} 1 & 1 & 1 \\ - 2 & - 4 & - 1 \\ 1 & 1 & 0 \end{array} \right]
$$

$\textcircled{6}$ 线性变换

$$
\boldsymbol {A} _ {0} = \boldsymbol {P} ^ {- 1} \boldsymbol {A} \boldsymbol {P} = \left[ \begin{array}{l l l} 0 & 0 & 2 \\ 1 & 0 & - 5 \\ 0 & 1 & 4 \end{array} \right], \quad \boldsymbol {b} _ {0} = \boldsymbol {P} ^ {- 1} \boldsymbol {b} = \left[ \begin{array}{l} 1 0 \\ - 2 3 \\ 9 \end{array} \right], \quad \boldsymbol {c} _ {0} = \boldsymbol {c} \boldsymbol {P} = \left[ \begin{array}{l l l} 0 & 0 & 1 \end{array} \right]
$$

即得到原系统的可观标准型。

# (2) 对偶原理

在研究系统的可控性和可观测性时，利用对偶原理常常带来许多方便。

设系统为 $\mathcal { Z } _ { 1 } \left( A , B , C \right)$ ，则系统 $\Sigma _ { 2 } ( A ^ { \mathrm { T } } , ~ C ^ { \mathrm { T } } , ~ B ^ { \mathrm { T } } )$ 为系统 $\varSigma _ { 1 }$ 的对偶系统。其动态方程分别为

$$
\boldsymbol {\Sigma} _ {1}: \dot {\boldsymbol {x}} = \boldsymbol {A} \boldsymbol {x} + \boldsymbol {B} \boldsymbol {u}, \quad \boldsymbol {y} = \boldsymbol {C} \boldsymbol {x} \tag {9-186}
$$

$$
\Sigma_ {2}: \dot {\boldsymbol {z}} = \boldsymbol {A} ^ {\mathrm {T}} \boldsymbol {z} + \boldsymbol {C} ^ {\mathrm {T}} v, \quad w = \boldsymbol {B} ^ {\mathrm {T}} \boldsymbol {z} \tag {9-187}
$$

式中， $x , \ z$ 均为 $n$ 维状态向量； $\smash { \pmb { u } } _ { \lambda } , \ w$ $w$ 均为 $p$ 维向量； $y , ~ \nu$ 均为 $q$ 维向量。注意到系统与对偶系统之间，其输入、输出向量的维数是相交换的，当 $\Sigma _ { 2 }$ 为 $\varSigma _ { 1 }$ 的对偶系统时， $\varSigma _ { 1 }$ 也是$\Sigma _ { 2 }$ 的对偶系统。

不难验证，系统 $\varSigma _ { 1 }$ 的可控性判别矩阵 $\left[ \pmb { { B } } \pmb { \mathcal { A } } \pmb { { B } } \cdots \pmb { { A } } ^ { n - 1 } \pmb { { B } } \right]$ 与对偶系统 $\varSigma _ { 2 }$ 的可观测性矩阵$[ ( { \pmb { B } } ^ { \mathrm { T } } ) ^ { \mathrm { T } } \ ( { \pmb { A } } ^ { \mathrm { T } } ) ^ { \mathrm { T } } ( { \pmb { B } } ^ { \mathrm { T } } ) ^ { \mathrm { T } } \cdots ( ( { \pmb { A } } ^ { \mathrm { T } } ) ^ { \mathrm { T } } ) ^ { n - 1 } ( { \pmb { B } } ^ { \mathrm { T } } ) ^ { \mathrm { T } } ]$ 完全相同；系统 $\mathcal { \Sigma } _ { 1 }$ 的可观测性矩阵 $[ { \pmb { C } } ^ { \mathrm { T } } { \pmb { A } } ^ { \mathrm { T } } { \pmb { C } } ^ { \mathrm { T } } \cdots$

$( A ^ { \mathrm { { T } } } ) ^ { n - 1 } C ^ { \mathrm { { T } } } ]$ 与对偶系统 $\varSigma _ { 2 }$ 的可控性判别矩阵 $[ \pmb { C } ^ { \mathrm { T } } \pmb { A } ^ { \mathrm { T } } \pmb { C } ^ { \mathrm { T } } \cdots ( \pmb { A } ^ { \mathrm { T } } ) ^ { n - 1 } \pmb { C } ^ { \mathrm { T } } ]$ 完全相同。

应用对偶原理，能把可观测的单输入-单输出系统化为可观测标准型的问题转化为将其对偶系统化为可控标准型的问题。设单输入-单输出系统动态方程为

$$
\dot {\boldsymbol {x}} = \boldsymbol {A} \boldsymbol {x} + \boldsymbol {b} u, \quad y = \boldsymbol {c x} \tag {9-188}
$$

系统可观测，但 $\pmb { A }$ 、 $c$ 不是可观测标准型。其对偶系统动态方程为

$$
\dot {\boldsymbol {z}} = \boldsymbol {A} ^ {\mathrm {T}} \boldsymbol {z} + \boldsymbol {c} ^ {\mathrm {T}} \boldsymbol {v}, \quad w = \boldsymbol {b} ^ {\mathrm {T}} \boldsymbol {z} \tag {9-189}
$$

对偶系统一定可控，但不是可控标准型。可利用已知的化为可控标准型的原理和步骤，先将对偶系统化为可控标准型，再一次使用对偶原理，便可获得原系统的可观测标准型。下面仅给出其计算步骤：

1) 列出对偶系统的可控性矩阵(即原系统的可观测性矩阵 $V _ { 1 }$ )

$$
\overline {{S}} _ {2} = V _ {1} = \left[ \begin{array}{c c c c} \boldsymbol {c} ^ {\mathrm {T}} & \boldsymbol {A} ^ {\mathrm {T}} \boldsymbol {c} ^ {\mathrm {T}} & \dots & (\boldsymbol {A} ^ {\mathrm {T}}) ^ {n - 1} \boldsymbol {c} ^ {\mathrm {T}} \end{array} \right]
$$

2) 求 $V _ { 1 }$ 的逆阵 $V _ { 1 } ^ { - 1 }$ ，且记为行向量组

$$
V _ {1} ^ {- 1} = \left[ \begin{array}{c} v _ {1} ^ {\mathrm {T}} \\ v _ {2} ^ {\mathrm {T}} \\ \vdots \\ v _ {n} ^ {\mathrm {T}} \end{array} \right]
$$

3) 取 $V _ { 1 } ^ { - 1 }$ 的第 $n$ 行 $ { \boldsymbol \nu } _ { n } ^ { \mathrm { T } }$ ，并按下列规则构造变换矩阵 $P$ ：

$$
\boldsymbol {P} = \left[ \begin{array}{c} v _ {n} ^ {\mathrm {T}} \\ v _ {n} ^ {\mathrm {T}} \boldsymbol {A} ^ {\mathrm {T}} \\ \vdots \\ v _ {n} ^ {\mathrm {T}} (\boldsymbol {A} ^ {\mathrm {T}}) ^ {n - 1} \end{array} \right]
$$

4) 求 $P$ 的逆阵 ${ \pmb P } ^ { - 1 }$ ，并引入 ${ \pmb P } ^ { - 1 }$ 变换，即 ${ \boldsymbol { z } } = { \boldsymbol { p } } ^ { - 1 } { \overline { { \boldsymbol { z } } } }$ ，变换后动态方程为

$$
\dot {\overline {{z}}} = \boldsymbol {P} \boldsymbol {A} ^ {\mathrm {T}} \boldsymbol {P} ^ {- 1} \overline {{z}} + \boldsymbol {P} \boldsymbol {c} ^ {\mathrm {T}} v, \quad \overline {{w}} = \boldsymbol {b} ^ {\mathrm {T}} \boldsymbol {P} ^ {- 1} \overline {{z}}
$$

5) 对对偶系统再利用对偶原理，便可获得原系统的可观测标准型，结果为

$$
\dot {\vec {x}} = \left(\boldsymbol {P} \boldsymbol {A} ^ {\mathrm {T}} \boldsymbol {P} ^ {- 1}\right) ^ {\mathrm {T}} \vec {x} + \left(\boldsymbol {b} ^ {\mathrm {T}} \boldsymbol {P} ^ {- 1}\right) ^ {\mathrm {T}} u = \boldsymbol {P} ^ {- \mathrm {T}} \boldsymbol {A} \boldsymbol {P} ^ {\mathrm {T}} \vec {x} + \boldsymbol {P} ^ {- \mathrm {T}} \boldsymbol {b} u
$$

$$
\bar {y} = \left(\boldsymbol {P c} ^ {\mathrm {T}}\right) ^ {\mathrm {T}} \bar {x} = \boldsymbol {c P} ^ {\mathrm {T}} \bar {x}
$$

与原系统动态方程相比较，可知将原系统化为可观测标准型需要进行 ${ \pmb P } ^ { \mathrm { T } }$ 变换，即令

其中 $\pmb { P } ^ { \mathrm { { T } } } = \left[ \nu _ { n } \quad \pmb { A } \pmb { \nu } _ { n } \quad \cdots \quad \pmb { A } ^ { n - 1 } \nu _ { n } \right]$ (9-191)

$$
\boldsymbol {x} = \boldsymbol {P} ^ {\mathrm {T}} \bar {\boldsymbol {x}} \tag {9-190}
$$

$\nu _ { n }$ 为原系统可观测性矩阵的逆阵中第 $n$ 行的转置。

(3) 非奇异线性变换的不变特性

从前面的研究中可以看到，为了便于研究系统固有特性，常常需要引入非奇异线性变换。例如：将 $\pmb { A }$ 阵对角化或约当化，需进行 $P$ 变换；将 $\pmb { A }$ ， $\pmb { b }$ 化为可控标准型，需进行 $P ^ { - 1 }$ 变换；将 $\pmb { A }$ ， $c$ 化为可观测标准型，需进行 ${ \pmb P } ^ { \mathrm { T } }$ 变换。虽然这些变换中的 $P$ 阵各不相同，但都是非奇异矩阵。经过变换后，系统的固有特性是否会引起改变呢？这当然是人们在研究线性变换时所需要回答的一个重要问题。下面的研究将会表明，系统经过非奇异线性变换，其特征值、传递矩阵、可控性、可观测性等重要性质均保持不变。下面

![](images/155081562f6d91c6ca82eaaf93fb76dc45156e3856ca3ac79f8492e33de8718d.jpg)  
非奇异线性

以 $P$ 变换为例进行论证。

设系统动态方程为

$$
\dot {x} = A x + B u, \quad y = C x + D u
$$

令 $\boldsymbol { x } = \boldsymbol { P } \boldsymbol { \overline { { x } } }$ ，变换后动态方程为

$$
\dot {\vec {x}} = \boldsymbol {P} ^ {- 1} \boldsymbol {A} \boldsymbol {P} \overline {{\boldsymbol {x}}} + \boldsymbol {P} ^ {- 1} \boldsymbol {B} \boldsymbol {u}, \quad \boldsymbol {y} = \overline {{\boldsymbol {y}}} = \boldsymbol {C} \boldsymbol {P} \overline {{\boldsymbol {x}}} + \boldsymbol {D} \boldsymbol {u}
$$

1) 变换后系统特征值不变。变换后系统的特征值为

$$
\begin{array}{l} \left| \lambda I - P ^ {- 1} A P \right| = \left| \lambda P ^ {- 1} P - P ^ {- 1} A P \right| = \left| P ^ {- 1} \lambda P - P ^ {- 1} A P \right| \\ = \left| \boldsymbol {P} ^ {- 1} (\lambda \boldsymbol {I} - \boldsymbol {A}) \boldsymbol {P} \right| = \left| \boldsymbol {P} ^ {- 1} \right| \left| \lambda \boldsymbol {I} - \boldsymbol {A} \right| \left| \boldsymbol {P} \right| = \left| \boldsymbol {P} ^ {- 1} \right| \left| \boldsymbol {P} \right| \left| \lambda \boldsymbol {I} - \boldsymbol {A} \right| \\ = \left| \boldsymbol {P} ^ {- 1} \boldsymbol {P} \right| \left| \lambda \boldsymbol {I} - \boldsymbol {A} \right| = \left| \boldsymbol {I} \right| \left| \lambda \boldsymbol {I} - \boldsymbol {A} \right| = \left| \lambda \boldsymbol {I} - \boldsymbol {A} \right| \\ \end{array}
$$

可见，系统变换后与变换前的特征值完全相同，这说明对于非奇异线性变换，系统特征值具有不变性。

2) 变换后系统传递矩阵不变。变换后系统的传递矩阵为

$$
\begin{array}{l} \boldsymbol {G} ^ {\prime} (s) = \boldsymbol {C P} (s \boldsymbol {I} - \boldsymbol {P} ^ {- 1} \boldsymbol {A} \boldsymbol {P}) ^ {- 1} \boldsymbol {P} ^ {- 1} \boldsymbol {B} + \boldsymbol {D} \\ = C P \left(P ^ {- 1} s I P - P ^ {- 1} A P\right) ^ {- 1} P ^ {- 1} B + D \\ = C P \left[ P ^ {- 1} (s I - A) P \right] ^ {- 1} P ^ {- 1} B + D \\ = C P P ^ {- 1} (s I - A) ^ {- 1} P P ^ {- 1} B + D \\ = \boldsymbol {C} (s \boldsymbol {I} - \boldsymbol {A}) ^ {- 1} \boldsymbol {B} + \boldsymbol {D} = \boldsymbol {G} (s) \\ \end{array}
$$

这表明变换前与变换后系统的传递矩阵完全相同，系统的传递矩阵对于非奇异线性变换具有不变性。

3) 变换后系统可控性不变。变换后系统可控性矩阵的秩为

$$
\begin{array}{l} \operatorname {r a n k} S ^ {\prime} = \operatorname {r a n k} \left[ \begin{array}{l l l l l l} P ^ {- 1} B & (P ^ {- 1} A P) P ^ {- 1} B & (P ^ {- 1} A P) ^ {2} P ^ {- 1} B & \dots & (P ^ {- 1} A P) ^ {n - 1} P ^ {- 1} B \end{array} \right] \\ = \operatorname {r a n k} \left[ \begin{array}{l l l l l} \boldsymbol {P} ^ {- 1} \boldsymbol {B} & \boldsymbol {P} ^ {- 1} \boldsymbol {A} \boldsymbol {B} & \boldsymbol {P} ^ {- 1} \boldsymbol {A} ^ {2} \boldsymbol {B} & \dots & \boldsymbol {P} ^ {- 1} \boldsymbol {A} ^ {n - 1} \boldsymbol {B} \end{array} \right] \\ = \operatorname {r a n k} P ^ {- 1} \left[ \begin{array}{l l l l l} B & A B & A ^ {2} B & \dots & A ^ {n - 1} B \end{array} \right] \\ = \operatorname {r a n k} \left[ \begin{array}{l l l l l} \boldsymbol {B} & \boldsymbol {A B} & \boldsymbol {A} ^ {2} \boldsymbol {B} & \dots & \boldsymbol {A} ^ {n - 1} \boldsymbol {B} \end{array} \right] = \operatorname {r a n k} S \\ \end{array}
$$

式中， $\pmb { S } ^ { \prime }$ 为变换后系统的可控性矩阵；S 为变换前系统的可控性矩阵。可见，变换后与变换前系统可控性矩阵的秩相等，根据系统可控性的秩判据可知，对于非奇异线性变换，系统的可控性不变。

4) 变换后系统可观测性不变。设变换后系统的可观测性矩阵为 $V ^ { \prime }$ ，变换前系统的可观测性矩阵为 V，则有

$$
\begin{array}{l} \operatorname {r a n k} V ^ {\prime} = \operatorname {r a n k} \left[ \left(\boldsymbol {C P}\right) ^ {\mathrm {T}} \quad \left(\boldsymbol {P} ^ {- 1} \boldsymbol {A P}\right) ^ {\mathrm {T}} \left(\boldsymbol {C P}\right) ^ {\mathrm {T}} \quad \left(\left(\boldsymbol {P} ^ {- 1} \boldsymbol {A P}\right) ^ {2}\right) ^ {\mathrm {T}} \left(\boldsymbol {C P}\right) ^ {\mathrm {T}} \dots \quad \left(\left(\boldsymbol {P} ^ {- 1} \boldsymbol {A P}\right) ^ {n - 1}\right) ^ {\mathrm {T}} \left(\boldsymbol {C P}\right) ^ {\mathrm {T}} \right] \\ = \operatorname {r a n k} \left[ \begin{array}{l l l l l} \boldsymbol {P} ^ {\mathrm {T}} \boldsymbol {C} ^ {\mathrm {T}} & \boldsymbol {P} ^ {\mathrm {T}} \boldsymbol {A} ^ {\mathrm {T}} \boldsymbol {C} ^ {\mathrm {T}} & \boldsymbol {P} ^ {\mathrm {T}} (\boldsymbol {A} ^ {2}) ^ {\mathrm {T}} \boldsymbol {C} ^ {\mathrm {T}} & \dots & \boldsymbol {P} ^ {\mathrm {T}} (\boldsymbol {A} ^ {n - 1}) ^ {\mathrm {T}} \boldsymbol {C} ^ {\mathrm {T}} \end{array} \right] \\ = \operatorname {r a n k} P ^ {\mathrm {T}} \left[ \begin{array}{l l l l l} C ^ {\mathrm {T}} & A ^ {\mathrm {T}} C ^ {\mathrm {T}} & (A ^ {2}) ^ {\mathrm {T}} C ^ {\mathrm {T}} & \dots & (A ^ {n - 1}) ^ {\mathrm {T}} C ^ {\mathrm {T}} \end{array} \right] \\ = \operatorname {r a n k} \left[ \begin{array}{l l l l l} \boldsymbol {C} ^ {\mathrm {T}} & \boldsymbol {A} ^ {\mathrm {T}} \boldsymbol {C} ^ {\mathrm {T}} & (\boldsymbol {A} ^ {2}) ^ {\mathrm {T}} \boldsymbol {C} ^ {\mathrm {T}} & \dots & (\boldsymbol {A} ^ {n - 1}) ^ {\mathrm {T}} \boldsymbol {C} ^ {\mathrm {T}} \end{array} \right] = \operatorname {r a n k} V \\ \end{array}
$$

可见，变换后与变换前系统的可观测性矩阵的秩相等，故系统的可观测性不变。

# (4) 线性定常系统的结构分解

系统中只要有一个状态变量不可控便称系统不可控，因而不可控系统便含有可控和不可控两种状态变量。类似地，系统中只要有一个状态变量不可观测便称系统不可观测，不可观测系统含有可观测和不可观测两种状态变量。从可控性和可观测性出发，状态变量便可分为可控可观测 $\scriptstyle { \boldsymbol { x } } _ { c o }$ 、可控不可观测 $\mathbf { x } _ { c \overline { { o } } }$ 、不可控可观测 $\scriptstyle { x _ { \overline { { c } } o } }$ 、不可控不可观测 $\pmb { x } _ { \scriptscriptstyle { c o } }$ 四类。由对应状态变量构成的子空间也分为四类，因而系统也对应分成了四类子系统，称为系统的结构分解，也有的参考文献称此为系统的规范分解。研究结构分解可以更明显地揭示系统的结构特性、传递特性。研究方法是选取一种特殊的线性变换，使原来的状态向量 $\boldsymbol { x }$ 变换成 $[ { \pmb x } _ { c o } ^ { \mathrm { { T } } } \ { \pmb x } _ { c \overline { { o } } } ^ { \mathrm { { T } } } \ { \pmb x } _ { \overline { { c } } o } ^ { \mathrm { { T } } } \ { \pmb x } _ { \overline { { c } } o } ^ { \mathrm { { T } } } \ { \pmb x } _ { \overline { { c } } o } ^ { \mathrm { { T } } } ] ^ { \mathrm { { T } } }$ ，相应地使原动态方程中的 A、B、 $c$ 矩阵变换成某种标准构造的形式。结构分解过程可先从整个系统的可控性分解开始，将可控与不可控的状态变量分离开，继而分别对可控和不可控子系统进行可观测性分解，便可以分离出四类状态变量及四类子系统。当然，结构分解的过程也可以从系统的可观测性分解开始。下面着重介绍结构分解的方法，有关证明略去。

1) 系统按可控性的结构分解。设不可控系统的动态方程为

$$
\dot {\boldsymbol {x}} = \boldsymbol {A} \boldsymbol {x} + \boldsymbol {B} \boldsymbol {u}, \quad \boldsymbol {y} = \boldsymbol {C} \boldsymbol {x} \tag {9-192}
$$

式中， $\boldsymbol { x }$ 为 $n$ 维状态向量； $\pmb { u }$ 为 $p$ 维输入向量； $\boldsymbol { y }$ 为 $q$ 维输出向量； $\pmb { A }$ ， $\pmb { B }$ ， $c$ 为具有相应维数的矩阵。若系统可控性矩阵的秩为 $r ( r { < } n )$ ，则可从可控性矩阵中选出 $r$ 个线性无关的列向量 $s _ { 1 } , s _ { 2 } , \cdots , s _ { r }$ ，另外再任意选取尽可能简单的 $n { - } r$ 个 $n$ 维列向量 $s _ { r + 1 , } s _ { r + 2 , } \cdots , s _ { n , }$ ${ \pmb S } _ { n }$ 使它们与 $\{ s _ { 1 } , s _ { 2 } , \ \cdots , s _ { r } \}$ 线性无关，这样就可以构成 $n \times n$ 非奇异变换矩阵。

$$
\boldsymbol {P} ^ {- 1} = \left[ \begin{array}{c c c c c c c c} \boldsymbol {s} _ {1} & \boldsymbol {s} _ {2} & \dots & \boldsymbol {s} _ {r} & \vdots & \boldsymbol {s} _ {r + 1} & \dots & \boldsymbol {s} _ {n} \end{array} \right]
$$

对式(9-192)进行非奇异线性变换

$$
\boldsymbol {x} = \boldsymbol {P} ^ {- 1} \left[ \begin{array}{l} \boldsymbol {x} _ {c} \\ \boldsymbol {x} _ {\bar {c}} \end{array} \right] \tag {9-193}
$$

式(9-192)便变换为下列的规范形式：

$$
\left[ \begin{array}{l} \dot {\boldsymbol {x}} _ {c} \\ \dot {\boldsymbol {x}} _ {\bar {c}} \end{array} \right] = \boldsymbol {P A P} ^ {- 1} \left[ \begin{array}{l} \boldsymbol {x} _ {c} \\ \boldsymbol {x} _ {\bar {c}} \end{array} \right] + \boldsymbol {P B u}, \quad \boldsymbol {y} = \boldsymbol {C P} ^ {- 1} \left[ \begin{array}{l} \boldsymbol {x} _ {c} \\ \boldsymbol {x} _ {\bar {c}} \end{array} \right] \tag {9-194}
$$

式中， $\mathbf { x } _ { c }$ 为 $r$ 维可控状态子向量； $\mathbf { \delta } _ { \mathbf { x } _ { \overline { { c } } } } ( \mathbf { x } _ { \overline { { c } } }$ 为 $n { - } r$ 维不可控状态子向量，并且

$$
\begin{array}{r} \pmb {P} \pmb {A} \pmb {P} ^ {- 1} = \left[ \begin{array}{c c} {\overline {{{\pmb {A}}}} _ {1 1}} & {\overline {{{\pmb {A}}}} _ {1 2}} \\ {\overline {{{\bf 0}}} & {\overline {{{\pmb {A}}}} _ {2 2}} \end{array} \right] \frac {r \text {行}}{n - r \text {行}}, \qquad \pmb {P} \pmb {B} = \left[ \begin{array}{c} {\overline {{{\pmb {B}}}} _ {1}} \\ {\overline {{{\bf 0}}}} \end{array} \right] \frac {r \text {行}}{n - r \text {行}}} \\ {\pmb {r} \text {列} \qquad n - r \text {列} \qquad p \text {列}} \end{array}
$$

$$
\boldsymbol {C P} ^ {- 1} = \left[ \begin{array}{c c c} {\bar {C} _ {1}} & & {\bar {C} _ {2}} \\ {r \text {列}} & & {n - r \text {列}} \end{array} \right] q \text {行} \tag {9-195}
$$

展开式(9-194)，有

$$
\dot {\boldsymbol {x}} _ {c} = \bar {\boldsymbol {A}} _ {1 1} \boldsymbol {x} _ {c} + \bar {\boldsymbol {A}} _ {1 2} \boldsymbol {x} _ {\bar {c}} + \bar {\boldsymbol {B}} _ {1} \boldsymbol {u}
$$

$$
\dot {\boldsymbol {x}} _ {\bar {c}} = \overline {{\boldsymbol {A}}} _ {2 2} \boldsymbol {x} _ {\bar {c}}
$$

$$
\boldsymbol {y} = \bar {\boldsymbol {C}} _ {1} \boldsymbol {x} _ {c} + \bar {\boldsymbol {C}} _ {2} \boldsymbol {x} _ {\bar {c}}
$$

将输出向量进行分解，令 $y { = } y _ { 1 } { + } y _ { 2 }$ ，则可得子系统动态方程，其中可控子系统动态方程为

$$
\dot {\boldsymbol {x}} _ {c} = \bar {\boldsymbol {A}} _ {1 1} \boldsymbol {x} _ {c} + \bar {\boldsymbol {A}} _ {1 2} \boldsymbol {x} _ {\bar {c}} + \bar {\boldsymbol {B}} _ {1} \boldsymbol {u}, \quad \boldsymbol {y} _ {1} = \bar {\boldsymbol {C}} _ {1} \boldsymbol {x} _ {c} \tag {9-196}
$$

不可控子系统动态方程为

$$
\dot {\boldsymbol {x}} _ {\bar {c}} = \bar {A} _ {2 2} \boldsymbol {x} _ {\bar {c}}, \quad \boldsymbol {y} _ {2} = \bar {C} _ {2} \boldsymbol {x} _ {\bar {c}} \tag {9-197}
$$

上述系统结构分解方式称为可控性规范分解，系统方框图如图 9-21 所示。

系统结构的可控性规范分解具有下列特点：

$\textcircled{1}$ 不可控系统与其可控子系统具有相同的传递函数矩阵。

由于

![](images/d0d73776708c4a1b77b249edc590cd119342359b094e3101051725f1d8563d52.jpg)  
图 9-21 系统可控性规范分解方框图

$$
\begin{array}{l} \operatorname {r a n k} \left[ \begin{array}{l l l l} \boldsymbol {B} & \boldsymbol {A B} & \dots & \boldsymbol {A} ^ {n - 1} \boldsymbol {B} \end{array} \right] \\ = \operatorname {r a n k} \left[ \begin{array}{l l l l} \boldsymbol {P B} & (\boldsymbol {P A P} ^ {- 1}) (\boldsymbol {P B}) & \dots & (\boldsymbol {P A P} ^ {- 1}) ^ {n - 1} (\boldsymbol {P B}) \end{array} \right] \\ = \operatorname {r a n k} \left[ \begin{array}{c c c c} \bar {\boldsymbol {B}} _ {1} & \bar {\boldsymbol {A}} _ {1 1} \bar {\boldsymbol {B}} _ {1} & \dots & \bar {\boldsymbol {A}} _ {1 1} ^ {n - 1} \bar {\boldsymbol {B}} _ {1} \\ \mathbf {0} & \mathbf {0} & \dots & \mathbf {0} \end{array} \right] \tag {9-198} \\ = \operatorname {r a n k} \left[ \begin{array}{l l l l} \bar {B} _ {1} & \bar {A} _ {1 1} \bar {B} _ {1} & \dots & \bar {A} _ {1 1} ^ {n - 1} \bar {B} _ {1} \end{array} \right] \\ = r \\ \end{array}
$$

$$
\begin{array}{l} \boldsymbol {C} (s \boldsymbol {I} - \boldsymbol {A}) ^ {- 1} \boldsymbol {B} = (\boldsymbol {C P} ^ {- 1}) (\boldsymbol {s I} - \boldsymbol {P A P} ^ {- 1}) ^ {- 1} (\boldsymbol {P B}) \\ = \left[ \begin{array}{l l} \overline {{\boldsymbol {C}}} _ {1} & \overline {{\boldsymbol {C}}} _ {2} \end{array} \right] \left[ s \boldsymbol {I} - \left[ \begin{array}{c c} \overline {{\boldsymbol {A}}} _ {1 1} & \overline {{\boldsymbol {A}}} _ {1 2} \\ \boldsymbol {0} & \overline {{\boldsymbol {A}}} _ {2 2} \end{array} \right] \right] ^ {- 1} \left[ \begin{array}{l} \overline {{\boldsymbol {B}}} _ {1} \\ \boldsymbol {0} \end{array} \right] \\ = \left[ \begin{array}{l l} \bar {C} _ {1} & \bar {C} _ {2} \end{array} \right] \left[ \begin{array}{c c} s I - \bar {A} _ {1 1} & - \bar {A} _ {1 2} \\ \mathbf {0} & s I - \bar {A} _ {2 2} \end{array} \right] ^ {- 1} \left[ \begin{array}{l} \bar {B} _ {1} \\ \mathbf {0} \end{array} \right] \tag {9-199} \\ = \left[ \begin{array}{c c} \bar {C} _ {1} & \bar {C} _ {2} \end{array} \right] \left[ \begin{array}{c c} (s I - \bar {A} _ {1 1}) ^ {- 1} & (s I - \bar {A} _ {1 1}) ^ {- 1} \bar {A} _ {1 2} (s I - \bar {A} _ {2 2}) ^ {- 1} \\ \mathbf {0} & (s I - \bar {A} _ {2 2}) ^ {- 1} \end{array} \right] \left[ \begin{array}{c} \bar {B} _ {1} \\ \mathbf {0} \end{array} \right] \\ = \overline {{\boldsymbol {C}}} _ {1} (s \boldsymbol {I} - \overline {{\boldsymbol {A}}} _ {1 1}) ^ {- 1} \overline {{\boldsymbol {B}}} _ {1} \\ \end{array}
$$

因而 $r$ 维子系统( $\overline { { A } } _ { 1 1 } , \overline { { B } } _ { 1 } , \overline { { C } } _ { 1 }$ )是可控的，并且和系统(A，B，C )具有相同的传递函数矩阵。

如果从传递特性的角度分析系统 $( A , B , C )$ ，可以等价地用分析子系统( $\overline { { A } } _ { 1 1 } , \overline { { B } } _ { 1 } , \overline { { C } } _ { 1 }$ )来代替，由于后者维数降低了很多，可能会使分析变得简单。

$\textcircled{2}$ 不可控子系统的特性与整个系统的稳定性及输出响应有关。

输入 $\pmb { u }$ 只能通过可控子系统传递到输出，而与不可控子系统无关，故 $\pmb { u }$ 到 $\boldsymbol { y }$ 之间的传递函数矩阵描述不能反映不可控部分的特性。但是，不可控子系统对整个系统的影响是存在的，不可忽视。因而要求 $\overline { { A } } _ { 2 2 }$ 仅含稳定特征值，以保证整个系统稳定，并且应考虑到可控子系统的状态响应 ${ \bf x } _ { c } ( t )$ 和整个系统的输出响应 $y ( t )$ 均与不可控子系统的状态$\mathbf { x } _ { \overline { { c } } }$ 有关。

$\textcircled{3}$ 不可控系统的可控性规范分解是不唯一的。

由于选取非奇异变换阵 $\pmb { P } ^ { - 1 }$ 的列向量 s1, $\pmb { S } 2$ , …, $\pmb { s } _ { r }$ 及 $\mathbf { \delta } _ { \mathbf { \delta } _ { \mathbf { \delta } } \mathbf { \delta } _ { \mathbf { \delta } _ { \mathbf { \delta } _ { \mathbf { \delta } _ { \mathbf { \delta } _ { \mathbf { \delta } _ { \mathbf { \delta } _ { \mathbf { \delta } _ { \delta } \mathbf { \delta } _ { \delta _ { \delta } \delta _ { \delta } \delta _ { \delta } \delta _ { \delta } } } } } } } } } }$ , …, ${ \pmb S } _ { n }$ 的非唯一性，虽然系统可控性规范分解的形式不变，但诸系数阵不相同，故可控性规范分解不是唯一的。  
$\textcircled{4}$ 不可控系统的可控性规范分解将整个系统的特征值分解为可控因子与不可控因子两类。

由于

$$
\det (s I - \bar {A}) = \det (s I - \bar {A} _ {1 1}) \cdot \det (s I - \bar {A} _ {2 2}) \tag {9-200}
$$

故 $\boldsymbol { x } _ { c }$ 的稳定性完全由 $\overline { { A } } _ { 1 1 }$ 的特征值 $\lambda _ { 1 }$ , $\lambda _ { 2 }$ , …, $\lambda _ { r }$ 决定； $\pmb { x } _ { \mp }$ 的稳定性完全由 $\overline { { A } } _ { 2 2 }$ 的特征值$\lambda _ { r + 1 ; }$ $\lambda _ { n }$ 决定，而 $\lambda _ { 1 }$ $\lambda _ { 2 }$ $\lambda _ { n }$ 都是 $\pmb { A }$ 的特征值。 $\lambda _ { 1 }$ $\lambda _ { r }$ 称为系统 $( A , B , C )$ 的可控因子或可控振型， $\lambda _ { r + 1 } ,$ $\lambda _ { r + 1 } , \cdots , \lambda _ { n }$ $\lambda _ { n }$ 称为不可控因子或不可控振型。

例 9-20 已知系统 $( A , b , c )$ ，其中

$$
\boldsymbol {A} = \left[ \begin{array}{l l l} 1 & 2 & - 1 \\ 0 & 1 & 0 \\ 1 & - 4 & 3 \end{array} \right], \quad \boldsymbol {b} = \left[ \begin{array}{l} 0 \\ 0 \\ 1 \end{array} \right], \quad \boldsymbol {c} = \left[ \begin{array}{l l l} 1 & - 1 & 1 \end{array} \right]
$$

试按可控性分解为规范形式。

解 系统可控性矩阵为

$$
\boldsymbol {S} = \left[ \begin{array}{l l l} \boldsymbol {b} & \boldsymbol {A b} & \boldsymbol {A ^ {2} b} \end{array} \right] = \left[ \begin{array}{l l l} 0 & - 1 & - 4 \\ 0 & 0 & 0 \\ 1 & 3 & 8 \end{array} \right]
$$

$$
\operatorname {r a n k} S = 2 <   n = 3
$$

故系统不可控。从可控性矩阵中选出两个线性无关的列向量[0 0 1]T 和[1 0 3]T，附加任意列向量[0 1 0]T，构成非奇异变换阵

$$
\boldsymbol {P} ^ {- 1} = \left[ \begin{array}{c c c} 0 & - 1 & 0 \\ 0 & 0 & 1 \\ 1 & 3 & 0 \end{array} \right]
$$

计算矩阵 $P$ 和变换后的各矩阵

$$
\boldsymbol {P} = (\boldsymbol {P} ^ {- 1}) ^ {- 1} = \left[ \begin{array}{c c c} 3 & 0 & 1 \\ - 1 & 0 & 0 \\ 0 & 1 & 0 \end{array} \right]
$$

$$
\boldsymbol {P} \boldsymbol {A} \boldsymbol {P} ^ {- 1} = \left[ \begin{array}{c c c} 0 & - 4 & 2 \\ 1 & 4 & - 2 \\ \hline 0 & 0 & 1 \end{array} \right], \quad \boldsymbol {P} \boldsymbol {b} = \left[ \begin{array}{l} 1 \\ 0 \\ \vdots \\ 0 \end{array} \right], \quad \boldsymbol {c} \boldsymbol {P} ^ {- 1} = \left[ \begin{array}{c c c} 1 & 2 & - 1 \end{array} \right]
$$

可控子系统动态方程为

$$
\dot {\boldsymbol {x}} _ {c} = \left[ \begin{array}{l l} 0 & - 4 \\ 1 & 4 \end{array} \right] \boldsymbol {x} _ {c} + \left[ \begin{array}{l} 2 \\ - 2 \end{array} \right] \boldsymbol {x} _ {\bar {c}} + \left[ \begin{array}{l} 1 \\ 0 \end{array} \right] u, \quad y _ {1} = \left[ \begin{array}{l l} 1 & 2 \end{array} \right] \boldsymbol {x} _ {c}
$$

不可控子系统动态方程为

$$
\dot {x} _ {\overline {{c}}} = x _ {\overline {{c}}}, \quad y _ {2} = - x _ {\overline {{c}}}
$$

2) 系统按可观测性的结构分解。系统按可观测性结构分解的所有结论，都对偶于系统按可控性结构分解的结果。设不可观测系统的动态方程为

$$
\dot {\boldsymbol {x}} = \boldsymbol {A} \boldsymbol {x} + \boldsymbol {B} \boldsymbol {u}, \quad \boldsymbol {y} = \boldsymbol {C} \boldsymbol {x} \tag {9-201}
$$

式中， $x$ 为 $n$ 维状态向量； $\pmb { u }$ 为 $p$ 维输入向量； $\boldsymbol { y }$ 为 $q$ 维输出向量。系统的可观测性矩阵为

$$
\boldsymbol {V} = \left[ \begin{array}{c} \boldsymbol {C} \\ \boldsymbol {C A} \\ \vdots \\ \boldsymbol {C A} ^ {n - 1} \end{array} \right]
$$

rank $V { = } l ( l { < } n )$ ，在 $V$ 中任意选取 $l$ 个线性无关的行向量 $\mathbf { \Delta } t _ { 1 } , t _ { 2 } , \cdots , \mathbf { \Delta } t _ { l }$ ，此外再选取 $n { - } l$ 个与之线性无关的行向量 $t _ { l + 1 , } ~ \cdots , t _ { n }$ $t _ { l + 1 , }$ ，构成非奇异线性变换阵

$$
\boldsymbol {T} = \left[ \begin{array}{c} t _ {1} \\ \vdots \\ t _ {l} \\ \dots \\ t _ {l + 1} \\ \vdots \\ t _ {n} \end{array} \right] \tag {9-202}
$$

对式(9-201)不可观测系统进行非奇异线性变换

$$
\boldsymbol {x} = \boldsymbol {T} ^ {- 1} \left[ \begin{array}{l} \boldsymbol {x} _ {o} \\ \boldsymbol {x} _ {\bar {\sigma}} \end{array} \right] \tag {9-203}
$$

可得系统结构按可观测性分解的规范表达式

$$
\left[ \begin{array}{l} \dot {\boldsymbol {x}} _ {o} \\ \dot {\boldsymbol {x}} _ {\bar {\sigma}} \end{array} \right] = \boldsymbol {T A T} ^ {- 1} \left[ \begin{array}{l} \boldsymbol {x} _ {o} \\ \boldsymbol {x} _ {\bar {\sigma}} \end{array} \right] + \boldsymbol {T B u}, \quad \boldsymbol {y} = \boldsymbol {C T} ^ {- 1} \left[ \begin{array}{l} \boldsymbol {x} _ {o} \\ \boldsymbol {x} _ {\bar {\sigma}} \end{array} \right] \tag {9-204}
$$

式中， $ { \boldsymbol { { x } } } _ { o }$ 为 $l$ 维可观测状态子向量； $\mathbf { \boldsymbol { x } } _ { \bar { o } }$ 为 $n { - } l$ 维不可观测状态子向量，并且

$$
\begin{array}{r} {\pmb {T A T} ^ {- 1} = \left[ \begin{array}{c c} {\hat {\pmb {A}} _ {1 1}} & {0} \\ {\hline \hat {\pmb {A}} _ {2 1}} & {\hat {\pmb {A}} _ {2 2}} \end{array} \right]   \begin{array}{l} {l \text {行}} \\ {n - l \text {行}} \end{array} , \qquad \pmb {T B} = \left[ \begin{array}{c} {\hat {\pmb {B}} _ {1}} \\ {\hline \hat {\pmb {B}} _ {2}} \end{array} \right]   \begin{array}{l} {l \text {行}} \\ {n - l \text {行}} \end{array} } \\ {\qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad p \text {列}} \end{array}
$$

$$
\boldsymbol {C} \boldsymbol {T} ^ {- 1} = \left[ \begin{array}{c c c c} & \hat {\boldsymbol {C}} _ {1} & & 0 \end{array} \right] q \text {行} \tag {9-205}
$$

$$
l \text {列} \quad n - l \text {列}
$$

展开式(9-204)，有

$$
\dot {\boldsymbol {x}} _ {o} = \hat {\boldsymbol {A}} _ {1 1} \boldsymbol {x} _ {o} + \hat {\boldsymbol {B}} _ {1} \boldsymbol {u}
$$

$$
\dot {\boldsymbol {x}} _ {\bar {o}} = \hat {\boldsymbol {A}} _ {2 1} \boldsymbol {x} _ {o} + \hat {\boldsymbol {A}} _ {2 2} \boldsymbol {x} _ {\bar {o}} + \hat {\boldsymbol {B}} _ {2} \boldsymbol {u}
$$

$$
\boldsymbol {y} = \hat {\boldsymbol {C}} _ {1} \boldsymbol {x} _ {o}
$$

可观测子系统动态方程为

$$
\dot {\boldsymbol {x}} _ {o} = \hat {\boldsymbol {A}} _ {1 1} \boldsymbol {x} _ {o} + \hat {\boldsymbol {B}} _ {1} \boldsymbol {u}, \quad \boldsymbol {y} _ {1} = \hat {\boldsymbol {C}} _ {1} \boldsymbol {x} _ {o} = \boldsymbol {y} \tag {9-206}
$$

不可观测子系统动态方程为

$$
\dot {\boldsymbol {x}} _ {\bar {\sigma}} = \hat {\boldsymbol {A}} _ {2 1} \boldsymbol {x} _ {o} + \hat {\boldsymbol {A}} _ {2 2} \boldsymbol {x} _ {\bar {\sigma}} + \hat {\boldsymbol {B}} _ {2} \boldsymbol {u}, \quad \boldsymbol {y} _ {2} = \mathbf {0} \tag {9-207}
$$

系统可观测性规范分解方框图如图 9-22 所示。

![](images/cc21714714364d105d06b1f8cedca42241811be54ad0d7b89b89b2cb3b2e3091.jpg)  
图 9-22 系统可观测性规范分解方框图

设 ${ \hat { \pmb { A } } } = { \pmb { T } } { \pmb { A } } { \pmb { T } } ^ { - 1 } = [ { \hat { \underline { { A } } } } _ { 1 1 } \ { | \begin{array} { l } { \ { \ { \bf 0 } } } \\ { { \hat { \pmb { A } } } _ { 2 1 } } \end{array} | } , \ { \hat { \pmb { B } } } = { \pmb { T } } { \pmb { B } } = [ { \hat { \underline { { B } } } } _ { 1 }  ]$

$$
\hat {\boldsymbol {C}} = \boldsymbol {C} \boldsymbol {T} ^ {- 1} = \left[ \begin{array}{c c} \hat {\boldsymbol {C}} _ {1} & \mathbf {0} \end{array} \right]
$$

与可控性规范分解相类似，称系统( $\hat { A } , \hat { B } , \hat { C }$ )为系统 $( A , B , C )$ 的可观测规范分解。可观测性规范分解也有与可控性规范分解相类似的分析与结论。

例 9-21 试将例 9-19 所示系统按可观测性进行分解。

解 系统的可观测性矩阵为

$$
\boldsymbol {V} = \left[ \begin{array}{l} \boldsymbol {c} \\ \boldsymbol {c A} \\ \boldsymbol {c A ^ {2}} \end{array} \right] = \left[ \begin{array}{l l l} 1 & - 1 & 1 \\ 2 & - 3 & 2 \\ 4 & - 7 & 4 \end{array} \right]
$$

$$
\operatorname {r a n k} V = 2 <   n = 3
$$

故系统不可观测。从可观测性矩阵中选取两个线性无关行向量[1 1 1]和[2 3 2]，再选取一个与之线性无关的行向量[0 0 1]，构成非奇异变换矩阵

$$
\boldsymbol {T} = \left[ \begin{array}{c c c} 1 & - 1 & 1 \\ 2 & - 3 & 2 \\ 0 & 0 & 1 \end{array} \right]
$$

计算变换后各矩阵

$$
\boldsymbol {T} ^ {- 1} = \left[ \begin{array}{c c c} 3 & - 1 & - 1 \\ 2 & - 1 & 0 \\ 0 & 0 & 1 \end{array} \right], \quad \boldsymbol {T A T} ^ {- 1} = \left[ \begin{array}{c c c} 0 & 1 & 0 \\ - 2 & 3 & 0 \\ - 5 & 3 & 2 \end{array} \right]
$$

$$
\boldsymbol {T} \boldsymbol {b} = \left[ \begin{array}{l} 1 \\ 2 \\ \vdots \\ 1 \end{array} \right], \quad \boldsymbol {c} \boldsymbol {T} ^ {- 1} = \left[ \begin{array}{l l l} 1 & 0 & 0 \end{array} \right]
$$

可观测子系统动态方程为

$$
\dot {\boldsymbol {x}} _ {o} = \left[ \begin{array}{l l} 0 & 1 \\ - 2 & 3 \end{array} \right] \boldsymbol {x} _ {o} + \left[ \begin{array}{l} 1 \\ 2 \end{array} \right] u, \quad y _ {1} = \left[ \begin{array}{l l} 1 & 0 \end{array} \right] \boldsymbol {x} _ {o} = y
$$

不可观测子系统动态方程为

$$
\dot {x} _ {\bar {o}} = \left[ \begin{array}{l l} - 5 & 3 \end{array} \right] x _ {o} + 2 x _ {\bar {o}} + u, \quad y _ {2} = 0
$$

# 9-3 李雅普诺夫稳定性分析

稳定性是系统的重要特性，是系统正常工作的必要条件，它描述初始条件下系统方程的解是否具有收敛性，而与输入作用无关。1892年俄国学者李雅普诺夫提出的稳定性理论是确定系统稳定性的更一般性理论，它采用了状态向量描述，不仅适用于单变量、线性、定常系统，而且适用于多变量、非线性、时变系统。在分析一些特定的非线性系统的稳定性时，李雅普诺夫理论有效地解决了用其他方法所不能解决的问题。李雅普诺夫理论在建立一系列关于稳定性概念的基础上，提出了判断系统稳定性的两种方法：一种方法是利用线性系统微分方程的解来判断系统稳定性，称之为李雅普诺夫第一法或间接法；另一种方法是首先利用经验和技巧来构造李雅普诺夫函数，进而利用李雅普诺夫函数来判断系统稳定性，称之为李雅普诺夫第二法或直接法。由于间接法需要解线性系统微分方程，求解系统微分方程往往并非易事，所以间接法的应用受到了很大限制。而直接法不需要解系统微分方程，给判断系统的稳定性带来极大方便，获得了广泛应用。

![](images/224334c9843b5f00707064e26b2b99414eb6bd7655aaa724157d2e7ceb6f94cc.jpg)  
李雅普诺夫

# 1. 李雅普诺夫意义下的稳定性

设系统方程为

$$
\dot {\boldsymbol {x}} = \boldsymbol {f} (\boldsymbol {x}, t) \tag {9-208}
$$

式中， $\boldsymbol { x }$ 为 $n$ 维状态向量，且显含时间变量 $t$ ； $\mathbf { \Psi } _ { f ( x , t ) }$ 为线性或非线性、定常或时变的 $n$ 维向量函数，其展开式为

$$
\dot {x} _ {i} = f _ {i} \left(x _ {1}, x _ {2}, \dots , x _ {n}, t\right); \quad i = 1, 2, \dots , n \tag {9-209}
$$

假定方程的解为 $\pmb { x } ( t ; \pmb { x } _ { 0 } , t _ { 0 } )$ ，式中 $\mathbf { \delta x } _ { 0 }$ 和 $t _ { 0 }$ 分别为初始状态向量和初始时刻，则初始条件 $\mathbf { \delta x } _ { 0 }$ 必满足 0 0 0 0x x x ( ; , ) t t  。 ${ \pmb x } ( t _ { 0 } ; { \pmb x } _ { 0 } , t _ { 0 } ) = { \pmb x } _ { 0 }$

# (1) 平衡状态

李雅普诺夫关于稳定性的研究均针对平衡状态而言。对于所有 t，满足

$$
\dot {\boldsymbol {x}} _ {e} = \boldsymbol {f} \left(\boldsymbol {x} _ {e}, t\right) = \mathbf {0} \tag {9-210}
$$

的状态 $ { \boldsymbol { { x } } } _ { e }$ 称为平衡状态。平衡状态的各分量相对于时间不再发生变化。若已知状态方程，令 $\dot { \mathbf { x } } = \mathbf { 0 }$ 所求得的解 $x$ ，便是一种平衡状态。

线性定常系统 ${ \dot { \mathbf { x } } } = A { \mathbf { x } }$ ，其平衡状态满足 $A \pmb { x } _ { e } = \pmb { 0 }$ ，当 $\pmb { A }$ 为非奇异矩阵时，系统只有唯一的零解，即只存在一个位于状态空间原点的平衡状态。若 $\pmb { A }$ 为奇异矩阵，则系统存在有无穷多个平衡状态。对于非线性系统，可能有一个或多个平衡状态。

# (2) 李雅普诺夫意义下的稳定性

设系统初始状态位于以平衡状态 $ { \boldsymbol { { x } } } _ { e }$ 为球心、 $\delta$ 为半径的闭球域 $S ( \delta )$ 内，即

$$
\left\| \boldsymbol {x} _ {0} - \boldsymbol {x} _ {e} \right\| \leqslant \delta , \quad t = t _ {0} \tag {9-211}
$$

若能使系统方程的解 $\pmb { x } ( t ; \pmb { x } _ { 0 } , t _ { 0 } )$ 在 $t \to \infty$ 的过程中，都位于以 $ { \boldsymbol { { x } } } _ { e }$ 为球心、任意规定的半径为 $\varepsilon$ 的闭球域 $S ( \varepsilon )$ 内，即

$$
\left\| \boldsymbol {x} \left(t; \boldsymbol {x} _ {0}, t _ {0}\right) - \boldsymbol {x} _ {0} \right\| \leqslant \varepsilon , \quad t \geqslant t _ {0} \tag {9-212}
$$

则称系统的平衡状态 $ { \boldsymbol { { x } } } _ { e }$ 在李雅普诺夫意义下是稳定的。该定义的平面几何表示如图 9-23(a)所示。式中 $\lVert \cdot \rVert$ 为欧几里得范数，其几何意义是空间距离的尺度。例如 $\left\| { \pmb x } _ { 0 } - { \pmb x } _ { e } \right\|$ 表示状态空间中 $\mathbf { \delta x } _ { 0 }$ 点至 $ { \boldsymbol { { x } } } _ { e }$ 点之间距离的尺度，其数学表达式为

$$
\left\| \boldsymbol {x} _ {0} - \boldsymbol {x} _ {e} \right\| = \left[ \left(x _ {1 0} - x _ {1 e}\right) ^ {2} + \dots + \left(x _ {n 0} - x _ {n e}\right) ^ {2} \right] ^ {\frac {1}{2}} \tag {9-213}
$$

实数 $\delta$ 与 $\varepsilon$ 有关，通常也与 $t _ { 0 }$ 有关。如果 $\delta$ 与 $t _ { 0 }$ 无关，则称平衡状态是一致稳定的。

![](images/672c4abc0adfc83c1578f2075927469557cd0062e6b9ed734836265ddb5969f4.jpg)  
(a)李雅普诺夫意义下的稳定性

![](images/af9a96815369039fdd367ec46eeecdddd67241264841a1dc3b6c2109ce146cc0.jpg)  
(b)渐近稳定性

![](images/e77efa04385563099be422139d9e6ec89aed3190165fd03f4c443bc272f17c8e.jpg)  
(c)不稳定性  
图 9-23 有关稳定性的平面几何表示

应当注意，按李雅普诺夫意义下的稳定性定义，当系统作不衰减的振荡运动时，将在平面描绘出一条封闭曲线，但只要不超出 $S ( \varepsilon )$ ，则认为是稳定的，这与经典控制理论中线性定常系统稳定性的定义是有差异的。经典控制理论中的稳定性，指的是渐近稳定性。

# (3) 渐近稳定性

若系统的平衡状态 $ { \boldsymbol { { x } } } _ { e }$ 不仅具有李雅普诺夫意义下的稳定性，且有

$$
\lim  _ {t \rightarrow \infty} \| \boldsymbol {x} (t; \boldsymbol {x} _ {0}, t _ {0}) - \boldsymbol {x} _ {e} \| = 0 \tag {9-214}
$$

则称此平衡状态是渐近稳定的。这时，从 $S ( \delta )$ 出发的轨迹不仅不会超出 $S ( \varepsilon )$ ，且当 $t \to \infty$ 时收敛于 $ { \boldsymbol { { x } } } _ { e }$ ，其平面几何表示如图 9-23(b)所示。显见经典控制理论中的稳定性定义与此处的渐近稳定性对应。

若 $\delta$ 与 $t _ { 0 }$ 无关，且式(9-214)的极限过程与 $t _ { 0 }$ 无关，则称平衡状态是一致渐近稳定的。

# (4) 大范围(全局)渐近稳定性

当初始条件扩展至整个状态空间，且平衡状态均具有渐近稳定性时，称此平衡状态是大范围渐近稳定的。此时 $\delta \to \infty$ ， $S ( \delta ) \to \infty$ 。当 $t \to \infty$ 时，由状态空间中任一点出发的轨迹都收敛至 x 。 $\pmb { x } _ { e }$

对于严格线性的系统，如果它是渐近稳定的，则必定是大范围渐近稳定的，这是因为线性系统的稳定性与初始条件的大小无关。而对于非线性系统来说，其稳定性往往与初始条件的大小密切相关，系统渐近稳定不一定是大范围渐近稳定。

# (5) 不稳定性

如果对于某个实数 $\varepsilon > 0$ 和任一个实数 $\delta > 0$ ，不管这两个实数有多么小，在 $S ( \delta )$ 内总存在着一个状态 $\mathbf { \delta x } _ { 0 }$ ，使得由这一状态出发的轨迹超出 $S ( \varepsilon )$ ，则平衡状态 $ { \boldsymbol { { x } } } _ { e }$ 称为是不稳定的，如图 9-23(c)所示。

下面介绍李雅普诺夫理论中判断系统稳定性的方法。

# 2. 李雅普诺夫第一法(间接法)

李雅普诺夫第一法是利用状态方程解的特性来判断系统稳定性的方法，它适用于线性定常、线性时变以及非线性函数可线性化的情况。由于本章主要研究线性定常系统，所以在此仅介绍线性定常系统的特征值判据。

定理 9-1 对于线性定常系统 $\dot { \mathbf { x } } = A \mathbf { x } , x ( 0 ) = x _ { 0 } , t \geqslant 0$ ，有

1) 系统的每一平衡状态是在李雅普诺夫意义下稳定的充分必要条件是， $\pmb { A }$ 的所有特征值均具有非正(负或零)实部，且具有零实部的特征值为 $\pmb { A }$ 的最小多项式的单根。  
2) 系统的唯一平衡状态 $\pmb { x } _ { e } = \pmb { 0 }$ 是渐近稳定的充分必要条件是， $\pmb { A }$ 的所有特征值均具有负实部。

证明 1) 设 $\pmb { x } _ { e }$ 为 ${ \dot { \mathbf { x } } } = A { \mathbf { x } }$ 的平衡状态，则由性质 $\dot { \pmb x } _ { e } = { \pmb 0 }$ 和 $\mathbf { \nabla } A \mathbf { x } _ { e } = \mathbf { 0 }$ 可知，对于所有$t \geqslant 0$ 均有

$$
\boldsymbol {x} _ {e} = \mathrm {e} ^ {A t} \boldsymbol {x} _ {e} \tag {9-215}
$$

于是，考虑到 $\boldsymbol { x } ( t ; x _ { 0 } , 0 ) = \mathrm { e } ^ { \boldsymbol { A } t } \boldsymbol { x } _ { 0 }$ ，有

$$
\boldsymbol {x} (t; \boldsymbol {x} _ {0}, 0) - \boldsymbol {x} _ {e} = \mathrm {e} ^ {\mathcal {A} t} \left(\boldsymbol {x} _ {0} - \boldsymbol {x} _ {e}\right), \quad \forall t \geqslant 0 \tag {9-216}
$$

这表明，当且仅当 $\left\| \mathbf { e } ^ { \boldsymbol { A } t } \right\| \leqslant k < \infty$ 时，对任意给的一个实数 $\varepsilon > 0$ ，都对应存在和初始时刻无关的一个实数 $\delta ( \varepsilon ) = \varepsilon / k$ ，使得由满足不等式

$$
\left\| \boldsymbol {x} _ {0} - \boldsymbol {x} _ {e} \right\| \leqslant \delta (\varepsilon) \tag {9-217}
$$

的任一初态 $\mathbf { \delta x } _ { 0 }$ 出发的受扰运动都满足不等式

$$
\left\| \boldsymbol {x} (t; \boldsymbol {x} _ {0}, 0) - \boldsymbol {x} _ {e} \right\| \leqslant \left\| \mathrm {e} ^ {A t} \right\| \cdot \left\| \boldsymbol {x} _ {0} - \boldsymbol {x} _ {e} \right\| \leqslant k \cdot \frac {\varepsilon}{k}, \quad \forall t \geqslant 0 \tag {9-218}
$$

从而由定义知，系统的每一个平衡状态均为李雅普诺夫意义下稳定。再引入非奇异变换阵 $P$ ，使得 $\hat { \pmb { A } } = \pmb { P } ^ { - 1 } \pmb { A } \pmb { P }$ 为矩阵 $\pmb { A }$ 的约当规范型，则又有

$$
\left\| \mathrm {e} ^ {\hat {A} t} \right\| \leqslant \left\| \boldsymbol {P} ^ {- 1} \right\| \cdot \left\| \mathrm {e} ^ {A t} \right\| \cdot \| \boldsymbol {P} \| \tag {9-219}
$$

因而 $\left\| \mathbf { e } ^ { \boldsymbol { A } t } \right\|$ 有界等价于 $\left\| \mathbf { e } ^ { \hat { A } t } \right\|$ 有界。但是，由 $\hat { \pmb { A } }$ 为约当规范型可知 $\mathrm { e } ^ { \hat { \boldsymbol { A } } t }$ 每一元的形式为

$$
t ^ {\beta_ {i}} \mathrm {e} ^ {\mathrm {a} _ {i} t + \mathrm {j} \omega_ {i} t}, \quad \alpha_ {i} + \mathrm {j} \omega_ {i} = \lambda_ {i} (\hat {\boldsymbol {A}}) = \lambda_ {i} (\boldsymbol {A}) \tag {9-220}
$$

式中， $\lambda _ { i } ( \cdot )$ 为( ) 的特征值； $\beta _ { i }$ 为特征值的重数。注意到式(9-220)中，当 $\alpha _ { i } < 0$ 时对任何正整数 $\beta _ { i }$ ，此元在 $[ 0 , \infty )$ 上为有界，而 $\alpha _ { i } = 0$ 时只对 $\beta _ { i } = 0$ ，此元在 $[ 0 , \infty )$ 上为有界。同时， $\mathrm { e } ^ { \boldsymbol { A } t }$ 的每一个元有界意味着 $\left\| \mathbf { e } ^ { \hat { \boldsymbol { A } } t } \right\|$ 有界。由此可知，当且仅当 $\pmb { A }$ 的所有特征值均具有负或零实部，且具有零实部的特征值为单根时， $\left\| \mathrm { e } ^ { \hat { \boldsymbol { A } } t } \right\|$ 为有界，也就是系统的每一个平衡状态为李雅普诺夫意义下的稳定。结论 1)证毕。

2) 由式(9-216)可知，当且仅当 $\left\| \mathbf { e } ^ { \boldsymbol { A } t } \right\|$ 对一切 $t \geqslant 0$ 为有界，且当 $t \to 0$ 时 $\left\| \mathbf { e } ^ { \boldsymbol { A } t } \right\| \to 0$ ，零平衡状态 $\mathbf { \boldsymbol { x } } _ { e } = \mathbf { \boldsymbol { 0 } }$ 为渐近稳定。如上所证，当且仅当 $\pmb { A }$ 的所有特征值均具有负或零实部时，$\left\| \mathbf { e } ^ { \hat { \boldsymbol { A } } t } \right\|$ 有界。又根据式(9-219)和式(9-220)可知，当且仅当 $t \to \infty$ 时 $t ^ { \beta _ { i } } \mathbf { e } ^ { \alpha _ { i } + \mathrm { j } \omega _ { i } t }  0$ ，可保证$t \to 0$ 时 $\left\| \mathbf { e } ^ { \boldsymbol { A } t } \right\| \to 0$ ，这等价于 $\pmb { A }$ 的特征值均具有负实部。结论2)证毕。

由于所讨论的系统为线性定常系统，当其为稳定时必是一致稳定，当其为渐定稳定时必是大范围一致渐近稳定。

# 3. 李雅普诺夫第二法(直接法)

根据古典力学中的振动现象，若系统能量(含动能与位能)随时间推移而衰减，系统迟早会达到平衡状态，但要找到实际系统的能量函数表达式并非易事。李雅普诺夫提出，可虚构一个能量函数，后来便被称为李雅普诺夫函数，一般它与 $x _ { 1 }$ ， $x _ { 2 }$ ，…， $x _ { n }$ 及 $t$ 有关，记以 $V ( { \boldsymbol { x } } , t )$ 。若不显含 $t$ ，则记以 $V ( x )$ 。它是一个标量函数，考虑到能量总大于零，故为正定函数。能量衰减特性用 $\dot { V } ( { \boldsymbol x } , t )$ 或 $\dot { V } ( \pmb { x } )$ 表示。李雅普诺夫第二法利用 $V$ 及 $\dot { V }$ 的符号特征，直接对平衡状态稳定性作出判断，无须求出系统状态方程的解，故称直接法。用此方法解决了一些用其他稳定性判据难以解决的非线性系统的稳定性问题，遗憾的是对一般非线性系统仍未找到构造李雅普诺夫函数的通用方法。对于线性系统，通常用二次型函数 $\boldsymbol { x } ^ { \mathrm { { r } } } \boldsymbol { P } \boldsymbol { x }$ 作为李雅普诺夫函数。

这里不打算对李雅普诺夫第二法中的诸稳定性定理在数学上作严格证明，而只着重于物理概念的阐述和应用。

# (1) 标量函数定号性的简要回顾

正定性 标量函数 $V ( x )$ 对所有在域 $S$ 中的非零状态 $\boldsymbol { x }$ 有 $V ( x ) > 0$ 且 $V ( \mathbf { 0 } ) { = } 0$ ，则在域 S(域 $S$ 包含状态空间的原点)内的标量函数 $V ( x )$ 称为是正定的。

负定性 如果 $- V ( x )$ 是正定函数，则标量函数 $V ( x )$ 称为负定函数。

正半定性 如果标量函数 $V ( x )$ 除了原点及某些状态处等于零外，在域 $S$ 内的所有状态都是正定的，则 $V ( x )$ 称为正半定函数。

负半定性 如果 $- V ( x )$ 是正半定函数，则标量函数 $V ( x )$ 称为负半定函数。

不定性 如果在域 $S$ 内，不论域 S 多么小， $V ( x )$ 既可为正值也可为负值，则标量函数 $V ( x )$ 称为不定函数。

(2) 李雅普诺夫第二法主要定理

定理 9-2(定常系统大范围渐近稳定判别定理 1) 对于定常系统

$$
\dot {\boldsymbol {x}} = \boldsymbol {f} (\boldsymbol {x}), \quad t \geqslant 0 \tag {9-221}
$$

其中 $\begin{array} { r } { f ( \mathbf { 0 } ) = \mathbf { 0 } } \end{array}$ ，如果存在一个具有连续一阶导数的标量函数 $V ( x )$ ， $V ( \mathbf { 0 } ) { = } 0$ ，并且对于状态空间 $X$ 中的一切非零点 $x$ 满足如下条件：

1) $V ( x )$ 为正定；  
2) $\dot { V } ( { \pmb x } )$ 为负定；  
3) 当 $\left\| { \boldsymbol { x } } \right\| \to \infty$ 时 $V ( { \pmb x } )  \infty$ 。

则系统的原点平衡状态是大范围渐近稳定的。

例 9-22 设系统状态方程为

$$
\dot {x} _ {1} = x _ {2} - x _ {1} \left(x _ {1} ^ {2} + x _ {2} ^ {2}\right)
$$

$$
\dot {x} _ {2} = - x _ {1} - x _ {2} \left(x _ {1} ^ {2} + x _ {2} ^ {2}\right)
$$

试确定系统的稳定性。

解 显然，原点 $\scriptstyle ( x _ { 1 } = 0$ ， $x _ { 2 } { = } 0$ )是该系统唯一的平衡状态。选取正定标量函数 $V ( x )$ 为

$$
V (\boldsymbol {x}) = x _ {1} ^ {2} + x _ {2} ^ {2}
$$

则沿任意轨迹 $V ( x )$ 对时间的导数

$$
\dot {V} (\boldsymbol {x}) = 2 x _ {1} \dot {x} _ {1} + 2 x _ {2} \dot {x} _ {2} = - 2 \left(x _ {1} ^ {2} + x _ {2} ^ {2}\right) ^ {2}
$$

是负定的。这说明 $V ( x )$ 沿任意轨迹是连续减小的，因此 $V ( \pmb { x } )$ 是一个李雅普诺夫函数。由于当 $\| { \boldsymbol { \mathbf { \mathit { x } } } } \| \to \infty$ 时 $V ( { \pmb x } )  \infty$ ，所以系统在原点处的平衡状态是大范围渐近稳定的。

一般地说，对于相当一部分系统，要构造一个李雅普诺夫函数 $V ( \pmb { x } )$ 使其满足定理 9-2 中所要求的 $\dot { V } ( \pmb { x } )$ 为负定这一条件，常常不易做到。同时，从直观上也容易理解，要求 $\dot { V } ( \pmb { x } )$ 为负定不免过于保守。下面给出将这一条件放宽后的定常系统大范围渐近稳定判别定理。

定理 9-3(定常系统大范围渐近稳定判别定理 2) 对于定常系统(9-221)，如果存在一个具有连续一阶导数的标量 $V ( x )$ ， $V ( \mathbf { 0 } ) { = } 0$ ，并且对状态空间 $X$ 中的一切非零点 $\boldsymbol { x }$ 满足如下的条件：

1) $V ( x )$ 为正定；  
2) $\dot { V } ( \pmb { x } )$ 为负半定；  
3) 对任意 $\pmb { x } \in X , \dot { V } ( \pmb { x } ( t ; \pmb { x } _ { 0 } , 0 ) ) \not \equiv 0$   
4) 当 $\left\| { \boldsymbol { \mathbf { \mathit { x } } } } \right\| \to \infty$ 时 $V ( { \pmb x } )  \infty$ 。

则系统的原点平衡状态是大范围渐近稳定的。

例 9-23 已知定常系统状态方程为

$$
\dot {x} _ {1} = x _ {2}
$$

$$
\dot {x} _ {2} = - x _ {1} - \left(1 + x _ {2}\right) ^ {2} x _ {2}
$$

试确定系统的稳定性。

解 易知原点 $( x _ { 1 } = 0$ ， $x _ { 2 } { = } 0 )$ 为系统唯一的平衡状态。现取 $V ( \pmb { x } ) { = } \pmb { x } _ { 1 } ^ { 2 } + \pmb { x } _ { 2 } ^ { 2 }$ ，且有

1) $V ( \pmb { x } ) { = } x _ { 1 } ^ { 2 } + x _ { 2 } ^ { 2 }$ 为正定。  
2) $\dot { V } ( x ) = 2 x _ { 1 } \dot { x } _ { 1 } + 2 x _ { 2 } \dot { x } _ { 2 } = - 2 x _ { 2 } ^ { 2 } ( 1 + x _ { 2 } ) ^ { 2 }$ 。容易看出，除了 $\textcircled{1} x _ { 1 }$ 任意， $x _ { 2 } { = } 0$ ； $\textcircled{2} x _ { 1 }$ 任意，$x _ { 2 } { = } - 1$ 时， $\dot { V } ( \pmb { x } ) = 0$ 以外，均有 $\dot { V } ( \pmb { x } ) < 0$ 。所以， $\dot { V } ( \pmb { x } )$ 为负半定。  
3) 检查是否 $\dot { V } ( \boldsymbol { x } ( t ; \boldsymbol { x } _ { 0 } , 0 ) ) \not \equiv 0 .$ 。考虑到使得 $\dot { V } ( \pmb { x } ) = 0$ 的可能性只有上述 $\textcircled{1}$ 和 $\textcircled{2}$ 两种情况，所以问题归结为判断这两种情况是否为系统的受扰运动解。先考察情况 $\textcircled{1}$ ：设$\overline { { \boldsymbol { x } } } ( t ; \boldsymbol { x } _ { 0 } , 0 ) = \left[ \boldsymbol { x } _ { 1 } ( t ) \quad 0 \right] ^ { \mathrm { T } }$ ，则由 $x _ { 2 } ( t ) { \equiv } 0$ 可导出 $\dot { x } _ { 2 } ( t ) = 0$ ，将此代入系统状态方程可得

$$
\begin{array}{l} \dot {x} _ {1} (t) = x _ {2} (t) = 0 \\ 0 = \dot {x} _ {2} (t) = - (1 + x _ {2} (t)) ^ {2} x _ {2} (t) - x _ {1} (t) = - x _ {1} (t) \\ \end{array}
$$

这表明，除了点 $( x _ { 1 } = 0$ ， $x _ { 2 } { = } 0$ )外， $\overline { { \boldsymbol { x } } } ( t ; \boldsymbol { x } _ { 0 } , 0 ) = \left[ \boldsymbol { x } _ { 1 } ( t ) \quad 0 \right] ^ { \mathrm { T } }$ 不是系统的受扰运动解。再考察情况 $\textcircled{2}$ ：设 $\overline { { \boldsymbol { x } } } ( t ; \boldsymbol { x } _ { 0 } , 0 ) = \left[ \boldsymbol { x } _ { 1 } ( t ) \right. \left. - 1 \right] ^ { \mathrm { T } }$ ，则由 $x _ { 2 } ( t ) = - 1$ 可导出 $\dot { x } _ { 2 } ( t ) = 0$ ，将此代入系统状态方程可得

$$
\begin{array}{l} \dot {x} _ {1} (t) = x _ {2} (t) = - 1 \\ 0 = \dot {x} _ {2} (t) = - (1 + x _ {2} (t)) ^ {2} x _ {2} (t) - x _ {1} (t) = - x _ {1} (t) \\ \end{array}
$$

显然这是一个矛盾的结果，表明 $\overline { { \boldsymbol { x } } } ( t ; \boldsymbol { x } _ { 0 } , 0 ) = \left[ \boldsymbol { x } _ { 1 } ( t ) \right. \left. - 1 \right] ^ { \mathrm { T } }$ 也不是系统的受扰运动解。综合以上分析可知， $\dot { V } ( \pmb { x } ( t ; \pmb { x } _ { 0 } , 0 ) ) \not \equiv 0 ,$ 。

4) 当 $\| { \pmb x } \|  \infty$ 时，显然有 $V ( { \pmb x } ) = \| { \pmb x } \| ^ { 2 }  \infty$ 。

于是，根据定理 9-3 可判定系统的原点平衡状态是大范围渐近稳定的。

由于上述给出的所有判别定理都只提供了充分条件，如果经多次试取李雅普诺夫函数都得不到确定的答案时，就要考虑其为不稳定的可能性。下面的定理给出了判别不稳定的充分条件。

定理 9-4(不稳定判别定理) 对于定常系统(9-221)，如果存在一个具有连续一阶导数的标量函数 $V ( x )$ （其中 $V ( \mathbf { 0 } ) { = } 0$ ），和围绕原点的域 $\varOmega$ ，使得对于一切 $\boldsymbol { x } \in \varOmega$ 和一切 $t \geqslant t _ { 0 }$ 满足如下条件：

1) $V ( x )$ 为正定；  
2) $\dot { V } ( \pmb { x } )$ 为正定。

则系统平衡状态为不稳定。

# 4. 线性定常系统的李雅普诺夫稳定性分析

下面介绍李雅普诺夫第二法在线性定常系统稳定性分析中的应用。

(1) 线性定常连续系统渐近稳定性的判别

设线性定常系统状态方程为 $\dot { \mathbf { x } } = A \mathbf { x } , x ( 0 ) = x _ { 0 } , t \geqslant 0$ ， $\pmb { A }$ 为非奇异矩阵，故原点是唯一平衡状态。设取正定二次型函数 $V ( x ) = { \bf { x } } ^ { \mathrm { { T } } } P { \bf { x } }$ 作为可能的李雅普诺夫函数，考虑到系统状态方程，则有

$$
\dot {V} (\boldsymbol {x}) = \dot {\boldsymbol {x}} ^ {\mathrm {T}} \boldsymbol {P} \boldsymbol {x} + \boldsymbol {x} ^ {\mathrm {T}} \boldsymbol {P} \dot {\boldsymbol {x}} = \boldsymbol {x} ^ {\mathrm {T}} \left(\boldsymbol {A} ^ {\mathrm {T}} \boldsymbol {P} + \boldsymbol {P} \boldsymbol {A}\right) \boldsymbol {x} \tag {9-222}
$$

令 $\pmb { A } ^ { \mathrm { T } } \pmb { P } + \pmb { P } \pmb { A } = - \pmb { Q }$ (9-223)

于是有

$$
\dot {V} (\boldsymbol {x}) = - \boldsymbol {x} ^ {\mathrm {T}} \boldsymbol {Q} \boldsymbol {x} \tag {9-224}
$$

根据定常系统大范围渐近稳定判别定理 1，只要 $\mathcal { Q }$ 正定(即 $\dot { V } ( \pmb { x } )$ 负定)，则系统是大范围渐近稳定的。于是线性定常连续系统渐近稳定的充分必要条件可表示为：给定一正定矩阵 $P$ ，存在着满足式(9-223)的正定矩阵 $\pmb { Q }$ ，而 $\boldsymbol { x } ^ { \mathrm { { T } } } \boldsymbol { P } \boldsymbol { x }$ 是该系统的一个李雅普诺夫函数，式(9-223)称为李雅普诺夫矩阵代数方程。

但是，按上述先给定 $P$ 、再验证 $\varrho$ 是否正定的步骤去分析系统稳定性时，若 $P$ 选取不当，往往会导致 $\varrho$ 非正定，需反复多次选取 $P$ 阵来检验 $\pmb { Q }$ 是否正定，使用中很不方便。因而在应用时，往往是先选取 $\varrho$ 为正定实对称矩阵，再求解式(9-223)，若所求得的 $P$ 阵为正定实对称矩阵，则可判定系统是渐近稳定的。由于使用中常选取 $\pmb { Q }$ 阵为单位阵或对角线阵，比起先选 $P$ 阵再检验 $\pmb { Q }$ 阵要方便得多，所以在判定系统的稳定性时常利用下述定理：

定理 9-5 线性定常系统 $\dot { { \mathbf { x } } } { = } { \mathbf { } } A { \mathbf { } } x { , } x ( 0 ) = x _ { 0 } , t \geqslant 0$ 的原点平衡状态 $\pmb { x } _ { \mathrm { e } } = \pmb { 0 }$ 为渐近稳定的充分必要条件是，对于任意给定的一个正定对称矩阵 $\pmb { Q }$ ，有唯一的正定对称矩阵 $P$ 使式(9-223)成立。

需要说明的是，在利用上述定理判断线性定常系统的渐近稳定性时，对 $\varrho$ 的唯一限制是其应为对称正定阵。显然，满足这种限制的 $\pmb { Q }$ 阵可能有无穷多个，但判断的结果即系统是否为渐近稳定，则和 $\pmb { Q }$ 阵的不同选择无关。上述定理的实质是给出了矩阵 $\pmb { A }$ 的所有特征值均具有负实部的充分必要条件。

根据定常系统大范围渐近稳定判别定理 2 可以推知，若系统任意的状态轨迹在非零状态不存在 $\dot { V } ( \pmb { x } )$ 恒为零时， $\pmb { Q }$ 阵可选择为正半定的，即允许 $\varrho$ 取半正定对角阵时主对角线上部分元素为零，而解得的 $P$ 阵仍应正定。

由于利用上述定理判断线性定常系统是否渐近稳定时需要求解李雅普诺夫方程(9-223)，但一般地说求解李雅普诺夫方程并非易事，因而这种方法往往不用来判定系统的渐近稳定性，而是用来构造线性定常连续渐近稳定系统。

例 9-24 已知线性定常连续系统状态方程为

$$
\dot {x} _ {1} = x _ {2}, \quad \dot {x} _ {2} = 2 x _ {1} - x _ {2}
$$

试用李雅普诺夫方程判定系统的渐近稳定性。

解 为便于对比，先用特征值判据判断。系统状态方程为

$$
\dot {\boldsymbol {x}} = \left[ \begin{array}{c c} 0 & 1 \\ 2 & - 1 \end{array} \right] \boldsymbol {x}, \quad \boldsymbol {A} = \left[ \begin{array}{c c} 0 & 1 \\ 2 & - 1 \end{array} \right]
$$

$$
\left| \lambda I - A \right| = \left[ \begin{array}{l l} \lambda & - 1 \\ - 2 & \lambda + 1 \end{array} \right] = \lambda^ {2} + \lambda - 2 = (\lambda - 1) (\lambda + 2)
$$

特征值为2，1，故系统不稳定。令

$$
\boldsymbol {A} ^ {\mathrm {T}} \boldsymbol {P} + \boldsymbol {P A} = - \boldsymbol {Q} = - \boldsymbol {I}
$$

$$
\boldsymbol {P} = \boldsymbol {P} ^ {\mathrm {T}} = \left[ \begin{array}{c c} P _ {1 1} & P _ {1 2} \\ P _ {1 2} & P _ {2 2} \end{array} \right]
$$

则有 $\begin{array} { r l } { { \small \bigg [ \begin{array} { c c } { 0 } & { 2 } \\ { 1 } & { - 1 } \end{array} \bigg ] } { \small \bigg [ \begin{array} { c c } { P _ { 1 1 } } & { P _ { 1 2 } } \\ { P _ { 1 2 } } & { P _ { 2 2 } } \end{array} \bigg ] } + { \small \bigg [ \begin{array} { c c } { P _ { 1 1 } } & { P _ { 1 2 } } \\ { P _ { 1 2 } } & { P _ { 2 2 } } \end{array} \bigg ] } { \small \bigg [ \begin{array} { c c } { 0 } & { 1 } \\ { 2 } & { - 1 } \end{array} \bigg ] } = { \small \bigg [ \begin{array} { c c } { - 1 } & { 0 } \\ { 0 } & { - 1 } \end{array} \bigg ] } } \end{array}$

展开有 $4 P _ { 1 2 } = - 1 , ~ 2 P _ { 1 2 } - 2 P _ { 2 2 } = - 1 , ~ P _ { 1 1 } - P _ { 1 2 } + 2 P _ { 2 2 } = 0$

解得 $P = { \left[ \begin{array} { l l } { P _ { 1 1 } } & { P _ { 1 2 } } \\ { P _ { 1 2 } } & { P _ { 2 2 } } \end{array} \right] } = { \left[ \begin{array} { l l } { - { \frac { 3 } { 4 } } } & { - { \frac { 1 } { 4 } } } \\ { - { \frac { 1 } { 4 } } } & { { \frac { 1 } { 4 } } } \end{array} \right] }$

由于 $P _ { 1 1 } = - \frac { 3 } { 4 } < 0 , \mathrm { d e t } P = - \frac { 1 } { 4 } < 0$ ，故 $P$ 不定，可知系统非渐近稳定。由特征值判据知系统是不稳定的。

# (2) 线性定常离散系统渐近稳定性的判别

设线性定常离散系统状态方程为

$$
\boldsymbol {x} (k + 1) = \boldsymbol {\Phi} \boldsymbol {x} (k), \quad \boldsymbol {x} (0) = \boldsymbol {x} _ {0}; \quad k = 0, 1, 2, \dots \tag {9-225}
$$

式中， $\pmb { \phi }$ 阵非奇异；原点是平衡状态。取正定二次型函数

$$
V (\boldsymbol {x} (k)) = \boldsymbol {x} ^ {\mathrm {T}} (k) \boldsymbol {P x} (k)
$$

以 $\Delta V ( \boldsymbol { x } ( \boldsymbol { k } ) )$ 代替 $\dot { V } ( \pmb { x } )$ ，有

$$
\Delta V (\boldsymbol {x} (k)) = V (\boldsymbol {x} (k + 1)) - V (\boldsymbol {x} (k))
$$

考虑到状态方程(9-225)有

$$
\begin{array}{l} \Delta V (\boldsymbol {x} (k)) = \boldsymbol {x} ^ {\mathrm {T}} (k + 1) \boldsymbol {P} \boldsymbol {x} (k + 1) - \boldsymbol {x} ^ {\mathrm {T}} (k) \boldsymbol {P} \boldsymbol {x} (k) = [ \boldsymbol {\Phi} \boldsymbol {x} (k) ] ^ {\mathrm {T}} \boldsymbol {P} [ \boldsymbol {\Phi} \boldsymbol {x} (k) ] - \boldsymbol {x} ^ {\mathrm {T}} (k) \boldsymbol {P} \boldsymbol {x} (k) \\ = \boldsymbol {x} ^ {\mathrm {T}} (k) \left(\boldsymbol {\Phi} ^ {\mathrm {T}} \boldsymbol {P} \boldsymbol {\Phi} - \boldsymbol {P}\right) \boldsymbol {x} (k) \\ \end{array}
$$

令 ${ \pmb { \phi } } ^ { \mathrm { T } } { \pmb { P } } { \pmb { \phi } } - { \pmb { P } } = - { \pmb { Q } }$ (9-226)

于是有 $\Delta V ( \pmb { x } ( k ) ) = - \pmb { x } ^ { \mathnormal { \mathrm { T } } } ( k ) \pmb { Q } \pmb { x } ( k )$

定理 9-6 系统(9-225)渐近稳定的充分必要条件是，给定任一正定对称矩阵 $\pmb { Q }$ ，存在一个正定对称矩阵 $P$ 使式(9-226)成立。

${ \pmb x } ^ { \operatorname { T } } ( k ) P { \pmb x } ( k )$ 是系统的一个李雅普诺夫函数，式(9-226)称为离散的李雅普诺夫代数方程，通常可取 $\scriptstyle Q = I _ { \circ }$ 。

如果 $\Delta V ( \boldsymbol { x } ( \boldsymbol { k } ) )$ 沿任一解的序列不恒为零，则 $\pmb { Q }$ 可取为正半定矩阵。

综上所述，李雅普诺夫稳定性判据如表 9-1 所示。

表 9-1 李雅普诺夫稳定性判据汇总表  

<table><tr><td></td><td>系统方程</td><td>原点稳定性</td><td>充分必要条件或充分条件</td></tr><tr><td rowspan="2">间接法</td><td rowspan="2">\(\dot{x}=Ax,t≥0\)x(0)=x0</td><td>稳定</td><td>A的所有特征值均具有非正(负或零)实部,且具有零实部的特征值为A的最小特征多项式的单根</td></tr><tr><td>渐近稳定</td><td>A的所有特征值均具有负实部</td></tr><tr><td>直接法</td><td>\(\dot{x}=f(x,t)\)f(0,t)=0t≥t0</td><td>稳定</td><td>V(x(T1; x0,t0),t)正定有界,\(V(x(T1; x0,t0),t)\)存在且连续,负定且有界</td></tr><tr><td rowspan="12">直接法</td><td rowspan="3">\(\dot{x}=f(x,t)\)f(0,t)=0t≥t0</td><td>一致渐近稳定</td><td>V(x(T1; x0), t)正定有界, \(\dot{V}(x(T1; x0), t)\)存在且连续,负定且有界</td></tr><tr><td>全局一致渐近稳定</td><td>V(x(T1; x0, t0), t)正定有界, \(\dot{V}(x(T1; x0, t0), t)\)存在且连续,负定且有界,并且当||x||→∞时,V(x,t)→∞</td></tr><tr><td>不稳定</td><td>V(x(T1; x0, t0), t)在原点某一邻域内正定且有界, \(\dot{V}(x(T1; x0, t0), t)\)在同样的领域内存在且连续,但为正定</td></tr><tr><td rowspan="4">\(\dot{x}=f(x)\)f(0)=0t≥t0</td><td>稳定</td><td>V(x)正定, \(\dot{V}(x)\)负半定</td></tr><tr><td>渐近稳定</td><td>V(x)正定, \(\dot{V}(x)\)负定或 \(\dot{V}(x)\)负半定且 \(\dot{V}(x; x_0, 0)\)不恒等于零</td></tr><tr><td>全局渐近稳定</td><td>满足渐近稳定条件,并且当||x||→∞时,V(x)→∞</td></tr><tr><td>不稳定</td><td>V(x)正定, \(\dot{V}(x)\)正定</td></tr><tr><td>\(\dot{x}=A(t)x\)x(t0)=x0t≥t0</td><td>一致渐近稳定</td><td>对任意给定的一个实对称、一致有界和一致正定的时变矩阵Q(t),有唯一的实对称、一致有界和一致正定的时变矩阵P(t)存在,并使- \(\dot{P}(t)=P(t)A(t)+A^{\mathrm{T}}(t)P(t)+Q(t)\)成立</td></tr><tr><td>\(\dot{x}=Ax, t≥0\)x(0)=x0</td><td>全局一致渐近稳定</td><td>对给定的任一个正定对称矩阵Q,有唯一存在的正定对称矩阵P,使ATP+PA=-Q成立</td></tr><tr><td rowspan="2">x(k+1)=f(x(k))f(0)=0k=1,2,...</td><td rowspan="2">全局一致渐近稳定</td><td>V(x(k))正定ΔV(x(k))=V(x(k+1))-V(x(k))负定当||x(k)||→∞时,V(x(k))→∞</td></tr><tr><td>V(x(k))正定, ΔV(x(k))负半定,由任意初始状态x(0)所确定的系统轨线x(k)的ΔV(x(k))不恒为零,||x(k)||→∞时,V(x(k))→∞</td></tr><tr><td>x(k+1)=Gx(k)x(0)=x0</td><td>渐近稳定</td><td>给定一正定对称矩阵Q,存在一个正定对称矩阵P,使GTPG-P=-Q成立</td></tr></table>

# 9-4 线性定常系统的反馈结构及状态观测器

无论是在经典控制理论还是在现代控制理论中，反馈都是系统设计的主要方式。但由于经典控制理论是用传递函数来描述的，它只能用输出量作为反馈量。而现代控制理论由于采用系统内部的状态变量来描述系统的物理特性，因而除了输出反馈外，还经常采用状态反馈。在进行系统的分析综合时，状态反馈能提供更多的校正信息，因而在形成最优控制规律、抑制或消除扰动影响、实现系统解耦控制等方面，状态反馈均获得了广泛应用。

为了利用状态进行反馈，必须用传感器来测量状态变量，但并不是所有状态变量在物理上都可测量，于是提出了用状态观测器给出状态估值的问题。因此，状态反馈与状态观测器的设计便构成了用状态空间法综合设计系统的主要内容。

# 1. 线性定常系统常用反馈结构及其对系统特性的影响

# (1) 两种常用反馈结构

在系统的综合设计中，两种常用的反馈形式是线性直接状态反馈和线性非动态输出反馈，简称为状态反馈和输出反馈。

1) 状态反馈。设有 $n$ 维线性定常系统

$$
\dot {\boldsymbol {x}} = \boldsymbol {A} \boldsymbol {x} + \boldsymbol {B} \boldsymbol {u}, \quad \boldsymbol {y} = \boldsymbol {C} \boldsymbol {x} \tag {9-227}
$$

式中， x 、 u 、 y 分别为 $n$ 维、 $p$ 维和 $q$ 维向量；A、B、 $c$ 分别为 $n \times n$ 、 $n \times p$ 、 $q \times n$ 实数矩阵。

当将系统的控制量 $\pmb { u }$ 取为状态变量的线性函数

$$
\boldsymbol {u} = \boldsymbol {v} - \boldsymbol {K x} \tag {9-228}
$$

时，称之为线性直接状态反馈，简称为状态反馈，其中 $\nu$ 为 $p$ 维参考输入向量， $\pmb { K }$ 为 $( p$ $\times n )$ 维实反馈增益矩阵。在研究状态反馈时，假定所有的状态变量都是可以用来反馈的。

将式(9-228)代入式(9-227)可得状态反馈系统动态方程

$$
\dot {\boldsymbol {x}} = (\boldsymbol {A} - \boldsymbol {B} \boldsymbol {K}) \boldsymbol {x} + \boldsymbol {B} \boldsymbol {v}, \quad \boldsymbol {y} = \boldsymbol {C} \boldsymbol {x} \tag {9-229}
$$

其传递函数矩阵为

$$
\boldsymbol {G} _ {K} (s) = \boldsymbol {C} (s \boldsymbol {I} - \boldsymbol {A} + \boldsymbol {B} \boldsymbol {K}) ^ {- 1} \boldsymbol {B} \tag {9-230}
$$

因此可用{ABK，B，C}来表示引入状态反馈后的闭环系统。由式(9-229)可以看出，引入状态反馈后系统的输出方程没有变化。

加入状态反馈后系统方框图如图 9-24 所示。

![](images/a94011d5a8d50977f58773354dd384d6a669b23f2b28f74b604cf008c8d57176.jpg)  
图 9-24 加入状态反馈后系统方框图

2) 输出反馈。系统的状态常常不能全部测量到，因而状态反馈法的应用受到了限制。在此情况下，人们常常采用输出反馈法。输出反馈的目的首先是使系统闭环成为稳定系统，然后在此基础上进一步改善闭环系统性能。

输出反馈有两种形式：一种是将输出量反馈至状态微分，另一种是将输出量反馈至参考输入。

输出量反馈至状态微分系统方框图如图 9-25 所示。输出反馈系统的动态方程为

$$
\dot {\boldsymbol {x}} = \boldsymbol {A} \boldsymbol {x} + \boldsymbol {B} \boldsymbol {u} - \boldsymbol {H} \boldsymbol {y} = (\boldsymbol {A} - \boldsymbol {H} \boldsymbol {C}) \boldsymbol {x} + \boldsymbol {B} \boldsymbol {u}, \quad \boldsymbol {y} = \boldsymbol {C} \boldsymbol {x} \tag {9-231}
$$

其传递函数矩阵为

$$
\boldsymbol {G} _ {H} (s) = \boldsymbol {C} (s \boldsymbol {I} - \boldsymbol {A} + \boldsymbol {H} \boldsymbol {C}) ^ {- 1} \boldsymbol {B} \tag {9-232}
$$

![](images/b56c7ae3f6e789b64f6d228f57c07461f597f8937e3c246047154939468c1b1f.jpg)

![](images/ef1b763cd45fdc42573ce4784150e666151389c9792e3e88f17c09155a4ac9c2.jpg)  
图 9-25 输出量反馈至状态微分系统方框图

将输出量反馈至参考输入系统方框图如图 9-26所示。当将系统的控制量 $\pmb { u }$ 取为输出$\boldsymbol { y }$ 的线性函数

$$
\boldsymbol {u} = \boldsymbol {v} - \boldsymbol {F} \boldsymbol {y} \tag {9-233}
$$

时，称之为线性非动态输出反馈，常简称为输出反馈，其中 $\nu$ 为 $p$ 维参考输入向量， $F$ 为 $p \times q$ 维实反馈增益矩阵。这是一种最常用的输出反馈，在一些参考书中往往只介绍这一种输出反馈，而不介绍输出至状态微分的反馈。

![](images/5ad38a84812c0742dc0000fee69f1abea79cf323124a2cd96efd594d711a478c.jpg)  
图 9-26 输出量反馈至参考输入系统方框图

将式(9-233)代入式(9-227)可得输出反馈系统动态方程

$$
\dot {\boldsymbol {x}} = (\boldsymbol {A} - \boldsymbol {B F C}) \boldsymbol {x} + \boldsymbol {B} \boldsymbol {v}, \quad \boldsymbol {y} = \boldsymbol {C x} \tag {9-234}
$$

其传递函数矩阵为

$$
\boldsymbol {G} _ {F} (s) = \boldsymbol {C} (s \boldsymbol {I} - \boldsymbol {A} + \boldsymbol {B} \boldsymbol {F} \boldsymbol {C}) ^ {- 1} \boldsymbol {B} \tag {9-235}
$$

不难看出，不管是状态反馈还是输出反馈，都可以改变状态的系数矩阵，但这并不表明二者具有等同的功能。由于状态能完整地表征系统的动态行为，因而利用状态反馈时，其信息量大而完整，可以在不增加系统维数的情况下，自由地支配响应特性。而输出反馈仅利用了状态变量的线性组合进行反馈，其信息量较小，所引入的补偿装置将使系统维数增加，且难以得到任意的所期望的响应特性。一个输出反馈系统的性能，一定有对应的状态反馈系统与之等同，例如对于图 9-26 所示输出反馈系统，只要令 $\mathbf { \partial } _ { F C = K }$ 便可确定状态反馈增益矩阵。但是，对于一个状态反馈系统，却不一定有对应的输出反馈系统与之等同，这是由于令 $\pmb { K } \mathrm { = } \pmb { F C }$ 来求解矩阵 $F$ 时，有可能因 $F$ 含有高阶导数而无法实现。对于非最小相位被控对象，如果含有在复平面右半平面上的极点，并且选择在复平面右半平面上的校正零点来加以对消时，便会有不稳定的隐患。但是，由于输出反馈所用的输出变量总是容易测量的，实现起来比较方便，因而获得了较广泛的应用。对于状态反馈系统中不便测量或不能测量的状态变量，需要利用状态观测器进行重构。有关状态观测器的设计问题，后面将作进一步阐述。

# (2) 反馈结构对系统性能的影响

由于引入反馈，系统状态的系数矩阵发生了变化，对系统的可控性、可观测性、稳定性、响应特性等均有影响。

# 1) 对系统可控性和可观测性的影响。

定理 9-7 对于系统(9-227)，状态反馈的引入不改变系统的可控性，但可能改变系统的可观测性。

证明 设被控系统 $\varSigma _ { 0 }$ 的动态方程为

$$
\dot {x} = A x + B u, \quad y = C x
$$

加入状态反馈后系统 $\varSigma _ { K }$ 的动态方程为

$$
\dot {\boldsymbol {x}} = (\boldsymbol {A} - \boldsymbol {B} \boldsymbol {K}) \boldsymbol {x} + \boldsymbol {B} \boldsymbol {v}, \quad \boldsymbol {y} = \boldsymbol {C} \boldsymbol {x}
$$

首先证明状态反馈系统 $\varSigma _ { K }$ 可控的充分必要条件是被控系统 $\varSigma _ { 0 }$ 可控。

系统 $\varSigma _ { 0 }$ 的可控性矩阵为

$$
\boldsymbol {S} _ {c} = \left[ \begin{array}{l l l l} \boldsymbol {B} & \boldsymbol {A B} & \dots & \boldsymbol {A} ^ {n - 1} \boldsymbol {B} \end{array} \right]
$$

系统 $\varSigma _ { K }$ 的可控性矩阵为

$$
\boldsymbol {S} _ {c K} = \left[ \begin{array}{l l l l} \boldsymbol {B} & (\boldsymbol {A} - \boldsymbol {B} \boldsymbol {K}) \boldsymbol {B} & \dots & (\boldsymbol {A} - \boldsymbol {B} \boldsymbol {K}) ^ {n - 1} \boldsymbol {B} \end{array} \right]
$$

由于

$$
\boldsymbol {B} = \left[ \begin{array}{l l l l} \boldsymbol {b} _ {1} & \boldsymbol {b} _ {2} & \dots & \boldsymbol {b} _ {p} \end{array} \right], \quad \boldsymbol {A B} = \left[ \begin{array}{l l l l} \boldsymbol {A b} _ {1} & \boldsymbol {A b} _ {2} & \dots & \boldsymbol {A b} _ {p} \end{array} \right]
$$

$$
\left(\boldsymbol {A} - \boldsymbol {B} \boldsymbol {K}\right) \boldsymbol {B} = \left[ \begin{array}{l l l l} \left(\boldsymbol {A} - \boldsymbol {B} \boldsymbol {K}\right) \boldsymbol {b} _ {1} & \left(\boldsymbol {A} - \boldsymbol {B} \boldsymbol {K}\right) \boldsymbol {b} _ {2} & \dots & \left(\boldsymbol {A} - \boldsymbol {B} \boldsymbol {K}\right) \boldsymbol {b} _ {p} \end{array} \right]
$$

式中， $\pmb { b } _ { i } ( i { = } 1 , 2 , \ \cdots , p )$ 为列向量。将 $\pmb { K }$ 表示为行向量组

$$
\boldsymbol {K} = \left[ \begin{array}{c} \boldsymbol {k} _ {1} \\ \boldsymbol {k} _ {2} \\ \vdots \\ \boldsymbol {k} _ {p} \end{array} \right]
$$

则 $( A - B K ) \pmb { b } _ { i } = A \pmb { b } _ { i } - \left[ \pmb { b } _ { 1 } \quad \pmb { b } _ { 2 } \quad . . . \quad \pmb { b } _ { p } \right] \left[ \begin{array} { c } { \pmb { k } _ { 1 } \pmb { b } _ { i } } \\ { \pmb { k } _ { 2 } \pmb { b } _ { i } } \\ { \vdots } \\ { \pmb { k } _ { p } \pmb { b } _ { i } } \end{array} \right]$

令 $c _ { 1 i } = k _ { 1 } b _ { i } , \quad c _ { 2 i } = k _ { 2 } b _ { i } , \quad \cdots , \quad c _ { p i } = k _ { p } b _ { i }$

式中， $c _ { j i } ( j { = } 1 , 2 , \cdots , p )$ 均为标量。故

$$
\left(\boldsymbol {A} - \boldsymbol {B K}\right) \boldsymbol {b} _ {i} = \boldsymbol {A} \boldsymbol {b} _ {i} - \left(c _ {1 i} \boldsymbol {b} _ {1} + c _ {2 i} \boldsymbol {b} _ {2} + \dots + c _ {p i} \boldsymbol {b} _ {p}\right)
$$

这说明 $( A { - } B \mathbf { \delta } \textbf { \textit { K } } ) B$ 的列是[B AB]列的线性组合。同理有 $( A - B K ) ^ { 2 } B$ 的列是[B AB $\pmb { A } ^ { 2 } \pmb { B } ]$ 列的线性组合，如此等等，故 $\pmb { S } _ { c K }$ 的每一列均可表为 $\pmb { S } _ { c }$ 的列的线性组合。由此可得

$$
\operatorname {r a n k} \boldsymbol {S} _ {c K} \leqslant \operatorname {r a n k} \boldsymbol {S} _ {c} \tag {9-236}
$$

另一方面， $\varSigma _ { 0 }$ 又可看成为 $\varSigma _ { K }$ 的状态反馈系统，即

$$
\dot {x} = A x + B u = \left[ (A - B K) + B K \right] x + B u
$$

同理可得

$$
\operatorname {r a n k} \boldsymbol {S} _ {c} \leqslant \operatorname {r a n k} \boldsymbol {S} _ {c K} \tag {9-237}
$$

由式(9-236)和式(9-237)可得

$$
\operatorname {r a n k} \boldsymbol {S} _ {c K} = \operatorname {r a n k} \boldsymbol {S} _ {c} \tag {9-238}
$$

从而当且仅当 $\varSigma _ { 0 }$ 可控时， $\varSigma _ { K }$ 可控。

再来证明状态反馈系统不一定能保持可观测性，对此只需举一反例说明。例如，考察

$$
\dot {\boldsymbol {x}} = \left[ \begin{array}{l l} 1 & 2 \\ 0 & 3 \end{array} \right] \boldsymbol {x} + \left[ \begin{array}{l} 0 \\ 1 \end{array} \right] u, \quad y = \left[ \begin{array}{l l} 1 & 1 \end{array} \right] \boldsymbol {x}
$$

其可观测性判别阵

$$
\boldsymbol {V} _ {o} = \left[ \begin{array}{l} \boldsymbol {c} \\ \boldsymbol {c A} \end{array} \right] = \left[ \begin{array}{l l} 1 & 1 \\ 1 & 5 \end{array} \right], \quad \operatorname {r a n k} \boldsymbol {V} _ {o} = n = 2
$$

故该系统可观测。现引入状态反馈，取 k=[0 4]，则状态反馈系统 $\varSigma _ { K }$ 为

$$
\dot {\boldsymbol {x}} = (\boldsymbol {A} - \boldsymbol {b} \boldsymbol {k}) \boldsymbol {x} + \boldsymbol {b} \nu = \left[ \begin{array}{l l} 1 & 2 \\ 0 & - 1 \end{array} \right] \boldsymbol {x} + \left[ \begin{array}{l} 0 \\ 1 \end{array} \right] \nu , \quad y = \left[ \begin{array}{l l} 1 & 1 \end{array} \right] \boldsymbol {x}
$$

其可观测性判别阵

$$
\boldsymbol {V} _ {o K} = \left[ \begin{array}{c} \boldsymbol {c} \\ \boldsymbol {c} (\boldsymbol {A} - \boldsymbol {b} \boldsymbol {k}) \end{array} \right] = \left[ \begin{array}{l l} 1 & 1 \\ 1 & 1 \end{array} \right], \quad \operatorname {r a n k} \boldsymbol {V} _ {o K} = 1 <   n = 2
$$

故该状态反馈系统为不可观测。而若取 $k = \left[ \begin{array} { l l } { 0 } & { 5 } \end{array} \right]$ ，则通过计算可知，此时它成为可观测的。这表明状态反馈可能改变系统的可观测性，其原因是状态反馈造成了所配置的极点与零点相对消。

定理 9-8 对于系统(9-227)，输出至状态微分反馈的引入不改变系统的可观测性，但可能改变系统的可控性。

证明 用对偶定理证明。设被控对象 $\mathcal { L } _ { 0 }$ 为 $( A , B , C )$ ，将输出反馈至状态微分的系统$\Sigma _ { H }$ 为 $( ( A { - } H C ) , B , C )$ ，若 $( A , B , C )$ 可观测，则对偶系统 $( \pmb { A } ^ { \mathrm { T } } , \pmb { C } ^ { \mathrm { T } } , \pmb { B } ^ { \mathrm { T } } )$ 可控，由定理9-7可知，系统 $( A ^ { \mathrm { T } } , C ^ { \mathrm { T } } , B ^ { \mathrm { T } } )$ 加入状态反馈后的系统 $( ( A ^ { \mathrm { T } } { - } C ^ { \mathrm { T } } H ^ { \mathrm { T } } ) , C ^ { \mathrm { T } } , B ^ { \mathrm { T } } )$ 的可控性不变，但可能改变其可观测性。因而有

$$
\begin{array}{l} \operatorname {r a n k} \left[ \begin{array}{c c c c} \boldsymbol {C} ^ {\mathrm {T}} & \boldsymbol {A} ^ {\mathrm {T}} \boldsymbol {C} ^ {\mathrm {T}} & \dots & (\boldsymbol {A} ^ {\mathrm {T}}) ^ {n - 1} \boldsymbol {C} ^ {\mathrm {T}} \end{array} \right] \\ = \operatorname {r a n k} \left[ \begin{array}{l l l l} \boldsymbol {C} ^ {\mathrm {T}} & (\boldsymbol {A} ^ {\mathrm {T}} - \boldsymbol {C} ^ {\mathrm {T}} \boldsymbol {H} ^ {\mathrm {T}}) \boldsymbol {C} ^ {\mathrm {T}} & \dots & (\boldsymbol {A} ^ {\mathrm {T}} - \boldsymbol {C} ^ {\mathrm {T}} \boldsymbol {H} ^ {\mathrm {T}}) ^ {n - 1} \boldsymbol {C} ^ {\mathrm {T}} \end{array} \right] \tag {9-239} \\ = \operatorname {r a n k} \left[ \begin{array}{l l l l} \boldsymbol {C} ^ {\mathrm {T}} & (\boldsymbol {A} - \boldsymbol {H C}) ^ {\mathrm {T}} \boldsymbol {C} ^ {\mathrm {T}} & \dots & ((\boldsymbol {A} - \boldsymbol {C H}) ^ {\mathrm {T}}) ^ {n - 1} \boldsymbol {C} ^ {\mathrm {T}} \end{array} \right] \\ \end{array}
$$

上式表明，系统 $\varSigma _ { 0 }$ 与系统 $\Sigma _ { H }$ 可观测性判别阵的秩相等，这意味着若 $\varSigma _ { 0 }$ 可观测，则 $\Sigma _ { H }$ 也是可观测的，输出至状态微分反馈的引入不改变系统的可观测性。

由于系统 $( \pmb { A } ^ { \mathrm { T } } , \ \pmb { C } ^ { \mathrm { T } } , \ \pmb { B } ^ { \mathrm { T } } )$ 的可观测性判别阵为

$$
\begin{array}{l} \bar {\boldsymbol {S}} _ {o} = \left[ \begin{array}{l l l l} (\boldsymbol {B} ^ {\mathrm {T}}) ^ {\mathrm {T}} & (\boldsymbol {A} ^ {\mathrm {T}}) ^ {\mathrm {T}} (\boldsymbol {B} ^ {\mathrm {T}}) ^ {\mathrm {T}} & \dots & ((\boldsymbol {A} ^ {\mathrm {T}}) ^ {\mathrm {T}}) ^ {n - 1} (\boldsymbol {B} ^ {\mathrm {T}}) ^ {\mathrm {T}} \end{array} \right] \\ = \left[ \begin{array}{l l l l} \boldsymbol {B} & \boldsymbol {A B} & \dots & \boldsymbol {A} ^ {n - 1} \boldsymbol {B} \end{array} \right] \\ \end{array}
$$

系统 $( ( A ^ { \mathrm { T } } { - } C ^ { \mathrm { T } } H ^ { \mathrm { T } } )$ ， $C ^ { \mathrm { T } }$ ， $\pmb { B } ^ { \textrm { T } }$ )的可观测性判别阵为

$$
\begin{array}{l} \bar {V} _ {o H} = \left[ \left(\boldsymbol {B} ^ {\mathrm {T}}\right) ^ {\mathrm {T}} \quad \left(\boldsymbol {A} ^ {\mathrm {T}} - \boldsymbol {C} ^ {\mathrm {T}} \boldsymbol {H} ^ {\mathrm {T}}\right) ^ {\mathrm {T}} \left(\boldsymbol {B} ^ {\mathrm {T}}\right) ^ {\mathrm {T}} \dots \left(\left(\boldsymbol {A} ^ {\mathrm {T}} - \boldsymbol {C} ^ {\mathrm {T}} \boldsymbol {H} ^ {\mathrm {T}}\right) ^ {\mathrm {T}}\right) ^ {n - 1} \left(\boldsymbol {B} ^ {\mathrm {T}}\right) ^ {\mathrm {T}} \right] \\ = \left[ \begin{array}{l l l l} \boldsymbol {B} & (\boldsymbol {A} - \boldsymbol {H C}) \boldsymbol {B} & \dots & (\boldsymbol {A} - \boldsymbol {H C}) ^ {n - 1} \boldsymbol {B} \end{array} \right] \\ \end{array}
$$

系统加入状态反馈后可能改变其可观测性意味着有可能使得

$$
\operatorname {r a n k} \bar {V} _ {o} \neq \operatorname {r a n k} \bar {V} _ {o H} \tag {9-240}
$$

因为 $\bar { V } _ { o }$ 也是系统 $\varSigma _ { 0 }$ 的可控性判别阵， $\overline { { V } } _ { o H }$ 又是系统 $\varSigma _ { H }$ 的可控性判别阵，式(9-240)表明，输出至状态微分的反馈可能改变系统的可控性。证毕。

定理 9-9 对于系统(9-227)，输出至参考输入反馈的引入能同时不改变系统的可控性和可观测性，即输出反馈系统 $\scriptstyle \sum _ { F }$ 为可控(可观测)的充分必要条件是被控系统 $\varSigma _ { 0 }$ 为可控(可观测)。

证明 首先，由于对任一输出至参考输入的反馈系统都能找到一个等价的状态反馈系统，由定理 9-7 知状态反馈可保持可控性，因而输出至参考输入反馈的引入不改变系统的可控性。

由于 $\varSigma _ { 0 }$ 和 $\Sigma _ { F }$ 的可观测性判别阵分别为

$$
\boldsymbol {V} _ {o} = \left[ \begin{array}{c} \boldsymbol {C} \\ \boldsymbol {C A} \\ \vdots \\ \boldsymbol {C A} ^ {n - 1} \end{array} \right], \quad \boldsymbol {V} _ {o F} = \left[ \begin{array}{c} \boldsymbol {C} \\ \boldsymbol {C} (\boldsymbol {A} - \boldsymbol {B F C}) \\ \vdots \\ \boldsymbol {C} (\boldsymbol {A} - \boldsymbol {B F C}) ^ {n - 1} \end{array} \right]
$$

并且 $C = \left[ \begin{array} { c } { c _ { 1 } } \\ { c _ { 2 } } \\ { \vdots } \\ { c _ { q } } \end{array} \right] , C A = \left[ \begin{array} { c } { c _ { 1 } A } \\ { c _ { 2 } A } \\ { \vdots } \\ { c _ { q } A } \end{array} \right] , C ( A - B F C ) = \left[ \begin{array} { c } { c _ { 1 } ( A - B F C ) } \\ { c _ { 2 } ( A - B F C ) } \\ { \vdots } \\ { c _ { q } ( A - B F C ) } \end{array} \right]$

式中， $\pmb { c } _ { i } ( i { = } 1 , 2 , \cdots , q )$ 为行向量，将 $F$ 表为列向量组 $\{ f _ { j } \}$ ，即 $F { = } [ f _ { 1 } \quad f _ { 2 } \quad \cdots \quad f _ { q } ]$ ，则

$$
\begin{array}{l} \boldsymbol {c} _ {i} (\boldsymbol {A} - \boldsymbol {B F C}) = \boldsymbol {c} _ {i} \boldsymbol {A} - \boldsymbol {c} _ {i} \boldsymbol {B} \left(\boldsymbol {f} _ {1} \boldsymbol {c} _ {1} + \boldsymbol {f} _ {2} \boldsymbol {c} _ {2} + \dots + \boldsymbol {f} _ {q} \boldsymbol {c} _ {q}\right) \\ = \boldsymbol {c} _ {i} \boldsymbol {A} - \left[ \left(\boldsymbol {c} _ {i} \boldsymbol {B} \boldsymbol {f} _ {1}\right) \boldsymbol {c} _ {1} + \left(\boldsymbol {c} _ {i} \boldsymbol {B} \boldsymbol {f} _ {2}\right) \boldsymbol {c} _ {2} + \dots + \left(\boldsymbol {c} _ {i} \boldsymbol {B} \boldsymbol {f} _ {q}\right) \boldsymbol {c} _ {q} \right] \\ \end{array}
$$

令式中 $c _ { i } B f _ { j } { = } \alpha _ { j }$ ， $\alpha _ { j }$ 为标量， $j { = } 1 , 2 , \cdots , q$ ，则有

$$
\boldsymbol {c} _ {i} (\boldsymbol {A} - \boldsymbol {B F C}) = \boldsymbol {c} _ {i} \boldsymbol {A} - \left(\alpha_ {1} \boldsymbol {c} _ {1} + \alpha_ {2} \boldsymbol {c} _ {2} + \dots + \alpha_ {q} \boldsymbol {c} _ {q}\right)
$$

该式表明 $C ( A { - } B F C$ )的行是 $[ C ^ { \mathrm { T } } A ^ { \mathrm { T } } C$ T] T的行的线性组合。同理有 $C \left( A { - } B F C \right) ^ { 2 }$ 的行是 $[ \pmb { C } ^ { \textup { T } }$ $\pmb { A } ^ { \mathrm { T } } \pmb { C } ^ { \mathrm { T } } ( \pmb { A } ^ { \mathrm { T } } ) ^ { 2 } \pmb { C }$ T]T 的行的线性组合，如此等等。故 $V _ { o F }$ 的每一行均可表为 $V _ { o }$ 的行的线性组合，由此可得

$$
\operatorname {r a n k} V _ {o F} \leqslant \operatorname {r a n k} V _ {o} \tag {9-241}
$$

由于 $\varSigma _ { 0 }$ 又可看成为 $\Sigma _ { F }$ 的输出反馈系统，因而有

$$
\operatorname {r a n k} V _ {o} \leqslant \operatorname {r a n k} V _ {o F} \tag {9-242}
$$

由式(9-241)和式(9-242)可得

$$
\operatorname {r a n k} V _ {o} = \operatorname {r a n k} V _ {o F} \tag {9-243}
$$

这表明输出至参考输入的反馈可保持系统的可观测性。证毕。

2) 对系统稳定性的影响。状态反馈和输出反馈都能影响系统的稳定性。加入反馈，使得通过反馈构成的闭环系统成为稳定系统，称之为镇定。由于状态反馈具有许多优越性，且输出反馈系统总可以找到与之性能等同的状态反馈系统，故在此只讨论状态反馈的镇定问题。对于线性定常被控系统

$$
\dot {\boldsymbol {x}} = \boldsymbol {A} \boldsymbol {x} + \boldsymbol {B} \boldsymbol {u}
$$

如果可以找到状态反馈控制律

$$
\boldsymbol {u} = - \boldsymbol {K} \boldsymbol {x} + \boldsymbol {v}
$$

其中， $\nu$ 为参考输入，使得通过反馈构成的闭环系统

$$
\dot {\boldsymbol {x}} = (\boldsymbol {A} - \boldsymbol {B K}) \boldsymbol {x} + \boldsymbol {B} \boldsymbol {v}
$$

是渐近稳定的，即(ABK )的特征值均具有负实部，则称系统实现了状态反馈镇定。

定理 9-10 当且仅当系统（9-227）的不可控部分渐近稳定时，系统是状态反馈可镇定的。

证明 由于 $\{ A , B \}$ 不完全可控，则一定可引入非奇异线性变换进行可控性结构分解，使得

$$
\overline {{\boldsymbol {A}}} = \boldsymbol {P} \boldsymbol {A} \boldsymbol {P} ^ {- 1} = \left[ \begin{array}{l l} \overline {{\boldsymbol {A}}} _ {c} & \overline {{\boldsymbol {A}}} _ {1 2} \\ 0 & \overline {{\boldsymbol {A}}} _ {c} \end{array} \right], \quad \overline {{\boldsymbol {B}}} = \boldsymbol {P} \boldsymbol {B} = \left[ \begin{array}{l} \overline {{\boldsymbol {B}}} _ {c} \\ \boldsymbol {0} \end{array} \right] \tag {9-244}
$$

式中， $\overline { { A } } _ { c }$ 为可控状态子矩阵； $\overline { { A } } _ { \overline { { c } } }$ 为不可控状态子矩阵； $\overline { { B } } _ { c }$ 为可控输入子矩阵。并且对任意 $\overline { { K } } = [ \overline { { K } } _ { 1 }$ $\overline { { { \cal K } } } _ { 2 } ]$ 可导出

$$
\begin{array}{l} \det  (s \boldsymbol {I} - \boldsymbol {A} + \boldsymbol {B} \boldsymbol {K}) = \det  (s \boldsymbol {I} - \bar {\boldsymbol {A}} + \bar {\boldsymbol {B}} \bar {\boldsymbol {K}}) \\ = \det  \left[ \begin{array}{c c} s \boldsymbol {I} - \overline {{\boldsymbol {A}}} _ {c} + \overline {{\boldsymbol {B}}} _ {c} \overline {{\boldsymbol {K}}} _ {1} & - \overline {{\boldsymbol {A}}} _ {1 2} + \overline {{\boldsymbol {B}}} _ {c} \overline {{\boldsymbol {K}}} _ {2} \\ \boldsymbol {0} & s \boldsymbol {I} - \overline {{\boldsymbol {A}}} _ {\bar {c}} \end{array} \right] \tag {9-245} \\ = \det  (s I - \bar {A} _ {c} + \bar {B} _ {c} \bar {K} _ {1}) \det  (s I - \bar {A} _ {\bar {c}}) \\ \end{array}
$$

由于 $\{ \overline { { A } } _ { c } , \overline { { B } } _ { c } \}$ 为可控子系统，故必存在 $\overline { { \pmb { K } } } _ { 1 }$ 使( $\overline { { A } } _ { c } - \overline { { B } } _ { c } \overline { { K } } _ { 1 }$ )的特征值均具有负实部。又因为状态反馈对不可控子系统的极点毫无影响，从而可知欲使(ABK)的特征值均具有负实部，只有使不可控部分 $\overline { { A } } _ { c }$ 的特征值均具有负实部。这表明系统由状态反馈可镇定的充分必要条件是不可控部分渐近稳定。证毕。

# 2. 系统的极点配置

状态反馈和输出反馈都能改变闭环系统的极点位置。所谓极点配置，就是利用状态反馈或输出反馈使闭环系统的极点位于所希望的极点位置。由于系统的性能和它的极点位置密切相关，因而极点配置问题在系统设计中是很重要的。这里需要解决两个问题：一是建立极点可配置的条件；二是确定极点配置所需要的反馈增益矩阵。

# (1) 极点可配置条件

这里给出的极点可配置条件既适合于单输入-单输出系统，也适合于多输入-多输出

系统。

1) 利用状态反馈的极点可配置条件。

定理 9-11 利用状态反馈任意配置闭环极点的充分必要条件是被控系统（9-227）可控。

证明 下面就单输入-多输出系统来证明该定理。这时被控系统 $( A , B , C )$ )中的 $\pmb { B }$ 为一列向量，记为 $\pmb { b }$ 。

充分性：若系统(A，b)可控，则通过非奇异线性变换 $\pmb { x } = \pmb { P } ^ { - 1 } \overline { { \pmb { x } } }$ 可变换为可控标准型

$$
\dot {\overline {{x}}} = \overline {{A}} \overline {{x}} + \overline {{b}} u
$$

式中

$$
\overline {{A}} = P A P ^ {- 1} = \left[ \begin{array}{c c c c c} 0 & 1 & 0 & \dots & 0 \\ 0 & 0 & 1 & \dots & 0 \\ \vdots & \vdots & \vdots & & \vdots \\ 0 & 0 & 0 & \dots & 1 \\ - a _ {0} & - a _ {1} & - a _ {2} & \dots & - a _ {n - 1} \end{array} \right], \quad \overline {{b}} = P b = \left[ \begin{array}{c} 0 \\ 0 \\ \vdots \\ 0 \\ 1 \end{array} \right]
$$

在单输入情况下，引入状态反馈

$$
u = v - k x = v - k P ^ {- 1} \bar {x} = v - \bar {k} \bar {x}
$$

其中

$$
\overline {{\boldsymbol {k}}} = \boldsymbol {k} \boldsymbol {P} ^ {- 1} = \left[ \begin{array}{c c c c} \overline {{\boldsymbol {k}}} _ {0} & \overline {{\boldsymbol {k}}} _ {1} & \dots & \overline {{\boldsymbol {k}}} _ {n - 1} \end{array} \right]
$$

则引入状态反馈后闭环系统的状态阵为

$$
\overline {{A}} - \overline {{b k}} = \left[ \begin{array}{c c c c c} 0 & 1 & 0 & \dots & 0 \\ 0 & 0 & 1 & \dots & 0 \\ \vdots & \vdots & \vdots & & \vdots \\ 0 & 0 & 0 & \dots & 1 \\ (- a _ {0} - \bar {k} _ {0}) & (- a _ {1} - \bar {k} _ {1}) & (- a _ {2} - \bar {k} _ {2}) & \dots & (- a _ {n - 1} - \bar {k} _ {n - 1}) \end{array} \right] \tag {9-246}
$$

对于式(9-246)这种特殊形式的矩阵，容易写出其闭环特征方程

$$
\begin{array}{l} \det  \left[ s I - (\bar {A} - \bar {b k}) \right] = s ^ {n} + \left(a _ {n - 1} + \bar {k} _ {n - 1}\right) s ^ {n - 1} + \left(a _ {n - 2} + \bar {k} _ {n - 2}\right) s ^ {n - 2} \tag {9-247} \\ + \dots + (a _ {1} + \bar {k} _ {1}) s + (a _ {0} + \bar {k} _ {0}) = 0 \\ \end{array}
$$

显然，该 $n$ 阶特征方程中的 $n$ 个系数，可通过 $\overline { { k } } _ { 0 }$ , $\overline { { k _ { \scriptscriptstyle 1 } } }$ , …, $\overline { { k } } _ { n - 1 }$ 来独立设置，也就是说$( { \overline { { A } } } - { \overline { { b } } } k$ )的特征值可以任意选择，即系统的极点可以任意配置。

必要性：如果系统 $( A , b )$ 不可控，就说明系统的有些状态将不受 $u$ 的控制，则引入状态反馈时就不可能通过控制来影响不可控的极点。证毕。

2) 利用输出反馈的极点可配置条件。

定理 9-12 用输出至状态微分的反馈任意配置闭环极点的充分必要条件是被控系统（9-227）可观测。

证明 下面以多输入-单输出系统为例给出定理的证明。根据对偶定理可知，若被控系统 $( A , B , c )$ 可观测，则对偶系统( $\pmb { A } ^ { \mathrm { T } }$ , T c , $\pmb { B } ^ { \mathrm { T } }$ )可控，由状态反馈极点配置定理知

$\left( \mathbf { \nabla } A ^ { \mathrm { T } } - c ^ { \mathrm { T } } h ^ { \mathrm { T } } \right.$ )的特征值可任意配置，其中 $\pmb { h }$ 为 $n \times 1$ 输出反馈向量。由于 $\left( \mathbf { \nabla } A ^ { \mathrm { T } } - c ^ { \mathrm { T } } h ^ { \mathrm { T } } \right.$ )的特征值与 $( A ^ { \mathrm { T } } - c ^ { \mathrm { T } } h ^ { \mathrm { T } } ) ^ { \mathrm { T } } \mathrm { = } A \mathrm { - } h c$ 的特征值相同，故当且仅当系统 $( A , B , c )$ 可观测时，可以任意配置 $\left( A - h c \right)$ 的特征值。证毕。

为了根据期望闭环极点来设计输出反馈向量 $h$ 的参数，只需将期望的系统特征多项式与该输出反馈系统特征多项式 $\left| \lambda I - ( A - h c ) \right|$ 相比即可。

对于多输入-单输出被控系统来说，当采用输出至参考输入的反馈时，反馈增益矩阵$F$ 为 $p \times 1$ 向量，记为 $f _ { i }$ ，则

$$
\boldsymbol {u} = \boldsymbol {v} - \boldsymbol {f} y
$$

输出反馈系统的动态方程为

$$
\dot {\boldsymbol {x}} = (\boldsymbol {A} - \boldsymbol {B f c}) \boldsymbol {x} + \boldsymbol {B v}, \quad y = \boldsymbol {c x}
$$

若令 $\scriptstyle f c = K$ ，该输出反馈便等价为状态反馈。适当选择 $f$ ，可使特征值任意配置。但是，当比例的状态反馈变换为输出反馈时，输出反馈中必定含有输出量的各阶导数，于是 $f$ 不是常数向量，这会给物理实现带来困难，因而其应用受限。可推论，当 $f$ 是常数向量时，便不能任意配置极点。

(2) 单输入-单输出系统的极点配置算法

对于具体的可控单输入-单输出系统，求解实现希望极点配置的状态反馈向量 $\pmb { k }$ 时，不必像定理9-11中证明那样去进行可控标准型变换，只需要运行如下简单算法。

步骤 1：列写系统状态方程及状态反馈控制律

$$
\dot {\boldsymbol {x}} = \boldsymbol {A} \boldsymbol {x} + \boldsymbol {b} \boldsymbol {u}, \quad \boldsymbol {u} = \boldsymbol {v} - \boldsymbol {k x}
$$

其中 $k { = } [ k _ { 0 } \quad k _ { 1 } \quad \cdots \quad k _ { n - 1 } ] _ { \mathrm { { c } } }$ 。

步骤 2：检验 $( \textbf { \em A } , \textbf { \em b } )$ 的可控性。若 rank[b Ab … An1 b]=n，则转下步。

步骤 3：由要求配置的闭环极点 $\lambda _ { 1 } , \lambda _ { 2 } , \cdots , \lambda _ { n }$ ，求出希望特征多项式 $a _ { 0 } ^ { * } ( s ) = \prod _ { i = 1 } ^ { n } \left( s - \lambda _ { i } \right) ,$ 。

步骤 4：计算状态反馈系统的特征多项式 $a _ { 0 } ( s ) { = } \mathrm { d e t } [ s I { - } A { + } b k ] ,$ 。

步骤 5：比较多项式 $a _ { 0 } ^ { * } ( s )$ 与 $a _ { 0 } ( s ) { \mathrm { . } }$ ，令其对应项系数相等，可确定状态反馈增益向量 $\pmb { k }$ 。

应当指出，应用极点配置方法来改善系统性能，有以下需要注意的方面：

1) 配置极点时并非离虚轴越远越好，以免造成系统带宽过大使抗扰性降低。  
2) 状态反馈向量 $k$ 中的元素不宜过大，否则物理实现不易。  
3) 闭环零点对系统动态性能影响甚大，在规定希望配置的闭环极点时，需要充分考虑闭环零点的影响。  
4) 状态反馈对系统的零点和可观测性没有影响，只有当任意配置的极点与系统零点存在对消时，状态反馈系统的零点和可观测性将会改变。

以上性质适用于单输入-多输出或单输出系统，但不适用于多输入-多输出系统。

例 9-25 已知单输入线性定常系统的状态方程为

$$
\dot {\boldsymbol {x}} = \left[ \begin{array}{r r r} 0 & 0 & 0 \\ 1 & - 6 & 0 \\ 0 & 1 & - 1 2 \end{array} \right] \boldsymbol {x} + \left[ \begin{array}{l} 1 \\ 0 \\ 0 \end{array} \right] u
$$

求状态反馈向量 $\pmb { k }$ ，使系统的闭环特征值为

$$
\lambda_ {1} = - 2, \quad \lambda_ {2} = - 1 + j, \quad \lambda_ {3} = - 1 - j
$$

解 系统的可控性判别矩阵为

$$
\boldsymbol {S} _ {c} = \left[ \begin{array}{l l l} \boldsymbol {b} & \boldsymbol {A b} & \boldsymbol {A ^ {2} b} \end{array} \right] = \left[ \begin{array}{l l l} 1 & 0 & 0 \\ 0 & 1 & - 6 \\ 0 & 0 & 1 \end{array} \right]
$$

$$
\operatorname {r a n k} S _ {c} = 3 = n
$$

系统可控，满足极点可配置条件。系统的特征多项式为

$$
\det  (s I - A) = \det  \left[ \begin{array}{c c c} s & 0 & 0 \\ - 1 & s + 6 & 0 \\ 0 & - 1 & s + 1 2 \end{array} \right] = s ^ {3} + 1 8 s ^ {2} + 7 2 s
$$

希望特征多项式为

$$
a _ {0} ^ {*} (s) = (s - \lambda_ {1}) (s - \lambda_ {2}) (s - \lambda_ {3}) = (s + 2) (s + 1 - j) (s + 1 + j) = s ^ {3} + 4 s ^ {2} + 6 s + 4
$$

于是可求得

$$
\overline {{\boldsymbol {k}}} = \left[ \begin{array}{l l l} a _ {0} ^ {*} - a _ {0} & a _ {1} ^ {*} - a _ {1} & a _ {2} ^ {*} - a _ {2} \end{array} \right] = \left[ \begin{array}{l l l} 4 & - 6 6 & - 1 4 \end{array} \right]
$$

变换矩阵为

$$
\begin{array}{l} \boldsymbol {P} ^ {- 1} = \left[ \begin{array}{l l l} \boldsymbol {A} ^ {2} \boldsymbol {b} & \boldsymbol {A} \boldsymbol {b} & \boldsymbol {b} \end{array} \right] \left[ \begin{array}{l l l} 1 & 0 & 0 \\ a _ {2} & 1 & 0 \\ a _ {1} & a _ {2} & 1 \end{array} \right] = \left[ \begin{array}{l l l} 0 & 0 & 1 \\ - 6 & 1 & 0 \\ 1 & 0 & 0 \end{array} \right] \left[ \begin{array}{l l l} 1 & 0 & 0 \\ 1 8 & 1 & 0 \\ 7 2 & 1 8 & 1 \end{array} \right] = \left[ \begin{array}{l l l} 7 2 & 1 8 & 1 \\ 1 2 & 1 & 0 \\ 1 & 0 & 0 \end{array} \right] \\ \boldsymbol {P} = \left[ \begin{array}{c c c} 0 & 0 & 1 \\ 0 & 1 & - 1 2 \\ 1 & - 1 8 & 1 4 4 \end{array} \right] \\ \boldsymbol {k} = \overline {{\boldsymbol {k}}} \boldsymbol {P} = \left[ \begin{array}{l l l} 4 & - 6 6 & - 1 4 \end{array} \right] \left[ \begin{array}{c c c} 0 & 0 & 1 \\ 0 & 1 & - 1 2 \\ 1 & - 1 8 & 1 4 4 \end{array} \right] = \left[ \begin{array}{l l l} - 1 4 & 1 8 6 & - 1 2 2 0 \end{array} \right] \\ \end{array}
$$

$$
\begin{array}{l} = \left[ \begin{array}{c c c} s + k _ {1} & k _ {2} & k _ {3} \\ - 1 & s + 6 & 0 \\ 0 & - 1 & s + 1 2 \end{array} \right] \\ = s ^ {3} + \left(k _ {1} + 1 8\right) s ^ {2} + \left(1 8 k _ {1} + k _ {2} + 7 2\right) s + \left(7 2 k _ {1} + 1 2 k _ {2} + k _ {3}\right) \\ \end{array}
$$

于是有 $k _ { \mathrm { 1 } } + 1 8 = 4$

$$
1 8 k _ {1} + k _ {2} + 7 2 = 6
$$

$$
7 2 k _ {1} + 1 2 k _ {2} + k _ {3} = 4
$$

可求得 $k _ { 1 } = - 1 4 , ~ k _ { 2 } = 1 8 6 , ~ k _ { 3 } = - 1 2 2 0$

$$
\boldsymbol {k} = \left[ \begin{array}{l l l} k _ {1} & k _ {2} & k _ {3} \end{array} \right] = \left[ \begin{array}{l l l} - 1 4 & 1 8 6 & - 1 2 2 0 \end{array} \right]
$$

# (3) 状态反馈对传递函数零点的影响

状态反馈在改变系统极点的同时，是否对系统的零点产生影响？下面来分析回答这一问题。

已知完全可控的单输入-单输出线性定常系统可经适当非奇异线性变换化为可控标准型

$$
\dot {\vec {x}} = \overline {{A}} \vec {x} + \overline {{b}} u, \quad y = \overline {{c x}}
$$

被控系统的传递函数为

$$
\begin{array}{l} G (s) = \boldsymbol {c} (s \boldsymbol {I} - \boldsymbol {A}) ^ {- 1} \boldsymbol {b} = \overline {{\boldsymbol {c}}} (s \boldsymbol {I} - \overline {{\boldsymbol {A}}}) ^ {- 1} \overline {{\boldsymbol {b}}} \\ = \frac {\left[ \begin{array}{l l l l} \beta_ {0} & \beta_ {1} & \cdots & \beta_ {n - 1} \end{array} \right]}{s ^ {n} + a _ {n - 1} s ^ {n - 1} + \cdots + a _ {1} s + a _ {0}} \left[ \begin{array}{c c c c} \times & \dots & \times & 1 \\ \times & \dots & \times & s \\ \vdots & & \vdots & \vdots \\ \times & \dots & \times & s ^ {n - 1} \end{array} \right] \left[ \begin{array}{l} 0 \\ \vdots \\ 0 \\ 1 \end{array} \right] \\ = \frac {\beta_ {n - 1} s ^ {n - 1} + \cdots + \beta_ {1} s + \beta_ {0}}{s ^ {n} + a _ {n - 1} s ^ {n - 1} + \cdots + a _ {1} s + a _ {0}} \\ \end{array}
$$

引入状态反馈后的闭环系统传递函数为

$$
\begin{array}{l} G _ {K} (s) = \boldsymbol {c} (s \boldsymbol {I} - \boldsymbol {A} + \boldsymbol {b k}) ^ {- 1} \boldsymbol {b} = \overline {{\boldsymbol {c}}} (s \boldsymbol {I} - \overline {{\boldsymbol {A}}} + \overline {{\boldsymbol {b k}}}) ^ {- 1} \overline {{\boldsymbol {b}}} \\ = \frac {\left[ \beta_ {0} \quad \beta_ {1} \quad \cdots \quad \beta_ {n - 1} \right]}{s ^ {n} + a _ {n - 1} ^ {*} s ^ {n - 1} + \cdots + a _ {1} ^ {*} s + a _ {0} ^ {*}} \left[ \begin{array}{c c c c} \times & \dots & \times & 1 \\ \times & \dots & \times & s \\ \vdots & & \vdots & \vdots \\ \times & \dots & \times & s ^ {n - 1} \end{array} \right] \left[ \begin{array}{l} 0 \\ \vdots \\ 0 \\ 1 \end{array} \right] \\ = \frac {\beta_ {n - 1} s ^ {n - 1} + \cdots + \beta_ {1} s + \beta_ {0}}{s ^ {n} + a _ {n - 1} ^ {*} s ^ {n - 1} + \cdots + a _ {1} ^ {*} s + a _ {0} ^ {*}} \\ \end{array}
$$

上述推导表明，由于 ad $\mathrm { j } ( s I - { \overline { { A } } }$ )与 adj $( s I - \overline { { A } } + \overline { { b } } \overline { { k } }$ )的第 $n$ 列相同，故 $G ( s )$ 与 $G _ { K } ( s )$ 的分子多项式相同，即闭环系统零点与被控系统零点相同，状态反馈对 $G ( s )$ 的零点没有影响，仅使 $G ( s )$ 的极点改变为闭环系统极点。然而可能有这种情况：引入状态反馈后恰巧使某些极点移到 $G ( s )$ 的零点处而构成极、零点对消，这时既失去了一个系统零点，又失去了一个系统极点，并且被对消掉的那些极点可能不可观测。这也是对状态反馈可能使系统失去可观测性的一个直观解释。

# 3. 全维状态观测器及其设计

当利用状态反馈配置系统极点时，需要用传感器测量状态变量以便实现反馈。但在许多情况下，通常只有被控对象的输入量和输出量能够用传感器测量，而多数状态变量不易测得或不可能测得，于是提出了利用被控对象的输入量和输出量建立状态观测器(又称为状态估计器、状态重构器)来重构状态的问题。当重构状态向量的维数等于被控对象状态向量的维数时，称为全维状态观测器。

# (1) 全维状态观测器构成方案

设被控对象动态方程为

$$
\dot {\boldsymbol {x}} = \boldsymbol {A} \boldsymbol {x} + \boldsymbol {B} \boldsymbol {u}, \quad \boldsymbol {y} = \boldsymbol {C} \boldsymbol {x} \tag {9-248}
$$

构造一个动态方程与式(9-248)相同且能用计算机实现的模拟被控系统

$$
\dot {\hat {x}} = A \hat {x} + B u, \quad \hat {y} = C \hat {x} \tag {9-249}
$$

式中， $\hat { x }$ 、 $\hat { y }$ 分别为模拟系统的状态向量和输出向量，是被控对象状态向量和输出向量的估值。当模拟系统与被控对象的初始状态向量相同时，在同一输入作用下，有 ${ \hat { x } } = x$ ，可用 $\hat { x }$ 作为状态反馈所需用的信息。但是，被控对象的初始状态可能很不相同，模拟系统中积分器初始条件的设置又只能预估，因而两个系统的初始状态总有差异，即使两个系统的 A、B、 $c$ 阵完全一样，也必定存在估计状态与被控对象实际状态的误差 $( { \hat { \mathbf { x } } } - { \mathbf { x } } )$ ，难以实现所需要的状态反馈。但是， $( { \hat { x } } - x )$ 的存在必定导致 $( { \hat { \mathbf { y } } } - \mathbf { y } )$ 的存在，而被控系统的输出量总是可以用传感器测量的，于是可根据一般反馈控制原理，将 $( { \hat { \mathbf { y } } } - \mathbf { y } )$ 负反馈至 $\dot { \hat { x } }$ 处，控制 $( { \hat { \mathbf { y } } } - \mathbf { y } )$ 尽快逼近于零，从而使 $( { \hat { \mathbf { x } } } - { \mathbf { x } } )$ 尽快逼近于零，便可以利用 $\hat { x }$ 来形成状态反馈。按以上原理构成的状态观测器及其实现状态反馈的方框图如图9-27所示。状态观测器有两个输入，即 $\pmb { u }$ 和 $\boldsymbol { y }$ ，输出为 $\hat { x }$ 。观测器含 $n$ 个积分器并对全部状态变量作出估计。 $\pmb { H }$ 为观测器输出反馈阵，它把 $( { \hat { \mathbf { y } } } - \mathbf { y } )$ 负反馈至 $\dot { \hat { \boldsymbol { x } } }$ 处，是为配置观测器极点，提高其动态性能，即尽快使 $( { \hat { \mathbf { x } } } - { \mathbf { x } } )$ 逼近于零而引入的，它是前面所介绍过的一种输出反馈。

# (2) 全维状态观测器分析设计

由图 9-27可列出全维状态观测器动态方程

$$
\dot {\hat {x}} = A \hat {x} + B u - H (\hat {y} - y), \quad \hat {y} = C \hat {x} \tag {9-250}
$$

故有 ${ \dot { \hat { x } } } = A { \hat { x } } + B u - H C ( { \hat { x } } - x ) = ( A - H C ) { \hat { x } } + B u + H y$ (9-251)

式中，(AHC)称为观测器系统矩阵。观测器分析设计的关键问题是能否在任何初始条件下，即尽管 ${ \hat { x } } \left( t _ { 0 } \right)$ 与 $x ( t _ { 0 } )$ 不同，但总能保证

$$
\lim  _ {t \rightarrow \infty} (\hat {\boldsymbol {x}} (t) - \boldsymbol {x} (t)) = \mathbf {0} \tag {9-252}
$$

成立。只有满足式(9-252)，状态反馈系统才能正常工作，式(9-231)所示系统才能作为实际的状态观测器，故式(9-252)称为观测器存在条件。

![](images/923b4e5a5d7a5a321ab04511628e94b76b8e12c7091f6cee02b96566ad0ce93e.jpg)  
图 9-27 状态观测器及其实现状态反馈的系统方框图

由式(9-251)与式(9-248)可得

$$
\dot {\boldsymbol {x}} - \dot {\hat {\boldsymbol {x}}} = (\boldsymbol {A} - \boldsymbol {H C}) (\boldsymbol {x} - \hat {\boldsymbol {x}}) \tag {9-253}
$$

其解为

$$
\boldsymbol {x} (t) - \hat {\boldsymbol {x}} (t) = \mathrm {e} ^ {(A - H C) (t - t _ {0})} \left[ \boldsymbol {x} \left(t _ {0}\right) - \hat {\boldsymbol {x}} \left(t _ {0}\right) \right] \tag {9-254}
$$

显见当 ${ \hat { x } } \left( t _ { 0 } \right) { = } { \mathbf { x } } ( t _ { 0 } )$ 时，恒有 ${ \pmb x } \left( t \right) = \hat { { \pmb x } } \left( t \right)$ ，所引入的输出反馈并不起作用。当 $\hat { \mathbf { x } } \left( t _ { 0 } \right) \neq \mathbf { x } \left( t _ { 0 } \right)$ 时，有 $\hat { \mathbf { x } } \left( t \right) \neq \mathbf { x } \left( t \right)$ ，输出反馈便起作用了，这时只要(AHC )的全部特征值具有负实部，初始状态向量误差总会按指数衰减规律满足式(9-252)，其衰减速率取决于观测器的极点配置。由前面的输出反馈定理可知，若被控对象可观测，则(AHC )的极点可任意配置，以满足$\hat { x }$ 逼近 $\boldsymbol { x }$ 的速率要求，因而保证了状态观测器的存在性。

定理 9-13 若被控系统 $( A , B , C )$ 可观测，则其状态可用形如

$$
\dot {\hat {x}} = A \hat {x} + B u - H C (\hat {x} - x) = (A - H C) \hat {x} + B u + H y \tag {9-255}
$$

的全维状态观测器给出估值，其中矩阵 $H$ 按任意配置观测器极点的需要来选择，以决定状态误差衰减的速率。

选择 $\pmb { H }$ 阵参数时，应注意防止数值过大带来的实现困难，如饱和效应、噪声加剧等，通常希望观测器响应速度比状态反馈系统的响应速度要快些。

例 9-26 设被控对象传递函数为

$$
\frac {Y (s)}{U (s)} = \frac {2}{(s + 1) (s + 2)}
$$

试设计全维状态观测器，将极点配置在10，10。

解 被控对象的传递函数为

$$
\frac {Y (s)}{U (s)} = \frac {2}{(s + 1) (s + 2)} = \frac {2}{s ^ {2} + 3 s + 2}
$$

根据传递函数可直接写出系统的可控标准型

$$
\dot {\boldsymbol {x}} = \boldsymbol {A} \boldsymbol {x} + \boldsymbol {b} \boldsymbol {u}, \quad \boldsymbol {y} = \boldsymbol {c} \boldsymbol {x}
$$

其中 $A = { \left[ \begin{array} { l l } { 0 } & { 1 } \\ { - 2 } & { - 3 } \end{array} \right] } , \quad b = { \left[ \begin{array} { l } { 0 } \\ { 1 } \end{array} \right] } , \quad c = \left[ 2 \quad 0 \right]$

显然，系统可控可观测。 $n { = } 2$ ， $q { = } 1$ ，输出反馈向量 $\pmb { h }$ 为 $2 \times 1$ 向量。全维状态观测器系统矩阵为

$$
\boldsymbol {A} - \boldsymbol {h} \boldsymbol {c} = \left[ \begin{array}{l l} 0 & 1 \\ - 2 & - 3 \end{array} \right] - \left[ \begin{array}{l} h _ {0} \\ h _ {1} \end{array} \right] \left[ \begin{array}{l l} 2 & 0 \end{array} \right] = \left[ \begin{array}{l l} - 2 h _ {0} & 1 \\ - 2 - 2 h _ {1} & - 3 \end{array} \right]
$$

观测器特征方程为

$$
\left| \lambda I - (A - h c) \right| = \lambda^ {2} + (2 h _ {0} + 3) \lambda + (6 h _ {0} + 2 h _ {1} + 2) = 0
$$

期望特征方程为

$$
(\lambda + 1 0) ^ {2} = \lambda^ {2} + 2 0 \lambda + 1 0 0 = 0
$$

令两特征方程同次项系数相等，可得

$$
2 h _ {0} + 3 = 2 0, \quad 6 h _ {0} + 2 h _ {1} + 2 = 1 0 0
$$

因而有 $h _ { \scriptscriptstyle 0 } = 8 . 5 , \quad h _ { \scriptscriptstyle 1 } = 2 3 . 5$

$h _ { 0 }$ ， $h _ { 1 }$ 分别为由 $( { \hat { y } } - y )$ 引至 $\dot { \hat { x } } _ { 1 } , \dot { \hat { x } } _ { 2 }$ 的反馈系数。被控对象及全维状态观测器组合系统的状态变量图如图 9-28 所示。

![](images/32ef9bef00c715b8ba9121238e6f466948c100e0ee657348cac87e150962648b.jpg)  
图 9-28 全维状态观测器及被控对象组合系统的状态变量图

# 4. 分离特性

当用全维状态观测器提供的状态估值 $\hat { x }$ 代替真实状态 $\boldsymbol { x }$ 来实现状态反馈时，为保持系统的期望特征值，其状态反馈阵 $\pmb { K }$ 是否需要重新设计？当观测器被引入系统以后，状态反馈系统部分是否会改变已经设计好的观测器极点配置，其观测器输出反馈阵 $\pmb { H }$ 是否需要重新设计？为此需要对引入观测器的状态反馈系统作进一步分析。整个系统的结构图如图 9-27所示，是一个 $2 n$ 维的复合系统，其中

$$
\boldsymbol {u} = \boldsymbol {v} - K \hat {\boldsymbol {x}} \tag {9-256}
$$

状态反馈子系统动态方程为

$$
\dot {\boldsymbol {x}} = \boldsymbol {A} \boldsymbol {x} + \boldsymbol {B} \boldsymbol {u} = \boldsymbol {A} \boldsymbol {x} - \boldsymbol {B} \boldsymbol {K} \hat {\boldsymbol {x}} + \boldsymbol {B} \boldsymbol {v}, \quad \boldsymbol {y} = \boldsymbol {C} \boldsymbol {x} \tag {9-257}
$$

全维状态观测器子系统动态方程为

$$
\dot {\hat {x}} = A \hat {x} + B u - H (\hat {y} - y) = (A - B K - H C) \hat {x} + H C x + B v \tag {9-258}
$$

故复合系统动态方程为

$$
\left[ \begin{array}{l} \dot {\boldsymbol {x}} \\ \dot {\hat {\boldsymbol {x}}} \end{array} \right] = \left[ \begin{array}{c c} \boldsymbol {A} & - \boldsymbol {B K} \\ \boldsymbol {H C} & \boldsymbol {A} - \boldsymbol {B K} - \boldsymbol {H C} \end{array} \right] \left[ \begin{array}{l} \boldsymbol {x} \\ \hat {\boldsymbol {x}} \end{array} \right] + \left[ \begin{array}{l} \boldsymbol {B} \\ \boldsymbol {B} \end{array} \right] \boldsymbol {v} \tag {9-259a}
$$

$$
\mathbf {y} = \left[ \begin{array}{l l} \mathbf {C} & \mathbf {0} \end{array} \right] \left[ \begin{array}{l} \mathbf {x} \\ \hat {\mathbf {x}} \end{array} \right] \tag {9-259b}
$$

在复合系统动态方程中，不用状态估值 $\hat { x }$ ，而用状态误差 $( { \pmb x } - \hat { { \pmb x } } )$ ，将会使分析研究更加

直观方便。由式(9-257)和式(9-258)可得

$$
\dot {\boldsymbol {x}} - \dot {\hat {\boldsymbol {x}}} = (\boldsymbol {A} - \boldsymbol {H C}) (\boldsymbol {x} - \hat {\boldsymbol {x}}) \tag {9-260}
$$

该式与 $\pmb { u }$ ， $\nu$ 无关，即 $( { \pmb x } - \hat { { \pmb x } } )$ 是不可控的。不管施加什么样的控制信号，只要（AHC）全部特征值都具有负实部，状态误差总会衰减到零，这正是所希望的，是状态观测器所具有的重要性质。对式(9-259)引入非奇异线性变换

$$
\left[ \begin{array}{l} \boldsymbol {x} \\ \hat {\boldsymbol {x}} \end{array} \right] = \left[ \begin{array}{c c} \boldsymbol {I} _ {n} & \boldsymbol {0} \\ \boldsymbol {I} _ {n} & - \boldsymbol {I} _ {n} \end{array} \right] \left[ \begin{array}{l} \boldsymbol {x} \\ \boldsymbol {x} - \hat {\boldsymbol {x}} \end{array} \right] \tag {9-261}
$$

则有 $\left[ \begin{array} { c } { \dot { x } } \\ { \dot { x } - \dot { \hat { x } } } \end{array} \right] = \left[ \begin{array} { c c } { A - B K } & { B K } \\ { \mathbf { 0 } } & { A - H C } \end{array} \right] \left[ \begin{array} { c } { x } \\ { x - \hat { x } } \end{array} \right] + \left[ \begin{array} { c } { B } \\ { \mathbf { 0 } } \end{array} \right] \nu$ (9-262a)

$$
y = \left[ \begin{array}{l l} C & 0 \end{array} \right] \left[ \begin{array}{c} x \\ x - \hat {x} \end{array} \right] \tag {9-262b}
$$

由于线性变换后系统传递函数矩阵具有不变性，由式(9-262)可导出系统传递函数矩阵

$$
\boldsymbol {G} (s) = \left[ \begin{array}{l l} \boldsymbol {C} & \boldsymbol {0} \end{array} \right] \left[ \begin{array}{c c} s \boldsymbol {I} - (\boldsymbol {A} - \boldsymbol {B} \boldsymbol {K}) & - \boldsymbol {B} \boldsymbol {K} \\ \boldsymbol {0} & s \boldsymbol {I} - (\boldsymbol {A} - \boldsymbol {H} \boldsymbol {C}) \end{array} \right] ^ {- 1} \left[ \begin{array}{l} \boldsymbol {B} \\ \boldsymbol {0} \end{array} \right] \tag {9-263}
$$

利用分块矩阵求逆公式

$$
\left[ \begin{array}{c c} \boldsymbol {R} & \boldsymbol {S} \\ \boldsymbol {0} & \boldsymbol {T} \end{array} \right] ^ {- 1} = \left[ \begin{array}{c c} \boldsymbol {R} ^ {- 1} & - \boldsymbol {R} ^ {- 1} \boldsymbol {S} \boldsymbol {T} ^ {- 1} \\ \boldsymbol {0} & \boldsymbol {T} ^ {- 1} \end{array} \right] \tag {9-264}
$$

可得 $\pmb { G } ( s ) = \pmb { C } \left[ s \pmb { I } - \left( \pmb { A } - \pmb { B } \pmb { K } \right) \right] ^ { - 1 } \pmb { B }$ (9-265)

式(9-265)正是引入真实状态 $x$ 作为反馈的状态反馈系统

$$
\dot {\boldsymbol {x}} = \boldsymbol {A} \boldsymbol {x} + \boldsymbol {B} (\boldsymbol {v} - \boldsymbol {K} \boldsymbol {x}) = (\boldsymbol {A} - \boldsymbol {B} \boldsymbol {K}) \boldsymbol {x} + \boldsymbol {B} \boldsymbol {v}
$$

$$
y = C x \tag {9-266}
$$

的传递函数矩阵。这说明复合系统与状态反馈子系统具有相同的传递特性，与观测器部分无关，可用估值状态 $\hat { x }$ 代替真实状态 $x$ 作为反馈。 $2 n$ 维复合系统导出了 $n \times n$ 传递矩阵，这是由于 $( { \pmb x } - \hat { { \pmb x } } )$ 的不可控造成的。

由于线性变换后特征值具有不变性，由式(9-262)易导出其特征值满足关系式

$$
\left[ \begin{array}{c c} s \boldsymbol {I} - (\boldsymbol {A} - \boldsymbol {B K}) & - \boldsymbol {B K} \\ \boldsymbol {0} & s \boldsymbol {I} - (\boldsymbol {A} - \boldsymbol {H C}) \end{array} \right] = | s \boldsymbol {I} - (\boldsymbol {A} - \boldsymbol {B K}) | \cdot | s \boldsymbol {I} - (\boldsymbol {A} - \boldsymbol {H C}) | \tag {9-267}
$$

该式表明复合系统特征值是由状态反馈子系统和全维状态观测器的特征值组合而成，且两部分特征值相互独立，彼此不受影响，因而状态反馈矩阵 $\pmb { K }$ 和输出反馈矩阵 $\pmb { H }$ 可根据各自的要求来独立进行设计，故有下述分离定理。

定理 9-14(分离定理) 若被控系统(A，B，C)可控可观测，用状态观测器估值形成状态反馈时，其系统的极点配置和观测器设计可分别独立进行，即 $\pmb { K }$ 和 $\pmb { H }$ 阵的设计可分别独立进行。

# 9-5 控制系统状态空间设计

例 9-27 内模控制器。

在许多实际场合，单纯的状态变量反馈方法并不是一种改善系统性能的实用方法。其主要原因是，状态变量反馈往往要求用具有无限带宽的 PD 控制器或 PID 控制器来实现，但实际部件和控制器都只有有限的带宽。

内模控制器是另一类校正控制器，能以零稳态误差渐近跟踪各类参考输入信号，如阶跃信号、斜坡信号及正弦信号等。众所周知，在经典控制理论中，对于阶跃输入信号，$I$ 型系统可以实现零稳态误差跟踪。如果在校正控制器中引入参考输入的内模，则可以在状态空间设计法中推广这一结论。采用类似的内模控制器方法，可以在更多的情况下实现零稳态误差跟踪。

设单输入-单输出系统的状态空间表达式为

$$
\dot {\boldsymbol {x}} (t) = \boldsymbol {A} \boldsymbol {x} (t) + \boldsymbol {b} u (t), \quad y (t) = \boldsymbol {c x} (t) \tag {9-268}
$$

式中， $\pmb { x } \in \mathbf { R } ^ { n }$ 为状态向量； $u$ 为标量输入； $y$ 为标量输出； $\pmb { A }$ ， $\pmb { b }$ 和 $c$ 维数适当。

生成参考输入信号 $r ( t )$ 的线性系统为

$$
\dot {\boldsymbol {x}} _ {r} (t) = \boldsymbol {A} _ {r} \boldsymbol {x} _ {r} (t), \quad r (t) = \boldsymbol {d} _ {r} \boldsymbol {x} _ {r} (t) \tag {9-269}
$$

其中，初始条件未知。此外，参考输入信号 $r ( t )$ 的生成系统也可以等效为

$$
r ^ {(n)} (t) = \alpha_ {n - 1} r ^ {(n - 1)} (t) + \alpha_ {n - 2} r ^ {(n - 2)} (t) + \dots + \alpha_ {1} \dot {r} (t) + \alpha_ {0} r (t) \tag {9-270}
$$

首先考虑参考输入 $r ( t )$ 为单位阶跃信号时的内模控制器设计。此时， $r ( t )$ 可由下列方程生成：

$$
\dot {x} _ {r} (t) = 0, \quad r (t) = x _ {r} (t)
$$

或等价为

$$
\dot {r} (t) = 0
$$

定义跟踪误差

$$
e (t) = r (t) - y (t)
$$

于是有 $\dot { e } ( t ) = - \dot { y } ( t ) = - c \dot { x } ( t )$ (9-271)

现在，引入两个中间变量 $z ( t )$ 和 $w ( t )$ ，定义为

$$
\boldsymbol {z} (t) = \dot {\boldsymbol {x}} (t), \quad w (t) = \dot {u} (t)
$$

故有 ${ \dot { z } } ( t ) = { \ddot { x } } ( t ) = A { \dot { x } } ( t ) + b { \dot { u } } ( t ) = A z ( t ) + b w ( t )$ (9-272)

则式(9-271)与式(9-272)构成如下增广系统方程：

$$
\left[ \begin{array}{l} \dot {e} \\ \dot {z} \end{array} \right] = \left[ \begin{array}{l l} 0 & - \boldsymbol {c c} \\ 0 & \boldsymbol {A} \end{array} \right] \left[ \begin{array}{l} e \\ z \end{array} \right] + \left[ \begin{array}{l} 0 \\ \boldsymbol {b} \end{array} \right] w \tag {9-273}
$$

当增广系统(9-273)可控时，即有

$$
\operatorname {r a n k} \left[ \begin{array}{c c c c c} 0 & - c b & - c A b & \dots & - c A ^ {n - 1} b \\ b & A b & A ^ {2} b & \dots & A ^ {n} b \end{array} \right] = n + 1 \tag {9-274}
$$

总可以找到反馈信号

![](images/55d93097b316ccbb84034c3c2ca5063f0fe9e61ea39621c3077b26392cc12034.jpg)  
综合应用

$$
w (t) = - k _ {1} e (t) - k _ {2} z (t) \tag {9-275}
$$

使该系统渐近稳定。这表明跟踪误差 $e ( t )$ 是渐近收敛的，因此系统输出能以零稳态误差跟踪参考输入信号。对式(9-275)求积分，可得系统内部的反馈控制信号为

$$
u (t) = - k _ {1} \int_ {0} ^ {t} e (\tau) \mathrm {d} \tau - \boldsymbol {k} _ {2} \boldsymbol {x} (t) \tag {9-276}
$$

与此对应的系统结构图如图 9-29所示。由图可见，在校正控制器中，除包含有状态变量

![](images/c6a6fd60c7538a0a9a7fd87086dd64c7d5db482dd67ba046115253f9ae33cfda.jpg)  
图 9-29 阶跃输入的内模设计系统结构图

反馈外，还包含了参考阶跃输入的内模(图中积分器环节)，故称为内模控制器。

下例为一个具体系统的单位阶跃输入内模控制器的设计过程。设有

$$
\dot {\boldsymbol {x}} (t) = \left[ \begin{array}{l l} 0 & 1 \\ - 2 & - 2 \end{array} \right] \boldsymbol {x} (t) + \left[ \begin{array}{l} 1 \\ 2 \end{array} \right] u (t)
$$

$$
y (t) = \left[ \begin{array}{c c} 1 & 0 \end{array} \right] x (t)
$$

要求系统输出能以零稳态误差跟踪单位阶跃参考输入信号。由式(9-273)知，增广系统方程为

$$
\left[ \begin{array}{l} \dot {e} \\ \dot {z} \end{array} \right] = \left[ \begin{array}{c c c} 0 & - 1 & 0 \\ 0 & 0 & 1 \\ 0 & - 2 & - 2 \end{array} \right] \left[ \begin{array}{l} e \\ z \end{array} \right] + \left[ \begin{array}{l} 0 \\ 1 \\ 2 \end{array} \right] w
$$

由于可控性矩阵

$$
\operatorname {r a n k} \left[ \begin{array}{l l l} 0 & - c b & - c A b \\ b & A b & A ^ {2} b \end{array} \right] = \operatorname {r a n k} \left[ \begin{array}{l l l} 0 & - 1 & - 2 \\ 1 & 2 & - 6 \\ 2 & - 6 & 8 \end{array} \right] = 3
$$

满秩，增广系统可控，故通过状态反馈

$$
w = - \boldsymbol {k} \left[ \begin{array}{l} e \\ z \end{array} \right] = - k _ {1} e - k _ {2} z _ {1} - k _ {3} z _ {2}
$$

式中 $\pmb { k } = [ k _ { 1 } k _ { 2 } k _ { 3 } ]$ ，可任意配置闭环增广系统

$$
\left[ \begin{array}{l} \dot {e} \\ \dot {z} _ {1} \\ \dot {z} _ {2} \end{array} \right] = \left\{\left[ \begin{array}{r r r} 0 & - 1 & 0 \\ 0 & 0 & 1 \\ 0 & - 2 & - 2 \end{array} \right] - \left[ \begin{array}{l} 0 \\ 1 \\ 2 \end{array} \right] \left[ \begin{array}{l l l} k _ {1} & k _ {2} & k _ {3} \end{array} \right] \right\} \left[ \begin{array}{l} e \\ z _ {1} \\ z _ {2} \end{array} \right]
$$

的极点。如果要求闭环极点为 $s _ { 1 , 2 } { = } _ { - 1 \pm \mathrm { j } }$ ， ${ \cal S } 3 ^ { = } - 1 0$ ，则希望特征方程为

$$
(s + 1 + j) (s + 1 - j) (s + 1 0) = s ^ {3} + 1 2 s ^ {2} + 2 2 s + 2 0 = 0
$$

而实际特征方程为

$$
\det  \left[ \begin{array}{c c c} s & 1 & 0 \\ k _ {1} & s + k _ {2} & k _ {3} - 1 \\ 2 k _ {1} & 2 (1 + k _ {2}) & s + 2 + 2 k _ {3} \end{array} \right] = s ^ {3} + (k _ {2} + 2 k _ {3} + 2) s ^ {2} + (2 - k _ {1} + 4 k _ {2} - 2 k _ {3}) s - 4 k _ {1} = 0
$$

令上述两个特征方程式的对应项系数相等，解得

$$
k _ {1} = - 5, \quad k _ {2} = 5, \quad k _ {3} = 2. 5
$$

则由式(9-276)得内模控制律为

$$
u (t) = 5 \int_ {0} ^ {t} e (\tau) \mathrm {d} \tau - 5 x _ {1} (t) - 2. 5 x _ {2} (t)
$$

相应的单位阶跃输入内模控制系统的结构图如图 9-30 所示。

![](images/333538743793c3d1922aa6a20f7fbc6a1f7f7a54a42b972053407abfaa48e0ed.jpg)  
图 9-30 单位阶跃输入内模控制系统结构图

显然，本例设计的内模控制系统是渐近稳定的。对任意初始跟踪误差 $e ( 0 )$ ，反馈控制信号都可以保证在 $t \to \infty$ 时， $e ( t ) \to 0$ 。在 MATLAB 的 Simulink 环境下，根据结构图 9-30 搭建内模控制系统模型，运行后可得图 9-31，其直观地表明了系统在单位阶跃参考输入时，跟踪误差的渐近收敛性。

![](images/be3b9fcc3805f6d5afc8133267bf8aa713fdd80915ca7247fe0b3bd4497f3c5d.jpg)  
图 9-31 单位阶跃输入下内模控制系统的跟踪误差响应(MATLAB)

考虑参考输入为斜坡信号的内模设计问题。设单位斜坡参考输入信号为 $r ( t ) { = } t$ ，并由下列系统生成：

$$
\dot {\boldsymbol {x}} _ {r} = \boldsymbol {A} _ {r} \boldsymbol {x} _ {r} = \left[ \begin{array}{l l} 0 & 1 \\ 0 & 0 \end{array} \right] \boldsymbol {x} _ {r}
$$

$$
r = \boldsymbol {d} _ {r} \boldsymbol {x} _ {r} = \left[ \begin{array}{c c} 1 & 0 \end{array} \right] \boldsymbol {x} _ {r}
$$

且有 $\ddot { r } ( t ) = 0$ ，则对于单输入-单输出系统(9-268)，定义跟踪误差 $e { = } r { - } y$ ，有

$$
\ddot {e} (t) = - \ddot {y} (t) = - c \dot {x} (t)
$$

令中间变量

$$
\boldsymbol {z} = \ddot {\boldsymbol {x}}, \quad \boldsymbol {w} = \ddot {\boldsymbol {u}}
$$

有 $z = { \ddot { x } } = A { \dot { x } } + b { \dot { u } }$

$$
\dot {z} = A \ddot {x} + b \ddot {u} = A z + b w
$$

$$
\ddot {e} = - \dot {y} = - c \ddot {x} = - c z
$$

构造增广系统

$$
\left[ \begin{array}{l} \dot {e} \\ \ddot {e} \\ \dot {z} \end{array} \right] = \left[ \begin{array}{l l l} 0 & 1 & 0 \\ 0 & 0 & - c \\ 0 & 0 & A \end{array} \right] \left[ \begin{array}{l} e \\ \dot {e} \\ z \end{array} \right] + \left[ \begin{array}{l} 0 \\ 0 \\ b \end{array} \right] w \tag {9-277}
$$

若系统(9-277)可控，即

$$
\operatorname {r a n k} \left[ \begin{array}{c c c c} 0 & 0 & - c b & - c A b \\ 0 & - c b & - c A b & - c A ^ {2} b \\ b & A b & A ^ {2} b & A ^ {3} b \end{array} \right] = n + 2
$$

则存在状态反馈

$$
w = - \left[ \begin{array}{l l l} k _ {1} & k _ {2} & \boldsymbol {k} _ {3} \end{array} \right] \left[ \begin{array}{l} e \\ \dot {e} \\ z \end{array} \right] = - k _ {1} e - k _ {2} \dot {e} - \boldsymbol {k} _ {3} z \tag {9-278}
$$

使增广闭环系统

$$
\begin{array}{l} \left[ \begin{array}{l} \dot {e} \\ \ddot {e} \\ \dot {z} \end{array} \right] = \left\{\left[ \begin{array}{c c c} 0 & 1 & 0 \\ 0 & 0 & - \boldsymbol {c} \\ 0 & 0 & \boldsymbol {A} \end{array} \right] - \left[ \begin{array}{l} 0 \\ 0 \\ \boldsymbol {b} \end{array} \right] \left[ \begin{array}{c c c} k _ {1} & k _ {2} & k _ {3} \end{array} \right] \right\} \left[ \begin{array}{l} e \\ \dot {e} \\ z \end{array} \right] \\ = \left[ \begin{array}{c c c} 0 & 1 & 0 \\ 0 & 0 & - \boldsymbol {c} \\ - k _ {1} \boldsymbol {b} & - k _ {2} \boldsymbol {b} & \boldsymbol {A} - \boldsymbol {b} \boldsymbol {k} _ {3} \end{array} \right] \left[ \begin{array}{l} e \\ \dot {e} \\ z \end{array} \right] \\ \end{array}
$$

渐近稳定。其中， $k _ { 1 }$ ， $k _ { 2 }$ 和 $k _ { 3 }$ 可由要求的闭环增广系统(9-278)的极点位置来确定。这样，当 $t \to \infty$ 时，必有 $e ( t ) \to 0$ 。

对式(9-278)作二次积分，可得含有输入内模信息的反馈控制信号

$$
u (t) = - k _ {1} \int_ {0} ^ {t} \int_ {0} ^ {t} e (\tau) \mathrm {d} \tau \mathrm {d} \tau - k _ {2} \int_ {0} ^ {t} e (\tau) \mathrm {d} \tau - k _ {3} x (t)
$$

斜坡输入的内模设计系统框图如图 9-32 所示。

由图9-32可见，虚框表示的控制器中含有两个积分器，这正是斜坡输入的内模形式。类似地，可以将内模方法推广到处理其他参考输入形式。此外，如果将扰动信号的生成模型也纳入校正控制器中，还可以通过扰动内模设计来克服持续扰动对系统性能的影响，请参见本章习题。

![](images/b8833ae2a79308e71bc3e9dc99e4f7811fd1a446e4a8a378ec8a149f37446756.jpg)  
图 9-32 斜坡输入的内模设计系统框图

例 9-28 打印机皮带驱动器。

在计算机外围设备中，常用的低价位打印机都配有皮带驱动器，用于驱动打印头沿打印页面横向移动。打印头可能是喷墨式或针式的。图9-33是一个装有直流电机的皮带驱动式打印机，其光传感器用来测定打印头的位置，皮带张力变化用于调节皮带的实际弹性状态。

![](images/058b31d0bb392dd23659bd23a1c88a10d77de2211765aa69acb43264266e5a00.jpg)  
图 9-33 打印机皮带驱动系统

设计要求：

1) 建立系统的状态空间模型，选择合适的电机参数、滑轮参数和控制器参数；  
2) 研究皮带弹性系数 $k$ 对打印机抗外界扰动性能的影响。

解 1) 状态空间建模及系统参数选择。图9-34为打印机皮带驱动器的基本模型。模型中记皮带弹性系数为 $k$ ，滑轮半径为 $r$ ，电机轴转角为 $\theta$ ，右滑轮的转角为 $\theta _ { p }$ ，打印头质量为 $m$ ，打印头位移为 $y ( t )$ 。光传感器用来测量 $y ( t )$ ，光传感器的输出电压为 $\nu _ { 1 }$ ，且 $\nu _ { 1 } { = } k _ { 1 } y$ 。控制器输出电压为 $\nu _ { 2 }$ ，对系统进行速度反馈，即有 $\nu _ { 2 } = - k _ { 2 } \frac { \mathrm { d } \nu _ { 1 } } { \mathrm { d } t }$ 。

系统参数取值情况如表 9-2 所示。

表 9-2 打印装置的参数  

<table><tr><td>质量</td><td>m=0.2kg</td></tr><tr><td>光传感器</td><td>k1=1V/m</td></tr><tr><td>滑轮半径</td><td>r=0.015m</td></tr><tr><td colspan="2">电机</td></tr><tr><td>电感</td><td>L≈0</td></tr><tr><td>电机和滑轮的摩擦系数</td><td>f=0.25N·m·s</td></tr><tr><td>电枢电阻</td><td>R=2Ω</td></tr><tr><td>电机传递系数</td><td>Km=2kg·m/A</td></tr><tr><td>电机和滑轮的转动惯量</td><td>J电机+J滑轮 = J=0.01kg·m²</td></tr></table>

![](images/7829b938d0892b56060e3385c7c24f65a564bc9625d820d8509786c21cdd5d33.jpg)  
图 9-34 打印机皮带驱动模型

下面推导系统的运动方程。注意到 $y = r \theta _ { p }$ ，可知皮带张力 $T _ { 1 }$ 和 $T _ { 2 }$ 分别为

$$
T _ {1} = k (r \theta - r \theta_ {p}) = k (r \theta - y), \quad T _ {2} = k (y - r \theta)
$$

式中， $k$ 为皮带弹性系数。于是，作用在质量 $m$ 上的皮带净张力为

$$
T _ {1} - T _ {2} = 2 k (r \theta - y) = 2 k x _ {1}
$$

其中， $x _ { 1 } = r \theta - y$ 为第一个状态变量，表示打印头实际位移 $y$ 与预期位移 $r \theta$ 之间的位移差。显然，质量 $m$ 的运动方程为

$$
m \frac {\mathrm {d} ^ {2} y}{\mathrm {d} t ^ {2}} = T _ {1} - T _ {2} = 2 k x _ {1}
$$

取第二个状态变量为 $x _ { 2 } = { \frac { \mathrm { d } y } { \mathrm { d } t } }$ ，于是有

$$
\frac {\mathrm {d} x _ {2}}{\mathrm {d} t} = \frac {2 k}{m} x _ {1} \tag {9-280}
$$

定义第三个状态变量为 $x _ { 3 } = { \frac { \mathrm { d } \theta } { \mathrm { d } t } }$ ，则 $x _ { 1 }$ 的导数

$$
\frac {\mathrm {d} x _ {1}}{\mathrm {d} t} = r \frac {\mathrm {d} \theta}{\mathrm {d} t} - \frac {\mathrm {d} y}{\mathrm {d} t} = - x _ {2} + r x _ {3} \tag {9-281}
$$

接着，推导电机旋转的运动方程：当 $L { = } 0$ 时，电机电枢电流 $i = \frac { \nu _ { 2 } } { R }$ ，而电机转矩为

$M _ { m } { = } K _ { m } i$ ，于是有

$$
M _ {m} = \frac {K _ {m}}{R} v _ {2} \tag {9-282}
$$

设作用在驱动皮带上的扰动转矩为 $M _ { d }$ ，则电机驱动皮带的有效转矩为 $\scriptstyle { M = M _ { m } - M _ { d \circ } }$ 显然，只有有效转矩驱动电机轴带动滑轮运动，因此有

$$
M = J \frac {\mathrm {d} ^ {2} \theta}{\mathrm {d} t ^ {2}} + f \frac {\mathrm {d} \theta}{\mathrm {d} t} + r \left(T _ {1} - T _ {2}\right)
$$

由于 $\frac { \mathrm { d } x _ { 3 } } { \mathrm { d } t } { = } \frac { \mathrm { d } ^ { 2 } \theta } { \mathrm { d } t ^ { 2 } } , \qquad T _ { 1 } - T _ { 2 } = 2 k x _ { 1 }$

故得 $\frac { \mathrm { d } x _ { 3 } } { \mathrm { d } t } { = } \frac { M _ { m } - M _ { d } } { J } { - } \frac { f } { J } x _ { 3 } { - } \frac { 2 k r } { J } x _ { 1 }$

在上式中，代入式(9-282)以及

$$
v _ {2} = - k _ {2} \frac {\mathrm {d} v _ {1}}{\mathrm {d} t}
$$

$$
v _ {1} = k _ {1} y, \quad x _ {2} = \frac {\mathrm {d} y}{\mathrm {d} t}
$$

得到 $\frac { M _ { m } } { J } = \frac { K _ { m } } { R J } \nu _ { 2 } = - \frac { K _ { m } k _ { 2 } } { R J } \frac { \mathrm { d } \nu _ { 1 } } { \mathrm { d } t } = - \frac { K _ { m } k _ { 1 } k _ { 2 } } { R J } x _ { 2 }$ Mm 2 x

最后可得 $\frac { \mathrm { d } x _ { 3 } } { \mathrm { d } t } = - \frac { 2 k r } { J } x _ { 1 } - \frac { K _ { m } k _ { 1 } k _ { 2 } } { R J } x _ { 2 } - \frac { f } { J } x _ { 3 } - \frac { M _ { d } } { J }$ dx d M (9-283)

式(9-280)、式(9-281)及式(9-283)构成了描述打印机皮带驱动系统的一阶运动微分方程组，其向量-矩阵形式为

$$
\dot {\boldsymbol {x}} = \left[ \begin{array}{c c c} 0 & - 1 & r \\ \frac {2 k}{m} & 0 & 0 \\ - \frac {2 k r}{J} & - \frac {K _ {m} k _ {1} k _ {2}}{R J} & - \frac {f}{J} \end{array} \right] \boldsymbol {x} + \left[ \begin{array}{c} 0 \\ 0 \\ - \frac {1}{J} \end{array} \right] M _ {d} \tag {9-284}
$$

式(9-284)的信号流图如图 9-35 所示，图中还表示了扰动力矩 $M _ { d }$ 的节点。

![](images/bd873b50ce5c3d5d908286aa4d8338998c90e09bf6d90567eb6442769e7549ae.jpg)  
图 9-35 打印机皮带驱动系统的信号流图

2) 皮带弹性系数的影响。为了研究如何抑制 $M _ { d }$ 对系统性能的影响，可由图 9-35 确定传递函数 $X _ { 1 } ( s ) / M _ { d } ( s )$ 。利用梅森增益公式，可得

$$
\frac {X _ {1} (s)}{M _ {d} (s)} = \frac {- \frac {r}{J} s ^ {- 2}}{1 - \left(L _ {1} + L _ {2} + L _ {3} + L _ {4}\right) + L _ {1} L _ {2}}
$$

其中回路增益

$$
L _ {1} = - \frac {f}{J} s ^ {- 1}, \quad L _ {2} = - \frac {2 k}{m} s ^ {- 2}
$$

$$
L _ {3} = - \frac {2 k r ^ {2}}{J} s ^ {- 2}, \quad L _ {4} = - \frac {2 k k _ {1} k _ {2} K _ {m} r}{m R J} s ^ {- 3}
$$

因而有

$$
\frac {X _ {1} (s)}{M _ {d} (s)} = \frac {- \left(\frac {r}{J}\right) s}{s ^ {3} + \left(\frac {f}{J}\right) s ^ {2} + \left(\frac {2 k}{m} + \frac {2 k r ^ {2}}{J}\right) s + \left(\frac {2 k f}{m J} + \frac {2 k K _ {m} k _ {1} k _ {2} r}{m R J}\right)}
$$

代入表 9-2 所示参数值，得

$$
\frac {X _ {1} (s)}{M _ {d} (s)} = \frac {- 1 . 5 s}{s ^ {3} + 2 5 s ^ {2} + 1 0 . 0 5 k s + k \left(2 5 0 + 1 5 k _ {2}\right)}
$$

为了抑制 $M _ { d }$ 对打印头位移差 $x _ { 1 } = r \theta - y$ 的影响，需要选择合适的皮带弹性系数 $k$ 和速度反馈系数 $k _ { 2 }$ 。令 $M _ { d } ( s ) = \frac { 1 } { s }$ ，有

$$
X _ {1} (s) = \frac {- 1 . 5}{s ^ {3} + 2 5 s ^ {2} + 1 0 . 0 5 k s + k \left(2 5 0 + 1 5 k _ {2}\right)}
$$

显然， $k$ 与 $k _ { 2 }$ 的选择应首先保证闭环系统的稳定性。系统的闭环特征方程为

$$
s ^ {3} + 2 5 s ^ {2} + 1 0. 0 5 k s + k \left(2 5 0 + 1 5 k _ {2}\right) = 0
$$

列劳斯表如下：

$$
\begin{array}{c c} s ^ {3} & 1 \\ s ^ {2} & 2 5 \\ s ^ {1} & \frac {2 5 \times 1 0 . 0 5 k - k (2 5 0 + 1 5 k _ {2})}{2 5} \\ s ^ {0} & k (2 5 0 + 1 5 k _ {2}) \end{array} \quad 0
$$

由劳斯判据知，使闭环系统稳定的充分必要条件为

$$
2 5 \times 1 0. 0 5 k - k (2 5 0 + 1 5 k _ {2}) > 0
$$

以及 $k ( 2 5 0 + 1 5 k _ { 2 } ) > 0$

整理得 $k > 0 , \qquad 0 < k _ { 2 } < 0 . 0 8 3 3$

在系统稳定的前提下，由终值定理可知，打印头稳态位移差

$$
\lim  _ {t \rightarrow \infty} x _ {1} (t) = \lim  _ {s \rightarrow 0} s X _ {1} (s) = 0
$$

打印头在运动过程中受单位阶跃扰动力矩作用下的动态特性，取决于皮带弹性系数 $k$ 和速度反馈系数 $k _ { 2 }$ 的选取。通常， $k$ 在 $1 \sim 4 0$ 范围内取值， $k _ { 2 } { < } 1$ 。一组合适的取值为 $k { = } 2 0$ 和 $k _ { 2 } { = } 0 . 0 8$ ，此时

$$
X _ {1} (s) = \frac {- 1 . 5}{s ^ {3} + 2 5 s ^ {2} + 2 0 1 s + 5 0 2 4} = \frac {- 1 . 5}{(s + 2 5) (s ^ {2} + 2 0 1)}
$$

对上式进行部分分式分解，有

$$
X _ {1} (s) = \frac {A _ {1}}{s + 2 5} + \frac {A _ {2} s + A _ {3}}{s ^ {2} + 2 0 1}
$$

其中， $A _ { 1 } = - 0 . 0 0 1 8$ ， $A _ { 2 } { = } 0 . 0 0 1 8$ ， $A _ { 3 } { = } - 0 . 0 4 5$ 。由于留数 $A _ { 1 }$ 和 $A _ { 2 }$ 比 $A _ { 3 }$ 小得多，其影响可略，故

$$
X _ {1} (s) \approx \frac {- 0 . 0 4 5}{s ^ {2} + 2 0 1}
$$

查本书附录 A，可得

$$
x _ {1} (t) \approx - 3. 1 7 \times 1 0 ^ {- 3} \sin (1 4. 1 8 t)
$$

其动态响应如图 9-36所示。由图可见，该系统可将外来阶跃扰动的影响抑制到相当微弱的程度，实现了预期的设计目标。

![](images/d564e5c832d6cc4754aeabf5069fa1b3f9818b6f27b3fc28c577597be2e1a319.jpg)  
图 9-36 打印头位移差 $x _ { 1 } ( t )$ 对阶跃扰动的响应 $k { = } 2 0$ ，MATLAB)

MATLAB 程序如下：

$\mathrm{k = 20}$ . $\mathrm{k}2 = 0.08$ num $= [-1.50]$ den $= [12510.05*\mathrm{k}\mathrm{k}*(250 + 15*\mathrm{k}2)]$ sys=tf(num,den); $t = 0$ ..0.01:3;   
step(sys,t); grid

例 9-29 自动检测系统。

电气开关面板上有各种开关、继电器和指示灯，若采用手工方式检测，会降低产量并造成较大的检验误差。图 9-37 是一个自动检测系统示意图，该系统通过直流电机来驱动一组探针，使探针穿过零件的引线，以便检测零件的导通性能、电阻及其他功能参数。

![](images/b979e34e5b64bb7c4797be70fd08aed2dfeb33ff9cfa42ae1b61040c860de1b1.jpg)  
图 9-37 自动检测系统示意图

该自动检测系统利用直流电机上的编码器来测量电压和探针的位置，如图9-38所示。其结构图模型如图 9-39所示，其中 $K _ { a }$ 为所需要的功率放大系数。

![](images/456e99d12a6619387b36e1588bee33882ad38a00c1e0cffec701f27e9ce7fc39.jpg)  
图 9-38 装有编码轮盘的直流电机示意图

![](images/dd8bb26cd7666c6311a1dfa68c89a56b5b9eff200867e314f5969a0467d0da59.jpg)  
图 9-39 直流电机结构图模型

设状态变量选择为： $x _ { \mathrm { 1 } } = \theta$ , $x _ { 2 } = \mathrm { d } \theta / \mathrm { d } t$ , $x _ { 3 } = i _ { f }$ ；假定这些状态变量均可测，且能用于反馈。图 9-40 所示为其闭环系统，其中控制律

$$
u = - K _ {1} x _ {1} - K _ {2} x _ {2} - K _ {3} x _ {3}
$$

本例的设计目标是：合理选择放大器增益 $K _ { a }$ 和状态反馈增益 $K _ { 1 }$ ， $K _ { 2 }$ 和 $K _ { 3 }$ ，使系统单位阶跃响应的调节时间小于 $2 s ( A { = } 2 \% )$ ，超调量小于 $4 \%$ 。

解 首先列写系统的状态方程。由图 9-40 可见，当系统状态反馈未接入时，有

$$
\dot {\boldsymbol {x}} (t) = \boldsymbol {A} \boldsymbol {x} (t) + \boldsymbol {b} u (t) = \left[ \begin{array}{c c c} 0 & 1 & 0 \\ 0 & - 1 & 1 \\ 0 & 0 & - 5 \end{array} \right] \boldsymbol {x} + \left[ \begin{array}{c} 0 \\ 0 \\ K _ {a} \end{array} \right] u
$$

当系统接入状态反馈控制律，并令 $K _ { 1 } { = } 1$ 时，得闭环系统方程为

$$
\dot {\boldsymbol {x}} (t) = \left[ \begin{array}{c c c} 0 & 1 & 0 \\ 0 & - 1 & 1 \\ - K _ {a} & - K _ {a} K _ {2} & - \left(5 + K _ {a} K _ {3}\right) \end{array} \right] \boldsymbol {x} (t) = \overline {{\boldsymbol {A}}} \boldsymbol {x} (t)
$$

![](images/31a721436699b4971b1e55069384aaf7889b54b9921f97eb1e971655557e512d.jpg)  
图 9-40 自动检测反馈控制系统信号流图

令 $\operatorname* { d e t } ( s I - { \overline { { A } } } ) = 0$ ，得闭环系统特征方程

$$
s ^ {3} + \left(6 + K _ {a} K _ {3}\right) s ^ {2} + \left[ 5 + K _ {a} \left(K _ {2} + K _ {3}\right) \right] s + K _ {a} = 0
$$

上式可写为

$$
s (s + 1) (s + 5) + K _ {a} K _ {3} \left(s ^ {2} + \frac {K _ {2} + K _ {3}}{K _ {3}} s + \frac {1}{K _ {3}}\right) = 0
$$

其等效闭环特征方程为

$$
1 + K _ {a} K _ {3} \frac {s ^ {2} + \frac {K _ {2} + K _ {3}}{K _ {3}} s + \frac {1}{K _ {3}}}{s (s + 1) (s + 5)} = 0
$$

以 $K _ { a } K _ { 3 }$ 为可变参数，绘制等效系统的根轨迹图，并适当选择待定参数，使系统性能满足设计指标。

根据给定的性能指标要求，应有

$$
\sigma \% \cong 100\mathrm{e}^{-\pi \zeta /\sqrt{1 - \zeta^2}}\% <   4\%
$$

$$
t _ {s} \cong \frac {4 . 4}{\zeta \omega_ {n}} <   2 \quad (\Delta = 2 \%)
$$

故可求得 $\zeta > 0 . 7 2 , \quad \varpi _ { n } > 3 . 1$

则系统希望主导极点在复平面上的有效取值区域，如图 9-41(a)中阴影线区域所示。

![](images/17cf7ffb9cf13294fa787e4238c7bcef1a1054fdbae9cb3f6e0dc4eb6a8fce54.jpg)  
图 9-41 自动检测系统设计(MATLAB)

(a)自动检测系统的根轨迹

$$
\mathrm {n u m} = [ 1 \quad 8 \quad 2 0 ]; \mathrm {d e n} = [ 1 \quad 6 \quad 5 \quad 0 ];
$$

$$
\begin{array}{l} \text {r l o c u s (n u m , d e n) ; h o l d o n} \end{array}
$$

%显示稳定性区域

$$
z e t a = 0. 7 2, w n = 3. 1;
$$

$$
x = - 1 0: 0. 1: - z e t a ^ {*} w n; y = - (s q r t (1 - z e t a \wedge 2) / z e t a) ^ {*} x;
$$

$$
x c = - 1 0: 0. 1: - z e t a ^ {*} w n; c = s q r t (w n ^ {\wedge} 2 - x c. ^ {\wedge} 2);
$$

$$
\operatorname {p l o t} (x, y, ^ {\prime \prime}; x, - y, ^ {\prime \prime}; x c, ^ {\prime \prime}; x c, - c, ^ {\prime \prime})
$$

$$
\operatorname {a x i s t} \left(\left[ - 1 0 \quad 1 \quad - 1 0 \quad 1 0 \right]\right);
$$

为了把根轨迹拉向图9-41(a)所示阴影线区域，将等效系统的开环零点取为 $s = - 4 \pm \mathrm { j } 2$ (位于阴影线区域内)，且令

$$
s ^ {2} + \frac {K _ {2} + K _ {3}}{K _ {3}} s + \frac {1}{K _ {3}} = (s + 4 + j 2) (s + 4 - j 2) = s ^ {2} + 8 s + 2 0
$$

即有 $\frac { K _ { _ { 2 } } + K _ { _ { 3 } } } { K _ { _ { 3 } } } = 8 , \frac { 1 } { K _ { _ { 3 } } } = 2 0$ 2 3 8,K K 

解出 $K _ { _ 2 } = 0 . 3 5 , \quad K _ { _ 3 } = 0 . 0 5$

运行图 9-41(b)所示 MATLAB 程序，可以画出以 $K _ { a } K _ { 3 }$ 为可变参数的根轨迹图，如图 9-41(a)所示。由图可见，当取根轨迹增益 $K _ { a } K _ { 3 } { = } 1 2$ 时，闭环极点位于有效取值区域之内。从而满足设计指标要求。本例最终设计结果为： $K _ { a } \mathrm { = } 2 4 0 . 0 0 , K _ { 1 } \mathrm { = } 1 . 0 0 , K _ { 2 } \mathrm { = } 0 . 3 5 , K _ { 3 } \mathrm { = } 0 . 0 5$ $K _ { 1 } { = } 1 . 0 0$ $K _ { 2 } { = } 0 . 3 5$ 。

最后，校验设计参数，系统的单位阶跃响应曲线如图 9-42所示。由图得，设计后系统的 $\sigma \% = 2 \% , t _ { s } = 0 . 8 8 \mathrm { s } ( A { = } 2 \% )$ ，系统确实满足了设计要求。

MATLAB 程序如下：

$\mathrm { K a } { = } 2 4 0$ ； $\mathrm { K } 1 { = } 1$ ； ${ \mathrm { K } } 2 { = } 0 . 3 5$ ； ${ \mathrm { K } } 3 { = } 0 . 0 5$ ；

$\mathbf { A } { = } \left[ 0 1 0 \right.$ ；0 -1 1；-Ka -Ka*K2 -5-Ka*K3］；

$\mathrm { \ b } { = } \left[ \mathrm { \ } 0 \mathrm { \ } 0 \mathrm { \ K a } \right]$ ；

$\mathrm { c } = \left[ \mathrm { ~ 1 ~ 0 ~ 0 ~ } \right]$

$\mathrm { d } { = } 0$ ；

sys=ss(A，b，c，d)；

t=0：0.01：3；

step(sys，t)；grid

![](images/b058efc49e158ca4db47744545552405369504a6b778ec81475b9c82e4c09139.jpg)  
图 9-42 自动检测系统的单位阶跃响应(MATLAB)

例 9-30 磁盘驱动读取系统(续)。

现代磁盘在每厘米宽度内有 5000 个磁道，每个磁道的典型宽度仅为 $1 \mu \mathrm { m }$ ，因此磁盘驱动读取系统对磁头的定位精度和磁头在磁道间移动的动态过程有严格的要求。

当不考虑磁场电感影响时，磁头控制系统的二阶开环模型如图 9-43 所示，采用状态反馈控制器后的闭环系统如图 9-44所示。设计要求：

1) 选择放大器增益 $K _ { a }$ 和反馈系数 $K _ { 2 }$ ，使系统二阶模型响应满足表 9-3 所示性能指标要求；

![](images/012782b153b3b221dbb40f48d9bd23b6565779e37b30c362e9943e99b93e931e.jpg)  
图 9-43 磁头控制系统的二阶开环模型

![](images/b282ac064fc317ade6e628d57c71a9f421df4b863e23ec615b5efbeb6cdb682b.jpg)  
图 9-44 具有两条状态变量反馈回路的闭环系统信号流图

2) 若考虑磁场电感的影响，且设电感 $L$ 为 $1 \mathrm { m H }$ ，则磁盘驱动读取系统中的电机传递函数为

$$
G _ {1} (s) = \frac {5 0 0 0}{s + 1 0 0 0}
$$

要求采用系统的三阶模型检验系统采用二阶模型时的设计结果。

表 9-3 磁盘驱动控制系统的设计要求和实际性能  

<table><tr><td>性能指标</td><td>期望值</td><td>二阶模型响应</td><td>三阶模型响应</td></tr><tr><td>超调量</td><td>&lt;5%</td><td>&lt;2%</td><td>0%</td></tr><tr><td>调节时间/ms</td><td>&lt;50</td><td>40.2</td><td>40.3</td></tr><tr><td>单位阶跃扰动的响应峰值</td><td>5.2×10-3</td><td>5.2×10-5</td><td>5.2×10-5</td></tr></table>

解 首 先 建 立 系 统 的 状 态 空 间 模 型 。 选 择 状 态 变 量 为 ： $x _ { 1 } ( t ) = y ( t )$ ，$x _ { 2 } ( t ) = \mathrm { d } y ( t ) / \mathrm { d } t = \mathrm { d } x _ { 1 } ( t ) / \mathrm { d } t$ ，由图 9-43 知，开环系统的二阶模型的状态方程为

$$
\dot {\boldsymbol {x}} (t) = \left[ \begin{array}{c c} 0 & 1 \\ 0 & - 2 0 \end{array} \right] \boldsymbol {x} (t) + \left[ \begin{array}{c} 0 \\ 5 K _ {a} \end{array} \right] r (t)
$$

假定磁头的位置及速度均可以测量，根据图9-44所示的状态反馈闭环系统，可得闭环系统的状态方程为

$$
\dot {\boldsymbol {x}} (t) = \left[ \begin{array}{c c} 0 & 1 \\ - 5 K _ {1} K _ {a} & - (2 0 + 5 K _ {2} K _ {a}) \end{array} \right] \boldsymbol {x} (t) + \left[ \begin{array}{c} 0 \\ 5 K _ {a} \end{array} \right] r (t)
$$

在上式中代入 $K _ { 1 } { = } 1$ ，可由 $\operatorname* { d e t } ( s I - { \overline { { A } } } ) = 0$ (其中 $\overline { { A } }$ 为闭环系统阵)，得

$$
\det  \left[ \begin{array}{c c} s & - 1 \\ 5 K _ {a} & s + (2 0 + 5 K _ {2} K _ {a}) \end{array} \right] = 0
$$

于是，闭环系统的特征方程为

$$
s ^ {2} + (2 0 + 5 K _ {2} K _ {a}) s + 5 K _ {a} = 0
$$

为了满足设计指标要求，根据

$$
\sigma \% = 100\mathrm{e}^{-\pi \zeta /\sqrt{1 - \zeta^2}}\% <   5\%
$$

$$
t _ {s} = \frac {4.4}{\zeta \omega_ {n}} <   0.05 \quad (\Delta = 2 \%
$$

应有 $\zeta > 0 . 6 9$ 以及 $\zeta \omega _ { n } > 8 8$ 。考虑到磁盘读取系统对动态过程的严格要求，现取

$$
\zeta = 0. 9, \quad \zeta \omega_ {n} = 1 2 5
$$

其对应的动态性能指标为 $\sigma \% { = } 1$ . $53 \%$ 和 $t _ { s } { = } 3 5 . 2 \mathrm { m s }$ ，比较满意。在此情况下，预期的闭环特征方程为

$$
s ^ {2} + 2 \zeta \omega_ {n} s + \omega_ {n} ^ {2} = s ^ {2} + 2 5 0 s + 1 9 2 9 0 = 0
$$

令实际系统的闭环特征方程与预期闭环特征方程的对应项系数相等，得

$$
5 K _ {a} = 1 9 2 9 0
$$

$$
2 0 + 5 K _ {2} K _ {a} = 2 5 0
$$

求得放大器增益 $K _ { a } { = } 3 8 5 8$ ，反馈增益 $K _ { 2 } { = } 0 . 0 1 2$ 。采用仿真方法计算闭环系统的实际响应，所得动态性能指标如表 9-3 中第 3 列所示。结果表明，所选择的系统参数满足对系统的设计指标要求。

如果考虑磁场电感影响，图 9-43 中的 $G _ { 1 } ( s ) { = } 5$ 应变为

$$
G _ {1} (s) = \frac {5 0 0 0}{s + 1 0 0 0}
$$

从而得到系统更精确的三阶开环模型。仍然沿用二阶系统模型时选取的系统参数，即$K _ { a } { = } 3 8 5 8$ ， $K _ { 1 } { = } 1$ ， $K _ { 2 } { = } 0 . 0 1 2$ ，对闭环系统的实际响应进行仿真计算，其结果如表 9-3 中第4 列所示。表明：三阶闭环系统同样满足设计要求，其动态性能与二阶闭环系统性能相近，这说明二阶开环模型足以精确地描述磁盘驱动读取系统。

三阶模型单位阶跃响应的 MATLAB 仿真结果如图 9-45 所示。

![](images/a442c96529ee1b02ac45fabee58168b81035f3dbe51477b8724814097aa6fe7e.jpg)  
图 9-45 磁盘驱动系统三阶模型的时间响应(MATLAB)

# 习 题

9-1 已知电枢控制的直流伺服电机的微分方程组及传递函数为

$$
u _ {a} = R _ {a} i _ {a} + L _ {a} \frac {\mathrm {d} i _ {a}}{\mathrm {d} t} + E _ {b}, E _ {b} = C _ {b} \frac {\mathrm {d} \theta_ {m}}{\mathrm {d} t}
$$

$$
M _ {m} = C _ {m} i _ {a}, M _ {m} = J _ {m} \frac {\mathrm {d} ^ {2} \theta_ {m}}{\mathrm {d} t ^ {2}} + f _ {m} \frac {\mathrm {d} \theta_ {m}}{\mathrm {d} t}
$$

$$
\frac {\Theta_ {m} (s)}{U _ {a} (s)} = \frac {C _ {m}}{s \left[ L _ {a} J _ {m} s ^ {2} + \left(L _ {a} f _ {m} + J _ {m} R _ {a}\right) s + \left(R _ {a} f _ {m} + C _ {b} C _ {m}\right) \right]}
$$

(1) 设状态变量 $x _ { 1 } = \theta _ { m }$ ， $x _ { 2 } = \dot { \theta } _ { m }$ ， $x _ { 3 } = \ddot { \theta } _ { m }$ ，输出量 $y = \theta _ { { } _ { m } }$ ，试建立其动态方程；  
(2) 设状态变量 $\overline { { x } } _ { 1 } = i _ { a }$ ， $\overline { { x } } _ { 2 } = \theta _ { m }$ ， $\overline { { x } } _ { 3 } = \dot { \theta } _ { m }$ ， $y = \theta _ { m }$ ，试建立其动态方程；  
(3) 设 $\mathbf { { x } } = T \mathbf { \overleftrightarrow { { x } } }$ ，确定两组状态变量间的变换矩阵 $T _ { \circ }$

# 9-2 设系统微分方程为

$$
\ddot {x} + 3 \dot {x} + 2 x = u
$$

式中， $u$ 为输入量， $x$ 为输出量。

(1) 设状态变量 $x _ { 1 } = x$ ， $x _ { 2 } = \dot { x }$ ，试列写动态方程；  
(2) 设状态变换 $x _ { 1 } = \overline { { x } } _ { 1 } + \overline { { x } } _ { 2 }$ ， $x _ { 2 } = - { \overline { { x } } _ { 1 } } - 2 { \overline { { x } } _ { 2 } }$ ，试确定变换矩阵 $T$ 及变换后的动态方程。

# 9-3 设系统微分方程为

$$
\ddot {y} + 6 \ddot {y} + 1 1 \dot {y} + 6 y = 6 u
$$

式中，u、y 分别为系统的输入、输出量。试列写可控标准型（即 $\pmb { A }$ 为友矩阵）及可观测标准型（即 A为友矩阵转置）状态空间表达式，并画出状态变量图。

9-4 已知系统结构图如图 9-46 所示，其状态变量为 $x _ { 1 }$ ， $x _ { 2 }$ ， $x _ { 3 }$ 。试求动态方程，并画出状态变量图。

![](images/133e0a12d73e59c3b856ad6c7ce8c590fa2a34b7e64d0c5bbcaa1e59c589a322.jpg)  
图 9-46 系统结构图

9-5 已知双输入-双输出系统状态方程和输出方程

$$
\dot {x} _ {1} = x _ {2} + u _ {1}
$$

$$
\dot {x} _ {2} = x _ {3} + 2 u _ {1} - u _ {2}
$$

$$
\dot {x} _ {3} = - 6 x _ {1} - 1 1 x _ {2} - 6 x _ {3} + 2 u _ {2}
$$

$$
y _ {1} = x _ {1} - x _ {2}
$$

$$
y _ {2} = 2 x _ {1} + x _ {2} - x _ {3}
$$

写出其向量-矩阵形式并画出状态变量图。

# 9-6 已知系统传递函数为

$$
G (s) = \frac {s ^ {2} + 6 s + 8}{s ^ {2} + 4 s + 3}
$$

试求可控标准型（ $\pmb { A }$ 为友矩阵）、可观测标准型（ $\pmb { A }$ 为友矩阵转置）、对角线型（ $\pmb { A }$ 为对角阵）的动态方程。

9-7 已知系统传递函数

$$
G (s) = \frac {5}{(s + 1) ^ {2} (s + 2)}
$$

试求约当型（A 为约当阵）动态方程。

9-8 已知矩阵

$$
\boldsymbol {A} = \left[ \begin{array}{l l l l} 0 & 1 & 0 & 0 \\ 0 & 0 & 1 & 0 \\ 0 & 0 & 0 & 1 \\ 1 & 0 & 0 & 0 \end{array} \right]
$$

试求 $\pmb { A }$ 的特征方程、特征值、特征向量，并求出变换矩阵将 $\pmb { A }$ 对角化。

9-9 已知矩阵

$$
\boldsymbol {A} = \left[ \begin{array}{c c} - 1 & 0 \\ 0 & 1 \end{array} \right]
$$

试用幂级数法及拉普拉斯变换法求出矩阵指数（即状态转移矩阵）。

9-10 试求下列状态方程的解：

$$
\dot {\boldsymbol {x}} = \left[ \begin{array}{c c c} - 1 & 0 & 0 \\ 0 & - 2 & 0 \\ 0 & 0 & - 3 \end{array} \right] \boldsymbol {x}
$$

9-11 已知系统状态方程为

$$
\dot {\boldsymbol {x}} = \left[ \begin{array}{c c} 1 & 0 \\ 1 & 1 \end{array} \right] \boldsymbol {x} + \left[ \begin{array}{c} 1 \\ 1 \end{array} \right] u
$$

初始条件为 $x _ { 1 } ( 0 ) { = } 1$ ， $x _ { 2 } ( 0 ) { = } 0$ 。试求系统在单位阶跃输入作用下的状态响应。

9-12 已知线性系统状态转移矩阵

$$
\boldsymbol {\Phi} (t) = \left[ \begin{array}{l l} 6 \mathrm {e} ^ {- t} - 5 \mathrm {e} ^ {- 2 t} & 4 \mathrm {e} ^ {- t} - 4 \mathrm {e} ^ {- 2 t} \\ - 3 \mathrm {e} ^ {- t} + 3 \mathrm {e} ^ {- 2 t} & - 2 \mathrm {e} ^ {- t} + 3 \mathrm {e} ^ {- 2 t} \end{array} \right]
$$

试求该系统的状态阵 $\pmb { A }$ 。

9-13 已知系统动态方程

$$
\dot {\boldsymbol {x}} = \left[ \begin{array}{c c c} 0 & 1 & 0 \\ - 2 & - 3 & 0 \\ - 1 & 1 & 3 \end{array} \right] \boldsymbol {x} + \left[ \begin{array}{l} 0 \\ 1 \\ 2 \end{array} \right] u
$$

$$
y = \left[ \begin{array}{c c c} 0 & 0 & 1 \end{array} \right] x
$$

试求传递函数 $G ( s )$ 。

9-14 试求习题 9-5 所示系统的传递函数矩阵。

9-15 已知差分方程

$$
y (k + 2) + 3 y (k + 1) + 2 y (k) = 2 u (k + 1) + 3 u (k)
$$

试列写可控标准型（A 为友矩阵）离散动态方程，并求出 $u ( k ) { = } 1$ 时的系统响应。给定 $y ( 0 ) { = } 0$ ， $y ( 1 ) { = } 1$ 。

9-16 已知连续系统动态方程为

$$
\dot {\boldsymbol {x}} = \left[ \begin{array}{l l} 0 & 1 \\ 0 & 2 \end{array} \right] \boldsymbol {x} + \left[ \begin{array}{l} 0 \\ 1 \end{array} \right] u, \qquad y = \left[ \begin{array}{l l} 1 & 0 \end{array} \right] \boldsymbol {x}
$$

设采样周期 $T { = } 1 \mathrm { s }$ ，试求离散化动态方程。

9-17 试判断下列系统的状态可控性：

(1) $\dot { \pmb { x } } = \left[ \begin{array} { c c c } { - 2 } & { 2 } & { - 1 } \\ { 0 } & { - 2 } & { 0 } \\ { 1 } & { - 4 } & { 0 } \end{array} \right] \pmb { x } + \left[ \begin{array} { c c c } { 0 } \\ { 0 } \\ { 1 } \end{array} \right] \pmb { u } \ ;$ 1   
(2) ${ \dot { \pmb { x } } } = { \left[ \begin{array} { l l l } { 1 } & { 1 } & { 0 } \\ { 0 } & { 1 } & { 0 } \\ { 0 } & { 1 } & { 1 } \end{array} \right] } { \pmb { x } } + { \left[ \begin{array} { l } { 0 } \\ { 1 } \\ { 0 } \end{array} \right] } { \boldsymbol { u } } \ ;$   
(3) ${ \dot { \pmb { x } } } = { \left[ \begin{array} { l l l } { 1 } & { 1 } & { 0 } \\ { 0 } & { 1 } & { 0 } \\ { 0 } & { 1 } & { 1 } \end{array} \right] } { \pmb { x } } + { \left[ \begin{array} { l l } { 0 } & { 0 } \\ { 0 } & { 1 } \\ { 1 } & { 0 } \end{array} \right] } { \left[ \begin{array} { l } { u _ { 1 } } \\ { u _ { 2 } } \end{array} \right] } ~ ;$   
(4) $\dot { \pmb { x } } = \left[ \begin{array} { l l l } { - 4 } & { } & { 0 } \\ { } & { - 4 } & { } \\ { 0 } & { } & { 1 } \end{array} \right] \pmb { x } + \left[ \begin{array} { l } { 1 } \\ { 2 } \\ { 1 } \end{array} \right] \pmb { u } _ { \mathrm { ~ o ~ } }$

9-18 已知 $a d { = } b c$ ，试计算 $\left[ \begin{array} { l l } { a } & { b } \\ { c } & { d } \end{array} \right] ^ { 1 0 0 }$ 。

9-19 设系统状态方程为

$$
\dot {\boldsymbol {x}} = \left[ \begin{array}{c c} 0 & 1 \\ - 1 & a \end{array} \right] \boldsymbol {x} + \left[ \begin{array}{c} 1 \\ b \end{array} \right] u
$$

设状态可控，试求 $a$ ，b。

9-20 设系统传递函数为

$$
G (s) = \frac {s + a}{s ^ {3} + 7 s ^ {2} + 1 4 s + 8}
$$

设状态可控，试求 a。

9-21 判断下列系统的输出可控性：

(1) ${ \dot { \pmb x } } = \left[ \begin{array} { l l l } { 0 } & { 1 } & { 0 } \\ { 0 } & { 0 } & { 1 } \\ { - 6 } & { - 1 1 } & { - 6 } \end{array} \right] { \pmb x } + \left[ \begin{array} { l } { 0 } \\ { 0 } \\ { 1 } \end{array} \right] { \pmb u } , \qquad { \ b y } = \left[ 1 \quad 0 \quad 0 \right] { \pmb x } ;$   
${ \begin{array} { r l } & { { \dot { \boldsymbol { x } } } = { \left[ \begin{array} { l l l } { 0 } & { 1 } & { 0 } \\ { 0 } & { 0 } & { 1 } \\ { - 6 } & { - 1 1 } & { - 6 } \end{array} \right] } { \boldsymbol { x } } + { \left[ \begin{array} { l } { 0 } \\ { 0 } \\ { 1 } \end{array} \right] } { \boldsymbol { u } } , \qquad { \boldsymbol { y } } = { \left[ \begin{array} { l l l } { 1 } & { 0 } & { 0 } \end{array} \right] } { \boldsymbol { x } } ~ ; } \\ & { { \dot { \boldsymbol { x } } } = { \left[ \begin{array} { l l l } { - a } & & { 0 } \\ & { - b } & \\ & & { - c } \\ { 0 } & & & { - d } \end{array} \right] } { \boldsymbol { x } } + { \left[ \begin{array} { l } { 0 } \\ { 0 } \\ { 1 } \\ { 1 } \end{array} \right] } { \boldsymbol { u } } , \qquad { \boldsymbol { y } } = { \left[ \begin{array} { l l l l } { 1 } & { 0 } & { 0 } & { 0 } \\ { 1 } & { 0 } & { 0 } \end{array} \right] } { \boldsymbol { x } } ~ ; } \\ & { \qquad } \end{array} }$ a(2)

9-22 试判断下列系统的可观测性：

(1) ${ \dot { \pmb x } } = \left[ \begin{array} { c c c } { { - 1 } } & { { - 2 } } & { { - 2 } } \\ { { } } & { { - 1 } } & { { 1 } } \\ { { 1 } } & { { 0 } } & { { - 1 } } \end{array} \right] { \pmb x } + \left[ \begin{array} { c } { { 2 } } \\ { { 0 } } \\ { { 1 } } \end{array} \right] { \pmb u } , \qquad { \ b y } = \left[ 1 \quad 1 \quad 0 \right] { \pmb x } \ ;$   
(2) ${ \dot { \pmb x } } = \left[ \begin{array} { l l l } { 2 } & { 0 } & { 0 } \\ { 0 } & { 2 } & { 0 } \\ { 0 } & { 3 } & { 1 } \end{array} \right] { \pmb x } , \qquad { \ b y } = \left[ 1 \quad 1 \quad 1 \right] { \pmb x } ;$   
(3) $\dot { \pmb x } = \left[ \begin{array} { c c c c } { - 1 } & { 1 } & { 0 } \\ & { - 1 } & { } \\ { 0 } & { - 2 } & { 1 } \\ { 0 } & { } & { - 2 } \end{array} \right] \pmb x , ~ \pmb y = \left[ \begin{array} { c c c c } { 1 } & { 0 } & { 0 } & { 0 } \\ { 0 } & { 0 } & { - 1 } & { 0 } \end{array} \right] \pmb x ~ ;$ y 

(4) $\dot { \pmb x } = \left[ 0 \begin{array} { c c c } { { 2 } } & { { 1 } } & { { 0 } } \\ { { 0 } } & { { 2 } } & { { 0 } } \\ { { 0 } } & { { 0 } } & { { - 3 } } \end{array} \right] { \pmb x } , \qquad { \boldsymbol y } = \left[ 0 \quad 1 \quad 1 \right] { \pmb x } _ { \mathrm { ~ o ~ } }$

9-23 试确定使下列系统可观测的 $^ { a }$ ，b：

$$
\dot {\boldsymbol {x}} = \left[ \begin{array}{l l} a & 1 \\ 0 & b \end{array} \right] \boldsymbol {x}, \qquad y = \left[ \begin{array}{l l} 1 & - 1 \end{array} \right] \boldsymbol {x}
$$

9-24 已知系统各矩阵为

$$
\boldsymbol {A} = \left[ \begin{array}{l l l} 1 & 3 & 2 \\ 0 & 4 & 2 \\ 0 & 0 & 1 \end{array} \right], \quad \boldsymbol {B} = \left[ \begin{array}{l l} 0 & 1 \\ 0 & 0 \\ 1 & 0 \end{array} \right], \quad \boldsymbol {C} = \left[ \begin{array}{l l l} 1 & 0 & 0 \\ 0 & 0 & 1 \end{array} \right]
$$

试用传递矩阵判断系统可控性、可观测性。

9-25 将下列状态方程化为可控标准型：

$$
\dot {\boldsymbol {x}} = \left[ \begin{array}{c c} 1 & - 2 \\ 3 & 4 \end{array} \right] \boldsymbol {x} + \left[ \begin{array}{c} 1 \\ 1 \end{array} \right] u
$$

9-26 已知系统传递函数为

$$
\frac {Y (s)}{U (s)} = \frac {s + 1}{s ^ {2} + 3 s + 2}
$$

试写出系统可控不可观测、可观测不可控、不可控不可观测的动态方程。

9-27 已知系统各矩阵为

$$
\boldsymbol {A} = \left[ \begin{array}{r r r r} 1 & 0 & 0 & 0 \\ 0 & 2 & 0 & 0 \\ - 6 & - 2 & 3 & 0 \\ 3 & - 2 & 0 & 4 \end{array} \right], \quad \boldsymbol {b} = \left[ \begin{array}{l} 1 \\ 0 \\ 3 \\ 2 \end{array} \right], \quad \boldsymbol {c} = \left[ \begin{array}{r r r r} - 4 & - 3 & 1 & 1 \end{array} \right]
$$

试求可控子系统与不可控子系统的动态方程。

9-28 系统各矩阵同习题 9-27，试求可观测子系统与不可观测子系统的动态方程。

9-29 设被控系统状态方程为

$$
\dot {\boldsymbol {x}} = \left[ \begin{array}{c c c} 0 & 1 & 0 \\ 0 & - 1 & 1 \\ 0 & - 1 & 1 0 \end{array} \right] \boldsymbol {x} + \left[ \begin{array}{c} 0 \\ 0 \\ 1 0 \end{array} \right] u
$$

可否用状态反馈任意配置闭环极点？求状态反馈阵，使闭环极点位于10，1j $\sqrt { 3 }$ ，并画出状态变量图。

9-30 设被控系统动态方程为

$$
\dot {\boldsymbol {x}} = \left[ \begin{array}{l l} 0 & 1 \\ 0 & 0 \end{array} \right] \boldsymbol {x} + \left[ \begin{array}{l} 0 \\ 1 \end{array} \right] u, \qquad y = \left[ \begin{array}{l l} 1 & 0 \end{array} \right] \boldsymbol {x}
$$

试设计全维状态观测器，使闭环极点位于r， $- 2 r ( r > 0 )$ ，并画出状态变量图。

9-31 设系统传递函数为

$$
\frac {(s - 1) (s + 2)}{(s + 1) (s - 2) (s + 3)}
$$

试问能否利用状态反馈将传递函数变成

$$
\frac {s - 1}{(s + 2) (s + 3)}
$$

若有可能，求出一个满足要求的状态反馈阵K，并画出状态变量图。（提示：状态反馈不改变原传递函数零点）

9-32 试用李雅普诺夫第二法判断下列线性系统平衡状态的稳定性：

$$
\dot {x} _ {1} = - x _ {1} + x _ {2}, \quad \dot {x} _ {2} = 2 x _ {1} - 3 x _ {2}
$$

9-33 已知系统状态方程为

$$
\dot {\boldsymbol {x}} = \left[ \begin{array}{c c c} 2 & \frac {1}{2} & - 3 \\ 0 & - 1 & 0 \\ 0 & \frac {1}{2} & - 1 \end{array} \right] \boldsymbol {x} + \left[ \begin{array}{l l} 1 & 0 \\ 0 & 2 \\ 1 & 0 \end{array} \right] \left[ \begin{array}{l} u _ {1} \\ u _ {2} \end{array} \right]
$$

当 $\varrho = I$ 时， $\pmb { P } \mathrm { = } 2$ 若选 $\varrho$ 为正半定矩阵， $\scriptstyle Q = ?$ 对应 $\pmb { P } { = } ?$ 判断系统稳定性。

9-34 设线性定常离散系统状态方程为

$$
\boldsymbol {x} (k + 1) = \left[ \begin{array}{l l l} 0 & 1 & 0 \\ 0 & 0 & 1 \\ \frac {k}{2} & 0 & 0 \end{array} \right] \boldsymbol {x} (k), \quad k > 0
$$

试求使系统渐近稳定的 $k$ 值范围。

9-35 设工业机器人如图 9-47 所示，其中两相伺服电机转动肘关节之后，通过小臂移动机器人的手腕。假定弹簧的弹性系数为 $k$ ，阻尼系数为 f，并选取系统的如下状态变量：

$$
x _ {1} = \phi_ {1} - \phi_ {2}, \quad x _ {2} = \frac {\omega_ {1}}{\omega_ {0}}, \quad x _ {3} = \frac {\omega_ {2}}{\omega_ {0}}
$$

其中 $\omega _ { \mathrm { 0 } } ^ { 2 } = \frac { k ( J _ { \mathrm { 1 } } + J _ { \mathrm { 2 } } ) } { J _ { \mathrm { 1 } } J _ { \mathrm { 2 } } }$ 。试列写该机器人的状态方程。

![](images/6a6fe030d9c5abad7582bc31a5f1ab9a35e159c48374689737b0c7aa8a2cb0c7.jpg)  
图 9-47 工业机器人示意图

9-36 为了完成空间站装配、卫星捕获等空间操作，航天飞机的货舱内装备了一种可膨胀机械臂的遥操作系统，如图9-48(a)所示。柔性机械臂的模型如图9-48(b)所示，其中 $J$ 是驱动电机的转动惯量， $u$ 为电机驱动转矩， $\theta _ { 1 }$ 和为柔性臂转角，k为柔性臂的弹性系数， $M$ 和 $I$ 分别为负载质量与转动惯量，l为机械臂在负载上的作用点到负载重心的距离。若选取状态变量为 $x _ { 1 } = \theta _ { 1 }$ ， $x _ { 2 } = \dot { \theta } _ { 1 }$ ， $x _ { 3 } = \theta _ { 2 }$ ， $x _ { 4 } = \dot { \theta } _ { 2 }$ ，试列写柔性机械臂系统的线性化状态方程。  
9-37 设磁悬浮试验系统如图9-49所示。在该系统上方装有一个电磁铁，产生电磁吸力 $F$ ，以便将铁球悬浮于空中。系统的下方装有一个间隙测量传感器，以测量铁球的悬浮间隙。由于没有引入反馈，该磁悬浮试验系统不能稳定工作。

假定电磁铁电感为 $\scriptstyle { L = 0 . 5 0 8 \mathrm { H } }$ ，电阻为 $R { = } 2 3 . 2 \Omega$ ，电流为 $i _ { 1 } { = } I _ { 0 } { + } i$ ，其中 $I _ { 0 } { = } 1 . 0 6 \mathrm { A }$ 是系统的标称工作电流。再假定铁球的质量为 $m { = } 1 . 7 5 \mathrm { k g }$ ，铁球悬浮间隙 $\mu _ { g } { = } X _ { 0 } { + } x$ ，其中 $X _ { 0 } { = } 4 . 3 6 \mathrm { m m }$ 为标称磁悬浮间隙。若电磁吸力满足如下条件：

$$
F = k \left(i / \mu_ {\mathrm {g}}\right) ^ {2}
$$

式中， 4 2 2 k 2.9 10 kg m / A     。选择 1 2,x x x $k = 2 . 9 \times 1 0 ^ { - 4 } \mathrm { k g } \cdot \mathrm { m } ^ { 2 } / \mathrm { A } ^ { 2 }$ $x _ { 1 } = x , x _ { 2 } = \frac { \mathrm { d } x } { \mathrm { d } t } , x _ { 3 } = i$ 3 , x  x i  为状态变量，试利用 F 的泰勒展开式，列写磁 $F$ 悬浮试验系统的线性化状态空间表达式。

![](images/2cae00960572dd0b0cafd9c41a03efad3c6396743b77aa54274d67e07d7c1eea.jpg)

![](images/d6003641c9705652fd5f843a06d28e1abe2bc219fdb5a8f1f1932853077aa661.jpg)  
(a)可膨胀机械臂遥操作  
图 9-48 遥操作系统示意图

![](images/8ab93dff968b04287a305bdaf8ee346ceed61a70262ea1bfe4ab73451e421420.jpg)

![](images/abec92c51157ded398b021b0391105486ac63f2fdc636a508e58ce03f03cd5e7.jpg)  
图 9-49 磁悬浮系统示意图

9-38 在大功率高性能的摩托车中，常采用图9-50所示的弹簧-质量-阻尼器系统作为减震器。若已知减震器的基本参数取为质量 $m { = } 1 \mathrm { k g }$ ，摩擦系数 $f = 9 \mathrm { k g \cdot m \cdot s }$ ，弹簧系数 $k = 2 0 \mathrm { k g } / \mathrm { m } , u ( t )$ 为力输入， $y ( t )$ 为位移输出。要求完成：

(1) 选择状态变量为 $x _ { 1 } = y \ , \ y _ { 2 } = { \dot { y } }$ $x _ { \mathrm { 1 } } = y$ $y _ { 2 } = \dot { y }$ ，列写系统的动态方程；  
(2) 计算系统的特征根及状态转移矩阵 $\phi ( t )$ ；  
(3) 若初始条件 $y ( 0 ) { = } 1$ ， ${ \dot { y } } ( 0 ) = 2$ ，在 $0 \leqslant t \leqslant 2$ 范围内，绘出系统零输入响应 $y ( t )$ 及 $\dot { y } ( t )$ ；  
(4) 重新设计 $f$ 和 $k$ 的合适值，使系统特征根为 $\scriptstyle { s _ { 1 } = s _ { 2 } = - 1 0 }$ ，以减轻震动对车手的影响。

9-39 设汽车悬架控制系统如图 9-51 所示，其中 $X _ { 1 } ( s ) , X _ { 2 } ( s )$ 和 $X _ { 3 } ( s )$ 为状态变量， $K _ { 1 }$ 、 $K _ { 2 }$ 和 $K _ { 3 }$ 为状态反馈系数，已知 $K \mathrm { { 1 } = } 1$ 。试确定 $K _ { 2 }$ 和 $K _ { 3 }$ 的合适取值，使闭环系统的三个特征根位于 $s { = } - 3$ 和 $s { = } - 6$ 之间。另外，还要求确定前置增益 $K _ { p }$ 值，使系统对阶跃输入的稳态误差为零。

![](images/fa872dbbcabfe9288dc352c0dd7356afa7a27a8bfc27d8f5efd0b3d92fffac5c.jpg)  
图 9-50 弹簧-质量-阻尼器系统示意图

9-40 在图 9-52(a)所示的新型游船上，采用了浮桥和稳定器来减少波浪对游船摇摆的影响，游船摇摆控制系统如图 9-52(b)所示。图中， $X _ { 1 }$ 、 $X _ { 2 }$ 和 $X _ { 3 }$ 为状态变量， $K _ { 2 }$ 和 $K _ { 3 }$ 为状态反馈增益。试确定

$K _ { 2 }$ 和 $K _ { 3 }$ 的合适取值，使闭环特征根为 $s _ { 1 , 2 } \mathrm { = } \mathrm { - } 2 \pm \mathrm { j } 2$ ， $_ { S 3 } { = } _ { - 1 5 }$ ，并画出系统在单位阶跃扰动作用下的响应曲线。

9-41 设内模控制系统如图 9-53 所示。试设计合适的内模控制器 $G _ { c } ( s )$ 和状态反馈增益向量 $k _ { 2 }$ ，使系统闭环极点 $\scriptstyle { s _ { 1 } = s _ { 2 } = s _ { 3 } = - 2 }$ ，且对阶跃输入的稳态跟踪误差为零，最后绘出系统的单位阶跃响应曲线。

![](images/f2b3012d227c45918340cba5112c9f1fdae2c6e03d93e71174f3c2af894a5644.jpg)  
图 9-51 汽车悬架控制系统结构图

![](images/237a06ec445f5f9a97147aa346fcfb25769b5be6d63c6159e0270232a34b97d9.jpg)

![](images/1be3fe9a37089ebdf9933ceb256ed691b44131f0a1086838a7762ae45a2607ac.jpg)  
(b)控制系统结构图

![](images/a9f297c8c80164072a8754e14254f1d7026ce53b0ec8df6fdd076aaeca37877f.jpg)  
图 9-52 游船摇摆控制系统  
图 9-53 内模控制系统结构图

9-42 设单位斜坡内模控制系统如图9-54所示，其中被控对象

$$
G _ {0} (s) = \frac {1}{(s + 1) (s + 2)}
$$

$x _ { 1 } ( t )$ 和 $x _ { 2 } ( t )$ 为状态变量。试设计合适的内模控制器

$$
G _ {c} (s) = \frac {k _ {1} + k _ {2} s}{s ^ {2}}
$$

及状态反馈增益 $k _ { 3 }$ 和 $k _ { 4 }$ ，使系统的闭环极点为 $\scriptstyle { s _ { 1 } = s _ { 2 } = s _ { 3 } = s _ { 4 } = - 2 }$ ，且系统对单位斜坡输入的稳态跟踪误差为零，最后绘出系统的单位斜坡响应曲线。

![](images/ad8ac626a0123f90893e1f2ce1fe0a39a03a6bf85f67e047f8113f862327dc5c.jpg)  
图 9-54 单位斜坡内模控制系统结构图

9-43 已知被控对象的动态方程

$$
\dot {\boldsymbol {x}} (t) = \boldsymbol {A} \boldsymbol {x} (t) + \boldsymbol {b} u (t), \quad y (t) = \boldsymbol {c x} (t)
$$

其中 $A = { \left[ \begin{array} { l l } { 0 } & { 1 } \\ { - 2 } & { - 2 } \end{array} \right] } , \quad b = { \left[ \begin{array} { l } { 1 } \\ { 2 } \end{array} \right] } , \quad c = { \left[ \begin{array} { l l } { 1 } & { 0 } \end{array} \right] }$

要求设计单位斜坡输入时的内模控制器，使系统闭环极点为 $s _ { 1 , 2 } { = } - 1 \pm \mathrm { j } 1$ ， $\scriptstyle { s 3 = s 4 = - 1 0 }$ ，并给出单位斜坡内模控制系统结构图及跟踪误差 $e ( t )$ 的响应曲线。

9-44 设带有扰动 $n ( t )$ 的单输入-单输出系统的状态空间表达式为

$$
\dot {\boldsymbol {x}} (t) = \boldsymbol {A} \boldsymbol {x} (t) + \boldsymbol {b} u (t), \quad y (t) = \boldsymbol {c x} (t) + n (t)
$$

式中， $\boldsymbol { x } \in \mathbf { R } ^ { n }$ 为状态向量； $u$ 为标量输入； $y$ 为标量输出；A、b、 $c$ 维数适当。设参考输入 $r ( t ) { = } t$ ，扰动信号 $n ( t ) { = } 1 ( t )$ ，为阶跃扰动。试论证可设计扰动内模控制器，使系统输出能以零稳态误差渐近跟踪斜坡输入 $t$ ，且不受阶跃扰动 $n ( t )$ 的影响。

9-45 设有系统

$$
\dot {\boldsymbol {x}} (t) = \left[ \begin{array}{l l} 0 & 1 \\ - 2 & - 2 \end{array} \right] \boldsymbol {x} (t) + \left[ \begin{array}{l} 1 \\ 2 \end{array} \right] u (t), \quad y (t) = \left[ \begin{array}{l l} 1 & 0 \end{array} \right] \boldsymbol {x} (t) + n (t)
$$

式中， $n ( t ) = 3 t ^ { 2 }$ 为输出端扰动信号。要求系统输出能以零稳态误差跟踪斜坡参考输入信号，并克服输出端加速度扰动对跟踪性能的影响。