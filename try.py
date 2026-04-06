h_labels = ["x3", "x4", "b"]
v_labels = ["x2", "x1", "F"]

last_data = [
            [2, -1, 1],  # строка x2
            [-1, 1, 2],  # строка x1
            [0, 0, 0]
            ]
n = 4 # кол-во иксов
m = 2 # кол-во ограничений

cs = [-2, -1, -3, -1]

F_xs = []
for i in range(n):
    F_xs.append(0)

b_vector = []
for i in range(m):
    b_vector.append(last_data[i][-1])

print("b_vector:", b_vector)
base_vars = v_labels[:-1]
print("base_vars:", base_vars)

print(str(b_vector[0])[:-1])

coef_x = []
for i in range(len(v_labels)-1):
    coef_row = []
    for j in range(len(h_labels)-1):
        coef_row.append(last_data[i][j])
    coef_x.append(coef_row)

print(coef_x)