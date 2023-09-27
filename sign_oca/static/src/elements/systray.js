odoo.define("sign_oca.systray", function (require) {
    "use strict";

    var core = require("web.core");
    var session = require("web.session");
    var SystrayMenu = require("web.SystrayMenu");
    var Widget = require("web.Widget");

    var QWeb = core.qweb;

    var RequestMenu = Widget.extend({
        template: "sign.oca.RequestMenu",
        events: {
            "show.bs.dropdown": "_onSignOcaRequestMenuShow",
            "click .o_mail_activity_action": "_onSignOcaRequestActionClick",
            "click .o_mail_preview": "_onSignOcaRequestFilterClick",
        },
        start: function () {
            this.$requests_preview = this.$(".o_mail_systray_dropdown_items");
            this._updateSignOcaRequestPreview();
            var channel = "sign.oca";
            this.call("bus_service", "addChannel", channel);
            this.call("bus_service", "startPolling");
            this.call(
                "bus_service",
                "onNotification",
                this,
                this._updateSignOcaRequestPreview
            );
            return this._super();
        },

        // Private
        _getSignOcaRequestData: function () {
            var self = this;
            return self
                ._rpc({
                    model: "res.users",
                    method: "sign_oca_request_user_count",
                    kwargs: {
                        context: session.user_context,
                    },
                })
                .then(function (data) {
                    self.requests = data;
                    self.requestCounter = _.reduce(
                        data,
                        function (total_count, p_data) {
                            return total_count + p_data.total_records;
                        },
                        0
                    );
                    self.$(".o_notification_counter").text(self.requestCounter);
                    self.$el.toggleClass("o_no_notification", !self.requestCounter);
                });
        },
        _updateSignOcaRequestPreview: function () {
            var self = this;
            self._getSignOcaRequestData().then(function () {
                self.$requests_preview.html(
                    QWeb.render("sign.oca.RequestMenuPreview", {
                        requests: self.requests,
                    })
                );
            });
        },
        _updateCounter: function (data) {
            if (data) {
                this.$(".o_notification_counter").text(this.requestCounter);
                this.$el.toggleClass("o_no_notification", !this.requestCounter);
            }
        },
        // ------------------------------------------------------------
        // Handlers
        // ------------------------------------------------------------

        _onSignOcaRequestFilterClick: function (event) {
            var data = _.extend(
                {},
                $(event.currentTarget).data(),
                $(event.target).data()
            );
            this.do_action({
                type: "ir.actions.act_window",
                name: data.model_name,
                res_model: "sign.oca.request.signer",
                views: [
                    [false, "list"],
                    [false, "form"],
                ],
                search_view_id: [false],
                domain: [
                    ["request_id.state", "=", "sent"],
                    ["partner_id", "child_of", [session.partner_id]],
                    ["signed_on", "=", false],
                    ["model", "=", data.res_model],
                ],
            });
        },
        _onSignOcaRequestMenuShow: function () {
            this._updateSignOcaRequestPreview();
        },
    });

    SystrayMenu.Items.push(RequestMenu);

    return RequestMenu;
});
