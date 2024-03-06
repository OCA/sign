odoo.define("sign_oca/static/src/components/sign_oca_pdf/sign_oca_pdf.js", function (
    require
) {
    "use strict";

    const core = require("web.core");
    const SignOcaPdfCommon = require("sign_oca/static/src/components/sign_oca_pdf_common/sign_oca_pdf_common.js");
    const SignRegistry = require("sign_oca.SignRegistry");
    class SignOcaPdf extends SignOcaPdfCommon {
        constructor() {
            super(...arguments);
            this.to_sign = false;
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
        renderButtons(to_sign) {
            var $buttons = $(
                core.qweb.render("oca_sign_oca.SignatureButtons", {
                    to_sign: to_sign,
                })
            );
            $buttons.on("click.o_sign_oca_button_sign", () => {
                this.env.services
                    .rpc({
                        model: this.props.model,
                        method: "action_sign",
                        args: [[this.props.res_id], this.info.items],
                    })
                    .then(() => {
                        this.props.trigger("history_back");
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
                return this.env.dataManager
                    .load_filters(payload)
                    .then(payload.on_success);
            } else {
                payload.__targetWidget = ev.target;
                this.trigger(evType.replace(/_/g, "-"), payload);
            }
        }
        postIframeField(item) {
            var signatureItem = super.postIframeField(...arguments);
            signatureItem[0].append(
                SignRegistry.map[item.field_type].generate(this, item, signatureItem)
            );
            return signatureItem;
        }
        checkFilledAll() {
            this.to_sign_update =
                _.filter(this.info.items, (item) => {
                    return (
                        item.required &&
                        item.role_id === this.info.role_id &&
                        !SignRegistry.map[item.field_type].check(item)
                    );
                }).length === 0;
            this.checkToSign();
        }
    }
    return SignOcaPdf;
});
