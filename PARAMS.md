# SBTC 参数表（一期第一阶段定版，2026-11-10）

> 基线：Bitcoin Core 源码 fork。共识规则 1:1 照抄 BTC，除文末注明的唯一有意差异（powLimit/创世 nBits 冷启动）外不动。

## 基本标识
| 项 | 值 | 理由 |
|---|---|---|
| 链名 (chain name) | `main`（内部）/ 对外名 SBTC | 内部 chain 标识沿用 main 结构，只换 genesis/参数，避免大改框架 |
| 货币名 | SBTC | 用户拍板 |
| 货币单位 | `sbtc`（currency unit = SBTC） | 与链名一致 |
| 数据目录 | `~/.sbtc`（Linux 默认 `~/.sbtc`） | 与 .bitcoin 区分，互不干扰 |
| 二进制 | `sbtcd` / `sbtc-cli` / `sbtc-tx` / `sbtc-wallet` | 由构建产物 bitcoind 等重命名/改 target 输出名实现 |
| 配置文件 | `sbtc.conf` | 跟随数据目录改名 |
| Qt 钱包 | 本阶段不编译 | daemon+cli 先行（一期范围已定：手机钱包不做，Qt 后续阶段） |

## 网络参数
| 项 | 值 | 理由 |
|---|---|---|
| P2P 端口 | **29333** | 避开 BTC 8333 等常用值，未被常用服务占用 |
| RPC 端口 | **29332** | 与 P2P 成对（RPC=P2P-1，与 BTC 8332/8333 习惯一致），避开 8332 |
| pchMessageStart (magic) | `0xfa, 0x53('S'), 0x42('B'), 0x54('T')`（已写入源码） | 后三字节为 ASCII "SBT"，与 BTC 的 f9 be b4 d9 完全不同，节点握手互不串链 |
| DNS seed | 空（注释掉所有 BTC seed） | 一期本地/自有节点，公开发布是后续阶段 |
| 固定种子节点 | 无（seednode/addnode 靠配置文件） | 本地起链不需要 |

## 地址编码
| 项 | 值 | 首字母效果 / 理由 |
|---|---|---|
| bech32 HRP | `sbtc` | 原生 segwit 地址以 `sbtc1...` 开头，一眼可辨、与 bc1 完全隔离 |
| bech32m (taproot) HRP | `sbtc` | 同上 |
| PUBKEY_ADDRESS (P2PKH base58) | **63** | base58 地址以 'S' 开头（63 对应首字符 S 区间），贴合 SBTC |
| SCRIPT_ADDRESS (P2SH base58) | **125** | 以 's' 开头区间，避免与 BTC 的 3 开头混淆 |
| SECRET_KEY (WIF) | **191** | 与 BTC 128 不同，私钥导入不会串链 |
| xpub/xprv 前缀 | 沿用 BTC 值（本阶段不动） | 扩展密钥前缀改动牵涉钱包测试面大，一期先保留，后续阶段评估（在报告中注明此项未改） |

> 注：base58 首字母由前缀字节 + 地址 hash 共同决定，上表为目标区间，实际生成地址后以验证结果为准回填。

## 共识参数（全部保持 BTC 原值）
| 项 | 值 |
|---|---|
| subsidyHalvingInterval | 210000 |
| 初始奖励 | 50 SBTC（nSubsidy 50 * COIN） |
| 目标出块间隔 nPowTargetSpacing | 600 秒（10 分钟） |
| 难度调整周期 nPowTargetTimespan | 1209600 秒（两周，2016 块） |
| coinbase 成熟度 | 100 |
| MAX_MONEY | 21,000,000 * COIN |
| BIP34/65/66、CSV、SegWit、Taproot 激活高度 | 沿用 BTC mainnet 的 buried deployment 高度设置（创世即已激活，一期不调整） |

## ★ 唯一有意的共识差异：powLimit / 创世 nBits（冷启动）
- BTC mainnet powLimit = `00000000ffffffff...`（难度 1 起步，创世块在 2009 年也要专业算力预期，现普通 CPU 几乎挖不动创世块）。
- SBTC 定版：powLimit = `7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff`（即 compact **0x207fffff**，regtest 量级）。
- 理由：新链冷启动、全网算力≈0，必须让普通电脑 CPU 能挖出创世后初期区块；难度每 2016 块按 BTC 原规则自动调整，网络算力上来后难度会自动上升，无需再改代码。
- 影响面：仅初期难度低；总量、减半、奖励、调整算法均未动。

## 创世区块
| 项 | 值 |
|---|---|
| timestamp (nTime) | **1794268800**（= 2026-11-10 00:00:00 UTC，`date -d "2026-11-10 UTC" +%s` 实算） |
| coinbase 文案 | `2026-11-10 SBTC genesis - a Bitcoin-compatible chain` |
| nVersion | 1 |
| nBits | 0x207fffff（对应上面 powLimit） |
| nonce | **1**（离线 Python 双 SHA256 算出，脚本 `~/workspace/sbtc/genesis.py`） |
| genesis hash | **7e1b06f27931f03323b009995fba5dbb35fc5c8584a12880a2a51e1db81ecfd9**（已填入 chainparams 并 assert） |
| merkle root | **de66eb7680f961b11718549ee22ba99394a416e7ac7b723c931ff50581ca2f38**（已填入并 assert） |
| 创世输出脚本 | 沿用 BTC 创世 pubkey 的 OP_CHECKSIG 脚本（创世输出本身不可花，与 BTC 同处理） |

## 附加改造（为新链必须）
- buried deployments（BIP34/65/66/CSV/SegWit）激活高度全部设 0（创世即激活），BIP34Hash = SBTC 创世 hash；Taproot 改 ALWAYS_ACTIVE。
- script_flag_exceptions 删除（那是 BTC 主网特定块的例外）。
- nMinimumChainWork / defaultAssumeValid 清零；checkpointData 只留 {0, 创世hash}；assumeutxo 数据清空；chainTxData 重置（nTime=1794268800, tx_count=1）。
- 客户端 UA 名 Satoshi → SBTC（src/clientversion.cpp UA_NAME）。
- 配置文件名 bitcoin.conf → sbtc.conf；默认数据目录 .bitcoin → .sbtc。

## 端口定版更正（写入源码前最终确认）
- P2P = **29333**，RPC = **29332**（上文统一以此为准）
