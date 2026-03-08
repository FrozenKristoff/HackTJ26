import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile, assemble
from qiskit_aer import Aer, AerSimulator
from qiskit.visualization import plot_histogram
import matplotlib as plt
from qiskit.quantum_info import Statevector
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt
from qiskit import transpile
from qiskit_ibm_runtime.fake_provider import FakeAthensV2 as fake
from qiskit_optimization import QuadraticProgram
import itertools

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt
import itertools


# -------------------------
# Appliance model
# -------------------------

class Appliance:
    def __init__(self, name, power, duration, earliest_start, latest_start, user):
        self.name = name
        self.power = power              # watts
        self.duration = max(1, int(duration))  # FIX: ensure >=1 slot
        self.earliest_start = earliest_start
        self.latest_start = latest_start
        self.user = user


# -------------------------
# Appliances
# -------------------------

appliances = [
    Appliance("Toaster", 100, 1, 1, 3, True),
    Appliance("Washer", 1800, 2, 0, 2, False),
    Appliance("Dryer", 2500, 2, 1, 3, False)
]


# -------------------------
# Energy price
# -------------------------

prices = [0.3,0.3,0.4,0.4,0.4,0.3]


# -------------------------
# QUBO construction
# -------------------------

def build_energy_qubo(appliances, T, power_budget, prices, A=100, C=0.001, D=1.0):

    variables = []
    qubo = {}
    index_of = {}

    # create variables
    for i, app in enumerate(appliances):
        starts = list(range(app.earliest_start, app.latest_start+1))

        for t in starts:
            variables.append((i,t))
            index_of[(i,t)] = len(variables)-1

    def add(u,v,val):
        if u>v:
            u,v=v,u
        qubo[(u,v)] = qubo.get((u,v),0)+val


    # start constraint (exactly one start)
    for i,app in enumerate(appliances):

        start_vars = [index_of[(i,t)] for t in range(app.earliest_start,app.latest_start+1)]

        for u in start_vars:
            add(u,u,-A)

        for u,v in itertools.combinations(start_vars,2):
            add(u,v,2*A)


    # electricity cost
    for i,app in enumerate(appliances):
        for t in range(app.earliest_start,app.latest_start+1):

            u = index_of[(i,t)]

            run_cost = app.power * sum(prices[tau] for tau in range(t, min(t+app.duration,T)))

            add(u,u,D*run_cost)


    # power constraint
    for tau in range(T):

        active = []

        for i,app in enumerate(appliances):

            for t in range(app.earliest_start,app.latest_start+1):

                if t <= tau < t + app.duration:

                    u = index_of[(i,t)]

                    active.append((u,app.power))

        B = power_budget[tau]

        for u,p in active:
            add(u,u,C*(p*p - 2*B*p))

        for (u1,p1),(u2,p2) in itertools.combinations(active,2):

            add(u1,u2,2*C*p1*p2)

    return qubo, variables


# -------------------------
# QUBO → Ising
# -------------------------

def qubo_to_ising(qubo,n):

    const=0
    h={i:0 for i in range(n)}
    J={}

    for (u,v),q in qubo.items():

        if u==v:

            const+=q/2
            h[u]+=-q/2

        else:

            const+=q/4
            h[u]+=-q/4
            h[v]+=-q/4
            J[(min(u,v),max(u,v))]=J.get((min(u,v),max(u,v)),0)+q/4

    return const,h,J


# -------------------------
# QAOA circuit
# -------------------------

def apply_cost_unitary(qc,gamma,h,J):

    for i,c in h.items():

        if abs(c)>1e-12:

            qc.rz(2*gamma*c,i)

    for (i,j),c in J.items():

        if abs(c)>1e-12:

            qc.rzz(2*gamma*c,i,j)


def apply_mixer_unitary(qc,beta,n):

    for i in range(n):

        qc.rx(2*beta,i)


def build_qaoa_circuit(n,h,J,gammas,betas):

    qc=QuantumCircuit(n,n)

    for i in range(n):

        qc.h(i)

    for gamma,beta in zip(gammas,betas):

        apply_cost_unitary(qc,gamma,h,J)

        apply_mixer_unitary(qc,beta,n)

    qc.measure(range(n),range(n))

    return qc


# -------------------------
# Run experiment
# -------------------------

T=6
power_budget=[4000]*T

qubo,variables=build_energy_qubo(appliances,T,power_budget,prices)

n=len(variables)

const,h,J=qubo_to_ising(qubo,n)

gammas=[0.1]
betas=[0.3]

qc=build_qaoa_circuit(n,h,J,gammas,betas)

sim=AerSimulator()

compiled=transpile(qc,sim)

result=sim.run(compiled,shots=1024).result()

counts=result.get_counts()

print("variables:",variables)

print("counts:",counts)

plot_histogram(counts)

plt.show()
