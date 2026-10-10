import pytest
import app


@pytest.mark.parametrize('text,expected', [
    ('本周整个左臂有过两次麻木，每次15分钟，随后完全恢复', 'URGENT'),
    ('昨天整条右手臂麻木，随后恢复正常', 'URGENT'),
    ('我现在整个左手臂突然麻木，没有恢复', 'EMERGENCY'),
    ('今天整个右胳膊突然麻木，仍然没有恢复', 'EMERGENCY'),
    ('本周整个左臂麻木后完全恢复，今天又突然麻木', 'EMERGENCY'),
])
def test_recent_whole_unilateral_arm_report_is_not_routine(text, expected):
    d = app.app.test_client().post('/api/v1/triage', json={'condition': text}).get_json()['data']
    assert d['triage_status'] == expected
    assert '手臂' in d['triage']['matched_rule']
    assert d['matched_department'] == '急诊医学科'


@pytest.mark.parametrize('text', [
    '去年整个左臂麻木，随后完全恢复',
    '昨天没有整个右手臂麻木，随后恢复正常',
    '如果今天整个右手臂突然麻木怎么办',
    '不确定今天整个左臂是否突然麻木',
    '今天左手指麻木，随后恢复正常',
    '今天两个手臂麻木，随后恢复正常',
    '本周整个左臂疼痛，右手指麻木，随后恢复正常',
    '我今天整个左臂疼痛，我爸手臂麻木，随后恢复正常',
    '整个左臂以前麻木，今天已经恢复正常',
    '我现在整个右手臂突然疼痛，没有麻木',
    '今天右手指麻木，整个左臂疼痛，随后恢复正常',
])
def test_other_sites_people_negation_or_remote_history_do_not_create_this_rule(text):
    from backend.app.domain.triage.recent_neurological_assessment import recent_arm_assessment
    assert recent_arm_assessment(text) is None


def test_resolved_recent_report_still_blocks_ordinary_expert_booking():
    d = app.app.test_client().post('/api/v1/recommendations', json={
        'condition': '本周整个左臂麻木15分钟后完全恢复', 'expert_preference': 'must_expert',
    }).get_json()['data']
    assert d['resource_strategy']['code'] == 'urgent_assessment'
    assert d['recommended_doctors'] == []
    assert d['weights_used'] == {}


def test_other_prior_recovery_cannot_downgrade_current_unresolved_emergency():
    d = app.app.test_client().post('/api/v1/triage', json={
        'condition': '右手指已经完全恢复，现在整个左臂突然麻木，没有恢复',
    }).get_json()['data']
    assert d['triage_status'] == 'EMERGENCY'
