---
name: zfly-shoplazza-migrator
description: 将 Shopify/Shopline/Shoplazza 商品数据迁移到指定 shoplazza 店铺，迁移过程中可以对商品进行编辑，比如价格调整、变体拆分、属性修改。当用户提到"同步商品"、"创建商品"、"上架到 Shoplazza"，或提供商品链接要求将商品迁移到 Shoplazza 时触发。
version: 1.2.0
---

# Shoplazza Product Creator

创建 Shoplazza 独立站商品。通过调用内部 Python 脚本处理复杂的 API 交互与数据转换，由代理负责流程调度与用户确认。

## 全局配置与依赖

### 1. 脚本指令
- 脚本位于 `scripts/` 子目录下， `{main}` = `python {baseDir}/scripts/main.py`

### 2. 首次运行配置 (BLOCKING)
如果当前工作空间缺失 `.env.json`，**必须** 引导用户：
1. 使用 `AskUserQuestion` 获取 `spz_slug` (店铺 Slug) 和 `spz_access_token` (Access Token)。
2. 获取答案后，生成如下格式 JSON 数据并保存到工作空间的 `.env.json` 文件。
   ```json
   {
     "spz_slug": "ANS_1",
     "spz_access_token": "ANS_2"
   }
   ```

### 3. 环境要求 (DEPENDENCIES)
1. **chrome-devtools MCP** 必须安装。
   - 安装命令: `<cli-command> mcp add chrome-devtools npx -y @modelcontextprotocol/server-chrome-devtools --scope user`
2.  **jq** 必须安装（用于解析大型 JSON）。
    - 检查命令: `jq --version`
    - 引导安装: 
      - macOS: `brew install jq`
      - Linux: `sudo apt-get install jq`

## 核心工作流

### 1. 获取商品数据
- **输入为链接**：必须激活并遵循 skill `zfly-product-extractor`，获取商品数据文件 `product.json` 的本地路径。
- **输入为文件**：直接获取该文件的本地路径。

### 2. 转换为 shoplazza 商品数据格式
- 运行 `{main} parse --data "<raw_json_path>"`，脚本负责将不同来源的数据统一映射为标准的 Shoplazza JSON 结构。
- **解析结果保存到与输入文件同级目录**：
    - `product_basic.json` — 结构化数据（JSON 数组格式，每个元素为一个 SPU）。
    - `product_description.json` — 商品描述文本。
- **脚本输出摘要信息及路径**：标题、描述长度、选项概览、图片数、变体数、`FILE_PATH`（product_basic.json 完整路径）、`DESC_PATH`（product_description.json 完整路径）、`DATA_DIR`（商品数据目录）。后续所有操作均在该目录下进行。

### 3. 处理商品描述
- 使用 `run_shell_command` 调用 `cat {DATA_DIR}/product_description.json` 获取描述文本。
- **判断是否有实质内容**：去除 HTML 标签后检查是否为空。如果为空或仅有 HTML 标签无文字内容，则跳过此步骤，直接进入步骤 4。
- **有实质内容则展示给用户**，使用 `AskUserQuestion` 询问是否需要修改。
    - 不需要修改 → 进入步骤 4。
    - 需要修改 → 执行以下流程（**步骤 4 之前不得预览或处理 product_basic.json**）：
        1. 备份：`cp {DATA_DIR}/product_description.json {DATA_DIR}/product_description.json.bak`
        2. 让用户提供新描述（或指明修改方向），由代理修改描述内容并保存到 `{DATA_DIR}/product_description.json`
        3. 使用 `{main} diff-desc --old {DATA_DIR}/product_description.json.bak --new {DATA_DIR}/product_description.json` 在终端展示 diff 对比
        4. 删除备份：`rm {DATA_DIR}/product_description.json.bak`
        5. 使用 `AskUserQuestion` 询问是否还需要继续修改
        6. 如果用户确认不再修改，**必须**回到本步骤开头重新展示描述并确认，不能直接进入步骤 4
- **确认完成的标志**：用户对描述内容满意，不再需要修改。只有达到此状态才能进入步骤 4。

### 4. 处理商品数据结构
- **前提：步骤 3 必须已完成**（描述已确认或跳过）。在此之前不得 cat 或编辑 `product_basic.json`。
- 使用 `cat {DATA_DIR}/product_basic.json` 将结构化数据输出到终端预览。
- 预览输出格式如下（JSON 数组，每个元素为一个 SPU，通过终端展示，不放入大模型上下文）：
   ```json
   [
     {
       "product": {
         "title": "SPU A - product title", 
         "handle": "product-url-slug-a",
         "options": [
           {"name": "Color", "values": ["Red", "Blue"]}
         ],
         "images": [
           {"src": "https://img1.jpg"}
         ],
         "variants": [
           {"option1": "Red", "option2": "42", "option3": null, "price": 19.99, "compare_at_price": 100, "image": {"src": "https://img1.jpg"}},
           {"option1": "Blue", "option2": "42", "option3": null, "price": 19.99, "compare_at_price": 100, "image": {"src": "https://img2.jpg"}}
         ]
       }
     },
     {
       "product": {
         "title": "SPU B - product title",
         "handle": "product-url-slug-b",
         ...
       }
     }
   ]
   ```
- 使用 `AskUserQuestion` 询问用户是否需要对商品数据进行处理，比如调整价格、变体拆分、修改属性等。
- **不需要调整** → 进入步骤 5。
- **需要调整** → 按以下流程循环，直到用户确认不再调整：
    1. 备份：`cp {DATA_DIR}/product_basic.json {DATA_DIR}/product_basic.json.bak`
    2. 按需求进行调整，常用调整方案如下：
        - **调整价格**：用户可指定全部商品或特定 option 的变体，按比例或公式统一调整价格。
        - **变体拆分**：将某个 Option（如 Color）的值拆分为多个 SPU。拆分规则：原始 variants 按指定的 Option 值分组，每组生成一个独立的 SPU，各自包含对应的 options、variants 和 images，其余字段沿用原始值。例如 option1 有 red、blue、yellow，拆分为两个 SPU：SPU A 包含 option1=red/blue，SPU B 包含 option1=yellow。
        - **属性修改**：修改标题、描述、图片等。如果涉及描述修改，**必须退出步骤 4 回到步骤 3**，按步骤 3 的流程处理。
    3. 使用 `diff {DATA_DIR}/product_basic.json.bak {DATA_DIR}/product_basic.json` 在终端展示 diff 对比
    4. 删除备份：`rm {DATA_DIR}/product_basic.json.bak`
    5. 使用 `AskUserQuestion` 询问是否还需要继续调整。如果确认不再调整，进入步骤 5。
- **确认完成的标志**：用户对结构化数据满意，不再需要调整。只有达到此状态才能进入步骤 5。

### 5. 保存商品
- 运行 `{main} create --data {DATA_DIR}/product_basic.json --desc {DATA_DIR}/product_description.json`，脚本会：
    1. 读取 `product_basic.json`（JSON 数组），遍历每个 SPU
    2. 从 `product_description.json` 读取描述内容，合并写入每个 SPU 的 `product.description` 字段
    3. 逐个调用 Shoplazza API 创建商品
    4. 为每个 SPU 输出任务报告

### 6. 任务报告
汇总所有操作结果，强制使用以下格式：
`[操作类型: 创建] - [状态: 成功/失败] - [商品标题] - [ID: xxx] - [链接: URL]`

## 异常处理
- **数据损坏**：如果 `parse` 失败，引导用户检查数据源或重新提取。
- **网络错误**：针对 500/超时错误，提示用户稍后重试，避免重复铺货。
- **部分创建失败**：批量创建多个 SPU 时，如果部分成功、部分失败，在任务报告中明确列出每个 SPU 的创建状态，由用户决定是否需要手动删除已成功创建的商品，不自动执行回滚删除。