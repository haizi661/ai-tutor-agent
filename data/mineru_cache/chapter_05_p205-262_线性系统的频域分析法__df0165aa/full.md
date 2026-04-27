# 第五章 线性系统的频域分析法

![](images/f5408e899f9dc9aec30059b6b40de81f269816ee9e0c7d2ee262de58dbe1b32d.jpg)  
本章导学

控制系统中的信号可以表示为不同频率正弦信号的合成。控制系统的频率特性反映正弦信号作用下系统响应的性能。应用频率特性研究线性系统的经典方法称为频域分析法。频域分析法具有以下特点：

1) 控制系统及其元部件的频率特性可以运用分析法和实验方法获得，并可用多种形式的曲线表示，因而系统分析和控制器设计可以应用图解法进行。  
2) 频率特性物理意义明确。对于一阶系统和二阶系统，频域性能指标和时域性能指标有确定的对应关系；对于高阶系统，可建立近似的对应关系。  
3) 控制系统的频域设计可以兼顾动态响应和噪声抑制两方面的要求。  
4) 频域分析法不仅适用于线性定常系统，还可以推广应用于某些非线性控制系统。

本章介绍频率特性的基本概念和频率特性曲线的绘制方法，研究频率域稳定判据和频域性能指标的估算。控制系统的频域综合问题，将在第六章介绍。

# 5-1 频 率 特 性

# 1. 频率特性的基本概念

首先以图 5-1 所示的 RC 滤波网络为例，建立频率特性的基本概念。设电容 $C$ 的初始电压为 $u _ { o _ { 0 } }$ ，取输入信号为正弦信号

$$
u _ {i} = A \sin \omega t \tag {5-1}
$$

记录网络的输入、输出信号。当输出响应 $u _ { o }$ 呈稳态时，记录曲线如图 5-2 所示。

由图5-2可见，RC网络的稳态输出信号仍为正弦信号，频率与输入信号的频率相同，幅值较输入信号有一定衰减，其相位存在一定延迟。

![](images/f72f5ee2d514d7a4e2ef908b2dcd860a438327d3b0335d7e9035a085cc18dbb9.jpg)  
图 5-1 RC 滤波网络

![](images/01c20cdd32bf0196ec607b98dc9651879645f73db01c424a87036e03fba6aa54.jpg)  
图 5-2 RC 网络的输入和稳态输出信号

RC网络的输入和输出的关系可由以下微分方程描述：

$$
T \frac {\mathrm {d} u _ {o}}{\mathrm {d} t} + u _ {o} = u _ {i} \tag {5-2}
$$

式中， $T { = } R C$ ，为时间常数。取拉氏变换并代入初始条件 $u _ { o } ( 0 ) = u _ { o _ { 0 } }$ ，得

$$
U _ {o} (s) = \frac {1}{T s + 1} \left[ U _ {i} (s) + T u _ {o _ {0}} \right] = \frac {1}{T s + 1} \left(\frac {A \omega}{s ^ {2} + \omega^ {2}} + T u _ {o _ {0}}\right) \tag {5-3}
$$

再由拉氏反变换求得

$$
u _ {o} (t) = \left(u _ {o _ {0}} + \frac {A \omega T}{1 + T ^ {2} \omega^ {2}}\right) e ^ {- \frac {t}{T}} + \frac {A}{\sqrt {1 + T ^ {2} \omega^ {2}}} \sin (\omega t - \arctan \omega T) \tag {5-4}
$$

式中第一项，由于 $T > 0$ ，将随时间增大而趋于零，为输出的瞬态分量；而第二项正弦信号为输出的稳态分量

$$
\begin{array}{l} u _ {o _ {s}} (t) = \frac {A}{\sqrt {1 + T ^ {2} \omega^ {2}}} \sin (\omega t - \arctan \omega T) \tag {5-5} \\ = A \cdot A (\omega) \sin [ \omega t + \varphi (\omega) ] \\ \end{array}
$$

在式(5-5)中， $A ( \omega ) = \frac { 1 } { \sqrt { 1 + T ^ { 2 } \omega ^ { 2 } } } , \varphi ( \omega ) = - \arctan \omega T$ ，分别反映 RC 网络在正弦信号作用下，输出稳态分量的幅值和相位的变化，称为幅值比和相位差，且皆为输入正弦信号频率 $\omega$ 的函数。

注意到 RC网络的传递函数为

$$
G (s) = \frac {1}{T s + 1} \tag {5-6}
$$

取 $\scriptstyle s = \mathrm { j } \omega$ ，则有

$$
G (\mathrm {j} \omega) = G (s) \mid_ {s = \mathrm {j} \omega} = \frac {1}{\sqrt {1 + T ^ {2} \omega^ {2}}} \mathrm {e} ^ {- \mathrm {j} \arctan \omega T} \tag {5-7}
$$

比较式(5-5)和式(5-7)可知， $A ( \omega )$ 和 $\varphi ( \omega )$ 分别为 $G ( \mathrm { j } \omega )$ 的幅值 $| G ( \mathrm { j } \omega ) |$ 和相角 $\angle G ( \mathrm { j } \omega )$ 。这一结论非常重要，反映了 $A ( \omega )$ 和 $\varphi ( \omega )$ 与系统数学模型的本质关系，具有普遍性。

设有稳定的线性定常系统，其传递函数为

$$
G (s) = \frac {\sum_ {i = 0} ^ {m} b _ {i} s ^ {m - i}}{\sum_ {i = 0} ^ {n} a _ {i} s ^ {n - i}} = \frac {B (s)}{A (s)} \tag {5-8}
$$

系统输入为谐波信号

$$
r (t) = A \sin (\omega t + \varphi) \tag {5-9}
$$

$$
R (s) = \frac {A (\omega \cos \varphi + s \sin \varphi)}{s ^ {2} + \omega^ {2}} \tag {5-10}
$$

由于系统稳定，输出响应稳态分量的拉氏变换

$$
\begin{array}{l} C _ {s} (s) = \frac {1}{s + j \omega} \left[ (s + j \omega) R (s) G (s) \Big | _ {s = - j \omega} \right] + \frac {1}{s - j \omega} \left[ (s - j \omega) R (s) G (s) \Big | _ {s = j \omega} \right] \tag {5-11} \\ = \frac {A}{s + j \omega} \frac {\cos \varphi - j \sin \varphi}{- 2 j} G (- j \omega) + \frac {A}{s - j \omega} \frac {\cos \varphi + j \sin \varphi}{2 j} G (j \omega) \\ \end{array}
$$

设

$$
G (\mathrm {j} \omega) = \frac {a (\omega) + \mathrm {j} b (\omega)}{c (\omega) + \mathrm {j} d (\omega)} = | G (\mathrm {j} \omega) | \mathrm {e} ^ {\mathrm {j} \angle [ G (\mathrm {j} \omega) ]} \tag {5-12}
$$

因为 $G ( s )$ 的分子和分母多项式为实系数，故式(5-12)中的 $a ( \omega )$ 和 $c ( \omega )$ 为关于 $\omega$ 的偶次幂实系数多项式， $b ( \omega )$ 和 $d ( \omega )$ 为关于 $\omega$ 的奇次幂实系数多项式，即 $a ( \omega )$ 和 $c ( \omega )$ 为 $\omega$ 的偶函数，$b ( \omega )$ 和 $d ( \omega )$ 为 $\omega$ 的奇函数。鉴于

$$
| G (\mathrm {j} \omega) | = \left(\frac {b ^ {2} (\omega) + a ^ {2} (\omega)}{c ^ {2} (\omega) + d ^ {2} (\omega)}\right) ^ {\frac {1}{2}} \tag {5-13}
$$

$$
\angle [ G (\mathrm {j} \omega) ] = \arctan \frac {b (\omega) c (\omega) - a (\omega) d (\omega)}{a (\omega) c (\omega) + d (\omega) b (\omega)} \tag {5-14}
$$

因而

$$
G (- \mathrm {j} \omega) = \frac {a (\omega) - \mathrm {j} b (\omega)}{c (\omega) - \mathrm {j} d (\omega)} = | G (\mathrm {j} \omega) | \mathrm {e} ^ {- \mathrm {j} \angle [ G (\mathrm {j} \omega) ]} \tag {5-15}
$$

再由式(5-11)得

$$
\begin{array}{l} C _ {s} (s) = \frac {A | G (\mathrm {j} \omega) |}{s + \mathrm {j} \omega} \frac {\mathrm {e} ^ {- \mathrm {j} (\varphi + \angle [ G (\mathrm {j} \omega) ])}}{- 2 \mathrm {j}} + \frac {A | G (\mathrm {j} \omega) |}{s - \mathrm {j} \omega} \frac {\mathrm {e} ^ {\mathrm {j} (\varphi + \angle [ G (\mathrm {j} \omega) ])}}{2 \mathrm {j}} \\ c _ {s} (t) = A | G (\mathrm {j} \omega) | \left[ \frac {\mathrm {e} ^ {\mathrm {j} (\omega t + \varphi + \angle [ G (\mathrm {j} \omega) ])} - \mathrm {e} ^ {- \mathrm {j} (\omega t + \varphi + \angle [ G (\mathrm {j} \omega) ])}}{2 \mathrm {j}} \right] \tag {5-16} \\ = A \left| G (\mathrm {j} \omega) \right| \sin (\omega t + \varphi + \angle [ G (\mathrm {j} \omega) ]) \\ \end{array}
$$

式(5-16)与式(5-5)相比较，由 $\varphi = 0$ ，得

$$
\left\{ \begin{array}{l} A (\omega) = | G (\mathrm {j} \omega) | \\ \varphi (\omega) = \angle [ G (\mathrm {j} \omega) ] \end{array} \right. \tag {5-17}
$$

式(5-16)表明，对于稳定的线性定常系统，由谐波输入产生的输出稳态分量仍然是与输入同频率的谐波函数，而幅值和相位的变化是频率 $\omega$ 的函数，且与系统数学模型相关。为此，定义谐波输入下，输出响应中与输入同频率的谐波分量与谐波输入的幅值之比 $A ( \omega )$ 为幅频特性，相位之差 $\varphi ( \omega )$ 为相频特性，并称其指数表达形式

$$
G (\mathrm {j} \omega) = A (\omega) \mathrm {e} ^ {\mathrm {j} \varphi (\omega)} \tag {5-18}
$$

为系统的频率特性。

上述频率特性的定义既可以适用于稳定系统，也可适用于不稳定系统。稳定系统的频率特性可以用实验方法确定，即在系统的输入端施加不同频率的正弦信号，然后测量系统输出的稳态响应，再根据幅值比和相位差作出系统的频率特性曲线。频率特性也是系统数学模型的一种表达形式。RC滤波网络的频率特性曲线如图 5-3所示。

对于不稳定系统，输出响应稳态分量中含有由系统传递函数的不稳定极点产生的呈发散或振荡发散的分量，所以不稳定系统的频率特性不能通过实验方法确定。

线性定常系统的传递函数为零初始条件下，输出和输入的拉氏变换之比

$$
G (s) = \frac {C (s)}{R (s)}
$$

![](images/d7f5401251cb239524ced012972d95aa5c935e8be43e40433d1a8d87b7561ae7.jpg)  
(a)幅频特性

![](images/681dbcd344ff049829b6bd6d864e0a4e0c6eae37dd47bd35dc944d0eb393717d.jpg)  
(b)相频特性  
图 5-3 RC网络的幅频特性和相频特性曲线(MATLAB)

上式的反变换式为

$$
g (t) = \frac {1}{2 \pi \mathrm {j}} \int_ {\sigma - \mathrm {j} \infty} ^ {\sigma + \mathrm {j} \infty} G (s) \mathrm {e} ^ {s t} \mathrm {d} s
$$

式中， $\sigma$ 位于 $G ( s )$ 的收敛域。若系统稳定，则 $\sigma$ 可以取为零。如果 $r ( \mathrm { t } )$ 的傅氏变换存在，可令 $\scriptstyle s = \mathrm { j } \omega$

$$
g (t) = \frac {1}{2 \pi} \int_ {- \infty} ^ {\infty} G (\mathrm {j} \omega) \mathrm {e} ^ {\mathrm {j} \omega t} \mathrm {d} \omega = \frac {1}{2 \pi} \int_ {- \infty} ^ {\infty} \frac {C (\mathrm {j} \omega)}{R (\mathrm {j} \omega)} \mathrm {e} ^ {\mathrm {j} \omega t} \mathrm {d} \omega
$$

因而 $G ( \mathrm { j } \omega ) = \frac { C ( \mathrm { j } \omega ) } { R ( \mathrm { j } \omega ) } = G ( s ) \left| _ { s = \mathrm { j } \omega } \right.$ j( j )  ( ) sC  G s    (5-19)

![](images/06c65d1ef807fbbc68b2544c85749fd0640dc048101ca3cbd619e0700fb52b3b.jpg)  
图 5-4 频率特性、传递函数和微分方程三种系统描述之间的关系

由此可知，稳定系统的频率特性等于输出和输入的傅氏变换之比，而这正是频率特性的物理意义。频率特性与微分方程和传递函数一样，也表征了系统的运动规律，成为系统频域分析的理论依据。系统三种描述方法的关系可用图 5-4 说明。

# 2. 频率特性的几何表示法

在工程分析和设计中，通常把线性系统的频率特性画成曲线，再运用图解法进行研究。常用的频率特性曲线有以下三种：

# (1) 幅相频率特性曲线

它又简称为幅相曲线或极坐标图。以横轴为实轴、纵轴为虚轴，构成复数平面。对于任一给定的频率 $\omega$ ，频率特性值为复数。若将频率特性表示为实数和虚数和的形式，则实部为实轴坐标值，虚部为虚轴坐标值。若将频率特性表示为复指数形式，则为复平面上的向量，而向量的长度为频率特性的幅值，向量与实轴正方向的夹角等于频率特性的相位。由于幅频特性为 $\omega$ 的偶函数，相频特性为 $\omega$ 的奇函数，则 $\omega$ 从零变化至 $+ \infty$ 和从零

变化至 $- \infty$ 的幅相曲线关于实轴对称，因此一般只绘制 $\omega$ 从零变化至 $+ \infty$ 的幅相曲线。在系统幅相曲线中，频率 $\omega$ 为参变量，一般用小箭头表示 $\omega$ 增大时幅相曲线的变化方向。

对于 RC 网络

$$
G (\mathrm {j} \omega) = \frac {1}{1 + \mathrm {j} T \omega} = \frac {1 - \mathrm {j} T \omega}{1 + (T \omega) ^ {2}}
$$

故有 $\left[ { \mathrm { R e } } G ( { \mathrm { j } } \omega ) - { \frac { 1 } { 2 } } \right] ^ { 2 } + \operatorname { I m } ^ { 2 } G ( { \mathrm { j } } \omega ) = \left( { \frac { 1 } { 2 } } \right) ^ { 2 }$

表明 RC 网络的幅相曲线是以 $\left( { \frac { 1 } { 2 } } , \mathrm { j 0 } \right)$ 为圆心，半径为 $\frac { 1 } { 2 }$ 的半圆，如图 5-5 所示。

![](images/3c1fd7984388cd62642de1aa1dcdc2526859e0bacecd778d05b060d4c87dc55b.jpg)  
图 5-5 RC网络的幅相曲线

# (2) 对数频率特性曲线

它又称为伯德曲线或伯德图。对数频率特性曲线由对数幅频曲线和对数相频曲线组成，是工程中广泛使用的一组曲线。

对数频率特性曲线的横坐标按 lg分度，单位为弧度/秒(rad/s)，对数幅频曲线的纵坐标按

$$
L (\omega) = 2 0 \lg | G (\mathrm {j} \omega) | = 2 0 \lg A (\omega) \tag {5-20}
$$

线性分度，单位是分贝(dB)。对数相频曲线的纵坐标按 $\varphi ( \omega )$ 线性分度，单位为度(°)。由此构成的坐标系称为半对数坐标系。

对数分度和线性分度如图 5-6 所示，在线性分度中，当变量增大或减小 1 时，坐标间距离变化一个单位长度；而在对数分度中，当变量增大或减小 10 倍，称为十倍频程(dec)，坐标间距离变化一个单位长度。设对数分度中的单位长度为 $L$ ，的某个十倍频程的左端点为 $\omega _ { 0 }$ ，则坐标点相对于左端点的距离为表 5-1 所示值乘以 $L$ 。

![](images/cde340b2e14318908df683d3e80aaaeb276ee7f608bb314e957731e72b84584f.jpg)

![](images/1bf2a327de6c7fd8d50a4ab7f7ef4b2dcd198d2200758f705ab9f003036af247.jpg)  
  
图 5-6 对数分度与线性分度

表 5-1 十倍频程中的对数分度  

<table><tr><td>\( \omega /{\omega }_{0} \)</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td><td>8</td><td>9</td><td>10</td></tr><tr><td>\( \lg \left( {\omega /{\omega }_{0}}\right) \)</td><td>0</td><td>0.301</td><td>0.477</td><td>0.602</td><td>0.699</td><td>0.788</td><td>0.845</td><td>0.903</td><td>0.954</td><td>1</td></tr></table>

对数频率特性采用的对数分度实现了横坐标的非线性压缩，便于在较大频率范围反映频率特性的变化情况。对数幅频特性采用 $2 0 1 \mathrm { g } A ( \omega )$ 则将幅值的乘除运算化为加减运算，可以简化曲线的绘制过程。RC 网络中取 $T { = } 0 . 5$ ，其对数频率特性曲线如图 5-7所示。

# (3) 对数幅相曲线

对数幅相曲线又称尼科尔斯曲线或尼科尔斯图。其特点是纵坐标为 $L ( \omega )$ ，单位为分贝(dB)，横坐标为 $\varphi ( \omega )$ ，单位为度 ${ \bf \Pi } ^ { ( \circ ) }$ ，均为线性分度，频率为参变量。图 5-8 为 RC 网络 $T { = } 0 . 5$ 时的尼科尔斯曲线。

![](images/5888423f4c2dcf10bbf846728c995a91fe4184f3429198c23bbd1b4b1d4de3f3.jpg)  
图 5-7 $\frac { 1 } { 1 + \mathrm { j } 0 . 5 \omega }$ 的对数频率特性曲线

![](images/518a5e7a76a4352f767b3bff782542a6601113ea1ac61e755afe904890514a2f.jpg)  
图 5-8 $\frac { 1 } { 1 + \mathrm { j } 0 . 5 \omega }$ 的对数幅相曲线

在尼科尔斯曲线对应的坐标系中，可以根据系统开环和闭环的关系，绘制关于闭环幅频特性的等 $M$ 簇线和闭环相频特性的等 $\alpha$ 簇线，因而可以根据频域指标要求确定校正网络，简化系统的设计过程。

# 5-2 典型环节与开环系统的频率特性

设线性定常系统结构如图 5-9所示，其开环传递函数为 $G ( s ) H ( s )$ ，为了绘制系统开环频率特性曲线，本节先研究开环系统的典型环节及相应的频率特性。

![](images/849d778cbef26c3f1f002857bc957d6f6724a8c1a5bd61f1bc612f2e4a0d0b02.jpg)  
图 5-9 典型系统结构图

# 1. 典型环节

由于开环传递函数的分子和分母多项式的系数皆为实数，系统开环零极点或为实数或为共轭复数。根据开环零极点可将分子和分母多项式分解成因式，再将因式分类，即得典型环节。典型环节可分为两大类：一类为最小相位环节；另一类为非最小相位环节。

最小相位环节有七种：

1) 比例环节 $K$ $( K > 0 )$ ；

2) 惯性环节 $1 / ( T s + 1 )$ $( T > 0 )$   
3) 一阶微分环节 $T s + 1$ $( T > 0 )$ ；  
4) 振荡环节 $1 / \left( s ^ { 2 } / \omega _ { n } ^ { 2 } + 2 \zeta s / \omega _ { n } + 1 \right)$ $( \omega _ { n } > 0 , 0 \leqslant \zeta < 1 )$   
5) 二阶微分环节 $s ^ { 2 } / \omega _ { n } ^ { 2 } + 2 \zeta s / \omega _ { n } + 1$ $( \omega _ { n } > 0 , 0 \leqslant \zeta < 1 )$   
6) 积分环节 $1 / s$ ；  
7) 微分环节 $s$

非最小相位环节有五种：

1) 比例环节 $K$ $( K < 0 )$   
2) 惯性环节 $1 / ( - T s + 1 )$ $( T > 0 )$ ;   
3) 一阶微分环节 $- T s + 1$ $( T > 0 )$   
4) 振荡环节 $1 / \left( s ^ { 2 } / \omega _ { n } ^ { 2 } - 2 \zeta s / \omega _ { n } + 1 \right)$ $1 / \left( s ^ { 2 } / \omega _ { n } ^ { 2 } - 2 \zeta s / \omega _ { n } + 1 \right) \qquad \left( \omega _ { n } > 0 , 0 < \zeta < 1 \right) ;$ $( \omega _ { n } > 0 , 0 < \zeta < 1 )$   
5) 二阶微分环节 $s ^ { 2 } / \omega _ { n } ^ { 2 } - 2 \zeta s / \omega _ { n } + 1$ $( \omega _ { n } > 0 , 0 < \zeta < 1 ) \textrm { o }$

除了比例环节外，非最小相位环节和与之相对应的最小相位环节的区别在于开环零极点的位置。非最小相位环节 $2 ) { \sim } 5 )$ )对应于 $s$ 开右半平面的开环零点或极点，而最小相位环节 2)～5)环节对应 $s$ 左半面的开环零点或极点。

开环传递函数的典型环节分解可将开环系统表示为若干个典型环节的串联形式

$$
G (s) H (s) = \prod_ {i = 1} ^ {N} G _ {i} (s) \tag {5-21}
$$

设典型环节的频率特性为

$$
G _ {i} (\mathrm {j} \omega) = A _ {i} (\omega) \mathrm {e} ^ {\mathrm {j} \varphi_ {i} (\omega)} \tag {5-22}
$$

则系统开环频率特性

$$
G (\mathrm {j} \omega) H (\mathrm {j} \omega) = \left[ \prod_ {i = 1} ^ {N} A _ {i} (\omega) \right] e ^ {\mathrm {j} \left[ \sum_ {i = 1} ^ {N} \varphi_ {i} (\omega) \right]} \tag {5-23}
$$

系统开环幅频特性和开环相频特性

$$
A (\omega) = \prod_ {i = 1} ^ {N} A _ {i} (\omega), \quad \varphi (\omega) = \sum_ {i = 1} ^ {N} \varphi_ {i} (\omega) \tag {5-24}
$$

系统开环对数幅频特性

$$
L (\omega) = 2 0 \lg A (\omega) = \sum_ {i = 1} ^ {N} 2 0 \lg A _ {i} (\omega) = \sum_ {i = 1} ^ {N} L _ {i} (\omega) \tag {5-25}
$$

式(5-24)和式(5-25)表明，系统开环频率特性表现为组成开环系统的诸典型环节频率特性的合成；而系统开环对数频率特性，则表现为诸典型环节对数频率特性叠加这一更为简单的形式。因此，本节研究典型环节频率特性的特点，在此基础上，介绍开环频率特性曲线的绘制方法。

# 2. 典型环节的频率特性

由典型环节的传递函数和频率特性的定义，取 $\omega \in ( 0 , + \infty )$ ，可以绘制典型环节的幅相

特性曲线和对数频率特性曲线分别如图 5-10 和图 5-11 所示。

![](images/2c5a854849e6eab7ef2c40cc26046980c796b3f288c14d25f2b27f5aef5e4f95.jpg)

![](images/40d28b252def2420aa6a967200f05d6d4896af418526f019110d6f18a6098924.jpg)  
与最小相位(积分/微分)环节

![](images/53c9b7f8fde81b8cebb5b7904158dce10abcd5d22b3db62012d257d64afde8c1.jpg)  
(振荡/二阶微分)环节   
图 5-10 典型环节幅相特性曲线

![](images/d90b988f2db6de097c85d715cc7e9711867caaeae44edc8f3796d979485d9235.jpg)

![](images/7f76ceceef96630a28aeb494e0b5c0091b6659d554dd36c67a596936ca497626.jpg)  
(a) (最小/非最小)相位比例环节 与最小相位(积分/微分)环节   
(惯性/一阶微分)环节

![](images/fd89159e5fbcbc0ce96b83bdd6f02449a1dc25fa5d4e1ceb259cc143b30ccced.jpg)  
(c) (最小/非最小)相位  
图 5-11 典型环节对数频率特性曲线(伯德图)

为了加深对典型环节频率特性的理解，以下介绍典型环节频率特性曲线的若干重要特点。

# (1) 非最小相位环节与对应的最小相位环节

对于每一种非最小相位的典型环节，都有一种最小相位环节与之对应，其特点是典型环节中的某个参数的符号相反。

最小相位的比例环节 $G ( s ) { = } K ( K > 0 )$ ，简称为比例环节，其幅频和相频特性为

$$
A (\omega) = K, \quad \varphi (\omega) = 0 ^ {\circ} \tag {5-26}
$$

非最小相位的比例环节 $G ( s ) { = } { - } K ( K > 0 )$ ，其幅频和相频特性为

$$
A (\omega) = K, \quad \varphi (\omega) = - 1 8 0 ^ {\circ} \tag {5-27}
$$

最小相位的惯性环节 $G ( s ) = { \frac { 1 } { 1 + T s } } \left( T > 0 \right)$ ，其幅频和相频特性为

$$
A (\omega) = \frac {1}{\left(1 + T ^ {2} \omega^ {2}\right) ^ {\frac {1}{2}}}, \quad \varphi (\omega) = - \arctan T \omega \tag {5-28}
$$

非最小相位的惯性环节，又称为不稳定惯性环节， $G ( s ) = { \frac { 1 } { 1 - T s } } \left( T > 0 \right)$ ，其幅频和相

频特性为

$$
A (\omega) = \frac {1}{\left(1 + T ^ {2} \omega^ {2}\right) ^ {\frac {1}{2}}}, \quad \varphi (\omega) = \arctan T \omega \tag {5-29}
$$

由式(5-28)和式(5-29)可知，最小相位惯性环节和非最小相位的惯性环节，其幅频特性相同，相频特性符号相反，幅相曲线关于实轴对称；对数幅频曲线相同，对数相频曲线关于 $0 ^ { \circ }$ 线对称。上述特点对于振荡环节和非最小相位(或不稳定)振荡环节、一阶微分环节和非最小相位一阶微分环节、二阶微分环节和非最小相位二阶微分环节均适用。

# (2) 传递函数互为倒数的典型环节

最小相位典型环节中，积分环节和微分环节、惯性环节和一阶微分环节、振荡环节和二阶微分环节的传递函数互为倒数，即有下述关系成立：

$$
G _ {1} (s) = 1 / G _ {2} (s) \tag {5-30}
$$

设 $G _ { 1 } ( \mathrm { j } \omega ) { = } A _ { 1 } ( \omega ) \mathrm { e } ^ { \mathrm { j } \varphi _ { 1 } ( \omega ) }$ ，则

$$
\left\{ \begin{array}{l} \varphi_ {2} (\omega) = - \varphi_ {1} (\omega) \\ L _ {2} (\omega) = 2 0 \lg A _ {2} (\omega) = 2 0 \lg \frac {1}{A _ {1} (\omega)} = - L _ {1} (\omega) \end{array} \right. \tag {5-31}
$$

由此可知，传递函数互为倒数的典型环节，对数幅频曲线关于 0dB 线对称，对数相频曲线关于 $0 ^ { \circ }$ 线对称。在非最小相位环节中，同样存在传递函数互为倒数的典型环节，其对数频率特性曲线的对称性亦成立。

# (3) 振荡环节和二阶微分环节

振荡环节的传递函数为

$$
G (s) = \frac {1}{\left(s / \omega_ {n}\right) ^ {2} + 2 \zeta \left(s / \omega_ {n}\right) + 1}; \quad \omega_ {n} > 0, \quad 0 <   \zeta <   1 \tag {5-32}
$$

振荡环节的频率特性

$$
A (\omega) = \frac {1}{\sqrt {\left(1 - \frac {\omega^ {2}}{\omega_ {n} ^ {2}}\right) ^ {2} + 4 \zeta^ {2} \frac {\omega^ {2}}{\omega_ {n} ^ {2}}}} \tag {5-33}
$$

$$
\varphi (\omega) = - \arctan \frac {2 \zeta \frac {\omega}{\omega_ {n}}}{1 - \frac {\omega^ {2}}{\omega_ {n} ^ {2}}} = \left\{ \begin{array}{l l} - \arctan \frac {2 \zeta \frac {\omega}{\omega_ {n}}}{1 - \frac {\omega^ {2}}{\omega_ {n} ^ {2}}}, & \omega \leqslant \omega_ {n} \\ - \left(1 8 0 ^ {\circ} - \arctan \frac {2 \zeta \frac {\omega}{\omega_ {n}}}{\frac {\omega^ {2}}{\omega_ {n} ^ {2}} - 1}\right), & \omega > \omega_ {n} \end{array} \right. \tag {5-34}
$$

显然， $\varphi ( 0 ) { = } 0 ^ { \circ }$ ， $\varphi ( \infty ) = - 1 8 0 ^ { \circ }$ ，且相频特性曲线从 $0 ^ { \circ }$ 单调减至 $- 1 8 0 ^ { \circ }$ 。当 $\omega { = } \omega _ { n }$ 时，

$\varphi ( \omega _ { n } ) { = } - 9 0 ^ { \circ }$ ，由式(5-33)得 $A ( \omega _ { n } ) = \frac { 1 } { 2 \zeta }$ ，表明振荡环节与虚轴的交点为 $- \mathrm { j } \frac { 1 } { 2 \zeta }$

由式(5-33)可得 $A ( 0 ) { = } 1$ , $A ( \infty ) { = } 0$ 。为分析 $A ( \omega )$ 的变化，求 $A ( \omega )$ 的极值，即令

$$
\frac {\mathrm {d} A (\omega)}{\mathrm {d} \omega} = \frac {- \left[ - \frac {2 \omega}{\omega_ {n} ^ {2}} \left(1 - \frac {\omega^ {2}}{\omega_ {n} ^ {2}}\right) + 4 \zeta^ {2} \frac {\omega}{\omega_ {n} ^ {2}} \right]}{\left[ \left(1 - \frac {\omega^ {2}}{\omega_ {n} ^ {2}}\right) ^ {2} + 4 \zeta^ {2} \frac {\omega^ {2}}{\omega_ {n} ^ {2}} \right] ^ {\frac {3}{2}}} = 0 \tag {5-35}
$$

得谐振频率

$$
\omega_ {r} = \omega_ {n} \sqrt {1 - 2 \zeta^ {2}}, \quad 0 <   \zeta \leqslant \sqrt {2} / 2 \tag {5-36}
$$

将 $\omega _ { r }$ 代入式(5-33)，求得谐振峰值

$$
M _ {r} = A \left(\omega_ {r}\right) = \frac {1}{2 \zeta \sqrt {1 - \zeta^ {2}}}, \quad 0 <   \zeta \leqslant \sqrt {2} / 2 \tag {5-37}
$$

因为 $\zeta = \frac { \sqrt { 2 } } { 2 }$ 时 $M _ { r } { = } 1$ ，当 $0 < \zeta < \frac { \sqrt { 2 } } { 2 }$ 时

$$
\frac {\mathrm {d} M _ {r}}{\mathrm {d} \zeta} = \frac {- (1 - 2 \zeta^ {2})}{\zeta^ {2} (1 - \zeta^ {2}) ^ {\frac {3}{2}}} <   0 \tag {5-38}
$$

可见 $\omega _ { r }$ ， $M _ { r }$ 均为阻尼比 的减函数 $( 0 < \zeta \leqslant \frac { \sqrt { 2 } } { 2 } )$ )。 当 $0 { < } \zeta { < } \frac { \sqrt { 2 } } { 2 }$ 且 $\omega \in ( 0 , \omega _ { r } )$ 时， $A ( \omega )$ 单调增； $\omega \in ( \omega _ { r } , \infty )$ 时， $A ( \omega )$ 单调减。而当 $\frac { \sqrt { 2 } } { 2 } < \zeta < 1$ 时， $A ( \omega )$ 单调减。不同阻尼比 $\zeta$ 情况下，振荡环节的幅相特性曲线和对数频率特性曲线分别如图 5-12 和图 5-13 所示，其中 u= $u { = } \frac { \omega } { \omega _ { n } }$ n

二阶微分环节的传递函数为振荡环节传递函数的倒数，按对称性可得二阶微分环节的对数频率曲线，并有

$$
\left\{ \begin{array}{l} A (0) = 1 \\ \varphi (0) = 0 ^ {\circ} ^ {\prime} \end{array} \right. \quad \left\{ \begin{array}{l} A (\omega_ {n}) = 2 \zeta \\ \varphi (\omega_ {n}) = 9 0 ^ {\circ} ^ {\prime} \end{array} \right. \quad \left\{ \begin{array}{l} A (\infty) = \infty \\ \varphi (\infty) = 1 8 0 ^ {\circ} \end{array} \right.
$$

当阻尼比 $\frac { \sqrt { 2 } } { 2 } < \zeta < 1$ 时， $A ( \omega )$ 从 1 单调增至 $\infty$ ；当阻尼比 $0 < \zeta < \frac { \sqrt { 2 } } { 2 }$ ， 且 $\omega \in ( 0 , \omega _ { r } )$ 时，$A ( \omega )$ 从 1单调减至

$$
\left\{ \begin{array}{l} A \left(\omega_ {r}\right) = 2 \zeta \sqrt {1 - \zeta^ {2}} <   1 \\ \omega_ {r} = \omega_ {n} \sqrt {1 - 2 \zeta^ {2}} \end{array} \right. \tag {5-39}
$$

而在 $\omega \in ( \omega _ { r } , \infty )$ 时， $A ( \omega )$ 单调增，二阶微分环节的概略幅相特性曲线如图 5-14 所示。

![](images/919605f3275e1c6c9b901ad07420200bc7308e687d132e3413d2592ae22da02f.jpg)  
图 5-12 振荡环节的幅相特性曲线

![](images/32dc86b2bca0589688dd4d07aeb3a5e2761cabd03d8dfedd392a5b734e63491f.jpg)  
图 5-13 振荡环节的对数频率特性曲线

非最小相位的二阶微分环节和不稳定振荡环节的频率特性曲线可按前述(1)中结论以及二阶微分环节和振荡环节的频率特性曲线加以确定。

# (4) 对数幅频渐近特性曲线

在控制工程中，为简化惯性环节、一阶微分环节、振荡环节和二阶微分环节的对数幅频曲线的作图，常用低频和高频渐近线近似表示对数幅频曲线，称之为对数幅频渐近特性曲线。

![](images/ee7862d6d5b49ed03e47c13099321442f7993e4006d0fb96aa65c7b39854c746.jpg)  
图 5-14 二阶微分环节的概略幅相特性曲线

对于惯性环节，对数幅频特性为

$$
L (\omega) = - 2 0 \lg \sqrt {1 + \omega^ {2} T ^ {2}} \tag {5-40}
$$

当 $\omega \ll { \frac { 1 } { T } }$ 时， $\omega ^ { 2 } T ^ { 2 } { \approx } 0$ ，有

$$
L (\omega) \approx - 2 0 \lg 1 = 0 \tag {5-41}
$$

当 $\omega \gg \frac { 1 } { T }$ 时， $\omega ^ { 2 } T ^ { 2 } \gg 1$ ，有

$$
L (\omega) \approx - 2 0 \lg \omega T \tag {5-42}
$$

因此惯性环节的对数幅频渐近特性为

$$
L _ {a} (\omega) = \left\{ \begin{array}{l l} 0, & \omega <   \frac {1}{T} \\ - 2 0 \lg \omega T, & \omega > \frac {1}{T} \end{array} \right. \tag {5-43}
$$

惯性环节的对数幅频渐近特性曲线如图 5-15所示，低频部分是零分贝线，高频部分是斜率为20dB/dec 的直线，两条直线交于 $\omega = { \frac { 1 } { T } }$ 处，称频率 $\frac { 1 } { T }$ 为惯性环节的交接频率。用渐近特性近似表示对数幅频特性存在误差

$$
\Delta L (\omega) = L (\omega) - L _ {a} (\omega) \tag {5-44}
$$

误差曲线如图 5-16所示。在交接频率处误差最大，约为3dB。根据误差曲线，可修正渐近特性曲线获得准确曲线。

![](images/7f1064b9b2eb9ba747c3cbf23c7fcea266e44d053ad6aa221a626e51b191c72f.jpg)  
图 5-15 惯性环节的对数幅频渐近特性曲线

![](images/825447afa075d25c171b78f7a46d0777d60d51798f613760fdd5c621eb3d4651.jpg)  
图 5-16 惯性环节的误差曲线

由于非最小相位惯性环节的对数幅频特性与惯性环节相同，故其对数幅频渐近特性亦相同。根据一阶微分环节和非最小相位一阶微分环节的对数幅频特性相等，且与惯性环节对数幅频特性互为倒数的特点，可知一阶微分环节和非最小相位一阶微分环节与惯性环节的对数幅频渐近特性曲线以0dB线互为镜像。

振荡环节的对数幅频特性为

$$
L (\omega) = - 2 0 \lg \sqrt {\left(1 - \frac {\omega^ {2}}{\omega_ {n} ^ {2}}\right) ^ {2} + 4 \zeta^ {2} \frac {\omega^ {2}}{\omega_ {n} ^ {2}}} \tag {5-45}
$$

当 $\omega \ll \omega _ { n }$ 时， $L ( \omega ) \approx 0$ ，低频渐近线为 0dB 线。而当 $\omega \gg \omega _ { n }$ 时， $L ( \omega ) { = } { - } 4 0 1 \mathrm { g } { \frac { \omega } { \omega _ { n } } }$ ，高频渐n近线为过 $( \omega _ { n } , 0 )$ 点，斜率为40dB/dec 的直线。振荡环节的交接频率为 $\omega _ { n }$ ，对数幅频渐近特性为

$$
L _ {a} (\omega) = \left\{ \begin{array}{l l} 0, & \omega <   \omega_ {n} \\ - 4 0 \lg \frac {\omega}{\omega_ {n}}, & \omega > \omega_ {n} \end{array} \right. \tag {5-46}
$$

由于 $L ( \omega )$ 中含有 $\zeta$ ，而 $L _ { a } ( \omega )$ 与阻尼比 无关，所以用渐近线近似表示对数幅频曲线存在误差，且误差的大小与 $\zeta$ 有关，误差曲线 $\Delta L ( \omega , \ \zeta )$ 为一曲线簇，如图 5-17 所示。根据误差曲线可以修正渐近特性曲线而获得准确曲线。

![](images/a865998962a77b6176e91eae7f37db34e2e9ea3900bd0effd4157d1b1972a56d.jpg)  
图 5-17 振荡环节的误差曲线

根据对数幅频特性定义还可知，非最小相位振荡环节与振荡环节的对数幅频渐近特性曲线相同，二阶微分环节和非最小相位二阶微分环节与振荡环节的对数幅频渐近特性曲线关于 0dB 线对称。

这里还应指出，半对数坐标系中的直线方程为

$$
k = \frac {L _ {a} \left(\omega_ {2}\right) - L _ {a} \left(\omega_ {1}\right)}{\lg \omega_ {2} - \lg \omega_ {1}} \tag {5-47}
$$

其中 $[ \omega _ { 1 }$ ， $L _ { a } ( \omega _ { 1 } ) ]$ 和 $\underline { \cdot } \omega _ { 2 }$ ， $L _ { a } ( \omega _ { 2 } ) ]$ 为直线上的两点，k(dB/dec)为直线斜率。

# 3. 开环幅相特性曲线

根据系统开环频率特性的表达式，可以通过取点、计算和作图等方法绘制系统开环幅相特性曲线。这里着重介绍结合工程需要，绘制概略开环幅相特性曲线的方法。

概略开环幅相特性曲线应反映开环频率特性的三个重要因素：

1) 开环幅相特性曲线的起点( $\scriptstyle ( \omega = 0 _ { + } )$ )和终点 $( \omega \mathrm { = } \infty )$ 。  
2) 开环幅相特性曲线与实轴的交点。设 $\omega { = } a b _ { x }$ 时， $G ( \mathrm { j } \omega _ { x } ) H ( \mathrm { j } \omega _ { x } )$ 的虚部为

$$
\operatorname {I m} \left[ G (\mathrm {j} \omega_ {x}) H (\mathrm {j} \omega_ {x}) \right] = 0 \tag {5-48}
$$

或

$$
\varphi \left(\omega_ {x}\right) = \angle [ G (\mathrm {j} \omega_ {x}) H (\mathrm {j} \omega_ {x}) ] = k \pi ; \quad k = 0, \pm 1, \pm 2, \dots \tag {5-49}
$$

称 $\omega _ { x }$ 为穿越频率，而开环频率特性曲线与实轴交点的坐标值为

$$
\operatorname {R e} \left[ G (\mathrm {j} \omega_ {x}) H (\mathrm {j} \omega_ {x}) \right] = G (\mathrm {j} \omega_ {x}) H (\mathrm {j} \omega_ {x}) \tag {5-50}
$$

3) 开环幅相特性曲线的变化范围(象限、单调性)。开环系统典型环节分解和典型环节幅相特性曲线的特点是绘制概略开环幅相特性曲线的基础，下面结合具体的系统加以介绍。

# 例 5-1 某 0 型单位反馈系统

![](images/e2042deb3131e4e9b823a71064821edfc741f39797c1cfc92f90b9e4a00e93a5.jpg)

$$
G (s) = \frac {K}{\left(T _ {1} s + 1\right) \left(T _ {2} s + 1\right)}; \quad K, T _ {1}, T _ {2} > 0
$$

试概略绘制系统开环幅相特性曲线。

解 由于惯性环节的角度变化为 $0 ^ { \circ } \sim \_ 9 0 ^ { \circ }$ ，故该系统开环幅相特性曲线

起点： $A ( 0 ) = K$ , $\varphi ( 0 ) = 0 ^ { \circ }$

终点： $A ( \infty ) = 0$ , $\varphi ( \infty ) = 2 \times ( - 9 0 ^ { \circ } ) = - 1 8 0 ^ { \circ }$

系统开环频率特性

$$
G (\mathrm {j} \omega) = \frac {K \left[ 1 - T _ {1} T _ {2} \omega^ {2} - \mathrm {j} \left(T _ {1} + T _ {2}\right) \omega \right]}{\left(1 + T _ {1} ^ {2} \omega^ {2}\right) \left(1 + T _ {2} ^ {2} \omega^ {2}\right)}
$$

令 $\mathrm { I m } G ( \mathrm { j } \omega _ { x } ) { = } 0$ ，得 $\omega _ { x } { = } 0$ ，即系统开环幅相特性曲线除在 $\omega { = } 0$ 处外与实轴无交点。

由于惯性环节单调地从 $0 ^ { \circ }$ 变化至 $\boldsymbol { \cdot } 9 0 ^ { \circ }$ ，故该系统幅相特性曲线的变化范围为第Ⅳ和第Ⅲ象限，系统概略开环幅相曲线如图 5-18实线所示。

若取 $K { < } 0$ ，由于非最小相位比例环节的相角恒为 $\cdot 1 8 0 ^ { \circ }$ ，故此时系统概略开环幅相特性曲线由原曲线绕原点顺时针旋转 $1 8 0 ^ { \circ }$ 而得，如图 5-18中虚线所示。

![](images/51b0d83458e69737372a1f1fc1f3272bea44be30c3f6a7916723112800a4a556.jpg)  
图 5-18 例5-1系统概略开环幅相特性曲线(MATLAB)

例 5-2 设系统开环传递函数为

$$
G (s) H (s) = \frac {K}{s \left(T _ {1} s + 1\right) \left(T _ {2} s + 1\right)}; \quad K, T _ {1}, T _ {2} > 0
$$

试绘制系统概略开环幅相特性曲线。

解 系统开环频率特性

$$
G (\mathrm {j} \omega) H (\mathrm {j} \omega) = \frac {K (1 - \mathrm {j} T _ {1} \omega) (1 - \mathrm {j} T _ {2} \omega) (- \mathrm {j})}{\omega (1 + T _ {1} ^ {2} \omega^ {2}) (1 + T _ {2} ^ {2} \omega^ {2})} = \frac {K \left[ - (T _ {1} + T _ {2}) \omega + \mathrm {j} (- 1 + T _ {1} T _ {2} \omega^ {2}) \right]}{\omega (1 + T _ {1} ^ {2} \omega^ {2}) (1 + T _ {2} ^ {2} \omega^ {2})}
$$

幅值变化： $A ( 0 _ { + } ) = \infty$ , $A ( \infty ) = 0$

$$
\begin{array}{l} \angle \left(\frac {1}{1 + \mathrm {j} T _ {1} \omega}\right): \quad 0 ^ {\circ} \sim - 9 0 ^ {\circ} \\ \angle \left(\frac {1}{1 + \mathrm {j} T _ {2} \omega}\right): \quad 0 ^ {\circ} \sim - 9 0 ^ {\circ} \\ \angle K: \quad 0 ^ {\circ} \sim 0 ^ {\circ} \\ \varphi (\omega): \quad - 9 0 ^ {\circ} \sim - 2 7 0 ^ {\circ} \\ \end{array}
$$

起点处： $\mathrm { R e } \big [ G ( \mathrm { j } 0 _ { + } ) H ( \mathrm { j } 0 _ { + } ) \big ] = - K ( T _ { 1 } + T _ { 2 } )$

$$
\operatorname {I m} \left[ G \left(\mathrm {j} 0 _ {+}\right) H \left(\mathrm {j} 0 _ {+}\right) \right] = - \infty
$$

与实轴的交点：令 $\operatorname { I m } \big [ G ( \mathrm { j } \omega ) H ( \mathrm { j } \omega ) \big ] = 0$ ，得 $\omega _ { x } = \frac { 1 } { \sqrt { T _ { 1 } T _ { 2 } } }$ ，于是

$$
G (\mathrm {j} \omega_ {x}) H (\mathrm {j} \omega_ {x}) = \operatorname {R e} \left[ G (\mathrm {j} \omega_ {x}) H (\mathrm {j} \omega_ {x}) \right] = - \frac {K T _ {1} T _ {2}}{T _ {1} + T _ {2}}
$$

由此做系统概略开环幅相特性曲线，如图 5-19 中曲线 $\textcircled{1}$ 所示。图中虚线为开环幅相特性曲线的低频渐近线。由于开环幅相特性曲线用于系统分析时不需要准确知道渐近线的位置，故一般根据 $\varphi ( 0 _ { + } )$ 取渐近线为坐标轴，图中曲线 $\textcircled{2}$ 为相应的概略开环幅相特性曲线。

![](images/395dd183644d65d54e1142ec8b24059dbe55daf550cf3bd074d1a718266c6fc1.jpg)  
图 5-19 例 5-2 系统概略开环幅相特性曲线

例 5-2 中系统型次即开环传递函数中积分环节个数 $\nu { = } 1$ ，若分别取 $\nu { = } 2$ ，3 和 4，则根据积分环节的相角，可将图 5-19 曲线分别绕原点旋转 $- 9 0 ^ { \circ }$ ， $- 1 8 0 ^ { \circ }$ 和 $- 2 7 0 ^ { \circ }$ ，即可得相应的概略开环幅相特性曲线，如图5-20所示。

![](images/595837d92dd9b55dd2280ba54a39a7ac51b0b97bb20ca3db691bbc7471430253.jpg)  
图 5-20 $\nu = 1 , 2 , 3 , 4$ 时系统概略开环幅相特性曲线(MATLAB)

例 5-3 已知单位反馈系统开环传递函数为

$$
G (s) = \frac {K (\tau s + 1)}{s \left(T _ {1} s + 1\right) \left(T _ {2} s + 1\right)}; \quad K, T _ {1}, T _ {2}, \tau > 0
$$

试绘制系统概略开环幅相特性曲线。

解 系统开环频率特性为

$$
G (\mathrm {j} \omega) = \frac {- \mathrm {j} K \left[ 1 - T _ {1} T _ {2} \omega^ {2} + T _ {1} \tau \omega^ {2} + T _ {2} \tau \omega^ {2} + \mathrm {j} \omega \left(\tau - T _ {1} - T _ {2} - T _ {1} T _ {2} \tau \omega^ {2}\right) \right]}{\omega \left(1 + T _ {1} ^ {2} \omega^ {2}\right) \left(1 + T _ {2} ^ {2} \omega^ {2}\right)}
$$

开环幅相曲线的起点 $G ( \mathrm { j } 0 _ { + } ) = \infty \angle ( - 9 0 ^ { \circ } )$ ，终点 $G ( \mathrm { j } \infty ) = 0 \angle ( - 1 8 0 ^ { \circ } )$ 。

与实轴的交点：当 $\tau < \frac { T _ { 1 } T _ { 2 } } { T _ { 1 } + T _ { 2 } }$ 时，得

$$
\left\{ \begin{array}{l} \omega_ {x} = \frac {1}{\sqrt {T _ {1} T _ {2} - T _ {1} \tau - T _ {2} \tau}} \\ G (\mathrm {j} \omega_ {x}) = - \frac {K (T _ {1} + T _ {2}) (T _ {1} T _ {2} - T _ {1} \tau - T _ {2} \tau + \tau^ {2})}{(T _ {1} T _ {2} - T _ {1} \tau - T _ {2} \tau + T _ {1} ^ {2}) (T _ {1} T _ {2} - T _ {1} \tau - T _ {2} \tau + T _ {2} ^ {2})} \end{array} \right.
$$

变化范围：

$\tau > \frac { T _ { 1 } T _ { 2 } } { T _ { 1 } + T _ { 2 } }$ 时，开环幅相特性曲线位于第Ⅲ象限或第Ⅳ与第Ⅲ象限；

$\tau < \frac { T _ { 1 } T _ { 2 } } { T _ { 1 } + T _ { 2 } }$ 时，开环幅相特性曲线位于第Ⅲ象限与第Ⅱ象限。

概略开环幅相特性曲线如图 5-21 所示。

应该指出，由于开环传递函数具有一阶微分环节，系统开环幅相特性曲线有凹凸现象，因为绘制的是概略幅相特性曲线，故这一现象无须准确反映。

例 5-4 已知系统开环传递函数为

$$
G (s) H (s) = \frac {K (- \tau s + 1)}{s (T s + 1)}; \quad K, \tau , T > 0
$$

试概略绘制系统概略开环幅相特性曲线。

解 系统开环频率特性为

$$
G (\mathrm {j} \omega) H (\mathrm {j} \omega) = \frac {K [ - (T + \tau) \omega - \mathrm {j} (1 - T \tau \omega^ {2}) ]}{\omega (1 + T ^ {2} \omega^ {2})}
$$

开环幅相特性曲线的起点： $A ( 0 _ { + } ) = \infty$ , $\varphi ( 0 _ { + } ) = - 9 0 ^ { \circ }$

开环幅相特性曲线的终点： $A ( \infty ) = 0$ , $\varphi ( \infty ) = - 2 7 0 ^ { \circ }$

与实轴的交点：令虚部为零，解得

$$
\omega_ {x} = \frac {1}{\sqrt {T \tau}}, \qquad G (\mathrm {j} \omega_ {x}) H (\mathrm {j} \omega_ {x}) = - K \tau
$$

因为 $\varphi ( \omega )$ 从 $- 9 0 ^ { \circ }$ 单调减至 $- 2 7 0 ^ { \circ }$ ，故幅相特性曲线在第Ⅲ与第Ⅱ象限间变化。

概略开环幅相特性曲线如图 5-22 所示。

![](images/9fc515f6fa4969dca4f63e3fac9e62fa086f2cf940ad0682c251f3d9cdd6e1bf.jpg)  
图 5-21 例5-3系统概略开环幅相特性曲线  
(MATLAB)

![](images/a56676d36bdecd76a3e93127045192c9db067382fc64a91b96839a75b0efed94.jpg)  
图 5-22 例5-4系统概略开环幅相特性曲线  
(MATLAB)

在例 5-4 中，系统含有非最小相位一阶微分环节，称开环传递函数含有非最小相位环节的系统为非最小相位系统，而开环传递函数全部由最小相位环节构成的系统称为最小相位系统。比较例 5-2、例 5-3和例 5-4可知，非最小相位环节的存在将对系统的频率特性产生一定的影响，故在控制系统分析中必须加以重视。

例 5-5 设系统开环传递函数为

$$
G (s) H (s) = \frac {K}{s \left(T s + 1\right) \left(s ^ {2} / \omega_ {n} ^ {2} + 1\right)}; \quad K, T > 0
$$

试绘制系统概略开环幅相特性曲线。

解 系统开环频率特性为

$$
G (\mathrm {j} \omega) H (\mathrm {j} \omega) = \frac {- K (T \omega + \mathrm {j})}{\omega (1 + T ^ {2} \omega^ {2}) \left(1 - \frac {\omega^ {2}}{\omega_ {n} ^ {2}}\right)}
$$

开环幅相特性曲线的起点：

$$
G \left(j 0 _ {+}\right) H \left(j 0 _ {+}\right) = \infty \angle (- 9 0 ^ {\circ})
$$

开环幅相特性曲线的终点：

$$
G (\mathrm {j} \infty) H (\mathrm {j} \infty) = 0 \angle (- 3 6 0 ^ {\circ})
$$

由开环频率特性表达式知， $G ( \mathrm { j } \omega ) H ( \mathrm { j } \omega )$ 的虚部不为零，故与实轴无交点。注意到开环系统含有等幅振荡环节 $( \zeta = 0 )$ )，当 $\omega$ 趋于 $\omega _ { n }$ 时， $A ( \omega _ { n } )$ 趋于无穷大，而相频特性

$$
\varphi \left(\omega_ {n -}\right) \approx - 9 0 ^ {\circ} - \arctan T \omega_ {n} > - 1 8 0 ^ {\circ}; \quad \omega_ {n -} = \omega_ {n} - \varepsilon , \quad \varepsilon > 0
$$

$$
\varphi \left(\omega_ {n +}\right) \approx - 9 0 ^ {\circ} - \arctan T \omega_ {n} - 1 8 0 ^ {\circ}; \quad \omega_ {n +} = \omega_ {n} + \varepsilon , \quad \varepsilon > 0
$$

即 $\varphi ( \omega )$ 在 $\omega { = } a b _ { n }$ 的附近，相角突变 $- 1 8 0 ^ { \circ }$ ，幅相曲线在 $\omega _ { n }$ 处呈现不连续现象。作系统概略开环幅相特性曲线如图 5-23 所示。

![](images/4188dec1b4986976ec58af0f1274b9bc7ffad01de4d08afda5fca9b892e87a0c.jpg)  
图 5-23 例5-5系统概略开环幅相特性曲线

根据以上例子，可以总结绘制概略开环幅相特性曲线的规律如下：

1) 开环幅相特性曲线的起点，取决于比例环节 $K$ 和系统积分或微分环节的个数 $\nu$ (系统型别)。

$\nu < 0$ ，起点为原点。

$\nu = 0$ ，起点为实轴上的点 $K$ 处 $( K$ 为系统开环增益，注意 $K$ 有正负之分)。

$\nu > 0$ ，设ν= 4k+i(k=0,1,2,； i=1,2,3,4),则 $K > 0$ 时为 $i \times ( - 9 0 ^ { \circ } )$ 的无穷远处， $K { < } 0$ 时为$i \times ( - 9 0 ^ { \circ } ) { - } 1 8 0 ^ { \circ }$ 的无穷远处。

2) 开环幅相特性曲线的终点，取决于开环传递函数分子、分母多项式中最小相位环节和非最小相位环节的阶次和。

设系统开环传递函数的分子、分母多项式的阶次分别为 $m$ 和 $n$ ，记除 $K$ 外，分子多项式中最小相位环节的阶次和为 $m _ { 1 }$ ，非最小相位环节的阶次和为 $m _ { 2 }$ ，分母多项式中最小相位环节的阶次和为 $n _ { 1 }$ ，非最小相位环节的阶次和为 $n _ { 2 }$ ，则有

$$
m = m _ {1} + m _ {2}, \quad n = n _ {1} + n _ {2}
$$

$$
\varphi (\infty) = \left\{ \begin{array}{l l} {\left[ \left(m _ {1} - m _ {2}\right) - \left(n _ {1} - n _ {2}\right) \right] \times 9 0 ^ {\circ},} & K > 0 \\ {\left[ \left(m _ {1} - m _ {2}\right) - \left(n _ {1} - n _ {2}\right) \right] \times 9 0 ^ {\circ} - 1 8 0 ^ {\circ},} & K <   0 \end{array} \right. \tag {5-51}
$$

特殊地，当开环系统为最小相位系统时，若

$$
n = m, \quad G (\mathrm {j} \infty) H (\mathrm {j} \infty) = K ^ {*} \tag {5-52}
$$

$$
n > m, \quad G (\mathrm {j} \infty) H (\mathrm {j} \infty) = 0 \angle [ (n - m) \times (- 9 0 ^ {\circ}) ] \tag {5-53}
$$

其中 $K ^ { * }$ 为系统开环根轨迹增益。

3) 若开环系统存在等幅振荡环节，重数 l 为正整数，即开环传递函数具有下述形式：

$$
G (s) H (s) = \frac {1}{\left(\frac {s ^ {2}}{\omega_ {n} ^ {2}} + 1\right) ^ {l}} G _ {1} (s) H _ {1} (s)
$$

$G _ { 1 } ( s ) H _ { 1 } ( s )$ 不含j $\omega _ { n }$ 的极点，则当 $\omega$ 趋于 $\omega _ { n }$ 时， $A ( \omega )$ 趋于无穷，而

$$
\varphi \left(\omega_ {n -}\right) \approx \varphi_ {1} \left(\omega_ {n}\right) = \angle \left[ G _ {1} (\mathrm {j} \omega_ {n}) H _ {1} (\mathrm {j} \omega_ {n}) \right]
$$

$$
\varphi \left(\omega_ {n +}\right) \approx \varphi_ {1} \left(\omega_ {n}\right) - l \times 1 8 0 ^ {\circ}
$$

即 $\varphi ( \omega )$ 在 $\omega { = } \omega _ { n }$ 附近，相角突变 $\cdot l \times 1 8 0 ^ { \circ }$ 。

# 4. 开环对数频率特性曲线

系统开环传递函数作典型环节分解后，根据式(5-21) $\sim$ 式(5-25)，可先作出各典型环节的对数频率特性曲线，然后采用叠加方法即可方便地绘制系统开环对数频率特性曲线。鉴于系统开环对数幅频渐近特性在控制系统的分析和设计中具有十分重要的作用，以下着重介绍开环对数幅频渐近特性曲线的绘制方法。

注意到典型环节中， $K$ 及 $\cdot K ( K { > } 0 )$ 、微分环节和积分环节的对数幅频特性曲线均为直线，故可直接取其为渐近特性。由式(5-25)得系统开环对数幅频渐近特性：

$$
L _ {a} (\omega) = \sum_ {i = 1} ^ {N} L _ {a _ {i}} (\omega) \tag {5-54}
$$

对于任意的开环传递函数，可按典型环节分解，将组成系统的各典型环节分为三部分：

1) $\frac { K } { s ^ { \nu } }$ 或 $\frac { - K } { s ^ { \nu } } ( K { > } 0 ) _ { \circ }$ sV   
2) 一阶环节，包括惯性环节、一阶微分环节以及对应的非最小相位环节，交接频率为 $1 / T$ 。  
3) 二阶环节，包括振荡环节、二阶微分环节以及对应的非最小相位环节，交接频率为n。 $\omega _ { n }$

记 $\omega _ { \mathrm { m i n } }$ 为最小交接频率，称 $\omega { < } \omega _ { \mathrm { m i n } }$ 的频率范围为低频段。开环对数幅频渐近特性曲线的绘制按以下步骤进行：

1) 开环传递函数典型环节分解。  
2) 确定一阶环节、二阶环节的交接频率，将各交接频率标注在半对数坐标图的 $\omega$ 轴上。  
3) 绘制低频段渐近特性线：由于一阶环节或二阶环节的对数幅频渐近特性曲线在交接频率前斜率为 0dB/dec，在交接频率处斜率发生变化，故在 $\omega { < } \omega _ { \mathrm { m i n } }$ 频段内，开环系统幅频渐近特性的斜率取决于 $K / \omega ^ { \nu }$ ，因而直线斜率为 $- 2 0 \nu \mathrm { d B } / \mathrm { d e c }$ 。为获得低频渐近线，还需确定该直线上的一点，可以采用以下三种方法。

方法一：在 $\omega { < } \omega _ { \mathrm { m i n } }$ 范围内，任选一点 $\omega _ { 0 }$ ，计算

$$
L _ {a} \left(\omega_ {0}\right) = 2 0 \lg K - 2 0 \nu \lg \omega_ {0} \tag {5-55}
$$

方法二：取频率为特定值 $\omega _ { 0 } { = } 1$ ，则

$$
L _ {a} (1) = 2 0 \lg K \tag {5-56}
$$

方法三：取 $L _ { a } ( \omega _ { 0 } )$ 为特殊值 0，有 $\frac { K } { \omega _ { 0 } ^ { \nu } } { = } 1$

$$
\omega_ {0} = K ^ {\frac {1}{\nu}} \tag {5-57}
$$

于是，过点 $( \omega 0 , L _ { a } ( \omega 0 ) )$ 在 $\omega { < } \omega _ { \mathrm { m i n } }$ 范围内可作斜率为20 dB/dec 的直线。显然，若有 $\omega _ { 0 } { > } \omega _ { \mathrm { m i n } }$ ，则点 $( \omega _ { 0 } , L _ { a } ( \omega _ { 0 } ) )$ 位于低频渐近特性曲线的延长线上。

4)作 $\omega \geqslant \omega _ { \mathrm { m i n } }$ 频段渐近特性线：在 $\omega \geqslant \omega _ { \mathrm { m i n } }$ 频段，系统开环对数幅频渐近特性曲线表现为分段折线。每两个相邻交接频率之间为直线，在每个交接频率点处，斜率发生变化，变化规律取决于该交接频率对应的典型环节的种类，如表5-2所示。

表 5-2 交接频率点处斜率的变化表  

<table><tr><td>典型环节类别</td><td>典型环节传递函数</td><td>交接频率</td><td>斜率变化</td></tr><tr><td rowspan="4">一阶环节(T&gt;0)</td><td>1/1+Ts</td><td rowspan="4">1/T</td><td rowspan="2">-20dB /dec</td></tr><tr><td>1/1-Ts</td></tr><tr><td>1+Ts</td><td rowspan="2">20dB /dec</td></tr><tr><td>1-Ts</td></tr><tr><td rowspan="4">二阶环节(ωn&gt;0,1&gt;ζ≥0)</td><td>1/(s^2/ωn^2+2ζ s/ωn+1)</td><td rowspan="4">ωn</td><td rowspan="2">-40dB /dec</td></tr><tr><td>1/(s^2/ωn^2-2ζ s/ωn+1)</td></tr><tr><td>s^2/ωn^2+2ζ s/ωn+1</td><td rowspan="2">40dB /dec</td></tr><tr><td>s^2/ωn^2-2ζ s/ωn+1</td></tr></table>

应该注意的是，当系统的多个环节具有相同交接频率时，该交接频率点处斜率的变化应为各个环节对应的斜率变化值的代数和。

以 $k { = } { \mathrm { - } } 2 0 \nu \mathrm { d B } / \mathrm { d e c }$ 的低频渐近线为起始直线，按交接频率由小到大顺序和由表 5-2确定斜率变化，再逐一绘制各段直线，得到系统开环对数幅频渐近特性曲线。

例 5-6 已知系统开环传递函数为

$$
G (s) H (s) = \frac {2 0 0 0 s - 4 0 0 0}{s ^ {2} (s + 1) (s ^ {2} + 1 0 s + 4 0 0)}
$$

试绘制系统开环对数幅频渐近特性曲线。

解 开环传递函数的典型环节分解形式为

$$
G (s) H (s) = \frac {- 1 0 \left(1 - \frac {s}{2}\right)}{s ^ {2} (s + 1) \left(\frac {s ^ {2}}{2 0 ^ {2}} + \frac {1}{2} \frac {s}{2 0} + 1\right)}
$$

开环系统由六个典型环节串联而成：非最小相位比例环节、两个积分环节、非最小相位一阶微分环节、惯性环节和振荡环节。

1) 确定各交接频率 $\omega _ { i }$ ， $i { = } 1 , 2 , 3$ 及斜率变化值。

非最小相位一阶微分环节： $\omega _ { 2 } { = } 2$ ，斜率增加 20dB/dec

惯性环节： $\omega _ { \mathrm { l } } { = } 1$ ，斜率减小 20dB/dec

振荡环节： $\omega _ { 3 } { = } 2 0$ ，斜率减小 40dB/dec

最小交接频率 $\omega _ { \mathrm { m i n } } { = } \omega _ { \mathrm { l } } { = } 1$ 。

2) 绘制低频段 $( \omega < \omega _ { \mathrm { m i n } } )$ 渐近特性曲线。因为 $\nu { = } 2$ ，则低频渐近线斜率 $k { = } { \mathrm { - } } 4 0 \mathrm { d } \mathrm { B } / \mathrm { d e c } .$ ，按方法二得直线上一点 $( \omega _ { 0 } , L _ { a } ( \omega _ { 0 } ) ) { = } ( 1 , 2 0 { \mathrm { d B } } ) _ { \circ }$ 。

3) 绘制频段 $\omega \geqslant \omega _ { \mathrm { m i n } }$ 渐近特性曲线。

$$
\omega_ {\min } \leqslant \omega <   \omega_ {2}, \quad k = - 6 0 \mathrm {d B} / \mathrm {d e c}
$$

$$
\omega_ {2} \leqslant \omega <   \omega_ {3}, \quad k = - 4 0 \mathrm {d B / d e c}
$$

$$
\omega \geqslant \omega_ {3}, \quad k = - 8 0 \mathrm {d B} / \mathrm {d e c}
$$

系统开环对数幅频渐近特性曲线如图 5-24 所示。

![](images/9a09e112a4145ddc2ec11a23470f99b82cf5d09b65ba277724940a81c622ad22.jpg)  
图 5-24 例 5-6 系统开环对数幅频渐近特性曲线(MATLAB)

开环对数相频特性曲线的绘制，一般由典型环节分解下的相频特性表达式，取若干

个频率点，列表计算各点的相角并标注在对数坐标图中，最后将各点光滑连接，即可得开环对数相频特性曲线。具体计算相角时应注意判别象限。例如在例5-6中

$$
\varphi (\omega) = \angle \left(\frac {1}{1 - \frac {\omega^ {2}}{4 0 0} + \mathrm {j} \frac {\omega}{4 0}}\right) = \left\{ \begin{array}{l l} - \arctan \frac {\frac {\omega}{4 0}}{1 - \frac {\omega^ {2}}{4 0 0}}, & 0 <   \omega \leqslant 2 0 \\ - \left(1 8 0 ^ {\circ} - \arctan \frac {\frac {\omega}{4 0}}{\frac {\omega^ {2}}{4 0 0} - 1}\right), & \omega > 2 0 \end{array} \right.
$$

# 5. 延迟环节和延迟系统

输出量经恒定延时后不失真地复现输入量变化的环节称为延迟环节。含有延迟环节的系统称为延迟系统。化工、电力系统多为延迟系统。延迟环节的输入输出的时域表达式为

$$
c (t) = 1 (t - \tau) r (t - \tau) \tag {5-58}
$$

式中， $\tau$ 为延迟时间，应用拉氏变换的实数位移定理，可得延迟环节的传递函数

$$
G (s) = \frac {C (s)}{R (s)} = \mathrm {e} ^ {- \tau s} \tag {5-59}
$$

延迟环节的频率特性为

![](images/3499510daa1774466b23a2f71069f64c64a3c63881e16af296574c0f6ac6bd6e.jpg)  
图 5-25 延迟系统及其开环幅相特性曲线

$$
G (\mathrm {j} \omega) = \mathrm {e} ^ {- \mathrm {j} \tau \omega} = 1 \cdot \angle (- 5 7. 3 \tau \omega) \tag {5-60}
$$

由式(5-60)可知，延迟环节幅相特性曲线为单位圆。当系统存在延迟现象，即开环系统表现为延迟环节和线性环节的串联形式时，延迟环节对系统开环频率特性的影响是造成了相频特性的明显变化，如图 5-25 所示。当线性环节 $G ( s ) { = } \frac { 1 0 } { 1 + s }$ 与延迟环节 $\mathrm { e } ^ { - 0 . 5 s }$ 串联后，系统开环幅相特性曲线为螺旋线。图中以(5, j0)为圆心，半径为5的半圆为惯性环节的幅相特性曲线，任取频率点 $\omega$ ，设惯性环

节的频率特性点为 $A$ ，则延迟系统的幅相特性曲线的 $B$ 点位于以 $| O A |$ 为半径，距 $A$ 点圆心角 $\scriptstyle \theta = 5 7 . 3 \times 0 . 5 \omega$ 的圆弧处。

# 6. 传递函数的频域实验确定

由前可知，稳定系统的频率响应为与输入同频率的正弦信号，且其幅值和相位的变化为频率的函数，因此可以运用频率响应实验确定稳定系统的数学模型。

# (1) 频率响应实验

频率响应实验原理如图 5-26 所示。首先选择信号源输出的正弦信号的幅值，以使

系统处于非饱和状态。在一定频率范围内，改变输入正弦信号的频率，记录各频率点处系统输出信号的波形。由稳态段的输入输出信号的幅值比和相位差绘制对数频率特性曲线。

![](images/5c2844eafc67796256b52b4e878ff41e1a28ca5bcd0e26fdb6bb7477db111054.jpg)  
图 5-26 频率响应实验原理方框图

# (2) 传递函数确定

从低频段起，将实验所得的对数幅频特性曲线用斜率为 0dB/dec，20dB/dec，40dB/dec，…直线分段近似，获得对数幅频渐近特性曲线。

由对数幅频渐近特性曲线可以确定最小相位条件下系统的传递函数，这是对数幅频渐近特性曲线绘制的逆问题，下面举例说明其方法和步骤。

例 5-7 图 5-27 为由频率响应实验获得的某最小相位系统的开环对数幅频特性曲线和对数幅频渐近特性曲线，试确定系统传递函数。

![](images/53d30f0ef3228f220333476dd336caad262442614ff6a726de63e31c919ac54b.jpg)  
图 5-27 系统开环对数幅频特性曲线

解 1) 确定系统积分或微分环节的个数。因为对数幅频渐近特性曲线的低频渐近线的斜率为 $- 2 0 \nu \mathrm { d B } / \mathrm { d e c }$ ，而由图 5-27 知低频渐近线斜率为$+ 2 0 \mathrm { d B / d e c }$ ，故有 $\nu { = } { - } 1$ ，系统含有一个微分环节。

2) 确定系统传递函数结构形式。由于对数幅频渐近特性曲线为分段折线，其各转折点对应的频率为所含一阶环节或二阶环节的交接频率，每个交接频率处斜率的变化取决于环节的种类。本例

中共有两个交接频率：

$\omega { = } \omega _ { 1 }$ 处，斜率变化-20dB/dec，对应惯性环节。

$\omega { = } \omega _ { 2 }$ 处，斜率变化-40dB/dec，可以对应振荡环节也可以为重惯性环节，本例中，对数幅频特性在 $\omega _ { 2 }$ 附近存在谐振现象，故应为振荡环节。因此所测系统应具有下述传递函数：

$$
G (s) = \frac {K s}{\left(1 + \frac {s}{\omega_ {1}}\right) \left(\frac {s ^ {2}}{\omega_ {2} ^ {2}} + 2 \zeta \frac {s}{\omega_ {2}} + 1\right)}
$$

其中参数 $\omega _ { \mathrm { l } }$ 、 $\omega _ { 2 }$ 、 $\zeta$ 及 $K$ 待定。

3)由给定条件确定传递函数参数。低频渐近线的方程为

$$
L _ {a} (\omega) = 2 0 \lg \frac {K}{\omega^ {\nu}} = 2 0 \lg K - 2 0 \nu \lg \omega
$$

由给定点 $( \omega , L _ { a } ( \omega ) ) { = } ( 1 , 0 )$ 及 $\nu { = } { - } 1$ 得 $K { = } 1$ 。

根据直线方程式(5-47)

$$
L _ {a} \left(\omega_ {a}\right) - L _ {a} \left(\omega_ {b}\right) = k \left(\lg \omega_ {a} - \lg \omega_ {b}\right)
$$

及给定点

$$
\omega_ {a} = 1, \quad L _ {a} (\omega_ {a}) = 0, \quad \omega_ {b} = \omega_ {1}, \quad L _ {a} (\omega_ {b}) = 1 2, \quad k = 2 0
$$

得 $\omega _ { 1 } = 1 0 ^ { \frac { 1 2 } { 2 0 } } = 3 . 9 8$

再由给定点

$$
\omega_ {a} = 1 0 0, \quad L _ {a} (\omega_ {a}) = 0, \quad \omega_ {b} = \omega_ {2}, \quad L _ {a} (\omega_ {b}) = 1 2, \quad k = - 4 0
$$

得 12 lg100 40 10          $\omega _ { 2 } = 1 0 ^ { \left( - \frac { 1 2 } { 4 0 } + \lg 1 0 0 \right) } = 5 0 . 1$

由前知，在谐振频率 $\omega _ { r }$ 处，振荡环节的谐振峰值为

$$
2 0 \lg M _ {r} = 2 0 \lg \frac {1}{2 \zeta \sqrt {1 - \zeta^ {2}}}
$$

而根据叠加性质，本例中 $2 0 1 \mathrm { g } M _ { r } { = } 2 0 { - } 1 2 { = } 8 ( \mathrm { d B } )$ ，故有 $M _ { r } { = } 2 . 5 1 2$ ，于是有

解得 $\zeta _ { 1 } = 0 . 2 0 4 , ~ \zeta _ { 2 } = 0 . 9 7 9$

$$
\zeta^ {4} - \zeta^ {2} + 0. 0 4 = 0
$$

因为 $0 { < } \zeta { < } 0 . 7 0 7$ 时才存在谐振峰值，故应选 $\zeta { = } 0 . 2 0 4$ 。于是，所测系统的传递函数为

$$
G (s) = \frac {s}{\left(\frac {s}{3 . 9 8} + 1\right) \left(\frac {s ^ {2}}{5 0 . 1 ^ {2}} + 0 . 4 0 8 \frac {s}{5 0 . 1} + 1\right)}
$$

值得注意的是，实际系统并不都是最小相位系统，而最小相位系统可以和某些非最小相位系统具有相同的对数幅频特性曲线，因此具有非最小相位环节和延迟环节的系统，还需依据上述环节对相频特性的影响并结合实测相频特性予以确定。

# 5-3 频率域稳定判据

控制系统的闭环稳定性是系统分析和设计所需解决的首要问题，奈奎斯特稳定判据(简称奈氏判据)和对数频率稳定判据是常用的两种频域稳定判据。频域稳定判据的特点是根据开环系统频率特性曲线判定闭环系统的稳定性。频域判据使用方便，易于推广。

# 1. 奈氏判据的数学基础

复变函数中的幅角原理是奈氏判据的数学基础，幅角原理用于控制系统的稳定性的判定还需选择辅助函数和闭合曲线。

# (1) 幅角原理

设 $s$ 为复数变量， $F ( s )$ 为 $s$ 的有理分式函数。对于 $s$ 平面上任意一点 $s$ ，通过复变函数 $F ( s )$ 的映射关系，在 $F ( s )$ 平面上可以确定关于 $s$ 的象。在 $s$ 平面上任选一条闭合曲线 $\varGamma$ ，且不通过 $F ( s )$ 的任一零点和极点，令 $s$ 从闭合曲线 $\varGamma$ 上任一点 $A$ 起，顺时针沿 $\varGamma$ 运动一周，再回到 $A$ 点，则相应地， $F ( s )$ 平面上亦从点 $F ( A )$ 起，到 $F ( A )$ 点止亦形成一条闭合曲线 $\boldsymbol { { \Gamma } } _ { \boldsymbol { F } }$ 。为讨论方便，取 $F ( s )$ 为下述简单形式：

$$
F (s) = \frac {(s - z _ {1}) (s - z _ {2})}{(s - p _ {1}) (s - p _ {2})} \tag {5-61}
$$

其中 $z _ { 1 }$ ， $z _ { 2 }$ 为 $F ( s )$ 的零点； $p _ { 1 }$ ， $p _ { 2 }$ 为 $F ( s )$ 的极点。不失一般性，取 $s$ 平面上 $F ( s )$ 的零点和极点以及闭合曲线的位置如图 5-28(a)所示， $\varGamma$ 包围 $F ( s )$ 的零点 $z _ { 1 }$ 和极点 $p _ { 1 }$ 。

![](images/c2f0cdfef4ca069a3d026aa5b0ece9392868b28d1fc19ef906f441572019aa40.jpg)

![](images/7951f2ad0cb33162a10786558e721c269f20dee4171d1f0016a29258ea9c19a6.jpg)  
  
图 5-28 $s$ 和 $F ( s )$ 平面的映射关系

设复变量 $s$ 沿闭合曲线 $\varGamma$ 顺时针运动一周，研究 $F ( s )$ 相角的变化情况

$$
\delta \angle [ F (s) ] = \oint_ {\Gamma} \angle [ F (s) ] d s \tag {5-62}
$$

因为

$$
\angle [ F (s) ] = \angle \left(s - z _ {1}\right) + \angle \left(s - z _ {2}\right) - \angle \left(s - p _ {1}\right) - \angle \left(s - p _ {2}\right) \tag {5-63}
$$

因而

$$
\delta \angle [ F (s) ] = \delta \angle \left(s - z _ {1}\right) + \delta \angle \left(s - z _ {2}\right) - \delta \angle \left(s - p _ {1}\right) - \delta \angle \left(s - p _ {2}\right) \tag {5-64}
$$

由于 $z _ { 1 }$ 和 $p _ { 1 }$ 被 $\varGamma$ 所包围，故按复平面向量的相角定义，逆时针旋转为正，顺时针旋转为负

$$
\delta \angle (s - z _ {1}) = \delta \angle (s - p _ {1}) = - 2 \pi
$$

而对于零点 $z _ { 2 }$ ，由于 $z _ { 2 }$ 未被 $\varGamma$ 所包围，过 $z _ { 2 }$ 作两条直线与闭合曲线 $\varGamma$ 相切，设 $s _ { 1 }$ ， $s _ { 2 }$ 为切点，则在 $\varGamma$ 的 $\widehat { s _ { 1 } s _ { 2 } }$ 段， $s \mathrm { - } z _ { 2 }$ 的角度减小，在 $\varGamma$ 的 $\widehat { s _ { 2 } s _ { 1 } }$ 段，角度增大，且有

$$
\delta \angle (s - z _ {2}) = \oint_ {\Gamma} \angle (s - z _ {2}) d s = \int_ {\Gamma s _ {1} s _ {2}} \angle (s - z _ {2}) d s + \int_ {\Gamma s _ {2} s _ {1}} \angle (s - z _ {2}) d s = 0
$$

$p _ { 2 }$ 未被 $\varGamma$ 包围，同理可得 $\delta \angle ( s - p _ { 2 } ) = 0$ 。

上述讨论表明，当 $s$ 沿 $s$ 平面任意闭合曲线 $\varGamma$ 运动一周时， $F ( s )$ 绕 $F ( s )$ 平面原点的圈数只和 $F ( s )$ 被闭合曲线 $\varGamma$ 所包围的极点和零点的代数和有关。上例中 $\delta \angle [ F ( s ) ] = 0$ 。因而，形成如下幅角原理。

幅角原理 设 $s$ 平面闭合曲线 $\varGamma$ 包围 $F ( s )$ 的 $Z$ 个零点和 $P$ 个极点，则 $s$ 沿 $\varGamma$ 顺时针运动一周时，在 $F ( s )$ 平面上， $F ( s )$ 闭合曲线 $\varGamma _ { F }$ 包围原点的圈数

$$
R = P - Z \tag {5-65}
$$

$R { < } 0$ 和 $R { > } 0$ 分别表示 $\varGamma _ { F }$ 顺时针包围和逆时针包围 $F ( s )$ 平面的原点， $R { = } 0$ 表示不包围 $F ( s )$ 平面的原点。

# (2) 复变函数 $F ( s )$ 的选择

控制系统的稳定性判定是利用已知开环传递函数来判定闭环系统的稳定性。为应用幅角原理，选择复变函数

$$
F (s) = 1 + G (s) H (s) = 1 + \frac {B (s)}{A (s)} = \frac {A (s) + B (s)}{A (s)} \tag {5-66}
$$

由式(5-66)可知， $F ( s )$ 具有以下特点：

1) $F ( s )$ 的零点为闭环传递函数的极点， $F ( s )$ 的极点为开环传递函数的极点。  
2) 因为开环传递函数分母多项式的阶次一般大于或等于分子多项式的阶次，故 $F ( s )$ 的零点和极点数相同。  
3) $s$ 沿闭合曲线 $\varGamma$ 运动一周所产生的两条闭合曲线 $\varGamma _ { F }$ 和 $\Gamma _ { G H }$ 只相差常数 1，即闭合曲线 $\varGamma _ { F }$ 可由 $\Gamma _ { G H }$ 沿实轴正方向平移一个单位长度获得。闭合曲线 $\varGamma _ { F }$ 包围 $F ( s )$ 平面原点的圈数等于闭合曲线 $\Gamma _ { G H }$ 包围 $F ( s )$ 平面(1，j0)点的圈数，其几何关系如图 5-29所示。

由 $F ( s )$ 的特点可以看出， $F ( s )$ 取上述特定形式具有两个优点：其一是建立了系统的开环极点和闭环极点与 $F ( s )$ 的零极点之间的直接联系；其二是建立了闭合曲线 $\varGamma _ { F }$ 和闭合曲线 $\Gamma _ { G H }$ 之间的转换关系。在已知开环传递函数 $G ( s ) H ( s )$ 的条件下，上述优点为幅角原理的应用创造了条件。

# (3) $s$ 平面闭合曲线 $\varGamma$ 的选择

系统的闭环稳定性取决于系统闭环传递函数极点即 $F ( s )$ 的零点的位置，因此当选择 $s$ 平面闭合曲线 $\varGamma$ 包围 $s$ 平面的右半平面时，若 $F ( s )$ 在 $s$ 右半平面的零点数 $Z { = } 0$ ，则闭环系统稳定。考虑到前述闭合曲线 $\varGamma$ 应不通过 $F ( s )$ 的零极点的要求， $\varGamma$ 可取图 5-30 所示的两种形式。

![](images/ec9ca76ae6fe1c2373234ad34a7554772d3033bb0226a4cbd0bef04661b4538f.jpg)  
图 5-29 $\varGamma _ { F }$ 与 $\Gamma _ { G H }$ 的几何关系

![](images/d957a932c6965d1f3ca82267058ecd5e8d1649f5ed8a9a0370ffc3ab5bd01eae.jpg)  
$G ( s ) H ( s )$ 无虚轴上的极点

![](images/01cb079b11cbdd4d1d9a6d90aebec60737881a2c17e4b897818f55b533fe4fc3.jpg)  
$G ( s ) H ( s )$ 有虚轴上的极点  
图 5-30 $s$ 平面的闭合曲线 $\varGamma$

当 $G ( s ) H ( s )$ 无虚轴上的极点时，见图 5-30(a)所示， $s$ 平面闭合曲线 $\varGamma$ 由两部分组成：

1) $\scriptstyle s = \infty e ^ { \mathrm { i } \theta }$ ， $\theta { \in } [ 0 ^ { \circ } , - 9 0 ^ { \circ } ]$ ，即圆心为原点、第Ⅳ象限中半径为无穷大的 1/4 圆； $\scriptstyle { s = j \omega }$ ，$\omega \in ( - \infty , 0 ]$ ，即负虚轴。  
2) $s { = } \mathrm { j } \omega , \omega { \in } [ 0 , + \infty )$ ，即正虚轴； $\scriptstyle s = \infty e ^ { \mathrm { i } \theta }$ ， $\theta { \in } [ 0 ^ { \circ } , + 9 0 ^ { \circ } ]$ ，即圆心为原点、第Ⅰ象限中

半径为无穷大的1/4 圆。

当 $G ( s ) H ( s )$ 在虚轴上有极点时，为避开开环极点，在图 5-30(a)所选闭合曲线 $\varGamma$ 的基础上加以扩展，构成图 5-30(b)所示的闭合曲线 $\varGamma _ { \circ }$

1) 开环系统含有积分环节时，在原点附近，取 $s { = } \varepsilon \operatorname { e } ^ { \mathrm { i } \theta } ( \varepsilon$ 为正无穷小量， $\theta \in [ - 9 0 ^ { \circ }$ ，$+ 9 0 ^ { \circ } ] ,$ )，即圆心为原点、半径为无穷小的半圆。  
2) 开环系统含有等幅振荡环节时，在j $\omega _ { n }$ 附近，取 $s { = } { \pm } \mathrm { j } \omega _ { n } { + } \varepsilon \mathrm { e } ^ { \mathrm { j } \theta } ( \varepsilon$ 为正无穷小量，$\theta { \in } [ - 9 0 ^ { \circ } , + 9 0 ^ { \circ } ] )$ ，即圆心为±j $\omega _ { n }$ 、半径为无穷小的半圆。

按上述 $\varGamma$ 曲线，函数 $F ( s )$ 位于 $s$ 右半平面的极点数即开环传递函数 $G ( s ) H ( s )$ 位于 $s$ 右半平面的极点数 $P$ 应不包括 $G ( s ) H ( s )$ 位于 $s$ 平面虚轴上的极点数。

# (4) $G ( s ) H ( s )$ 闭合曲线的绘制

由图 5-30 知， $s$ 平面闭合曲线 $\varGamma$ 关于实轴对称，鉴于 $G ( s ) H ( s )$ 为实系数有理分式函数，故闭合曲线 $\Gamma _ { G H }$ 亦关于实轴对称，因此只需绘制 $\Gamma _ { G H }$ 在 $\mathrm { I m } s { \geqslant } 0$ ， $s \invarGamma$ 对应的曲线段，得 $G ( s ) H ( s )$ 的半闭合曲线，称为奈奎斯特曲线，仍记为 $\Gamma _ { G H }$ 。

# 1) 若 $G ( s ) H ( s )$ 无虚轴上极点

$\Gamma _ { G H }$ 在 $\scriptstyle { s = j \omega }$ ， $\omega { \in } [ 0 , \ + \infty )$ 时，对应开环幅相特性曲线。

$\Gamma _ { G H }$ 在 $\scriptstyle s = \infty e ^ { \mathrm { j } \theta }$ ， $\theta \in [ 0 ^ { \circ }$ ， $+ 9 0 ^ { \circ } ]$ 时，对应原点 $( n { > } m$ 时)或 $( K ^ { * } , \ \mathrm { j 0 } )$ 点 $\scriptstyle ( n = m$ 时)， $K ^ { * }$ 为系统开环根轨迹增益。

2) 若 $G ( s ) H ( s )$ 有虚轴极点。当开环系统含有积分环节时，设

$$
G (s) H (s) = \frac {1}{s ^ {\nu}} G _ {1} (s); \quad \nu > 0, \quad | G _ {1} (\mathrm {j} 0) | \neq \infty \tag {5-67}
$$

有

$$
A \left(0 _ {+}\right) = \infty , \quad \varphi \left(0 _ {+}\right) = \angle [ G (\mathrm {j} 0 _ {+}) H (\mathrm {j} 0 _ {+}) ] = \nu \times (- 9 0 ^ {\circ}) + \angle [ G _ {1} (\mathrm {j} 0 _ {+}) ] \tag {5-68}
$$

于是在原点附近，闭合曲线 $\varGamma$ 为 $\scriptstyle s = \varepsilon \operatorname { e } ^ { \mathrm { { j } } \theta }$ ， $\theta { \in } [ 0 ^ { \circ } , ~ + 9 0 ^ { \circ } ]$ ，且有 $G _ { 1 } ( \varepsilon \mathrm { e } ^ { \mathrm { j } \theta } ) { = } G _ { 1 } ( \mathrm { j } 0 )$ ，故

$$
G (s) H (s) \mid_ {s = \varepsilon \mathrm {e} ^ {\mathrm {j} \theta}} \approx \infty \mathrm {e} ^ {\mathrm {j} \left(\angle \left(\frac {1}{\varepsilon^ {\nu} \mathrm {e} ^ {\mathrm {j} \theta \nu}}\right) + \angle [ G _ {1} (\varepsilon \mathrm {e} ^ {\mathrm {j} \theta}) ]\right)} = \infty \mathrm {e} ^ {\mathrm {j} [ \nu \times (- \theta) + \angle [ G _ {1} (\mathrm {j} 0) ] ]} \tag {5-69}
$$

对应的曲线为从 $G _ { 1 } ( \mathrm { j } 0 )$ 点起，半径为 $\infty$ 、圆心角为 $\nu \times ( - \theta )$ 的圆弧，即可从 $G ( \mathrm { j } 0 _ { + } ) H ( \mathrm { j } 0 _ { + } )$ 点起逆时针作半径无穷大、圆心角为 $\nu \times 9 0 ^ { \circ }$ 的圆弧，如图 5-31(a)中虚线所示。

当开环系统含有等幅振荡环节时，设

$$
G (s) H (s) = \frac {1}{\left(s ^ {2} + \omega_ {n} ^ {2}\right) ^ {\nu_ {1}}} G _ {1} (s); \quad \nu_ {1} > 0, \quad | G _ {1} (\pm j \omega_ {n}) | \neq \infty \tag {5-70}
$$

考虑 $s$ 在 $\mathrm { j } \omega _ { n }$ 附近沿 $\varGamma$ 运动时， $T _ { G H }$ 的变化为

$$
s = \mathrm {j} \omega_ {n} + \varepsilon \mathrm {e} ^ {\mathrm {j} \theta}; \quad \theta \in \left[ - 9 0 ^ {\circ}, + 9 0 ^ {\circ} \right] \tag {5-71}
$$

因为为正无穷小量，所以式(5-70)可写为

$$
G (s) H (s) = \frac {1}{(2 \mathrm {j} \omega_ {n} \varepsilon \mathrm {e} ^ {\mathrm {j} \theta} + \varepsilon^ {2} \mathrm {e} ^ {\mathrm {j} 2 \theta}) ^ {\nu_ {1}}} G _ {1} (\mathrm {j} \omega_ {n} + \varepsilon \mathrm {e} ^ {\mathrm {j} \theta}) \approx \frac {\mathrm {e} ^ {- \mathrm {j} (\theta + 9 0 ^ {\circ}) \nu_ {1}}}{(2 \omega_ {n} \varepsilon) ^ {\nu_ {1}}} G (\mathrm {j} \omega_ {n}) \tag {5-72}
$$

![](images/bc7947eb779c138c5755ccec361445d0dcb8ee3d319b8db880dbf9d2378bae42.jpg)

![](images/1e490081f28c16d592eb8d142c25e3c616719171f6be618d77be0b551068394f.jpg)  
(b)开环系统有等幅振荡环节   
图 5-31 $F ( s )$ 平面的半闭合曲线

故有 $\left\{ \begin{array} { l l } { A ( s ) = \infty } \\ { \qquad } \\ { \varphi ( s ) = \left\{ \begin{array} { l l } { \angle [ G _ { 1 } ( \mathrm { j } \omega _ { n } ) ] , } & { \qquad \theta = - 9 0 ^ { \circ } , \mathbb { E } [ ] _ { S } = \mathrm { j } \omega _ { n - } } \\ { \angle [ G _ { 1 } ( \mathrm { j } \omega _ { n } ) ] - ( \theta + 9 0 ^ { \circ } ) \nu _ { 1 } , } & { \qquad \theta \in ( - 9 0 ^ { \circ } , + 9 0 ^ { \circ } ) } \\ { \angle [ G _ { 1 } ( \mathrm { j } \omega _ { n } ) ] - \nu _ { 1 } \times 1 8 0 ^ { \circ } , \quad } & { \theta = 9 0 ^ { \circ } , \mathbb { E } [ ] _ { S } = \mathrm { j } \omega _ { n + } } \end{array} \right. } \end{array} \right.$ ( )A s   $\theta = - 9 0 ^ { \circ } .$ $\theta \in ( - 9 0 ^ { \circ } , + 9 0 ^ { \circ } )$ $s = \mathrm { j } \omega _ { n - }$ (5-73) 9 0 j , ns     即 $\theta = 9 0 ^ { \circ } { \mathrm { ~ } }$ $s = \mathrm { j } \omega _ { n + }$

因此， $s$ 沿 $\varGamma$ 在 $\mathrm { j } \omega _ { n }$ 附近运动时，对应的 $\Gamma _ { G H }$ 闭合曲线为半径无穷大，圆心角等于 $\nu _ { 1 } \times 1 8 0 ^ { \circ }$ 的圆弧，即应从 $G ( \mathrm { j } \omega _ { n - } ) H ( \mathrm { j } \omega _ { n - } )$ 点起以半径为无穷大顺时针作 $\nu _ { \mathrm { 1 } } \times 1 8 0 ^ { \circ }$ 的圆弧至$G ( \mathrm { j } \omega _ { n + } ) H ( \mathrm { j } \omega _ { n + } )$ 点，如图 5-31(b)中虚线所示。上述分析表明，半闭合曲线 $\Gamma _ { G H }$ 由开环幅相特性曲线和根据开环虚轴极点所补作的无穷大半径的虚线圆弧两部分组成。

# (5) 闭合曲线 $\varGamma _ { F }$ 包围原点圈数 $R$ 的计算

根据半闭合曲线 $\Gamma _ { G H }$ 可获得 $\varGamma _ { F }$ 包围原点的圈数 $R$ 。设 $N$ 为 $\Gamma _ { G H }$ 穿越(1，j0)点左侧负实轴的次数， $N _ { + }$ 表示正穿越的次数和(从上向下穿越)， $N _ { - }$ 表示负穿越的次数和(从下向上穿越)，则

$$
R = 2 N = 2 \left(N _ {+} - N _ {-}\right) \tag {5-74}
$$

在图 5-32 中，虚线为按系统型次 $\nu$ 或等幅振荡环节数 $\nu _ { 1 }$ 补作的圆弧，点 $A$ 、 $B$ 为奈氏曲线与负实轴的交点，按穿越负实轴上 $( - \infty , \ - 1 )$ 段的方向，分别有：

图(a) $A$ 点位于(1，j0)点左侧， $\Gamma _ { G H }$ 从下向上穿越，为一次负穿越。故 $N _ { - } { = } 1$ ， $N _ { + } { = } 0$ ，$R { = } { - } 2 N { = } { - } 2$ 。

图(b) $A$ 点位于(1，j0)点的右侧， $N _ { + } { = } N _ { - } { = } 0$ ， $R { = } 0$ 。

图(c) A， $B$ 点均位于(1，j0)点左侧，而在 $A$ 点处 $\Gamma _ { G H }$ 从下向上穿越，为一次负穿越；$B$ 点处则 $\Gamma _ { G H }$ 从上向下穿越，为一次正穿越，故有 $N _ { + } { = } N _ { - } { = } 1$ ， $R { = } 0$ 。

图(d) $A$ ， $B$ 点均位于(1，j0)点左侧， $A$ 点处 $\Gamma _ { G H }$ 从下向上穿越，为一次负穿越； $B$ 点处 $\Gamma _ { G H }$ 从上向下运动至实轴并停止，为半次正穿越，故 $N _ { - } { = } 1$ ， $N _ { + } { = } \frac { 1 } { 2 }$ $R { = } { - } 1$ 。

图(e) $A$ ， $B$ 点均位于(1, j0)点的左侧， $A$ 点对应 $\omega { = } 0$ ，随 $\omega$ 增大， $\Gamma _ { G H }$ 离开负实轴，为半次负穿越，而 $B$ 点处为一次负穿越，故有 $N _ { - } { = } \frac { 3 } { 2 }$ ， $N _ { + } { = } 0$ ， $R { = } { - } 3$ 。

![](images/3cc4c6ea6349d07c50c6c7e7e2db223b5b640c2e2d061b493f1e05d380e29590.jpg)

![](images/5ff75d8744c4c41ff2013fef7c67a64479bf7f88c5497562ff2f30f5442df00d.jpg)

![](images/63982934a20e5892ad78166a8589a80e80c1ee325e713891639d39e604c85b54.jpg)

![](images/b1305e757c92e9191a432ebe4f525c01826c523edff540933c43c8c0e76270e1.jpg)

![](images/04cef0d1de1d93504830a8ea26d91ee9fa12be118b554051e1f1439e1fc8bdad.jpg)  
  
图 5-32 系统开环半闭合曲线 $\Gamma _ { G H }$ 与 $\varGamma _ { F }$ 包围原点的圈数 $R$

$\varGamma _ { F }$ 包围原点的圆数 $R$ 等于 $\Gamma _ { G H }$ 包围(1, j0)点的圈数。计算 $R$ 的过程中应注意正确判断 $\Gamma _ { G H }$ 穿越(1, j0)点左侧负实轴时的方向、半次穿越和虚线圆弧所产生的穿越次数。

# 2. 奈奎斯特稳定判据(奈氏判据)

设闭合曲线 $\varGamma$ 如图 5-30 所示，在已知开环系统右半平面的极点数(不包括虚轴上的极点)和半闭合曲线 $\Gamma _ { G H }$ 的情况下，根据幅角原理和闭环稳定条件，可得下述奈氏判据。

奈氏判据 反馈控制系统稳定的充分必要条件是半闭合曲线 $T _ { G H }$ 不穿过(1，j0)点且逆时针包围临界点(1，j0)点的圈数R等于开环传递函数的正实部极点数 P。

由幅角原理可知，闭合曲线 $\varGamma$ 包围函数 $F ( s ) { = } 1 { + } G ( s ) H ( s )$ 的零点数即反馈控制系统正实部极点数为

$$
Z = P - R = P - 2 N \tag {5-75}
$$

当 $P \neq R$ 时， $Z \neq 0$ ，系统闭环不稳定。而当半闭合曲线 $\Gamma _ { G H }$ 穿过(1，j0)点时，表明存在$s { = } \pm \mathrm { j } \omega _ { n }$ ，使得

$$
G (\pm \mathrm {j} \omega_ {n}) H (\pm \mathrm {j} \omega_ {n}) = - 1 \tag {5-76}
$$

即系统闭环特征方程存在共轭纯虚根，则系统可能临界稳定。计算 $\Gamma _ { G H }$ 的穿越次数 $N$ 时，应注意不计及 $\Gamma _ { G H }$ 穿越(1，j0)点的次数。

例 5-8 已知单位反馈系统开环幅相特性曲线 $( K { = } 1 0 , P { = } 0$ , $\nu { = } 1$ )如图 5-33 所示，试确定系统闭环稳定时 $K$ 值的范围。

解 由图所示，开环幅相特性曲线与负实轴有三个交点，设交点处穿越频率分别为 $\omega _ { \mathrm { l } }$ ，$\omega _ { 2 }$ $\omega _ { 3 }$ ，系统开环传递函数形如

$$
G (s) = \frac {K}{s ^ {\nu}} G _ {1} (s)
$$

由题设条件知 $\nu { = } 1 , \operatorname* { l i m } _ { s \to 0 } G _ { 1 } ( s ) = 1$ $\nu { = } 1$ ，和

$$
G (\mathrm {j} \omega_ {i}) = \frac {K}{\mathrm {j} \omega_ {i}} G _ {1} (\mathrm {j} \omega_ {i}); \quad i = 1, 2, 3
$$

![](images/d5733a701c3008f1723bb69992448c8f4171112486498100f54993add12e713c.jpg)  
图 5-33 例 5-8 系统 $K { = } 1 0$ 时开环幅相特性曲线

当取 $K { = } 1 0$ 时

$$
G (\mathrm {j} \omega_ {1}) = - 2, \quad G (\mathrm {j} \omega_ {2}) = - 1. 5, \quad G (\mathrm {j} \omega_ {3}) = - 0. 5
$$

![](images/cb02035c31facf22d661da8435ac84eb398487cc919a6ced3534a51058498399.jpg)  
奈氏判据

若令 $G ( \mathrm { j } \omega _ { i } ) { = } { - } 1$ ，可得对应的 $K$ 值

$$
K _ {1} = \frac {- 1}{\frac {1}{j \omega_ {1}} G _ {1} (j \omega_ {1})} = \frac {- 1}{\frac {G (j \omega_ {1})}{K}} = \frac {- 1}{\frac {- 2}{1 0}} = 5, \quad K _ {2} = \frac {- 1}{\frac {G (j \omega_ {2})}{K}} = \frac {- 1}{\frac {- 1 . 5}{1 0}} = \frac {2 0}{3}, \quad K _ {3} = 2 0
$$

对应地，分别取 $0 { < } K { < } K _ { 1 }$ ， $K _ { 1 } { < } K { < } K _ { 2 }$ ， $K _ { 2 } { < } K { < } K _ { 3 }$ 和 $K { > } K _ { 3 }$ 时，开环幅相特性曲线分别如图 5-34(a)，(b)，(c)和(d)所示，图中按 $\nu$ 补作虚圆弧得半闭合曲线 $\varGamma _ { G }$ 。

![](images/39da59086f901cf83c229293f7bbddf4cb347f653efc08f0acaa7f9ce0370865.jpg)

![](images/8a65822f51e186604e2eaadd373d22b0cdbf7ec6d2dc21df75d414a9d1a6c82b.jpg)

![](images/e1ba74acf0d04cb5e7d18a196c035a3a461e49b0868dd60039fc054f5b53af9f.jpg)

![](images/5c89662084056d9ca54755cbdb0cdecc62d014077fefb4d9011cca3f74138980.jpg)  
图 5-34 例 5-8 系统在不同 $K$ 值条件下的开环幅相特性曲线及 $\varGamma _ { G }$ 曲线

根据 $\varGamma _ { G }$ 曲线计算包围次数，并判断系统闭环稳定性：

$0 < K < K _ { 1 }$ , $R = 0$ , $Z = 0$ ，闭环系统稳定；

$K _ { 1 } < K < K _ { 2 }$ , $R = - 2$ , $Z = 2$ ，闭环系统不稳定；

$K _ { 2 } < K < K _ { 3 }$ N N R, 1, 0,    $Z = 0$ ，闭环系统稳定；

3K K N N, 1, 2,    $R = - 2$ , $Z = 2$ ，闭环系统不稳定。

综上可得，系统闭环稳定时的 $K$ 值范围为(0，5)和 $\left( { \frac { 2 0 } { 3 } } , 2 0 \right)$ 。当 $K$ 等于 5， $\frac { 2 0 } { 3 }$ 和 20时， $\varGamma _ { G }$ 穿过临界点(1, j0)，且在这三个值的邻域，系统闭环稳定或不稳定，因此系统闭环临界稳定。

例 5-9 已知延迟系统开环传递函数为

$$
G (s) H (s) = \frac {2 e ^ {- \tau s}}{s + 1}, \quad \tau > 0
$$

试根据奈氏判据确定系统闭环稳定时，延迟时间 $\tau$ 值的范围。

解 由图 5-25可知，延迟系统开环幅相特性曲线即半闭合曲线 $\Gamma _ { G H }$ 为螺旋线，且为顺时针方向，若开环幅相特性曲线与(1，j0)点左侧的负实轴有 l 个交点，则 $\Gamma _ { G H }$ 包围 $( - 1$ ，j0)点的圈数为2l，由于 $P { = } 0$ ，故 $Z { = } 2 l$ ，系统闭环不稳定。若系统闭环稳定，则必须有 $l { = } 0$ 。设 $\omega _ { x }$ 为开环幅相特性曲线穿越负实轴时的频率，有

$$
\varphi \left(\omega_ {x}\right) = - \tau \omega_ {x} - \arctan \omega_ {x} = - (2 k + 1) \pi ; \quad k = 0, 1, 2, \dots
$$

鉴于

$$
A \left(\omega_ {x}\right) = \frac {2}{\sqrt {1 + \omega_ {x} ^ {2}}}
$$

当 $\omega _ { x }$ 增大时， $A ( \omega _ { x } )$ 减小。而在频率 $\omega$ 为最小的 $\omega _ { x m }$ 时，开环幅相特性曲线第一次穿过负实轴，因此 $\omega _ { x m }$ 求得为

$$
\varphi \left(\omega_ {x m}\right) = - \tau \omega_ {x m} - \arctan \omega_ {x m} = - \pi
$$

此时 $A ( \omega _ { x m } )$ 达到最大，为使 $l { = } 0$ ，必须使 $A ( \omega _ { x m } ) { < } 1$ ，即

$$
\omega_ {x m} > \sqrt {3}
$$

由 $\varphi ( \omega _ { x } ) = - ( 2 k + 1 ) \pi$ 解得

$$
\tau = \left[ (2 k + 1) \pi - \arctan \omega_ {x} \right] / \omega_ {x} > 0
$$

注意到

$$
\frac {\mathrm {d} \tau}{\mathrm {d} \omega_ {x}} = \frac {- \left[ (2 k + 1) \pi - \arctan \omega_ {x} + \frac {\omega_ {x}}{1 + \omega_ {x} ^ {2}} \right]}{\omega_ {x} ^ {2}} <   0
$$

为 $\omega _ { x }$ 的减函数，因此 $\omega _ { x m }$ 亦为 $\tau$ 的减函数，当 $\scriptstyle \tau = ( \pi - \arctan { \sqrt { 3 } } ) \left/ { \sqrt { 3 } } \right.$ 时， $\omega _ { x m } = \sqrt { 3 }$ ，系统临界稳定；当 $\tau { > } ( \pi { - } \arctan { \sqrt { 3 } } ) \big / \sqrt { 3 }$ 时， $\omega _ { x m } < \sqrt { 3 }$ ，系统不稳定。故系统闭环稳定时 $\tau$ 值的范围应为

$$
\tau <   \frac {\pi - \arctan \sqrt {3}}{\sqrt {3}} = \frac {2}{3 \sqrt {3}} \pi
$$

# 3. 对数频率稳定判据

奈氏判据基于复平面的半闭合曲线 $\Gamma _ { G H }$ 判定系统的闭环稳定性，由于半闭合曲线 $\Gamma _ { G H }$ 可以转换为半对数坐标下的曲线，所以可以推广运用奈氏判据，其关键问题是需要根据半对数坐标下的 $\Gamma _ { G H }$ 曲线确定穿越次数 $N$ 或 $N _ { + }$ 和 $N _ { - }$ 。

复平面 $\Gamma _ { G H }$ 曲线一般由两部分组成：开环幅相曲线和开环系统存在积分环节和等幅振荡环节时所补作的半径为无穷大的虚圆弧。而 $N$ 的确定取决于 $A ( \omega ) > 1$ 时 $\Gamma _ { G H }$ 穿越负实轴的次数，因此应建立和明确以下对应关系：

# (1) 穿越点确定

设 $\omega { = } \omega _ { c }$ 时

$$
\left\{ \begin{array}{l} A \left(\omega_ {c}\right) = | G (\mathrm {j} \omega_ {c}) H (\mathrm {j} \omega_ {c}) | = 1 \\ L \left(\omega_ {c}\right) = 2 0 \lg A \left(\omega_ {c}\right) = 0 \end{array} \right. \tag {5-77}
$$

称 $\omega _ { c }$ 为截止频率。对于复平面的负实轴和开环对数相频特性，当取频率为穿越频率 $\omega _ { x }$ 时

$$
\varphi \left(\omega_ {x}\right) = (2 k + 1) \pi ; \quad k = 0, \pm 1, \dots \tag {5-78}
$$

设半对数坐标下 $\Gamma _ { G H }$ 的对数幅频特性曲线和对数相频特性曲线分别为 $\varGamma _ { L }$ 和 $\varGamma _ { \varphi }$ ，由于 $\varGamma _ { L }$ 等于 $L ( \omega )$ 曲线，则 $\Gamma _ { G H }$ 在 $A ( \omega ) { > } 1$ 时，穿越负实轴的点等于 $\Gamma _ { G H }$ 在半对数坐标下，对数幅频特性 $L ( \omega ) { > } 0$ 时对数相频特性曲线 $\varGamma _ { \varphi }$ 与 $( 2 k + 1 ) \pi ( k = 0 , \pm 1 , \ \cdots )$ ，平行线的交点。

# (2) $\varGamma _ { \varphi }$ 确定

1)开环系统无虚轴上极点时， $\varGamma _ { \varphi }$ 等于 $\varphi ( \omega )$ 曲线。

2) 开环系统存在积分环节 $\frac { 1 } { s ^ { \nu } } ( \nu { > } 0 )$ 时，复数平面的 $\Gamma _ { G H }$ 曲线，需从 $\omega = 0 _ { + }$ 的开环幅sV相特性曲线的对应点 $G ( \mathrm { j } 0 \sb { + } ) H ( \mathrm { j } 0 \sb { + } ) \mathrm { j }$ 起，逆时针补作 $\nu \times 9 0 ^ { \circ }$ 半径为无穷大的虚圆弧。对应地，

需从对数相频特性曲线 $\omega$ 较小且 $L ( \omega ) { \ = } 0$ 的点处向上补作 $\nu \times 9 0 ^ { \circ }$ 的虚直线， $\varphi ( \omega )$ 曲线和补作的虚直线构成 $\varGamma _ { \varphi }$ 。

3) 开环系统存在等幅振荡环节 $\frac { 1 } { ( s ^ { 2 } + \omega _ { n } ^ { 2 } ) ^ { \nu _ { 1 } } } ( \nu _ { 1 } > 0 )$ 时，复数平面的 $\Gamma _ { G H }$ 曲线，需从$\omega = \omega _ { n } .$ 的开环幅相曲线的对应点 $G ( \mathrm { j } \omega _ { n - } ) H ( \mathrm { j } \omega _ { n - } )$ 起，顺时针补作 $\nu _ { 1 } \times 1 8 0 ^ { \circ }$ 半径为无穷大的虚圆弧至 $\omega = \omega _ { n ^ { + } }$ 的对应点 $G ( \mathrm { j } \omega _ { n + } ) H ( \mathrm { j } \omega _ { n + } )$ )处。对应地，需从对数相频特性曲线 $\varphi ( \omega _ { n - } )$ 点起向上补作 $\nu _ { 1 } \times 1 8 0 ^ { \circ }$ 的虚直线至 $\varphi ( \omega _ { n + } )$ 处， $\varphi ( \omega )$ 曲线和补作的虚直线构成 $\varGamma _ { \varphi \circ }$

# (3) 穿越次数计算

正穿越一次： $\Gamma _ { G H }$ 由上向下穿越(1，j0)点左侧的负实轴一次，等价于在 $L ( \omega ) { \mathrm { { > } } } 0$ 时，$\varGamma _ { \varphi }$ 由下向上穿越 $( 2 k { + } 1 ) \pi$ 线一次。

负穿越一次： $\Gamma _ { G H }$ 由下向上穿越(1，j0)点左侧的负实轴一次，等价于在 $L ( \omega ) { \mathrm { { > } } } 0$ 时，$\varGamma _ { \varphi }$ 由上向下穿越 $( 2 k { + } 1 ) \pi$ 线一次。

正穿越半次： $\Gamma _ { G H }$ 由上向下止于或由上向下起于(1，j0)点左侧的负实轴，等价于在$L ( \omega ) { > } 0$ 时， $\varGamma _ { \varphi }$ 由下向上止于或由下向上起于 $( 2 k { + } 1 ) \pi$ 线。

负穿越半次： $\Gamma _ { G H }$ 由下向上止于或由下向上起于(1，j0)点左侧的负实轴，等价于在$L ( \omega ) { > } 0$ 时， $\varGamma _ { \varphi }$ 由上向下止于或由上向下起于 $( 2 k { + } 1 ) \pi$ 线。

应该指出的是，补作的虚直线所产生的穿越皆为负穿越。

对数频率稳定判据 设 $P$ 为开环系统正实部的极点数，反馈控制系统稳定的充分必要条件是 $\varphi ( \omega _ { c } ) \neq ( 2 k + 1 ) \pi ( k { = } 0 , 1 , 2 ,$ …)和 $\mathbfcal { L } ( \omega ) { > } \mathbf { 0 }$ 时， $\boldsymbol { { \cal T } } _ { \varphi }$ 曲线穿越(2k+1)线的次数

$$
N = N _ {+} - N _ {-}
$$

满足

$$
Z = P - 2 N = 0 \tag {5-79}
$$

对数频率稳定判据和奈氏判据本质相同，其区别仅在于前者在 $L ( \omega ) { > } 0$ 的频率范围内依 $\varGamma _ { \varphi }$ 曲线确定穿越次数 $N _ { \circ }$

![](images/0ed2619567eb4fb9e1279ed0b6d1796faeea2caf5b43e4b98d60fdecf99e1a17.jpg)  
图 5-35 某系统开环幅相特性曲线

例 5-10 已知某系统开环稳定，开环幅相特性曲线如图 5-35 所示，试将开环幅相特性曲线表示为开环对数频率特性曲线，并运用对数稳定判据判断系统的闭环稳定性。

解 系统开环对数频率特性曲线如图 5-36所示，然而相角表示具有不唯一性，图中(a)和(b)为其中的两种形式。

因为开环系统稳定， $P { = } 0$ 。由开环幅相特性曲线知 $\nu { = } 0$ ，不需补作虚直线。

图(a)中， $L ( \omega ) { \mathrm { { > } } } 0$ 频段内， $\varphi ( \omega )$ 曲线与 $- 1 8 0 ^ { \circ }$ 线有两个交点，依频率由小到大，分别为一次负穿越和一次正穿越，故 $\scriptstyle N = N _ { + } - N _ { - } = 0$ 。

图(b)中， $L ( \omega ) { \mathrm { { > } } } 0$ 频段内， $\varphi \left( \omega \right)$ 曲线与 $1 8 0 ^ { \circ }$ 线和 $- 1 8 0 ^ { \circ }$ 线有四个交点，依频率由小到大，分别为半次负穿越、半次负穿越、半次正穿越和半次正穿越，故 $\scriptstyle N = N _ { + } - N _ { - } = 0$ 。

![](images/9aa8e861e9773847f0c57322f03dc6785e53a5d65893d14eea8340c4c7c7dfaf.jpg)

按对数稳定判据，图(a)和图(b)都有 $Z { = } P { - } 2 N { = } 0$ ，且 $\varphi \left( \omega _ { c } \right) \neq ( 2 k + 1 ) \pi$ ； $k { = } 0$ ，1，2，…，故系统闭环稳定。

例 5-11 已知开环系统型次 $\nu { = } 3$ ， $P { = } 0$ ，开环对数相频特性曲线如图 5-37 所示，图中 $\omega { < } \omega _ { c }$ 时， $L ( \omega ) { \ > } L ( \omega _ { c } )$ ，试确定闭环不稳定极点的个数。

![](images/8629f1547e163d8839356592c3f5d8aacbb9ba5cd7bd6a82a354a9294ac4be4e.jpg)  
图 5-36 某系统开环对数频率特性曲线

![](images/7fc9deacfaa7d3887288e7b64f7c6e85fc49488673b5e178c004bfb38acef9a9.jpg)  
图 5-37 例5-11系统开环对数相频特性曲线

解 因为 $\nu { = } 3$ ，需在低频处由 $\varphi \left( \omega \right)$ 曲线向上补作 $2 7 0 ^ { \circ }$ 的虚直线于 $1 8 0 ^ { \circ }$ ，如图 5-37所示。在 $L ( \omega ) { > } L ( \omega _ { c } ) { = } 0 \mathrm { d B }$ 频段内，存在两个与 $( 2 k + 1 ) \pi$ 线的交点， $\omega _ { \mathrm { l } }$ 处为一次负穿越， $\omega = 0$ 处为半次负穿越，故 $N _ { - } { = } 1 . 5$ ， $N _ { + } { = } 0$ ，按对数稳定判据

$$
Z = P - 2 N = 3
$$

故闭环不稳定极点的个数为 3。

# 4. 条件稳定系统

例 5-8系统的分析表明，若开环传递函数在开右半 $s$ 平面的极点数 $P { = } 0$ ，当开环传递函数的某些系数(如开环增益)改变时，闭环系统的稳定性将发生变化。这种闭环稳定有条件的系统称为条件稳定系统。

相应地，无论开环传递函数的系数怎样变化，例如 $G ( s ) H ( s ) = { \frac { K } { s ^ { 2 } ( T s + 1 ) } }$ 系统总是闭环不稳定的，这样的系统称为结构不稳定系统。为了表征系统的稳定程度，需要引入“稳定裕度”概念。

# 5-4 稳 定 裕 度

根据奈氏判据可知，对于系统开环传递函数，若开右半 $s$ 平面的极点数 $P { = } 0$ ，则系统闭环稳定性取决于闭合曲线 $\Gamma _ { G H }$ 包围(1, j0)点的圈数。当开环传递函数的某些系数发生

变化时， $\Gamma _ { G H }$ 包围(1, j0)点的情况亦随之改变。如例 5-8所示，当 $\Gamma _ { G H }$ 穿过(1,j0)点时，闭环系统临界稳定。因此，在稳定性研究中，称(1, j0)点为临界点，而闭合曲线 $\Gamma _ { G H }$ 相对于临界点的位置即偏离临界点的程度，反映系统的相对稳定性。进一步分析和工程应用表明，相对稳定性亦影响系统时域响应的性能。

频域的相对稳定性即稳定裕度常用相角裕度和幅值裕度 $h$ 来度量。

# 1. 相角裕度

设 $\omega _ { c }$ 为系统的截止频率，显然

$$
A \left(\omega_ {c}\right) = | G (\mathrm {j} \omega_ {c}) H (\mathrm {j} \omega_ {c}) | = 1 \tag {5-80}
$$

定义相角裕度为

$$
\gamma = 1 8 0 ^ {\circ} + \angle [ G (\mathrm {j} \omega_ {c}) H (\mathrm {j} \omega_ {c}) ] \tag {5-81}
$$

相角裕度的含义是，对于闭环稳定系统，如果系统开环相频特性再滞后度，则系统将处于临界稳定状态。

# 2. 幅值裕度 h

设 $\omega _ { x }$ 为系统的穿越频率，则系统在 $\omega _ { x }$ 处的相角

$$
\varphi \left(\omega_ {x}\right) = \angle [ G (\mathrm {j} \omega_ {x}) H (\mathrm {j} \omega_ {x}) ] = (2 k + 1) \pi ; \quad k = 0, \pm 1, \dots \tag {5-82}
$$

定义幅值裕度为

$$
h = \frac {1}{\left| G \left(\mathrm {j} \omega_ {x}\right) H \left(\mathrm {j} \omega_ {x}\right) \right|} \tag {5-83}
$$

幅值裕度 $h$ 的含义是，对于闭环稳定系统，如果系统开环幅频特性再增大 $h$ 倍，则系统将处于临界稳定状态，复平面中 和 $h$ 的表示如图 5-38(b)所示；对于闭环不稳定的系统，幅值裕度指出了为使系统临界稳定，开环幅频特性应当减小到原来的 $1 / h$ 。

对数坐标下，幅值裕度按下式定义：

$$
h (\mathrm {d B}) = - 2 0 \lg | G (\mathrm {j} \omega_ {x}) H (\mathrm {j} \omega_ {x}) | \quad (\mathrm {d B}) \tag {5-84}
$$

![](images/c1218d3b6a600729a55ccdfe6562f5f99bf8f56f1a22ede4cdda58e8219bc520.jpg)  
稳定系统

![](images/a9121dc8165e2e37795115b9033852702f9ab254065f0d8808a848c76096de62.jpg)  
不稳定系统  
(a)对数坐标平面

![](images/6e15346c60dcbb80e46a7b016fd8879afac40b2cf3652f4fce191e10ef5e9a73.jpg)  
稳定系统

![](images/faf5bbb610c5292311fa9c317a4d7fb0632a53dad0cffbd475bc995270ff4dc4.jpg)  
不稳定系统  
(b)极坐标平面

# 图 5-38 稳定和不稳定系统的相角裕度和幅值裕度

半对数坐标图中的 和 $h$ 的表示如图 5-38(a)所示。

当幅值裕度以分贝表示时，如果 $h$ 大于 1，则幅值裕度为正值；如果 $h$ 小于 1，则幅值裕度为负值。因此，正幅值裕度(以 dB 表示)表示系统是稳定的，负幅值裕度(以 dB 表示)表示系统是不稳定的。

一阶或二阶系统的幅值裕度为无穷大，因为这类系统的极坐标图与负实轴不相交。因此，理论上，一阶或二阶系统不可能是不稳定的(当然，一阶或二阶系统在一定意义上说只能是近似的，因为在推导系统方程时，忽略了一些小的时间滞后，因此它们不是真正的一阶或二阶系统。如果考虑这些小的滞后，则所谓的一阶或二阶系统也可能是不稳定的)。

注意，对于具有不稳定开环系统的非最小相位系统，除非 $G ( + \mathrm { j } \omega )$ 图包围 $( - 1 + \mathrm { j } 0 )$ 点，否则不能满足稳定条件。因此，这种稳定的非最小相位系统将具有负的相角裕度和幅值裕度。

条件稳定系统将具有两个或多个穿越频率，并且某些具有复杂动态特性的高阶系统还可能具有两个或多个截止频率，如图 5-39 所示。对于具有两个或多个截止频率的稳定系统，相角裕度应在最高的截止频率上测量。

![](images/37f7d3e8f992c6957d7b4b323d5d436ee7446fe1d7ce80a5ba1e58c649607e7b.jpg)

![](images/1e4a40a95e566e55ec1fb56bc026459d5664e4bf44f75d2372d233c93c7c1191.jpg)  
图 5-39 具有多于两个以上的穿越频率或截止频率系统的极坐标图

![](images/bb98901a1c0b041dba8f053af0b895ddedb969c3700f9e9abf2dc36cb8ae661f.jpg)  
稳定裕度

例 5-12 已知单位反馈系统

$$
G (s) = \frac {K}{(s + 1) ^ {3}}
$$

设 $K$ 分别为 4 和 10 时，试确定系统的稳定裕度。

解 系统开环频率特性

$$
G (\mathrm {j} \omega) = \frac {K}{(1 + \omega^ {2}) ^ {\frac {3}{2}}} \angle (- 3 \arctan \omega) = \frac {K [ (1 - 3 \omega^ {2}) - \mathrm {j} \omega (3 - \omega^ {2}) ]}{(1 + \omega^ {2}) ^ {3}}
$$

按 $\omega _ { x }$ ， $\omega _ { c }$ 定义可得

$$
\omega_ {x} = \sqrt {3}
$$

$K { = } 4$ 时：

$$
G (\mathrm {j} \omega_ {x}) = - 0. 5, \quad h = 2
$$

$$
\omega_ {c} = \sqrt {1 6 ^ {\frac {1}{3}} - 1} = 1. 2 3 3, \quad \angle [ G (\mathrm {j} \omega_ {c}) ] = - 1 5 2. 9 ^ {\circ}, \quad \gamma = 2 7. 1 ^ {\circ}
$$

$K { = } 1 0$ 时：

$$
G (\mathrm {j} \omega_ {x}) = - 1. 2 5, \quad h = 0. 8
$$

$$
\omega_ {c} = 1. 9 0 8, \quad \angle [ G (\mathrm {j} \omega_ {c}) ] = - 1 8 7. 0 ^ {\circ}, \quad \gamma = - 7. 0 ^ {\circ}
$$

分别作出 $K { = } 4$ 和 $K { = } 1 0$ 的开环幅相特性曲线即闭合曲线 $\varGamma _ { G }$ ，如图 5-40 所示。由奈氏判

![](images/5ee9ff5965772dc73d9c26bfad53c9b71c97e954fd8770ecbce54f264cc665fe.jpg)  
图 5-40 例 5-12 $K { = } 4$ 和 $K { = } 1 0$ 时系统开环幅相特性曲线

据知：

$K { = } 4$ 时，系统闭环稳定， $h { > } 1 , \gamma { > } 0$

$K { = } 1 0$ 时，系统闭环不稳定， $h < 1$ ，$\gamma < 0$

上述根据 $\mathrm { \Sigma } > 0$ 且 $h > 1$ 或 $h ( \mathrm { d B } ) > 0$ 判断系统的闭环稳定性方法可推广至半闭合曲线 $\Gamma _ { G H }$ 分别与单位圆或负实轴至多只有一个交点，或 $L ( \omega ) > 0$ ， $\varGamma _ { \varphi }$ 与$( 2 k + 1 ) \pi$ 线 $( k { = } 0 , \ \pm 1 , \ \cdots )$ 至多只有一个交点，且开环传递函数无 $s$ 开右半平面极点的情况。应注意的是，该结论对非最小相位系统并不都适用。此外，仅用相角裕度或幅值裕度，都不足以反映系统的稳定程度。

例 5-13 典型二阶系统如图 5-41 所示，试确定系统的相角裕度 。

解 典型二阶系统的开环频率特性为

$$
\begin{array}{l} G (\mathrm {j} \omega) = \frac {\omega_ {n} ^ {2}}{\mathrm {j} \omega (\mathrm {j} \omega + 2 \zeta \omega_ {n})} \\ = \frac {\omega_ {n} ^ {2}}{\omega \sqrt {\omega^ {2} + 4 \zeta^ {2} \omega_ {n} ^ {2}}} \angle \left(- \arctan \frac {\omega}{2 \zeta \omega_ {n}} - 9 0 ^ {\circ}\right) \\ \end{array}
$$

![](images/9c067bfb5693224c4fd82664be031c34e2fb895075eff8f321579f518eb14c8a.jpg)  
图 5-41 典型二阶系统结构图

设 $\omega _ { c }$ 为截止频率，则有

$$
| G (\mathrm {j} \omega_ {c}) | = \frac {\omega_ {n} ^ {2}}{\omega_ {c} \sqrt {\omega_ {c} ^ {2} + 4 \zeta^ {2} \omega_ {n} ^ {2}}} = 1
$$

可求得 $\omega _ { c } = \omega _ { n } ( \sqrt { 4 \zeta ^ { 4 } + 1 } - 2 \zeta ^ { 2 } ) ^ { \frac { 1 } { 2 } }$ (5-85)

按相角裕度定义

$$
\begin{array}{l} \gamma = 1 8 0 ^ {\circ} + \angle [ G (\mathrm {j} \omega_ {c}) ] = 9 0 ^ {\circ} - \arctan \frac {\omega_ {c}}{2 \zeta \omega_ {n}} = \arctan \frac {2 \zeta \omega_ {n}}{\omega_ {c}} \\ = \arctan \left[ 2 \zeta \left(\frac {1}{\sqrt {4 \zeta^ {4} + 1} - 2 \zeta^ {2}}\right) ^ {\frac {1}{2}} \right] \tag {5-86} \\ \end{array}
$$

因为 $\frac { \mathrm { d } } { \mathrm { d } \zeta } ( \sqrt { 4 \zeta ^ { 4 } + 1 } - 2 \zeta ^ { 2 } ) = \frac { 4 \zeta } { \sqrt { 4 \zeta ^ { 4 } + 1 } } ( 2 \zeta ^ { 2 } - \sqrt { 4 \zeta ^ { 4 } + 1 } ) < 0$ 2 4 4  ( 2 4 1) 0    

故 $\omega _ { c }$ 为 $\omega _ { n }$ 的增函数和的减函数， $\gamma$ 只与阻尼比有关，且为 $\zeta$ 的增函数。

对于高阶系统，一般难以准确计算截止频率 $\omega _ { c }$ 。在工程设计和分析时，只要求粗略估计系统的相角裕度，故一般可根据对数幅频渐近特性曲线确定截止频率 $\omega _ { c }$ ，即取 $\omega _ { c }$ 满足 $L _ { a } ( \omega _ { c } ) { = } 0$ ，再由相频特性确定相角裕度 。

例 5-14 单位反馈系统的开环传递函数为

$$
G (s) = \frac {K}{s (s + 1) (0 . 1 s + 1)}
$$

试分别确定系统开环增益 $K { = } 5$ 和 $K { = } 2 0$ 时的相角裕度和幅值裕度。

解 首先作出 $K { = } 5$ 和 $K { = } 2 0$ 时的对数幅频渐近特性和对数相频特性曲线，如图 5-42所示，它们具有相同的相频特性，但幅频特性不同。

由图 5-42 可得，当 $K { = } 5$ 时， $\omega _ { c } { = } 2 . 1$ ， $\gamma _ { 1 } \approx 1 3 . 6 ^ { \circ }$ ， $h _ { 1 } ( \mathrm { d B } ) \approx 6 . 8 5 \mathrm { d B }$ ；而当 $K { = } 2 0$ 时，$\omega _ { c } { = } - 4 . 2 3$ $\gamma _ { 2 } \approx - 9 . 7 ^ { \circ }$ $h _ { 2 } ( \mathrm { d B } ) \approx - 5 . 2 \mathrm { d B }$

![](images/2418811aa2b9c86e65f4ac64ad2105d044756ba896d1a1d5a0a3f3ab68abc4a7.jpg)  
(a)开环对数幅频渐近特性

![](images/f860babc2ea95087155bac13046e579e583a4ce93a8c07a79d958cda387e17d6.jpg)  
(b)开环对数频率特性  
图 5-42 例 5-14 系统开环对数频率特性曲线(MATLAB)

![](images/36838cd8819d733aee8436ebbfc34065e56577f96166c96ac2da20cbb7c704dd.jpg)  
截止频率

例 5-14表明，减小开环增益 $K$ ，可以增大系统的相角裕度，但 $K$ 的减小会使系统的稳态误差变大。为了使系统具有良好的过渡过程，通常要求相角裕度为 $3 0 ^ { \circ } \sim 6 0 ^ { \circ }$ ，而欲满足这一要求应使开环对数幅频特性在截止频率附近的斜率大于40dB/dec，且有一定宽度。因此，为了兼顾系统的稳态误差和过渡过程的要求，有必要应用校正方法。

# 3. 关于相角裕度和幅值裕度的几点说明

控制系统的相角裕度和幅值裕度是系统的极坐标图对(1, j0)点靠近程度的度量。因此，这两个裕量可以用来作为设计准则。

只用幅值裕度或者只用相角裕度，都不足以说明系统的相对稳定性。为了确定系统的相对稳定性，必须同时给出这两个量。

对于最小相位系统，只有当相角裕度和幅值裕度都是正值时，系统才是稳定的。负的裕度表示系统不稳定。

适当的相角裕度和幅值裕度可以防止系统中元件老化造成的影响，并且指明了频率值。为了得到满意的性能，相角裕度应当为 $3 0 ^ { \circ } \sim 6 0 ^ { \circ }$ ，幅值裕度应当大于 6dB。对于具有上述裕度的最小相位系统，即使开环增益与元件的时间常数在一定范围内变化，也能保证系统的稳定性。

对于最小相位系统，开环传递函数的幅值和相位特性有一定关系。要求相角裕度在$3 0 ^ { \circ }$ 和 $6 0 ^ { \circ }$ 之间，即在伯德图中，对数幅值曲线在截止频率处的斜率应大于40dB/dec。在大多数实际情况中，为了保证系统稳定，要求截止频率处的斜率为20dB/dec。如果截止频率上的斜率为40dB/dec，则系统可能是稳定的，也可能是不稳定的(即使系统是稳定的，相角裕度也比较小)。如果在截止频率处的斜率为60dB/dec，或者更陡，则系统多半是不稳定的。

对于非最小相位系统，稳定裕度的正确解释需要仔细地进行研究。确定非最小相位系统稳定性的最好方法，是采用极坐标图法，而不是伯德图法。

# 5-5 闭环系统的频域性能指标

反馈控制系统的闭环传递函数为

$$
\Phi (s) = \frac {G (s)}{1 + G (s) H (s)} = \frac {1}{H (s)} \cdot \frac {G (s) H (s)}{1 + G (s) H (s)} \tag {5-87}
$$

其中 $H ( s )$ 为主反馈通道的传递函数，一般为常数。在 $H ( s )$ 为常数的情况下，闭环频率特性的形状不受影响。因此，研究闭环系统频域指标时，只需针对单位反馈系统进行。作用在控制系统的信号除了控制输入外，常伴随输入端和输出端的多种确定性扰动和随机噪声，因而闭环系统的频域性能指标应该反映控制系统跟踪控制输入信号和抑制干扰信号的能力。

# 1. 控制系统的频带宽度

设 $\phi ( \mathrm { j } \omega )$ 为系统闭环频率特性，当闭环幅频特性下降到频率为零时的分贝值以下 3 分

贝，即 $0 . 7 0 7 | \phi ( \mathrm { j 0 } ) | ( \mathrm { d B } ) |$ 时，对应的频率称为带宽频率，记为 $\omega _ { b }$ 。即当 $\omega > \omega _ { b }$ 时

$$
2 0 \lg | \Phi (\mathrm {j} \omega) | <   2 0 \lg | \Phi (\mathrm {j} 0) | - 3 \tag {5-88}
$$

而频率范围(0， $\omega _ { b , }$ )称为系统的带宽，如图 5-43所示。带宽定义表明，对高于带宽频率的正弦输入信号，系统输出将呈现较大的衰减。对于Ⅰ型和Ⅰ型以上的开环系统，由于$\vert \phi ( \mathrm { j } 0 ) \vert { = } 1$ ， $2 0 \log | \phi ( \mathrm { j } 0 ) | { = } 0$ ，故

$$
2 0 \lg | \Phi (\mathrm {j} \omega) | <   - 3 (\mathrm {d B}), \omega > \omega_ {b} \tag {5-89}
$$

带宽是频域中一项非常重要的性能指标。对于一阶和二阶系统，带宽频率和系统参数具有解析关系。

设一阶系统的闭环传递函数为

$$
\Phi (s) = \frac {1}{T s + 1}
$$

因为开环系统为Ⅰ型， $\boldsymbol { \phi } ( \mathrm { j } 0 ) { = } 1$ ，按带宽定义

![](images/a3b0e0a7c68c05b6f142b282d35e7711e90485b228e5a4b24e725865adb29127.jpg)  
图 5-43 系统带宽频率与带宽

$$
2 0 \lg | \Phi (\mathrm {j} \omega_ {b}) | = 2 0 \lg \frac {1}{\sqrt {1 + T ^ {2} \omega_ {b} ^ {2}}} = 2 0 \lg \frac {1}{\sqrt {2}}
$$

可求得带宽频率

$$
\omega_ {b} = \frac {1}{T} \tag {5-90}
$$

对于二阶系统，闭环传递函数为

$$
\Phi (s) = \frac {\omega_ {n} ^ {2}}{s ^ {2} + 2 \zeta \omega_ {n} s + \omega_ {n} ^ {2}}
$$

系统幅频特性

$$
| \Phi (\mathrm {j} \omega) | = \frac {1}{\sqrt {\left(1 - \frac {\omega^ {2}}{\omega_ {n} ^ {2}}\right) ^ {2} + 4 \zeta^ {2} \frac {\omega^ {2}}{\omega_ {n} ^ {2}}}}
$$

因为 $\scriptstyle | \phi ( \mathrm { j } 0 ) | = 1$ ，由带宽定义得

$$
\sqrt {\left(1 - \frac {\omega_ {b} ^ {2}}{\omega_ {n} ^ {2}}\right) ^ {2} + 4 \zeta^ {2} \frac {\omega_ {b} ^ {2}}{\omega_ {n} ^ {2}}} = \sqrt {2}
$$

于是

$$
\omega_ {b} = \omega_ {n} \left[ (1 - 2 \zeta^ {2}) + \sqrt {\left(1 - 2 \zeta^ {2}\right) ^ {2} + 1} \right] ^ {\frac {1}{2}} \tag {5-91}
$$

由式(5-90)知，一阶系统的带宽频率和时间常数 $T$ 成反比。由式(5-91)知，二阶系统的带宽频率和自然频率 $\omega _ { n }$ 成正比。令 $A { = } \left( \frac { \omega _ { b } } { \omega _ { n } } \right) ^ { 2 }$ ，由于

$$
\frac {\mathrm {d} A}{\mathrm {d} \zeta} = \frac {- 4 \zeta}{\sqrt {(1 - 2 \zeta^ {2}) ^ {2} + 1}} \left[ \sqrt {(1 - 2 \zeta^ {2}) ^ {2} + 1} + (1 - 2 \zeta^ {2}) \right] <   0
$$

$A$ 为 $\zeta$ 的减函数，故 $\omega _ { b }$ 为 $\zeta$ 的减函数，即 $\omega _ { b }$ 与阻尼比 $\zeta$ 成反比。根据第三章中一阶系统和二阶系统上升时间和调节时间与参数的关系可知，系统的单位阶跃响应的速度和带宽成正比。对于任意阶次的控制系统，这一关系仍然成立。

设两个控制系统存在以下关系：

$$
\Phi_ {1} (s) = \Phi_ {2} \left(\frac {s}{\lambda}\right) \tag {5-92}
$$

其中为任意正常数。两个系统的闭环频率特性亦有

$$
\Phi_ {1} (\mathrm {j} \omega) = \Phi_ {2} \left(\mathrm {j} \frac {\omega}{\lambda}\right)
$$

当对数幅频特性 $2 0 1 \mathrm { g } | \phi _ { 1 } ( \mathrm { j } \omega ) |$ 和 $2 0 \log | \phi _ { 2 } | \biggl ( \frac { \omega } { \lambda } \biggr )$ |的横坐标分别取为 $\omega$ 和 $\frac { \omega } { \lambda }$ 时，其对数幅频特性曲线具有相同的形状，按带宽定义可得

$$
\omega_ {b _ {1}} = \lambda \omega_ {b _ {2}}
$$

即系统 $\phi _ { 1 } ( s )$ 的带宽频率为系统 $\phi _ { 2 } ( s )$ 带宽频率的倍。设两个系统的单位阶跃响应分别为$c _ { 1 } ( t )$ 和 $c _ { 2 } ( t )$ ，按拉氏变换，有

$$
\frac {1}{s} \Phi_ {1} (s) = \int_ {0} ^ {\infty} c _ {1} (t) \mathrm {e} ^ {- s t} \mathrm {d} t = \frac {1}{\lambda} \cdot \frac {1}{\frac {s}{\lambda}} \Phi_ {2} \left(\frac {s}{\lambda}\right) = \int_ {0} ^ {\infty} c _ {2} (\lambda t) \mathrm {e} ^ {- s t} \mathrm {d} t
$$

即得 $c _ { 1 } ( t ) = c _ { 2 } ( \lambda t )$ (5-93)

由时域性能指标可知，系统 $\phi _ { 1 } ( s )$ 的上升时间和过渡过程时间为 $\phi _ { 2 } ( s )$ 的 1/倍。即当系统的带宽扩大倍，系统的响应速度则加快倍。鉴于系统复现输入信号的能力取决于系统的幅频特性和相频特性，对于输入端信号，带宽大，则跟踪控制信号的能力强；而在另一方面，抑制输入端高频干扰的能力则弱，因此系统带宽的选择在设计中应折中考虑，不能一味求大。

# 2. 系统带宽与信号频谱的关系

受环境变化，元器件老化，电源波动和传感器、执行器非线性因素的影响，系统的输入和输出端不可避免地存在扰动和噪声，因此控制系统带宽的选择需综合考虑各种输入信号的频率范围及其对系统性能的影响，即应使系统对控制输入信号具有良好的跟踪能力和对扰动输入信号具有较强的抑制能力。从误差的角度来看，就是使各种输入信号所产生的误差尽可能地小。因此很有必要分析信号的频域分布及其对误差的影响。

# (1) 周期信号的频谱

设 $f ( t )$ 为周期函数，其周期为 T，可用下式描述：

$$
f (t) = f (t + l T); \quad l = 0, \pm 1, \dots \tag {5-94}
$$

若 $f ( t )$ 在区间[0,T ]内有界，且仅有有限个极值，即满足狄利克雷条件，则 $f ( t )$ 可展开为傅里叶级数

$$
f (t) = \sum_ {k = - \infty} ^ {\infty} c _ {k} \mathrm {e} ^ {\mathrm {j} \frac {2 \pi k}{T} t} \tag {5-95}
$$

其中 $c _ { k }$ 为复数，称为傅里叶系数，

$$
c _ {k} = \frac {1}{T} \int_ {- \frac {T}{2}} ^ {\frac {T}{2}} f (t) \mathrm {e} ^ {\mathrm {j} \frac {2 \pi k}{T} t} \mathrm {d} t = \frac {A _ {k}}{2} \mathrm {e} ^ {\mathrm {j} B _ {k}} \tag {5-96}
$$

且有 $c _ { 0 } = \frac { A _ { 0 } } { 2 } , ~ c _ { - k } = \overline { { { c } } } _ { k } = \frac { A _ { k } } { 2 } \mathrm { e } ^ { - \mathrm { j } B _ { k } }$

代入式(5-95)可得

$$
f (t) = \frac {A _ {0}}{2} + \sum_ {k = 1} ^ {\infty} A _ {k} \cos \left(\frac {2 \pi k}{T} t + B _ {k}\right) \tag {5-97}
$$

复系数表达式中的 $A _ { k }$ 和 $B _ { k }$ 表示 $f ( \mathrm { t } )$ 的第 $k$ 次谐波分量的幅值和相位，称复系数 $c _ { k }$ 的集合为周期信号的频谱。频谱可以有不同的表示形式，有时只列出复系数的幅值谱。对于图 5-44(a)所示的矩形波序列，其基波频率和复系数的幅值分别为

$$
\Omega = \frac {2 \pi}{T}, \quad | c _ {k} | = \frac {A \tau}{T} \cdot \frac {\sin \left(\frac {\pi k \tau}{T}\right)}{\frac {\pi k \tau}{T}}
$$

幅值谱如图 5-44(b)所示。

![](images/40db5e22c3a553b8622264e598e9c69c07898c56b7f45423a82e95b865db0a3c.jpg)

![](images/2cdc0b9673708d1374fa96566aea00eb72c6b79373776e5cf2761e783a1457c6.jpg)  
  
图 5-44 矩形波及其幅值谱

由图 5-44 可知，周期信号的幅值谱为一簇谱线，随 $k$ 增大，即 $\omega { = } \frac { 2 \pi } { T } k$ 的增大，幅值谱的包络线衰减。若系统的控制输入为矩形波时，系统的跟踪能力取决于带宽覆盖矩形波频谱的范围，带宽大则处于较高频率范围的谱线衰减小，故失真小。

# (2) 非周期函数的频谱

非周期函数可以看作是周期 $T \mathrm { \longrightarrow } \infty$ 的周期函数。若 $f ( t )$ 为绝对可积函数，则 $f ( t )$ 可以表示为傅氏积分

$$
f (t) = \frac {1}{2 \pi} \int_ {- \infty} ^ {\infty} F (\mathrm {j} \omega) \mathrm {e} ^ {\mathrm {j} \omega t} \mathrm {d} \omega \tag {5-98}
$$

$$
F (\mathrm {j} \omega) = \int_ {- \infty} ^ {\infty} f (t) \mathrm {e} ^ {- \mathrm {j} \omega t} \mathrm {d} t \tag {5-99}
$$

$f ( t )$ 和 $F ( \mathrm { j } \omega )$ 构成傅氏变换对，而 $F ( \mathrm { j } \omega )$ 表示 $f ( t )$ 谐波的分布特性，也简称为频谱。与周

期信号的频谱不同，非周期信号的频谱为连续谱，单个方波的幅值谱特性如图 5-45所示。

![](images/a6600b5e210b4d99b2c6927f73e69ab1e23f8f02c143a8cac7b6a4842691932f.jpg)

![](images/65e32cb46b8708cb26f5a6cec14dc9a53cd341ea0688d6c6720225b0d9372234.jpg)

# 图 5-45 单个方波及其频谱特性

由图 5-45可知，当控制输入信号频谱特性具有收敛形式时，可按跟踪要求选定常数$\varepsilon$ ，若 $\omega { > } \omega _ { b }$ 时， $| F ( \mathrm { j } \omega ) | { < } \varepsilon$ ，从而确定系统所需要的带宽频率 $\omega _ { b }$

综上所述，系统的分析应区分输入信号的性质、位置，根据其频谱或谱密度以及相应的传递函数选择合适带宽，而系统的设计则主要围绕带宽来进行。为了设计合适的系统带宽，需要确定系统的闭环频率特性。

# 3. 确定闭环频率特性的方法

工程上常用MATLAB方法获得闭环频率特性：在已知系统开环传递函数条件下，直接调用命令 feedback和 bode，可立即得到闭环对数幅频和相频曲线，然后可判读出系统谐振频率 $\omega _ { r }$ 、谐振峰值 $M _ { r } ( \mathrm { d B } )$ 及带宽频率 $\omega _ { b }$ 。

# 4. 闭环系统频域指标和时域指标的转换

系统时域指标物理意义明确、直观，但不能直接应用于频域的分析和综合。闭环系统频域指标 $\omega _ { b }$ 虽然能反映系统的跟踪速度和抗干扰能力，但由于需要通过闭环频率特性加以确定，在校正元件的形式和参数尚需确定时显得较为不便。鉴于系统开环频域指标相角裕度和截止频率 $\omega _ { c }$ 可以利用已知的开环对数频率特性曲线确定，且由前面分析知，y和 $\omega _ { c }$ 的大小在很大程度上决定了系统的性能,因此工程上常用γ和 $\omega _ { c }$ 来估算系统的时域性能指标。

# (1) 系统闭环和开环频域指标的关系

系统开环指标截止频率 $\omega _ { c }$ 与闭环指标带宽频率 $\omega _ { b }$ 有着密切的关系。如果两个系统的稳定程度相仿，则 $\omega _ { c }$ 大的系统， $\omega _ { b }$ 也大； $\omega _ { c }$ 小的系统， $\omega _ { b }$ 也小。因此 $\omega _ { c }$ 和系统响应速度存在正比关系， $\omega _ { c }$ 可用来衡量系统的响应速度。鉴于闭环振荡性指标谐振峰值 $M _ { r }$ 和开环指标相角裕度 都能表征系统的稳定程度，故下面建立 $M _ { r }$ 和的近似关系：

设系统开环相频特性可以表示为

$$
\varphi (\omega) = - 1 8 0 ^ {\circ} + \gamma (\omega) \tag {5-100}
$$

其中 ()表示相角相对于 $- 1 8 0 ^ { \circ }$ 的相移。因此开环频率特性可以表示为

$$
G (\mathrm {j} \omega) = A (\omega) \mathrm {e} ^ {- \mathrm {j} [ 1 8 0 ^ {\circ} - \gamma (\omega) ]} = A (\omega) \left[ - \cos \gamma (\omega) - \mathrm {j} \sin \gamma (\omega) \right] \tag {5-101}
$$

闭环幅频特性

$$
\begin{array}{l} M (\omega) = \left| \frac {G (\mathrm {j} \omega)}{1 + G (\mathrm {j} \omega)} \right| = \frac {A (\omega)}{\left[ 1 + A ^ {2} (\omega) - 2 A (\omega) \cos \gamma (\omega) \right] ^ {\frac {1}{2}}} \\ = \frac {1}{\sqrt {\left[ \frac {1}{A (\omega)} - \cos \gamma (\omega) \right] ^ {2} + \sin^ {2} \gamma (\omega)}} \tag {5-102} \\ \end{array}
$$

一般情况下，在 $M ( \omega )$ 的极大值附近， $\gamma \ ( \omega )$ 变化较小，且使 $M ( \omega )$ 为极值的谐振频率 $\omega _ { r }$ 常位于 $\omega _ { c }$ 附近，即有

$$
\cos \gamma \left(\omega_ {r}\right) \approx \cos \gamma \left(\omega_ {c}\right) = \cos \gamma \tag {5-103}
$$

由式(5-102)可知，令 d ( ) 0M A  $\frac { \mathrm { d } M ( \omega ) } { \mathrm { d } A ( \omega ) } = 0$ $A ( \omega ) = \frac { 1 } { \cos { \gamma ( \omega ) } }$ 相应的 $M ( \omega )$ 为极值，故谐振峰值为

$$
M _ {r} = M \left(\omega_ {r}\right) = \frac {1}{\left| \sin \gamma \left(\omega_ {r}\right) \right|} \approx \frac {1}{\left| \sin \gamma \right|} \tag {5-104}
$$

由于 $\cos \gamma ( \omega _ { r } ) \leqslant 1$ ，故在闭环幅频特性的峰值处对应的开环幅值 $A ( \omega _ { r } ) \geqslant 1$ ，而 $A ( \omega _ { c } ) = 1$ ，显然 $\omega _ { r } \leqslant \omega _ { c }$ 。因此随着相角裕度 的减小， $\omega _ { c } – \omega _ { r }$ 减小，当 $\gamma = 0$ 时， $\omega _ { r } = \omega _ { c }$ 。由此可知，γ较小时，式(5-104)的近似程度较高。控制系统的设计中，一般先根据控制要求提出闭环频域指标 $\omega _ { b }$ 和 $M _ { r }$ ，再由式(5-104)确定相角裕度 和选择合适的截止频率 $\omega _ { c }$ ，然后根据 和$\omega _ { c }$ 选择校正网络的结构并确定参数。

# (2) 开环频域指标和时域指标的关系

对于典型二阶系统，第三章已建立了时域指标超调量 $\sigma \%$ 和调节时间 $t _ { s }$ 与阻尼比的关系式。而欲确定 和 $\omega _ { c }$ 与 $\sigma \%$ 和 $t _ { s }$ 的关系，只需确定 和 $\omega _ { c }$ 关于 $\zeta$ 的计算公式。因为典型二阶系统的开环频率特性为

$$
G (\mathrm {j} \omega) = \frac {\omega_ {n} ^ {2}}{\mathrm {j} \omega (\mathrm {j} \omega + 2 \zeta \omega_ {n})} = \frac {\omega_ {n} ^ {2}}{\omega \sqrt {\omega^ {2} + 4 \zeta^ {2} \omega_ {n} ^ {2}}} \angle \left(- 9 0 ^ {\circ} - \arctan \frac {\omega}{2 \zeta \omega_ {n}}\right)
$$

由 $\omega _ { c }$ 定义及式(5-85)求得

$$
\frac {\omega_ {c}}{\omega_ {n}} = \left(\sqrt {4 \zeta^ {4} + 1} - 2 \zeta^ {2}\right) ^ {\frac {1}{2}} \tag {5-105}
$$

由式(5-86)求出相角裕度

$$
\begin{array}{l} \gamma = 1 8 0 ^ {\circ} + \angle [ G (\mathrm {j} \omega_ {c}) ] = 1 8 0 ^ {\circ} - 9 0 ^ {\circ} - \arctan \frac {\omega_ {c}}{2 \zeta \omega_ {n}} \\ = \arctan \frac {2 \zeta \omega_ {n}}{\omega_ {c}} = \arctan \left[ 2 \zeta \left(\sqrt {4 \zeta^ {4} + 1} - 2 \zeta^ {2}\right) ^ {- \frac {1}{2}} \right] \tag {5-106} \\ \end{array}
$$

上式表明，典型二阶系统的相角裕度 与阻尼比 存在一一对应关系，图 5-46 是根据式(5-106)绘制的 - 曲线。由图 5-46 可知， 为 的增函数。

当选定 后，可由 - 曲线确定，再由 $\zeta$ 确定 $\sigma \%$ 和 $t _ { s }$

例 5-15 设一单位反馈系统的开环传递函数

$$
G (s) = \frac {K}{s (T s + 1)}
$$

若已知单位速度信号输入下的稳态误差 $e _ { s s } ( \infty ) = 1 / 9$ ，相角裕度 $\gamma { = } 6 0 ^ { \circ }$ ，试确定系统时域指标 $\sigma \%$ 和 $t _ { s }$ 。

解 因为该系统为Ⅰ型系统，单位速度输入下的稳态误差为 $1 / K$ ，由题设条件得 $K { = } 9$ 。由 $\gamma { = } 6 0 ^ { \circ }$ ，查图 5-46 得阻尼比 $\zeta = 0 . 6 2$ ，因此超调量

$$
\sigma \% = \mathrm{e}^{-\pi \zeta /\sqrt{1 - \zeta^2}}\times 100\% = 7.5\%
$$

![](images/25ce803d3a6653cb8b020da943d65208305d71fad7d95641425bf5cd22e6e1c0.jpg)  
图 5-46 典型二阶系统的 -曲线

由于

$$
K / T = \omega_ {n} ^ {2}, \quad 1 / T = 2 \zeta \omega_ {n}
$$

$$
\omega_ {n} = 2 K \zeta = 1 1. 1 6
$$

调节时间

$$
t _ {s} = \frac {3.5}{\zeta \omega_ {n}} = 0.506 \quad (\Delta = 5 \%)
$$

如果采用 MATLAB 仿真方法，可得系统的时域指标为

$$
\sigma \% = 8.29\%, \quad t _ {s} = 0.47 (\Delta = 5 \%)
$$

表明对于典型的无零点二阶系统，时域指标的估算结果是较准确的。

# (3) 高阶系统的时域指标的估算

对于具有一对共轭复数闭环极点的线性定常高阶系统，阶跃动态响应与频率响应之间通常存在下列关系：

1) $M _ { r }$ 值表征了相对稳定性。如果 $M _ { r }$ 的值在 $1 . 0 < M _ { r } < 1 . 4 ( 0 \mathrm { d B } < M _ { r } ( \mathrm { d B } ) < 3 \mathrm { d B } )$ 范围内，这相当于有效阻尼比 在 $0 . 4 { < } \zeta { < } 0 . 7$ 范围内，则通常可以获得满意的动态性能。当$M _ { r }$ 的值大于 1.5 时，阶跃动态响应可能呈现出若干次过调。  
2) 谐振频率 $\omega _ { r }$ 的大小表征了动态响应的速度。 $\omega _ { r }$ 的值越大，时间响应便越快。换句话说，上升时间随 $\omega _ { r }$ 成反比变化。在开环频率响应中，动态响应中的阻尼自然频率 $\omega _ { d }$ 将位于截止频率 $\omega _ { c }$ 与穿越频率 $\omega _ { x }$ 之间的某一位置上。  
3) 对于弱阻尼系统，谐振频率 $\omega _ { r }$ 与阶跃动态响应中的阻尼自然频率 $\omega _ { d }$ 很接近。

如果高阶系统可以用标准二阶系统近似，或者说可以用一对共轭复数闭环极点近似，则可以利用上述三条关系，将高阶系统的阶跃动态响应与频率响应联系起来。

对于一般高阶系统，开环频域指标和时域指标不存在解析关系式。通过对大量系统的 $M _ { r }$ 和 $\omega _ { c }$ 的研究，并借助于式(5-104)，归纳为下述两个近似估算公式：

$$
\sigma = 0. 1 6 + 0. 4 \left(\frac {1}{\sin \gamma} - 1\right), \quad 3 5 ^ {\circ} \leqslant \gamma \leqslant 9 0 ^ {\circ} \tag {5-107}
$$

$$
t _ {s} = \frac {K _ {0} \pi}{\omega_ {c}} \tag {5-108}
$$

其中

$$
K _ {0} = 2 + 1. 5 \left(\frac {1}{\sin \gamma} - 1\right) + 2. 5 \left(\frac {1}{\sin \gamma} - 1\right) ^ {2}, \quad 3 5 ^ {\circ} \leqslant \gamma \leqslant 9 0 ^ {\circ}
$$

应用上述经验公式估算高阶系统的时域指标，一般偏于保守，即实际性能比估算结果要好。对控制系统进行初步设计时，使用经验公式，可以保证系统达到性能指标的要求且留有一定的余地，然后进一步应用MATLAB软件进行验证。应用 MATLAB软件可以方便地获得闭环系统对数频率特性和系统时间响应，便于统筹兼顾系统的频域性能和时域性能。

例 5-16 已知单位反馈系统开环传递函数

$$
G (s) = \frac {1 1 . 7}{s (1 + 0 . 0 5 s) (1 + 0 . 0 4 s)}
$$

试分别利用MATLAB方法绘制系统的开环及闭环对数幅频和相频曲线，求出系统闭环谐振峰值 $M _ { r }$ 和带宽频率 $\omega _ { b }$ ，并确定系统相应的时域指标 $\sigma \%$ 和 $t _ { s }$ 。

解 利用 MATLAB 的伯德图绘制命令 magin 和 bode，可得系统的开环及闭环对数幅频和相频曲线分别如图 5-47 和图 5-48 所示。由图 5-47 可知，系统的幅值裕度$h ( \mathrm { d B } ) = 1 1 . 7 \mathrm { d B }$ ，相角裕度 $\gamma { = } 4 2 . 5 ^ { \circ }$ ，其对应的穿越频率 $\omega _ { x } { = } 2 2 . 4 \mathrm { r a d / s }$ ，截止频率 $\omega _ { c } { = } 9 . 7 9 \mathrm { r a d / s }$ ，闭环系统是稳定的。由图5-48可知，系统的闭环谐振峰值 $M _ { r } ( \mathrm { d B } ) { = } 2 . 9 1 \mathrm { d B }$ 和带宽频率 $\omega _ { b } =$ 17.2。图 5-49 为图 5-48 闭环系统对数幅频特性曲线的局部放大图，其横坐标取为频率值。随着频率增高，系统闭环幅频特性最终减小到零，闭环系统表现为低通滤波器。

![](images/dcd7b5224fdb563916b4fefab2f0bb2ee2c31198837a5212eed9b06556ef183e.jpg)  
图 5-47 系统开环对数幅频和相频曲线

![](images/64149231258fc29f692e673d628da512053976b07e3a2eadb5906b7518900e59.jpg)  
图 5-48 系统闭环对数幅频和相频曲线

![](images/3a55cc2ef49462979a4b8b6c57bf69c384550f7a90f72f2763f46d8863a48206.jpg)  
图 5-49 系统闭环幅频特性曲线局部放大图

![](images/538ff73056fe0cd24a8e8eb470252083acb02913681730d8093167a96f3828ac.jpg)  
图 5-50 闭环系统单位阶跃响应曲线

若应用式(5-107)及式(5-108)估算该高阶系统的时域指标，可得 $\sigma \% { = } 3 5 . 2 1 \%$ ，$t _ { s } { = } 1 . 0 6 s ( A { = } 5 \% )$ 。另由 MATLAB 软件仿真可知系统的超调量 $\sigma \% { = } 2 6 . 8 \%$ ，调节时间 $t _ { S } =$ $0 . 8 5 9 s ( A { = } 2 \% )$ ， $t _ { s } { = } 0 . 6 3 9 s ( A { = } 5 \% )$ ，系统单位阶跃响应曲线如图 5-50 所示。本例求解过程的 MATLAB仿真程序如下：

$\mathrm{G = zpk}([\quad ],[0 - 25 - 20],11.7^{*}20^{*}25);$ $\%$ 开环传递函数的零极点描述sys=feedback(G,1); $\%$ 闭环传递函数求解figure(1);margin(G);grid $\%$ 系统开环对数幅频和相频特性曲线绘制，并求出幅值裕度和相角裕度，及其对应的穿越频率和截止频率figure(2);bode(sys);grid $\%$ 系统闭环对数幅频和相频特性曲线绘制figure(3);step(sys); $\%$ 闭环系统单位阶跃响应

从例 5-16 可以看出，近似公式估算与实际仿真结果相比，偏于保守。

# 5-6 控制系统频域设计

# 例 5-17 雕刻机控制系统。

图 5-51(a)所示为雕刻机，其 $x$ 轴方向配有两台驱动电机，用来驱动雕刻针运动；另外，还各有一台单独的电机用于在 $y$ 轴和 $z$ 轴方向驱动雕刻针。雕刻机 $x$ 轴方向位置控制系统模型如图 5-51(b)所示。

本例的设计目标是：用频率响应法选择控制器增益 $K _ { 1 }$ 的值，使系统阶跃响应的各项指标保持在允许范围内。

解 本例设计的基本思路是：首先选择增益 $K _ { 1 }$ 的初始值，绘制系统的开环和闭环对数频率特性曲线，然后用闭环对数频率特性来估算系统时间响应的各项指标。若系统性能不满足设计要求，则调整 $K _ { 1 }$ 的取值，重复以上设计过程。最后，用实际系统的仿真来检验设计结果。

现在，取 $K _ { 1 } { = } 2$ ，则系统开环频率特性为

$$
G (\mathrm {j} \omega) = \frac {1}{\mathrm {j} \omega (0 . 5 \mathrm {j} \omega + 1) (\mathrm {j} \omega + 1)}
$$

![](images/ba61efa659d4e6f9a05be7e93161a58ba6517f179a2e986f00d0a7006039790b.jpg)

![](images/cd7b7f8cf88880980f6618d55c8820d701ac2758052f55c53c4bd7e8f05a0d20.jpg)  
  
图 5-51 雕刻机控制系统

计算 $G ( \mathrm { j } \omega )$ 的幅值与相位，如表 5-3所示。根据表5-3可绘制开环对数频率特性图如图 5-52所示。由图可见，系统的相角裕度 $\gamma = 3 3 ^ { \circ }$ ，相应的闭环系统是稳定的。

表 5-3 雕刻机 G(j)的频率响应  

<table><tr><td>ω</td><td>0.2</td><td>0.4</td><td>0.8</td><td>1.0</td><td>1.4</td><td>1.8</td></tr><tr><td>20lg|G|/ dB</td><td>14</td><td>7</td><td>-1</td><td>-4</td><td>-9</td><td>-13</td></tr><tr><td>φ(ω)/ (°)</td><td>-107</td><td>-123</td><td>-150.5</td><td>-162</td><td>-179.5</td><td>-193</td></tr></table>

![](images/40ff331b5fe0898d4184d4854d944f8a5ca0d99f88a1d042356eede5373824c3.jpg)  
图 5-52 雕刻机 G(j)的开环对数频率特性图

![](images/bcbb5bb0a17fdbf2f1605f612ebe370ecc5c03355d7adaf7e0fbdff196c52390.jpg)  
图 5-53 系统闭环对数频率特性图(MATLAB)

由闭环频率特性函数

$$
\begin{array}{l} \Phi (\mathrm {j} \omega) = \frac {2}{(\mathrm {j} \omega) ^ {3} + 3 (\mathrm {j} \omega) ^ {2} + 2 (\mathrm {j} \omega) + 2} \\ = \frac {2}{(2 - 3 \omega^ {2}) + j \omega (2 - \omega) ^ {2}} \\ \end{array}
$$

可以画出闭环频率特性曲线，如图 5-53 所示。

由图可见，系统存在谐振频率，其值 $\omega _ { r } = 0 . 8$ ，相应的谐振峰值

$$
2 0 \lg M _ {r} = 5 \mathrm {d B}, \quad M _ {r} = 1. 7 8
$$

根据图 5-53，可以认为系统的主导极点为共轭复极点。于是，由图5-54给出的关系曲线，并由 $M _ { r } = 1 . 7 8$ 估计

出系统的阻尼比 $\zeta = 0 . 2 8$ ，然后进一步得到标准化谐振频率 $\omega _ { r } / \omega _ { n } { = } 0 . 9 2$ 。

![](images/c4a1ac4c03c68f25ebe5fd5e988b89dd1dfd0fca3aa59e6598d04ce87cf18011.jpg)  
图 5-54 在共轭复极点项的频率响应中，谐振峰值 $M _ { r _ { \mathrm { > } } }$ 、谐振频率 $\omega _ { \mathrm { \ell } }$ 与阻尼比的关系曲线

因为已求出 $\omega _ { r } { = } 0 . 8$ ，故无阻尼自然频率

$$
\omega_ {n} = \frac {0 . 8}{0 . 9 2} = 0. 8 7
$$

于是，雕刻机控制系统的二阶近似模型应为

$$
\Phi (s) = \frac {\omega_ {n} ^ {2}}{s ^ {2} + 2 \zeta \omega_ {n} s + \omega_ {n} ^ {2}} = \frac {0 . 7 6}{s ^ {2} + 0 . 4 9 s + 0 . 7 6}
$$

根据近似模型，可以估算出系统的超调量为

$$
\sigma \% = \mathrm{e}^{-\pi \zeta /\sqrt{1 - \zeta^2}}\times 100\% = 40\%
$$

调节时间 $( A { = } 2 \% )$ )为

$$
t _ {s} = \frac {4 . 4}{\zeta \omega_ {n}} = 1 7. 9 6 \mathrm {s}
$$

最后，按实际三阶系统进行仿真，其单位阶跃响应如图 5-55 所示，得到 $\sigma \% =$ $3 9 \%$ ， $t _ { p } = 4 \mathrm { s }$ ， $t _ { S } = 1 6 \mathrm { s }$ 。结果表明，二阶近似模型是合理的，可以用来调节系统的参数。在本例中，如果要求更小的超调量，应取 $K _ { 1 } { < } 2$ ，然后重复以上设计过程。

![](images/86d9dd69e3d2c6fa089ee6ef5dd7a28c36183ba075ec78edcd70ac07bb8e9d30.jpg)  
图 5-55 雕刻机控制系统的阶跃响应(MATLAB)

MATLAB 程序如下：

K12;G0zkp([ ],[0 1 2],K1);

%系统开环传递函数

Gfeedback(G0,1)

%系统的闭环传递函数

figure(1);bode(G0);grid

%绘制系统的开环频率特性曲线

figure(2);bode(G);grid

%绘制系统的闭环频率特性曲线

figure(3);step(G);grid

%系统的单位阶跃响应

例 5-18 磁盘驱动读取系统(续)。

图 1-16 所示的磁盘驱动器是用弹性簧片来悬挂磁头的。当考虑簧片的弹性影响时，磁头位置控制系统如图 5-56 所示。磁头与簧片的典型参数： $\zeta = 0 . 3$ ， $\omega _ { n } { = } 1 8 . 8 5 \times 1 0 ^ { 3 } \mathrm { r a d / s }$ 。要求确定开环增益 $K { = } 1 0 0$ 时，磁盘驱动读取系统的幅值裕度 $h ( \mathrm { d B } )$ 、相角裕度及闭环系统的带宽频率 $\omega _ { b }$ ，并估算系统单位阶跃响应的 $\sigma \%$ 和 $t _ { S }$ 。

![](images/84a3a2fc6bb89a4b6d029b3e3ce64f9f5ace2d127b6c99075d9e7feeb16855a0.jpg)  
图 5-56 磁头位置控制系统结构图(包括簧片的弹性影响)

解 取 $K _ { 1 } { = } 2 0 0 0$ ，则开环增益 $K { = } 1 0 0$ ，根据对数幅频特性表达式

$$
2 0 \lg \left| K _ {1} (\mathrm {j} \omega + 1) G _ {1} (\mathrm {j} \omega) G _ {2} (\mathrm {j} \omega) G _ {3} (\mathrm {j} \omega) \right|
$$

在一些选定的频率点上，画出开环系统对数幅频渐近特性，如图 5-57 所示。由图可见，在簧片自然频率 $\omega _ { n }$ 附近，幅频特性曲线比渐近线高约 5dB。

![](images/510c4ba34e7c84f12eb21fd5e24ac936e42fa0a21a85d3263de59e44a00e75cb.jpg)  
图 5-57 磁盘驱动读取系统开环对数幅频渐近特性

利用 MATLAB 软件，可以画出开环系统的对数频率特性，如图 5-58 所示。由图 5-58 可以确定： $h ( \mathrm { d B } ) { = } 2 2 . 8 \mathrm { d B }$ ， $\gamma { = } 3 7 . 3 ^ { \circ }$ ， $\omega _ { c } { = } 1 2 0 0 \mathrm { r a d / s } _ { \odot }$ 。

![](images/592eb876861764f2fe873169485d9795133b2a101bca5a457c79c0440877da73.jpg)  
图 5-58 磁盘驱动读取系统开环对数频率特性图(MATLAB)

为了确定闭环系统带宽频率 $\omega _ { b }$ ，绘制磁盘驱动读取系统准确的闭环对数幅频特性，

如图 5-59 所示。由图 5-59 可以确定 $\omega _ { b } { = } 2 0 0 0 \mathrm { r a d / s }$ 。显然，只要取 $K _ { 1 } { = } 2 0 0 0$ ，簧片自然频率 $\omega _ { n }$ 及 $\omega _ { n }$ 附近的系统谐振频率 $\omega _ { r }$ 就会位于闭环带宽 $\omega _ { b }$ 之外，从而使簧片弹性对系统动态性能的影响甚微。

![](images/e3e097c12ac11ee8292271275aa189d1cbf30ef89d9378467aebd8220eb823e7.jpg)  
图 5-59 磁盘驱动读取系统闭环对数频率特性(MATLAB)

系统单位阶跃响应的动态性能指标，可以利用下列式子估算：

$$
\sigma \% = 100 \left[ 0.16 + 0.4 \left(\frac{1}{\sin \gamma} - 1\right) \right] \% = 42.1 \%
$$

$$
K _ {0} = 2 + 1. 5 \left(\frac {1}{\sin \gamma} - 1\right) + 2. 5 \left(\frac {1}{\sin \gamma} - 1\right) ^ {2} = 4. 0 4
$$

$$
t _ {s} = \frac {K _ {0} \pi}{\omega_ {c}} = 10.1 \mathrm {ms} \quad (\Delta = 5 \%
$$

上述估算公式是偏保守的，仅能用于系统的初步设计。实际上，图 5-56所示磁头位置控制系统的单位阶跃响应曲线如图 5-60 所示。由图可得系统的动态性能

$$
\sigma \% \approx 31\%, \quad t _ {s} = 9.2 \mathrm{ms} \quad (\Delta = 2\%)
$$

MATLAB 程序如下：

num2000*0.05*[1,1]; den[conv(conv([0.001,1],[1/20,1]),conv([1,0],[(1/18850)^2,2*0.3/18850,1]))];

G0tf(num,den);Gfeedback(G0,1); %系统的开环和闭环传递函数

t0:0.0001:0.02;

figure(1);bode(G0);grid %绘制系统的开环频率特性曲线

figure(2);bode(G);grid %绘制系统的闭环频率特性曲线

figure(3);step(G,t);grid %系统的单位阶跃响应

Python 程序如下：

import control as ctr

```python
import matplotlib.pyplot as plt  
import numpy as np  
num = [2000*0.05,2000*0.05]  
den = [0,0,0.0001,0.051,1,0]  
G0 = ctr=tf(num,den) #系统的开环和闭环传递函数  
G = ctr_feedback(G0,1)  
t = np.arange(0,0.02,0.0001)  
plt.figure(1) #绘制系统的开环频率特性曲线  
ctr.bode_plot(G0)  
plt.grid(1)  
plt.figure(2) #绘制系统的闭环频率特性曲线  
ctr.bode_plot(G)  
plt.grid(1)  
plt.figure(3) #绘制系统的单位阶跃响应  
t1,y1 = ctr(step_response(G,t))  
plt.plot(t1,y1)  
pltylabel('Amplitude')  
pltxlabel('Time/sec')  
plt.grid(1)  
plt.show() 
```

![](images/1d78a6c4649a0c24c98959d98bb962d1581485d703431ad1397e1a832f52ce6a.jpg)  
图 5-60 磁头位置控制系统的单位阶跃响应(MATLAB)

# 习 题

5-1 设系统闭环稳定，闭环传递函数为 $\phi ( s )$ ，试根据频率特性的定义证明，输入为余弦函数$r ( t ) = A \cos ( \omega t + \varphi )$ 时，系统的稳态输出为

$$
c _ {s s} (t) = A \cdot | \Phi (\mathrm {j} \omega) | \cos [ \omega t + \varphi + \angle [ \Phi (\mathrm {j} \omega) ] ]
$$

5-2 若系统单位阶跃响应

$$
c (t) = 1 - 1. 8 \mathrm {e} ^ {- 4 t} + 0. 8 \mathrm {e} ^ {- 9 t}
$$

试确定系统的频率特性。

5-3 设控制系统结构图如图 5-61 所示，试确定在输入信号

$$
r (t) = \sin (t + 3 0 ^ {\circ}) - \cos (2 t - 4 5 ^ {\circ})
$$

作用下，系统的稳态误差 $e _ { s s } ( t )$ 。

5-4 典型二阶系统的开环传递函数

$$
G (s) = \frac {\omega_ {n} ^ {2}}{s (s + 2 \zeta \omega_ {n})}
$$

![](images/b2f8c979c5b6571340824b85df1899aa6de9d04b1833d7a39dbdff0d53c2d107.jpg)  
图 5-61 控制系统结构图

当取 $r ( t ) = 2 \sin t$ 时，系统的稳态输出

$$
c _ {s s} (t) = 2 \sin (t - 4 5 ^ {\circ})
$$

试确定系统参数 $\omega _ { n }$ ， $\zeta$ 。

5-5 已知系统开环传递函数

$$
G (s) H (s) = \frac {K (\tau s + 1)}{s ^ {2} (T s + 1)}; \quad K, \tau , T > 0
$$

试分析并绘制 $\tau > T$ 和 $T > \tau$ 情况下的概略开环幅相特性曲线。

5-6 已知系统开环传递函数

$$
G (s) H (s) = \frac {1}{s ^ {\nu} (s + 1) (s + 2)}
$$

试分别绘制 $\nu = 1$ ，2，3，4 时系统的概略开环幅相特性曲线。

5-7 已知系统开环传递函数

$$
G (s) = \frac {K (- T _ {2} s + 1)}{s \left(T _ {1} s + 1\right)}; \quad K, T _ {1}, T _ {2} > 0
$$

当取 $\omega { = } 1$ 时， $\angle [ G ( \mathrm { j } \omega ) ] = - 1 8 0 ^ { \circ }$ ， $| G ( \mathrm { j } \omega ) | { = } 0 . 5$ 。当输入为单位速度信号时，系统的稳态误差为 0.1，试写出系统开环频率特性表达式 $G ( \mathrm { j } \omega )$ 。

5-8 已知系统开环传递函数

$$
G (s) H (s) = \frac {1 0}{s (2 s + 1) \left(s ^ {2} + 0 . 5 s + 1\right)}
$$

试分别计算 $\omega { = } 0 . 5$ 和 $\omega = 2$ 时，开环频率特性的幅值 $A ( \omega )$ 和相位 $\varphi \left( \omega \right)$ 。

5-9 已知系统开环传递函数

$$
G (s) H (s) = \frac {1 0}{s (s + 1) \left(s ^ {2} / 4 + 1\right)}
$$

试绘制系统概略开环幅相特性曲线。

5-10 已知系统开环传递函数

$$
G (s) H (s) = \frac {(s + 1)}{s \left(\frac {s}{2} + 1\right) \left(\frac {s ^ {2}}{9} + \frac {s}{3} + 1\right)}
$$

要求选择频率点，列表计算 $A ( \omega )$ ， $L ( \omega )$ 和 $\varphi ( \omega )$ ，并据此在半对数坐标纸上绘制系统开环对数频率特性曲线。

5-11 绘制下列传递函数的对数幅频渐近特性曲线：

(1) $G ( s ) = { \frac { 2 } { ( 2 s + 1 ) ( 8 s + 1 ) } } ;$   
(2) $G ( s ) = { \frac { 2 0 0 } { s ^ { 2 } ( s + 1 ) ( 1 0 s + 1 ) } } ;$   
(3) $G ( s ) = { \frac { 8 { \Bigg ( } { \frac { s } { 0 . 1 } } + 1 { \Bigg ) } } { s { \big ( } s ^ { 2 } + s + 1 { \big ) } { \Bigg ( } { \frac { s } { 2 } } + 1 { \Bigg ) } } } ~ ;$ 1) 1 s       ；  
(4) $G ( s ) = { \frac { 1 0 { \left( \frac { s ^ { 2 } } { 4 0 0 } + \frac { s } { 1 0 } + 1 \right) } } { s ( s + 1 ) { \left( \frac { s } { 0 . 1 } + 1 \right) } } } \circ$

5-12 已知最小相位系统的对数幅频渐近特性曲线如图5-62所示，试确定系统的开环传递函数。

![](images/36025ed158c9f79fbb9b5ad019c0274195f34c315bda1547583b42512c59afaa.jpg)

![](images/2c730a111879c8a4505ef33e1af232ad235d6a93a219bd175be430a50475c1f2.jpg)

![](images/60757d3620176980be08ab39ed7e55d668955be826fd49a1f96850fcd7c67c31.jpg)  
  
图 5-62 系统开环对数幅频渐近特性

5-13 试用奈氏判据分别判断题5-5、题5-6中系统的闭环稳定性。  
5-14 已知下列系统开环传递函数(参数 $K , T , T _ { i } > 0$ ； $i { = } 1 , 2 , \ \cdots , 6 )$ ：

(1) $G ( s ) = \frac { K } { ( T _ { 1 } s + 1 ) ( T _ { 2 } s + 1 ) ( T _ { 3 } s + 1 ) } \ ;$   
(2) $G ( s ) = \frac { K } { s ( T _ { 1 } s + 1 ) ( T _ { 2 } s + 1 ) } ;$   
(3) $G ( s ) = \frac { K } { s ^ { 2 } ( T s + 1 ) } ;$   
(4) $G ( s ) = { \frac { K ( T _ { 1 } s + 1 ) } { s ^ { 2 } ( T _ { 2 } s + 1 ) } }$ ；  
(5) $G ( s ) = \frac { K } { s ^ { 3 } }$ 3 s ；  
(6) $G ( s ) = { \frac { K ( T _ { 1 } s + 1 ) ( T _ { 2 } s + 1 ) } { s ^ { 3 } } } \ ;$ s   
(7) $G ( s ) = \frac { K ( T _ { 5 } s + 1 ) ( T _ { 6 } s + 1 ) } { s ( T _ { 1 } s + 1 ) ( T _ { 2 } s + 1 ) ( T _ { 3 } s + 1 ) ( T _ { 4 } s + 1 ) } \ ;$   
(8) $G ( s ) = \frac { K } { T s - 1 } ;$   
(9) $G ( s ) = { \frac { - K } { - T s + 1 } } ;$   
(10) $G ( s ) = \frac { K } { s ( T s - 1 ) } \circ$

其系统开环幅相特性曲线分别如图 $5 { - } 6 3 ( \mathrm { a } ) { \sim } ( \mathrm { j } )$ 所示，试根据奈氏判据判定各系统的闭环稳定性，若系统闭环不稳定，确定其 $s$ 右半平面的闭环极点数。

5-15 根据奈氏判据确定题 5-9 系统的闭环稳定性。  
5-16 已知系统开环传递函数

$$
G (s) = \frac {K}{s (T s + 1) (s + 1)}; \quad K, T > 0
$$

试根据奈氏判据，确定其闭环稳定条件：

(1) $T { = } 2$ 时， $K$ 值的范围；  
(2) $K { = } 1 0$ 时， $T$ 值的范围；

(3) K， $T$ 值的范围。

5-17 试用对数稳定判据判定题 5-10 系统的闭环稳定性。

5-18 已知两个最小相位系统开环对数相频特性曲线如图5-64所示，试分别确定系统的稳定性。鉴于改变系统开环增益可使系统截止频率变化，试确定系统闭环稳定时，截止频率 $\omega _ { - }$ 的范围。

![](images/5e3ff689d59e5201fa8a632f02972b799b468fa0636a7ac507396aeac68251cd.jpg)

![](images/a86e63292bfd2bdb1a23f8a5cdd6e448ff672870745d67d49536acb521aab81f.jpg)

![](images/758287754c3f8d630579f61cf1c378bfbf1712f2e539cbd60c285e2208fe07cc.jpg)

![](images/b214db2028da1004466fe90cf8313430c6b6eeb1d1b4ed9bbf22564d4a1d5207.jpg)

![](images/8eb48d5fc4b699493c756ce8110fbce3e12750349fdfacf5d0a45eab04e086e4.jpg)

![](images/09f63b53bd2958298a7f73a0397d8bb8606cda476a888cd56682de7622e575c8.jpg)

![](images/693943eabf5abad33509087d17c9b39b92b07c4b527c9d85166fd285e1d2f025.jpg)

![](images/0550f14975b406d6f3302e1849e2189d8fc8f4756fc65a86759d9e23b9242ed1.jpg)

![](images/03dd4e23861b663f653be4d0743d622b73cc002316fb83abb504d2dc3f6fddd0.jpg)

![](images/95227914aeaa1cebaf7865309019d1fc4da53b258e8ccabf8a3f3979cb5e9a01.jpg)

![](images/5b302e706570e85fd52f694c659a54d3b4690bcf369897851b5e26a0e8cf6478.jpg)  
图 5-63 系统开环幅相曲线

![](images/663bafb3ef82ed31c99f691d1fff2c0e3040f5cc752cfb1088a8dfcf2cf67d8f.jpg)  
  
图 5-64 开环对数相频特性曲线

5-19 若单位反馈系统的开环传递函数

$$
G (s) = \frac {K e ^ {- 0 . 8 s}}{s + 1}
$$

试确定使系统稳定的 $K$ 值范围。

5-20 设单位反馈系统的开环传递函数

$$
G (s) = \frac {5 s ^ {2} \mathrm {e} ^ {- \tau s}}{(s + 1) ^ {4}}
$$

试确定闭环系统稳定时，延迟时间 $\tau$ 的范围。

5-21 设单位反馈控制系统的开环传递函数

$$
G (s) = \frac {a s + 1}{s ^ {2}}
$$

试确定相角裕度为 $4 5 ^ { \circ }$ 时参数 $^ { a }$ 的值。

5-22 对于典型二阶系统，已知参数 $\omega _ { n } { = } 3$ ， $\zeta = 0 . 7$ ，试确定截止频率 $\omega _ { - }$ 和相角裕度 。  
5-23 对于典型二阶系统，已知 $\sigma \% { = } 1 5 \%$ ， $t _ { S } { = } 3 \mathrm { s } ( \varDelta { = } 2 \% )$ ，试计算相角裕度 。  
5-24 根据题5-11所绘对数幅频渐近特性曲线，近似确定截止频率 $\omega _ { \mathrm { - } }$ ，并由此确定相角裕度 的近似值。

# 5-25 大型油船航向控制系统的开环传递函数为

$$
G (s) = \frac {E (s)}{\Delta (s)} = \frac {0 . 1 6 4 (s + 0 . 2) (- s + 0 . 3 2)}{s ^ {2} (s + 0 . 2 5) (s - 0 . 0 0 9)}
$$

其中， $E ( s )$ 为油船偏航角的拉氏变换；(s)是舵机偏转角的拉氏变换。试验证图 5-65所示的油船航向控制系统的开环对数频率特性的形状是否准确。

![](images/2d1c23851e9cf158ef7dc9470ca3d00dcaba713f13bf734eafea39a68c975eab.jpg)

![](images/017f7d949709f1e35b470242e3762890a55c07743dc12cae05df8b4fb3fea54a.jpg)  
图 5-65 油船航向控制系统的开环对数频率特性

5-26 图 5-66(a)是卫星修理示意图，宇航员的脚固定在航天飞机机械手臂顶端的工作台上，以便他能用双手来完成阻止卫星转动和点火启动卫星等操作。机械臂控制系统的框图如图 5-66(b)所示，其中

![](images/1f96e8a4559d6966f5b32ed9f38d0ff42e4f2e8cdd98283c2611969563e4924d.jpg)  
(a)航天飞机修理卫星示意图

![](images/50575919f4645d08ad74edf9af85299611f494e9dd39a243e1c9cd45c5566fb0.jpg)  
(b)机械臂控制系统框图  
图 5-66 航天飞机机械臂控制系统

$$
G _ {1} (s) = K = 1 0, \quad H (s) = 1
$$

若已知闭环传递函数为

$$
\Phi (s) = \frac {C (s)}{R (s)} = \frac {1 0}{s ^ {2} + 5 s + 1 0}
$$

要求：

(1) 确定系统对单位阶跃扰动的响应表达式 $c _ { n } ( t )$ 及 $c _ { n } ( \infty )$ 的值；  
(2) 计算闭环系统的带宽频率 $\omega _ { b }$ 。

5-27 试验中的旋翼飞机装有一个可以旋转的机翼，如图 5-67 所示。当飞机速度较低时，机翼将处在正常位置；而在飞机速度较高时，机翼将旋转到一个其他的合适位置，以便改善飞机的超音速飞行品质。假定飞机控制系统的 $H ( s ) { = } 1$ ，且

$$
G (s) = \frac {4 (0 . 5 s + 1)}{s (2 s + 1) \left[ \left(\frac {s}{8}\right) ^ {2} + \left(\frac {s}{2 0}\right) + 1 \right]}
$$

要求：

(1) 绘制开环系统的对数频率特性曲线；  
(2) 确定幅值增益为 0dB 时对应的频率 $\omega _ { - }$ 和相角为180°时对应的频率 $\omega _ { x }$ 。

5-28 美国卡耐尔基-梅隆大学机器人研究所开发研制了一套用于星际探索的系统，其目标机器人是一个六足步行机器人，如图 5-68(a)所示。该机器人单足控制系统结构图如图 5-68(b)所示。要求：

![](images/31a9d3c73e06658350c6b685002186a1a1a08fa7ce47142bdef227f033c41efa.jpg)

![](images/ad448ca86d11208437d4c6e5881449ba102b54219fcab16b34addc5c6459ac6e.jpg)  
图 5-67 旋转翼飞机示意图

(1) 绘制 $K { = } 2 0$ 时，闭环系统的对数频率特性；  
(2) 分别确定 $K { = } 2 0$ 和 $K { = } 4 0$ 时，闭环系统的谐振峰值 $M _ { r }$ 、谐振频率 $\omega _ { r }$ 和带宽频率 $\omega _ { b }$ 。

![](images/b2818a93008b019d7f785e029fa24808184754e2d767ce70ef37d0f8702a65ea.jpg)

![](images/414be03e856f5d258b522c96eb77ee279607254b168697a9eb8a019f584ae3c6.jpg)  
(b)单足控制系统结构图  
图 5-68 步行机器人

5-29 在脑外科、眼外科等类似手术中，患者肌肉的无意识运动可能会导致灾难性的后果。为了保证合适的手术条件，可以采用控制系统实施自动麻醉，以保证稳定的用药量，使患者肌肉放松。图5-69为麻醉控制系统模型，试确定控制器增益 $K$ 和时间常数，使系统谐振峰值 $M _ { r } \leqslant 1 . 5$ ，并确定相应的闭环带宽频率 $\omega _ { b }$ 。

![](images/537939e6f5e3c03d831d40a849b195007c372ae165a095dbdecc9d6f2c85e7e6.jpg)  
图 5-69 麻醉控制系统结构图