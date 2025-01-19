# 视频字幕提取器

## 项目结构
videototxt/
├── readme.txt           # 项目说明文档
├── requirements.txt     # 项目依赖
├── pip.conf            # pip源配置
├── pack_project.py     # 项目打包脚本
└── src/                # 源代码目录
    ├── main.py         # 主程序入口
    └── ui/
        └── main_window.py  # 主窗口界面

## 功能说明
本项目是一个基于OpenAI的Whisper模型的视频字幕提取工具，支持将视频中的语音转换为带时间轴的SRT格式字幕文件。

### 核心功能
1. 支持拖拽视频文件
2. 支持多种视频格式（mp4, avi, mov, mkv）
3. 可选择不同大小的Whisper模型
4. 实时显示处理进度
5. 生成标准SRT格式字幕
6. 支持自定义保存路径

### 模型说明
- 使用的是OpenAI开源的Whisper模型
- 模型完全基于本地运行，不需要网络连接
- 首次运行时会自动下载模型文件到本地缓存
- 模型存储位置：~/.cache/whisper/
- 提供四种模型选择：
  * base: 74M，适合快速测试
  * small: 244M，平衡速度和准确度
  * medium: 769M，默认选项，较好的准确度
  * large: 1.5G，最高准确度但速度最慢

### 代码详解

#### main.py
主程序入口，负责启动图形界面应用。

#### main_window.py
主要类说明：

1. SubtitleWorker类（继承QThread）
   - 负责后台处理视频和音频
   - 使用信号机制（progress/finished）与主界面通信
   - 主要方法：
     * __init__: 初始化线程，设置视频路径和模型大小
     * run: 执行字幕提取的主要流程
     * format_timestamp: 格式化时间戳为SRT格式

2. MainWindow类（继承QMainWindow）
   - 负责图形界面展示
   - 主要方法：
     * setup_ui: 设置界面布局和组件
     * dragEnterEvent/dropEvent: 处理文件拖放
     * process_video: 开始视频处理
     * save_subtitle: 保存字幕文件

### 处理流程
1. 视频处理：
   - 提取视频音频轨道
   - 转换为16kHz采样率的音频文件
   - 临时保存为mp3格式

2. 语音识别：
   - 加载选定的Whisper模型
   - 设置中文语言和转录任务
   - 使用beam search提高准确率
   - 分段识别音频内容

3. 字幕生成：
   - 将识别结果转换为SRT格式
   - 包含序号、时间戳和文本内容
   - 支持自定义保存位置

### 依赖说明
- PyQt5: 图形界面框架
- moviepy: 视频处理
- whisper: 语音识别
- torch: 深度学习框架（whisper依赖）
- numpy: 数值计算（whisper依赖）

### 安装说明
1. 解压项目文件
2. 运行 setup.bat (Windows) 或 setup.sh (Linux/Mac)
3. 等待环境自动配置完成
4. 运行 src/main.py 启动程序

### 使用说明
1. 启动程序后，可以在界面上选择要使用的模型大小
2. 将视频文件拖放到程序窗口中
3. 等待处理完成
4. 点击"保存字幕"按钮选择保存位置
5. 生成的字幕文件为标准SRT格式，可用于大多数视频播放器