/** @odoo-module **/
const {Component, onMounted, onWillStart, onWillUnmount, useRef} = owl;
import Dialog from "web.Dialog";
import core from "web.core";
const _t = core._t;
export default class SignOcaPdfCommon extends Component {
    setup() {
        super.setup(...arguments);
        this.field_template = "sign_oca.sign_iframe_field";
        console.log(this.props);
        this.pdf_url = this.getPdfUrl();
        this.viewer_url = "/web/static/lib/pdfjs/web/viewer.html?file=" + this.pdf_url;
        this.iframe = useRef("sign_oca_iframe");
        var iframeResolve = undefined;
        var iframeReject = undefined;
        this.iframeLoaded = new Promise(function (resolve, reject) {
            iframeResolve = resolve;
            iframeReject = reject;
        });
        this.items = {};
        onWillUnmount(() => {
            clearTimeout(this.reviewFieldsTimeout);
        });
        this.iframeLoaded.resolve = iframeResolve;
        this.iframeLoaded.reject = iframeReject;
        onWillStart(this.willStart.bind(this));
        onMounted(() => {
            this.waitIframeLoaded();
        });
    }
    getPdfUrl() {
        return "/web/content/" + this.props.model + "/" + this.props.res_id + "/data";
    }
    async willStart() {
        this.info = await this.env.services.rpc({
            model: this.props.model,
            method: "get_info",
            args: [[this.props.res_id]],
        });
    }
    waitIframeLoaded() {
        var error = this.iframe.el.contentDocument.getElementById("errorWrapper");
        if (error && window.getComputedStyle(error).display !== "none") {
            this.iframeLoaded.resolve();
            return Dialog.alert(this, _t("Need a valid PDF to add signature fields !"));
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
        _.each(this.info.items, (item) => {
            this.postIframeField(item);
        });
        $(this.iframe.el.contentDocument.getElementsByClassName("page")[0]).append(
            $("<div class='o_sign_oca_ready'/>")
        );

        $(this.iframe.el.contentDocument.getElementById("viewer")).addClass(
            "sign_oca_ready"
        );
        this.iframeLoaded.resolve();
    }
    postIframeField(item) {
        if (this.items[item.id]) {
            this.items[item.id].remove();
        }
        var page =
            this.iframe.el.contentDocument.getElementsByClassName("page")[
                item.page - 1
            ];
        var signatureItem = $(
            core.qweb.render(this.field_template, {
                ...item,
            })
        );
        page.append(signatureItem[0]);
        this.items[item.id] = signatureItem[0];
        return signatureItem;
    }
}
SignOcaPdfCommon.template = "sign_oca.SignOcaPdfCommon";
