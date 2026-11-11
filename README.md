# SBTC Core · Retracing Bitcoin's Mining Journey / 重走比特币挖矿之路 ⛏️

<div align="center">

**[English](#english) | [中文说明](#chinese)**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/github/v/release/jxsite/sbtc?color=orange&label=Release)](https://github.com/jxsite/sbtc/releases)
[![Explorer](https://img.shields.io/badge/Explorer-sbtc.leishen.work-blue)](https://sbtc.leishen.work)
[![GitHub Pages](https://img.shields.io/badge/Website-jxsite.github.io%2Fsbtc-green)](https://jxsite.github.io/sbtc/)

</div>

---

<a name="english"></a>
## 🌐 English

> **"In 2009, Satoshi Nakamoto mined the genesis block on a humble personal computer. Today, let us return to the genesis — retracing the path of pure CPU mining."**

### 🌟 What is SBTC?

On January 3, 2009, the Bitcoin genesis block was born. In that golden cypherpunk era:
- **No industrial mining monopolies**: Every personal computer was an equal peer and block generator.
- **Zero pre-mine, zero ICO, zero VC allocations**: Every single coin was generated fairly through Proof of Work.
- **One CPU, one vote**: Ordinary computer users could directly experience the thrill of mining their own blocks.

Fifteen years later, Bitcoin has become institutional digital gold, dominated by multi-million-dollar ASIC mining farms. Ordinary people can no longer participate in native mining.

**SBTC (Satoshi Bitcoin) was created to revive that spirit.** Forked directly from **Bitcoin Core v29.5**, SBTC is an independent Layer 1 native blockchain. It preserves 100% of Bitcoin's consensus rules while relaxing initial difficulty (`powLimit`) during the cold-start phase. Anyone can launch the software on a laptop or desktop and experience the pure joy of early Bitcoin mining!

---

### 💎 Consensus Specifications (1:1 Bitcoin Faithful)

SBTC is an **independent Layer 1 blockchain** with its own genesis block, peer-to-peer network, and native coin — **NOT an ERC-20 / smart contract token**.

| Parameter | SBTC Value | Description |
|:---|:---|:---|
| **Consensus Algorithm** | **Double SHA-256 (SHA-256d)** | Identical to Bitcoin's PoW consensus |
| **Max Supply** | **21,000,000 SBTC** (21 Million) | Fixed hard cap, strictly anti-inflationary |
| **Initial Block Reward** | **50 SBTC / block** | 50 newly minted coins per block |
| **Halving Interval** | **Every 210,000 blocks** | Halves approximately every 4 years |
| **Target Block Time** | **10 minutes** | Canonical Bitcoin block pacing |
| **Difficulty Adjustment**| **Every 2,016 blocks** | Retargets based on network hashrate |
| **Coinbase Maturity** | **100 confirmations** | Mined coins become spendable after 100 blocks |
| **Cold-Start Parameter**| `powLimit = 0x207fffff` | Initial threshold relaxed so standard CPUs can mine |
| **Fair Launch** | **0 Pre-mine / 0 ICO / 0 Team Allocation** | 100% distributed through PoW hashrate |

---

### 🚀 1-Minute Quick Start (Windows Package)

No developer setup required. Unpack and mine with a single click!

1. **Download the Package**:
   Download the latest pre-compiled archive **`SBTC-Windows-v1-Fixed.zip`** from [GitHub Releases](https://github.com/jxsite/sbtc/releases).
2. **Extract**:
   Unpack the archive into a dedicated folder (e.g., `D:\SBTC`).
3. **Start Mining**:
   Double-click **`2-开始挖矿.bat`**:
   - The script automatically connects to the public seed node and syncs existing blocks.
   - It creates your personal `miner` wallet and generates a unique address (`sbtc1q...`).
   - Mining starts immediately; each block prints height and reward notifications in the terminal.
4. **View GUI Wallet & Send Coins**:
   Double-click `3-停止节点.bat` to stop the background node, then double-click **`1-打开钱包.bat`** to open the Qt graphical desktop wallet.

---

### 🌐 Ecosystem & Infrastructure

* 🌍 **Official Website**: [https://jxsite.github.io/sbtc/](https://jxsite.github.io/sbtc/)
* 🔍 **Blockchain Explorer**: [https://sbtc.leishen.work](https://sbtc.leishen.work)  
  *Search blocks, transactions, and miner address balances in real time.*
* 🚰 **SBTC Faucet (Claim 1 Free SBTC)**: [https://jxsite.github.io/sbtc/faucet.html](https://jxsite.github.io/sbtc/faucet.html) *(Backup node: [https://sbtc.leishen.work/faucet](https://sbtc.leishen.work/faucet))*
* 📦 **Downloads**: [https://sbtc.leishen.work/download](https://sbtc.leishen.work/download)
* 📡 **Mainnet Seed Node**: `addnode=43.206.228.239:29333` (P2P port `29333`, RPC port `29332`)

---

### 🛠️ Linux / Developer Build Guide

```bash
# Install dependencies (Ubuntu / Debian)
sudo apt update && sudo apt install -y build-essential cmake libsqlite3-dev python3

# Clone and build headless node & CLI tools
git clone https://github.com/jxsite/sbtc.git
cd sbtc
cmake -B build -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_GUI=OFF -DBUILD_TESTS=OFF -DBUILD_BENCH=OFF \
  -DENABLE_WALLET=ON -DWITH_SQLITE=ON -DWITH_ZMQ=OFF
cmake --build build -j$(nproc)

# Binaries located at build/bin/{sbtcd, sbtc-cli, sbtc-tx, sbtc-wallet}
```

---

<br>
<hr>
<br>

<a name="chinese"></a>
## 🇨🇳 中文说明

> **“2009 年，中本聪在一台普通笔记本上挖出了创世区块。今天，让我们重返初心，重走中本聪之路。”**

### 🌟 为什么发起 SBTC？

2009 年 1 月 3 日，比特币创世区块诞生。在那个纯粹的黄金时代：
- **没有专业矿场垄断**：每台普通家用电脑都是一个平等的出块节点；
- **没有预挖、没有私募、没有 VC 代币分配**：所有代币均由 PoW 算力公平产出；
- **一人一机**：每个普通极客都能切身体会到“亲手挖出一个区块”的激动与浪漫。

十五年后的今天，比特币算力已被数以万计的工业级 ASIC 矿机垄断，普通人再也没有机会体验挖矿的乐趣。

**SBTC (Satoshi Bitcoin) 应运而生** —— 它是直接基于 **Bitcoin Core v29.5 源码** Fork 出来的独立 Layer 1 原生区块链。我们 1:1 严格复刻了比特币底层的全部共识规则，并在冷启动期放宽了初始难度（`powLimit`），让每位普通人打开笔记本电脑，就能轻松重新体验 2009 年开荒挖矿的完整历程！

---

### 💎 核心共识规则（1:1 纯粹 BTC 模型）

SBTC 是一条**完全独立的原生公链**，拥有自己的创世区块与独立 P2P 网络，**绝非任何公链上的代币智能合约**。

| 规则项 | SBTC 参数 | 机制说明 |
|:---|:---|:---|
| **共识算法** | **双重 SHA-256 (SHA-256d)** | 与比特币完全一致，保证底层最高级别安全 |
| **总量上限** | **21,000,000 SBTC** (2100 万枚) | 恒定总量，永不增发 |
| **初始出块奖励** | **50 SBTC / 区块** | 每挖出一个新块奖励 50 枚 |
| **减半周期** | **每 210,000 个区块** | 约 4 年减半一次，逐步递减 |
| **目标出块时间** | **10 分钟 / 块** | 与 BTC 保持一致节奏 |
| **难度调整机制** | **每 2016 块自动调整** | 根据全网总算力自适应调整难度 |
| **Coinbase 成熟度**| **100 个确认** | 挖到的币在后续 100 块确认后解锁可用 |
| **初始冷启动设定**| `powLimit = 0x207fffff` | 初期放宽算力门槛，普通 CPU 轻松出块 |
| **公平启动** | **0 预挖 / 0 私募 / 0 团队预留** | 100% 筹码纯靠 PoW 算力产出 |

---

### 🚀 极速开挖指南（Windows 一键挖矿包）

无需繁琐的环境配置，解压即用，1 分钟加入主网！

1. **下载挖矿包**：  
   前往 [GitHub Releases](https://github.com/jxsite/sbtc/releases) 下载最新已修复的 **`SBTC-Windows-v1-Fixed.zip`**，并解压到一个固定文件夹（如 `D:\SBTC`）。
2. **一键启动挖矿**：  
   双击运行 **`2-开始挖矿.bat`**：
   - 脚本会自动创建本地数据目录并连接全网种子节点；
   - 首次运行时，会自动为你生成**专属于你的独立矿工地址**（保存在 `我的矿工地址.txt` 中）；
   - 节点随后自动开启 CPU 挖矿，每次挖出新块，窗口都会实时打印当前高度和 50 SBTC 奖励提示！
3. **查看钱包与转账**：  
   - 先双击 `3-停止节点.bat` 退出挖矿，再双击 **`1-打开钱包.bat`** 即可调出 Qt 桌面图形钱包。
   - 挖出的币满 100 个确认后即可在钱包里自由转账。

---

### 🌐 链上生态与基础设施

* 🌍 **官网展示页**：[https://jxsite.github.io/sbtc/](https://jxsite.github.io/sbtc/)
* 🔍 **官方区块链浏览器**：[https://sbtc.leishen.work](https://sbtc.leishen.work)  
  *输入你的地址或交易 ID，即可实时查看出块确认与全网算力数据。*
* 🚰 **在线水龙头（免费领 1 SBTC）**：[https://jxsite.github.io/sbtc/faucet.html](https://jxsite.github.io/sbtc/faucet.html) *(备用节点: [https://sbtc.leishen.work/faucet](https://sbtc.leishen.work/faucet))*
* 📦 **钱包/节点下载中心**：[https://sbtc.leishen.work/download](https://sbtc.leishen.work/download)
* 📡 **主网种子节点**：`addnode=43.206.228.239:29333`（P2P 端口 `29333`，RPC 端口 `29332`）

---

### 📜 开源协议 / License

本项目严格遵循 **MIT 许可证**，沿用上游 Bitcoin Core 开源规范。  
This project is open-source under the terms of the MIT license. See [COPYING](COPYING) for details.
