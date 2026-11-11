# -*- coding: utf-8 -*-
"""
SBTC 24小时无人值守跨链自动发币机器人 (SBTC Auto-Swap Bot)
- 实时监听 BNB Smart Chain (BSC) 上的 USDT 入账
- 自动提取交易中的 SBTC 接收地址备注 (Memo)
- 自动调用本地节点 sbtc-cli 发货到账
"""

import sys
import os
import time
import json
import sqlite3
import subprocess
import urllib.request
import ssl

# ================= 核心配置 =================
# 汇率：1 USDT (BSC) = 1 SBTC
EXCHANGE_RATE = 1.0

# 你的 BSC 收款地址 (小写)
ADMIN_BSC_ADDRESS = "0x24eb5473fd1e59d99c5ba9ff1612ea596ebee077".lower()

# BSC 官方 USDT 合约地址 (18位精度)
USDT_CONTRACT = "0x55d398326f99059fF775485246999027B3197955".lower()

# ERC-20 Transfer 事件签名
TRANSFER_EVENT_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

# BSC 公开 RPC 节点列表 (自动轮换容灾)
BSC_RPC_LIST = [
    "https://bsc.publicnode.com",
    "https://1rpc.io/bnb",
    "https://bsc-rpc.publicnode.com",
    "https://bsc-dataseed.binance.org"
]

# 本地 SBTC 客户端路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SBTC_CLI = os.path.join(SCRIPT_DIR, "sbtc-cli.exe")
DATADIR = os.path.join(SCRIPT_DIR, "data")
CONF = os.path.join(SCRIPT_DIR, "sbtc.conf")
DB_PATH = os.path.join(SCRIPT_DIR, "orders.db")

# ================= 数据库初始化 =================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            bsc_tx_hash TEXT PRIMARY KEY,
            block_number INTEGER,
            from_address TEXT,
            usdt_amount REAL,
            sbtc_address TEXT,
            sbtc_amount REAL,
            sbtc_txid TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bot_state (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_last_scanned_block():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT value FROM bot_state WHERE key = 'last_block'")
    row = cur.fetchone()
    conn.close()
    return int(row[0]) if row else None

def set_last_scanned_block(block_num):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO bot_state (key, value) VALUES ('last_block', ?)", (str(block_num),))
    conn.commit()
    conn.close()

def is_order_processed(tx_hash):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT status FROM orders WHERE bsc_tx_hash = ?", (tx_hash,))
    row = cur.fetchone()
    conn.close()
    return row is not None

def record_order(bsc_tx_hash, block_num, from_addr, usdt_amount, sbtc_addr, sbtc_amount, sbtc_txid, status):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO orders 
        (bsc_tx_hash, block_number, from_address, usdt_amount, sbtc_address, sbtc_amount, sbtc_txid, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (bsc_tx_hash, block_num, from_addr, usdt_amount, sbtc_addr, sbtc_amount, sbtc_txid, status))
    conn.commit()
    conn.close()

# ================= BSC RPC 通信 =================
rpc_index = 0
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

def rpc_call(method, params):
    global rpc_index
    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time()),
        "method": method,
        "params": params
    }
    data = json.dumps(payload).encode()
    
    for _ in range(len(BSC_RPC_LIST)):
        rpc_url = BSC_RPC_LIST[rpc_index]
        try:
            req = urllib.request.Request(
                rpc_url,
                data=data,
                headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, context=ssl_ctx, timeout=6) as response:
                result = json.loads(response.read().decode())
                if "result" in result:
                    return result["result"]
                elif "error" in result:
                    print(f"[RPC Error on {rpc_url}]: {result['error']}")
        except Exception as e:
            # 切换到下一个备用 RPC
            rpc_index = (rpc_index + 1) % len(BSC_RPC_LIST)
            time.sleep(0.5)
    return None

def get_current_block():
    res = rpc_call("eth_blockNumber", [])
    return int(res, 16) if res else None

def get_transaction(tx_hash):
    return rpc_call("eth_getTransactionByHash", [tx_hash])

def get_usdt_transfer_logs(from_block, to_block):
    # topic[0] = Transfer
    # topic[2] = to (ADMIN_BSC_ADDRESS 填充到 32 字节)
    admin_topic = "0x" + ADMIN_BSC_ADDRESS.replace("0x", "").lower().zfill(64)
    params = [{
        "fromBlock": hex(from_block),
        "toBlock": hex(to_block),
        "address": USDT_CONTRACT,
        "topics": [
            TRANSFER_EVENT_TOPIC,
            None,
            admin_topic
        ]
    }]
    return rpc_call("eth_getLogs", params)

# ================= 本地 SBTC 节点调用 =================
def check_node_balance():
    try:
        cmd = [SBTC_CLI, f"-datadir={DATADIR}", f"-conf={CONF}", "getbalance"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
        if res.returncode == 0:
            return float(res.stdout.strip())
    except Exception as e:
        pass
    return None

def send_sbtc(recipient_address, amount):
    try:
        # 格式化金额，保留 8 位小数
        amount_str = f"{amount:.8f}"
        cmd = [SBTC_CLI, f"-datadir={DATADIR}", f"-conf={CONF}", "sendtoaddress", recipient_address, amount_str]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
        if res.returncode == 0:
            txid = res.stdout.strip()
            return True, txid
        else:
            return False, res.stderr.strip()
    except Exception as e:
        return False, str(e)

# ================= 解析 Memo 中的 SBTC 地址 =================
def parse_sbtc_address_from_calldata(input_data):
    # 标准 ERC20 transfer(address,uint256) 编码长度是 138 字符 (0x + 8选择器 + 64地址 + 64金额)
    if not input_data or len(input_data) <= 138:
        return None
    try:
        extra_hex = input_data[138:]
        raw_bytes = bytes.fromhex(extra_hex)
        text = raw_bytes.decode('utf-8', errors='ignore').strip('\x00').strip()
        # 验证是否为合法 SBTC 地址 (以 sbtc1 或 S 开头，长度 26~62)
        if (text.startswith("sbtc1") or text.startswith("S")) and 26 <= len(text) <= 65:
            return text
    except Exception:
        pass
    return None

# ================= 主循环 =================
def run_bot():
    print("=" * 65)
    print("   SBTC 24小时无人值守跨链自动发币机器人 (Auto-Swap Bot)")
    print("=" * 65)
    print(f"[*] 监控 BSC 收款地址: {ADMIN_BSC_ADDRESS}")
    print(f"[*] 当前设定汇率: 1 USDT = {EXCHANGE_RATE} SBTC")
    print(f"[*] USDT 合约 (BEP-20): {USDT_CONTRACT}")
    
    # 检查本地 SBTC 节点
    bal = check_node_balance()
    if bal is not None:
        print(f"[+] 本地 SBTC 节点连接正常！当前可供交割余额: {bal:,.2f} SBTC")
    else:
        print("[!] 警告: 尚未检测到本地 SBTC 节点运行。请确保 sbtc-qt 或 sbtcd 已启动！")

    init_db()

    last_block = get_last_scanned_block()
    curr_block = get_current_block()
    if not curr_block:
        print("[-] 无法连接 BSC RPC 节点，请检查网络！")
        return

    if not last_block:
        # 首次启动：从当前高度的前 100 个区块开始扫
        last_block = curr_block - 100
        print(f"[*] 首次启动，从区块 #{last_block} 开始监控...")
    else:
        print(f"[*] 恢复监控，从上次记录区块 #{last_block} 继续...")

    print("-" * 65)
    print("[*] 自动发币机器人已就绪，正在 7x24 实时监听 BSC 链上转账...")

    while True:
        try:
            curr_block = get_current_block()
            if not curr_block:
                time.sleep(3)
                continue

            if curr_block > last_block:
                # 每次最多扫 500 个块，防止 RPC 超限
                scan_to = min(curr_block, last_block + 500)
                logs = get_usdt_transfer_logs(last_block + 1, scan_to)

                if logs:
                    for log in logs:
                        tx_hash = log.get("transactionHash")
                        block_num = int(log.get("blockNumber", "0x0"), 16)
                        
                        if is_order_processed(tx_hash):
                            continue

                        # 获取转账金额 (18位小数)
                        raw_amount = int(log.get("data", "0x0"), 16)
                        usdt_amount = raw_amount / (10 ** 18)

                        # 获取发送者地址
                        sender = "0x" + log.get("topics", [None, ""])[1][-40:]

                        print(f"\n[🔔 收到入账] BSC Tx: {tx_hash}")
                        print(f"   买家 BSC 地址: {sender}")
                        print(f"   入账金额: {usdt_amount:.4f} USDT")

                        # 深入查询交易 input 获取 SBTC 接收地址
                        tx_detail = get_transaction(tx_hash)
                        input_data = tx_detail.get("input", "") if tx_detail else ""
                        sbtc_dest = parse_sbtc_address_from_calldata(input_data)

                        if sbtc_dest:
                            sbtc_amount = usdt_amount * EXCHANGE_RATE
                            print(f"   解析到 SBTC 接收地址: {sbtc_dest}")
                            print(f"   应发 SBTC 数量: {sbtc_amount:.4f} SBTC")
                            print("   正在调用本地 sbtc-cli 发货...")

                            success, result = send_sbtc(sbtc_dest, sbtc_amount)
                            if success:
                                print(f"   ✅ [发货成功！] SBTC TxID: {result}")
                                record_order(tx_hash, block_num, sender, usdt_amount, sbtc_dest, sbtc_amount, result, "COMPLETED")
                            else:
                                print(f"   ❌ [发货失败]: {result}")
                                record_order(tx_hash, block_num, sender, usdt_amount, sbtc_dest, sbtc_amount, "", f"FAILED: {result}")
                        else:
                            print("   ⚠️ 未在交易中检测到 SBTC 接收地址备注 (可能是外部直接转账)")
                            print("   已记入待人工复核名单。用户也可在网页端提供此 TxHash 补单。")
                            record_order(tx_hash, block_num, sender, usdt_amount, "", 0, "", "PENDING_NO_MEMO")

                last_block = scan_to
                set_last_scanned_block(last_block)

            # 打印心跳
            bal_str = f"{check_node_balance():,.2f}" if check_node_balance() else "未连接"
            print(f"\r[*] BSC 高度: #{last_block} | 监控状态: 正常 | 本地钱包余额: {bal_str} SBTC", end="", flush=True)

        except Exception as e:
            print(f"\n[!] 异常: {e}")

        time.sleep(3)

if __name__ == "__main__":
    run_bot()
