def hungarian_min(cost):
    """
    Венгерский алгоритм для задачи о назначениях (минимизация).
    cost: квадратная матрица n x n
    return: (min_cost, assignment)
        min_cost - минимальная суммарная стоимость
        assignment - список длины n, где assignment[i] = j означает, что работник i назначен на работу j
    
    Выбирает по одному элементу в каждой строке и каждом столбце так, чтобы сумма была минимальной.

    Если какие-то рёбра отсутствуют, нужно поставить большой штраф (10**9) вместо отсутствующего ребра.
    """
    n = len(cost)
    INF = 10**18

    u = [0] * (n + 1) # потенциалы строк
    v = [0] * (n + 1) # потенциалы столбцов

    p = [0] * (n + 1) # p[j] - какая строка назначена на столбец j
    
    way = [0] * (n + 1) # way[j] - вспомогательный массив для восстановления пути

    for i in range(1, n + 1): # Главный цикл по строкам
        p[0] = i
        j0 = 0
        minv = [INF] * (n + 1)
        used = [False] * (n + 1)

        while True: # внутренний цикл - поиск увеличивающего пути
            used[j0] = True
            i0 = p[j0]
            delta = INF
            j1 = -1

            for j in range(1, n + 1): # перебираем все столбцы j, которые ещё не посещены
                if not used[j]:
                    cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j

            for j in range(n + 1): # сдвиг потенциалов
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta

            j0 = j1
            if p[j0] == 0:
                break

        
        while True: # восстанавление пути
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break

    # восстанавление ответа
    assignment = [-1] * n
    for j in range(1, n + 1):
        if p[j] != 0:
            assignment[p[j] - 1] = j - 1

    min_cost = sum(cost[i][assignment[i]] for i in range(n))
    return min_cost, assignment

def main():
    # cost = [
    #     [4, 2, 3],
    #     [2, 3, 5],
    #     [3, 2, 4]
    # ]

    cost = [
        [12,  7, 15,  9, 11],
        [ 8,  6, 14, 12, 10],
        [13,  9, 11,  7, 1],
        [10, 12,  8, 15,  6],
        [ 9, 2, 13, 10,  8],
    ]

    min_cost, assignment = hungarian_min(cost)

    print("Минимальная стоимость:", min_cost)
    print("Назначение:", assignment)

    for i, j in enumerate(assignment):
        print(f"Работник {i} -> Работа {j} (стоимость {cost[i][j]})")

if __name__ == "__main__":
    main()
