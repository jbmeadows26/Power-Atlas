import { defineConfig, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath } from 'node:url';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve, dirname, relative } from 'node:path';

// Keep the full dashboard stylesheet in the same response as the HTML.
// A stale/missing fingerprinted CSS file must never expose raw HTML on iOS.
function inlineDashboardStyles():Plugin {
  let outDir:string;
  return {
    name:'inline-dashboard-styles',
    apply:'build',
    enforce:'post',
    configResolved(config){outDir=resolve(config.root,config.build.outDir);},
    closeBundle(){
      const htmlPath=resolve(outDir,'index.html');
      let html=readFileSync(htmlPath,'utf8');
      let count=0;
      html=html.replace(/<link\b[^>]*\brel=["']stylesheet["'][^>]*>/gi,tag=>{
        const href=tag.match(/\bhref=["']([^"']+)["']/i)?.[1];
        if(!href||/^(?:https?:|\/\/)/i.test(href))return tag;
        const local=href.startsWith('/')?href.slice(href.lastIndexOf('/assets/')):href;
        const cssPath=resolve(outDir,local.replace(/^\//,''));
        let css=readFileSync(cssPath,'utf8');
        // Fonts are optional; their external stylesheet cannot block dashboard layout.
        css=css.replace(/@import\s+(?:url\(\s*)?["']https:\/\/fonts\.googleapis\.com\/[^"']+["']\s*\)?\s*;/gi,'');
        if(/@import\b/i.test(css))throw Error('Unexpected CSS import: dashboard must be self-contained');
        css=css.replace(/url\(\s*(["']?)([^"'()]+)\1\s*\)/gi,(all,q,url)=>{
          if(/^(?:[a-z]+:|\/|#)/i.test(url))return all;
          return 'url("'+relative(outDir,resolve(dirname(cssPath),url)).replaceAll('\\','/')+'")';
        });
        if(/<\/style/i.test(css))throw Error('Unexpected style closing tag in CSS');
        count++;
        return '<style data-ea-dashboard-css="inline">'+css+'</style>';
      });
      if(count!==1||!html.includes('.shell{')||!html.includes('.ea-mobile-primary'))throw Error('Dashboard stylesheet missing from HTML');
      html=html.replace('</head>','<meta name="ea-release" content="'+(process.env.GITHUB_SHA||'local-build')+'"></head>');
      writeFileSync(htmlPath,html);
    }
  };
}

export default defineConfig({
  plugins: [react(),inlineDashboardStyles()],
  resolve: { alias: { '@appdeploy/client': fileURLToPath(new URL('./src/lib/api.ts', import.meta.url)) } },
  base: '/',
  build: { outDir: 'dist', cssCodeSplit:false, cssTarget:'safari14', target: ['chrome87', 'edge88', 'firefox78', 'safari14'] },
});
