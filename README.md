# HMX GGUF 模型转换工具

本项目从 [llama.cpp-npu](https://github.com/dx2331lxz/llama.cpp-npu) 提取，用于将 qwen3 模型转换为 Hexagon NPU HMX 优化的 GGUF 格式。

## 项目结构

```
hmx-gguf-converter/
├── convert_hf_to_gguf_htp.py   # 主转换脚本（包含 HMX 张量重排逻辑）
├── gguf-py/                     # GGUF Python 库（读写 GGUF 格式）
│   ├── gguf/                    # 核心模块
│   └── pyproject.toml
├── llama-quantize/              # 独立量化工具（C++，支持 macOS/Linux）
│   ├── CMakeLists.txt
│   └── llama.cpp/               # 内置 llama.cpp 源码（ggml、src、common 等）
├── models/                      # 内置 tokenizer 词表文件
│   ├── ggml-vocab-qwen2.gguf
│   ├── ggml-vocab-qwen3.gguf
│   ├── ggml-vocab-llama-spm.gguf
│   ├── ggml-vocab-llama-bpe.gguf
│   ├── ggml-vocab-gpt-neox.gguf
│   └── ggml-vocab-gpt-2.gguf
├── requirements.txt             # Python 依赖
└── README.md                    # 本文件
```

说明：当前仓库已经包含单独的 qwen3 词表文件 [models/ggml-vocab-qwen3.gguf](models/ggml-vocab-qwen3.gguf)。Qwen3 也可以直接从 HuggingFace 模型目录中的 tokenizer 文件导出词表，因此即使没有完整权重，也可以单独生成该文件。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 准备 HuggingFace 模型

从 HuggingFace 下载模型权重文件，例如 Qwen3-4B-Instruct-2507：

```bash
# 方式一：使用 huggingface-cli
huggingface-cli download Qwen/Qwen3-4B-Instruct-2507 --local-dir ./Qwen3-4B-Instruct-2507

# 方式二：使用 git clone
git lfs install
git clone https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507
```

模型目录应包含以下文件：
- `config.json` — 模型配置
- `model.safetensors` 或 `pytorch_model.bin` — 模型权重
- `tokenizer.json` / `tokenizer.model` — 分词器
- `tokenizer_config.json` — 分词器配置

对于 Qwen3，至少需要保留 tokenizer 相关文件，例如 `tokenizer.json`、`tokenizer_config.json`、`vocab.json`、`merges.txt`。如果需要重新生成内置词表文件，可以使用 `--vocab-only` 导出到 `models/ggml-vocab-qwen3.gguf`。

### 3. 转换为 F16-HMX GGUF

```bash
python convert_hf_to_gguf_htp.py \
    --outfile qwen3-4b-instruct-2507.f16-hmx.gguf \
    --outtype f16 \
    ./Qwen3-4B-Instruct-2507
```

转换完成后会生成 `qwen3-4b-instruct-2507.f16-hmx.gguf` 文件。

## 支持的模型

目前已验证支持以下模型系列的 HMX 转换：

- **Qwen / Qwen2 / Qwen2.5 / Qwen3**（推荐）
- **LLaMA / LLaMA 2 / LLaMA 3**（推荐）
- Mistral / Mixtral
- Phi / Phi-3
- Gemma / Gemma2
- InternLM2
- StableLM
- DeepSeek
- 以及更多（脚本内置支持 60+ 架构）

> **注意**：建议使用参数量小于 4B 的模型，以获得最佳 NPU 推理效果。

## HMX 转换原理

转换的核心在于 `modify_tensors()` 方法，它对注意力层和前馈层的权重矩阵执行 HMX 布局变换：

```python
# 对 ATTN_Q/K/V/OUT 和 FFN_UP/DOWN/GATE 权重矩阵：
# 原始形状: [n, k]（n 和 k 必须是 32 的倍数）
#
# 变换步骤：
# 1. reshape  → [n/32, 32, k/32, 32]
# 2. permute  → [n/32, k/32, 32, 32]
# 3. view     → [n/32, k/32, 32, 16, 2]
# 4. permute  → [n/32, k/32, 16, 32, 2]   ← FP16 HMX 优化布局
# 5. view     → [n, k]
```

这种 32×32 分块重排使得 Hexagon NPU 的 HMX (FP16 矩阵运算单元) 能够高效执行矩阵乘法。

## 完整转换命令参考

```bash
# 基本转换（F16 精度）
python convert_hf_to_gguf_htp.py --outfile model.f16-hmx.gguf --outtype f16 /path/to/hf_model

# Qwen3-4B-Instruct-2507
python convert_hf_to_gguf_htp.py \
    --outfile qwen3-4b-instruct-2507.f16-hmx.gguf \
    --outtype f16 \
    ./Qwen3-4B-Instruct-2507

# 仅导出词表
python convert_hf_to_gguf_htp.py --outfile model.gguf --vocab-only /path/to/hf_model

# 使用 BF16 精度
python convert_hf_to_gguf_htp.py --outfile model.bf16-hmx.gguf --outtype bf16 /path/to/hf_model

# 指定模型名称
python convert_hf_to_gguf_htp.py --outfile model.f16-hmx.gguf --outtype f16 --model-name "MyModel" /path/to/hf_model
```

## 后续量化（可选）

生成 F16-HMX GGUF 后，如果需要进一步量化（如 `IQ4_NL+Q8_0`），可以使用本项目自带的 `llama-quantize` 工具。

### 编译量化工具

支持 macOS 和 Linux：

```bash
cd llama-quantize
cmake -B build
cmake --build build --config Release
```

### 执行量化

```bash
# 量化（需要设置 REPACK_FOR_HVX 环境变量）
REPACK_FOR_HVX=1 ./llama-quantize/build/bin/llama-quantize \
    qwen3-4b-instruct-2507.f16-hmx.gguf \
    qwen3-4b-instruct-2507.iq4_nl+q8_0-hmx.gguf \
    IQ4_NL+Q8_0
```

更多量化类型和选项请参考 [llama-quantize/README.md](llama-quantize/README.md)。

## 在设备上运行

将量化后的模型文件传输到 Android 设备：

```bash
# 推送文件到设备
adb push qwen2.5-1.5b.iq4_nl+q8_0-hmx.gguf /data/local/tmp/llama.cpp/
adb push llama-cli /data/local/tmp/llama.cpp/
adb push libhtp_ops.so /data/local/tmp/llama.cpp/
adb push libhtp_ops_skel.so /data/local/tmp/llama.cpp/

# 在设备上运行推理
adb shell
cd /data/local/tmp/llama.cpp
LD_LIBRARY_PATH=. DSP_LIBRARY_PATH=. ./llama-cli -t 4 -fa \
    -m qwen3-4b-instruct-2507.iq4_nl+q8_0-hmx.gguf \
    -p "Hello my name is"
```

## 许可证

本项目基于 llama.cpp 项目，遵循 MIT 许可证。
