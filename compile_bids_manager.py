import os
import shutil

megserv_dir = r'\\megserv\Apps\Plugins_Windows\Bids_Pipeline'
audeserv = r'\\dynaserv\home\jegou\Softwares\Bids_pipeline'
# rhu_tools_dir = r'\\megserv\Apps\RHU_tools\Bids_Manager'
#dynamap_serv = r'\\139.124.150.47\dynamap\users\Jegou\Bids_pipeline_exe'

cmd_line = 'pyinstaller --onefile --icon=bids_manager\\bids_manager.ico --hidden-import PyQt5.sip bids_manager\\bids_manager.py'
os.system(cmd_line)
print('conversion is done')
# copy to bids manager in plugin_windows --hidden-import "PyQt5.sip, PyQt5.QtQuick, PyQt5.QtQml"
shutil.copy2(os.path.join('.', 'dist', 'bids_manager.exe'), os.path.join(audeserv, 'bids_manager.exe'))
# shutil.rmtree(os.path.join(megserv_dir, 'requirements_templates'))
# shutil.copytree(os.path.join('.', 'requirements_templates'), os.path.join(megserv_dir, 'requirements_templates'))
# # # copy to bids manager in Rhu_tools
shutil.copy2(os.path.join('.', 'dist', 'bids_manager.exe'), os.path.join(megserv_dir, 'bids_manager.exe'))
# shutil.rmtree(os.path.join(rhu_tools_dir, 'requirements_templates'))
# shutil.copytree(os.path.join('.', 'requirements_templates'), os.path.join(rhu_tools_dir, 'requirements_templates'))
print('copy is done')

