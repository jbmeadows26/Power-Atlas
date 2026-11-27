import {seal,unseal,parseBackup,readVault,saveVault,deleteVault} from "./vault-core.mjs";
const MAX_BACKUP=3*1024*1024;
export function setupVault({mount,scope,getProfile,validate,restore,clearProfile}){
 if(!mount)return {reset(){}};
 const el=(tag,value,cls)=>{const n=document.createElement(tag);if(value!==undefined)n.textContent=value;if(cls)n.className=cls;return n;};
 const note=el("p","Optional encrypted storage on this browser only. Your passphrase is not saved. If you lose it, the vault cannot be recovered. Clearing browser data may delete the vault; keep an encrypted backup. Open profiles remain in device memory, and encryption cannot protect a compromised browser.");
 const label=el("label","Vault passphrase"),pass=el("input");pass.type="password";pass.autocomplete="new-password";pass.minLength=12;pass.maxLength=256;pass.id=scope+"-vault-pass";label.htmlFor=pass.id;
 const repeatLabel=el("label","Confirm passphrase (required for saving)"),repeat=el("input");repeat.type="password";repeat.autocomplete="new-password";repeat.maxLength=256;repeat.id=scope+"-vault-confirm";repeatLabel.htmlFor=repeat.id;
 const buttons=el("div",undefined,"actions"),status=el("p","No profile is saved automatically.");status.setAttribute("role","status");status.id=scope+"-vault-status";
 const make=(caption,fn)=>{const b=el("button",caption);b.type="button";b.onclick=fn;buttons.append(b);return b;};
 const fileLabel=el("label","Encrypted backup file (optional)"),file=el("input");file.type="file";file.accept=".json,application/json";file.id=scope+"-vault-file";fileLabel.htmlFor=file.id;
 let busy=false,generation=0;
 function reset(){generation++;pass.value="";repeat.value="";file.value="";}
 function readPassword(confirmIt=false){const p=pass.value,r=repeat.value;pass.value="";repeat.value="";if(p.length<12||p.length>256)throw Error("Use a passphrase of 12–256 characters.");if(confirmIt&&p!==r)throw Error("Passphrases do not match.");return p;}
 async function action(fn){if(busy)return;busy=true;const token=generation;for(const b of buttons.children)b.disabled=true;status.textContent="Working locally…";
  try{await fn(token);}catch(e){status.textContent=e instanceof Error?e.message:"Local vault operation failed.";}finally{pass.value="";repeat.value="";file.value="";busy=false;for(const b of buttons.children)b.disabled=false;}}
 function ensure(token){if(generation!==token)throw Error("Workspace changed. Operation cancelled.");}
 make("Save encrypted profile",()=>action(async token=>{
  const p=readPassword(true),payload=validate(getProfile()),previous=await readVault(scope);ensure(token);
  if(!confirm(previous?"Replace the existing encrypted profile on this browser?":"Save an encrypted copy of your current profile on this browser?")){status.textContent="Save cancelled.";return;}
  const envelope=await seal(scope,payload,p);ensure(token);await saveVault(scope,envelope);status.textContent="Encrypted profile saved on this browser.";
 }));
 make("Restore saved profile",()=>action(async token=>{
  const p=readPassword(),envelope=await readVault(scope);ensure(token);if(!envelope)throw Error("No saved encrypted profile in this browser.");
  const payload=validate(await unseal(scope,envelope,p));ensure(token);
  if(!confirm("Replace the current open profile with the decrypted saved profile?")){status.textContent="Restore cancelled.";return;}
  restore(payload);status.textContent="Saved profile restored. It is open in this tab.";
 }));
 make("Export encrypted backup",()=>action(async token=>{
  const envelope=await readVault(scope);ensure(token);if(!envelope)throw Error("Save an encrypted profile before exporting.");
  const url=URL.createObjectURL(new Blob([JSON.stringify(envelope,null,2)],{type:"application/json"})),a=el("a");a.href=url;a.download=scope+"-encrypted-profile.json";a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);status.textContent="Encrypted backup prepared. No plaintext profile exported.";
 }));
 make("Restore encrypted backup",()=>action(async token=>{
  const p=readPassword(),f=file.files?.[0];if(!f||f.size>MAX_BACKUP)throw Error("Choose an encrypted backup JSON file within 3 MB.");
  const envelope=parseBackup(scope,await f.text()),payload=validate(await unseal(scope,envelope,p));ensure(token);
  if(!confirm("Replace your open profile with this backup? The saved vault will not change unless you explicitly save.")){status.textContent="Backup restore cancelled.";return;}
  restore(payload);status.textContent="Backup restored in this tab. Saved vault unchanged.";
 }));
 make("Lock and clear open profile",()=>action(async()=>{
  if(!confirm("Clear the open profile and private inputs? The encrypted saved copy, if any, remains.")){status.textContent="Lock cancelled.";return;}
  clearProfile();status.textContent="Open profile cleared. Saved encrypted copy unchanged.";
 }));
 make("Delete saved encrypted profile",()=>action(async()=>{
  if(!confirm("Permanently delete the saved encrypted profile from this browser? Export a backup first if needed.")){status.textContent="Deletion cancelled.";return;}
  await deleteVault(scope);status.textContent="Saved encrypted profile deleted. Open profile and external backups are unchanged.";
 }));
 mount.append(el("h2","Encrypted local profile"),note,label,pass,repeatLabel,repeat,fileLabel,file,buttons,status);
 if(!globalThis.isSecureContext||!globalThis.crypto?.subtle||!globalThis.indexedDB){for(const b of buttons.children)b.disabled=true;status.textContent="Encrypted local storage is unavailable on this browser.";}
 return {reset};
}
