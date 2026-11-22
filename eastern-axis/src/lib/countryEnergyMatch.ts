import {isoAlpha3} from './countryStatisticalSources.ts';

/**
 * Historical OWID snapshots used normalized country *names* as database keys.
 * New snapshots use ISO3. Legacy fallback is allowed only if the stored ISO3
 * independently matches the requested country. No name-only attribution.
 */
const alias:Record<string,string>={
  RU:'russia',CN:'china',KP:'northkorea',KR:'southkorea',IR:'iran',
  TW:'taiwan',GB:'unitedkingdom',TR:'turkey',US:'unitedstates',
  CD:'democraticrepublicofcongo',CZ:'czechia',VA:'vatican',
  PS:'palestine',MM:'myanmar'
};
const tidy=(name:string)=>name.toLowerCase().normalize('NFD')
  .replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]/g,'');

export const matchEnergyCountry=<T extends {name:string;iso3:string}>(
  byCountry:Record<string,T>|undefined|null,code:string,countryName?:string
):T|null=>{
  if(!byCountry)return null;
  const canonical=code==='all'?'OWID_WRL':isoAlpha3(code);
  if(!canonical)return null;
  const current=byCountry[canonical];
  if(current && (
    (code==='all'&&current.name==='World')||
    (code!=='all'&&current.iso3===canonical)
  ))return current;
  const oldKey=code==='all'?'world':
    (alias[code]||tidy(countryName||new Intl.DisplayNames(['en'],{type:'region'}).of(code)||code));
  const legacy=byCountry[oldKey];
  return legacy&&(
    (code==='all'&&legacy.name==='World')||
    (code!=='all'&&legacy.iso3===canonical)
  )?legacy:null;
};
