/** @odoo-module **/

import {Component, onMounted, useRef, useState} from "@odoo/owl";

import {Dialog} from "@web/core/dialog/dialog";
import {getStroke} from "@sign_biometric_oca/lib/perfect-freehand.esm";

const average = (a, b) => (a + b) / 2;

function getSvgPathFromStroke(points, closed = true) {
    const len = points.length;

    if (len < 4) {
        return ``;
    }

    let a = points[0];
    let b = points[1];
    const c = points[2];

    let result = `M${a[0].toFixed(2)},${a[1].toFixed(2)} Q${b[0].toFixed(
        2
    )},${b[1].toFixed(2)} ${average(b[0], c[0]).toFixed(2)},${average(
        b[1],
        c[1]
    ).toFixed(2)} T`;

    for (let i = 2, max = len - 1; i < max; i++) {
        a = points[i];
        b = points[i + 1];
        result += `${average(a[0], b[0]).toFixed(2)},${average(a[1], b[1]).toFixed(
            2
        )} `;
    }

    if (closed) {
        result += "Z";
    }

    return result;
}

export class BiometricSignatureDialog extends Component {
    setup() {
        this.title = this.env._t("Adopt Your Signature");
        this.svg = useRef("BiometricSignatureBox");
        this.state = useState({current_key: 0, paths: {}, recording: false});
        onMounted(() => {
            this.svg.el.style.height =
                this.svg.el.clientWidth / this.props.displaySignatureRatio;
            this.svg.el.setAttribute(
                "viewBox",
                "0 0 " +
                    this.svg.el.clientWidth +
                    " " +
                    parseFloat(this.svg.el.style.height)
            );
        });
    }
    addPoint(e, current_key) {
        this.state.paths[current_key] = [
            ...this.state.paths[current_key],
            [e.offsetX, e.offsetY, e.pressure, new Date().getTime()],
        ];
    }
    handlePointerUp(e) {
        this.addPoint(e, this.state.current_key);
        this.state.recording = false;
    }
    handlePointerDown(e) {
        e.target.setPointerCapture(e.pointerId);
        var current_key = this.state.current_key + 1;
        this.state.current_key = current_key;
        this.state.recording = true;
        this.state.paths[current_key] = [];
        this.addPoint(e, current_key);
    }
    handlePointerMove(e) {
        if (!this.state.recording) {
            return;
        }
        this.addPoint(e, this.state.current_key);
    }
    onClickClear() {
        this.state.current_key = 0;
        this.state.paths = [];
    }
    /**
     * Upload the signature image when confirm.
     *
     * @private
     */
    onClickConfirm() {
        var result = {
            paths: JSON.parse(JSON.stringify(this.state.paths)),
            data: this.pathData,
            width: this.svg.el.clientWidth,
            height: this.svg.el.clientHeight,
        };
        this.svg.el.style = {};
        this.svg.el.class = "";
        result.svg = btoa(new XMLSerializer().serializeToString(this.svg.el));
        this.props.uploadSignature(result);
        this.props.close();
    }
    get pathData() {
        var result = [];
        for (const key in this.state.paths) {
            result.push(
                getSvgPathFromStroke(
                    getStroke(this.state.paths[key], {
                        size: 8,
                        thinning: 0.5,
                        smoothing: 0.5,
                        streamline: 0.5,
                    })
                )
            );
        }
        return result;
    }
    get isSignatureEmpty() {
        return this.state.current_key === 0;
    }
}

BiometricSignatureDialog.template = "sign_biometric_oca.BiometricSignatureDialog";
BiometricSignatureDialog.components = {Dialog};
BiometricSignatureDialog.defaultProps = {
    displaySignatureRatio: 3.0,
};
