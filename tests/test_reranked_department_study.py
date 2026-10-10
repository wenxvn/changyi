import numpy as np
import pytest
from evaluation.core_exploration.reranked_department_study import select_candidates,make_pairs


def test_candidate_order_is_stable_and_uses_scores_not_gold():
    scores=np.zeros((2,12));scores[:,8]=1
    indices=select_candidates(scores)
    assert indices.shape==(2,10)
    assert indices[0].tolist()==[8,0,1,2,3,4,5,6,7,9]


def test_pair_inputs_cannot_include_source_target_or_keyentity():
    cases=[{'source_body':'input only','labels':['not input'],'keyentity':'not input'}]
    labels=[str(i) for i in range(12)]
    pairs=make_pairs(cases,labels,np.arange(10).reshape(1,10),'source_body')
    assert len(pairs)==10 and all(p[0]=='input only' for p in pairs)
    assert all('not input' not in p for p in pairs)


def test_missing_or_invalid_candidate_rows_cannot_reduce_denominator():
    with pytest.raises(ValueError):make_pairs([{'source_body':'a'}],['x']*12,np.zeros((0,10),dtype=int),'source_body')
    with pytest.raises(ValueError):select_candidates(np.full((1,12),np.nan))
