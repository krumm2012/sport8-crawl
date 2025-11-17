import time
from pathlib import Path

import requests


LOGIN_URL = "https://stadium.sports8.com.cn/StadiumHelper/login/loginServlet"
CAPTCHA_URL = "https://stadium.sports8.com.cn/StadiumHelper/common/checkCodeServlet"
INDEX_URL = "https://stadium.sports8.com.cn/StadiumHelper/index/PageIndexServlet?optype=toIndex"

USERNAME = "hehh"
PASSWORD = "20250805"


def save_captcha(session: requests.Session, out_path: Path) -> None:
    resp = session.get(
        CAPTCHA_URL,
        params={"width": 140, "height": 40, "ts": str(int(time.time() * 1000))},
        timeout=15,
        verify=False,
    )
    resp.raise_for_status()
    out_path.write_bytes(resp.content)


def main():
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/117.0.0.0 Safari/537.36"
        }
    )

    session.get(LOGIN_URL.replace("loginServlet", "login.jsp"), timeout=15, verify=False)

    captcha_dir = Path("./data/captcha")
    captcha_dir.mkdir(parents=True, exist_ok=True)

    for attempt in range(10):
        captcha_file = captcha_dir / f"captcha-{int(time.time())}.png"
        save_captcha(session, captcha_file)
        print(f"[Attempt {attempt+1}] Captcha saved at: {captcha_file.resolve()}")
        captcha = input("请输入图片中的验证码（输入 q 退出）: ").strip()
        if captcha.lower() == "q":
            print("退出登录流程。")
            return
        resp = session.post(
            LOGIN_URL,
            data={
                "loginname": USERNAME,
                "password": PASSWORD,
                "checkcode": captcha,
            },
            timeout=15,
            verify=False,
            allow_redirects=False,
        )
        if resp.status_code in (301, 302):
            target = resp.headers.get("Location")
            print("登录成功，重定向到:", target)
            break
        else:
            snippet = resp.text[:200]
            print("登录失败，服务器返回：")
            print(snippet)
    else:
        print("多次尝试后仍未登录成功，请重试。")
        return

    follow = session.get(INDEX_URL, timeout=15, verify=False)
    print("index status", follow.status_code)
    print("index first bytes", follow.text[:200])
    print("Cookies:", session.cookies.get_dict())


if __name__ == "__main__":
    main()

