# 视频人脸分类系统

从视频目录中提取人物头像，根据人像进行自动分类，根据人脸特征向量进行聚类，可交互的 HTML 页面。

## 快速开始

### 本地 Win11 运行

```bash
# 1. 激活 conda 环境
conda activate video

# 2. 确保 FFmpeg 已安装（默认路径: E:\local\ffmpeg\bin\ffmpeg.exe）

# 3. 创建符号链接（Windows）
mklink /J web/data %VIDEO_DIR%

# 4. 进入项目目录
cd tools

# 5. 运行完整处理流程（人脸检测 + 聚类 + 生成 HTML）。按照提示，选择对应的功能运行
run.bat
```

### 运行 Docker 版本

```bash
# 重建镜像
docker compose build --no-cache

# 容器内验证 GPU Provider
docker compose --profile tools run --rm pipeline python -c "import onnxruntime as ort; print(ort.get_available_providers())"

# 1. 把 docker-compose.yml 文件中的 HOST_VIDEO_ROOT 变量修改为视频目录

# 2. 运行完整处理流程
docker compose run --rm pipeline

# 3. 运行 Web 服务
docker compose run --rm -p 8080:8080 webapp

# 4. 访问 http://localhost:8080
# 5. 点击 "同步数据" 按钮，等待处理完成，然后，浏览视频
```

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        处理流程                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │ 视频扫描  │ -> │ 视频去重  │ -> │ 帧提取   │ -> │ 人脸检测 │ │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│                                                          │      │
│                                                          v      │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │ HTML页面 │ <- │数据存储   │ <- │ 人脸聚类 │ <- │ 特征提取 │ │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        核心模块                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  modules/                                                       │
│  ├── source.py      - 视频源管理、扫描、去重                    │
│  ├── portrait.py    - 人像数据管理、聚类                        │
│  └── builder.py     - UI 构建器、HTML 生成                      │
│                                                                 │
│  engine/                                                          │
│  ├── frame_extractor.py  - FFmpeg 帧提取                        │
│  ├── face_detector.py    - InsightFace 人脸检测                │
│  ├── face_clusterer.py   - 人脸聚类 (DBSCAN)                   │
│  └── face_storage.py     - 数据持久化                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 功能特性

- **自动人脸检测**：使用 InsightFace 深度学习模型检测视频中的人脸
- **人脸聚类**：基于 512 维人脸特征向量，使用 DBSCAN 算法自动将相似人脸分组
- **视频去重**：使用感知哈希（pHash）算法自动检测并去除重复视频
- **交互式索引**：生成的 HTML 页面支持搜索、筛选和下钻查看
- **视频关联**：每个人脸条目关联原始视频，支持一键打开视频查看原片
- **按视频分组**：详情页面将同一人物的不同出现按视频分组展示

## 目录结构

```
project/                        # 项目根目录
├── pipeline.py                 # 主处理流程
├── config.py                   # 配置文件
├── modules/                    # 核心模块
│   ├── source.py               # 视频源管理
│   ├── portrait.py             # 人像数据管理
│   └── builder.py              # UI 构建器
├── engine/                     # 引擎模块
│   ├── frame_extractor.py      # FFmpeg 帧提取
│   ├── face_detector.py        # InsightFace 人脸检测
│   ├── face_clusterer.py       # 人脸聚类
│   │   └── face_storage.py     # 数据持久化
├── tools/                      # 工具脚本
│   ├── run.bat                 # Windows 启动脚本
│   ├── regenerate_html.py      # 重新生成 HTML
│   └── ...
└── web/                        # 输出目录
    ├── index.html              # 人脸索引首页
    ├── detail.html             # 人物详情页
    ├── face_data/              # 数据目录
    │   ├── face_data.json      # 人脸数据
    │   └── thumbnails/         # 人脸缩略图
    └── data -> symlink         # 视频目录符号链接

```

### 目录映射关系

| 目录 | 说明 |
|------|------|
| `web/face_data/face_data.json` | 人脸检测和聚类数据 |
| `web/face_data/thumbnails/` | 提取的人脸缩略图 |
| `web/data` -> `../..` | 指向视频目录的符号链接 |

---

## 详细使用说明

### 1. 数据准备

将视频文件放在 `%WEIXIN_ROOT%/msg/video/2026-02/` 目录下（支持按月份分目录）。

**支持的视频格式**：MP4, AVI, MOV, MKV

### 2. 运行完整处理流程

```bash
# 使用 conda 环境
conda activate video

# 运行完整处理流程（自动去重）
python pipeline.py

# 或者禁用视频去重
python pipeline.py --no-dedupe

# 或者在去重后自动删除重复文件（谨慎使用！）
python pipeline.py --remove-duplicates
```

**处理流程**：
1. **视频扫描**：扫描指定目录下的所有视频文件
2. **视频去重**：使用感知哈希（pHash）检测重复视频
3. **帧提取**：使用 FFmpeg 从每个视频中提取帧
4. **人脸检测**：使用 InsightFace 检测人脸并提取 512 维特征向量
5. **人脸聚类**：使用 DBSCAN 聚类算法将相似人脸分组
6. **生成索引**：保存检测结果到 `face_data.json`，生成 HTML 页面

### 3. 重新生成 HTML 页面

如果已有人脸数据，想重新生成 HTML 页面：

```bash
python tools/regenerate_html.py
```

### 4. 单独运行视频去重

```bash
# 仅检测重复视频（不删除）
python video_deduplicator.py

# 检测并删除重复文件
python video_deduplicator.py --remove

# 自定义相似度阈值（0.85 = 85% 相似度）
python video_deduplicator.py --threshold 0.85
```

### 5. 查看日志

```bash
# 查看处理日志
cat processing.log

# 实时查看日志
tail -f processing.log

# Windows 上查看
type processing.log
```

---

## 配置参数

配置文件：`config.py`

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DCIM_ROOT` | 项目父目录 | 视频根目录 |
| `VIDEO_DIR` | `{DCIM_ROOT}/msg/video` | 视频目录 |
| `PROJECT_DIR` | `{VIDEO_DIR}/py` | 项目目录 |
| `FFMPEG_PATH` | `ffmpeg.exe` | FFmpeg 路径 |
| `USE_GPU` | `1` | 是否使用 GPU (1/0) |

### 视频处理配置

```python
VIDEO_PROCESSING_CONFIG = {
    'frames_per_video': 3,         # 每视频提取的帧数
    'skip_start_seconds': 1.0,    # 跳过开头秒数
    'skip_end_seconds': 1.0,      # 跳过结尾秒数
    'max_videos': None,           # 最大处理视频数，None=全部
    'parallel_workers': 1,        # 并行工作数
}
```

### 人脸检测配置

```python
FACE_DETECTION_CONFIG = {
    'use_gpu': True,              # 使用 GPU 加速
    'model_name': 'buffalo_l',    # InsightFace 模型
    'confidence_threshold': 0.7,  # 检测置信度阈值 (0-1)
    'min_face_size': (60, 60),   # 最小人脸尺寸
}
```

### 聚类配置

```python
CLUSTERING_CONFIG = {
    'dbscan': {
        'eps': 0.45,             # 距离阈值，越小分组越严格
        'min_samples': 2,        # 最小聚类大小
        'metric': 'cosine'       # 距离度量
    },
    'default_method': 'dbscan'   # 默认聚类方法
}
```

### 质量过滤配置

```python
QUALITY_FILTER_CONFIG = {
    'min_face_size': (60, 60),
    'confidence_threshold': 0.6,
    'max_faces_per_frame': 5,
    'min_face_quality_score': 0.3  # 模糊检测阈值
}
```

### 视频去重配置

```python
DEDUPLICATION_CONFIG = {
    'enabled': True,               # 启用/禁用视频去重
    'similarity_threshold': 0.90, # 相似度阈值 (0-1)
    'sample_frames': 3,            # 每视频采样的帧数
    'hash_size': 16,               # 感知哈希大小
    'remove_duplicates': False,   # 是否自动删除重复文件
}
```

### 日志配置

```python
LOGGING_CONFIG = {
    'log_file': 'processing.log',
    'level': 'INFO',              # DEBUG, INFO, WARNING, ERROR
}
```

---

## 视频去重说明

### 工作原理

系统使用 **感知哈希（pHash）** 算法检测重复视频：

1. **采样帧提取**：从每个视频的 10%、50%、90% 位置提取帧
2. **计算图像哈希**：对每帧计算 DCT 感知哈希
3. **生成视频指纹**：合并各帧哈希值生成视频唯一指纹
4. **相似度比较**：使用汉明距离计算视频间相似度
5. **分组标记**：相似度 ≥ 90% 的视频标记为重复

### 相似度阈值建议

| 阈值 | 效果 |
|------|------|
| 0.95 | 严格匹配，仅完全相同的视频被标记为重复 |
| 0.90 | **默认**，平衡精确度和召回率 |
| 0.85 | 宽松匹配，可能将相似视频误判为重复 |
| 0.80 | 很宽松，可能误判 |

### 处理策略

- **默认行为**：标记重复视频，但保留所有文件
- **手动删除**：查看报告后，手动决定删除哪些重复文件
- **自动删除** (`--remove-duplicates`)：自动删除重复文件，保留每组中的第一个

---

## HTML 页面功能

### 首页 (web/index.html)

- **卡片展示**：每个人物以卡片形式展示，包含头像缩略图
- **统计信息**：显示总人脸数、总人物数
- **搜索功能**：支持按人物 ID 搜索筛选
- **排序功能**：按人脸数/视频数/时间排序
- **主题切换**：支持明暗主题切换
- **下钻查看**：点击卡片进入该人物的详情页

### 详情页 (web/detail.html)

- **视频分组**：同一人物的所有人脸按视频分组显示
- **可折叠列表**：点击视频头部展开/收起该视频下的人脸列表
- **视频链接**：每个视频组提供 "Open Video" 链接，可直接打开原视频
- **人脸详情**：每张人脸显示帧号、时间戳、检测置信度

---

## 数据格式

### face_data.json 结构

```json
{
  "metadata": {
    "version": "1.0.0",
    "created_at": "2026-02-07T10:36:53",
    "updated_at": "2026-02-07T10:45:11"
  },
  "faces": {
    "face_id_1": {
      "id": "face_id_1",
      "source_video": "2026-02/video1.mp4",
      "video_name": "video1.mp4",
      "timestamp": 44.65,
      "frame_index": 2,
      "confidence": 0.729,
      "thumbnail_path": "thumbnails/video1_f002_t44.jpg",
      "embedding": [512 个浮点数...]
    }
  },
  "persons": {
    "person_0000": {
      "id": "person_0000",
      "cluster_id": 0,
      "faces": ["face_id_1", "face_id_2", ...],
      "face_count": 41,
      "video_count": 19,
      "unique_videos": ["2026-02/video1.mp4", ...]
    }
  }
}
```

---

## 技术栈

- **人脸检测**：InsightFace (buffalo_l 模型)
- **视频处理**：FFmpeg
- **视频去重**：感知哈希 (pHash) + DCT 变换
- **数据存储**：JSON (orjson)
- **前端**：原生 HTML/CSS/JavaScript，无外部依赖

---

## 环境要求

- Python 3.9+
- CUDA 支持（GPU 加速人脸检测）
- FFmpeg（已配置路径：`E:\local\ffmpeg\bin\ffmpeg.exe`）

### Python 依赖

```
insightface
onnxruntime-gpu
opencv-python
orjson
numpy
scikit-learn
scipy
```

### GPU 配置

```bash
# 使用 GPU（默认）
conda activate video
python pipeline.py

# 禁用 GPU，使用 CPU
set USE_GPU=0
python pipeline.py

# 或在代码中设置
export USE_GPU=0  # Linux/Mac
```

---

## 常见问题

### Q: 如何启动系统？

```bash
# 方法 1: 使用 run.bat（Windows）
cd tools
run.bat

# 方法 2: 直接运行 pipeline.py
conda activate video
python pipeline.py

# 方法 3: 使用 Python HTTP 服务器查看结果
python -m http.server 8080
# 访问 http://localhost:8080/py/web/index.html
```

### Q: 视频链接打不开？

确保视频文件在 `msg/video/` 目录下，且文件名与 `face_data.json` 中的 `source_video` 字段一致。检查符号链接 `web/data` 是否正确指向视频目录。

### Q: 缩略图不显示？

检查 `web/face_data/thumbnails/` 目录是否存在，以及图片文件是否完整。

### Q: 如何重新生成 HTML？

```bash
python tools/regenerate_html.py
```

### Q: 聚类结果不准确？

调整 `config.py` 中的 `eps` 参数：
- 增大 EPS（如 0.5）：分组更宽松，可能把不同人分到一起
- 减小 EPS（如 0.35）：分组更严格，可能同一人被分到多组

### Q: 如何查看视频去重报告？

去重报告会在运行时打印到控制台，也会保存到 `duplicate_report.txt`。

### Q: 处理速度很慢？

1. 确认 GPU 是否可用：`python -c "import onnxruntime; print(onnxruntime.get_available_providers())"`
2. 减少每视频帧数：修改 `config.py` 中 `frames_per_video`
3. 减少处理视频数：修改 `max_videos` 参数
4. 跳过去重：使用 `--no-dedupe` 参数

### Q: 误删了视频怎么办？

**重要**：默认情况下不会删除任何文件。如需删除，请先运行去重检查，查看报告确认后再决定是否使用 `--remove` 参数。

### Q: Windows 上创建符号链接失败？

需要管理员权限。以管理员身份运行 PowerShell：

```powershell
New-Item -ItemType Junction -Path "py\web\data" -Target "..\.."
```

---

## 性能优化

### 推荐配置

- **GPU**：NVIDIA RTX 2060+（推荐）
- **内存**：16GB+
- **存储**：SSD（用于存储缩略图）

### 处理大量视频

```python
# 在 config.py 中设置
VIDEO_PROCESSING_CONFIG = {
    'max_videos': 100,     # 限制每次处理数量
    'frames_per_video': 2, # 减少帧数
}
```

### 调整聚类参数

```python
# 人多视频多的情况
CLUSTERING_CONFIG = {
    'dbscan': {
        'eps': 0.4,         # 降低阈值，更严格聚类
        'min_samples': 3,   # 提高最小样本数
    }
}
```

---

## 故障排除

### 错误：No module named 'insightface'

```bash
conda activate video
pip install insightface
```

### 错误：FFmpeg not found

```bash
# 设置 FFmpeg 路径
set FFMPEG_PATH=E:\local\ffmpeg\bin\ffmpeg.exe
```

### 错误：CUDA out of memory

减少并发处理或降低帧数：
```python
VIDEO_PROCESSING_CONFIG = {
    'parallel_workers': 1,
    'frames_per_video': 1,
}
```

### 错误：Empty face detection results

1. 检查视频是否包含人脸
2. 降低 `confidence_threshold` 到 0.5
3. 检查视频质量是否太低

---

## 更新日志

**v1.2.0** (2026-03-03)
- 优化目录结构，使用 web/face_data/ 分离数据和静态文件
- 新增符号链接机制，支持视频文件直接访问
- 优化 HTML 页面，支持明暗主题切换

**v1.1.0** (2026-02-07)
- 新增视频去重功能（pHash 感知哈希算法）
- 新增 `video_deduplicator.py` 独立模块
- 新增命令行参数 `--no-dedupe` 和 `--remove-duplicates`
- 新增去重报告生成

**v1.0.0** (2026-02-07)
- 初始版本
- 人脸检测与聚类
- HTML 索引生成
- 按视频分组的详情页