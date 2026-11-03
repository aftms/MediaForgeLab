"""Create a private local CA and IP certificate; never publish private keys."""
from datetime import datetime, timedelta, timezone
import ipaddress
import json
from pathlib import Path
import shutil
import sys

BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE/'.runtime'/'python-deps'))
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID


def main():
    config_path=BASE/'config.local.json'
    config=json.loads(config_path.read_text(encoding='utf-8-sig'))
    folder=BASE/'.runtime'/'tls'
    folder.mkdir(parents=True,exist_ok=True)
    now=datetime.now(timezone.utc)
    if not (folder/'ca-key.pem').exists():
        key=rsa.generate_private_key(public_exponent=65537,key_size=3072)
        name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'MagForgeLab Local Home CA')])
        cert=(x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
              .serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(days=1)).not_valid_after(now+timedelta(days=3650))
              .add_extension(x509.BasicConstraints(ca=True,path_length=0),critical=True)
              .add_extension(x509.KeyUsage(False,False,False,False,False,True,True,False,False),critical=True)
              .sign(key,hashes.SHA256()))
        (folder/'ca-key.pem').write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
        (folder/'ca.pem').write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        (folder/'ca.cer').write_bytes(cert.public_bytes(serialization.Encoding.DER))
    else:
        key=serialization.load_pem_private_key((folder/'ca-key.pem').read_bytes(),password=None)
        cert=x509.load_pem_x509_certificate((folder/'ca.pem').read_bytes())
    leaf=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'MagForgeLab')])
    leaf_cert=(x509.CertificateBuilder().subject_name(name).issuer_name(cert.subject).public_key(leaf.public_key())
        .serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(days=1)).not_valid_after(now+timedelta(days=365))
        .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address(config['host'])),x509.IPAddress(ipaddress.ip_address('127.0.0.1')),x509.DNSName('localhost')]),critical=False)
        .add_extension(x509.BasicConstraints(ca=False,path_length=None),critical=True)
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),critical=False).sign(key,hashes.SHA256()))
    (folder/'server-key.pem').write_bytes(leaf.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
    (folder/'server.pem').write_bytes(leaf_cert.public_bytes(serialization.Encoding.PEM))
    config.update(loopback_port=8091,https_port=8443,tls_cert=str(folder/'server.pem'),tls_key=str(folder/'server-key.pem'),tls_ca=str(folder/'ca.cer'),ffmpeg=shutil.which('ffmpeg') or config.get('ffmpeg'),ffprobe=shutil.which('ffprobe') or config.get('ffprobe'))
    config_path.write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
    print('HTTPS configured. Public root certificate:',folder/'ca.cer')
    print('Leaf certificate expires:',leaf_cert.not_valid_after_utc.isoformat())


if __name__=='__main__':
    main()
