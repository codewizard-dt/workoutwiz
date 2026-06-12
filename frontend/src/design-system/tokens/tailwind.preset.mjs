const houseStyle = {
  theme: {
    extend: {
      colors: {
        canvas: "var(--canvas)",
        surface: "var(--surface)",
        paper: "var(--paper)",
        ink: "var(--ink)",
        "ink-2": "var(--ink-2)",
        "muted-2": "var(--muted-2)",
        line: "var(--line)",
        "line-2": "var(--line-2)",
      },
      borderRadius: {
        card: "14px",
        pill: "999px",
      },
      boxShadow: {
        card: "0 1px 2px 0 rgb(16 17 26 / 0.04)",
        "card-hover":
          "0 2px 4px -1px rgb(16 17 26 / 0.06), 0 8px 24px -6px rgb(16 17 26 / 0.08)",
        pop: "0 18px 44px -14px rgb(10 11 18 / 0.34), 0 4px 12px -4px rgb(10 11 18 / 0.16)",
        ring: "0 0 0 1px rgb(16 17 26 / 0.04)",
      },
      letterSpacing: {
        tight: "-0.01em",
      },
      keyframes: {
        fadeIn: { from: { opacity: "0" }, to: { opacity: "1" } },
        riseIn: {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        popIn: {
          from: { opacity: "0", transform: "scale(0.96)" },
          to: { opacity: "1", transform: "scale(1)" },
        },
        revealIn: {
          from: { opacity: "0", transform: "scale(1.03)" },
          to: { opacity: "1", transform: "scale(1)" },
        },
        travel: {
          "0%": { left: "-10%", opacity: "0" },
          "20%, 80%": { opacity: "1" },
          "100%": { left: "110%", opacity: "0" },
        },
        shimmer: {
          from: { transform: "translateX(-100%)" },
          to: { transform: "translateX(100%)" },
        },
        breathe: {
          "0%, 100%": { opacity: "0.35", transform: "scale(1)" },
          "50%": { opacity: "0.85", transform: "scale(1.05)" },
        },
        spinSlow: {
          from: { transform: "rotate(0deg)" },
          to: { transform: "rotate(360deg)" },
        },
        drawIn: {
          from: { strokeDashoffset: "1" },
          to: { strokeDashoffset: "0" },
        },
        bounceSoft: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(3px)" },
        },
      },
      animation: {
        fadeIn: "fadeIn 0.35s ease both",
        riseIn: "riseIn 0.5s cubic-bezier(0.22,1,0.36,1) both",
        popIn: "popIn 0.22s cubic-bezier(0.22,1,0.36,1) both",
        revealIn: "revealIn 0.5s cubic-bezier(0.22,1,0.36,1) both",
        travel: "travel 1.5s ease-in-out infinite",
        shimmer: "shimmer 1.7s ease-in-out infinite",
        breathe: "breathe 2.4s ease-in-out infinite",
        spinSlow: "spinSlow 9s linear infinite",
        drawIn: "drawIn 0.45s ease-out forwards",
        bounceSoft: "bounceSoft 1.3s ease-in-out infinite",
      },
    },
  },
};

export default houseStyle;
