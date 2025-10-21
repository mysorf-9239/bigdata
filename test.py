import sys
import random
from typing import List

random.seed(42)


def read_input():
  data = sys.stdin.read().strip().split()

  it = iter(data)

  n = int(next(it))

  C = [[0] * n for _ in range(n)]
  for i in range(n):
    for j in range(n):
      C[i][j] = float(next(it))

  return n, C


def tour_cost(route: List[int], C) -> float:
  n = len(route)

  s = 0.0
  for i in range(n - 1):
    s += C[route[i]][route[i + 1]]

  s += C[route[-1]][route[0]]

  return s


def fitness(cost: float) -> float:
  return 1.0 / (1.0 + cost)


def nearest_neighbor(start: int, C) -> List[int]:
  n = len(C)
  unvis = set(range(n))
  route = [start]
  unvis.remove(start)
  cur = start

  while unvis:
    nxt = min(unvis, key=lambda j: C[cur][j])
    route.append(nxt)
    unvis.remove(nxt)
    cur = nxt

  return route


def ox_crossover(p1: List[int], p2: List[int]) -> List[int]:
  n = len(p1)
  a, b = sorted(random.sample(range(n), 2))
  child = [-1] * n
  child[a:b + 1] = p1[a:b + 1]
  used = set(child[a:b + 1])
  pos = (b + 1) % n

  for x in p2:
    if x not in used:
      child[pos] = x
      pos = (pos + 1) % n

  return child


def mutate_swap(route: List[int], p: float):
  if random.random() < p:
    i, j = random.sample(range(len(route)), 2)
    route[i], route[j] = route[j], route[i]


def mutate_inversion(route: List[int], p: float):
  if random.random() < p:
    a, b = sorted(random.sample(range(len(route)), 2))
    route[a:b + 1] = reversed(route[a:b + 1])


def two_opt_limited(route: List[int], C, max_tries: int = 200):
  n = len(route)
  best = route
  best_cost = tour_cost(best, C)

  tries = 0
  while tries < max_tries:
    i = random.randrange(0, n - 1)
    j = random.randrange(i + 1, n)
    a, b = best[i], best[(i + 1) % n]
    c, d = best[j], best[(j + 1) % n]

    delta = (C[a][c] + C[b][d]) - (C[a][b] + C[c][d])
    if delta < -1e-12:
      new_route = best[:i + 1] + list(reversed(best[i + 1:j + 1])) + best[j + 1:]
      best = new_route
      best_cost += delta
      tries = 0
    else:
      tries += 1

  return best


def genetic_tsp(C, time_budget_sec=None) -> List[int]:
  n = len(C)

  if n <= 80:
    POP = 200
    GENS = 1000
    P_CROSS = 0.95
    P_SWAP = 0.20
    P_INV = 0.20
    ELIT = max(2, POP // 20)  # 5%
    SEED_NN = min(20, n)
    PATIENCE = 200
    TWO_OPT_TRIES = 300
  elif n <= 300:
    POP = 160
    GENS = 700
    P_CROSS = 0.95
    P_SWAP = 0.12
    P_INV = 0.12
    ELIT = max(2, POP // 20)
    SEED_NN = min(16, n)
    PATIENCE = 150
    TWO_OPT_TRIES = 200
  else:  # n up to ~1000
    POP = 120
    GENS = 500
    P_CROSS = 0.9
    P_SWAP = 0.08
    P_INV = 0.08
    ELIT = max(2, POP // 20)
    SEED_NN = min(12, n)
    PATIENCE = 120
    TWO_OPT_TRIES = 120

  population: List[List[int]] = []

  starts = random.sample(range(n), SEED_NN) if n > SEED_NN else list(range(n))
  for s in starts:
    population.append(nearest_neighbor(s, C))

  while len(population) < POP:
    route = list(range(n))
    random.shuffle(route)
    population.append(route)

  costs = [tour_cost(ind, C) for ind in population]
  best_idx = min(range(len(population)), key=lambda i: costs[i])
  best_route = population[best_idx][:]
  best_cost = costs[best_idx]

  no_improve = 0

  def tournament_index(k=3):
    cand = random.sample(range(len(population)), k)
    return min(cand, key=lambda i: costs[i])

  for gen in range(GENS):
    elites_idx = sorted(range(len(population)), key=lambda i: costs[i])[:ELIT]
    elites = [population[i][:] for i in elites_idx]

    new_pop: List[List[int]] = elites[:]

    while len(new_pop) < POP:
      p1 = population[tournament_index()]
      p2 = population[tournament_index()]

      if random.random() < P_CROSS:
        child = ox_crossover(p1, p2)
      else:
        child = p1[:] if random.random() < 0.5 else p2[:]

      mutate_swap(child, P_SWAP)
      mutate_inversion(child, P_INV)

      if random.random() < 0.15:
        child = two_opt_limited(child, C, max_tries=TWO_OPT_TRIES)

      new_pop.append(child)

    population = new_pop
    costs = [tour_cost(ind, C) for ind in population]

    gbest_idx = min(range(len(population)), key=lambda i: costs[i])
    gbest_cost = costs[gbest_idx]
    if gbest_cost + 1e-9 < best_cost:
      best_cost = gbest_cost
      best_route = population[gbest_idx][:]
      no_improve = 0
    else:
      no_improve += 1

    if no_improve >= PATIENCE:
      break

  best_route = two_opt_limited(best_route, C, max_tries=5 * TWO_OPT_TRIES)
  return best_route


def main():
  n, C = read_input()
  route0 = genetic_tsp(C)
  print(n)
  print(" ".join(str(x + 1) for x in route0))


if __name__ == "__main__":
  main()
