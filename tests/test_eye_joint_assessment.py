import pytest
import app


@pytest.mark.parametrize('text', [
    '我现在左眼发红疼痛，非常怕光',
    '右眼红，视力模糊',
    '过去两天左眼发红、疼痛、非常怕光',
])
def test_red_eye_with_photophobia_or_vision_change_precedes_uncertainty(text):
    d = app.app.test_client().post('/api/v1/triage', json={'condition': text}).get_json()['data']
    assert d['triage_status'] == 'EMERGENCY'
    assert '红眼' in d['triage']['matched_rule']
    assert not d['disease_prediction']['predictions']


@pytest.mark.parametrize('text', [
    '右膝肿胀且非常疼，摸起来发热，几乎无法弯曲',
    '左膝肿胀疼痛，不能弯曲',
    '过去两天右膝肿胀、疼痛，局部发热',
])
def test_same_joint_acute_compound_needs_timely_assessment(text):
    d = app.app.test_client().post('/api/v1/triage', json={'condition': text}).get_json()['data']
    assert d['triage_status'] == 'URGENT'
    assert '关节' in d['triage']['matched_rule']
    d = app.app.test_client().post('/api/v1/recommendations', json={'condition': text, 'expert_preference': 'must_expert'}).get_json()['data']
    assert d['resource_strategy']['code'] == 'urgent_assessment'
    assert d['recommended_doctors'] == []


@pytest.mark.parametrize('text', [
    '没有左眼发红，视力模糊', '左眼发红，没有怕光或视力模糊',
    '以前左眼发红怕光，现在好了', '如果左眼发红怕光怎么办',
    '不确定左眼是否发红怕光', '左眼发红，右眼视力模糊',
    '我左眼发红，我妈视力模糊', '左眼发红，头部疼痛',
    '右膝肿胀，没有疼痛，局部发热', '没有右膝肿胀疼痛，不能弯曲',
    '以前右膝肿胀疼痛发热，现在好了', '如果右膝肿胀疼痛不能弯曲怎么办',
    '不确定右膝是否肿胀疼痛发热', '左膝肿胀，右膝疼痛发热',
    '我右膝肿胀，我爸右膝疼痛发热', '右膝肿胀疼痛，头部发热',
    '过去两天左眼发红怕光，已经好了',
    '过去两天右膝肿胀疼痛，局部发热，已恢复正常',
])
def test_no_new_compound_from_unconfirmed_or_separate_evidence(text):
    from backend.app.domain.triage.eye_joint_assessment import eye_emergency_assessment, joint_urgent_assessment
    assert eye_emergency_assessment(text) is None
    assert joint_urgent_assessment(text) is None
