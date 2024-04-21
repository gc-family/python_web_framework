import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIRS = {
    os.path.join(BASE_DIR, "templates"),
}

STATIC_DIRS = {
    os.path.join(BASE_DIR, "static"),
}

MEDIA_DIRS = [
    os.path.join(BASE_DIR,"media"),
]