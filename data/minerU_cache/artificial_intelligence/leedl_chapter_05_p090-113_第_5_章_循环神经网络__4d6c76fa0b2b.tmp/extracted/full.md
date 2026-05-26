# 第 5 章 循环神经网络

循环神经网络（Recurrent Neural Network）是深度学习领域中一种非常经典的网络结构，在现实生活中有着广泛的应用。以槽填充（slot filling）为例，如图 5.1 所示，假设订票系统听到用户说：“我想在 6 月 1 日抵达上海。”，系统有一些槽（slot）：目的地和到达时间，系统要自动知道这边的每一个单词是属于哪一个槽，比如“上海”属于目的地槽，“6 月 1 号”属于到达时间槽。

![](images/582aae2e66d9695de8b1e512cc6a8011ce443c5d541813090570525696bdb4d9.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    A["用户"] --> B["订票系统"]
    B --> C["槽"]
    C --> D{目的地: 上海
到达时间: 6月1日}
    D --> E["我想在6月1日抵达上海。"]
```
</details>

图 5.1 槽填充示例

这个问题可以使用一个前馈神经网络（feedforward neural network）来解，如图 5.2 所示，输入是一个单词，把“上海”变成一个向量，“丢”到这个神经网络里面。要把一个单词丢到一个神经网络里面去，就必须把它变成一个向量。

![](images/3302f77c2b1eb92b7c0a56d3e179c9848aec2551ac5dd8c0c5edc6ec6d427cb9.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    subgraph Input Layer
        A["x1"] --> B["Hidden Layer"]
        C["x2"] --> B
        D["Input Layer"] --> E["Output Layer"]
    end
    subgraph Hidden Layer
        F["y1"] --> G["Output Layer"]
        H["y2"] --> G
        I["Input Layer"] --> J["Output Layer"]
    end
    style Input Layer fill:#f9f,stroke:#333
    style Hidden Layer fill:#bbf,stroke:#333
    style Output Layer fill:#dfd,stroke:#333
```
</details>

图 5.2 使用神经网络解决槽填充问题

以下是把单词用向量来表示的方法。

# 5.1 独热编码

假设词典中有 5 个单词：apple，bag，cat，dog，elephant，如式 (5.1)。向量的大小是词典大小。每一个维度对应词典的一个单词。对应单词的维度为 1，其他为 0。

$$
\mathrm{apple} = [ 1, 0, 0, 0, 0 ]
$$

$$
\mathrm{bag} = [ 0, 1, 0, 0, 0 ]
$$

$$
\mathrm{cat} = [ 0, 0, 1, 0, 0 ] \tag {5.1}
$$

$$
\mathrm{dog} = [ 0, 0, 0, 1, 0 ]
$$

$$
\text { elephant } = [ 0, 0, 0, 0, 1 ]
$$

如果只是用独热编码来描述一个单词，会有一些问题：因为很多单词可能都没有见过，所以需要在独热编码里面多加维度，用一个维度代表 other，如图 5.3(a) 所示。如果不是在词表中，有的单词就归类到 other 里面去（Pig，Cow 归类到 other 里面去）。我们可以用每一个单词的字母来表示它的向量，比如单词是 apple，apple 里面有出现 app、ple、ppl，在这个向量里面对应到 app、ple、ppl 的维度就是 1，其他都为 0，如图 5.3(b) 所示。

![](images/74601be27bd6e59fdd157f35abc362b1a346ad3bce2cc9b3f7318350d2fe716a.jpg)

<details>
<summary>text_image</summary>

apple 0
bag 0
cat 0
dog 0
elephant 0
...
"other" 1
w = "pig" w = "cow"
</details>

(a) 用 other 表示非词表中的单词

![](images/b9c8182dd0cbeb6f0fe7f578e7c2a38a45d7f30134ff7895bbadc51b2794b744.jpg)

<details>
<summary>text_image</summary>

a-a-a
0
a-a-b
0
...
a-p-p
1
...
p-l-e
1
...
p-p-l
1
...
26 × 26 × 26
w = "apple"
</details>

(b) 词哈希  
图 5.3 另一种编码方法

假设把单词表示为向量，把这个向量丢到前馈神经网络里面去，在该任务里面，输出是一个概率分布，该概率分布代表着输入单词属于每一个槽的概率，比如“上海”属于目的地的概率和“上海”属于出发地的概率，如图 5.4 所示。但是前馈网络会有问题，如图 5.5 所示，假设用户 1 说：“在 6 月 1 号抵达上海”。用户 2 说：“在 6 月 1 号离开上海”，这时候“上海”就变成了出发地。但是对于神经网络，输入一样的东西，输出就应该是一样的东西。在例子中，输入“上海”，输出要么让目的地概率最高，要么让出发地概率最高。不能一会让出发地的概率最高，一会让目的地概率最高。在这种情况下，如果神经网络有记忆力的，它记得它看过“抵达”，在看到“上海”之前；或者它记得它已经看过“离开”，在看到“上海”之前。通过记忆力，它可以根据上下文产生不同的输出。如果让神经网络是有记忆力，其就可以解决输入不同的单词，输出不同的问题。

![](images/3d9499d48a251807b1483e9e32b5153e60f9cfde77333241e545cb52092f5ab2.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    A["目的地 y1"] --> B["绿色节点"]
    C["出发地 y2"] --> D["绿色节点"]
    B --> E["x1"]
    D --> F["x2"]
    style A fill:#f9f,stroke:#333
    style C fill:#f9f,stroke:#333
    style B fill:#ccf,stroke:#333
    style D fill:#ccf,stroke:#333
    style E fill:#fff,stroke:#333
    style F fill:#fff,stroke:#333
```
</details>

图 5.4 使用前馈神经网络预测概率分布  
![](images/7e1eb0d7cb7e5b587894f68880d159d230f8569373482b219f3f6fbbe26a6c3a.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    A["用户1 在 6月 1日 抵达 上海"] --> B["other 时间 时间 other 目的地"]
    C["用户2 在 6月 1日 离开 上海"] --> D["other 时间 时间 other 出发地"]
```
</details>

图 5.5 前馈神经网络的问题

# 5.2 什么是 RNN？

在 RNN 里面，每一次隐藏层的神经元产生输出的时候，该输出会被存到记忆元（memorycell），图 5.6(a) 中的蓝色方块表示记忆元。下一次有输入时，这些神经元不仅会考虑输入 $x _ { 1 } , x _ { 2 }$ ，还会考虑存到记忆元里的值。除 $\textsf { T } x _ { 1 } , x _ { 2 }$ ，存在记忆元里的值 $a _ { 1 } , a _ { 2 }$ 也会影响神经网络的输出。

记忆元可简称为单元（cell），记忆元的值也可称为隐状态（hidden state）。

举个例子，假设图 5.6(b) 中的神经网络所有的权重都是 1，所有的神经元没有任何的偏置（bias）。为了便于计算，假设所有的激活函数都是线性的，输入是序列 $[ 1 , 1 ] ^ { \mathrm { T } } , [ 1 , 1 ] ^ { \mathrm { T } } , [ 2 , 2 ] ^ { \mathrm { T } } , \cdots ,$ ，所有的权重都是 1。首先设置记忆元的初始值都为 0，接着输入第一个 $[ 1 , 1 ] ^ { \mathrm { T } }$ ，对于左边的神经元（第一个隐藏层），其除了接到输入的 $[ 1 , 1 ] ^ { \mathrm { T } }$ ，还接到了记忆元（0 跟 0），输出就是 2。同理，右边神经元的输出为 2，第二层隐藏层输出为 4。

接下来循环神经网络会将绿色神经元的输出存在记忆元里去，所以记忆元里面的值被更新为 2。如图 5.6(c) 所示，接下来再输入 [1, 1]T，接下来绿色的神经元输入为 [1, 1]T、[2, 2]T，输出为 $[ 6 , 6 ] ^ { \mathrm { T } }$ ，第二层的神经元输出为 $[ 1 2 , 1 2 ] ^ { \mathrm { T } }$ 。所以因为循环神经网络有记忆元，就算输入相同，输出也可能不一样。

如图 5.6(d) 所示， $[ 6 , 6 ] ^ { \mathrm { T } }$ 存到记忆元里去，接下来输入是 $[ 2 , 2 ] ^ { \mathrm { T } }$ ，输出为 $[ 1 6 , 1 6 ] ^ { \mathrm { T } }$ ；第二层隐藏层为 $[ 3 2 , 3 2 ] ^ { \mathrm { T } }$ 。在做循环神经网络时，它会考虑序列的顺序，输入序列调换顺序之后输出不同。

因为当前时刻的隐状态使用与上一时刻隐状态相同的定义，所以隐状态的计算是循环的（recurrent），基于循环计算的隐状态神经网络被称为循环神经网络。

![](images/fb577b30aac7ceac5f5c86cf9feb8bbc312f7d274886c5cd91ebacaec3ccb248.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    subgraph Input Layer
        a1["a₁"] -->|存储| h1["∫"]
        a2["a₂"] --> h1
        h1 --> y1["y₁"]
        h1 --> y2["y₂"]
    end
    subgraph Hidden Layer
        h1a["x₁"] --> h2["∫"]
        h2 --> x1["x₁"]
        x2["x₂"]
    end
    subgraph Output Layer
        y1 --> h1
        y2 --> h2
    end
    h1 --> h1a
    h1 --> h2
    h2 --> x1
    x1 --> y1
    x2 --> y2
```
</details>

(a) 循环神经网络示例

![](images/77696ce367e1c34b1c58f10df30349e9d542c6aa4f26966fe55c63ea37bf83e4.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    A["0"] --> B["存储"]
    C["0"] --> B
    D["2"] --> E["输入层"]
    F["2"] --> E
    G["1"] --> H["输出层"]
    I["1"] --> H
    J["y1"] --> K["4"]
    L["y2"] --> M["4"]
    style A fill:#f9f,stroke:#333
    style C fill:#f9f,stroke:#333
    style D fill:#ccf,stroke:#333
    style F fill:#ccf,stroke:#333
    style G fill:#ccf,stroke:#333
    style I fill:#ccf,stroke:#333
    style J fill:#fff,stroke:#333
    style L fill:#fff,stroke:#333
    style M fill:#fff,stroke:#333
    style N fill:#fff,stroke:#333
```
</details>

(b) 循环神经网络运算示例：第 1 步

![](images/3d75442dcfb4f88bbebfb9c44a1b4a22d5e234645cdd30cc0e151768b7408219.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    A["2"] --> B["6"]
    C["2"] --> B["6"]
    D["1"] --> E["6"]
    F["1"] --> E["6"]
    B --> G["y1 12"]
    E --> H["y2 12"]
    style A fill:#f9f,stroke:#333
    style C fill:#f9f,stroke:#333
    style D fill:#f9f,stroke:#333
    style F fill:#f9f,stroke:#333
    style B fill:#ccf,stroke:#333
    style E fill:#ccf,stroke:#333
    style G fill:#cff,stroke:#333
    style H fill:#cff,stroke:#333
    style I fill:#ffc,stroke:#333
    style J fill:#ffc,stroke:#333
```
</details>

(c) 循环神经网络运算示例：第 2 步

![](images/dce49aa46af0e7349be26109b1242e749718af9997fca89207abe65af2f5db4a.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    A["6"] --> B["存储"]
    C["6"] --> B
    D["16"] --> E["16"]
    F["16"] --> E
    G["2"] --> H["2"]
    I["2"] --> H
    J["y1"] --> K["32"]
    L["y2"] --> M["32"]
    style A fill:#f9f,stroke:#333
    style C fill:#f9f,stroke:#333
    style D fill:#ccf,stroke:#333
    style E fill:#ccf,stroke:#333
    style F fill:#ccf,stroke:#333
    style G fill:#ccf,stroke:#333
    style H fill:#ccf,stroke:#333
    style I fill:#ccf,stroke:#333
    style J fill:#ccf,stroke:#333
    style K fill:#ccf,stroke:#333
    style L fill:#ccf,stroke:#333
    style M fill:#ccf,stroke:#333
    style N fill:#ccf,stroke:#333
```
</details>

(d) 循环神经网络运算示例：第 3 步   
图 5.6 循环神经网络运算示例

# 5.3 RNN 架构

使用循环神经网络处理槽填充这件事，如图 5.7 所示。用户说：“我想在 6 月 1 日抵达上海”，“抵达”就变成了一个向量“丢”到神经网络里面去，神经网络的隐藏层的输出为向量 $\mathbf { a } _ { 1 }$ ， $\pmb { a } _ { 1 }$ 产生“抵达”属于每一个槽填充的概率 $\pmb { y } _ { 1 }$ 。接下来 $\mathbf { a } _ { 1 }$ 会被存到记忆元里面去，“上海”会变为输入，这个隐藏层会同时考虑“上海”这个输入和存在记忆元里面的 $\mathbf { a } _ { 1 }$ ，得到 $\mathbf { a } _ { 2 }$ 。根据 $\mathbf { a } _ { 2 }$ 得到$\mathbf { \boldsymbol { y } } _ { 2 }$ ， $\mathbf { \boldsymbol { y } } _ { 2 }$ 是属于每一个槽填充的概率。

![](images/5c2e5c140f28b5e7a3fc4103097107f041026ed6e256e27af5566d330e4a277c.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    A["“抵达”在每个槽的概率"] --> B["y1"]
    B --> C["a1"]
    C --> D["a1"]
    D --> E["x1"]
    E --> F["抵达"]
    G["“上海”在每个槽的概率"] --> H["y2"]
    H --> I["a2"]
    I --> J["x2"]
    J --> K["抵达"]
    L["存储"] --> D
    style A fill:#f9f,stroke:#333
    style G fill:#f9f,stroke:#333
    style L fill:#ccf,stroke:#333
```
</details>

图 5.7 使用循环神经网络处理槽填充

这个不是三个网络，这是同一个网络在三个不同的时间点被使用了三次，用同样的权重用同样的颜色表示。

有了记忆元以后，输入同一个单词，希望输出不同的问题就有可能被解决。如图 5.8 所示，同样是输入“上海”这个单词，但是因为红色“上海”前接了“离开”，绿色“上海”前接了“抵达”，“离开”和“抵达”的向量不一样，隐藏层的输出会不同，所以存在记忆元里面的值会不同。虽然 $\mathbf { \boldsymbol { x } } _ { 2 }$ 的值是一样的，因为存在记忆元里面的值不同，所以隐藏层的输出会不同，所以最后的输出也就会不一样。

![](images/3ab9d3657e884a165ce365411f8b34a62ff3c2d9ab3103943ef91a94c9f5a109.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    A["“离开”在每个槽的概率"] --> B["y1"]
    B --> C["a1"]
    C --> D["存储"]
    D --> E["x1"]
    E --> F["离开"]
    G["“上海”在每个槽的概率"] --> H["y2"]
    H --> I["a2"]
    I --> J["存储"]
    J --> K["x2"]
    K --> L["存储"]
    L --> M["上海"]
    N["“抵达”在每个槽的概率"] --> O["y1"]
    O --> P["a1"]
    P --> Q["存储"]
    Q --> R["x1"]
    R --> S["抵达"]
    T["“上海”在每个槽的概率"] --> U["y2"]
    U --> V["a2"]
    V --> W["存储"]
    W --> X["x2"]
    X --> Y["存储"]
    Y --> Z["上海"]
    style A fill:#000,stroke:#fff,color:#fff
    style G fill:#000,stroke:#fff,color:#fff
    style N fill:#000,stroke:#fff,color:#fff
    style T fill:#000,stroke:#fff,color:#fff
    style B fill:#999,stroke:#333
    style H fill:#999,stroke:#333
    style O fill:#999,stroke:#333
    style P fill:#999,stroke:#333
    style Q fill:#999,stroke:#333
    style R fill:#999,stroke:#333
    style S fill:#999,stroke:#333
    style U fill:#999,stroke:#333
    style V fill:#999,stroke:#333
    style W fill:#999,stroke:#333
    style X fill:#999,stroke:#333
    style Y fill:#999,stroke:#333
    style Z fill:#999,stroke:#333
```
</details>

图 5.8 输入相同，输出不同示例

# 5.4 其他 RNN

循环神经网络的架构是可以任意设计的，之前提到的 RNN 只有一个隐藏层，但 RNN 也可以是深层的。比如把 $\mathbf { \Delta } _ { \mathbf { \mathcal { X } } _ { t } }$ 丢进去之后，它可以通过一个隐藏层，再通过第二个隐藏层，以此类推 (通过很多的隐藏层) 才得到最后的输出。每一个隐藏层的输出都会被存在记忆元里面，在下一个时间点的时候，每一个隐藏层会把前一个时间点存的值再读出来，以此类推最后得到输出，这个过程会一直持续下去。

![](images/3ab312eb1452107d58c60b471f54b673dbb81c293e6c6de91b7b8a5516927b6d.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    A["..."] --> B["..."]
    B --> C["..."]
    C --> D["..."]
    D --> E["..."]
    E --> F["..."]
    F --> G["..."]
    G --> H["..."]
    H --> I["..."]
    I --> J["..."]
    
    K["y_t"] --> L["↑"]
    M["y_{t+1}"] --> N["↑"]
    O["y_{t+2}"] --> P["↑"]
    
    Q["x_t"] --> R["↑"]
    S["x_{t+1}"] --> T["↑"]
    U["x_{t+2}"] --> V["↑"]
```
</details>

图 5.9 深层循环神经网络

# 5.4.1 Elman 网络 &Jordan 网络

循环神经网络会有不同的变形，如图 5.10 所示，刚才讲的是简单循环网络（Simple Re-current Network，SRN），即把隐藏层的值存起来，在下一个时间点在读出来。还有另外一种叫做 Jordan 网络，Jordan 网络存的是整个网络输出的值，它把输出值在下一个时间点在读进来，把输出存到记忆元里。Elman 网络没有目标，很难控制说它能学到什么隐藏层信息（学到什么放到记忆元里），但是 Jordan 网络是有目标，比较很清楚记忆元存储的东西。

简单循环网络也称为 Elman 网络。

![](images/f96583b5c6f9be14275f2dbf3c180052fad36651eb92a0b606b19aeafd71ae02.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    subgraph Elman 网络
        A["y_t"] -->|w_o| B["绿色节点"]
        C["y_{t+1}"] -->|w_o| D["绿色节点"]
        E["x_t"] -->|w_i| F["黄色节点"]
        G["x_{t+1}"] -->|w_i| H["黄色节点"]
    end
    
    subgraph Jordan 网络
        I["y_t"] -->|w_o| J["绿色节点"]
        K["y_{t+1}"] -->|w_o| L["绿色节点"]
        M["x_t"] -->|w_i| N["黄色节点"]
        O["x_{t+1}"] -->|w_i| P["黄色节点"]
        Q["w_h"] --> R["蓝色箭头指向 Jordan"]
    end
```
</details>

图 5.10 Elman 网络和 Jordan 网络

# 5.4.2 双向循环神经网络

循环神经网络还可以是双向。刚才 RNN 输入一个句子，它就是从句首一直读到句尾。如图 5.11 所示，假设句子里的每一个单词用 $\mathbf { \Delta } _ { \mathbf { \mathcal { X } } _ { t } }$ 表示，其是先读 $\mathbf { \Delta } _ { \mathbf { \mathcal { X } } _ { t } }$ ，再读 $\ X _ { t + 1 } , \ X _ { t + 2 } $ 。但其读取方向也可以是反过来的，它可以先读 ${ \pmb x } _ { t + 2 }$ ，再读 $\scriptstyle \pmb { x } _ { t + 1 } , \ \pmb { x } _ { t \circ }$ 。我们可以同时训练一个正向的循环神经网络，又可以训练一个逆向的循环神经网络，然后把这两个循环神经网络的隐藏层拿出来，都接给一个输出层得到最后的 $\pmb { y } _ { t }$ 。所以把正向的网络在输入 $\mathbf { \mathcal { x } } _ { t }$ 的时候跟逆向的网络在输入 $\mathbf { \mathcal { x } } _ { t }$ 时，都丢到输出层产生 $\pmb { y } _ { t }$ ，产生 $\pmb { y } _ { t + 1 } , \pmb { y } _ { t + 2 }$ ，以此类推。双向循环神经网络（Bidirectional Recurrent Neural Network，Bi-RNN）的好处是，神经元产生输出的时候，它看的范围是比较广的。如果只有正向的网络，再产生 $\boldsymbol { y } _ { t } \cdot \textit { \textbf { y } } _ { t + 1 }$ 的时候，神经元只看过 $\mathbf { \boldsymbol { x } } _ { 1 }$ 到${ \boldsymbol { x } } _ { t + 1 }$ 的输入。但双向循环神经网络产生 $\pmb { y } _ { t + 1 }$ 的时候，网络不只是看过 $\mathbf { \boldsymbol { x } } _ { 1 }$ , 到 ${ \pmb x } _ { t + 1 }$ 所有的输入，它也看了从句尾到 ${ \pmb x } _ { t + 1 }$ 的输入。网络就等于整个输入的序列。假设考虑的是槽填充，网络就等于看了整个句子后，才决定每一个单词的槽，这样会比看句子的一半还要得到更好的性能。

![](images/864001fd786b21dbcad7ea644905ca0466a1fe7f6090b1770ba7e0ad0a910661.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    A["x_t"] --> B["Green Block"]
    C["y_t"] --> B
    D["x_{t+1}"] --> E["Green Block"]
    F["y_{t+1}"] --> E
    G["x_{t+2}"] --> H["Green Block"]
    I["x_t"] --> J["Green Block"]
    K["x_{t+1}"] --> J
    L["x_{t+2}"] --> J
    B --> M["Blue Arrow"]
    E --> N["Blue Arrow"]
    H --> O["Blue Arrow"]
    J --> P["Blue Arrow"]
    M --> Q["Blue Arrow"]
    N --> R["Blue Arrow"]
    O --> S["Blue Arrow"]
    P --> T["Blue Arrow"]
```
</details>

图 5.11 双向循环神经网络

# 5.4.3 长短期记忆网络

之前提到的记忆元是最单纯的，可以随时把值存到记忆元去，也可以把值读出来。但最常用的记忆元是长短期记忆网络（Long Short-Term Memory network，LSTM），长时间的短期记忆。LSTM 是比较复杂的。LSTM 有三个门（gate），当外界某个神经元的输出想要被写到记忆元里面的时候，必须通过一个输入门（input gate），输入门要被打开的时候，才能把值写到记忆元里面。如果把这个关起来的话，就没有办法把值写进去。至于输入门的开关是神经网络自己学的，其可以自己学什么时候要把输入门打开，什么时候要把输入门关起来。输出的地方也有一个输出门（output gate），输出门会决定外界其他的神经元能否从这个记忆元里面把值读出来。把输出门关闭的时候是没有办法把值读出来，输出门打开的时候才可以把值读出来。跟输入门一样，输出门什么时候打开什么时候关闭，网络是自己学到的。第三个门称为遗忘门（forget gate），遗忘门决定什么时候记忆元要把过去记得的东西忘掉。这个遗忘门什么时候会把存在记忆元的值忘掉，什么时候会把存在记忆元里面的值继续保留下来，这也是网络自己学到的。整个 LSTM 可以看成有 4 个输入、1 个输出。在这 4 个输入中，一个是想要被存在记忆元的值，但不一定能存进去，还有操控输入门的信号、操控输出门的信号、操控遗忘门的信号，有着四个输入但它只会得到一个输出。

“-”应该在 short-term 中间，是长时间的短期记忆。之前的循环神经网络，它的记忆元在每一个时间点都会被洗掉，只要有新的输入进来，每一个时间点都会把记忆元洗掉，所以的短期是非常短的，但如果是长时间的短期记忆元，它记得会比较久一点，只要遗忘门不要决定要忘记，它的值就会被存起来。

![](images/9210144d0cfa4fd4f3c6d0a9c9de37317543d445283c871b281fddf9a72e4657.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    A["输入门"] --> B["记忆元"]
    B --> C["输出门"]
    C --> D["遗忘门"]
    D --> B
    B --> A
    style A fill:#f9f,stroke:#333
    style B fill:#bbf,stroke:#333
    style C fill:#f9f,stroke:#333
    style D fill:#f9f,stroke:#333
```
</details>

图 5.12 LSTM 结构

记忆元对应的计算公式为

$$
c ^ {\prime} = g (z) f \left(z _ {i}\right) + c f \left(z _ {f}\right) \tag {5.2}
$$

如图 5.13 所示，底下这个是外界传入单元的输入，还有输入门、遗忘门和输出门。假设要被存到单元的输入叫做 z，操控输入门的信号为 $z _ { i }$ ，操控遗忘门的信号为 $z _ { f }$ ，操控输出门为 $z _ { o }$ ，综合这些东西会得到一个输出记为 $a _ { \circ }$ 。假设单元里面有这四个输入之前，它里面已经存了值 c。输出 a 会长什么样子，把 z 通过激活函数得到 $g ( z )$ ， $z _ { i }$ 通过另外一个激活函数得到 $f ( z _ { i } )$ （激活函数通常会选择 sigmoid 函数），因为其值介在 0 到 1 之间的，这个 0 到 1 之间的值代表了这个门被打开的程度。（如果 f 的输出是 1，表示为被打开的状态，反之代表这个门是关起来的）。

接下来，把 $g ( z )$ 乘以 $f ( z _ { i } )$ 得到 $g ( z ) f ( z _ { i } )$ ，对于遗忘门的 $z _ { f }$ ，也通过 sigmoid 的函数得到$f ( z _ { f } )$ 接下来把存到记忆元里面的值 c 乘以 $f ( z _ { f } )$ 得到 $\mathrm { c } f ( z _ { f } )$ ，加起来 $c ^ { ' } = g ( z ) f ( z _ { i } ) + c f ( z _ { f } )$ ，那么 $c ^ { ' }$ 就是重新存到记忆元里面的值。所以根据目前的运算，这个 $f ( z _ { i } )$ 控制这个 $g ( z )$ 。假设输入 $f ( z _ { i } ) 0$ ，那 $g ( z ) f ( z _ { i } )$ 就等于 0，就好像是没有输入一样，如果 $f ( z _ { i } )$ 等于 1 就等于是把 $g ( z )$ 当做输入。那这个 $f ( z _ { f } )$ 决定是否要把存在记忆元的值洗掉，假设 $f ( z _ { f } )$ 为 1，遗忘门开启的时候，这时候 $c$ 会直接通过，把之前的值还会记得。如果 $f ( z _ { f } )$ 等于 0(遗忘门关闭的时候) $\mathinner { | { c f \mathopen { \left( z _ { f } \right) } } }$ 等于 $0 _ { \circ }$ 。然后把这个两个值加起来 $( c ^ { ' } = g ( z ) f ( z _ { i } ) + c f ( z _ { f } ) )$ 写到记忆元里面得到$c ^ { ' }$ 。这个遗忘门的开关是跟直觉是相反的，遗忘门打开的时候代表的是记得，关闭的时候代表的是遗忘。那这个 $c ^ { ' }$ 通过 $h ( c ^ { ' } )$ ，将 $h ( c ^ { ' } )$ 乘以 $f ( z _ { o } )$ 得到 $a = f ( c ^ { ' } f ( z _ { o } )$ 。输出门受 $f ( z _ { o } )$ 所操控， $f ( z _ { o } )$ 等于 1 的话，就说明 $h ( c ^ { ' } )$ 能通过， $f ( z _ { o } )$ 等于 0 的话，说明记忆元里面存在的值没有办法通过输出门被读取出来。

# 5.4.4 LSTM 举例

如图 5.14 所示，网络里面只有一个 LSTM 的单元，输入都是三维的向量，输出都是一维的输出。这三维的向量跟输出还有记忆元的关系是这样的。假设 $x _ { 2 }$ 的值是 1 时， $x _ { 1 }$ 的值就会被写到记忆元里；假设 $x _ { 2 }$ 的值是-1 时，就会重置这个记忆元；假设 $x _ { 3 }$ 的值为 1 时，才会把输出打开，才能看到输出，看到记忆元的数字。

假设原来存到记忆元里面的值是 0，当第二个维度 $x _ { 2 }$ 的值是 1 时，3 会被存到记忆元里面去。第四个维度的 $x _ { 2 }$ 等于，所以 4 会被存到记忆元里面去，所以会得到 $7 \phantom { . 0 }$ 。第六个维度的$x _ { 3 }$ 等于 1，这时候 7 会被输出。第七个维度的 $x _ { 2 }$ 的值为-1，记忆元里面的值会被洗掉变为 0。第八个维度的 $x _ { 2 }$ 的值为 1，所以把 6 存进去，因为 $x _ { 3 }$ 的值为 1，所以把 6 输出。

![](images/1c3ebb45bd8cc1df935efb5f71cf8df13892594068de75b66a68cbe938e29d17.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    A["输入层 z_i"] --> B["乘法器"]
    B --> C["隐藏门 c"]
    C --> D["块"]
    D --> E["输出层 f(z_i)"]
    E --> F["乘法器 g(z)"]
    F --> G["块"]
    G --> H["输出层 f(z_o)"]
    H --> I["乘法器 h(z_o)"]
    I --> J["块"]
    J --> K["输出层 f(z_o)"]
    K --> L["乘法器 f(z_o)"]
    L --> M["块"]
    M --> N["输出层 f(z_o)"]
    N --> O["乘法器 f(z_o)"]
    O --> P["块"]
    P --> Q["输出层 f(z_o)"]
    Q --> R["乘法器 f(z_o)"]
    R --> S["块"]
    S --> T["输出层 f(z_o)"]
    T --> U["乘法器 f(z_o)"]
    U --> V["块"]
    V --> W["输出层 f(z_o)"]
    W --> X["乘法器 f(z_o)"]
    X --> Y["块"]
    Y --> Z["输出层 f(z_o)"]
    Z --> AA["乘法器 f(z_o)"]
    AA --> AB["块"]
    AB --> AC["输出层 f(z_o)"]
    AC --> AD["乘法器 f(z_o)"]
    AD --> AE["块"]
    AE --> AF["输出层 f(z_o)"]
    AF --> AG["乘法器 f(z_o)"]
    AG --> AH["块"]
    AH --> AI["输出层 f(z_o)"]
    AI --> AJ["乘法器 f(z_o)"]
    AJ --> AK["块"]
    AK --> AL["输出层 f(z_o)"]
    AL --> AM["乘法器 f(z_o)"]
    AM --> AN["块"]
    AN --> AO["输出层 f(z_o)"]
    AO --> AP["乘法器 f(z_o)"]
    AP --> AQ["块"]
    AQ --> AR["输出层 f(z_o)"]
    AR --> AS["乘法器 f(z_o)"]
    AS --> AT["块"]
    AT --> AU["输出层 f(z_o)"]
    AU --> AV["乘法器 f(z_o)"]
    AV --> AW["块"]
    AW --> AX["输出层 f(z_o)"]
    AX --> AY["乘法器 f(z_o)"]
    AY --> AZ["块"]
    AZ --> BA["输出层 f(z_o)"]
    BA --> BB["乘法器 f(z_o)"]
    BB --> BC["块"]
    BC --> BD["输出层 f(z_o)"]
    BD --> BE["乘法器 f(z_o)"]
    BE --> BF["块"]
    BF --> BG["输出层 f(z_o)"]
    BG --> BH["乘法器 f(z_o)"]
    BH --> BI["块"]
    BI --> BJ["输出层 f(z_o)"]
    BJ --> BK["乘法器 f(z_o)"]
    BK --> BL["块"]
    BL --> BM["输出层 f(z_o)"]
    BM --> BN["乘法器 f(z_o)"]
    BN --> BO["块"]
    BO --> BP["输出层 f(z_o)"]
    BP --> BQ["乘法器 f(z_o)"]
    BQ --> BR["块"]
    BR --> BS["输出层 f(z_o)"]
    BS --> BT["乘法器 f(z_o)"]
    BT --> BU["块"]
    BU --> BV["输出层 f(z_o)"]
    BV --> BW["乘法器 f(z_o)"]
    BW --> BX["块"]
    BX --> BY["输出层 f(z_o)"]
    BY --> BZ["乘法器 f(z_o)"]
    BZ --> CA["块"]
```
</details>

图 5.13 LSTM 记忆元示例

![](images/31442521d357229ad5601e349b0118c4acfcb2af1116b31ff3ffc73ccb2a624a.jpg)

<details>
<summary>heatmap</summary>

| | 0 | 0 | 3 | 3 | 7 | 7 | 7 | 0 | 6 |
|---|---|---|---|---|---|---|---|---|---|
| x1 | 1 | 3 | 2 | 4 | 2 | 1 | 3 | 6 | 1 |
| x2 | 0 | 1 | 0 | 1 | 0 | 0 | -1 | 1 | 0 |
| x3 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 |
| y | 0 | 0 | 0 | 0 | 0 | 7 | 0 | 0 | 6 |
</details>

图 5.14 LSTM 示例

# 5.4.5 LSTM 运算示例

图 5.15 给出了 LSTM 实际的运算的例子。记忆元的四个输入标量是这样来的：输入的三维向量乘以线性变换（linear transform）后所得到的结果， $x _ { 1 } , x _ { 2 } , x _ { 3 }$ 乘以权重再加上偏置。假设这些值是已知的，在实际运算之前，先根据它的输入，分析下可能会得到的结果。底下这个外界传入的单元， $x _ { 1 }$ 乘以 1，其他的向量乘以 0，所以就直接把 $x _ { 1 }$ 当做输入。在输入门时，$x _ { 2 }$ 乘以 100，偏置乘以 −10。假设 $x _ { 2 }$ 是没有值的话，通常输入门是关闭的（偏置等于 −10）。因为 −10 通过 sigmoid 函数之后会接近 0，所以就代表是关闭的，若 $x _ { 2 }$ 的值大于 1 的话，结果会是一个正值，代表输入门会被打开。遗忘门通常会被打开的，因为其偏置等于 10，它平常会一直记得东西，只有当 $x _ { 2 }$ 的值为一个很大的负值时，才会把遗忘门关起来。输出门平常是被关闭的，因为偏置是一个很大的负值，若 $x _ { 3 }$ 有一个很大的正值的话，压过偏置把输出打

开。

![](images/13449d1d8899f73d9db410ef7faf4c588b9fc145c0c7565ef1dc98ae8bcfac07.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    subgraph Input
        x1["x₁"] -->|0| A["+"]
        x2["x₂"] -->|0| A
        x3["x₃"] -->|-10| A
        x1x["x₁"] -->|0| B["+"]
        x2x["x₂"] -->|100| B
        x3x["x₃"] -->|-10| B
    end
    A --> C["输出门"]
    B --> D["输入门"]
    C --> E["块"]
    D --> E
    E --> F["遗忘门"]
    F --> G["输出"]
    style A fill:#f9f,stroke:#333
    style B fill:#f9f,stroke:#333
    style C fill:#ccf,stroke:#333
    style D fill:#ccf,stroke:#333
    style E fill:#cfc,stroke:#333
    style F fill:#fcc,stroke:#333
    style G fill:#fcc,stroke:#333
    subgraph Output
        y["y"] --> E
        x1["x₁"] --> F
        x2["x₂"] --> F
        x3["x₃"] --> G
        x1x["x₁"] --> H["块"]
        x2x["x₂"] --> H
        x3x["x₃"] --> I["块"]
        x1x["x₁"] --> J["块"]
        x2x["x₂"] --> K["块"]
        x3x["x₃"] --> L["块"]
        x1x["x₁"] --> M["块"]
        x2x["x₂"] --> N["块"]
        x3x["x₃"] --> O["块"]
        x1x["x₁"] --> P["块"]
        x2x["x₂"] --> Q["块"]
        x3x["x₃"] --> R["块"]
        x1x["x₁"] --> S["块"]
        x2x["x₂"] --> T["块"]
        x3x["x₃"] --> U["块"]
        x1x["x₁"] --> V["块"]
        x2x["x₂"] --> W["块"]
        x3x["x₃"] --> X["块"]
        x1x["x₁"] --> Y["块"]
        x2x["x₂"] --> Z["块"]
        x3x["x₃"] --> AA["块"]
        x1x["x₁"] --> AB["块"]
        x2x["x₂"] --> AC["块"]
        x3x["x₃"] --> AD["块"]
        x1x["x₁"] --> AE["块"]
        x2x["x₂"] --> AF["块"]
        x3x["x₃"] --> AG["块"]
        x1x["x₁"] --> AH["块"]
        x2x["x₂"] --> AI["块"]
        x3x["x₃"] --> AJ["块"]
        x1x["x₁"] --> AK["块"]
        x2x["x₂"] --> AL["块"]
        x3x["x₃"] --> AM["块"]
        x1x["x₁"] --> AN["块"]
        x2x["x₂"] --> AO["块"]
        x3x["x₃"] --> AP["块"]
        x1x["x₁"] --> AQ["块"]
        x2x["x₂"] --> AR["块"]
        x3x["x₃"] --> AS["块"]
        x1x["x₁"] --> AT["块"]
        x2x["x₂"] --> AU["块"]
        x3x["x₃"] --> AV["块"]
        x1x["x₁"] --> AW["块"]
        x2x["x₂"] --> AX["块"]
        x3x["x₃"] --> AY["块"]
        x1x["x₁"] --> AZ["块"]
        x2x["x₂"] --> BA["块"]
        x3x["x₃"] --> BB["块"]
        x1x["x₁"] --> BC["块"]
        x2x["x₂"] --> BD["块"]
        x3x["x₃"] --> BE["块"]
        x1x["x₁"] --> BF["块"]
        x2x["x₂"] --> BG["块"]
        x3x["x₃"] --> BH["块"]
        x1x["x₁"] --> BI["块"]
        x2x["x₂"] --> BJ["块"]
        x3x["x₃"] --> BK["块"]
        x1x["x₁"] --> BL["块"]
        x2x["x₂"] --> BM["块"]
        x3x["x₃"] --> BN["块"]
        x1x["x₁"] --> BO["块"]
        x2x["x₂"] --> BP["块"]
        x3x["x₃"] --> BQ["块"]
        x1x["x₁"] --> BR["块"]
        x2x["x₂"] --> BS["块"]
        x3x["x₃"] --> BT["块"]
        x1x["x₁"] --> BU["块"]
        x2x["x₂"] --> BV["块"]
        x3x["x₃"] --> BW["块"]
        x1x["x₁"] --> BX["块"]
        x2x["x₂"] --> BY["块"]
        x3x["x₃"] --> BZ["块"]
        x1x["x₁"] --> CA["块"]
        x2x["x₂"] --> CB["块"]
        x3x["x₃"] --> CC["块"]
        x1x["x₁"] --> CD["块"]
        x2x["x₂"] --> CE["块"]
        x3x["x₃"] --> CF["块"]
        x1x["x₁"] --> CG["块"]
        x2x["x₂"] --> CH["块"]
        x3x["x₃"] --> CI["块"]
        x1x["x₁"] --> CJ["块"]
        x2x["x₂"] --> CK["块"]
        x3x["x₃"] --> CR["块"]
```
</details>

图 5.15 LSTM 运算示例

接下来，实际的输入一下看看。为了简化计算，假设 g 和 h 都是线性的。假设存到记忆元里面的初始值是 0，如图 5.17 所示，输入第一个向量 $[ 3 , 1 , 0 ] ^ { \mathrm { T } }$ ，输入这边 $3 ^ { * } 1 { = } 3$ ，这边输入的是的值为 3。输入门这边 $\left( 1 * 1 0 0 - 1 0 \approx 1 \right)$ 是被打开 (输入门约等于 1)。 $( g ( z ) * f ( z _ { i } ) = 3 )$ 。遗忘门 $( 1 * 1 0 0 + 1 0 \approx 1 )$ 是被打开的 (遗忘门约等于 1)。 $0 ~ ^ { * } 1 + 3 { = } 3 ( c ^ { ' } = g ( z ) f ( z _ { i } ) + c f ( z _ { f } ) )$ ，所以存到记忆元里面的为 3。输出门 (-10) 是被关起来的，所以 3 无关通过，所以输出值为 0。

![](images/b1864254ba18d148c9820378b2910e396f45d3a7c3dc6eb18f2ad7c83c6db485.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    A["输入 0"] --> B["100"]
    C["输入 1"] --> D["100"]
    E["输入 2"] --> F["100"]
    G["输入 3"] --> H["100"]
    I["输入 4"] --> J["100"]
    K["输入 5"] --> L["100"]
    M["输入 6"] --> N["100"]
    O["输入 7"] --> P["100"]
    Q["输入 8"] --> R["100"]
    S["输入 9"] --> T["100"]
    U["输入 10"] --> V["100"]
    W["输入 11"] --> X["100"]
    Y["输入 12"] --> Z["100"]
    AA["输入 13"] --> AB["100"]
    AC["输入 14"] --> AD["100"]
    AE["输入 15"] --> AF["100"]
    AG["输入 16"] --> AH["100"]
    AI["输入 17"] --> AJ["100"]
    AK["输入 18"] --> AL["100"]
    AM["输入 19"] --> AN["100"]
    AO["输入 20"] --> AP["100"]
    AQ["输入 21"] --> AR["100"]
    AS["输入 22"] --> AT["100"]
    AU["输入 23"] --> AV["100"]
    AW["输入 24"] --> AX["100"]
    AY["输出 0"] --> AZ["+"]
    BA["输出 1"] --> BB["+"]
    BC["输出 2"] --> BD["+"]
    BE["输出 3"] --> BF["+"]
    BG["输出 4"] --> BH["+"]
    BI["输出 5"] --> BJ["+"]
    BK["输出 6"] --> BL["+"]
    BM["输出 7"] --> BN["+"]
    BO["输出 8"] --> BP["+"]
    BZ["输入 0"] --> CA["+"]
    CB["输入 1"] --> CD["+"]
    CE["输入 2"] --> CF["+"]
    CG["输入 3"] --> CH["+"]
    CI["输入 4"] --> CJ["+"]
    CK["输入 5"] --> CL["+"]
    CM["输入 6"] --> CN["+"]
    CO["输入 7"] --> CP["+"]
    CS["输入 8"] --> CT["+"]
    CU["输入 9"] --> CV["+"]
    CW["输入 10"] --> CX["+"]
    CY["输入 11"] --> CZ["+"]
    DA["输入 12"] --> DB["+"]
    DC["输入 13"] --> DD["+"]
    DJ["输入 14"] --> DE["+"]
    DF["块"] --> DG["x_1"]
    DF --> DH["x_2"]
    DF --> DI["x_3"]
```
</details>

图 5.16 LSTM 运算示例：第 1 步

接下来输入 $[ 4 , 1 , 0 ] ^ { \mathrm { T } }$ ，如图 5.17 所示，传入输入的值为 4，输入门会被打开，遗忘门也会被打开，所以记忆元里面存的值等于 $7 \ : \ : ( 3 + 4 = 7 )$ ），输出门仍然会被关闭的，所以 7 没有办法被输出，所以整个记忆元的输出为 0。

接下来输入 $[ 2 , 0 , 0 ] ^ { \mathrm { T } }$ ，如图 5.18 所示，传入输入的值为 2，输入门关闭 $( \approx 0 )$ ），输入被输入门给挡住了 $( 0 \times 2 = 0 )$ ），遗忘门打开（10）。原来记忆元里面的值还是 $7 \ : \ : ( 1 \times 7 + 0 = 7 )$ ）。输出门仍然为 0，所以没有办法输出，所以整个输出还是 0。

![](images/9040fa31c9e40053080138b31ee2a3083f21c3252f2d30a474e738f4ad183345.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    A["输入 0"] --> B["+"]
    C["输入 1"] --> B
    D["输入 2"] --> B
    E["输入 3"] --> B
    F["输入 4"] --> B
    G["输入 5"] --> B
    H["输入 6"] --> B
    I["输入 7"] --> J["块"]
    K["块"] --> L["+"]
    M["块"] --> N["块"]
    O["块"] --> P["块"]
    Q["块"] --> R["块"]
    S["块"] --> T["块"]
    U["块"] --> V["块"]
    W["块"] --> X["块"]
    Y["块"] --> Z["块"]
    AA["块"] --> AB["块"]
    AC["块"] --> AD["块"]
    AE["块"] --> AF["块"]
    AG["块"] --> AH["块"]
    AI["块"] --> AJ["块"]
    AK["块"] --> AL["块"]
    AM["块"] --> AN["块"]
    AO["块"] --> AP["块"]
    AQ["块"] --> AR["块"]
    AS["块"] --> AT["块"]
    AU["块"] --> AV["块"]
    AW["块"] --> AX["块"]
    AY["输入 0"] --> AZ["+"]
    BA["输入 1"] --> BB["+"]
    BC["输入 2"] --> BD["+"]
    BE["输入 3"] --> BF["+"]
    BG["输入 4"] --> BH["+"]
    BI["输入 5"] --> BJ["+"]
    BK["输入 6"] --> BL["+"]
    BM["输入 7"] --> BN["块"]
    BO["输入 8"] --> BP["块"]
    BZ["输出 0"] --> AA
    CA["输出 1"] --> AB
    CB["输出 2"] --> AC
    CC["输出 3"] --> AD
    DD["输出 4"] --> AE
    FF["输出 5"] --> BG
    DG["输出 6"] --> BH
    DH["输出 7"] --> BI
    BI --> AE
    AE --> DB
    AF --> DC
    AG --> DD
    AH --> DC
    AI --> DB
    AJ --> DC
    AK --> DB
    AL --> DC
    AM --> DC
    AN --> DC
    AO --> DC
    AP --> DC
    AQ --> DC
    BB --> DC
    BC --> DC
    AD --> DC
    AE --> DC
    AF --> DC
    AG --> DC
    AH --> DC
    AI --> DC
    AJ --> DC
    AK --> DC
    AL --> DC
    AM --> DC
    AN --> DC
    AO --> DC
    AP --> DC
    AQ --> DC
    BB --> DC
    BC --> DC
    AD --> DC
    AE --> DC
    AF --> DC
    AG --> DC
    AH --> DC
    AI --> DC
    AJ --> DC
    AK --> DC
```
</details>

图 5.17 LSTM 运算示例：第 2 步

![](images/544b7921b459c5d900dc237ed063ec18f432c34e30e6176099f681297ff5b597.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    subgraph Input
        A["输入1"] --> B["输入2"]
        C["输入3"] --> D["输入4"]
        E["输入5"] --> F["输入6"]
        G["输入7"] --> H["输入8"]
        I["输入9"] --> J["输入10"]
        K["输入11"] --> L["输入12"]
        M["输入13"] --> N["输入14"]
        O["输入15"] --> P["输入16"]
        Q["输入17"] --> R["输入18"]
        S["输入19"] --> T["输入20"]
    end

    subgraph Hidden
        U["块"] --> V["块"]
        W["块"] --> X["块"]
        Y["块"] --> Z["块"]
    end

    subgraph Output
        AA["输出1"] --> AB["输出2"]
        AC["输出3"] --> AD["输出4"]
        AE["输出5"] --> AF["输出6"]
        AG["输出7"] --> AH["输出8"]
        AI["输出9"] --> AJ["输出10"]
        AK["输出11"] --> AL["输出12"]
        AM["输出13"] --> AN["输出14"]
        AO["输出15"] --> AP["输出16"]
        AQ["输出17"] --> AR["输出18"]
        AS["输出18"] --> AT["输出19"]

    subgraph Output
        AU["块"] --> AV["块"]
    end

    style Input fill:#f9f,stroke:#333
    style Hidden fill:#ccf,stroke:#333
    style Output fill:#cfc,stroke:#333
```
</details>

图 5.18 LSTM 运算示例：第 3 步

接下来输入 $[ 1 , 0 , 1 ] ^ { \mathrm { T } }$ ，如图 5.19 所示，传入输入的值为 1，输入门是关闭的，遗忘门是打开的，记忆元里面存的值不变，输出门被打开，整个输出为 7，记忆元里面存的 7 会被读取出来。

最后输入 $[ 3 , - 1 , 0 ] ^ { \mathrm { T } }$ ，如图 5.20 所示，传入输入的值为 3，输入门关闭，遗忘门关闭，记忆元里面的值会被洗掉变为 0，输出门关闭，所以整个输出为 0。

# 5.5 LSTM 原理

在原来的神经网络里面会有很多的神经元，我们会把输入乘以不同的权重当做不同神经元的输入，每一个神经元都是一个函数，输入一个值然后输出一个值。但是如果是 LSTM 的话，只要把 LSTM 想成是一个神经元。所以要用一个 LSTM 的神经元，其实就是原来简单的神经元换成 LSTM。

如图 5.22 所示，为了简化，假设隐藏层只有两个神经元，输入 $x _ { 1 } , x _ { 2 }$ 会乘以不同的权重当做 LSTM 不同的输入。输入 $( x _ { 1 } , x _ { 2 } )$ 会乘以不同的权重会去操控输出门，乘以不同的权重操控输入门，乘以不同的权重当做底下的输入，乘以不同的权重当做遗忘门。第二个 LSTM也是一样的。所以 LSTM 是有四个输入跟一个输出，对于 LSTM 来说，这四个输入是不一样的。在原来的神经网络里是一个输入一个输出。在 LSTM 里面它需要四个输入，它才能产生一个输出。LSTM 因为需要四个输入，四个输入都是不一样，原来的一个神经元就只有一个输入和输出。假设用的神经元的数量跟 LSTM 是一样的，则 LSTM 需要的参数量是一般神经网络的四倍。

![](images/260724ff9cc25dce023068657ac04110f64c9656f879692ae09ecab7fa8d79da.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    A["输入门 100"] --> B["+"]
    B --> C["输出门 7"]
    C --> D["遗忘门 7"]
    D --> E["块"]
    E --> F["+"]
    F --> G["x1 3 4 2 1 3"]
    F --> H["x2 1 4 2 1 3"]
    F --> I["x3 0 0 0 1 0"]
    style A fill:#f9f,stroke:#333
    style B fill:#ccf,stroke:#333
    style C fill:#cfc,stroke:#333
    style D fill:#fcc,stroke:#333
    style E fill:#cff,stroke:#333
    style F fill:#ffc,stroke:#333
    style G fill:#cfc,stroke:#333
    style H fill:#cfc,stroke:#333
    style I fill:#cfc,stroke:#333
```
</details>

图 5.19 LSTM 运算示例：第 4 步

![](images/604ec061d459246ce1048684b66a738c4b049e664fb23a71bb50d29d93d8d2c2.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    A["输入"] --> B["块"]
    B --> C["输出门"]
    C --> D["块"]
    D --> E["遗忘门"]
    E --> F["块"]
    F --> G["输出"]
    style A fill:#f9f,stroke:#333
    style B fill:#ccf,stroke:#333
    style C fill:#cfc,stroke:#333
    style D fill:#fcc,stroke:#333
    style E fill:#cff,stroke:#333
    style F fill:#ffc,stroke:#333
    style G fill:#cfc,stroke:#333
    subgraph Input
        H["输入1"] --> I["输入2"]
        J["输入3"] --> K["输入4"]
        L["输入5"] --> M["输入6"]
        N["输入7"] --> O["输入8"]
        P["输入9"] --> Q["输入10"]
        R["输入11"] --> S["输入12"]
        T["输入13"] --> U["输入14"]
        V["输入15"] --> W["输入16"]
        X["输入17"] --> Y["输入18"]
        Z["输入19"] --> AA["输入20"]
        AB["输入21"] --> AC["输入22"]
        AD["输入23"] --> AE["输入24"]
        AF["输入25"] --> AG["输入26"]
        AH["输入27"] --> AI["输入28"]
        AJ["输入29"] --> AK["输入30"]
    end
    subgraph Output
        L1["1"] --> M1["0"]
        M2["0"] --> N2["0"]
        N3["1"] --> O3["0"]
        O4["0"] --> P4["0"]
        P5["1"] --> Q5["0"]
        Q6["0"] --> R6["0"]
        R7["1"] --> AA7["0"]
        AA7 --> AB7["0"]
        AB7 --> AC7["0"]
        AC7 --> AD7["0"]
        AD7 --> AE7["0"]
        AE7 --> AF7["0"]
    end
    style Input fill:#f9f,stroke:#333
    style Output fill:#ccf,stroke:#333
```
</details>

图 5.20 LSTM 运算示例：第 5 步

如图 5.23 所示，假设有一整排的 LSTM，这些 LSTM 里面的记忆元都存了一个值，把所有的值接起来就变成了向量，写为 $c ^ { t - 1 }$ （一个值就代表一个维度）。现在在时间点 t，输入向量 $\mathbf { \mathcal { x } } _ { t }$ ，这个向量首先会乘上一矩阵（线性变换）变成一个向量 z，向量 z 的维度就代表了操控每一个 LSTM 的输入。z 这个维度正好就是 LSTM 记忆元的数量。z 的第一维就丢给第一个单元。这个 $\mathbf { \mathcal { x } } _ { t }$ 会乘上另外的一个变换得到 $z ^ { i }$ ，然后这个 $z ^ { i }$ 的维度也跟单元的数量一样， $z ^ { i }$ 的每一个维度都会去操控输入门。遗忘门跟输出门也都是一样，不再赘述。所以我们把 $\mathbf { \Delta } _ { \mathbf { \mathcal { X } } _ { t } }$ 乘以四个不同的变换得到四个不同的向量，四个向量的维度跟单元的数量一样，这四个向量合起来就会去操控这些记忆元运作。

![](images/378aabab390760047afdd8ad5e0bdc8ee0cfec8f480250d4cdb74616bcfe9b42.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    A["x1"] --> Z1["z1"]
    B["x2"] --> Z2["z2"]
    Z1 --> X1["x1"]
    Z2 --> X2["x2"]
    style Z1 fill:#f9f,stroke:#333
    style Z2 fill:#f9f,stroke:#333
    style X1 fill:#ccf,stroke:#333
    style X2 fill:#ccf,stroke:#333
    note right of Z1
        输入
    end
```
</details>

图 5.21 把 LSTM 想成一个神经元

![](images/f91d39e9b729a2f298605207cacf8a37e2bf1e0033791a54ff4d2ba7879e24cb.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    subgraph Layer1
        A["+"] --> B["输出门"]
        B --> C["单元"]
        C --> D["输入门"]
        D --> E["块"]
        E --> F["+"]
    end
    subgraph Layer2
        G["+"] --> H["输出门"]
        H --> I["单元"]
        I --> J["输入门"]
        J --> K["块"]
        K --> L["+"]
    end
    style Layer1 fill:#f9f,stroke:#333
    style Layer2 fill:#bbf,stroke:#333
    subgraph Cell1
        C --> M["单元"]
        M --> N["输入门"]
        N --> O["块"]
        O --> P["+"]
    end
    subgraph Cell2
        I --> Q["单元"]
        Q --> R["输入门"]
        R --> S["块"]
        S --> T["+"]
    end
```
</details>

图 5.22 LSTM 需要 4 个输入

如图 5.24 所示，输入分别就是 $z , z ^ { i } , z ^ { o } , z ^ { f }$ (都是向量)，丢到单元里面的值其实是向量的一个维度，因为每一个单元输入的维度都是不一样的，所以每一个单元输入的值都会是不一样。所以单元是可以共同一起被运算的。 $z ^ { i }$ 通过激活函数跟 $_ { z }$ 相乘， $z ^ { f }$ 通过激活函数跟之前存在单元里面的值相乘，然后将 z 跟 $z ^ { i }$ 相乘的值加上 $z ^ { f }$ 跟 $c ^ { t - 1 }$ 相乘的值， $z ^ { o }$ 通过激活函数的结果输出，跟之前相加的结果再相乘，最后就得到了输出 $\pmb { y } _ { t }$ 。

之前那个相加以后的结果就是记忆元里面存放的值 $c ^ { t }$ ，这个过程反复的进行，在下一个时间点输入 ${ \pmb x } _ { t + 1 }$ ，把 $_ { z }$ 跟输入门相乘，把遗忘门跟存在记忆元里面的值相乘，将前面两个值再相加起来，在乘上输出门的值，得到下一个时间点的输出 $\pmb { y } _ { t + 1 }$ 但这还不是 LSTM 的最终形态，真正的 LSTM 会把上一个时间的输出接进来，当做下一个时间的输入，即下一个时间点操控这些门的值不是只看那个时间点的输入 $x _ { t }$ ，还看前一个时间点的输出 $\boldsymbol { h } ^ { t }$ 。其实还不止这样，还会添加 peephole 连接，如图 5.25 所示。peephole 就是把存在记忆元里面的值也拉过来。操控 LSTM 四个门的时候，同时考虑了 $\boldsymbol { x } _ { t + 1 } , \boldsymbol { h } ^ { t } , \boldsymbol { c } ^ { t }$ ，把这三个向量并在一起乘上不同的变换得到四个不同的向量再去操控 LSTM。

![](images/eef88f663d0cc945b028f15f6ecf0232a7d57b4bea1405efc63ab121fb4ce89b.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    A["z_f"] --> B["4个向量"]
    C["z_i"] --> B
    D["z"] --> B
    E["z_o"] --> B
    B --> F["单元"]
    F --> G["输入门"]
    G --> H["块"]
    H --> I["输出门"]
    I --> J["单元"]
    J --> K["输入门"]
    K --> L["块"]
    L --> M["输出门"]
    M --> N["单元"]
    N --> O["输入门"]
    O --> P["块"]
    P --> Q["..."]
    Q --> R["单元"]
    R --> S["输入门"]
    S --> T["块"]
    T --> U["输出门"]
    U --> V["单元"]
    V --> W["输入门"]
    W --> X["块"]
    X --> Y["..."]
    Y --> Z["单元"]
    Z --> AA["输入门"]
    AA --> AB["块"]
    AB --> AC["..."]
    AC --> AD["单元"]
    AD --> AE["输入门"]
    AE --> AF["块"]
    AF --> AG["..."]
    AG --> AH["单元"]
    AH --> AI["输入门"]
    AI --> AJ["块"]
    AJ --> AK["..."]
    AK --> AL["单元"]
    AL --> AM["输入门"]
    AM --> AN["块"]
    AN --> AO["..."]
    AO --> AP["单元"]
    AP --> AQ["输入门"]
    AQ --> AR["块"]
    AR --> AS["..."]
    AS --> AT["单元"]
    AT --> AU["输入门"]
    AU --> AV["块"]
    AV --> AW["..."]
    AW --> AX["单元"]
    AX --> AY["输入门"]
    AY --> AZ["块"]
    AZ --> BA["..."]
    BA --> BB["单元"]
    BB --> BC["输入门"]
    BC --> BD["块"]
    BD --> BE["..."]
    BE --> BF["单元"]
    BF --> BG["输入门"]
    BG --> BH["块"]
    BH --> BI["..."]
    BI --> BJ["单元"]
    BJ --> BK["输入门"]
    BK --> BL["块"]
    BL --> BM["..."]
    BM --> BN["单元"]
    BN --> BO["输入门"]
    BO --> BP["块"]
    BP --> BQ["..."]
    BQ --> BR["单元"]
    BR --> BS["输入门"]
    BS --> BT["块"]
    BT --> BU["..."]
    BU --> BV["单元"]
    BV --> BW["输入门"]
    BW --> BX["块"]
    BX --> BY["..."]
    BY --> BZ["单元"]
    BZ --> CA["输入门"]
    CA --> CB["块"]
    CB --> CC["..."]
    CC --> CD["单元"]
    CD --> CE["输入门"]
    CE --> CF["块"]
    CF --> CG["..."]
    CG --> CH["单元"]
    CH --> CI["输入门"]
    CI --> CJ["块"]
    CJ --> CK["..."]
    CK --> CR["单元"]
    CR --> CS["输入门"]
    CS --> CT["块"]
    CT --> CU["..."]
    CU --> CV["单元"]
    CV --> CW["输入门"]
    CW --> CX["块"]
    CX --> CY["..."]
    CY --> CZ["单元"]
    CZ --> DA["输入门"]
    DA --> DB["块"]
```
</details>

图 5.23 输入向量与记忆元的关系  
![](images/10fa2a368bde9b0b77c6bcb0b8e12142125c1daee420cb36e32965f0cde07584.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    subgraph Input Layer
        A["×"] --> B["+"]
        C["×"] --> D["×"]
        E["z"] --> F["×"]
        G["z_i"] --> H["×"]
        I["z_o"] --> J["×"]
        K["x_t"] --> L["z_f"]
        M["c_{t-1}"] --> N["×"]
        O["x_t"] --> P["×"]
        Q["y_t"] --> R["×"]
    end
    subgraph Hidden Layer
        S["f"] --> T["单元"]
        U["h"] --> T
        V["f"] --> T
        W["f"] --> T
        X["f"] --> T
        Y["f"] --> Z["块"]
        AA["输入门"] --> AB["块"]
        AC["输入门"] --> AD["块"]
        AE["块"] --> AF["Z_f"]
    end
    subgraph Output Layer
        AG["z"] --> AH["块"]
        AI["z_i"] --> AJ["块"]
        AK["块"] --> AL["块"]
        AM["块"] --> AN["块"]
    end
    style Input Layer fill:#f9f,stroke:#333
    style Hidden Layer fill:#ccf,stroke:#333
    style Output Layer fill:#cfc,stroke:#333
```
</details>

图 5.24 记忆元一起运算示例

LSTM 通常不会只有一层，若有五六层的话，如图 5.26 所示。一般做 RNN 的时候，其实指的就用 LSTM。

门控循环单元（Gated Recurrent Unit，GRU）是 LSTM 稍微简化的版本，它只有两个门。虽然少了一个门，但其性能跟 LSTM 差不多，少了 1/3 的参数，也是比较不容易过拟合。

# 5.6 RNN 学习方式

如果要做学习，需要定义一个损失函数（loss function）来评估模型的好坏，选一个参数要让损失最小。以槽填充为例，如图 5.27 所示，给定一些句子，要给句子一些标签，告诉机器说第一个单词它是属于 other 槽，“上海”是目的地槽，“on”属于 other 槽，“June”和“1st”属于时间槽。“抵达”丢到循环神经网络的时候，循环神经网络会得到一个输出 $\pmb { y } _ { 1 }$ 。接下来这个 $\pmb { y } _ { 1 }$ 会看它的参考向量（reference vector）算它的交叉熵。我们会期望如果丢进去的是“抵达”，其参考向量应该对应到 other 槽的维度，其他为 0，这个参考向量的长度就是槽的数量。如果有四十个槽，参考向量的维度就是 40。输入的这个单词对应到 other 槽的话，对应到 other 槽维度为 1, 其它为 0。把“上海”丢进去之后，因为“上海”属于目的地槽，希望说把 $\mathbf { \boldsymbol { x } } _ { 2 }$ 丢进去的话， $\pmb { y } _ { 2 }$ 要跟参考向量距离越近越好。那 $\mathbf { \boldsymbol { y } } _ { 2 }$ 的参考向量是对应到目的地槽是 1，其它为 $0 _ { \circ }$ 。注意，在丢 $\mathbf { \boldsymbol { x } } _ { 2 }$ 之前，一定要丢 $\mathbf { \boldsymbol { x } } _ { 1 }$ （在丢“上海”之前先把“抵达”丢进去），不然就不知道存到记忆元里面的值是多少。所以在训练的时候，不能够把这些单词序列打散来看，单词序列仍然要当做一个整体来看。把“on”丢进去，参考向量对应的 other 的维度是 1，其它是 0. RNN 的损失函数输出和参考向量的交叉熵的和就是要最小化的对象。

![](images/bc81110ee735d7d1412e377bc1e837d98327223ce9816da2272bc0ca12665a3d.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    subgraph Input Layer
        A["c_{t-1}"] --> B["×"]
        B --> C["+"]
        C --> D["×"]
        D --> E["×"]
        E --> F["×"]
        F --> G["×"]
        G --> H["×"]
        H --> I["×"]
        I --> J["×"]
        J --> K["×"]
        K --> L["×"]
        L --> M["×"]
        M --> N["×"]
        N --> O["×"]
        O --> P["×"]
        P --> Q["×"]
        Q --> R["×"]
    end

    subgraph Hidden Layer
        S["z_f"] --> T["h_{t-1}"]
        T --> U["x_t"]
        U --> V["z_i"]
        V --> W["x_t+1"]
        W --> X["z_o"]
        X --> Y["h_t"]
        Y --> Z["x_t+1"]
        Z --> AA["z_o"]
        AA --> AB["h_t+1"]
        AB --> AC["x_t+1"]
        AC --> AD["z_i"]
        AD --> AE["h_t+1"]
        AE --> AF["x_t"]
        AF --> AG["z_o"]
        AG --> AH["h_t+1"]
        AH --> AI["x_t+1"]
        AI --> AJ["z_i"]
        AJ --> AK["h_t+1"]
        AK --> AL["x_t+1"]
        AL --> AM["z_o"]
        AM --> AN["h_t+1"]
        AN --> AO["x_t+1"]
        AO --> AP["z_i"]
        AP --> AQ["h_t+1"]
        AQ --> AR["x_t"]
        AR --> AS["z_o"]
        AS --> AT["h_t+1"]
        AT --> AU["x_t+1"]
        AU --> AV["z_i"]
        AV --> AW["h_t+1"]
        AW --> AX["x_t+1"]
        AX --> AY["z_o"]
        AY --> AZ["h_t+1"]
        AZ --> BA["x_t+1"]
        BA --> BB["z_i"]
        BB --> BC["h_t+1"]
        BC --> BD["x_t"]
        BD --> BE["z_o"]
        BE --> BF["h_t+1"]
        BF --> BG["x_t+1"]
    end

    subgraph Output Layer
        C_t_minus_1["c_{t-1}"] --> C_t
    end

    style Input Layer fill:#f9f,stroke:#333
    style Hidden Layer fill:#ccf,stroke:#333
    style Output Layer fill:#cfc,stroke:#333
```
</details>

图 5.25 peephole 连接

有了这个损失函数以后，对于训练也是用梯度下降来做。也就是现在定义出了损失函数L，要更新这个神经网络里面的某个参数 w，就是计算对 w 的偏微分，偏微分计算出来以后，就用梯度下降的方法去更新里面的参数。梯度下降用在前馈神经网络里面我们要用一个有效率的算法称为反向传播。循环神经网络里面，为了要计算方便，提出了反向传播的进阶版，即随时间反向传播（BackPropagation Through Time，BPTT）。BPTT 跟反向传播其实是很类似的，只是循环神经网络它是在时间序列上运作，所以 BPTT 它要考虑时间上的信息，如图 5.28 所示。

RNN 的训练是比较困难的，如图 5.29 所示。一般而言，在做训练的时候，期待学习曲线是像蓝色这条线，这边的纵轴是总损失（total loss），横轴是回合的数量，我们会希望随着回合的数量越来越多，随着参数不断的更新，损失会慢慢地下降，最后趋向收敛。但是不幸的是，在训练循环神经网络的时候，有时候会看到绿色这条线。如果第一次训练循环神经网络，绿色学习曲线非常剧烈的抖动，然后抖到某个地方，我们会觉得这程序有 bug。

如图 5.30 所示，RNN 的误差表面是总损失的变化是非常陡峭的或崎岖的。误差表面有一些地方非常平坦，一些地方非常陡峭。纵轴是总损失，x 和 y 轴代表是两个参数。这样会造成什么样的问题呢？假设我们从橙色的点当做初始点，用梯度下降开始调整参数，更新参数，可能会跳过一个悬崖，这时候损失会突然爆长，损失会非常上下剧烈的震荡。有时候我们可能会遇到更惨的状况，就是以正好我们一脚踩到这个悬崖上，会发生这样的事情，因为在悬崖上的梯度很大，之前的梯度会很小，所以措手不及，因为之前梯度很小，所以可能把学习率调的比较大。很大的梯度乘上很大的学习率结果参数就更新很多，整个参数就飞出去了。裁剪（clipping）可以解决该问题，当梯度大于某一个阈值的时候，不要让它超过那个阈值，当梯度大于 15 时，让梯度等于 15 结束。因为梯度不会太大，所以我们要做裁剪的时候，就算是踩着这个悬崖上，也不飞出来，会飞到一个比较近的地方，这样还可以继续做 RNN 的训练。

![](images/bfe681568ed153953726396b9520b292a50428cbf2641731f183f5a7a2fe88b5.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    subgraph Layer1
        A["ct-1"] --> B["×"]
        B --> C["+"]
        C --> D["×"]
        D --> E["xt"]
        E --> F["ct-1"]
    end

    subgraph Layer2
        G["ct-1"] --> H["×"]
        H --> I["+"]
        I --> J["×"]
        J --> K["ct-1"]
    end

    subgraph Layer3
        L["ct-1"] --> M["×"]
        M --> N["+"]
        N --> O["×"]
        O --> P["ct-1"]
    end

    subgraph Layer4
        Q["ct-1"] --> R["×"]
        R --> S["+"]
        S --> T["×"]
        T --> U["ct-1"]
    end

    subgraph Layer5
        V["ct-1"] --> W["×"]
        W --> X["+"]
        X --> Y["×"]
        Y --> Z["ct-1"]
    end

    subgraph Layer6
        AA["ct-1"] --> AB["×"]
        AB --> AC["+"]
        AC --> AD["×"]
        AD --> AE["ct-1"]
    end

    subgraph Layer7
        AF["ct-1"] --> AG["×"]
        AG --> AH["+"]
        AH --> AI["×"]
        AI --> AJ["ct-1"]
    end

    subgraph Layer8
        AK["ct-1"] --> AL["×"]
        AL --> AM["+"]
        AM --> AN["×"]
        AN --> AO["ct-1"]
    end

    subgraph Layer9
        AP["ct-1"] --> AQ["×"]
        AQ --> AR["+"]
        AR --> AS["×"]
        AS --> AT["ct-1"]
    end

    subgraph Layer10
        AU["ct-1"] --> AV["×"]
        AV --> AW["+"]
        AW --> AX["×"]
        AX --> AY["ct-1"]
    end

    subgraph Layer11
        AZ["ct-1"] --> BA["×"]
        BA --> BB["+"]
        BB --> BC["×"]
        BC --> BD["ct-1"]
    end

    subgraph Layer12
        BE["ct-1"] --> BF["×"]
        BF --> BG["+"]
        BG --> BH["×"]
        BH --> BI["ct-1"]
    end

    subgraph Layer13
        BJ["ct-1"] --> BK["×"]
        BK --> BL["+"]
        BL --> BM["×"]
        BM --> BN["ct-1"]
    end

    subgraph Layer14
        BO["ct-1"] --> BP["×"]
        BP --> BQ["+"]
        BQ --> BR["×"]
        BR --> BS["ct-1"]
    end

    subgraph Layer15
        BT["ct-1"] --> BU["×"]
        BU --> BV["+"]
        BV --> BW["×"]
        BW --> BX["ct-1"]
    end

    subgraph Layer16
        BY["ct-1"] --> BZ["×"]
        BZ --> CA["+"]
        CA --> CB["×"]
        CB --> CC["ct-1"]
    end

    subgraph Layer17
        CD["ct-1"] --> CE["×"]
        CE --> CF["+"]
        CF --> CG["×"]
        CG --> CH["ct-1"]
    end

    subgraph Layer18
        CI["ct-1"] --> CJ["×"]
        CJ --> CK["+"]
        CK --> CR["×"]
        CR --> CS["ct-1"]
    end

    subgraph Layer19
        DD["ct-1"] --> DE["×"]
        DE --> DF["+"]
        DF --> DG["×"]
        DG --> DH["ct-1"]
    end

    subgraph Layer20
        DI["ct-1"] --> DJ["×"]
        DJ --> DK["+"]
        DK --> DL["×"]
        DL --> DM["ct-1"]
    end

    subgraph Layer21
        EQ["ct-1"] --> RZ["×"]
        RZ --> SZA["+"]
        SZA --> TX["×"]
        TX --> CU["ct-1"]
    end

    subgraph Layer22
        DV["ct-1"] --> DW["bf_1, zi, zo, xt, xt+1, xt+2, xt+3, xt+4, xt+5, xt+6, xt+7, xt+8, xt+9, xt+10"]

    BZ & AC & AD & AE & AF & AG & AH & AI & AJ & AK & AL & AM & AN & AO & AP & AQ & AR & AS & AT & AU & AV & AW & AX & AY & AZ & BA & BB & BC & BD & BE & BF & BG & BH & BI & BJ & BK & BL & BM & BN & BO & BP & BPB & BBA & BC & BD & BE & BF & BG & BG & BH & BH & BK & BK & BL & BK & BLB & BK & BBA & BBA & BBA & BBA & BBA & BBA & BBA & BBA & BBA & BBA & BBA & BBA & BBA & BBA & BBA & BBA & BBA & BBA & BBA & BBA & BBA & BBA & BBA & BBA & BBA & BBA & BBA & BBA & BBA & BBA & BBA & BBA & BBA & BBA
    style A fill:#f9f,stroke:#333
    style B fill:#ccf,stroke:#333
    style AC fill:#cfc,stroke:#333
    style AD fill:#fcc,stroke:#333
    style AE fill:#cff,stroke:#333
    style AF fill:#ffc,stroke:#333
    style AG fill:#cfc,stroke:#333
    style AH fill:#fcc,stroke:#333
    style AI fill:#ffc,stroke:#333
    style AJ fill:#cfc,stroke:#333
    style AK fill:#fcc,stroke:#333
    style AL fill:#cfc,stroke:#333
    style BC fill:#fcc,stroke:#333
    style BD fill:#cfc,stroke:#333
    style BE fill:#fcc,stroke:#333
    style BF fill:#cfc,stroke:#333
    style BG fill:#fcc,stroke:#333
    style BH fill:#cfc,stroke:#333
    style BI fill:#fcc,stroke:#333
    style BJ fill:#cfc,stroke:#333
    style BK fill:#fcc,stroke:#333
    style BL fill:#cfc,stroke:#333
    style BLB fill:#fcc,stroke:#333
```
</details>

图 5.26 多层 LSTM

之前讲过 ReLU 激活函数的时候，梯度消失（vanishing gradient）来源于 Sigmoid 函数。但 RNN 会有很平滑的误差表面不是来自于梯度消失。把 Sigmoid 函数换成 ReLU，其实在 RNN 性能通常是比较差的，所以激活函数并不是关键点。

有更直观的方法来知道一个梯度的大小，可以把某一个参数做小小的变化，看它对网络输出的变化有多大，就可以测出这个参数的梯度大小，如图 5.31 所示。举一个很简单的例子，只有一个神经元，这个神经元是线性的。输入没有偏置，输入的权重是 1，输出的权重也是 1，转移的权重是 $w _ { \circ }$ 。也就是说从记忆元接到神经元的输入的权重是 $w .$ 。

如图 5.32 所示，假设给神经网络的输入是 $[ 1 , 0 , 0 , 0 ] ^ { \mathrm { T } }$ ，比如神经网络在最后一个时间点（1000 个输出值是 $w ^ { 9 9 9 } )$ ）。假设 w 是要学习的参数，我们想要知道它的梯度，所以是改变 w 的值时候，对神经元的输出有多大的影响。假设 $w = 1 , y _ { 1 0 0 0 } = 1$ ，假设 $w = 1 . 0 1 , y _ { 1 0 0 0 } \approx 2 0 0 0 0$ ，w 有一点小小的变化，会对它的输出影响是非常大的。所以 w 有很大的梯度。有很大的梯度也并没有，把学习率设小一点就好了。但把 w 设为 0.99，那 $y _ { 1 0 0 0 } \approx 0$ 。如果把 w 设为 0.01，$y _ { 1 0 0 0 } \approx 0$ 。也就是说在 1 的这个地方有很大的梯度，但是在 0.99 这个地方就突然变得非常小，这个时候需要一个很大的学习率。设置学习率很麻烦，误差表面很崎岖，梯度是时大时小的，在非常小的区域内，梯度有很多的变化。从这个例子可以看出，RNN 训练的问题其实来自它把同样的东西在转移的时候，在时间按时间的时候，反复使用。所以 $w$ 只要一有变化，它完全由可能没有造成任何影响，一旦造成影响，影响很大，梯度会很大或很小。所以 RNN 不好训练的原因不是来自激活函数而是来自于它有时间序列同样的权重在不同的时间点被反复的使用。

![](images/1946c4cfe36e31ddac402a7219b1f926a4dd1806f86d554d8cab56e02571db6d.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    A["0 1 0"] --> B["y1"]
    B --> C["a1"]
    C --> D["a1"]
    D --> E["x1"]
    E --> F["x2"]
    F --> G["x3"]
    G --> H["other"]
    I["0 1 0"] --> J["y2"]
    J --> K["a2"]
    K --> L["a2"]
    L --> M["x3"]
    M --> N["other"]
    O["0 1 0"] --> P["y3"]
    P --> Q["a3"]
    Q --> R["x3"]
    R --> S["other"]
    T["0 1 0"] --> U["y3"]
    U --> V["a3"]
    V --> W["x3"]
    W --> X["other"]
    Y["0 1 0"] --> Z["y3"]
    Z --> AA["a3"]
    AA --> AB["x3"]
    AB --> AC["other"]
    AD["0 1 0"] --> AE["y3"]
    AE --> AF["a3"]
    AF --> AG["x3"]
    AG --> AH["other"]
    AI["0 1 0"] --> AJ["y3"]
    AJ --> AK["a3"]
    AK --> AL["x3"]
    AL --> AM["other"]
    AN["0 1 0"] --> AO["y3"]
    AO --> AP["a3"]
    AP --> AQ["x3"]
    AQ --> AR["other"]
    AS["0 1 0"] --> AT["y3"]
    AT --> AU["a3"]
    AU --> AV["x3"]
    AV --> AW["other"]
    AX["0 1 0"] --> AY["y3"]
    AY --> AZ["a3"]
    AZ --> BA["x3"]
    BA --> BB["other"]
    BC["0 1 0"] --> BD["y3"]
    BD --> BE["a3"]
    BE --> BF["x3"]
    BF --> BG["other"]
    BH["0 1 0"] --> BI["y3"]
    BI --> BJ["a3"]
    BJ --> BK["x3"]
    BK --> BL["other"]
```
</details>

图 5.27 RNN 计算损失示意

![](images/0e93a74ecaee315473a737441161730655ad44acccc03f3d40e4babbd5d36bfd.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    subgraph Input Layer
        a1["a₁"] -->|w ← w - η∂L / ∂w| x1["x₁"]
        a2["a₂"] -->|w ← w - η∂L / ∂w| x1
        a1 -->|复制| y1["y₁"]
        a2 -->|复制| y2["y₂"]
    end
    subgraph Hidden Layer
        h1["∫"] --> x1
        h2["∫"] --> x2["x₂"]
    end
    style Input Layer fill:#f9f,stroke:#333
    style Hidden Layer fill:#bbf,stroke:#333
    style Output Layer fill:#dfd,stroke:#333
```
</details>

图 5.28 随时间反向传播

# 5.7 如何解决 RNN 梯度消失或者爆炸

有什么样的技巧可以解决这个问题呢？广泛被使用的技巧是 LSTM，LSTM 可以让误差表面不要那么崎岖。它会把那些平坦的地方拿掉，解决梯度消失的问题，不会解决梯度爆炸（gradient exploding）的问题。有些地方还是非常的崎岖的，有些地方仍然是变化非常剧烈的，但是不会有特别平坦的地方。如果做 LSTM 时，大部分地方变化的很剧烈，所以做 LSTM的时候，可以把学习率设置的小一点，保证在学习率很小的情况下进行训练。

![](images/d5cfd2caf57dd700e27fb2ceff25b0dbf5d1e8ffab296cc679520a4353ed1fd2.jpg)

<details>
<summary>line</summary>

| 回合 | 总损失 (有时候) | 总损失 (幸运) |
| ---- | --------------- | ------------- |
| 1    | ~0.8            | ~0.6          |
| 2    | ~0.7            | ~0.5          |
| 3    | ~0.6            | ~0.4          |
| 4    | ~0.5            | ~0.3          |
| 5    | ~1.0            | ~0.2          |
| 6    | ~0.8            | ~0.1          |
| 7    | ~1.0            | ~0.1          |
| 8    | ~0.7            | ~0.1          |
| 9    | ~0.5            | ~0.1          |
| 10   | ~0.4            | ~0.1          |
| 11   | ~0.5            | ~0.1          |
| 12   | ~1.0            | ~0.1          |
| 13   | ~0.5            | ~0.1          |
| 14   | ~1.0            | ~0.1          |
| 15   | ~0.5            | ~0.1          |
| 16   | ~0.5            | ~0.1          |
| 17   | ~0.5            | ~0.1          |
| 18   | ~0.5            | ~0.1          |
| 19   | ~0.5            | ~0.1          |
| 20   | ~0.5            | ~0.1          |
| 21   | ~0.5            | ~0.1          |
| 22   | ~0.5            | ~0.1          |
| 23   | ~0.5            | ~0.1          |
</details>

图 5.29 训练 RNN 时的学习曲线  
![](images/7dbcbb711743a78fe7445833ccbd7f30856d05d9847247892d09feae259d334e.jpg)

<details>
<summary>other</summary>

| W1    | W2    | 总损失 |
|-------|-------|--------|
| -2.8  | 4.6   | 0.35   |
| -2.6  | 4.8   | 0.30   |
| -2.4  | 5.0   | 0.25   |
| -2.2  | 5.2   | 0.20   |
| -2.0  | 5.4   | 0.15   |
</details>

图 5.30 RNN 训练中的裁剪技巧

Q: 为什么 LSTM 可以解决梯度消失的问题，可以避免梯度特别小呢？为什么把 RNN换成 LSTM？。

A：LSTM 可以处理梯度消失的问题。用这边的式子回答看看。RNN 跟 LSTM 在面对记忆元的时候，它处理的操作其实是不一样的。在 RNN 里面，在每一个时间点，神经元的输出都要记忆元里面去，记忆元里面的值都是会被覆盖掉。但是在 LSTM 里面不一样，它是把原来记忆元里面的值乘上一个值再把输入的值加起来放到单元里面。所以它的记忆和输入是相加的。LSTM 和 RNN 不同的是，如果权重可以影响到记忆元里面的值，一旦发生影响会永远都存在。而 RNN 在每个时间点的值都会被格式化掉，所以只要这个影响被格式化掉它就消失了。但是在 LSTM 里面，一旦对记忆元造成影响，影响一直会被留着，除非遗忘门要把记忆元的值洗掉。不然记忆元一旦有改变，只会把新的东西加进来，不会把原来的值洗掉，所以它不会有梯度消失的问题。

![](images/4f8e2065532c1448658d078d0481fdba1a6beeea69ee257dfd7e1a0515711d2f.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph LR
    A["w = 1"] --> B["y¹⁰⁰⁰ = 1"]
    C["w = 1.01"] --> D["y¹⁰⁰⁰ ≈ 20000"]
    E["w = 0.99"] --> F["y¹⁰⁰⁰ ≈ 0"]
    G["w = 0.01"] --> H["y¹⁰⁰⁰ ≈ 0"]
    I["较大的学习率?"] --> J["较小的学习率?"]
    K["较小的学习率"] --> L["较大的学习率"]
```
</details>

图 5.31 参数变化对网络输出的影响

![](images/c361c63af400c5d3c11277a7302247843a6753e0aadd7d3e6153b893e65136b7.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph LR
    A["Node 1"] -->|w| B["Node 2"]
    B -->|w| C["Node 3"]
    C -->|w| D["Node 4"]
    D -->|w| E["Node 5"]
    E -->|w| F["Node 6"]
    style A fill:#f9f,stroke:#333
    style B fill:#f9f,stroke:#333
    style C fill:#f9f,stroke:#333
    style D fill:#f9f,stroke:#333
    style E fill:#f9f,stroke:#333
    style F fill:#f9f,stroke:#333
    note right of B "w=1"
    note right of C "w=999"
    note right of D "w=1000"
    note right of E "w=1000"
    note right of F "w=1000"
    note left of A "y1"
    note right of F "y1000"
```
</details>

图 5.32 RNN 难以训练的原因

遗忘门可能会把记忆元的值洗掉。其实 LSTM 的第一个版本其实就是为了解决梯度消失的问题，所以它是没有遗忘门，遗忘门是后来才加上去的。甚至有个传言是：在训练 LSTM的时候，要给遗忘门特别大的偏置，确保遗忘门在多数的情况下都是开启的，只要少数的情况是关闭的。

有另外一个版本用门操控记忆元，叫做 GRU，LSTM 有三个门，而 GRU 有两个门，所以 GRU 需要的参数是比较少的。因为它需要的参数量比较少，所以它在训练的时候是比较鲁棒的。如果训练 LSTM 的时候，过拟合的情况很严重，可以试下 GRU。GRU 的精神就是：旧的不去，新的不来。它会把输入门跟遗忘门联动起来，也就是说当输入门打开的时候，遗忘门会自动的关闭 (格式化存在记忆元里面的值)，当遗忘门没有要格式化里面的值，输入门就会被关起来。也就是要把记忆元里面的值清掉，才能把新的值放进来。

其实还有其他技术可以处理梯度消失的问题。比如顺时针循环神经网络（clockwise RNN）[1] 或结构约束的循环网络（Structurally Constrained Recurrent Network，SCRN）[2] 等等。

论文“A Simple Way to Initialize Recurrent Networks of Rectified Linear Units”[3] 采用了不同的做法。一般的 RNN 用单位矩阵（identity matrix）来初始化转移权重和 ReLU 激活函数可以得到很好的性能。刚才不是说用 ReLU 的性能会比较呀，如果用一般训练的方法随机初始化权重，ReLU 跟 sigmoid 函数来比的话，sigmoid 性能会比较好。但是使用了单位矩阵，这时候用 ReLU 性能会比较好。

# 5.8 RNN 其他应用

槽填充的例子中假设输入跟输出的数量是一样的，也就是说输入有几个单词，我们就给每一个单词槽标签，RNN 可以做到更复杂的事情。

# 5.8.1 多对一序列

比如输入是一个序列，输出是一个向量。情感分析（sentiment analysis）是典型的应用，如图 5.33 所示，某家公司想要知道，他们的产品在网上的评价是正面的还是负面的。他们可能会写一个爬虫，把跟他们产品有关的文章都爬下来。那这一篇一篇的看太累了，所以可以用一个机器学习的方法学习一个分类器（classifier）来判断文档的正、负面。或者在电影上，情感分析就是给机器看很多的文章，机器要自动判断哪些文章是正类，哪些文章是负类。

机器可以学习一个循环神经网络，输入是字符序列，循环神经网络把这个序列读过一遍。在最后一个时间点，把隐藏层拿出来，在通过几个变换，就可以得到最后的情感分析。

情感分析是一个分类问题，但是因为输入是序列，所以用 RNN 来处理。

![](images/799cd3ecf49ee663b17b240c23423726b9fc784c0b881a3121df655d84782c46.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph LR
    A["正面"] --> B["视觉"]
    B --> C["......"]
    C --> D["正面"]
    D --> E["视觉"]
    E --> F["......"]
    F --> G["正面"]
    G --> H["视觉"]
    H --> I["......"]
    I --> J["正面"]
    J --> K["视觉"]
    K --> L["......"]
    L --> M["正面"]
    M --> N["视觉"]
    N --> O["......"]
    O --> P["正面"]
    P --> Q["视觉"]
    Q --> R["......"]
    R --> S["正面"]
    S --> T["视觉"]
    T --> U["......"]
    U --> V["正面"]
    V --> W["视觉"]
    W --> X["......"]
    X --> Y["正面"]
    Y --> Z["视觉"]
    Z --> AA["......"]
    AA --> AB["正面"]
    AB --> AC["视觉"]
    AC --> AD["......"]
    AD --> AE["正面"]
    AE --> AF["视觉"]
    AF --> AG["......"]
    AG --> AH["正面"]
    AH --> AI["视觉"]
    AI --> AJ["......"]
    AJ --> AK["正面"]
    AK --> AL["视觉"]
    AL --> AM["......"]
    AM --> AN["正面"]
    AN --> AO["视觉"]
    AO --> AP["......"]
    AP --> AQ["正面"]
    AQ --> AR["视觉"]
    AR --> AS["......"]
    AS --> AT["正面"]
    AT --> AU["视觉"]
    AU --> AV["......"]
    AV --> AW["正面"]
    AW --> AX["视觉"]
    AX --> AY["......"]
    AY --> AZ["正面"]
    AZ --> BA["视觉"]
    BA --> BB["......"]
    BB --> BC["正面"]
    BC --> BD["视觉"]
    BD --> BE["......"]
    BE --> BF["正面"]
    BF --> BG["视觉"]
    BG --> BH["......"]
    BH --> BI["正面"]
    BI --> BJ["视觉"]
    BJ --> BK["......"]
    BK --> BL["正面"]
    BL --> BM["视觉"]
    BM --> BN["......"]
    BN --> BO["正面"]
    BO --> BP["视觉"]
    BP --> BQ["......"]
    BQ --> BR["正面"]
    BR --> BS["视觉"]
    BS --> BT["......"]
    BT --> BU["正面"]
    BU --> BV["视觉"]
    BV --> BW["......"]
    BW --> BX["正面"]
    BX --> BY["视觉"]
    BY --> BZ["......"]
    BZ --> CA["正面"]
    CA --> CB["视觉"]
    CB --> CC["......"]
    CC --> CD["正面"]
    CD --> CE["视觉"]
    CE --> CF["......"]
    CF --> CG["正面"]
    CG --> CH["视觉"]
    CH --> CI["......"]
    CI --> CJ["正面"]
    CJ --> CK["视觉"]
    CK --> CR["......"]
    CR --> CS["正面"]
    CS --> CT["视觉"]
    CT --> CU["......"]
    CU --> CV["正面"]
    CV --> CW["视觉"]
    CW --> CX["......"]
    CX --> CY["正面"]
    CY --> CZ["视觉"]
    CZ --> DA["......"]
```
</details>

图 5.33 情感分析示例

用 RNN 来作关键术语抽取（key term extraction）。关键术语抽取意思就是说给机器看一个文章，机器要预测出这篇文章有哪些关键单词。如图 5.34 所示，如果能够收集到一些训练数据 (一些文档，这些文档都有标签，哪些单词是对应的，那就可以直接训练一个 RNN)，那这个 RNN 把文档当做输入，通过嵌入层（embedding layer），用 RNN 把这个文档读过一次，把出现在最后一个时间点的输出拿过来做注意力，可以把这样的信息抽出来再丢到前馈神经网络得到最后的输出。

![](images/9b3795ced3e8f36f89b29e9f810acbbeea4d63814447b6cb11a6e88d7cf451ff.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    A["文档"] --> B["嵌入层"]
    B --> C["隐藏层"]
    C --> D["ΣαiVi"]
    D --> E["输出层"]
    E --> F["关键术语: DNN, LSTN"]
    subgraph 输入层
        G1["V1"] --> H1["V2"] --> I1["V3"] --> J1["V4"] --> K1["..."]
        H1 --> L1["V1"]
        I1 --> M1["V2"]
        J1 --> N1["V3"]
        K1 --> O1["..."]
        L1 --> P1["V1"]
        M1 --> Q1["V2"]
        N1 --> R1["V3"]
        O1 --> S1["V4"]
        P1 --> T1["V1"]
        Q1 --> U1["V2"]
        R1 --> V1["V3"]
        S1 --> W1["V4"]
        T1 --> X1["V1"]
    end
    subgraph 输出层
        Y1["V1"] --> Z1["V2"] --> AA["V3"] --> AB["V4"] --> AC["V1"]
        Z1 --> AD["V2"] --> AE["V3"] --> AF["V4"] --> AG["V1"]
        AA --> AH["V2"] --> AI["V3"] --> AJ["V4"] --> AK["V1"]
        AL["X1"] --> AM["X2"] --> AN["X3"] --> AO["X4"] --> AP["..."]
        AM --> AQ["X1"]
        AN --> AR["X2"]
        AO --> AS["X3"]
        AP --> AT["X4"]
        AR --> AU["X5"]
        AS --> AV["X6"]
        AT --> AW["X7"]
    end
```
</details>

图 5.34 关键术语抽取

# 5.8.2 多对多序列

RNN 也可以处理多对多的问题，比如输入和输出都是序列，但输出序列比输入序列短。如图 5.35 所示，在语音识别这个任务里面输入是声音序列，一句话就是一段声音信号。一般处理声音信号的方式就是在这个声音信号里面，每隔一小段时间，就把它用向量来表示。这个一小段时间是很短的（比如 0.01 秒）。那输出序列是字符序列。

如果是原来的 RNN（槽填充的那个 RNN），把这一串输入丢进去，它充其量只能做到，告诉我们每一个向量对应到哪一个字符。加入说中文的语音识别的话，那输出目标理论上就是这个世界上所有可能中文的单词，常用的可能是八千个，RNN 分类器的数量可能就是八千个。虽然很大，但也是没有办法做的。但是充其量只能做到说：每一个向量属于一个字符。每一个输入对应的时间间隔是很小的（0.01 秒），所以通常是好多个向量对应到同一个字符。所以识别结果为“好好好棒棒棒棒棒”，这不是语音识别的结果。有一招叫做修剪（trimming），即把重复的东西拿掉，就变成“好棒”。这样会有一个严重的问题，因为它没有识别“好棒棒”。

![](images/ff62f6b3ae93bd8cf420d52340bfa88bbb5cc6b11b95013f75f510adf64dab6e.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    A["输入: 向量序列"] --> B["好好棒"]
    B --> C["棒棒"]
    C --> D["棒棒"]
    D --> E["棒棒"]
    E --> F["修剪"]
    style A fill:#f9f,stroke:#333
    style B fill:#ccf,stroke:#333
    style C fill:#ccf,stroke:#333
    style D fill:#ccf,stroke:#333
    style E fill:#ccf,stroke:#333
    style F fill:#ccf,stroke:#333
```
</details>

图 5.35 语音识别示例

需要把“好棒”跟“好棒棒”分开来，怎么办，有一招叫做“CTC”，如图 5.36 所示，在输出时候，不只是输出所有中文的字符，还可以输出一个符号”null”，其代表没有任何东西。所以输入一段声音特征序列，它的输出是“好 null null 棒 null null null null”，然后把“null”的部分拿掉，它就变成“好棒”。如果我们输入另外一个序列，它的输出是“好 null null 棒 null 棒 nullnull”，然后把“null”拿掉，所以它的输出就是“好棒棒”。这样就可以解决叠字的问题了。

![](images/304ed66a7beea7eb0b1eb4a071ec0a3276f099ffb3a220784bf161d07415be37.jpg)

<details>
<summary>text_image</summary>

"好棒"
好 棒 "好棒
棒"
</details>

图 5.36 CTC 技巧

CTC 怎么做训练呢？如图 5.37 所示，CTC 在做训练的时候，手上的训练数据就会告诉我们说，这一串声音特征对应到这一串字符序列，但它不会告诉我们说“好”是对应第几个字符到第几个字符。这时候要穷举所有可能的对齐，简单来说，我们不知道“好”对应到那几个字符，“棒”对应到哪几个字符。假设我们所有的状况都是可能的。可能第一个是“好 null 棒 nullnull null”，可能是“好 null null 棒 null null”，也可能是“好 null null null 棒 null”。假设全部都是对的，一起训练。穷举所有的可能，可能性太多了。

![](images/9a5c250a3f6c34a89c784cbd9d16230cb06fc3d0198cf93fe136f381296c737a.jpg)

<details>
<summary>text_image</summary>

声音特征:
标签: 好棒
好 φ 棒 φ φ φ
好 φ φ 棒 φ φ
好 φ φ φ 棒 φ
...
</details>

图 5.37 CTC 训练

在做英文识别的时候，RNN 输出目标就是字符（英文的字母 + 空白）。直接输出字母，然后如果字和字之间有边界，就自动有空白。如图 5.38 所示，第一帧是输出 H，第二帧是输出 null，第三帧是输出 null，第四帧是输出 I 等等。如果我们看到输出是这样子话，最后把“null”的地方拿掉，这句话的识别结果就是“HIS FRIEND’S”。我们不需要告诉机器说：”HIS”是一个单词，“FRIEND’s”是一个单词, 机器通过训练数据会自己学到这件事情。如果用 CTC来做语音识别，就算是有某一个单词在训练数据中从来没有出现过（比如英文中的人名或地名），机器也是有机会把它识别出来。

![](images/2b47bcfd6955949365af930f2fc1d91e510b5e40db67b49ac72dcf1ed016ba56.jpg)

<details>
<summary>line</summary>

| Label | Value |
|-------|-------|
| H     | 1     |
| φ     | 0     |
| I     | 1     |
| S     | 0     |
| -     | 1     |
| φ     | 0     |
| φ     | 1     |
| φ     | 0     |
| φ     | 1     |
| F     | 1     |
| φ     | 0     |
| R     | 1     |
| I     | 0     |
| φ     | 1     |
| φ     | 0     |
| φ     | 1     |
| E     | 1     |
| N     | 0     |
| D     | 1     |
| φ     | 0     |
| '    | 1     |
| S     | 0     |
</details>

图 5.38 CTC 语音识别示例

# 5.8.3 序列到序列

另一个 RNN 的应用是序列到序列（Sequence-to-Sequence，Seq2Seq）学习，在序列到序列学习里面,RNN 的输入跟输出都是序列 (但是两者的长度是不一样的)。刚在在 CTC时，输入比较长，输出比较短。在这边我们要考虑的是不确定输入跟输出谁比较长谁比较短。比如机器翻译（machine translation），输入英文单词序列把它翻译成中文的字符序列。英文和中文序列的长短是未知的。

假如输入机器学习，然后用 RNN 读过去，然后在最后一个时间点，这个记忆元里面就存了所有输入序列的信息，如图 5.39 所示。

接下来，我们让机器吐一个字符（“机”），就让它输出下一个字符，把之前的输出出来的字符当做输入，再把记忆元里面的值读进来，它就会输出“器”。那这个“机”怎么接到这个地方呢，有很多支支节节的技巧。在下一个时间输入“器”，输出“学”，然后输出“习”，然后一直输出下去，如图 5.40 所示。

![](images/8ff3ca832535d5f97dabac462f5ba4bdc12b2405b4a922b00071fbb1b24565bc.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    A["机器"] --> B["数据处理模块"]
    C["学习"] --> B
    B --> D["包含输入序列的所有信息"]
```
</details>

图 5.39 记忆元存储所有序列信息

![](images/554b7711c2d3d8094bb6ed7b8e4c674cb928449710b6c28c87b0129656c0cb27.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph LR
    A["机器"] --> B["学习"]
    B --> C["机器"]
    C --> D["学习"]
    D --> E["机器"]
    E --> F["学习"]
    F --> G["机器"]
    G --> H["学习"]
    H --> I["机器"]
    I --> J["学习"]
    J --> K["机器"]
    K --> L["学习"]
    L --> M["机器"]
    M --> N["学习"]
    N --> O["机器"]
    O --> P["学习"]
    P --> Q["机器"]
    Q --> R["学习"]
    R --> S["机器"]
    S --> T["学习"]
    T --> U["机器"]
    U --> V["学习"]
    V --> W["机器"]
    W --> X["学习"]
    X --> Y["机器"]
    Y --> Z["学习"]
    Z --> AA["机器"]
    AA --> AB["学习"]
    AB --> AC["机器"]
    AC --> AD["学习"]
    AD --> AE["机器"]
    AE --> AF["学习"]
    AF --> AG["机器"]
    AG --> AH["学习"]
    AH --> AI["机器"]
    AI --> AJ["学习"]
    AJ --> AK["机器"]
    AK --> AL["学习"]
    AL --> AM["机器"]
    AM --> AN["学习"]
    AN --> AO["机器"]
    AO --> AP["学习"]
    AP --> AQ["机器"]
    AQ --> AR["学习"]
    AR --> AS["机器"]
    AS --> AT["学习"]
    AT --> AU["机器"]
    AU --> AV["学习"]
    AV --> AW["机器"]
    AW --> AX["学习"]
    AX --> AY["机器"]
    AY --> AZ["学习"]
    AZ --> BA["机器"]
    BA --> BB["学习"]
    BB --> BC["机器"]
    BC --> BD["学习"]
    BD --> BE["机器"]
    BE --> BF["学习"]
    BF --> BG["机器"]
    BG --> BH["学习"]
    BH --> BI["机器"]
    BI --> BJ["学习"]
    BJ --> BK["机器"]
    BK --> BL["学习"]
    BL --> BM["机器"]
    BM --> BN["学习"]
    BN --> BO["机器"]
    BO --> BP["学习"]
    BP --> BQ["机器"]
    BQ --> BR["学习"]
    BR --> BS["机器"]
    BS --> BT["学习"]
    BT --> BU["机器"]
    BU --> BV["学习"]
    BV --> BW["机器"]
    BW --> BX["学习"]
    BX --> BY["机器"]
    BY --> BZ["学习"]
    BZ --> CA["机器"]
    CA --> CB["学习"]
    CB --> CC["机器"]
    CC --> CD["学习"]
    CD --> CE["机器"]
    CE --> CF["学习"]
    CF --> CG["机器"]
    CG --> CH["学习"]
    CH --> CI["机器"]
    CI --> CJ["学习"]
    CJ --> CK["机器"]
    CK --> CR["学习"]
    CR --> CS["机器"]
    CS --> CT["学习"]
    CT --> CU["机器"]
    CU --> CV["学习"]
    CV --> CW["机器"]
    CW --> CX["学习"]
    CX --> CY["机器"]
    CY --> CZ["学习"]
```
</details>

图 5.40 RNN 会一直生成字符

要怎么阻止让它产生单词呢？要多加一个符号“断”，所以机器的输出不是只有字符，它还有一个可能输出“断”。如果“习”后面是符号“===”（断）的话，就停下来了，如图 5.41 所示。这是训练的起来的。序列到序列学习，假设做翻译，原来是输入某种语言的文字，翻译成另外一种语言的文字。有没有可能直接输入某种语言的声音信号，输出另外一种语言的文字呢？我们完全不做语音识别。比如把英文翻译成中文，收集一大堆英文的句子，看看它对应的中文翻译。我们完全不要做语音识别，直接把英文的声音信号丢到这个模型里面去，看它能不能输出正确的中文。这一招居然是行得通的。假设要把闽南语转成英文，但是闽南语的语音识别系统不好做，因为闽南语根本就没有标准文字系统。如果训练闽南语转英文语音识别系统的时候，只需要收集闽南语的声音信号跟它的英文翻译就可以了，不需要闽南语语音识别的结果，也不需要知道闽南语的文字。

![](images/35422f71454adefc86f7adee1f7b6dcaec135aaf94cd8e701945c7da1e51f282.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph LR
    A["机器"] --> B["学习"]
    B --> C["机器"]
    C --> D["学习"]
    D --> E["机器"]
    E --> F["学习"]
    F --> G["机器"]
    G --> H["学习"]
    H --> I["机器"]
    I --> J["学习"]
    J --> K["机器"]
    K --> L["学习"]
    L --> M["机器"]
    M --> N["学习"]
    N --> O["机器"]
    O --> P["学习"]
    P --> Q["机器"]
    Q --> R["学习"]
    R --> S["机器"]
    S --> T["学习"]
    T --> U["机器"]
    U --> V["学习"]
    V --> W["机器"]
    W --> X["学习"]
    X --> Y["机器"]
    Y --> Z["学习"]
    Z --> AA["机器"]
    AA --> AB["学习"]
    AB --> AC["机器"]
    AC --> AD["学习"]
    AD --> AE["机器"]
    AE --> AF["学习"]
    AF --> AG["机器"]
    AG --> AH["学习"]
    AH --> AI["机器"]
    AI --> AJ["学习"]
    AJ --> AK["机器"]
    AK --> AL["学习"]
    AL --> AM["机器"]
    AM --> AN["学习"]
    AN --> AO["机器"]
    AO --> AP["学习"]
    AP --> AQ["机器"]
    AQ --> AR["学习"]
    AR --> AS["机器"]
    AS --> AT["学习"]
    AT --> AU["机器"]
    AU --> AV["学习"]
    AV --> AW["机器"]
    AW --> AX["学习"]
    AX --> AY["机器"]
```
</details>

图 5.41 添加截止符号

序列到序列的技术也被用到句法解析（syntactic parsing）。句法解析，让机器看一个句子，得到句子结构树。如图 5.42 所示，只要把树状图描述成一个序列，比如：“John has a dog.”，序列到序列学习直接学习一个序列到序列模型，其输出直接就是句法解析树，这个是可以训练的起来的。LSTM 的输出的序列也是符合文法结构，左、右括号都有。

![](images/6ee2483ad4149058d704ee143bbf92fe9f524050a1b6c32fd455dec3b78f63b3.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph TD
    A["John has a dog."] --> B["NP"]
    A --> C["VP"]
    B --> D["NNP"]
    B --> E["john"]
    C --> F["VBZ"]
    C --> G["has"]
    C --> H["DP"]
    H --> I["DT"]
    H --> J["NN"]
    K["a"] --> L["dog"]
    M["(S (NP NNP)NP (VP VBZ (NP DT NN)NP)VP.)S"] --> L
```
</details>

图 5.42 句法解析示例

要将一个文档表示成一个向量，如图 5.43 所示，往往会用词袋（Bag-of-Words，BoW）的方法，用这个方法的时候，往往会忽略掉单词顺序信息。举例来说，有一个单词序列是“whiteblood cells destroying an infection”，另外一个单词序列是：“an infection destroying white bloodcells”，这两句话的意思完全是相反的。但是我们用词袋的方法来描述的话，他们的词袋完全是一样的。它们里面有完全一摸一样的六个单词，因为单词的顺序是不一样的，所以他们的意思一个变成正面的，一个变成负面的，他们的意思是很不一样的。

可以用序列到序列自编码器这种做法来考虑单词序列顺序的情况下，把一个文档变成一个向量。

![](images/46bfc813be94b30af5891e6376c6d69e2dac0ac1b27d73eee457f52812cb94b5.jpg)

<details>
<summary>flowchart</summary>

```mermaid
graph LR
    A["white blood cells destroying an infection"] --> B["正面"]
    C["an infection destroying white blood cells"] --> D["负面"]
```
</details>

图 5.43 文档转成向量示例

# 参考文献

[1] KOUTNIK J, GREFF K, GOMEZ F, et al. A clockwork rnn[C]//International conference on machine learning. PMLR, 2014: 1863-1871.   
[2] MIKOLOV T, JOULIN A, CHOPRA S, et al. Learning longer memory in recurrent neural networks[C]//ICLR. 2015.   
[3] LE Q V, JAITLY N, HINTON G E. A simple way to initialize recurrent networks of rectified linear units[J]. arXiv preprint arXiv:1504.00941, 2015.