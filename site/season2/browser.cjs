const assert=require('node:assert/strict');
const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{});
try{
for(const [width,height] of [[320,800],[390,844],[1280,900]]){
  const p=await b.newPage({viewport:{width,height}});const errors=[];
  p.on('pageerror',e=>errors.push(e.message));
  await p.goto('http://127.0.0.1:8783/');
  await p.getByText('M05',{exact:true}).waitFor();
  const select=p.locator('#matches');assert.equal(await select.locator('option').count(),7);
  assert.equal(await select.inputValue(),'R3-01');
  await p.locator('#speed').selectOption('4');
  await p.getByRole('button',{name:'Play',exact:true}).click();
  await p.waitForFunction(()=>Number(document.querySelector('#seek').value)>44);
  await p.locator('#seek').press('End');
  assert.match(await p.locator('#actions').innerText(),/M02 · 0 HP/);
  assert.match(await p.locator('#actions').innerText(),/M05 · 340 HP/);
  assert((await p.locator('#canvas').evaluate(c=>!!c.getContext('2d').getImageData(0,0,2,2).data[3])));
  assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true);
  assert.deepEqual(errors,[]);
  assert.equal((await p.request.get('http://127.0.0.1:8783/data.json')).status(),404,'old results must not be staged');
  console.log('Knockout season replay and old-results removal verified at '+width+'×'+height);
  await p.close();
}
}finally{await b.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
