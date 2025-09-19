/** @odoo-module QWeb **/
/* global document, window, Event, KeyboardEvent, console */
import {_t} from "@web/core/l10n/translation";

export function offset(el) {
    const box = el.getBoundingClientRect();
    const docElem = document.documentElement;
    return {
        top: box.top + window.scrollY - docElem.clientTop,
        left: box.left + window.scrollY - docElem.clientLeft,
    };
}

function swapWithNext(arr, index) {
    if (index < 0 || index >= arr.length - 1) {
        console.error("Invalid index");
        return arr;
    }
    // Swap element at index with the next one
    const temp = arr[index];
    arr[index] = arr[index + 1];
    arr[index + 1] = temp;
    return arr;
}

function sortItemsForArrow(parent) {
    const signItemsToComplete = parent.checkSignItemsCompletion();
    for (let i = 0; i + 1 < signItemsToComplete.length; i++) {
        const item = signItemsToComplete[i].data;
        const position_y_down = item.position_y + item.height;
        const position_x = item.position_x;
        const page = item.page;

        const next_item = signItemsToComplete[i + 1].data;
        const position_y_next_item = next_item.position_y;
        const position_x_next_item = next_item.position_x;
        const page_next_item = next_item.page;
        if (
            position_y_down >= position_y_next_item &&
            position_x > position_x_next_item &&
            page == page_next_item
        ) {
            swapWithNext(signItemsToComplete, i);
            i = 0;
        }
    }
    return signItemsToComplete;
}

/**
 * Starts the sign item navigator
 * @param { SignablePDFIframe } parent
 * @param { HTMLElement } target
 * @param { Environment } env
 */
export function startSignItemNavigator(parent, target, env) {
    const state = {
        started: false,
        isScrolling: false,
    };
    const navigator = parent.iframe.el.contentDocument.getElementsByClassName(
        "o_sign_sign_item_navigator"
    )[0];
    const navLine = parent.iframe.el.contentDocument.getElementsByClassName(
        "o_sign_sign_item_navline"
    )[0];
    const checkSignItemsCompletion = sortItemsForArrow(parent);
    let signItemsToComplete = checkSignItemsCompletion;

    function _scrollToSignItemPromise(item) {
        return new Promise((resolve) => {
            if (env.isSmall) {
                state.isScrolling = true;
                item.scrollIntoView({
                    behavior: "smooth",
                    block: "center",
                    inline: "center",
                });
                return resolve();
            }

            state.isScrolling = true;
            const viewer = parent.iframe.el.contentDocument.getElementById("viewer");

            // Recalculate container height each time
            const containerHeight = target.offsetHeight;
            const viewerHeight = viewer.offsetHeight;

            let scrollOffset = containerHeight / 4;

            // Get the latest scroll position
            const updatedScrollTop =
                offset(item).top - offset(viewer).top - scrollOffset;

            // Adjust for overscroll cases
            if (updatedScrollTop + containerHeight > viewerHeight) {
                scrollOffset += updatedScrollTop + containerHeight - viewerHeight;
            }
            if (updatedScrollTop < 0) {
                scrollOffset += updatedScrollTop;
            }

            // Ensure navigator updates properly
            scrollOffset +=
                offset(target).top -
                navigator.offsetHeight / 2 +
                item.getBoundingClientRect().height / 2;

            // Dynamic animation duration
            const duration = Math.max(
                Math.min(
                    500,
                    5 *
                        (Math.abs(target.scrollTop - updatedScrollTop) +
                            Math.abs(navigator.getBoundingClientRect().top) -
                            scrollOffset)
                ),
                100
            );

            // Perform scroll
            target.scrollTo({top: updatedScrollTop, behavior: "smooth"});

            // Update navigator animation
            const an = navigator.animate(
                {top: `${scrollOffset}px`},
                {duration, fill: "forwards"}
            );
            const an2 = navLine.animate(
                {top: `${scrollOffset}px`},
                {duration, fill: "forwards"}
            );

            Promise.all([an.finished, an2.finished]).then(() => {
                resolve();
            });
        });
    }

    function setTip(text) {
        navigator.style.fontFamily = "Helvetica";
        navigator.innerText = text;
    }

    function scrollToSignItem({el: item}) {
        setTip(_t("Next"));

        _scrollToSignItemPromise(item).then(() => {
            // Define input to deal with input fields if present
            const input = item.querySelector("input");
            if (input) {
                if (input.type === "text") {
                    input.focus();
                } else if (input.type === "checkbox") {
                    input.focus();
                    // Additional auto check and launch its events for faster filling
                    input.checked = true;
                    input.dispatchEvent(new Event("change", {bubbles: true}));
                    input.dispatchEvent(
                        new KeyboardEvent("keydown", {
                            key: " ", // Space key to simulate manual checking
                            code: "Space",
                            keyCode: 32,
                            bubbles: true,
                        })
                    );
                } else {
                    input.focus();
                }
            }
            // Field can be signature div or anything else
            else if (item.dataset.field) {
                const clickableElement =
                    item.firstElementChild && item.querySelector("div")
                        ? item.firstElementChild
                        : item;
                clickableElement.click();
            } else {
                item.focus();
            }
            item.classList.add("ui-selected");
            state.isScrolling = false;
        });
    }

    function goToNextSignItem() {
        if (!state.started) {
            state.started = true;
            goToNextSignItem();
            return false;
        }
        const selectedElements = target.querySelectorAll(".ui-selected");
        selectedElements.forEach((selectedElement) => {
            selectedElement.classList.remove("ui-selected");
        });
        if (signItemsToComplete.length > 0) {
            scrollToSignItem(signItemsToComplete[0]);
        } else {
            setTip(_t("Click on Validate Button"));
        }
    }

    navigator.addEventListener("click", () => {
        if (checkSignItemsCompletion.length > 0) {
            goToNextSignItem();
            signItemsToComplete = signItemsToComplete.slice(1);
        }
    });

    setTip(_t("Click to start"));
    navigator.focus();

    function toggle(force) {
        navigator.style.display = force ? "" : "none";
        navLine.style.display = force ? "" : "none";
    }

    // If the window is resized in computers only, this function asks user to fill all fields again
    const watch_navigator = () => {
        signItemsToComplete = [...checkSignItemsCompletion];
        setTip(_t("Click to start"));
    };
    const mediaQuery = window.matchMedia("(min-width: 768px)");
    if (mediaQuery.matches) {
        window.addEventListener("resize", watch_navigator);
    }

    return {
        setTip,
        goToNextSignItem,
        toggle,
        state,
    };
}
