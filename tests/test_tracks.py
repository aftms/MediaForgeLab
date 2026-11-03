import json,sys,tempfile,time,unittest,subprocess,shutil,array
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from media import subtitle_cues,MediaError,process_options
from personal_fixture import Fixture

class CaptionTests(unittest.TestCase):
 def test_bounded_complete_plain_text_cues(self):
  with tempfile.TemporaryDirectory() as root:
   path=Path(root)/'captions.vtt'
   path.write_text('WEBVTT\n\n00:00:01.000 --> 00:00:03.000\n<b>Teste</b> &amp; seguro\n\n00:00:04.000 --> 00:00:05.000\nincompleto',encoding='utf-8')
   self.assertEqual(subtitle_cues(path),[dict(start=1,end=3,text='Teste & seguro')])
   path.write_text('WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nÚltima legenda\n',encoding='utf-8')
   self.assertEqual(subtitle_cues(path)[0]['text'],'Última legenda')
   path.write_text('x'*300000+'\n\n00:00:06.000 --> 00:00:09.000\nFim\n\n',encoding='utf-8')
   self.assertEqual(subtitle_cues(path)[0]['text'],'Fim')
   self.assertEqual(subtitle_cues(path.with_name('missing')),[])

@unittest.skipUnless(shutil.which('ffmpeg'),'FFmpeg required')
class TrackPipelineTests(unittest.TestCase):
 def test_languages_audio_selection_seek_off_and_single_lease(self):
  fixture=Fixture(tracks=True);m=fixture.app.media
  try:
   def start(audio,subtitle,position):
    data=m.start(dict(id='fixture-vod',owner='fixture-track-owner',audio=audio,subtitle=subtitle,position=position),'127.0.0.1','web')
    deadline=time.monotonic()+40
    while time.monotonic()<deadline:
     data=m.pulse(data,'127.0.0.1')
     if data['state']=='ready' and (subtitle<0 or data.get('cues')):return data
     time.sleep(.15)
    self.fail('Pipeline did not prepare captions: '+str({k:data.get(k) for k in ('state','cues','audio_index','subtitle_index')})+' file='+repr((m.root/data['token']/'captions.vtt').read_text(encoding='utf-8') if (m.root/data['token']/'captions.vtt').exists() else 'missing')+' process='+str(m.session['process'].poll()))
   first=start(0,0,0)
   self.assertEqual(len(first['audio']),2);self.assertEqual(len(first['subtitles']),2)
   self.assertEqual(first['video_mode'],'remux');self.assertEqual(first['subtitles'][0]['language'],'por')
   self.assertTrue(any('portuguesa' in c['text'] for c in first['cues']))
   self.assertEqual(m.session['process'].args.count('-i'),1)
   with self.assertRaises(MediaError):m.start(dict(id='fixture-vod',owner='another-device-1'),'127.0.0.2','web')
   for invalid_audio in (-1,101,'bad'):
    with self.assertRaises(MediaError):m.start(dict(id='fixture-vod',owner='fixture-track-owner',audio=invalid_audio),'127.0.0.1','web')
    self.assertEqual(m.session['token'],first['token'])
   for invalid in (-2,101,'bad'):
    with self.assertRaises(MediaError):m.start(dict(id='fixture-vod',owner='fixture-track-owner',subtitle=invalid),'127.0.0.1','web')
    self.assertEqual(m.session['token'],first['token'])
   second=start('auto',1,10)
   self.assertEqual(second['position'],10);self.assertEqual(second['audio_index'],1)
   self.assertTrue(any('English' in c['text'] and 1<=c['start']<=3 for c in second['cues']),second['cues'])
   self.assertFalse((m.root/first['token']).exists())
   segment=next((m.root/second['token']).glob('s*.ts'))
   pcm=subprocess.run([shutil.which('ffmpeg'),'-v','quiet','-i',str(segment),'-vn','-t','1','-ac','1','-ar','16000','-f','s16le','pipe:1'],stdout=subprocess.PIPE,check=True,timeout=10,**process_options()).stdout
   samples=array.array('h',pcm);crossings=sum(a<=0<b for a,b in zip(samples,samples[1:]));frequency=crossings/(len(samples)/16000)
   self.assertTrue(800<frequency<960,frequency)
   off=start(0,-1,0);self.assertEqual(off['audio_index'],0);self.assertNotIn('cues',off);self.assertFalse((m.root/off['token']/'captions.vtt').exists())
   m.release(off,'127.0.0.1');self.assertFalse(m.status()['active'])
  finally:fixture.close()

if __name__=='__main__':unittest.main()
