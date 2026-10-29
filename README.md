# 禅宗法脉 · 交互谱系与祖师资料库（chan-lineage）

把一张禅宗传承关系图，升级为**可溯源、可引用**的祖师资料库：点开谱系中任一节点，
即可看到其生平、师承、代表公案 / 语录，并标注精确出处（哪部灯录·第几卷·哪则）。

> 设计目标：图是骨架，引文与生平是血肉。所有内容**可溯源、可校核**，绝不杜撰。

## 许可（License）

- 本仓库采用 **Creative Commons Attribution 4.0 International（CC BY 4.0）**，见 [`LICENSE`](LICENSE)。
  该许可最适合「以公版古籍为底本、经结构化与注释的知识资源」：要求署名、允许再创作与商用，
  契合「援引 CBETA / 灯录须注明来源」的学术伦理。
- 古籍文本本身属公版；CBETA 电子佛典数字化版本依其授权（CC）**转载并醒目署名来源**。
- 仓库内的生成脚本（`tools/`）为极轻量辅助代码，同样以 CC BY 4.0 提供。

## 数据来源与学术诚信

- **底本**：《景德传灯录》《五灯会元》《祖堂集》《联灯会要》《五灯全书》；数字化参考 CBETA 电子佛典。
- **铁律**：每条引文（公案 / 语录 / 偈颂）必须来自权威底本并填 `ref`；**不得杜撰**生平或公案。
  灯录未载者留空或标 `status: named_only`。
- **校对工作流**：默认 `status: draft`（已据灯录填实，待逐字比对 CBETA），校核无误后升 `core`。
  凡存疑记载（如「拈花微笑」之史源性），在 `bio` / `verify` 中显式说明，不混入定论。

## 目录结构

```
chan-lineage/
├── LICENSE                # CC BY 4.0
├── README.md              # 本文件
├── data/
│   ├── lineage.json       # 结构化谱系（tree 嵌套 + nodes 扁平 + meta），1977 节点 / 最大 23 世
│   ├── schema.md          # 祖师 YAML 字段定义与诚信规则
│   ├── METHODOLOGY.md     # 严谨化方法学：证据等级/核验流程/正典 CBETA 目录
│   └── patriarchs/        # 每位祖师一份 <id>.yaml（生平/引文/出处）
├── sources/               # CBETA 抽取文本（不入库，`tools/extract_cbeta.py` 重建）
├── reports/               # 校核报告（cbeta_check_*.md/json，入库留证）
├── site/
│   └── index.html         # 自包含交互站点（数据内嵌，双击即可打开，无需服务器）
│                          # 注：Obsidian 离线库里的「站点/index.html」是另一套宣纸风版式，
│                          #     由 tools/offline_generate.py 生成；两者数据同源、版式不同，勿当同一文件
└── tools/
    ├── extract_lineage.py     # 从分支图 HTML 抽取 → data/lineage.json
    ├── build_site.py         # 从 lineage.json + YAML → site/index.html
    ├── gen_core_patriarchs.py# 生成「核心脊柱」祖师卡（批量，据灯录）
    ├── gen_patriarchs_phase2.py# 生成「阶段二」扩展祖师卡（临济主脉+云门/法眼/青原系，据灯录）
    ├── gen_patriarchs_song.py  # 生成「阶段三」卡（宋以后巨匠 + 黄龙/虎丘支派关键人物）
    ├── gen_phase4.py           # 升格临济宗主脉核心祖师（三圣慧然/定上座/灌谿等 16 人）为 draft
    ├── gen_phase5.py           # 升格各宗派骨干祖师（云门/法眼/曹洞/沩仰/青原系等 29 人）为 draft
    └── gen_stubs.py            # 为所有「尚未有卡」的节点生成 named_only 结构占位卡
    └── upgrade_citations.py    # (Phase R1) 补文献锚点 + evidence/verify_status 透明字段
    ├── fix_garbled_names.py    # (Phase R2·a) 修复分支图 IDS 乱码名 + 5 卡升 sourced（据五灯会元核校）
    ├── clean_ids.py            # (Phase R2·a) 剥离 id 中分支图残留的 ** 分隔符并同步 tree/parent/YAML 名
    ├── fix_mojibake.py         # (Phase R2·b) Unicode 缺字乱码订正 + YAML 内部 id/name 对账器
    ├── audit_integrity.py      # 数据完整性回归守卫（id 唯一/parent 无环/tree==flat/节点↔卡 100%）
    ├── extract_cbeta.py       # (Phase R2·c) CBETA XML P5 → sources/*.txt（带行锚点纯文本）
    ├── cbeta_check.py         # (Phase R2·c) 逐字校核器：人名定位 + 语句比对，输出 A/B/C 分级报告
    ├── extract_entries.py     # (Phase R2·d) 灯录条目切分：7 部灯录 → 5,520 条「一人一条」结构化条目
    ├── enrich_cards.py        # (Phase R2·d) 条目回填：named_only 空壳 → 有正文的 draft（标 extracted）
    ├── offline_generate.py    # 离线库生成器（Obsidian「宗脉谱系」唯一真源副本，仓库→库自动同步）
    ├── offline_verify.py      # 离线库完整性校验器（9 项断言，依据 站点/MANIFEST.json 聚合指纹）
    └── rebuild_offline.py     # 一键灾备重建：定位/克隆仓库 → 同步工具 → 重建 1976 份 → 校验
```

> 灾备与恢复：见 [`DISASTER_RECOVERY.md`](DISASTER_RECOVERY.md)。离线库被整目录删除时，一条 `python3 tools/rebuild_offline.py` 即可从零恢复并自证完整（已实测空目录→1976 份，聚合指纹逐字节一致）。

## 当前进度

| 项 | 状态 |
|---|---|
| 谱系结构（1977 节点 / 最大 23 世） | ✅ 已抽取至 `data/lineage.json` |
| 交互站点（可折叠树 + 点击看详情 + 搜索 + 展开全部/重置） | ✅ `site/index.html`（数据内嵌，可离线双击打开） |
| 祖师卡 schema | ✅ `data/schema.md`（含 draft→core 校对工作流） |
| 核心脊柱祖师卡（七佛→六祖→南岳/青原→五家七宗开祖 + 赵州/石头/药山/德山/雪峰等） | ✅ **29 份 `status: draft`** |
| 阶段二扩展卡（临济主脉 7 人 + 云门/法眼/青原系 13 人） | ✅ **20 份 `status: draft`**（核心+阶段二 累计 49 份） |
| 阶段三卡（宋以后巨匠 + 黄龙/虎丘支派关键人物） | ✅ **9 份 `status: draft`**：白云守端/圆悟克勤/虎丘绍隆/大慧宗杲/黄龙祖心/死心悟新/灵源惟清/天童华/密庵咸杰；＋1 占位（`黄龙机`，`named_only`） |
| 阶段四升格卡（临济宗主脉核心祖师） | ✅ **16 份 `status: draft`**：三圣慧然/魏府大觉/灌谿闲/定上座/宝寿沼/纸衣道者/桐峰庵主/西院明/守廓侍者/叶县归省/广慧元琏/谷隐聪/神鼎洪諲/浮山法远/杨亿居士/李遵勗居士。**累计 74 份 `draft`** |
| 阶段五升格卡（各宗派骨干祖师：云门/法眼/曹洞/沩仰/青原系等） | ✅ **29 份 `status: draft`**：云居膺/疏山仁/龙牙遁/九峰虔/九峰满/华严静/洞山守初(已含)/德山缘密/百丈恒/清凉泰钦/保福展/鼓山晏(已含)/兴善惟宽/西堂藏(已含)/归宗常/长庆安/巴陵鉴/罗汉琛(已含)/大梅常/庞蕴居士/灵云志勤/无著文喜/径山洪諲/天童华(已含)/香严闲/芙蓉楷/盘山积/盐官安国师/智门祚/章敬怀晖/鹅湖大义/汾州无业/大珠慧海/石巩慧藏/龙湖普闻/佛日契嵩 等（依图谱节点实际命名升格）。**累计 103 份 `draft`** |
| **全量节点覆盖**（1976 个非根节点） | ✅ 1976 份卡与 1976 个非根节点 **100% 对应（0 缺漏 / 0 孤儿）**：其中 **1408 份 `draft`**（含真实生平 + 机缘语：2 份 `line_verified`、3 份 `sourced`、1298 份 `extracted`、103 份 `anchor_only`、2 份无标注）、**568 份 `named_only`**（在所校七部灯录中确无独立条目，含 1 份黄龙派同名异人诚实占位） |
| 西天二十八祖（印度付法血脉） | ⚠️ 图谱中以单一汇总节点呈现，已写综述卡；各祖独立卡待补 |
| 长尾：仅列名者 | ✅ 原 1866 份 `named_only` 占位卡，经 Phase R2·d 语料回填后**降至 568 份**（其余 1298 张已获真实条目内容）。剩余 568 张措辞已改为可辩护表述（「在所校七部灯录中未见独立条目」，非旧版不可证的「未载生平事迹与语录原文」） |
| 杨岐派 house 着色归一（图谱 `杨歧/杨岐` 异体） | ✅ 已修：`杨歧会禅师` 子树 193 节点归一为「杨岐派」；汾阳善昭/石霜楚圆/玄沙备亦归正为临济宗/青原系 |
| 黄龙慧南开祖卡片 id 错位修复 | ✅ 开祖真实节点为 `黄龙南禅师`（已补卡）；原误挂 `黄龙机禅师` 节点（另一人）的旧卡已改为诚实占位（`named_only`），不再误植 |
| **Phase R1 严谨化（证据等级 + 核验状态）** | ✅ 全部 103 份 `draft` 卡补 `evidence: primary` + `verify_status: anchor_only`，45 份缺失者补齐 `source_ref`/`cbeta`（统一用可核验 CBETA 大正藏 T 编号，卷次除个别确信者外标「待核」，不编造）；站点新增「证据等级 / 核验状态」渲染；新增 [`METHODOLOGY.md`](METHODOLOGY.md) 固化证据等级与正典目录。**当时边界：该阶段环境无法抓取 CBETA 全文，故均 `anchor_only`；此限制已于 Phase R2·c 解除** |
| **Phase R2·a（乱码节点名修复 + 5 卡升 `sourced`）** | ✅ 修复 5 个因分支图 CJK 部首拆解记号（IDS）残留的乱码节点名，均经《五灯会元》原文联网核验还原真实法讳：报慈从瑰（后于 R2·c 订正为从瓌）、幻堂中仁、双溪印、祐圣法居、煮山宁（后于 R2·c 订正为𡺸山宁）；并修正 2 处错挂房支（报慈从瑰→法眼宗、煮山宁→云门宗）。该 5 张卡升为 `verify_status: sourced`（已据《五灯会元》原文摘录生平/上堂语，标注卷次出处），为 `anchor_only` 与 `line_verified` 间的中间态。详见 [`METHODOLOGY.md`](METHODOLOGY.md) §2。**draft 累计 103 → 108；named_only 1873 → 1868** |
| **Phase R2·b（Unicode 缺字映射乱码 + YAML 一致性对账）** | ✅ 修正 5 个节点名因字体缺字 / 抽取映射错误导致的 Unicode 乱码：源串 `U+24986`→`瑫`(U+746B)、`U+255FF`→`裕`(U+88D5)，均经《五灯会元》/CBETA 目录/佛学词典联网核验还原真实法讳：国泰瑫、安国瑫、潭州龙兴裕、福州迁宗院行瑫仁慧、杭州倾心寺法瑫宗一；并回写这 5 张卡 YAML 的 `id`/`name` 字段。同时修复 `clean_ids.py` 仅重命名文件、未回写内部 `id` 的遗漏——导致 28 张卡的内部 `id` 仍带 `**` 分隔符、与节点脱节（点击节点看不到卡）；本阶段统一令 **YAML 内部 id/name == 文件名 == 节点 id**，全站节点↔卡 100% 对应（0 孤儿 / 0 缺卡），卡档数量与档位不变（draft 108 / named_only 1868）。脚本见 [`tools/fix_mojibake.py`](tools/fix_mojibake.py) |
| **Phase R2·c（CBETA XML P5 语料管线 + 逐字校核）** | ✅ 打通官方语料管线：经 SSH sparse-checkout 取 [`cbeta-org/xml-p5`](https://github.com/cbeta-org/xml-p5) 中 7 部灯录（景德传灯录 T51n2076 / 续传灯录 T51n2077 / 五灯会元 X80n1565 / 古尊宿语录 X68n1315 / 建中靖国续灯录 X78n1556 / 嘉泰普灯录 X79n1559 / 镇州临济慧照禅师语录 T47n1985），抽取为带 CBETA 行锚点的纯文本（`T51n2076_p0377a20` 规范引用，共 126,914 行）；`tools/cbeta_check.py` 对 110 张 draft 卡做「人名定位 + 语句逐字比对」，结果 **A 双证 52 / B 单证 58 / C 未命中 0**。据此订正 3 处名讳：**从瑰→从瓌**（景录卷二一 p0377a20）、**迁宗院→僊（仙）宗院**、**煮山→𡺸山**（U+21EB8，⿰山耆，音 qí，《字彙》「出《释典》」，与最初分支图 IDS `[山*耆]` 吻合，此前猜作「煮」系误判，已自纠）；5 张卡升级（从瓌/𡺸山宁 `line_verified`，龙兴裕/行瑫仁慧 `sourced`，国泰瑫/安国瑫补 CBETA 定位）。**draft 108 → 110；语料不入库**（CBETA 授权 + 体积），由 `tools/extract_cbeta.py` 一键重建 |
| **Phase R2·d（灯录条目批量回填，`draft` 110 → 1408）** | ✅ 打通「语料→条目→卡片」回填链：[`tools/extract_entries.py`](tools/extract_entries.py) 按「XX禪師XX禪師」双标题定界，以**法名共享后缀 ≥2 字**判定标题对（兼容续传灯录「汾陽善昭禪師汾陽太子院善昭禪師」体例），把 7 部灯录切成 **5,520 条「一人一条」**结构化条目；[`tools/enrich_cards.py`](tools/enrich_cards.py) 按名精确匹配回填，**1,298 张 `named_only` 空壳升级为有正文的 `draft`**。全库机缘语 3,394 条 / **20.8 万字**（原约 0.8 万字）。**同时订正一处系统性错误断言**：旧卡 bio 统一写「《灯录》仅列其名…未载生平事迹与语录原文」，实测其中七成有完整条目——该断言不可证且已被证伪，已全部改写；剩余 568 张亦改为「在所校七部灯录中未见独立条目（七部之外尚有《祖堂集》《联灯会要》《五灯全书》等未校，不可据此断言无记载）」。新增 `verify_status: extracted` 档（机器抽取，未逐字人工校订），与 `sourced`/`line_verified` 严格分档不混用 |

## 本地构建与预览

```bash
# 1) 抽取谱系（仅在分支图 HTML 更新后重跑）
python3 tools/extract_lineage.py

# 2) 生成 / 增补核心祖师卡（批量，据灯录）
python3 tools/gen_core_patriarchs.py
python3 tools/gen_patriarchs_phase2.py
python3 tools/gen_patriarchs_song.py
python3 tools/gen_phase4.py         # 升格临济主脉核心祖师为 draft（按需调用）
python3 tools/gen_stubs.py          # 为剩余所有节点生成 named_only 占位卡

# 3) 生成站点（每次增删 patriarchs/*.yaml 后重跑）
python3 tools/build_site.py

# 4) 预览：直接双击 site/index.html，或起本地服务器
python3 -m http.server -d site 8000   # 然后访问 http://localhost:8000
```

## 如何贡献一份祖师卡

1. 确认 `id` 与 `data/lineage.json` 中节点 `id` 完全一致（否则点击节点看不到卡片）。
2. 在 `data/patriarchs/` 新建 `<id>.yaml`，按 `data/schema.md` 填写；先标 `status: draft`。
3. 引文务必标注 `ref`（灯录·卷·条）；存疑处用 `verify` / `bio` 显式说明，不混入定论。
4. 跑 `python3 tools/build_site.py` 重新生成站点。
5. （推荐）提交前逐字比对 CBETA，无误则改 `status: core`。

## 已知数据说明

- **节点命名采用尊号缩写**：如 `临济玄禅师`、`六祖大鉴禅师`、`清凉益禅师`（= 法眼文益）、
  `黄龙南禅师`（= 黄龙慧南，黄龙派开祖）、`杨歧会禅师`（= 杨岐方会，「歧」为「岐」异体）。
  部分宋以后巨匠在图谱中以**驻地名/尊号**呈现：`白云守端`=`白云端禅师`、`圆悟克勤`=`昭觉勤禅师`、
  `虎丘绍隆`=`虎丘隆禅师`、`大慧宗杲`=`径山杲禅师`（驻锡径山）。卡片内 `name` 给出标准全名，便于检索。
- **注意同名异人**：`黄龙机禅师` 与开祖 `黄龙南禅师`（= 黄龙慧南）**并非同一人**——前者是黄龙派中
  师承玄泉彦禅师的另一位法嗣，后者才是黄龙派开祖。两者的卡片已分别处理，避免误植。
- **西天二十八祖在图谱中折叠为单一汇总节点**（`PRE::……西天二十八祖……`），已写综述卡；
  后续可据 CBETA 拆为二十八张独立卡。
- **杨岐派 house 已归一**：`杨歧会禅师` 子树 193 节点现统一为「杨岐派」配色；汾阳善昭、石霜楚圆
  归为「临济宗」，玄沙备归为「青原系」，分支图配色已与宗派一致。
- **谱系主干准确、部分支派为独立脊柱**：临济主脉（临济玄→兴化→南院→风穴→首山→汾阳→石霜圆→杨歧会）
  父子链完整且父链一路追溯至七佛；杨岐/黄龙一系在图谱中以独立「脊柱分支」挂于 root 下，
  属原分支图的结构呈现（卡片内 `teacher` 字段仍按灯录给出真实师承）。
- **宋以后巨匠已在树中**：白云守端、圆悟克勤、大慧宗杲、虎丘绍隆等节点**早已收录**于谱系树
  （见上「节点命名」条），本轮已据这些节点补卡。若想再向下延伸（如元代高峰原妙、中峰明本等
  临济正宗远裔），可在 `data/lineage.json` 增补节点后，再用 `gen_patriarchs_song.py` 补卡。

## 版权与署名

- 古籍文本：公版；CBETA 数字化版本依其授权（CC）转载并署名。
- 本仓库结构化数据与代码：CC BY 4.0，署名 `chan-lineage` 贡献者。
