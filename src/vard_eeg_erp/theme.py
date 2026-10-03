"""Light desktop styling inspired by Metronic's spacing and color language."""

STYLE = """
QWidget { color: #252F4A; font-size: 13px; }
QMainWindow, QWidget#workspace { background: #F5F7FA; }
QFrame#sidebar { background: #FFFFFF; border-right: 1px solid #E8EDF3; }
QFrame#card, QFrame#toolbar { background: #FFFFFF; border: 1px solid #E8EDF3; border-radius: 12px; }
QLabel { background: transparent; border: none; }
QLabel#brand { color: #1B84FF; font-size: 26px; font-weight: 800; }
QLabel#title { font-size: 25px; font-weight: 700; }
QLabel#subtitle, QLabel#muted { color: #78829D; font-size: 12px; }
QLabel#section { font-size: 15px; font-weight: 700; }
QLabel#metric { font-size: 25px; font-weight: 700; }
QLabel#badge { background: #FFF8DD; color: #8A6500; border-radius: 6px; padding: 7px 12px; font-weight: 600; }
QLabel#notice { background: #EFF6FF; color: #315885; border-radius: 8px; padding: 12px; }
QPushButton { background: #FFFFFF; border: 1px solid #DBDFE9; border-radius: 7px; padding: 9px 14px; font-weight: 600; }
QPushButton:hover { background: #F1F6FC; border-color: #A6CFFF; }
QPushButton:pressed { background: #DBEAFE; }
QPushButton#primary { background: #1B84FF; color: white; border: 1px solid #1B84FF; }
QPushButton#primary:hover { background: #0671E8; }
QPushButton:disabled { color: #99A1B7; background: #F4F5F8; border-color: #E8EDF3; }
QPushButton#nav { text-align: left; border: none; padding: 12px 14px; color: #78829D; }
QPushButton#nav:checked { background: #EFF6FF; color: #1B84FF; }
QPushButton#nav:hover { background: #F5F8FC; }
QComboBox, QDoubleSpinBox, QSpinBox, QLineEdit { background: #FFFFFF; border: 1px solid #DBDFE9; border-radius: 6px; padding: 7px; min-height: 20px; }
QComboBox:focus, QDoubleSpinBox:focus { border-color: #1B84FF; }
QComboBox QAbstractItemView { background: #FFFFFF; selection-background-color: #EFF6FF; selection-color: #1B84FF; }
QTableWidget { background: #FFFFFF; alternate-background-color: #F9FAFC; border: none; gridline-color: #EFF2F5; selection-background-color: #EFF6FF; selection-color: #1B84FF; }
QHeaderView::section { background: #F9FAFC; color: #78829D; border: none; border-bottom: 1px solid #EFF2F5; padding: 10px; font-weight: 600; }
QSlider::groove:horizontal { height: 5px; background: #E8EDF3; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #1B84FF; border-radius: 2px; }
QSlider::handle:horizontal { background: #1B84FF; width: 14px; margin: -5px 0; border-radius: 7px; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: #F5F7FA; width: 8px; }
QScrollBar::handle:vertical { background: #CBD5E1; border-radius: 4px; min-height: 24px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QDialog { background: #FFFFFF; }
QPlainTextEdit { background: #F9FAFC; border: 1px solid #E8EDF3; border-radius: 8px; padding: 12px; }
QProgressBar { background: #E8EDF3; border: none; border-radius: 2px; max-height: 4px; }
QProgressBar::chunk { background: #1B84FF; }
QToolTip { background: #252F4A; color: white; border: none; padding: 6px; }
"""
