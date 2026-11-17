import { build } from 'esbuild';
await build({
  entryPoints: ['server/endpoint.ts'],
  outfile: 'api/index.js',
  bundle: true,
  platform: 'node',
  format: 'esm',
  target: 'node24',
  packages: 'external',
  minify: false,
  sourcemap: false,
  logLevel: 'info',
});
