#!/usr/bin/python3

from pyVoIP.VoIP import VoIPPhone, InvalidStateError
from pprint import pprint
import configparser
import socket
import ifaddr
import uuid
import requests
import sys

from PySide6.QtGui import QIcon, QAction, QPixmap
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget

#Get computer ID, tested in both Windows and Linux
computer_id = hex(uuid.getnode())[2:]

#Get LAN ip address of computer
adapters = ifaddr.get_adapters()
myipv4=None
for adapter in adapters:
  if myipv4 is not None:
    break
  if adapter.name != 'lo' and \
     not adapter.name.startswith('docker') and \
     not adapter.name.startswith('br-') and \
     not 'Loopback' in adapter.name:
    #print("IP of network adapter " + adapter.nice_name)
    #print(adapter.ips)
    for ip in adapter.ips:
      if isinstance(ip.ip, str):
        myipv4=ip.ip
        break
        #print("   %s/%s" % (ip.ip, ip.network_prefix))

def download_config(computer_id):
  res = requests.get('https://cloudaware.eu/'+computer_id+'.ini')
  if res.status_code == 200:
    print("Downloading new config!")
    with open('config.ini', 'w') as file:
      file.write(res.text)

def read_config():
  config = configparser.ConfigParser()
  config.read('config.ini')
  return config

def get_actions():
  actions = []
  for section in config.sections():
    if section.startswith('action_'):
      actions.append(section)
  print(actions)
    
download_config(computer_id)
config = read_config()
actions = get_actions()

#print(config['DEFAULT']['path'])     # -> "/path/name/"
#config['DEFAULT']['path'] = '/var/shared/'    # update
#config['DEFAULT']['default_message'] = 'Hey! help me!!'   # create
#with open('config.ini', 'w') as configfile:    # save
#    config.write(configfile)

def action_exec(configitems, voipdata):
  print(configitems['executable'])

def action_webhook(configitems, voipdata):
  print(configitems['url'])


def answer(call):
  try:
    print("Answering")
    #pprint(call.request)
    pprint(call.request.headers['From']['number'])
    for action in actions:
      if 'enabled' in config[action] and \
        ( config[action]['enabled'] != 'false' or config[action]['enabled'] != 'False' ):
        func = getattr(sys.modules[__name__], action)
        func(dict(config[action]), call.request.headers)
    #pprint(call.request.body)
    #call.answer()
    #call.hangup()
  except InvalidStateError:
    pass

class MainWindow(QMainWindow):
  def __init__(self):
    super().__init__()
    self.setWindowTitle("VoIP CTI")
    layout = QVBoxLayout()

    logo = QLabel(self)
    pixmap = QPixmap('Telforce_logo_v1.png')
    logo.setPixmap(pixmap)

    label = QLabel("VoIP CTI 1.0\nComputer ID: %s" %(computer_id) )
    #self.button = QPushButton("Push for Window")
    layout.addWidget(logo)
    layout.addWidget(label)
    #layout.addWidget(self.button)
    #self.setLayout(layout)
    #self.button.clicked.connect(self.show_new_window)
    #self.setCentralWidget(self.button)
    widget = QWidget()
    widget.setLayout(layout)
    self.setCentralWidget(widget)

if __name__ == "__main__":
  phone = VoIPPhone(config['voip']['host'], int(config['voip']['port']), config['voip']['user'], config['voip']['password'], myIP=myipv4, callCallback=answer)
  phone.start()

  app = QApplication([])
  app.setQuitOnLastWindowClosed(False)

  # Create the icon
  icon = QIcon("telephone-handset.png")

  # Create the tray
  tray = QSystemTrayIcon()
  tray.setIcon(icon)
  tray.setVisible(True)

  w = MainWindow()

  # Create the menu
  menu = QMenu()

  action = QAction("Info")
  action.triggered.connect(w.show)
  w.show

  # Add a Quit option to the menu.
  quit = QAction("Quit")
  quit.triggered.connect(app.quit)

  menu.addAction(action)
  menu.addAction(quit)

  # Add the menu to the tray
  tray.setContextMenu(menu)

  app.exec()

  #input('Press enter to disable the phone')
  phone.stop()
