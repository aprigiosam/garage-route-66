"""Telas do balcão. Só orquestram: as regras de negócio estão em oficina/models.py."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from oficina import validators as v
from oficina.models import ItemOS, OrdemServico, Veiculo

from .forms import DecisaoForm, EntregaForm, ItemForm, NovaOSForm, erros_de

S = OrdemServico.Status
COLUNAS = [S.ORCAMENTO, S.APROVADA, S.EM_EXECUCAO, S.PRONTA]
# Transições com formulário próprio (exigem dados); as demais são um clique.
TRANSICOES_COM_FORMULARIO = {S.APROVADA, S.RECUSADA, S.ENTREGUE}


def _ordens():
    return OrdemServico.objects.select_related("cliente", "veiculo").prefetch_related("itens")


def buscar(qs, termo):
    """Busca por nº da OS, placa, nome ou telefone do cliente."""
    termo = (termo or "").strip()
    if not termo:
        return qs
    filtro = Q(cliente__nome__icontains=termo)
    placa = v.normalizar_placa(termo)
    if placa:
        filtro |= Q(veiculo__placa__contains=placa)
    digitos = v.somente_digitos(termo)
    if len(digitos) >= 4:
        filtro |= Q(cliente__telefone__contains=digitos)
    if termo.isdigit():
        filtro |= Q(numero=int(termo))
    return qs.filter(filtro)


@login_required
def quadro(request):
    termo = request.GET.get("q", "")
    if termo.strip():
        contexto = {"termo": termo, "resultados": buscar(_ordens(), termo)[:50]}
    else:
        ordens = list(_ordens().filter(status__in=COLUNAS).order_by("aberta_em"))
        contexto = {"colunas": [(s, [o for o in ordens if o.status == s]) for s in COLUNAS]}
    # Requisição HTMX (busca enquanto digita): devolve só o miolo, não a página inteira.
    template = "balcao/_quadro_conteudo.html" if request.headers.get("HX-Request") else "balcao/quadro.html"
    return render(request, template, contexto)


@login_required
def placa_info(request):
    """HTMX: ao digitar a placa na Nova OS, mostra se o veículo já é cadastrado."""
    placa = v.normalizar_placa(request.GET.get("placa", ""))
    veiculo = Veiculo.objects.select_related("cliente").filter(placa=placa).first() if len(placa) == 7 else None
    return render(request, "balcao/_placa_info.html", {"placa": placa, "veiculo": veiculo})


@login_required
def os_nova(request):
    form = NovaOSForm(request.POST or None, initial={"placa": request.GET.get("placa", "")})
    if request.method == "POST" and form.is_valid():
        try:
            os = form.save()
        except ValidationError as erro:
            form.add_error(None, erros_de(erro))
        else:
            messages.success(request, f"OS {os.numero} aberta.")
            return redirect("balcao:os_detalhe", numero=os.numero)
    return render(request, "balcao/os_nova.html", {"form": form})


def _contexto_detalhe(os, item_form=None, decisao_form=None, entrega_form=None):
    destinos = OrdemServico.TRANSICOES[S(os.status)]
    return {
        "os": os,
        "itens": list(os.itens.all()),
        "total_pecas": os.total(ItemOS.Tipo.PECA),
        "total_servicos": os.total(ItemOS.Tipo.SERVICO),
        "total_geral": os.total(),
        "item_form": item_form or (ItemForm() if os.editavel else None),
        "decisao_form": decisao_form or (DecisaoForm() if S.APROVADA in destinos else None),
        "entrega_form": entrega_form or (EntregaForm() if S.ENTREGUE in destinos else None),
        "acoes": [d for d in sorted(destinos, key=list(S).index) if d not in TRANSICOES_COM_FORMULARIO],
    }


def _get_os(numero):
    return get_object_or_404(
        OrdemServico.objects.select_related("cliente", "veiculo").prefetch_related(
            "itens__fornecedor", "aprovacoes", "historico"
        ),
        numero=numero,
    )


@login_required
def os_detalhe(request, numero):
    return render(request, "balcao/os_detalhe.html", _contexto_detalhe(_get_os(numero)))


@login_required
@require_POST
def item_adicionar(request, numero):
    os = _get_os(numero)
    form = ItemForm(request.POST, instance=ItemOS(os=os))
    if form.is_valid():
        form.save()
        messages.success(request, "Item adicionado.")
        return redirect("balcao:os_detalhe", numero=numero)
    return render(request, "balcao/os_detalhe.html", _contexto_detalhe(os, item_form=form), status=400)


@login_required
@require_POST
def item_situacao(request, numero, item_id):
    os = _get_os(numero)
    item = get_object_or_404(ItemOS, pk=item_id, os=os)
    situacao = request.POST.get("situacao")
    if situacao not in (ItemOS.Situacao.DEVOLVIDO, ItemOS.Situacao.REMOVIDO):
        messages.error(request, "Situação inválida.")
        return redirect("balcao:os_detalhe", numero=numero)
    item.situacao, item.motivo_situacao = situacao, request.POST.get("motivo", "")[:200]
    try:
        item.full_clean()
        item.save()
        messages.success(request, f"Item marcado como {item.get_situacao_display().lower()}.")
    except ValidationError as erro:
        messages.error(request, erros_de(erro))
    return redirect("balcao:os_detalhe", numero=numero)


@login_required
@require_POST
def os_status(request, numero):
    os = _get_os(numero)
    destino = request.POST.get("destino")
    if destino not in S.values or destino in TRANSICOES_COM_FORMULARIO:
        messages.error(request, "Ação inválida.")
        return redirect("balcao:os_detalhe", numero=numero)
    try:
        os.alterar_status(destino, motivo=request.POST.get("motivo", "")[:200])
        messages.success(request, f"OS {os.numero}: {os.get_status_display()}.")
    except ValidationError as erro:
        messages.error(request, erros_de(erro))
    return redirect("balcao:os_detalhe", numero=numero)


@login_required
@require_POST
def os_decisao(request, numero):
    os = _get_os(numero)
    form = DecisaoForm(request.POST)
    if form.is_valid():
        try:
            form.save(os)
            messages.success(request, f"OS {os.numero}: {os.get_status_display()}.")
            return redirect("balcao:os_detalhe", numero=numero)
        except ValidationError as erro:
            form.add_error(None, erros_de(erro))
    return render(request, "balcao/os_detalhe.html", _contexto_detalhe(os, decisao_form=form), status=400)


@login_required
@require_POST
def os_entregar(request, numero):
    os = _get_os(numero)
    form = EntregaForm(request.POST)
    if form.is_valid():
        try:
            form.save(os)
            messages.success(request, f"OS {os.numero} entregue.")
            return redirect("balcao:os_detalhe", numero=numero)
        except ValidationError as erro:
            form.add_error(None, erros_de(erro))
    return render(request, "balcao/os_detalhe.html", _contexto_detalhe(os, entrega_form=form), status=400)
