/** @odoo-module **/
/* global */
/* Copyright 2025 Kencove - Mohamed Alkobrosli
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl). */

import {Reactive} from "@web/core/utils/reactive";
import {reactive} from "@odoo/owl";
import {registry} from "@web/core/registry";

export class WatchSignRequestsService extends Reactive {
    static modelToLoad = [];
    static serviceDependencies = ["bus_service", "orm", "notification"];

    constructor() {
        super();
        this.ready = this.setup(...arguments).then(() => this);
    }

    async setup(env, {bus_service, orm, notification}) {
        this.env = env;
        this.bus_service = bus_service;
        this.orm = orm;
        this.notification = notification;
        this.sign_requests = reactive({signerCounter: 0, signerGroups: []});

        this.bus_service.subscribe("sign_oca_request_updates", async ({message}) => {
            if (message) {
                await this.fetchSystraySigner();
            }
        });
    }
    async fetchSystraySigner() {
        const groups = await this.orm.call("res.users", "sign_oca_request_user_count");
        let total = 0;
        for (const group of groups) {
            total += group.total_records || 0;
        }
        this.sign_requests.signerGroups = groups;
        this.sign_requests.signerCounter = total;
        return {groups, total};
    }
    getTotalSignRequests() {
        return this.sign_requests.signerCounter;
    }
}

export const watchSignRequestsService = {
    dependencies: WatchSignRequestsService.serviceDependencies,
    async start(env, services) {
        return new WatchSignRequestsService(env, services).ready;
    },
};

registry.category("services").add("watchSignRequests", watchSignRequestsService);
