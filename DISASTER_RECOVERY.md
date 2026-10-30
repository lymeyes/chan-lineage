# 灾备与恢复（DISASTER RECOVERY）

> 一页纸运行手册。目标：**任何一次误删／同步回滚／磁盘损坏，都能在一个动作内恢复到可自证完整的状态。**

## 1. 先分清「真源」与「派生物」

| 角色 | 位置 | 是否受版本保护 | 说明 |
|---|---|---|---|
| **真源** | GitHub `lymeyes/chan-lineage`（`data/lineage.json` + `data/patriarchs/*.yaml` + `tools/`） | ✅ git（公开仓） | 唯一权威。1977 节点 / 1976 卡 |
| 派生物 A | `Project/chan-lineage/site/index.html` | ✅ git | 在线站点（Pages/本地预览） |
| 派生物 B | `~/Obsidian/Bookshelf/宗脉谱系/` | ⚠️ 普通文件夹（**非 vault，不进 git**） | 派生物，可随时从 GitHub 真源 `rebuild_offline.py` 一键重建；**不再受 vault git 保护**，别依赖「git 历史取回」这条路 |

**关键认知**：派生物 B 里的一切（1976 份 `.md`、`站点/index.html`、`MANIFEST.json`，**连生成器 `_generate.py` 本身**）都可以从真源重建。所以不要把它当资产，当缓存。

> 历史坑：早期版本把 `_generate.py` 只放在派生物 B 里 —— 目录一删，重建工具一起没了，等于「唯一一把钥匙锁在柜子里」。现已在仓库 `tools/offline_generate.py` 留存副本，由重建脚本自动同步过去。

## 2. 一条命令恢复

```bash
python3 ~/WorkBuddy/task/Project/chan-lineage/tools/rebuild_offline.py
```

它依次做四件事：

1. 定位数据源（本机仓库 → 环境变量 `CHAN_LINEAGE_DATA`；**两者都没有则自动 `git clone`**，SSH 优先、HTTPS 回退）
2. 把仓库里的生成器／校验器同步进离线库（保证工具自身不丢）
3. 重建 1976 份 `祖师/*.md` + `站点/index.html` + `站点/MANIFEST.json`
4. 跑完整性校验，9 项全 PASS 才算成功（退出码 0）

常用变体：

| 场景 | 命令 |
|---|---|
| 只核对，不重建 | `python3 tools/rebuild_offline.py --verify-only` |
| 顺带清掉历史残留旧名文件 | `python3 tools/rebuild_offline.py --prune` |
| 恢复到别的目录（演练/比对） | `python3 tools/rebuild_offline.py --target /path/to/dir` |
| 本机仓库也没了 | 同上一条命令即可，脚本会自己从 GitHub 克隆 |

## 2.5 「git 历史取回」路（仅当数据位于 vault git 内时成立）

> ⚠️ **2026-10-30 起数据已移至 `~/Obsidian/Bookshelf/宗脉谱系`（普通文件夹，非 vault），此路已失效。**
> 若派生物 B 被删，唯一权威恢复手段是下一节的 `rebuild_offline.py`（从 GitHub 真源重建），不要指望本地 git 历史。

（以下仅作历史留存；适用前提是数据位于某个 vault git 内、且 `.gitignore` 对其开了例外：）

派生物 B 若纳入 vault git（私有仓 `lymeyes/Noteshelf`），即使它被同步删除、甚至被 obsidian-git 自动提交了这次删除，**历史提交里仍有完整副本**：

```bash
cd ~/Obsidian/Noteshelf
git log --oneline -5 -- "我的书库/宗脉谱系"     # 找到删除前的提交
git checkout <sha> -- "我的书库/宗脉谱系"        # 整目录取回
```

> 前提：`.gitignore` 里 `我的书库/*` + `!我的书库/宗脉谱系/` 这两行必须在。
> 注意 git 的硬规则：父目录被整体忽略时，无法重新包含其子目录，所以必须写成 `我的书库/*` 而非 `我的书库/`。

## 3. 判断「是否完好」的唯一标准

不要靠数文件，跑校验器：

```bash
python3 ~/Obsidian/Bookshelf/宗脉谱系/_校验.py   # 退出码 0 = 完好
```

9 项断言：祖师数量 / 逐份齐全 / **内容聚合指纹** / index.html 哈希 / 总览哈希 / README 哈希 / 生成器哈希 / 无残留 / 与仓库节点数一致。

判定依据是 `站点/MANIFEST.json`：1976 份文件逐份 sha256 再聚合的指纹（当前 `8d52b09a644830c9…`）。**指纹一致 = 内容一个字节都没变**，比「看着像全的」可靠。

## 4. 自动化

| 项 | 设置 |
|---|---|
| 每日 09:00 完整性校验 | 自动化 `ccb2f321-234d-4b41-a9c8-bd1e26b12dc6`，**只在 FAIL 时提醒**，全 PASS 静默 |

## 5. 故障速查

| 现象 | 成因 | 处置 |
|---|---|---|
| `_校验.py` 报「缺失 N 份」 | 同步删除／未重建 | 跑 `rebuild_offline.py` |
| 报「内容聚合指纹不一致」但文件都在 | 有人改了 `.md` 或 YAML 变了未重建 | 同上（以真源为准重建） |
| 报「多余 M 个」 | 历史旧名残留（生成器只写不删） | `rebuild_offline.py --prune` |
| 报「与节点数一致」FAIL | 仓库节点数 ≠ 清单（`data/` 变过） | 先重建，仍失败则查 `data/lineage.json` |
| 重建时 `找不到 chan-lineage/data` | 本机仓库被移走 + 克隆失败 | 检查 SSH 权限 `ssh -T git@github.com`；或手动 clone 后设 `CHAN_LINEAGE_DATA` |
| QSync 又把目录删了 | 双向同步传播删除 | 重建即可；长期应让 QSync 排除 `站点/`（生成物无需同步） |

## 6. 恢复演练（建议每季度一次）

```bash
python3 tools/rebuild_offline.py --target ~/WorkBuddy/task/Temp/dr-test
```

若新目录的聚合指纹与现库一致，说明恢复链有效。**没有演练过的备份等于没有备份。**
（2026-10-29 实测：空白目录 → 1976 份，指纹 `8d52b09a644830c9…` 与实库逐字节一致。）

## 7. 防线现状（含已确认的缺口）

| # | 层 | 状态 |
|---|---|---|
| 1 | 真源在 GitHub `chan-lineage`（异机、可 clone） | ✅ |
| 2 | 一条命令重建，重建工具自身也在仓库内 | ✅ |
| 3 | 哈希自证（`MANIFEST.json` 逐份 sha256 聚合 + `_校验.py` 9 项） | ✅ |
| 4 | 每日 09:00 自动校验（仅 FAIL 时报） | ✅ |
| 5 | 派生物 B 进 vault git | ❌ 2026-10-30 起数据移至 `Bookshelf`（非 vault），此层失效；恢复靠 GitHub 真源重建 |
| 6 | QNAP 共享文件夹**回收站** | ✅ 已开（2026-10-29 事故即靠它恢复） |
| 7 | QNAP **快照** | ❌ **未开**（用户空间不足，明确不启用） |
| 8 | 异地独立副本（tar 另存 NAS/NUC） | ❌ 用户明确不要 |

**缺口影响评估**：第 7、8 层缺失只影响「NAS 侧」的兜底强度。由于真源在 GitHub（`chan-lineage`），离线库现为普通文件夹（`Bookshelf`）可随时重建，
**NAS 不构成单点**；真正会导致数据不可恢复的只剩「两个 GitHub 仓库同时消失 + 本机磁盘全毁」。
