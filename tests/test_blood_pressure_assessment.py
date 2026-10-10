import pytest
import app


@pytest.mark.parametrize('text,expected', [
    ('我52岁，今天量血压发现很高，有轻微头痛', 'INSUFFICIENT_INFORMATION'),
    ('我45岁，现在血压190/120 mmHg，背痛', 'EMERGENCY'),
    ('我45岁，今天血压180/90 mmHg，没有胸痛或气短', 'URGENT'),
    ('我45岁，目前血压150/120毫米汞柱，没有头痛', 'URGENT'),
    ('我45岁，今天血压190/120 mmHg，没有背痛或麻木', 'URGENT'),
    ('我45岁，今天血压190/120', 'INSUFFICIENT_INFORMATION'),
    ('我45岁，现在血压120/190 mmHg', 'INSUFFICIENT_INFORMATION'),
    ('我45岁，现在血压很高，读数25/16 kPa', 'INSUFFICIENT_INFORMATION'),
    ('今天血压190/120 mmHg', 'INSUFFICIENT_INFORMATION'),
    ('我12岁，现在血压190/120 mmHg', 'INSUFFICIENT_INFORMATION'),
    ('我28岁，怀孕，目前血压190/120 mmHg', 'INSUFFICIENT_INFORMATION'),
    ('我45岁，现在血压190/120 mmHg，我爸背痛', 'INSUFFICIENT_INFORMATION'),
    ('我45岁，今天血压190/120 mmHg，昨天背痛', 'URGENT'),
    ('我45岁，现在血压190/120 mmHg，背痛已恢复正常', 'URGENT'),
    ('我45岁，今天血压190/120 mmHg，现在血压120/80 mmHg', 'INSUFFICIENT_INFORMATION'),
    ('我45岁，昨天。血压190/120 mmHg。今天。血压190/120 mmHg', 'URGENT'),
    ('我45岁，今天不确定是否血压190/120 mmHg', 'INSUFFICIENT_INFORMATION'),
    ('我45岁，现在血压190', 'INSUFFICIENT_INFORMATION'),
    ('我45岁，现在血压１９０／１２０ mmHg，没有背痛', 'URGENT'),
    ('我45岁，现在血压190/120 mmHg，现在血压190/120毫米汞柱', 'URGENT'),
])
def test_current_pressure_report_cannot_become_ordinary_booking(text, expected):
    d = app.app.test_client().post('/api/v1/triage', json={'condition': text}).get_json()['data']
    assert d['triage_status'] == expected
    if expected == 'INSUFFICIENT_INFORMATION':
        assert d['matched_department'] is None
    if expected == 'URGENT':
        d = app.app.test_client().post('/api/v1/recommendations', json={'condition': text, 'expert_preference': 'must_expert'}).get_json()['data']
        assert d['resource_strategy']['code'] == 'urgent_assessment'
        assert d['recommended_doctors'] == []


@pytest.mark.parametrize('text', [
    '我45岁，昨天血压190/120 mmHg',
    '我45岁，如果今天血压190/120 mmHg怎么办',
    '我45岁，今天没有测血压，血压很高吗',
    '我45岁，今天没有血压很高',
    '我45岁，今天体重190，心率120',
    '我45岁，现在血压120/80 mmHg',
    '我45岁，今天血压120/80 mmHg，昨天血压190/120 mmHg',
])
def test_noncurrent_denied_hypothetical_and_other_numbers_do_not_create_pressure_risk(text):
    from backend.app.domain.triage.blood_pressure_assessment import blood_pressure_assessment
    assert blood_pressure_assessment(text) is None


def test_generic_no_red_flags_does_not_invent_missing_reading():
    d = app.app.test_client().post('/api/v1/triage', json={
        'condition': '我52岁，今天量血压发现很高',
        'followup_answers': [{'question_id': 'red_flag_check', 'value': 'none'}],
    }).get_json()['data']
    assert d['triage_status'] == 'INSUFFICIENT_INFORMATION'
