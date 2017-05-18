import numpy as np
import scipy
import scipy.linalg
import scipy.io
import copy as cp
import argparse
import scipy.sparse
import scipy.sparse.linalg

from hdvv import *

class Block:
    def __init__(self):
        self.index = 0
        self.n_sites = 0
        self.sites = []
        self.lattice = [] 
        self.vectors = np.array([]) # local eigenvector matrix for block [P|Q]
        self.np     = 0            # number of p-space vectors
        self.nq     = 0            # number of q-space vectors
        self.ss_dims= []            # number of vectors in each subspace [P,Q,...]
        self.n_ss   = 0             # number of subspaces, usually 2 or 3
        self.full_dim= 1             # dimension of full space in block  

        self.Spi = {}                # matrix_rep of i'th S^+ in local basis
        self.Smi = {}                # matrix_rep of i'th S^- in local basis
        self.Szi = {}                # matrix_rep of i'th S^z in local basis

        self.H     = np.array([])    # Hamiltonian on block sublattice
        self.S2    = np.array([])    # S2 on block sublattice
        self.Sz    = np.array([])    # Sz on block sublattice

    def init(self,_index,_sites,_ss):
        """
        _index = index of block
        _sites = list of lattice sites contained in block
        _ss    = list of dimensions of vectors per subspace
        """
        self.index = _index
        self.sites = _sites
        self.n_sites = len(self.sites)
        for si in range(0,self.n_sites):
            self.full_dim *= 2
        
        vec_count = 0
        for ss in _ss:
            self.ss_dims.append(ss)
            vec_count += ss
        if (self.full_dim-vec_count) < 0:
            print "Problem setting block dimensions", self
            exit(-1)
        self.ss_dims.append(self.full_dim-vec_count)
        return 

    def __str__(self):
        out = " Block %-4i:" %(self.index)
        for si in range(0,self.n_sites):
            if si < self.n_sites-1:
                out += "%5i," %(self.sites[si])
            else:
                out += "%5i" %(self.sites[si])
        out += " : " + str(self.ss_dims)
        return out
    def extract_j12(self,j12):
        if self.n_sites == 0:
            print " No sites yet!"
        self.j12 = j12[:,self.sites][self.sites]

    def extract_lattice(self,lattice):
        if self.n_sites == 0:
            print " No sites yet!"
        self.lattice = lattice[self.sites]
    
    def form_H(self):
        self.H, tmp, self.S2, self.Sz = form_hdvv_H(self.lattice, self.j12)  # rewrite this
        self.H = self.vecs.T.dot(self.H).dot(self.vecs)
        self.S2 = self.vecs.T.dot(self.S2).dot(self.vecs)
        self.Sz = self.vecs.T.dot(self.Sz).dot(self.vecs)

    def form_site_operators(self):
        sx = .5*np.array([[0,1.],[1.,0]])
        sy = .5*np.array([[0,(0-1j)],[(0+1j),0]])
        sz = .5*np.array([[1,0],[0,-1]])
        s2 = .75*np.array([[1,0],[0,1]])
        s1 = sx + sy + sz
        I1 = np.eye(2)
 
        sp = sx + sy*(0+1j)
        sm = sx - sy*(0+1j)
 
        sp = sp.real
        sm = sm.real
        for i,s in enumerate(self.sites):
            i1 = np.eye(np.power(2,i))
            i2 = np.eye(np.power(2,self.n_sites-i-1))
            self.Spi[s] = np.kron(i1,np.kron(sp,i2))
            self.Smi[s] = np.kron(i1,np.kron(sm,i2))
            self.Szi[s] = np.kron(i1,np.kron(sz,i2))
            # Transform to P|Q basis
            self.Spi[s] = self.vecs.T.dot(self.Spi[s]).dot(self.vecs)
            self.Smi[s] = self.vecs.T.dot(self.Smi[s]).dot(self.vecs)
            self.Szi[s] = self.vecs.T.dot(self.Szi[s]).dot(self.vecs)


    def H_pp(self):
        # get view of PP block of H
        return self.H[0:self.np, 0:self.np]

    def H_ss(self,i,j):
        """ 
        Get view of space1,space2 block of H for whole block 
        where space1, space2 are the spaces of the bra and ket respectively
            i.e., H_ss(0,1) would return <P|H|Q>
        """
        if   i==0 and j==0:
            assert(self.np>0)
            return self.H[0:self.np, 0:self.np]
        elif i==1 and j==0:
            assert(self.np>0)
            assert(self.nq>0)
            return self.H[self.np:self.np+self.nq , 0:self.np]
        elif i==0 and j==1:
            assert(self.np>0)
            assert(self.nq>0)
            return self.H[0:self.np , self.np:self.np+self.nq]
        elif i==1 and j==1:
            assert(self.nq>0)
            return self.H[self.np:self.np+self.np+self.nq, self.np:self.np+self.nq]
        return self.H[0:self.np, 0:self.np]

    def S2_pp(self):
        # get view of PP block of S2 
        return self.S2[0:self.np, 0:self.np]

    def Sz_pp(self):
        # get view of PP block of Sz
        return self.Sz[0:self.np, 0:self.np]

    def Spi_pp(self,site):
        # get view of PP block of S^+ operator on site
        return self.Spi[site][0:self.np, 0:self.np]

    def Smi_pp(self,site):
        # get view of PP block of S^- operator on site
        return self.Smi[site][0:self.np, 0:self.np]

    def Szi_pp(self,site):
        # get view of PP block of S^z operator on site
        return self.Szi[site][0:self.np, 0:self.np]

    def Spi_ss(self,site,i,j):
        """ 
        Get view of space1,space2 block of S^+ operator on site
        where space1, space2 are the spaces of the bra and ket respectively
            i.e., Spi(3,0,1) would return S+ at site 3, between P and Q
            <P|S^+_i|Q>
        """
        if   i==0 and j==0:
            assert(self.np>0)
            return self.Spi[site][0:self.np, 0:self.np]
        elif i==1 and j==0:
            assert(self.np>0)
            assert(self.nq>0)
            return self.Spi[site][self.np:self.np+self.nq , 0:self.np]
        elif i==0 and j==1:
            assert(self.np>0)
            assert(self.nq>0)
            return self.Spi[site][0:self.np , self.np:self.np+self.nq]
        elif i==1 and j==1:
            assert(self.nq>0)
            return self.Spi[site][self.np:self.np+self.np+self.nq, self.np:self.np+self.nq]
    def Smi_ss(self,site,i,j):
        """ 
        Get view of space1,space2 block of S^z operator on site
        where space1, space2 are the spaces of the bra and ket respectively
            i.e., Smi(3,0,1) would return S- at site 3, between P and Q
            <P|S^-_i|Q>
        """
        if   i==0 and j==0:
            assert(self.np>0)
            return self.Smi[site][0:self.np, 0:self.np]
        elif i==1 and j==0:
            assert(self.np>0)
            assert(self.nq>0)
            return self.Smi[site][self.np:self.np+self.nq , 0:self.np]
        elif i==0 and j==1:
            assert(self.np>0)
            assert(self.nq>0)
            return self.Smi[site][0:self.np , self.np:self.np+self.nq]
        elif i==1 and j==1:
            assert(self.nq>0)
            return self.Smi[site][self.np:self.np+self.np+self.nq, self.np:self.np+self.nq]
    def Szi_ss(self,site,i,j):
        """ 
        Get view of space1,space2 block of S^z operator on site
        where space1, space2 are the spaces of the bra and ket respectively
            i.e., Szi(3,0,1) would return Sz at site 3, between P and Q
            <P|S^z_i|Q>
        """
        if   i==0 and j==0:
            assert(self.np>0)
            return self.Szi[site][0:self.np, 0:self.np]
        elif i==1 and j==0:
            assert(self.np>0)
            assert(self.nq>0)
            return self.Szi[site][self.np:self.np+self.nq , 0:self.np]
        elif i==0 and j==1:
            assert(self.np>0)
            assert(self.nq>0)
            return self.Szi[site][0:self.np , self.np:self.np+self.nq]
        elif i==1 and j==1:
            assert(self.nq>0)
            return self.Szi[site][self.np:self.np+self.np+self.nq, self.np:self.np+self.nq]





def build_dimer_H(tb_l, tb_r, Bi, Bj,j12):
    bi = Bi.index
    bj = Bj.index
    h12 = np.zeros((tb_l.block_dims[bi]*tb_l.block_dims[bj],tb_r.block_dims[bi]*tb_r.block_dims[bj]))
    for si in Bi.sites:
        for sj in Bj.sites:
    
            space_i_l = tb_l.address[Bi.index]
            space_i_r = tb_r.address[Bi.index]
            space_j_l = tb_l.address[Bj.index]
            space_j_r = tb_r.address[Bj.index]
            spi = Bi.Spi_ss(si,space_i_l,space_i_r)
            smi = Bi.Smi_ss(si,space_i_l,space_i_r)
            szi = Bi.Szi_ss(si,space_i_l,space_i_r)
            
            spj = Bj.Spi_ss(sj,space_j_l,space_j_r)
            smj = Bj.Smi_ss(sj,space_j_l,space_j_r)
            szj = Bj.Szi_ss(sj,space_j_l,space_j_r)
           
            h12  -= j12[si,sj] * np.kron(spi, smj)
            h12  -= j12[si,sj] * np.kron(smi, spj)
            h12  -= j12[si,sj] * np.kron(szi, szj) * 2
    return h12


class Tucker_Block:
    def __init__(self):
        self.id = 0         # (-1):PPP, (1):PQP, (1,3):QPQ, etc 
        self.start = 0      # starting point in super ci 
        self.stop = 0       # stopping point in super ci
        self.address = []
        self.blocks = []
        self.n_blocks = 0
        self.full_dim = 1
        self.block_dims = [] 

    def init(self,_id,blocks,add,_start):
        self.address = cp.deepcopy(add)
        self.blocks = blocks 
        self.n_blocks = len(blocks)
        self.id = _id
        self.start = _start
        for bi in range(0,self.n_blocks):
            self.full_dim *= self.blocks[bi].ss_dims[self.address[bi]]
            self.block_dims.append( self.blocks[bi].ss_dims[self.address[bi]])
        
        self.stop = self.start + self.full_dim

    def __str__(self):
        out = ""
        for a in self.address:
            out += "%3s"%a
        out += " :: "
        for a in self.block_dims:
            out += "%3s"%a
        out += " :: "+ "%i"%self.full_dim
        return out

