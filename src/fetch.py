from __future__ import annotations

import time
from datetime import date
from typing import Any, Dict, List

from .login import Sport8Client


def fetch_sales_detail(client: Sport8Client, target_date: date) -> Dict[str, Any]:
    payload = {
        "method": "getStadiumSalesDetail",
        "date": target_date.strftime("%Y-%m-%d"),
        "userId": client.tokens["setUserid"],
        "stadiumId": client.tokens["setStadiumId"],
        "token": client.tokens["setToken"],
        "nonce": str(int(time.time())),
    }
    response = client.api_post("/StadiumHelper/sales/StadiumSalesServlet", payload)
    data = response.json()

    if str(data.get("result_code")) != "0":
        message = data.get("result_msg", "未知错误")
        raise RuntimeError(f"获取数据失败：{message}")

    return data["result_data"]


