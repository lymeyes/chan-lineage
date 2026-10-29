#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""宗脉谱系离线库 · 一键灾备重建（从零恢复）
=============================================
背景
----
Obsidian 的「我的书库/宗脉谱系」是**派生产物**（由本仓库 data/ 生成），
它不受 vault git 保护、只走 QSync↔NAS 同步，曾因同步把整目录删空一次。
此前「重建工具 `_generate.py`」本身也只存在那个目录里 —— 目录一删，工具一起没了。

本脚本的作用：把「脚本」也纳入仓库真源，并做到
    **只要有 GitHub 上的 chan-lineage，一条命令即可从零恢复整库并自证完整。**
恢复链：GitHub 仓库（含数据 + 生成器 + 校验器）→ 本脚本 → 1976 份祖师卡 + 站点 + 清单。

用法
----
  python3 tools/rebuild_offline.py                # 重建 + 校验（默认目标见 --target）
  python3 tools/rebuild_offline.py --prune        # 重建并清理历史残留旧名文件
  python3 tools/rebuild_offline.py --verify-only   # 只校验，不重建
  python3 tools/rebuild_offline.py --target /path  # 指定离线库目录
  CHAN_LINEAGE_DATA=/path/to/data python3 tools/rebuild_offline.py   # 指定数据源
  本机仓库丢失时：自动 git clone（先 SSH，失败回退 HTTPS）到临时目录再重建。

退出码：0 重建且校验通过；1 失败。
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

DEFAULT_TARGET = os.path.expanduser("~/Obsidian/Noteshelf/我的书库/宗脉谱系")
REPO_SSH = "git@github.com:lymeyes/chan-lineage.git"
REPO_HTTPS = "https://github.com/lymeyes/chan-lineage.git"

HERE = os.path.dirname(os.path.realpath(__file__))
REPO = os.path.dirname(HERE)  # tools/ 的上一级


def log(msg):
    print("[rebuild] " + msg, flush=True)


def find_repo_data():
    """返回可用的 data 目录；优先本仓库，其次环境变量。"""
    for c in (os.path.join(REPO, "data"),
              os.environ.get("CHAN_LINEAGE_DATA", "")):
        if c and os.path.exists(os.path.join(c, "lineage.json")):
            return REPO, c
    return None, None


def clone_repo(tmp):
    """本机仓库不完整时，从 GitHub 重新克隆（SSH 优先，HTTPS 回退）。"""
    for url, label in ((REPO_SSH, "SSH"), (REPO_HTTPS, "HTTPS")):
        dst = os.path.join(tmp, "chan-lineage")
        if os.path.exists(dst):
            shutil.rmtree(dst, ignore_errors=True)
        log("本机数据缺失，尝试从 GitHub 克隆（%s）…" % label)
        r = subprocess.run(["git", "clone", "--depth", "1", url, dst],
                           capture_output=True, text=True)
        if r.returncode == 0 and os.path.exists(os.path.join(dst, "data", "lineage.json")):
            log("克隆成功：%s" % dst)
            return dst
        log("  %s 失败：%s" % (label, (r.stderr or "").strip().splitlines()[-1:] or ""))
    return None


def run(cmd, env=None):
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    out = (r.stdout or "") + (r.stderr or "")
    return r.returncode, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default=DEFAULT_TARGET, help="离线库目录")
    ap.add_argument("--prune", action="store_true", help="顺便清理历史残留文件")
    ap.add_argument("--verify-only", action="store_true", help="只校验不重建")
    a = ap.parse_args()

    target = os.path.abspath(os.path.expanduser(a.target))
    log("离线库目标：%s" % target)

    tmp = None
    repo, data = find_repo_data()
    if data is None:
        tmp = tempfile.mkdtemp(prefix="chan-lineage-")
        cloned = clone_repo(tmp)
        if not cloned:
            log("失败：本机无数据，且 GitHub 克隆失败（检查网络/SSH 权限）。")
            return 1
        repo = cloned
        data = os.path.join(cloned, "data")

    env = dict(os.environ, CHAN_LINEAGE_DATA=data)
    log("数据源：%s" % data)

    # 1) 把仓库里的生成器/校验器同步到离线库（保证工具自身也不会丢）
    os.makedirs(target, exist_ok=True)
    for src, dst in ((os.path.join(repo, "tools", "offline_generate.py"), "_generate.py"),
                     (os.path.join(repo, "tools", "offline_verify.py"), "_校验.py")):
        if not os.path.exists(src):
            log("失败：仓库缺少 %s" % src)
            return 1
        shutil.copyfile(src, os.path.join(target, dst))
    log("生成器 / 校验器已同步到离线库")

    if not a.verify_only:
        # 2) 重建
        cmd = [sys.executable, os.path.join(target, "_generate.py")]
        if a.prune:
            cmd.append("--prune")
        rc, out = run(cmd, env=env)
        print(out.rstrip()[-1500:])
        if rc != 0:
            log("失败：生成器退出码 %d" % rc)
            return 1

    # 3) 校验
    rc, out = run([sys.executable, os.path.join(target, "_校验.py")], env=env)
    print(out.rstrip())
    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)
    if rc == 0:
        log("完成：库已恢复且完整性校验全部通过。")
    else:
        log("完成重建，但完整性校验未通过（见上方 FAIL 项）。")
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
