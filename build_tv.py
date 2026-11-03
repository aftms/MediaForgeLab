"""Build private TV packages with installed SDKs. No provider credentials."""
import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import zipfile
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

BASE = Path(__file__).resolve().parent
BUILD = BASE / '.runtime' / 'tv-build'


def run(args, cwd=None):
    result = subprocess.run([str(a) for a in args], cwd=cwd, capture_output=True, text=True,
                            errors='replace', creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if result.returncode:
        # SDK diagnostics do not contain source credentials; private config is
        # never passed as a command argument or printed.
        raise RuntimeError(Path(args[0]).name+': '+(result.stderr or result.stdout)[-2500:])


def samsung(server, profile):
    root = BUILD / 'samsung'
    root.mkdir(parents=True, exist_ok=True)
    # Never nest the previous signed widget or stale signatures in a rebuild.
    for name in ('MagForgeLab.wgt', 'Media Forge Lab.wgt', 'MediaForgeLab.wgt', 'author-signature.xml', 'signature1.xml'):
        (root/name).unlink(missing_ok=True)
    keypath = BASE / '.runtime' / 'tv-access.json'
    if not keypath.exists():
        with keypath.open('x', encoding='utf-8') as f:
            json.dump({'key': secrets.token_hex(32)}, f)
    from tv_access import TVAccess
    access = TVAccess(keypath)
    for file in (BASE / 'public' / 'tv').iterdir():
        if file.is_file(): shutil.copyfile(file, root / file.name)
    (root/'config.js').write_text('window.MAG_TV_CONFIG='+json.dumps({'base':server,'key':access.key})+';',encoding='utf-8')
    html=(root/'index.html').read_text(encoding='utf-8').replace('<script src="config.js">','<script src="$WEBAPIS/webapis/webapis.js"></script><script src="config.js">')
    (root/'index.html').write_text(html,encoding='utf-8')
    personal=(root/'personal.html').read_text(encoding='utf-8').replace('<script src="config.js">','<script src="$WEBAPIS/webapis/webapis.js"></script><script src="config.js">')
    (root/'personal.html').write_text(personal,encoding='utf-8')
    collection=(root/'collections.html').read_text(encoding='utf-8').replace('<script src="config.js">','<script src="$WEBAPIS/webapis/webapis.js"></script><script src="config.js">')
    (root/'collections.html').write_text(collection,encoding='utf-8')
    xml=(BASE/'tv/samsung/config.xml').read_text(encoding='utf-8').replace('http://192.168.1.240:8090',server)
    (root/'config.xml').write_text(xml,encoding='utf-8')
    shutil.copyfile(BASE/'public/web/icon-512.png',root/'icon.png')
    tool=Path(os.environ.get('TIZEN_STUDIO','C:/tizen-studio'))/'tools/ide/bin/tizen.bat'
    # Profiles are managed by Tizen; never read/export certificate passwords.
    run([tool,'package','-t','wgt','-s',profile,'--',root])
    package=next(root.glob('*.wgt'))
    destination=BUILD/'MediaForgeLab-Samsung.wgt'
    shutil.copyfile(package,destination)
    print('Samsung:',destination)


def android(server, debug=False):
    from PIL import Image, ImageDraw, ImageFont
    root=BUILD/'android';root.mkdir(parents=True,exist_ok=True)
    sdk=Path(os.environ.get('ANDROID_HOME',str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk')))
    if not (sdk/'build-tools/35.0.1/aapt2.exe').is_file():
        sdk=Path(os.environ['LOCALAPPDATA'])/'Android/Sdk'
    java=Path(os.environ.get('JAVA_HOME','C:/Program Files/Android/Android Studio/jbr'))/'bin'
    tools=sdk/'build-tools/35.0.1';jar=sdk/'platforms/android-35/android.jar'
    for folder in ['res/drawable','res/xml','src','classes','dex']:(root/folder).mkdir(parents=True,exist_ok=True)
    shutil.copyfile(BASE/'tv/android/AndroidManifest.xml',root/'AndroidManifest.xml')
    shutil.copyfile(BASE/'public/web/icon-192.png',root/'res/drawable/icon.png')
    banner=Image.new('RGB',(320,180),'#142935');logo=Image.open(BASE/'public/web/icon-192.png').convert('RGBA');logo.thumbnail((104,104));banner.paste(logo,(108,12),logo)
    draw=ImageDraw.Draw(banner);font=ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf',25);draw.text((160,145),'Media Forge Lab',font=font,anchor='mm',fill='#c4f4e9');banner.save(root/'res/drawable/banner.png')
    network=ET.Element('network-security-config');ET.SubElement(network,'base-config',{'cleartextTrafficPermitted':'false'});domain=ET.SubElement(network,'domain-config',{'cleartextTrafficPermitted':'true'});ET.SubElement(domain,'domain',{'includeSubdomains':'false'}).text=urlsplit(server).hostname
    ET.ElementTree(network).write(root/'res/xml/network_security.xml',encoding='utf-8',xml_declaration=True)
    shutil.copyfile(BASE/'tv/android/MainActivity.java',root/'src/MainActivity.java')
    (root/'src/BuildConfig.java').write_text('package local.magforgelab.tv; final class BuildConfig {static final String SERVER='+json.dumps(server)+';static final boolean DEBUG='+('true' if debug else 'false')+';}',encoding='utf-8')
    run([tools/'aapt2.exe','compile','--dir',root/'res','-o',root/'resources.zip'])
    run([tools/'aapt2.exe','link','-I',jar,'--manifest',root/'AndroidManifest.xml','-o',root/'unsigned.apk',root/'resources.zip'])
    run([java/'javac.exe','--release','8','-encoding','UTF-8','-classpath',jar,'-d',root/'classes',root/'src/MainActivity.java',root/'src/BuildConfig.java'])
    # D8 launcher requires JAVA_HOME. The child gets only this explicit setting.
    previous=os.environ.get('JAVA_HOME');os.environ['JAVA_HOME']=str(java.parent)
    try:run([tools/'d8.bat','--lib',jar,'--min-api','26','--output',root/'dex',*sorted((root/'classes').rglob('*.class'))])
    finally:
        if previous is None:os.environ.pop('JAVA_HOME',None)
        else:os.environ['JAVA_HOME']=previous
    with zipfile.ZipFile(root/'unsigned.apk','a') as apk:
        for dex in (root/'dex').glob('*.dex'):apk.write(dex,dex.name)
    run([tools/'zipalign.exe','-f','4',root/'unsigned.apk',root/'aligned.apk'])
    key=BASE/'.runtime/tv-android-signing.p12';password=BASE/'.runtime/tv-android-signing.pass'
    if not key.exists():
        if not password.exists():password.write_text(secrets.token_urlsafe(32),encoding='utf-8')
        run([java/'keytool.exe','-genkeypair','-keystore',key,'-storetype','PKCS12','-storepass:file',password,'-alias','magforgelab','-dname','CN=MagForgeLab Local TV','-keyalg','RSA','-keysize','3072','-validity','3650'])
    destination=BUILD/'MediaForgeLab-AndroidTV.apk'
    previous=os.environ.get('JAVA_HOME');os.environ['JAVA_HOME']=str(java.parent)
    try:
        run([tools/'apksigner.bat','sign','--ks',key,'--ks-pass','file:'+str(password),'--out',destination,root/'aligned.apk'])
        run([tools/'apksigner.bat','verify',destination])
    finally:
        if previous is None:os.environ.pop('JAVA_HOME',None)
        else:os.environ['JAVA_HOME']=previous
    print('Android TV:',destination)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--target',choices=['samsung','android','all'],default='all');parser.add_argument('--profile',default='HealhForgeLabTV');parser.add_argument('--debug',action='store_true');args=parser.parse_args()
    config=json.loads((BASE/'config.local.json').read_text(encoding='utf-8-sig'))
    server='http://%s:%s'%(config['host'],config['port'])
    BUILD.mkdir(parents=True,exist_ok=True)
    if args.target in ('samsung','all'):samsung(server,args.profile)
    if args.target in ('android','all'):android(server,args.debug)
