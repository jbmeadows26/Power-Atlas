import test from 'node:test';
import assert from 'node:assert/strict';
import {parseSocialCsv} from '../backend/socialSources.ts';

const spec=(slug,column)=>({slug,column,meaning:'test',sourceName:'verified source'});
function fixture(column,tail={}){
 const rows=['Entity,Code,Year,'+column];
 for(let i=0;i<70;i++){
  const code=String.fromCharCode(65+Math.floor(i/26),65+i%26,65);
  rows.push('Country '+i+','+code+',2022,0.35');
 }
 for(const [key,year,value] of [
   ['USA',2025,tail.usa??14.500179],['OWID_WRL',2025,tail.world??4.737237],
   ['CHN',2022,tail.china??4.5],['USA',2022,0.25],
   ['OWID_WRL',2024,0.2]
 ])rows.push((key==='USA'?'United States':key==='CHN'?'China':'World')+','+key+','+year+','+value);
 return rows.join('\n')+'\n';
}
test('official OWID CO2 schema, country codes and max-year selection',()=>{
 const data=parseSocialCsv(fixture('CO₂ emissions per capita'),spec('co-emissions-per-capita','CO₂ emissions per capita'));
 assert.deepEqual(data.get('USA'),{year:'2025',value:14.500179});
 assert.deepEqual(data.get('OWID_WRL'),{year:'2025',value:4.737237});
 assert.equal(data.get('CHN')?.year,'2022');
});
test('Gini survey and WID pretax remain different series with distinct schemas',()=>{
 const bank=parseSocialCsv(fixture('Gini coefficient',{usa:0.417625278,world:0.4}),spec('gini-coefficient-wb','Gini coefficient'));
 const pretax=parseSocialCsv(fixture('Gini coefficient (before tax)',{usa:0.5869,world:0.6769}),spec('gini-coefficient-wid','Gini coefficient (before tax)'));
 assert.notEqual(bank.get('USA')?.value,pretax.get('USA')?.value);
 assert.equal(pretax.get('OWID_WRL')?.value,0.6769);
 assert.equal(bank.get('USA')?.value,0.417625278);
});
test('Gini value range and missing cells fail closed',()=>{
 const gini=spec('gini-coefficient-wb','Gini coefficient');
 const invalid=fixture('Gini coefficient',{usa:1.4,world:-4});
 const data=parseSocialCsv(invalid,gini);
 assert.equal(data.get('USA')?.value,0.25);
 assert.equal(data.get('OWID_WRL')?.value,0.2);
});
test('schema drift fails closed',()=>{
 assert.throws(()=>parseSocialCsv(fixture('Carbon dioxide'),spec('co-emissions-per-capita','CO₂ emissions per capita')),/schema changed/);
 assert.throws(()=>parseSocialCsv('Entity,Code,Year,Gini coefficient\nChina,CHN,2025,0.5',spec('gini-coefficient-wb','Gini coefficient')),/unexpectedly short/);
});
test('quoted entity strings do not shift Code or Year',()=>{
 const s=fixture('Gini coefficient',{usa:0.48,world:0.4}).replace('United States,USA,2025','"United States, dependent areas",USA,2025');
 const rows=parseSocialCsv(s,spec('gini-coefficient-wb','Gini coefficient'));
 assert.equal(rows.get('USA')?.value,0.48);
});
