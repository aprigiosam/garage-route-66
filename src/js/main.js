/**
 * Garage Route 66 — Scripts de Interatividade, Acessibilidade e Conversão
 * Fonte única de configuração no topo para manutenção simples.
 */

import { getConfig, trackEvent, openTrackedWhatsApp } from './tracking.js';

const CLIENT = getConfig();
const SITE_CONFIG = {
    name: CLIENT.site.name,
    addressFull: CLIENT.address.full,
    timezone: CLIENT.hours.timezone,
    hours: CLIENT.hours,
};

const FOCUSABLE_SELECTOR =
    'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

const prefersReducedMotion = () =>
    window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;


/**
 * Cria ícone SVG com segurança via DOM API (sem innerHTML).
 */
function createToastIcon(type) {
    const svgNS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('class', 'w-4 h-4 shrink-0');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-width', '2.5');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('aria-hidden', 'true');

    const path = document.createElementNS(svgNS, 'path');
    path.setAttribute('stroke-linecap', 'round');
    path.setAttribute('stroke-linejoin', 'round');

    if (type === 'error') {
        path.setAttribute(
            'd',
            'M12 9v2m0 4h.01M10.29 3.86l-7.5 13A1 1 0 003.65 18h16.7a1 1 0 00.86-1.5l-7.5-13a1 1 0 00-1.72 0z'
        );
    } else {
        path.setAttribute('d', 'M5 13l4 4L19 7');
    }

    svg.appendChild(path);
    return svg;
}

/**
 * Sistema de notificação Toast acessível e seguro (textContent).
 */
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-box');
    if (!container) return;

    const toast = document.createElement('div');
    const styleByType =
        type === 'error'
            ? 'bg-garage-red border border-red-400/40'
            : 'bg-emerald-700 border border-emerald-500/40';

    toast.className = `${styleByType} text-white px-4 py-3 rounded-xl shadow-xl text-sm font-semibold flex items-center gap-2.5 transition-all duration-200 transform -translate-y-2 opacity-0 pointer-events-auto`;
    if (type === 'error') {
        toast.setAttribute('role', 'alert');
    } else {
        toast.setAttribute('role', 'status');
    }

    const icon = createToastIcon(type);
    const label = document.createElement('span');
    label.textContent = message;

    toast.appendChild(icon);
    toast.appendChild(label);
    container.appendChild(toast);

    requestAnimationFrame(() => {
        toast.classList.remove('-translate-y-2', 'opacity-0');
        toast.classList.add('translate-y-0', 'opacity-100');
    });

    const hideDelay = 3400;
    const removeDelay = prefersReducedMotion() ? 0 : 250;

    setTimeout(() => {
        toast.classList.remove('translate-y-0', 'opacity-100');
        toast.classList.add('-translate-y-2', 'opacity-0');
        setTimeout(() => toast.remove(), removeDelay);
    }, hideDelay);
}

/**
 * Atualiza todos os indicadores de status Aberto/Fechado (Hero + Localização)
 * utilizando Intl.DateTimeFormat.formatToParts para o fuso de São Paulo.
 */
function updateOpenStatus() {
    const badges = document.querySelectorAll('.js-open-status');
    if (!badges.length) return;

    const formatter = new Intl.DateTimeFormat('en-US', {
        timeZone: SITE_CONFIG.timezone,
        weekday: 'short',
        hour: '2-digit',
        hourCycle: 'h23',
    });

    const parts = formatter.formatToParts(new Date());
    const weekday = parts.find((p) => p.type === 'weekday')?.value;
    const hour = Number(parts.find((p) => p.type === 'hour')?.value);

    const weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
    const { weekdayOpen, weekdayClose, saturdayOpen, saturdayClose } = SITE_CONFIG.hours;

    let isOpen = false;
    if (weekdays.includes(weekday) && hour >= weekdayOpen && hour < weekdayClose) {
        isOpen = true;
    } else if (weekday === 'Sat' && hour >= saturdayOpen && hour < saturdayClose) {
        isOpen = true;
    }

    badges.forEach((badge) => {
        const isCompact = badge.dataset.statusVariant === 'compact';
        if (isOpen) {
            badge.textContent = '● Aberto agora';
            badge.className = isCompact
                ? 'js-open-status inline-flex items-center text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 mt-1'
                : 'js-open-status text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30';
        } else {
            badge.textContent = '● Fechado no momento';
            badge.className = isCompact
                ? 'js-open-status inline-flex items-center text-[11px] font-bold px-2 py-0.5 rounded-full bg-red-500/15 text-red-400 border border-red-500/30 mt-1'
                : 'js-open-status text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-red-500/15 text-red-400 border border-red-500/30';
        }
    });
}

/**
 * Copia o endereço usando Clipboard API moderna com fallback invisível.
 */
async function copyAddress() {
    const addressText = SITE_CONFIG.addressFull;

    if (navigator.clipboard && window.isSecureContext) {
        try {
            await navigator.clipboard.writeText(addressText);
            showToast('Endereço copiado para a área de transferência!', 'success');
            return;
        } catch (_err) {
            // Prossegue para o fallback abaixo
        }
    }

    const tempInput = document.createElement('textarea');
    tempInput.value = addressText;
    tempInput.setAttribute('readonly', '');
    tempInput.style.cssText = 'position:fixed;top:0;left:0;opacity:0;pointer-events:none;';
    document.body.appendChild(tempInput);
    tempInput.select();

    try {
        const copied = document.execCommand('copy');
        if (copied) {
            showToast('Endereço copiado para a área de transferência!', 'success');
        } else {
            showToast('Não foi possível copiar automaticamente. Endereço: Rua Bem Te Vi, 32.', 'error');
        }
    } catch (_err) {
        showToast('Não foi possível copiar automaticamente. Endereço: Rua Bem Te Vi, 32.', 'error');
    } finally {
        document.body.removeChild(tempInput);
    }
}

/**
 * Inicialização principal após o DOM carregar.
 */
document.addEventListener('DOMContentLoaded', () => {
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    const mobileBackdrop = document.getElementById('mobile-menu-backdrop');
    const iconMenuOpen = document.getElementById('icon-menu-open');
    const iconMenuClose = document.getElementById('icon-menu-close');

    const quoteModal = document.getElementById('quote-modal');
    const quoteModalPanel = document.getElementById('quote-modal-panel');
    const quoteForm = document.getElementById('quote-form');
    const carModelInput = document.getElementById('car-model');
    const customerNameInput = document.getElementById('customer-name');
    const serviceSelect = document.getElementById('service-select');
    const problemDescInput = document.getElementById('problem-desc');
    const whatsappFab = document.getElementById('whatsapp-fab');

    let isMobileMenuOpen = false;
    let isModalOpen = false;
    let lastFocusedElement = null;
    let modalCloseTimer = null;

    // 1. Ano dinâmico no rodapé
    const yearEl = document.getElementById('current-year');
    if (yearEl) {
        yearEl.textContent = String(new Date().getFullYear());
    }

    // 2. Sincroniza links de WhatsApp com o número centralizado em SITE_CONFIG
    // Links diretos de WhatsApp passam pela função rastreada (href fica como fallback sem JS)
    document.querySelectorAll('[data-whatsapp-msg]').forEach((link) => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            openTrackedWhatsApp('', '', {
                customMessage: link.getAttribute('data-whatsapp-msg'),
                source: link.getAttribute('data-track-source') || 'link_direto',
            });
        });
    });

    // Cliques em telefone, rota e Instagram
    document.querySelectorAll('[data-track]').forEach((el) => {
        el.addEventListener('click', () => trackEvent(el.getAttribute('data-track')));
    });

    // 3. Fallback seguro para imagem do Hero (sem depender de placehold.co)
    const heroImg = document.getElementById('hero-image');
    if (heroImg) {
        heroImg.addEventListener('error', () => {
            heroImg.classList.add('hidden');
            const fallback = document.getElementById('hero-image-fallback');
            if (fallback) fallback.classList.remove('hidden');
        });
    }

    // 4. Controle de visibilidade do botão flutuante do WhatsApp (FAB)
    function updateFabVisibility() {
        if (!whatsappFab) return;
        const shouldShow = window.scrollY >= 260 && !isModalOpen && !isMobileMenuOpen;

        if (shouldShow) {
            whatsappFab.classList.remove('opacity-0', 'translate-y-4', 'pointer-events-none');
            whatsappFab.classList.add('opacity-100', 'translate-y-0');
            whatsappFab.removeAttribute('aria-hidden');
            whatsappFab.removeAttribute('tabindex');
        } else {
            whatsappFab.classList.add('opacity-0', 'translate-y-4', 'pointer-events-none');
            whatsappFab.classList.remove('opacity-100', 'translate-y-0');
            whatsappFab.setAttribute('aria-hidden', 'true');
            whatsappFab.setAttribute('tabindex', '-1');
        }
    }

    // 5. Menu Mobile acessível
    function openMobileMenu() {
        if (!mobileMenu || !mobileMenuBtn || isMobileMenuOpen) return;
        isMobileMenuOpen = true;
        mobileMenu.classList.remove('hidden');
        if (mobileBackdrop) mobileBackdrop.classList.remove('hidden');
        mobileMenuBtn.setAttribute('aria-expanded', 'true');
        mobileMenuBtn.setAttribute('aria-label', 'Fechar menu de navegação');
        if (iconMenuOpen) iconMenuOpen.classList.add('hidden');
        if (iconMenuClose) iconMenuClose.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');
        updateFabVisibility();
    }

    function closeMobileMenu({ restoreFocus = false } = {}) {
        if (!mobileMenu || !mobileMenuBtn || !isMobileMenuOpen) return;
        isMobileMenuOpen = false;
        mobileMenu.classList.add('hidden');
        if (mobileBackdrop) mobileBackdrop.classList.add('hidden');
        mobileMenuBtn.setAttribute('aria-expanded', 'false');
        mobileMenuBtn.setAttribute('aria-label', 'Abrir menu de navegação');
        if (iconMenuOpen) iconMenuOpen.classList.remove('hidden');
        if (iconMenuClose) iconMenuClose.classList.add('hidden');
        if (!isModalOpen) {
            document.body.classList.remove('overflow-hidden');
        }
        updateFabVisibility();
        if (restoreFocus) {
            mobileMenuBtn.focus();
        }
    }

    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', () => {
            if (isMobileMenuOpen) {
                closeMobileMenu();
            } else {
                openMobileMenu();
            }
        });
    }

    if (mobileBackdrop) {
        mobileBackdrop.addEventListener('click', () => closeMobileMenu());
    }

    if (mobileMenu) {
        mobileMenu.querySelectorAll('a[href^="#"]').forEach((anchor) => {
            anchor.addEventListener('click', () => closeMobileMenu());
        });
    }

    // Fecha menu mobile automaticamente ao redimensionar para desktop (>= 768px)
    window.addEventListener('resize', () => {
        if (window.innerWidth >= 768 && isMobileMenuOpen) {
            closeMobileMenu();
        }
    });

    // 6. Modal de Pré-Orçamento (animação real, scroll lock, focus trap e pré-seleção)
    function openQuoteModal(preselectedService = '') {
        if (!quoteModal || !quoteModalPanel) return;

        if (modalCloseTimer) {
            clearTimeout(modalCloseTimer);
            modalCloseTimer = null;
        }

        lastFocusedElement = document.activeElement;
        if (isMobileMenuOpen) {
            closeMobileMenu();
        }

        if (serviceSelect && preselectedService) {
            const matchingOption = Array.from(serviceSelect.options).find(
                (opt) => opt.value === preselectedService
            );
            if (matchingOption) {
                serviceSelect.value = preselectedService;
            }
        }

        isModalOpen = true;
        document.body.classList.add('overflow-hidden');
        quoteModal.classList.remove('hidden');
        quoteModal.classList.add('flex');
        updateFabVisibility();

        requestAnimationFrame(() => {
            quoteModal.classList.remove('opacity-0');
            quoteModal.classList.add('opacity-100');
            quoteModalPanel.classList.remove('scale-95', 'translate-y-2', 'opacity-0');
            quoteModalPanel.classList.add('scale-100', 'translate-y-0', 'opacity-100');
        });

        if (carModelInput) {
            carModelInput.focus({ preventScroll: true });
        }
    }

    function closeQuoteModal() {
        if (!quoteModal || !quoteModalPanel || !isModalOpen) return;

        isModalOpen = false;
        quoteModal.classList.remove('opacity-100');
        quoteModal.classList.add('opacity-0');
        quoteModalPanel.classList.remove('scale-100', 'translate-y-0', 'opacity-100');
        quoteModalPanel.classList.add('scale-95', 'translate-y-2', 'opacity-0');

        const finishClose = () => {
            quoteModal.classList.add('hidden');
            quoteModal.classList.remove('flex');
            if (!isMobileMenuOpen) {
                document.body.classList.remove('overflow-hidden');
            }
            updateFabVisibility();
            if (lastFocusedElement && typeof lastFocusedElement.focus === 'function') {
                lastFocusedElement.focus();
            }
            lastFocusedElement = null;
            modalCloseTimer = null;
        };

        if (prefersReducedMotion()) {
            finishClose();
        } else {
            modalCloseTimer = setTimeout(finishClose, 200);
        }
    }

    // Focus trap (Tab / Shift+Tab) dentro do modal
    function handleModalKeydown(event) {
        if (event.key === 'Escape') {
            if (isModalOpen) {
                closeQuoteModal();
            } else if (isMobileMenuOpen) {
                closeMobileMenu({ restoreFocus: true });
            }
            return;
        }

        if (event.key !== 'Tab' || !isModalOpen || !quoteModalPanel) return;

        const focusables = Array.from(quoteModalPanel.querySelectorAll(FOCUSABLE_SELECTOR)).filter(
            (el) => el.offsetParent !== null
        );
        if (!focusables.length) return;

        const first = focusables[0];
        const last = focusables[focusables.length - 1];

        if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first.focus();
        }
    }

    document.addEventListener('keydown', handleModalKeydown);

    // Gatilhos de abertura do modal (botões gerais e cards de serviço)
    document.querySelectorAll('[data-open-quote]').forEach((trigger) => {
        trigger.addEventListener('click', () => {
            const service = trigger.getAttribute('data-quote-service') || '';
            openQuoteModal(service);
        });
    });

    // Gatilhos de fechamento do modal
    document.querySelectorAll('[data-close-quote]').forEach((btn) => {
        btn.addEventListener('click', closeQuoteModal);
    });

    if (quoteModal) {
        quoteModal.addEventListener('click', (event) => {
            if (event.target === quoteModal) {
                closeQuoteModal();
            }
        });
    }

    // Envio do formulário de pré-orçamento para o WhatsApp
    if (quoteForm) {
        quoteForm.addEventListener('submit', (event) => {
            event.preventDefault();

            const carModel = carModelInput ? carModelInput.value.trim() : '';
            const service = serviceSelect ? serviceSelect.value : 'Avaliação geral';
            const problem = problemDescInput ? problemDescInput.value.trim() : '';

            if (!carModel) {
                showToast('Por favor, informe o modelo e ano do veículo.', 'error');
                if (carModelInput) carModelInput.focus();
                return;
            }

            const customerName = customerNameInput ? customerNameInput.value.trim() : '';

            showToast(`Abrindo WhatsApp da ${SITE_CONFIG.name}...`, 'success');
            quoteForm.reset();
            closeQuoteModal();
            openTrackedWhatsApp(service, carModel, { customerName, problem, source: 'modal_orcamento' });
        });
    }

    // 7. Copiar endereço
    const copyAddressBtn = document.getElementById('copy-address-btn');
    if (copyAddressBtn) {
        copyAddressBtn.addEventListener('click', copyAddress);
    }

    // 8. Status Aberto/Fechado + atualização periódica a cada 60s
    updateOpenStatus();
    setInterval(updateOpenStatus, 60000);

    // 9. Monitoramento de scroll para o FAB
    updateFabVisibility();
    window.addEventListener('scroll', updateFabVisibility, { passive: true });
});
