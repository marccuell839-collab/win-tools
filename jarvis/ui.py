import json
import math
import threading
from pathlib import Path

import keyring
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QSettings, QRectF, QUrl
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QIcon, QPixmap
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTextEdit, QDialog, QFormLayout, QComboBox, QCheckBox,
    QMessageBox, QSystemTrayIcon, QMenu, QDialogButtonBox)
try:
    import sounddevice as sd
except (ImportError, OSError):
    sd = None
import miniaudio
import numpy as np
from .core import Agent, Desktop
from .voice import transcribe, edge_synthesize

from .visuals import Core as Orb

STYLE = """
QWidget { background:#080f16; color:#d7e5e7; font-family:'Segoe UI'; font-size:13px; }
QLabel { background:transparent; }
QLabel#brand {color:#e8f3f2; font-size:19px; font-weight:600; letter-spacing:5px;}
QLabel#eyebrow {color:#75b9bb; font-family:Consolas; font-size:10px; letter-spacing:2px;}
QLabel#sub {color:#81979f; font-size:11px;}
QLabel#greeting {color:#edf4ef; font-size:32px; font-weight:300;}
QLabel#headline {color:#dcf0ec; font-size:21px; font-weight:400;}
QLabel#detail {color:#92a6ad; font-size:12px;}
QLabel#status {color:#b6e9df; font-size:12px;}
QWidget#card {background:#0c1720; border:1px solid #1b303a; border-radius:12px;}
QWidget#command {background:#10202a; border:1px solid #29424b; border-radius:16px;}
QLineEdit,QTextEdit,QComboBox {background:#101e28; color:#e4efed; border:1px solid #29414b; border-radius:9px; padding:11px; selection-background-color:#2d626b;}
QLineEdit#commandInput {background:transparent; border:0; font-size:16px; padding:12px;}
QTextEdit {font-size:13px;}
QPushButton {background:#10212b; border:1px solid #29404a; border-radius:8px; padding:10px 14px; color:#b9cdd0;}
QPushButton:hover {background:#1a323c; border-color:#6ea5aa; color:#f1fffc;}
QPushButton:pressed {background:#254650;}
QPushButton:disabled {color:#536c75; border-color:#1a2c35;}
QPushButton#quiet {background:transparent; border:0; color:#8caaaf; padding:7px 10px;}
QPushButton#quiet:hover {background:#132630; color:#d6f6ee;}
QPushButton#stop {background:#251b20; border-color:#493038; color:#dcacaf;}
QPushButton#primary {background:#b1e8dc; border:0; color:#102f32; font-weight:600;}
QPushButton#primary:hover {background:#d4fff1;}
QCheckBox {color:#8fa7ae; font-size:11px; spacing:8px; background:transparent;}
QCheckBox::indicator {width:14px;height:14px;border:1px solid #44616d;border-radius:4px;background:#0d1c26;}
QCheckBox::indicator:checked {background:#9ad7ce;border-color:#9ad7ce;}
QToolTip {background:#16303b;color:#e4f5ef;border:1px solid #416774;padding:7px;}
"""

class Job(QThread):
    result = Signal(str)
    error = Signal(str)
    status = Signal(str)
    approval = Signal(object)
    def __init__(self, kind, payload, config, history):
        super().__init__()
        self.kind,self.payload,self.config,self.history = kind,payload,config,history
        self.cancel = threading.Event()
        self.gate = threading.Event()
        self.accepted = False
    def approve(self,args):
        self.accepted = False
        self.gate.clear()
        self.approval.emit(args)
        while not self.gate.wait(.1):
            if self.cancel.is_set(): return False
        return self.accepted and not self.cancel.is_set()
    def run(self):
        try:
            if self.kind == 'agent':
                agent = Agent(self.config['or_key'],self.config['model'],Desktop(),self.approve,self.status.emit,self.cancel)
                answer = agent.run(self.payload,self.history)
            elif self.kind == 'transcribe':
                answer = transcribe(self.config['dg_key'],self.payload,self.config['stt_language'])
            else:
                answer = edge_synthesize(self.payload,self.config['voice'],self.config['tone'])
            self.result.emit(answer)
        except Exception as exc:
            self.error.emit(f'{type(exc).__name__}: {exc}')

class Settings(QDialog):
    def __init__(self,parent):
        super().__init__(parent)
        self.setWindowTitle('JARVIS · الإعدادات')
        self.setMinimumWidth(480)
        form = QFormLayout(self)
        self.fields = {}
        c = parent.config()
        for key,label in [('or_key','OpenRouter API key'),('dg_key','Deepgram key · اختياري للميكروفون'),('model','Free model')]:
            edit = QLineEdit(c[key])
            if key.endswith('_key'): edit.setEchoMode(QLineEdit.Password)
            form.addRow(label, edit)
            self.fields[key] = edit
        for key,label,choices in [
            ('voice','الصوت الرجالي · Edge TTS',['ar-DZ-IsmaelNeural','ar-SA-HamedNeural','ar-EG-ShakirNeural','en-GB-RyanNeural']),
            ('tone','النبرة',['serious','calm','energetic']),
            ('stt_language','لغة الميكروفون',['ar','en','fr'])]:
            box = QComboBox()
            box.addItems(choices)
            box.setCurrentText(c[key])
            form.addRow(label,box)
            self.fields[key] = box
        self.voice_enabled = QCheckBox('نطق الردود عبر Edge TTS · إنترنت، دون مفتاح')
        self.voice_enabled.setChecked(c['speak'])
        form.addRow(self.voice_enabled)
        info = QLabel('النبرة تغيّر السرعة والحدة، وليست محاكاة مشاعر كاملة.\nالمفاتيح تُحفظ في Windows Credential Manager.\nDeepgram اختياري وقد يستهلك رصيدًا. لا توجد نماذج محلية ثقيلة.')
        info.setWordWrap(True)
        form.addRow(info)
        buttons = QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)
    def save(self):
        model = self.fields['model'].text().strip()
        if model != 'openrouter/free' and not model.endswith(':free'):
            QMessageBox.warning(self,'Model','اختر openrouter/free أو نموذجًا ينتهي بـ :free')
            return
        try:
            for key,field in self.fields.items():
                value = field.text().strip() if isinstance(field,QLineEdit) else field.currentText()
                if key.endswith('_key'):
                    keyring.set_password('YacineJarvis',key,value)
                else: self.parent().prefs.setValue(key,value)
            self.parent().prefs.setValue('speak',self.voice_enabled.isChecked())
            self.parent().refresh_connection()
            self.accept()
        except Exception as exc:
            QMessageBox.warning(self,'Key storage failed',str(exc))

class Window(QWidget):
    emergency = Signal()
    def __init__(self):
        super().__init__()
        self.setWindowTitle('JARVIS · Yacine')
        self.setWindowFlags(self.windowFlags()|Qt.WindowStaysOnTopHint)
        self.resize(1100,780)
        self.setMinimumSize(940,720)
        self.prefs = QSettings('Appnova','YacineJarvis')
        self.jobs = set()
        self.current = None
        self.history = []
        self.recording = None
        self.frames = []
        self.recorded_samples = 0
        self.audio_file = None
        self.dialog = None
        self.quitting = False
        self.play_timer = QTimer(self)
        self.play_timer.timeout.connect(self.playback_changed)
        self.play_timer.start(250)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(36,26,36,22)
        outer.setSpacing(12)
        def label(text,name='sub'):
            w=QLabel(text); w.setObjectName(name); return w
        top=QHBoxLayout()
        top.addWidget(label('J A R V I S','brand'))
        top.addWidget(label('  /  PERSONAL INTELLIGENCE','eyebrow'))
        top.addStretch()
        self.motion=QPushButton('حركة هادئة'); self.motion.setObjectName('quiet')
        self.motion.setCheckable(True); top.addWidget(self.motion)
        settings=QPushButton('الإعدادات'); settings.setObjectName('quiet')
        settings.clicked.connect(lambda: Settings(self).exec()); top.addWidget(settings)
        outer.addLayout(top)
        divider=QWidget(); divider.setFixedHeight(1); divider.setStyleSheet('background:#21313a;'); outer.addWidget(divider)
        greeting=QHBoxLayout(); greeting.setContentsMargins(0,12,0,0)
        greeting.addWidget(label('مساحتك. بصوتك.','greeting')); greeting.addStretch()
        identity=QVBoxLayout(); identity.addWidget(label('YACINE / PRIVATE DESKTOP','eyebrow'))
        identity.addWidget(label('مصمّم ليكون امتدادًا لأوامرك.','detail'))
        greeting.addLayout(identity); outer.addLayout(greeting)
        body=QHBoxLayout(); body.setSpacing(16)
        left=QVBoxLayout(); left.setSpacing(15); left.addStretch()
        left.addWidget(label('01  /  CONNECTION','eyebrow'))
        left.addWidget(label('حاضر يا ياسين.','headline'))
        intro=label('اكتب ما تريد، أو سجّل صوتك.\nخطوة بخطوة، أمام عينيك.','detail')
        intro.setWordWrap(True); left.addWidget(intro)
        left.addSpacing(16)
        for title,prompt in [('افتح موقعًا  ↗','افتح موقع '),('ساعدني في مهمة  ↗','ساعدني في '),('اشرح ما على الشاشة  ↗','اشرح لي ما يظهر على شاشتي')]:
            button=QPushButton(title); button.setObjectName('quiet')
            button.clicked.connect(lambda checked=False,text=prompt:self.prefill(text))
            left.addWidget(button)
        left.addStretch()
        left_widget=QWidget(); left_widget.setFixedWidth(218); left_widget.setLayout(left); body.addWidget(left_widget)
        self.orb=Orb(); body.addWidget(self.orb,1)
        self.motion.toggled.connect(self.set_motion)
        right=QVBoxLayout(); right.setSpacing(12); right.addStretch()
        def card(kicker,title,detail):
            box=QWidget(); box.setObjectName('card')
            layout=QVBoxLayout(box); layout.setContentsMargins(16,16,16,16); layout.setSpacing(8)
            layout.addWidget(label(kicker,'eyebrow'))
            heading=label(title,'detail'); heading.setWordWrap(True); layout.addWidget(heading)
            sub=label(detail,'sub'); sub.setWordWrap(True); layout.addWidget(sub)
            right.addWidget(box)
            return heading
        self.connection=card('INTELLIGENCE','OpenRouter','نموذج مجاني · يحتاج مفتاحك')
        card('VOICE ENGINE','صوت عربي رجالي','Edge TTS · دون مفتاح')
        self.screen_state=card('DESKTOP ACCESS','الرؤية متوقفة','تتحكّم أنت في كل خطوة')
        right.addStretch()
        right_widget=QWidget(); right_widget.setFixedWidth(190); right_widget.setLayout(right); body.addWidget(right_widget)
        outer.addLayout(body,1)
        self.status=label('●  جاهز · في انتظار أوامرك','status'); self.status.setAlignment(Qt.AlignCenter); outer.addWidget(self.status)
        command=QWidget(); command.setObjectName('command')
        command_row=QHBoxLayout(command); command_row.setContentsMargins(10,8,10,8)
        self.input=QLineEdit(); self.input.setObjectName('commandInput'); self.input.setPlaceholderText('ماذا نفعل اليوم، ياسين؟')
        self.input.setAlignment(Qt.AlignRight); self.input.returnPressed.connect(self.submit); command_row.addWidget(self.input,1)
        self.mic=QPushButton('تسجيل صوتي'); self.mic.clicked.connect(self.toggle_record); command_row.addWidget(self.mic)
        self.send=QPushButton('تنفيذ  ↗'); self.send.setObjectName('primary'); self.send.clicked.connect(self.submit); command_row.addWidget(self.send)
        outer.addWidget(command)
        permission=QHBoxLayout()
        self.screen=QCheckBox('السماح بإرسال لقطات الشاشة إلى OpenRouter لهذه الجلسة')
        self.screen.toggled.connect(lambda on:self.screen_state.setText('الرؤية مفعّلة لهذه الجلسة' if on else 'الرؤية متوقفة'))
        permission.addWidget(self.screen); permission.addStretch()
        stop=QPushButton('إيقاف'); stop.setObjectName('stop'); stop.clicked.connect(self.stop); permission.addWidget(stop)
        outer.addLayout(permission)
        bottom=QHBoxLayout()
        self.activity_button=QPushButton('سجل النشاط  +'); self.activity_button.setObjectName('quiet'); self.activity_button.setCheckable(True)
        bottom.addWidget(self.activity_button); bottom.addStretch()
        bottom.addWidget(label('CTRL + ALT + ESC  /  STOP','eyebrow'))
        bottom.addStretch(); bottom.addWidget(label('APPNOVA  /  DESKTOP EDITION','eyebrow'))
        outer.addLayout(bottom)
        self.logbox=QTextEdit(); self.logbox.setReadOnly(True); self.logbox.setFixedHeight(145); self.logbox.hide()
        self.activity_button.toggled.connect(self.toggle_activity); outer.addWidget(self.logbox)
        self.log('JARVIS','جاهز يا ياسين. أضف مفتاح OpenRouter في الإعدادات.')
        self.record_timer = QTimer(self); self.record_timer.setSingleShot(True); self.record_timer.timeout.connect(self.finish_record)
        self.emergency.connect(self.stop)
        self.listener = None
        try:
            from pynput.keyboard import GlobalHotKeys
            self.listener = GlobalHotKeys({'<ctrl>+<alt>+<esc>':self.emergency.emit})
            self.listener.start()
        except Exception as exc: self.log('HOTKEY',str(exc))
        pix = QPixmap(64,64); pix.fill(QColor('#07101b'))
        paint = QPainter(pix); paint.setPen(QPen(QColor('#63e5ff'),5)); paint.drawEllipse(10,10,44,44); paint.end()
        self.setWindowIcon(QIcon(pix))
        self.tray = QSystemTrayIcon(QIcon(pix),self)
        menu = QMenu(); menu.addAction('إظهار JARVIS',self.restore); menu.addAction('إيقاف',self.stop); menu.addAction('خروج',self.quit)
        self.tray.setContextMenu(menu); self.tray.activated.connect(lambda reason:self.restore() if reason == QSystemTrayIcon.Trigger else None); self.tray.show()
        self.tray.setToolTip('JARVIS · Yacine')
        self.refresh_connection()
    def refresh_connection(self):
        self.connection.setText('OpenRouter · مفتاح محفوظ' if self.config()['or_key'] else 'OpenRouter · أضف مفتاحك')
    def prefill(self,text):
        self.input.setText(text); self.input.setFocus()
    def set_motion(self,quiet):
        self.orb.reduce_motion = quiet
        self.motion.setText('تشغيل الحركة' if quiet else 'حركة هادئة')
        self.orb.update()
    def toggle_activity(self,visible):
        self.logbox.setVisible(visible)
        self.activity_button.setText('سجل النشاط  −' if visible else 'سجل النشاط  +')
    def set_status(self,text):
        translations={'ANALYZING':'جاري التفكير','EXECUTING':'جاري التنفيذ','LISTENING':'أسمعك'}
        for key,value in translations.items(): text=text.replace(key,value)
        self.status.setText('●  '+text)
        if 'التفكير' in text: self.orb.mode='thinking'
    def config(self):
        def secret(key):
            try: return keyring.get_password('YacineJarvis',key) or ''
            except Exception: return ''
        return {'or_key':secret('or_key'),'dg_key':secret('dg_key'),
            'model':self.prefs.value('model','openrouter/free'),
            'voice':self.prefs.value('voice','ar-DZ-IsmaelNeural'),
            'tone':self.prefs.value('tone','serious'),
            'stt_language':self.prefs.value('stt_language','ar'),
            'speak':self.prefs.value('speak',True,type=bool)}
    def log(self,who,text):
        self.logbox.append('')
        cursor = self.logbox.textCursor(); cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(f'{who}  ›  {text}\n')
        self.logbox.setTextCursor(cursor); self.logbox.ensureCursorVisible()
    def restore(self):
        self.showNormal(); self.raise_(); self.activateWindow()
    def start_job(self,kind,payload):
        job = Job(kind,payload,self.config(),list(self.history))
        self.jobs.add(job); self.current = job
        self.send.setEnabled(False); self.mic.setEnabled(False); self.orb.active = True
        self.orb.mode = 'thinking'
        self.set_status('جاري تجهيز الرد الصوتي…' if kind == 'voice' else 'جاري العمل…')
        job.status.connect(self.set_status)
        job.approval.connect(self.approve)
        job.result.connect(lambda result:self.result(job,result))
        job.error.connect(lambda err:self.log('ERROR',err))
        job.finished.connect(lambda:self.finished(job))
        job.start()
    def finished(self,job):
        self.jobs.discard(job)
        if self.current is job:
            self.current = None; self.send.setEnabled(True); self.mic.setEnabled(True)
            self.orb.active = False; self.set_status('جاهز · في انتظار أوامرك')
        job.deleteLater()
        if self.quitting and not self.jobs: QApplication.quit()
    def submit(self):
        text = self.input.text().strip()
        if not text or self.current or self.recording: return
        if not self.config()['or_key']:
            Settings(self).exec(); return
        if not self.screen.isChecked():
            QMessageBox.information(self,'Screen permission','التحكم يحتاج موافقتك على إرسال لقطات الشاشة. فعّل الخيار فوق حقل الأوامر.'); return
        self.stop_audio(); self.input.clear(); self.log('YACINE',text)
        self.hide()
        self.start_job('agent',text)
    def result(self,job,value):
        if job.cancel.is_set():
            if job.kind == 'voice': Path(value).unlink(missing_ok=True)
            return
        if job.kind == 'agent':
            self.history.extend([{'role':'user','content':job.payload},{'role':'assistant','content':value}])
            self.history = self.history[-8:]
            self.log('JARVIS',value)
            if self.config()['speak']:
                # Start next job after this thread has fully finished.
                job.finished.connect(lambda:self.start_job('voice',value) if not job.cancel.is_set() and not self.quitting else None)
        elif job.kind == 'transcribe':
            self.input.setText(value)
            self.log('MIC','راجع الأمر ثم اضغط تنفيذ.' if value else 'لم يتم التعرّف على كلام.')
        else:
            self.stop_audio(); self.audio_file = value
            try:
                if sd is None: raise RuntimeError('Audio backend unavailable; text mode still works.')
                decoded = miniaudio.decode_file(value, output_format=miniaudio.SampleFormat.SIGNED16, nchannels=1, sample_rate=24000)
                sd.play(np.frombuffer(decoded.samples, dtype=np.int16), 24000)
                self.orb.active = True
            except Exception as exc:
                self.log('VOICE',str(exc))
    def approve(self,args):
        job = self.current
        if not job or job.cancel.is_set(): return
        self.dialog = QMessageBox(self)
        self.dialog.setWindowTitle('تأكيد التحكم · JARVIS')
        self.dialog.setText('السماح بهذه الخطوة؟\n'+json.dumps(args,ensure_ascii=False,indent=2))
        self.dialog.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
        self.dialog.setDefaultButton(QMessageBox.No)
        self.restore()
        accepted = self.dialog.exec() == QMessageBox.Yes
        self.dialog = None
        if accepted and not job.cancel.is_set():
            self.hide()
            # Allow focus to return to the target before releasing worker.
            def release():
                job.accepted = True; job.gate.set()
            QTimer.singleShot(450,release)
        else: job.gate.set()
    def toggle_record(self):
        if self.recording:
            self.finish_record(); return
        if self.current: return
        if not self.config()['dg_key']:
            QMessageBox.information(self,'Microphone','Edge TTS ينطق فقط. للتعرّف على كلامك أضف Deepgram key، أو اكتب الأمر.'); return
        self.stop_audio()
        try:
            import sounddevice as sd
            self.frames = []; self.recorded_samples = 0
            def callback(data,frames,time,status):
                if self.recorded_samples < 16000*30:
                    self.frames.append(bytes(data)); self.recorded_samples += frames
            self.recording = sd.RawInputStream(samplerate=16000,channels=1,dtype='int16',callback=callback)
            self.recording.start(); self.mic.setText('■ إنهاء التسجيل'); self.send.setEnabled(False)
            self.set_status('LISTENING · تسجيل حتى 30 ثانية'); self.orb.active = True; self.orb.mode = 'listening'
            self.record_timer.start(30000)
        except Exception as exc:
            self.close_recording(); self.log('MIC',str(exc))
    def close_recording(self):
        self.record_timer.stop()
        if self.recording:
            self.recording.stop(); self.recording.close(); self.recording = None
        self.mic.setText('تسجيل صوتي'); self.send.setEnabled(not bool(self.current))
    def finish_record(self):
        if not self.recording: return
        self.close_recording()
        pcm = b''.join(self.frames); self.frames.clear()
        if pcm: self.start_job('transcribe',pcm)
    def playback_changed(self):
        try: playing = sd is not None and sd.get_stream().active
        except RuntimeError: playing = False
        if not self.current and not self.recording:
            self.orb.active = playing
            self.orb.mode = 'speaking' if playing else 'ready'

    def stop_audio(self):
        if sd is not None: sd.stop()
        if self.audio_file:
            try: Path(self.audio_file).unlink(missing_ok=True)
            except OSError: pass
            self.audio_file = None
    def stop(self):
        for job in self.jobs: job.cancel.set(); job.gate.set()
        if self.dialog: self.dialog.reject()
        self.close_recording(); self.frames.clear(); self.stop_audio()
        self.set_status('توقّف بأمرك'); self.orb.active = False; self.orb.mode = 'ready'
    def closeEvent(self,event):
        if QSystemTrayIcon.isSystemTrayAvailable():
            event.ignore(); self.hide()
        else:
            event.ignore(); self.quit()
    def quit(self):
        self.quitting = True; self.stop(); self.hide(); self.tray.hide()
        if self.listener: self.listener.stop()
        if not self.jobs: QApplication.quit()


def launch(argv):
    app = QApplication(argv)
    app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(STYLE)
    window = Window(); window.show()
    sys_exit = app.exec()
    raise SystemExit(sys_exit)
