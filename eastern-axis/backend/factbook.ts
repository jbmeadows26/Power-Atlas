import { createHash } from 'node:crypto';

export const ARCHIVE_BASELINE = '2026-01-23';
export const ARCHIVE_REVISION = '144d6977b2b01ac1cbd220de754c0a005616760b';

/** Community mirror of the final public-domain CIA World Factbook reference. */
const index = String.raw`af|AF|Afghanistan
al|AL|Albania
ag|DZ|Algeria
an|AD|Andorra
ao|AO|Angola
ac|AG|Antigua and Barbuda
ar|AR|Argentina
am|AM|Armenia
as|AU|Australia
au|AT|Austria
aj|AZ|Azerbaijan
bf|BS|The Bahamas
ba|BH|Bahrain
bg|BD|Bangladesh
bb|BB|Barbados
bo|BY|Belarus
be|BE|Belgium
bh|BZ|Belize
bn|BJ|Benin
bt|BT|Bhutan
bl|BO|Bolivia
bk|BA|Bosnia and Herzegovina
bc|BW|Botswana
br|BR|Brazil
bx|BN|Brunei
bu|BG|Bulgaria
uv|BF|Burkina Faso
bm|MM|Burma
by|BI|Burundi
cb|KH|Cambodia
cm|CM|Cameroon
ca|CA|Canada
cv|CV|Cape Verde
ct|CF|Central African Republic
cd|TD|Chad
ci|CL|Chile
ch|CN|China
co|CO|Colombia
cn|KM|Comoros
cg|CD|Congo DR
cf|CG|Congo
cs|CR|Costa Rica
iv|CI|Cote d'Ivoire
hr|HR|Croatia
cu|CU|Cuba
cy|CY|Cyprus
ez|CZ|Czechia
da|DK|Denmark
dj|DJ|Djibouti
do|DM|Dominica
dr|DO|Dominican Republic
ec|EC|Ecuador
eg|EG|Egypt
es|SV|El Salvador
ek|GQ|Equatorial Guinea
er|ER|Eritrea
en|EE|Estonia
wz|SZ|Eswatini
et|ET|Ethiopia
fj|FJ|Fiji
fi|FI|Finland
fr|FR|France
gb|GA|Gabon
ga|GM|The Gambia
gg|GE|Georgia
gm|DE|Germany
gh|GH|Ghana
gr|GR|Greece
gj|GD|Grenada
gt|GT|Guatemala
gv|GN|Guinea
pu|GW|Guinea-Bissau
gy|GY|Guyana
ha|HT|Haiti
ho|HN|Honduras
hu|HU|Hungary
ic|IS|Iceland
in|IN|India
id|ID|Indonesia
ir|IR|Iran
iz|IQ|Iraq
ei|IE|Ireland
is|IL|Israel
it|IT|Italy
jm|JM|Jamaica
ja|JP|Japan
jo|JO|Jordan
kz|KZ|Kazakhstan
ke|KE|Kenya
kr|KI|Kiribati
kn|KP|North Korea
ks|KR|South Korea
kv||Kosovo
ku|KW|Kuwait
kg|KG|Kyrgyzstan
la|LA|Laos
lg|LV|Latvia
le|LB|Lebanon
lt|LS|Lesotho
li|LR|Liberia
ly|LY|Libya
ls|LI|Liechtenstein
lh|LT|Lithuania
lu|LU|Luxembourg
ma|MG|Madagascar
mi|MW|Malawi
my|MY|Malaysia
mv|MV|Maldives
ml|ML|Mali
mt|MT|Malta
rm|MH|Marshall Islands
mr|MR|Mauritania
mp|MU|Mauritius
mx|MX|Mexico
fm|FM|Micronesia
md|MD|Moldova
mn|MC|Monaco
mg|MN|Mongolia
mj|ME|Montenegro
mo|MA|Morocco
mz|MZ|Mozambique
wa|NA|Namibia
nr|NR|Nauru
np|NP|Nepal
nl|NL|Netherlands
nz|NZ|New Zealand
nu|NI|Nicaragua
ng|NE|Niger
ni|NG|Nigeria
no|NO|Norway
mk|MK|North Macedonia
mu|OM|Oman
pk|PK|Pakistan
ps|PW|Palau
pm|PA|Panama
pp|PG|Papua New Guinea
pa|PY|Paraguay
pe|PE|Peru
rp|PH|Philippines
pl|PL|Poland
po|PT|Portugal
qa|QA|Qatar
ro|RO|Romania
rs|RU|Russia
rw|RW|Rwanda
sc|KN|Saint Kitts and Nevis
st|LC|Saint Lucia
vc|VC|Saint Vincent and the Grenadines
ws|WS|Samoa
sm|SM|San Marino
tp|ST|Sao Tome and Principe
sa|SA|Saudi Arabia
sg|SN|Senegal
ri|RS|Serbia
se|SC|Seychelles
sl|SL|Sierra Leone
sn|SG|Singapore
lo|SK|Slovakia
si|SI|Slovenia
bp|SB|Solomon Islands
so|SO|Somalia
sf|ZA|South Africa
od|SS|South Sudan
sp|ES|Spain
ce|LK|Sri Lanka
su|SD|Sudan
ns|SR|Suriname
sw|SE|Sweden
sz|CH|Switzerland
sy|SY|Syria
ti|TJ|Tajikistan
tz|TZ|Tanzania
th|TH|Thailand
tt|TL|Timor-Leste
to|TG|Togo
tn|TO|Tonga
td|TT|Trinidad and Tobago
ts|TN|Tunisia
tu|TR|Turkey
tx|TM|Turkmenistan
tv|TV|Tuvalu
ug|UG|Uganda
up|UA|Ukraine
ae|AE|United Arab Emirates
uk|GB|United Kingdom
us|US|United States
uy|UY|Uruguay
uz|UZ|Uzbekistan
nh|VU|Vanuatu
vt|VA|Vatican City (Holy See)
ve|VE|Venezuela
vm|VN|Vietnam
ym|YE|Yemen
za|ZM|Zambia
zi|ZW|Zimbabwe
tw|TW|Taiwan
ee||European Union
at||Ashmore and Cartier Islands
kt|CX|Christmas Island
ck|CC|Cocos (Keeling) Islands
cr||Coral Sea Islands
hm|HM|Heard Island and McDonald Islands
nf|NF|Norfolk Island
hk|HK|Hong Kong
mc|MO|Macau
fo|FO|Faroe Islands
gl|GL|Greenland
ip||Clipperton Island
fp|PF|French Polynesia
fs|TF|French Southern and Antarctic Lands
nc|NC|New Caledonia
tb|BL|Saint Barthelemy
rn|MF|Saint Martin
sb|PM|Saint Pierre and Miquelon
wf|WF|Wallis and Futuna
aa|AW|Aruba
uc|CW|Curacao
nn|SX|Sint Maarten
cw|CK|Cook Islands
ne|NU|Niue
tl|TK|Tokelau
bv|BV|Bouvet Island
jn||Jan Mayen
sv||Svalbard
ax||Akrotiri (Sovereign Base)
av|AI|Anguilla
bd|BM|Bermuda
io|IO|British Indian Ocean Territory
vi|VG|British Virgin Islands
cj|KY|Cayman Islands
dx||Dhekelia (Sovereign Base)
fk|FK|Falkland Islands
gi|GI|Gibraltar
gk|GG|Guernsey
je|JE|Jersey
im|IM|Isle of Man
mh|MS|Montserrat
pc|PN|Pitcairn Islands
sh|SH|Saint Helena
sx|GS|South Georgia and the South Sandwich Islands
tk|TC|Turks and Caicos Islands
aq|AS|American Samoa
gq|GU|Guam
bq||Navassa Island
cq|MP|Northern Mariana Islands
rq|PR|Puerto Rico
vq|VI|US Virgin Islands
wq||Wake Island
um||US Pacific Island Wildlife Refuges
ay|AQ|Antarctica
gz||Gaza Strip
pf||Paracel Islands
pg||Spratly Islands
we||West Bank
xq||Arctic Ocean
zh||Atlantic Ocean
xo||Indian Ocean
zn||Pacific Ocean
oo||Southern Ocean
xx||World`;
export const ARCHIVE_ENTITIES = index.trim().split('\n').map(line => {
  const [gec, iso, name] = line.split('|');
  return { code: iso || 'FB-' + gec.toUpperCase(), iso: iso || null, gec, name };
});
type Document = Record<string, unknown>;
type ArchivedFile = { data: Document; url: string; hash: string };
const cache = new Map<string, { value: unknown; validUntil: number }>();
const folders = [
  'africa', 'antarctica', 'australia-oceania',
  'central-america-n-caribbean', 'central-asia',
  'east-n-southeast-asia', 'europe', 'middle-east',
  'north-america', 'oceans', 'south-america', 'south-asia', 'world'
];

function extract(value: unknown): string | null {
  if (typeof value === 'string') {
    return value.replace(/<br\s*\/?>/gi, ' ')
      .replace(/<[^>]*>/g, '')
      .replace(/&amp;/gi, '&')
      .replace(/&nbsp;/gi, ' ')
      .replace(/\s+/g, ' ').trim() || null;
  }
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
  const object = value as Document;
  if (typeof object.text === 'string') return extract(object.text);
  const values = Object.entries(object).filter(([k]) => k !== 'note')
    .map(([key, part]) => {
      const text = extract(part);
      return text ? key + ': ' + text : '';
    }).filter(Boolean);
  return values.length ? values.join(' · ') : null;
}

function field(data: unknown, ...keys: string[]): string | null {
  let value: unknown = data;
  for (const key of keys) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
    const found = Object.entries(value as Document)
      .find(([label]) => label.trim().toLowerCase() === key.toLowerCase());
    if (!found) return null;
    value = found[1];
  }
  return extract(value);
}

function candidates(gec: string, region: string): string[] {
  const first: string[] = [];
  if (gec === 'xx') first.push('world');
  if (['xq', 'zh', 'xo', 'zn', 'oo'].includes(gec)) first.push('oceans');
  if (gec === 'ay') first.push('antarctica');
  if (['gz', 'we'].includes(gec)) first.push('middle-east');
  if (['pf', 'pg'].includes(gec)) first.push('east-n-southeast-asia');
  if (gec === 'ee') first.push('europe');
  if (region === 'Africa') first.push('africa');
  if (region === 'Europe') first.push('europe');
  if (region === 'Oceania') first.push('australia-oceania');
  if (region === 'Americas') first.push('north-america', 'central-america-n-caribbean', 'south-america');
  if (region === 'Asia') first.push('east-n-southeast-asia', 'middle-east', 'central-asia', 'south-asia');
  return [...new Set([...first, ...folders])];
}

async function fetchArchive(folder: string, gec: string): Promise<ArchivedFile> {
  const rawURL = 'https://raw.githubusercontent.com/factbook/factbook.json/' +
    ARCHIVE_REVISION + '/' + folder + '/' + gec + '.json';
  const response = await fetch(rawURL, { signal: AbortSignal.timeout(7000) });
  if (!response.ok) throw new Error('Not found');
  const raw = await response.text();
  const data = JSON.parse(raw) as Document;
  if (!data.Introduction && !data.Geography) throw new Error('Invalid archive schema');
  return {
    data,
    url: 'https://github.com/factbook/factbook.json/blob/' + ARCHIVE_REVISION +
      '/' + folder + '/' + gec + '.json',
    hash: createHash('sha256').update(raw).digest('hex'),
  };
}

export async function readFactbook(code: string, region: string) {
  const entry = ARCHIVE_ENTITIES.find(x => x.code === code.toUpperCase());
  if (!entry) return null;
  const existing = cache.get(entry.code);
  if (existing && Date.now() < existing.validUntil) return existing.value;
  const dirs = candidates(entry.gec, region);
  let file: ArchivedFile | null = null;
  try {
    file = await Promise.any(dirs.slice(0, 4).map(dir => fetchArchive(dir, entry.gec)));
  } catch {
    try {
      file = await Promise.any(dirs.slice(4).map(dir => fetchArchive(dir, entry.gec)));
    } catch {
      file = null;
    }
  }
  if (!file) {
    const missing = {
      status: 'archive_unavailable', code: entry.code,
      reason: 'Pinned archive record is unavailable. No historical values have been substituted.',
    };
    cache.set(entry.code, { value: missing, validUntil: Date.now() + 60000 });
    return missing;
  }
  const d = file.data;
  const fields = {
    background: field(d, 'Introduction', 'Background'),
    location: field(d, 'Geography', 'Location'),
    area: field(d, 'Geography', 'Area', 'total'),
    climate: field(d, 'Geography', 'Climate'),
    terrain: field(d, 'Geography', 'Terrain'),
    resources: field(d, 'Geography', 'Natural resources'),
    population: field(d, 'People and Society', 'Population'),
    languages: field(d, 'People and Society', 'Languages'),
    government: field(d, 'Government', 'Government type'),
    capital: field(d, 'Government', 'Capital'),
    economy: field(d, 'Economy', 'Economic overview'),
    industries: field(d, 'Economy', 'Industries'),
    electricity: field(d, 'Energy', 'Electricity access'),
    military: field(d, 'Military and Security', 'Military and security forces'),
    expenditure: field(d, 'Military and Security', 'Military expenditures'),
    transportation: field(d, 'Transportation', 'Ports and terminals'),
    disputes: field(d, 'Transnational Issues', 'Disputes - international'),
  };
  const result = {
    status: 'available',
    code: entry.code, country: entry.name, gec: entry.gec.toUpperCase(),
    asOf: ARCHIVE_BASELINE, fields, sourceUrl: file.url,
    sha256: file.hash, sourceRevision: ARCHIVE_REVISION,
    warning: 'Historical Factbook reference; not current geopolitical, military or economic intelligence.',
  };
  cache.set(entry.code, { value: result, validUntil: Date.now() + 86400000 });
  return result;
}
