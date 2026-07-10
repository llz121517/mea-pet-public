# 🐱 MeaPet — 梅尔桌宠

一个会说话、会吐槽、会记住你的桌面宠物。

**立绘（Live2D + PNG 差分双引擎）+ 语音合成 + AI 对话 + 记忆养成** 全都有，模型和图片都已打包，下载就能用。
注：这是AI写的，有错误直接私信我
---

## 🚀 打开就玩

**Windows 用户** → 双击 **`启动桌宠.bat`**

它会自动帮你搞定**一切**：

| 阶段 | 自动做什么 | 需要你做什么 |
|------|-----------|------------|
| ① 找 Python | 检测系统是否已安装，没有就**自动下载便携版**到 `_python\` 目录 | 等一两分钟 |
| ② 装依赖 | 自动 `pip install` PyQt5、PyTorch、Live2D、VITS 等所有需要的库 | 等几分钟 |
| ③ 配置向导 | 弹出图形化设置窗口 | 选 AI 大脑、设语音 |
| ④ 启动桌宠 | 自动运行 pet.py | 🐱 开玩 |

> 所有下载都用**清华镜像**，国内用户下载飞快。如果哪天镜像挂了会自动切官方源。

配置向导里只用选两样东西：

1. **AI 大脑** — 推荐选「Ollama」（免费，不需要任何 Key）
   - 向导可以帮你下载安装 Ollama + 拉取模型
   - 对话用 `qwen2.5:7b`，识图用 `minicpm-v`
2. **语音** — 开/关，选中文还是日语
   - **VITS 引擎**：轻量便携，模型已打包，开箱即用
   - **GPT-SoVITS 引擎**：高表现力，需额外下载整合包

> 不想用图形界面？复制 `config.example.json` 为 `config.json` 后手动编辑也一样。

### 配置向导随时可以重开

桌宠右键菜单 → **`⚙ 再次配置`** → 即可重新弹出配置向导，改后端、改语音、重新检测环境。

---

## ✨ 它能做什么

| 功能 | 说明 |
|------|------|
| 💬 **聊天** | 双击桌宠打开 Galgame 风格输入框，AI 会回复你。支持 Ollama / DeepSeek 两种后端 |
| 🎤 **语音合成** | 文字回复会合成语音读出来，中/日双语可选。支持 **VITS**（轻量便携）和 **GPT-SoVITS**（高表现力）双引擎 |
| 👀 **屏幕观察** | 定时截图 + 视觉 AI 分析你在干嘛，三层决策（场景摘要→策略评估→回复），偶尔主动吐槽 |
| 🌐 **搜索辅助** | 发现屏幕上不认识的词会自行搜索后再吐槽，不做无根据的评论 |
| 🖱️ **摸头互动** | 鼠标在头部区域左右拖拽，会触发摸头反应 |
| 🎭 **换表情** | 右键菜单切换心情，立绘会变。**18 种表情 + 眨眼动画**，横跨 5 套服装 × 2 朝向 = **180+ 张差分立绘** |
| 🎨 **双渲染引擎** | **Live2D 动态模型**（Cubism 3+，WebGL 渲染）或 **PNG 差分立绘**（高性能），右键一键切换 |
| 📝 **记忆养成** | 记住你和它说过的话，好感度分 7 个等级（陌生人→挚友），每天有获取上限 |
| 📊 **养成面板** | 右键打开半透明面板，看好感度、心情、回忆统计、背景 CG |
| 😴 **待机模式** | 右键设待机，它会闭眼睡觉，窗口鼠标穿透 |
| 💬 **对话气泡** | 角色头顶显示 Galgame 风格半透明姓名牌 + 文字气泡，淡入淡出动画 |
| 📦 **离线安装** | 把 PyTorch 的 `.whl` 放进 `wheels\` 目录，自动跳过下载 |

### 屏幕观察的聪明之处

观察模块不是简单的截图→回复，而是**三层决策**：

1. **截图** → 截取当前屏幕
2. **场景摘要** → 视觉 AI 用一句话描述屏幕内容（不超过 30 字）
3. **策略评估** → 考虑冷落时长（>10 分钟主动搭话，>30 分钟表达在意，<3 分钟保持沉默）+ 屏幕内容，决定：**说/不说**、什么**策略**（毒舌吐槽/关心进度/轻松陪聊/好奇询问）、是否需**搜索**补充信息

---

## 📋 配置

编辑 `config.json`：

```json
{
  "llm": {
    "backend": "deepseek",        // "ollama" 或 "deepseek"
    "host": "http://127.0.0.1:11434",  // Ollama 地址
    "model": "deepseek-v4-flash",      // 对话模型名
    "api_key": "sk-xxx",               // DeepSeek API Key
    "api_base": "https://api.deepseek.com",  // API 地址（可换中转）
    "temperature": 0.7,
    "bridge_url": "http://127.0.0.1:18888"  // CC Switch 中转地址
  },
  "vision": {
    "model": "minicpm-v"           // 屏幕观察的视觉模型
  },
  "tts": {
    "enabled": true,
    "engine": "vits",              // "vits" 或 "gpt_sovits"
    "gpt_weights_dir": "./models/GPT_weights",
    "sovits_weights_dir": "./models/SoVITS_weights",
    "gpt_model": "mea_pro-e50.ckpt",
    "sovits_model": "mea_pro_e24_s13704.pth",
    "ref_dir": "./GPT-Sovits",
    "top_k": 15, "top_p": 0.8, "temperature": 0.6, "speed": 1.0,
    "translate_to_jp": true,       // 中文回复→日语语音
    "voice_lang": "jp",
    "translate_api_key": "",
    "translate_model": "deepseek-chat"
  },
  "display": {
    "scale": 0.5,                  // 窗口缩放
    "fps": 30                      // 帧率
  },
  "character": {
    "name": "梅尔",
    "default_outfit": "01",        // 默认服装编号
    "default_direction": "A"       // 默认朝向 A/B
  },
  "sprite_dir": "./sprites",
  "live2d": {
    "model_dir": "./live2d/model/mea_live2d",
    "enabled": true,               // true=Live2D, false=PNG
    "scale": 0.15
  }
}
```

### 运行

**🪟 Windows 用户** → 双击 `启动桌宠.bat`：
- 没装 Python 会自动下载便携版到 `_python\` 目录
- 第一次运行会自动打开配置向导
- 配置完成后自动启动桌宠
- 已装好 Python 和依赖后，再次双击直接开玩

**或者手动运行：**

第一次使用，先运行配置向导：
```bash
python setup_wizard.py
```

配置完成后，直接启动桌宠：
```bash
python pet.py
```

启动后，桌面宠物会出现在屏幕右下角。

---

## 🔑 API Key 清单

本项目在以下功能中可能需要 API Key（部分功能可选）：

| # | 配置项 / 环境变量 | 所属功能 | 是否需要 | 用途说明 |
|---|------------------|---------|---------|---------|
| 1 | `config.json` → `llm.api_key` | **AI 对话**（DeepSeek 后端） | 可选 | LLM 对话密钥。如果 `backend` 设为 `"deepseek"` 则需要；设为 `"ollama"` 则不需要 |
| 2 | `config.json` → `tts.translate_api_key` | **TTS 日语翻译** | 可选 | 将中文回复翻译成日语再合成语音时使用。如果 AI 后端本身就是 DeepSeek，则自动共用同一个 Key |
| 3 | `config.json` → `llm.api_base` | **AI 对话** | 可选 | API 地址。默认 `https://api.deepseek.com/v1`，可改为其他 OpenAI 兼容 API |

| 后端模式 | `config.json` 设置 | 需要什么 | 说明 |
|---------|-------------------|---------|------|
| **Ollama**（本地免费） | `"backend": "ollama"` | 不需要 API Key | 本地运行，免费，推荐 |
| **DeepSeek API** | `"backend": "deepseek"` | DeepSeek API Key | 需要 `api_key`，填入 `config.json` |

> 👀 **关于屏幕识图**：偷看屏幕功能**始终使用 Ollama**（需要视觉模型如 minicpm-v），与 LLM 后端无关。即使 AI 对话选了 DeepSeek，想要识图功能也需要安装 Ollama + 视觉模型。

### 快速判断

```
只用 Ollama（本地）+ 中文语音     → 不需要任何 API Key ✅
只用 Ollama（本地）+ 日语语音     → 只需要 translate_api_key（翻译用）
用 DeepSeek 对话 + 中文语音       → 只需要 DEEPSEEK_API_KEY
用 DeepSeek 对话 + 日语语音       → 只需要 DEEPSEEK_API_KEY（翻译自动共用）
只用 Ollama，不开语音             → 不需要任何 API Key ✅

👀 屏幕识图功能：无论选什么后端，都需要 Ollama + 视觉模型（minicpm-v）
```

---

## 🎮 操作指南

| 操作 | 效果 |
|------|------|
| 左键拖拽 | 移动桌宠 |
| 双击 | 打开聊天输入框（Galgame 风格） |
| 头部区域左右拖拽 | 触发摸头反应 |
| 右键 | 弹出菜单（切换表情、⚙ 再次配置、待机、渲染切换、养成面板、退出） |
| `ESC` | 关闭输入框 / 状态面板 |

---

## 🧩 项目结构

```
mea-pet/
├── 启动桌宠.bat            # 🎯 一键启动（自动装 Python + 依赖）
├── setup_wizard.py          # 🎯 可视化配置向导（选后端、语音、装环境）
├── pet.py                   # 主程序入口（透明窗口 + 对话气泡 + 事件循环）
├── config.json              # 用户配置（已加入 .gitignore）
├── config.example.json      # 配置模板（含所有可配置项）
│
├── chat.py                  # LLM 对话引擎（Ollama / DeepSeek 双后端）
├── memory.py                # SQLite 记忆与养成系统（好感度 7 级 + 心情）
├── status_panel.py          # 养成状态面板（半透明 CG 背景）
├── chat_input.py            # Galgame 风格聊天输入框
│
├── renderer.py              # PNG 差分立绘渲染（18 种表情映射）
├── live2d_widget.py         # Live2D OpenGL 渲染（Cubism 3+）
│
├── tts.py                   # 语音合成调度器（VITS / GPT-SoVITS 双引擎）
├── vits_infer.py            # VITS 推理脚本
├── vits_core/               # VITS 模型核心代码（monotonic_align / text / ...）
├── vits_models/             # VITS 语音模型（已打包 G_latest.pth）
├── vits_requirements.txt    # VITS 依赖清单
├── gsv_infer.py             # GPT-SoVITS 推理子进程
│
├── watcher.py               # 屏幕观察模块（三层决策系统）
├── utils.py                 # 工具函数（安全 print、日志、UTF-8 兼容）
│
├── sprites/                 # 📸 PNG 差分立绘（5 套服装 × 2 朝向 × 多表情）
│   ├── mea01A_001.png       # 服装01-朝向A-表情001
│   ├── mea01B_002.png       # 服装01-朝向B-表情002
│   └── ...
├── live2d/                  # Live2D 模型与资源
│   └── model/mea_live2d/   # 默认 Live2D 模型
├── GPT-Sovits/              # GPT-SoVITS 参考音频
│   ├── clam/
│   ├── normal/
│   └── soft/
│
├── voice_cache/             # 语音缓存（运行时自动生成）
├── audio_cache/             # 临时音频文件
├── wheels/                  # 📦 可选的离线 .whl 安装包（放进这里自动用）
├── _python/                 # 🆕 便携版 Python（自动下载到这里）
└── mea_memory.db            # SQLite 记忆数据库（运行时自动创建）
```

---

## 🎨 表情与立绘

### 18 种表情映射

| 编号 | 名字 | 说明 |
|------|------|------|
| 001 | default | 默认表情（含泪光特色） |
| 002 | melancholy | 忧郁 / 略带悲伤 |
| 011 | content | 满足 / 眯眼微笑 |
| 012 | peaceful | 安宁 / 幸福微笑 |
| 101 | curious | 好奇 / 内省 |
| 102 | innocent | 天真 / 微羞好奇 |
| 171 | teary | 泪眼 / 失望 / 悲伤 |
| 181 | shy_a | 害羞 / 别扭 A |
| 182 | shy_b | 害羞 / 别扭 B |
| 191 | intrigued | 感兴趣 / 挑眉 |
| 192 | surprised | 惊讶 / 好奇瞪眼 |
| 301 | sad_a | 悲伤 / 梦幻落寞 |
| 302 | sad_b | 悲伤 / 忧郁 B |
| 601 | gentle | 温柔好奇 / 微担忧 |
| 611 | annoyed_a | 不耐烦 / 烦躁 A |
| 612 | annoyed_b | 不耐烦 / 烦躁 B |
| 701 | wistful | 沉思 / 温柔悲伤 |
| 702 | pensive | 忧愁 / 更深沉思 |

横跨 **5 套服装**（01/02/11/12）、**2 个朝向**（A/B）、部分表情带 `_a` 眨眼变体，总计 **180+ 张 PNG 差分立绘**，全部已打包。

### 双渲染引擎切换

- **Live2D**（默认）：动态模型，呼吸/眨眼动画，WebGL 硬件加速
- **PNG 差分**：无需 GPU，高性能，覆盖所有表情

右键菜单可一键切换渲染模式。

---

## 🛠️ 技术细节

### Python 自动安装

启动脚本 `启动桌宠.bat` 按优先级检测 Python：
1. **Hermes venv**（自带 PyTorch，免装依赖）
2. **系统 PATH** / `py` 启动器
3. **常见安装路径**（`%LOCALAPPDATA%\Programs\Python\`）
4. **便携版** `_python\`（有 pip 则直接用）
5. 都没有 → 从清华镜像自动下载 **Python 3.11 embeddable** 到 `_python\`，自动配置 pip

### VITS 语音引擎

- 模型基于 **VITS-fast-fine-tuning** 训练，内置日语词典（`dic/`），首次使用免下载
- 对话回复自动翻译为日语后合成（通过 DeepSeek API 翻译）
- 配置向导优先使用已有 Python（已有 PyTorch 则直接复用），否则创建 venv 从清华镜像安装
- Python 3.12+ 兼容：固定 `setuptools==69.5.1` + `numpy<2` 解决 C 扩展兼容问题

### GPT-SoVITS 引擎

- 通过子进程调用独立整合包，不污染主进程依赖
- 支持多参考音频目录（`clam`/`normal`/`soft`）
- 高表现力，适合需要丰富情感的语音场景

### 国内加速

- 所有 `pip install` 默认用 `pypi.tuna.tsinghua.edu.cn` 镜像
- PyTorch 用 `mirrors.tuna.tsinghua.edu.cn/pytorch/whl/cpu`
- 镜像挂了自动回落官方源

### 离线安装

把 PyTorch、PyQt5 等难下载的 `.whl` 文件放进 `wheels\` 目录，配置向导会自动使用本地文件，跳过网络下载。

---

## 🔧 自定义

### 更换 Live2D 模型

1. 将模型文件放入 `live2d/model/` 目录
2. 更新 `config.json` 中的 `live2d.model_dir` 路径
3. 重启应用

### 修改角色设定

编辑 `chat.py` 中的 `SYSTEM_PROMPT` 即可修改角色的性格、说话风格和行为规则。

### 添加新情绪 / 表情

在 `renderer.py` 的 `EXPRESSION_MAP` 和 `MOOD_TO_EXPRESSION` 中添加映射，然后在 `sprites/` 中放置对应编号的 PNG 文件。

### 添加新服装

按命名规则在 `sprites/` 中放置文件：`mea{服装编号}{朝向}_{表情}.png`，并在 `config.json` 的 `character.default_outfit` 中设置默认服装。

---

## 🔍 常见问题

<details>
<summary><b>双击启动桌宠.bat 后窗口一闪而过</b></summary>

打开命令提示符，手动运行 `启动桌宠.bat` 查看错误信息。常见原因：
- 网络问题导致依赖安装失败（重试或手动配置镜像）
- Python 下载失败（检查 `_python\` 目录是否完整）
</details>

<details>
<summary><b>Ollama 连接失败</b></summary>

1. 确认 Ollama 已启动（任务栏有 Ollama 图标）
2. 确认 `config.json` 中 `llm.host` 为 `http://127.0.0.1:11434`
3. 运行 `ollama list` 检查模型是否已拉取
</details>

<details>
<summary><b>语音合成没有声音</b></summary>

1. 确认 `config.json` 中 `tts.enabled` 为 `true`
2. VITS 引擎：检查 `vits_models/` 下是否有 `G_latest.pth`
3. GPT-SoVITS 引擎：检查模型路径是否正确
4. 用 `python vits_infer.py --text "测试" --output test.wav` 单独测试
</details>

<details>
<summary><b>屏幕观察不吐槽</b></summary>

1. 确认已安装 Ollama 并拉取了视觉模型（`minicpm-v`）
2. 观察模块使用冷落感知：最近 3 分钟内说过话则保持沉默
3. 检查 `config.json` 中 `vision.model` 是否正确
</details>

<details>
<summary><b>Live2D 不显示</b></summary>

1. 确认 `live2d/model/mea_live2d/` 下有 `.model3.json` 文件
2. 确认 `config.json` 中 `live2d.enabled` 为 `true`
3. 尝试右键切换为 PNG 渲染模式
</details>

<details>
<summary><b>Windows 中文乱码</b></summary>

启动脚本已自动设置 `chcp 65001`（UTF-8）和 `PYTHONIOENCODING=utf-8`。如果仍有乱码，检查系统区域设置是否支持 UTF-8。
</details>

---

## ⚠️ 已知限制

- Live2D 渲染需要支持 OpenGL 的显卡
- GPT-SoVITS 引擎需要单独下载整合包（~2GB），VITS 引擎已内置
- 屏幕观察依赖 Ollama 视觉模型，需额外下载（minicpm-v 约 5.5GB）
- 嵌入版 Python（`_python\`）首次安装 pip 需要联网

---

## 📝 许可说明

> **注意**：本项目使用 **Live2D Cubism Core** 进行 WebGL 渲染，该 SDK 属于 [Live2D Inc.](https://www.live2d.com/) 的专有软件。
> 使用 Live2D Cubism SDK 需要遵守 Live2D 的 [软件许可协议](https://www.live2d.com/legal/license/)。

- 项目代码：MIT License
- Live2D 模型资源：版权归原作者所有
- GPT-SoVITS：遵循其开源许可证
- VITS：遵循其开源许可证

---

## 🙏 致谢

- [Live2D Cubism](https://www.live2d.com/) — Live2D 渲染引擎
- [GPT-SoVITS-CPUFast](https://github.com/baicai-1145/GPT-SoVITS-CPUFast) — 推理加速引擎
- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) — 语音合成
- [VITS-fast-fine-tuning](https://github.com/Plachtaa/VITS-fast-fine-tuning) — VITS 训练框架
- [Ollama](https://ollama.ai/) — 本地 LLM 运行
- [DeepSeek](https://deepseek.com/) — 对话 API
- [Sakura](https://github.com/Rvosy/sakura) — 主动搭话 prompt 架构参考
