
data = [(1,2),(2,3),(0,1)]
print([x1 if x1==0 else x2+10 for x1, x2 in data])