import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const NODE_MAX_WIDTH = 420;
const NODE_TYPES = ["HF URL Downloader", "HF Downloader", "Auto Model Downloader"];

function getTitleBarWidth(node, size) {
    const defaultWidth = node.constructor?.size?.[0];
    if (defaultWidth > 0) {
        return Math.min(size[0], defaultWidth);
    }
    return Math.min(size[0], NODE_MAX_WIDTH);
}

function constrainNodeWidth(node) {
    if (!node?.size) return;
    if (node.size[0] > NODE_MAX_WIDTH) {
        node.size[0] = NODE_MAX_WIDTH;
        node.setDirtyCanvas(true);
    }
}

function constrainUrlWidget(node) {
    if (node.type !== "HF URL Downloader") return;
    const widget = node.widgets?.find((w) => w.name === "url");
    if (!widget?.inputEl) return;
    widget.inputEl.style.maxWidth = `${NODE_MAX_WIDTH - 20}px`;
    widget.inputEl.style.wordBreak = "break-all";
}

app.registerExtension({
    name: "HF Downloader",
    async setup() {
        NODE_TYPES.forEach((nodeType) => {
            const origNode = LiteGraph.registered_node_types[nodeType];
            if (!origNode) {
                console.error(`Original node not found: ${nodeType}`);
                return;
            }

            const origOnDrawTitleBar = origNode.prototype.onDrawTitleBar;

            origNode.prototype.onDrawTitleBar = function (ctx, title_height, size, collapsed) {
                if (origOnDrawTitleBar) {
                    origOnDrawTitleBar.call(this, ctx, title_height, size, collapsed);
                }

                if (this.progress > 0) {
                    const ratio = Math.min(1, Math.max(0, this.progress));
                    const barWidth = getTitleBarWidth(this, size);
                    const width = barWidth * ratio;

                    ctx.save();
                    ctx.beginPath();
                    ctx.rect(0, 0, barWidth, title_height);
                    ctx.clip();

                    ctx.fillStyle = "rgba(32, 128, 255, 0.35)";
                    ctx.beginPath();
                    if (ctx.roundRect) {
                        ctx.roundRect(0, 0, width, title_height, [4, 4, 0, 0]);
                    } else {
                        ctx.rect(0, 0, width, title_height);
                    }
                    ctx.fill();
                    ctx.restore();
                }
            };

            origNode.prototype.setProgress = function (ratio) {
                this.progress = Math.min(1, Math.max(0, ratio));
                this.setDirtyCanvas(true);
            };
        });

        api.addEventListener("progress", ({ detail }) => {
            if (!detail?.node) return;

            const node = app.graph.getNodeById(detail.node);
            if (!node || !NODE_TYPES.includes(node.type)) return;

            const ratio = detail.max ? detail.value / detail.max : 0;
            node.setProgress(ratio);

            if (ratio >= 1) {
                setTimeout(() => {
                    node.progress = undefined;
                    node.setDirtyCanvas(true);
                }, 600);
            }
        });

    },

    nodeCreated(node) {
        if (!NODE_TYPES.includes(node.type)) return;
        constrainNodeWidth(node);
        constrainUrlWidget(node);

        const urlWidget = node.widgets?.find((w) => w.name === "url");
        if (urlWidget) {
            const origCallback = urlWidget.callback;
            urlWidget.callback = function (...args) {
                if (origCallback) origCallback.apply(this, args);
                constrainNodeWidth(node);
            };
        }
    },
});
