"""One fixed top10 cross-encoder comparison, local and research-only."""
import argparse
import hashlib
import json
import os
import time
from pathlib import Path
import numpy as np
from .semantic_department_study import load_cases,model_path,encode,measure,CACHE
from .medjourney_readonly import write_new

ROOT=Path(__file__).resolve().parent/'results/reranked-department-v1'
MODEL='BAAI/bge-reranker-base'
REVISION='2cfc18c9415c912f9d8155881c133215df768a70'


def reranker_path(download=False):
    from huggingface_hub import snapshot_download
    return snapshot_download(MODEL,revision=REVISION,cache_dir=str(CACHE),token=False,local_files_only=not download,
                             max_workers=2,allow_patterns=['config.json','model.safetensors','tokenizer.json',
                                                          'tokenizer_config.json','special_tokens_map.json','sentencepiece.bpe.model'])


def select_candidates(matrix, k=10):
    if matrix.ndim!=2 or not np.isfinite(matrix).all() or matrix.shape[1]<k:
        raise ValueError('Finite full candidate matrix required')
    return np.argsort(-matrix,axis=1,kind='stable')[:,:k]


def make_pairs(cases, labels, candidates, view):
    if candidates.shape != (len(cases),10) or (candidates<0).any() or (candidates>=len(labels)).any():
        raise ValueError('Exactly ten valid candidates per source row required')
    return [(c[view],labels[int(i)]) for c,indices in zip(cases,candidates) for i in indices]


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=['freeze','download','candidates','evaluate']);args=parser.parse_args()
    os.environ['HF_HUB_DISABLE_PROGRESS_BARS']='1';os.environ['TOKENIZERS_PARALLELISM']='false'
    meta,cases=load_cases();labels=sorted({x for c in cases for x in c['labels']});ROOT.mkdir(exist_ok=True)
    protocol={'source_sha256':meta['source_sha256'],'labels':labels,'model':MODEL,'revision':REVISION,
              'candidate_retriever':'frozen_bge_small_zh_label_names','top_k':10,'pair_document':'label_name_only',
              'max_length':256,'batch':16,'threads':2,'source_exposure':'used_for_development',
              'encoder_fits':0,'score_kind':'sigmoid_logit_for_ordering_not_calibrated_probability','deployment':False}
    if args.mode=='freeze':write_new(ROOT/'protocol.json',protocol);print('TOP10_PROTOCOL_FROZEN');return
    frozen=(ROOT/'protocol.json').read_bytes()
    if json.loads(frozen)!=protocol:raise ValueError('Frozen protocol changed')
    if args.mode=='download':
        local=Path(reranker_path(True));hashes={}
        for path in sorted(local.glob('*')):
            if path.is_file():
                h=hashlib.sha256()
                with path.open('rb') as f:
                    for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
                hashes[path.name]=h.hexdigest()
        if 'model.safetensors' not in hashes:raise ValueError('Safe weight file missing')
        write_new(ROOT/'model-download.json',{'model':MODEL,'revision':REVISION,'license':'MIT_official_card','files_sha256':hashes})
        print('RERANKER_DOWNLOAD_VERIFIED');return
    import torch
    from transformers import AutoTokenizer,AutoModel,AutoModelForSequenceClassification
    torch.set_num_threads(2);torch.set_num_interop_threads(2)
    local=model_path();tokenizer=AutoTokenizer.from_pretrained(local,local_files_only=True,trust_remote_code=False)
    retriever=AutoModel.from_pretrained(local,local_files_only=True,trust_remote_code=False,use_safetensors=True).to('cpu').eval()
    label_vectors=encode(retriever,tokenizer,labels);candidate_views={}
    for view in ['source_body','complaint_only']:
        candidates=select_candidates(encode(retriever,tokenizer,[c[view] for c in cases])@label_vectors.T)
        candidate_views[view]=candidates
    candidate_record={view:[{'case_id':c['case_id'],'indices':indices.tolist()} for c,indices in zip(cases,m)] for view,m in candidate_views.items()}
    candidate_file=ROOT/'candidate-pools.json'
    if candidate_file.exists():
        if json.loads(candidate_file.read_text(encoding='utf-8'))!=candidate_record:raise ValueError('Candidate pool changed')
    else:write_new(candidate_file,candidate_record)
    if args.mode=='candidates':
        counts={view:sum(any(labels[int(i)] in c['labels'] for i in ids) for c,ids in zip(cases,matrix)) for view,matrix in candidate_views.items()}
        write_new(ROOT/'candidate-recall.json',{'full_rows_per_view':500,'top_k':10,
                  'candidate_sha256':hashlib.sha256(candidate_file.read_bytes()).hexdigest(),
                  'source_label_recalled':counts,'target_was_not_used_to_generate_candidates':True})
        print('CANDIDATE_RECALL',json.dumps(counts));return
    del retriever
    local=reranker_path();tokenizer=AutoTokenizer.from_pretrained(local,local_files_only=True,trust_remote_code=False)
    reranker=AutoModelForSequenceClassification.from_pretrained(local,local_files_only=True,trust_remote_code=False,use_safetensors=True).to('cpu').eval()
    baseline_path=Path(__file__).resolve().parent/'results/medjourney-readonly-v1/first-source-comparison.json'
    baseline=json.loads(baseline_path.read_text(encoding='utf-8'))
    for view,candidates in candidate_views.items():
        output=ROOT/f'{view}-result.json'
        if output.exists():print('ALREADY_COMPLETE',view);continue
        start=time.perf_counter();scores=np.zeros((len(cases),len(labels)),dtype=np.float32)
        pairs=make_pairs(cases,labels,candidates,view)
        values=[]
        with torch.inference_mode():
            for offset in range(0,len(pairs),16):
                batch=tokenizer(pairs[offset:offset+16],padding=True,truncation=True,max_length=256,return_tensors='pt')
                logits=reranker(**batch).logits.reshape(-1).float()
                values.extend(torch.sigmoid(logits).cpu().tolist())
                if offset%800==0:print('PROGRESS',view,offset,'of',len(pairs),flush=True)
        for row,(indices,s) in enumerate(zip(candidates,np.array(values).reshape(len(cases),10))):scores[row,indices]=s
        legacy={r['case_id']:r for v in baseline['results'] if v['view']==view for r in v['rows']}
        item=measure(cases,labels,scores,legacy);item.update(method='frozen_bge_top10_reranker_base',view=view,
              top10_oracle_source_label_matches=sum(any(labels[int(i)] in c['labels'] for i in ids) for c,ids in zip(cases,candidates)),
              pair_inferences=len(pairs),elapsed_seconds=time.perf_counter()-start,
              candidate_sha256=hashlib.sha256(candidate_file.read_bytes()).hexdigest(),protocol_sha256=hashlib.sha256(frozen).hexdigest(),
              encoder_fits=0,clinical_validation=False,score_kind=protocol['score_kind'])
        write_new(output,item);print('COMPLETED',view,json.dumps(item['summary']),flush=True)


if __name__=='__main__':main()
