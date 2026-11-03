import http.client
import json
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import admin_service as manager


class ManagerTests(unittest.TestCase):
    def setUp(self):
        self.server=manager.ThreadingHTTPServer(('127.0.0.1',0),manager.Handler)
        self.port=patch.object(manager,'PORT',self.server.server_port)
        self.port.start()
        self.thread=threading.Thread(target=self.server.serve_forever,kwargs={'poll_interval':.02},daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join(2);self.port.stop()

    def post(self, action, headers):
        connection=http.client.HTTPConnection(*self.server.server_address,timeout=3)
        connection.request('POST','/action',body=json.dumps({'action':action}),headers=headers)
        response=connection.getresponse();body=json.loads(response.read());connection.close()
        return response.status,body

    def test_actions_need_same_origin_and_token(self):
        with patch.object(manager.control,'live',return_value=None),patch.object(manager.control,'start',return_value=0) as start:
            self.assertEqual(self.post('start',{})[0],403)
            self.assertEqual(self.post('start',{'X-MAG-Control-Action':manager.ACTION,'Origin':'https://foreign.invalid'})[0],403)
            start.assert_not_called()
            self.assertEqual(self.post('start',{'X-MAG-Control-Action':manager.ACTION})[0],200)
            start.assert_called_once()

    def test_catalog_update_prevents_stop_or_restart(self):
        with patch.object(manager.control,'live',return_value={'url':'http://fixture.invalid'}),patch.object(manager.control,'request',return_value={'running':True}),patch.object(manager.control,'stop') as stop:
            for action in ('stop','restart'):
                self.assertEqual(self.post(action,{'X-MAG-Control-Action':manager.ACTION})[0],409)
            stop.assert_not_called()


if __name__=='__main__':unittest.main()
