
def add(multipolyline, index, new_point):
    for i in range(len(multipolyline)):
        l = len(multipolyline[i])
        if index > l:
            index -= l
        else:
            multipolyline[i].insert(index, new_point)
            break
    return multipolyline

def split(multipolyline, index):
    temp1 = []
    temp2 = []
    sum = 0
    for i in range(len(multipolyline)):
        l = len(multipolyline[i])
        if sum + l < index:
            temp1.append(multipolyline[i])
        elif (sum < index) and (sum + l) > index:
            temp1.append(
                multipolyline[i][:(index-sum) + 1])
            if sum == 0:
                temp2.append(multipolyline[i][index:])
            else:
                temp2.append(multipolyline[i][-sum:])
        else:
            temp2.append(multipolyline[i])
        sum += l
    print temp1
    print temp2

l = [[1, 2, 3], [4, 5, 6]]
print l
index = 2
print add(l, index, '##')
split(l, index)
#print add(l, 3, 10)
#print add(l, 1, 10)
#print add(l, 8, 10)