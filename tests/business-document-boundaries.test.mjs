import test from 'node:test';
import assert from 'node:assert/strict';
import {assertSafeXML,normalizeCell,zipEntryFilter,validateDecodedEntries} from '../site/business-intelligence/document-formats.mjs';
import {extractDocument} from '../site/business-intelligence/documents.mjs';
test('multiline cells cannot create phantom fields or shift subsequent row provenance',()=>{
 const text=['Supplier,'+normalizeCell('Example\r\nCountry,XX'),'Country,US'].join('\n');
 const {facts}=extractDocument(text,'fixture.xlsx');
 assert.equal(facts.length,2);assert.equal(facts[0].value,'Example Country,XX');assert.equal(facts[1].field,'country');assert.equal(facts[1].value,'US');assert.equal(facts[1].line,2);
});
test('DTD and entity syntax rejected before XML parsing',()=>{
 assert.throws(()=>assertSafeXML('<!DOCTYPE x [<!ENTITY a "boom">]><x>&a;</x>'),/unsupported/);
 assert.throws(()=>assertSafeXML('<!ENTITY a SYSTEM "https://example.com/private">'),/unsupported/);
 assert.doesNotThrow(()=>assertSafeXML('<worksheet/>'));
});
test('stored ZIP forged output size, invalid sizes and aggregate decoded sizes fail closed',()=>{
 const entry={name:'xl/worksheets/sheet1.xml',compression:0,size:1024,originalSize:0};
 assert.throws(()=>zipEntryFilter()(entry),/mismatch/);
 for(const size of [-1,NaN,Infinity,1.5])assert.throws(()=>zipEntryFilter()({...entry,size,originalSize:size}),/Invalid/);
 assert.throws(()=>zipEntryFilter()({...entry,compression:8,size:6*1024*1024,originalSize:1}),/limits/);
 assert.throws(()=>validateDecodedEntries({a:new Uint8Array(5*1024*1024+1)}),/limits/);
 const filter=zipEntryFilter();for(let i=0;i<4;i++)filter({...entry,size:5*1024*1024,originalSize:5*1024*1024});assert.throws(()=>filter({...entry,size:1,originalSize:1}),/limits/);
 assert.equal(zipEntryFilter()({...entry,size:10,originalSize:10}),true);
});
