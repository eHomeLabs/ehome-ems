const {chromium}=require('playwright');
const http=require('node:http'),fs=require('node:fs/promises'),path=require('node:path');
const root=path.resolve(__dirname,'..'),out=path.join(root,'docs/screenshots');
(async()=>{
 await fs.mkdir(out,{recursive:true});
 const server=http.createServer(async(req,res)=>{try{const url=new URL(req.url,'http://localhost');const file=path.resolve(root,'.'+decodeURIComponent(url.pathname).replace('/ehome_ems_assets/','/custom_components/ehome_ems/frontend/assets/'));if(!file.startsWith(root+path.sep))throw Error('path');res.setHeader('Content-Type',file.endsWith('.webp')?'image/webp':file.endsWith('.html')?'text/html':file.endsWith('.json')?'application/json':'text/javascript');res.end(await fs.readFile(file));}catch{res.statusCode=404;res.end();}});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));let browser;
 try{
  browser=await chromium.launch({headless:true,args:['--no-sandbox']});const page=await browser.newPage({viewport:{width:1440,height:1500},deviceScaleFactor:1});
  await page.clock.setFixedTime(new Date('2026-11-01T10:00:00Z'));
  await page.goto('http://127.0.0.1:'+server.address().port+'/tests/fixtures/panel.html');
  await page.getByRole('button',{name:'Vue d’ensemble',exact:true}).waitFor();
  await page.locator('.flow-house img').evaluate(img=>img.decode());
  await page.locator('.kpis .spark-note').first().getByText('Tendance sur 15 mn',{exact:true}).waitFor();
  await page.locator('main').screenshot({path:path.join(out,'overview.png')});
  await page.locator('.flow').screenshot({path:path.join(out,'energy-flow.png')});
  await page.locator('.home-diagnostic summary').click();await page.locator('.home-diagnostic').screenshot({path:path.join(out,'home-balance.png')});
  await page.getByRole('button',{name:'Mes Appareils',exact:true}).click();await page.getByText('0,81 kWh',{exact:true}).waitFor();
  await page.locator('.cards').screenshot({path:path.join(out,'appliances.png')});
  await page.getByRole('button',{name:'Stockage',exact:true}).click();await page.getByRole('heading',{name:'Aferiy',exact:true}).waitFor();
  await page.locator('.stack').first().screenshot({path:path.join(out,'storage.png')});
  await page.getByRole('button',{name:'Aujourd’hui',exact:true}).click();await page.locator('.weather-card').getByText('Éclaircies',{exact:true}).waitFor();
  await page.locator('.today').screenshot({path:path.join(out,'today.png')});
  await page.getByRole('button',{name:'Historique',exact:true}).click();await page.locator('.history-chart svg').first().waitFor();await page.locator('main').screenshot({path:path.join(out,'history.png')});
  await page.getByRole('button',{name:'Configuration',exact:true}).click();await page.locator('.settings-shortcuts').waitFor();
  await page.locator('main').screenshot({path:path.join(out,'configuration.png')});
  console.log('Captured 8 actual 0.2.2 UI screenshots with simulated data.');
 }finally{if(browser)await browser.close();await new Promise(r=>server.close(r));}
})().catch(e=>{console.error(e);process.exitCode=1;});
