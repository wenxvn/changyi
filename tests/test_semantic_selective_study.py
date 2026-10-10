import numpy as np
from evaluation.core_exploration.semantic_selective_study import split_groups,choose_threshold,fit_calibration,assess


def rows():
    return [{'case_id':str(i),'group':str(i//2),'similarity':.5+i/100,'margin':i/1000,
             'source_label_match':i%3==0} for i in range(40)]


def test_same_input_group_cannot_cross_cal_and_test():
    cal,test = split_groups(rows(),42)
    assert not {r['group'] for r in cal}&{r['group'] for r in test}
    assert len(cal)+len(test)==40


def test_test_labels_cannot_change_calibrator_or_threshold():
    cal,test = split_groups(rows(),42)
    predict,params=fit_calibration(cal); chosen=choose_threshold(cal,predict(cal))
    before=predict(test)
    for r in test:r['source_label_match']=not r['source_label_match']
    predict2,params2=fit_calibration(cal)
    assert params==params2
    assert chosen==choose_threshold(cal,predict2(cal))
    np.testing.assert_array_equal(before,predict2(test))


def test_no_cal_feasible_target_rejects_every_test_row():
    r=rows()
    for x in r:x['source_label_match']=False
    chosen=choose_threshold(r,np.full(40,.9))
    assert chosen['threshold'] is None
    result=assess(r,np.full(40,.9),chosen['threshold'])
    assert result['retained']==0 and result['rejected']==40
    assert result['retained_precision'] is None


def test_coverage_and_retained_precision_use_full_rejection_denominator():
    r=rows()
    for i,x in enumerate(r):x['source_label_match']=i<20
    p=np.array([.9]*20+[.1]*20)
    chosen=choose_threshold(r,p)
    result=assess(r,p,chosen['threshold'])
    assert result['total_rows']==40 and result['retained']==20
    assert result['coverage']==.5 and result['retained_precision']==1


def test_duplicate_groups_have_equal_group_weight_in_precision():
    r=[{'group':'a','source_label_match':True}]*9+[{'group':'b','source_label_match':False}]
    result=assess(r,np.full(10,.9),.5)
    assert result['retained_precision']==.5
