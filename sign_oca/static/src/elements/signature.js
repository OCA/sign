odoo.define("sign_oca.signatureElement", function (require) {
    "use strict";
    const core = require("web.core");
    const _t = core._t;
    const SignRegistry = require("sign_oca.SignRegistry");
    const Dialog = require("web.Dialog");
    var NameAndSignature = require("web.name_and_signature").NameAndSignature;
    const SignatureDialog = Dialog.extend({
        template: "sign_oca.sign_oca_sign_dialog",
        custom_events: {
            signature_changed: "_onChangeSignature",
        },
        init: function (parent, options) {
            options = options || {};
            this.item = options.item;
            options.title = options.title || _t("Adopt Your Signature");
            options.size = options.size || "medium";
            if (!options.buttons) {
                options.buttons = [];
                options.buttons.push({text: _t("Cancel"), close: true});
                options.buttons.push({
                    text: _t("Sign"),
                    classes: "btn-primary",
                    disabled: true,
                    click: () => {
                        this.sign();
                    },
                });
            }
            this._super(parent, options);
            this.nameAndSignature = new NameAndSignature(
                this,
                options.signatureOptions
            );
        },
        willStart: function () {
            return Promise.all([
                this.nameAndSignature.appendTo($("<div>")),
                this._super.apply(this, arguments),
            ]);
        },
        start: function () {
            var self = this;
            this.opened().then(function () {
                self.$(".o_sign_oca_signature").replaceWith(self.nameAndSignature.$el);
                self.nameAndSignature.resetSignature();
            });
            return this._super.apply(this, arguments);
        },
        _onChangeSignature: function () {
            this.$footer
                .find(".btn-primary")
                .prop("disabled", this.nameAndSignature.isSignatureEmpty());
        },
        sign: function () {
            if (this.nameAndSignature.isSignatureEmpty()) {
                /* TODO: Remove signature*/
            } else {
                var signature = this.nameAndSignature.getSignatureImage()[1];
                this.item.value = signature;
                this.getParent().postIframeField(this.item);
            }
            this.getParent().checkFilledAll();
            var next_items = _.filter(
                this.getParent().info.items,
                (i) => i.tabindex > this.item.tabindex
            ).sort((a, b) => a.tabindex - b.tabindex);
            if (next_items.length > 0) {
                this.getParent().items[next_items[0].id].dispatchEvent(
                    new Event("focus_signature")
                );
            }
            this.close();
        },
    });
    const signatureSignOca = {
        generate: function (parent, item, signatureItem) {
            var input = $(
                core.qweb.render("sign_oca.sign_iframe_field_signature", {item: item})
            )[0];
            if (item.role_id === parent.info.role_id) {
                signatureItem[0].addEventListener("focus_signature", () => {
                    var signatureOptions = {
                        fontColor: "DarkBlue",
                        defaultName: parent.info.partner.name,
                    };
                    new SignatureDialog(parent, {signatureOptions, item}).open();
                });
                input.addEventListener("click", (ev) => {
                    ev.preventDefault();
                    ev.stopPropagation();
                    var signatureOptions = {
                        fontColor: "DarkBlue",
                        defaultName: parent.info.partner.name,
                    };
                    new SignatureDialog(parent, {signatureOptions, item}).open();
                });
                input.addEventListener("keydown", (ev) => {
                    if ((ev.keyCode || ev.which) !== 9) {
                        return true;
                    }
                    ev.preventDefault();
                    var next_items = _.filter(
                        parent.info.items,
                        (i) =>
                            i.tabindex > item.tabindex && i.role_id === parent.role_id
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
    SignRegistry.add("signature", signatureSignOca);
    return signatureSignOca;
});
