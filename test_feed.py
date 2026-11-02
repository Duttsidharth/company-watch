import unittest
import fetch_updates as f
class FeedTests(unittest.TestCase):
 def test_no_private_config(self):
  with self.assertRaises(ValueError):f.validate_watchlist({'companies':[{'symbol':'ABC','name':'Test','quantity':1}]})
 def test_unsafe_links(self):
  self.assertEqual(f.safe_url('javascript:alert(1)'),'')
  self.assertEqual(f.safe_url('https://user:pass@example.com'),'')
 def test_failure_retains_actual_success_date(self):
  old={'lastSuccessAt':'2026-10-30','items':[{'title':'Prior','link':'https://example.com','date':'2026-10-30'}]}
  def fail():raise TimeoutError()
  x=f.fetch_section(fail,old,'news','2026-11-02')
  self.assertEqual(x['status'],'stale');self.assertEqual(x['lastSuccessAt'],'2026-10-30');self.assertEqual(x['items'][0]['title'],'Prior')
 def test_empty_success_is_not_failure(self):
  x=f.fetch_section(lambda:[],None,'news','2026-11-02');self.assertEqual(x['status'],'ok');self.assertEqual(x['items'],[])
 def test_dedup(self):
  a={'title':'News','link':'https://example.com'};self.assertEqual(len(f.clean_items([a,a],'news')),1)
 def test_nse_bad_payload_is_failure(self):
  orig=f.get_json;f.get_json=lambda url:{'error':'blocked'}
  try:
   x=f.fetch_section(lambda:f.nse_announcements('ABC'),None,'announcements','2026-11-02');self.assertEqual(x['status'],'unavailable')
  finally:f.get_json=orig
if __name__=='__main__':unittest.main()
