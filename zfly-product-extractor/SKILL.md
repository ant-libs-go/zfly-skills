---
name: zfly-product-extractor
description: 提取 Shopify、Shopline 或 Shoplazza 独立站商品的原始 JSON 数据和关联图片。当用户提供这些平台的商品链接并要求获取结构化数据、变体配置或下载商品图片时触发。
version: 1.0.0
---

# Extract Product Data (JSON Interface)

本技能通过 Chrome 自动化工具直接访问独立站的数据接口，获取最准确的原始 JSON 数据并解析。

## 全局配置与依赖

### 1. 脚本指令
- 脚本位于 `scripts/` 子目录下，`{main}` = `python {baseDir}/scripts/main.py`

### 2. 环境要求 (DEPENDENCIES)
1. **chrome-devtools MCP** 必须安装。
   - 安装命令: `<cli-command> mcp add chrome-devtools npx -y @modelcontextprotocol/server-chrome-devtools --scope user`
2. **jq** 必须安装（用于解析大型 JSON）。
   - 检查命令: `jq --version`
   - 引导安装: 
     - macOS: `brew install jq`
     - Linux: `sudo apt-get install jq`

## 核心约束 (STRICT RULES)
1. **必须按工作流执行**：禁止跳过工作流，比如通过猜测的方式判断属于什么平台。
2. **浏览器访问**：严禁使用 `curl` 或外部 Python 脚本向接口或网页发起请求。必须在当前浏览器的上下文（Session/Cookie）内完成访问。
3. **规避截断**：严禁通过 `innerText` 或 `evaluate_script` 将大型 JSON 读入对话框（会导致内容截断）。必须使用 `get_network_request` 并通过 `responseFilePath` 参数直接将数据落盘。
4. **禁止行为**：严禁通过 `take_snapshot` 分析网页 DOM 结构来汇总数据。

## 核心工作流

### 1. 根据用户输入的 URL 推导所属的平台
- 接收商品 URL 后，通过浏览器 `chrome-devtools` 访问该 URL，使用以下规则推导所属平台：
    - 如果用户已经告诉了是哪家平台则跳过该步骤。
    - 统计页面源码（`page.content()`）中关键字的出现频次：`shopify`、`shopline`、`shoplazza`，频次最高者即判定为该平台。
    - 如果用户提供的平台不属于`shopify`、`shopline`、`shoplazza`，或源码中均未出现平台关键字则通知用户不支持该平台。
- **严禁通过 URL 路径以及经验猜测所属平台，必须通过上述方案进行推导。**

### 2. 根据所属平台构造数据接口 URL
- **Shopify**: 
    - 在原 URL 末尾添加 `.json`。
    - 例如：`https://domain.com/products/shoes` -> `https://domain.com/products/shoes.json`。
- **Shopline**: 
    - 提取 URL 中的 `handle`（最后一个路径段）并构造为 `https://{netloc}/api/product/products.json?handle={handle}`。
    - 例如：`https://domain.com/products/shoes` -> `https://domain.com/api/product/products.json?handle=shoes`
- **Shoplazza**: 
    - 访问原始 URL 并从源码中正则匹配 `product_id`（规则：`product_id["']?\s*[:=]\s*["']([^"']+)["']` 或 `og:product_id` 元标签）。
    - 构造 `https://{netloc}/api/products/{product_id}`。

### 3. 访问与数据持久化
- **创建目录**: 提取 handle 并**删除所有 Emoji**，在当前工作空间创建该 handle 命名的目录（若已存在则加序号，如`-1/-2`）。
- **访问接口**：使用浏览器访问 **数据接口 URL**。
- **定位请求**: 使用 `mcp_chrome-devtools_list_network_requests` 找到该数据接口 URL 对应的 `reqid`。
- **直接落盘**: 调用 `mcp_chrome-devtools_get_network_request(reqid=..., responseFilePath="{handle}/product.json")`。
- **合法性校验**: 执行 `jq '.' {handle}/product.json` 验证其为有效的 JSON 格式。

### 4. 解析并下载图片
- 运行 `{main} download-images --data {handle}/product.json --jq-path "<jq_表达式>" --output-dir {handle}/images`
- **各平台对应的 `--jq-path` 参数**:
    - **Shopify**: `--jq-path '.product.images[].src'`
    - **Shopline**: `--jq-path '.products[0].images[]'`
    - **Shoplazza**: `--jq-path '.data.product.images[].src'`
- **脚本自动完成以下操作**:
    - 通过 `jq` 提取图片 URL
    - 以 `https:` 开头补全（处理 `//` 前缀）
    - 去除 URL 中的查询参数（如 `?v=...`）
    - 从 URL 中提取并保留文件后缀（如 `.jpg`、`.png`），无后缀则默认为 `.jpg`
    - 按 `001`、`002`... 顺序命名并下载到 `{handle}/images/` 目录
- **输出**: 打印所有下载成功的文件名及汇总信息。

### 5. 完成任务
- 输出数据文件的保存路径
- 输出图片文件的保存路径及所有文件名。
- 如果没有错误则在完成任务后关闭使用后的浏览器（除非用户要求不关闭）。

## 异常处理
- **验证码**：引导用户在浏览器窗口手动完成验证后继续。
