const assert = require('assert/strict'), fs = require('fs'), vm = require('vm');
const source = fs.readFileSync(require('path').join(__dirname, '../public/tv/tv.js'), 'utf8');
const api = source.slice(source.indexOf('function api('), source.indexOf('function query('));
for (const finalStatus of [200, 403]) {
  const calls = [], responses = [
    [403, {error: 'Pedido recusado.'}],
    [200, {action_token: 'new-action'}],
    [finalStatus, finalStatus === 200 ? {favorite: true} : {error: 'Pedido recusado.'}]
  ];
  let result;
  function XHR() { this.headers = {}; }
  XHR.prototype.open = function(method, url) { this.method = method; this.url = url; };
  XHR.prototype.setRequestHeader = function(k, v) { this.headers[k] = v; };
  XHR.prototype.send = function(body) {
    assert.ok(responses.length, 'Must not loop on repeated rejection');
    calls.push({method: this.method, url: this.url, headers: this.headers, body});
    const [status, data] = responses.shift(); this.status = status;
    this.responseText = JSON.stringify(data); this.onload();
  };
  const context = {XMLHttpRequest: XHR, cfg: {key: 'local-test-key'},
    base: 'http://127.0.0.1:8090', action: 'old-action'};
  vm.createContext(context); vm.runInContext(api, context);
  context.api('/api/favorite', {id: 'tv:1', favorite: true}, (error, data) => { result = {error, data}; });
  assert.equal(calls.length, 3);
  assert.equal(calls[1].method, 'GET');
  assert.equal(calls[1].url, context.base + '/api/library');
  assert.equal(calls[0].headers['X-MAG-Action'], 'old-action');
  assert.equal(calls[2].headers['X-MAG-Action'], 'new-action');
  assert.equal(calls[0].body, calls[2].body);
  assert.equal(calls[2].headers['X-MAG-TV'], 'local-test-key');
  assert.equal(result.error, finalStatus === 200 ? null : 'Pedido recusado.');
}
console.log('PASS: stale TV action token refreshes and retries the same operation once; repeated 403 stops.');
