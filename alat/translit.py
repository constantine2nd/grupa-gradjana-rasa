# -*- coding: utf-8 -*-
import sys, re
D = {'Љ':'Lj','Њ':'Nj','Џ':'Dž','љ':'lj','њ':'nj','џ':'dž',
     'А':'A','Б':'B','В':'V','Г':'G','Д':'D','Ђ':'Đ','Е':'E','Ж':'Ž','З':'Z',
     'И':'I','Ј':'J','К':'K','Л':'L','М':'M','Н':'N','О':'O','П':'P','Р':'R',
     'С':'S','Т':'T','Ћ':'Ć','У':'U','Ф':'F','Х':'H','Ц':'C','Ч':'Č','Ш':'Š',
     'а':'a','б':'b','в':'v','г':'g','д':'d','ђ':'đ','е':'e','ж':'ž','з':'z',
     'и':'i','ј':'j','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r',
     'с':'s','т':'t','ћ':'ć','у':'u','ф':'f','х':'h','ц':'c','ч':'č','ш':'š'}
def tr(s):
    out=[]
    for i,ch in enumerate(s):
        r=D.get(ch)
        if r is None: out.append(ch); continue
        # ALL-CAPS run: LJ/NJ/DŽ uppercase
        if r in ('Lj','Nj','Dž'):
            nxt = s[i+1] if i+1<len(s) else ''
            if nxt and nxt.isupper() and nxt in D: r = r.upper()
        out.append(r)
    return ''.join(out)
p=sys.argv[1]
t=open(p,encoding='utf-8').read()
open(p,'w',encoding='utf-8').write(tr(t))
print('ok')
