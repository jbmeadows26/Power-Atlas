import {test} from "node:test";import assert from "node:assert/strict";
import {seal,unseal,parseBackup} from "../site/private-workspace/vault-core.mjs";
const password="QA passphrase for tests only",payload={dependencies:[{name:"QA confidential supplier",cost:12345}]};
test("authenticated portable envelope contains no plaintext and round trips",async()=>{
 const a=await seal("business",payload,password),b=await seal("business",payload,password);
 assert.notEqual(a.salt,b.salt);assert.notEqual(a.iv,b.iv);assert.notEqual(a.ciphertext,b.ciphertext);
 assert.ok(!JSON.stringify(a).includes("QA confidential supplier"));assert.ok(!JSON.stringify(a).includes(password));
 assert.deepEqual(await unseal("business",parseBackup("business",JSON.stringify(a)),password),payload);
 await assert.rejects(unseal("business",a,"wrong passphrase for tests"),/Could not unlock/);
 await assert.rejects(unseal("personal",a,password),/wrong workspace/);
 const bad={...a,ciphertext:(a.ciphertext[0]==="A"?"B":"A")+a.ciphertext.slice(1)};await assert.rejects(unseal("business",bad,password),/Could not unlock/);
 assert.throws(()=>parseBackup("business",JSON.stringify({...a,iterations:1})));
 await assert.rejects(seal("business",payload,"short"),/passphrase/);
});
