/* @ds-bundle: {"format":3,"namespace":"WorkoutWizDesignSystem_1665e3","components":[{"name":"Avatar","sourcePath":"components/core/Avatar.jsx"},{"name":"Badge","sourcePath":"components/core/Badge.jsx"},{"name":"Button","sourcePath":"components/core/Button.jsx"},{"name":"Card","sourcePath":"components/core/Card.jsx"},{"name":"CardHeader","sourcePath":"components/core/Card.jsx"},{"name":"CardTitle","sourcePath":"components/core/Card.jsx"},{"name":"CardDescription","sourcePath":"components/core/Card.jsx"},{"name":"CardContent","sourcePath":"components/core/Card.jsx"},{"name":"CardFooter","sourcePath":"components/core/Card.jsx"},{"name":"IconButton","sourcePath":"components/core/IconButton.jsx"},{"name":"Tag","sourcePath":"components/core/Tag.jsx"},{"name":"ChatBubble","sourcePath":"components/fitness/ChatBubble.jsx"},{"name":"Progress","sourcePath":"components/fitness/Progress.jsx"},{"name":"ProgressRing","sourcePath":"components/fitness/ProgressRing.jsx"},{"name":"SetRow","sourcePath":"components/fitness/SetRow.jsx"},{"name":"StatTile","sourcePath":"components/fitness/StatTile.jsx"},{"name":"Checkbox","sourcePath":"components/forms/Checkbox.jsx"},{"name":"Radio","sourcePath":"components/forms/Checkbox.jsx"},{"name":"Field","sourcePath":"components/forms/Field.jsx"},{"name":"Label","sourcePath":"components/forms/Field.jsx"},{"name":"Input","sourcePath":"components/forms/Input.jsx"},{"name":"Select","sourcePath":"components/forms/Select.jsx"},{"name":"Switch","sourcePath":"components/forms/Switch.jsx"},{"name":"Textarea","sourcePath":"components/forms/Textarea.jsx"},{"name":"Tabs","sourcePath":"components/navigation/Tabs.jsx"}],"sourceHashes":{"components/core/Avatar.jsx":"11a483c67d91","components/core/Badge.jsx":"34b5f12fb82b","components/core/Button.jsx":"d3dbf8d0bfe6","components/core/Card.jsx":"ba5c386532a0","components/core/IconButton.jsx":"9ffd8eacf80c","components/core/Tag.jsx":"f6e73f476dd4","components/fitness/ChatBubble.jsx":"e986b19f66d6","components/fitness/Progress.jsx":"d887da519256","components/fitness/ProgressRing.jsx":"35c20147926f","components/fitness/SetRow.jsx":"6a20702fba4e","components/fitness/StatTile.jsx":"0215a3c8dd0b","components/forms/Checkbox.jsx":"5db49db82768","components/forms/Field.jsx":"d7a6670663a8","components/forms/Input.jsx":"cf651bd60223","components/forms/Select.jsx":"c51b4184c150","components/forms/Switch.jsx":"5547d39bf31e","components/forms/Textarea.jsx":"abee7d9d651a","components/navigation/Tabs.jsx":"5ecf091cd999","ui_kits/app/App.jsx":"f3d974d01441","ui_kits/app/BuilderScreen.jsx":"5df59dea3df5","ui_kits/app/CoachScreen.jsx":"7f6122184b1e","ui_kits/app/ExercisesScreen.jsx":"2d6bb3affead","ui_kits/app/Sidebar.jsx":"47eef861170f","ui_kits/app/TodayScreen.jsx":"c72d30078594","ui_kits/app/data.jsx":"31cd2273a732"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.WorkoutWizDesignSystem_1665e3 = window.WorkoutWizDesignSystem_1665e3 || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/core/Avatar.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Avatar — circular user/coach image or initials.
 * Falls back to initials over the ember gradient when no `src`.
 */
function Avatar({
  src = null,
  name = "",
  size = "md",
  ring = false,
  className = "",
  ...props
}) {
  const initials = name.split(" ").map(w => w[0]).filter(Boolean).slice(0, 2).join("").toUpperCase();
  const cls = ["ww-avatar", size !== "md" ? `ww-avatar--${size}` : "", ring ? "ww-avatar--ring" : "", className].filter(Boolean).join(" ");
  return /*#__PURE__*/React.createElement("span", _extends({
    className: cls
  }, props), src ? /*#__PURE__*/React.createElement("img", {
    src: src,
    alt: name
  }) : initials || "?");
}
Object.assign(__ds_scope, { Avatar });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Avatar.jsx", error: String((e && e.message) || e) }); }

// components/core/Badge.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Badge — compact status / category pill.
 * `dot` prepends a small status dot in the current color.
 */
function Badge({
  variant = "soft",
  dot = false,
  className = "",
  children,
  ...props
}) {
  const cls = ["ww-badge", `ww-badge--${variant}`, dot ? "ww-badge--dot" : "", className].filter(Boolean).join(" ");
  return /*#__PURE__*/React.createElement("span", _extends({
    className: cls
  }, props), children);
}
Object.assign(__ds_scope, { Badge });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Badge.jsx", error: String((e && e.message) || e) }); }

// components/core/Button.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Button — primary action primitive for Workout Wiz.
 * Variants map to the brand: `gradient` is the signature ember CTA,
 * `primary` the flat ember, plus accent/secondary/outline/ghost/destructive/link.
 */
function Button({
  variant = "primary",
  size = "md",
  block = false,
  iconStart = null,
  iconEnd = null,
  className = "",
  children,
  ...props
}) {
  const cls = ["ww-btn", `ww-btn--${variant}`, size !== "md" ? `ww-btn--${size}` : "", block ? "ww-btn--block" : "", className].filter(Boolean).join(" ");
  return /*#__PURE__*/React.createElement("button", _extends({
    className: cls
  }, props), iconStart, children, iconEnd);
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Button.jsx", error: String((e && e.message) || e) }); }

// components/core/Card.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Card — primary content container. Soft rounded corners, warm
 * hairline ring + shadow. Use the sub-components for structured layout.
 */
function Card({
  interactive = false,
  flush = false,
  className = "",
  children,
  ...props
}) {
  const cls = ["ww-card", interactive ? "ww-card--interactive" : "", flush ? "ww-card--flush" : "", className].filter(Boolean).join(" ");
  return /*#__PURE__*/React.createElement("div", _extends({
    className: cls
  }, props), children);
}
function CardHeader({
  className = "",
  children,
  ...props
}) {
  return /*#__PURE__*/React.createElement("div", _extends({
    className: ["ww-card__header", className].filter(Boolean).join(" ")
  }, props), children);
}
function CardTitle({
  className = "",
  children,
  ...props
}) {
  return /*#__PURE__*/React.createElement("div", _extends({
    className: ["ww-card__title", className].filter(Boolean).join(" ")
  }, props), children);
}
function CardDescription({
  className = "",
  children,
  ...props
}) {
  return /*#__PURE__*/React.createElement("div", _extends({
    className: ["ww-card__desc", className].filter(Boolean).join(" ")
  }, props), children);
}
function CardContent({
  className = "",
  children,
  ...props
}) {
  return /*#__PURE__*/React.createElement("div", _extends({
    className: ["ww-card__body", className].filter(Boolean).join(" ")
  }, props), children);
}
function CardFooter({
  className = "",
  children,
  ...props
}) {
  return /*#__PURE__*/React.createElement("div", _extends({
    className: ["ww-card__footer", className].filter(Boolean).join(" ")
  }, props), children);
}
Object.assign(__ds_scope, { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Card.jsx", error: String((e && e.message) || e) }); }

// components/core/IconButton.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * IconButton — square, icon-only button. Same variants as Button.
 * Always pass an `aria-label` for accessibility.
 */
function IconButton({
  variant = "ghost",
  size = "md",
  className = "",
  children,
  ...props
}) {
  const cls = ["ww-btn", "ww-iconbtn", `ww-btn--${variant}`, size !== "md" ? `ww-btn--${size}` : "", className].filter(Boolean).join(" ");
  return /*#__PURE__*/React.createElement("button", _extends({
    className: cls
  }, props), children);
}
Object.assign(__ds_scope, { IconButton });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/IconButton.jsx", error: String((e && e.message) || e) }); }

// components/core/Tag.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Tag — squared chip with an optional remove affordance.
 * Used for filter chips (muscle group, equipment) in the exercise browser.
 */
function Tag({
  onRemove,
  className = "",
  children,
  ...props
}) {
  return /*#__PURE__*/React.createElement("span", _extends({
    className: ["ww-tag", className].filter(Boolean).join(" ")
  }, props), children, onRemove && /*#__PURE__*/React.createElement("span", {
    className: "ww-tag__x",
    role: "button",
    "aria-label": "Remove",
    onClick: onRemove
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "12",
    height: "12",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2.5",
    strokeLinecap: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M18 6 6 18M6 6l12 12"
  }))));
}
Object.assign(__ds_scope, { Tag });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Tag.jsx", error: String((e && e.message) || e) }); }

// components/fitness/ChatBubble.jsx
try { (() => {
/**
 * ChatBubble — the AI coach ↔ user message bubble. Signature
 * component for the multi-agent coaching surface. Coach bubbles can
 * show the routed agent (COACH / WORKOUT_GENERATE / WORKOUT_LOG).
 */
function ChatBubble({
  from = "coach",
  route = null,
  avatar = null,
  meta = null,
  className = "",
  children
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: ["ww-chat", `ww-chat--${from}`, className].filter(Boolean).join(" ")
  }, avatar, /*#__PURE__*/React.createElement("div", {
    className: "ww-chat__body"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ww-chat__bubble"
  }, children), /*#__PURE__*/React.createElement("div", {
    className: "ww-chat__meta"
  }, route && /*#__PURE__*/React.createElement("span", {
    className: "ww-chat__route"
  }, route), meta)));
}
Object.assign(__ds_scope, { ChatBubble });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/fitness/ChatBubble.jsx", error: String((e && e.message) || e) }); }

// components/fitness/Progress.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Progress — horizontal ember-filled progress bar (0–100).
 */
function Progress({
  value = 0,
  className = "",
  ...props
}) {
  const pct = Math.max(0, Math.min(100, value));
  return /*#__PURE__*/React.createElement("div", _extends({
    className: ["ww-progress", className].filter(Boolean).join(" "),
    role: "progressbar",
    "aria-valuenow": pct,
    "aria-valuemin": 0,
    "aria-valuemax": 100
  }, props), /*#__PURE__*/React.createElement("div", {
    className: "ww-progress__fill",
    style: {
      width: `${pct}%`
    }
  }));
}
Object.assign(__ds_scope, { Progress });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/fitness/Progress.jsx", error: String((e && e.message) || e) }); }

// components/fitness/ProgressRing.jsx
try { (() => {
/**
 * ProgressRing — circular progress dial. Used for the rest timer and
 * session completion. Renders the ember gradient stroke over a track.
 */
function ProgressRing({
  value = 0,
  size = 88,
  stroke = 8,
  label = null,
  sublabel = null,
  className = ""
}) {
  const pct = Math.max(0, Math.min(100, value));
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - pct / 100 * c;
  const gid = "ring-grad-" + Math.round(size) + "-" + Math.round(stroke);
  return /*#__PURE__*/React.createElement("div", {
    className: className,
    style: {
      position: "relative",
      width: size,
      height: size,
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement("svg", {
    width: size,
    height: size,
    style: {
      transform: "rotate(-90deg)"
    }
  }, /*#__PURE__*/React.createElement("defs", null, /*#__PURE__*/React.createElement("linearGradient", {
    id: gid,
    x1: "0",
    y1: "0",
    x2: "1",
    y2: "1"
  }, /*#__PURE__*/React.createElement("stop", {
    offset: "0",
    stopColor: "var(--amber-500)"
  }), /*#__PURE__*/React.createElement("stop", {
    offset: "1",
    stopColor: "var(--ember-600)"
  }))), /*#__PURE__*/React.createElement("circle", {
    cx: size / 2,
    cy: size / 2,
    r: r,
    fill: "none",
    stroke: "var(--stone-200)",
    strokeWidth: stroke
  }), /*#__PURE__*/React.createElement("circle", {
    cx: size / 2,
    cy: size / 2,
    r: r,
    fill: "none",
    stroke: `url(#${gid})`,
    strokeWidth: stroke,
    strokeLinecap: "round",
    strokeDasharray: c,
    strokeDashoffset: offset,
    style: {
      transition: "stroke-dashoffset 280ms cubic-bezier(0.22,1,0.36,1)"
    }
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      position: "absolute",
      inset: 0,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      gap: 0
    }
  }, label != null && /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)",
      fontWeight: 700,
      fontSize: size * 0.26,
      letterSpacing: "-0.02em",
      lineHeight: 1
    }
  }, label), sublabel != null && /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-2xs)",
      color: "var(--muted-foreground)",
      textTransform: "uppercase",
      letterSpacing: "var(--tracking-caps)"
    }
  }, sublabel)));
}
Object.assign(__ds_scope, { ProgressRing });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/fitness/ProgressRing.jsx", error: String((e && e.message) || e) }); }

// components/fitness/SetRow.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * SetRow — one row in the workout builder / logger: exercise name,
 * its metrics (reps × weight or duration), and a done state.
 */
function SetRow({
  index = null,
  name,
  sub = null,
  metrics = [],
  done = false,
  action = null,
  className = "",
  ...props
}) {
  return /*#__PURE__*/React.createElement("div", _extends({
    className: ["ww-setrow", className].filter(Boolean).join(" "),
    "data-done": done
  }, props), index != null && /*#__PURE__*/React.createElement("span", {
    className: "ww-setrow__idx"
  }, index), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    className: "ww-setrow__name"
  }, name), sub && /*#__PURE__*/React.createElement("div", {
    className: "ww-setrow__sub"
  }, sub)), metrics.map((m, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    className: "ww-setrow__metric"
  }, m.value, /*#__PURE__*/React.createElement("small", null, m.unit))), action);
}
Object.assign(__ds_scope, { SetRow });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/fitness/SetRow.jsx", error: String((e && e.message) || e) }); }

// components/fitness/StatTile.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * StatTile — a single headline metric (volume, streak, PRs).
 * Value renders in the mono numeric face; optional unit + delta.
 */
function StatTile({
  label,
  value,
  unit = null,
  delta = null,
  icon = null,
  className = "",
  ...props
}) {
  return /*#__PURE__*/React.createElement("div", _extends({
    className: ["ww-stat", className].filter(Boolean).join(" ")
  }, props), /*#__PURE__*/React.createElement("span", {
    className: "ww-stat__label"
  }, icon, label), /*#__PURE__*/React.createElement("span", {
    className: "ww-stat__value"
  }, value, unit && /*#__PURE__*/React.createElement("small", null, " ", unit)), delta && /*#__PURE__*/React.createElement("span", {
    className: `ww-stat__delta ww-stat__delta--${delta.dir}`
  }, delta.dir === "up" ? "▲" : "▼", " ", delta.label));
}
Object.assign(__ds_scope, { StatTile });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/fitness/StatTile.jsx", error: String((e && e.message) || e) }); }

// components/forms/Checkbox.jsx
try { (() => {
/**
 * Checkbox — controlled checkbox with label. Toggle via `checked` + `onChange`.
 */
function Checkbox({
  checked = false,
  onChange,
  disabled = false,
  className = "",
  children
}) {
  return /*#__PURE__*/React.createElement("label", {
    className: ["ww-check", className].filter(Boolean).join(" "),
    "data-checked": checked,
    "data-disabled": disabled
  }, /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    checked: checked,
    disabled: disabled,
    onChange: e => onChange && onChange(e.target.checked, e),
    style: {
      position: "absolute",
      opacity: 0,
      width: 0,
      height: 0
    }
  }), /*#__PURE__*/React.createElement("span", {
    className: "ww-check__box"
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "3.5",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M20 6 9 17l-5-5"
  }))), children && /*#__PURE__*/React.createElement("span", null, children));
}

/**
 * Radio — controlled radio with label.
 */
function Radio({
  checked = false,
  onChange,
  disabled = false,
  name,
  value,
  className = "",
  children
}) {
  return /*#__PURE__*/React.createElement("label", {
    className: ["ww-check", "ww-check--radio", className].filter(Boolean).join(" "),
    "data-checked": checked,
    "data-disabled": disabled
  }, /*#__PURE__*/React.createElement("input", {
    type: "radio",
    name: name,
    value: value,
    checked: checked,
    disabled: disabled,
    onChange: e => onChange && onChange(value, e),
    style: {
      position: "absolute",
      opacity: 0,
      width: 0,
      height: 0
    }
  }), /*#__PURE__*/React.createElement("span", {
    className: "ww-check__box"
  }), children && /*#__PURE__*/React.createElement("span", null, children));
}
Object.assign(__ds_scope, { Checkbox, Radio });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Checkbox.jsx", error: String((e && e.message) || e) }); }

// components/forms/Field.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Field — label + control wrapper with optional hint / error text.
 */
function Field({
  label,
  htmlFor,
  required = false,
  hint = null,
  error = null,
  className = "",
  children
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: ["ww-field", className].filter(Boolean).join(" ")
  }, label && /*#__PURE__*/React.createElement("label", {
    className: "ww-label",
    htmlFor: htmlFor
  }, label, required && /*#__PURE__*/React.createElement("span", {
    className: "ww-label__req"
  }, "*")), children, error ? /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-xs)",
      color: "var(--destructive)"
    }
  }, error) : hint ? /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-xs)",
      color: "var(--muted-foreground)"
    }
  }, hint) : null);
}

/**
 * Label — standalone form label.
 */
function Label({
  required = false,
  className = "",
  children,
  ...props
}) {
  return /*#__PURE__*/React.createElement("label", _extends({
    className: ["ww-label", className].filter(Boolean).join(" ")
  }, props), children, required && /*#__PURE__*/React.createElement("span", {
    className: "ww-label__req"
  }, "*"));
}
Object.assign(__ds_scope, { Field, Label });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Field.jsx", error: String((e && e.message) || e) }); }

// components/forms/Input.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Input — single-line text field. Optionally renders a leading icon.
 */
function Input({
  icon = null,
  invalid = false,
  className = "",
  ...props
}) {
  const input = /*#__PURE__*/React.createElement("input", _extends({
    className: ["ww-input", icon ? "ww-input--with-icon" : "", className].filter(Boolean).join(" "),
    "aria-invalid": invalid || undefined
  }, props));
  if (!icon) return input;
  return /*#__PURE__*/React.createElement("span", {
    className: "ww-input-wrap"
  }, /*#__PURE__*/React.createElement("span", {
    className: "ww-input-wrap__icon"
  }, icon), input);
}
Object.assign(__ds_scope, { Input });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Input.jsx", error: String((e && e.message) || e) }); }

// components/forms/Select.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Select — styled native <select>. Pass <option> children or an
 * `options` array of { value, label }.
 */
function Select({
  options = null,
  invalid = false,
  className = "",
  children,
  ...props
}) {
  return /*#__PURE__*/React.createElement("select", _extends({
    className: ["ww-select", className].filter(Boolean).join(" "),
    "aria-invalid": invalid || undefined
  }, props), options ? options.map(o => /*#__PURE__*/React.createElement("option", {
    key: o.value,
    value: o.value
  }, o.label)) : children);
}
Object.assign(__ds_scope, { Select });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Select.jsx", error: String((e && e.message) || e) }); }

// components/forms/Switch.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Switch — controlled on/off toggle.
 */
function Switch({
  checked = false,
  onChange,
  disabled = false,
  className = "",
  ...props
}) {
  return /*#__PURE__*/React.createElement("button", _extends({
    type: "button",
    role: "switch",
    "aria-checked": checked,
    disabled: disabled,
    "data-checked": checked,
    className: ["ww-switch", className].filter(Boolean).join(" "),
    onClick: () => onChange && onChange(!checked)
  }, props), /*#__PURE__*/React.createElement("span", {
    className: "ww-switch__thumb"
  }));
}
Object.assign(__ds_scope, { Switch });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Switch.jsx", error: String((e && e.message) || e) }); }

// components/forms/Textarea.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Textarea — multi-line text field.
 */
function Textarea({
  invalid = false,
  className = "",
  ...props
}) {
  return /*#__PURE__*/React.createElement("textarea", _extends({
    className: ["ww-textarea", className].filter(Boolean).join(" "),
    "aria-invalid": invalid || undefined
  }, props));
}
Object.assign(__ds_scope, { Textarea });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Textarea.jsx", error: String((e && e.message) || e) }); }

// components/navigation/Tabs.jsx
try { (() => {
/**
 * Tabs — segmented control (default) or underline nav.
 * Controlled via `value` + `onChange`. Items: { value, label, icon? }.
 */
function Tabs({
  items = [],
  value,
  onChange,
  variant = "segmented",
  className = ""
}) {
  return /*#__PURE__*/React.createElement("div", {
    role: "tablist",
    className: ["ww-tabs", variant === "underline" ? "ww-tabs--underline" : "", className].filter(Boolean).join(" ")
  }, items.map(it => /*#__PURE__*/React.createElement("button", {
    key: it.value,
    role: "tab",
    type: "button",
    className: "ww-tab",
    "data-active": value === it.value,
    "aria-selected": value === it.value,
    onClick: () => onChange && onChange(it.value)
  }, it.icon, it.label)));
}
Object.assign(__ds_scope, { Tabs });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/navigation/Tabs.jsx", error: String((e && e.message) || e) }); }

// ui_kits/app/App.jsx
try { (() => {
function LoginScreen({
  onLogin
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "login"
  }, /*#__PURE__*/React.createElement("div", {
    className: "login__card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "login__brand"
  }, /*#__PURE__*/React.createElement("img", {
    src: "../../assets/logo-mascot.png",
    alt: ""
  }), /*#__PURE__*/React.createElement("b", null, "Workout", /*#__PURE__*/React.createElement("span", null, " Wiz"))), /*#__PURE__*/React.createElement("h2", null, "Welcome back"), /*#__PURE__*/React.createElement("p", {
    className: "sub"
  }, "Your AI strength coach is ready."), /*#__PURE__*/React.createElement("form", {
    onSubmit: e => {
      e.preventDefault();
      onLogin();
    }
  }, /*#__PURE__*/React.createElement(Field, {
    label: "Email",
    htmlFor: "le"
  }, /*#__PURE__*/React.createElement(Input, {
    id: "le",
    type: "email",
    defaultValue: "jhona@gym.com"
  })), /*#__PURE__*/React.createElement(Field, {
    label: "Password",
    htmlFor: "lp"
  }, /*#__PURE__*/React.createElement(Input, {
    id: "lp",
    type: "password",
    defaultValue: "password"
  })), /*#__PURE__*/React.createElement(Button, {
    type: "submit",
    variant: "gradient",
    size: "lg",
    block: true
  }, "Sign in")), /*#__PURE__*/React.createElement("p", {
    className: "sub",
    style: {
      marginTop: 16,
      marginBottom: 0
    }
  }, "New here? ", /*#__PURE__*/React.createElement("a", {
    href: "#",
    style: {
      color: "var(--ember-600)",
      fontWeight: 600
    }
  }, "Create an account"))));
}
const TITLES = {
  coach: {
    h: "Coach",
    p: "Plan, log, and learn — your AI strength coach."
  },
  today: {
    h: "Today",
    p: "Wednesday, June 6 · Push day"
  },
  exercises: {
    h: "Exercises",
    p: "Browse the movement library."
  },
  builder: {
    h: "Build workout",
    p: "Log a session set by set."
  }
};
function App() {
  const [authed, setAuthed] = React.useState(false);
  const [route, setRoute] = React.useState("coach");
  const [hasSession, setHasSession] = React.useState(true);
  if (!authed) return /*#__PURE__*/React.createElement(LoginScreen, {
    onLogin: () => setAuthed(true)
  });
  const t = TITLES[route];
  return /*#__PURE__*/React.createElement("div", {
    className: "app-shell"
  }, /*#__PURE__*/React.createElement(Sidebar, {
    route: route,
    setRoute: setRoute,
    onLogout: () => setAuthed(false)
  }), /*#__PURE__*/React.createElement("div", {
    className: "main ww-scroll"
  }, route !== "coach" && /*#__PURE__*/React.createElement("div", {
    className: "topbar"
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h1", null, t.h), /*#__PURE__*/React.createElement("p", null, t.p)), route === "today" && /*#__PURE__*/React.createElement(Button, {
    variant: "gradient",
    iconStart: /*#__PURE__*/React.createElement(Icon, {
      name: "sparkles",
      size: 15,
      color: "#fff"
    }),
    onClick: () => setRoute("coach")
  }, "Ask coach")), route === "coach" && /*#__PURE__*/React.createElement(CoachScreen, {
    onAddSession: () => {
      setHasSession(true);
    }
  }), route === "today" && /*#__PURE__*/React.createElement(TodayScreen, {
    hasSession: hasSession
  }), route === "exercises" && /*#__PURE__*/React.createElement(ExercisesScreen, null), route === "builder" && /*#__PURE__*/React.createElement(BuilderScreen, null)));
}
window.App = App;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/app/App.jsx", error: String((e && e.message) || e) }); }

// ui_kits/app/BuilderScreen.jsx
try { (() => {
function BuilderScreen() {
  const [sequences, setSequences] = React.useState([{
    phase: "main",
    sets: [{
      exId: "1",
      type: "STRENGTH",
      reps: "10",
      weight: "60"
    }]
  }]);
  const exOptions = EXERCISES.map(e => ({
    value: e.id,
    label: e.name
  }));
  const addSeq = () => setSequences(s => [...s, {
    phase: "main",
    sets: []
  }]);
  const removeSeq = i => setSequences(s => s.filter((_, j) => j !== i));
  const setPhase = (i, phase) => setSequences(s => s.map((q, j) => j === i ? {
    ...q,
    phase
  } : q));
  const addSet = i => setSequences(s => s.map((q, j) => j === i ? {
    ...q,
    sets: [...q.sets, {
      exId: "",
      type: "STRENGTH",
      reps: "",
      weight: ""
    }]
  } : q));
  const updSet = (i, k, patch) => setSequences(s => s.map((q, j) => j === i ? {
    ...q,
    sets: q.sets.map((st, m) => m === k ? {
      ...st,
      ...patch
    } : st)
  } : q));
  const rmSet = (i, k) => setSequences(s => s.map((q, j) => j === i ? {
    ...q,
    sets: q.sets.filter((_, m) => m !== k)
  } : q));
  return /*#__PURE__*/React.createElement("div", {
    className: "page",
    style: {
      maxWidth: 720
    }
  }, /*#__PURE__*/React.createElement(Field, {
    label: "Start time",
    htmlFor: "st"
  }, /*#__PURE__*/React.createElement(Input, {
    id: "st",
    type: "datetime-local",
    defaultValue: "2026-06-06T08:30",
    style: {
      maxWidth: 260
    }
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      margin: "24px 0 14px"
    }
  }, /*#__PURE__*/React.createElement("h3", {
    className: "section-title",
    style: {
      margin: 0
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "layers"
  }), " Sequences"), /*#__PURE__*/React.createElement(Button, {
    variant: "outline",
    size: "sm",
    onClick: addSeq,
    iconStart: /*#__PURE__*/React.createElement(Icon, {
      name: "plus",
      size: 15
    })
  }, "Add sequence")), sequences.length === 0 && /*#__PURE__*/React.createElement("div", {
    className: "empty-note"
  }, "Add at least one sequence to record your workout."), sequences.map((seq, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    className: "seq"
  }, /*#__PURE__*/React.createElement("div", {
    className: "seq__head"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 10
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "eyebrow"
  }, "Phase"), /*#__PURE__*/React.createElement("div", {
    style: {
      width: 150
    }
  }, /*#__PURE__*/React.createElement(Select, {
    value: seq.phase,
    onChange: e => setPhase(i, e.target.value),
    options: [{
      value: "warmup",
      label: "Warmup"
    }, {
      value: "main",
      label: "Main"
    }, {
      value: "cooldown",
      label: "Cooldown"
    }]
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 8
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "outline",
    size: "sm",
    onClick: () => addSet(i),
    iconStart: /*#__PURE__*/React.createElement(Icon, {
      name: "plus",
      size: 14
    })
  }, "Add set"), /*#__PURE__*/React.createElement(IconButton, {
    "aria-label": "Remove sequence",
    variant: "destructive",
    size: "sm",
    onClick: () => removeSeq(i)
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "trash-2",
    size: 14
  })))), seq.sets.length === 0 && /*#__PURE__*/React.createElement("p", {
    className: "muted",
    style: {
      fontSize: 13,
      margin: "4px 2px"
    }
  }, "No sets yet \u2014 add one above."), /*#__PURE__*/React.createElement("div", {
    className: "seq__sets"
  }, seq.sets.map((st, k) => /*#__PURE__*/React.createElement("div", {
    key: k,
    style: {
      display: "grid",
      gridTemplateColumns: "1fr 92px 92px auto",
      gap: 10,
      alignItems: "end"
    }
  }, /*#__PURE__*/React.createElement(Field, {
    label: k === 0 ? "Exercise" : undefined
  }, /*#__PURE__*/React.createElement(Select, {
    value: st.exId,
    onChange: e => updSet(i, k, {
      exId: e.target.value
    })
  }, /*#__PURE__*/React.createElement("option", {
    value: ""
  }, "Select exercise\u2026"), exOptions.map(o => /*#__PURE__*/React.createElement("option", {
    key: o.value,
    value: o.value
  }, o.label)))), /*#__PURE__*/React.createElement(Field, {
    label: k === 0 ? "Reps" : undefined
  }, /*#__PURE__*/React.createElement(Input, {
    type: "number",
    placeholder: "10",
    value: st.reps,
    onChange: e => updSet(i, k, {
      reps: e.target.value
    })
  })), /*#__PURE__*/React.createElement(Field, {
    label: k === 0 ? "Weight" : undefined
  }, /*#__PURE__*/React.createElement(Input, {
    type: "number",
    placeholder: "60",
    value: st.weight,
    onChange: e => updSet(i, k, {
      weight: e.target.value
    })
  })), /*#__PURE__*/React.createElement(IconButton, {
    "aria-label": "Remove set",
    variant: "ghost",
    size: "md",
    onClick: () => rmSet(i, k)
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "x",
    size: 16
  }))))))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 10,
      marginTop: 18
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "gradient",
    iconStart: /*#__PURE__*/React.createElement(Icon, {
      name: "save",
      size: 16,
      color: "#fff"
    })
  }, "Save workout"), /*#__PURE__*/React.createElement(Button, {
    variant: "ghost"
  }, "Cancel")));
}
window.BuilderScreen = BuilderScreen;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/app/BuilderScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/app/CoachScreen.jsx
try { (() => {
function GeneratedWorkout({
  session,
  onAdd,
  added
}) {
  return /*#__PURE__*/React.createElement(Card, {
    className: "gen-card",
    style: {
      marginTop: 6
    }
  }, /*#__PURE__*/React.createElement(CardHeader, null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 10
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "dumbbell",
    size: 18,
    color: "var(--ember-500)"
  }), /*#__PURE__*/React.createElement(CardTitle, null, session.title)), /*#__PURE__*/React.createElement(CardDescription, null, "~45 min \xB7 6 movements \xB7 dumbbell & barbell")), /*#__PURE__*/React.createElement(CardContent, null, session.phases.map(ph => /*#__PURE__*/React.createElement("div", {
    key: ph.phase
  }, /*#__PURE__*/React.createElement("div", {
    className: "phase-label"
  }, ph.phase), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: 6
    }
  }, ph.sets.map((s, i) => /*#__PURE__*/React.createElement(SetRow, {
    key: i,
    name: s.name,
    sub: s.sub,
    metrics: s.metrics
  })))))), /*#__PURE__*/React.createElement(CardFooter, null, /*#__PURE__*/React.createElement(Button, {
    variant: added ? "secondary" : "primary",
    size: "sm",
    onClick: onAdd,
    iconStart: /*#__PURE__*/React.createElement(Icon, {
      name: added ? "check" : "plus",
      size: 15
    })
  }, added ? "Added to Today" : "Add to Today"), /*#__PURE__*/React.createElement(Button, {
    variant: "ghost",
    size: "sm",
    iconStart: /*#__PURE__*/React.createElement(Icon, {
      name: "refresh-cw",
      size: 15
    })
  }, "Regenerate")));
}
function CoachScreen({
  onAddSession
}) {
  const [messages, setMessages] = React.useState([]);
  const [draft, setDraft] = React.useState("");
  const [added, setAdded] = React.useState(false);
  const streamRef = React.useRef(null);
  const suggestions = [{
    icon: "sparkles",
    text: "Build me a 30-min upper-body dumbbell session",
    route: "WORKOUT_GENERATE"
  }, {
    icon: "heart-pulse",
    text: "How many rest days for hypertrophy?",
    route: "COACH"
  }, {
    icon: "clipboard-check",
    text: "I did 3×10 bench at 60kg and a 20-min run",
    route: "WORKOUT_LOG"
  }];
  React.useEffect(() => {
    if (streamRef.current) streamRef.current.scrollTop = streamRef.current.scrollHeight;
  }, [messages]);
  function reply(text, route) {
    // canned coach responses keyed by route
    if (route === "WORKOUT_GENERATE") {
      return {
        from: "coach",
        route,
        text: "Here's a session tuned to your push day and the equipment in your profile. Want me to drop it into Today?",
        workout: TODAY_SESSION,
        meta: "conf 0.95 · 1.8s"
      };
    }
    if (route === "WORKOUT_LOG") {
      return {
        from: "coach",
        route,
        text: "Logged — bench press 3×10 @ 60 kg plus a 20-min cardio run. Nice work, that's 1,800 kg of volume on chest today.",
        meta: "conf 0.93 · 2.1s"
      };
    }
    if (route === "COACH") {
      return {
        from: "coach",
        route,
        text: "For hypertrophy most lifters do well with 1–2 rest days a week, training each muscle group twice with ~48h between sessions. Recovery is where the growth happens.",
        meta: "conf 0.97 · 0.4s"
      };
    }
    return {
      from: "coach",
      route: "FALLBACK",
      text: "I'm your fitness coach — I can plan workouts, answer training questions, and log your sessions. Ask me anything in that lane!",
      meta: "conf 0.99 · 0.4s"
    };
  }
  function classify(t) {
    const s = t.toLowerCase();
    if (/(build|generate|plan|give me|workout|session)/.test(s)) return "WORKOUT_GENERATE";
    if (/(did|logged|completed|i just|reps|sets)/.test(s)) return "WORKOUT_LOG";
    if (/(how|why|what|should|many|rest|muscle)/.test(s)) return "COACH";
    return "FALLBACK";
  }
  function send(text, forcedRoute) {
    if (!text.trim()) return;
    const route = forcedRoute || classify(text);
    setMessages(m => [...m, {
      from: "user",
      text
    }]);
    setDraft("");
    setTimeout(() => setMessages(m => [...m, reply(text, route)]), 480);
  }
  return /*#__PURE__*/React.createElement("div", {
    className: "coach-wrap"
  }, /*#__PURE__*/React.createElement("div", {
    className: "coach-stream ww-scroll",
    ref: streamRef
  }, /*#__PURE__*/React.createElement("div", {
    className: "coach-inner"
  }, messages.length === 0 && /*#__PURE__*/React.createElement("div", {
    className: "coach-hero"
  }, /*#__PURE__*/React.createElement("img", {
    className: "glyph",
    src: "../../assets/logo-mascot.png",
    alt: ""
  }), /*#__PURE__*/React.createElement("h2", null, "What are we training today?"), /*#__PURE__*/React.createElement("p", null, "Ask for a workout, log what you did, or get coaching \u2014 your AI strength coach routes it for you.")), messages.map((m, i) => m.from === "user" ? /*#__PURE__*/React.createElement(ChatBubble, {
    key: i,
    from: "user",
    avatar: /*#__PURE__*/React.createElement(Avatar, {
      name: "Jhona Q",
      size: "sm"
    })
  }, m.text) : /*#__PURE__*/React.createElement(ChatBubble, {
    key: i,
    from: "coach",
    route: m.route,
    avatar: /*#__PURE__*/React.createElement(CoachGlyph, null),
    meta: m.meta
  }, m.text, m.workout && /*#__PURE__*/React.createElement(GeneratedWorkout, {
    session: m.workout,
    added: added,
    onAdd: () => {
      setAdded(true);
      onAddSession && onAddSession();
    }
  }))))), /*#__PURE__*/React.createElement("div", {
    className: "coach-composer"
  }, /*#__PURE__*/React.createElement("div", {
    className: "composer-inner"
  }, messages.length === 0 && /*#__PURE__*/React.createElement("div", {
    className: "suggest-row"
  }, suggestions.map((s, i) => /*#__PURE__*/React.createElement("button", {
    key: i,
    className: "suggest",
    onClick: () => send(s.text, s.route)
  }, /*#__PURE__*/React.createElement(Icon, {
    name: s.icon,
    size: 14
  }), " ", s.text))), /*#__PURE__*/React.createElement("div", {
    className: "composer-box"
  }, /*#__PURE__*/React.createElement("textarea", {
    rows: 1,
    placeholder: "Message your coach\u2026",
    value: draft,
    onChange: e => setDraft(e.target.value),
    onKeyDown: e => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        send(draft);
      }
    }
  }), /*#__PURE__*/React.createElement(Button, {
    variant: "gradient",
    size: "md",
    onClick: () => send(draft),
    iconStart: /*#__PURE__*/React.createElement(Icon, {
      name: "arrow-up",
      size: 16,
      color: "#fff"
    })
  })))));
}
window.CoachScreen = CoachScreen;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/app/CoachScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/app/ExercisesScreen.jsx
try { (() => {
function ExercisesScreen() {
  const [q, setQ] = React.useState("");
  const [filters, setFilters] = React.useState([]);
  const allMuscles = ["Chest", "Back", "Shoulders", "Quads", "Biceps", "Triceps", "Core"];
  const toggle = m => setFilters(f => f.includes(m) ? f.filter(x => x !== m) : [...f, m]);
  const rows = EXERCISES.filter(e => {
    const matchesQ = !q || e.name.toLowerCase().includes(q.toLowerCase());
    const matchesF = filters.length === 0 || e.muscles.some(m => filters.includes(m));
    return matchesQ && matchesF;
  });
  return /*#__PURE__*/React.createElement("div", {
    className: "page"
  }, /*#__PURE__*/React.createElement("div", {
    className: "filter-bar"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 280
    }
  }, /*#__PURE__*/React.createElement(Input, {
    placeholder: "Search exercises\u2026",
    value: q,
    onChange: e => setQ(e.target.value),
    icon: /*#__PURE__*/React.createElement(Icon, {
      name: "search",
      size: 16
    })
  })), /*#__PURE__*/React.createElement("div", {
    className: "chips"
  }, allMuscles.map(m => /*#__PURE__*/React.createElement("button", {
    key: m,
    className: "suggest",
    style: filters.includes(m) ? {
      background: "var(--ember-500)",
      color: "#fff",
      borderColor: "var(--ember-500)"
    } : {},
    onClick: () => toggle(m)
  }, m)))), filters.length > 0 && /*#__PURE__*/React.createElement("div", {
    className: "chips",
    style: {
      marginBottom: 14
    }
  }, filters.map(f => /*#__PURE__*/React.createElement(Tag, {
    key: f,
    onRemove: () => toggle(f)
  }, f))), /*#__PURE__*/React.createElement("table", {
    className: "ex-table"
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", {
    style: {
      width: "36%"
    }
  }, "Exercise"), /*#__PURE__*/React.createElement("th", null, "Category"), /*#__PURE__*/React.createElement("th", null, "Muscle groups"), /*#__PURE__*/React.createElement("th", null, "Equipment"))), /*#__PURE__*/React.createElement("tbody", null, rows.map(e => /*#__PURE__*/React.createElement("tr", {
    key: e.id
  }, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("span", {
    className: "tier-dot",
    style: {
      background: TIER_COLOR[e.tier]
    }
  }), /*#__PURE__*/React.createElement("span", {
    className: "ex-name"
  }, e.name)), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement(Badge, {
    variant: e.category === "Cardio" ? "amber" : e.category === "Core" ? "secondary" : "soft"
  }, e.category)), /*#__PURE__*/React.createElement("td", {
    className: "muted"
  }, e.muscles.join(", ")), /*#__PURE__*/React.createElement("td", {
    className: "muted"
  }, e.equip.join(", ")))), rows.length === 0 && /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
    colSpan: 4,
    style: {
      textAlign: "center",
      color: "var(--muted-foreground)",
      padding: 28
    }
  }, "No exercises match your filters.")))), /*#__PURE__*/React.createElement("p", {
    className: "muted",
    style: {
      fontSize: 12,
      marginTop: 12,
      display: "flex",
      gap: 16
    }
  }, /*#__PURE__*/React.createElement("span", null, /*#__PURE__*/React.createElement("span", {
    className: "tier-dot",
    style: {
      background: TIER_COLOR[1]
    }
  }), "Tier 1 \u2014 compound"), /*#__PURE__*/React.createElement("span", null, /*#__PURE__*/React.createElement("span", {
    className: "tier-dot",
    style: {
      background: TIER_COLOR[2]
    }
  }), "Tier 2 \u2014 accessory"), /*#__PURE__*/React.createElement("span", null, /*#__PURE__*/React.createElement("span", {
    className: "tier-dot",
    style: {
      background: TIER_COLOR[3]
    }
  }), "Tier 3 \u2014 isolation")));
}
window.ExercisesScreen = ExercisesScreen;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/app/ExercisesScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/app/Sidebar.jsx
try { (() => {
function Sidebar({
  route,
  setRoute,
  onLogout
}) {
  const nav = [{
    id: "coach",
    label: "Coach",
    icon: "sparkles"
  }, {
    id: "today",
    label: "Today",
    icon: "dumbbell"
  }, {
    id: "exercises",
    label: "Exercises",
    icon: "list"
  }, {
    id: "builder",
    label: "Build workout",
    icon: "plus-circle"
  }];
  return /*#__PURE__*/React.createElement("aside", {
    className: "side"
  }, /*#__PURE__*/React.createElement("div", {
    className: "side__brand"
  }, /*#__PURE__*/React.createElement("img", {
    src: "../../assets/logo-mascot.png",
    alt: ""
  }), /*#__PURE__*/React.createElement("b", null, "Workout", /*#__PURE__*/React.createElement("span", null, " Wiz"))), /*#__PURE__*/React.createElement("div", {
    className: "side__sec"
  }, "Train"), nav.map(n => /*#__PURE__*/React.createElement("button", {
    key: n.id,
    className: "nav-item",
    "data-active": route === n.id,
    onClick: () => setRoute(n.id)
  }, /*#__PURE__*/React.createElement(Icon, {
    name: n.icon
  }), n.label)), /*#__PURE__*/React.createElement("div", {
    className: "side__sec"
  }, "Progress"), /*#__PURE__*/React.createElement("button", {
    className: "nav-item",
    onClick: () => setRoute("today")
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "trending-up"
  }), " Stats"), /*#__PURE__*/React.createElement("button", {
    className: "nav-item"
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "trophy"
  }), " Personal records"), /*#__PURE__*/React.createElement("div", {
    className: "side__spacer"
  }), /*#__PURE__*/React.createElement("div", {
    className: "side__user"
  }, /*#__PURE__*/React.createElement(Avatar, {
    name: "Jhona Querouts",
    size: "sm"
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "nm"
  }, "Jhona Q."), /*#__PURE__*/React.createElement("div", {
    className: "em"
  }, "jhona@gym.com")), /*#__PURE__*/React.createElement(IconButton, {
    "aria-label": "Log out",
    variant: "ghost",
    size: "sm",
    onClick: onLogout
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "log-out",
    size: 15
  }))));
}
window.Sidebar = Sidebar;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/app/Sidebar.jsx", error: String((e && e.message) || e) }); }

// ui_kits/app/TodayScreen.jsx
try { (() => {
function TodayScreen({
  hasSession
}) {
  const [done, setDone] = React.useState({});
  const session = TODAY_SESSION;
  const allSets = session.phases.flatMap(p => p.sets);
  const completed = Object.values(done).filter(Boolean).length;
  const pct = Math.round(completed / allSets.length * 100);
  return /*#__PURE__*/React.createElement("div", {
    className: "page"
  }, /*#__PURE__*/React.createElement("div", {
    className: "grid-stats",
    style: {
      marginBottom: 22
    }
  }, /*#__PURE__*/React.createElement(StatTile, {
    label: "Weekly volume",
    value: "12,480",
    unit: "kg",
    delta: {
      dir: "up",
      label: "8%"
    },
    icon: /*#__PURE__*/React.createElement(Icon, {
      name: "dumbbell",
      size: 14,
      color: "var(--ember-500)"
    })
  }), /*#__PURE__*/React.createElement(StatTile, {
    label: "Streak",
    value: "14",
    unit: "days",
    icon: /*#__PURE__*/React.createElement(Icon, {
      name: "flame",
      size: 14,
      color: "var(--ember-500)"
    })
  }), /*#__PURE__*/React.createElement(StatTile, {
    label: "Sessions",
    value: "5",
    unit: "/ 6",
    delta: {
      dir: "up",
      label: "on pace"
    },
    icon: /*#__PURE__*/React.createElement(Icon, {
      name: "calendar-check",
      size: 14,
      color: "var(--ember-500)"
    })
  }), /*#__PURE__*/React.createElement(StatTile, {
    label: "Avg session",
    value: "47",
    unit: "min",
    delta: {
      dir: "down",
      label: "3 min"
    },
    icon: /*#__PURE__*/React.createElement(Icon, {
      name: "timer",
      size: 14,
      color: "var(--ember-500)"
    })
  })), /*#__PURE__*/React.createElement("div", {
    className: "grid-2"
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h3", {
    className: "section-title"
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "dumbbell"
  }), " Today's session"), hasSession ? /*#__PURE__*/React.createElement(Card, {
    flush: true
  }, /*#__PURE__*/React.createElement(CardHeader, null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between"
    }
  }, /*#__PURE__*/React.createElement(CardTitle, null, session.title), /*#__PURE__*/React.createElement(Badge, {
    variant: "soft"
  }, completed, "/", allSets.length, " sets")), /*#__PURE__*/React.createElement(CardDescription, null, "Generated by your coach \xB7 ~45 min")), /*#__PURE__*/React.createElement(CardContent, null, /*#__PURE__*/React.createElement(Progress, {
    value: pct
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      height: 14
    }
  }), session.phases.map(ph => /*#__PURE__*/React.createElement("div", {
    key: ph.phase
  }, /*#__PURE__*/React.createElement("div", {
    className: "phase-label"
  }, ph.phase), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: 6,
      marginBottom: 6
    }
  }, ph.sets.map((s, i) => {
    const key = ph.phase + i;
    return /*#__PURE__*/React.createElement(SetRow, {
      key: key,
      name: s.name,
      sub: s.sub,
      metrics: s.metrics,
      done: !!done[key],
      action: /*#__PURE__*/React.createElement(Checkbox, {
        checked: !!done[key],
        onChange: v => setDone(d => ({
          ...d,
          [key]: v
        }))
      })
    });
  }))))), /*#__PURE__*/React.createElement(CardFooter, null, /*#__PURE__*/React.createElement(Button, {
    variant: "gradient",
    iconStart: /*#__PURE__*/React.createElement(Icon, {
      name: "play",
      size: 15,
      color: "#fff"
    })
  }, "Start session"), /*#__PURE__*/React.createElement(Button, {
    variant: "ghost",
    iconStart: /*#__PURE__*/React.createElement(Icon, {
      name: "pencil",
      size: 15
    })
  }, "Edit"))) : /*#__PURE__*/React.createElement("div", {
    className: "empty-note"
  }, "No session planned yet. Ask your coach to build one \u2192")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h3", {
    className: "section-title"
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "timer"
  }), " Rest timer"), /*#__PURE__*/React.createElement(Card, {
    flush: true
  }, /*#__PURE__*/React.createElement(CardContent, {
    style: {
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: 16,
      padding: 24
    }
  }, /*#__PURE__*/React.createElement(ProgressRing, {
    value: 62,
    label: "0:45",
    sublabel: "rest",
    size: 132,
    stroke: 11
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 8
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "outline",
    size: "sm",
    iconStart: /*#__PURE__*/React.createElement(Icon, {
      name: "rotate-ccw",
      size: 14
    })
  }, "Reset"), /*#__PURE__*/React.createElement(Button, {
    variant: "primary",
    size: "sm",
    iconStart: /*#__PURE__*/React.createElement(Icon, {
      name: "pause",
      size: 14,
      color: "#fff"
    })
  }, "Pause")))), /*#__PURE__*/React.createElement("h3", {
    className: "section-title",
    style: {
      marginTop: 22
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "flame"
  }), " This week"), /*#__PURE__*/React.createElement(Card, {
    flush: true
  }, /*#__PURE__*/React.createElement(CardContent, {
    style: {
      display: "flex",
      justifyContent: "space-between",
      gap: 4
    }
  }, ["M", "T", "W", "T", "F", "S", "S"].map((d, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 30,
      height: 30,
      borderRadius: "50%",
      display: "grid",
      placeItems: "center",
      fontSize: 13,
      fontWeight: 600,
      background: i < 5 ? "var(--gradient-ember)" : "var(--muted)",
      color: i < 5 ? "#fff" : "var(--muted-foreground)"
    }
  }, i < 5 ? /*#__PURE__*/React.createElement(Icon, {
    name: "check",
    size: 15,
    color: "#fff"
  }) : ""), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: "var(--muted-foreground)"
    }
  }, d))))))));
}
window.TodayScreen = TodayScreen;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/app/TodayScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/app/data.jsx
try { (() => {
/* Shared helpers + sample data for the Workout Wiz app kit. */

// Lucide icon → React element (lucide UMD provides icon node factories)
function Icon({
  name,
  size = 18,
  color,
  style,
  strokeWidth = 1.75
}) {
  const node = lucide[name] ? lucide.createElement(lucide[name]) : null;
  if (!node) return null;
  node.setAttribute("width", size);
  node.setAttribute("height", size);
  node.setAttribute("stroke-width", strokeWidth);
  return /*#__PURE__*/React.createElement("span", {
    style: {
      display: "inline-flex",
      color,
      ...style
    },
    dangerouslySetInnerHTML: {
      __html: node.outerHTML
    }
  });
}
function CoachGlyph({
  size = 36
}) {
  return /*#__PURE__*/React.createElement("span", {
    className: "ww-coach-avatar",
    style: {
      width: size,
      height: size
    }
  }, /*#__PURE__*/React.createElement("img", {
    src: "../../assets/logo-mascot.png",
    alt: "Wiz",
    style: {
      width: size * 0.66,
      height: size * 0.66
    }
  }));
}
const EXERCISES = [{
  id: "1",
  name: "Barbell Bench Press",
  category: "Strength",
  muscles: ["Chest", "Triceps"],
  equip: ["Barbell"],
  tier: 1
}, {
  id: "2",
  name: "Back Squat",
  category: "Strength",
  muscles: ["Quads", "Glutes"],
  equip: ["Barbell"],
  tier: 1
}, {
  id: "3",
  name: "Deadlift",
  category: "Strength",
  muscles: ["Back", "Hamstrings"],
  equip: ["Barbell"],
  tier: 1
}, {
  id: "4",
  name: "Dumbbell Row",
  category: "Strength",
  muscles: ["Back", "Biceps"],
  equip: ["Dumbbell"],
  tier: 2
}, {
  id: "5",
  name: "Overhead Press",
  category: "Strength",
  muscles: ["Shoulders", "Triceps"],
  equip: ["Barbell"],
  tier: 2
}, {
  id: "6",
  name: "Pull-up",
  category: "Strength",
  muscles: ["Back", "Biceps"],
  equip: ["Bodyweight"],
  tier: 1
}, {
  id: "7",
  name: "Dumbbell Bicep Curl",
  category: "Strength",
  muscles: ["Biceps"],
  equip: ["Dumbbell"],
  tier: 3
}, {
  id: "8",
  name: "Romanian Deadlift",
  category: "Strength",
  muscles: ["Hamstrings", "Glutes"],
  equip: ["Barbell"],
  tier: 2
}, {
  id: "9",
  name: "Incline Dumbbell Press",
  category: "Strength",
  muscles: ["Chest", "Shoulders"],
  equip: ["Dumbbell"],
  tier: 2
}, {
  id: "10",
  name: "Lat Pulldown",
  category: "Strength",
  muscles: ["Back"],
  equip: ["Cable"],
  tier: 3
}, {
  id: "11",
  name: "Treadmill Run",
  category: "Cardio",
  muscles: ["Full body"],
  equip: ["Machine"],
  tier: 2
}, {
  id: "12",
  name: "Plank",
  category: "Core",
  muscles: ["Core"],
  equip: ["Bodyweight"],
  tier: 3
}];
const TIER_COLOR = {
  1: "var(--ember-500)",
  2: "var(--amber-500)",
  3: "var(--stone-400)"
};

// A coach-generated session used by the Coach + Today screens
const TODAY_SESSION = {
  title: "Upper Body · Push",
  phases: [{
    phase: "Warmup",
    sets: [{
      name: "Arm Circles",
      sub: "Shoulders",
      metrics: [{
        value: "2×60",
        unit: "sec"
      }]
    }, {
      name: "Band Pull-apart",
      sub: "Rear delts",
      metrics: [{
        value: "2×15",
        unit: "reps"
      }]
    }]
  }, {
    phase: "Main",
    sets: [{
      name: "Barbell Bench Press",
      sub: "Chest · Barbell",
      metrics: [{
        value: "3×10",
        unit: "reps"
      }, {
        value: "60",
        unit: "kg"
      }]
    }, {
      name: "Overhead Press",
      sub: "Shoulders · Barbell",
      metrics: [{
        value: "3×8",
        unit: "reps"
      }, {
        value: "40",
        unit: "kg"
      }]
    }, {
      name: "Incline DB Press",
      sub: "Chest · Dumbbell",
      metrics: [{
        value: "3×12",
        unit: "reps"
      }, {
        value: "22",
        unit: "kg"
      }]
    }, {
      name: "Tricep Pushdown",
      sub: "Triceps · Cable",
      metrics: [{
        value: "3×15",
        unit: "reps"
      }, {
        value: "30",
        unit: "kg"
      }]
    }]
  }, {
    phase: "Cooldown",
    sets: [{
      name: "Chest Stretch",
      sub: "Pecs",
      metrics: [{
        value: "60",
        unit: "sec"
      }]
    }]
  }]
};
Object.assign(window, {
  Icon,
  CoachGlyph,
  EXERCISES,
  TIER_COLOR,
  TODAY_SESSION
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/app/data.jsx", error: String((e && e.message) || e) }); }

__ds_ns.Avatar = __ds_scope.Avatar;

__ds_ns.Badge = __ds_scope.Badge;

__ds_ns.Button = __ds_scope.Button;

__ds_ns.Card = __ds_scope.Card;

__ds_ns.CardHeader = __ds_scope.CardHeader;

__ds_ns.CardTitle = __ds_scope.CardTitle;

__ds_ns.CardDescription = __ds_scope.CardDescription;

__ds_ns.CardContent = __ds_scope.CardContent;

__ds_ns.CardFooter = __ds_scope.CardFooter;

__ds_ns.IconButton = __ds_scope.IconButton;

__ds_ns.Tag = __ds_scope.Tag;

__ds_ns.ChatBubble = __ds_scope.ChatBubble;

__ds_ns.Progress = __ds_scope.Progress;

__ds_ns.ProgressRing = __ds_scope.ProgressRing;

__ds_ns.SetRow = __ds_scope.SetRow;

__ds_ns.StatTile = __ds_scope.StatTile;

__ds_ns.Checkbox = __ds_scope.Checkbox;

__ds_ns.Radio = __ds_scope.Radio;

__ds_ns.Field = __ds_scope.Field;

__ds_ns.Label = __ds_scope.Label;

__ds_ns.Input = __ds_scope.Input;

__ds_ns.Select = __ds_scope.Select;

__ds_ns.Switch = __ds_scope.Switch;

__ds_ns.Textarea = __ds_scope.Textarea;

__ds_ns.Tabs = __ds_scope.Tabs;

})();
