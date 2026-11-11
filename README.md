# SBTC Core · 重走比特币挖矿之路 ⛏️

> **“2009 年，中本聪在一台普通笔记本上挖出了创世区块。今天，让我们重返初心，重走中本聪之路。”**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/github/v/release/jxsite/sbtc?color=orange&label=Release)](https://github.com/jxsite/sbtc/releases)
[![Explorer](https://img.shields.io/badge/Explorer-sbtc.leishen.work-blue)](https://sbtc.leishen.work)
[![GitHub Pages](https://img.shields.io/badge/Website-jxsite.github.io%2Fsbtc-green)](https://jxsite.github.io/sbtc/)

---

## 🌟 为什么发起 SBTC？

2009 年 1 月 3 日，比特币创世区块诞生。在那个纯粹的黄金时代：
- **没有专业矿场垄断**，每台普通家用电脑都是一个平等的出块节点；
- **没有预挖、没有私募、没有 VC 代币分配**，所有代币均由 PoW 算力公平产出；
- **一人一机**，每个普通极客都能切身体会到“亲手挖出一个区块”的激动与浪漫。

十五年后的今天，比特币算力已被数以万计的工业级 ASIC 矿机垄断，普通人再也没有机会体验挖矿的乐趣。

**SBTC (Satoshi Bitcoin) 应运而生** —— 它是直接基于 **Bitcoin Core v29.5 源码** Fork 出来的独立 Layer 1 原生区块链。我们 1:1 严格复刻了比特币底层的全部共识规则，并在冷启动期放宽了初始难度（`powLimit`），让每位普通人打开笔记本电脑，就能轻松重新体验 2009 年开荒挖矿的完整历程！

---

## 💎 核心共识规则（1:1 纯粹 BTC 模型）

SBTC 是一条**完全独立的原生公链**，拥有自己的创世区块与独立 P2P 网络，**不是任何公链上的代币智能合约**。

| 规则项 | SBTC 参数 | 机制说明 |
|:---|:---|:---|
| **算法** | **双重 SHA-256 (SHA-256d)** | 与比特币完全一致，保证底层最高安全级别 |
| **总量上限** | **21,000,000 SBTC** (2100 万枚) | 恒定总量，永不增发 |
| **初始出块奖励** | **50 SBTC / 区块** | 每挖出一个新块奖励 50 枚 |
| **减半周期** | **每 210,000 个区块** | 约 4 年减半一次，逐步稀缺 |
| **目标出块时间** | **10 分钟 / 块** | 与 BTC 保持一致节奏 |
| **难度调整机制** | **每 2016 块自动调整** | 根据全网总算力自适应调整难度 |
| **Coinbase 成熟度**| **100 个确认** | 挖到的币在后续 100 块确认后解锁可用 |
| **初始冷启动设定**| `powLimit = 0x207fffff` | 初期放宽算力门槛，普通 CPU 轻松出块 |
| **公平启动** | **0 预挖 / 0 私募 / 0 团队预留** | 100% 筹码纯靠 PoW 算力产出 |

---

## 🚀 极速开挖指南（Windows 一键挖矿包）

无需繁琐的环境配置，解压即用，1 分钟加入主网！

### 步骤 1：下载挖矿包
前往 [GitHub Releases](https://github.com/jxsite/sbtc/releases) 下载最新已修复的 **`SBTC-Windows-v1-Fixed.zip`**，并解压到一个固定文件夹（如 `D:\SBTC`）。

### 步骤 2：一键启动挖矿
双击运行 **`2-开始挖矿.bat`**：
* 脚本会自动创建本地数据目录并连接全网种子节点；
* 首次运行时，会自动为你生成**专属于你的独立矿工地址**（保存在 `我的矿工地址.txt` 中）；
* 节点随后自动开启 CPU 挖矿，每次挖出新块，窗口都会实时打印当前高度和 50 SBTC 奖励提示！

### 步骤 3：查看钱包与转账
* **图形钱包**：先双击 `3-停止节点.bat` 退出挖矿，再双击 **`1-打开钱包.bat`** 即可调出 Qt 桌面图形钱包。
* **查看收益**：挖出的币满 100 个确认后即可自由发送转账。

---

## 🌐 链上生态与基础设施

* 🌍 **官网展示页**：[https://jxsite.github.io/sbtc/](https://jxsite.github.io/sbtc/)
* 🔍 **官方区块链浏览器**：[https://sbtc.leishen.work](https://sbtc.leishen.work)  
  *输入你的地址或交易 ID，即可实时查看出块确认与全网算力数据。*
* 🚰 **在线水龙头体验**：[https://sbtc.leishen.work/faucet](https://sbtc.leishen.work/faucet)
* 📦 **钱包/节点下载中心**：[https://sbtc.leishen.work/download](https://sbtc.leishen.work/download)

---

## ⚙️ 节点参数与网络拓扑

如果你在自己的服务器或 Linux 主机上运行节点，配置如下：

```ini
# sbtc.conf 配置文件
server=1
listen=1
addnode=43.206.228.239:29333
fallbackfee=0.0001
```

* **P2P 监听端口**：`29333`
* **RPC 通信端口**：`29332`
* **网络通信 Magic**：`0xfa, 0x53('S'), 0x42('B'), 0x54('T')`
* **原生隔离见证 (Bech32) 地址前缀**：`sbtc1...`
* **传统 Base58 地址前缀**：`S...` (版本号 63)

---

## 🛠️ Linux / 开发者自编译指南

### 1. 编译无头节点与命令行工具 (`sbtcd` / `sbtc-cli`)
```bash
# 安装基础依赖
sudo apt update && sudo apt install -y build-essential cmake libsqlite3-dev python3

# 克隆源码并配置编译
git clone https://github.com/jxsite/sbtc.git
cd sbtc
cmake -B build -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_GUI=OFF -DBUILD_TESTS=OFF -DBUILD_BENCH=OFF \
  -DENABLE_WALLET=ON -DWITH_SQLITE=ON -DWITH_ZMQ=OFF
cmake --build build -j$(nproc)

# 产物在 build/bin/ 目录下：sbtcd, sbtc-cli, sbtc-tx, sbtc-wallet
```

### 2. 编译 Linux Qt 图形桌面钱包 (`sbtc-qt`)
安装 Qt5 依赖后，在 CMake 配置时开启 `-DBUILD_GUI=ON` 即可。

---

## 📜 开源协议

本项目严格遵循 **MIT 许可证**，沿用上游 Bitcoin Core 开源规范。  
详见 [COPYING](COPYING)。版权归 The Bitcoin Core developers 与 SBTC Core 社区所有。
