/** @odoo-module **/
/* global window, document, HTMLElement */

import {signal, t, useProps, whenReady} from "@odoo/owl";
import {mountComponent} from "@web/env";
import SignOcaPdf from "../sign_oca_pdf/sign_oca_pdf.esm.js";
import {MainComponentsContainer} from "@web/core/main_components_container";
import {rpc} from "@web/core/network/rpc";
import {startSignItemNavigator} from "./sign_oca_navigator.esm";

export class SignOcaPdfPortal extends SignOcaPdf {
    props = useProps({
        access_token: t.string(),
        signer_id: t.number(),
    });

    setup() {
        this.rpc = rpc;
        this.signOcaFooter = signal.ref(HTMLElement);
        this.signer_id = this.props.signer_id;
        this.access_token = this.props.access_token;
        super.setup(...arguments);
    }
    async willStart() {
        this.info = await this.rpc(
            "/sign_oca/info/" + this.signer_id + "/" + this.access_token
        );
    }
    getPdfUrl() {
        return "/sign_oca/content/" + this.signer_id + "/" + this.access_token;
    }
    checkToSign() {
        this.to_sign = this.to_sign_update;
        const signButton = document.getElementById("sign_oca_button");
        if (this.to_sign_update) {
            this.signOcaFooter().style.display = "";
            if (signButton) {
                signButton.disabled = false;
            }
        } else {
            this.signOcaFooter().style.display = "none";
            if (signButton) {
                signButton.disabled = true;
            }
        }
    }
    postIframeFields() {
        super.postIframeFields(...arguments);
        this.checkFilledAll();
        // Is essential to make sure the navigator will never duplicate
        const iframeDocument = this.iframe().contentDocument;
        const target = iframeDocument.getElementById("viewerContainer");
        for (const className of [
            "o_sign_sign_item_navline",
            "o_sign_sign_item_navigator",
        ]) {
            if (iframeDocument.getElementsByClassName(className).length === 0) {
                const element = iframeDocument.createElement("div");
                element.className = className;
                target.append(element);
            }
        }
        // Load navigator
        this.navigate();
    }
    async _onClickSign(ev) {
        ev.target.disabled = true;
        const position = await this.getLocation();
        this.rpc("/sign_oca/sign/" + this.signer_id + "/" + this.access_token, {
            items: this.info.items,
            latitude: position && position.coords && position.coords.latitude,
            longitude: position && position.coords && position.coords.longitude,
        }).then((action) => {
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
    navigate() {
        const target = this.iframe().contentDocument.getElementById("viewerContainer");
        this.navigator = startSignItemNavigator(this, target, this.env);
    }
}
SignOcaPdfPortal.template = "sign_oca.SignOcaPdfPortal";
SignOcaPdfPortal.components = {MainComponentsContainer};

export async function initDocumentToSign(document, sign_oca_backend_info) {
    await whenReady();
    await mountComponent(SignOcaPdfPortal, document.body, {
        name: "Sign OCA",
        props: {
            access_token: sign_oca_backend_info.access_token,
            signer_id: sign_oca_backend_info.signer_id,
        },
    });
}
export default {SignOcaPdfPortal, initDocumentToSign};
