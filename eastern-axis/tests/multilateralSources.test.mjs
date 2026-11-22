import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {ISO2_TO_ISO3,MULTILATERAL_SOURCES,countrySourceUrl,iso3Of,multilateralCoverage} from '../src/lib/multilateralSources.ts';

test('ISO 3166-1 code map is complete, bijective and refuses unassigned aggregations',()=>{
  assert.equal(Object.keys(ISO2_TO_ISO3).length,249);
  assert.equal(new Set(Object.values(ISO2_TO_ISO3)).size,249);
  for(const [alpha2,alpha3] of Object.entries(ISO2_TO_ISO3)){
    assert.match(alpha2,/^[A-Z]{2}$/);
    assert.match(alpha3,/^[A-Z]{3}$/);
    assert.equal(iso3Of(alpha2.toLowerCase()),alpha3);
    assert.equal(iso3Of(alpha3),alpha3);
  }
  for(const [a,b] of [['US','USA'],['GB','GBR'],['CN','CHN'],['DE','DEU'],
    ['JP','JPN'],['TR','TUR'],['CI','CIV'],['CD','COD'],['CG','COG'],
    ['RU','RUS'],['KR','KOR'],['KP','PRK']])assert.equal(iso3Of(a),b);
  for(const code of ['WLD','XK','UK','all','000',''])assert.equal(iso3Of(code),null);
});
test('discovery providers never masquerade as live connected data',()=>{
  assert.equal(MULTILATERAL_SOURCES.length,10);
  assert.equal(multilateralCoverage.integrated,4);
  assert.equal(multilateralCoverage.reference,5);
  assert.equal(multilateralCoverage.archived,1);
  assert.equal(MULTILATERAL_SOURCES.find(s=>s.id==='wdi')?.status,'connected');
  assert.equal(MULTILATERAL_SOURCES.find(s=>s.id==='owid')?.status,'partial');
  assert.equal(MULTILATERAL_SOURCES.find(s=>s.id==='comtrade')?.status,'partial');
  for(const id of ['imf','undata','oecd','unctad','who'])assert.equal(
    MULTILATERAL_SOURCES.find(s=>s.id===id)?.status,'reference',id);
  assert.equal(MULTILATERAL_SOURCES.find(s=>s.id==='cia')?.status,'archive');
  for(const source of MULTILATERAL_SOURCES){
    assert.match(source.url,/^https:\/\//,source.id);
    assert.ok(source.metrics&&source.scope&&source.notes&&source.access,source.id);
    if(source.status==='reference')assert.match(source.scope,/Discovery only/,source.id);
  }
});
test('standard country link is constructed only from validated ISO3; incomplete mappings fall back',()=>{
  assert.equal(countrySourceUrl('wdi','CI'),'https://data.worldbank.org/country/CIV');
  assert.equal(countrySourceUrl('wdi','TR'),'https://data.worldbank.org/country/TUR');
  assert.equal(countrySourceUrl('wdi','XK'),'https://data.worldbank.org/');
  assert.equal(countrySourceUrl('imf','US'),'https://data.imf.org/');
  assert.equal(countrySourceUrl('nonexistent','US'),'');
});
test('every source card remains expandable and linked to its official platform',()=>{
  const comp=readFileSync(new URL('../src/MultilateralSourceGuide.tsx',import.meta.url),'utf8');
  const factbook=readFileSync(new URL('../src/Factbook.tsx',import.meta.url),'utf8');
  const shell=readFileSync(new URL('../src/App.tsx',import.meta.url),'utf8');
  assert.match(comp,/aria-expanded=\{open\}/);
  assert.match(comp,/MULTILATERAL_SOURCES\.map/);
  assert.match(comp,/countrySourceUrl\(item.id,countryCode\)/);
  assert.match(factbook,/MultilateralSourceGuide context="factbook"/);
  assert.match(shell,/MultilateralSourceGuide context="library"/);
});
