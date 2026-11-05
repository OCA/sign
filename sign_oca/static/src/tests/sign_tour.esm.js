/* Copyright 2025 Kencove - Mohamed Alkobrosli
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */
odoo.define("sign_oca.sign_tour", function (require) {
    var tour = require("web_tour.tour");

    var steps = [
        {
            trigger: "a:contains('Your Documents to be Signed')",
        },
    ];

    tour.register(
        "test_sign_tour",
        {
            url: "/my",
            test: true,
        },
        steps
    );
    return {
        steps: steps,
    };
});

odoo.define("sign_oca.sign_doc_tour", function (require) {
    var tour = require("web_tour.tour");

    var steps = [
        {
            trigger: "td a",
        },
    ];

    tour.register(
        "test_sign_doc_tour",
        {
            url: "/my/sign_requests",
            test: true,
        },
        steps
    );
    return {
        steps: steps,
    };
});
