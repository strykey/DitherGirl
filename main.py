import sys
import os
import webview
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from backend.api import DitherGirlAPI

BASE_DIR = Path(__file__).parent
FRONTEND_DIR = BASE_DIR / "frontend"


def main():
    api = DitherGirlAPI()

    window = webview.create_window(
        title="Dither Girl",
        url=str(FRONTEND_DIR / "splash.html"),
        js_api=api,
        width=1400,
        height=900,
        min_size=(1100, 700),
        background_color="#0a0a0a",
        text_select=False,
    )

    webview.start(debug=False)


if __name__ == "__main__":
    main()
