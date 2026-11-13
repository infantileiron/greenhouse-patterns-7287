"""Apriori + blocked permutation, with BH over the prespecified full rule family."""
from collections import Counter, defaultdict
from itertools import combinations
import random
from statistics import mean
from src.utils.csv_data import checksum

def bh_adjust(pvalues):
    m=len(pvalues); result=[1.0]*m; running=1.0
    for rank,index in reversed(list(enumerate(sorted(range(m),key=lambda i:pvalues[i]),1))):
        running=min(running,pvalues[index]*m/rank)
        result[index]=min(1.0,running)
    return result

def apriori(transactions, min_support, max_length=3):
    if not 0<min_support<=1: raise ValueError('支持度须在(0,1]')
    n=len(transactions)
    if n<20: raise ValueError('至少20株样本')
    tx=[frozenset(x) for x in transactions]
    universe=sorted(set().union(*tx))
    previous={frozenset([x]) for x in universe if sum(x in t for t in tx)/n>=min_support}
    frequent={s:sum(s<=t for t in tx) for s in previous}
    for k in range(2,max_length+1):
        candidates={a|b for a in previous for b in previous if len(a|b)==k}
        candidates={s for s in candidates if all(frozenset(z) in previous for z in combinations(s,k-1))}
        counts={s:sum(s<=t for t in tx) for s in candidates}
        previous={s for s,count in counts.items() if count/n>=min_support}
        frequent.update({s:counts[s] for s in previous})
        if not previous: break
    return frequent

def analyze(rows, params):
    support=float(params['min_support']); confidence=float(params['min_confidence'])
    permutations=int(params['permutations']); seed=int(params['seed'])
    if not .02<=support<=.8 or not .1<=confidence<=1: raise ValueError('支持度0.02–0.8，置信度0.1–1')
    if not 99<=permutations<=1999: raise ValueError('置换次数99–1999')
    if not 20<=len(rows)<=5000: raise ValueError('样本量20–5000')
    transactions=[frozenset(r['symptoms']) for r in rows]
    items=sorted(set().union(*transactions))
    if not 2<=len(items)<=12: raise ValueError('症状种类应为2–12')
    n=len(rows); masks={x:sum(1<<i for i,t in enumerate(transactions) if x in t) for x in items}
    blocks=defaultdict(list)
    for i,row in enumerate(rows): blocks[row['greenhouse']].append(i)
    rng=random.Random(seed)
    perm_masks={}
    for item in items:
        generated=[]
        for _ in range(permutations):
            mask=0
            for indices in blocks.values():
                count=sum(item in transactions[i] for i in indices)
                for idx in rng.sample(indices,count): mask|=1<<idx
            generated.append(mask)
        perm_masks[item]=generated
    # Determine the complete family before applying support/confidence display filters.
    family=[]
    for size in (1,2):
        for antecedent in combinations(items,size):
            mask=masks[antecedent[0]]
            for x in antecedent[1:]: mask&=masks[x]
            ac=mask.bit_count()
            for consequent in items:
                if consequent in antecedent: continue
                bc=masks[consequent].bit_count(); joint=(mask&masks[consequent]).bit_count()
                p=(1+sum((mask&permuted).bit_count()>=joint for permuted in perm_masks[consequent]))/(permutations+1)
                conf=joint/ac if ac else 0
                family.append({'antecedent':list(antecedent),'consequent':consequent,'count':joint,
                    'antecedent_count':ac,'consequent_count':bc,'support':joint/n,'confidence':conf,
                    'lift':conf/(bc/n) if bc else 0,'p_value':p})
    adjusted=bh_adjust([r['p_value'] for r in family])
    for row,q in zip(family,adjusted): row['q_value']=q
    frequent=apriori(transactions,support,3)
    rules=[r for r in family if r['support']>=support and r['confidence']>=confidence]
    rules.sort(key=lambda r:(r['q_value'],-r['lift'],r['antecedent'],r['consequent']))
    for rank,rule in enumerate(rules,1): rule['rule_id']=f'R{rank:03}'
    frequencies=[{'item':x,'count':masks[x].bit_count(),'rate':masks[x].bit_count()/n} for x in items]
    heatmap=[{'a':a,'b':b,'count':(masks[a]&masks[b]).bit_count()} for a in items for b in items]
    return {'sample_count':n,'item_count':len(items),'family_size':len(family),'frequent_itemsets':len(frequent),
        'rules':rules,'significant_count':sum(r['q_value']<=.05 for r in rules),'frequencies':frequencies,
        'greenhouses':[{'name':g,'count':len(ids)} for g,ids in sorted(blocks.items())], 'heatmap':heatmap,
        'checksum':checksum(rows),'params':params,'method':'温室内置换后件；完整单后件规则族先做BH，再按支持度/置信度展示筛选',
        'caveat':'探索性关联，不代表因果。BH依赖独立或正相关假设；相关症状规则存在依赖，q值仅供复查排序，需独立样本验证。'}
