/** @odoo-module **/

import {BiometricSignatureDialog} from "./biometric_signature_dialog.esm";
import core from "web.core";
import {registry} from "@web/core/registry";

const signatureSignOca = {
    uploadSignature: function (parent, item, signatureItem, data) {
        item.value = data;
        console.log(item);
        parent.postIframeField(item);
        parent.checkFilledAll();
        var next_items = _.filter(
            parent.info.items,
            (i) => i.tabindex > item.tabindex
        ).sort((a, b) => a.tabindex - b.tabindex);
        if (next_items.length > 0) {
            parent.items[next_items[0].id].dispatchEvent(new Event("focus_signature"));
        }
    },
    generate: function (parent, item, signatureItem) {
        var input = $(
            core.qweb.render(
                "sign_biometric_oca.sign_iframe_field_biometric_signature",
                {item: item}
            )
        )[0];
        if (item.role === parent.info.role) {
            signatureItem[0].addEventListener("focus_signature", () => {
                var signatureOptions = {
                    displaySignatureRatio:
                        signatureItem[0].clientWidth / signatureItem[0].clientHeight,
                };
                parent.env.services.dialog.add(BiometricSignatureDialog, {
                    ...signatureOptions,
                    uploadSignature: (data) =>
                        this.uploadSignature(parent, item, signatureItem, data),
                });
            });
            input.addEventListener("click", (ev) => {
                ev.preventDefault();
                ev.stopPropagation();
                var signatureOptions = {
                    displaySignatureRatio:
                        signatureItem[0].clientWidth / signatureItem[0].clientHeight,
                };
                parent.env.services.dialog.add(BiometricSignatureDialog, {
                    ...signatureOptions,
                    uploadSignature: (data) =>
                        this.uploadSignature(parent, item, signatureItem, data),
                });
            });
            input.addEventListener("keydown", (ev) => {
                if ((ev.keyCode || ev.which) !== 9) {
                    return true;
                }
                ev.preventDefault();
                var next_items = _.filter(
                    parent.info.items,
                    (i) => i.tabindex > item.tabindex && i.role === parent.info.role
                );
                if (next_items.length > 0) {
                    ev.currentTarget.blur();
                    parent.items[next_items[0].id].dispatchEvent(
                        new Event("focus_signature")
                    );
                }
            });
        }
        return input;
    },
    check: function (item) {
        return Boolean(item.value);
    },
};
registry.category("sign_oca").add("biometric", signatureSignOca);
