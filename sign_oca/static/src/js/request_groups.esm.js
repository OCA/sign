/* @odoo-module */

import {Record} from "@mail/core/common/record";

export class RequestGroup extends Record {
    static pending_count = 0;
    /** @returns {import("models").RequestGroup} */
    static get(data) {
        return super.get(data);
    }
    /** @returns {import("models").RequestGroup|import("models").RequestGroup[]} */
    static insert(data) {
        return super.insert(...arguments);
    }

    /** @type {number} */
    domain;
    /** @type {string} */
    type;
    /** @type {number} */
    pending_count;

    _onChangePendingCount() {
        if (this.pending_count === 0) {
            this.delete();
        }
    }
}

RequestGroup.register();
