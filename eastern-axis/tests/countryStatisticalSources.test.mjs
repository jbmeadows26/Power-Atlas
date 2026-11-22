import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {countryStatisticalSources,isoCrosswalkSize,isoAlpha2,isoAlpha3,sourceTotals} from '../src/lib/countryStatisticalSources.ts';

test('ISO 3166 alpha-2/alpha-3 crosswalk covers all 249 standard entities without guessing names',()=>{
 assert.equal(isoCrosswalkSize,249);
 for(const [iso2,iso3] of [['US','USA'],['CN','CHN'],['RU','RUS'],['IR','IRN'],
   ['TR','TUR'],['CI','CIV'],['DE','DEU'],['JP','JPN'],['GB','GBR'],['KR','KOR'],
   ['KP','PRK'],['CD','COD'],['CG','COG'],['PS','PSE'],['ZA','ZAF']]){
   assert.equal(isoAlpha3(iso2),iso3);
   assert.equal(isoAlpha2(iso3),iso2);
   assert.equal(isoAlpha3(iso3),iso3);
 }
 for(const key of ['WLD','XK','-99','World','Turkey','Cote dIvoire','OWID_WRL','']){
   assert.equal(isoAlpha3(key),null,'Unknown or nonstandard geography cannot silently become a country: '+key);
 }
});

test('source directory separates existing ingestion, partial connections and discovery-only links',()=>{
 assert.equal(countryStatisticalSources.length,9);
 assert.deepEqual(sourceTotals(),{ingested:1,partial:3,discovery:4,archived:1});
 assert.equal(new Set(countryStatisticalSources.map(s=>s.id)).size,countryStatisticalSources.length);
 for(const source of countryStatisticalSources){
   assert.match(source.landingUrl,/^https:\/\//,source.id);
   assert.match(source.apiDocsUrl,/^https:\/\//,source.id);
   assert.ok(source.metricExamples&&source.identifierPolicy&&source.coverageNote);
   assert.ok(!source.landingUrl.includes('vercel.app'));
 }
 assert.equal(countryStatisticalSources.find(s=>s.id==='who').status,'discovery');
 assert.equal(countryStatisticalSources.find(s=>s.id==='comtrade').status,'partial');
 assert.match(countryStatisticalSources.find(s=>s.id==='comtrade').identifierPolicy,/M49/);
 assert.match(countryStatisticalSources.find(s=>s.id==='owid').identifierPolicy,/ISO alpha-3/);
 assert.match(countryStatisticalSources.find(s=>s.id==='cia-archive').coverageNote,/February 4, 2026/);
});

test('World Factbook and Coverage Audit integrate the source explorer on demand',()=>{
 const factbook=readFileSync(new URL('../src/Factbook.tsx',import.meta.url),'utf8');
 const coverage=readFileSync(new URL('../src/GlobalSystems.tsx',import.meta.url),'utf8');
 const component=readFileSync(new URL('../src/CountryStatisticalSources.tsx',import.meta.url),'utf8');
 assert.match(factbook,/CountryStatisticalSources countryCode=\{current\?\.iso\}/);
 assert.match(coverage,/CountryStatisticalSources context="coverage"/);
 assert.match(component,/<details className="css-root">/);
 assert.match(component,/<summary/);
 assert.match(component,/isoAlpha3\(countryCode\)/);
 assert.match(component,/an external publisher link is not proof/i);
});
