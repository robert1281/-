from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                           QPushButton, QTextEdit, QProgressBar, QLabel,
                           QFileDialog, QComboBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import os
os.environ['KMP_DUPLICATE_LIB_OK']='True'
import whisper
from moviepy.editor import VideoFileClip
import time

class SubtitleWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    
    def __init__(self, video_path, model_size="medium"):
        super().__init__()
        self.video_path = video_path
        self.model_size = model_size
        
    def run(self):
        try:
            # 提取音频
            self.progress.emit("正在提取音频...")
            video = VideoFileClip(self.video_path)
            duration = video.duration
            self.progress.emit(f"视频总长度: {int(duration)}秒")
            
            audio_path = "temp_audio.mp3"
            # 提高音频质量
            video.audio.write_audiofile(audio_path, fps=16000, bitrate="192k", verbose=False, logger=None)
            
            # 加载模型
            self.progress.emit(f"正在加载{self.model_size}模型...")
            model = whisper.load_model(self.model_size)
            
            # 识别音频
            self.progress.emit("开始识别音频...")
            
            result = model.transcribe(
                audio_path,
                language="zh",  # 指定中文
                task="transcribe",  # 转录任务
                initial_prompt="这是一段中文音频。",  # 提示模型使用中文
                best_of=5,  # 使用beam search提高准确率
                verbose=True  # 启用详细输出
            )
            
            # 格式化字幕
            self.progress.emit("正在生成SRT格式字幕...")
            srt_content = ""
            total_segments = len(result["segments"])
            
            for i, segment in enumerate(result["segments"], 1):
                start = self.format_timestamp(segment["start"])
                end = self.format_timestamp(segment["end"])
                text = segment["text"].strip()
                srt_content += f"{i}\n{start} --> {end}\n{text}\n\n"
                
                # 显示每个片段的识别结果和进度
                percentage = min(100, int(i / total_segments * 100))
                progress_msg = f"正在处理: {percentage}% (片段 {i}/{total_segments})"
                self.progress.emit(progress_msg)
                print(f"[{start} --> {end}] {text}")
            
            # 清理临时文件
            os.remove(audio_path)
            
            self.progress.emit("识别完成！")
            self.finished.emit(srt_content)
            
        except Exception as e:
            import traceback
            error_msg = f"错误: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)  # 在控制台打印详细错误信息
            self.finished.emit(f"错误: {str(e)}")
    
    def format_timestamp(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        msecs = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{msecs:03d}"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("视频字幕提取器")
        self.setAcceptDrops(True)
        self.setup_ui()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 创建模型选择下拉框
        self.model_combo = QComboBox()
        self.model_combo.addItems(["base", "small", "medium", "large"])
        self.model_combo.setCurrentText("medium")  # 默认使用medium模型
        layout.addWidget(QLabel("选择模型 (越大越准确但越慢):"))
        layout.addWidget(self.model_combo)
        
        # 创建拖放提示标签
        self.drop_label = QLabel("将视频文件拖放到这里")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 5px;
                padding: 30px;
                background: #f0f0f0;
            }
        """)
        
        # 创建进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        
        # 创建状态标签
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 创建文本显示区域
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        
        # 创建按钮布局
        button_layout = QVBoxLayout()
        
        # 创建保存按钮
        self.save_button = QPushButton("保存字幕")
        self.save_button.clicked.connect(self.save_subtitle)
        self.save_button.hide()
        
        # 添加组件到布局
        layout.addWidget(self.drop_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.save_button)
        
        self.setMinimumSize(600, 400)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        files = event.mimeData().urls()
        if files:
            video_path = files[0].toLocalFile()
            if video_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                self.process_video(video_path)
            else:
                self.status_label.setText("请拖入有效的视频文件")
                
    def process_video(self, video_path):
        self.progress_bar.show()
        self.status_label.setText("正在处理...")
        # 使用选择的模型大小
        self.worker = SubtitleWorker(video_path, self.model_combo.currentText())
        self.worker.progress.connect(self.update_status)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()
        
    def update_status(self, message):
        self.status_label.setText(message)
        
    def on_finished(self, result):
        self.progress_bar.hide()
        if result.startswith("错误"):
            self.status_label.setText(result)
        else:
            self.text_edit.setText(result)
            self.save_button.show()
            self.status_label.setText("处理完成！")
            
    def save_subtitle(self):
        # 获取视频文件所在的目录作为默认保存路径
        default_path = os.path.dirname(self.worker.video_path)
        default_name = os.path.splitext(os.path.basename(self.worker.video_path))[0] + ".srt"
        default_save_path = os.path.join(default_path, default_name)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存字幕",
            default_save_path,  # 默认使用视频同名的srt文件
            "字幕文件 (*.srt);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.text_edit.toPlainText())
                self.status_label.setText(f"字幕已保存到: {file_path}")
            except Exception as e:
                self.status_label.setText(f"保存失败: {str(e)}") 