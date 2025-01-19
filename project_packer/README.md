# Python项目打包工具

这是一个通用的Python项目打包工具，专门用于打包基于conda环境的Python项目。

## 功能特点

1. 自动导出conda环境配置
2. 复制项目源代码和配置文件
3. 创建环境还原脚本
4. 支持Windows系统

## 使用方法

### 1. 准备工作

1. 将 `project_packer` 文件夹复制到您的项目根目录
2. 确保您的项目具有以下基本结构： 
your_project/
├── src/ # 源代码目录
├── requirements.txt # Python包依赖
├── pip.conf # pip源配置（可选）
└── readme.txt # 项目说明（可选）
bash
python pack_project.py
project_backup_YYYYMMDD_HHMMSS/
├── environment.yml # conda环境配置
├── setup.bat # 环境还原脚本
├── src/ # 项目源代码
├── requirements.txt # 依赖配置
└── pip.conf # pip配置

### 2. 运行打包脚本

1. 确保已激活正确的conda环境
2. 运行打包脚本：python pack_project.py
### 3. 打包结果
脚本会在项目目录下创建一个带时间戳的备份文件夹：
roject_backup_YYYYMMDD_HHMMSS/
├── environment.yml # conda环境配置
├── setup.bat # 环境还原脚本
├── src/ # 项目源代码
├── requirements.txt # 依赖配置
└── pip.conf # pip配置
### 4. 还原项目

1. 复制备份文件夹到目标机器
2. 运行 `setup.bat`
3. 等待环境配置完成

## 注意事项

1. 确保已安装Anaconda或Miniconda
2. 运行脚本前请激活正确的conda环境
3. 建议在打包前更新requirements.txt
4. Windows系统需要管理员权限运行setup.bat

## 常见问题

1. 如果找不到conda命令，脚本会自动搜索常见安装路径
2. 如果环境导出失败，请检查conda环境是否正确激活
3. 如果文件复制失败，请检查文件权限

使用方法：
1. 将整个 `project_packer` 文件夹复制到项目根目录
2. 如果项目缺少配置文件，脚本会自动从模板创建
3. 在命令行中进入 project_packer 目录
4. 运行：`python pack_project.py`

这样就实现了python 和 conda环境的打包还原。