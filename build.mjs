import { mkdir, copyFile } from 'node:fs/promises';
await mkdir('dist/images', { recursive: true });
for (const file of ['index.html', 'app.js', 'config.json']) await copyFile(file, `dist/${file}`);
for (const file of ['oum-malak-original.jpg', 'oum-malak-watermark.jpg']) await copyFile(`images/${file}`, `dist/images/${file}`);
console.log('Oum Malak website and photos ready for Cloudflare Workers.');
