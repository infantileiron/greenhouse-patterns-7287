import csv
import io
import json
import random
from src.config.database import initialize,save,get,all_records
from src.utils.security import hash_password
from src.utils.csv_data import checksum
from src.services.mining import analyze
from src.services.report import create_report
ITEMS=['叶斑','黄化','卷叶','萎蔫','根褐变','茎软腐','白粉','叶缘焦枯','生长迟缓','花蕾脱落']
def make_rows():
    rng=random.Random(261105); rows=[]
    for i in range(800):
        items=set(); fungal=rng.random()<.31; root=rng.random()<.23
        probs=[.9 if fungal else .07,.76 if fungal else .1,.18,.84 if root else .06,.9 if root else .04,.72 if root else .035,.2,.15,.75 if root else .1,.14]
        for item,p in zip(ITEMS,probs):
            if rng.random()<p: items.add(item)
        rows.append({'plant_id':f'NL-{i+1:04}','greenhouse':f'温室{1+i%8:02}','symptoms':sorted(items)})
    return rows

def seed():
    initialize()
    for role,name in [('admin','林站长'),('analyst','周农艺师'),('viewer','陈观察员')]:
        key='seed-'+role
        if not get('users',key): save('users',{'id':key,'name':name,'email':role+'@nanling.test','role':role,'password':hash_password('Nanling!2611')},True)
    rows=make_rows()
    save('datasets',{'id':'seed-dataset','name':'2026年11月温室病征调查','filename':'symptom_checks_202611.csv','rows':rows,'checksum':checksum(rows)},True)
    for idx,confidence in [(1,.65),(2,.8)]:
        save('studies',{'id':f'seed-study-{idx}','name':['11月病征组合复查','高置信度保守筛查'][idx-1],'dataset_id':'seed-dataset','min_support':.12,'min_confidence':confidence,'permutations':999,'seed':261105},True)
    if not get('runs','seed-run'):
        study=get('studies','seed-study-1'); result=analyze(rows,{k:study[k] for k in ('min_support','min_confidence','permutations','seed')})
        save('runs',{'id':'seed-run','study_id':'seed-study-1','status':'succeeded','result':result,'error':None},True)
    run=get('runs','seed-run')
    ids=[r['rule_id'] for r in run['result']['rules'][:3]]
    if ids:
        review=save('reviews',{'id':'seed-review','run_id':'seed-run','rule_ids':ids,'note':'先复查根褐变与萎蔫组合，独立样本确认后再设计干预','status':'approved','submitted_by':'analyst@nanling.test','reviewed_by':'admin@nanling.test'},True)
        create_report(review)
        save('reviews',{'id':'seed-pending-review','run_id':'seed-run','rule_ids':ids[:1],'note':'请农艺师安排复查，当前关联不代表病因','status':'pending','submitted_by':'analyst@nanling.test'},True)
    counts={table:len(all_records(table)) for table in ('users','datasets','studies','runs','reviews','reports')}
    print(json.dumps(counts,ensure_ascii=False))
    return counts
if __name__=='__main__': seed()
