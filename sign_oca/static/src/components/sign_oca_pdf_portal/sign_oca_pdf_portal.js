odoo.define("sign_oca.document_portal_base", function (require) {
    "use strict";
    const {useRef} = owl.hooks;
    const env = require("web.public_env");
    var session = require("web.session");
    const SignOcaPdf = require("sign_oca/static/src/components/sign_oca_pdf/sign_oca_pdf.js");
    class SignOcaPdfPortal extends SignOcaPdf {
        constructor() {
            super(...arguments);
            this.signOcaFooter = useRef("sign_oca_footer");
        }
        async willStart() {
            this.info = await this.env.services.rpc({
                route:
                    "/sign_oca/info/" +
                    this.props.signer_id +
                    "/" +
                    this.props.access_token,
            });
        }

        getPdfUrl() {
            return (
                "/sign_oca/content/" +
                this.props.signer_id +
                "/" +
                this.props.access_token
            );
        }
        checkToSign() {
            this.to_sign = this.to_sign_update;
            if (this.to_sign_update) {
                $(this.signOcaFooter.el).show();
            } else {
                $(this.signOcaFooter.el).hide();
            }
        }
        postIframeFields() {
            super.postIframeFields(...arguments);
            this.checkFilledAll();
        }
        _onClickSign() {
            this.env.services.rpc({
                route:
                    "/sign_oca/sign/" +
                    this.props.signer_id +
                    "/" +
                    this.props.access_token,
                params: {items: this.info.items},
            });
        }
    }
    SignOcaPdfPortal.template = "sign_oca.SignOcaPdfPortal";
    function initDocumentToSign(properties) {
        return session.session_bind(session.origin).then(function () {
            session.module_list.push("web");
            session.module_list.push("portal");
            session.module_list.push("sign_oca");
            return Promise.all([
                session.load_translations(),
                session.load_qweb(session.module_list),
            ]).then(async function () {
                await session.is_bound;
                env.qweb.addTemplates(session.owlTemplates);
                await owl.utils.whenReady();
                var component = new SignOcaPdfPortal(undefined, properties);
                component.mount(document.body);
            });
        });
    }
    return {
        initDocumentToSign: initDocumentToSign,
        Document: Document,
    };
});
