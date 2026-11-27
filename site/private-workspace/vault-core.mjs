// Shared encrypted local vault. The calling workspace must validate its own
// schema and obtain explicit consent before storage, export or restoration.
const VERSION=1,ITERATIONS=600000,MAX_BYTES=2*1024*1024;
const encoder=new TextEncoder(),decoder=new TextDecoder("utf-8",{fatal:true});
const scopes=new Set(["business","personal"]);
function assertScope(scope){if(!scopes.has(scope))throw Error("Unknown vault scope");}
function assertPassword(password){if(typeof password!=="string"||password.length<12||password.length>256)throw Error("Use a passphrase of 12–256 characters.");}
function encode(bytes){let s="";for(let i=0;i<bytes.length;i+=8192)s+=String.fromCharCode(...bytes.subarray(i,i+8192));return btoa(s);}
function decode(s,max){if(typeof s!=="string"||s.length>Math.ceil(max/3)*4||!/^[A-Za-z0-9+/]*={0,2}$/.test(s))throw Error("Invalid encrypted vault");let b;try{b=Uint8Array.from(atob(s),c=>c.charCodeAt(0));}catch{throw Error("Invalid encrypted vault");}if(b.length>max||encode(b)!==s)throw Error("Invalid encrypted vault");return b;}
function validate(envelope,scope){
 assertScope(scope);
 if(!envelope||typeof envelope!=="object"||Array.isArray(envelope)||Object.keys(envelope).sort().join(",")!=="ciphertext,iterations,iv,kdf,salt,scope,version"||envelope.version!==VERSION||envelope.scope!==scope||envelope.kdf!=="PBKDF2-SHA256/AES-256-GCM"||envelope.iterations!==ITERATIONS)throw Error("Unsupported vault or wrong workspace");
 const salt=decode(envelope.salt,16),iv=decode(envelope.iv,12),cipher=decode(envelope.ciphertext,MAX_BYTES+16);
 if(salt.length!==16||iv.length!==12||cipher.length<17)throw Error("Invalid encrypted vault");
 return {salt,iv,cipher};
}
const aad=scope=>encoder.encode("Eastern Axis local vault v1:"+scope);
async function key(password,salt){
 const base=await crypto.subtle.importKey("raw",encoder.encode(password),"PBKDF2",false,["deriveKey"]);
 return crypto.subtle.deriveKey({name:"PBKDF2",hash:"SHA-256",salt,iterations:ITERATIONS},base,{name:"AES-GCM",length:256},false,["encrypt","decrypt"]);
}
export async function seal(scope,payload,password){
 assertScope(scope);assertPassword(password);
 if(!payload||typeof payload!=="object"||Array.isArray(payload))throw Error("Invalid profile payload");
 const plain=encoder.encode(JSON.stringify(payload));if(plain.length>MAX_BYTES)throw Error("Local vault payload exceeds 2 MB");
 const salt=crypto.getRandomValues(new Uint8Array(16)),iv=crypto.getRandomValues(new Uint8Array(12));
 try{const k=await key(password,salt),cipher=new Uint8Array(await crypto.subtle.encrypt({name:"AES-GCM",iv,additionalData:aad(scope),tagLength:128},k,plain));return {version:VERSION,scope,kdf:"PBKDF2-SHA256/AES-256-GCM",iterations:ITERATIONS,salt:encode(salt),iv:encode(iv),ciphertext:encode(cipher)};}
 finally{plain.fill(0);}
}
export async function unseal(scope,envelope,password){
 assertPassword(password);const {salt,iv,cipher}=validate(envelope,scope);
 let plain;
 try{const k=await key(password,salt);plain=new Uint8Array(await crypto.subtle.decrypt({name:"AES-GCM",iv,additionalData:aad(scope),tagLength:128},k,cipher));const payload=JSON.parse(decoder.decode(plain));if(!payload||typeof payload!=="object"||Array.isArray(payload))throw Error("Invalid profile");return payload;}
 catch{throw Error("Could not unlock vault: incorrect passphrase or invalid data");}
 finally{plain?.fill(0);}
}
export function parseBackup(scope,text){
 if(typeof text!=="string"||text.length>Math.ceil((MAX_BYTES+16)/3)*4+1024)throw Error("Invalid or oversized encrypted backup");
 let envelope;try{envelope=JSON.parse(text);}catch{throw Error("Invalid encrypted backup");}
 validate(envelope,scope);return envelope;
}
const DB="eastern-axis-encrypted-vault-v1",STORE="ciphertext";
function db(){
 return new Promise((resolve,reject)=>{
  const req=indexedDB.open(DB,1);
  req.onupgradeneeded=()=>req.result.createObjectStore(STORE);
  req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(Error("Local storage unavailable"));req.onblocked=()=>reject(Error("Local storage blocked"));
 });
}
async function operation(scope,mode,fn){
 assertScope(scope);const d=await db();
 try{return await new Promise((resolve,reject)=>{
  const tx=d.transaction(STORE,mode),request=fn(tx.objectStore(STORE));let result;
  request.onsuccess=()=>{result=request.result;};tx.oncomplete=()=>resolve(result??null);tx.onerror=tx.onabort=()=>reject(Error("Local vault storage failed"));
 });}finally{d.close();}
}
export async function readVault(scope){const envelope=await operation(scope,"readonly",s=>s.get(scope));if(envelope!==null)validate(envelope,scope);return envelope;}
export async function saveVault(scope,envelope){validate(envelope,scope);await operation(scope,"readwrite",s=>s.put(envelope,scope));}
export async function deleteVault(scope){await operation(scope,"readwrite",s=>s.delete(scope));}
