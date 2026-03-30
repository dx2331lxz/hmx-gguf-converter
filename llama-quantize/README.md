# llama-quantize 独立项目

这是从 [llama.cpp-npu](https://github.com/dx2331lxz/llama.cpp-npu) 项目中提取的独立量化工具项目，可以单独编译出 `llama-quantize` 可执行文件。

## 功能

`llama-quantize` 用于将 GGUF 格式的模型进行量化（如将 F16/F32 模型量化为 `IQ4_NL+Q8_0`、`Q4_0`、`Q8_0` 等格式），以减小模型大小并提高推理速度。

## 前置要求

- CMake >= 3.14
- C/C++ 编译器（支持 C++17）
- 本项目已内置所有需要的 llama.cpp 源代码，无需额外依赖

## 编译方法

```bash
# 进入 llama-quantize 目录
cd llama-quantize

# 创建并进入构建目录
cmake -B build

# 编译
cmake --build build --config Release

# 编译后的可执行文件位于 build/bin/llama-quantize
```

### 编译选项

可以通过 CMake 选项配置编译：

```bash
# 启用 CUDA 加速
cmake -B build -DGGML_CUDA=ON

# 启用 CANN NPU 加速
cmake -B build -DGGML_CANN=ON

# 静态链接
cmake -B build -DBUILD_SHARED_LIBS=OFF
```

## 使用方法

```bash
# 基本用法
./build/bin/llama-quantize model-f16.gguf model-q4.gguf Q4_0

# 使用 IQ4_NL+Q8_0 混合量化
./build/bin/llama-quantize model-f16.gguf model-iq4nl-q8.gguf IQ4_NL+Q8_0

# 指定线程数
./build/bin/llama-quantize model-f16.gguf model-q8.gguf Q8_0 8

# 使用 importance matrix
./build/bin/llama-quantize --imatrix imatrix.dat model-f16.gguf model-iq4xs.gguf IQ4_XS
```

### 支持的量化类型

| 类型               | 说明                 |
| ------------------ | -------------------- |
| Q4_0               | 4 bit 量化           |
| Q4_1               | 4 bit 量化（带偏移） |
| Q5_0               | 5 bit 量化           |
| Q5_1               | 5 bit 量化（带偏移） |
| Q8_0               | 8 bit 量化           |
| Q2_K, Q3_K_S/M/L   | K-quant 系列         |
| Q4_K_S/M, Q5_K_S/M | K-quant 系列         |
| Q6_K               | 6 bit K-quant        |
| IQ1_S, IQ1_M       | 1-bit 重要性量化     |
| IQ2_XXS/XS/S/M     | 2-bit 重要性量化     |
| IQ3_XXS/XS/S/M     | 3-bit 重要性量化     |
| IQ4_NL, IQ4_XS     | 4-bit 非线性量化     |
| Q4_0+F16           | 混合量化             |
| Q4_0+Q8_0          | 混合量化             |
| IQ4_NL+Q8_0        | 混合量化             |
| F16                | 16 bit 浮点          |
| BF16               | BFloat16             |
| F32                | 32 bit 浮点          |

### 命令行选项

```
--allow-requantize     允许重新量化已量化的张量
--leave-output-tensor  不量化 output.weight 张量
--pure                 禁用 k-quant 混合，所有张量使用相同类型
--imatrix <file>       使用 importance matrix 文件优化量化
--include-weights <n>  指定使用 importance matrix 的张量
--exclude-weights <n>  指定排除 importance matrix 的张量
--output-tensor-type   指定 output.weight 张量的类型
--token-embedding-type 指定 token embedding 张量的类型
--keep-split           保持与输入相同的分片方式
--override-kv          覆盖模型元数据键值对
```

## 项目结构

```
llama-quantize/
├── CMakeLists.txt     # 独立构建配置
├── README.md          # 本文档
└── llama.cpp/         # 内置 llama.cpp 源代码
    ├── cmake/         # CMake 模块
    ├── common/        # 通用工具库
    ├── examples/      # 量化工具源代码
    ├── ggml/          # 张量计算库（含 HTP 后端）
    ├── include/       # 公共头文件
    └── src/           # llama 推理库
```
