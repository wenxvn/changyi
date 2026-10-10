import pytest
import app


@pytest.mark.parametrize('text', ['年龄儿童，性别男', '我25岁，女性', '宝宝2个月大，男孩', '新生儿', '我今年60岁，男性'])
def test_demographic_information_does_not_create_disease_or_ordinary_booking(text):
    d = app.app.test_client().post('/api/v1/triage', json={'condition': text}).get_json()['data']
    assert d['triage_status'] == 'INSUFFICIENT_INFORMATION'
    assert d['matched_department'] is None
    assert d['triage']['disease_candidates'] == []
    assert d['triage']['symptom_tags'] == []
    resources = app.app.test_client().post('/api/v1/recommendations', json={'condition': text}).get_json()['data']
    assert resources['recommended_doctors'] == []


@pytest.mark.parametrize('text', ['儿童咳嗽', '我25岁，胸痛伴呼吸困难', '宝宝接种疫苗', '女性体检', '小孩皮肤科挂号'])
def test_symptoms_and_care_purposes_are_not_discarded_as_demographics(text):
    from backend.app.domain.triage.input_adequacy import demographic_only_description
    assert not demographic_only_description(text)


def test_real_child_emergency_still_precedes_information_gate():
    d = app.app.test_client().post('/api/v1/triage', json={'condition': '儿童现在呼吸困难'}).get_json()['data']
    assert d['triage_status'] == 'EMERGENCY'
