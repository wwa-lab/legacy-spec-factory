import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const pptxgen = require("/Users/liujie/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/pptxgenjs@4.0.1/node_modules/pptxgenjs/dist/pptxgen.cjs.js");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Codex";
pptx.company = "Legacy Spec Factory";
pptx.subject = "AI-Powered IBM i Delivery Accelerator";
pptx.title = "AI-Powered IBM i Delivery Accelerator - One Page Impact";
pptx.lang = "en-US";
pptx.theme = {
  headFontFace: "Arial",
  bodyFontFace: "Arial",
  lang: "en-US",
};
pptx.defineLayout({ name: "CUSTOM_WIDE", width: 13.333, height: 7.5 });
pptx.layout = "CUSTOM_WIDE";
pptx.margin = 0;

const slide = pptx.addSlide();
slide.background = { color: "061521" };

const C = {
  bg: "061521",
  top: "0A2235",
  panel: "0B2233",
  panel2: "081C2C",
  border: "21465C",
  muted: "A8B8C9",
  soft: "7F93A7",
  white: "FFFFFF",
  teal: "18BBD0",
  green: "5ED68C",
  red: "FF6363",
  amber: "F5B84D",
  violet: "9E84FF",
};

function rect(x, y, w, h, fill, line = fill, transparency = 0) {
  slide.addShape(pptx.ShapeType.rect, {
    x, y, w, h,
    fill: { color: fill, transparency },
    line: { color: line === "none" ? fill : line, transparency: line === "none" ? 100 : 0, width: 1 },
  });
}

function line(x1, y1, x2, y2, color, width = 1, transparency = 0) {
  slide.addShape(pptx.ShapeType.line, {
    x: x1, y: y1, w: x2 - x1, h: y2 - y1,
    line: { color, width, transparency, beginArrowType: "none", endArrowType: "none" },
  });
}

function arrow(x1, y1, x2, y2, color, width = 1.5) {
  slide.addShape(pptx.ShapeType.line, {
    x: x1, y: y1, w: x2 - x1, h: y2 - y1,
    line: { color, width, beginArrowType: "none", endArrowType: "triangle" },
  });
}

function text(value, x, y, w, h, opts = {}) {
  slide.addText(value, {
    x, y, w, h,
    margin: opts.margin ?? 0,
    breakLine: false,
    fit: "shrink",
    fontFace: opts.fontFace ?? "Arial",
    fontSize: opts.fontSize ?? 14,
    bold: opts.bold ?? false,
    color: opts.color ?? C.white,
    align: opts.align ?? "left",
    valign: opts.valign ?? "top",
    italic: opts.italic ?? false,
    paraSpaceAfterPt: 0,
    breakLine: false,
  });
}

function panel(x, y, w, h, border = C.border) {
  rect(x, y, w, h, C.panel, border);
}

function pill(x, y, label, color) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w: 1.05, h: 0.26,
    rectRadius: 0.04,
    fill: { color, transparency: 82 },
    line: { color, transparency: 0, width: 0.8 },
  });
  text(label, x, y + 0.045, 1.05, 0.16, { fontSize: 7.5, bold: true, color, align: "center" });
}

// Source-deck chrome.
rect(0, 0, 13.333, 0.75, C.top, "none");
rect(0.67, 0.46, 0.08, 0.2, C.green, "none");
text("DELIVERY VALUE", 0.86, 0.47, 2.5, 0.16, { fontSize: 7.8, bold: true, color: C.muted });
line(0.67, 1.38, 12.65, 1.38, C.border, 0.8);
line(0.67, 6.94, 12.65, 6.94, C.border, 0.8);
line(10.55, 0, 12.5, 7.5, C.border, 0.6, 55);
line(11.28, 0, 12.9, 7.5, C.border, 0.6, 70);

text("AI-powered IBM i delivery accelerator: faster delivery with controlled evidence", 0.67, 0.94, 11.25, 0.36, {
  fontSize: 20.5,
  bold: true,
});
text("Standardized AS400 skill chains turn scarce expert judgment into repeatable delivery workflows.", 0.69, 1.56, 8.8, 0.24, {
  fontSize: 10.5,
  color: C.muted,
});
text("Executive brief", 10.75, 1.55, 1.85, 0.22, {
  fontSize: 8.5,
  color: C.soft,
  align: "right",
});

// Three outcome panels.
panel(0.84, 2.08, 3.75, 3.02);
text("Developer onboarding", 1.16, 2.42, 3.15, 0.26, { fontSize: 15.5, bold: true });
text("1 month", 1.16, 3.05, 1.25, 0.42, { fontSize: 23, bold: true, color: C.red });
arrow(2.47, 3.28, 3.15, 3.28, C.teal, 1.4);
text("1 week", 3.18, 3.05, 1.08, 0.42, { fontSize: 23, bold: true, color: C.green });
text("AS400 developers learn the delivery path through reusable requirements, specs, review gates and test assets.", 1.18, 3.78, 3.05, 0.62, {
  fontSize: 10.1,
  color: C.white,
  align: "center",
});
text("Outcome: onboarding cycle reduced from 1 month to 1 week.", 1.18, 4.55, 3.1, 0.22, { fontSize: 8.3, color: C.muted, align: "center" });

panel(4.94, 2.08, 2.73, 3.02, C.amber);
text("+10%", 5.43, 2.87, 1.75, 0.55, { fontSize: 34, bold: true, color: C.amber, align: "center" });
text("Phase-1 delivery speed", 5.28, 3.58, 2.04, 0.42, { fontSize: 13.8, bold: true, align: "center" });
text("Faster first-phase execution by reducing manual preparation and repeated SME clarification.", 5.18, 4.22, 2.25, 0.52, {
  fontSize: 9.2,
  align: "center",
});

panel(8.04, 2.08, 3.72, 3.02);
text("Control is preserved", 8.37, 2.42, 2.95, 0.26, { fontSize: 15.5, bold: true });
text("Reusable workflow, visible gates", 8.37, 2.92, 2.95, 0.22, { fontSize: 12.5, bold: true, color: C.teal });
slide.addShape(pptx.ShapeType.ellipse, {
  x: 8.85,
  y: 3.55,
  w: 0.58,
  h: 0.58,
  fill: { color: C.teal, transparency: 86 },
  line: { color: C.teal, width: 1 },
});
text("Prepare", 8.85, 3.76, 0.58, 0.1, { fontSize: 6.8, bold: true, color: C.teal, align: "center" });
slide.addShape(pptx.ShapeType.ellipse, {
  x: 10.35,
  y: 3.55,
  w: 0.58,
  h: 0.58,
  fill: { color: C.amber, transparency: 86 },
  line: { color: C.amber, width: 1 },
});
text("Generate", 10.35, 3.76, 0.58, 0.1, { fontSize: 6.4, bold: true, color: C.amber, align: "center" });
slide.addShape(pptx.ShapeType.ellipse, {
  x: 10.35,
  y: 4.25,
  w: 0.58,
  h: 0.58,
  fill: { color: C.violet, transparency: 86 },
  line: { color: C.violet, width: 1 },
});
text("Review", 10.35, 4.46, 0.58, 0.1, { fontSize: 6.8, bold: true, color: C.violet, align: "center" });
slide.addShape(pptx.ShapeType.ellipse, {
  x: 8.85,
  y: 4.25,
  w: 0.58,
  h: 0.58,
  fill: { color: C.green, transparency: 86 },
  line: { color: C.green, width: 1 },
});
text("Evidence", 8.85, 4.46, 0.58, 0.1, { fontSize: 6.5, bold: true, color: C.green, align: "center" });
arrow(9.43, 3.84, 10.30, 3.84, C.soft, 1);
arrow(10.64, 4.13, 10.64, 4.20, C.soft, 1);
arrow(10.35, 4.54, 9.48, 4.54, C.soft, 1);
arrow(9.14, 4.25, 9.14, 4.18, C.soft, 1);
text("Human approval remains at the review gates; evidence stays reusable.", 8.52, 4.96, 2.75, 0.18, { fontSize: 7.3, color: C.muted, align: "center" });

// Bottom proof rail.
rect(0.84, 5.56, 10.92, 0.68, C.panel2, C.border);
const steps = [
  ["Intake & normalize", C.teal],
  ["Understand & assess", C.green],
  ["Specify & design", C.amber],
  ["Generate & review", C.red],
  ["Test & orchestrate", C.violet],
];
let sx = 1.04;
for (let i = 0; i < steps.length; i += 1) {
  const [label, color] = steps[i];
  slide.addShape(pptx.ShapeType.ellipse, {
    x: sx,
    y: 5.78,
    w: 0.18,
    h: 0.18,
    fill: { color },
    line: { color },
  });
  text(label, sx + 0.25, 5.71, 1.55, 0.28, { fontSize: 7.6, bold: true, color: C.white });
  if (i < steps.length - 1) {
    arrow(sx + 1.86, 5.87, sx + 2.18, 5.87, C.soft, 0.8);
  }
  sx += 2.16;
}
text("Skill-family flow: requirement-normalizer / program + impact analyzers / specs / generator-reviewer / UT handoff, with BR-ID continuity.", 1.12, 6.05, 9.8, 0.16, {
  fontSize: 7.3,
  color: C.muted,
});

text("AI-Powered IBM i Delivery Accelerator | Executive Brief", 0.67, 7.08, 5.8, 0.15, { fontSize: 6.8, color: C.soft });
text("01", 12.15, 7.06, 0.5, 0.18, { fontSize: 7.4, bold: true, color: C.soft, align: "right" });

await pptx.writeFile({ fileName: "/Users/liujie/Downloads/ai-powered-ibm-i-delivery-accelerator-one-page.pptx" });
