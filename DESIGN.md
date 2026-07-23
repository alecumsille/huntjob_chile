# DESIGN.md — Sistema de Diseño Semántico (HuntJob Chile)

Inspirado en [Design.md](https://getdesign.md/design-md): Especificación canónica de diseño UI/UX, tokens visuales y patrones estéticos para **HuntJob Chile**.

---

## 🎨 1. Paleta de Colores & Tokens HSL

```css
:root {
  /* Dark Mode Elegante / Titanium Slate */
  --bg-primary: HSL(222, 47%, 11%);      /* #0F172A - Azul Nocturno Profundo */
  --bg-secondary: HSL(217, 33%, 17%);    /* #1E293B - Card Background */
  --bg-tertiary: HSL(215, 25%, 27%);     /* #334155 - Subtle Borders */

  /* Colores de Acento Vibrantes */
  --accent-cyan: HSL(191, 91%, 48%);     /* #0EA5E9 - Primario / Acción */
  --accent-indigo: HSL(246, 83%, 64%);   /* #6366F1 - Gradiente Secundario */
  --accent-emerald: HSL(158, 64%, 52%);  /* #10B981 - Exitos / Match ATS Alto */
  --accent-amber: HSL(38, 92%, 50%);     /* #F59E0B - Advertencias / Match Medio */
  --accent-rose: HSL(347, 89%, 60%);    /* #F43F5E - Errores / Match Bajo */

  /* Tipografía */
  --text-main: HSL(210, 40%, 98%);       /* #F8FAFC - Texto Principal */
  --text-muted: HSL(215, 20%, 65%);      /* #94A3B8 - Texto Secundario */
}
```

---

## 💎 2. Efectos & Glassmorphism

- **Cards en Glassmorphism:**
  ```css
  background: rgba(30, 41, 59, 0.7);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  ```
- **Sombras & Elevación:**
  ```css
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
  ```

---

## 🔤 3. Tipografía & Jerarquía Visual

- **Fuente Primaria:** `Inter`, `system-ui`, `-apple-system`, `sans-serif`
- **Fuente Secundaria / Títulos:** `Outfit`, `sans-serif`
- **Fuente Monospace (Código/ATS Keywords):** `JetBrains Mono`, `monospace`
- **Escala de Títulos:**
  - `H1`: 2.25rem (36px), Bold 700, Letter-spacing -0.02em
  - `H2`: 1.75rem (28px), SemiBold 600
  - `H3`: 1.25rem (20px), Medium 500
  - `Body`: 1.0rem (16px), Regular 400, Line-height 1.6

---

## ⚡ 4. Micro-Animaciones & Transiciones

- **Hover en Botones:**
  `transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);`
  `transform: translateY(-2px);`
  `box-shadow: 0 10px 20px -5px rgba(14, 165, 233, 0.4);`
- **Indicadores de Carga (Spinners):**
  Pulsos de gradiente entre `--accent-cyan` y `--accent-indigo`.

---

## 🏷️ 5. Badges de Verificación ATS (Estilo Hallmark)

- **Match Alto (85% - 100%):** Fondo Emerald HSL(158, 64%, 52%, 0.15) con borde Emerald.
- **Match Medio (60% - 84%):** Fondo Amber HSL(38, 92%, 50%, 0.15) con borde Amber.
- **Match Bajo (0% - 59%):** Fondo Rose HSL(347, 89%, 60%, 0.15) con borde Rose.
