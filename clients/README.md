# MCP 客户端配置模板

`mcp.json` 是给 **使用者** 复制粘贴用的，本项目的代码不会读取它。

使用前把里面两处 `REPLACE_WITH_PROJECT_DIR` 换成你自己的项目目录（绝对路径），例如项目放在 `D:\tools\memobird-mcp`：

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

注意：

- Windows 路径里的 `\` 在 JSON 中要写成 `\\`
- macOS / Linux 把 `.venv\\Scripts\\python.exe` 换成 `.venv/bin/python`
- 前提是已经在该目录执行过 `uv sync`，`.venv` 才存在
- 凭据读项目根目录的 `.env`，不需要写进这份配置
