/** @odoo-module **/

import {attr, one} from "@mail/model/model_field";
import {registerModel} from "@mail/model/model_core";

registerModel({
    name: "ir.model.request",
    fields: {
        /**
         * Determines the name of the views that are available for this model.
         */
        availableWebViews: attr({
            compute() {
                return ["kanban", "list", "form", "activity"];
            },
        }),
        requestGroup: one("RequestGroup", {
            inverse: "irModel",
        }),
        iconUrl: attr(),
        id: attr({
            identifying: true,
        }),
        model: attr({
            default: "sign.oca.request",
            required: true,
        }),
        name: attr(),
    },
});
