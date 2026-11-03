"""Install only Media Forge Lab on the explicitly selected private LAN TV."""
import argparse
import ipaddress
import json
import os
from pathlib import Path
import subprocess

BASE=Path(__file__).resolve().parent


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('target',choices=('samsung','android'));parser.add_argument('--ip');args=parser.parse_args()
    saved=BASE/'.runtime/tv-devices.json'
    devices=json.loads(saved.read_text(encoding='utf-8')) if saved.exists() else {}
    address=args.ip or devices.get(args.target)
    cfg=json.loads((BASE/'config.local.json').read_text(encoding='utf-8-sig'))
    if not address or ipaddress.ip_address(address) not in ipaddress.ip_network(cfg['allowed_network']):
        parser.error('Indique --ip com o endereÃ§o da TV na rede privada do portal.')
    if args.target=='samsung':
        sdk=Path(os.environ.get('TIZEN_STUDIO','C:/tizen-studio'))
        subprocess.run([str(sdk/'tools/sdb.exe'),'connect',address+':26101'],check=True)
        subprocess.run([str(sdk/'tools/ide/bin/tizen.bat'),'install','-n','MediaForgeLab-Samsung.wgt','-s',address+':26101','--',str(BASE/'.runtime/tv-build')],check=True)
    else:
        sdk=Path(os.environ['LOCALAPPDATA'])/'Android/Sdk'
        adb=str(sdk/'platform-tools/adb.exe')
        subprocess.run([adb,'connect',address+':5555'],check=True)
        subprocess.run([adb,'-s',address+':5555','install','--no-incremental','-r',str(BASE/'.runtime/tv-build/MediaForgeLab-AndroidTV.apk')],check=True)
    print('Media Forge Lab instalada. Abra-a na lista de aplicaÃ§Ãµes da TV.')
