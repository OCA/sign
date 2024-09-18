/* @odoo-module */

import {Component, onWillUpdateProps, useEffect, useRef, useState} from "@odoo/owl";

import {useService} from "@web/core/utils/hooks";
import {hidePDFJSButtons} from "@web/libs/pdfjs";

/**
 * @typedef {Object} Props
 * @property {number} threadId
 * @property {string} threadModel
 * @extends {Component<Props, Env>}
 */
export class AttachmentView extends Component {
    static template = "mail.AttachmentView";
    static components = {};
    static props = [];

    setup() {
    }

    close() {
        this.update({isOpen: false});
    }
    async fetchData() {
        const data = await this.messaging.rpc({
            model: "res.users",
            method: "sign_oca_request_user_count",
            args: [],
            kwargs: {context: session.user_context},
        });

        this.update({
            requestGroups: data.map((vals) =>
                this.messaging.models.RequestGroup.convertData(vals)
            ),
            extraCount: 0,
        });
    }
    /**
     * @param {MouseEvent} ev
     */
    onClickDropdownToggle(ev) {
        ev.preventDefault();
        if (this.isOpen) {
            this.update({isOpen: false});
        } else {
            this.update({isOpen: true});
            this.fetchData();
        }
    }
    /**
     * Closes the menu when clicking outside, if appropriate.
     *
     * @private
     * @param {MouseEvent} ev
     */
    onClickCaptureGlobal(ev) {
        if (!this.exists()) {
            return;
        }
        if (!this.component || !this.component.root.el) {
            return;
        }
        if (this.component.root.el.contains(ev.target)) {
            return;
        }
        this.close();
    }
}
