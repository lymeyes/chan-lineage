# 禅宗法脉资料库 · 严谨化方法学（METHODOLOGY）

> 本文件定义本项目的**证据等级、核验流程与正典典籍目录**，是所有祖师卡内容可信度的统一标尺。
> 目的：让每一张卡片的"出自哪里、核验到哪一步"都**可核验、可复现、不杜撰**。

---

## 1. 内容可信度三档（status）

| 档位 | 含义 | 进入条件 |
|---|---|---|
| `core` | 已对照 CBETA 电子佛典**逐字校核**正文 | Phase R2 完成后由 `draft` 晋升 |
| `draft` | 内容据正典灯录整理，**已锚定到具体典籍 work 级**（其中 5 张 `sourced` 已据《五灯会元》原文摘录），正文未逐字校核 | 当前 108 张均在此档 |
| `named_only` | 仅列名（姓名/法系/师承可从谱系推导），**无任何生平或公案内容** | 诚实占位，绝不为无据者编造事迹 |

> 诚实底线：凡谱系中"有名无事迹"的节点，一律 `named_only`，**宁缺毋滥，绝不杜撰**。

---

## 2. 证据等级（evidence）与核验状态（verify_status）

每张 `draft`/`core` 卡额外带两个透明字段：

- `evidence`
  - `primary` —— 内容源自**前代禅宗正典**（灯录、语录、坛经等一手文献），非现代二手摘编。
  - `secondary` —— 内容取自现代综述/百科，无具体前代典籍锚点（本项目默认 `primary`）。
- `verify_status`
  - `sourced` —— 已**据正典原文摘录具体生平/语录**（如《五灯会元》文句），并标注卷次与出处，但**尚未对照 CBETA/卍续藏 X 部逐字对校**。比 `anchor_only` 多一步"有可溯原文"，是 `anchor_only` 与 `line_verified` 之间的中间态。
  - `anchor_only` —— 已锚定到典籍 **work 级**（含 CBETA 目录号），但**无具体正文摘录**，卷次/字句待校。
  - `line_verified` —— 已对照 CBETA/卍续藏逐字核对（当前暂无，待 Phase R2）。

**当前状态**：共 108 张 `draft` 卡，均为 `evidence: primary`。其中 **5 张为 `sourced`**（报慈从瑰、幻堂中仁、双溪印、祐圣法居、煮山宁，内容据《五灯会元》原文核校）；其余 103 张为 `anchor_only`。
即：内容引自正典、可信来源明确，但卷次与字句待逐字校核——这一限制已在每张卡上显式标注，不夸大。

---

## 3. 正典典籍目录（CBETA 编号 · 可独立核验）

下列为本项目引用的一手文献及其 **CBETA 目录编号**（大正藏 `T` / 卍续藏 `X`）。
编号属固定目录事实，可在 CBETA 官网检索核验；卷次除个别高度确信者外统一标"待核"，**不编造卷次**。

| 典籍 | CBETA 编号 | 编者/作者 | 备注 |
|---|---|---|---|
| 景德传灯录 | **T51n2076** | 道原（北宋） | 本项目最主要的一手谱系/语录源 |
| 五灯会元 | X（卍续藏，编号待核） | 普济（南宋） | 汇辑五部灯录；CBETA 未入大正藏 |
| 碧岩录 | **T48n2003** | 圜悟克勤 | 公案评唱 |
| 从容录 | **T48n2004** | 万松行秀 | 公案评唱 |
| 古尊宿语录 | **T47n1991** | 赜藏主 编 | 临济、沩仰等尊宿语录汇集 |
| 镇州临济慧照禅师语录（临济录） | **T47n1985** | 临济义玄 | 临济宗根本语录 |
| 黄檗山断际禅师传心法要 | **T48n2012** | 黄檗希运 | 心法要门 |
| 六祖大师法宝坛经 | **T48n2007**（宗宝本） | 惠能 | 另有契嵩本 T48n2008 等 |
| 宗镜录 | **T48n2016** | 永明延寿 | 禅教合一巨著 |
| 信心铭 | **T48n2010** | （传统归 僧璨，作者有争议） | |
| 参同契 | **T48n2011** | 石头希迁 | |
| 传法正宗记 | **T51n2078** | 契嵩 | 宗派传承史辩 |
| 佛祖历代通载 | **T49n2036** | 念常 | 编年佛教史 |
| 释氏稽古略 | **T49n2037** | 觉岸 | 编年佛教史 |
| 祖堂集 | **未入 CBETA**（朝鲜版·高丽藏系统） | 静、筠（南唐） | 最古灯录之一，需另寻版本 |
| 禅源诸诠集都序 | **T48n2015** | 宗密 | |
| 顿悟入道要门论 | **T48n2014** | 大珠慧海 | |

---

## 3.1 语料落盘与逐字校核流水线（Phase R2·c 起）

官方全文经 SSH sparse-checkout 从 `cbeta-org/xml-p5` 取单部，不入库（授权 + 体积），落 `.cache/xml-p5/`：

```bash
git clone --filter=blob:none --no-checkout --depth 1 git@github.com:cbeta-org/xml-p5.git .cache/xml-p5
cd .cache/xml-p5 && git sparse-checkout init --no-cone
git sparse-checkout set 'T/T51/T51n2076.xml' 'T/T51/T51n2077.xml' 'T/T47/T47n1985.xml' \
  'X/X80/X80n1565.xml' 'X/X68/X68n1315.xml' 'X/X78/X78n1556.xml' 'X/X79/X79n1559.xml'
git checkout master && cd ../.. && python3 tools/extract_cbeta.py && python3 tools/cbeta_check.py
```

**已入库语料的准确坐标（实测校订，勿凭记忆写编号）**

| 文献 | CBETA 编号 | 校订要点 |
|---|---|---|
| 景德傳燈錄 | T51n2076 | 30 卷，禅宗谱系主干 |
| 續傳燈錄 | T51n2077 | 非《五灯会元》，二者常被混淆 |
| 五燈會元 | **X80n1565** | 卍续藏，不在大正藏；20 卷 |
| 古尊宿語錄 | **X68n1315** | 非 T47n1991（后者实为《金陵清凉院文益禅师语录》） |
| 建中靖國續燈錄 | **X78n1556** | 非 X77n1524（后者实为《补续高僧传》） |
| 嘉泰普燈錄 | X79n1559 | 另有总目录 X79n1558 |
| 鎮州臨濟慧照禪師語錄 | T47n1985 | 临济录 |

**比对规则（避免两类系统性误判）**

1. **gaps 容错**：CBETA 对未编码 rare 字使用 `<g ref="#CBxxxxx">`（内容为私用区字符，如 `法<g ref="#CB05287">󱒧</g>宗一`）。比对前两侧统一剔除私用区/增补平面字符，否则「法瑫宗一」永远匹配不到。
2. **滑窗取样**：经文一行仅约 12–16 字，长窗口易跨行。语句取首/中/尾三处起点，窗口长度 12→9→6 逐级回退。
3. **短键上下文校验**：法名尾 2 字作检索键时，命中行必须含「禪師/和尚/首座/大師/法嗣」等称谓，否则判为假阳性（如「法居」误撞「受衣法。居嶺南」）。

**分级定义**

- **A 双证**：至少 1 条语句在目标经文逐字命中，且人名在同经定位 → 可升 `sourced`，逐字复核后可升 `line_verified`。
- **B 单证**：仅语句命中或仅人名定位（或命中落在非目标经文）→ 保留 `draft`，需人工核卷次/异体字。
- **C 未命中**：需排查卷次错、异体字、缺字 gap 或卡片语句系转述而非原文。

> 当前基线（2026-10-29）：110 张 draft 卡 → **A 52 / B 58 / C 0**。报告留证于 `reports/cbeta_check_<date>.{md,json}`。

## 4. 引用字段规范（卡片 YAML）

每张卡顶部字段含义：

```yaml
id: 临济玄禅师          # 必须 == data/lineage.json 节点 id
name: 临济义玄
honorific: 临济义玄禅师 · 慧照禅师（谥）
school: 临济宗
dynasty: 唐
region: 镇州临济院
teacher: 黄檗希运
source_ref: 五灯会元·卷十一·临济义玄 / 镇州临济慧照禅师语录（临济录）
cbeta: T47n1985（临济慧照禅师语录）   # 可核验的 CBETA 编号
evidence: primary
verify_status: anchor_only
status: draft
verify: 待 CBETA 逐字校对《临济录》。
bio: |
  …（内容据上述正典整理）…
sayings:
- text: "…公案原文…"
  ref: 临济录·四料简        # 与该卡 source_ref 对应的具体出处
```

`sayings[].ref` 指向具体公案/语录出处；`source_ref`/`cbeta` 指向整卡的一手文献锚点。

---

## 5. 已知限制与后续路线（Phase R2）

- **当前环境无法抓取 CBETA 全文**：`api.cbetaonline` 子域被代理拦截、`cbetaonline.dila.edu.tw` 主站为 SPA 无可用取文接口、Wikisource 超时、`ctext` 需鉴权。
  故 `verify_status` 统一为 `anchor_only`，**卷次/字句未逐字校核**。
- **Phase R2（逐字校核）前置条件**：在可访问 CBETA 语料（官网下载包 / 本地镜像 / 有访问权的主机）的环境中，
  按 `cbeta` 编号 + 祖师名定位原文，逐字比对 `bio`/`sayings[].text`，无误者升 `status: core` + `verify_status: line_verified`；
  发现出入者修正并标注修订。
- **不追求"看起来完整"**：`named_only` 占位卡（1873 张）将持续保留，直到在 CBETA 中找到该人确有言行记载、再升 `draft`/`core`。

---

## 6. 工具链

| 脚本 | 作用 |
|---|---|
| `tools/gen_stubs.py` | 为所有"尚无卡"的节点生成 `named_only` 诚实占位 |
| `tools/gen_phase4.py` / `gen_phase5.py` | 临济主脉 / 各宗派骨干升格为 `draft` |
| `tools/upgrade_citations.py` | 补齐缺锚点卡的 `source_ref`/`cbeta`，并加 `evidence`/`verify_status`（Phase R1） |
| `tools/build_site.py` | 由 lineage.json + YAML 生成自包含 `site/index.html` |
| `tools/clean_ids.py` | 剥离节点 id 中分支图抽取残留的 `**` 分隔符（如 `L::洛京黑**涧**和尚`→`L::洛京黑涧和尚`），同步 tree/parent 引用与 YAML 文件名 |
| `tools/fix_garbled_names.py` | 修复 CJK 部首拆解记号（IDS）残留的乱码节点名，并据《五灯会元》原文升 5 张卡为 `sourced` |
| `tools/fix_mojibake.py` | 修正字体缺字映射错误导致的 Unicode 乱码（`U+24986`→`瑫`、`U+255FF`→`裕`），并统一 YAML 内部 id/name == 文件名 == 节点 id（对账器） |
| `tools/audit_integrity.py` | 数据完整性回归守卫：id 唯一 / parent 完整无环 / 无乱码 / tree==flat / 节点↔卡 100% 对应；全过才退出 0 |
| `tools/extract_cbeta.py` | 从 CBETA XML P5（`.cache/xml-p5` sparse checkout）抽取带行锚点的纯文本到 `sources/*.txt`，锚点格式 `T51n2076_p0377a20`；兼容 T/X 两藏属性顺序差异 |
| `tools/cbeta_check.py` | 逐字校核器：简繁归一（zhconv）+ 去标点/缺字 gap 后做「人名定位 + 语句多点滑窗比对」，输出 A 双证 / B 单证 / C 未命中分级报告到 `reports/` |
