"""清理脚本

删除不需要的文件和目录
"""
import os
import shutil
from pathlib import Path

# 需要删除的文件和目录
TO_DELETE = [
    '__pycache__',
    '.DS_Store',
    '*.pyc',
    '*.pyo',
    '*.pyd',
    '.Python',
    'pip-log.txt',
    'pip-delete-this-directory.txt',
    '.pytest_cache',
    '.coverage',
    'htmlcov',
]

# 需要保留的目录
KEEP_DIRS = {
    '.git',
    '.venv',
    'venv',
    'data',
    'templates',
    'static',
    'routes',
    'services',
    'utils',
    'uploads',
}


def cleanup():
    """执行清理"""
    base_dir = Path(__file__).parent
    deleted_count = 0
    
    print("开始清理项目...")
    print("="*50)
    
    # 删除 __pycache__ 目录
    for pycache in base_dir.rglob('__pycache__'):
        if pycache.is_dir():
            print(f"删除: {pycache.relative_to(base_dir)}")
            shutil.rmtree(pycache)
            deleted_count += 1
    
    # 删除 .pyc 文件
    for pyc in base_dir.rglob('*.pyc'):
        print(f"删除: {pyc.relative_to(base_dir)}")
        pyc.unlink()
        deleted_count += 1
    
    # 删除 .DS_Store 文件
    for ds_store in base_dir.rglob('.DS_Store'):
        print(f"删除: {ds_store.relative_to(base_dir)}")
        ds_store.unlink()
        deleted_count += 1
    
    print("="*50)
    print(f"清理完成！共删除 {deleted_count} 个文件/目录")
    
    # 显示项目结构
    print("\n当前项目结构：")
    print_tree(base_dir, max_depth=2)


def print_tree(directory, prefix="", max_depth=2, current_depth=0):
    """打印目录树"""
    if current_depth >= max_depth:
        return
    
    items = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name))
    
    for i, item in enumerate(items):
        # 跳过隐藏文件和特定目录
        if item.name.startswith('.') and item.name not in {'.gitignore', '.editorconfig'}:
            continue
        if item.name in {'__pycache__', '.venv', 'venv', '.git'}:
            continue
        
        is_last = i == len(items) - 1
        current_prefix = "└── " if is_last else "├── "
        print(f"{prefix}{current_prefix}{item.name}")
        
        if item.is_dir() and current_depth < max_depth - 1:
            extension = "    " if is_last else "│   "
            print_tree(item, prefix + extension, max_depth, current_depth + 1)


if __name__ == '__main__':
    cleanup()
