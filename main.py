"""JARVIS Windows application entry point and packaged-run smoke check."""
import os
import sys
from pathlib import Path


def self_test():
    """Run inside the packaged EXE on Windows CI to catch DLL/Qt failures."""
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    try:
        import ctypes
        import keyring
        import miniaudio
        import edge_tts
        import sounddevice
        import websocket
        import pyautogui
        import pynput
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QIcon
        from jarvis.ui import Window, STYLE
        from jarvis.visuals import Core
        from jarvis.core import Agent, Desktop
        from jarvis.listening import Listener
        bundle = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
        dll_name = f'python{sys.version_info.major}{sys.version_info.minor}.dll'
        if sys.platform == 'win32':
            if not (bundle / dll_name).is_file():
                raise RuntimeError(f'{dll_name} is missing from the PyInstaller bundle: {bundle}')
            ctypes.WinDLL(dll_name)
        icon = bundle / 'assets' / 'jarvis.png'
        if not icon.is_file() or QIcon(str(icon)).isNull():
            raise RuntimeError('Bundled JARVIS icon is missing or unreadable')
        app = QApplication([])
        app.setStyleSheet(STYLE)
        core = Core()
        core.resize(320,320)
        core.show()
        app.processEvents()
        if core.grab().isNull():
            raise RuntimeError('Qt could not render the JARVIS core')
        core.close()
        return 0
    except Exception:
        import traceback
        Path('jarvis-self-test-error.txt').write_text(traceback.format_exc(),encoding='utf-8')
        return 1


if __name__ == '__main__':
    if '--self-test' in sys.argv:
        raise SystemExit(self_test())
    from jarvis.ui import launch
    launch(sys.argv)
