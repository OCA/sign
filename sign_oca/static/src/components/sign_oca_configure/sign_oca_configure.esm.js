/** @odoo-module **/

import {ComponentWrapper} from "web.OwlCompatibility";
import AbstractAction from "web.AbstractAction";
import Dialog from "web.Dialog";
import core from "web.core";
import ControlPanel from "web.ControlPanel";
import SignOcaPdfCommon from "../sign_oca_pdf_common/sign_oca_pdf_common.esm.js";
const _t = core._t;
export class SignOcaConfigureControlPanel extends ControlPanel {}
SignOcaConfigureControlPanel.template = "sign_oca.SignOcaConfigureControlPanel";
export class SignOcaConfigure extends SignOcaPdfCommon {
    setup() {
        super.setup(...arguments);
        this.field_template = "sign_oca.sign_iframe_field_configure";
        this.contextMenu = undefined;
        this.isMobile = this.env.device.isMobile || this.env.device.isMobileDevice;
    }
    postIframeFields() {
        super.postIframeFields(...arguments);
        _.each(
            this.iframe.el.contentDocument.getElementsByClassName("page"),
            (page) => {
                page.addEventListener("mousedown", (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    return false;
                });
                page.addEventListener("contextmenu", (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (this.contextMenu !== undefined) {
                        this.contextMenu.remove();
                        this.contextMenu = undefined;
                    }
                    var position = page.getBoundingClientRect();
                    this.contextMenu = $(
                        core.qweb.render("sign_oca.sign_iframe_contextmenu", {
                            page,
                            e,
                            left: ((e.pageX - position.x) * 100) / position.width + "%",
                            top: ((e.pageY - position.y) * 100) / position.height + "%",
                            info: this.info,
                            page_id: parseInt(page.dataset.pageNumber, 10),
                        })
                    );
                    page.append(this.contextMenu[0]);
                });
            }
        );
        this.iframe.el.contentDocument.addEventListener(
            "click",
            (ev) => {
                if (this.contextMenu && !this.creatingItem) {
                    if (this.contextMenu[0].contains(ev.target)) {
                        this.creatingItem = true;
                        this.env.services
                            .rpc({
                                model: this.props.model,
                                method: "add_item",
                                args: [
                                    [this.props.res_id],
                                    {
                                        field_id: parseInt(ev.target.dataset.field, 10),
                                        page: parseInt(ev.target.dataset.page, 10),
                                        position_x: parseFloat(
                                            ev.target.parentElement.style.left
                                        ),
                                        position_y: parseFloat(
                                            ev.target.parentElement.style.top
                                        ),
                                        width: 20,
                                        height: 1.5,
                                    },
                                ],
                            })
                            .then((data) => {
                                this.info.items[data.id] = data;
                                this.postIframeField(data);
                                this.contextMenu.remove();
                                this.contextMenu = undefined;
                                this.creatingItem = false;
                            });
                    } else {
                        this.contextMenu.remove();
                        this.contextMenu = undefined;
                    }
                }
            },
            // We need to enforce it to happen no matter what
            true
        );
        this.iframeLoaded.resolve();
    }
    postIframeField(item) {
        var signatureItem = super.postIframeField(...arguments);
        var dragItem =
            signatureItem[0].getElementsByClassName("o_sign_oca_draggable")[0];
        var resizeItems = signatureItem[0].getElementsByClassName("o_sign_oca_resize");
        signatureItem[0].addEventListener(
            "click",
            (e) => {
                if (
                    e.target.classList.contains("o_sign_oca_resize") ||
                    e.target.classList.contains("o_sign_oca_draggable")
                ) {
                    return;
                }
                var target = e.currentTarget;
                // TODO: Open Dialog for configuration
                var dialog = new Dialog(this, {
                    title: _t("Edit field"),
                    $content: $(
                        core.qweb.render("sign_oca.sign_oca_field_edition", {
                            item,
                            info: this.info,
                        })
                    ),

                    buttons: [
                        {
                            text: _t("Save"),
                            classes: "btn-primary",
                            close: true,
                            click: () => {
                                var field_id = parseInt(
                                    dialog.$el.find('select[name="field_id"]').val(),
                                    10
                                );
                                var role_id = parseInt(
                                    dialog.$el.find('select[name="role_id"]').val(),
                                    10
                                );
                                var required = dialog.$el
                                    .find("input[name='required']")
                                    .prop("checked");
                                var placeholder = dialog.$el
                                    .find("input[name='placeholder']")
                                    .val();
                                this.env.services
                                    .rpc({
                                        model: this.props.model,
                                        method: "set_item_data",
                                        args: [
                                            [this.props.res_id],
                                            item.id,
                                            {
                                                field_id,
                                                role_id,
                                                required,
                                                placeholder,
                                            },
                                        ],
                                    })
                                    .then(() => {
                                        item.field_id = field_id;
                                        item.name = _.filter(
                                            this.info.fields,
                                            (field) => field.id === field_id
                                        )[0].name;
                                        item.role_id = role_id;
                                        item.required = required;
                                        item.placeholder = placeholder;
                                        target.remove();
                                        this.postIframeField(item);
                                    });
                            },
                        },
                        {
                            text: _t("Delete"),
                            classes: "btn-danger",
                            close: true,
                            click: () => {
                                this.env.services
                                    .rpc({
                                        model: this.props.model,
                                        method: "delete_item",
                                        args: [[this.props.res_id], item.id],
                                    })
                                    .then(() => {
                                        delete this.info.items[item.id];
                                        target.remove();
                                    });
                            },
                        },
                        {
                            text: _t("Cancel"),
                            close: true,
                        },
                    ],
                }).open();
            },
            true
        );
        var startFunction = "mousedown";
        var endFunction = "mouseup";
        var moveFunction = "mousemove";
        if (this.isMobile) {
            startFunction = "touchstart";
            endFunction = "touchend";
            moveFunction = "touchmove";
        }
        dragItem.addEventListener(startFunction, (mousedownEvent) => {
            mousedownEvent.preventDefault();
            var parentPage = mousedownEvent.target.parentElement.parentElement;
            this.movingItem = mousedownEvent.target.parentElement;
            var mousemove = this._onDragItem.bind(this);
            parentPage.addEventListener(moveFunction, mousemove);
            parentPage.addEventListener(
                endFunction,
                (mouseupEvent) => {
                    mouseupEvent.currentTarget.removeEventListener(
                        moveFunction,
                        mousemove
                    );
                    var target = $(this.movingItem);
                    var position = target.parent()[0].getBoundingClientRect();
                    var newPosition = mouseupEvent;
                    if (mouseupEvent.changedTouches) {
                        newPosition = mouseupEvent.changedTouches[0];
                    }
                    var left =
                        (Math.max(
                            0,
                            Math.min(position.width, newPosition.pageX - position.x)
                        ) *
                            100) /
                        position.width;
                    var top =
                        (Math.max(
                            0,
                            Math.min(position.height, newPosition.pageY - position.y)
                        ) *
                            100) /
                        position.height;
                    target.css("left", left + "%");
                    target.css("top", top + "%");
                    item.position_x = left;
                    item.position_y = top;
                    this.env.services.rpc({
                        model: this.props.model,
                        method: "set_item_data",
                        args: [
                            [this.props.res_id],
                            item.id,
                            {
                                position_x: left,
                                position_y: top,
                            },
                        ],
                    });
                    this.movingItem = undefined;
                },
                {once: true}
            );
        });
        _.each(resizeItems, (resizeItem) => {
            resizeItem.addEventListener(startFunction, (mousedownEvent) => {
                mousedownEvent.preventDefault();
                var parentPage = mousedownEvent.target.parentElement.parentElement;
                this.resizingItem = mousedownEvent.target.parentElement;
                var mousemove = this._onResizeItem.bind(this);
                parentPage.addEventListener(moveFunction, mousemove);
                parentPage.addEventListener(
                    endFunction,
                    (mouseupEvent) => {
                        mouseupEvent.stopPropagation();
                        mouseupEvent.preventDefault();
                        mouseupEvent.currentTarget.removeEventListener(
                            moveFunction,
                            mousemove
                        );
                        var target = $(this.resizingItem);
                        var newPosition = mouseupEvent;
                        if (mouseupEvent.changedTouches) {
                            newPosition = mouseupEvent.changedTouches[0];
                        }
                        var targetPosition = target
                            .find(".o_sign_oca_resize")[0]
                            .getBoundingClientRect();
                        var itemPosition = target[0].getBoundingClientRect();
                        var pagePosition = target.parent()[0].getBoundingClientRect();
                        var width =
                            (Math.max(
                                0,
                                newPosition.pageX +
                                    targetPosition.width -
                                    itemPosition.x
                            ) *
                                100) /
                            pagePosition.width;
                        var height =
                            (Math.max(
                                0,
                                newPosition.pageY +
                                    targetPosition.height -
                                    itemPosition.y
                            ) *
                                100) /
                            pagePosition.height;
                        target.css("width", width + "%");
                        target.css("height", height + "%");
                        item.width = width;
                        item.height = height;
                        this.env.services.rpc({
                            model: this.props.model,
                            method: "set_item_data",
                            args: [
                                [this.props.res_id],
                                item.id,
                                {
                                    width: width,
                                    height: height,
                                },
                            ],
                        });
                    },
                    {once: true}
                );
            });
        });
        return signatureItem;
    }
    _onResizeItem(e) {
        e.stopPropagation();
        e.preventDefault();
        var target = $(this.resizingItem);
        var targetPosition = target
            .find(".o_sign_oca_resize")[0]
            .getBoundingClientRect();
        var itemPosition = target[0].getBoundingClientRect();
        var newPosition = e;
        if (e.targetTouches) {
            newPosition = e.targetTouches[0];
        }
        var pagePosition = target.parent()[0].getBoundingClientRect();
        var width =
            (Math.max(0, newPosition.pageX + targetPosition.width - itemPosition.x) *
                100) /
            pagePosition.width;
        var height =
            (Math.max(0, newPosition.pageY + targetPosition.height - itemPosition.y) *
                100) /
            pagePosition.height;
        target.css("width", width + "%");
        target.css("height", height + "%");
    }
    _onDragItem(e) {
        e.stopPropagation();
        e.preventDefault();
        var target = $(this.movingItem);
        var position = target.parent()[0].getBoundingClientRect();
        var newPosition = e;
        if (e.targetTouches) {
            newPosition = e.targetTouches[0];
        }
        var left =
            (Math.max(0, Math.min(position.width, newPosition.pageX - position.x)) *
                100) /
            position.width;
        var top =
            (Math.max(0, Math.min(position.height, newPosition.pageY - position.y)) *
                100) /
            position.height;
        target.css("left", left + "%");
        target.css("top", top + "%");
    }
}

export const SignOcaConfigureAction = AbstractAction.extend({
    hasControlPanel: true,
    init: function (parent, action) {
        this._super.apply(this, arguments);
        this.model =
            (action.params.res_model !== undefined && action.params.res_model) ||
            action.context.params.res_model;
        this.res_id =
            (action.params.res_id !== undefined && action.params.res_id) ||
            action.context.params.id;
    },
    async start() {
        await this._super(...arguments);
        this.component = new ComponentWrapper(this, SignOcaConfigure, {
            model: this.model,
            res_id: this.res_id,
        });
        this.$el.addClass("o_sign_oca_action");
        return this.component.mount(this.$(".o_content")[0]);
    },
    getState: function () {
        var result = this._super(...arguments);
        result = _.extend({}, result, {
            res_model: this.model,
            res_id: this.res_id,
        });
        return result;
    },
});
core.action_registry.add("sign_oca_configure", SignOcaConfigureAction);
SignOcaConfigure.template = "sign_oca.SignOcaConfigure";
