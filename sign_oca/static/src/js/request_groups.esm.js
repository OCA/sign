/** @odoo-module **/

import {attr, many, one} from "@mail/model/model_field";
import {registerModel} from "@mail/model/model_core";

registerModel({
    name: "RequestGroup",
    modelMethods: {
        convertData(data) {
            return {
                domain: data.domain,
                irModel: {
                    iconUrl: data.icon,
                    id: data.id,
                    model: data.model,
                    name: data.name,
                },
                pending_count: data.total_records,
            };
        },
    },
    recordMethods: {
        /**
         * @private
         */
        _onChangePendingCount() {
            if (this.pending_count === 0) {
                this.delete();
            }
        },
    },
    fields: {
        requestGroupViews: many("RequestGroupView", {
            inverse: "requestGroup",
        }),
        domain: attr(),
        irModel: one("ir.model.request", {
            identifying: true,
            inverse: "requestGroup",
        }),
        pending_count: attr({
            default: 0,
        }),
        type: attr(),
    },
    onChanges: [
        {
            dependencies: ["pending_count", "type"],
            methodName: "_onChangePendingCount",
        },
    ],
});
