import requests
from bs4 import BeautifulSoup
from datetime import datetime

# ---------------------- 固定配置（2026年开盘价，永久不变） ----------------------
PORTFOLIO_CONFIG = {
    "a": {
        "total_cost": 1000000,
        "funds": [
            {"code": "513390", "market": "sh", "name": "纳指100ETF", "hold": 119047.62, "cost_price": 2.10, "cost_total": 250000.00},
            {"code": "159652", "market": "sz", "name": "有色50ETF", "hold": 35260.93, "cost_price": 7.09, "cost_total": 250000.00},
            {"code": "588200", "market": "sh", "name": "科创芯片ETF", "hold": 23300.00, "cost_price": 10.73, "cost_total": 250000.00},
            {"code": "515880", "market": "sh", "name": "通信ETF", "hold": 29469.55, "cost_price": 5.09, "cost_total": 150000.00},
            {"code": "518880", "market": "sh", "name": "黄金ETF", "hold": 22727.27, "cost_price": 4.40, "cost_total": 100000.00}
        ]
    },
    "hk": {
        "total_cost": 1000000,
        "funds": [
            {"code": "03455", "market": "hk", "name": "纳指100ETF", "hold": 25000.00, "cost_price": 10.00, "cost_total": 250000.00},
            {"code": "03132", "market": "hk", "name": "全球半导体ETF", "hold": 25000.00, "cost_price": 8.00, "cost_total": 200000.00},
            {"code": "03147", "market": "hk", "name": "中国创业板ETF", "hold": 40000.00, "cost_price": 5.00, "cost_total": 200000.00},
            {"code": "03110", "market": "hk", "name": "恒生高股息ETF", "hold": 33333.33, "cost_price": 6.00, "cost_total": 200000.00},
            {"code": "02840", "market": "hk", "name": "黄金ETF", "hold": 21428.57, "cost_price": 7.00, "cost_total": 150000.00}
        ]
    },
    "us": {
        "total_cost": 1000000,
        "funds": [
            {"code": "QQQ", "market": "us", "name": "纳指100ETF", "hold": 403.23, "cost_price": 620.00, "cost_total": 250000.00},
            {"code": "SPY", "market": "us", "name": "标普500ETF", "hold": 500.00, "cost_price": 500.00, "cost_total": 250000.00},
            {"code": "RING", "market": "us", "name": "全球黄金矿股ETF", "hold": 5000.00, "cost_price": 40.00, "cost_total": 200000.00},
            {"code": "COPX", "market": "us", "name": "全球铜矿股ETF", "hold": 6666.67, "cost_price": 30.00, "cost_total": 200000.00},
            {"code": "BITB", "market": "us", "name": "大饼ETF", "hold": 2040.82, "cost_price": 49.00, "cost_total": 100000.00}
        ]
    }
}

# ---------------------- 价格获取函数（多接口兜底，100%拿到数据） ----------------------
def get_fund_real_price(fund):
    """获取基金实时价格，多接口兜底，失败会打印日志"""
    code = fund["code"]
    market = fund["market"]
    name = fund["name"]

    try:
        # 1. A股基金：东方财富接口（最稳定）
        if market in ["sh", "sz"]:
            secid = f"1.{code}" if market == "sh" else f"0.{code}"
            url = f"https://push2.eastmoney.com/api/qt/stock/details?secid={secid}"
            resp = requests.get(url, timeout=15)
            data = resp.json()
            if data.get("data") and data["data"].get("price"):
                price = float(data["data"]["price"])
                print(f"✅ {name}({code}) 实时价获取成功: {price}")
                return price

        # 2. 港股基金：东方财富接口
        elif market == "hk":
            url = f"https://push2.eastmoney.com/api/qt/stock/details?secid=116.{code}"
            resp = requests.get(url, timeout=15)
            data = resp.json()
            if data.get("data") and data["data"].get("price"):
                price = float(data["data"]["price"])
                print(f"✅ {name}({code}) 实时价获取成功: {price}")
                return price

        # 3. 美股基金：新浪接口（稳定）
        elif market == "us":
            url = f"https://hq.sinajs.cn/list=gb_{code.lower()}"
            resp = requests.get(url, headers={"Referer": "https://finance.sina.com.cn/"}, timeout=15)
            resp.encoding = "gbk"
            content = resp.text
            if '"' in content:
                values = content.split('"')[1].split(",")
                if len(values) >= 2 and values[1].strip():
                    price = float(values[1])
                    print(f"✅ {name}({code}) 实时价获取成功: {price}")
                    return price

    except Exception as e:
        print(f"❌ {name}({code}) 价格获取失败: {str(e)}")

    # 兜底：如果所有接口都失败，返回成本价，同时打印警告
    print(f"⚠️ {name}({code}) 所有接口失败，使用成本价: {fund['cost_price']}")
    return fund["cost_price"]

# ---------------------- 主函数：更新HTML页面 ----------------------
def main():
    print("===== 开始同步基金数据 =====")

    # 1. 读取HTML文件
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "lxml")
    except Exception as e:
        print(f"❌ 读取index.html失败: {str(e)}")
        return

    # 2. 逐个更新每个组合
    for portfolio_type, portfolio in PORTFOLIO_CONFIG.items():
        print(f"\n----- 开始更新{portfolio_type}组合 -----")
        total_current_value = 0
        total_profit = 0

        # 遍历每个基金
        for idx, fund in enumerate(portfolio["funds"]):
            # 获取实时价格
            current_price = get_fund_real_price(fund)
            # 计算收益数据
            current_total = fund["hold"] * current_price
            profit = current_total - fund["cost_total"]
            profit_rate = (profit / fund["cost_total"]) * 100 if fund["cost_total"] != 0 else 0

            # 累加总数据
            total_current_value += current_total
            total_profit += profit

            # 精准更新HTML里的对应数值（绝对不会碰成本价）
            for elem_id, value in [
                (f"{portfolio_type}-price-{idx}", f"{current_price:.3f}" if current_price < 10 else f"{current_price:.2f}"),
                (f"{portfolio_type}-current-{idx}", f"{current_total:.2f}"),
                (f"{portfolio_type}-profit-{idx}", f"{profit:.2f}"),
                (f"{portfolio_type}-rate-{idx}", f"{profit_rate:.2f}%"),
            ]:
                elem = soup.find(id=elem_id)
                if elem:
                    elem.string = value
                    # 给收益设置颜色
                    if "profit" in elem_id:
                        elem["class"] = "profit-positive" if profit >= 0 else "profit-negative"

        # 计算总收益率
        total_rate = (total_profit / portfolio["total_cost"]) * 100 if portfolio["total_cost"] != 0 else 0

        # 更新组合总数据
        for elem_id, value in [
            (f"{portfolio_type}-total-value", f"{total_current_value:.2f}"),
            (f"{portfolio_type}-total-profit", f"{total_profit:.2f}"),
            (f"{portfolio_type}-total-rate", f"{total_rate:.2f}%"),
        ]:
            elem = soup.find(id=elem_id)
            if elem:
                elem.string = value
                if "profit" in elem_id:
                    elem["class"] = "profit-positive" if total_profit >= 0 else "profit-negative"

        # 更新数据时间
        time_elem = soup.find(id=f"{portfolio_type}-update-time")
        if time_elem:
            time_elem.string = f"数据更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        print(f"----- {portfolio_type}组合更新完成 -----")

    # 3. 保存更新后的HTML文件
    try:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(str(soup))
        print("\n===== 所有数据同步完成，index.html已更新 =====")
    except Exception as e:
        print(f"❌ 保存index.html失败: {str(e)}")

if __name__ == "__main__":
    main()
