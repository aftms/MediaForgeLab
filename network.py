"""Install one narrow Private-profile firewall rule; Windows UAC owns consent."""
import argparse
import base64
import ctypes
import json
from pathlib import Path
import subprocess
import sys
import time

from server import BASE, load_config

RESULT = BASE / '.runtime' / 'firewall-result.json'


def firewall_script(config):
    # All interpolated values were parsed as IPv4, bounded port and IPv4Network.
    return """$ErrorActionPreference = 'Stop'
$name = 'GatewayForgeLab-MAG-Portal-Local'
$rule = Get-NetFirewallRule -Name $name -ErrorAction SilentlyContinue
if ($rule) {
    $rule | Set-NetFirewallRule -Enabled True -Direction Inbound -Action Allow -Profile Private -EdgeTraversalPolicy Block
    $rule | Get-NetFirewallPortFilter | Set-NetFirewallPortFilter -Protocol TCP -LocalPort PORT
    $rule | Get-NetFirewallAddressFilter | Set-NetFirewallAddressFilter -LocalAddress 'HOST' -RemoteAddress 'NETWORK'
} else {
    New-NetFirewallRule -Name $name -DisplayName 'MAG Portal - apenas rede local' -Direction Inbound -Action Allow -Enabled True -Profile Private -Protocol TCP -LocalPort PORT -LocalAddress 'HOST' -RemoteAddress 'NETWORK' -EdgeTraversalPolicy Block | Out-Null
}
""".replace('PORT', str(config['port'])).replace('HOST', config['host']).replace('NETWORK', str(config['network']))


def apply():
    config = load_config(BASE / 'config.local.json')
    encoded = base64.b64encode(firewall_script(config).encode('utf-16-le')).decode('ascii')
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-EncodedCommand', encoded],
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    RESULT.parent.mkdir(exist_ok=True)
    RESULT.write_text(json.dumps({'ok': result.returncode == 0, 'admin': bool(ctypes.windll.shell32.IsUserAnAdmin()),
                                  'error': result.stderr.decode('utf-8', errors='replace')[:6000] if result.returncode else None, 'port': config['port'],
                                  'host': config['host'], 'network': str(config['network'])}), encoding='utf-8')
    return result.returncode


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if sys.platform != 'win32':
        print('Este auxiliar e para a firewall do Windows.')
        return 1
    if args.apply or ctypes.windll.shell32.IsUserAnAdmin():
        return apply()
    if RESULT.exists():
        RESULT.unlink()
    print('Aguarde a confirmacao de Administrador do Windows (UAC).', flush=True)
    status = ctypes.windll.shell32.ShellExecuteW(None, 'runas', sys.executable,
               subprocess.list2cmdline([str(Path(__file__).resolve()), '--apply']), str(BASE), 0)
    if status <= 32:
        print('Elevacao nao autorizada. A regra nao foi aplicada.')
        return 1
    for _ in range(120):
        if RESULT.exists():
            result = json.loads(RESULT.read_text(encoding='utf-8'))
            print('Regra local aplicada.' if result['ok'] else 'Nao foi possivel aplicar a regra.')
            return 0 if result['ok'] else 1
        time.sleep(.5)
    print('Ainda sem confirmacao. Consulte .runtime/firewall-result.json.')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
