/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Katmanlı kurumsal charcoal-gri + koyu mavi zeminler (saf siyah yok).
        bg: "#0B0E14", // sayfa zemini (charcoal)
        surface: "#12161F", // kart
        raised: "#191F29", // yükseltilmiş yüzey (panel, input)
        hover: "#212836", // hover'da yüzey
        sidebar: "#0E121A", // sol navigasyon zemini (bir ton daha koyu)
        line: "rgba(255,255,255,0.08)", // yüzey ayrım kenarlığı
        "line-soft": "rgba(255,255,255,0.06)",
        // "İşlenmiş metal" aksanı — ince üst kenar parıltısı için.
        metal: "rgba(188,200,218,0.16)",
        // Durum renkleri
        ok: {
          DEFAULT: "#37C98A",
          dim: "rgba(55,201,138,0.14)",
          glow: "rgba(55,201,138,0.55)",
        },
        gold: {
          DEFAULT: "#E3B23C",
          dim: "rgba(227,178,60,0.13)",
          line: "rgba(227,178,60,0.34)",
        },
        // Mavi: birincil vurgu (ASELSAN mavisinin koyu zemine açılmış hali).
        brand: {
          DEFAULT: "#4C9AF5",
          hi: "#66ABF7",
          lo: "#3B82E8",
          glow: "rgba(76,154,245,0.55)",
          ring: "rgba(76,154,245,0.18)",
          dim: "rgba(76,154,245,0.14)",
        },
        // Turuncu: dikkat rengi (auto-fix rozetleri, uyarı, deneme sayısı).
        warn: {
          DEFAULT: "#F59E42",
          hi: "#F7B267",
          dim: "rgba(245,158,66,0.13)",
          line: "rgba(245,158,66,0.34)",
        },
        // Desatüre kırmızı: hata (neon yok).
        danger: {
          DEFAULT: "#E0796F",
          dim: "rgba(224,121,111,0.10)",
          line: "rgba(224,121,111,0.32)",
        },
        // Kırık beyaz metin: birincil ~%87, ikincil ~%60, soluk ~%40.
        ink: {
          DEFAULT: "#E6E8EC",
          muted: "#9BA3AF",
          faint: "#6B7382",
        },
      },
      fontFamily: {
        sans: ["Inter", "Segoe UI", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Consolas", "monospace"],
      },
      boxShadow: {
        card: "0 8px 24px rgba(0,0,0,0.35)",
        "card-hover": "0 12px 32px rgba(0,0,0,0.45)",
        "brand-glow": "0 0 0 3px rgba(76,154,245,0.18), 0 0 12px 2px rgba(76,154,245,0.5)",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(3px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-dot": {
          "0%,100%": { opacity: "1" },
          "50%": { opacity: "0.4" },
        },
        blink: {
          "0%,50%": { opacity: "1" },
          "50.01%,100%": { opacity: "0" },
        },
        "collapsible-down": {
          from: { height: "0" },
          to: { height: "var(--radix-collapsible-content-height)" },
        },
        "collapsible-up": {
          from: { height: "var(--radix-collapsible-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "fade-in": "fade-in 180ms ease-out",
        "pulse-dot": "pulse-dot 1.3s ease-in-out infinite",
        blink: "blink 1s steps(1) infinite",
        "collapsible-down": "collapsible-down 180ms ease-out",
        "collapsible-up": "collapsible-up 160ms ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
