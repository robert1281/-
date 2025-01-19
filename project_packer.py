import os
import sys
import shutil
import subprocess
import json
from datetime import datetime
from pathlib import Path

class ProjectPacker:
    def __init__(self, project_dir=None):
        """初始化项目打包器"""
        self.project_dir = project_dir or os.path.dirname(os.path.abspath(__file__))
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.config = self.load_config()
        self.conda_executable = self._get_conda_executable()

    def _get_conda_executable(self):
        """获取conda可执行文件的路径"""
        if sys.platform.startswith('win'):
            # 尝试从CONDA_PREFIX环境变量获取conda路径
            conda_prefix = os.environ.get('CONDA_PREFIX')
            if conda_prefix:
                # 回退到conda的根目录
                conda_root = os.path.dirname(os.path.dirname(conda_prefix))
                conda_path = os.path.join(conda_root, 'Scripts', 'conda.exe')
                if os.path.exists(conda_path):
                    return conda_path
                
                # 尝试其他可能的路径
                conda_path = os.path.join(conda_root, 'condabin', 'conda.bat')
                if os.path.exists(conda_path):
                    return conda_path
                
            # 如果上述方法失败，尝试从默认安装路径查找
            possible_paths = [
                os.path.join(os.environ.get('USERPROFILE', ''), 'Anaconda3', 'Scripts', 'conda.exe'),
                os.path.join(os.environ.get('USERPROFILE', ''), 'Miniconda3', 'Scripts', 'conda.exe'),
                os.path.join('C:', os.sep, 'ProgramData', 'Anaconda3', 'Scripts', 'conda.exe'),
                os.path.join('C:', os.sep, 'ProgramData', 'Miniconda3', 'Scripts', 'conda.exe'),
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    return path
                
            return 'conda'  # 如果找不到，返回默认命令
        else:
            return 'conda'  # Unix系统直接使用conda命令

    def load_config(self):
        """加载打包配置"""
        default_config = {
            "project_name": Path(self.project_dir).name,
            "include_files": ["*.py", "*.txt", "*.md", "*.yml", "*.yaml", "*.json", "*.conf"],
            "exclude_files": ["__pycache__", "*.pyc", "*.pyo", "*.pyd", ".git", ".idea", ".vscode"],
            "include_dirs": ["src", "docs", "tests", "configs"],
            "exclude_dirs": ["venv", "env", "build", "dist", "__pycache__", ".pytest_cache"],
            "backup_dir": "project_backups"
        }

        config_file = os.path.join(self.project_dir, "packer_config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                print(f"警告: 无法加载配置文件: {e}")

        return default_config

    def get_conda_info(self):
        """获取conda环境信息"""
        try:
            # 获取当前环境名称
            env_name = os.path.basename(os.environ.get('CONDA_PREFIX', ''))
            if not env_name:
                return None, "未检测到conda环境"

            # 获取Python版本
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}"

            return {
                "env_name": env_name,
                "python_version": python_version,
                "platform": sys.platform
            }, None
        except Exception as e:
            return None, f"获取conda信息失败: {e}"

    def export_conda_env(self, output_dir):
        """导出conda环境"""
        conda_info, error = self.get_conda_info()
        if error:
            print(error)
            return False

        try:
            # 导出完整环境
            env_file = os.path.join(output_dir, 'environment.yml')
            subprocess.run([self.conda_executable, 'env', 'export', '-n', conda_info['env_name'], '-f', env_file], 
                         check=True, shell=True if sys.platform.startswith('win') else False)

            # 创建精简版环境文件
            env_file_min = os.path.join(output_dir, 'environment.min.yml')
            subprocess.run([self.conda_executable, 'env', 'export', '-n', conda_info['env_name'], '--from-history', '-f', env_file_min],
                         check=True, shell=True if sys.platform.startswith('win') else False)

            print(f"conda环境已导出到: {env_file}")
            print(f"精简环境配置已导出到: {env_file_min}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"导出conda环境失败: {e}")
            return False
        except Exception as e:
            print(f"导出过程中出现错误: {e}")
            return False

    def should_include_file(self, file_path):
        """检查文件是否应该包含在打包中"""
        from fnmatch import fnmatch
        
        file_name = os.path.basename(file_path)
        rel_path = os.path.relpath(file_path, self.project_dir)

        # 检查排除项
        for pattern in self.config["exclude_files"]:
            if fnmatch(file_name, pattern) or fnmatch(rel_path, pattern):
                return False

        # 检查包含项
        for pattern in self.config["include_files"]:
            if fnmatch(file_name, pattern) or fnmatch(rel_path, pattern):
                return True

        return False

    def copy_project_files(self, output_dir):
        """复制项目文件"""
        def copy_file_with_path(src, dst):
            dst_dir = os.path.dirname(dst)
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)
            shutil.copy2(src, dst)

        copied_files = []
        for root, dirs, files in os.walk(self.project_dir):
            # 过滤目录
            dirs[:] = [d for d in dirs if d not in self.config["exclude_dirs"]]

            for file in files:
                src_path = os.path.join(root, file)
                if self.should_include_file(src_path):
                    rel_path = os.path.relpath(src_path, self.project_dir)
                    dst_path = os.path.join(output_dir, rel_path)
                    try:
                        copy_file_with_path(src_path, dst_path)
                        copied_files.append(rel_path)
                    except Exception as e:
                        print(f"复制文件失败 {rel_path}: {e}")

        return copied_files

    def create_setup_scripts(self, output_dir):
        """创建环境设置脚本"""
        # Windows setup script
        win_script = '''@echo off
echo 正在创建conda环境...
conda env create -f environment.yml
if errorlevel 1 (
    echo 尝试使用精简配置创建环境...
    conda env create -f environment.min.yml
)
echo 正在安装项目依赖...
pip install -r requirements.txt
echo 环境设置完成！
pause
'''
        # Unix setup script
        unix_script = '''#!/bin/bash
echo "正在创建conda环境..."
if ! conda env create -f environment.yml; then
    echo "尝试使用精简配置创建环境..."
    conda env create -f environment.min.yml
fi
echo "正在安装项目依赖..."
pip install -r requirements.txt
echo "环境设置完成！"
'''
        # 创建Windows脚本
        with open(os.path.join(output_dir, 'setup.bat'), 'w', encoding='utf-8') as f:
            f.write(win_script)

        # 创建Unix脚本
        unix_script_path = os.path.join(output_dir, 'setup.sh')
        with open(unix_script_path, 'w', encoding='utf-8') as f:
            f.write(unix_script)
        
        # 设置Unix脚本权限
        if not sys.platform.startswith('win'):
            os.chmod(unix_script_path, 0o755)

    def create_readme(self, output_dir, copied_files):
        """创建项目说明文件"""
        readme_content = f'''# {self.config["project_name"]} - 项目备份

## 备份信息
- 备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Python版本: {sys.version.split()[0]}
- 平台: {sys.platform}

## 文件列表
{chr(10).join("- " + f for f in sorted(copied_files))}

## 安装说明
1. 确保已安装Anaconda或Miniconda
2. Windows用户运行 setup.bat，Unix/Linux用户运行 setup.sh
3. 脚本会自动创建conda环境并安装所需依赖

## 注意事项
- 如果完整环境安装失败，脚本会尝试使用精简配置
- 建议查看 environment.yml 了解详细的依赖要求
'''
        with open(os.path.join(output_dir, 'BACKUP_README.md'), 'w', encoding='utf-8') as f:
            f.write(readme_content)

    def pack(self):
        """执行打包操作"""
        # 创建输出目录
        output_base = os.path.join(self.project_dir, self.config["backup_dir"])
        output_dir = os.path.join(output_base, f'{self.config["project_name"]}_{self.timestamp}')
        os.makedirs(output_dir, exist_ok=True)

        print(f"开始打包项目到: {output_dir}")

        # 导出conda环境
        if self.export_conda_env(output_dir):
            # 复制项目文件
            copied_files = self.copy_project_files(output_dir)
            print(f"已复制 {len(copied_files)} 个文件")

            # 创建设置脚本
            self.create_setup_scripts(output_dir)
            print("已创建环境设置脚本")

            # 创建说明文件
            self.create_readme(output_dir, copied_files)
            print("已创建项目说明文件")

            print(f"\n项目打包完成！")
            print(f"打包文件位置: {output_dir}")
            return True
        return False

def main():
    packer = ProjectPacker()
    packer.pack()

if __name__ == '__main__':
    main() 