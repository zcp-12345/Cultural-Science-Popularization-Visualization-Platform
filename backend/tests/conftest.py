"""确保 `app` 包可导入（无需依赖 editable 安装）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
