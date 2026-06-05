import * as m from 'file:///C:/Users/moham/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const p=m.Presentation.create({slideSize:{width:1920,height:1080}});
console.log('presentation keys', Object.keys(p));
console.log('slides keys', Object.keys(p.slides || {}));
console.log('slides proto', Object.getOwnPropertyNames(Object.getPrototypeOf(p.slides || {})));
console.log('export fn', p.export?.toString().slice(0,500));
console.log('save fn', p.save?.toString().slice(0,400));
console.log('inspect fn', p.inspect?.toString().slice(0,300));
