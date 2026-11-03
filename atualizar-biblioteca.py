"""Request the portal's transactional background refresh; never restart playback."""
import json
import time
import urllib.request
from server import BASE, load_config

if __name__ == '__main__':
    try:
        cfg = load_config(BASE / 'config.local.json')
        origin = 'http://%s:%s' % (cfg['host'],cfg['port'])
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        def request(path, body=None, token=''):
            headers = {'Content-Type':'application/json','X-MAG-Action':token}
            req = urllib.request.Request(origin+path,data=json.dumps(body).encode() if body is not None else None,headers=headers)
            with opener.open(req,timeout=20) as response:
                return json.load(response)
        token = request('/api/library')['action_token']
        status = request('/api/refresh',{},token)
        previous = None
        while status.get('running'):
            if status.get('stage') != previous:
                previous = status.get('stage')
                print(previous,flush=True)
            time.sleep(2)
            status = request('/api/refresh')
        if status.get('error'):
            print(status['error'],flush=True)
            raise SystemExit(1)
        added = status.get('summary',{}).get('added',{})
        print('%s canais, %s filmes e %s series adicionados.' % (added.get('tv',0),added.get('movie',0),added.get('series',0)),flush=True)
        print('Catalogo aplicado sem reiniciar o portal.',flush=True)
    except Exception:
        print('Atualizacao indisponivel. Inicie o portal e tente novamente.',flush=True)
        raise SystemExit(1)
