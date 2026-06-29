import json, os, glob
from pathlib import Path
from datetime import datetime, timezone
from graphify.detect import save_manifest

# Save manifest for --update
detect = json.loads(Path('graphify-out/.graphify_detect.json').read_text(encoding='utf-8'))
save_manifest(detect.get('all_files') or detect['files'], root='f:/ProcureIQ-v0/procureIQ-v0')

# Update cumulative cost tracker
extract = json.loads(Path('graphify-out/.graphify_extract.json').read_text(encoding='utf-8'))
input_tok = extract.get('input_tokens', 0)
output_tok = extract.get('output_tokens', 0)

cost_path = Path('graphify-out/cost.json')
if cost_path.exists():
    cost = json.loads(cost_path.read_text(encoding='utf-8'))
else:
    cost = {'runs': [], 'total_input_tokens': 0, 'total_output_tokens': 0}

cost['runs'].append({
    'date': datetime.now(timezone.utc).isoformat(),
    'input_tokens': input_tok,
    'output_tokens': output_tok,
    'files': detect.get('total_files', 0),
})
cost['total_input_tokens'] += input_tok
cost['total_output_tokens'] += output_tok
cost_path.write_text(json.dumps(cost, indent=2, ensure_ascii=False), encoding='utf-8')

print(f'This run: {input_tok:,} input tokens, {output_tok:,} output tokens')
print(f'All time: {cost["total_input_tokens"]:,} input, {cost["total_output_tokens"]:,} output ({len(cost["runs"])} runs)')

# Cleanup temp files
for f in [
    'graphify-out/.graphify_detect.json',
    'graphify-out/.graphify_extract.json',
    'graphify-out/.graphify_ast.json',
    'graphify-out/.graphify_semantic.json',
    'graphify-out/.graphify_analysis.json',
]:
    try: os.remove(f)
    except: pass

for c in glob.glob('graphify-out/.graphify_chunk_*.json'):
    try: os.remove(c)
    except: pass

try: os.remove('graphify-out/.needs_update')
except: pass

print('Cleanup complete.')
print('\nFinal outputs in graphify-out/:')
for f in sorted(Path('graphify-out').iterdir()):
    if not f.name.startswith('.') and f.is_file():
        print(' ', f.name)
