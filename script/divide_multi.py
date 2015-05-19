a = [[1,2,3],[4,5,6],[7,8,9]]

b = 5

for i in range(len(a)):
    l = len(a[i])
    print str(b) + ' : ' + str(l)
    if b > l :
        print 'here'
        b = b - l
    else:
        print b
        a[i].insert(b,'NEW VALUE')
        break

print a
'''
temp1 = []
temp2 = []
sum = 0
for i in range(len(a)):
    l = len(a[i])
    if sum + l < b:
        temp1.append(a[i])
    elif (sum < b) and (sum + l) > b:
        temp1.append(a[i][:(b-sum)])
        temp2.append(a[i][-sum + 1:])
    else:
        temp2.append(a[i])
    sum += l

print temp1
print temp2
'''