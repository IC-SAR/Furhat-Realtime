from nt import environ
import os

def enable_web_server():
  os.environ['WEB_ENABLED'] = 0

def disable_web_server():
  os.environ['WEB_ENABLED'] = 1

def bind_ip_to_all_io(): 
  os.environ['WEB_HOST'] = '0.0.0.0'

def set_port_num(port_num: int = 7860):
  os.environ['WEB_PORT'] = port_num
