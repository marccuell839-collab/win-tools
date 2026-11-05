import { mkdir, copyFile } from 'node:fs/promises';
await mkdir('dist', { recursive: true });
for (const file of ['index.html', 'app.js', 'config.json']) await copyFile(file, `dist/${file}`);
console.log('Oum Malak static site prepared in dist/');
