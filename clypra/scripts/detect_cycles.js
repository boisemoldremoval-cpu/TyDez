import fs from 'fs';
import path from 'path';

const SRC_DIR = path.resolve('src');
const TSCONFIG_PATH = path.resolve('tsconfig.json');

// Get all files recursively
function getFiles(dir) {
  let results = [];
  const list = fs.readdirSync(dir);
  list.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    if (stat && stat.isDirectory()) {
      results = results.concat(getFiles(filePath));
    } else if (filePath.endsWith('.ts') || filePath.endsWith('.tsx')) {
      results.push(filePath);
    }
  });
  return results;
}

// Resolve import path to absolute file path
function resolveImport(importPath, currentFileDir) {
  let resolvedPath = '';
  if (importPath.startsWith('@/')) {
    resolvedPath = path.join(SRC_DIR, importPath.slice(2));
  } else if (importPath.startsWith('.') || importPath.startsWith('..')) {
    resolvedPath = path.resolve(currentFileDir, importPath);
  } else {
    // External package
    return null;
  }

  // Check extensions
  const extensions = ['.ts', '.tsx', '/index.ts', '/index.tsx'];
  if (fs.existsSync(resolvedPath) && fs.statSync(resolvedPath).isFile()) {
    return resolvedPath;
  }
  for (const ext of extensions) {
    const p = resolvedPath + ext;
    if (fs.existsSync(p) && fs.statSync(p).isFile()) {
      return p;
    }
  }
  return null;
}

// Build dependency graph
const graph = {};
const files = getFiles(SRC_DIR);

files.forEach(file => {
  let content = fs.readFileSync(file, 'utf8');
  
  // Strip multi-line comments
  content = content.replace(/\/\*[\s\S]*?\*\//g, '');
  // Strip single-line comments
  content = content.replace(/\/\/.*$/gm, '');

  const dir = path.dirname(file);
  const imports = [];

  // Match import ... from '...'
  const importRegex = /from\s+['"]([^'"]+)['"]/g;
  let match;
  while ((match = importRegex.exec(content)) !== null) {
    imports.push(match[1]);
  }

  // Match import '...' (dynamic or side-effects)
  const sideEffectRegex = /import\s+['"]([^'"]+)['"]/g;
  while ((match = sideEffectRegex.exec(content)) !== null) {
    if (!imports.includes(match[1])) {
      imports.push(match[1]);
    }
  }

  const resolvedImports = imports
    .map(imp => resolveImport(imp, dir))
    .filter(Boolean);

  const relativeFile = path.relative(SRC_DIR, file);
  graph[relativeFile] = resolvedImports.map(imp => path.relative(SRC_DIR, imp));
});

// Find cycles in graph
const cycles = [];
const visited = {};
const recStack = {};

function dfs(node, pathStack = []) {
  visited[node] = true;
  recStack[node] = true;
  pathStack.push(node);

  const neighbors = graph[node] || [];
  for (const neighbor of neighbors) {
    if (!visited[neighbor]) {
      dfs(neighbor, pathStack);
    } else if (recStack[neighbor]) {
      // Cycle detected
      const cycleStartIndex = pathStack.indexOf(neighbor);
      if (cycleStartIndex !== -1) {
        const cycle = pathStack.slice(cycleStartIndex).concat(neighbor);
        cycles.push(cycle);
      }
    }
  }

  recStack[node] = false;
  pathStack.pop();
}

Object.keys(graph).forEach(node => {
  if (!visited[node]) {
    dfs(node, []);
  }
});

// Output results
console.log(JSON.stringify({
  totalFiles: files.length,
  cycleCount: cycles.length,
  cycles: cycles.map(c => c.join(' -> '))
}, null, 2));
