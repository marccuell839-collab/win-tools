"""Render the minimal interface without microphone or network access."""
import os
os.environ['QT_QPA_PLATFORM']='offscreen'
from unittest.mock import patch
from PySide6.QtWidgets import QApplication,QPushButton
from jarvis.ui import Window,Settings,STYLE
app=QApplication([]);app.setStyleSheet(STYLE)
with patch.object(Window,'start_listener'):
    w=Window(boot=False);w.show();app.processEvents()
    assert [b for b in w.findChildren(QPushButton) if b.isVisible()]==[w.gear]
    assert w.grab().save('ui-preview.png')
    settings=Settings(w);settings.show();app.processEvents()
    assert 'vision' in settings.checks and 'listen' in settings.checks
    assert 'dg_key' in settings.fields
    settings.close()
    w.session=False
    with patch.object(w,'say') as say:
        listener=object();w.voice_listener=listener
        w.heard(listener,'كلام عادي')
        say.assert_not_called()
        with patch.object(w,'halt_listener'):
            w.heard(listener,'جارفيس')
        say.assert_called_once()
        assert say.call_args.args[0]=='نعم سيدي.'
    w.voice_listener=None
    w.stop()
    assert w.paused and not w.session
    if w.hotkey:w.hotkey.stop()
    w.tray.hide()
print('Minimal UI and wake-flow smoke test passed')
