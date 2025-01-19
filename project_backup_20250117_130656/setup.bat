@echo off
echo 正在创建conda环境...
conda env create -f environment.yml
echo 正在安装项目依赖...
pip install -r requirements.txt
echo 环境设置完成！
pause
