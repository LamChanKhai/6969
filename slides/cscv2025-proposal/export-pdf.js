module.paths.push('/usr/lib/node_modules');
process.env.PLAYWRIGHT_BROWSERS_PATH = process.env.PLAYWRIGHT_BROWSERS_PATH || '/opt/playwright-browsers';
const fs=require('fs');
const path=require('path');
const {chromium}=require('playwright');
const {PDFDocument}=require('pdf-lib');
const ROOT=__dirname,DECK=path.join(ROOT,'deck.html'),OUT=path.join(ROOT,'deck.pdf'),TMP=path.join(ROOT,'.pdf-tmp');
(async()=>{
  fs.rmSync(TMP,{recursive:true,force:true});fs.mkdirSync(TMP,{recursive:true});
  const b=await chromium.launch({headless:true,args:['--disable-dev-shm-usage','--no-sandbox']});
  const ctx=await b.newContext({viewport:{width:1920,height:1080}});
  const p=await ctx.newPage();
  await p.goto('file://'+DECK,{waitUntil:'networkidle',timeout:90000});
  await p.evaluate(()=>document.fonts.ready);
  await p.addStyleTag({content:`
    @page{size:1920px 1080px;margin:0}
    html,body{margin:0!important;padding:0!important;background:white!important}
    #slide-nav,.theme-toggle,.thumb-toggle,.thumb-nav,nav,header,footer{display:none!important}
    body{padding-left:0!important}
    .slide-wrap{width:1920px!important;height:1080px!important;overflow:hidden!important;border:0!important}
    .slide-wrap > .slide{transform:none!important}
    .slide{width:1920px!important;height:1080px!important;min-height:1080px!important;max-height:1080px!important;margin:0!important;border:0!important;overflow:hidden!important}
    .slide.pdf-hide,.slide-wrap.pdf-hide{display:none!important}
    *{-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important}
    *,*::before,*::after{box-shadow:none!important;text-shadow:none!important;filter:none!important;-webkit-filter:none!important;backdrop-filter:none!important;-webkit-backdrop-filter:none!important}
    .card{border:1px solid var(--border-strong,#cbd5e1)!important}
  `});
  await p.emulateMedia({media:'print'});
  const n=await p.evaluate(()=>document.querySelectorAll('.deck > .slide-wrap > .slide').length);
  console.log(`[info] rendering ${n} slides...`);
  const chunks=[];
  for(let i=0;i<n;i++){
    await p.evaluate(idx=>{
      document.querySelectorAll('.deck > .slide-wrap').forEach((w,j)=>w.classList.toggle('pdf-hide',j!==idx));
    },i);
    const out=path.join(TMP,`p-${String(i+1).padStart(3,'0')}.pdf`);
    await p.pdf({path:out,width:'1920px',height:'1080px',printBackground:true,preferCSSPageSize:true,pageRanges:'1'});
    chunks.push(out);
    if((i+1)%10===0)console.log(`[info] ...${i+1}/${n}`);
  }
  await b.close();
  const merged=await PDFDocument.create();
  for(const f of chunks){
    const src=await PDFDocument.load(fs.readFileSync(f));
    const pages=await merged.copyPages(src,src.getPageIndices());
    pages.forEach(pg=>merged.addPage(pg));
  }
  fs.writeFileSync(OUT,await merged.save());
  fs.rmSync(TMP,{recursive:true,force:true});
  console.log(`[ok] wrote ${OUT}`);
})();
