'use strict';
// Generates assets/icon.png (512), assets/icon.ico (Win), assets/icon.icns (Mac)
// Run via: npm run icons
const { createCanvas } = require('canvas');
const { imagesToIco }  = require('png-to-ico');
const fs = require('fs');
const path = require('path');
const assets = path.join(__dirname, '..', 'assets');

function drawIcon(size) {
  const canvas = createCanvas(size, size);
  const ctx    = canvas.getContext('2d');
  const r      = size * 0.16;

  ctx.beginPath();
  ctx.moveTo(r, 0); ctx.lineTo(size - r, 0);
  ctx.quadraticCurveTo(size, 0, size, r);
  ctx.lineTo(size, size - r);
  ctx.quadraticCurveTo(size, size, size - r, size);
  ctx.lineTo(r, size);
  ctx.quadraticCurveTo(0, size, 0, size - r);
  ctx.lineTo(0, r);
  ctx.quadraticCurveTo(0, 0, r, 0);
  ctx.closePath();

  const grad = ctx.createLinearGradient(0, 0, size, size);
  grad.addColorStop(0, '#0f172a'); grad.addColorStop(1, '#2563EB');
  ctx.fillStyle = grad; ctx.fill();

  ctx.font = (size * 0.55) + 'px serif';
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText('🚛', size / 2, size / 2);

  if (size >= 128) {
    ctx.fillStyle = 'rgba(255,255,255,0.8)';
    ctx.font = 'bold ' + Math.round(size * 0.14) + 'px sans-serif';
    ctx.fillText('PRO', size / 2, size - size * 0.15);
  }
  return canvas.toBuffer('image/png');
}

(async () => {
  // 512×512 main PNG
  const png512 = drawIcon(512);
  fs.writeFileSync(path.join(assets, 'icon.png'), png512);
  console.log('✓ assets/icon.png');

  // ICO: 16, 32, 48, 256
  const icoSizes  = [16, 32, 48, 256];
  const icoBuffers = icoSizes.map(drawIcon);

  // Build ICO manually (modern PNG-in-ICO, works on Vista+)
  let offset = 6 + icoSizes.length * 16;
  const offsets = icoBuffers.map(buf => { const o = offset; offset += buf.length; return o; });
  const hdr = Buffer.alloc(6);
  hdr.writeUInt16LE(0, 0); hdr.writeUInt16LE(1, 2); hdr.writeUInt16LE(icoSizes.length, 4);
  const dir = Buffer.concat(icoSizes.map((s, i) => {
    const d = Buffer.alloc(16);
    d.writeUInt8(s === 256 ? 0 : s, 0); d.writeUInt8(s === 256 ? 0 : s, 1);
    d.writeUInt8(0, 2); d.writeUInt8(0, 3);
    d.writeUInt16LE(1, 4); d.writeUInt16LE(32, 6);
    d.writeUInt32LE(icoBuffers[i].length, 8); d.writeUInt32LE(offsets[i], 12);
    return d;
  }));
  fs.writeFileSync(path.join(assets, 'icon.ico'), Buffer.concat([hdr, dir, ...icoBuffers]));
  console.log('✓ assets/icon.ico');

  // ICNS: ic09 = 512×512 PNG (macOS 10.5+)
  const totalLen = Buffer.alloc(4); totalLen.writeUInt32BE(8 + 8 + png512.length, 0);
  const blockLen = Buffer.alloc(4); blockLen.writeUInt32BE(8 + png512.length, 0);
  fs.writeFileSync(path.join(assets, 'icon.icns'),
    Buffer.concat([Buffer.from('icns'), totalLen, Buffer.from('ic09'), blockLen, png512]));
  console.log('✓ assets/icon.icns');
})();
