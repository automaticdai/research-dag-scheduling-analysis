import random

capacity = 100
consumer_num = 10
trails_super = 1000
trials = 100000


def run_once_unconstrained():
    cores = [[],[]]
    capacities = [capacity,capacity]

    # generate consumers
    consumers = []
    for i in range(consumer_num):
        consumers.append(random.randint(1,capacity))

    consumers.sort()
    print(consumers)

    # our allocation (lower bound)
    for i in consumers:
        if capacities[0] > capacities[1]:
            if i <= capacities[0]:
                capacities[0] = capacities[0] - i
                cores[0].append(i)
        # core 2 has more capacity
        else:
            if i <= capacities[1]:
                capacities[1] = capacities[1] - i
                cores[1].append(i)

    alpha_ours = capacity * 2 - (capacities[0] + capacities[1]) 

    print("allocation:", cores)
    print("capacities:", capacities)
    print("alpha:", alpha_ours)
    print("----------")

    # generate a lot of random allocation (shuffle consumers)
    for k in range(trials):
        cores = [[],[]]
        capacities = [capacity,capacity]
        random.shuffle(consumers)
        for i in consumers:
            if capacities[0] > capacities[1]:
                if i <= capacities[0]:
                    capacities[0] = capacities[0] - i
                    cores[0].append(i)
            # core 2 has more capacity
            else:
                if i <= capacities[1]:
                    capacities[1] = capacities[1] - i
                    cores[1].append(i)
        alpha = capacity * 2 - (capacities[0] + capacities[1])
        if (alpha < alpha_ours):
            print("Found a counter example:")
            print("allocation:", cores)
            print("capacities:", capacities)
            print("alpha:", alpha)
            print("----------")


def run_once_constrained():
    cores = [[],[]]
    capacities = [capacity,capacity]
    capacities_safe = [capacity,capacity]
    
    # generate consumers
    consumers = []
    for i in range(consumer_num):
        consumers.append(random.randint(1,capacity))

    consumers.sort(reverse=False)
    print(consumers)

    # our allocation (lower bound)
    for i in consumers:
        if capacities[0] > capacities[1]:
            if i <= capacities_safe[0]:
                capacities[0] = capacities[0] - i
                # update safer capacity
                capacities_safe[0] = capacities[0]
                capacities_safe[1] = capacities[1] - i
                cores[0].append(i)
        # core 2 has more capacity
        else:
            if i <= capacities_safe[1]:
                capacities[1] = capacities[1] - i
                # update safer capacity
                capacities_safe[0] = capacities[0] - i
                capacities_safe[1] = capacities[1]
                cores[1].append(i)

    alpha_ours = capacity * 2 - (capacities[0] + capacities[1]) 

    print("allocation:", cores)
    print("capacities:", capacities)
    print("alpha:", alpha_ours)
    
    # generate a lot of random allocation (shuffle consumers)
    for _ in range(trials):
        cores = [[],[]]
        capacities = [capacity,capacity]
        random.shuffle(consumers)
        for i in consumers:
            if capacities[0] > capacities[1]:
                if i <= capacities[0]:
                    capacities[0] = capacities[0] - i
                    cores[0].append(i)
            # core 2 has more capacity
            else:
                if i <= capacities[1]:
                    capacities[1] = capacities[1] - i
                    cores[1].append(i)
        alpha = capacity * 2 - (capacities[0] + capacities[1])
        if (alpha < alpha_ours):
            print("Warning:")
            print("allocation:", cores)
            print("capacities:", capacities)
            print("alpha:", alpha)
            print("----------")

            raise Exception("Found a counter example!")

    print("----------")


for ii in range(trails_super):
    print("({:d}/{:d})".format(ii, trails_super))
    run_once_constrained()
 