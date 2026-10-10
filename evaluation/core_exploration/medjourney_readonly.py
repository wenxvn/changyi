"""Local read-only source comparison; no raw data persistence or model fitting."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent / 'results/medjourney-readonly-v1'
SOURCE = Path(__file__).resolve().parent / 'results/medjourney-dr-structure-review-v1.json'
PREFIX = "你是一名医生，请给出以下主诉对应的科室，直接输出科室，不用给出解释或任何文本描述，多个科室用'，'分割。"
ALIASES = {'普外科': '普通外科', '耳鼻喉科': '耳鼻咽喉科', '急诊科': '急诊医学科', '小儿内科': '儿内科'}
STATUSES = {'ROUTINE', 'URGENT', 'EMERGENCY', 'INSUFFICIENT_INFORMATION'}


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def source_cases(raw, expected_sha):
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError('Pinned source changed')
    rows = [json.loads(line) for line in raw.decode('utf-8-sig').splitlines() if line.strip()]
    if len(rows) != 500:
        raise ValueError('Full source denominator must be 500')
    cases = []
    for n, row in enumerate(rows):
        if set(row) != {'prompt', 'target', 'keyentity'} or not all(isinstance(v, str) for v in row.values()):
            raise ValueError('Unexpected DR schema')
        if not row['prompt'].startswith(PREFIX):
            raise ValueError('Unknown instruction boundary')
        body = row['prompt'][len(PREFIX):]
        complaint, sep, _ = body.partition('&&')
        labels = [v.strip() for v in re.split('[，,、;；]', row['target']) if v.strip()]
        if not complaint.strip() or not labels:
            raise ValueError('Empty source input or label')
        cases.append({'case_id': f'DR{n:03}', 'source_body': body, 'complaint_only': complaint,
                      'labels': labels, 'group': digest(complaint), 'has_suffix': bool(sep),
                      'source_prompt_sha256': digest(row['prompt']), 'target_sha256': digest(row['target'])})
    return cases


def write_new(path, value):
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)


def summary(rows):
    total = len(rows)
    routed = sum(r['routed'] for r in rows)
    groups = {}
    for row in rows:
        groups.setdefault(row['group'], []).append(row)
    return {'rows': total, 'input_groups': len(groups),
            'statuses': dict(Counter(r['status'] for r in rows)),
            'api_errors': sum(not r['api_valid'] for r in rows),
            'ordinary_department_routes': routed,
            'coverage_full_denominator': routed / total if total else None,
            'strict_source_agreement': sum(r['strict_correct'] for r in rows) / total if total else None,
            'alias_agreement_full_denominator': sum(r['alias_correct'] for r in rows) / total if total else None,
            'alias_agreement_retained': sum(r['alias_correct'] for r in rows) / routed if routed else None,
            'group_weighted_alias_agreement': sum(sum(r['alias_correct'] for r in g) / len(g) for g in groups.values()) / len(groups) if groups else None,
            'no_accepted_label_in_directory': sum(not r['label_in_directory'] for r in rows)}


def evaluate(cases, view, predict, directory):
    rows = []
    for case in cases:
        result = predict(case[view])
        valid = isinstance(result, dict) and isinstance(result.get('triage_status'), str) and result['triage_status'] in STATUSES
        status = result.get('triage_status') if valid else None
        dept = result.get('matched_department') if valid else None
        routed = valid and status in {'ROUTINE', 'URGENT'} and isinstance(dept, str) and bool(dept)
        labels = {ALIASES.get(x, x) for x in case['labels']}
        rows.append({'case_id': case['case_id'], 'group': case['group'], 'has_suffix': case['has_suffix'],
                     'input_sha256': digest(case[view]), 'source_prompt_sha256': case['source_prompt_sha256'],
                     'target_sha256': case['target_sha256'], 'api_valid': valid, 'status': status,
                     'matched_department': dept, 'routed': bool(routed),
                     'strict_correct': bool(routed and dept in case['labels']),
                     'alias_correct': bool(routed and dept in labels),
                     'label_in_directory': bool(labels.intersection(directory))})
    return {'view': view, 'full': summary(rows),
            'without_suffix': summary([r for r in rows if not r['has_suffix']]),
            'with_suffix': summary([r for r in rows if r['has_suffix']]), 'rows': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['freeze', 'evaluate'])
    parser.add_argument('--run-id')
    args = parser.parse_args()
    if args.run_id and (args.mode != 'evaluate' or not re.fullmatch(r'development-[a-z0-9_-]{1,48}', args.run_id)):
        parser.error('run-id is only for an explicitly named development recheck')
    meta = json.loads(SOURCE.read_text(encoding='utf-8'))
    raw = urlopen(meta['source_url'], timeout=30).read()
    cases = source_cases(raw, meta['source_sha256'])
    if len({c['group'] for c in cases}) != 499 or sum(c['has_suffix'] for c in cases) != 131:
        raise ValueError('Source group/suffix identity changed')
    import app
    from backend.app import composition
    from .versioned_challenge import identity
    directory = sorted({d['department'] for d in composition.REAL_DOCTORS if isinstance(d.get('department'), str)})
    protocol = {'source_sha256': meta['source_sha256'], 'aliases': ALIASES, 'directory_names': directory,
                'source_rows': 500, 'complaint_groups': 499, 'suffix_rows': 131,
                'views': ['source_body', 'complaint_only'], 'source_license': meta['source_license'],
                'analysis_basis': meta['analysis_basis'], 'new_fits': 0, 'clinical_validation': False,
                'scope': 'local_source_benchmark_comparison_not_training_or_redistribution',
                'development_exposure': 'source_preflight_exposed_no_predictions_before_protocol'}
    ROOT.mkdir(exist_ok=True)
    if args.mode == 'freeze':
        write_new(ROOT / 'protocol.json', protocol)
        print(json.dumps({k:v for k,v in protocol.items() if k != 'directory_names'}, ensure_ascii=True))
        return
    frozen_raw = (ROOT / 'protocol.json').read_bytes()
    if json.loads(frozen_raw) != protocol:
        raise ValueError('Frozen input/mapping/directory protocol changed')
    path = ROOT / ((args.run_id + '.json') if args.run_id else 'first-source-comparison.json')
    if path.exists():
        raise ValueError('Never overwrite first source comparison')
    before = identity()
    client = app.app.test_client()
    def predict(text):
        response = client.post('/api/v1/triage', json={'condition': text})
        payload = response.get_json(silent=True)
        return payload.get('data') if response.status_code == 200 and isinstance(payload, dict) else None
    results = [evaluate(cases, view, predict, set(directory)) for view in protocol['views']]
    if identity() != before:
        raise ValueError('Runtime/research identity changed during evaluation')
    report = {'protocol_sha256': hashlib.sha256(frozen_raw).hexdigest(), 'identity': before,
              'evaluation_exposure': 'used_for_development' if args.run_id else protocol['development_exposure'],
              'source_metadata': meta, 'new_fits': 0, 'clinical_validation': False,
              'risk_labels': None, 'calibration_metrics': None,
              'raw_inputs_targets_keyentities_persisted': False,
              'source_suffix_label_transfer_not_certified': True, 'results': results}
    write_new(path, report)
    print(json.dumps({r['view']:r['full'] for r in results}, ensure_ascii=True))


if __name__ == '__main__':
    main()
