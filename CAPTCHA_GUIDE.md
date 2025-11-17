# 验证码识别指南

## 📋 概述

本项目提供了通用的验证码识别工具，专门针对 `https://stadium.sports8.com.cn/StadiumHelper/` 的验证码。

**识别效果**：
- ✅ 成功率：100%（基于测试样本）
- ✅ 速度：< 1 秒
- ✅ 支持：4位字母验证码
- ✅ 引擎：ddddocr（带带弟弟 OCR）

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install ddddocr
```

### 2. 测试识别

```bash
# 测试默认目录（data/captcha/）
python3 captcha_recognizer.py

# 测试单个图片
python3 captcha_recognizer.py -f captcha.png

# 批量测试目录
python3 captcha_recognizer.py -d data/captcha/

# 交互式模式
python3 captcha_recognizer.py -i
```

---

## 📖 使用方法

### 方法 1：命令行工具

#### 测试单个图片

```bash
python3 captcha_recognizer.py -f data/captcha/captcha-1763111888.png
```

**输出示例**：
```
======================================================================
测试单个验证码
======================================================================

图片: data/captcha/captcha-1763111888.png
✓ 已加载 ddddocr 识别引擎

✓ 识别结果: RGC5
  长度: 4 个字符

======================================================================
```

#### 批量测试目录

```bash
python3 captcha_recognizer.py -d data/captcha/
```

**输出示例**：
```
======================================================================
批量测试验证码识别
目录: data/captcha
======================================================================

找到 2 个图片文件

[1/2] captcha-1763111994.png
  ✓ 识别结果: MWMN

[2/2] captcha-1763111888.png
  ✓ 识别结果: RGC5

======================================================================
识别完成: 2/2 成功
成功率: 100.0%
======================================================================
```

#### 测试预处理效果

```bash
python3 captcha_recognizer.py -f captcha.png -p
```

这会测试图片预处理（对比度增强、锐化）对识别效果的影响。

#### 交互式模式

```bash
python3 captcha_recognizer.py -i
```

提供交互式菜单，可以选择不同的测试模式。

---

### 方法 2：在 Python 代码中使用

#### 基本使用

```python
from captcha_recognizer import CaptchaRecognizer

# 创建识别器
recognizer = CaptchaRecognizer()

# 从文件识别
result = recognizer.recognize_from_file("captcha.png")
print(f"识别结果: {result}")

# 从字节数据识别
with open("captcha.png", "rb") as f:
    image_bytes = f.read()
result = recognizer.recognize_from_bytes(image_bytes)
print(f"识别结果: {result}")
```

#### 从 URL 识别

```python
import requests
from captcha_recognizer import CaptchaRecognizer

# 创建会话
session = requests.Session()

# 创建识别器
recognizer = CaptchaRecognizer()

# 从 URL 识别
captcha_url = "https://stadium.sports8.com.cn/StadiumHelper/login/loginServlet?action=getCheckCode"
result = recognizer.recognize_from_url(session, captcha_url)
print(f"识别结果: {result}")
```

#### 批量测试

```python
from captcha_recognizer import CaptchaRecognizer

recognizer = CaptchaRecognizer()
recognizer.batch_test("data/captcha/")
```

---

## 🔧 API 参考

### CaptchaRecognizer 类

#### `__init__()`
初始化识别器，自动加载 ddddocr 引擎。

#### `recognize_from_file(image_path)`
从文件识别验证码。

**参数**：
- `image_path` (str): 图片文件路径

**返回**：
- `str`: 识别结果，失败返回 `None`

**示例**：
```python
result = recognizer.recognize_from_file("captcha.png")
```

#### `recognize_from_bytes(image_bytes)`
从字节数据识别验证码。

**参数**：
- `image_bytes` (bytes): 图片字节数据

**返回**：
- `str`: 识别结果，失败返回 `None`

**示例**：
```python
with open("captcha.png", "rb") as f:
    result = recognizer.recognize_from_bytes(f.read())
```

#### `recognize_from_url(session, captcha_url)`
从 URL 识别验证码。

**参数**：
- `session` (requests.Session): requests 会话对象
- `captcha_url` (str): 验证码 URL

**返回**：
- `str`: 识别结果，失败返回 `None`

**示例**：
```python
import requests
session = requests.Session()
result = recognizer.recognize_from_url(session, "https://example.com/captcha")
```

#### `preprocess_image(image_bytes, save_path=None)`
预处理图片（增强对比度、锐化）。

**参数**：
- `image_bytes` (bytes): 原始图片字节
- `save_path` (str, 可选): 保存路径

**返回**：
- `bytes`: 处理后的图片字节

**示例**：
```python
with open("captcha.png", "rb") as f:
    processed = recognizer.preprocess_image(f.read(), "processed.png")
```

#### `batch_test(image_dir)`
批量测试目录中的验证码图片。

**参数**：
- `image_dir` (str): 图片目录路径

**示例**：
```python
recognizer.batch_test("data/captcha/")
```

---

## 🎯 集成到爬虫

### 更新 auto_crawl.py（自动识别版本）

如果你想让 `auto_crawl.py` 自动识别验证码，可以这样修改：

```python
from captcha_recognizer import CaptchaRecognizer

# 在 auto_login_and_extract 函数中
def auto_login_and_extract():
    # ... 前面的代码 ...
    
    # 创建验证码识别器
    recognizer = CaptchaRecognizer()
    
    # 获取验证码
    captcha_url = f"{BASE_URL}/StadiumHelper/login/loginServlet?action=getCheckCode"
    
    # 尝试自动识别
    max_attempts = 3
    for attempt in range(max_attempts):
        print(f"\n尝试识别验证码 ({attempt+1}/{max_attempts})...")
        
        # 识别验证码
        captcha_text = recognizer.recognize_from_url(driver, captcha_url)
        
        if captcha_text and len(captcha_text) == 4:
            print(f"✓ 识别结果: {captcha_text}")
            
            # 自动填写验证码
            captcha_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='验证码']")
            captcha_input.clear()
            captcha_input.send_keys(captcha_text)
            
            # 点击登录
            login_button = driver.find_element(By.CSS_SELECTOR, "button.log-form-submit")
            login_button.click()
            
            # 等待登录结果
            time.sleep(2)
            
            # 检查是否登录成功
            if "login" not in driver.current_url.lower():
                print("✓ 登录成功！")
                break
            else:
                print("✗ 验证码错误，重试...")
        else:
            print(f"✗ 识别失败: {captcha_text}")
    
    # ... 后面的代码 ...
```

---

## 📊 识别效果

### 测试结果

基于 `data/captcha/` 目录中的样本：

| 图片 | 实际验证码 | 识别结果 | 状态 |
|------|-----------|---------|------|
| captcha-1763111888.png | RGC5 | RGC5 | ✅ 正确 |
| captcha-1763111994.png | MWMN | MWMN | ✅ 正确 |

**成功率**: 100% (2/2)

### 验证码特点

该网站的验证码具有以下特点：

1. **字符数量**: 4 个字符
2. **字符类型**: 大写字母
3. **颜色**: 彩色字符（橙、绿、紫、棕等）
4. **干扰**: 有干扰线
5. **倾斜**: 字符有轻微倾斜
6. **背景**: 白色背景 + 干扰线

### 识别策略

ddddocr 引擎能够很好地处理这种类型的验证码：
- ✅ 自动去除干扰线
- ✅ 自动处理倾斜
- ✅ 自动识别彩色字符
- ✅ 无需预处理

---

## 🔍 故障排除

### 问题 1: 未安装 ddddocr

**错误信息**:
```
⚠️  未安装 ddddocr，请运行: pip install ddddocr
```

**解决方案**:
```bash
pip install ddddocr
```

### 问题 2: 识别率低

**可能原因**:
- 验证码图片质量差
- 验证码格式变化

**解决方案**:
1. 尝试预处理：
   ```bash
   python3 captcha_recognizer.py -f captcha.png -p
   ```

2. 收集更多失败样本，调整预处理参数

### 问题 3: 识别速度慢

**可能原因**:
- 首次加载 ddddocr 模型较慢

**解决方案**:
- 正常现象，首次加载后会缓存模型
- 后续识别速度会很快（< 1 秒）

---

## 💡 高级用法

### 自定义预处理

如果默认的预处理效果不好，可以自定义：

```python
from PIL import Image, ImageEnhance, ImageFilter
import io

def custom_preprocess(image_bytes):
    img = Image.open(io.BytesIO(image_bytes))
    
    # 转灰度
    img = img.convert('L')
    
    # 二值化
    threshold = 128
    img = img.point(lambda x: 0 if x < threshold else 255, '1')
    
    # 转回字节
    output = io.BytesIO()
    img.save(output, format='PNG')
    return output.getvalue()

# 使用
recognizer = CaptchaRecognizer()
with open("captcha.png", "rb") as f:
    processed = custom_preprocess(f.read())
    result = recognizer.recognize_from_bytes(processed)
```

### 多引擎尝试

如果单个引擎识别率不高，可以尝试多个引擎：

```python
def recognize_with_fallback(image_bytes):
    # 尝试 ddddocr
    recognizer = CaptchaRecognizer()
    result = recognizer.recognize_from_bytes(image_bytes)
    
    if result and len(result) == 4:
        return result
    
    # 尝试其他引擎（如 pytesseract）
    # ...
    
    return None
```

---

## 📚 相关文档

- [项目总览](readme.md)
- [快速开始](QUICKSTART.md)
- [一键运行指南](ONE_CLICK_GUIDE.md)
- [自动登录指南](AUTO_LOGIN_GUIDE.md)

---

## 🔗 参考资源

- [ddddocr 项目](https://github.com/sml2h3/ddddocr)
- [Pillow 文档](https://pillow.readthedocs.io/)


