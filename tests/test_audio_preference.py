import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from media import preferred_audio

class AudioPreferenceTests(unittest.TestCase):
 def test_shared_language_cases(self):
  for tracks,expected in json.loads(Path(__file__).with_name('audio-preference-cases.json').read_text(encoding='utf-8')):
   with self.subTest(tracks=tracks):self.assertEqual(preferred_audio(tracks,None),expected)
 def test_original_fallback(self):
  self.assertEqual(preferred_audio([dict(language='spa'),dict(language='fra')],1),1)

if __name__=='__main__':unittest.main()
