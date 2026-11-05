package dz.oummalak.manager;

import android.app.*;
import android.os.*;
import android.content.*;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.view.*;
import android.widget.*;
import org.json.*;
import java.net.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;

public class MainActivity extends Activity {
  private static final int WINE=Color.rgb(55,15,35), GOLD=Color.rgb(202,159,99), IVORY=Color.rgb(250,245,238);
  private static final String BASE="https://rlgbbkyrpkrfavpvivvg.supabase.co";
  private final ExecutorService pool=Executors.newSingleThreadExecutor();
  private LinearLayout page, root;
  private String pubKey="", access="", refresh="", selectedId="";
  private Uri selectedPhoto;
  private EditText emailField, otpField, titleField, categoryField, priceField, descriptionField, heroField, subtitleField, aboutField, contactTextField, contactUrlField;
  private JSONArray products=new JSONArray(), socials=new JSONArray();
  private JSONObject site=new JSONObject();
  private boolean authenticated=false;
  private String section="products";
  private android.content.SharedPreferences prefs;
  private interface Work { void run() throws Exception; }

  @Override public void onCreate(Bundle b){
    super.onCreate(b);
    getWindow().setStatusBarColor(WINE);
    getWindow().setNavigationBarColor(WINE);
    prefs=getSharedPreferences("manager",MODE_PRIVATE);
    pubKey=prefs.getString("public_key",BuildConfig.SUPABASE_KEY);
    access=prefs.getString("access","");refresh=prefs.getString("refresh","");
    if(pubKey.isEmpty()) setupKey(); else if(access.isEmpty()) loginPage(); else verifyAdmin();
  }
  private void work(Work w){pool.execute(()->{try{w.run();}catch(Exception e){runOnUiThread(()->error(e.getMessage()));}});}
  private void ui(Runnable r){runOnUiThread(r);}
  private void error(String e){new AlertDialog.Builder(this).setTitle("تعذر إتمام العملية").setMessage(e==null?"تحقق من الاتصال والصلاحيات":e).setPositiveButton("حسنًا",null).show();}
  private int dp(float x){return (int)(getResources().getDisplayMetrics().density*x);}
  private TextView text(String v,int size,int color,boolean bold){
    TextView t=new TextView(this);t.setText(v);t.setTextSize(size);t.setTextColor(color);
    if(bold)t.setTypeface(null,Typeface.BOLD);t.setPadding(dp(2),dp(8),dp(2),dp(8));return t;
  }
  private void init(String heading,String sub){
    root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setBackgroundColor(IVORY);
    TextView bar=text("✺  أم ملاك  |  الإدارة",24,GOLD,true);bar.setBackgroundColor(WINE);bar.setGravity(Gravity.CENTER);
    bar.setPadding(dp(12),dp(22),dp(12),dp(22));root.addView(bar);
    ScrollView sc=new ScrollView(this);sc.setFillViewport(true);
    page=new LinearLayout(this);page.setOrientation(LinearLayout.VERTICAL);page.setPadding(dp(20),dp(20),dp(20),dp(30));
    page.addView(text(heading,27,WINE,true));page.addView(text(sub,13,Color.DKGRAY,false));
    sc.addView(page);root.addView(sc,new LinearLayout.LayoutParams(-1,0,1));setContentView(root);
  }
  private EditText field(String label,String initial,boolean multi){
    page.addView(text(label,14,WINE,true));EditText input=new EditText(this);input.setSingleLine(!multi);
    input.setText(initial);input.setTextSize(15);input.setPadding(dp(12),dp(12),dp(12),dp(12));
    if(multi)input.setMinLines(3);input.setBackgroundTintList(android.content.res.ColorStateList.valueOf(GOLD));
    page.addView(input,new LinearLayout.LayoutParams(-1,-2));return input;
  }
  private void button(String label,Runnable run){
    Button b=new Button(this);b.setText(label);b.setTextColor(Color.WHITE);
    b.setBackgroundTintList(android.content.res.ColorStateList.valueOf(WINE));
    LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,dp(53));p.setMargins(0,dp(7),0,dp(6));
    page.addView(b,p);b.setOnClickListener(v->run.run());
  }
  private void headerNav(){
    LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);
    String[] titles={"المنتجات","محتوى الموقع","التواصل والسوشيال"};
    String[] ids={"products","site","social"};
    for(int i=0;i<titles.length;i++){final String id=ids[i];Button b=new Button(this);
      b.setText(titles[i]);b.setTextSize(11);b.setAllCaps(false);
      b.setTextColor(Color.WHITE);b.setBackgroundTintList(android.content.res.ColorStateList.valueOf(section.equals(id)?WINE:GOLD));
      row.addView(b,new LinearLayout.LayoutParams(0,dp(55),1));b.setOnClickListener(v->{section=id;render();});}
    page.addView(row);
  }
  private void setupKey(){
    init("ربط التطبيق","المفتاح المطلوب هنا Publishable فقط، ولا تضع مفاتيح service_role أو secret.");
    EditText k=field("Supabase Publishable Key","",false);
    button("حفظ مفتاح الربط",()->{String value=k.getText().toString().trim();if(value.isEmpty()){error("أدخل المفتاح العام");return;}
      pubKey=value;prefs.edit().putString("public_key",pubKey).apply();loginPage();});
  }
  private void loginPage(){
    authenticated=false;init("دخول بدون كلمة مرور","أدخلي بريد الإدارة، ثم رمز التأكيد الذي يصلك على البريد.");
    emailField=field("البريد الإلكتروني",prefs.getString("email",""),false);
    button("إرسال رمز الدخول",()->{
      String email=emailField.getText().toString().trim();
      if(!email.contains("@")){error("أدخلي بريدًا صحيحًا");return;}
      work(()->{JSONObject data=new JSONObject().put("email",email).put("create_user",false);
        request("POST","/auth/v1/otp",data.toString().getBytes(StandardCharsets.UTF_8),"application/json",false);
        prefs.edit().putString("email",email).apply();ui(()->{page.addView(text("تم إرسال الطلب. تحققي من البريد.",14,WINE,true));otpField=field("رمز البريد (6 أرقام)","",false);button("تأكيد الرمز",()->verifyOtp(email));});});
    });
    button("تغيير مفتاح الربط العام",this::setupKey);
  }
  private void verifyOtp(String email){
    String code=otpField.getText().toString().trim();
    if(code.length()<6){error("أدخلي الرمز الذي وصلك");return;}
    work(()->{JSONObject d=new JSONObject().put("email",email).put("token",code).put("type","email");
      JSONObject result=new JSONObject(request("POST","/auth/v1/verify",d.toString().getBytes(StandardCharsets.UTF_8),"application/json",false));
      access=result.getString("access_token");refresh=result.optString("refresh_token");
      prefs.edit().putString("access",access).putString("refresh",refresh).apply();verifyAdmin();
    });
  }
  private void verifyAdmin(){
    work(()->{
      try{
        JSONObject user=new JSONObject(request("GET","/auth/v1/user",null,null,true));
        String id=user.getString("id");
        JSONArray allowed=new JSONArray(request("GET","/rest/v1/om_malak_admins?user_id=eq."+id+"&select=user_id",null,null,true));
        if(allowed.length()==0)throw new Exception("هذا البريد غير مضاف إلى قائمة الإدارة. أضفه من Supabase Authentication ثم om_malak_admins.");
        authenticated=true;loadAll();
      }catch(Exception e){access="";refresh="";prefs.edit().remove("access").remove("refresh").apply();ui(()->{loginPage();error(e.getMessage());});}
    });
  }
  private String request(String method,String endpoint,byte[] body,String mime,boolean auth) throws Exception{
    return requestRetry(method,endpoint,body,mime,auth,true);
  }
  private String requestRetry(String method,String endpoint,byte[] body,String mime,boolean auth,boolean retry) throws Exception{
    URL u=new URL(BASE+endpoint);HttpURLConnection c=(HttpURLConnection)u.openConnection();
    c.setRequestMethod(method);c.setConnectTimeout(18000);c.setReadTimeout(35000);c.setRequestProperty("apikey",pubKey);
    c.setRequestProperty("Accept","application/json");
    if(auth&&!access.isEmpty())c.setRequestProperty("Authorization","Bearer "+access);
    if(mime!=null)c.setRequestProperty("Content-Type",mime);
    if(body!=null){c.setDoOutput(true);try(OutputStream out=c.getOutputStream()){out.write(body);}}
    int status=c.getResponseCode();InputStream stream=status>=400?c.getErrorStream():c.getInputStream();
    String response="";if(stream!=null)try(InputStream in=stream){response=new String(in.readAllBytes(),StandardCharsets.UTF_8);}
    c.disconnect();
    if(status==401&&auth&&retry&&!refresh.isEmpty()){
      JSONObject d=new JSONObject().put("refresh_token",refresh);
      JSONObject token=new JSONObject(requestRetry("POST","/auth/v1/token?grant_type=refresh_token",d.toString().getBytes(StandardCharsets.UTF_8),"application/json",false,false));
      access=token.getString("access_token");refresh=token.optString("refresh_token",refresh);
      prefs.edit().putString("access",access).putString("refresh",refresh).apply();
      return requestRetry(method,endpoint,body,mime,auth,false);
    }
    if(status>=400)throw new Exception("HTTP "+status+": "+response.substring(0,Math.min(response.length(),240)));
    return response;
  }
  private void loadAll(){
    work(()->{
      products=new JSONArray(request("GET","/rest/v1/om_malak_products?select=*&order=created_at.desc",null,null,true));
      socials=new JSONArray(request("GET","/rest/v1/om_malak_social_links?select=*&order=sort_order.asc",null,null,true));
      JSONArray st=new JSONArray(request("GET","/rest/v1/om_malak_settings?select=*&id=eq.1",null,null,true));
      if(st.length()>0)site=st.getJSONObject(0);ui(this::render);
    });
  }
  private void render(){
    if(!authenticated){loginPage();return;}
    init("مرحبًا بكِ ♡","إدارة إبداعاتك بدون ضغط الصور، مع مزامنة مباشرة للموقع.");
    headerNav();
    if(section.equals("products"))productPage();else if(section.equals("site"))sitePage();else socialPage();
    button("تحديث البيانات ↻",this::loadAll);
    button("تسجيل الخروج",()->{
      work(()->{try{request("POST","/auth/v1/logout",new byte[0],"application/json",true);}catch(Exception ignored){}
        access="";refresh="";prefs.edit().remove("access").remove("refresh").apply();ui(this::loginPage);});
    });
  }
  private void productPage(){
    page.addView(text("المنتجات المنشورة: "+products.length(),18,WINE,true));
    button("+ إضافة منتج جديد",()->productEditor(null));
    for(int i=0;i<products.length();i++){
      JSONObject p=products.optJSONObject(i);if(p==null)continue;
      page.addView(text("✧ "+p.optString("title")+"   |   "+p.optString("category"),17,WINE,true));
      page.addView(text(p.optBoolean("published")?"منشور":"مخفي",12,GOLD,false));
      button("تعديل المنتج",()->productEditor(p));
      button("حذف المنتج",()->new AlertDialog.Builder(this).setTitle("حذف المنتج؟")
        .setMessage(p.optString("title")).setNegativeButton("إلغاء",null)
        .setPositiveButton("حذف",(d,w)->removeProduct(p)).show());
    }
  }
  private void productEditor(JSONObject p){
    selectedId=p==null?"":p.optString("id");selectedPhoto=null;
    init(selectedId.isEmpty()?"منتج جديد":"تعديل المنتج","ارفع الصورة الأصلية كما هي؛ بدون ضغط أو تغيير الجودة.");
    titleField=field("اسم المنتج",p==null?"":p.optString("title"),false);
    categoryField=field("التصنيف",p==null?"جلابيات":p.optString("category"),false);
    priceField=field("السعر بالدينار (اختياري)",p==null?"":p.isNull("price")?"":p.optString("price"),false);
    descriptionField=field("الوصف",p==null?"":p.optString("description"),true);
    button("اختيار صورة من الهاتف (دون ضغط)",()->{
      Intent in=new Intent(Intent.ACTION_OPEN_DOCUMENT);in.setType("image/*");in.addCategory(Intent.CATEGORY_OPENABLE);
      in.putExtra(Intent.EXTRA_MIME_TYPES,new String[]{"image/jpeg","image/png","image/webp"});startActivityForResult(in,204);
    });
    button("حفظ ونشر المنتج",()->saveProduct(p));
    button("عودة",this::render);
  }
  @Override protected void onActivityResult(int request,int result,Intent data){
    super.onActivityResult(request,result,data);
    if(request==204&&result==RESULT_OK&&data!=null){selectedPhoto=data.getData();if(selectedPhoto!=null){
      try{getContentResolver().takePersistableUriPermission(selectedPhoto,Intent.FLAG_GRANT_READ_URI_PERMISSION);}catch(Exception ignored){}
      Toast.makeText(this,"تم اختيار الصورة الأصلية",Toast.LENGTH_SHORT).show();
    }}
  }
  private void saveProduct(JSONObject previous){
    String name=titleField.getText().toString().trim(),category=categoryField.getText().toString().trim();
    if(name.isEmpty()||category.isEmpty()){error("أكملي الاسم والتصنيف");return;}
    if(selectedId.isEmpty()&&selectedPhoto==null){error("اختاري صورة المنتج أولًا");return;}
    String value=priceField.getText().toString().trim();
    work(()->{
      JSONObject d=new JSONObject().put("title",name).put("category",category)
        .put("description",descriptionField.getText().toString().trim()).put("published",true);
      if(value.isEmpty())d.put("price",JSONObject.NULL);else d.put("price",Double.parseDouble(value));
      String oldPath=previous==null?"":previous.optString("storage_path");
      String newPath="";
      if(selectedPhoto!=null){
        String mime=getContentResolver().getType(selectedPhoto);
        if(mime==null||!(mime.equals("image/jpeg")||mime.equals("image/png")||mime.equals("image/webp")))throw new Exception("نوع الصورة غير مدعوم");
        byte[] bytes;try(InputStream in=getContentResolver().openInputStream(selectedPhoto)){if(in==null)throw new IOException("Cannot read photo");bytes=in.readAllBytes();}
        if(bytes.length>20*1024*1024)throw new Exception("الحد الأقصى للصورة 20MB");
        String ext=mime.equals("image/png")?"png":mime.equals("image/webp")?"webp":"jpg";
        newPath=UUID.randomUUID().toString()+"."+ext;
        request("POST","/storage/v1/object/om-malak-gallery/"+newPath,bytes,mime,true);
        d.put("image_url",BASE+"/storage/v1/object/public/om-malak-gallery/"+newPath).put("storage_path",newPath);
      }
      try{
        byte[] payload=d.toString().getBytes(StandardCharsets.UTF_8);
        if(selectedId.isEmpty())request("POST","/rest/v1/om_malak_products",payload,"application/json",true);
        else request("PATCH","/rest/v1/om_malak_products?id=eq."+selectedId,payload,"application/json",true);
      }catch(Exception e){
        if(!newPath.isEmpty())try{request("DELETE","/storage/v1/object/om-malak-gallery/"+newPath,null,null,true);}catch(Exception ignored){}
        throw e;
      }
      if(!newPath.isEmpty()&&!oldPath.isEmpty())try{request("DELETE","/storage/v1/object/om-malak-gallery/"+oldPath,null,null,true);}catch(Exception ignored){}
      ui(()->{Toast.makeText(this,"تم حفظ المنتج ♡",Toast.LENGTH_LONG).show();loadAll();});
    });
  }
  private void removeProduct(JSONObject p){
    work(()->{String id=p.getString("id");request("DELETE","/rest/v1/om_malak_products?id=eq."+id,null,null,true);
      String path=p.optString("storage_path");if(!path.isEmpty())try{request("DELETE","/storage/v1/object/om-malak-gallery/"+path,null,null,true);}catch(Exception ignored){}
      ui(()->{Toast.makeText(this,"تم الحذف",Toast.LENGTH_SHORT).show();loadAll();});});
  }
  private void sitePage(){
    heroField=field("العنوان الرئيسي",site.optString("hero_title","أم ملاك"),false);
    subtitleField=field("العنوان الفرعي",site.optString("hero_subtitle"),false);
    aboutField=field("وصف الصفحة",site.optString("hero_description"),true);
    contactTextField=field("نص زر التواصل",site.optString("contact_label"),false);
    contactUrlField=field("رابط التواصل",site.optString("contact_url"),false);
    button("حفظ محتوى الموقع",()->{
      String url=contactUrlField.getText().toString().trim();
      if(!url.startsWith("https://")){error("استعمل رابط HTTPS فقط");return;}
      work(()->{JSONObject d=new JSONObject().put("hero_title",heroField.getText().toString().trim())
        .put("hero_subtitle",subtitleField.getText().toString().trim())
        .put("hero_description",aboutField.getText().toString().trim())
        .put("contact_label",contactTextField.getText().toString().trim()).put("contact_url",url);
        request("PATCH","/rest/v1/om_malak_settings?id=eq.1",d.toString().getBytes(StandardCharsets.UTF_8),"application/json",true);
        ui(()->{Toast.makeText(this,"تم حفظ المحتوى",Toast.LENGTH_SHORT).show();loadAll();});});
    });
  }
  private void socialPage(){
    page.addView(text("روابط شبكات التواصل",19,WINE,true));
    for(int i=0;i<socials.length();i++){
      JSONObject x=socials.optJSONObject(i);if(x==null)continue;
      page.addView(text(x.optString("label")+" : "+x.optString("url"),13,WINE,false));
      button("تعديل الرابط",()->socialEditor(x));
      button("حذف الرابط",()->new AlertDialog.Builder(this).setTitle("حذف الرابط؟")
        .setNegativeButton("إلغاء",null).setPositiveButton("حذف",(d,w)->work(()->{
          request("DELETE","/rest/v1/om_malak_social_links?id=eq."+x.getString("id"),null,null,true);ui(this::loadAll);
        })).show());
    }
    button("+ إضافة حساب تواصل",()->socialEditor(null));
  }
  private void socialEditor(JSONObject x){
    init(x==null?"إضافة رابط":"تعديل رابط","روابط Facebook وInstagram وTikTok وTelegram وغيرها.");
    EditText label=field("اسم المنصة",x==null?"":x.optString("label"),false);
    EditText url=field("الرابط HTTPS",x==null?"":x.optString("url"),false);
    button("حفظ الرابط",()->{
      String val=url.getText().toString().trim(),name=label.getText().toString().trim();
      if(name.isEmpty()||!val.startsWith("https://")){error("أدخل اسمًا ورابط HTTPS");return;}
      work(()->{JSONObject j=new JSONObject().put("label",name).put("url",val).put("enabled",true);
        String path="/rest/v1/om_malak_social_links";
        if(x!=null)path+="?id=eq."+x.getString("id");
        request(x==null?"POST":"PATCH",path,j.toString().getBytes(StandardCharsets.UTF_8),"application/json",true);
        ui(()->{section="social";loadAll();});});
    });
    button("عودة",this::render);
  }
}
