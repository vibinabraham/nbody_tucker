import numpy as np
import scipy
import scipy.linalg
import scipy.io
import copy as cp
import argparse
import scipy.sparse
import scipy.sparse.linalg


from hdvv import *
from block import *

def printm(m):
    # {{{
    """ print matrix """
    for r in m:
        for ri in r:
            print "% 10.13f" %ri,
        print
    # }}}

def vibin_pt2(n_blocks,lattice_blocks, tucker_blocks, tucker_blocks_pt,n_body_order,pt_order, l, v, j12, pt_type):
# {{{
    """

        E(2) = v_sA H_AX [D_XX - E_s^0]^-1 H_XA v_As

             = v_sA H_AX

        pt_type: mp or en
                
                 mp uses H1 as zeroth-order Hamiltonian
                 en uses the diagonal of H for zeroth-order
    """
    do_2b_diag = 0

    if pt_type == "mp" or pt_type == "lcc":
        do_2b_diag = 0
    elif pt_type == "en":
        do_2b_diag = 1
    else:
        print " Bad value for pt_type"
        exit(-1)

    n_roots = v.shape[1]
    e2 = np.zeros((n_roots))
    dim_tot_X = 0
    dim_tot_A = 0
    for t_l in sorted(tucker_blocks_pt):
        tb_l = tucker_blocks_pt[t_l]
        dim_tot_X += tb_l.full_dim
    for t_l in sorted(tucker_blocks):
        tb_l = tucker_blocks[t_l]
        dim_tot_A += tb_l.full_dim
    
    H_Xs = np.zeros((dim_tot_X, n_roots))
    D_X = np.zeros((dim_tot_X))
    
    for t_l in sorted(tucker_blocks_pt):
        tb_l = tucker_blocks_pt[t_l]
        D_X[tb_l.start:tb_l.stop] = build_H_diag(lattice_blocks, tb_l, tb_l, j12, do_2b_diag)

        for t_r in sorted(tucker_blocks):
            tb_r = tucker_blocks[t_r]
            hv,s2v = pt_build_H1v(lattice_blocks, tb_l, tb_r, j12,v[tb_r.start:tb_r.stop,:])
            H_Xs[tb_l.start:tb_l.stop,:] += hv

    RHv = np.array(())
    res = 1/(l-D_X)
    RHv = np.multiply(res, H_Xs[:,0]).reshape(dim_tot_X,1)
    e2 = H_Xs[:,0].T.dot(RHv)

    """
    Vibin adding stuff
    Insights:
    The variable 'l'  is the NB0 part. nroots is 1 for single referenece.
    tucker_blocks_pt always forms  +2 tuceker vectors from NBn.
    """

    #####Vibin checking SZ for diagonal##########################
    #Szzz = np.zeros((dim_tot_X,dim_tot_X)) 
    #for t_l in sorted(tucker_blocks_pt):
    #    tb_l = tucker_blocks_pt[t_l]
    #    for t_r in sorted(tucker_blocks_pt):
    #        tb_r = tucker_blocks_pt[t_r]
    #        Szzz[tb_l.start:tb_l.stop, tb_r.start:tb_r.stop],tmp = pt_build_H0Sz(lattice_blocks, tb_l, tb_r, j12)
    #printm(Szzz)
    #Szz = np.zeros((dim_tot_X,1))
    #for t_l in sorted(tucker_blocks_pt):
    #    tb_l = tucker_blocks_pt[t_l]
    #    for t_r in sorted(tucker_blocks):
    #        tb_r = tucker_blocks[t_r]
    #        Szz[tb_l.start:tb_l.stop, tb_r.start:tb_r.stop],tmp = pt_build_H0Sz(lattice_blocks, tb_l, tb_r, j12)
    #printm(Szz)
    ################################################


    print("pt 2 % 10.15f " %e2)

    HRHv,Smp3 = H1_build_tucker_blocked_sigma(n_blocks,tucker_blocks_pt, lattice_blocks, n_body_order+pt_order, j12,RHv)
    e3 = np.dot(RHv.T, HRHv)
    print("pt 3 % 10.15f " %e3)


    RHRHv = np.multiply(res,HRHv[:,0]).reshape(dim_tot_X,1)
    HRHRHv,Smp4 = H1_build_tucker_blocked_sigma(n_blocks,tucker_blocks_pt, lattice_blocks, n_body_order+pt_order, j12,RHRHv)
    e4_main = np.dot(RHv.T, HRHRHv)

    HRRH = np.dot(RHv.T,RHv)
    e4_renorm = e2 * HRRH
    #print("pt 4 % 10.15f " %e4_main)
    #print("pt 4 % 10.15f " %e4_renorm)
    e4 = e4_main - e4_renorm

    print("pt 4 % 10.15f " %e4)


    RHRHRHv = np.multiply(res, HRHRHv[:,0]).reshape(dim_tot_X,1)
    HRHRHRHv,Smp5 = H1_build_tucker_blocked_sigma(n_blocks,tucker_blocks_pt, lattice_blocks, n_body_order+pt_order, j12,RHRHRHv)
    e5_main = np.dot(RHv.T, HRHRHRHv)

    HRRHRH = np.dot(RHv.T,RHRHv)

    e5_renorm1 = 2 * e2 * HRRHRH
    e5_renorm2 = e3 * HRRH


    e5 = e5_main - e5_renorm1 - e5_renorm2

    print("pt 5 % 10.15f " %e5)

    RHRHRHRHv = np.multiply(res, HRHRHRHv[:,0]).reshape(dim_tot_X,1)
    HRHRHRHRHv,Smp5 = H1_build_tucker_blocked_sigma(n_blocks,tucker_blocks_pt, lattice_blocks, n_body_order+pt_order, j12,RHRHRHRHv)
    e6_main = np.dot(RHv.T, HRHRHRHRHv)

    print("pt 6 % 10.15f " %e6_main)


    RRHv = np.multiply(res, RHv[:,0]).reshape(dim_tot_X,1)
    RRRHv = np.multiply(res,RRHv[:,0]).reshape(dim_tot_X,1)

    HRRRH = np.dot(RHv.T,RRHv)
    HRRRRH = np.dot(RHv.T,RRRHv)

    e_8_1 = e2 * e2 * e2 * HRRRRH
    e_8_2 = e2 * e2 * HRRH * HRRRH
    e_8_3 = e2 * HRRH * HRRH * HRRH


    







    exit (-1)
    return e2
# }}}

def eqn_pt(n_blocks,lattice_blocks, tucker_blocks, tucker_blocks_pt,n_body_order,pt_order, l, v, j12, pt_type):
# {{{
    do_2b_diag = 0

    if pt_type == "lcc" or "mp":
        do_2b_diag = 0
    else:
        print " Bad value for pt_type"
        exit(-1)
    """
    C(n) = R * V * C(n-1) - sum_k  R * E(k) * C(n-k)
    
    The second term is omitted coz it is the non renormalised term and makes the method non size consistent.
    """
    var_order = 0
    var_order = n_body_order - pt_order

    n_roots = v.shape[1]
    e2 = np.zeros((n_roots))

    tucker_blocks_0 = {}
    tucker_blocks_1 = {}
    dim_tot_X = 0 #Dim of orthogonal space
    dim_tot_A = 0 #Dim of model space
    for t_l in sorted(tucker_blocks):
        if t_l[0] <= var_order:
            tb_l = cp.deepcopy(tucker_blocks[t_l])
            tb_l.start = dim_tot_A
            tb_l.stop = tb_l.start + tb_l.full_dim 
            
            tucker_blocks_0[t_l] = tb_l 
            
            dim_tot_A += tb_l.full_dim
        else:
            tb_l = cp.deepcopy(tucker_blocks[t_l])
            tb_l.start = dim_tot_X
            tb_l.stop = tb_l.start + tb_l.full_dim 
            
            tucker_blocks_1[t_l] = tb_l 
            
            dim_tot_X += tb_l.full_dim
            

    D_X = np.zeros((dim_tot_X))     #diagonal of X space
    H_Xs = np.zeros((dim_tot_X, n_roots))
    E_mpn = np.zeros((pt_order+1,n_roots))         #PT energy
    #v_n = np.zeros((dim_tot_X,n_roots))   #list of PT vectors
    v_n = np.zeros((dim_tot_X,n_roots*(pt_order+1)))   #list of PT vectors
       

    print " Configurations defining the variational space"
    for t_l in sorted(tucker_blocks_0):
        #print " 0: ", tucker_blocks_0[t_l]
        print tucker_blocks_0[t_l], " Range= %8i:%-8i" %( tucker_blocks_0[t_l].start, tucker_blocks_0[t_l].stop)
    print 
    print " Configurations defining the perturbational space"
    for t_l in sorted(tucker_blocks_1):
        print tucker_blocks_1[t_l], " Range= %8i:%-8i" %( tucker_blocks_1[t_l].start, tucker_blocks_1[t_l].stop)
        #print " 1: ", tucker_blocks_1[t_l]
  

    for t_l in sorted(tucker_blocks_1):
        tb_l = tucker_blocks_1[t_l]
        D_X[tb_l.start:tb_l.stop] = build_H_diag(lattice_blocks, tb_l, tb_l, j12, do_2b_diag)
        for t_r in sorted(tucker_blocks_0):
            tb_r = tucker_blocks_0[t_r]
            hv,s2v = pt_build_H1v(lattice_blocks, tb_l, tb_r, j12,v[tb_r.start:tb_r.stop,:])
            H_Xs[tb_l.start:tb_l.stop,:] += hv

    RHv = np.array(())
    res = 1/(l-D_X)
    RHv = np.multiply(res, H_Xs[:,0]).reshape(dim_tot_X,1)
    e2 = H_Xs[:,0].T.dot(RHv)

    print("pt 2 % 10.15f " %e2)

    HRHv,Smp3 = H1_build_tucker_blocked_sigma(n_blocks,tucker_blocks_1, lattice_blocks, n_body_order+pt_order, j12,RHv)
    e3 = np.dot(RHv.T, HRHv)
    print("pt 3 % 10.15f " %e3)


    RHRHv = np.multiply(res,HRHv[:,0]).reshape(dim_tot_X,1)
    HRHRHv,Smp4 = H1_build_tucker_blocked_sigma(n_blocks,tucker_blocks_1, lattice_blocks, n_body_order+pt_order, j12,RHRHv)
    e4_main = np.dot(RHv.T, HRHRHv)

    HRRH = np.dot(RHv.T,RHv)
    e4_renorm = e2 * HRRH
    #print("pt 4 % 10.15f " %e4_main)
    #print("pt 4 % 10.15f " %e4_renorm)
    e4 = e4_main - e4_renorm

    print("pt 4 % 10.15f " %e4)


    RHRHRHv = np.multiply(res, HRHRHv[:,0]).reshape(dim_tot_X,1)
    HRHRHRHv,Smp5 = H1_build_tucker_blocked_sigma(n_blocks,tucker_blocks_1, lattice_blocks, n_body_order+pt_order, j12,RHRHRHv)
    e5_main = np.dot(RHv.T, HRHRHRHv)

    HRRHRH = np.dot(RHv.T,RHRHv)

    e5_renorm1 = 2 * e2 * HRRHRH
    e5_renorm2 = e3 * HRRH


    e5 = e5_main - e5_renorm1 - e5_renorm2

    print("pt 5 % 10.15f " %e5)


    #
    RRHv = np.multiply(res, RHv[:,0]).reshape(dim_tot_X,1)
    RRRHv = np.multiply(res,RRHv[:,0]).reshape(dim_tot_X,1)

    HRRRH = np.dot(RHv.T,RRHv)
    HRRRRH = np.dot(RHv.T,RRRHv)
    #

    #E6
    RHRHRHRHv = np.multiply(res, HRHRHRHv[:,0]).reshape(dim_tot_X,1)
    HRHRHRHRHv,Smp5 = H1_build_tucker_blocked_sigma(n_blocks,tucker_blocks_1, lattice_blocks, n_body_order+pt_order, j12,RHRHRHRHv)
    e6_main = np.dot(RHv.T, HRHRHRHRHv)

    print("pt 6 main % 10.15f " %e6_main)


    RRHRHv = np.multiply(res, RHRHv[:,0]).reshape(dim_tot_X,1)
    HRRHRHv,Smp5 = H1_build_tucker_blocked_sigma(n_blocks,tucker_blocks_1, lattice_blocks, n_body_order+pt_order, j12,RRHRHv)
    HRHRRHRH = np.dot(RHv.T,HRRHRHv)
    e6_renorm1 = e2 * HRHRRHRH


    HRRHRHRH = np.dot(RHv.T,RHRHRHv)
    e6_renorm2 = 2 * e2 * HRRHRHRH



    HRRHRH = np.dot(RHv.T,RHRHv)
    e6_renorm3 = 2 * e3 * HRRHRH


    e6_renorm4 =  e4_main * HRRH 

    e6_renorm5 =  e2 * e2 * HRRRH  

    e6_renorm6 =  e2 * HRRH * HRRH  

    e6 = e6_main - e6_renorm1 - e6_renorm2 - e6_renorm3 - e6_renorm4 + e6_renorm5 + e6_renorm6

    print("pt 6 r1 % 10.15f " %e6_renorm1)
    print("pt 6 r2 % 10.15f " %e6_renorm2)
    print("pt 6 r3 % 10.15f " %e6_renorm3)
    print("pt 6 r4 % 10.15f " %e6_renorm4)
    print("pt 6 r5 % 10.15f " %e6_renorm5)
    print("pt 6 r6 % 10.15f " %e6_renorm6)
    print("")
    print("pt 6    % 10.15f " %e6)

    #e_8_1 = e2 * e2 * e2 * HRRRRH
    #e_8_2 = e2 * e2 * HRRH * HRRRH
    #e_8_3 = e2 * HRRH * HRRH * HRRH

    #e8_cut = 4 * e_8_1 + 12 * e_8_2 + 4 * e_8_3

    #print("pt8ct % 10.15f " %e8_cut)



    exit (-1)
    return e2
# }}}

def PT_mp(n_blocks,lattice_blocks, tucker_blocks, tucker_blocks_pt,n_body_order,pt_order, l, v, j12, pt_type,pt_mit):
# {{{
    do_2b_diag = 0

    if pt_type == "lcc" or "mp":
        do_2b_diag = 0
    else:
        print " Bad value for pt_type"
        exit(-1)
    """
    C(n) = R * V * C(n-1) - sum_k  R * E(k) * C(n-k)
    
    The second term is omitted coz it is the non renormalised term and makes the method non size consistent.
    """
    var_order = 0
    var_order = n_body_order - pt_order

    n_roots = v.shape[1]
    e2 = np.zeros((n_roots))

    if pt_mit > pt_order :
        print("Method may not be extensive")

    tucker_blocks_0 = {}
    tucker_blocks_1 = {}
    dim_tot_X = 0 #Dim of orthogonal space
    dim_tot_A = 0 #Dim of model space
    for t_l in sorted(tucker_blocks):
        if t_l[0] <= var_order:
            tb_l = cp.deepcopy(tucker_blocks[t_l])
            tb_l.start = dim_tot_A
            tb_l.stop = tb_l.start + tb_l.full_dim 
            
            tucker_blocks_0[t_l] = tb_l 
            
            dim_tot_A += tb_l.full_dim
        else:
            tb_l = cp.deepcopy(tucker_blocks[t_l])
            tb_l.start = dim_tot_X
            tb_l.stop = tb_l.start + tb_l.full_dim 
            
            tucker_blocks_1[t_l] = tb_l 
            
            dim_tot_X += tb_l.full_dim
            

    D_X = np.zeros((dim_tot_X))     #diagonal of X space
    H_Xs = np.zeros((dim_tot_X, n_roots))
    E_mpn = np.zeros((pt_mit+1,n_roots))         #PT energy
    #v_n = np.zeros((dim_tot_X,n_roots))   #list of PT vectors
    v_n = np.zeros((dim_tot_X,n_roots*(pt_mit+1)))   #list of PT vectors
       

    print " Configurations defining the variational space"
    for t_l in sorted(tucker_blocks_0):
        #print " 0: ", tucker_blocks_0[t_l]
        print tucker_blocks_0[t_l], " Range= %8i:%-8i" %( tucker_blocks_0[t_l].start, tucker_blocks_0[t_l].stop)
    print 
    print " Configurations defining the perturbational space"
    for t_l in sorted(tucker_blocks_1):
        print tucker_blocks_1[t_l], " Range= %8i:%-8i" %( tucker_blocks_1[t_l].start, tucker_blocks_1[t_l].stop)
        #print " 1: ", tucker_blocks_1[t_l]
  

    for t_l in sorted(tucker_blocks_1):
        tb_l = tucker_blocks_1[t_l]
        D_X[tb_l.start:tb_l.stop] = build_H_diag(lattice_blocks, tb_l, tb_l, j12, do_2b_diag)
        for t_r in sorted(tucker_blocks_0):
            tb_r = tucker_blocks_0[t_r]
            hv,s2v = pt_build_H1v(lattice_blocks, tb_l, tb_r, j12,v[tb_r.start:tb_r.stop,:])
            H_Xs[tb_l.start:tb_l.stop,:] += hv


    H_Xs = H_Xs.reshape(dim_tot_X,n_roots)

    v_lcc = np.zeros((dim_tot_X,n_roots))   #list of PT vectors
    v_upper = np.zeros((dim_tot_A,n_roots))   #list of PT vectors

    E_corr = np.zeros(n_roots)
    
    
    #first_order_E = np.zeros((n_roots,n_roots))
    first_order_E = H_Xs[0:n_roots,:]
    first_order_E = v.dot(first_order_E)


    print
    print "     PT correction   "

    
    ##truncate at given order for extensive result
    pt_mit = pt_order-1

    for s in range(0, n_roots):
        res = 1/(l[s]-D_X)
        v_n[: ,s] = np.multiply(res, H_Xs[:,s])
        E_mpn[0,s] = np.dot(H_Xs[:,s].T,v_n[:,s])
        #DHv = np.multiply(res, H_Xs[:,s])
        #e2[s] = H_Xs[:,s].T.dot(DHv)
        v_lcc[:,s] = v_n[:,s] 

        print " %6s  %16s  %16s " %("Order","Correction","Energy")
        print " %6i  %16.8f  %16.8f " %(1,first_order_E[0,s],E_corr[s])

        E_corr[s] = E_mpn[0,s] 
        print " %6i  %16.8f  %16.8f " %(2,E_mpn[0,s],E_corr[s])

        #for i in range(1,pt_order-1):
        for i in range(1,pt_mit):
            h1,S1 = H1_build_tucker_blocked_sigma(n_blocks,tucker_blocks_1, lattice_blocks, n_body_order, j12,v_n[:,(i-1)*n_roots+s].reshape(dim_tot_X,1))
            v_n[:,i*n_roots+s] = h1.reshape(dim_tot_X)
            #RENORMALISED TERMS
            for k in range(0,i):
                v_n[:,i*n_roots+s] -= np.multiply(E_mpn[k-1,s],v_n[:,(i-k-1)*n_roots+s].reshape(dim_tot_X))


            v_n[:,i*n_roots+s] = np.multiply(res,v_n[:,i*n_roots+s])

            E_mpn[i,s] = np.dot(H_Xs[:,s].T, v_n[:,i*n_roots+s])
            E_corr[s] += E_mpn[i,s]
            #print " %6i  %16.8f  %16.8f " %(i+2,E_mpn[i,s],E_corr[s]+E_mpn[i,s])
            print " %6i  %16.8f  %16.8f " %(i+2,E_mpn[i,s],E_corr[s])
            v_lcc[:,s] += v_n[:,i*n_roots+s].reshape(dim_tot_X)
         
                
        v_upper[:,s] = v[0:dim_tot_A,s]
        #print "Correlation %16.8f " %(E_corr[s])


    #v = np.append(v,v_n[:,0]).reshape(dim_tot_X+dim_tot_A,1)
    #print v_upper.shape
    #print v_lcc.shape
    v_lcc = np.append(v_upper,v_lcc).reshape(dim_tot_X+dim_tot_A,n_roots)
    #printm(E_mpn)
    np.set_printoptions(suppress = True, precision = 5, linewidth=200)
    #print(v_lcc)
    
    norm = np.linalg.norm(v_lcc)
    print
    print "Norm of the PT vector:    %16.8f " %(norm)
    v_lcc = v_lcc/norm
    return E_corr, v_lcc
# }}}

def PT_lcc_3(n_blocks,lattice_blocks, tucker_blocks, tucker_blocks_pt,n_body_order,pt_order, l, v, j12, pt_type,n):
# {{{
    do_2b_diag = 0

    if pt_type == "lcc" or "mp":
        do_2b_diag = 0
    else:
        print " Bad value for pt_type"
        exit(-1)
    """
    C(n) = R * V * C(n-1) - sum_k  R * E(k) * C(n-k)
    
    The second term is omitted coz it is the non renormalised term and makes the method non size consistent.
    """
    n = n-1
    var_order = 0
    var_order = n_body_order - pt_order

    n_roots = v.shape[1]
    e2 = np.zeros((n_roots))

    tucker_blocks_0 = {}
    tucker_blocks_1 = {}
    dim_tot_X = 0 #Dim of orthogonal space
    dim_tot_A = 0 #Dim of model space
    for t_l in sorted(tucker_blocks):
        if t_l[0] <= var_order:
            tb_l = cp.deepcopy(tucker_blocks[t_l])
            tb_l.start = dim_tot_A
            tb_l.stop = tb_l.start + tb_l.full_dim 
            
            tucker_blocks_0[t_l] = tb_l 
            
            dim_tot_A += tb_l.full_dim
        else:
            tb_l = cp.deepcopy(tucker_blocks[t_l])
            tb_l.start = dim_tot_X
            tb_l.stop = tb_l.start + tb_l.full_dim 
            
            tucker_blocks_1[t_l] = tb_l 
            
            dim_tot_X += tb_l.full_dim
            

    D_X = np.zeros((dim_tot_X))     #diagonal of X space
    H_Xs = np.zeros((dim_tot_X, n_roots))
    E_mpn = np.zeros((n+1,n_roots))         #PT energy
    v_n = np.zeros((dim_tot_X,n_roots))   #list of PT vectors
       

    print " Configurations defining the variational space"
    for t_l in sorted(tucker_blocks_0):
        #print " 0: ", tucker_blocks_0[t_l]
        print tucker_blocks_0[t_l], " Range= %8i:%-8i" %( tucker_blocks_0[t_l].start, tucker_blocks_0[t_l].stop)
    print 
    print " Configurations defining the perturbational space"
    for t_l in sorted(tucker_blocks_1):
        print tucker_blocks_1[t_l], " Range= %8i:%-8i" %( tucker_blocks_1[t_l].start, tucker_blocks_1[t_l].stop)
        #print " 1: ", tucker_blocks_1[t_l]
  

    for t_l in sorted(tucker_blocks_1):
        tb_l = tucker_blocks_1[t_l]
        D_X[tb_l.start:tb_l.stop] = build_H_diag(lattice_blocks, tb_l, tb_l, j12, do_2b_diag)
        for t_r in sorted(tucker_blocks_0):
            tb_r = tucker_blocks_0[t_r]
            hv,s2v = pt_build_H1v(lattice_blocks, tb_l, tb_r, j12,v[tb_r.start:tb_r.stop,:])
            H_Xs[tb_l.start:tb_l.stop,:] += hv

    #print v
    #print l
    #print H_Xs
    #print D_X

    H_Xs = H_Xs.reshape(dim_tot_X,n_roots)

    v_lcc = np.zeros((dim_tot_X,n_roots))   #list of PT vectors
    v_upper = np.zeros((dim_tot_A,n_roots))   #list of PT vectors

    E_corr = np.zeros(n_roots)
    
    print
    print "     LCC Iterations"
    for s in range(0, n_roots):
        res = 1/(l[s]-D_X)
        v_n[: ,s] = np.multiply(res, H_Xs[:,s])
        E_mpn[0,s] = np.dot(H_Xs[:,s].T,v_n[:,s])
        #DHv = np.multiply(res, H_Xs[:,s])
        #e2[s] = H_Xs[:,s].T.dot(DHv)
        v_lcc[:,s] = v_n[:,s] 
        E_corr[s] = E_mpn[0,s] 

        print " %6s  %16s  %16s " %("Order","Correction","Energy")
        print " %6i  %16.8f  %16.8f " %(2,E_mpn[0,s],E_corr[s])

        for i in range(1,n):
            h1,S1 = H1_build_tucker_blocked_sigma(n_blocks,tucker_blocks_1, lattice_blocks, n_body_order, j12,v_n[:,s].reshape(dim_tot_X,1))
            v_n[:,s] = h1.reshape(dim_tot_X)
            v_n[:,s] = np.multiply(res,v_n[:,s]) 

            E_mpn[i,s] = np.dot(H_Xs[:,s].T, v_n[:,s])
            E_corr[s] += E_mpn[i,s]
            print " %6i  %16.8f  %16.8f " %(i+2,E_mpn[i,s],E_corr[s])
            v_lcc[:,s] += v_n[:,s].reshape(dim_tot_X)
         
            if max(abs(E_mpn[i+1,s]),abs(E_mpn[i,s])) < 1e-8:
                print "LCC Converged"
                break
            elif i+1 == n:
                print
                print " Converged only upto  %12.1e order " %(abs(E_mpn[i+1,s]-E_mpn[i,s]))
                
        v_upper[:,s] = v[0:dim_tot_A,s]
        #print "Correlation %16.8f " %(E_corr[s])

    #v = np.append(v,v_n[:,0]).reshape(dim_tot_X+dim_tot_A,1)
    #print v_upper.shape
    #print v_lcc.shape
    v_lcc = np.append(v_upper,v_lcc).reshape(dim_tot_X+dim_tot_A,n_roots)
    #printm(E_mpn)
    np.set_printoptions(suppress = True, precision = 5, linewidth=200)
    #print(v_lcc)
    
    norm = np.linalg.norm(v_lcc)
    print
    print "Norm of the LCC vector:    %16.8f " %(norm)
    v_lcc = v_lcc/norm
    return E_corr, v_lcc

# }}}

def PT_lcc_2(n_blocks,lattice_blocks, tucker_blocks, tucker_blocks_pt,n_body_order,pt_order, l, v, j12, pt_type):
    do_2b_diag = 0# {{{

    if pt_type == "lcc":
        do_2b_diag = 0
    else:
        print " Bad value for pt_type"
        exit(-1)
    """
    C(n) = R * V * C(n-1) - sum_k  R * E(k) * C(n-k)
    
    The second term is omitted coz it is the non renormalised term and makes the method non size consistent.
    """
    n = 20 #the order of wf

    n_roots = v.shape[1]
    e2 = np.zeros((n_roots))


    dim_tot_X = 0 #Dim of orthogonal space
    dim_tot_A = 0 #Dim of model space
    for t_l in sorted(tucker_blocks_pt):
        tb_l = tucker_blocks_pt[t_l]
        dim_tot_X += tb_l.full_dim
    for t_l in sorted(tucker_blocks):
        tb_l = tucker_blocks[t_l]
        dim_tot_A += tb_l.full_dim

    D_X = np.zeros((dim_tot_X))     #diagonal of X space
    H_Xs = np.zeros((dim_tot_X, n_roots))
    E_mpn = np.zeros((n+1,n_roots))         #PT energy
    v_n = np.zeros((dim_tot_X,n_roots))   #list of PT vectors
       

    #Forming the resolvent

    for t_l in sorted(tucker_blocks_pt):
        tb_l = tucker_blocks_pt[t_l]
        D_X[tb_l.start:tb_l.stop] = build_H_diag(lattice_blocks, tb_l, tb_l, j12, do_2b_diag)
        for t_r in sorted(tucker_blocks):
            tb_r = tucker_blocks[t_r]
            hv,s2v = pt_build_H1v(lattice_blocks, tb_l, tb_r, j12,v[tb_r.start:tb_r.stop,:])
            H_Xs[tb_l.start:tb_l.stop,:] += hv

    #print v
    #print l
    #print H_Xs
    #print D_X

    H_Xs = H_Xs.reshape(dim_tot_X,n_roots)
    E_corr = np.zeros(n_roots)

    for s in range(0, n_roots):
        res = 1/(l[s]-D_X)
        v_n[: ,s] = np.multiply(res, H_Xs[:,s])
        E_mpn[0,s] = np.dot(H_Xs[:,s].T,v_n[:,s])
        #DHv = np.multiply(res, H_Xs[:,s])
        #e2[s] = H_Xs[:,s].T.dot(DHv)

        E_corr[s] = E_mpn[0,s] 
        print " %6i  %16.8f  %16.8f " %(1,E_mpn[0,s],E_corr[s])

        for i in range(1,n):
            h1,S1 = H1_build_tucker_blocked_sigma(n_blocks,tucker_blocks_pt, lattice_blocks, n_body_order+pt_order, j12,v_n[:,s].reshape(dim_tot_X,1))
            v_n[:,s] = h1.reshape(dim_tot_X)
            v_n[:,s] = np.multiply(res,v_n[:,s]) 
            E_mpn[i,s] = np.dot(H_Xs[:,s].T, v_n[:,s])
            #print " %6i  %16.8f  %16.8f " %(i+1,E_mpn[i],E_corr)
            #E_corr += E_mpn[i+1]
            E_corr[s] += E_mpn[i,s]
            print " %6i  %16.8f  %16.8f " %(i+1,E_mpn[i,s],E_corr)
         
            if max(abs(E_mpn[i+1,s]),abs(E_mpn[i,s])) < 1e-8:
                break
        print "Correlation %16.8f " %(E_corr[s])

    v = np.append(v,v_n[:,0]).reshape(dim_tot_X+dim_tot_A,n_roots)
    #printm(v)

    return v# }}}

def PT_lcc(n_blocks,lattice_blocks, tucker_blocks, tucker_blocks_pt,n_body_order,pt_order, l, v, j12, pt_type):
# {{{
    do_2b_diag = 0

    if pt_type == "lcc":
        do_2b_diag = 0
    else:
        print " Bad value for pt_type"
        exit(-1)
    """
    C(n) = R * V * C(n-1) - sum_k  R * E(k) * C(n-k)
    
    The second term is omitted coz it is the non renormalised term and makes the method non size consistent.
    """
    n = 10 #the order of wf

    dim_tot_X = 0 #Dim of orthogonal space
    dim_tot_A = 0 #Dim of model space
    for t_l in sorted(tucker_blocks_pt):
        tb_l = tucker_blocks_pt[t_l]
        dim_tot_X += tb_l.full_dim
    for t_l in sorted(tucker_blocks):
        tb_l = tucker_blocks[t_l]
        dim_tot_A += tb_l.full_dim

    D_X = np.zeros((dim_tot_X))     #diagonal of X space
    H_Xs = np.zeros((dim_tot_X, 1))
    E_mpn = np.zeros((n+2))         #PT energy
    v_n = np.zeros((dim_tot_X,1))   #list of PT vectors
       

    #Forming the resolvent

    for t_l in sorted(tucker_blocks_pt):
        tb_l = tucker_blocks_pt[t_l]
        D_X[tb_l.start:tb_l.stop] = build_H_diag(lattice_blocks, tb_l, tb_l, j12, do_2b_diag)
        for t_r in sorted(tucker_blocks):
            tb_r = tucker_blocks[t_r]
            hv,s2v = pt_build_H1v(lattice_blocks, tb_l, tb_r, j12,v[tb_r.start:tb_r.stop,:])
            H_Xs[tb_l.start:tb_l.stop,:] += hv

    res = 1/(l - D_X) 



    #First order wavefunction
    H_Xs = H_Xs.reshape(dim_tot_X)
    v_n[: ,0] = np.multiply(res, H_Xs)

    #Second order energy
    E_mpn[1] = np.dot(H_Xs.T,v_n[:,0])
    emp2 = E_mpn[1]
       
    print " %6s  %16s  %16s " %("Order","Correction","Energy")
    print " %6i  %16.8f  %16.8f " %(1,E_mpn[0], 0.0)
    E_corr = E_mpn[1] 
    for i in range(1,n):
        h1,S1 = H1_build_tucker_blocked_sigma(n_blocks,tucker_blocks_pt, lattice_blocks, n_body_order+pt_order, j12,v_n[:,0].reshape(dim_tot_X,1))
        v_n[:,0] = h1.reshape(dim_tot_X)
        v_n[:,0] = np.multiply(res,v_n[:,0]) 
        E_mpn[i+1] = np.dot(H_Xs.T, v_n[:,0])
        print " %6i  %16.8f  %16.8f " %(i+1,E_mpn[i],E_corr)
        E_corr += E_mpn[i+1]
       
        if max(abs(E_mpn[i+1]),abs(E_mpn[i])) < 1e-8:
            break
    return E_corr

# }}}

def PT_nth_vector(n_blocks,lattice_blocks, tucker_blocks, tucker_blocks_pt,n_body_order,pt_order, l, v, j12, pt_type):
# {{{
    do_2b_diag = 0

    if pt_type == "lcc":
        do_2b_diag = 0
    else:
        print " Bad value for pt_type"
        exit(-1)
    """

    C(n) = R * V * C(n-1) - sum_k  R * E(k) * C(n-k)
    
    The second term is omitted coz it is the non renormalised term and makes the method non size consistent.

    """
    n = 40 #the order of wf

    dim_tot_X = 0 #Dim of orthogonal space
    dim_tot_A = 0 #Dim of model space
    for t_l in sorted(tucker_blocks_pt):
        tb_l = tucker_blocks_pt[t_l]
        dim_tot_X += tb_l.full_dim
    for t_l in sorted(tucker_blocks):
        tb_l = tucker_blocks[t_l]
        dim_tot_A += tb_l.full_dim

    D_X = np.zeros((dim_tot_X))     #diagonal of X space
    H_Xs = np.zeros((dim_tot_X, 1))
    E_mpn = np.zeros((n+2))         #PT energy
    v_n = np.zeros((dim_tot_X,n+1))   #list of PT vectors
       

    #Forming the resolvent

    for t_l in sorted(tucker_blocks_pt):
        tb_l = tucker_blocks_pt[t_l]
        D_X[tb_l.start:tb_l.stop] = build_H_diag(lattice_blocks, tb_l, tb_l, j12, do_2b_diag)
        for t_r in sorted(tucker_blocks):
            tb_r = tucker_blocks[t_r]
            hv,s2v = pt_build_H1v(lattice_blocks, tb_l, tb_r, j12,v[tb_r.start:tb_r.stop,:])
            H_Xs[tb_l.start:tb_l.stop,:] += hv

    res = 1/(l - D_X) 



    #First order wavefunction
    H_Xs = H_Xs.reshape(dim_tot_X)
    v_n[: ,0] = np.multiply(res, H_Xs)

    #Second order energy
    E_mpn[1] = np.dot(H_Xs.T,v_n[:,0])
    emp2 = E_mpn[1]
    

    vv_n = 0
    wigner = np.zeros((2*n+2))
       
    E_corr = E_mpn[1] 

    print " %6s  %16s  %16s " %("Order","Correction","Energy")
    print " %6i  %16.8f  %16.8f " %(1,E_mpn[0], 0.0)
    E_corr = E_mpn[1] 
    for i in range(1,n):
        h1,S1 = H1_build_tucker_blocked_sigma(n_blocks,tucker_blocks_pt, lattice_blocks, n_body_order+pt_order, j12,v_n[:,i-1].reshape(dim_tot_X,1))
        v_n[:,i] = h1.reshape(dim_tot_X)

        ##RENORMALISED TERMS
        #for k in range(0,i):
        #    v_n[:,i] -= np.multiply(E_mpn[k],v_n[:,i-k-1].reshape(dim_tot_X))

        ##RENORMALISED TERMS for size consistent part
        #if i < pt_order/2:
        #    for k in range(0,pt_order):
        #        v_n[:,i] -= np.multiply(E_mpn[k],v_n[:,i-k-1].reshape(dim_tot_X))

        v_n[:,i] = np.multiply(res,v_n[:,i]) 
        E_mpn[i+1] = np.dot(H_Xs.T, v_n[:,i])
        wigner[i] = E_mpn[i]
        print " %6i  %16.8f  %16.8f " %(i+1,E_mpn[i],E_corr)
        E_corr += E_mpn[i+1]
       
        if max(abs(E_mpn[i+1]),abs(E_mpn[i])) < 1e-8:
            break
        #if i >= n/2-1:
        #    wigner[2*i+1] = np.dot(vv_n1,v_n[:,i]) 
        #    h2,S2 = H1_build_tucker_blocked_sigma(n_blocks,tucker_blocks_pt, lattice_blocks, n_body_order+pt_order, j12,v_n[:,i].reshape(dim_tot_X,1))
        #    vv_n2 = h2.reshape(dim_tot_X)
        #    wigner[2*i+2] = np.dot(vv_n2,v_n[:,i])


    return E_corr
# }}}

def pt_build_H1(blocks,tb_l, tb_r,j12):
  # {{{
    """
    Build the Hamiltonian between two tensor blocks, tb_l and tb_r, without ever constructing a full hilbert space

    Forming H1
    """

    n_blocks = len(blocks)
    assert(n_blocks == tb_l.n_blocks)
    assert(n_blocks == tb_r.n_blocks)
    H_dim_layout = []  # dimensions of Ham block as a tensor (d1,d2,..,d1',d2',...)
    H_dim_layout = np.append(tb_l.block_dims,tb_r.block_dims)
   
    """
    form one-block and two-block terms of H separately
        1-body

            for each block, form Hamiltonian in subspace, and combine
            with identity on other blocks

        2-body
            
            for each block-dimer, form Hamiltonian in subspace, and combine
            with identity on other blocks
    """
    # How many blocks are different between left and right?
    different = []
    for bi in range(0,n_blocks):
        if tb_l.address[bi] != tb_r.address[bi]:
            different.append(bi)
    #if len(different) > 2:
    #    print " Nothing to do, why are we here?"
    #    exit(-1)
    
    H  = np.zeros((tb_l.full_dim,tb_r.full_dim))
    S2 = np.zeros((tb_l.full_dim,tb_r.full_dim))
   
    #print " Ham block size", H.shape, H_dim_layout
    H.shape = H_dim_layout
    S2.shape = H_dim_layout
    #   Add up all the one-body contributions, making sure that the results is properly dimensioned for the 
    #   target subspace

    if len(different) == 0:

        assert(tb_l.full_dim == tb_r.full_dim)
        full_dim = tb_l.full_dim
        #<abcd|H1+H2+H3+H4|abcd>
        
        
        #   <ab|H12|ab> Ic Id
        # + <ac|H13|ac> Ib Id
        # + Ia <bc|H23|bc> Id + etc
        
        for bi in range(0,n_blocks):
            for bj in range(bi+1,n_blocks):
                Bi = blocks[bi]
                Bj = blocks[bj]
                dim_e = full_dim / tb_l.block_dims[bi] / tb_l.block_dims[bj]

                #build full Hamiltonian on sublattice
                h2,s2 = build_dimer_H(tb_l, tb_r, Bi, Bj, j12)
                h2.shape = (tb_l.block_dims[bi],tb_l.block_dims[bj],tb_r.block_dims[bi],tb_r.block_dims[bj])
                s2.shape = (tb_l.block_dims[bi],tb_l.block_dims[bj],tb_r.block_dims[bi],tb_r.block_dims[bj])

                #h = np.kron(h12,np.eye(dim_e))   
            
                tens_inds    = []
                tens_inds.extend([bi,bj])
                tens_inds.extend([bi+n_blocks, bj+n_blocks])
                for bk in range(0,n_blocks):
                    if (bk != bi) and (bk != bj):
                        tens_inds.extend([bk])
                        tens_inds.extend([bk+n_blocks])
                        assert(tb_l.block_dims[bk] == tb_r.block_dims[bk] )
                        h2 = np.tensordot(h2,np.eye(tb_l.block_dims[bk]),axes=0)
                        s2 = np.tensordot(s2,np.eye(tb_l.block_dims[bk]),axes=0)
               
                sort_ind = np.argsort(tens_inds)
               
                H  += h2.transpose(sort_ind)
                S2 += s2.transpose(sort_ind)
    
    
    
    
    
    
    elif len(different) == 1:

        full_dim_l = tb_l.full_dim
        full_dim_r = tb_r.full_dim
        #<abcd|H1+H2+H3+H4|abcd>
        #
        #   <a|H1|a> Ib Ic Id  , for block 1 being different


        bi = different[0] 

        Bi = blocks[bi]
        dim_e_l = full_dim_l / tb_l.block_dims[bi] 
        dim_e_r = full_dim_r / tb_r.block_dims[bi] 
        h1 = Bi.H_ss(tb_l.address[bi],tb_r.address[bi])
        s1 = Bi.S2_ss(tb_l.address[bi],tb_r.address[bi])

        h1.shape = (tb_l.block_dims[bi],tb_r.block_dims[bi])
        s1.shape = (tb_l.block_dims[bi],tb_r.block_dims[bi])

        assert(dim_e_l == dim_e_r)
        dim_e = dim_e_l
       
        
        tens_inds    = []
        tens_inds.extend([bi])
        tens_inds.extend([bi+n_blocks])
        
        
        #   <ab|H12|Ab> Ic Id
        # + <ac|H13|Ac> Ib Id
        # + <ad|H13|Ad> Ib Id
        
        for bj in range(0,bi):
            Bj = blocks[bj]
            dim_e_l = full_dim_l / tb_l.block_dims[bi] / tb_l.block_dims[bj]
            dim_e_r = full_dim_r / tb_r.block_dims[bi] / tb_r.block_dims[bj]
         
            assert(dim_e_l == dim_e_r)
            dim_e = dim_e_l
            
            #build full Hamiltonian on sublattice
            #h12 = build_dimer_H(tb_l, tb_r, Bi, Bj, j12)
            h2,s2 = build_dimer_H(tb_l, tb_r, Bj, Bi, j12)
          
            h2.shape = (tb_l.block_dims[bj],tb_l.block_dims[bi],tb_r.block_dims[bj],tb_r.block_dims[bi])
            s2.shape = (tb_l.block_dims[bj],tb_l.block_dims[bi],tb_r.block_dims[bj],tb_r.block_dims[bi])
         
            
            #h = np.kron(h12,np.eye(dim_e))   
            
            tens_dims    = []
            tens_inds    = []
            tens_inds.extend([bj,bi])
            tens_inds.extend([bj+n_blocks, bi+n_blocks])
            for bk in range(0,n_blocks):
                if (bk != bi) and (bk != bj):
                    tens_inds.extend([bk])
                    tens_inds.extend([bk+n_blocks])
                    assert(tb_l.block_dims[bk] == tb_r.block_dims[bk] )
                    h2 = np.tensordot(h2,np.eye(tb_l.block_dims[bk]),axes=0)
                    s2 = np.tensordot(s2,np.eye(tb_l.block_dims[bk]),axes=0)
            
            sort_ind = np.argsort(tens_inds)
            H  += h2.transpose(sort_ind)
            S2 += s2.transpose(sort_ind)
        
        for bj in range(bi+1, n_blocks):
            Bj = blocks[bj]
            dim_e_l = full_dim_l / tb_l.block_dims[bi] / tb_l.block_dims[bj]
            dim_e_r = full_dim_r / tb_r.block_dims[bi] / tb_r.block_dims[bj]
         
            assert(dim_e_l == dim_e_r)
            dim_e = dim_e_l
            
            #build full Hamiltonian on sublattice
            #h12 = build_dimer_H(tb_l, tb_r, Bi, Bj, j12)
            h2,s2 = build_dimer_H(tb_l, tb_r, Bi, Bj, j12)
          
            h2.shape = (tb_l.block_dims[bi],tb_l.block_dims[bj],tb_r.block_dims[bi],tb_r.block_dims[bj])
            s2.shape = (tb_l.block_dims[bi],tb_l.block_dims[bj],tb_r.block_dims[bi],tb_r.block_dims[bj])
         
            
            #h = np.kron(h12,np.eye(dim_e))   
            
            tens_dims    = []
            tens_inds    = []
            tens_inds.extend([bi,bj])
            tens_inds.extend([bi+n_blocks, bj+n_blocks])
            for bk in range(0,n_blocks):
                if (bk != bi) and (bk != bj):
                    tens_inds.extend([bk])
                    tens_inds.extend([bk+n_blocks])
                    assert(tb_l.block_dims[bk] == tb_r.block_dims[bk] )
                    h2 = np.tensordot(h2,np.eye(tb_l.block_dims[bk]),axes=0)
                    s2 = np.tensordot(s2,np.eye(tb_l.block_dims[bk]),axes=0)
            
            sort_ind = np.argsort(tens_inds)
            H  += h2.transpose(sort_ind)
            S2 += s2.transpose(sort_ind)
    
    
    
    
    elif len(different) == 2:
    
        full_dim_l = tb_l.full_dim
        full_dim_r = tb_r.full_dim
        #<abcd|H1+H2+H3+H4|abcd> = 0


        bi = different[0] 
        bj = different[1] 

        Bi = blocks[bi]
        Bj = blocks[bj]

        dim_e_l = full_dim_l / tb_l.block_dims[bi] / tb_l.block_dims[bj] 
        dim_e_r = full_dim_r / tb_r.block_dims[bi] / tb_r.block_dims[bj] 

        assert(dim_e_l == dim_e_r)
        dim_e = dim_e_l
        
        
        #  <ac|H13|Ac> Ib Id  for 1 3 different
        
        #build full Hamiltonian on sublattice
        #h12 = build_dimer_H(tb_l, tb_r, Bi, Bj, j12)
        h2,s2 = build_dimer_H(tb_l, tb_r, Bi, Bj, j12)
       
        h2.shape = (tb_l.block_dims[bi],tb_l.block_dims[bj],tb_r.block_dims[bi],tb_r.block_dims[bj])
        s2.shape = (tb_l.block_dims[bi],tb_l.block_dims[bj],tb_r.block_dims[bi],tb_r.block_dims[bj])
        #h2 = np.kron(h12,np.eye(dim_e))   
        
        tens_dims    = []
        tens_inds    = []
        tens_inds.extend([bi,bj])
        tens_inds.extend([bi+n_blocks, bj+n_blocks])
        for bk in range(0,n_blocks):
            if (bk != bi) and (bk != bj):
                tens_inds.extend([bk])
                tens_inds.extend([bk+n_blocks])
                tens_dims.extend([tb_l.block_dims[bk]])
                tens_dims.extend([tb_r.block_dims[bk]])
                h2 = np.tensordot(h2,np.eye(tb_l.block_dims[bk]),axes=0)
                s2 = np.tensordot(s2,np.eye(tb_l.block_dims[bk]),axes=0)
        
        sort_ind = np.argsort(tens_inds)
        #H += h2.reshape(tens_dims).transpose(sort_ind)
        H += h2.transpose(sort_ind)
        S2 += s2.transpose(sort_ind)

    H = H.reshape(tb_l.full_dim,tb_r.full_dim)
    S2 = S2.reshape(tb_l.full_dim,tb_r.full_dim)
    return H,S2
    # }}}

def pt_build_H1v(blocks,tb_l, tb_r,j12,v):
  # {{{
    """
    Build the Hamiltonian vector product between two tensor blocks, tb_l and tb_r, without ever constructing a full hilbert space
    
    Form the H1.v 
    """

    n_blocks = len(blocks)
    assert(n_blocks == tb_l.n_blocks)
    assert(n_blocks == tb_r.n_blocks)
    H_dim_layout = []  # dimensions of Ham block as a tensor (d1,d2,..,d1',d2',...)
    H_dim_layout = np.append(tb_l.block_dims,tb_r.block_dims)
   
    """
    form one-block and two-block terms of H separately
        1-body

            for each block, form Hamiltonian in subspace, and combine
            with identity on other blocks

        2-body
            
            for each block-dimer, form Hamiltonian in subspace, and combine
            with identity on other blocks
    """
    # How many blocks are different between left and right?
    different = []
    for bi in range(0,n_blocks):
        if tb_l.address[bi] != tb_r.address[bi]:
            different.append(bi)
    #if len(different) > 2:
    #    print " Nothing to do, why are we here?"
    #    exit(-1)
    
    n_sig = v.shape[1]  # number of sigma vectors 

    Hv  = np.zeros((tb_l.full_dim,n_sig))
    S2v = np.zeros((tb_l.full_dim,n_sig))


    #   Add up all the one-body contributions, making sure that the results is properly dimensioned for the 
    #   target subspace

    if len(different) == 0:

        assert(tb_l.full_dim == tb_r.full_dim)
        full_dim = tb_l.full_dim
        #<abcd|H1+H2+H3+H4|abcd>
        #
        #   <ab|H12|ab> Ic Id
        # + <ac|H13|ac> Ib Id
        # + Ia <bc|H23|bc> Id + etc
        
        for bi in range(0,n_blocks):
            for bj in range(bi+1,n_blocks):
                Bi = blocks[bi]
                Bj = blocks[bj]
                dim_e = full_dim / tb_l.block_dims[bi] / tb_l.block_dims[bj]

                #build full Hamiltonian on sublattice
                h2,s2 = build_dimer_H(tb_l, tb_r, Bi, Bj, j12)
                h2.shape = (tb_l.block_dims[bi],tb_l.block_dims[bj],tb_r.block_dims[bi],tb_r.block_dims[bj])
                s2.shape = (tb_l.block_dims[bi],tb_l.block_dims[bj],tb_r.block_dims[bi],tb_r.block_dims[bj])

                # 
                # restructure incoming trial vectors as a tensor
                #   
                #   <abcdef| h24 |abcdef> = <ce|h24|ce> I0 I1 I3 I4 I5
                #
                #   v(0,1,2,3,4,5) => v(2,1,0,3,4,5) 
                #                  => v(2,4,0,3,1,5) * h(2,4,2,4) =  sig(2,4,0,3,1,5)
                #                                                 => sig(0,4,2,3,1,5)
                #                                                 => sig(0,1,2,3,4,5)
                #
                v_ind = cp.deepcopy(tb_r.block_dims)
                v_ind.extend([n_sig])
                v_tens = v.reshape(v_ind)
                
                sort_ind = [bi,bj]
                for bk in range(0,n_blocks+1):
                    if bk != bi and bk != bj:
                        sort_ind.extend([bk])
                v_tens = v_tens.transpose(sort_ind)
                
                sort_ind = np.argsort(sort_ind)

                h2v = np.tensordot(h2,v_tens,axes=([0,1],[0,1]) )
                s2v = np.tensordot(s2,v_tens,axes=([0,1],[0,1]) )
                
                h2v = h2v.transpose(sort_ind)
                s2v = s2v.transpose(sort_ind)

                Hv  += h2v.reshape(tb_l.full_dim, n_sig)
                S2v += s2v.reshape(tb_l.full_dim, n_sig)
            
    
    
    elif len(different) == 1:

        full_dim_l = tb_l.full_dim
        full_dim_r = tb_r.full_dim
        #<abcd|H1+H2+H3+H4|abcd>
        #
        #   <a|H1|a> Ib Ic Id  , for block 1 being different


        bi = different[0] 

        Bi = blocks[bi]
        dim_e_l = full_dim_l / tb_l.block_dims[bi] 
        dim_e_r = full_dim_r / tb_r.block_dims[bi] 
        h1 = Bi.H_ss(tb_l.address[bi],tb_r.address[bi])
        s1 = Bi.S2_ss(tb_l.address[bi],tb_r.address[bi])

        h1.shape = (tb_l.block_dims[bi],tb_r.block_dims[bi])
        s1.shape = (tb_l.block_dims[bi],tb_r.block_dims[bi])

        assert(dim_e_l == dim_e_r)
        dim_e = dim_e_l
                
       
        v_ind = cp.deepcopy(tb_r.block_dims)
        v_ind.extend([n_sig])
        v_tens = v.reshape(v_ind)
        
        sort_ind = [bi]
        for bk in range(0,n_blocks+1):
            if bk != bi:
                sort_ind.extend([bk])
        v_tens = v_tens.transpose(sort_ind)
        
        h1v = np.tensordot(h1,v_tens,axes=([1],[0]) )
        s1v = np.tensordot(s1,v_tens,axes=([1],[0]) )
        sort_ind = np.argsort(sort_ind)

        h1v = h1v.transpose(sort_ind)
        s1v = s1v.transpose(sort_ind)
        #Hv  += h1v.reshape(tb_l.full_dim, n_sig)
        #S2v += s1v.reshape(tb_l.full_dim, n_sig)
        
        #   <ab|H12|Ab> Ic Id
        # + <ac|H13|Ac> Ib Id
        # + <ad|H13|Ad> Ib Id
        
        for bj in range(0,bi):
            Bj = blocks[bj]
            dim_e_l = full_dim_l / tb_l.block_dims[bi] / tb_l.block_dims[bj]
            dim_e_r = full_dim_r / tb_r.block_dims[bi] / tb_r.block_dims[bj]
         
            assert(dim_e_l == dim_e_r)
            dim_e = dim_e_l
            
            #build full Hamiltonian on sublattice
            #h12 = build_dimer_H(tb_l, tb_r, Bi, Bj, j12)
            h2,s2 = build_dimer_H(tb_l, tb_r, Bj, Bi, j12)
          
            h2.shape = (tb_l.block_dims[bj],tb_l.block_dims[bi],tb_r.block_dims[bj],tb_r.block_dims[bi])
            s2.shape = (tb_l.block_dims[bj],tb_l.block_dims[bi],tb_r.block_dims[bj],tb_r.block_dims[bi])
         
            v_ind = cp.deepcopy(tb_r.block_dims)
            v_ind.extend([n_sig])
            v_tens = v.reshape(v_ind)
            
            sort_ind = [bj,bi]
            for bk in range(0,n_blocks+1):
                if bk != bi and bk != bj:
                    sort_ind.extend([bk])
            v_tens = v_tens.transpose(sort_ind)
            
            h2v = np.tensordot(h2,v_tens,axes=([2,3],[0,1]) )
            s2v = np.tensordot(s2,v_tens,axes=([2,3],[0,1]) )

            sort_ind = np.argsort(sort_ind)
            
            h2v = h2v.transpose(sort_ind)
            s2v = s2v.transpose(sort_ind)

            Hv += h2v.reshape(tb_l.full_dim, n_sig)
            S2v += s2v.reshape(tb_l.full_dim, n_sig)
        
        for bj in range(bi+1, n_blocks):
            Bj = blocks[bj]
            dim_e_l = full_dim_l / tb_l.block_dims[bi] / tb_l.block_dims[bj]
            dim_e_r = full_dim_r / tb_r.block_dims[bi] / tb_r.block_dims[bj]
         
            assert(dim_e_l == dim_e_r)
            dim_e = dim_e_l
            
            #build full Hamiltonian on sublattice
            #h12 = build_dimer_H(tb_l, tb_r, Bi, Bj, j12)
            h2,s2 = build_dimer_H(tb_l, tb_r, Bi, Bj, j12)
          
            h2.shape = (tb_l.block_dims[bi],tb_l.block_dims[bj],tb_r.block_dims[bi],tb_r.block_dims[bj])
            s2.shape = (tb_l.block_dims[bi],tb_l.block_dims[bj],tb_r.block_dims[bi],tb_r.block_dims[bj])
         
            v_ind = cp.deepcopy(tb_r.block_dims)
            v_ind.extend([n_sig])
            v_tens = v.reshape(v_ind)
            
            sort_ind = [bi,bj]
            for bk in range(0,n_blocks+1):
                if bk != bi and bk != bj:
                    sort_ind.extend([bk])
            v_tens = v_tens.transpose(sort_ind)
            
            h2v = np.tensordot(h2,v_tens,axes=([2,3],[0,1]) )
            s2v = np.tensordot(s2,v_tens,axes=([2,3],[0,1]) )

            sort_ind = np.argsort(sort_ind)
            
            h2v = h2v.transpose(sort_ind)
            s2v = s2v.transpose(sort_ind)

            Hv  += h2v.reshape(tb_l.full_dim, n_sig)
            S2v += s2v.reshape(tb_l.full_dim, n_sig)
    
    elif len(different) == 2:
    
        full_dim_l = tb_l.full_dim
        full_dim_r = tb_r.full_dim
        #<abcd|H1+H2+H3+H4|abcd> = 0


        bi = different[0] 
        bj = different[1] 

        Bi = blocks[bi]
        Bj = blocks[bj]

        dim_e_l = full_dim_l / tb_l.block_dims[bi] / tb_l.block_dims[bj] 
        dim_e_r = full_dim_r / tb_r.block_dims[bi] / tb_r.block_dims[bj] 

        assert(dim_e_l == dim_e_r)
        dim_e = dim_e_l
        
        
        #  <ac|H13|Ac> Ib Id  for 1 3 different
        
        #build full Hamiltonian on sublattice
        #h12 = build_dimer_H(tb_l, tb_r, Bi, Bj, j12)
        h2,s2 = build_dimer_H(tb_l, tb_r, Bi, Bj, j12)
       
        h2.shape = (tb_l.block_dims[bi],tb_l.block_dims[bj],tb_r.block_dims[bi],tb_r.block_dims[bj])
        s2.shape = (tb_l.block_dims[bi],tb_l.block_dims[bj],tb_r.block_dims[bi],tb_r.block_dims[bj])
            
        v_ind = cp.deepcopy(tb_r.block_dims)
        v_ind.extend([n_sig])
        v_tens = v.reshape(v_ind)
        
        sort_ind = [bi,bj]
        for bk in range(0,n_blocks+1):
            if bk != bi and bk != bj:
                sort_ind.extend([bk])
        v_tens = v_tens.transpose(sort_ind)
        
        h2v = np.tensordot(h2,v_tens,axes=([2,3],[0,1]) )
        s2v = np.tensordot(s2,v_tens,axes=([2,3],[0,1]) )
        
        sort_ind = np.argsort(sort_ind)
        
        h2v = h2v.transpose(sort_ind)
        s2v = s2v.transpose(sort_ind)

        Hv  += h2v.reshape(tb_l.full_dim, n_sig)
        S2v += s2v.reshape(tb_l.full_dim, n_sig)

    return Hv,S2v
    # }}}

def H1_build_tucker_blocked_sigma(n_blocks,tucker_blocks, lattice_blocks, n_body_order, j12,v):
    #{{{

    """
        s   = <abcd| H | aBcD> v_aBcD
        
            = <bd|H24|BD>v_BD I1*v_a I3v_c
            
    A function to give part of the nth PT vector by doing H1.v
    """
    dim_tot = 0
    for ti in sorted(tucker_blocks):
        tbi = tucker_blocks[ti]
        dim_tot += tbi.full_dim


    Hv = np.zeros((dim_tot, v.shape[1]))
    S2v = np.zeros((dim_tot, v.shape[1]))

        
    for t_l in sorted(tucker_blocks):
        for t_r in sorted(tucker_blocks):
            tb_l = tucker_blocks[t_l]
            tb_r = tucker_blocks[t_r]
            v_r = cp.deepcopy( v[tb_r.start:tb_r.stop,:])

            #print " Here:", tb_l, tb_r
            #if tb_l.start == tb_r.start:
            #    continue 
            hv,s2v = pt_build_H1v(lattice_blocks, tb_l, tb_r, j12,v_r)
            #h,s2 = build_H(lattice_blocks, tb_l, tb_r, j12)
            
            Hv[tb_l.start:tb_l.stop,:] += hv
            S2v[tb_l.start:tb_l.stop,:] += s2v
            #H[tb_l.start:tb_l.stop, tb_r.start:tb_r.stop] = build_H(lattice_blocks, tb_l, tb_r, j12)
            #H[tb_r.start:tb_r.stop, tb_l.start:tb_l.stop] = H[tb_l.start:tb_l.stop, tb_r.start:tb_r.stop].T

    return Hv, S2v
    # }}}

def build_dimer_newH0Sz(tb_l, tb_r, Bi, Bj,j12):
# {{{
    """
    A build dimer block to confirm if the Sz.Sz in between two blocks are diagonal or not.
    Not in use. Also Sz.Sz not diagonal.
    """
    bi = Bi.index
    bj = Bj.index
    
    h12 = np.zeros((tb_l.block_dims[bi]*tb_l.block_dims[bj],tb_r.block_dims[bi]*tb_r.block_dims[bj]))
    s2 = np.zeros((tb_l.block_dims[bi]*tb_l.block_dims[bj],tb_r.block_dims[bi]*tb_r.block_dims[bj]))
    sz = np.zeros((tb_l.block_dims[bi]*tb_l.block_dims[bj],tb_r.block_dims[bi]*tb_r.block_dims[bj]))

    h12.shape = (tb_l.block_dims[bi], tb_r.block_dims[bi], tb_l.block_dims[bj], tb_r.block_dims[bj])
    s2.shape = (tb_l.block_dims[bi], tb_r.block_dims[bi], tb_l.block_dims[bj], tb_r.block_dims[bj])
    sz.shape = (tb_l.block_dims[bi], tb_r.block_dims[bi], tb_l.block_dims[bj], tb_r.block_dims[bj])
    for si in Bi.sites:
        space_i_l = tb_l.address[Bi.index]
        space_i_r = tb_r.address[Bi.index]
        szi = Bi.Szi_ss(si,space_i_l,space_i_r)
        
        for sj in Bj.sites:
            space_j_l = tb_l.address[Bj.index]
            space_j_r = tb_r.address[Bj.index]
            szj = Bj.Szi_ss(sj,space_j_l,space_j_r)
           
            #h12  -= j12[si,sj] * np.kron(spi, smj)
            #h12  -= j12[si,sj] * np.kron(smi, spj)
            #h12  -= j12[si,sj] * np.kron(szi, szj) * 2
           
            s1s2 = 2 * np.tensordot(szi,szj, axes=0)
            #h12 -= j12[si,sj] * np.tensordot(spi,smj, axes=0)
            #h12 -= j12[si,sj] * np.tensordot(smi,spj, axes=0)
            #h12 -= j12[si,sj] * 2 * np.tensordot(szi,szj, axes=0)

            h12 -= j12[si,sj] * s1s2
            s2  += s1s2

    sort_ind = [0,2,1,3]
    h12 = h12.transpose(sort_ind)
    h12 = h12.reshape(tb_l.block_dims[bi]*tb_l.block_dims[bj],tb_r.block_dims[bi]*tb_r.block_dims[bj])
    s2 = s2.transpose(sort_ind)
    s2 = s2.reshape(tb_l.block_dims[bi]*tb_l.block_dims[bj],tb_r.block_dims[bi]*tb_r.block_dims[bj])
    return h12, s2
# }}}

def pt_build_H0Sz(blocks,tb_l, tb_r,j12):
  # {{{
    """
    Build the Hamiltonian between two tensor blocks, tb_l and tb_r, without ever constructing a full hilbert space

    A function formed to check if the Sz.Sz block is diagonal. Currently not in use. Also it is not diagonal
      
    """

    n_blocks = len(blocks)
    assert(n_blocks == tb_l.n_blocks)
    assert(n_blocks == tb_r.n_blocks)
    H_dim_layout = []  # dimensions of Ham block as a tensor (d1,d2,..,d1',d2',...)
    H_dim_layout = np.append(tb_l.block_dims,tb_r.block_dims)
   
    """
    form one-block and two-block terms of H separately
        1-body

            for each block, form Hamiltonian in subspace, and combine
            with identity on other blocks

        2-body
            
            for each block-dimer, form Hamiltonian in subspace, and combine
            with identity on other blocks
    """
    # How many blocks are different between left and right?
    different = []
    for bi in range(0,n_blocks):
        if tb_l.address[bi] != tb_r.address[bi]:
            different.append(bi)
    #if len(different) > 2:
    #    print " Nothing to do, why are we here?"
    #    exit(-1)
    
    H  = np.zeros((tb_l.full_dim,tb_r.full_dim))
    S2 = np.zeros((tb_l.full_dim,tb_r.full_dim))
   
    #print " Ham block size", H.shape, H_dim_layout
    H.shape = H_dim_layout
    S2.shape = H_dim_layout
    #   Add up all the one-body contributions, making sure that the results is properly dimensioned for the 
    #   target subspace

    if len(different) == 0:

        assert(tb_l.full_dim == tb_r.full_dim)
        full_dim = tb_l.full_dim
        #<abcd|H1+H2+H3+H4|abcd>
        
        
        #   <ab|H12|ab> Ic Id
        # + <ac|H13|ac> Ib Id
        # + Ia <bc|H23|bc> Id + etc
        
        for bi in range(0,n_blocks):
            for bj in range(bi+1,n_blocks):
                Bi = blocks[bi]
                Bj = blocks[bj]
                dim_e = full_dim / tb_l.block_dims[bi] / tb_l.block_dims[bj]

                #build full Hamiltonian on sublattice
                h2,s2 = build_dimer_newH0Sz(tb_l, tb_r, Bi, Bj, j12)
                h2.shape = (tb_l.block_dims[bi],tb_l.block_dims[bj],tb_r.block_dims[bi],tb_r.block_dims[bj])
                s2.shape = (tb_l.block_dims[bi],tb_l.block_dims[bj],tb_r.block_dims[bi],tb_r.block_dims[bj])

                #h = np.kron(h12,np.eye(dim_e))   
            
                tens_inds    = []
                tens_inds.extend([bi,bj])
                tens_inds.extend([bi+n_blocks, bj+n_blocks])
                for bk in range(0,n_blocks):
                    if (bk != bi) and (bk != bj):
                        tens_inds.extend([bk])
                        tens_inds.extend([bk+n_blocks])
                        assert(tb_l.block_dims[bk] == tb_r.block_dims[bk] )
                        h2 = np.tensordot(h2,np.eye(tb_l.block_dims[bk]),axes=0)
                        s2 = np.tensordot(s2,np.eye(tb_l.block_dims[bk]),axes=0)
               
                sort_ind = np.argsort(tens_inds)
               
                H  += h2.transpose(sort_ind)
                S2 += s2.transpose(sort_ind)
    
    
    
    
    
    
    elif len(different) == 1:

        full_dim_l = tb_l.full_dim
        full_dim_r = tb_r.full_dim
        #<abcd|H1+H2+H3+H4|abcd>
        #
        #   <a|H1|a> Ib Ic Id  , for block 1 being different


        bi = different[0] 

        Bi = blocks[bi]
        dim_e_l = full_dim_l / tb_l.block_dims[bi] 
        dim_e_r = full_dim_r / tb_r.block_dims[bi] 
        h1 = Bi.H_ss(tb_l.address[bi],tb_r.address[bi])
        s1 = Bi.S2_ss(tb_l.address[bi],tb_r.address[bi])

        h1.shape = (tb_l.block_dims[bi],tb_r.block_dims[bi])
        s1.shape = (tb_l.block_dims[bi],tb_r.block_dims[bi])

        assert(dim_e_l == dim_e_r)
        dim_e = dim_e_l
       
        
        tens_inds    = []
        tens_inds.extend([bi])
        tens_inds.extend([bi+n_blocks])
        
        
        #   <ab|H12|Ab> Ic Id
        # + <ac|H13|Ac> Ib Id
        # + <ad|H13|Ad> Ib Id
        
        for bj in range(0,bi):
            Bj = blocks[bj]
            dim_e_l = full_dim_l / tb_l.block_dims[bi] / tb_l.block_dims[bj]
            dim_e_r = full_dim_r / tb_r.block_dims[bi] / tb_r.block_dims[bj]
         
            assert(dim_e_l == dim_e_r)
            dim_e = dim_e_l
            
            #build full Hamiltonian on sublattice
            #h12 = build_dimer_H(tb_l, tb_r, Bi, Bj, j12)
            h2,s2 = build_dimer_newH0Sz(tb_l, tb_r, Bi, Bj, j12)
          
            h2.shape = (tb_l.block_dims[bj],tb_l.block_dims[bi],tb_r.block_dims[bj],tb_r.block_dims[bi])
            s2.shape = (tb_l.block_dims[bj],tb_l.block_dims[bi],tb_r.block_dims[bj],tb_r.block_dims[bi])
         
            
            #h = np.kron(h12,np.eye(dim_e))   
            
            tens_dims    = []
            tens_inds    = []
            tens_inds.extend([bj,bi])
            tens_inds.extend([bj+n_blocks, bi+n_blocks])
            for bk in range(0,n_blocks):
                if (bk != bi) and (bk != bj):
                    tens_inds.extend([bk])
                    tens_inds.extend([bk+n_blocks])
                    assert(tb_l.block_dims[bk] == tb_r.block_dims[bk] )
                    h2 = np.tensordot(h2,np.eye(tb_l.block_dims[bk]),axes=0)
                    s2 = np.tensordot(s2,np.eye(tb_l.block_dims[bk]),axes=0)
            
            sort_ind = np.argsort(tens_inds)
            H  += h2.transpose(sort_ind)
            S2 += s2.transpose(sort_ind)
        
        for bj in range(bi+1, n_blocks):
            Bj = blocks[bj]
            dim_e_l = full_dim_l / tb_l.block_dims[bi] / tb_l.block_dims[bj]
            dim_e_r = full_dim_r / tb_r.block_dims[bi] / tb_r.block_dims[bj]
         
            assert(dim_e_l == dim_e_r)
            dim_e = dim_e_l
            
            #build full Hamiltonian on sublattice
            #h12 = build_dimer_H(tb_l, tb_r, Bi, Bj, j12)
            h2,s2 = build_dimer_newH0Sz(tb_l, tb_r, Bi, Bj, j12)
          
            h2.shape = (tb_l.block_dims[bi],tb_l.block_dims[bj],tb_r.block_dims[bi],tb_r.block_dims[bj])
            s2.shape = (tb_l.block_dims[bi],tb_l.block_dims[bj],tb_r.block_dims[bi],tb_r.block_dims[bj])
         
            
            #h = np.kron(h12,np.eye(dim_e))   
            
            tens_dims    = []
            tens_inds    = []
            tens_inds.extend([bi,bj])
            tens_inds.extend([bi+n_blocks, bj+n_blocks])
            for bk in range(0,n_blocks):
                if (bk != bi) and (bk != bj):
                    tens_inds.extend([bk])
                    tens_inds.extend([bk+n_blocks])
                    assert(tb_l.block_dims[bk] == tb_r.block_dims[bk] )
                    h2 = np.tensordot(h2,np.eye(tb_l.block_dims[bk]),axes=0)
                    s2 = np.tensordot(s2,np.eye(tb_l.block_dims[bk]),axes=0)
            
            sort_ind = np.argsort(tens_inds)
            H  += h2.transpose(sort_ind)
            S2 += s2.transpose(sort_ind)
    
    
    
    
    elif len(different) == 2:
    
        full_dim_l = tb_l.full_dim
        full_dim_r = tb_r.full_dim
        #<abcd|H1+H2+H3+H4|abcd> = 0


        bi = different[0] 
        bj = different[1] 

        Bi = blocks[bi]
        Bj = blocks[bj]

        dim_e_l = full_dim_l / tb_l.block_dims[bi] / tb_l.block_dims[bj] 
        dim_e_r = full_dim_r / tb_r.block_dims[bi] / tb_r.block_dims[bj] 

        assert(dim_e_l == dim_e_r)
        dim_e = dim_e_l
        
        
        #  <ac|H13|Ac> Ib Id  for 1 3 different
        
        #build full Hamiltonian on sublattice
        #h12 = build_dimer_H(tb_l, tb_r, Bi, Bj, j12)
        h2,s2 = build_dimer_newH0Sz(tb_l, tb_r, Bi, Bj, j12)
       
        h2.shape = (tb_l.block_dims[bi],tb_l.block_dims[bj],tb_r.block_dims[bi],tb_r.block_dims[bj])
        s2.shape = (tb_l.block_dims[bi],tb_l.block_dims[bj],tb_r.block_dims[bi],tb_r.block_dims[bj])
        #h2 = np.kron(h12,np.eye(dim_e))   
        
        tens_dims    = []
        tens_inds    = []
        tens_inds.extend([bi,bj])
        tens_inds.extend([bi+n_blocks, bj+n_blocks])
        for bk in range(0,n_blocks):
            if (bk != bi) and (bk != bj):
                tens_inds.extend([bk])
                tens_inds.extend([bk+n_blocks])
                tens_dims.extend([tb_l.block_dims[bk]])
                tens_dims.extend([tb_r.block_dims[bk]])
                h2 = np.tensordot(h2,np.eye(tb_l.block_dims[bk]),axes=0)
                s2 = np.tensordot(s2,np.eye(tb_l.block_dims[bk]),axes=0)
        
        sort_ind = np.argsort(tens_inds)
        #H += h2.reshape(tens_dims).transpose(sort_ind)
        H += h2.transpose(sort_ind)
        S2 += s2.transpose(sort_ind)

    H = H.reshape(tb_l.full_dim,tb_r.full_dim)
    S2 = S2.reshape(tb_l.full_dim,tb_r.full_dim)
    return H,S2
    # }}}
