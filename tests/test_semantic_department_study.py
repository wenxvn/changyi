import numpy as np
import pytest
from evaluation.core_exploration.semantic_department_study import measure


def cases():
    return [{'case_id':str(i),'group':str(i),'has_suffix':i==1,'labels':['乙科']} for i in range(3)]


def legacy():
    return {str(i):{'status':s} for i,s in enumerate(['ROUTINE','EMERGENCY','INSUFFICIENT_INFORMATION'])}


def test_retrieval_and_legacy_ordinary_scopes_are_reported_separately():
    result = measure(cases(), ['甲科','乙科','丙科'], np.array([[0,.9,.1]]*3), legacy())
    assert result['summary']['closed_set_label_matches'] == 3
    assert result['summary']['legacy_ordinary_scope_matches'] == 1
    assert result['summary']['full_rows'] == 3
    assert result['summary']['without_suffix_rows'] == 2


def test_zero_overlap_abstains_instead_of_assigning_first_label():
    result = measure(cases(), ['甲科','乙科','丙科'], np.zeros((3,3)), legacy())
    assert result['summary']['retrieval_abstentions'] == 3
    assert result['summary']['closed_set_label_matches'] == 0
    assert all(r['predicted_label'] is None for r in result['rows'])


@pytest.mark.parametrize('matrix',[np.zeros((2,3)),np.full((3,3),np.nan)])
def test_missing_rows_or_invalid_scores_cannot_shrink_denominator(matrix):
    with pytest.raises(ValueError):measure(cases(), ['甲科','乙科','丙科'], matrix, legacy())
