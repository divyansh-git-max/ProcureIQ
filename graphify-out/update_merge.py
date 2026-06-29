import json, glob, os
from pathlib import Path
from graphify.cache import save_semantic_cache

# Merge chunk files
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
print(f'Merged {len(chunks)} chunks: {len(all_nodes)} nodes, {len(all_edges)} edges')

# Save to cache
saved = save_semantic_cache(all_nodes, all_edges, all_hyperedges, root='f:/ProcureIQ-v0/procureIQ-v0')
print(f'Cached {saved} files')

# Merge cached + new
cached_path = Path('graphify-out/.graphify_cached.json')
cached = json.loads(cached_path.read_text(encoding='utf-8')) if cached_path.exists() else {'nodes':[],'edges':[],'hyperedges':[]}
new = json.loads(Path('graphify-out/.graphify_semantic_new.json').read_text(encoding='utf-8'))
all_nodes_f = cached['nodes'] + new.get('nodes', [])
all_edges_f = cached['edges'] + new.get('edges', [])
all_hyperedges_f = cached.get('hyperedges', []) + new.get('hyperedges', [])
seen = set()
deduped = []
for n in all_nodes_f:
    if n['id'] not in seen:
        seen.add(n['id'])
        deduped.append(n)

merged = {'nodes': deduped, 'edges': all_edges_f, 'hyperedges': all_hyperedges_f,
          'input_tokens': new.get('input_tokens', 0), 'output_tokens': new.get('output_tokens', 0)}
Path('graphify-out/.graphify_semantic.json').write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding='utf-8')
print(f'Semantic final: {len(deduped)} nodes, {len(all_edges_f)} edges')

# Merge AST + semantic into extract
ast = json.loads(Path('graphify-out/.graphify_ast.json').read_text(encoding='utf-8'))
sem = merged
seen2 = {n['id'] for n in ast['nodes']}
merged_nodes = list(ast['nodes'])
for n in sem['nodes']:
    if n['id'] not in seen2:
        merged_nodes.append(n)
        seen2.add(n['id'])
merged_edges = ast['edges'] + sem['edges']
merged_hyperedges = sem.get('hyperedges', [])
extract = {'nodes': merged_nodes, 'edges': merged_edges, 'hyperedges': merged_hyperedges,
           'input_tokens': sem.get('input_tokens', 0), 'output_tokens': sem.get('output_tokens', 0)}
Path('graphify-out/.graphify_extract.json').write_text(json.dumps(extract, indent=2, ensure_ascii=False), encoding='utf-8')
print(f'Extract: {len(merged_nodes)} nodes, {len(merged_edges)} edges')

# Cleanup temp
for f in ['graphify-out/.graphify_cached.json', 'graphify-out/.graphify_uncached.txt', 'graphify-out/.graphify_semantic_new.json', 'graphify-out/.graphify_semantic.json', 'graphify-out/.graphify_ast.json']:
    try: os.remove(f)
    except: pass
for c in chunks:
    try: os.remove(c)
    except: pass
print('Temp files cleaned.')
