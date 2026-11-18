import { build } from 'esbuild';
await build({
  entryPoints: ['server/neon-function.ts'],
  outfile: 'neon-release/index.mjs',
  bundle: true,
  platform: 'node',
  format: 'esm',
  target: 'node24',
  packages: 'bundle',
  minify: false,
  sourcemap: false,
  logLevel: 'info',
});
