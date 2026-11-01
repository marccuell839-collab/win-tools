"""Offscreen UI paint test; never controls desktop or calls cloud APIs."""
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from PySide6.QtWidgets import QApplication
from jarvis.ui import Window, STYLE
app = QApplication([])
app.setStyleSheet(STYLE)
w = Window()
w.show()
app.processEvents()
assert w.width() >= 470
assert w.input.isEnabled()
assert not w.screen.isChecked()
assert w.grab().save('ui-preview.png')
w.activity_button.setChecked(True)
app.processEvents()
assert w.logbox.isVisible()
w.activity_button.setChecked(False)
w.motion.setChecked(True)
assert w.orb.reduce_motion
w.prefill('افتح موقعًا')
assert w.input.text() == 'افتح موقعًا'
w.resize(940,720)
app.processEvents()
assert w.send.geometry().width() > 0
assert w.orb.width() >= 350
w.stop()
if w.listener: w.listener.stop()
w.tray.hide()
print('UI smoke test passed')
