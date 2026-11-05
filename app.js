// أم ملاك — Public portfolio. Products are published through reviewed GitHub updates.
// Administration will be added later as a separate application.
const $=s=>document.querySelector(s);
const products=[
{title:'تشكيلة الأم والبنت',category:'جلابيات',description:'طقم أنيق باللون العنابي وتفاصيل مطرزة بعناية. للاستفسار عن المقاسات والتفصيل، تواصلي مع أم ملاك على فيسبوك.',image:'./images/oum-malak-original.jpg'},
{title:'لمسات أم ملاك',category:'جلابيات',description:'تفاصيل التشكيلة العنابية بتوقيع أم ملاك. للاستفسار عن الطلبات والألوان، تواصلي معنا على فيسبوك.',image:'./images/oum-malak-watermark.jpg'}
];
const FACEBOOK='https://www.facebook.com/share/19drC5x1CW/';
document.addEventListener('DOMContentLoaded',()=>{
 const splash=$('#splash');const closeSplash=()=>splash?.classList.add('done');
 window.addEventListener('load',()=>setTimeout(closeSplash,1100),{once:true});
 setTimeout(closeSplash,3200);
 if($('#year'))$('#year').textContent=new Date().getFullYear();
 const grid=$('#products');if(!grid)return;
 grid.replaceChildren(...products.map(product=>{
  const article=document.createElement('article');article.className='product';
  const thumb=document.createElement('div');thumb.className='thumb';
  const img=document.createElement('img');img.src=product.image;img.alt=product.title;img.loading='lazy';
  img.addEventListener('error',()=>{thumb.classList.add('image-unavailable');img.alt='صورة المنتج قيد التجهيز';});
  thumb.append(img);const info=document.createElement('div');info.className='product-info';
  const label=document.createElement('span');label.textContent=product.category;
  const heading=document.createElement('h3');heading.textContent=product.title;
  const description=document.createElement('p');description.textContent=product.description;
  const link=document.createElement('a');link.href=FACEBOOK;link.target='_blank';link.rel='noopener noreferrer';link.textContent='استفسري عبر فيسبوك ←';
  info.append(label,heading,description,link);article.append(thumb,info);return article;
 }));
 if($('#empty'))$('#empty').hidden=true;
});
