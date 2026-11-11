/** @odoo-module **/
/* global window, setTimeout, document, clearTimeout */
import {_t} from "@web/core/l10n/translation";
import {Component, onMounted, onWillStart, onWillUnmount, useRef} from "@odoo/owl";
import {AlertDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {renderToString} from "@web/core/utils/render";
import {useService} from "@web/core/utils/hooks";

export default class SignOcaPdfCommon extends Component {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.field_template = "sign_oca.sign_iframe_field";
        this.pdf_url = this.getPdfUrl();
        this.viewer_url = "/web/static/lib/pdfjs/web/viewer.html?file=" + this.pdf_url;
        this.iframe = useRef("sign_oca_iframe");
        var iframeResolve = "";
        var iframeReject = "";
        this.iframeLoaded = new Promise(function (resolve, reject) {
            iframeResolve = resolve;
            iframeReject = reject;
        });
        this.items = {};
        onWillUnmount(() => {
            clearTimeout(this.reviewFieldsTimeout);
            this.unbindPageRendered();
        });
        this.iframeLoaded.resolve = iframeResolve;
        this.iframeLoaded.reject = iframeReject;
        onWillStart(this.willStart.bind(this));
        onMounted(() => {
            this.waitIframeLoaded();
        });
        this.dialogService = useService("dialog");
    }
    getPdfUrl() {
        return "/web/content/" + this.model + "/" + this.res_id + "/data";
    }
    async willStart() {
        this.info = await this.orm.call(this.model, "get_info", [[this.res_id]]);
    }
    waitIframeLoaded() {
        var error = this.iframe.el.contentDocument.getElementById("errorWrapper");
        if (error && window.getComputedStyle(error).display !== "none") {
            this.iframeLoaded.resolve();
            return this.dialogService.add(AlertDialog, {
                body: _t("Need a valid PDF to add signature fields !"),
            });
        }
        var nbPages =
            this.iframe.el.contentDocument.getElementsByClassName("page").length;
        var nbLayers =
            this.iframe.el.contentDocument.getElementsByClassName(
                "endOfContent"
            ).length;
        if (nbPages > 0 && nbLayers > 0) {
            this.postIframeFields();
            this.reviewFields();
        } else {
            var self = this;
            setTimeout(function () {
                self.waitIframeLoaded();
            }, 50);
        }
    }
    reviewFields() {
        if (
            this.iframe.el.contentDocument.getElementsByClassName("o_sign_oca_ready")
                .length === 0
        ) {
            this.postIframeFields();
        }
        this.reviewFieldsTimeout = setTimeout(this.reviewFields.bind(this), 1000);
    }
    postIframeFields() {
        this.iframe.el.contentDocument
            .getElementById("viewerContainer")
            .addEventListener(
                "drop",
                (e) => {
                    e.stopImmediatePropagation();
                    e.stopPropagation();
                },
                true
            );
        var iframeCss = document.createElement("link");
        iframeCss.setAttribute("rel", "stylesheet");
        iframeCss.setAttribute("href", "/sign_oca/get_assets.css");

        var iframeJs = document.createElement("script");
        iframeJs.setAttribute("type", "text/javascript");
        iframeJs.setAttribute("src", "/sign_oca/get_assets.js");
        this.iframe.el.contentDocument
            .getElementsByTagName("head")[0]
            .append(iframeCss);
        this.iframe.el.contentDocument.getElementsByTagName("head")[0].append(iframeJs);
        $.each(this.info.items, (key) => {
            this.postIframeField(this.info.items[key]);
        });
        $(this.iframe.el.contentDocument.getElementsByClassName("page")[0]).append(
            $("<div class='o_sign_oca_ready'/>")
        );

        $(this.iframe.el.contentDocument.getElementById("viewer")).addClass(
            "sign_oca_ready"
        );
        this.iframeLoaded.resolve();
        this.bindPageRendered();
    }
    /*
     * The pdf.js viewer only keeps a few pages rendered and resets the DOM of the
     * others, which destroys the field elements injected into those pages. The single
     * o_sign_oca_ready marker on the first page cannot detect that loss, so the
     * fields of the other pages would never come back. Inject the items of a
     * page again every time pdf.js finishes rendering it.
     */
    bindPageRendered() {
        if (this.pageRenderedBound) {
            return;
        }
        const app =
            this.iframe.el.contentWindow &&
            this.iframe.el.contentWindow.PDFViewerApplication;
        if (!app || !app.eventBus) {
            this.bindPageRenderedTimeout = setTimeout(
                this.bindPageRendered.bind(this),
                250
            );
            return;
        }
        this.pageRenderedBound = true;
        this.pageRenderedBus = app.eventBus;
        this.pageRenderedHandler = (ev) => {
            const pageNumber = ev && ev.pageNumber;
            if (!pageNumber || !this.info || !this.iframe.el) {
                return;
            }
            $.each(this.info.items, (key) => {
                const item = this.info.items[key];
                const el = this.items[item.id];
                if (item.page === pageNumber && !(el && el.isConnected)) {
                    this.postIframeField(item);
                }
            });
        };
        this.pageRenderedBus.on("pagerendered", this.pageRenderedHandler);
    }
    unbindPageRendered() {
        clearTimeout(this.bindPageRenderedTimeout);
        if (this.pageRenderedBus) {
            this.pageRenderedBus.off("pagerendered", this.pageRenderedHandler);
        }
        this.pageRenderedBus = null;
        this.pageRenderedHandler = null;
        this.pageRenderedBound = false;
    }
    /*
     * Return the live element of an item, bringing its page back into view
     * when pdf.js has recycled it, so that the page is rendered again and
     * its fields are injected by the pagerendered handler.
     */
    async getLiveItemElement(item_id) {
        const item = this.info.items[item_id];
        const isLive = () => this.items[item_id] && this.items[item_id].isConnected;
        if (!isLive() && item && this.iframe.el) {
            const app = this.iframe.el.contentWindow.PDFViewerApplication;
            app.pdfViewer.currentPageNumber = item.page;
            for (let i = 0; i < 60 && !isLive(); i++) {
                await new Promise((resolve) => setTimeout(resolve, 50));
            }
        }
        return isLive() ? this.items[item_id] : null;
    }
    postIframeField(item) {
        if (this.items[item.id]) {
            // Keep text typed in a field whose change event has not fired yet,
            // e.g. when pdf.js removed the page while the input had the focus.
            const input = this.items[item.id].querySelector("input");
            if (input && input.type === "text" && input.value !== (item.value || "")) {
                item.value = input.value;
                if (this.checkFilledAll) {
                    this.checkFilledAll();
                }
            }
            this.items[item.id].remove();
        }
        var page =
            this.iframe.el.contentDocument.getElementsByClassName("page")[
                item.page - 1
            ];
        var signatureItem = $(
            renderToString(this.field_template, {
                ...item,
            })
        );
        page.append(signatureItem[0]);
        this.items[item.id] = signatureItem[0];
        return signatureItem;
    }
    // CheckSignItemsCompletion and navigate functions for handling navigation
    checkSignItemsCompletion() {
        const signItemsToComplete = [];
        $.each(this.info.items, (key, value) => {
            if (this.postIframeField(value) && this.postIframeField(value)[0]) {
                const $element = $(value);
                const signItemToComplete = {};
                signItemToComplete.data = $element[0];
                signItemToComplete.el = this.postIframeField(value)[0];
                signItemsToComplete.push(signItemToComplete);
            }
        });
        return signItemsToComplete;
    }
}
SignOcaPdfCommon.template = "sign_oca.SignOcaPdfCommon";
SignOcaPdfCommon.props = [];
