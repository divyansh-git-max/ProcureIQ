import json
from graphify.extract import collect_files, extract
from graphify.cache import check_semantic_cache
from pathlib import Path

detect = json.loads(Path('graphify-out/.graphify_detect.json').read_text(encoding='utf-8'))

# AST extraction on changed code files
code_files = []
for f in detect.get('files', {}).get('code', []):
    p = Path(f)
    code_files.extend(collect_files(p) if p.is_dir() else [p])

if code_files:
    result = extract(code_files, cache_root=Path('f:/ProcureIQ-v0/procureIQ-v0'))
    Path('graphify-out/.graphify_ast.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print('AST:', len(result['nodes']), 'nodes,', len(result['edges']), 'edges')
else:
    Path('graphify-out/.graphify_ast.json').write_text(json.dumps({'nodes':[],'edges':[],'input_tokens':0,'output_tokens':0}, ensure_ascii=False), encoding='utf-8')
    print('No code files changed - empty AST')

# Cache check for doc/image files
all_non_code = [f for cat in ('document', 'paper', 'image') for f in detect['files'].get(cat, [])]
cached_nodes, cached_edges, cached_hyperedges, uncached = check_semantic_cache(all_non_code, root='f:/ProcureIQ-v0/procureIQ-v0')

if cached_nodes or cached_edges or cached_hyperedges:
    Path('graphify-out/.graphify_cached.json').write_text(json.dumps({'nodes': cached_nodes, 'edges': cached_edges, 'hyperedges': cached_hyperedges}, ensure_ascii=False), encoding='utf-8')
else:
    try:
        Path('graphify-out/.graphify_cached.json').unlink()
    except:
        pass

Path('graphify-out/.graphify_uncached.txt').write_text('\n'.join(uncached), encoding='utf-8')
print(f'Cache: {len(all_non_code)-len(uncached)} hits, {len(uncached)} need extraction')
for f in uncached:
    print(' ', f)
