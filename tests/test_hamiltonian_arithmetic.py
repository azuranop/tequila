from tequila.hamiltonian import QubitHamiltonian, PauliString, paulis
from numpy import random, kron, eye, allclose
from tequila import BitString, QubitWaveFunction
from tequila import paulis
import numpy, pytest

def test_ketbra():
    ket = QubitWaveFunction.from_string("1.0*|00> + 1.0*|11>").normalize()
    operator = paulis.KetBra(ket=ket, bra="|00>")
    result = operator*QubitWaveFunction.from_int(0, n_qubits=2)
    assert(result == ket)

@pytest.mark.parametrize("n_qubits", [1,2,3,5])
def test_ketbra_random(n_qubits):
    ket = numpy.random.uniform(0.0, 1.0, 2**n_qubits)
    bra = QubitWaveFunction.from_int(0, n_qubits=n_qubits)
    operator = paulis.KetBra(ket=ket, bra=bra)
    result = operator * bra
    assert result == QubitWaveFunction.from_array(ket)

def test_paulistring_conversion():
    X1 = QubitHamiltonian.init_from_string("X0")
    X2 = paulis.X(0)
    keys = [i for i in X2.keys()]
    pwx = PauliString.from_openfermion(key=keys[0], coeff=X2[keys[0]])
    X3 = QubitHamiltonian.init_from_paulistring(pwx)
    assert (X1 == X2)
    assert (X2 == X3)

    H = paulis.X(0) * paulis.Y(1) * paulis.Z(2) + paulis.X(3) * paulis.Y(4) * paulis.Z(5)
    PS = []
    for key, value in H.items():
        PS.append(PauliString.from_openfermion(key, value))
    PS2 = H.paulistrings
    assert (PS == PS2)

    H = make_random_pauliword(complex=True)
    for i in range(5):
        H += make_random_pauliword(complex=True)
    PS = []
    for key, value in H.items():
        PS.append(PauliString.from_openfermion(key, value))
    PS2 = H.paulistrings
    assert (PS == PS2)


def test_simple_arithmetic():
    qubit = random.randint(0, 5)
    primitives = [paulis.X, paulis.Y, paulis.Z]
    assert (paulis.X(qubit).conjugate() == paulis.X(qubit))
    assert (paulis.Y(qubit).conjugate() == -1 * paulis.Y(qubit))
    assert (paulis.Z(qubit).conjugate() == paulis.Z(qubit))
    assert (paulis.X(qubit).transpose() == paulis.X(qubit))
    assert (paulis.Y(qubit).transpose() == -1 * paulis.Y(qubit))
    assert (paulis.Z(qubit).transpose() == paulis.Z(qubit))
    for P in primitives:
        assert (P(qubit) * P(qubit) == QubitHamiltonian())
        n = random.randint(0, 10)
        nP = QubitHamiltonian.init_zero()
        for i in range(n):
            nP += P(qubit)
        assert (n * P(qubit) == nP)

    for i, Pi in enumerate(primitives):
        i1 = (i + 1) % 3
        i2 = (i + 2) % 3
        assert (Pi(qubit) * primitives[i1](qubit) == 1j * primitives[i2](qubit))
        assert (primitives[i1](qubit) * Pi(qubit) == -1j * primitives[i2](qubit))

        for qubit2 in random.randint(6, 10, 5):
            if qubit2 == qubit: continue
            P = primitives[random.randint(0, 2)]
            assert (Pi(qubit) * primitives[i1](qubit) * P(qubit2) == 1j * primitives[i2](qubit) * P(qubit2))
            assert (P(qubit2) * primitives[i1](qubit) * Pi(qubit) == -1j * P(qubit2) * primitives[i2](qubit))


def test_special_operators():
    # sigma+ sigma- as well as Q+ and Q-
    assert (paulis.Sp(0) * paulis.Sp(0) == QubitHamiltonian.init_zero())
    assert (paulis.Sm(0) * paulis.Sm(0) == QubitHamiltonian.init_zero())

    assert (paulis.Qp(0) * paulis.Qp(0) == paulis.Qp(0))
    assert (paulis.Qm(0) * paulis.Qm(0) == paulis.Qm(0))
    assert (paulis.Qp(0) * paulis.Qm(0) == QubitHamiltonian.init_zero())
    assert (paulis.Qm(0) * paulis.Qp(0) == QubitHamiltonian.init_zero())

    assert (paulis.Sp(0) * paulis.Sm(0) == paulis.Qp(0))
    assert (paulis.Sm(0) * paulis.Sp(0) == paulis.Qm(0))

    assert (paulis.Sp(0) + paulis.Sm(0) == paulis.X(0))
    assert (paulis.Qp(0) + paulis.Qm(0) == paulis.I(0))


def test_transfer_operators():
    assert (paulis.decompose_transfer_operator(ket=0, bra=0) == paulis.Qp(0))
    assert (paulis.decompose_transfer_operator(ket=0, bra=1) == paulis.Sp(0))
    assert (paulis.decompose_transfer_operator(ket=1, bra=0) == paulis.Sm(0))
    assert (paulis.decompose_transfer_operator(ket=1, bra=1) == paulis.Qm(0))

    assert (paulis.decompose_transfer_operator(ket=BitString.from_binary(binary="00"),
                                               bra=BitString.from_binary("00")) == paulis.Qp(
        0) * paulis.Qp(1))
    assert (paulis.decompose_transfer_operator(ket=BitString.from_binary(binary="01"),
                                               bra=BitString.from_binary("01")) == paulis.Qp(
        0) * paulis.Qm(1))
    assert (paulis.decompose_transfer_operator(ket=BitString.from_binary(binary="01"),
                                               bra=BitString.from_binary("10")) == paulis.Sp(
        0) * paulis.Sm(1))
    assert (paulis.decompose_transfer_operator(ket=BitString.from_binary(binary="00"),
                                               bra=BitString.from_binary("11")) == paulis.Sp(
        0) * paulis.Sp(1))

    assert (paulis.decompose_transfer_operator(ket=0, bra=0, qubits=[1]) == paulis.Qp(1))
    assert (paulis.decompose_transfer_operator(ket=1, bra=0, qubits=[1]) == paulis.Sm(1))
    assert (paulis.decompose_transfer_operator(ket=1, bra=1, qubits=[1]) == paulis.Qm(1))

@pytest.mark.parametrize("qubits", [1,2,3,4])
def test_projectors(qubits):
    real = numpy.random.uniform(0.0,1.0,2**qubits)
    imag = numpy.random.uniform(0.0,1.0,2**qubits)
    array = real + 1.j*imag
    wfn = QubitWaveFunction.from_array(arr=array)
    P = paulis.Projector(wfn=wfn.normalize())
    assert(P.is_hermitian())
    assert(wfn.apply_qubitoperator(P) == wfn)
    PM = P.to_matrix()
    assert((PM.dot(PM) == PM).all)

def test_conjugation():
    primitives = [paulis.X, paulis.Y, paulis.Z]
    factors = [1, -1, 1j, -1j, 0.5 + 1j]
    string = QubitHamiltonian.init_unit()
    cstring = QubitHamiltonian.init_unit()
    for repeat in range(10):
        for q in random.randint(0, 7, 5):
            ri = random.randint(0, 2)
            P = primitives[ri]
            sign = 1
            if ri == 1:
                sign = -1
            factor = factors[random.randint(0, len(factors) - 1)]
            cfactor = factor.conjugate()
            string *= factor * P(qubit=q)
            cstring *= cfactor * sign * P(qubit=q)

        assert (string.conjugate() == cstring)


def test_transposition():
    primitives = [paulis.X, paulis.Y, paulis.Z]
    factors = [1, -1, 1j, -1j, 0.5 + 1j]

    assert ((paulis.X(0) * paulis.X(1) * paulis.Y(2)).transpose() == -1 * paulis.X(0) * paulis.X(1) * paulis.Y(2))
    assert ((paulis.X(0) * paulis.X(1) * paulis.Z(2)).transpose() == paulis.X(0) * paulis.X(1) * paulis.Z(2))

    for repeat in range(10):
        string = QubitHamiltonian.init_unit()
        tstring = QubitHamiltonian.init_unit()
        for q in range(5):
            ri = random.randint(0, 2)
            P = primitives[ri]
            sign = 1
            if ri == 1:
                sign = -1
            factor = factors[random.randint(0, len(factors) - 1)]
            string *= factor * P(qubit=q)
            tstring *= factor * sign * P(qubit=q)

        assert (string.transpose() == tstring)


def make_random_pauliword(complex=True):
    primitives = [paulis.X, paulis.Y, paulis.Z]
    result = QubitHamiltonian.init_unit()
    for q in random.choice(range(10), 5, replace=False):
        P = primitives[random.randint(0, 2)]
        real = random.uniform(0, 1)
        imag = 0
        if complex:
            imag = random.uniform(0, 1)
        factor = real + imag * 1j
        result *= factor * P(q)
    return result


def test_dagger():
    assert (paulis.X(0).dagger() == paulis.X(0))
    assert (paulis.Y(0).dagger() == paulis.Y(0))
    assert (paulis.Z(0).dagger() == paulis.Z(0))

    for repeat in range(10):
        string = make_random_pauliword(complex=False)
        assert (string.dagger() == string)
        assert ((1j * string).dagger() == -1j * string)

def test_matrix_form():
    H = -1.0 * paulis.Z(0) -1.0 * paulis.Z(1) + 0.1 * paulis.X(0)*paulis.X(1) 
    Hm= H.to_matrix()
    assert (Hm[0,0] == -2.0)
    assert (Hm[0,3] == 0.10)
    assert (Hm[1,2] == 0.10)

    Hm2 = (H + paulis.Z(2)).to_matrix()
    Hm2p = kron(Hm, eye(2, dtype=Hm2.dtype)) + kron(eye(len(Hm), dtype=Hm2.dtype), paulis.Z(0).to_matrix())
    assert allclose(Hm2 , Hm2p)

    Hm3 = (H * paulis.Z(2)).to_matrix()
    Hm3p = kron(Hm, paulis.Z(0).to_matrix())
    assert allclose(Hm3 , Hm3p)

