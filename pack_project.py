import os
import sys
import shutil
import subprocess
from datetime import datetime

def get_conda_path():
    """获取conda可执行文件的路径"""
    # 从CONDA_PREFIX环境变量获取conda路径
    conda_prefix = os.environ.get('CONDA_PREFIX')
    if conda_prefix:
        conda_root = os.path.dirname(os.path.dirname(conda_prefix))
        possible_paths = [
            os.path.join(conda_root, 'Scripts', 'conda.exe'),
            os.path.join(conda_root, 'condabin', 'conda.bat'),
            os.path.join(conda_root, 'Library', 'bin', 'conda.bat'),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
    
    # 如果上述方法失败，尝试从默认安装路径查找
    program_data = os.environ.get('PROGRAMDATA', 'C:\\ProgramData')
    possible_paths = [
        os.path.join(program_data, 'Anaconda3', 'Scripts', 'conda.exe'),
        os.path.join(program_data, 'Miniconda3', 'Scripts', 'conda.exe'),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
            
    return None

def export_conda_env(output_dir):
    """导出conda环境"""
    env_name = os.path.basename(os.environ.get('CONDA_PREFIX', ''))
    if not env_name:
        print("错误：未检测到conda环境")
        return False

    conda_path = get_conda_path()
    if not conda_path:
        print("错误：找不到conda可执行文件")
        return False

    print(f"使用conda路径: {conda_path}")
    output_file = os.path.join(output_dir, 'environment.yml')
    
    try:
        # 使用完整路径执行conda命令
        cmd = f'"{conda_path}" env export -n {env_name} -f "{output_file}"'
        subprocess.run(cmd, shell=True, check=True)
        print(f"conda环境已导出到: {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"导出conda环境失败: {e}")
        return False

def copy_project_files(project_dir, output_dir):
    """复制项目文件"""
    # 要复制的文件和目录
    items_to_copy = ['src', 'requirements.txt', 'pip.conf', 'readme.txt']
    
    for item in items_to_copy:
        src_path = os.path.join(project_dir, item)
        dst_path = os.path.join(output_dir, item)
        
        if os.path.exists(src_path):
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
            else:
                shutil.copy2(src_path, dst_path)
            print(f"已复制: {item}")
        else:
            print(f"警告: 未找到 {item}")

def create_setup_script(output_dir):
    """创建环境设置脚本"""
    setup_content = '''@echo off
echo 正在创建conda环境...
conda env create -f environment.yml
echo 正在安装项目依赖...
pip install -r requirements.txt
echo 环境设置完成！
pause
'''
    setup_file = os.path.join(output_dir, 'setup.bat')
    with open(setup_file, 'w', encoding='utf-8') as f:
        f.write(setup_content)
    print(f"已创建设置脚本: {setup_file}")

def main():
    # 获取当前项目目录
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 创建打包目录
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join(project_dir, 'project_backup_' + timestamp)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"开始打包项目到: {output_dir}")
    
    # 导出conda环境
    if export_conda_env(output_dir):
        # 复制项目文件
        copy_project_files(project_dir, output_dir)
        # 创建设置脚本
        create_setup_script(output_dir)
        print("\n项目打包完成！")
        print(f"打包文件位置: {output_dir}")
    else:
        print("项目打包失败！")

if __name__ == '__main__':
    main() 