# 第11章 概率图模型

概率论只不过是把常识归纳为计算问题

—皮埃尔-西蒙·拉普拉斯（Pierre-Simon Laplace）

概率图模型（Probabilistic Graphical Model，PGM），简称图模型（Graph-ical Model，GM），是指一种用图结构来描述多元随机变量之间条件独立关系的概率模型，从而给研究高维空间中的概率模型带来了很大的便捷性

对于一个?? 维随机向量 $\pmb { X } = [ X _ { 1 } , X _ { 2 } , \cdots , X _ { K } ] ^ { \intercal }$ ，其联合概率为高维空间中的分布，一般难以直接建模．假设每个变量为离散变量并有??个取值，在不作任何独立假设条件下，则需要???? −1个参数才能表示其概率分布．当 $M = 2 , K = 1 0 0$ 时，参数量约为 $1 0 ^ { 3 0 }$ ，远远超出了目前计算机的存储能力

一种有效减少参数量的方法是独立性假设．一个??维随机向量?? 的联合概率分解为??个条件概率的乘积，

$$
p (\boldsymbol {x}) \triangleq P (\boldsymbol {X} = \boldsymbol {x}) \tag {11.1}
$$

$$
= \prod_ {k = 1} ^ {K} p (x _ {k} | x _ {1}, \dots , x _ {k - 1}), \tag {11.2}
$$

其中 $x _ { k }$ 表示变量 $X _ { k }$ 的取值．如果某些变量之间存在条件独立，其参数量就可以大幅减少

假设有四个二值变量 $X _ { 1 } , X _ { 2 } , X _ { 3 } , X _ { 4 }$ ，在不知道这几个变量依赖关系的情况下，可以用一个联合概率表来记录每一种取值的概率 $p ( \pmb { x } _ { 1 : 4 } )$ ，共需要 $2 ^ { 4 } - 1 = 1 5$ 个参数．假设在已知 $X _ { 1 }$ 时， $X _ { 2 }$ 和 $X _ { 3 }$ 独立，即有

$$
p (x _ {2} | x _ {1}, x _ {3}) = p (x _ {2} | x _ {1}), \tag {11.3}
$$

$$
p (x _ {3} | x _ {1}, x _ {2}) = p (x _ {3} | x _ {1}). \tag {11.4}
$$

在本书中，随机变量用斜体的大写字母表示，其取值用斜体的小写字母表示；随机向量用粗斜体的大写字母表示，其取值用粗斜体的小写字母表示

在已知 $X _ { 2 }$ 和 $X _ { 3 }$ 时， $X _ { 4 }$ 也和 $X _ { 1 }$ 独立，即有

$$
p (x _ {4} | x _ {1}, x _ {2}, x _ {3}) = p (x _ {4} | x _ {2}, x _ {3}), \tag {11.5}
$$

那么其联合概率??(??)可以分解为

$$
p (\boldsymbol {x}) = p (x _ {1}) p (x _ {2} | x _ {1}) p (x _ {3} | x _ {1}, x _ {2}) p (x _ {4} | x _ {1}, x _ {2}, x _ {3}), \tag {11.6}
$$

$$
= p (x _ {1}) p (x _ {2} | x _ {1}) p (x _ {3} | x _ {1}) p (x _ {4} | x _ {2}, x _ {3}), \tag {11.7}
$$

即4个局部条件概率的乘积．如果分别用4个表格来记录这4个条件概率的话，只需要 $1 + 2 + 2 + 4 = 9$ 个独立参数

当概率模型中的变量数量比较多时，其条件依赖关系也比较复杂．我们可以使用图结构的方式将概率模型可视化，以一种直观、简单的方式描述随机变量之间的条件独立性，并可以将一个复杂的联合概率模型分解为一些简单条件概率模型的组合．图11.1给出了上述例子中4个变量之间的条件独立性的图形化描述．图中每个节点表示一个变量，每条连边表示变量之间的依赖关系

![](images/5d0eeefab9f70c388b11a31d2051679e4e8b84e88718efc962095d1b87ed2d85.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    X1 --> X3
    X1 --> X2
    X2 --> X4
    X3 --> X4
```
</details>

图 11.1 变量 $X _ { 1 } , X _ { 2 } , X _ { 3 } , X _ { 4 }$ 之间条件独立性的图形化表示

图模型的基本问题 图模型有三个基本问题：

（1） 表示问题：对于一个概率模型，如何通过图结构来描述变量之间的依赖关系  
（2） 学习问题：图模型的学习包括图结构的学习和参数的学习．在本章中，我们只关注在给定图结构时的参数学习，即参数估计问题  
（3） 推断问题：在已知部分变量时，计算其他变量的条件概率分布

图模型与机器学习 很多机器学习模型都可以归结为概率模型，即建模输入和输出之间的条件概率分布．因此，图模型提供了一种新的角度来解释机器学习模型，并且这种角度有很多优点，比如了解不同机器学习模型之间的联系，方便设计新模型等．在机器学习中，图模型越来越多地用来设计和分析各种学习算法

# 11.1 模型表示

图由一组节点和节点之间的边组成．在概率图模型中，每个节点都表示一个随机变量（或一组随机变量），边表示这些随机变量之间的概率依赖关系

常见的概率图模型可以分为两类：有向图模型和无向图模型

（1）有向图模型使用有向非循环图（Directed Acyclic Graph，DAG）来描述变量之间的关系．如果两个节点之间有连边，表示对应的两个变量为因果关系，即不存在其他变量使得这两个节点对应的变量条件独立  
（2）无向图模型使用无向图（Undirected Graph）来描述变量之间的关系每条边代表两个变量之间有概率依赖关系，但是并不一定是因果关系

图11.2给出了两个代表性图模型（有向图和无向图）的示例，分别表示了四个变量 $\{ X _ { 1 } , X _ { 2 } , X _ { 3 } , X _ { 4 } \}$ 之间的依赖关系．图中带阴影的节点表示可观测到的变量，不带阴影的节点表示隐变量，连边表示两变量间的条件依赖关系

在本章后文中，节点、随机变量、变量的概念会 经 常 混 用．每 个节点对应一个随机变量

![](images/113f8655821745c2466d3facc7428a53046d4588724e5cedfc84477ed20799c6.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    X1 --> X3
    X1 --> X2
    X2 --> X4
    X3 --> X4
```
</details>

(a)有向图：贝叶斯网络

![](images/d6009f134e0fc120e81e692ef757c6b7191d84620824618b75df0cc8a5adfdde.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    X1 --> X3
    X1 --> X2
    X3 --> X4
    X2 --> X4
```
</details>

(b)无向图：马尔可夫随机场  
图11.2 有向图和无向图示例

# 11.1.1 有向图模型

有向图模型（Directed Graphical Model），也称为贝叶斯网络（BayesianNetwork）或信念网络（Belief Network，BN），是一类用有向图来描述随机向量概率分布的模型

定义 11.1–贝叶斯网络： 对于一个?? 维随机向量?? 和一个有?? 个节点的有向非循环图??，??中的每个节点都对应一个随机变量，每个连接 $e _ { i j }$ 表示两个随机变量 $X _ { i }$ 和 $X _ { j }$ 之间具有非独立的因果关系．令 $\scriptstyle \mathbf { X } _ { \pi _ { k } }$ 表示变量 $X _ { k }$ 的所有父节点变量集合， $P ( X _ { k } | X _ { \pi _ { k } } )$ 表示每个随机变量的局部条件概率分布（Local Conditional Probability Distribution）．如果 ?? 的联合概率分布可以分解为每个随机变量 $X _ { k }$ 的局部条件概率的连乘形式，即

$$
p (\boldsymbol {x}) = \prod_ {k = 1} ^ {K} p (x _ {k} | \boldsymbol {x} _ {\pi_ {k}}), \tag {11.8}
$$

那么(??, ??)构成了一个贝叶斯网络

条件独立性 在贝叶斯网络中，如果两个节点是直接连接的，它们肯定是非条件独立的，是直接因果关系．父节点是“因”，子节点是“果”

如果两个节点不是直接连接的，但可以由一条经过其他节点的路径来连接，那么这两个节点之间的条件独立性就比较复杂．以三个节点的贝叶斯网络为例，给定三个节点 $X _ { 1 } , X _ { 2 } , X _ { 3 }$ ，其中 $X _ { 1 }$ 和 $X _ { 3 }$ 是不直接连接的，通过节点 $X _ { 2 }$ 连接这三个节点之间可以有四种连接关系，如图11.3所示．在图11.3a和图11.3b中，$X _ { 1 }$ ⟂/ $X _ { 3 } | \emptyset$ ，但 $X _ { 1 }$ ⟂ $X _ { 3 } | X _ { 2 }$ ；在图11.3c中， $X _ { 1 }$ ⟂/ $X _ { 3 } | \emptyset$ ，但 $X _ { 1 }$ ⟂ $X _ { 3 } | X _ { 2 }$ ；在图11.3d中，$X _ { 1 }$ ⟂ $X _ { 3 } | \emptyset$ ，但 $X _ { 1 }$ ⟂/ $X _ { 3 } | X _ { 2 }$

![](images/5f3787199f97825b409c4a358a6f21186741b2a8c03a28f122f9dd71fca417ff.jpg)  
图11.3 三个变量的依赖关系示例

图11.3中的四种关系分别为：

参见习题11-1

（1） 间接因果关系（图11.3a）：当 $X _ { 2 }$ 已知时， $X _ { 1 }$ 和 $X _ { 3 }$ 为条件独立，即$X _ { 1 }$ ⟂ $X _ { 3 } | X _ { 2 }$   
（2） 间接果因关系（图11.3b）：当 $X _ { 2 }$ 已知时， $X _ { 1 }$ 和 $X _ { 3 }$ 为条件独立，即$X _ { 1 }$ ⟂ $X _ { 3 } | X _ { 2 }$   
（3） 共因关系（图11.3c）：当 $X _ { 2 }$ 未知时， $X _ { 1 }$ 和 $X _ { 3 }$ 是不独立的；当 $X _ { 2 }$ 已知时， $X _ { 1 }$ 和 $X _ { 3 }$ 条件独立，即 $X _ { 1 }$ ⟂ $X _ { 3 } | X _ { 2 }$   
（4） 共果关系（图11.3d）：当 $X _ { 2 }$ 未知时， $X _ { 1 }$ 和 $X _ { 3 }$ 是独立的；当 $X _ { 2 }$ 已知时，$X _ { 1 }$ 和 $X _ { 3 }$ 不独立，即 $X _ { 1 }$ ⟂/ $X _ { 3 } | X _ { 2 }$

局部马尔可夫性质 对一个更一般的贝叶斯网络，其局部马尔可夫性质为：每个随机变量在给定父节点的情况下，条件独立于它的非后代节点

$$
X _ {k} \perp \perp Z | X _ {\pi_ {k}}, \tag {11.9}
$$

从 公 式(11.2)和 公 式(11.8)可得到．参见习题11-2

其中 $Z$ 为 $X _ { k }$ 的非后代变量

# 11.1.2 常见的有向图模型

很多经典的机器学习模型可以使用有向图模型来描述，比如朴素贝叶斯分类器、隐马尔可夫模型、深度信念网络等

# 11.1.2.1 Sigmoid 信念网络

为了减少模型参数，可以使用参数化模型来建模有向图模型中的条件概率分布．一种简单的参数化模型为Sigmoid信念网络[Neal, 1992]

Sigmoid 信念网络（Sigmoid Belief Network，SBN）中的变量取值为 {0, 1}对于变量 $X _ { k }$ 和它的父节点集合 $\pi _ { k }$ ，其条件概率分布表示为

$$
p (x _ {k} = 1 | \boldsymbol {x} _ {\pi_ {k}}; \theta) = \sigma (\theta_ {0} + \sum_ {x _ {i} \in \boldsymbol {x} _ {\pi_ {k}}} \theta_ {i} x _ {i}), \tag {11.10}
$$

其中 ??(⋅) 是 Logistic 函数， $\theta _ { i }$ 是可学习的参数．假设变量 $X _ { k }$ 的父节点数量为??，如果使用表格来记录条件概率需要 $2 ^ { M }$ 个参数，如果使用参数化模型只需要?? +1个参数．如果对不同的变量的条件概率都共享使用一个参数化模型，其参数数量又可以大幅减少

值得一提的是，Sigmoid信念网络与Logistic回归模型都采用Logistic函数来计算条件概率．如果假设Sigmoid信念网络中只有一个叶子节点，其所有的父节点之间没有连接，且取值为实数，那么Sigmoid信念网络的网络结构和Logis-tic回归模型类似，如图11.4所示．但是，这两个模型的区别在于，Logistic回归模型中的??作为一种确定性的参数，而非变量．因此，Logistic回归模型只建模条件概率??(??|??)，是一种判别模型；而Sigmoid信念网络建模联合概率??(??, ??)，是一种生成模型

更复杂的深度信念网络，参见第12.3节

Logistic 回归模型也经常被看作一种条件无向图模型

![](images/063cf678dff84d5fdb85d4c086043faa4aa45bd7356f566051633e862f8a896f.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    X1["X₁"] --> Y["Y"]
    Xm["Xₘ"] --> Y["Y"]
    XM["Xₘ"] --> Y["Y"]
```
</details>

(a)只有一层的简单Sigmoid信念网络

![](images/54fbb306d4db6698e7d49f8632200f46d5ac7c4840c0be0a2f1c4d68511ab90a.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    X1 --> Y
    Xm --> Y
    XM --> Y
```
</details>

(b) Logistic 回归模型  
图 11.4 Sigmoid 信念网络和 Logistic 回归模型的比较

# 11.1.2.2 朴素贝叶斯分类器

朴素贝叶斯（Naive Bayes，NB）分类器是一类简单的概率分类器，在强（朴素）独立性假设的条件下运用贝叶斯公式来计算每个类别的条件概率

给定一个有??维特征的样本??和类别??，类别??的条件概率为

$$
p (y | \boldsymbol {x}; \theta) = \frac {p (x _ {1} , \cdots , x _ {M} | y ; \theta) p (y ; \theta)}{p (x _ {1} , \cdots , x _ {M})} \tag {11.11}
$$

$$
\propto p (x _ {1}, \dots , x _ {M} | y; \theta) p (y; \theta), \tag {11.12}
$$

其中??为概率分布的参数

在朴素贝叶斯分类器中，假设在给定?? 的情况下， $X _ { m }$ 之间是条件独立的，即$X _ { m }$ ⟂ $X _ { k } | Y , \forall m \neq k .$ ．图11.5给出了朴素贝叶斯分类器的图模型表示

![](images/2c8154fb3310d890ed8457c8ccf24eaaec8ad185eab454b04481c921372077d9.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    x1["x₁"] --> y["y"]
    xm["xₘ"] --> y["y"]
    xM["xₘ"] --> y["y"]
    y["y"] --> xm["xₘ"]
    y["y"] --> xM["xₘ"]
```
</details>

图11.5 朴素贝叶斯模型

条件概率分布 $p ( y | \pmb { x } )$ 可以分解为

$$
p (y | \boldsymbol {x}; \theta) \propto p (y | \theta_ {c}) \prod_ {m = 1} ^ {M} p (x _ {m} | y; \theta_ {m}), \tag {11.13}
$$

其中 $\theta _ { c }$ 是??的先验概率分布的参数， $\theta _ { m }$ 是条件概率分布 $p ( x _ { m } | y ; \theta _ { m } )$ 的参数．若$x _ { m }$ 为连续值， $p ( x _ { m } | y ; \theta _ { m } )$ 可以用高斯分布建模；若 $x _ { m }$ 为离散值， $p ( x _ { m } | y ; \theta _ { m } )$ 可以用多项分布建模

虽然朴素贝叶斯分类器的条件独立性假设太强，但是在实际应用中，朴素贝叶斯分类器在很多任务上也能得到很好的结果，并且模型简单，可以有效防止过拟合．

# 11.1.2.3 隐马尔可夫模型

隐马尔可夫模型（Hidden Markov Model，HMM）[Baum et al., 1966] 是用来表示一种含有隐变量的马尔可夫过程

图11.6给出隐马尔可夫模型的图模型表示，其中 $X _ { 1 : T }$ 为可观测变量， $Y _ { 1 : T }$ 为隐变量．所有的隐变量构成一个马尔可夫链，每个可观测标量 $X _ { t }$ 依赖当前时刻的隐变量 $Y _ { t }$

![](images/46b5f2ef2d1a4a4f0a8b8b7c85c3a89d81cc5830bdbef7d00a8df7251a4cf3eb.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    Y1["Y₁"] --> Y2["Y₂"]
    Y2 --> ... 
    ... --> YT-1["Y_{T-1}"]
    YT-1 --> YT["Y_T"]
    Y1 --> X1["X₁"]
    Y2 --> X2["X₂"]
    YT --> XT1["..."]
    YT --> XT2["..."]
    YT --> XT3["..."]
```
</details>

图11.6 隐马尔可夫模型

马 尔 可 夫 链 参 见第D.3.1.1节

隐马尔可夫模型的联合概率可以分解为

$$
p (\boldsymbol {x}, \boldsymbol {y}; \theta) = \prod_ {t = 1} ^ {T} p (y _ {t} | y _ {t - 1}, \theta_ {s}) p (x _ {t} | y _ {t}, \theta_ {t}), \tag {11.14}
$$

为了描述方便，这里用$p ( y _ { 1 } | y _ { 0 } )$ 表示 $p ( y _ { 1 } )$

其中??和??分别为可观测变量和隐变量的取值，条件概率 $p ( x _ { t } | y _ { t } , \theta _ { t } )$ 称为输出概率，条件概率 $p ( y _ { t } | y _ { t - 1 } , \theta _ { s } )$ 称为转移概率， $\theta _ { s }$ 和 $\theta _ { t }$ 分别表示两类条件概率的参数

# 11.1.3 无向图模型

无向图模型，也称为马尔可夫随机场（Markov Random Field，MRF）或马尔可夫网络（Markov Network），是一类用无向图来描述一组具有局部马尔可夫性质的随机向量??的联合概率分布的模型

定义11.2–马尔可夫随机场：对于一个随机向量 $\pmb { X } = [ X _ { 1 } , \cdots , X _ { K } ] ^ { \intercal }$ 和一个有??个节点的无向图??(??, ℰ)（可以存在循环），图??中的节点??表示随机变量 $X _ { k } , 1 \le k \le K$ ．如果(??, ??)满足局部马尔可夫性质，即一个变量 $X _ { k }$ 在给定它的邻居的情况下独立于所有其他变量，

$$
p (x _ {k} | \boldsymbol {x} _ {\backslash k}) = p (x _ {k} | \boldsymbol {x} _ {\mathcal {N} (k)}), \tag {11.15}
$$

其中??(??)为变量 $X _ { k }$ 的邻居集合，K??为除 $X _ { k }$ 外其他变量的集合，那么(??, ??)就构成了一个马尔可夫随机场

无向图的局部马尔可夫性质 无向图中的局部马尔可夫性质可以表示为

$$
X _ {k} \perp \perp X _ {\backslash \mathcal {N} (k), \backslash k} \mid X _ {\mathcal {N} (k)},
$$

其中 $X _ { \backslash \mathcal { N } ( k ) , \backslash k }$ 表示除 $\pmb { X } _ { \mathcal { N } ( k ) }$ 和 $X _ { k }$ 外的其他变量

对于图11.2b中的4个变量，根据马尔可夫性质，可以得到 $X _ { 1 }$ ⟂ $X _ { 4 } | X _ { 2 } , X _ { 3 }$ 和$X _ { 2 }$ ⟂ $X _ { 3 } | X _ { 1 } , X _ { 4 }$

# 11.1.4 无向图模型的概率分解

团 由于无向图模型并不提供一个变量的拓扑顺序，因此无法用链式法则对$p ( { \pmb x } )$ 进行逐一分解．无向图模型的联合概率一般以全连通子图为单位进行分解无向图中的一个全连通子图，称为团（Clique），即团内的所有节点之间都连边在图11.7所示的无向图中共有 7 个团，包括 $\{ X _ { 1 } , X _ { 2 } \} , \{ X _ { 1 } , X _ { 3 } \} , \{ X _ { 2 } , X _ { 3 } \} , \{ X _ { 3 } , X _ { 4 } \}$ ，$\{ X _ { 2 } , X _ { 4 } \} , \{ X _ { 1 } , X _ { 2 } , X _ { 3 } \} , \{ X _ { 2 } , X _ { 3 } , X _ { 4 } \}$

在所有团中，如果一个团不能被其他的团包含，这个团就是一个最大团（Maximal Clique）

![](images/9d5325867b1d5446ab8647b51491143625137efb79e0489c5f3a62fe689e2ad9.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    X1["X₁"] --> X3["X₃"]
    X2["X₂"] --> X3["X₃"]
    X3["X₃"] --> X4["X₄"]
    X2["X₂"] --> X3["X₃"]
    X3["X₃"] --> X4["X₄"]
    style X1 fill:#fff,stroke:#000
    style X2 fill:#fff,stroke:#000
    style X3 fill:#fff,stroke:#000
    style X4 fill:#fff,stroke:#000
    classDef green fill:#fff,stroke:#000,stroke-dasharray: 5 5;
    classDef blue fill:#fff,stroke:#000,stroke-dasharray: 5 5;
```
</details>

图11.7 无向图模型中的团和最大团

因子分解 无向图中的联合概率可以分解为一系列定义在最大团上的非负函数的乘积形式

定理 11.1 – Hammersley-Clifford 定理：如果一个分布 $p ( { \pmb x } ) > 0$ 满足无向图??中的局部马尔可夫性质，当且仅当??(??)可以表示为一系列定义在最大团上的非负函数的乘积形式，即

$$
p (\boldsymbol {x}) = \frac {1}{Z} \prod_ {c \in \mathcal {C}} \phi_ {c} (\boldsymbol {x} _ {c}), \tag {11.16}
$$

其中??为??中的最大团集合， $\phi _ { c } ( \pmb { x } _ { c } ) \geq 0$ 是定义在团??上的势能函数（Po-tential Function），?? 是配分函数（Partition Function），用来将乘积归一化为概率形式：

$$
Z = \sum_ {\boldsymbol {x} \in \mathcal {X}} \prod_ {c \in \mathcal {C}} \phi_ {c} (\boldsymbol {x} _ {c}), \tag {11.17}
$$

其中??为随机向量??的取值空间

Hammersley-Clifford 定理的证明可以参考 [Koller et al., 2009]．无向图模型与有向图模型的一个重要区别是有配分函数??．配分函数的计算复杂度是指数级的，因此在推断和参数学习时都需要重点考虑

吉布斯分布 公式(11.16)中定义的分布形式也称为吉布斯分布（Gibbs Distri-bution）．根据Hammersley-Clifford定理，无向图模型和吉布斯分布是一致的吉布斯分布一定满足马尔可夫随机场的条件独立性质，并且马尔可夫随机场的概率分布一定可以表示成吉布斯分布

由于势能函数必须为正，因此我们一般定义为

$$
\phi_ {c} (\boldsymbol {x} _ {c}) = \exp (- E _ {c} (\boldsymbol {x} _ {c})), \tag {11.18}
$$

其中 $E _ { c } ( \pmb { x } _ { c } )$ 为能量函数（Energy Function）

https://nndl.github.io/

配分函数的计算参见第11.3.1.2节

这里的负号是遵从物理上习惯，即能量越低意味着概率越高

因此，无向图上定义的概率分布可以表示为

$$
\begin{array}{l} P (\boldsymbol {x}) = \frac {1}{Z} \prod_ {c \in \mathcal {C}} \exp (- E _ {c} (\boldsymbol {x} _ {c})) (11.19) \\ = \frac {1}{Z} \exp \Big (\sum_ {c \in \mathcal {C}} - E _ {c} (\boldsymbol {x} _ {c}) \Big). (11.20) \\ \end{array}
$$

这种形式的分布又称为玻尔兹曼分布（Boltzmann Distribution）．任何一个无向图模型都可以用公式(11.20)来表示其联合概率玻尔兹曼分布参见第12.1节

# 11.1.5 常见的无向图模型

很多经典的机器学习模型可以使用无向图模型来描述，比如对数线性模型（也叫最大熵模型）、条件随机场、玻尔兹曼机、受限玻尔兹曼机等

# 11.1.5.1 对数线性模型

势能函数一般定义为

$$
\phi_ {c} (\boldsymbol {x} _ {c} | \theta_ {c}) = \exp \Big (\theta_ {c} ^ {\top} f _ {c} (\boldsymbol {x} _ {c}) \Big), \tag {11.21}
$$

其中函数 $f _ { c } ( \pmb { x } _ { c } )$ 为定义在 $\pmb { x } _ { c }$ 上的特征向量， $\theta _ { c }$ 为权重向量．这样联合概率 $p ( { \pmb x } )$ 的对数形式为

$$
\log p (\boldsymbol {x}; \theta) = \sum_ {c \in \mathcal {C}} \theta_ {c} ^ {\top} f _ {c} (\boldsymbol {x} _ {c}) - \log Z (\theta), \tag {11.22}
$$

其中??代表所有势能函数中的参数 $\theta _ { c }$ ．这种形式的无向图模型也称为对数线性模型（Log-Linear Model）或最大熵模型（Maximum Entropy Model）[Bergeret al., 1996; Della Pietra et al., 1997]．图11.8a所示是一个常用的最大熵模型

如果用对数线性模型来建模条件概率 $p ( y | \pmb { x } )$ ，

$$
p (y | \boldsymbol {x}; \theta) = \frac {1}{Z (\boldsymbol {x} ; \theta)} \exp \Big (\theta^ {\top} f (\boldsymbol {x}, y) \Big), \tag {11.23}
$$

其中 $\begin{array} { r } { Z ( \pmb { x } ; \theta ) = \sum _ { \nu } \exp ( \theta ^ { \top } f _ { y } ( \pmb { x } , y ) ) } \end{array}$

对数线性模型也称为条件最大熵模型或Softmax回归模型

# 11.1.5.2 条件随机场

条件随机场（Conditional Random Field，CRF）[Lafferty et al., 2001] 是一种直接建模条件概率的无向图模型

和条件最大熵模型不同，条件随机场建模的条件概率 $p ( \pmb { y } | \pmb { x } )$ 中，??一般为随机向量，因此需要对 $p ( \pmb { y } | \pmb { x } )$ 进行因子分解．假设条件随机场的最大团集合为??，https://nndl.github.io/

玻 尔 兹 曼 机 参 见第12.1节

受限玻尔兹曼机参见第12.2节

Softmax回归模型参见第3.3节

其条件概率为

$$
p (\boldsymbol {y} | \boldsymbol {x}; \theta) = \frac {1}{Z (\boldsymbol {x} ; \theta)} \exp \Big (\sum_ {c \in \mathcal {C}} \theta_ {c} ^ {\intercal} f _ {c} (\boldsymbol {x}, \boldsymbol {y} _ {c}) \Big), \tag {11.24}
$$

其中 $\begin{array} { r } { Z ( \mathbf { \boldsymbol { x } } ; \theta ) = \sum _ { \gamma } \exp ( \sum _ { c \in \mathcal { C } } f _ { c } ( \mathbf { \boldsymbol { x } } , \mathbf { \boldsymbol { y } } _ { c } ) ^ { \intercal } \theta _ { c } ) } \end{array}$ 为归一化项

一个最常用的条件随机场为图11.8b中所示的链式结构，称为线性链条件随机场（Linear-Chain CRF），其条件概率为

$$
p (\mathbf {y} | \mathbf {x}; \theta) = \frac {1}{Z (\mathbf {x} ; \theta)} \exp \Bigl (\sum_ {t = 1} ^ {T} \theta_ {1} ^ {\top} f _ {1} (\mathbf {x}, y _ {t}) + \sum_ {t = 1} ^ {T - 1} \theta_ {2} ^ {\top} f _ {2} (\mathbf {x}, y _ {t}, y _ {t + 1}) \Bigr), \tag {11.25}
$$

其中 $f _ { 1 } ( x , y _ { t } )$ 为状态特征，一般和位置??相关， $f _ { 2 } ( x , y _ { t } , y _ { t + 1 } )$ 为转移特征，一般可以简化为 $f _ { 2 } ( y _ { t } , y _ { t + 1 } )$ 并使用状态转移矩阵来表示

![](images/49d19968ff5957de20f5c8fde46116c3497bfc41d8489fbdee88436b01971358.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    Y --> X
```
</details>

(a)最大熵模型

![](images/eaadeabc22ea26118cf68306e7d79bd56d4efa8f4d7610297d70c814b9021f07.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    Y1 --> X
    Y2 --> X
    Y2 --> ... --> YT-1
    YT --> X
    YT --> YT
```
</details>

(b)线性链的条件随机场  
图11.8 最大熵模型和线性链条件随机场

# 11.1.6 有向图和无向图之间的转换

有向图和无向图可以相互转换，但将无向图转为有向图通常比较困难．在实际应用中，将有向图转为无向图更加重要，这样可以利用无向图上的精确推断算法，比如联合树算法（Junction Tree Algorithm）

无向图模型可以表示有向图模型无法表示的一些依赖关系，比如循环依赖；但它不能表示有向图模型能够表示的某些关系，比如因果关系

以图11.9a中的有向图为例，其联合概率分布可以分解为

$$
p (\boldsymbol {x}) = p (x _ {1}) p (x _ {2}) p (x _ {3}) p (x _ {4} | x _ {1}, x _ {2}, x _ {3}), \tag {11.26}
$$

其中 $p ( x _ { 4 } | x _ { 1 } , x _ { 2 } , x _ { 3 } )$ 和四个变量都相关．如果要转换为无向图，需要将这四个变量都归属于一个团中．因此，需要将 $x _ { 4 }$ 的三个父节点之间都加上连边，如图11.9b所示．这个过程称为道德化（Moralization）．转换后的无向图称为道德图（Moral Graph）．在道德化的过程中，原来有向图的一些独立性会丢失，比如上面例子中 $X _ { 1 }$ ⟂ $X _ { 2 }$ ⟂ $X _ { 3 } | \mathcal { O }$ 在道德图中不再成立

道德化的名称来源是：有共同儿子的父节点都必须结婚（即有连边）

![](images/3e3bb8dad47af07cb44c37e2176b39de6c71b989e827303366e7b305be13c1cb.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    X1 --> X2
    X2 --> X4
    X3 --> X4
```
</details>

(a) 有向图

![](images/c05ffeb43c246475c48962eaa4d558659428a3e1da2bcd12c2195b1c7e00c38a.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    X1 --> X2
    X1 --> X3
    X2 --> X4
    X2 --> X1
    X3 --> X2
    X3 --> X4
```
</details>

(b) 道德图  
图11.9 具有“共果关系”的有向图的道德化示例

# 11.2 学习

图模型的学习可以分为两部分：一是网络结构学习，即寻找最优的网络结构；二是网络参数估计，即已知网络结构，估计每个条件概率分布的参数

网络结构学习比较困难，一般是由领域专家来构建．本节只讨论在给定网络结构条件下的参数估计问题．图模型的参数估计问题又分为不包含隐变量时的参数估计问题和包含隐变量时的参数估计问题

# 11.2.1 不含隐变量的参数估计

如果图模型中不包含隐变量，即所有变量都是可观测的，那么网络参数一般可以直接通过最大似然来进行估计

有向图模型 在有向图模型中，所有变量??的联合概率分布可以分解为每个随机变量 $x _ { k }$ 的局部条件概率 $p ( x _ { k } | x _ { \pi _ { k } } ; \theta _ { k } )$ 的连乘形式，其中 $\theta _ { k }$ 为第??个变量的局部条件概率的参数

给定?? 个训练样本 $\mathcal { D } = \{ \pmb { x } ^ { ( n ) } \} _ { n = 1 } ^ { N }$ 1，其对数似然函数为

$$
\mathcal {L} (\mathcal {D}; \theta) = \frac {1}{N} \sum_ {n = 1} ^ {N} \log p (\boldsymbol {x} ^ {(n)}; \theta) \tag {11.27}
$$

$$
= \frac {1}{N} \sum_ {n = 1} ^ {N} \sum_ {k = 1} ^ {K} \log p (x _ {k} ^ {(n)} | x _ {\pi_ {k}} ^ {(n)}; \theta_ {k}), \tag {11.28}
$$

其中 $\theta _ { k }$ 为模型中的所有参数

因为所有变量都是可观测的，最大化对数似然ℒ(??; ??)，只需要分别最大化每个变量的条件似然来估计其参数

$$
\theta_ {k} = \arg \max \sum_ {n = 1} ^ {N} \log p (x _ {k} ^ {(n)} | x _ {\pi_ {k}} ^ {(n)}; \theta_ {k}). \tag {11.29}
$$

如果变量??是离散的，简单直接的方式是在训练集上统计每个变量的条件概率表．但是条件概率表需要的参数比较多．假设条件概率 $p ( x _ { k } | x _ { \pi _ { k } } )$ 的父节点数量为??，所有变量为二值变量，其条件概率表需要 $2 ^ { M }$ 个参数．为了减少参数数量，可以使用参数化的模型，比如Sigmoid信念网络．如果变量??是连续的，可以使用高斯函数来表示条件概率分布，称为高斯信念网络．在此基础上，还可以通过让所有的条件概率分布共享使用同一组参数来进一步减少参数的数量

无向图模型 在无向图模型中，所有变量??的联合概率分布可以分解为定义在最大团上的势能函数的连乘形式．以对数线性模型为例，

$$
p (\boldsymbol {x}; \theta) = \frac {1}{Z (\theta)} \exp \biggl (\sum_ {c \in \mathcal {C}} \theta_ {c} ^ {\top} f _ {c} (\boldsymbol {x} _ {c}) \biggr), \tag {11.30}
$$

其中 $\begin{array} { r } { Z ( \theta ) = \sum _ { x } \exp ( \sum _ { c \in \mathcal { C } } \theta _ { c } ^ { \top } f _ { c } ( { \bf x } _ { c } ) ) } \end{array}$

给定?? 个训练样本 $\mathcal { D } = \{ \pmb { x } ^ { ( n ) } \} _ { n = 1 } ^ { N }$ ，其对数似然函数为

$$
\mathcal {L} (\mathcal {D}; \theta) = \frac {1}{N} \sum_ {n = 1} ^ {N} \log p (\boldsymbol {x} ^ {(n)}; \theta) \tag {11.31}
$$

$$
= \frac {1}{N} \sum_ {n = 1} ^ {N} \left(\sum_ {c \in \mathcal {C}} \theta_ {c} ^ {\intercal} f _ {c} (\boldsymbol {x} _ {c} ^ {(n)})\right) - \log Z (\theta), \tag {11.32}
$$

其中 $\theta _ { c }$ 为定义在团??上的势能函数的参数

采用梯度上升方法进行最大似然估计， $\mathcal { L } ( \mathcal { D } ; \theta )$ 关于参数 $\theta _ { c }$ 的偏导数为

$$
\frac {\partial \mathcal {L} (\mathcal {D} ; \theta)}{\partial \theta_ {c}} = \frac {1}{N} \sum_ {n = 1} ^ {N} \left(f _ {c} \left(\boldsymbol {x} _ {c} ^ {(n)}\right)\right) - \frac {\partial \log Z (\theta)}{\partial \theta_ {c}} \tag {11.33}
$$

其中

$$
\frac {\partial \log Z (\theta)}{\partial \theta_ {c}} = \sum_ {\boldsymbol {x}} \frac {1}{Z (\theta)} \cdot \exp \left(\sum_ {c \in \mathcal {C}} \theta_ {c} ^ {\top} f _ {c} (\boldsymbol {x} _ {c})\right) \cdot f _ {c} (\boldsymbol {x} _ {c}) \tag {11.34}
$$

$$
= \sum_ {\boldsymbol {x}} p (\boldsymbol {x}; \theta) f _ {c} (\boldsymbol {x} _ {c}) \triangleq \mathbb {E} _ {\boldsymbol {x} \sim p (\boldsymbol {x}; \theta)} \left[ f _ {c} (\boldsymbol {x} _ {c}) \right]. \tag {11.35}
$$

因此，

$$
\frac {\partial \mathcal {L} (\mathcal {D} ; \theta)}{\partial \theta_ {c}} = \frac {1}{N} \sum_ {n = 1} ^ {N} f _ {c} \left(\boldsymbol {x} _ {c} ^ {(n)}\right) - \mathbb {E} _ {\boldsymbol {x} \sim p (\boldsymbol {x}; \theta)} \left[ f _ {c} \left(\boldsymbol {x} _ {c}\right) \right] \tag {11.36}
$$

$$
= \mathbb {E} _ {\boldsymbol {x} \sim \tilde {p} (\boldsymbol {x})} \left[ f _ {c} \left(\boldsymbol {x} _ {c}\right) \right] - \mathbb {E} _ {\boldsymbol {x} \sim p (\boldsymbol {x}; \theta)} \left[ f _ {c} \left(\boldsymbol {x} _ {c}\right) \right], \tag {11.37}
$$

其中 $\tilde { p } ( \boldsymbol { x } )$ 定义为经验分布（Empirical Distribution）．由于在最优点时梯度为0，因此无向图的最大似然估计的优化目标等价于：对于每个团??上的特征 $f _ { c } ( { \pmb x } _ { c } )$ ，使得其在经验分布 $\tilde { p } ( \boldsymbol { x } )$ 下的期望等于其在模型分布 $p ( \pmb { x } ; \theta )$ 下的期望

对比公式(11.29)和公式(11.37)可以看出，无向图模型的参数估计要比有向图更为复杂．在有向图中，每个局部条件概率的参数是独立的；而在无向图中，所有的参数都是相关的，无法分解

对于一般的无向图模型，公式 (11.37) 中的 $\mathbb { E } _ { { \pmb x } \sim p ( { \pmb x } ; \theta ) } [ f _ { c } ( { \pmb x } _ { c } ) ]$ 往往很难计算，因为涉及在联合概率空间 $p ( \pmb { x } ; \theta )$ 计算期望．当模型变量比较多时，这个计算往往无法实现．因此，无向图的参数估计通常采用近似的方法：1）利用采样来近似计算这个期望；2）采用坐标上升法，即固定其他参数，来优化一个势能函数的参数

# 11.2.2 含隐变量的参数估计

如果图模型中包含隐变量，即有部分变量是不可观测的，就需要用EM算法进行参数估计

# 11.2.2.1 EM 算法

在一个包含隐变量的图模型中，令??定义可观测变量集合，??定义隐变量集合，一个样本??的边际似然函数（Marginal Likelihood）为

$$
p (\boldsymbol {x}; \theta) = \sum_ {\boldsymbol {z}} p (\boldsymbol {x}, \boldsymbol {z}; \theta), \tag {11.38}
$$

其中??为模型参数．边际似然也称为证据（Evidence）

图11.10给出了带隐变量的贝叶斯网络的图模型结构，其中矩形表示其中的变量重复??次．这种表示方法称为盘子表示法（Plate Notation），是图模型中表示重复变量的方法

![](images/07870ad30c2871db355fe061e52b34b41dd59656298892db00fdc4691c18b1a3.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    z[" z "] --> x[" x "]
    x --> θ[ θ ]
    θ --> x
    style z fill:#fff,stroke:#000
    style x fill:#fff,stroke:#000
    style θ fill:#fff,stroke:#000
```
</details>

图11.10 带隐变量的贝叶斯网络

给定??个训练样本 $\mathcal { D } = \{ \pmb { x } ^ { ( n ) } \} _ { n = 1 } ^ { N }$ ，整个训练集的对数边际似然为

$$
\begin{array}{l} \mathcal {L} (\mathcal {D}; \theta) = \frac {1}{N} \sum_ {n = 1} ^ {N} \log p (\boldsymbol {x} ^ {(n)}; \theta) (11.39) \\ = \frac {1}{N} \sum_ {n = 1} ^ {N} \log \sum_ {\mathbf {z}} p (\mathbf {x} ^ {(n)}, \mathbf {z}; \theta). (11.40) \\ \end{array}
$$

通过最大化整个训练集的对数边际似然 $\mathcal { L } ( \mathcal { D } ; \theta )$ ，可以估计出最优的参数$\theta ^ { * }$ ．然而计算边际似然函数时涉及 $p ( x )$ 的推断问题，需要在对数函数的内部进行求和（或积分）．这样，当计算参数??的梯度时，这个求和操作依然存在．除非$p ( \pmb { x } , \pmb { z } ; \theta )$ 的形式非常简单，否则这个求和难以直接计算

为了计算 $\log p ( \pmb { x } ; \theta )$ ，我们引入一个额外的变分函数 $q ( \pmb { z } ) , q ( \pmb { z } )$ 为定义在隐变量??上的分布．样本??的对数边际似然函数为

$$
\log p (\boldsymbol {x}; \theta) = \log \sum_ {\boldsymbol {z}} q (\boldsymbol {z}) \frac {p (\boldsymbol {x} , \boldsymbol {z} ; \theta)}{q (\boldsymbol {z})} \tag {11.41}
$$

$$
\geq \sum_ {z} q (z) \log \frac {p (x , z ; \theta)}{q (z)} \tag {11.42}
$$

$$
\triangleq E L B O (q, \boldsymbol {x}; \theta), \tag {11.43}
$$

其中 $E L B O ( q , x ; \theta )$ 为对数边际似然函数 $\log p ( \pmb { x } ; \theta )$ 的下界，称为证据下界（Evi-dence Lower BOund，ELBO）

公式(11.42)使用了Jensen不等式，即对于凹函数 $g , g \left( \mathbb { E } [ X ] \right) \geq \mathbb { E } \left[ g ( X ) \right]$ 成立．由 Jensen 不等式的性质可知，仅当 $q ( \pmb { z } ) = p ( \pmb { z } | \pmb { x } ; \theta )$ 时，对数边际似然函数$\log p ( \pmb { x } ; \theta )$ 和其下界 $E L B O ( q , x ; \theta )$ 相等，即 $\begin{array} { r } { \log p ( { \pmb x } ; \theta ) = E L B O ( q , { \pmb x } ; \theta ) } \end{array}$

这样，最大化对数边际似然函数 $\log p ( \pmb { x } ; \theta )$ 的过程可以分解为两个步骤：

（1）先找到近似分布??(??)使得 $\begin{array} { r } { \log p ( { \pmb x } ; \theta ) = E L B O ( q , { \pmb x } ; \theta ) } \end{array}$

（2）再寻找参数??最大化 $E L B O ( q , x ; \theta )$ ．这就是期望最大化（Expectation-Maximum，EM）算法

EM算法是含隐变量图模型的常用参数估计方法，通过迭代的方法来最大化边际似然．EM算法具体分为两个步骤：E步和M步．这两步不断重复，直到收敛到某个局部最优解．在第??步更新时，E步和M步分别为：

（1）E 步（Expectation Step）：固定参数 $\theta _ { t }$ ，找到一个分布 $q _ { t + 1 } ( z )$ 使得证据下界 $E L B O ( q , x ; \theta _ { t } )$ 等于 $\log p ( \pmb { x } ; \theta _ { t } )$ ）：

根据Jensen不等式的性质， $q ( \pmb { z } ) = p ( \pmb { z } | \pmb { x } , \theta _ { t } )$ 时， $E L B O ( q , x ; \theta _ { t } )$ 最大．因此在E步中，最理想的分布 $q ( \boldsymbol { z } )$ 是等于后验分布 $p ( \boldsymbol { z } | \boldsymbol { x } ; \boldsymbol { \theta } _ { t } )$ ．而计算后验分布$p ( \boldsymbol { z } | \boldsymbol { x } ; \boldsymbol { \theta } _ { t } )$ 是一个推断（Inference）问题．如果 $z$ 是有限的一维离散变量（比如混合高斯模型）， $p ( \boldsymbol { z } | \boldsymbol { x } ; \boldsymbol { \theta } _ { t } )$ 计算起来还比较容易；否则， $p ( \boldsymbol { z } | \boldsymbol { x } ; \boldsymbol { \theta } _ { t } )$ 一般情况下很难计算，需要通过变分推断的方法来进行近似估计

（2）M 步（Maximization Step）：固定 $q _ { t + 1 } ( z )$ ，找到一组参数使得证据下界最大，即

$$
\theta_ {t + 1} = \underset {\theta} {\arg \max} E L B O (q _ {t + 1}, \boldsymbol {x}; \theta). \tag {11.44}
$$

利用Jensen不等式，参见第D.2.7.1节

参见习题11-4

推断参见第11.3节

变 分 推 断 参 见第11.4节

这一步可以看作全观测变量图模型的参数估计问题，可以使用第11.2.1节中方法进行参数估计

收敛性证明 假设在第??步时的模型参数为 $\theta _ { t }$ ，在E步时找到一个分布 $q _ { t + 1 } ( z )$ 使得 $\log p ( \pmb { x } | \theta _ { t } ) = E L B O ( q , \pmb { x } ; \theta _ { t } )$ ．在M步时固定 $q _ { t + 1 } ( z )$ 找到一组参数 $\theta _ { t + 1 }$ ，使得 $E L B O ( q _ { t + 1 } , \pmb { x } | \theta _ { t + 1 } ) \geq E L B O ( q _ { t + 1 } , \pmb { x } ; \theta _ { t } )$ ．因此有

$$
\log p (\boldsymbol {x}; \theta_ {t + 1}) \geq E L B O (q _ {t + 1}, \boldsymbol {x}; \theta_ {t + 1}) \geq E L B O (q _ {t + 1}, \boldsymbol {x}; \theta_ {t}) = \log p (\boldsymbol {x}; \theta_ {t}), \tag {11.45}
$$

即每经过一次迭代，对数边际似然增加，即 $\log p ( \pmb { x } ; \theta _ { t + 1 } ) \geq \log p ( \pmb { x } ; \theta _ { t } )$ ）：

信息论的视角 对数边际似然 $\log p ( \pmb { x } ; \theta )$ 可以通过下面方式进行分解：

首先因为 $p ( \pmb { x } , z ; \theta ) = p ( \pmb { z } | \pmb { x } ; \theta ) p ( \pmb { x } ; \theta )$ ，有 $\log p ( \pmb { x } , \pmb { z } ; \theta ) = \log p ( \pmb { z } | \pmb { x } ; \theta ) +$ $\log p ( \pmb { x } ; \theta )$ ，进一步有 $\begin{array} { r } { \log p ( { \pmb x } ; \theta ) = \log p ( { \pmb x } , { \pmb z } ; \theta ) - \log p ( { \pmb z } | { \pmb x } ; \theta ) } \end{array}$

这样，对数边际似然 $\log p ( \pmb { x } ; \theta )$ 可以分解为

$$
\log p (\boldsymbol {x}; \theta) = \sum_ {\boldsymbol {z}} q (\boldsymbol {z}) \log p (\boldsymbol {x}; \theta) \tag {11.46} \quad \sum_ {\boldsymbol {z}} q (\boldsymbol {z}) = 1.
$$

$$
= \sum_ {z} q (z) \left(\log p (x, z; \theta) - \log p (z | x; \theta)\right) \tag {11.47}
$$

$$
= \sum_ {z} q (z) \log \frac {p (x , z ; \theta)}{q (z)} - \sum_ {z} q (z) \log \frac {p (z | x ; \theta)}{q (z)} \tag {11.48}
$$

$$
= E L B O (q, \boldsymbol {x}; \theta) + \mathrm{KL} (q (\boldsymbol {z}) \| p (\boldsymbol {z} | \boldsymbol {x}; \theta)), \tag {11.49}
$$

其中 $\mathrm { K L } ( q ( \pmb { z } ) | | p ( \pmb { z } | \pmb { x } ; \theta ) )$ 为分布??(??)和后验分布 $p ( \boldsymbol { z } | \boldsymbol { x } ; \boldsymbol { \theta } )$ 的KL散度

由于 $\mathrm { K L } ( q ( \boldsymbol { z } ) | | p ( \boldsymbol { z } | \boldsymbol { x } ; \boldsymbol { \theta } ) ) \geq 0$ ，因此 $E L B O ( q , x ; \theta )$ 为 $\log p ( \pmb { x } ; \theta )$ 的一个下界．当且仅当 $q ( \pmb { z } ) = p ( \pmb { z } | \pmb { x } ; \theta )$ 时， $\mathrm { K L } ( q ( \mathbf { \boldsymbol { z } } ) | | p ( \mathbf { \boldsymbol { z } } | \mathbf { \boldsymbol { x } } ; \theta ) ) = 0 , \mathrm { ~ } E L B O ( q , \mathbf { \boldsymbol { x } } ; \theta ) =$ $\log p ( \pmb { x } ; \theta )$

参见第E.3.2节

图11.11为EM算法在第??步迭代时的示例

（1）图11.11a表示第??步迭代时的初始状态

此时参数为 $\theta _ { t }$ ，并且通常有 $\mathrm { K L } ( q ( \boldsymbol { z } ) | | p ( \boldsymbol { z } | \boldsymbol { x } ; \boldsymbol { \theta } _ { t } ) ) > 0$

（2）图11.11b表示E步更新

固定参数 $\theta _ { t }$ ，找到分布 $q _ { t + 1 } ( z )$ 使得 $\mathrm { K L } ( q _ { t + 1 } ( \boldsymbol { z } ) | | p ( \boldsymbol { z } | \boldsymbol { x } ; \boldsymbol { \theta } _ { t } ) ) = 0$ ，这时证据下界 $E L B O ( q _ { t + 1 } , \pmb { x } ; \theta _ { t } )$ 和 $\log p ( \pmb { x } ; \theta _ { t } )$ 相等

（3）图11.11c表示M步更新

固定分布 $q _ { t + 1 } ( z )$ ，寻找参数 $\theta _ { t + 1 }$ 使得证据下界 $E L B O ( q _ { t + 1 } , x ; \theta _ { t + 1 } )$ 最大．由于这时通常 $\mathrm { K L } ( q _ { t + 1 } ( \boldsymbol { z } ) | | p ( \boldsymbol { z } | \boldsymbol { x } ; \boldsymbol { \theta } _ { t } ) ) > 0$ ，从而 $\log p ( { \pmb x } ; \theta _ { t + 1 } )$ 也变大

![](images/6d18466a99301ccb3df4f7b7742c205fb0a24bbb3f51f8c4c23decfe3bbc1d48.jpg)  
图11.11 EM算法在第??步迭代时的示例

# 11.2.2.2 高斯混合模型

本节介绍一个EM算法的应用例子：高斯混合模型

高斯混合模型（Gaussian Mixture Model，GMM）是由多个高斯分布组成的模型，其总体密度函数为多个高斯密度函数的加权组合．如果一个连续随机变量或连续随机向量的分布比较复杂，那么我们通常可以用高斯混合模型来估计其分布情况

不失一般性，这里考虑一维的情况．假设样本??是从?? 个高斯分布中的一个分布生成的，但是无法观测到具体由哪个分布生成．我们引入一个隐变量 $z \in$ $\{ 1 , \cdots , K \}$ 来表示样本??来自于哪个高斯分布，??服从多项分布：

$$
p (z = k; \pi) = \pi_ {k}, \quad 1 \leq k \leq K, \tag {11.50}
$$

其中 $\pi = [ \pi _ { 1 } , \pi _ { 2 } , \cdots , \pi _ { K } ]$ 为多项分布的参数，并满足 $\pi _ { k } \geq 0 ,$ ∀??， $\begin{array} { r } { \sum _ { k = 1 } ^ { K } \pi _ { k } = 1 } \end{array}$ $\pi _ { k }$ 表示样本??由第??个高斯分布生成的概率

给定?? = ??，条件分布 $p ( x | z = k )$ 为高斯分布：

$$
p (x \mid z = k; \mu_ {k}, \sigma_ {k}) = \mathcal {N} (x; \mu_ {k}, \sigma_ {k}) \tag {11.51}
$$

$$
= \frac {1}{\sqrt {2 \pi} \sigma_ {k}} \exp \Big (- \frac {(x - \mu_ {k}) ^ {2}}{2 \sigma_ {k} ^ {2}} \Big), \tag {11.52}
$$

其中 $\mu _ { k }$ 和 $\sigma _ { k }$ 分别为第??个高斯分布的均值和方差

从高斯混合模型中生成一个样本??的过程可以分为两步：

（1） 首先根据多项分布 $p ( z ; \pi )$ 随机选取一个高斯分布  
（2） 假设选中第??个高斯分布（即 $z = k )$ ），再从高斯分布 $\mathcal N ( \boldsymbol x ; \mu _ { k } , \boldsymbol \sigma _ { k } )$ 中选取一个样本??

图11.12给出了高斯混合模型的图模型表示

![](images/67c3e3a256ff8d2c18bab122746da5a63d96f096ee36859aef6881477177a45d.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    π --> z_n["z^(n)"]
    z_n --> x_n["x^(n)"]
    x_n --> μ_k["μ_k"]
    x_n --> σ_k["σ_k"]
    μ_k --> K["K"]
    σ_k --> K
    style z_n fill:#f9f,stroke:#333
    style x_n fill:#f9f,stroke:#333
    style μ_k fill:#ccf,stroke:#333
    style σ_k fill:#ccf,stroke:#333
```
</details>

图11.12 高斯混合模型

在高斯混合模型中，随机变量??的概率密度函数为

$$
p (x) = \sum_ {k = 1} ^ {K} \pi_ {k} \mathcal {N} (x; \mu_ {k}, \sigma_ {k}). \tag {11.53}
$$

参数估计 给定?? 个由高斯混合模型生成的训练样本 $x ^ { ( 1 ) } , x ^ { ( 2 ) } , \cdots , x ^ { ( N ) }$ ，希望能学习其中的参数 $\pi _ { k } , \mu _ { k } , \sigma _ { k } , 1 \le k \le K$ ．由于我们无法观测样本 $x ^ { ( n ) }$ 是从哪个高斯分布生成的，因此无法直接用最大似然来进行参数估计

对每个样本 $x ^ { ( n ) }$ ，其对数边际分布为

$$
\log p (x ^ {(n)}) = \log \sum_ {z ^ {(n)}} p (z ^ {(n)}) p (x ^ {(n)} | z ^ {(n)}) \tag {11.54}
$$

$$
= \log \sum_ {k = 1} ^ {K} \pi_ {k} \mathcal {N} (x ^ {(n)}; \mu_ {k}, \sigma_ {k}). \tag {11.55}
$$

根据EM算法，参数估计可以分为两步进行迭代：

（1）E步 先固定参数 $\mu , \sigma$ ，计算后验分布 $p ( z ^ { ( n ) } | x ^ { ( n ) } )$ ，即

$$
\gamma_ {n k} \triangleq p (z ^ {(n)} = k | x ^ {(n)}) \tag {11.56}
$$

$$
= \frac {p (z ^ {(n)}) p (x ^ {(n)} | z ^ {(n)})}{p (x ^ {(n)})} \tag {11.57}
$$

$$
= \frac {\pi_ {k} \mathcal {N} (x ^ {(n)} ; \mu_ {k} , \sigma_ {k})}{\sum_ {k = 1} ^ {K} \pi_ {k} \mathcal {N} (x ^ {(n)} ; \mu_ {k} , \sigma_ {k})}, \tag {11.58}
$$

其中 $\gamma _ { n k }$ 定义了样本 $x ^ { ( n ) }$ 属于第??个高斯分布的后验概率

（2）M步 令 $q ( z = k ) = \gamma _ { n k }$ ，训练集??的证据下界为

$$
E L B O (\gamma , \mathcal {D}; \pi , \mu , \sigma) = \sum_ {n = 1} ^ {N} \sum_ {k = 1} ^ {K} \gamma_ {n k} \log \frac {p (x ^ {(n)} , z ^ {(n)} = k)}{\gamma_ {n k}} \tag {11.59}
$$

$$
= \sum_ {n = 1} ^ {N} \sum_ {k = 1} ^ {K} \gamma_ {n k} \left(\log \mathcal {N} (x ^ {(n)}; \mu_ {k}, \sigma_ {k}) + \log \frac {\pi_ {k}}{\gamma_ {n k}}\right) \tag {11.60}
$$

$$
= \sum_ {n = 1} ^ {N} \sum_ {k = 1} ^ {K} \gamma_ {n k} \left(\frac {- (x - \mu_ {k}) ^ {2}}{2 \sigma_ {k} ^ {2}} - \log \sigma_ {k} + \log \pi_ {k}\right) + C, \tag {11.61}
$$

其中??为和参数无关的常数

将参数估计问题转为优化问题：

$$
\max _ {\pi , \mu , \sigma} E L B O (\gamma , \mathcal {D}; \pi , \mu , \sigma), \tag {11.62}
$$

$$
\text { s.t. } \quad \sum_ {k = 1} ^ {K} \pi_ {k} = 1.
$$

利用拉格朗日乘数法来求解上面的等式约束优化问题，分别求拉格朗日函数 $\begin{array} { r l } {  { E L B O ( \gamma , \mathcal { D } ; \pi , \mu , \sigma ) + \lambda ( \sum _ { k = 1 } ^ { K } \pi _ { k } - 1 ) } } \end{array}$ 关于 $\pi _ { k } , \mu _ { k } , \sigma _ { k }$ 的偏导数，并令其等于0．可得

$$
\pi_ {k} = \frac {N _ {k}}{N}, \tag {11.63}
$$

$$
\mu_ {k} = \frac {1}{N _ {k}} \sum_ {n = 1} ^ {N} \gamma_ {n k} x ^ {(n)}, \tag {11.64}
$$

$$
\sigma_ {k} ^ {2} = \frac {1}{N _ {k}} \sum_ {n = 1} ^ {N} \gamma_ {n k} (x ^ {(n)} - \mu_ {k}) ^ {2}, \tag {11.65}
$$

参见习题11-5

其中

$$
N _ {k} = \sum_ {n = 1} ^ {N} \gamma_ {n k}. \tag {11.66}
$$

高斯混合模型的参数学习过程如算法11.1所示

算法11.1 高斯混合模型的参数学习过程  
输入: 训练样本: $x^{(1)}, x^{(2)}, \cdots, x^{(N)}$ ;
1 随机初始化参数: $\pi_{k}, \mu_{k}, \sigma_{k}, 1 \leq k \leq K;$ 2 repeat
    // E 步
3    固定参数, 根据公式(11.58)计算 $\gamma_{nk}, 1 \leq k \leq K, 1 \leq n \leq N;$ // M 步
4    固定 $\gamma_{nk}$ ，根据公式(11.63)、公式(11.64)和公式(11.65)，计算 $\pi_{k}, \mu_{k}, \sigma_{k}, 1 \leq k \leq K;$ 5 until 对数边际分布 $\sum_{n=1}^{N} \log p(x^{(n)})$ 收敛;
输出: $\pi_{k}, \mu_{k}, \sigma_{k}, 1 \leq k \leq K$

图11.13给出一个高斯混合模型训练过程的简单示例．给定一组数据，我们用两个高斯分布来估计这组数据的分布情况

![](images/4d91b905d5dda7dc468dc0f195a3ed0ae0ef70602e786c3dcc8c60900afbb057.jpg)

<details>
<summary>area</summary>

| x    | Area 1 | Area 2 |
| ---- | ------ | ------ |
| -1   | 0.00   | 0.00   |
| 0    | 0.30   | 0.00   |
| 1    | 0.25   | 0.00   |
| 2    | 0.10   | 0.00   |
| 3    | 0.05   | 0.00   |
| 4    | 0.02   | 0.00   |
| 5    | 0.01   | 0.00   |
| 6    | 0.00   | 0.05   |
| 7    | 0.00   | 0.15   |
| 8    | 0.00   | 0.35   |
| 9    | 0.00   | 0.45   |
| 10   | 0.00   | 0.35   |
| 11   | 0.00   | 0.15   |
| 12   | 0.00   | 0.05   |
</details>

(a) 初始化

![](images/5538ff306fde5139ea9f210bd6008b4879fb8e1d8f4d8f21937905be1cae0ffb.jpg)

<details>
<summary>area</summary>

| x    | Area 1 | Area 2 | Area 3 |
| ---- | ------ | ------ | ------ |
| -1   | 0.00   | 0.00   | 0.00   |
| 0    | 0.00   | 0.00   | 0.00   |
| 1    | 0.05   | 0.05   | 0.05   |
| 2    | 0.10   | 0.10   | 0.10   |
| 3    | 0.15   | 0.15   | 0.15   |
| 4    | 0.20   | 0.20   | 0.20   |
| 5    | 0.15   | 0.15   | 0.15   |
| 6    | 0.10   | 0.10   | 0.10   |
| 7    | 0.05   | 0.05   | 0.05   |
| 8    | 0.00   | 0.00   | 0.00   |
| 9    | 0.00   | 0.00   | 0.00   |
| 10   | 0.00   | 0.00   | 0.00   |
| 11   | 0.00   | 0.00   | 0.00   |
| 12   | 0.00   | 0.00   | 0.00   |
| 13   | 0.00   | 0.00   | 0.00   |
| 14   | 0.00   | 0.00   | 0.00   |
| 15   | 0.00   | 0.00   | 0.00   |
| 16   | 0.00   | 0.00   | 0.00   |
| 17   | 0.00   | 0.00   | 0.00   |
| 18   | 0.00   | 0.00   | 0.00   |
| 19   | 0.00   | 0.00   | 0.00   |
| 20   | 0.05   | 0.15   | 0.15   |
| 21   | 0.15   | 0.35   | 0.35   |
| 22   | 0.35   | 0.65   | 0.65   |
| 23   | 0.65   | 1.15   | 1.15   |
| 24   | 1.15   | 1.75   | 1.75   |
| 25   | 1.75   | 2.45   | 2.45   |
| 26   | 2.45   | 3.25   | 3.25   |
| 27   | 3.25   | 4.15   | 4.15   |
| 28   | 4.15   | 5.15   | 5.15   |
| 29   | 5.15   | 6.25   | 6.25   |
| 30+  | -      | -      | -      |
</details>

(b) 第1次迭代

![](images/6a3fd9a9954739f80b5b298f507b556223c6d86047ba4cc84c935ab02328800f.jpg)

<details>
<summary>area</summary>

| x    | Red Area | Yellow Area |
| ---- | -------- | ----------- |
| -1   | 0.00     | 0.00        |
| 0    | 0.05     | 0.00        |
| 1    | 0.15     | 0.00        |
| 2    | 0.25     | 0.00        |
| 3    | 0.35     | 0.05        |
| 4    | 0.40     | 0.10        |
| 5    | 0.35     | 0.15        |
| 6    | 0.25     | 0.20        |
| 7    | 0.15     | 0.25        |
| 8    | 0.05     | 0.30        |
| 9    | 0.00     | 0.35        |
| 10   | 0.00     | 0.40        |
| 11   | 0.00     | 0.45        |
| 12   | 0.00     | 0.50        |
</details>

(c) 第4次迭代

![](images/4c2e4c214c7f9230693c120ba565851b3c9ba1a3839002d6265945b158dacc48.jpg)

<details>
<summary>area</summary>

| x    | Area 1 | Area 2 |
| ---- | ------ | ------ |
| 3.5  | 0.4    | 0.1    |
| 4.0  | 0.3    | 0.2    |
| 4.5  | 0.2    | 0.3    |
| 5.0  | 0.1    | 0.4    |
| 5.5  | 0.05   | 0.35   |
| 6.0  | 0.02   | 0.3    |
| 6.5  | 0.01   | 0.2    |
| 7.0  | 0.0    | 0.1    |
| 7.5  | 0.0    | 0.05   |
| 8.0  | 0.0    | 0.02   |
| 8.5  | 0.0    | 0.01   |
| 9.0  | 0.0    | 0.0    |
| 9.5  | 0.0    | 0.0    |
| 10.0 | 0.0    | 0.0    |
</details>

(d) 第8次迭代

![](images/cffa0614e31e7997f02455ff6df233da2792586b536c175f85a4cd041eacac21.jpg)

<details>
<summary>area</summary>

| x    | Area  |
| ---- | ----- |
| -1   | 0.00  |
| 0    | 0.00  |
| 1    | 0.00  |
| 2    | 0.00  |
| 3    | 0.00  |
| 4    | 0.00  |
| 5    | 0.00  |
| 6    | 0.00  |
| 7    | 0.00  |
| 8    | 0.00  |
| 9    | 0.00  |
| 10   | 0.00  |
| 11   | 0.00  |
| 12   | 0.00  |
</details>

(e) 第 12 次迭代

![](images/e231333426272d5df83b22eee9868641a91d211ee9187a6202b16edf33bde610.jpg)

<details>
<summary>area</summary>

| x    | Red Area | Yellow Area |
| ---- | -------- | ----------- |
| -1   | 0.00     | 0.00        |
| 0    | 0.00     | 0.00        |
| 1    | 0.05     | 0.00        |
| 2    | 0.15     | 0.00        |
| 3    | 0.30     | 0.05        |
| 4    | 0.45     | 0.15        |
| 5    | 0.35     | 0.25        |
| 6    | 0.20     | 0.35        |
| 7    | 0.10     | 0.45        |
| 8    | 0.05     | 0.35        |
| 9    | 0.02     | 0.25        |
| 10   | 0.01     | 0.15        |
| 11   | 0.00     | 0.05        |
| 12   | 0.00     | 0.00        |
</details>

(f) 第 16 次迭代  
图11.13 高斯混合模型训练过程示例

# 11.3 推断

在图模型中，推断（Inference）是指在观测到部分变量 $\pmb { e } = \{ e _ { 1 } , e _ { 2 } , \cdots , e _ { M } \}$ 时，计算其他变量的某个子集 $\pmb q = \{ q _ { 1 } , q _ { 2 } , \cdots , q _ { N } \}$ 的条件概率 $p ( \pmb q | \pmb e )$

假设一个图模型中，除了变量??、??外，其余变量表示为 $z .$ ．根据贝叶斯公式有

$$
p (\boldsymbol {q} | \boldsymbol {e}) = \frac {p (\boldsymbol {q} , \boldsymbol {e})}{p (\boldsymbol {e})} \tag {11.67}
$$

$$
= \frac {\sum_ {z} p (\boldsymbol {q} , \boldsymbol {e} , z)}{\sum_ {\boldsymbol {q} , z} p (\boldsymbol {q} , \boldsymbol {e} , z)}. \tag {11.68}
$$

因此，图模型的推断问题的关键为求任意一个变量子集的边际概率分布问题

在图模型中，常用的推断算法可以分为精确推断算法和近似推断算法两类

# 11.3.1 精确推断

精确推断（Exact Inference）算法是指可以计算出条件概率 $p ( \pmb q | \pmb e )$ 的精确解的算法

# 11.3.1.1 变量消除法

以图11.2a的有向图为例，假设推断问题为计算后验概率 $p ( x _ { 1 } | x _ { 4 } )$ ，需要计算两个边际概率 $p ( x _ { 1 } , x _ { 4 } )$ 和 $p ( x _ { 4 } )$

不失一般性，这里假设所有变量都为离散变量

根据条件独立性假设，有

$$
p (x _ {1}, x _ {4}) = \sum_ {x _ {2}, x _ {3}} p (x _ {1}) p (x _ {2} | x _ {1}) p (x _ {3} | x _ {1}) p (x _ {4} | x _ {2}, x _ {3}), \tag {11.69}
$$

假设每个变量取??个值，计算上面的边际分布需要 $K ^ { 2 }$ 次加法以及 $K ^ { 2 } \times 3$ 次乘法根据乘法的分配律，

$$
a b + a c = a (b + c), \tag {11.70}
$$

边际概率 $p ( x _ { 1 } , x _ { 4 } )$ 可以写为

$$
p (x _ {1}, x _ {4}) = p (x _ {1}) \sum_ {x _ {3}} p (x _ {3} | x _ {1}) \sum_ {x _ {2}} p (x _ {2} | x _ {1}) p (x _ {4} | x _ {2}, x _ {3}). \tag {11.71}
$$

这样计算量可以减少到 $K ^ { 2 } + K$ 次加法和 $K ^ { 2 } + K + 1$ 次乘法

这种方法是利用动态规划的思想，每次消除一个变量，来减少计算边际分布的计算复杂度，称为变量消除法（Variable Elimination Algorithm）．随着图模型规模的增长，变量消除法的收益越大

变量消除法可以按照不同的顺序来消除变量．比如上面的推断问题也可以按照 $x _ { 3 } , x _ { 2 }$ 的消除顺序进行计算

同理，边际概率 $p ( x _ { 4 } )$ 可以通过以下方式计算：

$$
p (x _ {4}) = \sum_ {x _ {3}} \sum_ {x _ {2}} p (x _ {4} | x _ {2}, x _ {3}) \sum_ {x _ {1}} p (x _ {3} | x _ {1}) p (x _ {2} | x _ {1}) p (x _ {1}). \tag {11.72}
$$

变量消除法的一个缺点是在计算多个边际分布时存在很多重复的计算．比如在上面的图模型中，计算边际概率 $p ( x _ { 4 } )$ 和 $p ( x _ { 3 } )$ 时很多局部的求和计算是一样的．

# 11.3.1.2 信念传播算法

信念传播（Belief Propagation，BP）算法，也称为和积（Sum-Product）算法或消息传递（Message Passing）算法，是将变量消除法中的和积（Sum-Product）操作看作消息（Message），并保存起来，这样可以节省大量的计算资源．

我们先介绍链式结构上的信念传播算法

![](images/01652b80be7fd9cdaa6fd8075eb466ec91aff6fffac4f846ba5ece3f0d0989af.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph LR
    X1["X₁"] -->|μ₁,₂(x₂)| X2["X₂"]
    X2 -->|μ₂,₃(x₃)| ... 
    ... -->|μₜ₋₁,T(xₜ)| XT["XT"]
    X1 -->|μ₂,₁(x₁)| X2
    X2 -->|μ₃,₂(x₂)| ... 
    ... -->|μₜ,T₋₁(xₜ₋₁)| XT
```
</details>

图11.14 无向马尔可夫链的消息传递过程

本节以无向图为例来介绍信念传播算法，但其同样适用于有向图

以图11.14所示的无向马尔可夫链为例，其联合概率 $p ( { \pmb x } )$ 为

$$
p (\boldsymbol {x}) = \frac {1}{Z} \prod_ {c \in \mathcal {C}} \phi_ {c} (\boldsymbol {x} _ {c}) \tag {11.73}
$$

$$
= \frac {1}{Z} \prod_ {t = 1} ^ {T - 1} \phi (x _ {t}, x _ {t + 1}) \tag {11.74}
$$

其中 $\phi ( x _ { t } , x _ { t + 1 } )$ 是定义在团 $( x _ { t } , x _ { t + 1 } )$ 上的势能函数

第??个变量的边际概率 $p ( x _ { t } )$ 为

$$
p (x _ {t}) = \sum_ {x _ {1}} \dots \sum_ {x _ {t - 1}} \sum_ {x _ {t + 1}} \dots \sum_ {x _ {T}} p (\boldsymbol {x}) \tag {11.75}
$$

$$
= \frac {1}{Z} \sum_ {x _ {1}} \dots \sum_ {x _ {t - 1}} \sum_ {x _ {t + 1}} \dots \sum_ {x _ {T}} \prod_ {t = 1} ^ {T - 1} \phi (x _ {t}, x _ {t + 1}). \tag {11.76}
$$

假设每个变量取??个值，不考虑归一化项，通过公式(11.76)计算边际分布需要$K ^ { T - 1 }$ 次加法以及 $K ^ { T - 1 } \times ( T - 1 )$ 次乘法

根据乘法的分配律，边际概率 $p ( x _ { t } )$ 可以通过下面方式进行计算：

$$
\begin{array}{l} p (x _ {t}) = \frac {1}{Z} \left(\sum_ {x _ {1}} \dots \sum_ {x _ {t - 1}} \prod_ {j = 1} ^ {t - 1} \phi (x _ {j}, x _ {j + 1})\right) \cdot \left(\sum_ {x _ {t + 1}} \dots \sum_ {x _ {T}} \prod_ {j = t} ^ {T - 1} \phi (x _ {j}, x _ {j + 1})\right) \\ = \frac {1}{Z} \left(\sum_ {x _ {t - 1}} \phi (x _ {t - 1}, x _ {t}) \dots \left(\sum_ {x _ {2}} \phi (x _ {2}, x _ {3}) \left(\sum_ {x _ {1}} \phi (x _ {1}, x _ {2})\right)\right)\right). \\ \left(\sum_ {x _ {t + 1}} \phi (x _ {t}, x _ {t + 1}) \dots \Big (\sum_ {x _ {T - 1}} \phi (x _ {T - 2}, x _ {T - 1}) \Big (\sum_ {x _ {T}} \phi (x _ {T - 1}, x _ {T}) \Big) \Big)\right) \\ = \frac {1}{Z} \mu_ {t - 1, t} (x _ {t}) \mu_ {t + 1, t} (x _ {t}), \tag {11.77} \\ \end{array}
$$

其中 $\mu _ { t - 1 , t } ( x _ { t } )$ 定义为变量 $X _ { t - 1 }$ 向变量 $X _ { t }$ 传递的消息，定义为

$$
\mu_ {t - 1, t} (x _ {t}) \triangleq \sum_ {x _ {t - 1}} \phi (x _ {t - 1}, x _ {t}) \mu_ {t - 2, t - 1} (x _ {t - 1}). \tag {11.78}
$$

$\mu _ { t + 1 , t } ( x _ { t } )$ 是变量 $X _ { t + 1 }$ 向变量 $X _ { t }$ 传递的消息，定义为

$$
\mu_ {t + 1, t} (x _ {t}) \triangleq \sum_ {x _ {t + 1}} \phi (x _ {t}, x _ {t + 1}) \mu_ {t + 2, t + 1} (x _ {t + 1}). \tag {11.79}
$$

$\mu _ { t - 1 , t } ( x _ { t } )$ 和 $\mu _ { t + 1 , t } ( x _ { t } )$ 都可以递归计算．因此，边际概率 $p ( x _ { t } )$ 的计算复杂度减少为 $O ( T K ^ { 2 } )$ ．如果要计算整个序列上所有变量的边际概率，不需要将消息传递的过程重复??次，因为其中每两个相邻节点上的消息是相同的

链式结构图模型的消息传递过程为：

（1） 依次计算前向传递的消息 $\mu _ { t - 1 , t } ( x _ { t } ) , t = 1 , \cdots , T - 1$   
（2） 依次计算反向传递的消息 $\mu _ { t + 1 , t } ( x _ { t } ) , t = T - 1 , \cdots , 1$   
（3） 在任意节点??上计算配分函数??，

$$
Z = \sum_ {x _ {t}} \mu_ {t - 1, t} (x _ {t}) \mu_ {t + 1, t} (x _ {t}). \tag {11.80}
$$

这样，我们可以通过公式(11.77)计算所有变量的边际概率

树结构上的信念传播算法 信念传播算法也可以推广到具有树结构的图模型上．如果一个有向图满足任意两个变量只有一条路径（忽略方向），且只有一个没有父节点的节点，那么这个有向图为树结构，其中唯一没有父节点的节点称为根节点．如果一个无向图满足任意两个变量只有一条路径，那么这个无向图也为树结构．在树结构的无向图中，任意一个节点都可以作为根节点

树结构图模型的消息传递过程为：

（1） 从叶子节点到根节点依次计算并传递消息  
（2） 从根节点开始到叶子节点，依次计算并传递消息  
（3） 在每个节点上计算所有接收消息的乘积（如果是无向图还需要归一化），就得到了所有变量的边际概率

如果图结构中存在环路，可以使用联合树算法（Junction Tree Algorithm）[Lauritzen et al., 1988] 来将图结构转换为无环图

# 11.3.2 近似推断

在实际应用中，精确推断一般用于结构比较简单的推断问题．当图模型的结构比较复杂时，精确推断的计算开销会比较大．此外，如果图模型中的变量是连续的，并且其积分函数没有闭式（Closed-Form）解，那么也无法使用精确推断因此，在很多情况下也常常采用近似的方法来进行推断

近似推断（Approximate Inference）主要有以下三种方法：

（1） 环路信念传播：当图模型中存在环路，使用信念传播算法时，消息会在环路中一直传递，可能收敛或不收敛．环路信念传播（Loopy Belief Propagation，LBP）是在具有环路的图上依然使用信念传播算法，即使得到不精确解，在某些任务上也可以近似精确解  
（2） 变分推断：图模型中有些变量的局部条件分布可能非常复杂，或其积分无法计算．变分推断（Variational Inference）是引入一个变分分布（通常是比较简单的分布）来近似这些条件概率，然后通过迭代的方法进行计算．首先是更新变分分布的参数来最小化变分分布和真实分布的差异（比如交叉熵或KL距离），然后再根据变分分布来进行推断

（3） 采样法（Sampling Method）：通过模拟的方式来采集符合某个分布??(??)的一些样本，并用这些样本来估计和分布 $p ( { \pmb x } )$ 有关的运算，比如期望等

我们在下面两节分别介绍变分推断和基于采样法的近似推断

# 11.4 变分推断

变分法（Calculus Of Variations）是17世纪末发展起来的一个数学分支，主要研究变分问题，即泛函的极值问题

函数（Function）是表示自变量到因变量的映射关系： $y = f ( x )$ ．而泛函（Functional）是函数的函数，即它的输入是函数，输出是实数： $F ( f ( x ) )$ ，一般称$F ( f ( x ) )$ 为 $f ( x )$ 的泛函，但是泛函要求 $f ( x )$ 满足一定的边界条件，并且具有连续的二阶导数．一个泛函的例子是熵，其输入是一个概率分布 $p ( x )$ ，输出是该分布的不确定性

传统的微积分通常可以用来寻找函数 $f ( x )$ 的极值点，而变分法则是用来寻找一个函数 $f ( x )$ 使得泛函 $F ( f ( x ) )$ 取得极大或极小值．变方法的应用十分广泛，比如最大熵问题，即寻找一个概率分布，使得该概率分布的熵最大

假设在一个贝叶斯模型中，??为一组观测变量，??为一组隐变量（参数也看作随机变量，包含在??中），我们的推断问题为计算条件概率密度 $p ( \pmb { z } | \pmb { x } )$ ．根据贝叶斯公式，条件概率密度 $p ( \pmb { z } | \pmb { x } )$ 可以写为

$$
p (\boldsymbol {z} | \boldsymbol {x}) = \frac {p (\boldsymbol {x} , \boldsymbol {z})}{p (\boldsymbol {x})} = \frac {p (\boldsymbol {x} , \boldsymbol {z})}{\int p (\boldsymbol {x} , \boldsymbol {z}) \mathrm{d} \boldsymbol {z}}. \tag {11.81}
$$

对于很多模型来说，计算上面公式中的积分是不可行的，要么积分没有闭式解，要么是指数级的计算复杂度

变分推断（Variational Inference）是变分法在推断问题中的应用，是寻找一个简单分布 $q ^ { * } ( z )$ 来近似条件概率密度 $p ( \pmb { z } | \pmb { x } )$ ，也称为 变分贝叶斯（Varia-tional Bayesian）．这样，推断问题转换为一个泛函优化问题：

$$
q ^ {*} (\boldsymbol {z}) = \underset {q (\boldsymbol {z}) \in \mathcal {Q}} {\arg \min} \mathrm{KL} (q (\boldsymbol {z}) \| p (\boldsymbol {z} | \boldsymbol {x})), \tag {11.82}
$$

其中??为候选的概率分布族．由于 $p ( \pmb { z } | \pmb { x } )$ 难以直接计算，因此我们不能直接优化上面公式的KL散度

我们在EM算法中已经证明

$$
\log p (\boldsymbol {x}) = E L B O (q, \boldsymbol {x}) + \mathrm{KL} (q (\boldsymbol {z}) \| p (\boldsymbol {z} | \boldsymbol {x})). \tag {11.83}
$$

概率分布可以看作一个函数．熵的定义参见第E.1节

不失一般性，这里假设??和??为连续随机向量

闭式解是指问题的解为闭式（closed-form）函数，从解的函数中就可以算出任何对应值闭式解也称为解析解，和数值解相对应

参见习题11-7

EM 算 法 参 见第11.2.2.1节

参见公式(11.49)

在EM算法的E步中，我们假设 $p ( \pmb { z } | \pmb { x } )$ 是可计算的，并让 $q ( { \boldsymbol { z } } ) = p ( { \boldsymbol { z } } | { \boldsymbol { x } } )$ ，这样$E L B O ( q , x )$ 等于 $\log p ( { \pmb x } )$ ．而变分推断可以看作EM算法的扩展版，主要处理不能精确推断 $p ( \pmb { z } | \pmb { x } )$ 的情况

结合公式(11.82)和公式(11.83)，有

$$
\begin{array}{l} q ^ {*} (\boldsymbol {z}) = \underset {q (\boldsymbol {z}) \in \mathcal {Q}} {\arg \min} \left(\log p (\boldsymbol {x}) - E L B O (q, \boldsymbol {x})\right) (11.84) \\ = \underset {q (z) \in \mathcal {Q}} {\arg \max} E L B O (q, \boldsymbol {x}). (11.85) \\ \end{array}
$$

这样，公式(11.82)中优化问题转换为寻找一个简单分布 $q ^ { * } ( z )$ 来最大化证据下界$E L B O ( q , x )$

在变分推断中，候选分布族??的复杂性决定了优化问题的复杂性．一个通常的选择是平均场（mean-field）分布族，即??可以分拆为多组相互独立的变量．概率密度 $q ( \pmb { z } )$ 可以分解为

$$
q (\boldsymbol {z}) = \prod_ {m = 1} ^ {M} q _ {m} (\boldsymbol {z} _ {m}), \tag {11.86}
$$

其中 $z _ { m }$ 是隐变量的子集，可以是单变量，也可以是一组多元变量

证据下界 $E L B O ( q , x )$ 可以写为

$$
\begin{array}{l} E L B O (q, \boldsymbol {x}) = \int q (\boldsymbol {z}) \log \frac {p (\boldsymbol {x} , \boldsymbol {z})}{q (\boldsymbol {z})} \mathrm{d} \boldsymbol {z} (11.87) \\ = \int q (\boldsymbol {z}) \left(\log p (\boldsymbol {x}, \boldsymbol {z}) - \log q (\boldsymbol {z})\right) \mathrm{d} \boldsymbol {z} (11.88) \\ = \int \prod_ {m = 1} ^ {M} q _ {m} (\mathbf {z} _ {m}) \left(\log p (\mathbf {x}, \mathbf {z}) - \sum_ {m = 1} ^ {M} \log q _ {m} (\mathbf {z} _ {m})\right) d \mathbf {z}. (11.89) \\ \end{array}
$$

假设只关心隐变量的子集 $z _ { j }$ 的近似分布 $q _ { j } ( z _ { j } )$ ，上式可以写为

$$
\begin{array}{l} E L B O (q, \boldsymbol {x}) = \int q _ {j} \left(\int \prod_ {m \neq j} q _ {m} \log p (\boldsymbol {x}, \boldsymbol {z}) \mathrm{d} \boldsymbol {z} _ {m}\right) \mathrm{d} \boldsymbol {z} _ {j} \\ - \int q _ {j} \log q _ {j} \mathrm{d} \mathbf {z} _ {j} + \text { const } (11.90) \\ = \int q _ {j} \boxed {\log \tilde {p} (\boldsymbol {x}, \boldsymbol {z} _ {j})} \mathrm{d} \boldsymbol {z} _ {j} - \int q _ {j} \log q _ {j} \mathrm{d} \boldsymbol {z} _ {j} + \text { const }, (11.91) \\ \end{array}
$$

其中 $\tilde { p } ( { \boldsymbol { x } } , z _ { j } )$ 可以看作一个关于 $z _ { j }$ 的未归一化的分布，并有

$$
\log \tilde {p} (\boldsymbol {x}, \boldsymbol {z} _ {j}) = \int \prod_ {m \neq j} q _ {m} \log p (\boldsymbol {x}, \boldsymbol {z}) \mathrm{d} \boldsymbol {z} _ {m} \tag {11.92}
$$

这 里 $q _ { m } ( z _ { m } )$ 用 简 写$q _ { m }$ 表示

const为一个常数

$$
= \mathbb {E} _ {q (\boldsymbol {z} \backslash j)} [ \log p (\boldsymbol {x}, \boldsymbol {z}) ] + \text { const }, \tag {11.93}
$$

其中 $z _ { \ l \mathrm { V } }$ 为除变量子集 $z _ { j }$ 外的其他隐变量

假设我们固定 $z _ { \ l \mathrm { V } }$ 不变，先优化 $q _ { j } ( z _ { j } )$ 使得 $E L B O ( q , x )$ 最大．根据公式(11.91)，$E L B O ( q , x )$ 可以看作 $- \operatorname { K L } ( q _ { j } ( \pmb { z } _ { j } ) | | \tilde { p } ( \pmb { x } , \pmb { z } _ { j } ) )$ 加上一个常数．因此，最小化KL散度$\mathrm { K L } ( q _ { j } ( \boldsymbol { z } _ { j } ) | | \tilde { p } ( \boldsymbol { x } , \boldsymbol { z } _ { j } ) )$ 就等价于最大化公式(11.91)，即最优的 $q _ { j } ^ { * } ( z _ { j } )$ 正比于对数联合概率密度 $\log p ( { \pmb x } , { \pmb z } )$ 的期望的指数：

$$
q _ {j} ^ {*} (\boldsymbol {z} _ {j}) = \tilde {p} (\boldsymbol {x}, \boldsymbol {z} _ {j}) \propto \exp \left(\mathbb {E} _ {q (\boldsymbol {z} _ {\backslash j})} [ \log p (\boldsymbol {x}, \boldsymbol {z}) ]\right), \tag {11.94}
$$

其中期望是根据 $q ( \boldsymbol { z } _ { \backslash j } )$ 计算的．我们可以通过选择合适的 $q _ { m } ( z _ { m } ) , 1 \leq m \leq M$ ，使得这个期望具有闭式解

由于 $q _ { j } ^ { * } ( z _ { j } )$ 的计算要依赖于其他隐变量，我们可以用坐标上升法（Coordi-nate Ascent Algorithm）来迭代地优化每个 $q _ { j } ^ { * } ( z _ { j } ) , j = 1 , \cdots , M$ ．通过不断循环迭代地应用公式(11.94)，证据下界 $E L B O ( q , x )$ 会收敛到一个局部最优解

变分推断通常和参数学习一起使用，比如应用在EM算法的E步中来近似条件分布 $p ( \pmb { z } | \pmb { x } )$ ．在变分推断中，我们通常选择一些比较简单的分布 $q ( \boldsymbol { z } )$ 来近似推断 $p ( \pmb { z } | \pmb { x } )$ ．当 $p ( \pmb { z } | \pmb { x } )$ 比较复杂时，近似效果不佳．这时可以利用神经网络的强大拟合能力来近似 $p ( \pmb { z } | \pmb { x } )$ ，这种思想被应用在变分自编码器中

# 11.5 基于采样法的近似推断

在很多实际机器学习任务中，推断某个概率分布并不是最终目的，而是基于这个概率分布进一步计算并作出决策．通常这些计算和期望相关

不失一般性，假设要推断的概率分布为 $p ( x )$ ，并基于 $p ( x )$ 来计算函数 $f ( x )$ 的期望：

$$
\mathbb {E} _ {p} [ f (x) ] = \int_ {x} f (x) p (x) \mathrm{d} x. \tag {11.95}
$$

当 $p ( x )$ 比较复杂或难以精确推断时，我们可以通过采样法来近似计算期望$\mathbb { E } _ { p } [ f ( x ) ]$ 的解

# 11.5.1 采样法

采样法（Sampling Method）也称为蒙特卡罗方法（Monte Carlo Method）或统计模拟方法，是20世纪40年代中期提出的一种通过随机采样来近似估计一

变分自编码器参见第13.2节

采样也叫抽样

在本节中，我们假设??为连续变量．如果??是离散变量，可以将积分替换为求和

蒙特卡罗方法诞生于20世纪40年代美国的“曼哈顿计划”，其名字来源于摩纳哥的一个以赌博业闻名的城市蒙特卡罗，象征概率

些计算问题数值解的方法．随机采样指从给定概率密度函数 $p ( x )$ 中抽取出符合其概率分布的样本

由于电子计算机的出现和快速发展，这种方法作为一种独立方法被提出来，使得当时很多难以计算的问题都可以通过随机模拟的方法来进行估计

为了计算公式(11.95)中的 $\mathbb { E } _ { p } [ f ( x ) ]$ ，我们可以通过数值解的方法来近似计算．首先从 $p ( x )$ 中独立抽取??个样本 $x ^ { ( 1 ) } , x ^ { ( 2 ) } , \cdots , x ^ { ( N ) } , f ( x )$ 的期望可以用这??个样本的均值 $\bar { f } _ { N }$ 来近似，即

$$
\bar {f} _ {N} = \frac {1}{N} \left(f (x ^ {(1)}) + \dots + f (x ^ {(N)})\right). \tag {11.96}
$$

根据大数定律，当??趋向于无穷大时，样本均值收敛于期望值

$$
\bar {f} _ {N} \stackrel {P} {\rightarrow} \mathbb {E} _ {p} [ f (x) ] \qquad \text {当} N \to \infty . \tag {11.97}
$$

这就是采样法的理论依据

采样法的一个最简单的应用例子是计算圆周率π．我们知道半径为??的圆的面积为 $\pi r ^ { 2 }$ ，而直径为2??的正方形的面积为 $4 r ^ { 2 }$ ．当我们用正方形去嵌套一个相切的圆时，它们的面积之比是 ${ } _ { { \frac { 1 } { 4 } } \pi . } ^ { \frac { 1 } { 2 } }$ ．当不知道π时，我们无法计算圆的面积．因此，需要通过模拟的方法来进行近似估计．首先在正方形内部按均值采样的方式随机生成若干点，计算它们与圆心点的距离，从而判断它们是否落在圆的内部．然后去统计落在圆内部的点占到所有点的比例．当有足够的点时，这个比例应该接近于 ${ \frac { 1 } { 4 } } \pi$ ，从而近似估算出π的值

随机采样 采样法的难点是如何进行随机采样，即如何让计算机生成满足概率密度函数 $p ( x )$ 的样本．我们知道，计算机可以比较容易地随机生成一个在[0, 1]区间上均布分布的样本 $\xi .$ ．如果要随机生成服从某个非均匀分布的样本，就需要一些间接的采样方法

如果一个分布的概率密度函数为 $p ( x )$ ，其累积分布函数 $\operatorname { c d f } ( x )$ 为连续的严格增函数，且存在逆函数 $\operatorname { c d f } ^ { - 1 } ( y ) , y \in [ 0 , 1 ]$ ，那么我们可以利用累积分布函数的逆函数来生成服从该随机分布的样本．假设 $\xi$ 是[0, 1]区间上均匀分布的随机变量，则 $\operatorname { c d f } ^ { - 1 } ( \xi )$ 服从概率密度函数为 $p ( x )$ 的分布

但当 $p ( x )$ 非常复杂，其累积分布函数的逆函数难以计算，或者不知道 $p ( x )$ 号的精确值，只知道未归一化的分布 ${ \hat { p } } ( x )$ 时，就难以直接对 $p ( x )$ 进行采样，往往需要使用一些间接的采样策略，比如拒绝采样、重要性采样、马尔可夫链蒙特卡罗采样等．这些方法一般是先根据一个比较容易采样的分布进行采样，然后通过一些策略来间接得到符合 $p ( x )$ 分布的样本

数值解就是用数值方法求出解，给出一系列对应的自变量和解．数值 解 和解 析 解或闭 式解相对应

参见习题11-10

$\begin{array} { r } { p ( x ) = \frac { 1 } { Z } \hat { p } ( x ) } \end{array}$ ，其中??为配分函数

# 11.5.2 拒绝采样

拒绝采样（Rejection Sampling）是一种间接采样方法，也称为接受-拒绝采样（Acceptance-Rejection Sampling）

假设原始分布??(??)难以直接采样，我们可以引入一个容易采样的分布??(??)，一般称为提议分布（Proposal Distribution），然后以某个标准来拒绝一部分的样本使得最终采集的样本服从分布??(??)．在拒绝采样中，已知未归一化的分布̂??(??)，我们需要构建一个提议分布??(??)和一个常数??，使得????(??)可以覆盖函数̂??(??)，即 $k q ( x ) \geq \hat { p } ( x ) , \forall x$ ，如图11.15所示

![](images/bcb0446b287991e4da59001c0aa3513b1da75a0c5eb8180d7c374b53ebb8dfb8.jpg)

<details>
<summary>line</summary>

| x    | p(x)  | kq(x) |
| ---- | ----- | ----- |
| -6   | 0.000 | 0.000 |
| -4   | 0.000 | 0.150 |
| -2   | 0.150 | 0.350 |
| 0    | 0.050 | 0.400 |
| 2    | 0.280 | 0.350 |
| 4    | 0.150 | 0.150 |
| 6    | 0.000 | 0.000 |
</details>

图 11.15 拒绝采样

对于每次抽取的样本 ，̂?? 计算接受概率（Acceptance Probability）：

$$
\alpha (\hat {x}) = \frac {\hat {p} (\hat {x})}{k q (\hat {x})}, \tag {11.98}
$$

并以概率??( ̂??)来接受样本 ．̂?? 拒绝采样的采样过程如算法11.2所示

算法11.2 拒绝采样的采样过程  
输入: 提议分布 $q(x)$ , 常数 k, 样本集合 $V = \varnothing$ ;

1 repeat
2    根据 $q(x)$ 随机生成一个样本 $\hat{x}$ ;
3    计算接受概率 $\alpha(\hat{x})$ ;
4    从 $(0,1)$ 的均匀分布中随机生成一个值 z;
5    if $z \leq \alpha(\hat{x})$ then // 以 $\alpha(\hat{x})$ 的概率接受 $\hat{x}$ 6 $V = V \cup \{\hat{x}\}$ ;
7    end
8 until 获得 N 个样本 ( $|V| = N$ );
输出: 样本集合 V

为简单起见，我们把概率密度函数为??(??)的分布简称为分布??(??)，下同．

提议分布在很多文献中也翻译为参考分布

判断一个拒绝采样方法的好坏就是看其采样效率，即总体的接受率．如果函数 $k q ( x )$ 远大于原始分布函数 ${ \hat { p } } ( x )$ ，拒绝率会比较高，采样效率会非常不理想．但要找到一个和 ${ \hat { p } } ( x )$ 比较接近的提议分布往往比较困难．特别是在高维空间中，其采样率会非常低，导致很难应用到实际问题中

# 11.5.3 重要性采样

如果采样的目的是计算分布 $p ( x )$ 下函数 $f ( x )$ 的期望，那么实际上抽取的样本不需要严格服从分布 $p ( x )$ ．也可以通过另一个分布，即提议分布 $q ( x )$ ，直接采样并估计 $\mathbb { E } _ { p } [ f ( x ) ]$

函数??(??)在分布??(??)下的期望可以写为

$$
\begin{array}{l} \mathbb {E} _ {p} [ f (x) ] = \int_ {x} f (x) p (x) \mathrm{d} x (11.99) \\ = \int_ {x} f (x) \frac {p (x)}{q (x)} q (x) \mathrm{d} x (11.100) \\ = \int_ {x} f (x) w (x) q (x) \mathrm{d} x (11.101) \\ = \mathbb {E} _ {q} [ f (x) w (x) ]. (11.102) \\ \end{array}
$$

其中??(??)称为重要性权重

重要性采样（Importance Sampling）是通过引入重要性权重，将分布 $p ( x )$ 下 $f ( x )$ 的期望变为在分布 $q ( x )$ 下 $f ( x ) w ( x )$ 的期望，从而可以近似为

$$
\hat {f} _ {N} = \frac {1}{N} \left(f (x ^ {(1)}) w (x ^ {(1)}) + \dots + f (x ^ {(N)}) w (x ^ {(N)})\right), \tag {11.103}
$$

其中 ${ x ^ { ( 1 ) } , \cdots , x ^ { ( N ) } }$ 为独立从 $q ( x )$ 中随机抽取的点

重要性采样也可以在只知道未归一化的分布 ${ \hat { p } } ( x )$ 的情况下计算函数 ??(??)的期望

$$
\begin{array}{l} \mathbb {E} _ {p} [ f (x) ] = \int_ {x} f (x) \frac {\hat {p} (x)}{Z} \mathrm{d} x (11.104) \\ = \frac {\int_ {x} \hat {p} (x) f (x) d x}{\int_ {x} \hat {p} (x) \mathrm{d} x} (11.105) \\ \approx \frac {\sum_ {n = 1} ^ {N} f (x ^ {(n)}) \hat {w} (x ^ {(n)})}{\sum_ {n = 1} ^ {N} \hat {w} (x ^ {(n)})}, (11.106) \\ \end{array}
$$

其中 $\begin{array} { r } { \hat { w } ( x ) = \frac { \hat { p } ( x ) } { q ( x ) } , x ^ { ( 1 ) } , \cdots , x ^ { ( N ) } } \end{array}$ 为独立从??(??)中随机抽取的点

$\begin{array} { r } { p ( x ) = \frac { \hat { p } ( x ) } { Z } } \end{array}$ ) ，?? 为配分函数

# 11.5.4 马尔可夫链蒙特卡罗方法

在高维空间中，拒绝采样和重要性采样的效率随空间维数的增加而指数降低．马尔可夫链蒙特卡罗（Markov Chain Monte Carlo，MCMC）方法是一种更好的采样方法，可以很容易地对高维变量进行采样

MCMC方法也有很多不同的具体采样方法，但其核心思想是将采样过程看作一个马尔可夫链

$$
\boldsymbol {x} _ {1}, \boldsymbol {x} _ {2}, \dots , \boldsymbol {x} _ {t - 1}, \boldsymbol {x} _ {t}, \boldsymbol {x} _ {t + 1}, \dots
$$

第?? + 1次采样依赖于第??次抽取的样本 $\mathbf { \boldsymbol { x } } _ { t }$ 以及状态转移分布（即提议分布）$q ( \pmb { x } | \pmb { x } _ { t } )$ ．如果这个马尔可夫链的平稳分布为 $p ( { \pmb x } )$ ，那么在状态平稳时抽取的样本就服从 $p ( { \pmb x } )$ 的分布

MCMC方法的关键是如何构造出平稳分布为 $p ( { \pmb x } )$ 的马尔可夫链，并且该马尔可夫链的状态转移分布 $q ( \pmb { x } | \pmb { x } ^ { \prime } )$ 一般为比较容易采样的分布．当??为离散变量时， $q ( { \pmb x } | { \pmb x } ^ { \prime } )$ 可以是一个状态转移矩阵；当??为连续变量时， $q ( \boldsymbol { x } | \boldsymbol { x } ^ { \prime } )$ 可以是参数密度函数，比如各向同性的高斯分布 $q ( \pmb { x } | \pmb { x } ^ { \prime } ) = \mathcal { N } ( \pmb { x } | \pmb { x } ^ { \prime } , \pmb { \sigma } ^ { 2 } I )$ ，其中 $\sigma ^ { 2 }$ 为超参数

使用MCMC方法进行采样时需要注意两点．1）马尔可夫链需要经过一段时间的随机游走才能达到平稳状态，这段时间称为预烧期（Burn-in Period）．预烧期内的采样点并不服从分布 $p ( { \pmb x } )$ ，需要丢弃．2）基于马尔可夫链抽取的相邻样本是高度相关的．而在机器学习中，我们一般需要抽取的样本是独立同分布的．为了使得抽取的样本之间独立，我们可以每间隔??次随机游走，抽取一个样本．如果??足够大，可以认为抽取的样本是独立的

# 11.5.4.1 Metropolis-Hastings 算法

Metropolis-Hastings算法，简称MH算法，是一种应用广泛的MCMC方法假设马尔可夫链的状态转移分布（即提议分布） $q ( \pmb { x } | \pmb { x } ^ { \prime } )$ 为一个比较容易采样的分布，其平稳分布往往不是 $p ( { \pmb x } )$ ．为此，MH算法引入拒绝采样的思想来修正提议分布，使得最终采样的分布为 $p ( { \pmb x } )$

在MH算法中，假设第??次采样的样本为 $\mathbf { \boldsymbol { x } } _ { t }$ ，首先根据提议分布 $q ( \pmb { x } | \pmb { x } _ { t } )$ 抽取一个样本??̂，并以概率 $A ( \hat { \pmb x } , { \pmb x } _ { t } )$ 来接受??̂作为第?? + 1次的采样样本 $\boldsymbol { x } _ { t + 1 }$ ，

$$
A (\hat {\boldsymbol {x}}, \boldsymbol {x} _ {t}) = \min \left(1, \frac {p (\hat {\boldsymbol {x}}) q (\boldsymbol {x} _ {t} | \hat {\boldsymbol {x}})}{p (\boldsymbol {x} _ {t}) q (\hat {\boldsymbol {x}} | \boldsymbol {x} _ {t})}\right). \tag {11.107}
$$

MH算法的采样过程如算法11.3所示

在MH算法中，因为每次 $q ( \pmb { x } | \pmb { x } _ { t } )$ 随机生成一个样本??̂，并以概率 $A ( \hat { \pmb x } , { \pmb x } _ { t } )$ 的方式接受，所以修正的马尔可夫链状态转移概率为

$$
q ^ {\prime} (\hat {\boldsymbol {x}} | \boldsymbol {x} _ {t}) = q (\hat {\boldsymbol {x}} | \boldsymbol {x} _ {t}) A (\hat {\boldsymbol {x}}, \boldsymbol {x} _ {t}), \tag {11.108}
$$

马 尔 可 夫 链 参 见第 节

算法 11.3 Metropolis-Hastings 算法的采样过程  
输入: 提议分布 $q(x|x')$ , 采样间隔 M, 样本集合 V = ∅;
随机初始化 $x_{0}, t = 0;$ repeat
    // 预热过程
    根据 $q(x|x_{t})$ 随机生成一个样本 $\hat{x}$ ;
    计算接受概率 $A(\hat{x}, x_{t})$ ;
    从 (0,1) 的均匀分布中随机生成一个值 z;
    if $z \leq A(\hat{x}, x_{t})$ then // 以 $A(\hat{x}, x_{t})$ 的概率接受 $\hat{x}$ $x_{t+1} = \hat{x};$ else // 拒绝接受 $\hat{x}$ $x_{t+1} = x_{t};$ end
    t++;
    if 未到平稳状态 then continue;
    if t mod M = 0 then // 采样过程, 每隔 M 次采一个样本 $V = V \cup \{x_{t}\};$ end
until 获得 N 个样本 ( $|V| = N$ );
输出: 样本集合 V

该修正的马尔可夫链可以达到平稳状态，且平稳分布为??(??)

证明. 根据马尔可夫链的细致平稳条件，有

细致平稳条件参见定 理D.1

$$
p (\boldsymbol {x} _ {t}) q ^ {\prime} (\hat {\boldsymbol {x}} | \boldsymbol {x} _ {t}) = p (\boldsymbol {x} _ {t}) q (\hat {\boldsymbol {x}} | \boldsymbol {x} _ {t}) A (\hat {\boldsymbol {x}}, \boldsymbol {x} _ {t}) \tag {11.109}
$$

$$
= p (\boldsymbol {x} _ {t}) q (\hat {\boldsymbol {x}} | \boldsymbol {x} _ {t}) \min \left(1, \frac {p (\hat {\boldsymbol {x}}) q (\boldsymbol {x} _ {t} | \hat {\boldsymbol {x}})}{p (\boldsymbol {x} _ {t}) q (\hat {\boldsymbol {x}} | \boldsymbol {x} _ {t})}\right) \tag {11.110}
$$

$$
= \min \left(p (\boldsymbol {x} _ {t}) q (\hat {\boldsymbol {x}} | \boldsymbol {x} _ {t}), p (\hat {\boldsymbol {x}}) q (\boldsymbol {x} _ {t} | \hat {\boldsymbol {x}})\right) \tag {11.111}
$$

$$
= p (\hat {\boldsymbol {x}}) q \left(\boldsymbol {x} _ {t} \mid \hat {\boldsymbol {x}}\right) \min \left(\frac {p \left(\boldsymbol {x} _ {t}\right) q \left(\hat {\boldsymbol {x}} \mid \boldsymbol {x} _ {t}\right)}{p \left(\hat {\boldsymbol {x}}\right) q \left(\boldsymbol {x} _ {t} \mid \hat {\boldsymbol {x}}\right)}, 1\right) \tag {11.112}
$$

$$
= p (\hat {\boldsymbol {x}}) q \left(\boldsymbol {x} _ {t} \mid \hat {\boldsymbol {x}}\right) A \left(\boldsymbol {x} _ {t}, \hat {\boldsymbol {x}}\right) \tag {11.113}
$$

$$
= p (\hat {\boldsymbol {x}}) q ^ {\prime} \left(\boldsymbol {x} _ {t} \mid \hat {\boldsymbol {x}}\right). \tag {11.114}
$$

因此， $p ( { \pmb x } )$ 是状态转移概率为 $q ^ { \prime } ( \hat { \pmb x } | \pmb x _ { t } )$ 的马尔可夫链的平稳分布

![](images/4c5fe3f0bf1d8f9bf00fd45f58dd0c33817fd728cfcf853427b61edb84d0cecb.jpg)

# 11.5.4.2 Metropolis 算法

如果MH算法中的提议分布是对称的，即 $q ( \hat { \pmb x } | \pmb x _ { t } ) = q ( \pmb x _ { t } | \hat { \pmb x } )$ ，第?? + 1次采样的接受率可以简化为

$$
A (\hat {\boldsymbol {x}}, \boldsymbol {x} _ {t}) = \min \left(1, \frac {p (\hat {\boldsymbol {x}})}{p (\boldsymbol {x} _ {t})}\right). \tag {11.115}
$$

这种MCMC方法称为Metropolis算法

# 11.5.4.3 吉布斯采样

吉布斯采样（Gibbs Sampling）是一种有效地对高维空间中的分布进行采样的MCMC方法，可以看作Metropolis-Hastings算法的特例．吉布斯采样使用全条件概率（Full Conditional Probability）作为提议分布来依次对每个维度进行采样，并设置接受率为?? = 1

对于一个??维的随机向量 $\pmb { X } = [ X _ { 1 } , X _ { 2 } , \cdots , X _ { M } ] ^ { \intercal }$ ，其第??个变量 $X _ { m }$ 的全条件概率为

$$
p (x _ {m} | \boldsymbol {x} _ {\backslash m}) \triangleq P (X _ {m} = x _ {m} | X _ {\backslash m} = \boldsymbol {x} _ {\backslash m}) \tag {11.116}
$$

$$
= p (x _ {m} | x _ {1}, x _ {2}, \dots , x _ {m - 1}, x _ {m + 1}, \dots , x _ {M}), \tag {11.117}
$$

其中 $\pmb { x } _ { \backslash m } = [ x _ { 1 } , x _ { 2 } , \cdots , x _ { m - 1 } , x _ { m + 1 } , \cdots , x _ { M } ] ^ { \intercal }$ 表示除 $X _ { m }$ 外其他变量的取值

吉布斯采样可以按照任意的顺序根据全条件分布依次对每个变量进行采样．假设从一个随机的初始化状态 $\pmb { x } ^ { ( 0 ) } = [ x _ { 1 } ^ { ( 0 ) } , x _ { 2 } ^ { ( 0 ) } , \cdots , x _ { M } ^ { ( 0 ) } ] ^ { \intercal }$ ??(0)]T 开始，按照下标顺序依次对??个变量进行采样

$$
x _ {1} ^ {(1)} \sim p (x _ {1} | x _ {2} ^ {(0)}, x _ {3} ^ {(0)}, \dots , x _ {M} ^ {(0)}), \tag {11.118}
$$

$$
x _ {2} ^ {(1)} \sim p (x _ {2} | x _ {1} ^ {(1)}, x _ {3} ^ {(0)} \dots , x _ {M} ^ {(0)}), \tag {11.119}
$$

$$
x _ {M} ^ {(1)} \sim p (x _ {M} | x _ {1} ^ {(1)}, x _ {2} ^ {(1)} \dots , x _ {M - 1} ^ {(1)}), \tag {11.120}
$$

$$
x _ {1} ^ {(t)} \sim p (x _ {1} | x _ {2} ^ {(t - 1)}, x _ {3} ^ {(t - 1)}, \dots , x _ {M} ^ {(t - 1)}), \tag {11.121}
$$

$$
x _ {2} ^ {(t)} \sim p (x _ {2} | x _ {1} ^ {(t)}, x _ {3} ^ {(t - 1)} \dots , x _ {M} ^ {(t - 1)}), \tag {11.122}
$$

$$
x _ {M} ^ {(t)} \sim p (x _ {M} | x _ {1} ^ {(t)}, x _ {2} ^ {(t)} \dots , x _ {M - 1} ^ {(t)}), \tag {11.123}
$$

其中 $x _ { m } ^ { ( t ) }$ 是第??次迭代时变量 $X _ { m }$ 的采样

吉布斯采样的每单步采样也构成一个马尔可夫链．假设每个单步（采样维度为第??维）的状态转移概率 $q ( \pmb { x } | \pmb { x } ^ { \prime } )$ 为

$$
q (\boldsymbol {x} | \boldsymbol {x} ^ {\prime}) = \left\{ \begin{array}{c l} \frac {p (\boldsymbol {x})}{p \left(\boldsymbol {x} _ {\backslash m} ^ {\prime}\right)} & \text { if } \quad \boldsymbol {x} _ {\backslash m} = \boldsymbol {x} _ {\backslash m} ^ {\prime} \\ 0 & \text { otherwise }, \end{array} \right. \tag {11.124}
$$

其中边际分布 $\begin{array} { r } { p ( \pmb { x } _ { \backslash m } ^ { \prime } ) = \sum _ { \pmb { x } _ { m } ^ { \prime } } p ( \pmb { x } ^ { \prime } ) } \end{array}$ ，等式 ${ \pmb x } _ { \backslash m } = { \pmb x } _ { \backslash m } ^ { \prime }$ 表示 $x _ { k } = x _ { k } ^ { \prime } , \forall k \neq m$ ，因此有 $p ( \pmb { x } _ { \backslash m } ^ { \prime } ) = p ( \pmb { x } _ { \backslash m } )$ ，并可以得到

$$
p (\boldsymbol {x} ^ {\prime}) q (\boldsymbol {x} | \boldsymbol {x} ^ {\prime}) = p (\boldsymbol {x} ^ {\prime}) \frac {p (\boldsymbol {x})}{p (\boldsymbol {x} _ {\backslash i} ^ {\prime})} = p (\boldsymbol {x}) \frac {p (\boldsymbol {x} ^ {\prime})}{p (\boldsymbol {x} _ {\backslash i})} = p (\boldsymbol {x}) q (\boldsymbol {x} ^ {\prime} | \boldsymbol {x}). \tag {11.125}
$$

根据细致平稳条件，公式(11.124)中定义的状态转移概率 $q ( \boldsymbol { x } | \boldsymbol { x } ^ { \prime } )$ 的马尔可夫链的平稳分布为 $p ( { \pmb x } )$ ．随着迭代次数?? 的增加，样本 $\pmb { x } ^ { ( t ) } = [ x _ { 1 } ^ { ( t ) } , x _ { 2 } ^ { ( t ) } \cdots , x _ { M } ^ { ( t ) } ] ^ { \intercal }$ 将收敛于概率分布 $p ( { \pmb x } )$

# 11.6 总结和深入阅读

概率图模型提供了一个用图形来描述概率模型的框架，这种可视化方法使我们可以更加容易地理解复杂模型的内在性质．目前，概率图模型已经是一个非常庞大的研究领域，涉及众多的模型和算法．很多机器学习模型也都可以用概率图模型来描述．图11.16给出了概率图模型所涵盖的内容

![](images/aa665b910321c82ec4391f0bcd894d398d0650384f059d3661540fc4566341c0.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    A["概率图模型"] --> B["模型表示"]
    A --> C["学习"]
    A --> D["推断"]
    B --> E["有向图模型"]
    B --> F["无向图模型"]
    C --> G["参数学习"]
    C --> H["结构学习"]
    D --> I["精确推断"]
    D --> J["近似推断"]
    E --> K["朴素贝叶斯模型"]
    E --> L["隐马尔可夫模型"]
    E --> M["深度信念网络"]
    F --> N["对数线性模型"]
    F --> O["条件随机场"]
    F --> P["玻尔兹曼机"]
    G --> Q["最大似然估计"]
    G --> R["最大后验"]
    G --> S["EM算法"]
    H --> T["结构搜索"]
    H --> U["贝叶斯优化"]
    H --> V["结构EM算法"]
    I --> W["变量消除算法"]
    I --> X["信念传播算法"]
    I --> Y["联合树算法"]
    J --> Z["环路信念传播"]
    J --> AA["变分推断"]
    J --> AB["采样法"]
```
</details>

图11.16 概率图模型所涵盖内容的简单概括

在本章中，我们只介绍了部分内容．要更全面深入地了解概率图模型，可以阅读《Probabilistic Graphical Models: Principles and Techniques》[Kolleret al., 2009]、《Probabilistic Reasoning in Intelligent Systems: Networks of Plau-sible Inference》[Pearl, 2014] 或《Pattern Recognition and Machine Learning》[Bishop, 2007] 中的相关章节

概率图模型中最基本的假设是条件独立性．图形化表示直观地描述了随机变量之间的条件独立性，有利于将复杂的概率模型分解为简单模型的组合，并更好地理解概率模型的表示、推断、学习等方法

20世纪90年代末，概率图模型的研究逐步成熟．到21世纪，图模型在机器学习、计算机视觉、自然语言处理等领域开始不断发展壮大．其中比较有代表性的模型有：条件随机场 [Lafferty et al., 2001]、潜在狄利克雷分配（Latent DirichletAllocation）[Blei et al., 2003] 等．此外，图模型的结构学习也一直是非常重要但极具挑战性的研究方向

图模型与神经网络的关系 图模型和神经网络有着类似的网络结构，但两者也有很大的不同．图模型的节点是随机变量，其图结构的主要功能是描述变量之间的依赖关系，一般是稀疏连接．使用图模型的好处是可以有效地进行统计推断而神经网络中的节点是神经元，是一个计算节点．图模型中的每个变量一般有着明确的解释，变量之间依赖关系一般是人工来定义．而神经网络中的单个神经元则没有直观的解释．如果将神经网络中每个神经元看作一个二值随机变量，那神经网络就变成一个Sigmoid信念网络

神经网络是判别模型，直接用来分类．而图模型不但可以是判别模型，也可以是生成模型．生成模型不但可以用来生成样本，也可以通过贝叶斯公式用来做分类．图模型的参数学习的目标函数为似然函数或条件似然函数，若包含隐变量则通常通过EM算法来求解．而神经网络参数学习的目标函数为交叉熵或平方误差等损失函数

目前，神经网络和概率图模型的结合越来越紧密．一方面我们可以利用神经网络强大的表示能力和拟合能力来建模图模型中的推断问题（比如变分自编码器，第13.2节），生成问题（比如生成对抗网络，第13.3节），或势能函数（比如 LSTM+CRF 模型 [Lample et al., 2016; Ma et al., 2016]）；另一方面可以利用图模型的算法来解决复杂结构神经网络中的学习和推断问题，比如图神经网络（Graph Neural Network，GNN）[Gilmer et al., 2017; Li et al., 2015; Scarselliet al., 2009] 和结构化注意力 [Kim et al., 2017]

# 习题

习题11-1 根据贝叶斯网络的定义，证明图11.3中的四种因果关系

习题 11-2 证明公式 (11.9)

参见公式(11.9)

习题11-3 根据公式(11.37)，推导线性链条件随机场（参见公式(11.25)）的参数更新公式

习题11-4 证明仅当 $q ( \pmb { z } ) = p ( \pmb { z } | \pmb { x } ; \theta )$ 时，对数边际似然函数 $\log p ( \pmb { x } ; \theta )$ 和其下界$E L B O ( q , x ; \theta )$ 相等

习题11-5 在高斯混合分布的参数估计中，证明M步中的参数更新公式，即公式(11.63)、公式 (11.64) 和公式 (11.65)

习题11-6 考虑一个伯努利混合分布，即

$$
p (x; \mu , \pi) = \sum_ {k = 1} ^ {K} \pi_ {k} p (x; \mu_ {k}), \tag {11.126}
$$

其中 $p ( x ; \mu _ { k } ) = \mu _ { k } ^ { x } ( 1 - \mu _ { k } ) ^ { ( 1 - x ) }$ 为伯努利分布

给定一组训练集合 ${ \cal D } = \{ x ^ { ( 1 ) } , x ^ { ( 2 ) } , \cdots , x ^ { ( N ) } \}$ ，若用EM算法来进行参数估计，推导其每步的参数更新公式

习题11-7 在变分推断的目标公式(11.82)中，试分析为什么使用的KL散度是KL $\big ( q ( \pmb { z } ) \big | \big | p ( \pmb { z } | \pmb { x } ) \big )$ 而不是 $\begin{array} { r } { \mathrm { K L } \left( p ( \pmb { z } | \pmb { x } ) | | \pmb { q } ( \pmb { z } ) \right) } \end{array}$

习题11-8 在图11.2a的有向图中，分析按不同的消除顺序计算边际概率 $p ( x _ { 3 } )$ 时的计算复杂度

习题11-9 在树结构的图模型上应用信念传播算法时，推导其消息计算公式

习题11-10 证明若分布??(??)存在累积分布函数的逆函数 $\operatorname { c d f } ^ { - 1 } ( y ) , y \in [ 0 , 1 ]$ ，且随机变量 $\xi$ 为[0, 1]区间上的均匀分布，则 $\operatorname { c d f } ^ { - 1 } ( \xi )$ 服从分布 ??(??)

伯努利混合分布参见第D.2.1.1节

参见第11.5.1节

# 参考文献

Baum L E, Petrie T, 1966. Statistical inference for probabilistic functions of finite state markov chains [J]. The annals of mathematical statistics, 37(6):1554-1563.   
Berger A L, Pietra V J D, Pietra S A D, 1996. A maximum entropy approach to natural language processing[J]. Computational linguistics, 22(1):39-71.   
Bishop C M, 2007. Pattern recognition and machine learning[M]. 5th edition. Springer.   
Blei D M, Ng A Y, Jordan M I, 2003. Latent dirichlet allocation[J]. Journal of machine Learning research, 3(Jan):993-1022.   
Della Pietra S, Della Pietra V, Lafferty J, 1997. Inducing features of random fields[J]. IEEE transactions on pattern analysis and machine intelligence, 19(4):380-393.   
Gilmer J, Schoenholz S S, Riley P F, et al., 2017. Neural message passing for quantum chemistry[J]. arXiv preprint arXiv:1704.01212.   
Kim Y, Denton C, Hoang L, et al., 2017. Structured attention networks[C]//Proceedings of 5th International Conference on Learning Representations.   
Koller D, Friedman N, 2009. Probabilistic graphical models: principles and techniques[M]. MIT press.   
Lafferty J D, McCallum A, Pereira F C N, 2001. Conditional random fields: Probabilistic models for segmenting and labeling sequence data[C]//Proceedings of the Eighteenth International Conference on Machine Learning.   
https://nndl.github.io/

Lample G, Ballesteros M, Subramanian S, et al., 2016. Neural architectures for named entity recognition[J]. arXiv preprint arXiv:1603.01360.   
Lauritzen S L, Spiegelhalter D J, 1988. Local computations with probabilities on graphical structures and their application to expert systems[J]. Journal of the Royal Statistical Society. Series B (Methodological):157-224.   
Li Y, Tarlow D, Brockschmidt M, et al., 2015. Gated graph sequence neural networks[J]. arXiv preprint arXiv:1511.05493.   
Ma X, Hovy E, 2016. End-to-end sequence labeling via bi-directional lstm-cnns-crf[J]. arXiv preprint arXiv:1603.01354.   
Neal R M, 1992. Connectionist learning of belief networks[J]. Artificial intelligence, 56(1):71-113.   
Pearl J, 2014. Probabilistic reasoning in intelligent systems: networks of plausible inference[M]. Elsevier.   
Scarselli F, Gori M, Tsoi A C, et al., 2009. The graph neural network model[J]. IEEE Transactions on Neural Networks, 20(1):61-80.