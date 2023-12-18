/** @odoo-module **/

import SignOcaPdfCommon from "../sign_oca_pdf_common/sign_oca_pdf_common.esm.js";
import core from "web.core";
import {registry} from "@web/core/registry";
const SignRegistry = registry.category("sign_oca");
export default class SignOcaPdf extends SignOcaPdfCommon {
    setup() {
        super.setup(...arguments);
        this.to_sign = false;
        this.sensitiveData = {};
    }
    async willStart() {
        await super.willStart(...arguments);
        this.checkFilledAll();
    }
    checkToSign() {
        this.props.updateControlPanel({
            cp_content: {
                $buttons: this.renderButtons(this.to_sign_update),
            },
        });
        this.to_sign = this.to_sign_update;
    }
    async _encryptSensitiveData(publicKeyBase64) {
        const publicKeyBytes = Uint8Array.from(atob(publicKeyBase64), (c) =>
            c.charCodeAt(0)
        );
        var importedPublicKey = await crypto.subtle.importKey(
            "spki",
            publicKeyBytes.buffer,
            {name: "ECDH", namedCurve: "P-256"},
            true,
            []
        );
        const privateKey = await crypto.subtle.generateKey(
            {
                name: "ECDH",
                namedCurve: "P-256",
            },
            true,
            ["deriveKey"]
        );
        const sharedKey = await crypto.subtle.deriveKey(
            {
                name: "ECDH",
                public: importedPublicKey,
            },
            privateKey.privateKey,
            {
                name: "AES-CBC",
                length: 256,
            },
            true,
            ["encrypt", "decrypt"]
        );
        const iv = crypto.getRandomValues(new Uint8Array(16));
        const encryptedBuffer = await crypto.subtle.encrypt(
            {
                name: "AES-CBC",
                iv: iv,
            },
            sharedKey,
            new TextEncoder().encode(JSON.stringify(this.sensitiveData))
        );
        const publicKey = await crypto.subtle.exportKey("spki", privateKey.publicKey);
        this.encryptedData = {
            iv: btoa(String.fromCharCode(...iv)),
            data: btoa(String.fromCharCode(...new Uint8Array(encryptedBuffer))),
            public: btoa(String.fromCharCode(...new Uint8Array(publicKey))),
        };
    }
    renderButtons(to_sign) {
        var $buttons = $(
            core.qweb.render("oca_sign_oca.SignatureButtons", {
                to_sign: to_sign,
            })
        );
        $buttons.on("click.o_sign_oca_button_sign", () => {
            // TODO: Add encryption here
            var todoFirst = [];
            this.encryptedData = {};
            if (
                Object.keys(this.sensitiveData).length > 0 &&
                this.info.certificate_id
            ) {
                todoFirst.push(
                    new Promise((resolve) => {
                        this.env.services
                            .rpc({
                                model: "sign.oca.certificate",
                                method: "read",
                                args: [[this.info.certificate_id], ["data"]],
                            })
                            .then((public_certificate_info) => {
                                this._encryptSensitiveData(
                                    public_certificate_info[0].data
                                ).then(() => {
                                    resolve();
                                });
                            });
                    })
                );
            }
            Promise.all(todoFirst).then(() => {
                this.env.services
                    .rpc({
                        model: this.props.model,
                        method: "action_sign",
                        args: [
                            [this.props.res_id],
                            this.info.items,
                            this.encryptedData,
                        ],
                    })
                    .then(() => {
                        this.props.trigger("history_back");
                    });
            });
        });
        return $buttons;
    }
    _trigger_up(ev) {
        const evType = ev.name;
        const payload = ev.data;
        if (evType === "call_service") {
            let args = payload.args || [];
            if (payload.service === "ajax" && payload.method === "rpc") {
                // Ajax service uses an extra 'target' argument for rpc
                args = args.concat(ev.target);
            }
            const service = this.env.services[payload.service];
            const result = service[payload.method].apply(service, args);
            payload.callback(result);
        } else if (evType === "get_session") {
            if (payload.callback) {
                payload.callback(this.env.session);
            }
        } else if (evType === "load_views") {
            const params = {
                model: payload.modelName,
                context: payload.context,
                views_descr: payload.views,
            };
            this.env.dataManager
                .load_views(params, payload.options || {})
                .then(payload.on_success);
        } else if (evType === "load_filters") {
            return this.env.dataManager.load_filters(payload).then(payload.on_success);
        } else {
            payload.__targetWidget = ev.target;
            this.trigger(evType.replace(/_/g, "-"), payload);
        }
    }
    postIframeField(item) {
        if (item.role_id === this.info.role_id) {
            var signatureItem = super.postIframeField(...arguments);
            signatureItem[0].append(
                SignRegistry.get(item.field_type).generate(this, item, signatureItem)
            );
            return signatureItem;
        }
    }
    checkFilledAll() {
        this.to_sign_update =
            _.filter(this.info.items, (item) => {
                return (
                    item.required &&
                    item.role_id === this.info.role_id &&
                    !SignRegistry.get(item.field_type).check(item)
                );
            }).length === 0;
        this.checkToSign();
    }
}
