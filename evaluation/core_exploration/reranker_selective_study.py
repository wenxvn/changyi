"""Same predeclared numerical compatibility protocol for fixed reranker outputs."""
import hashlib
import json
from pathlib import Path
from .semantic_selective_study import SEEDS,split_groups,fit_calibration,choose_threshold,assess
from .medjourney_readonly import write_new

ROOT=Path(__file__).resolve().parent/'results/reranker-selective-v1'
SOURCE=Path(__file__).resolve().parent/'results/reranked-department-v1'


def main():
    inputs={view:(SOURCE/f'{view}-result.json').read_bytes() for view in ['source_body','complaint_only']}
    items={view:json.loads(raw) for view,raw in inputs.items()}
    if any(len(x['rows'])!=500 or x['summary']['full_rows']!=500 for x in items.values()):
        raise ValueError('Both complete source views required')
    ROOT.mkdir(exist_ok=True)
    protocol={'input_sha256':{v:hashlib.sha256(raw).hexdigest() for v,raw in inputs.items()},
              'seeds':SEEDS,'cal_fraction_groups':.4,'features':['similarity','margin'],
              'score_kind':'sigmoid_reranker_logit_not_clinical_probability','target':.8,
              'threshold_grid':[i/20 for i in range(21)],'minimum_rows':10,'minimum_text_groups':5,
              'calibrator':'group_weighted_scaler_LR_C1_no_class_balancing','encoder_fits':0,
              'source_exposure':'used_for_development','clinical_validation':False,
              'text_groups_not_certified_symptom_diversity':True}
    write_new(ROOT/'protocol.json',protocol)
    plans=[]
    for view,item in items.items():
        for seed in SEEDS:
            cal,test=split_groups(item['rows'],seed);predict,parameters=fit_calibration(cal)
            selection=choose_threshold(cal,predict(cal))
            plan={'view':view,'seed':seed,'parameters':parameters,'selection':selection,
                  'cal_ids':[r['case_id'] for r in cal],'test_ids':[r['case_id'] for r in test]}
            plans.append((plan,cal,test,predict))
    write_new(ROOT/'cal-selections.json',[x[0] for x in plans])
    results=[]
    for plan,cal,test,predict in plans:
        result={**plan,'cal':assess(cal,predict(cal),plan['selection']['threshold']),
                'test':assess(test,predict(test),plan['selection']['threshold'])}
        result['empirical_test_target_met']=result['test']['retained']>=10 and result['test']['retained_precision'] is not None and result['test']['retained_precision']>=.8
        results.append(result)
        print(plan['view'],plan['seed'],result['test']['retained'],result['test']['retained_precision'],flush=True)
    write_new(ROOT/'results.json',{'protocol':protocol,'statistical_supervised_fits':10,'encoder_fits':0,
                                  'clinical_validation':False,'results':results})


if __name__=='__main__':main()
