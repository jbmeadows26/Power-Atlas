import {test} from "node:test";
import assert from "node:assert/strict";
import {codeValue,lookup,landed} from "../site/business-intelligence/procurement.mjs";
const index={records:{"01234567":{general:"Free",special:null,column2:"5%"},"0123456789":{general:null,special:null,column2:null}},ambiguous:["12345678"]};
test("exact code lookup preserves leading zeros and blank rate",()=>{assert.equal(codeValue("0123.45.67"),"01234567");assert.equal(codeValue("0123.45.67.89"),"0123456789");assert.equal(codeValue("123456"),null);assert.equal(lookup(index,"0123456789").row.general,null);assert.equal(lookup(index,"12345678").status,"ambiguous");assert.equal(lookup(index,"0123456700").status,"not found");assert.equal(lookup(null,"01234567").status,"unavailable");});
test("landed cost only uses explicitly entered inputs",()=>{assert.deepEqual(landed(10000,15,400,75),{duty:1500,total:11975});assert.deepEqual(landed(100,0,0,0),{duty:0,total:100});assert.equal(landed(100,null,0,0),null);assert.equal(landed(100,-1,0,0),null);});
