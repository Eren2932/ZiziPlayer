import importlib.util, unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('preflight',str(Path(__file__).with_name('check_desktop_connection.py')))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class PreflightTests(unittest.TestCase):
 def values(self,url,allow='false',token='fixture'):
  return dict(RESOLVER_URL=url,RESOLVER_TOKEN=token,DESKTOP_ALLOW_HTTP=allow)
 def test_https(self): self.assertIsNone(m.check(self.values('https://example.org')))
 def test_schemeless_optin(self): self.assertIsNone(m.check(self.values('example.org:8080','true')))
 def test_schemeless_default_closed(self): self.assertIsNotNone(m.check(self.values('example.org:8080')))
 def test_http_optin(self): self.assertIsNone(m.check(self.values('http://example.org:8080','true')))
 def test_loopback(self): self.assertIsNone(m.check(self.values('http://127.0.0.1:8080')))
 def test_missing_secret(self): self.assertIsNotNone(m.check(self.values('https://example.org',token='')))
 def test_bad_urls(self):
  for url in ['file:///a','https://user:pass@example.org','https://example.org?x=y','https://example.org#x','https://example.org:99999','https://example.org:0','https://example.org\nfoo']:
   with self.subTest(url=url): self.assertIsNotNone(m.check(self.values(url)))
 def test_header_injection(self): self.assertIsNotNone(m.check(self.values('https://example.org',token='fixture\r\ninjected')))
 def test_no_value_disclosure(self):
  text=m.check(self.values('https://private-fixture.invalid:99999',token='sensitive-fixture'))
  self.assertNotIn('private-fixture',text);self.assertNotIn('sensitive-fixture',text)
if __name__=='__main__': unittest.main()
