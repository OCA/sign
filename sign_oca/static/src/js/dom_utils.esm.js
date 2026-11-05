/** @odoo-module **/
/* global document */

/**
 * Build a DOM element from an HTML string (replaces the jQuery
 * `$(html)[0]` idiom, jQuery is no longer shipped with Odoo 20).
 */
export function parseHTML(html) {
    const template = document.createElement("template");
    template.innerHTML = html.trim();
    return template.content.firstElementChild;
}
