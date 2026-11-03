package local.magforgelab.tv;

import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.net.Uri;
import android.view.KeyEvent;
import android.view.View;
import android.view.WindowManager;
import android.webkit.*;
import android.widget.FrameLayout;
import android.widget.VideoView;

/** Only the configured LAN portal can load; the bridge exposes no filesystem. */
public final class MainActivity extends Activity {
 private WebView web;
 private VideoView player;
 private volatile int position;
 private int generation;
 private volatile String phase="idle";
 private volatile long openedAt, preparedMs, frameMs;
 private final android.os.Handler handler = new android.os.Handler(android.os.Looper.getMainLooper());
 private final Runnable tick = new Runnable() { public void run() {
   if (player != null) position = player.getCurrentPosition();
   handler.postDelayed(this, 500);
 }};
 private boolean allowed(Uri uri) {
   Uri base = Uri.parse(BuildConfig.SERVER);
   return base.getScheme().equals(uri.getScheme()) && base.getHost().equals(uri.getHost())
       && base.getPort()==uri.getPort() && uri.getUserInfo()==null;
 }
 private void js(String code) { if(web!=null) web.evaluateJavascript("window.MagTV && "+code,null); }
 @Override public void onCreate(Bundle saved) {
   super.onCreate(saved);
   getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,WindowManager.LayoutParams.FLAG_FULLSCREEN);
   FrameLayout layout = new FrameLayout(this);
   player = new VideoView(this);
   FrameLayout.LayoutParams videoParams = new FrameLayout.LayoutParams(-1,-1,android.view.Gravity.CENTER);
   layout.addView(player,videoParams); player.setVisibility(View.GONE);
   web = new WebView(this); web.setBackgroundColor(Color.TRANSPARENT);
   WebView.setWebContentsDebuggingEnabled(BuildConfig.DEBUG);
   WebSettings settings=web.getSettings();settings.setJavaScriptEnabled(true);settings.setDomStorageEnabled(true);
   settings.setAllowFileAccess(false);settings.setAllowContentAccess(false);settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
   settings.setCacheMode(WebSettings.LOAD_NO_CACHE);settings.setMediaPlaybackRequiresUserGesture(true);
   settings.setUseWideViewPort(true);settings.setLoadWithOverviewMode(true);
   web.setWebViewClient(new WebViewClient(){
    @Override public boolean shouldOverrideUrlLoading(WebView view,WebResourceRequest req){return !allowed(req.getUrl()) || !req.getUrl().getPath().startsWith("/tv/");}
    @Override public WebResourceResponse shouldInterceptRequest(WebView view,WebResourceRequest req){
     if(!allowed(req.getUrl())) return new WebResourceResponse("text/plain","UTF-8",403,"Forbidden",null,new java.io.ByteArrayInputStream(new byte[0]));
     return null;
    }
   });
   web.addJavascriptInterface(new Bridge(),"MagPlayer");
   layout.addView(web,new FrameLayout.LayoutParams(-1,-1));setContentView(layout);
   web.loadUrl(BuildConfig.SERVER+"/tv/");web.requestFocus();handler.post(tick);
 }
 private void stopPlayer(){phase="idle";++generation;player.stopPlayback();player.setVisibility(View.GONE);position=0;getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);}
 private final class Bridge {
   @JavascriptInterface public void play(final String url){
    Uri uri=Uri.parse(url);
    phase="requested";
    if(!allowed(uri)||!uri.getPath().matches("/(?:media|personal)/hls/[a-f0-9]{48}/index\\.m3u8")||uri.getQuery()!=null||uri.getFragment()!=null){phase="rejected";runOnUiThread(()->js("MagTV.error()"));return;}
    runOnUiThread(()->{stopPlayer();final int stamp=generation;phase="preparing";getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);openedAt=android.os.SystemClock.elapsedRealtime();preparedMs=0;frameMs=0;player.setVisibility(View.VISIBLE);
     player.setOnPreparedListener(mp->{if(stamp==generation){phase="prepared";preparedMs=android.os.SystemClock.elapsedRealtime()-openedAt;getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);player.start();}});
     player.setOnInfoListener((mp,what,extra)->{if(stamp==generation&&what==android.media.MediaPlayer.MEDIA_INFO_VIDEO_RENDERING_START){phase="playing";frameMs=android.os.SystemClock.elapsedRealtime()-openedAt;}return false;});
     player.setOnErrorListener((mp,what,extra)->{if(stamp==generation){stopPlayer();phase="error";js("MagTV.error()");}return true;});
     player.setOnCompletionListener(mp->{if(stamp==generation)js("MagTV.ended()");});
     player.setVideoURI(uri);web.requestFocus();
    });
   }
   @JavascriptInterface public void stop(){runOnUiThread(()->stopPlayer());}
   @JavascriptInterface public double position(){return position/1000.0;}
   @JavascriptInterface public String status(){return phase+":"+preparedMs+":"+frameMs;}
   @JavascriptInterface public void exit(){runOnUiThread(()->finish());}
   @JavascriptInterface public void keyboard(){runOnUiThread(()->{
    web.requestFocus();((android.view.inputmethod.InputMethodManager)getSystemService(INPUT_METHOD_SERVICE)).showSoftInput(web,android.view.inputmethod.InputMethodManager.SHOW_IMPLICIT);
   });}
 }
 @Override public boolean dispatchKeyEvent(KeyEvent e){
   int code=e.getKeyCode();
   if(code==KeyEvent.KEYCODE_BACK){if(e.getAction()==KeyEvent.ACTION_UP)js("MagTV.back()");return true;}
   int direction=code==KeyEvent.KEYCODE_DPAD_LEFT?37:code==KeyEvent.KEYCODE_DPAD_UP?38:code==KeyEvent.KEYCODE_DPAD_RIGHT?39:code==KeyEvent.KEYCODE_DPAD_DOWN?40:code==KeyEvent.KEYCODE_DPAD_CENTER||code==KeyEvent.KEYCODE_ENTER?13:0;
   if(direction!=0){if(e.getAction()==KeyEvent.ACTION_DOWN&&(direction!=13||e.getRepeatCount()==0))js("MagTV.remote("+direction+")");return true;}
   int mapped=code==KeyEvent.KEYCODE_MEDIA_PLAY?415:code==KeyEvent.KEYCODE_MEDIA_PAUSE?19:code==KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE?10252:code==KeyEvent.KEYCODE_MEDIA_STOP?413:code==KeyEvent.KEYCODE_MEDIA_FAST_FORWARD?417:code==KeyEvent.KEYCODE_MEDIA_REWIND?412:code==KeyEvent.KEYCODE_CHANNEL_UP?427:code==KeyEvent.KEYCODE_CHANNEL_DOWN?428:0;
   if(mapped!=0){if(e.getAction()==KeyEvent.ACTION_DOWN&&e.getRepeatCount()==0)web.evaluateJavascript("document.dispatchEvent(new KeyboardEvent('keydown',{keyCode:"+mapped+",bubbles:true}))",null);return true;}
   return super.dispatchKeyEvent(e);
 }
 @Override protected void onPause(){js("MagTV.suspend()");stopPlayer();super.onPause();}
 @Override protected void onDestroy(){handler.removeCallbacks(tick);stopPlayer();web.removeJavascriptInterface("MagPlayer");web.destroy();super.onDestroy();}
}
