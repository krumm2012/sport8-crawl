# Sport8 验证码识别方法分析报告

## 📋 概述

Sport8-Crawl 项目使用 **ddddocr** 库进行验证码自动识别。

## 🔧 核心实现

### 1. 识别引擎

```python
import ddddocr

class CaptchaRecognizer:
    def __init__(self):
        self.ocr = ddddocr.DdddOcr(show_ad=False)
```

**依赖库:**
- `ddddocr` - 开源 OCR 识别库（基于深度学习）
- `PIL/Pillow` - 图像处理

### 2. 识别流程

```
获取验证码图片 → 字节数据 → ddddocr.classification() → 清理结果
```

**代码示例:**
```python
def recognize_from_bytes(self, image_bytes):
    # 使用 ddddocr 识别
    result = self.ocr.classification(image_bytes)
    
    # 后处理
    result = result.strip().upper()  # 去空格、转大写
    result = ''.join(c for c in result if c.isalnum())  # 只保留字母数字
    
    return result
```

### 3. 图片预处理（可选）

```python
def preprocess_image(self, image_bytes):
    img = Image.open(io.BytesIO(image_bytes))
    
    # 1. 转换为 RGB
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # 2. 增强对比度
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    
    # 3. 锐化
    img = img.filter(ImageFilter.SHARPEN)
    
    return img
```

## 📊 使用方法

### 方法 1: 自动识别（推荐）

```python
from captcha_recognizer import CaptchaRecognizer

recognizer = CaptchaRecognizer()

# 从文件识别
result = recognizer.recognize_from_file("captcha.png")

# 从 URL 识别（使用 session）
result = recognizer.recognize_from_url(session, captcha_url)

# 从 base64 识别
result = recognizer.recognize_from_bytes(base64.b64decode(base64_str))
```

### 方法 2: 批量测试

```bash
# 测试单个图片
python3 captcha_recognizer.py -f data/captcha/captcha_test.png

# 批量测试目录
python3 captcha_recognizer.py -d data/captcha/

# 交互式模式
python3 captcha_recognizer.py -i
```

## 🚀 集成到登录流程

### 完整示例

```python
import requests
from captcha_recognizer import CaptchaRecognizer

# 1. 创建 session
session = requests.Session()

# 2. 获取验证码
captcha_url = "https://stadium.sports8.com.cn/StadiumHelper/common/checkCodeServlet"
params = {"width": 578, "height": 136, "ts": str(int(time.time() * 1000))}
resp = session.get(captcha_url, params=params, verify=False)

# 3. 自动识别验证码
recognizer = CaptchaRecognizer()
captcha_code = recognizer.recognize_from_bytes(resp.content)

print(f"识别结果: {captcha_code}")

# 4. 提交登录
login_endpoint = "https://stadium.sports8.com.cn/StadiumHelper/login/loginServlet"
payload = {
    "loginname": "hehh",
    "password": "20250805",
    "checkcode": captcha_code,
}
resp = session.post(login_endpoint, data=payload, verify=False)
```

## 📈 性能评估

### 优点
- ✅ **全自动** - 无需人工干预
- ✅ **快速** - 识别时间 < 1 秒
- ✅ **准确** - ddddocr 对简单验证码准确率 > 90%
- ✅ **开源免费** - 无 API 调用费用

### 缺点
- ⚠️ **依赖安装** - 需要安装 ddddocr（较大）
- ⚠️ **准确率** - 复杂验证码可能识别错误
- ⚠️ **不支持** - 极复杂验证码（如滑动、点击）

## 🔧 安装依赖

```bash
pip install ddddocr pillow
```

**注意:** ddddocr 依赖较多，安装可能需要几分钟。

## 📝 改进建议

### 1. 识别失败处理
```python
for attempt in range(3):  # 最多尝试 3 次
    captcha_code = recognizer.recognize_from_bytes(image_bytes)
    
    # 尝试登录
    success = try_login(captcha_code)
    
    if success:
        break
    
    # 失败则刷新验证码重试
    refresh_captcha()
```

### 2. 人工兜底
```python
captcha_code = recognizer.recognize_from_bytes(image_bytes)

# 让用户确认或修改
user_input = input(f"验证码识别结果 [{captcha_code}]，按 Enter 确认或输入新值: ")
if user_input.strip():
    captcha_code = user_input.strip()
```

### 3. 保存错误样本
```python
if not success:
    # 保存识别失败的验证码用于改进
    error_dir = Path("data/captcha/errors")
    error_dir.mkdir(parents=True, exist_ok=True)
    error_path = error_dir / f"error_{int(time.time())}.png"
    error_path.write_bytes(image_bytes)
```

## 🎯 实际应用

在 `unified_crawler.py` 中的使用:

```python
def auto_login(self):
    recognizer = CaptchaRecognizer() if CaptchaRecognizer else None
    
    for attempt in range(5):
        # 获取验证码图片
        captcha_src = captcha_img.get_attribute("src")
        
        if recognizer and "data:image" in captcha_src:
            # 自动识别
            captcha_code = recognizer.recognize_from_base64(
                captcha_src.split(",")[1]
            )
            print(f"自动识别结果: {captcha_code}")
        else:
            # 手动输入
            captcha_code = input("请输入验证码: ")
```

## 📚 参考

- **ddddocr 文档:** https://github.com/sml2h3/ddddocr
- **项目文件:** `captcha_recognizer.py`
- **使用示例:** `unified_crawler.py` (auto_login 方法)

---

**结论:** 使用 ddddocr 可以实现全自动验证码识别，准确率较高，适合 Sport8 的简单数字字母验证码。
