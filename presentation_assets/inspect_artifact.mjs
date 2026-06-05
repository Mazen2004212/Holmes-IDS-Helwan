import * as m from 'file:///C:/Users/moham/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
console.log('PresentationFile', Object.getOwnPropertyNames(m.PresentationFile));
console.log('Presentation proto', Object.getOwnPropertyNames(m.Presentation?.prototype || {}));
console.log('Slide?', m.Presentation.create ? 'has create' : 'no');
console.log('Blob?', Object.keys(m).filter(k=>k.toLowerCase().includes('blob')).join(','));
