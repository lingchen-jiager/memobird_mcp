# memobird-mcp

把咕咕机（Memobird 热敏打印机）接进 AI 对话，或者用一行 Python 直接出纸。

- **MCP 服务**：标准 Model Context Protocol，WorkBuddy / Claude Desktop / Cursor 等客户端可直接挂载
- **快速出纸**：`uv run memobird text "..."` 或 `import memobird_mcp as mb; mb.text("...")`
- **零硬编码密钥**：凭据只从 `.env` 或环境变量读取，仓库里只有占位符
- **标准 uv 项目**：`uv sync` 一把装好，依赖锁定在 `uv.lock`

---

## 一、目录结构

```
memobird-mcp/
├── pyproject.toml          # 项目定义与依赖
├── uv.lock                 # 依赖锁（建议入库）
├── .python-version         # 固定 3.12
├── .env.example            # 凭据模板（占位符，可入库）
├── .env                    # 你的真实凭据（已被 .gitignore 忽略）
├── run.py                  # 启动入口，python run.py 即可，无需安装
├── start-sse.bat           # 双击以 SSE 方式起服务
├── LICENSE
├── README.md
├── clients/                # MCP 客户端配置模板
│   └── mcp.json            # 粘贴前改掉 REPLACE_WITH_PROJECT_DIR
└── src/memobird_mcp/
    ├── __init__.py         # 对外导出 mb.text / mb.image / mb.mixed ...
    ├── config.py           # 读 .env / 环境变量、校验凭据
    ├── client.py           # 开放平台 HTTP 客户端（三层结构）
    ├── tools.py            # 把打印能力注册成 MCP 工具
    ├── server.py           # stdio / sse / http 三种传输
    ├── quick.py            # 一行代码出纸的便捷封装
    └── cli.py              # 命令行 memobird
```

## 二、前置条件

1. **uv**：`uv --version` 能输出版本即可（本项目在 uv 0.7.x 上验证）。
2. **Python 3.12**：`.python-version` 已写死为 `3.12`。`uv sync` 会优先使用本机已安装的 3.12，**不会**额外下载新的解释器。
3. **咕咕机 + 开发者账号**：到 [open.memobird.cn](https://open.memobird.cn) 注册开发者、添加设备，拿到两样东西：
   - `ak`：开发者 API Key
   - `memobirdID`：设备号

## 三、安装

```bash
cd memobird-mcp        # 进到你 clone / 解压出来的目录
uv sync
```

执行后会出现 `.venv/` 与 `uv.lock`，同时把 `memobird_mcp` 以可编辑模式装进虚拟环境。

## 四、配置凭据（唯一需要手动填的东西）

```bash
cp .env.example .env
```

然后编辑 `.env`，填两行：

```ini
MEMOBIRD_AK=你的开发者AK
MEMOBIRD_DEVICE_ID=你的设备号
```

说明：

- `.env` 已在 `.gitignore` 里，不会被提交。
- 代码中没有任何真实密钥，`.env.example` 里只有占位符。
- 如果系统里已经设置了同名环境变量，**环境变量优先**（`.env` 不会覆盖已有值）。
- 也可以在启动时用 `--ak` / `--did` 临时覆盖，但会被同一进程的所有调用继承，注意别把命令行历史留成泄漏点。

**验证配置**（只绑定设备，不出纸）：

```bash
uv run memobird whoami
# 设备 <你的设备号> 绑定成功，userID = <你的 userID>
```

---

## 五、接入 WorkBuddy（MCP）

思路只有一句话：**把项目下载到本地，然后在配置里把路径改成你自己电脑上的实际路径。**

作者机器上的路径写进文档没有意义——你机器上不存在，所以模板里一律是 `REPLACE_WITH_PROJECT_DIR`，由你来替换。

> **WorkBuddy 的操作入口**：左下角 `+` → 连接器 → 添加自定义 MCP → 粘贴 JSON → 保存 → 在列表里点一次"信任 / 启用" → 开新会话。

### 1. 先把项目装起来

下载仓库 ZIP 解压（或 `git clone`），然后：

```bash
cd 你解压出来的目录/memobird-mcp
uv sync
cp .env.example .env      # 填入 AK 与设备号
```

`uv sync` 之后目录里会出现 `.venv\Scripts\python.exe`，下一步的配置就是要指向它。

### 2. 复制模板，改两个路径

`clients/mcp.json` 的内容：

```json
{
  "mcpServers": {
    "memobird": {
      "command": "REPLACE_WITH_PROJECT_DIR\\.venv\\Scripts\\python.exe",
      "args": ["REPLACE_WITH_PROJECT_DIR\\run.py"]
    }
  }
}
```

把两处 `REPLACE_WITH_PROJECT_DIR` 换成你自己的目录，例如项目放在 `D:\tools\memobird-mcp`：

```json
{
  "mcpServers": {
    "memobird": {
      "command": "D:\\tools\\memobird-mcp\\.venv\\Scripts\\python.exe",
      "args": ["D:\\tools\\memobird-mcp\\run.py"]
    }
  }
}
```

两个要点：

- Windows 路径里的 `\` 在 JSON 中必须写成 `\\`，写单反斜杠会解析失败
- macOS / Linux 把 `.venv\\Scripts\\python.exe` 换成 `.venv/bin/python`

### 3. 粘贴并信任

保存配置后**一定要在列表里点一次"信任 / 启用"**，然后开一个新会话。新增的自定义 MCP 不会自动生效，这一步最容易漏。

### 4. 验证

新会话里问一句"你现在有哪些 memobird 工具"，应该能看到 5 个：`print_text`、`print_image`、`print_url`、`print_mixed`、`print_status`。

接着直接说人话即可：

- "帮我把这句话打印出来：今天下午三点开会"
- "打印这张图 D:\photo.png"
- "查一下 71514704 出纸了没有"

### 5. 连不上时按这个顺序查

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 工具列表里没有 memobird | 没点"信任" / 配置没保存 | 重新保存并信任，再开新会话 |
| 提示找不到文件或程序 | 路径写错，或项目被移动/改名 | 把 `command` 里的路径粘到资源管理器地址栏，确认 python.exe 真的存在 |
| 调用时报"缺少凭据" | `.env` 没建或没填 | 在项目目录执行 `uv run memobird whoami` 先验证 |
| 进程秒退、没有任何输出 | stdio 模式在等客户端握手 | 正常现象，不要手动单独运行后干等 |
| 返回了 Content ID 但不出纸 | 打印机离线 / 没纸 / 电量低 | 检查设备；用 `print_status` 复查 |
| 报 HTTP 错误 | 后端是明文 HTTP，可能被网络拦截 | 浏览器打开 `http://open.memobird.cn` 看通不通 |

> 提醒：项目一旦挪位置，配置里的两个路径要同步改，否则 MCP 会启动失败。

---

## 六、Python 模块 / 命令行快速出纸

### 1. 命令行（最快，无需写代码）

在本项目目录下：

```bash
uv run memobird text "今天下午三点开会"
uv run memobird image D:\photo.png
uv run memobird mixed "会议纪要" -i D:\photo.png
uv run memobird url https://example.com
uv run memobird status 71514704
uv run memobird whoami
```

不在项目目录里也行，加 `--directory`：

```bash
uv run --directory /path/to/memobird-mcp memobird text "hi"
```

参数说明：

- `text` 后面可以跟多段，会用空格拼成一句
- `mixed` 把文字和图片印在同一张小票上，`-i` 指定图片
- `-v` 打开 DEBUG 日志（输出到 stderr，不干扰结果）
- 退出码：`0` 成功，`1` 打印失败，`2` 凭据缺失

### 2. 在 Python 里一行调用

在项目里写脚本，用 `uv run` 执行：

```python
import memobird_mcp as mb

content_id = mb.text("你好，咕咕机")
print("Content ID:", content_id)

mb.image(r"D:\photo.png")
mb.url("https://example.com")
mb.status(content_id)
```

图文混排：

```python
from PIL import Image
import memobird_mcp as mb

mb.mixed("今日待办\n1. 写周报\n2. 三点开会", Image.open(r"D:\photo.png"))
```

想在**别的项目**里用，把它装进去即可：

```bash
uv add --editable /path/to/memobird-mcp
```

### 3. 更底层一点的写法

需要复用同一台设备、或自己控制连接时：

```python
from memobird_mcp import MemobirdDevice, PrintPayloadBuilder
from memobird_mcp.config import get_credentials

ak, device_id = get_credentials()
bird = MemobirdDevice(ak=ak, device_id=device_id)   # 构造时绑定一次，之后复用

cid = bird.print_text("hello")
bird.print_payload(
    PrintPayloadBuilder()
    .add_text("小票标题")
    .add_image(r"D:\photo.png")
    .add_text("——完——")
)
bird.check_print_status(cid)
```

设置环境变量优先级：显式传参 > 系统环境变量 > `.env`。

---

## 七、SSE / HTTP（给局域网设备或其他语言）

```bash
uv run python run.py -t sse -p 8000 --host 0.0.0.0
```

或者直接双击项目根目录的 `start-sse.bat`（固定监听 `0.0.0.0:8000`）。

- SSE 入口：`http://127.0.0.1:8000/sse`
- 首个事件返回 `event: endpoint` + `data: /messages/?session_id=xxx`，之后所有 JSON-RPC 通过 POST 发到该地址
- 局域网设备用本机内网 IP 访问，记得放行 Windows 防火墙对应端口
- 一个 SSE 连接对应一个会话，多设备并发请起多实例或多端口
- 也有 `-t http`（streamable HTTP），给支持该传输的客户端用

---

## 八、可用工具一览

| 工具 | 参数 | 说明 |
| --- | --- | --- |
| `print_text` | `text: str` | 纯文本，GBK 编码 |
| `print_image` | `image_path: str` | 本地绝对路径，或 `data:image/png;base64,...` |
| `print_url` | `url: str` | 由咕咕机服务端抓取渲染，URL 必须公网可访问 |
| `print_mixed` | `text: str`, `image_path: str = ""` | 图文混排成一张小票 |
| `print_status` | `content_id: int` | 查询是否已出纸 |

前四个工具都返回 `Content ID: xxx`，可再用 `print_status` 复查。

---

## 九、已知限制与坑

1. **emoji 与生僻字会静默消失**：开放平台要求 GBK 编码，无法编码的字符直接被丢弃，不会报错。
2. **图片会被缩放**：超过 384px 宽等比缩到 384px，再转 1 位黑白。细节多的照片出来偏灰，建议先用高对比度版本。
3. **`print_url` 只能打公网页面**：内网地址、需要登录的页面打不出来。
4. **后端是明文 HTTP**（`http://open.memobird.cn/home`）：个别网络环境会被拦截或劫持，报网络错误先查这个域名通不通。
5. **AK 有每日打印条数限制**：超限时开放平台返回 `showapi_res_code != 1`。
6. **每次启动都会调一次 `setuserbind`**：这是正常设计，幂等，返回同一个 userID。
7. **不要移动或删除 `.venv`**：MCP 配置里的 `command` 指向它的绝对路径，搬家后必须同步改配置。
8. **stdout 只能有 JSON-RPC**：stdio 模式下任何 `print()` 都会污染协议流，所以本项目日志统一写 stderr。

---

## 十、安全须知

- 真实 AK **只**存在于 `.env` 一个文件里，其余文件（含本 README、代码、`clients/` 模板）全是占位符。
- 分享、截图、上传这个项目前，确认 `.env` 已被排除；`.gitignore` 已经帮你挡住了 `git`，但压缩包/网盘不会。
- 不要把自己的 AK 贴到聊天窗口、issue、论坛里。AK 等同于"能往你打印机上出纸的凭证"。
- 一旦怀疑泄漏，去 open.memobird.cn 重置 AK，然后只改 `.env` 一处，不用动代码。

---

## 十一、发布前的检查清单

```bash
# 1. 确认 .env 已被忽略
git check-ignore -v .env          # 应输出 .gitignore:xxx:.env

# 2. 全文扫描，只应命中 .env（其余文件都该是占位符）
grep -rnE '\b[0-9a-f]{32}\b' . --exclude-dir=.venv --exclude-dir=.git

# 3. 确认没把本机绝对路径写进仓库（应无输出）
grep -rnE 'C:\\\\Users|/Users/|/home/' . --exclude-dir=.venv --exclude-dir=.git
```

- **该提交**：`.env.example`、`clients/mcp.json`、`uv.lock`、`LICENSE`、`README.md`
- **不该提交**：`.env`、`.venv/`、`__pycache__/`
- `pyproject.toml` 里的 `authors` 记得改成你自己的
- 想让别人能直接 `pip install` / `uv add`，把包发到 PyPI 即可（`uv build && uv publish`）；国内用户走 `UV_DEFAULT_INDEX` 或清华镜像会快很多。不想发 PyPI 也没关系，别人下载 ZIP 照样能用。
