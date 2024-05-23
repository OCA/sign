/** @odoo-module **/

const {App, mount, useRef} = owl;

import SignOcaPdf from "../sign_oca_pdf/sign_oca_pdf.esm.js";

import env from "web.public_env";
import {renderToString} from "@web/core/utils/render";
import session from "web.session";
import {templates} from "@web/core/assets";
export class SignOcaPdfPortal extends SignOcaPdf {
    setup() {
        super.setup(...arguments);
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
            "/sign_oca/content/" + this.props.signer_id + "/" + this.props.access_token
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
        this.env.services
            .rpc({
                route:
                    "/sign_oca/sign/" +
                    this.props.signer_id +
                    "/" +
                    this.props.access_token,
                params: {items: this.info.items},
            })
            .then((action) => {
                // As we are on frontend env, it is not possible to use do_action(), so we
                // redirect to the corresponding URL or reload the page if the action is not
                // an url.
                if (action.type === "ir.actions.act_url") {
                    window.location = action.url;
                } else {
                    window.location.reload();
                }
            });
    }
}
SignOcaPdfPortal.template = "sign_oca.SignOcaPdfPortal";
SignOcaPdfPortal.props = {
    access_token: {type: String},
    signer_id: {type: Number},
};
export function initDocumentToSign(properties) {
    return session.session_bind(session.origin).then(function () {
        return Promise.all([
            session.load_translations(["web", "portal", "sign_oca"]),
        ]).then(async function () {
            var app = new App(null, {templates, test: true});
            renderToString.app = app;
            mount(SignOcaPdfPortal, document.body, {
                env,
                props: properties,
                templates: templates,
            });
        });
    });
}
