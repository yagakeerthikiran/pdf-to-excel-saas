import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';

const ROOT = process.cwd();
const FRONTEND = path.join(ROOT, 'frontend');
const ERR=[], WARN=[];
const exists = p => fs.existsSync(p);
const read = p => fs.readFileSync(p,'utf8');
const walk = (d, out=[]) => { for (const e of fs.readdirSync(d,{withFileTypes:true})) { const p=path.join(d,e.name); if (e.isDirectory()) walk(p,out); else out.push(p); } return out; };

const err=(f,m)=>ERR.push(`${f}: ${m}`);
const warn=(f,m)=>WARN.push(`${f}: ${m}`);

// --- Config checks ---
if (!exists(path.join(FRONTEND,'postcss.config.js')))
  err('frontend/postcss.config.js','missing PostCSS config');
if (!exists(path.join(FRONTEND,'tailwind.config.ts')) && !exists(path.join(FRONTEND,'tailwind.config.js')))
  err('frontend/tailwind.config.(ts|js)','missing Tailwind config');

const globals = path.join(FRONTEND,'app','globals.css');
if (exists(globals)) {
  const css = read(globals);
  for (const l of ['@tailwind base;','@tailwind components;','@tailwind utilities;']) {
    if (!css.includes(l)) warn('frontend/app/globals.css',`missing "${l}"`);
  }
} else {
  warn('frontend/app/globals.css','missing (not fatal)');
}

const nextCfg = path.join(FRONTEND,'next.config.js');
if (exists(nextCfg) && !/output\s*:\s*["']standalone["']/.test(read(nextCfg)))
  warn('frontend/next.config.js',"consider output: 'standalone'");

// Lockfile sanity
try { execSync('npm ci --ignore-scripts --legacy-peer-deps --dry-run',{cwd:FRONTEND,stdio:'ignore'}); }
catch { err('frontend/package-lock.json','lockfile out of sync with package.json'); }

// --- Source checks ---
const appDir = path.join(FRONTEND,'app');
const files = exists(appDir) ? walk(appDir).filter(p=>p.endsWith('.ts')||p.endsWith('.tsx')) : [];
const stripeAllowed = path.normalize('frontend/app/api/stripe/create-checkout/route.ts');

for (const f of files) {
  const rel = path.relative(ROOT,f).replace(/\\/g,'/');
  const src = read(f);

  // Client directive
  if (src.includes("'use client'") || src.includes('"use client"')) {
    if (!/^\s*['"]use client['"]/.test(src))
      err(rel, `"use client" must be the first statement (wrap with server page).`);
    if (/export\s+const\s+(runtime|dynamic)\s*=/.test(src))
      err(rel, `client component exporting runtime/dynamic (move to server wrapper).`);
    if (/from\s+['"]@\/lib\/supabase\/server['"]/.test(src))
      err(rel, `client component importing server Supabase; use '@/lib/supabase/client'.`);
  }

  // API route using client supabase
  if (rel.includes('/app/api/') && /from\s+['"]@\/lib\/supabase\/client['"]/.test(src))
    err(rel, `API route imports client Supabase; use server client.`);

  // Stripe constructor outside approved route
  if (/new\s+Stripe\s*\(/.test(src) && path.normalize(rel)!==path.normalize(stripeAllowed))
    err(rel, `top-level "new Stripe()" detected; use lazy getter inside Stripe route.`);
}

// Report
if (WARN.length) {
  console.log('Preflight warnings:');
  for (const w of WARN) console.log('  - ' + w);
  console.log();
}
if (ERR.length)  {
  console.error('Preflight failures:');
  for (const e of ERR) console.error('  - ' + e);
  process.exit(1);
}
console.log(' Preflight passed.');
