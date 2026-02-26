import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

# ---------------------- 配置部分（2026年开盘价，你的持仓） ----------------------
PORTFOLIOS = {
    "a": {
        "total": 1000000,
        "funds": [
            {"code": "513390", "market": "sh", "name": "纳指100ETF", "ratio": 0.25, "cost_price": 2.10},
            {"code": "159652", "market": "sz", "name": "有色50ETF", "ratio": 0.25, "cost_price": 7.09},
            {"code": "588200", "market": "sh", "name": "科创芯片ETF", "ratio": 0.25, "cost_price": 10.73},
            {"code": "515880", "market": "sh", "name": "通信ETF", "ratio": 0.15, "cost_price": 5.09},
            {"code": "518880", "market": "sh", "name": "黄金ETF", "ratio": 0.10, "cost_price": 4.40}
        ]
    },
    "hk": {
        "total": 1000000,
        "funds": [
            {"code": "03455", "market": "hk", "name": "纳指100ETF", "ratio": 0.25, "cost_price": 10.00},
            {"code": "03132", "market": "hk", "name": "全球半导体ETF", "ratio": 0.20, "cost_price": 8.00},
            {"code": "03147", "market": "hk", "name": "中国创业板ETF", "ratio": 0.20, "cost_price": 5.00},
            {"code": "03110", "market": "hk", "name": "恒生高股息ETF", "ratio": 0.20, "cost_price": 6.00},
            {"code": "02840", "market": "hk", "name": "黄金ETF", "ratio": 0.15, "cost_price": 7.00}
        ]
    },
    "us": {
        "total": 1000000,
        "funds": [
            {"code": "QQQ", "market": "us", "name": "纳指100ETF", "ratio": 0.25, "cost_price": 620.00},
            {"code": "SPY", "market": "us", "name": "标普500ETF", "ratio": 0.25, "cost_price": 500.00},
            {"code": "RING", "market": "us", "name": "全球黄金矿股ETF", "ratio": 0.20, "cost_price": 40.00},
            {"code": "COPX", "market": "us", "name": "全球铜矿股ETF", "ratio": 0.20, "cost_price": 30.00},
            {"code": "BITB", "market": "us", "name": "大饼ETF", "ratio": 0.10, "cost_price": 49.00}
        ]
    }
}

# ---------------------- 数据获取函数（东方财富免费接口，稳定） ----------------------
def get_current_price(fund):
    """根据基金类型获取实时价格"""
    try:
        if fund["market"] in ["sh", "sz"]:
            # A股：东方财富接口
            secid = f"1.{fund['code']}" if fund["market"] == "sh" else f"0.{fund['code']}"
            url = f"http://push2.eastmoney.com/api/qt/stock/get?secid={secid}"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            if data["data"] and data["data"]["price"]:
                return float(data["data"]["price"])
        elif fund["market"] == "hk":
            # 港股：东方财富接口
            url = f"http://push2.eastmoney.com/api/qt/stock/get?secid=116.{fund['code']}"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            if data["data"] and data["data"]["price"]:
                return float(data["data"]["price"])
        elif fund["market"] == "us":
            # 美股：用新浪备用接口（东方财富美股需特殊处理，新浪更简单）
            url = f"https://hq.sinajs.cn/list=gb_{fund['code'].lower()}"
            resp = requests.get(url, headers={"Referer": "https://finance.sina.com.cn/"}, timeout=10)
            resp.encoding = "gbk"
            line = resp.text.split('"')[1]
            if line:
                values = line.split(",")
                if len(values) > 1 and values[1]:
                    return float(values[1])
    except Exception as e:
        print(f"获取 {fund['name']} 价格失败: {e}")
    # 如果获取失败，返回成本价（避免报错）
    return fund["cost_price"]

# ---------------------- 主函数 ----------------------
def main():
    # 1. 读取index.html
    if not os.path.exists("index.html"):
        print("错误：index.html 不存在！")
        return
    with open("index.html", "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml")

    # 2. 逐个更新组合
    for portfolio_type, portfolio in PORTFOLIOS.items():
        total_current = 0
        total_profit = 0

        # 更新每个基金
        for idx, fund in enumerate(portfolio["funds"]):
            # 获取实时价格
            current_price = get_current_price(fund)
            # 计算数据
            cost_total = portfolio["total"] * fund["ratio"]
            hold = cost_total / fund["cost_price"]
            current_total = hold * current_price
            profit = current_total - cost_total
            profit_rate = (profit / cost_total) * 100 if cost_total != 0 else 0

            # 累加总数据
            total_current += current_total
            total_profit += profit

            # 精准更新HTML中的对应ID（不会出错）
            for elem_id, value in [
                (f"{portfolio_type}-price-{idx}", f"{current_price:.3f}" if current_price < 10 else f"{current_price:.2f}"),
                (f"{portfolio_type}-current-total-{idx}", f"{current_total:.2f}"),
                (f"{portfolio_type}-profit-{idx}", f"{profit:.2f}"),
                (f"{portfolio_type}-rate-{idx}", f"{profit_rate:.2f}%")
            ]:
                elem = soup.find(id=elem_id)
                if elem:
                    elem.string = value
                    # 给收益加颜色
                    if "profit" in elem_id:
                        elem["class"] = "profit negative" if profit < 0 else "profit"

        # 更新组合总计
        total_rate = (total_profit / portfolio["total"]) * 100 if portfolio["total"] != 0 else 0
        for elem_id, value in [
            (f"{portfolio_type}-total-value", f"{total_current:.2f}"),
            (f"{portfolio_type}-total-profit", f"{total_profit:.2f}"),
            (f"{portfolio_type}-total-rate", f"{total_rate:.2f}%")
        ]:
            elem = soup.find(id=elem_id)
            if elem:
                elem.string = value
                if "profit" in elem_id:
                    elem["class"] = "profit negative" if total_profit < 0 else "profit"

        # 更新时间
        time_elem = soup.find(id=f"{portfolio_type}-update-time")
        if time_elem:
            time_elem.string = f"数据更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    # 3. 保存更新后的index.html
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(str(soup))
    print("✅ 数据同步成功！index.html 已更新")

if __name__ == "__main__":
    main()
