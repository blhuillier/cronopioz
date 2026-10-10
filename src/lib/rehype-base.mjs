/**
 * Prefix root-relative href/src attributes in Markdown content with Astro's base path,
 * so "/images/…" and "/projects/…" also work when the site is served under /<repo>/.
 * Handles both parsed elements and raw HTML nodes (project bodies are mostly raw HTML).
 */
export default function rehypeBase({ base = '/' } = {}) {
  const prefix = base.replace(/\/$/, '');
  const fix = (v) =>
    typeof v === 'string' && v.startsWith('/') && !v.startsWith('//') && !v.startsWith(prefix + '/') ? prefix + v : v;
  const rawRe = /\b(href|src)=(["'])(\/(?!\/)[^"']*)\2/g;
  return (tree) => {
    if (!prefix) return;
    const walk = (node) => {
      if (node.type === 'element' && node.properties) {
        for (const key of ['href', 'src']) node.properties[key] = fix(node.properties[key]);
      } else if (node.type === 'raw' && typeof node.value === 'string') {
        node.value = node.value.replace(rawRe, (m, attr, q, url) => `${attr}=${q}${fix(url)}${q}`);
      }
      if (node.children) node.children.forEach(walk);
    };
    walk(tree);
  };
}
