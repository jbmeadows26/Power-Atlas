import {readFileSync} from 'node:fs';
import {summarizeAcceptance} from '../site/development-control/acceptance-rules.mjs';
const input=JSON.parse(readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(summarizeAcceptance(input.registry,input.releaseContext)));
