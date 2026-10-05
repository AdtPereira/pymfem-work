'''
   Exercicio 8 - Capacitor de placas paralelas, dominio D1 (so o interior)
   Adaptado de PyMFEM examples/ex0.py

   Problema:  -div(eps0 grad V) = 0   em Omega (ar entre as placas)
              V = +V0/2               placa superior   (Dirichlet)
              V = -V0/2               placa inferior   (Dirichlet)
              V = 0                   plano y = 0      (Dirichlet, so no quarto)
              dV/dn = 0               laterais e x = 0 (Neumann natural)

   Geometria (SI, coordenadas centradas): placas em y = +-b/2, x em [-a/2, a/2].
   Modelo 2D planar com profundidade Lz = a (como o "depth" do FEMM).
   Numeros entre colchetes = atributos de contorno do MakeCartesian2D.

   Modelo completo (--model full):

                     placa superior: V = +V0/2   [3]
              +=========================================+  y = +b/2
              |   Omega (ar, eps0)   ^ y                |
   [4]        |                      |       |  |  E    |        [2]
   dV/dn = 0  |                      +--> x  v  v       |  dV/dn = 0
              |                    (0,0)                |
              +=========================================+  y = -b/2
           x = -a/2  placa inferior: V = -V0/2   [1]     x = +a/2

           |<----------------- a = 10 cm --------------->|   b = 2 cm

   Meio modelo (--model half): x em [0, a/2]

                  placa superior: V = +V0/2   [3]
              +=====================+  y = +b/2
   simetria   |                     |
   par    [4] |      Omega          | [2]  dV/dn = 0
   dV/dn = 0  |                     |
              +=====================+  y = -b/2
            x = 0                  x = +a/2
                  placa inferior: V = -V0/2   [1]

   Quarto de modelo (--model quarter): x em [0, a/2], y em [0, b/2]

                  placa superior: V = +V0/2   [3]
              +=====================+  y = +b/2
   simetria   |                     |
   par    [4] |      Omega          | [2]  dV/dn = 0
   dV/dn = 0  |                     |
              +---------------------+  y = 0
            x = 0     [1]  V = 0     x = +a/2
                 (simetria impar)

   Legenda:  ====  Dirichlet (eletrodo)    |  Neumann homogeneo
             ----  Dirichlet V = 0 (plano de simetria impar)

   Dois dieletricos (--interface, so com --model full; horizontal tambem com half).
   Atributos de ELEMENTO: 1 = dieletrico 1 (eps_r1), 2 = dieletrico 2 (eps_r2).

   Interface horizontal em y = pos (camadas em SERIE):

              +=========================================+  y = +b/2
              |          [2]  eps_r2                    |
              |- - - - - - - - - - - - - - - - - - - - -|  y = pos
              |          [1]  eps_r1                    |
              +=========================================+  y = -b/2

        C = eps0 a Lz / (d1/eps_r1 + d2/eps_r2),  d1 = pos + b/2,  d2 = b/2 - pos
        D_n continuo, E_1 / E_2 = eps_r2 / eps_r1

   Interface vertical em x = pos (faixas em PARALELO):

              +====================:====================+  y = +b/2
              |                    :                    |
              |   [1]  eps_r1      :     [2]  eps_r2    |
              |                    :                    |
              +====================:====================+  y = -b/2
           x = -a/2             x = pos                 x = +a/2

        C = eps0 Lz (eps_r1 w1 + eps_r2 w2) / b,  w1 = pos + a/2,  w2 = a/2 - pos
        E tangencial continuo (|E| = V0/b nos dois), D_1 / D_2 = eps_r1 / eps_r2

   A interface precisa cair sobre uma linha da malha (o script verifica).
   Nenhuma condicao e imposta nela: V continuo vem do espaco H1 e a
   continuidade de D_n = eps dV/dn e natural na forma fraca.

   Como rodar:
      python capacitor_d1.py                    # modelo completo
      python capacitor_d1.py --model half       # meio modelo  (x >= 0)
      python capacitor_d1.py --model quarter    # quarto       (x >= 0, y >= 0)
      python capacitor_d1.py -o 2 -s 2.5e-3 -e tri
      python capacitor_d1.py -i horizontal -er1 1 -er2 4          # interface em y = 0
      python capacitor_d1.py -i horizontal -p 0.005 --model half
      python capacitor_d1.py -i vertical -p 0.02 -er1 2.2 -er2 10

   Saidas (prefixo d1_<model>):
      d1_<model>[_<interface>].mesh, ..._V.gf, ..._E.gf, ..._D.gf -> GLVis
      d1_<model>[_<interface>].png                        -> V, |E| e |D| com setas
'''
import numpy as np
import mfem.ser as mfem

# ---------------------------------------------------------------------------
# Dados do problema (SI)
# ---------------------------------------------------------------------------
EPS0 = 8.8541878128e-12   # F/m
A = 0.10                  # lado da placa  a [m]
B = 0.02                  # separacao      b [m]
V0 = 100.0                # tensao entre as placas [V]
LZ = A                    # profundidade do modelo 2D [m]

# Atributos de contorno do MakeCartesian2D
BOTTOM, RIGHT, TOP, LEFT = 1, 2, 3, 4

# Atributos de ELEMENTO (regioes de material)
#   1 -> dieletrico 1 (eps_r1): abaixo (horizontal) ou a esquerda (vertical)
#   2 -> dieletrico 2 (eps_r2): acima  (horizontal) ou a direita  (vertical)
DIEL1, DIEL2 = 1, 2

# Para cada modelo: retangulo [x0,x1] x [y0,y1], condicoes de Dirichlet
# {atributo: valor} e fatores de simetria (N_W energia, N_Q carga).
MODELS = {
    'full':    dict(x=(-A/2, A/2), y=(-B/2, B/2),
                    dirichlet={TOP: +V0/2, BOTTOM: -V0/2}, NW=1, NQ=1),
    'half':    dict(x=(0.0, A/2),  y=(-B/2, B/2),
                    dirichlet={TOP: +V0/2, BOTTOM: -V0/2}, NW=2, NQ=2),
    'quarter': dict(x=(0.0, A/2),  y=(0.0, B/2),
                    dirichlet={TOP: +V0/2, BOTTOM: 0.0},   NW=4, NQ=2),
}


def make_mesh(model, h, elem):
    '''Retangulo do modelo, malha estruturada com tamanho de elemento ~h.'''
    (x0, x1), (y0, y1) = MODELS[model]['x'], MODELS[model]['y']
    Lx, Ly = x1 - x0, y1 - y0
    nx, ny = max(1, round(Lx / h)), max(1, round(Ly / h))
    etype = (mfem.Element.QUADRILATERAL if elem == 'quad'
             else mfem.Element.TRIANGLE)
    mesh = mfem.Mesh.MakeCartesian2D(nx, ny, etype, True, Lx, Ly, False)

    # MakeCartesian2D cria [0,Lx]x[0,Ly]; desloca para [x0,x1]x[y0,y1].
    # MoveVertices recebe o deslocamento ordenado byNODES: (x de todos, y de todos).
    nv = mesh.GetNV()
    disp = mfem.Vector(np.concatenate([np.full(nv, x0), np.full(nv, y0)]))
    mesh.MoveVertices(disp)
    return mesh


def check_config(model, interface, pos, h):
    '''Verifica se o modelo de simetria e compativel com a interface e se a
    interface cai sobre uma linha da malha (necessario para eps descontinuo
    ser representado exatamente).'''
    cfg = MODELS[model]
    if interface == 'horizontal' and model == 'quarter':
        raise SystemExit('Interface horizontal quebra a simetria impar em y = 0: '
                         'use --model full ou half.')
    if interface == 'vertical' and model != 'full':
        raise SystemExit('Interface vertical quebra a simetria par em x = 0: '
                         'use --model full.')
    if interface == 'none':
        return
    lo, hi = cfg['y'] if interface == 'horizontal' else cfg['x']
    if not lo < pos < hi:
        raise SystemExit(f'--pos = {pos} fora do intervalo aberto ({lo}, {hi}).')
    n = round((hi - lo) / h)
    step = (hi - lo) / n
    k = (pos - lo) / step
    if abs(k - round(k)) > 1e-9:
        raise SystemExit(f'A interface em {pos} m nao coincide com uma linha da '
                         f'malha (passo {step} m). Ajuste --pos ou --size.')


def set_materials(mesh, interface, pos):
    '''Atribui DIEL1/DIEL2 a cada elemento pela posicao do seu centro.'''
    if interface == 'none':
        return                       # todos ficam com atributo 1
    axis = 1 if interface == 'horizontal' else 0
    for e in range(mesh.GetNE()):
        T = mesh.GetElementTransformation(e)
        c = T.Transform(mfem.Geometries.GetCenter(mesh.GetElementBaseGeometry(e)))
        mesh.SetAttribute(e, DIEL1 if c[axis] < pos else DIEL2)
    mesh.SetAttributes()             # atualiza mesh.attributes


def analytic_C(interface, er1, er2, pos):
    '''Capacitancia exata do D1 (sem espraiamento).'''
    if interface == 'none':          # um so meio, eps_r1
        return EPS0 * er1 * A * LZ / B
    if interface == 'horizontal':    # camadas em SERIE
        d1, d2 = pos + B/2, B/2 - pos
        return EPS0 * A * LZ / (d1/er1 + d2/er2)
    w1, w2 = pos + A/2, A/2 - pos    # vertical: faixas em PARALELO
    return EPS0 * LZ * (er1*w1 + er2*w2) / B


def element_fields(mesh, V):
    '''E = -grad V no centro de cada elemento: (xc, yc, Ex, Ey) em SI.'''
    xc, yc, Ex, Ey = [], [], [], []
    grad = mfem.Vector()
    for e in range(mesh.GetNE()):
        T = mesh.GetElementTransformation(e)
        ip = mfem.Geometries.GetCenter(mesh.GetElementBaseGeometry(e))
        T.SetIntPoint(ip)
        V.GetGradient(T, grad)
        p = T.Transform(ip)
        xc.append(p[0]); yc.append(p[1])
        Ex.append(-grad[0]); Ey.append(-grad[1])
    return np.array(xc), np.array(yc), np.array(Ex), np.array(Ey)


def run(model='full', order=1, h=5e-3, elem='quad', interface='none',
        er1=1.0, er2=1.0, pos=0.0, visualization=True):
    cfg = MODELS[model]
    check_config(model, interface, pos, h)

    # 1. Malha (no ex0: leitura de arquivo + UniformRefinement)
    #    + atributos de elemento = regioes de material
    mesh = make_mesh(model, h, elem)
    set_materials(mesh, interface, pos)
    print(f'Modelo: {model} | interface: {interface} | elementos: {mesh.GetNE()} | '
          f'atributos de elemento: {list(mesh.attributes.ToList())} | '
          f'atributos de contorno: {list(mesh.bdr_attributes.ToList())}')

    # 2. Espaco H1 de ordem p (igual ao ex0)
    fec = mfem.H1_FECollection(order, mesh.Dimension())
    fespace = mfem.FiniteElementSpace(mesh, fec)
    print('Numero de incognitas: ' + str(fespace.GetTrueVSize()))

    # 3. DOFs de Dirichlet: SO as placas (e y=0 no quarto).
    #    No ex0 era GetBoundaryTrueDofs (todo o contorno); aqui as laterais
    #    ficam livres -> Neumann homogeneo natural.
    nbdr = mesh.bdr_attributes.Max()
    ess_bdr = mfem.intArray([0] * nbdr)
    for attr in cfg['dirichlet']:
        ess_bdr[attr - 1] = 1
    ess_tdof_list = mfem.intArray()
    fespace.GetEssentialTrueDofs(ess_bdr, ess_tdof_list)

    # 4. Solucao V: chute inicial 0 e valores de Dirichlet em cada placa
    #    (no ex0 bastava x = 0).
    V = mfem.GridFunction(fespace)
    V.Assign(0.0)
    for attr, val in cfg['dirichlet'].items():
        marker = mfem.intArray([0] * nbdr)
        marker[attr - 1] = 1
        V.ProjectBdrCoefficient(mfem.ConstantCoefficient(val), marker)

    # 5. Lado direito: zero (sem carga livre). No ex0 era f = 1.
    b = mfem.LinearForm(fespace)
    b.Assign(0.0)

    # 6. Forma bilinear a(V,w) = int eps grad V . grad w
    #    eps constante por partes: o PWConstCoefficient escolhe o valor pelo
    #    atributo do elemento (posicao k do vetor <-> atributo k+1).
    #    Nao ha nenhuma condicao a impor na interface: a continuidade de V
    #    vem do espaco H1 e a de D_n = eps dV/dn e natural na forma fraca.
    eps_vals = mfem.Vector([EPS0 * er1, EPS0 * er2])
    eps = mfem.PWConstCoefficient(eps_vals)
    a = mfem.BilinearForm(fespace)
    a.AddDomainIntegrator(mfem.DiffusionIntegrator(eps))
    a.Assemble()

    # Copia da matriz SEM eliminacao de Dirichlet, para energia e carga
    # (FormLinearSystem altera a matriz de "a").
    k = mfem.BilinearForm(fespace)
    k.AddDomainIntegrator(mfem.DiffusionIntegrator(eps))
    k.Assemble()
    k.Finalize()
    K = k.SpMat()

    # 7. Sistema A X = B com eliminacao de Dirichlet
    Aop = mfem.SparseMatrix()
    Bv = mfem.Vector()
    X = mfem.Vector()
    a.FormLinearSystem(ess_tdof_list, V, b, Aop, X, Bv)
    print('Tamanho do sistema linear: ' + str(Aop.Height()))

    # 8. PCG + Gauss-Seidel simetrico (igual ao ex0)
    M = mfem.GSSmoother(Aop)
    mfem.PCG(Aop, M, Bv, X, 0, 2000, 1e-24, 0.0)
    a.RecoverFEMSolution(X, b, V)

    # 9. Capacitancia
    v = V.GetDataArray().copy()
    KV = mfem.Vector(fespace.GetVSize())
    K.Mult(V, KV)
    kv = KV.GetDataArray().copy()

    # 9a. Energia por metro: W' = 1/2 V^T K V
    W = 0.5 * v @ kv
    W_tot = cfg['NW'] * W
    C_W = 2 * W_tot / V0**2 * LZ

    # 9b. Carga por metro na placa superior: Q'+ = soma das reacoes (K V)_i
    top = mfem.intArray([0] * nbdr)
    top[TOP - 1] = 1
    top_dofs = mfem.intArray()
    fespace.GetEssentialVDofs(top, top_dofs)       # marcador -1 nos DOFs da placa
    idx = np.where(np.array(top_dofs.ToList()) != 0)[0]
    Q = kv[idx].sum()
    C_Q = cfg['NQ'] * Q / V0 * LZ

    C_exact = analytic_C(interface, er1, er2, pos)
    print(f"\nW'  (modelado)   = {W:.6e} J/m")
    print(f"Q'+ (modelado)   = {Q:.6e} C/m")
    print(f'C (energia)      = {C_W*1e12:.6f} pF   erro rel. = {abs(C_W-C_exact)/C_exact:.2e}')
    print(f'C (carga)        = {C_Q*1e12:.6f} pF   erro rel. = {abs(C_Q-C_exact)/C_exact:.2e}')
    print(f'C (analitico)    = {C_exact*1e12:.6f} pF')

    # 9c. Campo por regiao: |E| e |D| = eps |E| medios em cada dieletrico
    xc, yc, Ex, Ey = element_fields(mesh, V)
    Emag = np.hypot(Ex, Ey)
    attr = np.array([mesh.GetAttribute(e) for e in range(mesh.GetNE())])
    print()
    for k, er in ((DIEL1, er1), (DIEL2, er2)):
        if np.any(attr == k):
            Ek = Emag[attr == k].mean()
            print(f'Regiao {k} (eps_r = {er:g}): |E| = {Ek:10.3f} V/m   '
                  f'|D| = {EPS0*er*Ek:.6e} C/m^2')

    # 10. Campo eletrico E = -grad V, projetado em L2 vetorial (descontinuo)
    gradV = mfem.GradientGridFunctionCoefficient(V)
    Ecoef = mfem.ScalarVectorProductCoefficient(-1.0, gradV)
    l2fec = mfem.L2_FECollection(max(order - 1, 0), mesh.Dimension())
    l2space = mfem.FiniteElementSpace(mesh, l2fec, mesh.Dimension())
    E = mfem.GridFunction(l2space)
    E.ProjectCoefficient(Ecoef)

    #     Deslocamento eletrico D = eps E = -eps grad V, no mesmo espaco L2.
    #     O L2 e descontinuo, entao representa o salto de D tangencial (ou de
    #     E normal) na interface sem suavizar. O coeficiente -eps e montado
    #     como outro PWConstCoefficient, valor por atributo de elemento.
    neg_eps = mfem.PWConstCoefficient(mfem.Vector([-EPS0 * er1, -EPS0 * er2]))
    Dcoef = mfem.ScalarVectorProductCoefficient(neg_eps, gradV)
    D = mfem.GridFunction(l2space)
    D.ProjectCoefficient(Dcoef)

    # 11. Arquivos para GLVis: glvis -m d1_full.mesh -g d1_full_V.gf
    #     (_E.gf e _D.gf sao campos vetoriais: GLVis mostra o modulo e,
    #      com a tecla 'v', as setas)
    tag = f'd1_{model}' + ('' if interface == 'none' else f'_{interface}')
    mesh.Save(f'{tag}.mesh')
    V.Save(f'{tag}_V.gf')
    E.Save(f'{tag}_E.gf')
    D.Save(f'{tag}_D.gf')

    if visualization:
        plot(mesh, V, tag, interface, pos, er1, er2)
    return C_W, C_Q


def plot(mesh, V, tag, interface='none', pos=0.0, er1=1.0, er2=1.0):
    '''Tres paineis: V (cores + equipotenciais), |E| com setas de E e
    |D| = eps |E| com setas de D. E e D sao constantes por elemento (P1).'''
    import matplotlib.pyplot as plt
    import matplotlib.tri as mtri

    verts = np.array(mesh.GetVertexArray())
    tris, owner = [], []          # owner[t] = elemento de origem do triangulo t
    for e in range(mesh.GetNE()):
        vv = list(mesh.GetElementVertices(e))
        sub = [vv] if len(vv) == 3 else [[vv[0], vv[1], vv[2]], [vv[0], vv[2], vv[3]]]
        tris += sub
        owner += [e] * len(sub)
    owner = np.array(owner)
    triang = mtri.Triangulation(verts[:, 0] * 100, verts[:, 1] * 100, tris)  # em cm

    nod = mfem.Vector()
    V.GetNodalValues(nod, 1)
    vnod = nod.GetDataArray().copy()

    # E = -grad V no centro de cada elemento (posicoes em cm) e D = eps E
    xc, yc, Ex, Ey = element_fields(mesh, V)
    xc, yc = xc * 100, yc * 100
    attr = np.array([mesh.GetAttribute(e) for e in range(mesh.GetNE())])
    eps_e = EPS0 * np.where(attr == DIEL2, er2, er1)
    Dx, Dy = eps_e * Ex, eps_e * Ey

    hcm = np.sqrt(np.ptp(verts[:, 0]) * np.ptp(verts[:, 1]) / mesh.GetNE()) * 100
    step = max(1, len(xc) // 150)

    def field_panel(ax, Fx, Fy, cmap, label, title):
        '''|F| constante por elemento sobre a malha real + setas de F.'''
        Fmag = np.hypot(Fx, Fy)
        lo, hi = Fmag.min(), Fmag.max()
        pad = 0.01 * hi if hi > 0 else 1.0       # evita faixa nula se |F| e uniforme
        pc = ax.tripcolor(triang, facecolors=Fmag[owner], cmap=cmap,
                          vmin=lo - pad, vmax=hi + pad)
        scale = hi / (0.7 * hcm * np.sqrt(step))  # maior seta ~ 0,7 do passo
        ax.quiver(xc[::step], yc[::step], Fx[::step], Fy[::step], color='w',
                  angles='xy', scale_units='xy', scale=scale, width=0.003)
        fig.colorbar(pc, ax=ax, label=label)
        ax.set_title(title)

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(9, 8.5), constrained_layout=True)

    tpc = ax1.tripcolor(triang, vnod, shading='gouraud', cmap='coolwarm')
    ax1.tricontour(triang, vnod, levels=11, colors='k', linewidths=0.6)
    fig.colorbar(tpc, ax=ax1, label='V [V]')
    ax1.set_title(f'{tag}: potencial V e equipotenciais')

    field_panel(ax2, Ex, Ey, 'viridis', '|E| [V/m]',
                f'{tag}: campo eletrico E = -grad V')
    field_panel(ax3, Dx, Dy, 'magma', '|D| [C/m$^2$]',
                f'{tag}: deslocamento eletrico D = eps E')

    for ax in (ax1, ax2, ax3):
        if interface == 'horizontal':
            ax.axhline(pos * 100, color='k', ls='--', lw=1.5)
        elif interface == 'vertical':
            ax.axvline(pos * 100, color='k', ls='--', lw=1.5)
        ax.set_aspect('equal')
        ax.set_xlabel('x [cm]'); ax.set_ylabel('y [cm]')
    fig.savefig(f'{tag}.png', dpi=130)
    print(f'Figura salva: {tag}.png')


if __name__ == '__main__':
    from mfem.common.arg_parser import ArgParser

    parser = ArgParser(description='Exercicio 8 - capacitor, dominio D1')
    parser.add_argument('--model', default='full', choices=list(MODELS),
                        help='full, half (x>=0) ou quarter (x>=0, y>=0)')
    parser.add_argument('-o', '--order', default=1, type=int,
                        help='Ordem polinomial dos elementos')
    parser.add_argument('-s', '--size', default=5e-3, type=float,
                        help='Tamanho do elemento [m]')
    parser.add_argument('-e', '--elem', default='quad', choices=['quad', 'tri'],
                        help='Tipo de elemento')
    parser.add_argument('-i', '--interface', default='none',
                        choices=['none', 'horizontal', 'vertical'],
                        help='Interface entre os dois dieletricos')
    parser.add_argument('-er1', '--eps-r1', dest='er1', default=1.0, type=float,
                        help='eps_r do dieletrico 1 (abaixo / a esquerda)')
    parser.add_argument('-er2', '--eps-r2', dest='er2', default=4.0, type=float,
                        help='eps_r do dieletrico 2 (acima / a direita)')
    parser.add_argument('-p', '--pos', default=0.0, type=float,
                        help='Posicao da interface [m]: y (horizontal) ou x (vertical)')
    parser.add_argument('-no-vis', '--no-visualization', dest='vis',
                        action='store_false', default=True,
                        help='Nao gerar a figura')
    args = parser.parse_args()
    parser.print_options(args)

    run(model=args.model, order=args.order, h=args.size, elem=args.elem,
        interface=args.interface, er1=args.er1, er2=args.er2, pos=args.pos,
        visualization=args.vis)
