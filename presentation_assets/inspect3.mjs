import * as m from 'file:///C:/Users/moham/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const p=m.Presentation.create({slideSize:{width:1920,height:1080}});
const s=p.slides.add();
console.log('slide proto', Object.getOwnPropertyNames(Object.getPrototypeOf(s)));
console.log('slide export', s.export?.toString().slice(0,600));
