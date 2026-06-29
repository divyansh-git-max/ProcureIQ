import json, glob
from pathlib import Path
from graphify.cache import save_semantic_cache

# Merge chunk files into semantic_new
chunks = sorted(glob.glob('graphify-out/.graphify_chunk_*.json'))
all_nodes, all_edges, all_hyperedges = [], [], []
total_in, total_out = 0, 0
for c in chunks:
    d = json.loads(Path(c).read_text(encoding='utf-8'))
    all_nodes += d.get('nodes', [])
    all_edges += d.get('edges', [])
    all_hyperedges += d.get('hyperedges', [])
    total_in += d.get('input_tokens', 0)
    total_out += d.get('output_tokens', 0)

Path('graphify-out/.graphify_semantic_new.json').write_text(json.dumps({
    'nodes': all_nodes, 'edges': all_edges, 'hyperedges': all_hyperedges,
    'input_tokens': total_in, 'output_tokens': total_out,
}, indent=2, ensure_ascii=False), encoding='utf-8')
print(f'Merged {len(chunks)} chunks: {total_in} in / {total_out} out tokens, {len(all_nodes)} nodes, {len(all_edges)} edges')

# Save to cache
saved = save_semantic_cache(all_nodes, all_edges, all_hyperedges, root='f:/ProcureIQ-v0/procureIQ-v0')
print(f'Cached {saved} files')

# Merge cached + new into final semantic
cached_path = Path('graphify-out/.graphify_cached.json')
cached = json.loads(cached_path.read_text(encoding='utf-8')) if cached_path.exists() else {'nodes':[],'edges':[],'hyperedges':[]}
new = json.loads(Path('graphify-out/.graphify_semantic_new.json').read_text(encoding='utf-8'))

all_nodes_final = cached['nodes'] + new.get('nodes', [])
all_edges_final = cached['edges'] + new.get('edges', [])
all_hyperedges_final = cached.get('hyperedges', []) + new.get('hyperedges', [])
seen = set()
deduped = []
for n in all_nodes_final:
    if n['id'] not in seen:
        seen.add(n['id'])
        deduped.append(n)

merged = {
    'nodes': deduped,
    'edges': all_edges_final,
    'hyperedges': all_hyperedges_final,
    'input_tokens': new.get('input_tokens', 0),
    'output_tokens': new.get('output_tokens', 0),
}
Path('graphify-out/.graphify_semantic.json').write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding='utf-8')
print(f'Semantic final: {len(deduped)} nodes, {len(all_edges_final)} edges ({len(cached["nodes"])} from cache, {len(new.get("nodes",[]))} new)')

# Cleanup
import os
for f in ['graphify-out/.graphify_cached.json', 'graphify-out/.graphify_uncached.txt', 'graphify-out/.graphify_semantic_new.json']:
    try: os.remove(f)
    except: pass
for c in chunks:
    try: os.remove(c)
    except: pass
print('Temp files cleaned up')
