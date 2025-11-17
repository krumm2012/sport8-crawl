from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, Optional

import requests
from requests import Session

from .config import Settings
from .utils import parse_local_storage, with_base


class LoginError(RuntimeError):
    """Raised when the interactive login fails after multiple attempts."""


class Sport8Client:
    """HTTP client responsible for authenticating and performing API calls."""

    def __init__(self, settings: Settings, session: Optional[Session] = None) -> None:
        self.settings = settings
        requests.packages.urllib3.disable_warnings()  # type: ignore[attr-defined]
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/117.0.0.0 Safari/537.36"
                ),
                "Origin": self.base_url,
            }
        )
        self.tokens: Dict[str, str] = {}

    @property
    def base_url(self) -> str:
        return self.settings.base_url

    def _captcha_path(self) -> Path:
        folder = Path("data") / "captcha"
        folder.mkdir(parents=True, exist_ok=True)
        return folder / f"captcha-{int(time.time())}.png"

    def fetch_captcha(self) -> Path:
        """Download captcha image and return the path."""
        params = {"width": 578, "height": 136, "ts": str(int(time.time() * 1000))}
        resp = self.session.get(
            with_base(self.base_url, "/StadiumHelper/common/checkCodeServlet"),
            params=params,
            timeout=20,
            verify=False,
        )
        resp.raise_for_status()
        path = self._captcha_path()
        path.write_bytes(resp.content)
        return path

    def _open_captcha(self, path: Path) -> None:
        try:
            resolved = str(path.resolve())
            if sys.platform.startswith("darwin"):
                os.system(f"open '{resolved}'")
            elif sys.platform.startswith("win"):
                os.startfile(resolved)  # type: ignore[attr-defined]
            elif sys.platform.startswith("linux"):
                os.system(f"xdg-open '{resolved}' >/dev/null 2>&1")
        except Exception:
            pass

    def _initialise_session(self) -> None:
        login_page = with_base(self.base_url, "/StadiumHelper/login/login.jsp")
        self.session.get(login_page, timeout=20, verify=False)
        self.session.headers["Referer"] = login_page

    @staticmethod
    def _extract_alert(html: str) -> str:
        match = re.search(r'id="myAlertMsg">([^<]*)', html)
        return match.group(1).strip() if match else ""

    def interactive_login(self, max_attempts: int = 10) -> None:
        """Prompt the user to solve captchas until authentication succeeds."""
        self._initialise_session()

        login_endpoint = with_base(
            self.base_url, "/StadiumHelper/login/loginServlet"
        )

        for attempt in range(1, max_attempts + 1):
            captcha_path = self.fetch_captcha()
            print(
                f"[尝试 {attempt}/{max_attempts}] "
                f"验证码已保存：{captcha_path.resolve()}"
            )
            self._open_captcha(captcha_path)
            code = input("请输入图片中的验证码（输入 q 退出）: ").strip()
            if code.lower() == "q":
                raise LoginError("用户取消登录。")

            payload = {
                "loginname": self.settings.username,
                "password": self.settings.password,
                "checkcode": code,
            }
            resp = self.session.post(
                login_endpoint,
                data=payload,
                timeout=20,
                verify=False,
                allow_redirects=False,
            )

            if resp.status_code in (301, 302) and "Location" in resp.headers:
                print("登录成功，正在加载主页...")
                location = resp.headers["Location"]
                print(f"登录重定向地址：{location}")
                try:
                    self._populate_tokens_from_location(location)
                except LoginError:
                    try:
                        self._populate_tokens_from_page()
                    except LoginError:
                        self._debug_response(resp, "redirect")
                        raise
                else:
                    return

                return

            if resp.url.endswith("login.jsp"):
                message = self._extract_alert(resp.text)
                if message:
                    print(f"登录失败，服务器返回：{message}")
                else:
                    print("登录失败，服务器返回：")
                    print(resp.text[:200])
                continue

            print("登录成功，正在加载主页...")
            try:
                self._populate_tokens_from_response(resp)
            except LoginError:
                try:
                    self._populate_tokens_from_page()
                except LoginError:
                    self._debug_response(resp, "page")
                    self._dump_cookies()
                    raise
            return

        raise LoginError("多次尝试后仍未成功登录。")

    def _populate_tokens_from_response(self, response: requests.Response) -> None:
        try:
            payload = response.json()
        except ValueError as exc:
            self._debug_response(response, "login_response")
            raise LoginError("登录成功，但响应不是预期的 JSON。") from exc

        result = payload.get("result_data") or {}
        tokens = {
            "setUserid": result.get("userId"),
            "setStadiumId": result.get("stadiumId"),
            "setToken": result.get("token"),
            "setCode": result.get("code"),
            "setCustId": result.get("custId"),
            "setLoginname": result.get("loginname"),
            "setMobile": result.get("mobile"),
        }
        missing = [key for key, value in tokens.items() if not value]
        if missing:
            raise LoginError(
                f"登录成功，但缺少认证字段：{', '.join(missing)}。"
            )
        cleaned_tokens = {k: v for k, v in tokens.items() if v is not None}
        self.tokens = cleaned_tokens  # type: ignore[assignment]

    def _populate_tokens_from_page(self) -> None:
        index_url = with_base(
            self.base_url, "/StadiumHelper/index/PageIndexServlet?optype=toIndex"
        )
        resp = self.session.get(index_url, timeout=20, verify=False)
        resp.raise_for_status()
        self.tokens = parse_local_storage(resp.text)

        required_keys = ["setUserid", "setStadiumId", "setToken", "setCode"]
        missing = [key for key in required_keys if key not in self.tokens]
        if missing:
            self._debug_response(resp, "page_missing")
            self._dump_cookies()
            raise LoginError(
                f"登录成功，但仍未获取到认证字段：{', '.join(missing)}。"
            )

    def _populate_tokens_from_location(self, location: str) -> None:
        from urllib.parse import urlparse, parse_qs

        parsed = urlparse(location)
        query = parse_qs(parsed.query)

        token_map = {
            "setUserid": ["userid", "userId"],
            "setStadiumId": ["stadiumId", "stadiumid"],
            "setToken": ["token"],
            "setCode": ["code"],
            "setCustId": ["custId", "custid"],
            "setLoginname": ["loginname", "loginName"],
            "setMobile": ["mobile", "phone"],
        }

        tokens: Dict[str, str] = {}
        for target_key, possible_keys in token_map.items():
            for key in possible_keys:
                values = query.get(key)
                if values:
                    tokens[target_key] = values[0]
                    break

        cleaned_tokens = {k: v for k, v in tokens.items() if v}
        if not cleaned_tokens:
            raise LoginError("登录成功，但跳转链接中未包含登录凭据。")

        self.tokens = cleaned_tokens  # type: ignore[assignment]

        if parsed.path:
            follow_url = with_base(self.base_url, parsed.path + ("?" + parsed.query if parsed.query else ""))
            self.session.get(follow_url, timeout=20, verify=False)

    def _debug_response(
        self, response: Optional[requests.Response], suffix: str
    ) -> None:
        try:
            debug_dir = Path("data") / "debug"
            debug_dir.mkdir(parents=True, exist_ok=True)
            timestamp = int(time.time())
            if response is not None:
                path = debug_dir / f"login-debug-{suffix}-{timestamp}.txt"
                path.write_text(response.text[:4000], encoding="utf-8")
        except Exception:
            pass

    def _dump_cookies(self) -> None:
        try:
            debug_dir = Path("data") / "debug"
            debug_dir.mkdir(parents=True, exist_ok=True)
            timestamp = int(time.time())
            cookies_path = debug_dir / f"cookies-{timestamp}.txt"
            lines = [
                f"{name}={value}"
                for name, value in self.session.cookies.get_dict().items()
            ]
            cookies_path.write_text("\n".join(lines), encoding="utf-8")
        except Exception:
            pass

    def api_post(self, path: str, json: Dict[str, str]) -> requests.Response:
        if not self.tokens:
            raise RuntimeError("尚未登录，无法调用 API。")

        headers = {
            "Authorization": f"Bearer {self.tokens.get('setCode','')}",
            "Content-Type": "application/json",
        }
        resp = self.session.post(
            with_base(self.base_url, path),
            json=json,
            headers=headers,
            timeout=30,
            verify=False,
        )
        resp.raise_for_status()
        return resp

