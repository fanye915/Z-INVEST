import requests
import json
from datetime import datetime

# 基金配置
fund_config = {
    "a_share": [
        {"code": "sh513390", "name": "纳指100ETF", "position": 0.25, "cost_price": 2.10},
        {"code": "sz159652", "name": "有色50ETF", "position": 0.25, "cost_price": 7.09},
        {"code": "sh588200", "name": "科创芯片ETF", "position": 0.25, "cost_price": 10.73},
        {"code": "sh515880", "name": "通信ETF", "position": 0.15, "cost_price": 5.09},
        {"code": "sh518880", "name": "黄金ETF", "position": 0.10, "cost_price": 4.40}
    ],
    "hk_share": [
        {"code": "hk03455", "name": "纳指100ETF", "position": 0.25, "cost_price": 10.00},
        {"code": "hk03132", "name": "全球半导体ETF", "position": 0.20, "cost_price": 8.00},
        {"code": "hk03147", "name": "中国创业板ETF", "position": 0.20, "cost_price": 5.00},
        {"code": "hk03110", "name": "恒生高股息ETF", "position": 0.20, "cost_price": 6.00},
        {"code": "hk02840", "name": "黄金ETF", "position": 0.15, "cost_price": 7.00}
    ],
    "us_share": [
        {"code": "gb_qqq", "name": "纳指100ETF", "position": 0.25, "cost_price": 620.00},
        {"code": "gb_spy", "name": "标普500ETF", "position": 0.25, "cost_price": 500.00},
        {"code": "gb_ring", "name": "全球黄金矿股ETF", "position": 0.20, "cost_price": 40.00},
        {"code": "gb_copx", "name": "全球铜矿股ETF", "position": 0.20, "cost_price": 30.00},
        {"code": "gb_bitb", "name": "大饼ETF", "position": 0.10, "cost_price": 49.00}
    ]
}

# 总仓位
total_amount = {
    "a_share": 1000000,
    "hk_share": 1000000,
    "us_share": 1000000
}

def get_fund_data(codes):
    """获取新浪财经的基金数据，适配不同类型基金的返回格式"""
    url = f"https://hq.sinajs.cn/list={','.join(codes)}"
    headers = {
        "Referer": "https://finance.sina.com.cn/"
    }
    response = requests.get(url, headers=headers)
    response.encoding = "gbk"
    data = {}
    lines = response.text.split("\n")
    for line in lines:
        if line.startswith("var hq_str_"):
            code = line.split("=")[0].replace("var hq_str_", "")
            values = line.split('"')[1].split(",")
            if len(values) >= 4:
                # 尝试获取当前价格，先试A股格式（values[3]），不行的话试港股/美股格式（values[1]）
                current_price = None
                try:
                    current_price = float(values[3])
                except ValueError:
                    try:
                        current_price = float(values[1])
                    except ValueError:
                        print(f"警告：基金{code}的返回格式异常，无法获取当前价格，返回值：{values[:10]}")
                        continue
                data[code] = {
                    "name": values[0],
                    "current_price": current_price,
                    "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
    return data

def calculate_profit(fund, current_price, total_amount):
    """计算收益"""
    position_amount = total_amount * fund["position"]
    hold = position_amount / fund["cost_price"]
    current_total = hold * current_price
    profit = current_total - position_amount
    profit_rate = (profit / position_amount) * 100
    return {
        "hold": round(hold, 2),
        "current_price": current_price,
        "position_amount": round(position_amount, 2),
        "current_total": round(current_total, 2),
        "profit": round(profit, 2),
        "profit_rate": round(profit_rate, 2)
    }

def main():
    # 获取所有基金代码
    all_codes = []
    for category in fund_config.values():
        for fund in category:
            all_codes.append(fund["code"])
    
    # 获取基金数据
    fund_data = get_fund_data(all_codes)
    
    # 计算每个基金的收益
    result = {}
    for category_name, category in fund_config.items():
        category_result = []
        total_profit = 0
        total_current = 0
        for fund in category:
            if fund["code"] not in fund_data:
                print(f"警告：未获取到 {fund['name']}（{fund['code']}）的数据，跳过该基金")
                continue
            current_price = fund_data[fund["code"]]["current_price"]
            profit_data = calculate_profit(fund, current_price, total_amount[category_name])
            category_result.append({
                "code": fund["code"],
                "name": fund["name"],
                "cost_price": fund["cost_price"],
                **profit_data
            })
            total_profit += profit_data["profit"]
            total_current += profit_data["current_total"]
        result[category_name] = {
            "funds": category_result,
            "total_amount": total_amount[category_name],
            "total_current": total_current,
            "total_profit": total_profit,
            "total_profit_rate": round((total_profit / total_amount[category_name]) * 100, 2) if total_amount[category_name] !=0 else 0,
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    # 保存数据到data.json
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 更新index.html里的更新时间和实时价格
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
    except FileNotFoundError:
        print("错误：未找到index.html文件，请确认文件在根目录")
        return
    
    # 更新每个组合的更新时间
    for category_name, short_name in [("a_share", "a"), ("hk_share", "hk"), ("us_share", "us")]:
        update_time = result[category_name]["update_time"]
        # 替换更新时间
        html_content = html_content.replace(
            f'数据更新时间: {update_time}',
            f'数据更新时间: {update_time}'
        )
    
    # 更新每个基金的实时价格和收益
    for category_name in ["a_share", "hk_share", "us_share"]:
        for fund in result[category_name]["funds"]:
            # 替换实时价格
            html_content = html_content.replace(
                f'<td class="current-price">{fund["cost_price"]}</td>',
                f'<td class="current-price">{fund["current_price"]}</td>'
            )
            # 替换当前总额
            html_content = html_content.replace(
                f'<td class="current-total">{fund["position_amount"]}</td>',
                f'<td class="current-total">{fund["current_total"]}</td>'
            )
            # 替换收益
            profit_class = "profit" if fund["profit"] >= 0 else "profit negative"
            html_content = html_content.replace(
                f'<td class="profit">0.00</td>',
                f'<td class="{profit_class}">{fund["profit"]}</td>'
            )
            # 替换收益率
            html_content = html_content.replace(
                f'<td class="profit-rate">0.00%</td>',
                f'<td class="profit-rate">{fund["profit_rate"]}%</td>'
            )
    
    # 替换总计数据
    for category_name, short_name in [("a_share", "a"), ("hk_share", "hk"), ("us_share", "us")]:
        total_current = result[category_name]["total_current"]
        total_profit = result[category_name]["total_profit"]
        total_profit_rate = result[category_name]["total_profit_rate"]
        html_content = html_content.replace(
            f'<div class="value total-value-{short_name}">1000000.00</div>',
            f'<div class="value total-value-{short_name}">{total_current:.2f}</div>'
        )
        profit_class = "profit" if total_profit >= 0 else "profit negative"
        html_content = html_content.replace(
            f'<div class="value {profit_class} total-profit-{short_name}">0.00</div>',
            f'<div class="value {profit_class} total-profit-{short_name}">{total_profit:.2f}</div>'
        )
        html_content = html_content.replace(
            f'<div class="value total-rate-{short_name}">0.00%</div>',
            f'<div class="value total-rate-{short_name}">{total_profit_rate}%</div>'
        )
    
    # 保存更新后的index.html
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("数据同步完成，已更新data.json和index.html")

if __name__ == "__main__":
    main()
