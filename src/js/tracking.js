/**
 * Rastreamento de leads e envio para WhatsApp.
 * Lê a configuração do cliente injetada no build (#client-config).
 */

export function getConfig() {
    const el = document.getElementById('client-config');
    try {
        return JSON.parse(el.textContent);
    } catch (_e) {
        console.error('client-config ausente ou inválido');
        return null;
    }
}

const LS_KEY = 'gr66_leads';

function bumpLocalCounter(eventName, service) {
    try {
        const data = JSON.parse(localStorage.getItem(LS_KEY) || '{"total":0,"byEvent":{},"byService":{},"byDay":{}}');
        const day = new Date().toISOString().slice(0, 10);
        data.total += 1;
        data.byEvent[eventName] = (data.byEvent[eventName] || 0) + 1;
        if (service) data.byService[service] = (data.byService[service] || 0) + 1;
        data.byDay[day] = (data.byDay[day] || 0) + 1;
        localStorage.setItem(LS_KEY, JSON.stringify(data));
    } catch (_e) {
        /* localStorage indisponível (modo privado): ignora */
    }
}

/** Dispara evento em dataLayer, gtag (GA4), Clarity e contador local. */
export function trackEvent(eventName, params = {}) {
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({ event: eventName, ...params });
    if (typeof window.gtag === 'function') window.gtag('event', eventName, params);
    if (typeof window.clarity === 'function') window.clarity('event', eventName);
    bumpLocalCounter(eventName, params.service_name);
}

/**
 * Formata a mensagem com a tag [Site Oficial], rastreia e abre o WhatsApp.
 * @param {string} serviceName  Serviço desejado
 * @param {string} vehicleInfo  Modelo/ano do veículo
 * @param {{customerName?: string, problem?: string, source?: string, customMessage?: string}} [extra]
 */
export function openTrackedWhatsApp(serviceName, vehicleInfo, extra = {}) {
    const cfg = getConfig();
    const tag = cfg.site.trackingTag;
    const { customerName = '', problem = '', source = 'site', customMessage = '' } = extra;

    let text;
    if (customMessage) {
        text = `${tag} ${customMessage}`;
    } else {
        text = `${tag} Olá *${cfg.site.name}*! Gostaria de um pré-orçamento:\n\n`;
        if (customerName) text += `👤 *Nome:* ${customerName}\n`;
        if (vehicleInfo) text += `🚗 *Veículo:* ${vehicleInfo}\n`;
        if (serviceName) text += `🔧 *Serviço:* ${serviceName}\n`;
        if (problem) text += `📝 *Detalhes:* ${problem}\n`;
        text += `\nPoderiam me informar disponibilidade de horário?`;
    }

    trackEvent('whatsapp_click', {
        service_name: serviceName || 'geral',
        has_vehicle_info: Boolean(vehicleInfo),
        source,
    });

    const url = `https://wa.me/${cfg.contact.whatsappNumber}?text=${encodeURIComponent(text)}`;
    window.open(url, '_blank', 'noopener,noreferrer');
}
