package com.voiceforge.app

import android.Manifest
import android.content.pm.PackageManager
import android.media.*
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.*
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.UUID
import kotlin.concurrent.thread

class MainActivity:ComponentActivity() {
 private var recorder:AudioRecord?=null
 private var active=false
 private var worker:Thread?=null
 private val status=mutableStateOf("سجّل عينة صوتك أولاً")
 private lateinit var sample:File
 private var audioPlayer:MediaPlayer?=null
 private val permission=registerForActivityResult(ActivityResultContracts.RequestPermission()) {if(it) startRecord() else status.value="الميكروفون يحتاج إذناً"}
 private fun startRecord(){
  if(active)return
  val rate=24000
  val size=maxOf(4096,AudioRecord.getMinBufferSize(rate,AudioFormat.CHANNEL_IN_MONO,AudioFormat.ENCODING_PCM_16BIT))
  if(size<=0)return
  val r=AudioRecord(MediaRecorder.AudioSource.MIC,rate,AudioFormat.CHANNEL_IN_MONO,AudioFormat.ENCODING_PCM_16BIT,size*2)
  if(r.state!=AudioRecord.STATE_INITIALIZED){r.release();return}
  sample=File(cacheDir,"voice.wav"); recorder=r;active=true;r.startRecording();status.value="جاري التسجيل"
  worker=thread {
   val output=java.io.ByteArrayOutputStream()
   val buf=ByteArray(size)
   while(active){
    val n=try{r.read(buf,0,buf.size)}catch(_:Exception){-1}
    if(n<0)break
    if(n>0 && output.size()<24000*2*60)output.write(buf,0,n)
   }
   val pcm=output.toByteArray()
   val header=ByteBuffer.allocate(44).order(ByteOrder.LITTLE_ENDIAN)
   header.put("RIFF".toByteArray());header.putInt(pcm.size+36);header.put("WAVEfmt ".toByteArray())
   header.putInt(16);header.putShort(1.toShort());header.putShort(1.toShort());header.putInt(rate);header.putInt(rate*2)
   header.putShort(2.toShort());header.putShort(16.toShort());header.put("data".toByteArray());header.putInt(pcm.size)
   sample.outputStream().use{it.write(header.array());it.write(pcm)}
   runOnUiThread{status.value="تم حفظ عينة من ${pcm.size/48000} ثانية"}
  }
 }
 private fun stopRecord(){if(!active)return;active=false;try{recorder?.stop()}catch(_:Exception){};worker?.join(1000);recorder?.release();recorder=null}
 override fun onDestroy(){stopRecord();audioPlayer?.release();super.onDestroy()}
 override fun onCreate(savedInstanceState:Bundle?){super.onCreate(savedInstanceState)
  setContent {
   var endpoint by remember{mutableStateOf(getPreferences(0).getString("api","")?:"")}
   var phrase by remember{mutableStateOf("مرحباً، أنا جارڤيس، وهذا كلام جديد بصوتي!")}
   var promptIndex by remember{mutableIntStateOf(0)}
   var lang by remember{mutableStateOf("ar")}
   var mood by remember{mutableStateOf(.5f)}
   var busy by remember{mutableStateOf(false)}
   var result by remember{mutableStateOf<File?>(null)}
   val prompts=listOf("مرحباً، أنا أسجل صوتي لكي أستعمله في إنشاء كلام جديد بطريقة طبيعية.",
      "اليوم يوم جميل، وفيه الكثير من الأفكار الجديدة التي تستحق أن نكتشفها.",
      "تحدث بصوت واضح وهادئ، وتوقف قليلاً بين الجمل حتى نسمع كل كلمة.")
   val scope= rememberCoroutineScope()
   MaterialTheme(colorScheme=darkColorScheme(primary=Color(0xFF5BE1DF))){
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp),verticalArrangement=Arrangement.spacedBy(13.dp)){
     Text("VOICEFORGE",style=MaterialTheme.typography.headlineLarge)
     Text("توليد الصوت بواسطة عينتك المسجلة")
     OutlinedTextField(value=endpoint,onValueChange={endpoint=it;getPreferences(0).edit().putString("api",it).apply()},label={Text("رابط خادم الصوت")},modifier=Modifier.fillMaxWidth())
     Text("اقرأ النص التالي وسجّل 10–30 ثانية")
     Text(prompts[promptIndex],style=MaterialTheme.typography.titleMedium)
     OutlinedButton(onClick={promptIndex=(promptIndex+1)%prompts.size}){Text("نص آخر")}
     Button(onClick={if(active)stopRecord() else if(checkSelfPermission(Manifest.permission.RECORD_AUDIO)==PackageManager.PERMISSION_GRANTED)startRecord() else permission.launch(Manifest.permission.RECORD_AUDIO)}){Text(if(active)"إيقاف التسجيل" else "سجّل صوتي")}
     Text(status.value)
     HorizontalDivider()
     OutlinedTextField(value=phrase,onValueChange={phrase=it},label={Text("ماذا تريد أن يقول صوتك؟")},modifier=Modifier.fillMaxWidth(),minLines=3)
     Row{listOf("ar","en","fr").forEach { x -> FilterChip(selected=lang==x,onClick={lang=x},label={Text(x)});Spacer(Modifier.width(6.dp))}}
     Text("مستوى التعبير: ${(mood*100).toInt()}%")
     Slider(value=mood,onValueChange={mood=it},valueRange=.2f.. .9f)
     Button(enabled=!busy && !active && phrase.isNotBlank(),onClick={
      if(!endpoint.startsWith("https://")){status.value="أدخل رابط خدمة صوت آمنة HTTPS أولاً"}
      else if(!::sample.isInitialized || !sample.exists()){status.value="سجّل العينة أولاً"}
      else{busy=true;status.value="جاري التوليد";scope.launch{
       try {val bytes=withContext(Dispatchers.IO){send(endpoint.trimEnd('/'),phrase,lang,mood,sample)}
        val target=File(getExternalFilesDir(null),"voice-${UUID.randomUUID()}.wav");target.writeBytes(bytes)
        result=target;status.value="تم إنشاء ملف WAV"
       }catch(e:Exception){status.value="خطأ: ${e.message}"}finally{busy=false}
      }}
     }){Text(if(busy)"جاري التوليد..." else "توليد بصوتي")}
     if(result!=null) Button(onClick={audioPlayer?.release();audioPlayer=MediaPlayer().apply{setDataSource(result!!.absolutePath);prepare();start()}}){Text("▶ تشغيل الصوت")}
     Text("استعمل صوتك أو صوتاً حصلت على موافقة واضحة لاستنساخه.",style=MaterialTheme.typography.bodySmall)
    }
   }
  }
 }
 private fun send(base:String,text:String,language:String,mood:Float,file:File):ByteArray{
  val boundary="VF${UUID.randomUUID()}"
  val c=URL("$base/synthesize").openConnection() as HttpURLConnection
  c.requestMethod="POST";c.doOutput=true;c.connectTimeout=15000;c.readTimeout=300000
  c.setRequestProperty("Content-Type","multipart/form-data; boundary=$boundary")
  c.outputStream.use {o->
   fun field(name:String,value:String){o.write("--$boundary\r\nContent-Disposition: form-data; name=\"$name\"\r\n\r\n$value\r\n".toByteArray())}
   field("text",text);field("language",language);field("exaggeration",mood.toString())
   o.write("--$boundary\r\nContent-Disposition: form-data; name=\"audio\"; filename=\"voice.wav\"\r\nContent-Type: audio/wav\r\n\r\n".toByteArray())
   file.inputStream().use{it.copyTo(o)}
   o.write("\r\n--$boundary--\r\n".toByteArray())
  }
  if(c.responseCode !in 200..299)throw Exception("HTTP ${c.responseCode}: ${c.errorStream?.bufferedReader()?.readText()?.take(120)}")
  return c.inputStream.use{it.readBytes()}
 }
}