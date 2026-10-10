"""Cal-only numerical compatibility calibration; never a clinical probability."""
import hashlib
import json
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from .medjourney_readonly import write_new

ROOT = Path(__file__).resolve().parent / 'results/semantic-selective-v1'
INPUT = Path(__file__).resolve().parent / 'results/semantic-department-v1/first-retrieval-comparison.json'
SEEDS = (42,7,13,23,101)


def split_groups(rows, seed):
    groups = sorted({r['group'] for r in rows}, key=lambda g:hashlib.sha256(f'{seed}:{g}'.encode()).hexdigest())
    cal_groups = set(groups[:int(len(groups)*.4)])
    return [r for r in rows if r['group'] in cal_groups], [r for r in rows if r['group'] not in cal_groups]


def weights(rows):
    counts = {}
    for r in rows: counts[r['group']] = counts.get(r['group'],0)+1
    return np.array([1/counts[r['group']] for r in rows])


def choose_threshold(cal, probabilities):
    candidates = []
    for step in range(21):
        threshold = step/20
        selected = [r for r,p in zip(cal, probabilities) if p>=threshold]
        precision = np.average([r['source_label_match'] for r in selected], weights=weights(selected)) if selected else None
        candidates.append({'threshold':threshold,'retained':len(selected),'groups':len({r['group'] for r in selected}),
                           'group_weighted_precision':float(precision) if precision is not None else None,
                           'feasible':bool(len(selected)>=10 and len({r['group'] for r in selected})>=5 and precision>=.8)})
    feasible = [x for x in candidates if x['feasible']]
    chosen = max(feasible, key=lambda x:(x['retained'],-x['threshold'])) if feasible else None
    return {'threshold':chosen['threshold'] if chosen else None,'candidates':candidates}


def fit_calibration(cal):
    X = np.array([[r['similarity'],r['margin']] for r in cal])
    y = np.array([r['source_label_match'] for r in cal], dtype=int)
    w = weights(cal)
    if len(set(y))<2:
        value = float(np.average(y, weights=w))
        return lambda rows:np.full(len(rows),value), {'kind':'degenerate_constant','value':value}
    scaler = StandardScaler().fit(X, sample_weight=w)
    model = LogisticRegression(C=1,max_iter=500,random_state=42).fit(scaler.transform(X), y, sample_weight=w)
    def predict(rows):
        return model.predict_proba(scaler.transform([[r['similarity'],r['margin']] for r in rows]))[:,1]
    return predict, {'kind':'cal_only_logistic_compatibility','scaler_mean':scaler.mean_.tolist(),
                     'scaler_scale':scaler.scale_.tolist(),'coefficient':model.coef_.tolist(),'intercept':model.intercept_.tolist()}


def assess(rows, probability, threshold):
    y = np.array([r['source_label_match'] for r in rows], dtype=float)
    p = np.clip(np.array(probability),1e-7,1-1e-7)
    w = weights(rows)
    accepted = np.array([False]*len(rows)) if threshold is None else p>=threshold
    kept = [r for r,a in zip(rows,accepted) if a]
    bins = []
    for step in range(10):
        mask = (p>=step/10)&(p<(step+1)/10)
        if mask.any():
            confidence = float(np.average(p[mask],weights=w[mask])); accuracy=float(np.average(y[mask],weights=w[mask]))
            bins.append({'lower':step/10,'rows':int(mask.sum()),'weight':float(w[mask].sum()/w.sum()),
                         'predicted_compatibility':confidence,'observed_compatibility':accuracy})
    return {'total_rows':len(rows),'groups':len({r['group'] for r in rows}),
            'retained':len(kept),'rejected':len(rows)-len(kept), 'coverage':len(kept)/len(rows),
            'retained_precision':float(np.average([r['source_label_match'] for r in kept],weights=weights(kept))) if kept else None,
            'brier':float(np.average((p-y)**2,weights=w)),
            'nll':float(np.average(-(y*np.log(p)+(1-y)*np.log(1-p)),weights=w)),
            'ece_compatibility':sum(b['weight']*abs(b['predicted_compatibility']-b['observed_compatibility']) for b in bins),
            'reliability_bins':bins}


def main():
    raw = INPUT.read_bytes(); source = json.loads(raw)
    ROOT.mkdir(exist_ok=True)
    protocol = {'input_sha256':hashlib.sha256(raw).hexdigest(),'seeds':SEEDS,'cal_fraction_groups':.4,
                'features':['similarity','margin'],'calibrator':'weighted_scaler_unweighted_LR_C1_maxiter500',
                'threshold_grid':[i/20 for i in range(21)],'cal_target':.8,'minimum_rows':10,'minimum_text_groups':5,
                'text_groups_not_certified_clinical_symptom_diversity':True,
                'source_exposure':'used_for_development','clinical_probability':False,'encoder_fits':0,
                'statistical_calibration_is_supervised_parameter_fitting':True}
    write_new(ROOT/'protocol.json',protocol)
    plans = []
    for item in source['results']:
        if item['method']!='frozen_bge_label_names': continue
        for seed in SEEDS:
            cal,test = split_groups(item['rows'],seed)
            predict, parameters = fit_calibration(cal)
            selection = choose_threshold(cal,predict(cal))
            plan = {'view':item['view'],'seed':seed,'parameters':parameters,'selection':selection,
                    'cal_ids':[r['case_id'] for r in cal],'test_ids':[r['case_id'] for r in test]}
            plans.append((plan,cal,test,predict))
    # Lock every selected threshold before any test assessment.
    write_new(ROOT/'cal-selections.json',[x[0] for x in plans])
    results = []
    for plan,cal,test,predict in plans:
        result = {**plan,'cal':assess(cal,predict(cal),plan['selection']['threshold']),
                  'test':assess(test,predict(test),plan['selection']['threshold'])}
        result['empirical_test_precision_target_met'] = result['test']['retained']>=10 and result['test']['retained_precision'] is not None and result['test']['retained_precision']>=.8
        results.append(result)
        print(plan['view'],plan['seed'],json.dumps(result['test']))
    write_new(ROOT/'results.json',{'protocol':protocol,'calibration_fits':len(results),'encoder_fits':0,
                                 'clinical_validation':False,'test_not_new_unseen_external_source':True,
                                 'text_group_gate_does_not_close_clinical_diversity_requirement':True,'results':results})


if __name__=='__main__':main()
