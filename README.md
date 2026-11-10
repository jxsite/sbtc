SBTC Core
=========

SBTC 是一条复刻比特币（BTC）规则的独立区块链，基于 Bitcoin Core v29.5 源码 fork，
不是任何链上的代币合约。它有自己的创世区块、自己的节点网络，用普通电脑 CPU 就能挖矿。

- 总量 2100 万、初始出块奖励 50、每 210,000 块减半、目标 10 分钟出块、难度每 2016 块
  按 BTC 原规则调整、coinbase 成熟度 100、双 SHA256 工作量证明——与 BTC 一一对应。
- 唯一有意的共识差异：`powLimit` 放宽到 0x207fffff 量级（冷启动）。新链初期全网算力
  近乎为零，不放宽普通 CPU 挖不出创世后的区块；难度会随 2016 块调整自动上升，
  总量、减半、奖励、调整算法均未动。详见 [PARAMS.md](PARAMS.md)。

参数摘要
--------

| 项 | 值 |
|---|---|
| 基线版本 | Bitcoin Core v29.5（上游 commit `16ca532c8212d691daed14940da0f71f84f7b3fc`） |
| P2P 端口 | 29333 |
| RPC 端口 | 29332 |
| 网络 magic | `fa 53 42 54`（后三字节为 ASCII "SBT"） |
| bech32 前缀 | `sbtc`（地址以 `sbtc1...` 开头） |
| base58 地址前缀 | P2PKH = 63（以 `S` 开头）、P2SH = 125、WIF = 191 |
| 数据目录 / 配置文件 | `~/.sbtc` / `sbtc.conf` |
| 二进制 | `sbtcd` / `sbtc-cli` / `sbtc-tx` / `sbtc-wallet` / `sbtc-qt` |

创世区块：

- nTime = 1794268800（2026-11-10 00:00:00 UTC）
- coinbase 文案：`2026-11-10 SBTC genesis - a Bitcoin-compatible chain`
- genesis hash = `7e1b06f27931f03323b009995fba5dbb35fc5c8584a12880a2a51e1db81ecfd9`
- 离线计算脚本见 [genesis.py](genesis.py)

快速开始
--------

- 官网 / 区块浏览器：<https://sbtc.leishen.work>
- Windows 一键包（钱包 + 挖矿脚本）下载页：<https://sbtc.leishen.work/download>
- 水龙头：<https://sbtc.leishen.work/faucet>
  （水龙头收款地址 `sbtc1qdvpnzrkjafu73svy47ykhankf4z9fv6k57utvy`，
  注资确认后自动开放领取，每次 1 SBTC、每地址/IP 24 小时限 1 次）
- 种子节点：在 `sbtc.conf` 里加一行即可连接主网种子：

  ```
  addnode=43.206.228.239:29333
  ```

自己编译
--------

Linux 节点 + 命令行钱包（无 GUI）：

```sh
cmake -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_GUI=OFF -DBUILD_TESTS=OFF \
  -DBUILD_BENCH=OFF -DBUILD_FUZZ_BINARY=OFF -DENABLE_WALLET=ON -DWITH_SQLITE=ON \
  -DWITH_ZMQ=OFF -DBUILD_TX=ON -DBUILD_WALLET_TOOL=ON
cmake --build build -j2
# 产物：build/bin/{sbtcd,sbtc-cli,sbtc-tx,sbtc-wallet}
```

Linux Qt 桌面钱包：另装 Qt 5 依赖后加 `-DBUILD_GUI=ON` 用独立构建目录
（产物 `sbtc-qt`）。Windows 64 位交叉编译：先
`make -C depends HOST=x86_64-w64-mingw32`，再用
`depends/x86_64-w64-mingw32/toolchain.cmake` 配置 CMake 构建。
通用构建说明见上游文档 `doc/build-unix.md`、`doc/build-windows-mingw.md`。

目录说明
--------

- 链节点与钱包源码即本仓库主体（Bitcoin Core 目录结构）。
- `PARAMS.md`：SBTC 全部定版参数与理由。
- `genesis.py`：创世区块离线计算脚本（双 SHA256），结果已写入
  `src/kernel/chainparams.cpp` 并有断言校验。
- `explorer/`：区块浏览器 + 水龙头服务源码（Python 标准库零依赖，
  systemd 单元 `sbtc-explorer.service`），即 sbtc.leishen.work 线上所用版本。

许可证
------

MIT，沿用上游 Bitcoin Core 的许可证，见 [COPYING](COPYING)。
版权归 The Bitcoin Core developers 与 SBTC Core developers 所有。
