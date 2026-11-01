import sys
import json
import threading
import time
from pathlib import Path
import keyring
import numpy as np
import miniaudio
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QSettings
from PySide6.QtGui import QColor, QPainter, QPen, QIcon, QPixmap, QShortcut, QKeySequence
from PySide6.QtWidgets import (QApplication,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,
    QLineEdit,QTextEdit,QDialog,QFormLayout,QComboBox,QCheckBox,QMessageBox,QSystemTrayIcon,
    QMenu,QDialogButtonBox,QTabWidget,QSpinBox)
try:
    import sounddevice as sd
except (ImportError,OSError): sd=None
from .visuals import Core
from .core import Agent,Desktop
from .voice import edge_synthesize
from .listening import Listener,wake_command

STYLE='''
QWidget {background:#000;color:#cce8e9;font-family:'Segoe UI';font-size:13px;}
QDialog,QTabWidget::pane {background:#080f16;}
QLabel {background:transparent;}
QPushButton {background:#10212b;border:1px solid #29404a;border-radius:8px;padding:10px 16px;}
QPushButton:hover {background:#203d48;}
QPushButton:disabled {color:#536770;}
QPushButton#gear {background:transparent;border:0;color:#76989e;font-size:22px;padding:8px;}
QLineEdit,QTextEdit,QComboBox,QSpinBox {background:#101d26;border:1px solid #29414b;border-radius:7px;padding:9px;}
QCheckBox {spacing:10px;background:transparent;}
QTabBar::tab {background:#10212b;padding:12px;}
QTabBar::tab:selected {background:#24434d;}
'''

class Job(QThread):
    result=Signal(str); error=Signal(str); status=Signal(str); approval=Signal(object)
    def __init__(self,kind,payload,config,history):
        super().__init__();self.kind=kind;self.payload=payload;self.config=config;self.history=history
        self.cancel=threading.Event();self.gate=threading.Event();self.accepted=False
        self.value=None
    def approve(self,args):
        self.accepted=False;self.gate.clear();self.approval.emit(args)
        while not self.gate.wait(.1):
            if self.cancel.is_set(): return False
        return self.accepted and not self.cancel.is_set()
    def run(self):
        try:
            if self.kind=='agent':
                value=Agent(self.config['or_key'],self.config['model'],Desktop(),self.approve,
                    self.status.emit,self.cancel).run(self.payload,self.history,vision=self.config['vision'])
            else: value=edge_synthesize(self.payload,self.config['voice'],self.config['tone'])
            self.result.emit(value)
        except Exception as exc: self.error.emit(f'{type(exc).__name__}: {exc}')

class Settings(QDialog):
    def __init__(self,parent):
        super().__init__(parent);self.setWindowTitle('JARVIS · الإعدادات');self.resize(680,600)
        root=QVBoxLayout(self);tabs=QTabWidget();root.addWidget(tabs);self.fields={};self.checks={}
        c=parent.config()
        def page(title):
            w=QWidget();f=QFormLayout(w);f.setSpacing(16);tabs.addTab(w,title);return f
        general=page('الذكاء والرؤية')
        for key,title in [('or_key','مفتاح OpenRouter'),('model','النموذج المجاني')]:
            w=QLineEdit(c[key]);self.fields[key]=w
            if key.endswith('key'):w.setEchoMode(QLineEdit.Password)
            general.addRow(title,w)
        def check(form,key,text):
            w=QCheckBox(text);w.setChecked(c[key]);self.checks[key]=w;form.addRow(w)
        check(general,'vision','تفعيل الرؤية: إرسال لقطات الشاشة إلى OpenRouter')
        note=QLabel('الرؤية تلتقط الشاشة عند الأمر وبعد الخطوات، وتشمل التطبيقات الظاهرة.\nالشاشة الرئيسية فقط. يتم إخفاء جارفيس أثناء التصوير.\nالنقر والكتابة يحتاجان تأكيدك. لا توجد مراقبة مصوّرة مستمرة.')
        note.setWordWrap(True);general.addRow(note)
        audio=page('الصوت والاستماع')
        k=QLineEdit(c['dg_key']);k.setEchoMode(QLineEdit.Password);self.fields['dg_key']=k;audio.addRow('مفتاح Deepgram',k)
        for key,title,options in [('voice','الصوت',['ar-DZ-IsmaelNeural','ar-SA-HamedNeural','ar-EG-ShakirNeural','en-GB-RyanNeural']),
            ('tone','النبرة',['serious','calm','energetic']),('stt_language','لغة الاستماع',['ar','en','fr'])]:
            w=QComboBox();w.addItems(options);w.setCurrentText(c[key]);self.fields[key]=w;audio.addRow(title,w)
        check(audio,'speak','نطق الردود عبر Edge TTS · دون مفتاح')
        check(audio,'listen','استماع مستمر لكلمة جارفيس عبر Deepgram')
        warning=QLabel('عند التفعيل، يُرسل صوت الميكروفون إلى Deepgram حتى قبل كلمة النداء، وقد يستهلك رصيدًا.\nيتوقف الميكروفون أثناء الرد والتنفيذ لمنع سماع نفسه.\nقل «جارفيس»، انتظر «نعم سيدي»، ثم أمْلِ أمرك.\nبعد الرد يمكنك متابعة الحديث؛ قل «شكرا جارفيس» للعودة للانتظار.')
        warning.setWordWrap(True);audio.addRow(warning)
        device=QComboBox();device.addItem('ميكروفون النظام الافتراضي',-1)
        if sd:
            try:
                for index,d in enumerate(sd.query_devices()):
                    if d['max_input_channels']>0:device.addItem(d['name'],index)
            except Exception:pass
        ix=device.findData(c['device']);device.setCurrentIndex(max(0,ix));self.device=device;audio.addRow('الميكروفون',device)
        idle=QSpinBox();idle.setRange(10,120);idle.setValue(c['idle']);idle.setSuffix(' ثانية');self.idle=idle;audio.addRow('مهلة متابعة الحديث',idle)
        display=page('الواجهة والتحكم')
        check(display,'greeting','الترحيب الصوتي عند التشغيل')
        check(display,'quiet','تقليل الحركة')
        check(display,'topmost','إبقاء الدائرة فوق النوافذ')
        display.addRow(QLabel('Ctrl+Alt+Esc: إيقاف التنفيذ والاستماع\nCtrl+,: الإعدادات · F11: ملء الشاشة\nإغلاق النافذة: العمل من شريط النظام'))
        resume=QPushButton('استئناف الاستماع');resume.clicked.connect(parent.resume_listening);display.addRow(resume)
        stop=QPushButton('إيقاف فوري');stop.clicked.connect(parent.stop);display.addRow(stop)
        chat=page('المحادثة والسجل')
        self.history=QTextEdit();self.history.setReadOnly(True);self.history.setPlainText('\n'.join(parent.logs));chat.addRow(self.history)
        self.command=QLineEdit();self.command.setPlaceholderText('اكتب أمرًا أو رسالة');chat.addRow(self.command)
        send=QPushButton('إرسال');send.clicked.connect(self.send);self.command.returnPressed.connect(self.send);chat.addRow(send)
        refresh=QPushButton('تحديث السجل');refresh.clicked.connect(lambda:self.history.setPlainText('\n'.join(parent.logs)));chat.addRow(refresh)
        clear=QPushButton('مسح المحادثة');clear.clicked.connect(self.clear);chat.addRow(clear)
        buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save);buttons.rejected.connect(self.reject);root.addWidget(buttons)
    def clear(self):self.parent().history.clear();self.parent().logs.clear();self.history.clear()
    def send(self):
        text=self.command.text().strip()
        if text:self.accept();QTimer.singleShot(0,lambda:self.parent().submit(text))
    def save(self):
        model=self.fields['model'].text().strip()
        if model!='openrouter/free' and not model.endswith(':free'):
            QMessageBox.warning(self,'Model','اختر نموذجًا مجانيًا ينتهي بـ :free');return
        if self.checks['listen'].isChecked() and not self.fields['dg_key'].text().strip():
            QMessageBox.warning(self,'Microphone','أضف مفتاح Deepgram لتفعيل الاستماع.');return
        try:
            for key,w in self.fields.items():
                value=w.text().strip() if isinstance(w,QLineEdit) else w.currentText()
                if key.endswith('_key'):keyring.set_password('YacineJarvis',key,value)
                else:self.parent().prefs.setValue(key,value)
            for key,w in self.checks.items():self.parent().prefs.setValue(key,w.isChecked())
            self.parent().prefs.setValue('device',self.device.currentData());self.parent().prefs.setValue('idle',self.idle.value())
            self.parent().paused=False;self.parent().apply_settings();self.accept()
        except Exception as exc:QMessageBox.warning(self,'Settings',str(exc))

class Window(QWidget):
    emergency=Signal()
    def __init__(self,boot=True):
        super().__init__();self.setWindowTitle('JARVIS');self.resize(900,720);self.setMinimumSize(440,480)
        self.prefs=QSettings('Appnova','YacineJarvis');self.jobs=set();self.current=None;self.history=[];self.logs=[]
        self.audio_file=None;self.playing=False;self.after_speech=None;self.voice_listener=None;self.listeners=set()
        self.paused=False;self.quitting=False;self.dialog=None;self.settings_open=False
        self.session=False;self.deadline=0;self.pending_command='';self.next_voice=None;self.ready_at=0;self.pending_action=False;self.epoch=0
        outer=QVBoxLayout(self);outer.setContentsMargins(20,12,20,25)
        top=QHBoxLayout();top.addStretch();self.gear=QPushButton('⚙');self.gear.setObjectName('gear')
        self.gear.setAccessibleName('الإعدادات');self.gear.setToolTip('الإعدادات · Ctrl+,');self.gear.clicked.connect(self.open_settings);top.addWidget(self.gear);outer.addLayout(top)
        self.orb=Core();outer.addWidget(self.orb,1)
        # The same original icon is used by the EXE, window and system tray.
        root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
        icon_path = root / 'assets' / 'jarvis.png'
        if icon_path.is_file():
            app_icon = QIcon(str(icon_path))
        else:
            pix = QPixmap(64, 64);pix.fill(Qt.black)
            p = QPainter(pix);p.setPen(QPen(QColor('#7fe7e9'),3))
            p.drawEllipse(9,9,46,46);p.end()
            app_icon = QIcon(pix)
        self.setWindowIcon(app_icon);self.tray=QSystemTrayIcon(app_icon,self)
        menu=QMenu();menu.addAction('إظهار',self.restore);menu.addAction('الإعدادات',self.open_settings)
        menu.addAction('استئناف الاستماع',self.resume_listening);menu.addAction('إيقاف',self.stop);menu.addAction('خروج',self.quit)
        self.tray.setContextMenu(menu);self.tray.activated.connect(lambda r:self.restore() if r==QSystemTrayIcon.Trigger else None);self.tray.show()
        self.emergency.connect(self.stop);self.hotkey=None
        try:
            from pynput.keyboard import GlobalHotKeys
            self.hotkey=GlobalHotKeys({'<ctrl>+<alt>+<esc>':self.emergency.emit});self.hotkey.start()
        except Exception as exc:self.log('HOTKEY',str(exc))
        QShortcut(QKeySequence('Ctrl+,'),self,activated=self.open_settings)
        QShortcut(QKeySequence('F11'),self,activated=lambda:self.showNormal() if self.isFullScreen() else self.showFullScreen())
        self.timer=QTimer(self);self.timer.timeout.connect(self.tick);self.timer.start(150)
        self.apply_settings()
        if boot:QTimer.singleShot(600,self.boot)
    def config(self):
        def secret(k):
            try:return keyring.get_password('YacineJarvis',k) or ''
            except Exception:return ''
        c={k:self.prefs.value(k,v) for k,v in dict(model='openrouter/free',voice='ar-DZ-IsmaelNeural',tone='serious',stt_language='ar').items()}
        for k,v in dict(speak=True,vision=False,listen=False,greeting=True,quiet=False,topmost=False).items():c[k]=self.prefs.value(k,v,type=bool)
        c.update(or_key=secret('or_key'),dg_key=secret('dg_key'),device=self.prefs.value('device',-1,type=int),idle=self.prefs.value('idle',30,type=int))
        return c
    def apply_settings(self):
        self.cached=self.config();self.orb.reduce_motion=self.cached['quiet']
        visible=self.isVisible();self.setWindowFlag(Qt.WindowStaysOnTopHint,self.cached['topmost'])
        if visible:self.show()
        self.halt_listener()
    def boot(self):
        if self.cached['greeting']:
            ready=self.cached['or_key'] and self.cached['dg_key'] and self.cached['listen']
            self.say('مرحبا سيدي، كل الأنظمة شغالة.' if ready else 'مرحبا سيدي. أكمل إعداداتي لنبدأ.')
        else:self.resume_listening()
    def log(self,who,text):
        self.logs.append(f'{who} › {text}');self.logs=self.logs[-150:]
        if who in ('ERROR','MIC'):
            self.gear.setToolTip(text+'\nافتح الإعدادات للتفاصيل')
            self.tray.showMessage('JARVIS',text,QSystemTrayIcon.Warning,5000)
    def restore(self):self.showNormal();self.raise_();self.activateWindow()
    def open_settings(self):
        if self.settings_open:return
        self.settings_open=True;self.halt_listener()
        try:Settings(self).exec()
        finally:self.settings_open=False
    def set_status(self,text):
        self.orb.mode='thinking';self.orb.active=True;self.tray.setToolTip('JARVIS · '+text)
    def halt_listener(self):
        if self.voice_listener:self.voice_listener.cancel.set();self.voice_listener=None
    def resume_listening(self):self.paused=False;self.session=False;self.deadline=0
    def start_listener(self):
        if self.listeners or self.voice_listener:return
        c=self.cached
        listener=Listener(c['dg_key'],c['stt_language'],None if c['device']<0 else c['device'])
        self.listeners.add(listener);self.voice_listener=listener
        listener.ready.connect(lambda:self.listener_ready(listener))
        listener.utterance.connect(lambda text:self.heard(listener,text))
        listener.error.connect(lambda text:self.listener_error(listener,text))
        listener.finished.connect(lambda:self.listener_finished(listener));listener.start()
    def listener_ready(self,listener):
        if self.voice_listener is listener:
            self.tray.setToolTip('JARVIS · الميكروفون يعمل · قل جارفيس')
            if self.session:self.deadline=time.monotonic()+self.cached['idle']
    def listener_error(self,listener,text):
        if self.voice_listener is listener:self.paused=True;self.log('MIC',text)
    def listener_finished(self,listener):
        self.listeners.discard(listener)
        if self.voice_listener is listener:self.voice_listener=None
        listener.deleteLater();self.maybe_quit()
    def heard(self,listener,text):
        if listener is not self.voice_listener or self.current or self.playing or self.paused:return
        if self.session and time.monotonic()>self.deadline:self.session=False
        if self.session and any(x in text for x in ['شكرا جارفيس','شكراً جارفيس','انتهينا','توقف عن الاستماع']):
            self.session=False;self.say('حاضر سيدي.');return
        command=wake_command(text)
        if not self.session:
            if command is None:return
            self.halt_listener();self.pending_command=command;self.say('نعم سيدي.',self.arm_command);return
        self.submit(command if command else text)
    def arm_command(self):
        self.session=True;self.deadline=time.monotonic()+self.cached['idle']
        if self.pending_command:
            command=self.pending_command;self.pending_command='';self.submit(command)
    def tick(self):
        try:playing=sd is not None and sd.get_stream().active
        except RuntimeError:playing=False
        if self.playing and not playing:
            self.playing=False;self.stop_audio();self.ready_at=time.monotonic()+.5
            callback=self.after_speech;self.after_speech=None
            if callback:callback()
        if not self.current:
            self.orb.mode='speaking' if playing else ('listening' if self.session and self.voice_listener else 'ready')
            self.orb.active=playing or bool(self.session and self.voice_listener)
        if self.session and not self.current and not playing and self.deadline and time.monotonic()>self.deadline:self.session=False
        if not (self.current or self.pending_action or playing or self.paused or self.quitting or self.settings_open) and time.monotonic()>self.ready_at:
            if self.cached['listen'] and self.cached['dg_key']:self.start_listener()
    def start_job(self,kind,payload):
        self.halt_listener();job=Job(kind,payload,self.cached,list(self.history));self.jobs.add(job);self.current=job
        job.status.connect(self.set_status);job.approval.connect(self.approve)
        job.result.connect(lambda value:self.result(job,value));job.error.connect(lambda text:self.log('ERROR',text))
        job.finished.connect(lambda:self.finished(job));self.set_status('جاري العمل');job.start()
    def result(self,job,value):job.value=value
    def finished(self,job):
        self.jobs.discard(job)
        if self.current is job:self.current=None
        value=job.value
        if job.cancel.is_set():
            if job.kind=='voice' and value:Path(value).unlink(missing_ok=True)
        elif value:
            if job.kind=='agent':
                self.history.extend([{'role':'user','content':job.payload},{'role':'assistant','content':value}]);self.history=self.history[-8:]
                self.log('JARVIS',value);self.restore();self.say(value,self.follow_up)
            else:
                try:
                    if sd is None:raise RuntimeError('Audio backend unavailable')
                    decoded=miniaudio.decode_file(value,output_format=miniaudio.SampleFormat.SIGNED16,nchannels=1,sample_rate=24000)
                    self.audio_file=value;sd.play(np.frombuffer(decoded.samples,dtype=np.int16),24000);self.playing=True
                except Exception as exc:
                    Path(value).unlink(missing_ok=True);self.log('ERROR',str(exc));self.finish_silent()
        else:
            self.restore()
            if job.kind=='voice':self.finish_silent()
        job.deleteLater();self.maybe_quit()
    def follow_up(self):self.session=True;self.deadline=time.monotonic()+self.cached['idle']
    def finish_silent(self):
        callback=self.after_speech;self.after_speech=None
        if callback:callback()
    def say(self,text,after=None):
        if self.current:return
        self.halt_listener();self.after_speech=after
        if self.cached['speak']:self.start_job('voice',text)
        else:self.finish_silent()
    def submit(self,text):
        if self.current or self.pending_action or not text.strip():return
        if not self.cached['or_key']:
            self.log('ERROR','أضف مفتاح OpenRouter في الإعدادات.');self.say('أضف مفتاح الذكاء في الإعدادات، سيدي.');return
        self.paused=False;self.stop_audio();self.halt_listener();self.log('YACINE',text)
        self.hide()
        # Give the compositor time to reveal the target applications before capture.
        self.ready_at=time.monotonic()+2
        self.pending_action=True;epoch=self.epoch
        def begin():
            if epoch!=self.epoch:return
            self.pending_action=False
            if not self.paused and not self.quitting:self.start_job('agent',text)
        QTimer.singleShot(350,begin)
    def approve(self,args):
        job=self.current
        if not job or job.cancel.is_set():return
        self.restore();self.dialog=QMessageBox(self)
        self.dialog.setWindowTitle('تأكيد التحكم')
        self.dialog.setText('السماح بهذه الخطوة؟\n'+json.dumps(args,ensure_ascii=False,indent=2))
        self.dialog.setStandardButtons(QMessageBox.Yes|QMessageBox.No);self.dialog.setDefaultButton(QMessageBox.No)
        accepted=self.dialog.exec()==QMessageBox.Yes;self.dialog=None
        if accepted and not job.cancel.is_set():
            self.hide()
            def release():job.accepted=True;job.gate.set()
            QTimer.singleShot(450,release)
        else:job.gate.set()
    def stop_audio(self):
        if sd:sd.stop()
        self.playing=False
        if self.audio_file:
            try:Path(self.audio_file).unlink(missing_ok=True)
            except OSError:pass
            self.audio_file=None
    def stop(self):
        self.epoch+=1;self.pending_action=False
        self.paused=True;self.session=False;self.pending_command='';self.after_speech=None;self.halt_listener()
        for job in self.jobs:job.cancel.set();job.gate.set()
        if self.dialog:self.dialog.reject()
        self.stop_audio();self.orb.active=False;self.orb.mode='ready';self.tray.setToolTip('JARVIS · متوقف')
    def closeEvent(self,event):
        event.ignore()
        if QSystemTrayIcon.isSystemTrayAvailable():self.hide()
        else:self.quit()
    def maybe_quit(self):
        if self.quitting and not self.jobs and not self.listeners:QApplication.quit()
    def quit(self):
        self.quitting=True;self.stop();self.hide();self.tray.hide()
        if self.hotkey:self.hotkey.stop()
        self.maybe_quit()

def launch(argv):
    app=QApplication(argv);app.setQuitOnLastWindowClosed(False);app.setStyleSheet(STYLE)
    window=Window();window.show();raise SystemExit(app.exec())
