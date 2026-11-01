"""Procedural, resolution-independent HUD. No image assets or video loops."""
import math
import time
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer
from PySide6.QtGui import QPainter, QPen, QColor, QRadialGradient, QPainterPath, QFont
from PySide6.QtWidgets import QWidget


class Core(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(350, 400)
        self.phase = 0.0
        self.active = False
        self.mode = 'ready'
        self.reduce_motion = False
        self.last = time.monotonic()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)

    def tick(self):
        now = time.monotonic()
        dt = min(now - self.last, .1)
        self.last = now
        if self.isVisible() and not self.reduce_motion:
            self.phase += dt * (1 if self.active else .3)
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.translate(self.width()/2, self.height()/2)
        scale = min(self.width()/480, self.height()/460)
        p.scale(scale, scale)
        t = self.phase
        cyan = QColor('#7fe7e9')
        if self.mode == 'listening': cyan = QColor('#c1eee0')
        elif self.mode == 'thinking': cyan = QColor('#8cc5fc')
        elif self.mode == 'speaking': cyan = QColor('#80eedb')
        # Quiet halo; fades naturally into the application surface.
        glow = QRadialGradient(0, 0, 235)
        glow.setColorAt(0, QColor(45,134,155,28))
        glow.setColorAt(.58, QColor(31,116,132,22))
        glow.setColorAt(1, QColor(8,16,23,0))
        p.setPen(Qt.NoPen); p.setBrush(glow); p.drawEllipse(QRectF(-235,-235,470,470))
        p.setBrush(Qt.NoBrush)
        for radius in (153,182,196):
            p.setPen(QPen(QColor(111,196,208,35), .7))
            p.drawEllipse(QRectF(-radius,-radius,radius*2,radius*2))
        for i in range(120):
            a = math.radians(i*3)
            r = 197
            length = 8 if i%10 == 0 else (4 if i%5 == 0 else 2)
            p.setPen(QPen(QColor(124,202,214,110 if i%5==0 else 38),1))
            p.drawLine(QPointF(math.cos(a)*r,math.sin(a)*r),QPointF(math.cos(a)*(r+length),math.sin(a)*(r+length)))
        for radius,angle,span in [(182,t*20,65),(182,t*20+180,35),(169,-t*13+50,105),(154,t*11+190,44)]:
            for width,alpha in [(6,10),(3,25),(1.2,180)]:
                c = QColor(cyan); c.setAlpha(alpha)
                p.setPen(QPen(c,width)); p.drawArc(QRectF(-radius,-radius,2*radius,2*radius),int(angle*16),span*16)
        # A moving spherical field, projected from real 3D meridians.
        def project(lat,lon):
            r = 130 + 2*math.sin(t*1.2)
            x = r*math.cos(lat)*math.cos(lon)
            y = r*math.sin(lat)
            z = r*math.cos(lat)*math.sin(lon)
            tilt = .28
            return QPointF(x, y*math.cos(tilt)-z*math.sin(tilt)),z
        for j in range(22):
            path = QPainterPath()
            lon = j*math.tau/22+t*.16
            for k in range(65):
                pt,z = project(-math.pi/2+k*math.pi/64,lon)
                if k == 0: path.moveTo(pt)
                else: path.lineTo(pt)
            p.setPen(QPen(QColor(90,202,219,40+int(22*(1+math.sin(lon)))),.65)); p.drawPath(path)
        for j in range(-7,8):
            path = QPainterPath()
            for k in range(97):
                pt,z = project(j*math.pi/18,k*math.tau/96)
                if k == 0: path.moveTo(pt)
                else: path.lineTo(pt)
            p.setPen(QPen(QColor(86,193,211,52),.65)); p.drawPath(path)
        # Center plate makes typography legible over the spherical mesh.
        inner = QRadialGradient(0,0,110)
        inner.setColorAt(0,QColor(7,18,25,248)); inner.setColorAt(.6,QColor(7,18,25,225)); inner.setColorAt(1,QColor(7,18,25,0))
        p.setPen(Qt.NoPen); p.setBrush(inner); p.drawEllipse(QRectF(-110,-110,220,220)); p.setBrush(Qt.NoBrush)
        p.setPen(QColor('#c3f8f2'))
        font = QFont('Segoe UI',25,QFont.Light); font.setLetterSpacing(QFont.AbsoluteSpacing,7)
        p.setFont(font); p.drawText(QRectF(-118,-30,243,52),Qt.AlignCenter,'JARVIS')
        p.setFont(QFont('Consolas',8)); p.setPen(QColor('#61949d'))
        p.drawText(QRectF(-110,23,220,20),Qt.AlignCenter,'P E R S O N A L   C O R E')
        for i in range(-19,20):
            envelope = math.exp(-((i/12)**2))
            h = 2 + envelope*(16 if self.active else 5)*abs(math.sin(i*.55+t*3))
            c = QColor(cyan); c.setAlpha(90+int(envelope*150))
            p.setPen(QPen(c,1.5)); p.drawLine(QPointF(i*4,60-h),QPointF(i*4,60+h))
        for angle in (t*.3, t*.3+2.3):
            x,y = math.cos(angle)*182, math.sin(angle)*182
            p.setPen(Qt.NoPen); p.setBrush(QColor('#e7fff9')); p.drawEllipse(QPointF(x,y),2.4,2.4)
        p.setBrush(Qt.NoBrush)
        for side in (-1,1):
            p.setPen(QPen(QColor('#385b65'),1))
            x = side*218
            p.drawLine(QPointF(x,-22),QPointF(x,22))
            p.drawLine(QPointF(x,0),QPointF(x+side*9,0))
        p.end()
