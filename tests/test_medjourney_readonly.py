import hashlib
import json
import pytest
from evaluation.core_exploration.medjourney_readonly import PREFIX, ALIASES, source_cases, evaluate, digest


def raw_rows(count=500):
    rows = [{'prompt': PREFIX + f'complaint {i}&&annotation', 'target': '科室甲', 'keyentity': 'not input'} for i in range(count)]
    return ('\n'.join(json.dumps(r, ensure_ascii=False) for r in rows)).encode()


def test_reader_strips_only_registered_instruction_and_keeps_source_suffix_separate():
    raw = raw_rows()
    rows = source_cases(raw, hashlib.sha256(raw).hexdigest())
    assert len(rows) == 500
    assert rows[0]['source_body'] == 'complaint 0&&annotation'
    assert rows[0]['complaint_only'] == 'complaint 0'
    assert not any('keyentity' in r or 'target' in r or 'prompt' in r for r in rows)
    assert rows[0]['target_sha256'] == digest('科室甲')


def test_pinned_source_and_full_denominator_are_verified_before_requests():
    raw = raw_rows()
    with pytest.raises(ValueError, match='Pinned'):
        source_cases(raw, 'wrong')
    raw = raw_rows(499)
    with pytest.raises(ValueError, match='500'):
        source_cases(raw, hashlib.sha256(raw).hexdigest())


def test_unknown_role_instruction_is_not_silently_passed_to_serving_api():
    raw = raw_rows().replace(PREFIX.encode(), b'different instruction', 1)
    with pytest.raises(ValueError, match='boundary'):
        source_cases(raw, hashlib.sha256(raw).hexdigest())


def test_conservative_aliases_do_not_collapse_child_and_specialty_labels():
    assert ALIASES['急诊科'] == '急诊医学科'
    assert '小儿呼吸内科' not in ALIASES
    assert '牙周病科' not in ALIASES
    assert '脊柱外科' not in ALIASES


def cases():
    return [{'case_id': str(i), 'source_body': f'input {i}', 'complaint_only': f'input {i}',
             'labels': ['科室甲'], 'group': str(i), 'has_suffix': False,
             'source_prompt_sha256': 'fixture', 'target_sha256': 'fixture'} for i in range(4)]


def test_info_emergency_and_errors_remain_in_full_specialty_denominator():
    responses = iter([{'triage_status': 'ROUTINE', 'matched_department': '科室甲'},
                      {'triage_status': 'INSUFFICIENT_INFORMATION', 'matched_department': None},
                      {'triage_status': 'EMERGENCY', 'matched_department': '急诊医学科'}, None])
    received = []
    def predict(text):
        received.append(text)
        return next(responses)
    r = evaluate(cases(), 'source_body', predict, set())
    assert received == [f'input {i}' for i in range(4)]
    assert r['full']['rows'] == 4
    assert r['full']['api_errors'] == 1
    assert r['full']['coverage_full_denominator'] == .25
    assert r['full']['alias_agreement_full_denominator'] == .25
    assert r['full']['alias_agreement_retained'] == 1
    assert r['full']['no_accepted_label_in_directory'] == 4


def test_input_groups_are_weighted_without_unioning_gold_labels():
    c = cases()[:3]
    c[1]['group'] = c[0]['group']
    responses = iter([{'triage_status':'ROUTINE', 'matched_department':x} for x in ['科室甲','科室乙','科室甲']])
    r = evaluate(c, 'complaint_only', lambda _: next(responses), {'科室甲'})
    assert r['full']['input_groups'] == 2
    assert r['full']['alias_agreement_full_denominator'] == pytest.approx(2/3)
    assert r['full']['group_weighted_alias_agreement'] == .75


def test_malformed_api_status_counts_as_error_without_crashing():
    r = evaluate(cases(), 'source_body', lambda _: {'triage_status':[]}, set())
    assert r['full']['api_errors'] == 4
    assert r['full']['coverage_full_denominator'] == 0
    assert r['full']['alias_agreement_retained'] is None
