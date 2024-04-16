/** @odoo-module **/

import {registry} from "@web/core/registry";
import {systrayService} from "@sign_oca/js/systray_service.esm";

const serviceRegistry = registry.category("services");
serviceRegistry.add("request_systray_service", systrayService);
