module.paths.push('/usr/lib/node_modules');
process.env.PLAYWRIGHT_BROWSERS_PATH = process.env.PLAYWRIGHT_BROWSERS_PATH || '/opt/playwright-browsers';
const fs=require('fs');
const path=require('path');
const {chromium}=require('playwright');
const ROOT=__dirname,DECK=path.join(ROOT,'deck.html'),OUT=path.join(ROOT,'deck.pptx');
const BUNDLE='/usr/lib/node_modules/dom-to-pptx/dist/dom-to-pptx.bundle.js';
(async()=>{
  const bundleSrc=fs.readFileSync(BUNDLE,'utf8');
  const b=await chromium.launch({headless:true});
  const ctx=await b.newContext({viewport:{width:1920,height:1080}});
  const p=await ctx.newPage();
  p.on('console',m=>console.log(`[browser:${m.type()}]`,m.text()));
  await p.goto('file://'+DECK,{waitUntil:'networkidle',timeout:60000});
  await p.evaluate(()=>document.fonts.ready);
  await p.addStyleTag({content:`
    html,body{margin:0!important;padding:0!important}
    #slide-nav,.theme-toggle,.thumb-toggle,.thumb-nav,nav{display:none!important}
    body{padding-left:0!important}
    .slide-wrap > .slide{transform:none!important}
    .slide{width:1920px!important;height:1080px!important;min-height:1080px!important;max-height:1080px!important;margin:0!important;border:0!important;overflow:hidden!important;position:relative!important}
  `});
  await p.evaluate(()=>document.body.offsetHeight);
  await new Promise(r=>setTimeout(r,500));
  await p.addScriptTag({content:bundleSrc});
  const b64=await p.evaluate(async()=>{
    const slides=Array.from(document.querySelectorAll('.deck > .slide-wrap > .slide'));
    slides.forEach(s=>{s.style.width='1920px';s.style.height='1080px';s.style.minHeight='1080px';s.style.maxHeight='1080px';s.style.overflow='hidden';});
    void document.body.offsetHeight;
    return new Promise((resolve,reject)=>{
      let cap=null;
      URL.createObjectURL=blob=>{
        const r=new FileReader();
        r.onload=()=>{cap=r.result.split(',')[1];resolve(cap);};
        r.onerror=()=>reject(r.error);
        r.readAsDataURL(blob);
        return 'blob:captured';
      };
      window.domToPptx.exportToPptx(slides,{fileName:'deck.pptx'}).catch(reject);
      setTimeout(()=>{if(!cap)reject(new Error('no blob'));},15000);
    });
  });
  fs.writeFileSync(OUT,Buffer.from(b64,'base64'));
  await b.close();
  console.log(`[ok] wrote ${OUT} (${fs.statSync(OUT).size} bytes)`);
})();
